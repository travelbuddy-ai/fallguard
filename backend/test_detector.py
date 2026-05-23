"""
Test fall_detector.py logic with synthetic keypoints — no device, no images needed.

Monkeypatches _run_inference so we control exactly what pose the model "sees".
Tests the full state machine: standing frames → fallen frame → fall_detected=True.

Run with:
  python test_detector.py
"""

import sys
import types
import numpy as np

# ---------------------------------------------------------------------------
# Synthetic keypoint helpers
# COCO format for YOLOv8: (17, 3) array of [x, y, confidence] in pixel coords
# We only need shoulders (5,6) and hips (11,12) for the angle calculation.
# ---------------------------------------------------------------------------

def _make_kps(
    shoulder_y: float, hip_y: float,
    shoulder_x: float = 320.0, hip_x: float = 320.0,
    conf: float = 0.9,
) -> np.ndarray:
    """Build a (17,3) keypoint array with the key joints set."""
    kps = np.zeros((17, 3), dtype=np.float32)
    kps[5]  = [shoulder_x - 40, shoulder_y, conf]  # left shoulder
    kps[6]  = [shoulder_x + 40, shoulder_y, conf]  # right shoulder
    kps[11] = [hip_x - 40,      hip_y,      conf]  # left hip
    kps[12] = [hip_x + 40,      hip_y,      conf]  # right hip
    return kps


# Standing: shoulders at y=150, hips at y=320 → body mostly vertical (~14°)
STANDING_KPS = _make_kps(shoulder_y=150, hip_y=320)

# Fallen: shoulders and hips at same y, far apart horizontally → ~90°
FALLEN_KPS   = _make_kps(shoulder_y=240, hip_y=260, shoulder_x=160, hip_x=480)

# Low confidence: should be ignored
LOW_CONF_KPS = _make_kps(shoulder_y=150, hip_y=320, conf=0.1)


# ---------------------------------------------------------------------------
# Patch ultralytics so FallDetector can be imported without the model download
# ---------------------------------------------------------------------------

def _patch_ultralytics():
    fake_kp = types.SimpleNamespace(data=None)
    fake_result = types.SimpleNamespace(keypoints=fake_kp)
    fake_yolo = types.SimpleNamespace()
    fake_yolo_class = lambda name: fake_yolo

    fake_module = types.ModuleType("ultralytics")
    fake_module.YOLO = fake_yolo_class
    sys.modules["ultralytics"] = fake_module


_patch_ultralytics()

from fall_detector import FallDetector  # noqa: E402 (import after patch)


# ---------------------------------------------------------------------------
# Override _run_inference to return our synthetic keypoints
# ---------------------------------------------------------------------------

def run_sequence(detector: FallDetector, keypoint_frames: list, device_id: str):
    results = []
    for kps in keypoint_frames:
        # Patch inference for this frame
        if kps is None:
            detector._run_inference = lambda img: []
        else:
            _kps = kps  # capture for closure
            detector._run_inference = lambda img, k=_kps: [k]

        # _decode is also patched — just return a dummy array
        detector._decode = lambda b: np.zeros((480, 640, 3), dtype=np.uint8)

        result = detector.analyze(b"dummy", device_id)
        results.append(result)
    return results


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

PASS = "\033[92m PASS\033[0m"
FAIL = "\033[91m FAIL\033[0m"


def check(label: str, condition: bool):
    print(f"{'✓' if condition else '✗'}{PASS if condition else FAIL}  {label}")
    return condition


def test_standing_then_fall():
    print("\n── Test 1: standing × 3 → fallen → fall_detected ──")
    d = FallDetector.__new__(FallDetector)
    d._states = {}

    frames = [STANDING_KPS, STANDING_KPS, STANDING_KPS, FALLEN_KPS]
    results = run_sequence(d, frames, "test-device")

    r_stand = results[0]
    r_fall  = results[3]

    ok = True
    ok &= check("standing frame → pose_state=standing",   r_stand["pose_state"] == "standing")
    ok &= check("standing frame → fall_detected=False",   r_stand["fall_detected"] == False)
    ok &= check("fallen frame  → pose_state=fallen",      r_fall["pose_state"] == "fallen")
    ok &= check("fallen frame  → fall_detected=True",     r_fall["fall_detected"] == True)
    ok &= check("persons_detected=1",                     r_fall["persons_detected"] == 1)
    return ok


def test_fall_without_prior_standing():
    print("\n── Test 2: fallen with no prior standing → no alert ──")
    d = FallDetector.__new__(FallDetector)
    d._states = {}

    frames = [FALLEN_KPS, FALLEN_KPS]
    results = run_sequence(d, frames, "test-device-2")

    ok = True
    ok &= check("fallen with no history → fall_detected=False", results[0]["fall_detected"] == False)
    return ok


def test_no_double_alert():
    print("\n── Test 3: fall not re-triggered while still fallen ──")
    d = FallDetector.__new__(FallDetector)
    d._states = {}

    frames = [STANDING_KPS, STANDING_KPS, FALLEN_KPS, FALLEN_KPS, FALLEN_KPS]
    results = run_sequence(d, frames, "test-device-3")

    ok = True
    ok &= check("first fallen frame → fall_detected=True",  results[2]["fall_detected"] == True)
    ok &= check("second fallen frame → fall_detected=False", results[3]["fall_detected"] == False)
    ok &= check("third fallen frame  → fall_detected=False", results[4]["fall_detected"] == False)
    return ok


def test_low_confidence_ignored():
    print("\n── Test 4: low-confidence keypoints ignored ──")
    d = FallDetector.__new__(FallDetector)
    d._states = {}

    frames = [STANDING_KPS, STANDING_KPS, LOW_CONF_KPS]
    results = run_sequence(d, frames, "test-device-4")

    ok = True
    ok &= check("low-conf frame → pose_state=unknown",      results[2]["pose_state"] == "unknown")
    ok &= check("low-conf frame → fall_detected=False",     results[2]["fall_detected"] == False)
    return ok


def test_no_person_detected():
    print("\n── Test 5: empty frame (no person) → unknown ──")
    d = FallDetector.__new__(FallDetector)
    d._states = {}

    frames = [STANDING_KPS, None]  # None → _run_inference returns []
    results = run_sequence(d, frames, "test-device-5")

    ok = True
    ok &= check("empty frame → pose_state=unknown",     results[1]["pose_state"] == "unknown")
    ok &= check("empty frame → persons_detected=0",     results[1]["persons_detected"] == 0)
    return ok


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("FallDetector unit tests")
    print("=" * 40)

    results = [
        test_standing_then_fall(),
        test_fall_without_prior_standing(),
        test_no_double_alert(),
        test_low_confidence_ignored(),
        test_no_person_detected(),
    ]

    total  = len(results)
    passed = sum(results)
    print(f"\n{'=' * 40}")
    print(f"Results: {passed}/{total} passed")

    sys.exit(0 if passed == total else 1)
