import io
import time
from collections import deque
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image

MODEL_NAME = "yolov8n-pose.pt"  # nano — fast, auto-downloads ~6MB on first run

# COCO keypoint indices (YOLOv8 uses same 17-point format)
LEFT_SHOULDER, RIGHT_SHOULDER = 5, 6
LEFT_HIP, RIGHT_HIP = 11, 12

# Tuning knobs
FALLEN_ANGLE = 55       # degrees from vertical → fallen
STANDING_ANGLE = 40     # degrees from vertical → upright
MIN_KEYPOINT_CONF = 0.25
MIN_PERSON_CONF = 0.4   # discard low-confidence detections
HISTORY_LEN = 6

_model = None


def _load_model():
    global _model
    if _model is None:
        from ultralytics import YOLO
        print("[FallDetector] Loading YOLOv8n-pose…")
        _model = YOLO(MODEL_NAME)
        print("[FallDetector] Model ready.")


class _DeviceState:
    def __init__(self):
        self.history: deque = deque(maxlen=HISTORY_LEN)
        self.last_state: str = "unknown"


class FallDetector:
    def __init__(self):
        _load_model()
        self._states: dict = {}
        print("[FallDetector] Ready.")

    # ------------------------------------------------------------------
    def analyze(self, image_bytes: bytes, device_id: str) -> dict:
        state = self._states.setdefault(device_id, _DeviceState())

        img = self._decode(image_bytes)
        if img is None:
            return self._build_result(device_id, False, 0.0, None, "unknown", 0)

        persons = self._run_inference(img)

        if not persons:
            state.history.append("unknown")
            state.last_state = "unknown"
            return self._build_result(device_id, False, 0.0, None, "unknown", 0)

        # Classify every detected person; a fall by ANY person triggers the alert
        current_state = "unknown"
        best_angle: Optional[float] = None
        best_conf = 0.0

        for kps in persons:
            angle, conf = self._body_angle(kps)
            if angle is None:
                continue

            if angle > FALLEN_ANGLE:
                pstate = "fallen"
            elif angle < STANDING_ANGLE:
                pstate = "standing"
            else:
                pstate = "transitioning"

            # Prioritise fallen over other states when multiple people present
            if pstate == "fallen" or current_state == "unknown":
                current_state = pstate
                best_angle = angle
                best_conf = conf

        was_standing = "standing" in state.history
        is_new_fall = (
            current_state == "fallen"
            and was_standing
            and state.last_state != "fallen"
        )

        state.history.append(current_state)
        state.last_state = current_state

        return self._build_result(
            device_id, is_new_fall, best_conf, best_angle, current_state, len(persons)
        )

    def reset_device(self, device_id: str):
        self._states.pop(device_id, None)

    # ------------------------------------------------------------------
    def _decode(self, image_bytes: bytes) -> Optional[np.ndarray]:
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            return np.array(img)
        except Exception as exc:
            print(f"[FallDetector] Image decode error: {exc}")
            return None

    def _run_inference(self, img: np.ndarray) -> List[np.ndarray]:
        """Returns one (17, 3) keypoint array per detected person [x, y, conf]."""
        results = _model(img, verbose=False, conf=MIN_PERSON_CONF)
        persons = []
        for r in results:
            if r.keypoints is None or r.keypoints.data is None:
                continue
            kps = r.keypoints.data.cpu().numpy()  # (N, 17, 3)
            for i in range(kps.shape[0]): 
                persons.append(kps[i])
        return persons

    def _body_angle(self, kp: np.ndarray) -> Tuple[Optional[float], float]:
        """
        YOLOv8 keypoint format: [x, y, conf] in pixel coords.
        Returns (angle_from_vertical_degrees, min_keypoint_confidence).
        Vertical body → ~0°.  Horizontal (fallen) → ~90°.
        """
        ls, rs = kp[LEFT_SHOULDER], kp[RIGHT_SHOULDER]
        lh, rh = kp[LEFT_HIP], kp[RIGHT_HIP]

        conf = float(min(ls[2], rs[2], lh[2], rh[2]))
        if conf < MIN_KEYPOINT_CONF:
            return None, conf

        mid_shoulder = np.array([(ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2])
        mid_hip = np.array([(lh[0] + rh[0]) / 2, (lh[1] + rh[1]) / 2])

        # y increases downward; hip_y > shoulder_y when standing
        dy = mid_hip[1] - mid_shoulder[1]
        dx = mid_hip[0] - mid_shoulder[0]
        angle = float(np.degrees(np.arctan2(abs(dx), abs(dy) + 1e-6)))
        return angle, conf

    @staticmethod
    def _build_result(
        device_id: str,
        fall_detected: bool,
        confidence: float,
        body_angle: Optional[float],
        pose_state: str,
        persons_detected: int,
    ) -> dict:
        return {
            "device_id": device_id,
            "fall_detected": fall_detected,
            "confidence": round(confidence, 3),
            "body_angle": round(body_angle, 1) if body_angle is not None else None,
            "pose_state": pose_state,
            "persons_detected": persons_detected,
            "timestamp": time.time(),
        }
