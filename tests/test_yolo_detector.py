from pathlib import Path
import importlib.util
import subprocess
import sys
import tempfile
import unittest

from satellite_edge_node.detectors import build_detector_with_fallback
from satellite_edge_node.yolo_detector import (
    DETECTOR_VERSION,
    YoloModelUnavailable,
    normalize_yolo_results,
)


class FakeTensor:
    def __init__(self, value):
        self.value = value

    def detach(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return self.value


class FakeBoxes:
    xyxy = FakeTensor([[10, 20, 110, 120]])
    conf = FakeTensor([0.91])
    cls = FakeTensor([0])


class FakeResult:
    boxes = FakeBoxes()
    names = {0: "brick_kiln"}


class YoloDetectorTests(unittest.TestCase):
    def test_missing_yolo_weights_raise_clean_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.pt"
            with self.assertRaises(YoloModelUnavailable) as ctx:
                build_detector_with_fallback("yolo", model_path=missing)
            self.assertIn("YOLO model weights not found", str(ctx.exception))

    def test_missing_yolo_weights_can_fallback_to_baseline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.pt"
            detector, reason = build_detector_with_fallback("yolo", model_path=missing, fallback_to_baseline=True)
            self.assertEqual(detector.name, "fallback")
            self.assertIn("YOLO model weights not found", reason)

    def test_explicit_fallback_marks_detection_truthfully(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            missing = root / "missing.pt"
            tile = root / "kiln_high_test.tile"
            tile.write_bytes(b"demo")
            detector, reason = build_detector_with_fallback("yolo", model_path=missing, fallback_to_baseline=True)

            detection = detector.detect_tile(tile)

            self.assertTrue(detection.fallback_used)
            self.assertEqual(detection.detector_mode, "fallback")
            self.assertFalse(detection.detector_is_real)
            self.assertTrue(detection.simulated)
            self.assertEqual(detection.fallback_reason, reason)

    def test_strict_yolo_cli_fails_loudly_without_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            missing = root / "missing.pt"
            raw_tiles.mkdir()

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "satellite_edge_node.orbital_pass",
                    "--raw-tiles",
                    str(raw_tiles),
                    "--transmission-queue",
                    str(queue),
                    "--detector",
                    "yolo",
                    "--model-path",
                    str(missing),
                ],
                check=False,
                text=True,
                capture_output=True,
            )

            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 2)
            self.assertIn("Detector setup failed", output)
            self.assertIn("--allow-baseline-fallback", output)
            self.assertFalse((queue / "telemetry.jsonl").exists())

    def test_yolo_results_normalize_to_payload_schema(self):
        detection = normalize_yolo_results(tile_id="tile_001", results=[FakeResult()], confidence_threshold=0.25)

        self.assertTrue(detection.kiln_detected)
        self.assertEqual(detection.detector_version, DETECTOR_VERSION)
        self.assertEqual(detection.detector_mode, "yolo")
        self.assertTrue(detection.detector_is_real)
        self.assertFalse(detection.simulated)
        self.assertEqual(detection.bbox, [10.0, 20.0, 110.0, 120.0])
        self.assertEqual(detection.confidence, 0.91)
        self.assertEqual(detection.compliance_risk, "high")
        self.assertIn("yolo_detection:brick_kiln", detection.signals)

    def test_yolo_low_confidence_result_becomes_negative(self):
        detection = normalize_yolo_results(tile_id="tile_001", results=[FakeResult()], confidence_threshold=0.95)

        self.assertFalse(detection.kiln_detected)
        self.assertIsNone(detection.bbox)
        self.assertEqual(detection.detector_version, DETECTOR_VERSION)

    def test_real_yolo_inference_requires_optional_local_setup(self):
        if importlib.util.find_spec("ultralytics") is None:
            self.skipTest("ultralytics is not installed")
        if not Path("models/brick_kiln_yolo.pt").exists():
            self.skipTest("local YOLO weights are not installed")


if __name__ == "__main__":
    unittest.main()
