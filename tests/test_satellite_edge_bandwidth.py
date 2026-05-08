import json
import tempfile
import unittest
from pathlib import Path

from ground_station_ui.queue_reader import summarize_telemetry
from satellite_edge_node.baseline_detector import DetectionResult
from satellite_edge_node.orbital_pass import RequiredCropUnavailable, simulate_orbital_pass
from satellite_edge_node.payloads import bandwidth_saved_bytes, compression_ratio, encode_payload, telemetry_record


class BandwidthMathTests(unittest.TestCase):
    def test_bandwidth_saved_uses_real_byte_difference(self):
        self.assertEqual(bandwidth_saved_bytes(1000, 125), 875)
        self.assertEqual(bandwidth_saved_bytes(100, 125), 0)

    def test_compression_ratio_handles_zero_byte_downlink(self):
        self.assertEqual(compression_ratio(1000, 250), 4.0)
        self.assertEqual(compression_ratio(0, 0), 1.0)
        self.assertEqual(compression_ratio(1000, 0), float("inf"))

    def test_telemetry_record_contains_detector_version_and_sizes(self):
        detection = DetectionResult(
            tile_id="tile_001",
            kiln_detected=True,
            confidence=0.81,
            compliance_risk="high",
            coordinates={"lat": 29.4, "lon": 76.9},
            bbox=[1, 2, 3, 4],
            crop_ref=None,
            signals=["test"],
        )
        record = telemetry_record(
            tile_path=Path("data/raw_tiles/tile_001.bin"),
            detection=detection,
            inference_latency_ms=1.2,
            original_payload_bytes=1000,
            transmitted_payload_bytes=100,
            json_payload_bytes=100,
            crop_payload_bytes=0,
            crop_path=None,
            crop_error=None,
            output_path=Path("transmission_queue/tile_001.json"),
        )

        self.assertEqual(record["detector_version"], "baseline_detector:v0.1")
        self.assertEqual(record["detector_mode"], "baseline")
        self.assertFalse(record["detector_is_real"])
        self.assertTrue(record["simulated"])
        self.assertFalse(record["fallback_used"])
        self.assertEqual(record["bandwidth_saved_bytes"], 900)
        self.assertEqual(record["compression_ratio"], 10.0)
        self.assertEqual(record["action"], "TRANSMIT_ALERT")

    def test_telemetry_record_includes_triage_decision_label(self):
        detection = DetectionResult(
            tile_id="tile_high_001",
            kiln_detected=True,
            confidence=0.81,
            compliance_risk="high",
            coordinates=None,
            bbox=[1, 2, 3, 4],
            crop_ref=None,
            signals=["test"],
        )
        record = telemetry_record(
            tile_path=Path("data/raw_tiles/tile_high_001.bin"),
            detection=detection,
            inference_latency_ms=1.0,
            original_payload_bytes=1000,
            transmitted_payload_bytes=100,
            json_payload_bytes=100,
            crop_payload_bytes=0,
            crop_path=None,
            crop_error=None,
            output_path=None,
            triage_min_confidence=0.25,
        )
        self.assertIn(record["triage_decision"], {"CROP_OR_REVIEW", "FULL_DOWNLINK", "JSON_ALERT_ONLY"})
        self.assertEqual(record["triage"]["driven_by"], "yolo-only")
        self.assertEqual(record["triage"]["risk_band_used"], "high")

    def test_telemetry_record_low_confidence_below_detector_floor_is_ignored(self):
        detection = DetectionResult(
            tile_id="tile_low_001",
            kiln_detected=False,
            confidence=0.1,
            compliance_risk="low",
            coordinates=None,
            bbox=None,
            crop_ref=None,
            signals=[],
        )
        record = telemetry_record(
            tile_path=Path("data/raw_tiles/tile_low_001.bin"),
            detection=detection,
            inference_latency_ms=0.5,
            original_payload_bytes=1000,
            transmitted_payload_bytes=0,
            json_payload_bytes=0,
            crop_payload_bytes=0,
            crop_path=None,
            crop_error=None,
            output_path=None,
            triage_min_confidence=0.25,
        )
        self.assertEqual(record["triage_decision"], "IGNORE")


