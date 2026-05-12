"""Vision tool — captures a frame and uses Claude Vision to describe the desk."""

import base64

VISION_URL = "http://localhost:8001"


def look_at_desk(question: str = "What objects can you see on the desk?", agent=None) -> str:
    import anthropic
    import requests as req

    # 1. Try to grab a snapshot from the vision server
    img_b64 = None
    try:
        resp = req.get(f"{VISION_URL}/snapshot", timeout=5)
        if resp.status_code == 200:
            img_b64 = base64.b64encode(resp.content).decode()
    except Exception:
        pass

    # 2. If we have an image, ask Claude Vision
    if img_b64:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": img_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "You are JARVIS, an AI assistant analyzing a live camera feed of "
                            "the user's desk. "
                            f"{question} "
                            "Be concise and specific. Mention notable objects, their state, "
                            "and anything unusual."
                        ),
                    },
                ],
            }],
        )
        return msg.content[0].text

    # 3. Fallback: return raw YOLO detections
    try:
        resp = req.get(f"{VISION_URL}/detections", timeout=3)
        items = resp.json().get("detections", [])
        if not items:
            return "No objects detected. The desk appears empty or nothing is in frame."
        summary = ", ".join(f"{d['label']} ({d['confidence']:.0%})" for d in items)
        return f"Currently visible on desk: {summary}"
    except Exception:
        return (
            "Vision server is not running. "
            "Start it with: uvicorn vision.server:app --port 8001"
        )
