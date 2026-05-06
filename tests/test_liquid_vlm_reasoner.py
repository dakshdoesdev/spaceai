import builtins
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from satellite_edge_node.baseline_detector import DetectionResult
from satellite_edge_node.liquid_vlm_reasoner import (
    LiquidLocalReasoner,
    LiquidMockReasoner,
    LiquidReasonerUnavailable,
    build_reasoner,
)
from satellite_edge_node.orbital_pass import simulate_orbital_pass


class LiquidVlmReasonerTests(unittest.TestCase):
    def test_disabled_reasoner_builds_to_none(self):
        self.assertIsNone(build_reasoner("disabled"))

    def test_mock_reasoner_is_marked_simulated(self):
        detection = DetectionResult(
            tile_id="tile_001",
            kiln_detected=True,
            confidence=0.87,
            compliance_risk="high",
            coordinates=None,
            bbox=[1, 2, 3, 4],
            crop_ref=None,
            signals=["test"],
            detector_mode="yolo",
            detector_is_real=True,
            simulated=False,
        )

        reasoning = LiquidMockReasoner().reason(
            image_path=Path("transmission_queue/crops/tile_001_crop.png"),
            detection=detection,
        )

        self.assertEqual(reasoning.reasoner_mode, "liquid-mock")
        self.assertFalse(reasoning.reasoner_is_real)
        self.assertIn("mock", reasoning.model_name.lower())
        self.assertIn("simulated", reasoning.confidence_note.lower())

    def test_local_reasoner_fails_honestly_when_transformers_unavailable(self):
        real_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            if name == "transformers":
                raise ImportError("no transformers here")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=guarded_import):
            with self.assertRaises(LiquidReasonerUnavailable) as ctx:
                LiquidLocalReasoner()

        self.assertIn("requires `transformers`", str(ctx.exception))

    def test_disabled_orbital_pass_produces_no_vlm_reasoning(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()
            tile = raw_tiles / "kiln_high_001.tile"
            tile.write_bytes(b"demo")
            tile.with_suffix(tile.suffix + ".meta.json").write_text(
                json.dumps(
                    {
                        "tile_id": "kiln_high_001",
                        "kiln_detected": True,
                        "confidence": 0.88,
                        "compliance_risk": "high",
                        "bbox": [1, 1, 10, 10],
                    }
                ),
                encoding="utf-8",
            )

            records = simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline")
            payload = json.loads((queue / "kiln_high_001.json").read_text(encoding="utf-8"))

        self.assertEqual(records[0]["requested_reasoner_mode"], "disabled")
        self.assertNotIn("vlm_reasoning", records[0])
        self.assertNotIn("vlm_reasoning", payload)

    def test_mock_reasoner_metadata_is_written_to_payload_and_telemetry(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()
            tile = raw_tiles / "kiln_high_001.tile"
            tile.write_bytes(b"demo")
            tile.with_suffix(tile.suffix + ".meta.json").write_text(
                json.dumps(
                    {
                        "tile_id": "kiln_high_001",
                        "kiln_detected": True,
                        "confidence": 0.88,
                        "compliance_risk": "high",
                        "bbox": [1, 1, 10, 10],
                    }
                ),
                encoding="utf-8",
            )

            records = simulate_orbital_pass(
                raw_tiles,
                queue,
                detector_mode="baseline",
                reasoner_mode="liquid-mock",
            )
            payload = json.loads((queue / "kiln_high_001.json").read_text(encoding="utf-8"))

        self.assertEqual(records[0]["requested_reasoner_mode"], "liquid-mock")
        self.assertEqual(payload["vlm_reasoning"]["reasoner_mode"], "liquid-mock")
        self.assertFalse(payload["vlm_reasoning"]["reasoner_is_real"])
        self.assertEqual(records[0]["vlm_reasoning"]["reasoner_mode"], "liquid-mock")


if __name__ == "__main__":
    unittest.main()
