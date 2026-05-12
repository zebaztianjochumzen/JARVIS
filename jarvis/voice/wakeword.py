"""Backend wake word detection using openwakeword.

Runs in a daemon thread, continuously listening to the default microphone.
Any connected WebSocket client (registered via add_listener / remove_listener)
receives a {"type": "wake_word_detected"} dict when "Hey JARVIS" is heard.

Degrades gracefully: if openwakeword or sounddevice are not installed, the
thread exits cleanly and the browser-based fallback in VoiceControl.jsx
continues to work.

Environment:
  WAKEWORD_THRESHOLD  — detection confidence threshold (default: 0.5)
  WAKEWORD_MODEL      — model name to use (default: hey_jarvis_v0.1)
"""

import os
import queue
import threading
from typing import List

_listeners: List[queue.Queue] = []
_lock     = threading.Lock()
_started  = False


def add_listener(q: queue.Queue) -> None:
    with _lock:
        if q not in _listeners:
            _listeners.append(q)


def remove_listener(q: queue.Queue) -> None:
    with _lock:
        if q in _listeners:
            _listeners.remove(q)


def _broadcast() -> None:
    with _lock:
        targets = list(_listeners)
    for q in targets:
        try:
            q.put_nowait({"type": "wake_word_detected"})
        except Exception:
            pass


def start() -> None:
    """Start the background listener thread (idempotent)."""
    global _started
    if _started:
        return
    _started = True
    t = threading.Thread(target=_listen_loop, daemon=True, name="wakeword-listener")
    t.start()


def _listen_loop() -> None:
    threshold  = float(os.environ.get("WAKEWORD_THRESHOLD", "0.5"))
    model_name = os.environ.get("WAKEWORD_MODEL", "hey_jarvis_v0.1")

    try:
        import numpy as np
        import sounddevice as sd
        from openwakeword.model import Model

        oww = Model(wakeword_models=[model_name], inference_framework="onnx")
        print(f"[WakeWord] openwakeword loaded — listening for '{model_name}' (threshold={threshold})", flush=True)

        SAMPLE_RATE = 16_000
        CHUNK       = 1_280   # ~80 ms at 16 kHz — recommended by openwakeword

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16",
            blocksize=CHUNK,
        ) as stream:
            while True:
                audio_chunk, _ = stream.read(CHUNK)
                flat = audio_chunk.flatten()

                prediction = oww.predict(flat)
                scores     = prediction.get(model_name, [0])
                score      = float(scores[-1]) if hasattr(scores, "__len__") else float(scores)

                if score >= threshold:
                    print(f"[WakeWord] Detected! score={score:.3f}", flush=True)
                    _broadcast()
                    # Debounce: discard ~1.5 s of audio so we don't double-trigger
                    debounce_chunks = int(SAMPLE_RATE * 1.5 / CHUNK)
                    for _ in range(debounce_chunks):
                        try:
                            stream.read(CHUNK)
                        except Exception:
                            break

    except ImportError as e:
        print(f"[WakeWord] Disabled — missing dependency: {e}. Browser wake-word fallback is active.", flush=True)
    except Exception as e:
        print(f"[WakeWord] Disabled — {e}. Browser wake-word fallback is active.", flush=True)
