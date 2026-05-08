import tempfile
import unittest
from pathlib import Path

from kilnwatch.ground_station import (
    calculate_metrics,
    cumulative_series,
    detector_modes,
    load_ground_station_records,
    mission_proof_counts,
    proof_status_summary,
    received_alert_rows,
    reasoner_statuses,
    resolve_crop_evidence,
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

    def test_alert_rows_use_orbital_pass_triage_label(self):
        """The dashboard sources its decision from the new triage_decision field."""
        payload = {
            "tile_id": "live-1",
            "event": "alert",
            "action": "TRANSMIT_ALERT",
            "triage_decision": "CROP_OR_REVIEW",
            "compliance_risk": "medium",
            "confidence": 0.41,
        }
        event = {
            "tile_id": "live-1",
            "action": "TRANSMIT_ALERT",
            "triage_decision": "CROP_OR_REVIEW",
            "compliance_risk": "medium",
            "confidence": 0.41,
        }
        rows = received_alert_rows([payload], [event])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["decision"], "CROP_OR_REVIEW")
        self.assertEqual(rows[0]["risk"], "medium")

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

    def test_reasoner_statuses_distinguish_disabled_mock_and_real(self):
        self.assertEqual(reasoner_statuses([], []), {"disabled"})

        mock_status = reasoner_statuses(
            [{"vlm_reasoning": {"reasoner_mode": "liquid-mock", "reasoner_is_real": False}}],
            [],
        )
        self.assertEqual(mock_status, {"liquid-mock"})

        real_status = reasoner_statuses(
            [],
            [{"vlm_reasoning": {"reasoner_mode": "liquid-local", "reasoner_is_real": True}}],
        )
        self.assertEqual(real_status, {"liquid-real"})

    def test_proof_status_reports_strict_yolo_real(self):
        status = proof_status_summary(
            [
                {
                    "detector_mode": "yolo-strict",
                    "detector_is_real": True,
                    "simulated": False,
                    "fallback_used": False,
                    "detector_version": "ultralytics:yolov8",
                    "confidence_threshold": 0.25,
                }
            ],
            [],
            sample_data=False,
        )

        self.assertEqual(status.detector_label, "STRICT YOLO REAL")
        self.assertEqual(status.reasoner_label, "LFM DISABLED")
        self.assertEqual(status.truth_fields["detector_mode"], "yolo-strict")
        self.assertIs(status.truth_fields["detector_is_real"], True)
        self.assertIs(status.truth_fields["simulated"], False)

    def test_proof_status_reports_baseline_and_fallback_honestly(self):
        baseline = proof_status_summary(
            [{"detector_mode": "baseline", "detector_is_real": False, "simulated": True}],
            [],
        )
        fallback = proof_status_summary(
            [{"detector_mode": "baseline", "simulated": True, "fallback_used": True}],
            [],
        )

        self.assertEqual(baseline.detector_label, "BASELINE SIMULATION")
        self.assertIs(baseline.truth_fields["simulated"], True)
        self.assertEqual(fallback.detector_label, "FALLBACK USED")
        self.assertIs(fallback.truth_fields["fallback_used"], True)

    def test_proof_status_does_not_call_mixed_detector_records_strict_real(self):
        status = proof_status_summary(
            [
                {"detector_mode": "yolo", "detector_is_real": True, "simulated": False},
                {"detector_mode": "baseline", "detector_is_real": False, "simulated": True},
            ],
            [],
        )

        self.assertEqual(status.detector_label, "MIXED DETECTOR METADATA")

    def test_proof_status_reports_sample_data(self):
        status = proof_status_summary([{"sample_demo_data": True}], [], sample_data=True)

        self.assertEqual(status.detector_label, "SAMPLE DATA")
        self.assertIn("SAMPLE DATA", status.notes)

    def test_proof_status_distinguishes_liquid_mock_from_real(self):
        mock = proof_status_summary(
            [
                {
                    "vlm_reasoning": {
                        "reasoner_mode": "liquid-mock",
                        "reasoner_is_real": False,
                        "model_name": "LiquidAI/LFM2.5-VL-450M (mock)",
                    }
                }
            ],
            [],
        )
        real = proof_status_summary(
            [
                {
                    "vlm_reasoning": {
                        "reasoner_mode": "liquid-local",
                        "reasoner_is_real": True,
                        "model_name": "LiquidAI/LFM2.5-VL-450M",
                    }
                }
            ],
            [],
        )

        self.assertEqual(mock.reasoner_label, "LIQUID MOCK")
        self.assertEqual(real.reasoner_label, "LIQUID LFM REAL")
        self.assertIs(mock.truth_fields["vlm_reasoning"]["reasoner_is_real"], False)
        self.assertIs(real.truth_fields["vlm_reasoning"]["reasoner_is_real"], True)

    def test_mission_proof_counts_detections_and_real_queue_crops(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue = Path(temp_dir) / "transmission_queue"
            crops = queue / "crops"
            crops.mkdir(parents=True)
            crop_path = crops / "tile-a_crop.png"
            crop_path.write_bytes(b"real crop bytes")

            counts = mission_proof_counts(
                [
                    {
                        "tile_id": "tile-a",
                        "triage_decision": "CROP_OR_REVIEW",
                        "kiln_detected": True,
                        "crop_ref": str(crop_path),
                    },
                    {
                        "tile_id": "tile-b",
                        "triage_decision": "JSON_ALERT_ONLY",
                        "kiln_detected": True,
                    },
                ],
                [],
                queue_dir=queue,
            )

        self.assertEqual(counts.detections, 2)
        self.assertEqual(counts.crops_generated, 1)

    def test_crop_evidence_reports_missing_crop_without_inventing_preview(self):
        evidence = resolve_crop_evidence(
            [{"tile_id": "tile-a", "triage_decision": "CROP_OR_REVIEW"}],
            [],
        )

        self.assertEqual(len(evidence), 1)
        self.assertFalse(evidence[0].available)
        self.assertEqual(evidence[0].message, "no real crop available")

    def test_crop_evidence_accepts_queue_crop_ref(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue = Path(temp_dir) / "transmission_queue"
            crops = queue / "crops"
            crops.mkdir(parents=True)
            crop_path = crops / "kiln_crop.png"
            crop_path.write_bytes(b"png bytes")

            evidence = resolve_crop_evidence(
                [{"tile_id": "tile-a", "triage_decision": "CROP_OR_REVIEW", "crop_ref": str(crop_path)}],
                [],
                queue_dir=queue,
            )

        self.assertTrue(evidence[0].available)
        self.assertEqual(evidence[0].tile_id, "tile-a")
        self.assertEqual(evidence[0].source_field, "crop_ref")

    def test_crop_evidence_accepts_telemetry_crop_path_for_review_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue = Path(temp_dir) / "transmission_queue"
            crops = queue / "crops"
            crops.mkdir(parents=True)
            crop_path = crops / "kiln_crop.png"
            crop_path.write_bytes(b"png bytes")

            evidence = resolve_crop_evidence(
                [{"tile_id": "tile-a", "triage_decision": "CROP_OR_REVIEW"}],
                [{"tile_id": "tile-a", "crop_path": str(crop_path)}],
                queue_dir=queue,
            )

        self.assertTrue(evidence[0].available)
        self.assertEqual(evidence[0].source_field, "crop_path")

    def test_crop_evidence_rejects_raw_final_roboflow_and_tile_paths(self):
        forbidden_paths = [
            "data/raw_tiles/source.png",
            "data/final_demo_tiles/source.png",
            "datasets/roboflow/source.png",
            "transmission_queue/crops/placeholder.tile",
        ]
        for candidate in forbidden_paths:
            with self.subTest(candidate=candidate):
                evidence = resolve_crop_evidence(
                    [{"tile_id": "tile-a", "triage_decision": "CROP_OR_REVIEW", "crop_ref": candidate}],
                    [],
                )

                self.assertFalse(evidence[0].available)
                self.assertIsNone(evidence[0].path)
                self.assertEqual(evidence[0].message, "no real crop available")

    def test_crop_evidence_rejects_missing_crop_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            queue = Path(temp_dir) / "transmission_queue"
            queue.mkdir()
            evidence = resolve_crop_evidence(
                [{"tile_id": "tile-a", "triage_decision": "CROP_OR_REVIEW", "payload_uri": "crops/missing.png"}],
                [],
                queue_dir=queue,
            )

        self.assertFalse(evidence[0].available)
        self.assertEqual(evidence[0].message, "no real crop available")


if __name__ == "__main__":
    unittest.main()