class OrbitalPassTests(unittest.TestCase):
    def test_orbital_pass_uses_file_sizes_and_queue_outputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()

            positive = raw_tiles / "kiln_medium_001.tile"
            negative = raw_tiles / "farm_negative_001.tile"
            positive.write_bytes(b"x" * 2048)
            negative.write_bytes(b"y" * 1024)
            # Medium-risk + sub-FULL confidence keeps this as CROP_OR_REVIEW so the
            # crop+JSON path is exercised without triggering full-tile copy.
            (positive.with_suffix(positive.suffix + ".meta.json")).write_text(
                json.dumps(
                    {
                        "tile_id": "kiln_medium_001",
                        "kiln_detected": True,
                        "confidence": 0.7,
                        "compliance_risk": "medium",
                        "coordinates": {"lat": 29.39, "lon": 76.96},
                        "bbox": [4, 4, 20, 20],
                        "signals": ["sidecar_test"],
                    }
                ),
                encoding="utf-8",
            )

            records = simulate_orbital_pass(raw_tiles, queue)
            summary = summarize_telemetry(records)

            self.assertEqual(len(records), 2)
            self.assertEqual(summary["original_payload_bytes"], 3072)
            self.assertGreater(summary["bandwidth_saved_bytes"], 0)
            self.assertEqual(summary["alerts"], 1)
            self.assertTrue((queue / "kiln_medium_001.json").exists())
            self.assertFalse((queue / "farm_negative_001.json").exists())
            self.assertTrue((queue / "telemetry.jsonl").exists())
            self.assertIsNone([record for record in records if record["tile_id"] == "farm_negative_001"][0]["output_path"])

    def test_orbital_pass_can_run_with_explicit_baseline_detector(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()
            (raw_tiles / "farm_negative_001.tile").write_bytes(b"y" * 1024)

            records = simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline")

            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["requested_detector_mode"], "baseline")
            self.assertEqual(records[0]["detector_version"], "baseline_detector:v0.1")
            self.assertEqual(records[0]["detector_mode"], "baseline")
            self.assertFalse(records[0]["detector_is_real"])
            self.assertTrue(records[0]["simulated"])

    def test_reset_queue_removes_only_generated_queue_artifacts(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            crops = queue / "crops"
            raw_tiles.mkdir()
            crops.mkdir(parents=True)

            tile = raw_tiles / "kiln_high_001.tile"
            sidecar = tile.with_suffix(tile.suffix + ".meta.json")
            tile.write_bytes(b"x" * 2048)
            sidecar.write_text(
                json.dumps(
                    {
                        "tile_id": "kiln_high_001",
                        "kiln_detected": True,
                        "confidence": 0.88,
                        "compliance_risk": "high",
                        "bbox": [4, 4, 20, 20],
                    }
                ),
                encoding="utf-8",
            )
            (queue / "stale_payload.json").write_text('{"stale":true}', encoding="utf-8")
            (queue / "telemetry.jsonl").write_text('{"tile_id":"stale"}\n', encoding="utf-8")
            (crops / "stale_crop.png").write_bytes(b"stale")
            preserved = queue / "manual_notes.txt"
            preserved.write_text("keep me", encoding="utf-8")

            records = simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline", reset_queue=True)
            telemetry_lines = (queue / "telemetry.jsonl").read_text(encoding="utf-8").splitlines()

            self.assertEqual(len(records), 1)
            self.assertEqual(len(telemetry_lines), 1)
            self.assertIn("kiln_high_001", telemetry_lines[0])
            self.assertFalse((queue / "stale_payload.json").exists())
            self.assertFalse((crops / "stale_crop.png").exists())
            self.assertTrue(preserved.exists())
            self.assertTrue(tile.exists())
            self.assertTrue(sidecar.exists())

    def test_real_crop_file_is_created_from_png_and_counted_in_bytes(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is not installed")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()

            tile = raw_tiles / "kiln_crop_test.png"
            Image.new("RGB", (32, 32), color="white").save(tile)
            # Medium-risk + 0.7 confidence -> CROP_OR_REVIEW. We're testing the
            # crop file path, so we want the JSON+crop tier, not full-tile.
            (tile.with_suffix(tile.suffix + ".meta.json")).write_text(
                json.dumps(
                    {
                        "tile_id": "kiln_crop_test",
                        "kiln_detected": True,
                        "confidence": 0.7,
                        "compliance_risk": "medium",
                        "bbox": [8, 8, 24, 24],
                        "signals": ["crop_test"],
                    }
                ),
                encoding="utf-8",
            )

            records = simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline", reset_queue=True)

            crop_path = Path(records[0]["crop_path"])
            payload_path = queue / "kiln_crop_test.json"
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            self.assertTrue(crop_path.exists())
            self.assertGreater(crop_path.stat().st_size, 0)
            self.assertEqual(payload["detector_mode"], "baseline")
            self.assertFalse(payload["detector_is_real"])
            self.assertTrue(payload["simulated"])
            self.assertEqual(payload["action"], "TRANSMIT_ALERT")
            self.assertEqual(payload["triage_decision"], "CROP_OR_REVIEW")
            self.assertEqual(payload["crop_ref"], str(crop_path))
            self.assertIn("crop_error", payload)
            self.assertIsNone(payload["crop_error"])
            self.assertNotIn("full_tile_ref", payload)
            self.assertIsNone(records[0]["crop_error"])
            self.assertEqual(records[0]["crop_payload_bytes"], crop_path.stat().st_size)
            self.assertEqual(records[0]["full_tile_payload_bytes"], 0)
            self.assertEqual(records[0]["json_payload_bytes"], len(encode_payload(payload)))
            for key in (
                "original_payload_bytes",
                "json_payload_bytes",
                "crop_payload_bytes",
                "transmitted_payload_bytes",
                "bandwidth_saved_bytes",
            ):
                self.assertEqual(payload["byte_accounting"][key], records[0][key])
            self.assertEqual(
                records[0]["transmitted_payload_bytes"],
                records[0]["json_payload_bytes"] + records[0]["crop_payload_bytes"],
            )

    def test_unreadable_crop_does_not_claim_crop_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()
            tile = raw_tiles / "kiln_crop_blob.tile"
            tile.write_bytes(b"not an image")
            (tile.with_suffix(tile.suffix + ".meta.json")).write_text(
                json.dumps(
                    {
                        "tile_id": "kiln_crop_blob",
                        "kiln_detected": True,
                        "confidence": 0.9,
                        "compliance_risk": "high",
                        "bbox": [1, 1, 10, 10],
                    }
                ),
                encoding="utf-8",
            )

            records = simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline")
            payload = json.loads((queue / "kiln_crop_blob.json").read_text(encoding="utf-8"))

            self.assertIsNone(payload["crop_ref"])
            self.assertIn("not a readable image", records[0]["crop_error"])
            self.assertEqual(records[0]["crop_payload_bytes"], 0)

    def test_full_downlink_tier_copies_full_tile_into_queue(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow is not installed")

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()

            tile = raw_tiles / "kiln_full_001.png"
            Image.new("RGB", (32, 32), color="red").save(tile)
            (tile.with_suffix(tile.suffix + ".meta.json")).write_text(
                json.dumps(
                    {
                        "tile_id": "kiln_full_001",
                        "kiln_detected": True,
                        "confidence": 0.92,
                        "compliance_risk": "high",
                        "bbox": [4, 4, 28, 28],
                        "signals": ["full_downlink_test"],
                    }
                ),
                encoding="utf-8",
            )

            records = simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline", reset_queue=True)

            payload = json.loads((queue / "kiln_full_001.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["triage_decision"], "FULL_DOWNLINK")
            self.assertEqual(payload["action"], "TRANSMIT_FULL_TILE")
            self.assertIn("full_tile_ref", payload)
            self.assertIn("crop_ref", payload)
            full_tile_path = Path(payload["full_tile_ref"])
            self.assertTrue(full_tile_path.exists())
            self.assertEqual(full_tile_path.stat().st_size, tile.stat().st_size)
            self.assertEqual(records[0]["full_tile_payload_bytes"], tile.stat().st_size)

    def test_json_only_tier_writes_payload_without_crop(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()

            tile = raw_tiles / "kiln_json_001.tile"
            tile.write_bytes(b"x" * 1024)
            # confidence above the IGNORE floor, but risk is low → JSON_ALERT_ONLY.
            (tile.with_suffix(tile.suffix + ".meta.json")).write_text(
                json.dumps(
                    {
                        "tile_id": "kiln_json_001",
                        "kiln_detected": True,
                        "confidence": 0.7,
                        "compliance_risk": "low",
                        "bbox": [1, 1, 5, 5],
                        "signals": ["json_only_test"],
                    }
                ),
                encoding="utf-8",
            )

            records = simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline", reset_queue=True)
            payload = json.loads((queue / "kiln_json_001.json").read_text(encoding="utf-8"))

            self.assertEqual(payload["triage_decision"], "JSON_ALERT_ONLY")
            self.assertEqual(payload["action"], "TRANSMIT_JSON_ONLY")
            self.assertNotIn("crop_ref", payload)
            self.assertNotIn("full_tile_ref", payload)
            self.assertEqual(records[0]["crop_payload_bytes"], 0)
            self.assertEqual(records[0]["full_tile_payload_bytes"], 0)
            self.assertFalse((queue / "crops" / "kiln_json_001_crop.png").exists())

    def test_ignore_tier_drops_tile_with_no_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()

            tile = raw_tiles / "farm_negative.tile"
            tile.write_bytes(b"y" * 512)

            records = simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline", reset_queue=True)

            self.assertEqual(records[0]["triage_decision"], "IGNORE")
            self.assertEqual(records[0]["action"], "DROP_RAW_TILE")
            self.assertEqual(records[0]["transmitted_payload_bytes"], 0)
            self.assertFalse((queue / "farm_negative.json").exists())

    def test_require_crops_fails_for_alert_without_real_crop(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_tiles = root / "raw_tiles"
            queue = root / "queue"
            raw_tiles.mkdir()
            tile = raw_tiles / "kiln_crop_blob.tile"
            tile.write_bytes(b"not an image")
            (tile.with_suffix(tile.suffix + ".meta.json")).write_text(
                json.dumps(
                    {
                        "tile_id": "kiln_crop_blob",
                        "kiln_detected": True,
                        "confidence": 0.9,
                        "compliance_risk": "high",
                        "bbox": [1, 1, 10, 10],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RequiredCropUnavailable, "not a readable image"):
                simulate_orbital_pass(raw_tiles, queue, detector_mode="baseline", require_crops=True)

            self.assertFalse((queue / "kiln_crop_blob.json").exists())


if __name__ == "__main__":
    unittest.main()
