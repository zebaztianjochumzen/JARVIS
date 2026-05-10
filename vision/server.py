"""JARVIS Vision Server — captures MacBook camera, runs YOLOv8-nano + hand gesture detection."""

import asyncio
import json
import os
import time
import threading
from queue import Queue as _Queue, Empty

import numpy as np
import cv2

# Force a specific camera index (0 = built-in MacBook FaceTime camera).
# Override with env var CAMERA_INDEX=1 if the wrong camera is selected.
CAMERA_INDEX = int(os.environ.get("CAMERA_INDEX", 0))
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

try:
    from vision.gesture_control import SwipeDetector as _SwipeDetector
    _gesture_detector: _SwipeDetector | None = _SwipeDetector()
except ImportError:
    _gesture_detector = None

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared state between capture thread and HTTP handlers
_lock = threading.Lock()
_latest_raw: np.ndarray | None = None
_latest_annotated: np.ndarray | None = None
_latest_detections: list[dict] = []

# Controls whether the camera loop is running; starts inactive
_active = threading.Event()

# ── Gesture WebSocket state ────────────────────────────────────────────────────
_gesture_q: _Queue = _Queue()
_gesture_ws_clients: list[WebSocket] = []
_gesture_ws_lock = threading.Lock()
_gesture_hand_visible: bool = False
_gesture_hand_ts: float = 0.0  # last time we sent a hand_status event

# HUD colour: BGR(247, 195, 79) ≈ JARVIS blue #4fc3f7
HUD_COLOR = (247, 195, 79)
HUD_DIM   = (180, 130, 50)


def _capture_loop():
    global _latest_raw, _latest_annotated, _latest_detections

    from ultralytics import YOLO
    model = YOLO("yolov8n.pt")  # ~6 MB — downloads automatically on first run

    cap = None
    while True:
        if not _active.is_set():
            # Release camera and clear state while inactive
            if cap is not None:
                cap.release()
                cap = None
            with _lock:
                _latest_raw        = None
                _latest_annotated  = None
                _latest_detections = []
            _active.wait()  # block until /start is called
            continue

        # Open / reopen camera
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(CAMERA_INDEX)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  1280)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            if not cap.isOpened():
                time.sleep(2)
                continue

        ret, frame = cap.read()
        if not ret:
            cap.release()
            cap = None
            time.sleep(0.5)
            continue

        annotated   = frame.copy()
        detections  = []

        results = model(frame, verbose=False, imgsz=640)
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf  = float(box.conf[0])
                label = model.names[int(box.cls[0])]
                detections.append({
                    "label":      label,
                    "confidence": round(conf, 2),
                    "box":        [x1, y1, x2, y2],
                })
                # HUD-style bracket corners instead of a full rectangle
                L = 14
                for (sx, sy, dx, dy) in [
                    (x1, y1, 1,  1),
                    (x2, y1, -1, 1),
                    (x1, y2, 1, -1),
                    (x2, y2, -1, -1),
                ]:
                    cv2.line(annotated, (sx, sy), (sx + dx*L, sy),          HUD_COLOR, 1, cv2.LINE_AA)
                    cv2.line(annotated, (sx, sy), (sx,        sy + dy*L),   HUD_COLOR, 1, cv2.LINE_AA)
                # Label
                txt = f"[ {label.upper()} ]  {conf:.0%}"
                cv2.putText(annotated, txt, (x1 + 4, y1 - 7),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.38, HUD_COLOR, 1, cv2.LINE_AA)

        # Status overlay (top-right)
        status = f"OBJECTS: {len(detections)}"
        (tw, th), _ = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)
        h, w = annotated.shape[:2]
        cv2.putText(annotated, status, (w - tw - 10, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, HUD_DIM, 1, cv2.LINE_AA)

        # ── Gesture detection ──────────────────────────────────────────────────
        if _gesture_detector is not None:
            global _gesture_hand_visible, _gesture_hand_ts
            try:
                annotated, gesture = _gesture_detector.process(annotated)
                now = time.time()
                if gesture:
                    _gesture_q.put({"type": "gesture", "gesture": gesture,
                                    "ts": time.strftime("%H:%M:%S")})
                new_visible = _gesture_detector.hand_visible
                if new_visible != _gesture_hand_visible or now - _gesture_hand_ts > 3.0:
                    _gesture_hand_visible = new_visible
                    _gesture_hand_ts = now
                    _gesture_q.put({"type": "hand_status", "visible": new_visible})
            except Exception:
                pass

        with _lock:
            _latest_raw        = frame.copy()
            _latest_annotated  = annotated
            _latest_detections = detections

        time.sleep(0.1)  # ~10 fps inference


threading.Thread(target=_capture_loop, daemon=True).start()


# ── Control endpoints ──────────────────────────────────────────────────────────

@app.post("/start")
def start_camera():
    _active.set()
    return {"status": "started"}


@app.post("/stop")
def stop_camera():
    _active.clear()
    return {"status": "stopped"}


# ── Stream endpoints ───────────────────────────────────────────────────────────

def _mjpeg_frames():
    while True:
        with _lock:
            frame = _latest_annotated
        if frame is None:
            time.sleep(0.05)
            continue
        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buf.tobytes()
            + b"\r\n"
        )
        time.sleep(0.05)  # ~20 fps stream


@app.get("/stream")
def video_stream():
    return StreamingResponse(
        _mjpeg_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


@app.get("/snapshot")
def snapshot():
    with _lock:
        frame = _latest_raw
    if frame is None:
        return JSONResponse({"error": "no frame yet"}, status_code=503)
    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return StreamingResponse(iter([buf.tobytes()]), media_type="image/jpeg")


@app.get("/detections")
def get_detections():
    with _lock:
        d = list(_latest_detections)
    return {"detections": d}


@app.get("/cameras")
def list_cameras():
    """Return all available camera indices so you can identify which is built-in vs phone."""
    found = []
    for i in range(6):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
            h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
            found.append({"index": i, "width": int(w), "height": int(h)})
            cap.release()
    return {"cameras": found, "active_index": CAMERA_INDEX}


@app.get("/health")
def health():
    with _lock:
        ready = _latest_raw is not None
    return {
        "status": "ok",
        "camera_ready": ready,
        "camera_active": _active.is_set(),
        "gesture_enabled": _gesture_detector is not None,
    }


# ── Gesture WebSocket ──────────────────────────────────────────────────────────

@app.on_event("startup")
async def _start_gesture_dispatcher() -> None:
    asyncio.create_task(_gesture_dispatcher())


async def _gesture_dispatcher() -> None:
    loop = asyncio.get_event_loop()
    while True:
        try:
            event = await loop.run_in_executor(None, lambda: _gesture_q.get(timeout=1))
        except Empty:
            continue
        payload = json.dumps(event)
        with _gesture_ws_lock:
            dead: list[WebSocket] = []
            for ws in _gesture_ws_clients:
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                _gesture_ws_clients.remove(ws)


@app.websocket("/ws/gestures")
async def gesture_websocket(ws: WebSocket) -> None:
    await ws.accept()
    with _gesture_ws_lock:
        _gesture_ws_clients.append(ws)
    try:
        while True:
            await ws.receive_text()  # keep alive — client sends nothing
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        with _gesture_ws_lock:
            if ws in _gesture_ws_clients:
                _gesture_ws_clients.remove(ws)
