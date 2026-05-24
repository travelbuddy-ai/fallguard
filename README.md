English | [简体中文](./README_zh.md)

# FallGuard

FallGuard is a standalone fall detection device built on the Tuya T5AI board + camera module. It detects falls in real time, sends an instant photo alert to caregivers via Telegram, and confirms the situation directly with the person on the ground using voice.

## High-Level Architecture

```
[T5AI + Camera]
│
├── Always running: frame diff motion detector (on-device)
│
└── Motion spike detected?
        │
        ▼
POST /analyze → Python backend (laptop / ngrok)
  Body: raw JPEG    Header: X-Device-ID
        │
        ▼
YOLOv8-pose: is this a fall?
(person horizontal + was previously vertical)
        │
        ├── fall_detected: false ──→ return result, do nothing
        │
        └── fall_detected: true
                │
                ├── 📸 Save snapshot + timestamp to /snapshots
                │
                ├── 🤖 Telegram alert → caregiver's phone
                │      fall photo + timestamp
                │
                └── Return {"fall_detected": true} to T5AI
                        │
                        ▼
              [T5AI] reads response
                        │
                        ├── Sets DP: fall_alert = true
                        │   Smart Life push: "⚠️ Fall detected" (WIP)
                        │
                        └── Screen + speaker:
                            "A fall has been detected. Your emergency contacts have been alerted."
```

## Hardware

| Component       | Details                                                                                                                         |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Tuya T5AI Board | [T5-E1-IPEX development board](https://developer.tuya.com/en/docs/iot-device-dev/T5-E1-IPEX-development-board?id=Ke9xehig1cabj) |
| Camera module   | Connected to T5AI camera interface                                                                                              |

## Repository Structure

```
fallguard/
├── src/                      # T5AI firmware (C)
├── backend/
│   ├── server.py             # FastAPI server
│   ├── fall_detector.py      # YOLOv8-pose fall detection
│   ├── telegram_alert.py     # Telegram snapshot alerts
│   ├── simulate_fall.py      # Test script — send a photo to /analyze
│   ├── test_detector.py      # Unit tests — no device needed
│   └── requirements.txt
├── config/                   # Board-specific build configs
└── CMakeLists.txt
```

## Backend Setup

```bash
cd backend
cp .env.example .env      # add Telegram credentials (optional)
pip install -r requirements.txt
python server.py           # runs on :8080
```

### Endpoints

| Method | Path                 | Description                                                 |
| ------ | -------------------- | ----------------------------------------------------------- |
| POST   | `/analyze`           | Receive JPEG from device, run pose detection, return result |
| POST   | `/mock-fall`         | Always returns fall_detected:true — for firmware testing    |
| GET    | `/health`            | Liveness check                                              |
| GET    | `/falls`             | List recent fall events                                     |
| POST   | `/reset/{device_id}` | Clear pose history for a device                             |

### Environment Variables

| Variable             | Description                                        |
| -------------------- | -------------------------------------------------- |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather (optional)               |
| `TELEGRAM_CHAT_ID`   | Your Telegram chat ID (optional)                   |
| `SNAPSHOTS_DIR`      | Where to save fall images (default: `./snapshots`) |
| `PORT`               | Server port (default: `8080`)                      |

No Tuya credentials needed in the backend — all Tuya Cloud communication is handled directly by the T5AI firmware.

## Tuya Cloud Setup

Define three boolean DPs on the device in [iot.tuya.com](https://iot.tuya.com):

| DP Code      | Trigger                              | Smart Life Automation             |
| ------------ | ------------------------------------ | --------------------------------- |
| `fall_alert` | Fall detected by backend             | "⚠️ Fall detected"                |
| `user_ok`    | User said "Yes, I'm okay"            | "✅ False alarm. Person is okay." |
| `needs_help` | User said "No" or no response in 30s | "⚠️ Person needs help"            |

## Firmware Build

1. `tos.py config choice` — select `T5AI.config`
2. `tos.py build` — outputs `.bin` to `.build/bin/`
3. Flash with `tyutool_gui`
