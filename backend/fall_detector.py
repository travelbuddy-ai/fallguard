import io
import time
from collections import deque
from typing import Optional, Tuple

import numpy as np
from PIL import Image

# Lazy-import tensorflow so the module can be imported without TF installed
# (e.g. during IDE analysis). TF is loaded on first FallDetector instantiation.
_tf = None
_hub = None


def _load_tf():
    global _tf, _hub
    if _tf is None:
        import tensorflow as tf
        import tensorflow_hub as hub
        _tf = tf
        _hub = hub


# MoveNet Lightning keypoint indices (COCO format, 17 points)
NOSE = 0
LEFT_SHOULDER, RIGHT_SHOULDER = 5, 6
LEFT_HIP, RIGHT_HIP = 11, 12
LEFT_KNEE, RIGHT_KNEE = 13, 14
LEFT_ANKLE, RIGHT_ANKLE = 15, 16

MOVENET_URL = "https://tfhub.dev/google/movenet/singlepose/lightning/4"
INPUT_SIZE = 192  # Lightning model uses 192x192

# Tuning knobs ---------------------------------------------------------------
# Body angle (degrees from vertical) thresholds
FALLEN_ANGLE = 55      # above this → lying/fallen
STANDING_ANGLE = 40    # below this → upright

MIN_KEYPOINT_CONF = 0.25  # ignore keypoints below this confidence
HISTORY_LEN = 6           # pose history window per device
# ---------------------------------------------------------------------------


class _DeviceState:
    def __init__(self):
        self.history: deque = deque(maxlen=HISTORY_LEN)
        self.last_state: str = "unknown"


class FallDetector:
    def __init__(self):
        _load_tf()
        print("[FallDetector] Loading MoveNet Lightning from TF Hub…")
        model = _hub.load(MOVENET_URL)
        self._infer = model.signatures["serving_default"]
        self._states: dict = {}
        print("[FallDetector] Ready.")

    # ------------------------------------------------------------------
    def analyze(self, image_bytes: bytes, device_id: str) -> dict:
        """
        Run pose estimation on a single JPEG frame.

        Returns a dict with:
          fall_detected (bool), confidence (float), body_angle (float|None),
          pose_state (str: standing | fallen | transitioning | unknown)
        """
        state = self._states.setdefault(device_id, _DeviceState())

        tensor = self._preprocess(image_bytes)
        if tensor is None:
            return self._build_result(device_id, False, 0.0, None, "unknown")

        keypoints = self._run_inference(tensor)
        angle, conf = self._body_angle(keypoints)

        if angle is None:
            state.history.append("unknown")
            return self._build_result(device_id, False, conf, None, "unknown")

        if angle > FALLEN_ANGLE:
            current_state = "fallen"
        elif angle < STANDING_ANGLE:
            current_state = "standing"
        else:
            current_state = "transitioning"

        # Fall = first time we see "fallen" after at least one "standing" frame
        was_standing = "standing" in state.history
        is_new_fall = (
            current_state == "fallen"
            and was_standing
            and state.last_state != "fallen"
        )

        state.history.append(current_state)
        state.last_state = current_state

        return self._build_result(device_id, is_new_fall, conf, angle, current_state)

    def reset_device(self, device_id: str):
        """Clear pose history for a device (call after alert acknowledged)."""
        self._states.pop(device_id, None)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _preprocess(self, image_bytes: bytes) -> Optional[object]:
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img = img.resize((INPUT_SIZE, INPUT_SIZE))
            arr = np.array(img, dtype=np.int32)
            return _tf.constant(arr[np.newaxis, ...])
        except Exception as exc:
            print(f"[FallDetector] Image decode error: {exc}")
            return None

    def _run_inference(self, tensor) -> np.ndarray:
        outputs = self._infer(image=tensor)
        # output_0 shape: (1, 1, 17, 3) → [y, x, confidence] normalised 0-1
        return outputs["output_0"].numpy()[0, 0]

    def _body_angle(self, kp: np.ndarray) -> Tuple[Optional[float], float]:
        """
        Returns (angle_from_vertical_degrees, min_keypoint_confidence).

        The body vector runs from the mid-hip to mid-shoulder.
        Vertical → angle ≈ 0°.  Horizontal → angle ≈ 90°.
        """
        ls, rs = kp[LEFT_SHOULDER], kp[RIGHT_SHOULDER]
        lh, rh = kp[LEFT_HIP], kp[RIGHT_HIP]

        conf = float(min(ls[2], rs[2], lh[2], rh[2]))
        if conf < MIN_KEYPOINT_CONF:
            return None, conf

        mid_shoulder_y = (ls[0] + rs[0]) / 2
        mid_shoulder_x = (ls[1] + rs[1]) / 2
        mid_hip_y = (lh[0] + rh[0]) / 2
        mid_hip_x = (lh[1] + rh[1]) / 2

        # In image coords y increases downward; hip_y > shoulder_y when standing
        dy = mid_hip_y - mid_shoulder_y
        dx = mid_hip_x - mid_shoulder_x
        angle = float(np.degrees(np.arctan2(abs(dx), abs(dy) + 1e-6)))
        return angle, conf

    @staticmethod
    def _build_result(
        device_id: str,
        fall_detected: bool,
        confidence: float,
        body_angle: Optional[float],
        pose_state: str,
    ) -> dict:
        return {
            "device_id": device_id,
            "fall_detected": fall_detected,
            "confidence": round(confidence, 3),
            "body_angle": round(body_angle, 1) if body_angle is not None else None,
            "pose_state": pose_state,
            "timestamp": time.time(),
        }
