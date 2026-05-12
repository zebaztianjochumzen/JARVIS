"""Free dictation mode — hold a hotkey anywhere on the system, speak, release, JARVIS pastes.

Flow:
  1. pynput GlobalHotKey listens for DICTATION_HOTKEY (default: <ctrl>+<shift>+space)
  2. On press  → start sounddevice recording into a BytesIO buffer
  3. On release → stop recording, POST audio to /api/transcribe, paste result

Requires: pynput, sounddevice, pyperclip, pyautogui, requests, scipy
Run as a daemon thread from main.py or launch standalone.
"""

import io
import os
import queue
import threading
import time

HOTKEY      = os.environ.get("DICTATION_HOTKEY", "<ctrl>+<shift>+space")
API_URL     = os.environ.get("DICTATION_API_URL", "http://localhost:8000/api/transcribe")
SAMPLE_RATE = 16_000
CHANNELS    = 1
MAX_SECS    = 30


_recording   = False
_audio_q:    queue.Queue = queue.Queue()
_rec_thread: threading.Thread | None = None
_started     = False


def start() -> None:
    """Start the global hotkey listener in a daemon thread."""
    global _started
    if _started:
        return
    _started = True

    t = threading.Thread(target=_hotkey_loop, daemon=True, name="dictation-hotkey")
    t.start()
    print("[Dictation] Hotkey listener started — hold", HOTKEY, "to dictate.", flush=True)


# ── Hotkey loop ───────────────────────────────────────────────────────────────

def _hotkey_loop() -> None:
    try:
        from pynput import keyboard
    except ImportError:
        print("[Dictation] pynput not installed — dictation disabled.", flush=True)
        return

    def on_press():
        global _recording
        if not _recording:
            _recording = True
            _start_recording()

    def on_release():
        global _recording
        if _recording:
            _recording = False
            _stop_and_transcribe()

    try:
        with keyboard.GlobalHotKeys({HOTKEY: on_press}) as h:
            # Also bind release — GlobalHotKeys doesn't expose release directly,
            # so we listen on a suppressed listener in a separate thread.
            _start_release_listener(on_release)
            h.join()
    except Exception as exc:
        print(f"[Dictation] Hotkey error: {exc}", flush=True)


def _start_release_listener(on_release_cb) -> None:
    """Monitor key-up for all modifier+space combos and fire on_release_cb."""
    try:
        from pynput import keyboard

        # We consider "released" when the space key is lifted (simplified heuristic)
        def on_key_release(key):
            try:
                if key == keyboard.Key.space:
                    on_release_cb()
            except Exception:
                pass

        t = keyboard.Listener(on_release=on_key_release)
        t.daemon = True
        t.start()
    except Exception:
        pass


# ── Recording ─────────────────────────────────────────────────────────────────

def _start_recording() -> None:
    global _rec_thread
    # Clear any stale frames
    while not _audio_q.empty():
        try:
            _audio_q.get_nowait()
        except queue.Empty:
            break

    _rec_thread = threading.Thread(target=_record_loop, daemon=True, name="dictation-rec")
    _rec_thread.start()
    print("[Dictation] Recording…", flush=True)


def _record_loop() -> None:
    try:
        import sounddevice as sd
        import numpy as np
    except ImportError:
        print("[Dictation] sounddevice/numpy not installed.", flush=True)
        return

    frames = []
    start  = time.time()

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS,
                        dtype="int16", callback=callback):
        while _recording and (time.time() - start) < MAX_SECS:
            time.sleep(0.05)

    audio = np.concatenate(frames, axis=0) if frames else None
    _audio_q.put(audio)


def _stop_and_transcribe() -> None:
    threading.Thread(target=_transcribe_worker, daemon=True, name="dictation-tx").start()


def _transcribe_worker() -> None:
    try:
        import numpy as np
        audio = _audio_q.get(timeout=5)
    except Exception:
        print("[Dictation] No audio captured.", flush=True)
        return

    if audio is None or len(audio) < SAMPLE_RATE * 0.3:
        return  # too short

    wav_bytes = _to_wav_bytes(audio)
    if not wav_bytes:
        return

    try:
        import requests
        resp = requests.post(
            API_URL,
            files={"audio": ("dictation.wav", wav_bytes, "audio/wav")},
            data={"format": "wav"},
            timeout=30,
        )
        data = resp.json()
    except Exception as exc:
        print(f"[Dictation] Transcription request failed: {exc}", flush=True)
        return

    text = data.get("transcript", "").strip()
    if not text:
        print("[Dictation] Empty transcript.", flush=True)
        return

    print(f"[Dictation] Transcript: {text}", flush=True)
    _paste_text(text)


def _to_wav_bytes(audio) -> bytes | None:
    """Convert int16 numpy array to WAV bytes (no scipy dependency)."""
    try:
        import struct
        import numpy as np

        if audio.ndim > 1:
            audio = audio[:, 0]

        raw = audio.astype(np.int16).tobytes()
        num_samples    = len(audio)
        num_channels   = 1
        bits_per_sample = 16
        byte_rate      = SAMPLE_RATE * num_channels * bits_per_sample // 8
        block_align    = num_channels * bits_per_sample // 8
        data_chunk_size = num_samples * block_align
        riff_chunk_size = 36 + data_chunk_size

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", riff_chunk_size, b"WAVE",
            b"fmt ", 16, 1,           # PCM
            num_channels, SAMPLE_RATE,
            byte_rate, block_align, bits_per_sample,
            b"data", data_chunk_size,
        )
        return header + raw
    except Exception as exc:
        print(f"[Dictation] WAV conversion failed: {exc}", flush=True)
        return None


def _paste_text(text: str) -> None:
    """Copy text to clipboard then simulate Ctrl+V to paste."""
    try:
        import pyperclip
        pyperclip.copy(text)
    except Exception as exc:
        print(f"[Dictation] Clipboard write failed: {exc}", flush=True)
        return

    time.sleep(0.1)

    try:
        import pyautogui
        pyautogui.hotkey("ctrl", "v")
    except Exception as exc:
        print(f"[Dictation] Paste failed: {exc}", flush=True)
