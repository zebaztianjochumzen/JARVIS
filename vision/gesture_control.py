"""MediaPipe Tasks-API hand swipe detector for JARVIS gesture control."""

import math
import os
import time
from collections import deque

import cv2
import mediapipe as mp
import numpy as np
from mediapipe import Image as _MpImage, ImageFormat as _MpFmt
from mediapipe.tasks import python as _mp_python
from mediapipe.tasks.python import vision as _mp_vision

# ── Model path ─────────────────────────────────────────────────────────────────
_MODEL = os.path.join(os.path.dirname(__file__), "..", "models", "hand_landmarker.task")

# ── Swipe tuning ───────────────────────────────────────────────────────────────
HISTORY_FRAMES = 15    # frames to track  (~0.75 s at 20 fps)
SWIPE_MIN_DIST = 0.18  # normalised screen fraction
COOLDOWN       = 1.4   # seconds between gestures

# ── Visuals ────────────────────────────────────────────────────────────────────
HUD_COLOR = (79, 195, 247)   # BGR — JARVIS blue
HUD_DIM   = (50, 120, 160)

# MediaPipe hand connections (index pairs into the 21 landmarks)
_CONNECTIONS = [
    (0,1),(1,2),(2,3),(3,4),       # thumb
    (0,5),(5,6),(6,7),(7,8),       # index
    (0,9),(9,10),(10,11),(11,12),  # middle
    (0,13),(13,14),(14,15),(15,16),# ring
    (0,17),(17,18),(18,19),(19,20),# pinky
    (5,9),(9,13),(13,17),          # palm
]


class SwipeDetector:
    def __init__(self) -> None:
        base = _mp_python.BaseOptions(model_asset_path=os.path.abspath(_MODEL))
        opts = _mp_vision.HandLandmarkerOptions(
            base_options=base,
            running_mode=_mp_vision.RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.70,
            min_hand_presence_confidence=0.50,
            min_tracking_confidence=0.50,
        )
        self._detector = _mp_vision.HandLandmarker.create_from_options(opts)
        self._history: deque[tuple[float, float]] = deque(maxlen=HISTORY_FRAMES)
        self._last_ts  = 0.0
        self._frame_ts = 0          # monotonic ms counter for Tasks API
        self.hand_visible = False

    def process(self, bgr_frame: np.ndarray) -> tuple[np.ndarray, str | None]:
        """Process one BGR camera frame.

        Returns (annotated_frame, gesture_or_None).
        gesture: "swipe_left" | "swipe_right" | "swipe_up" | "swipe_down"
        """
        rgb = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
        mp_img = _MpImage(image_format=_MpFmt.SRGB, data=rgb)

        self._frame_ts += 50  # ~20 fps; Tasks VIDEO mode needs strictly increasing ms
        result = self._detector.detect_for_video(mp_img, self._frame_ts)

        annotated = bgr_frame.copy()
        gesture   = None
        h, w      = annotated.shape[:2]

        if result.hand_landmarks:
            self.hand_visible = True
            lm = result.hand_landmarks[0]

            # Draw skeleton
            pts = [(int(p.x * w), int(p.y * h)) for p in lm]
            for a, b in _CONNECTIONS:
                cv2.line(annotated, pts[a], pts[b], HUD_COLOR, 1, cv2.LINE_AA)
            for x, y in pts:
                cv2.circle(annotated, (x, y), 3, HUD_COLOR, -1, cv2.LINE_AA)

            wrist = lm[0]
            self._history.append((wrist.x, wrist.y))
            gesture = self._detect_swipe()
            if gesture:
                self._draw_gesture_label(annotated, w, h, gesture)
        else:
            self.hand_visible = False
            self._history.clear()

        self._draw_status(annotated, w, h)
        return annotated, gesture

    # ── Internal ───────────────────────────────────────────────────────────────

    def _detect_swipe(self) -> str | None:
        if len(self._history) < HISTORY_FRAMES:
            return None
        now = time.time()
        if now - self._last_ts < COOLDOWN:
            return None

        pts = list(self._history)
        dx = pts[-1][0] - pts[0][0]
        dy = pts[-1][1] - pts[0][1]

        if abs(dx) < SWIPE_MIN_DIST and abs(dy) < SWIPE_MIN_DIST:
            return None

        self._last_ts = now
        self._history.clear()

        if abs(dx) >= abs(dy):
            return "swipe_right" if dx > 0 else "swipe_left"
        return "swipe_down" if dy > 0 else "swipe_up"

    def _draw_gesture_label(self, frame: np.ndarray, w: int, h: int, gesture: str) -> None:
        label = gesture.replace("_", " ").upper()
        (tw, _), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.putText(frame, label, (w // 2 - tw // 2, h - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, HUD_COLOR, 1, cv2.LINE_AA)

    def _draw_status(self, frame: np.ndarray, w: int, h: int) -> None:
        color = HUD_COLOR if self.hand_visible else HUD_DIM
        label = "HAND  ACTIVE" if self.hand_visible else "NO HAND"
        cv2.circle(frame, (14, h - 14), 4, color, -1, cv2.LINE_AA)
        cv2.putText(frame, label, (24, h - 9),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.32, color, 1, cv2.LINE_AA)
