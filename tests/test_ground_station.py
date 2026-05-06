import tempfile
import unittest
from pathlib import Path

from kilnwatch.ground_station import (
    calculate_metrics,
    cumulative_series,
    detector_modes,
    load_ground_station_records,
    received_alert_rows,
    safe_review_payloads,
)


class GroundStationTests(unittest.TestCase):
    def test_metrics_summarize_downlink_savings(self):
        metrics = calculate_metrics(
            [
                {"triage_decision": "IGNORE", "raw_bytes_processed": 1000, "downlinked_bytes": 0, "inference_latency_ms": 10},
                {
                    "triage_decision": "JSON_ALERT_ONLY",
                    "raw_bytes_processed": 1000,
                    "downlinked_bytes": 10,
                    "inference_latency_ms": 20,
                },
                {
                    "triage_decision": "CROP_OR_REVIEW",
                    "raw_bytes_processed": 1000,
                    "downlinked_bytes": 100,
                    "inference_latency_ms": 30,
                },
            ]
        )
        self.assertEqual(metrics.raw_bytes_processed, 3000)
        self.assertEqual(metrics.downlinked_bytes, 110)
        self.assertEqual(metrics.bytes_saved, 2890)
        self.assertAlmostEqual(metrics.bandwidth_saved_percent, 96.33333333333334)
        self.assertEqual(metrics.tiles_processed, 3)
        self.assertEqual(metrics.ignored_tiles, 1)
        self.assertEqual(metrics.json_alerts, 1)
        self.assertEqual(metrics.crop_or_full_review_alerts, 1)
        self.assertEqual(metrics.average_latency_ms, 20)

    def test_cumulative_series_tracks_raw_vs_downlinked_bytes(self):
        series = cumulative_series(
            [
                {"tile_id": "a", "raw_bytes_processed": 100, "downlinked_bytes": 10},
                {"tile_id": "b", "raw_bytes_processed": 200, "downlinked_bytes": 20},
            ]
        )
        self.assertEqual(series[-1]["Raw bytes processed in orbit"], 300)
        self.assertEqual(series[-1]["Bytes downlinked"], 30)

    def test_alert_rows_exclude_ignored_tiles(self):
        rows = received_alert_rows(
            [{"tile_id": "b", "triage_decision": "JSON_ALERT_ONLY", "payload_type": "json_alert"}],
            [
                {"tile_id": "a", "triage_decision": "IGNORE"},
                {"tile_id": "b", "triage_decision": "JSON_ALERT_ONLY"},
            ],
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["tile_id"], "b")

    def test_review_payloads_only_include_image_allowed_decisions(self):
        payloads = safe_review_payloads(
            [
                {"tile_id": "a", "triage_decision": "JSON_ALERT_ONLY", "payload_uri": "x"},
                {"tile_id": "b", "triage_decision": "CROP_OR_REVIEW", "payload_uri": "y"},
                {"tile_id": "c", "triage_decision": "FULL_DOWNLINK", "payload_uri": "z"},
            ]
        )
        self.assertEqual([payload["tile_id"] for payload in payloads], ["b", "c"])

    def test_metrics_accept_orbital_pass_telemetry_schema(self):
        metrics = calculate_metrics(
            [
                {"action": "DROP_RAW_TILE", "original_payload_bytes": 1000, "transmitted_payload_bytes": 100},
                {"action": "TRANSMIT_ALERT", "original_payload_bytes": 2000, "transmitted_payload_bytes": 500},
            ]
        )
        self.assertEqual(metrics.raw_bytes_processed, 3000)
        self.assertEqual(metrics.downlinked_bytes, 600)
        self.assertEqual(metrics.ignored_tiles, 1)
        self.assertEqual(metrics.crop_or_full_review_alerts, 1)

    def test_real_records_take_precedence_over_sample_records(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            queue = root / "transmission_queue"
            logs = root / "telemetry_logs"
            queue.mkdir()
            logs.mkdir()
            (queue / "real.json").write_text('{"tile_id":"real","action":"TRANSMIT_ALERT"}', encoding="utf-8")
            (logs / "sample.jsonl").write_text(
                '{"sample_demo_data":true,"tile_id":"sample","triage_decision":"IGNORE"}\n',
                encoding="utf-8",
            )

            payloads, events, sample = load_ground_station_records(queue, logs)

        self.assertFalse(sample)
        self.assertEqual([payload["tile_id"] for payload in payloads], ["real"])
        self.assertEqual(events, [])

    def test_detector_modes_read_baseline_and_yolo_metadata(self):
        modes = detector_modes(
            [{"detector_metadata": {"mode": "yolo_v8_real"}}],
            [{"detector_version": "baseline_detector:v0.1"}],
        )
        self.assertIn("yolo_v8_real", modes)
        self.assertIn("baseline_detector:v0.1", modes)


if __name__ == "__main__":
    unittest.main()
