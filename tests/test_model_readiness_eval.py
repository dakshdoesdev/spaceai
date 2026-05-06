import json
import tempfile
import unittest
from pathlib import Path

from scripts.check_model_ready import check_model_ready
from scripts.evaluate_detector import evaluate_detector


class ModelReadinessAndEvaluationTests(unittest.TestCase):
    def test_missing_model_reports_real_detector_unavailable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            result = check_model_ready(Path(temp_dir) / "missing.pt")

        self.assertFalse(result["ready_for_strict_yolo"])
        self.assertEqual(result["status"], "real detector unavailable")
        self.assertTrue(any("weights not found" in item for item in result["missing"]))

    def test_evaluator_marks_baseline_sample_as_simulated(self):
        result = evaluate_detector(
            Path("datasets/kilnwatch/manifests/baseline_sample_eval_manifest.jsonl"),
            Path("transmission_queue/telemetry.jsonl"),
        )

        self.assertEqual(result["evaluation_status"], "simulated_baseline")
        self.assertEqual(result["detector_mode_used"], "baseline")
        self.assertEqual(result["number_of_tiles"], 3)
        self.assertEqual(result["positives"], 1)
        self.assertEqual(result["negatives"], 2)
        self.assertIn("do not claim real detector accuracy", result["overclaim_warning"])

    def test_evaluator_reports_real_yolo_only_for_yolo_non_sample_rows(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = root / "manifest.jsonl"
            telemetry = root / "telemetry.jsonl"
            manifest.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "tile_id": "real_positive",
                                "image_path": "local/real_positive.png",
                                "lat": 29.0,
                                "lon": 76.0,
                                "source": "manual_license_checked_dataset",
                                "split": "test",
                                "label": "brick_kiln",
                                "kiln_detected": True,
                                "notes": "License checked local test row.",
                            }
                        ),
                        json.dumps(
                            {
                                "tile_id": "real_negative",
                                "image_path": "local/real_negative.png",
                                "lat": 29.1,
                                "lon": 76.1,
                                "source": "manual_license_checked_dataset",
                                "split": "test",
                                "label": "negative",
                                "kiln_detected": False,
                                "notes": "License checked local test row.",
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            telemetry.write_text(
                "\n".join(
                    [
                        json.dumps(
                            {
                                "tile_id": "real_positive",
                                "detector_version": "yolo_ultralytics:v0.1",
                                "requested_detector_mode": "yolo",
                                "kiln_detected": True,
                                "confidence": 0.9,
                                "original_payload_bytes": 1000,
                                "transmitted_payload_bytes": 100,
                            }
                        ),
                        json.dumps(
                            {
                                "tile_id": "real_negative",
                                "detector_version": "yolo_ultralytics:v0.1",
                                "requested_detector_mode": "yolo",
                                "kiln_detected": False,
                                "confidence": 0.1,
                                "original_payload_bytes": 1000,
                                "transmitted_payload_bytes": 0,
                            }
                        ),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            result = evaluate_detector(manifest, telemetry)

        self.assertEqual(result["evaluation_status"], "real_yolo")
        self.assertEqual(result["detector_mode_used"], "yolo")
        self.assertEqual(result["detected_positives"], 1)
        self.assertEqual(result["false_positives"], 0)
        self.assertEqual(result["false_negatives"], 0)


if __name__ == "__main__":
    unittest.main()

