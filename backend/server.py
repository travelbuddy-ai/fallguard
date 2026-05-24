"""
FallGuard Backend — FastAPI server

Receives JPEG frames from the T5AI device, runs YOLOv8-pose fall detection,
and returns the result. The device handles all Tuya Cloud communication.

Endpoints:
  POST /analyze            — main inference endpoint (called by the device)
  GET  /health             — liveness check
  GET  /falls              — list of saved fall events (last 20)
  POST /reset/{device_id}  — clear pose history after alert is handled
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import BackgroundTasks, Request
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from fall_detector import FallDetector
from tuya_alert import TuyaAlert
from telegram_alert import send_fall_alert as telegram_send, send_mock_fall_alert as telegram_mock

# ---------------------------------------------------------------------------
app = FastAPI(title="FallGuard Backend", version="1.0.0")

detector = FallDetector()
alert = TuyaAlert()

SNAPSHOTS_DIR = Path(os.getenv("SNAPSHOTS_DIR", "snapshots"))
SNAPSHOTS_DIR.mkdir(exist_ok=True)
# ---------------------------------------------------------------------------


def _save_snapshot(image_bytes: bytes, device_id: str, result: dict):
    ts = result.get("timestamp", time.time())
    dt_str = datetime.fromtimestamp(ts).strftime("%Y%m%d_%H%M%S")
    safe_id = device_id.replace("/", "_")

    img_path = SNAPSHOTS_DIR / f"fall_{safe_id}_{dt_str}.jpg"
    meta_path = SNAPSHOTS_DIR / f"fall_{safe_id}_{dt_str}.json"

    img_path.write_bytes(image_bytes)
    meta_path.write_text(json.dumps({
        "device_id": device_id,
        "timestamp": ts,
        "datetime_utc": dt_str,
        "body_angle": result.get("body_angle"),
        "confidence": result.get("confidence"),
        "snapshot": str(img_path),
    }, indent=2))
    print(f"[server] Snapshot saved → {img_path}")


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.post("/analyze")
async def analyze_frame(request: Request, background_tasks: BackgroundTasks):
    """
    Called by the T5AI device when motion is detected.

    Request:
      Header  X-Device-ID: <device_id>    (e.g. "t5ai-living-room")
      Body    raw JPEG bytes

    Response JSON:
      {
        "fall_detected": bool,
        "pose_state": "standing" | "fallen" | "transitioning" | "unknown",
        "body_angle": float | null,
        "confidence": float,
        "persons_detected": int,
        "device_id": str,
        "timestamp": float
      }

    If fall_detected is true, the device should:
      1. Set fall_alert DP on Tuya Cloud
      2. Trigger voice prompt: "Are you okay?"
      3. Set user_ok or needs_help DP based on response
    """
    image_bytes = await request.body()
    device_id = request.headers.get("X-Device-ID", "t5ai-default")

    if not image_bytes:
        return JSONResponse({"error": "empty body — send raw JPEG"}, status_code=400)

    result = detector.analyze(image_bytes, device_id)

    print(f"[analyze] {json.dumps(result)}")

    if result["fall_detected"]:
        print(
            f"[FALL] device={device_id} "
            f"angle={result['body_angle']}° "
            f"conf={result['confidence']}"
        )
        background_tasks.add_task(_save_snapshot, image_bytes, device_id, result)
        background_tasks.add_task(telegram_send, image_bytes, result)

    return JSONResponse(result)


@app.post("/mock-fall")
async def mock_fall(request: Request, background_tasks: BackgroundTasks):
    """
    Testing endpoint — returns fall_detected: true AND fires the Tuya Cloud
    fall_alert DP so the device receives it via MQTT.
    """
    device_id = request.headers.get("X-Device-ID", "")
    result = {
        "device_id": device_id or os.getenv("TUYA_DEVICE_ID", "unknown"),
        "fall_detected": True,
        "pose_state": "fallen",
        "body_angle": 78.3,
        "confidence": 0.91,
        "persons_detected": 1,
        "timestamp": time.time(),
    }
    background_tasks.add_task(alert.send_fall_alert, device_id)
    background_tasks.add_task(telegram_mock, result)
    return JSONResponse(result)


@app.get("/health")
def health():
    return {"status": "ok", "model": "yolov8n-pose"}


@app.get("/falls")
def list_falls():
    """Return the 20 most recent fall events."""
    events = []
    for path in sorted(SNAPSHOTS_DIR.glob("fall_*.json"), reverse=True)[:20]:
        try:
            events.append(json.loads(path.read_text()))
        except Exception:
            pass
    return {"count": len(events), "falls": events}


@app.post("/reset/{device_id}")
def reset_device(device_id: str):
    """Clear pose history for a device."""
    detector.reset_device(device_id)
    return {"status": "reset", "device_id": device_id}


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
