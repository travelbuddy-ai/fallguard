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


# Bounding boxes [x1, y1, x2, y2]
STANDING_BOX = np.array([260.0, 50.0,  380.0, 400.0])  # tall box  (w=120, h=350)
FALLEN_BOX   = np.array([100.0, 200.0, 540.0, 300.0])  # wide box  (w=440, h=100)

# Standing: shoulders at y=150, hips at y=320 → body mostly vertical (~14°)
STANDING_KPS = _make_kps(shoulder_y=150, hip_y=320)

# Fallen: shoulders and hips at same y, far apart horizontally → ~90°
FALLEN_KPS   = _make_kps(shoulder_y=240, hip_y=260, shoulder_x=160, hip_x=480)

# Backward fall: low-conf keypoints but wide bounding box
BACKWARD_FALL_KPS = _make_kps(shoulder_y=150, hip_y=320, conf=0.1)  # bad keypoints

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

def run_sequence(detector: FallDetector, frames: list, device_id: str):
    """frames: list of (kps, box) tuples, or None for empty frame."""
    results = []
    for frame in frames:
        if frame is None:
            detector._run_inference = lambda img: []
        else:
            _frame = frame
            detector._run_inference = lambda img, f=_frame: [f]

        detector._decode = lambda b: np.zeros((480, 640, 3), dtype=np.uint8)
        results.append(detector.analyze(b"dummy", device_id))
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

    frames = [
        (STANDING_KPS, STANDING_BOX),
        (STANDING_KPS, STANDING_BOX),
        (STANDING_KPS, STANDING_BOX),
        (FALLEN_KPS,   FALLEN_BOX),
    ]
    results = run_sequence(d, frames, "test-device")

    ok = True
    ok &= check("standing frame → pose_state=standing",  results[0]["pose_state"] == "standing")
    ok &= check("standing frame → fall_detected=False",  results[0]["fall_detected"] == False)
    ok &= check("fallen frame  → pose_state=fallen",     results[3]["pose_state"] == "fallen")
    ok &= check("fallen frame  → fall_detected=True",    results[3]["fall_detected"] == True)
    ok &= check("persons_detected=1",                    results[3]["persons_detected"] == 1)
    return ok


def test_fall_without_prior_standing():
    print("\n── Test 2: fallen with no prior standing → no alert ──")
    d = FallDetector.__new__(FallDetector)
    d._states = {}

    frames = [(FALLEN_KPS, FALLEN_BOX), (FALLEN_KPS, FALLEN_BOX)]
    results = run_sequence(d, frames, "test-device-2")

    ok = True
    ok &= check("fallen with no history → fall_detected=False", results[0]["fall_detected"] == False)
    return ok


def test_no_double_alert():
    print("\n── Test 3: fall not re-triggered while still fallen ──")
    d = FallDetector.__new__(FallDetector)
    d._states = {}

    frames = [
        (STANDING_KPS, STANDING_BOX),
        (STANDING_KPS, STANDING_BOX),
        (FALLEN_KPS,   FALLEN_BOX),
        (FALLEN_KPS,   FALLEN_BOX),
        (FALLEN_KPS,   FALLEN_BOX),
    ]
    results = run_sequence(d, frames, "test-device-3")

    ok = True
    ok &= check("first fallen frame  → fall_detected=True",  results[2]["fall_detected"] == True)
    ok &= check("second fallen frame → fall_detected=False", results[3]["fall_detected"] == False)
    ok &= check("third fallen frame  → fall_detected=False", results[4]["fall_detected"] == False)
    return ok


def test_low_confidence_ignored():
    print("\n── Test 4: low-confidence keypoints + tall box → not fallen ──")
    d = FallDetector.__new__(FallDetector)
    d._states = {}

    frames = [
        (STANDING_KPS, STANDING_BOX),
        (STANDING_KPS, STANDING_BOX),
        (LOW_CONF_KPS, STANDING_BOX),  # bad keypoints but tall box → not fallen
    ]
    results = run_sequence(d, frames, "test-device-4")

    ok = True
    ok &= check("low-conf + tall box → pose_state != fallen",  results[2]["pose_state"] != "fallen")
    ok &= check("low-conf + tall box → fall_detected=False",   results[2]["fall_detected"] == False)
    return ok


def test_no_person_detected():
    print("\n── Test 5: empty frame (no person) → unknown ──")
    d = FallDetector.__new__(FallDetector)
    d._states = {}

    frames = [(STANDING_KPS, STANDING_BOX), None]
    results = run_sequence(d, frames, "test-device-5")

    ok = True
    ok &= check("empty frame → pose_state=unknown",  results[1]["pose_state"] == "unknown")
    ok &= check("empty frame → persons_detected=0",  results[1]["persons_detected"] == 0)
    return ok


def test_backward_fall():
    print("\n── Test 6: backward fall — bad keypoints but wide bbox → fall_detected ──")
    d = FallDetector.__new__(FallDetector)
    d._states = {}

    frames = [
        (STANDING_KPS,     STANDING_BOX),
        (STANDING_KPS,     STANDING_BOX),
        (BACKWARD_FALL_KPS, FALLEN_BOX),   # low-conf kps but wide box
    ]
    results = run_sequence(d, frames, "test-device-6")

    ok = True
    ok &= check("backward fall → pose_state=fallen",    results[2]["pose_state"] == "fallen")
    ok &= check("backward fall → fall_detected=True",   results[2]["fall_detected"] == True)
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
        test_backward_fall(),
    ]

    total  = len(results)
    passed = sum(results)
    print(f"\n{'=' * 40}")
    print(f"Results: {passed}/{total} passed")

    sys.exit(0 if passed == total else 1)
