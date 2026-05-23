"""
Tuya Cloud alert integration.

Flow:
  1. Exchange client_id + secret for an access token (cached until expiry).
  2. POST a device command to set the `fall_alert` boolean DP to true.
  3. A Tuya Smart / Smart Life automation on the device fires a push notification
     when that DP changes to true.

Set up the DP and automation once in the Tuya IoT Platform and Tuya Smart app.
"""

import hashlib
import hmac
import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

TUYA_BASE_URL = os.getenv("TUYA_BASE_URL", "https://openapi.tuyaus.com")
TUYA_CLIENT_ID = os.getenv("TUYA_CLIENT_ID", "")
TUYA_CLIENT_SECRET = os.getenv("TUYA_CLIENT_SECRET", "")
TUYA_DEVICE_ID = os.getenv("TUYA_DEVICE_ID", "")

# The data-point code you define in the Tuya IoT Platform for your device.
# Create a Boolean DP with this code, then make a Smart app automation:
#   trigger: fall_alert == true  →  action: send push notification
FALL_ALERT_DP_CODE = "fall_alert"
# user_ok and needs_help DPs are set directly by the T5AI firmware
# after voice response — the backend does not touch them


class TuyaAlert:
    def __init__(self):
        self._token: str = ""
        self._token_expiry: float = 0.0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send_fall_alert(self, device_id: str = "", extra: dict = None) -> bool:
        device_id = device_id or TUYA_DEVICE_ID
        if not (TUYA_CLIENT_ID and TUYA_CLIENT_SECRET and device_id):
            print("[TuyaAlert] Not configured — skipping alert. Check .env.")
            return False

        try:
            token = self._get_token()
            return self._send_command(token, device_id, FALL_ALERT_DP_CODE, True)
        except Exception as exc:
            print(f"[TuyaAlert] Error: {exc}")
            return False

    def clear_fall_alert(self, device_id: str = "") -> bool:
        """Reset the fall_alert DP back to false after the alert is handled."""
        device_id = device_id or TUYA_DEVICE_ID
        if not (TUYA_CLIENT_ID and TUYA_CLIENT_SECRET and device_id):
            return False
        try:
            token = self._get_token()
            return self._send_command(token, device_id, FALL_ALERT_DP_CODE, False)
        except Exception as exc:
            print(f"[TuyaAlert] clear error: {exc}")
            return False

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry:
            return self._token

        path = "/v1.0/token?grant_type=1"
        t = _ts()
        sign = _sign(TUYA_CLIENT_ID, TUYA_CLIENT_SECRET, t, "", "GET", path)
        headers = _base_headers(TUYA_CLIENT_ID, t, sign)

        resp = requests.get(f"{TUYA_BASE_URL}{path}", headers=headers, timeout=10)
        data = resp.json()

        if not data.get("success"):
            raise RuntimeError(f"Tuya token fetch failed: {data}")

        self._token = data["result"]["access_token"]
        # expire 60 s before actual expiry to avoid edge-case races
        self._token_expiry = time.time() + data["result"]["expire_time"] - 60
        print("[TuyaAlert] Token refreshed.")
        return self._token

    def _send_command(self, token: str, device_id: str, code: str, value) -> bool:
        path = f"/v1.0/iot-03/devices/{device_id}/commands"
        body_dict = {"commands": [{"code": code, "value": value}]}
        body_str = json.dumps(body_dict, separators=(",", ":"))

        t = _ts()
        sign = _sign(TUYA_CLIENT_ID, TUYA_CLIENT_SECRET, t, token, "POST", path, body_str)
        headers = {**_base_headers(TUYA_CLIENT_ID, t, sign, token), "Content-Type": "application/json"}

        resp = requests.post(
            f"{TUYA_BASE_URL}{path}",
            headers=headers,
            data=body_str,
            timeout=10,
        )
        result = resp.json()
        ok = result.get("success", False)
        if ok:
            print(f"[TuyaAlert] Command sent: {code}={value} → device {device_id}")
        else:
            print(f"[TuyaAlert] Command failed: {result}")
        return ok


# ---------------------------------------------------------------------------
# Signing helpers (Tuya OpenAPI v1.0)
# ---------------------------------------------------------------------------

def _ts() -> str:
    """Millisecond timestamp string."""
    return str(int(time.time() * 1000))


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _sign(
    client_id: str,
    secret: str,
    timestamp: str,
    access_token: str,
    method: str,
    path: str,
    body: str = "",
) -> str:
    """
    Tuya HMAC-SHA256 signature.
    https://developer.tuya.com/en/docs/iot/new-singnature?id=Kbw0q34cs2e5g
    """
    content_hash = _sha256_hex(body)
    str_to_sign = "\n".join([method, content_hash, "", path])
    sign_str = client_id + access_token + timestamp + str_to_sign
    return hmac.new(
        secret.encode("utf-8"),
        sign_str.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest().upper()


def _base_headers(client_id: str, timestamp: str, sign: str, token: str = "") -> dict:
    h = {
        "client_id": client_id,
        "sign": sign,
        "t": timestamp,
        "sign_method": "HMAC-SHA256",
    }
    if token:
        h["access_token"] = token
    return h
