English | [简体中文](./README_zh.md)

# FallGuard

FallGuard is a standalone fall detection device built on the Tuya T5AI board + camera module. It detects falls in real time, alerts caregivers via phone, and confirms the situation directly with the person on the ground.

## High-Level Architecture

```
[T5AI + Camera]
│
├── Always running: frame diff motion detector (on-device)
│
└── Motion spike detected?
        │
        ▼
Send frame to backend (laptop / ngrok / Render)
        │
        ▼
Python server: YOLOv8-pose check
"Is this a fall pose? Person horizontal + previously vertical?"
        │
        ▼
Fall confirmed → POST fall_alert DP to Tuya Cloud
              → Smart Life push: "⚠️ Fall detected"
              → store snapshot with timestamp
        │
        ▼
[T5AI] screen lights up + speaker plays:
"Are you okay? Please say Yes or No"
        │
        ├── Hears "YES"
        │       ↓
        │   T5AI sets DP: user_ok = true
        │   Smart Life push: "✅ False alarm. Person is okay."
        │
        ├── Hears "NO"
        │       ↓
        │   T5AI sets DP: needs_help = true
        │   Smart Life push: "⚠️ Person needs help"
        │   Repeat every 60s until caregiver acknowledges
        │
        └── No response in 30s
                ↓
            T5AI sets DP: needs_help = true
            Smart Life push: "⚠️ No response — person may be unconscious"
            Repeat every 60s until caregiver acknowledges
```

## Hardware

| Component | Details |
| --- | --- |
| Tuya T5AI Board | [T5-E1-IPEX development board](https://developer.tuya.com/en/docs/iot-device-dev/T5-E1-IPEX-development-board?id=Ke9xehig1cabj) |
| Camera module | Connected to T5AI camera interface |

## Repository Structure

```
fallguard/
├── src/                  # T5AI firmware (C)
├── backend/              # Python inference server
│   ├── server.py         # FastAPI server
│   ├── fall_detector.py  # YOLOv8-pose fall detection
│   ├── tuya_alert.py     # Tuya Cloud alerts
│   └── requirements.txt
├── config/               # Board-specific build configs
└── CMakeLists.txt
```

## Backend Setup

```bash
cd backend
cp .env.example .env      # fill in Tuya credentials
pip install -r requirements.txt
python server.py           # runs on :8080
```

### Endpoints

| Method | Path | Description |
| --- | --- | --- |
| POST | `/analyze` | Receive JPEG frame from device, run pose detection |
| GET | `/health` | Liveness check |
| GET | `/falls` | List recent fall events |
| POST | `/reset/{device_id}` | Clear pose history for a device |

### Environment Variables

| Variable | Description |
| --- | --- |
| `TUYA_BASE_URL` | Tuya API region (`openapi.tuyaus.com` for US) |
| `TUYA_CLIENT_ID` | Access ID from iot.tuya.com project |
| `TUYA_CLIENT_SECRET` | Access Secret from iot.tuya.com project |
| `TUYA_DEVICE_ID` | Device ID of the T5AI board |

## Firmware Build

1. `tos.py config choice` — select `T5AI.config`
2. `tos.py build` — outputs `.bin` to `.build/bin/`
3. Flash with `tyutool_gui`

## Tuya Cloud Setup

1. Create a project at [iot.tuya.com](https://iot.tuya.com)
2. Define three boolean DPs on the device:
   - `fall_alert` — triggered when a fall is detected
   - `user_ok` — triggered when user responds "Yes, I'm okay"
   - `needs_help` — triggered when user responds "No, I need help"
3. Create automations in Smart Life app for each DP → push notification
