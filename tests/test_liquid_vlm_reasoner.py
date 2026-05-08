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
    VlmReasoning,
    _decode_new_tokens,
    _parse_local_response,
    build_reasoner,
)
from satellite_edge_node.orbital_pass import simulate_orbital_pass


class LiquidVlmReasonerTests(unittest.TestCase):
    def _detection(self, *, confidence: float = 0.87, risk: str = "high") -> DetectionResult:
        return DetectionResult(
            tile_id="tile_001",
            kiln_detected=True,
            confidence=confidence,
            compliance_risk=risk,
            coordinates=None,
            bbox=[1, 2, 30, 30],
            crop_ref=None,
            signals=["test"],
            detector_mode="yolo",
            detector_is_real=True,
            simulated=False,
        )

    def test_disabled_reasoner_builds_to_none(self):
        self.assertIsNone(build_reasoner("disabled"))

    def test_mock_reasoner_is_marked_simulated(self):
        detection = self._detection()

        reasoning = LiquidMockReasoner().reason(
            image_path=Path("transmission_queue/crops/tile_001_crop.png"),
            detection=detection,
            crop_path=Path("transmission_queue/crops/tile_001_crop.png"),
        )

        self.assertEqual(reasoning.reasoner_mode, "liquid-mock")
        self.assertFalse(reasoning.reasoner_is_real)
        self.assertTrue(reasoning.reasoner_output_valid)
        self.assertEqual(reasoning.reasoned_over, "crop")
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
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is not installed")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()
            tile = raw_tiles / "kiln_high_001.png"
            Image.new("RGB", (32, 32), color="white").save(tile)
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
        self.assertTrue(payload["vlm_reasoning"]["reasoner_output_valid"])
        self.assertEqual(records[0]["vlm_reasoning"]["reasoner_mode"], "liquid-mock")

    def test_local_response_prompt_echo_is_not_valid_structured_reasoning(self):
        prompt_echo = (
            "Return ONLY a single JSON object with these exact keys, no prose:\n"
            "{\n"
            '  "credible_kiln":         true|false,\n'
            '  "compliance_risk":       "low"|"medium"|"high",\n'
            '  "human_review_needed":   true|false,\n'
            '  "visual_summary":        "<one sentence describing the crop>",\n'
            '  "risk_reasoning":        "<one sentence: why this is or is not a kiln>",\n'
            '  "confidence_note":       "<caveats about image quality or scale>"\n'
            "}"
        )

        reasoning = _parse_local_response(
            prompt_echo,
            detection=self._detection(),
            reasoner_mode="liquid-local",
            model_name="LiquidAI/LFM2.5-VL-450M",
            reasoned_over="crop",
            crop_path_used=Path("queue/crops/tile_001_crop.png"),
        )

        self.assertTrue(reasoning.reasoner_is_real)
        self.assertFalse(reasoning.reasoner_output_valid)
        self.assertEqual(reasoning.risk_reasoning, "Liquid call succeeded, structured parse failed.")
        self.assertIn("Return ONLY", reasoning.raw_output_excerpt)

    def test_local_response_invalid_parse_is_real_but_invalid(self):
        reasoning = _parse_local_response(
            "The image may show a kiln, but I cannot return JSON.",
            detection=self._detection(risk="medium"),
            reasoner_mode="liquid-local",
            model_name="LiquidAI/LFM2.5-VL-450M",
            reasoned_over="crop",
            crop_path_used=Path("queue/crops/tile_001_crop.png"),
        )

        self.assertTrue(reasoning.reasoner_is_real)
        self.assertFalse(reasoning.reasoner_output_valid)
        self.assertEqual(reasoning.compliance_risk, "medium")
        self.assertIn("cannot return JSON", reasoning.raw_output_excerpt)

    def test_local_response_expected_json_is_valid(self):
        reasoning = _parse_local_response(
            json.dumps(
                {
                    "credible_kiln": True,
                    "compliance_risk": "high",
                    "human_review_needed": True,
                    "visual_summary": "Rectangular kiln-like structure is visible.",
                    "risk_reasoning": "The crop has a likely kiln footprint.",
                    "confidence_note": "Small crop, but morphology is clear.",
                }
            ),
            detection=self._detection(),
            reasoner_mode="liquid-local",
            model_name="LiquidAI/LFM2.5-VL-450M",
            reasoned_over="crop",
            crop_path_used=Path("queue/crops/tile_001_crop.png"),
        )

        self.assertTrue(reasoning.reasoner_is_real)
        self.assertTrue(reasoning.reasoner_output_valid)
        self.assertEqual(reasoning.reasoned_over, "crop")
        self.assertEqual(reasoning.crop_path_used, "queue/crops/tile_001_crop.png")
        self.assertIsNone(reasoning.raw_output_excerpt)

    def test_decode_new_tokens_excludes_prompt_tokens(self):
        class Processor:
            def batch_decode(self, token_batches, **kwargs):
                self.kwargs = kwargs
                self.token_batches = token_batches
                return ["decoded:" + ",".join(str(token) for token in token_batches[0])]

        processor = Processor()
        decoded = _decode_new_tokens(
            processor,
            outputs=[[101, 102, 103, 201, 202]],
            inputs={"input_ids": [[101, 102, 103]]},
        )

        self.assertEqual(decoded, "decoded:201,202")
        self.assertEqual(processor.token_batches, [[201, 202]])
        self.assertFalse(processor.kwargs["clean_up_tokenization_spaces"])

    def test_orbital_pass_reasoner_receives_crop_after_generation(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is not installed")

        class RecordingReasoner:
            mode = "recording"

            def __init__(self):
                self.calls = []

            def reason(self, *, image_path, detection, crop_path=None):
                self.calls.append(
                    {
                        "image_path": image_path,
                        "crop_path": crop_path,
                        "crop_exists": crop_path is not None and crop_path.is_file(),
                    }
                )
                return VlmReasoning(
                    visual_summary="Valid crop-level Liquid output.",
                    risk_reasoning="Crop contains kiln-like rectangular geometry.",
                    compliance_risk="low",
                    human_review_needed=False,
                    confidence_note="Test fixture.",
                    reasoner_mode=self.mode,
                    reasoner_is_real=True,
                    reasoner_output_valid=True,
                    model_name="test-liquid",
                    reasoned_over="crop" if crop_path else "none",
                    crop_path_used=str(crop_path) if crop_path else None,
                )

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()
            tile = raw_tiles / "kiln_crop_test.png"
            Image.new("RGB", (40, 40), color="white").save(tile)
            tile.with_suffix(tile.suffix + ".meta.json").write_text(
                json.dumps(
                    {
                        "tile_id": "kiln_crop_test",
                        "kiln_detected": True,
                        "confidence": 0.7,
                        "compliance_risk": "medium",
                        "bbox": [8, 8, 32, 32],
                    }
                ),
                encoding="utf-8",
            )
            reasoner = RecordingReasoner()

            records = simulate_orbital_pass(
                raw_tiles,
                queue,
                detector_mode="baseline",
                reasoner=reasoner,
                reasoner_mode="liquid-local",
                reset_queue=True,
            )
            payload = json.loads((queue / "kiln_crop_test.json").read_text(encoding="utf-8"))

        self.assertEqual(len(reasoner.calls), 1)
        self.assertEqual(reasoner.calls[0]["image_path"], tile)
        self.assertTrue(reasoner.calls[0]["crop_exists"])
        self.assertEqual(payload["triage_decision"], "CROP_OR_REVIEW")
        self.assertEqual(payload["triage"]["driven_by"], "yolo-only")
        self.assertEqual(payload["vlm_reasoning"]["reasoned_over"], "crop")
        self.assertEqual(payload["vlm_reasoning"]["crop_path_used"], str(reasoner.calls[0]["crop_path"]))
        self.assertEqual(payload["crop_ref"], str(reasoner.calls[0]["crop_path"]))
        self.assertEqual(records[0]["vlm_reasoning"]["reasoner_output_valid"], True)


if __name__ == "__main__":
    unittest.main()
