#!/usr/bin/env python
"""Evaluate KilnWatch detector telemetry against a manifest without overclaiming."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from sklearn.metrics import precision_score, recall_score, accuracy_score, roc_auc_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


DEFAULT_MANIFEST = Path("datasets/kilnwatch/manifests/baseline_sample_eval_manifest.jsonl")
DEFAULT_TELEMETRY = Path("transmission_queue/telemetry.jsonl")


def evaluate_detector(manifest_path: Path, telemetry_path: Path) -> dict[str, Any]:
    manifest_rows = _read_jsonl(manifest_path)
    telemetry_rows = _read_jsonl(telemetry_path) if telemetry_path.exists() else []
    telemetry_by_tile = {str(row.get("tile_id")): row for row in telemetry_rows if row.get("tile_id")}

    evaluated: list[tuple[dict[str, Any], dict[str, Any]]] = []
    missing_predictions: list[str] = []
    for row in manifest_rows:
        tile_id = str(row.get("tile_id", ""))
        record = telemetry_by_tile.get(tile_id)
        if record is None:
            missing_predictions.append(tile_id)
            continue
        evaluated.append((row, record))

    positives = sum(1 for row in manifest_rows if _truth_positive(row))
    negatives = sum(1 for row in manifest_rows if not _truth_positive(row))
    detected_positives = sum(1 for row, record in evaluated if _truth_positive(row) and _predicted_positive(record))
    false_positives = sum(1 for row, record in evaluated if not _truth_positive(row) and _predicted_positive(record))
    false_negatives = sum(1 for row, record in evaluated if _truth_positive(row) and not _predicted_positive(record))
    confidences = [_confidence(record) for _, record in evaluated if _confidence(record) is not None]
    raw_bytes = sum(_int_value(record.get("raw_bytes_processed", record.get("original_payload_bytes"))) for _, record in evaluated)
    downlinked_bytes = sum(_int_value(record.get("downlinked_bytes", record.get("transmitted_payload_bytes"))) for _, record in evaluated)
    bandwidth_saved = max(0, raw_bytes - downlinked_bytes)
    detector_mode = _detector_mode([record for _, record in evaluated])
    sample_or_placeholder = _is_simulated(manifest_rows, [record for _, record in evaluated], detector_mode)

    result = {
        "evaluation_status": "simulated_baseline" if sample_or_placeholder else "real_yolo",
        "overclaim_warning": _warning(sample_or_placeholder, missing_predictions),
        "manifest_path": str(manifest_path),
        "telemetry_path": str(telemetry_path),
        "detector_mode_used": detector_mode,
        "number_of_tiles": len(manifest_rows),
        "evaluated_tiles": len(evaluated),
        "missing_predictions": missing_predictions,
        "positives": positives,
        "negatives": negatives,
        "detected_positives": detected_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "average_confidence": round(sum(confidences) / len(confidences), 4) if confidences else 0.0,
        "raw_bytes_processed": raw_bytes,
        "downlinked_bytes": downlinked_bytes,
        "bandwidth_saved": bandwidth_saved,
        "bandwidth_saved_percent": round((bandwidth_saved / raw_bytes) * 100, 2) if raw_bytes else 0.0,
    }

    if SKLEARN_AVAILABLE and evaluated:
        y_true = [1 if _truth_positive(row) else 0 for row, _ in evaluated]
        y_pred_label = [1 if _predicted_positive(record) else 0 for _, record in evaluated]
        y_pred_prob = [_confidence(record) or (1.0 if _predicted_positive(record) else 0.0) for _, record in evaluated]

        precision = precision_score(y_true, y_pred_label, zero_division=0)
        recall = recall_score(y_true, y_pred_label, zero_division=0)
        accuracy = accuracy_score(y_true, y_pred_label)
        
        result["sklearn_metrics"] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "accuracy": round(accuracy, 4),
        }
        
        try:
            auc = roc_auc_score(y_true, y_pred_prob)
            result["sklearn_metrics"]["roc_auc"] = round(auc, 4)
        except ValueError:
            # roc_auc_score throws ValueError if only one class is present in y_true
            result["sklearn_metrics"]["roc_auc"] = None

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate KilnWatch telemetry against a manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--telemetry", type=Path, default=DEFAULT_TELEMETRY)
    parser.add_argument("--output", type=Path, help="Optional JSON output path.")
    args = parser.parse_args()

    result = evaluate_detector(args.manifest, args.telemetry)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                value = json.loads(line)
                if isinstance(value, dict):
                    rows.append(value)
    return rows


def _truth_positive(row: dict[str, Any]) -> bool:
    return bool(row.get("kiln_detected"))


def _predicted_positive(record: dict[str, Any]) -> bool:
    detection = record.get("detection")
    if isinstance(detection, dict) and "kiln_detected" in detection:
        return bool(detection.get("kiln_detected"))
    if "kiln_detected" in record:
        return bool(record.get("kiln_detected"))
    return record.get("action") == "TRANSMIT_ALERT" or record.get("event") == "alert"


def _confidence(record: dict[str, Any]) -> float | None:
    value = record.get("confidence")
    if value is None and isinstance(record.get("detection"), dict):
        value = record["detection"].get("confidence")
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _detector_mode(records: list[dict[str, Any]]) -> str:
    if not records:
        return "no_predictions"
    modes = {str(record.get("detector_mode", "")).lower() for record in records}
    versions = {str(record.get("detector_version", "")).lower() for record in records}
    requested = {str(record.get("requested_detector_mode", "")).lower() for record in records}
    fallback = any(record.get("fallback_used") or record.get("fallback_reason") or record.get("detector_fallback_reason") for record in records)
    if fallback:
        return "yolo_requested_baseline_fallback"
    if "yolo" in modes or any("yolo" in version for version in versions) or "yolo" in requested:
        return "yolo"
    if "baseline" in modes or any("baseline" in version for version in versions) or "baseline" in requested:
        return "baseline"
    return "unknown"


def _is_simulated(manifest_rows: list[dict[str, Any]], records: list[dict[str, Any]], detector_mode: str) -> bool:
    sample_manifest = any(str(row.get("source", "")).startswith("sample_demo") for row in manifest_rows)
    placeholder_notes = any("not ground truth" in str(row.get("notes", "")).lower() for row in manifest_rows)
    baseline = detector_mode != "yolo"
    sample_records = any(
        record.get("sample_demo_data") or record.get("simulated") or record.get("detector_is_real") is False
        for record in records
    )
    return sample_manifest or placeholder_notes or baseline or sample_records


def _warning(sample_or_placeholder: bool, missing_predictions: list[str]) -> str:
    parts: list[str] = []
    if sample_or_placeholder:
        parts.append("SIMULATED/SAMPLE evaluation; do not claim real detector accuracy.")
    if missing_predictions:
        parts.append("Some manifest rows have no telemetry prediction.")
    if not parts:
        parts.append("Real YOLO telemetry against non-sample manifest rows; still report dataset scope and license.")
    return " ".join(parts)


def _int_value(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
