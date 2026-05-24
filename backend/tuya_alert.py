"""
Tuya Cloud alert integration — used by /mock-fall for testing only.

The production fall response (user_ok / needs_help) is handled directly
by the T5AI firmware via tuya_iot_dp_obj_report().
"""

import hashlib
import hmac
import json
import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

TUYA_BASE_URL    = os.getenv("TUYA_BASE_URL", "https://openapi.tuyaus.com")
TUYA_CLIENT_ID   = os.getenv("TUYA_CLIENT_ID", "")
TUYA_CLIENT_SECRET = os.getenv("TUYA_CLIENT_SECRET", "")
TUYA_DEVICE_ID   = os.getenv("TUYA_DEVICE_ID", "")

FALL_ALERT_DP_CODE = "fall_alert"


class TuyaAlert:
    def __init__(self):
        self._token: str = ""
        self._token_expiry: float = 0.0

    def send_fall_alert(self, device_id: str = "", extra: dict = None) -> bool:
        device_id = device_id or TUYA_DEVICE_ID
        if not (TUYA_CLIENT_ID and TUYA_CLIENT_SECRET and device_id):
            print("[TuyaAlert] Not configured — skipping alert. Check .env.")
            return False
        try:
            token = self._get_token()
            sent = self._send_command(token, device_id, FALL_ALERT_DP_CODE, True)
            if sent:
                time.sleep(3)
                self._send_command(token, device_id, FALL_ALERT_DP_CODE, False)
            return sent
        except Exception as exc:
            print(f"[TuyaAlert] Error: {exc}")
            return False

    def _get_token(self) -> str:
        if self._token and time.time() < self._token_expiry:
            return self._token
        path = "/v1.0/token?grant_type=1"
        t = _ts()
        sign = _sign(TUYA_CLIENT_ID, TUYA_CLIENT_SECRET, t, "", "GET", path)
        resp = requests.get(f"{TUYA_BASE_URL}{path}", headers=_base_headers(TUYA_CLIENT_ID, t, sign), timeout=10)
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Tuya token fetch failed: {data}")
        self._token = data["result"]["access_token"]
        self._token_expiry = time.time() + data["result"]["expire_time"] - 60
        print("[TuyaAlert] Token refreshed.")
        return self._token

    def _send_command(self, token: str, device_id: str, code: str, value) -> bool:
        path = f"/v1.0/iot-03/devices/{device_id}/commands"
        body_str = json.dumps({"commands": [{"code": code, "value": value}]}, separators=(",", ":"))
        t = _ts()
        sign = _sign(TUYA_CLIENT_ID, TUYA_CLIENT_SECRET, t, token, "POST", path, body_str)
        headers = {**_base_headers(TUYA_CLIENT_ID, t, sign, token), "Content-Type": "application/json"}
        resp = requests.post(f"{TUYA_BASE_URL}{path}", headers=headers, data=body_str, timeout=10)
        result = resp.json()
        ok = result.get("success", False)
        print(f"[TuyaAlert] {'Command sent' if ok else 'Command failed'}: {code}={value} → {device_id}")
        return ok


def _ts() -> str:
    return str(int(time.time() * 1000))

def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()

def _sign(client_id, secret, timestamp, access_token, method, path, body="") -> str:
    str_to_sign = "\n".join([method, _sha256_hex(body), "", path])
    sign_str = client_id + access_token + timestamp + str_to_sign
    return hmac.new(secret.encode(), sign_str.encode(), digestmod=hashlib.sha256).hexdigest().upper()

def _base_headers(client_id, timestamp, sign, token="") -> dict:
    h = {"client_id": client_id, "sign": sign, "t": timestamp, "sign_method": "HMAC-SHA256"}
    if token:
        h["access_token"] = token
    return h
