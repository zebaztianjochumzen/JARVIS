"""JARVIS Vision Server — captures MacBook camera, runs YOLOv8-nano, streams MJPEG."""

import time
import threading
import numpy as np
import cv2
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

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
            cap = cv2.VideoCapture(0)
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


@app.get("/health")
def health():
    with _lock:
        ready = _latest_raw is not None
    return {"status": "ok", "camera_ready": ready, "camera_active": _active.is_set()}
