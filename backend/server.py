"""
FallGuard Backend — FastAPI server

Receives JPEG frames from the T5AI device, runs MoveNet pose estimation,
detects falls, saves snapshots, and fires Tuya Cloud alerts.

Endpoints:
  POST /analyze    — main inference endpoint (called by the device)
  GET  /health     — liveness check
  GET  /falls      — list of saved fall events (last 20)
  POST /reset/{device_id} — clear pose history after alert is handled
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

# ---------------------------------------------------------------------------
app = FastAPI(title="FallGuard Backend", version="1.0.0")

detector = FallDetector()
alert = TuyaAlert()

SNAPSHOTS_DIR = Path(os.getenv("SNAPSHOTS_DIR", "snapshots"))
SNAPSHOTS_DIR.mkdir(exist_ok=True)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Background task helpers
# ---------------------------------------------------------------------------

def _save_snapshot(image_bytes: bytes, device_id: str, result: dict):
    ts = result.get("timestamp", time.time())
    dt_str = datetime.fromtimestamp(ts).strftime("%Y%m%d_%H%M%S")
    safe_id = device_id.replace("/", "_")

    img_path = SNAPSHOTS_DIR / f"fall_{safe_id}_{dt_str}.jpg"
    meta_path = SNAPSHOTS_DIR / f"fall_{safe_id}_{dt_str}.json"

    img_path.write_bytes(image_bytes)

    meta = {
        "device_id": device_id,
        "timestamp": ts,
        "datetime_utc": dt_str,
        "body_angle": result.get("body_angle"),
        "confidence": result.get("confidence"),
        "snapshot": str(img_path),
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"[server] Snapshot saved → {img_path}")


def _handle_fall(image_bytes: bytes, device_id: str, result: dict):
    _save_snapshot(image_bytes, device_id, result)
    sent = alert.send_fall_alert(device_id=device_id, extra=result)
    if sent:
        # Reset DP after a short delay so the next fall can re-trigger the automation
        time.sleep(3)
        alert.clear_fall_alert(device_id=device_id)


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
        "body_angle": float | null,   // degrees from vertical
        "confidence": float,
        "device_id": str,
        "timestamp": float
      }
    """
    image_bytes = await request.body()
    device_id = request.headers.get("X-Device-ID", "t5ai-default")

    if not image_bytes:
        return JSONResponse({"error": "empty body — send raw JPEG"}, status_code=400)

    result = detector.analyze(image_bytes, device_id)

    if result["fall_detected"]:
        print(
            f"[FALL] device={device_id} "
            f"angle={result['body_angle']}° "
            f"conf={result['confidence']}"
        )
        background_tasks.add_task(_handle_fall, image_bytes, device_id, result)

    return JSONResponse(result)


@app.get("/health")
def health():
    return {"status": "ok", "model": "movenet_lightning_v4"}


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
    """Clear pose history for a device (call this after the alert is acknowledged)."""
    detector.reset_device(device_id)
    return {"status": "reset", "device_id": device_id}


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
