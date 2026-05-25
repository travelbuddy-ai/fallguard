"""
Telegram alert — sends fall snapshot + message to a Telegram chat.

Setup:
  1. Message @BotFather on Telegram → /newbot → copy the token
  2. Message your bot once, then run:
       curl https://api.telegram.org/bot<TOKEN>/getUpdates
     Copy the chat_id from the response.
  3. Add to .env:
       TELEGRAM_BOT_TOKEN=your_token
       TELEGRAM_CHAT_ID=your_chat_id
"""

import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_fall_alert(image_bytes: bytes, result: dict) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "[Telegram] Not configured — set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"
        )
        return False

    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    caption = (
        f"🚨 FALL ALERT! 🚨\n"
        f"Halp! I've fallen and I can't get up! 👵\n"
        f"\n"
        f"Time — {dt}\n"
        # f"\n"
        # f"Pose: {result.get('pose_state', 'unknown')}\n"
        # f"Angle: {result.get('body_angle')}°\n"
        # f"Confidence: {result.get('confidence')}\n"
        # f"Device: {result.get('device_id')}"
    )

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto",
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            files={"photo": ("fall.jpg", image_bytes, "image/jpeg")},
            timeout=10,
        )
        ok = resp.json().get("ok", False)
        print(
            f"[Telegram] {'Alert sent' if ok else 'Send failed'}: {resp.text if not ok else ''}"
        )
        return ok
    except Exception as exc:
        print(f"[Telegram] Error: {exc}")
        return False


def send_mock_fall_alert(result: dict) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(
            "[Telegram] Not configured — set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env"
        )
        return False

    dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = (
        f"🚨 FALL DETECTED (mock) — {dt}\n"
        f"Pose: {result.get('pose_state', 'unknown')}\n"
        f"Angle: {result.get('body_angle')}°\n"
        f"Confidence: {result.get('confidence')}\n"
        f"Device: {result.get('device_id')}"
    )

    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text},
            timeout=10,
        )
        ok = resp.json().get("ok", False)
        print(
            f"[Telegram] {'Mock alert sent' if ok else 'Send failed'}: {resp.text if not ok else ''}"
        )
        return ok
    except Exception as exc:
        print(f"[Telegram] Error: {exc}")
        return False
