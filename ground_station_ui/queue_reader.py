"""Read only downlinked payloads from the transmission queue."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_payloads(transmission_queue: Path) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for path in sorted(transmission_queue.glob("*.json")):
        if path.name == "telemetry.json":
            continue
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict):
            payloads.append({"_queue_file": str(path), **payload})
    return payloads


def read_telemetry(transmission_queue: Path) -> list[dict[str, Any]]:
    telemetry_path = transmission_queue / "telemetry.jsonl"
    if not telemetry_path.exists():
        return []

    records: list[dict[str, Any]] = []
    with telemetry_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            record = json.loads(line)
            if isinstance(record, dict):
                records.append(record)
    return records


def summarize_telemetry(records: list[dict[str, Any]]) -> dict[str, float | int]:
    original = sum(int(record.get("original_payload_bytes", 0)) for record in records)
    transmitted = sum(int(record.get("transmitted_payload_bytes", 0)) for record in records)
    saved = max(0, original - transmitted)
    compression_ratio = float("inf") if transmitted == 0 and original > 0 else (original / transmitted if transmitted else 1.0)
    alert_count = sum(1 for record in records if record.get("action") == "TRANSMIT_ALERT")

    return {
        "processed_tiles": len(records),
        "alerts": alert_count,
        "original_payload_bytes": original,
        "transmitted_payload_bytes": transmitted,
        "bandwidth_saved_bytes": saved,
        "compression_ratio": compression_ratio,
    }

