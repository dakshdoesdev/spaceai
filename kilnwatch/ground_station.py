"""Ground-station telemetry loading and bandwidth accounting."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


TRANSMISSION_QUEUE_DIR = Path("transmission_queue")
TELEMETRY_LOG_DIR = Path("telemetry_logs")
ALT_TELEMETRY_LOG_DIR = Path("telemetry")
REVIEW_DECISIONS = {"CROP_OR_REVIEW", "FULL_DOWNLINK"}
CROP_REFERENCE_FIELDS = ("crop_ref", "crop_path", "payload_uri")
NO_REAL_CROP_AVAILABLE = "no real crop available"
FORBIDDEN_CROP_SOURCE_FRAGMENTS = (
    "data/raw_tiles",
    "data/final_demo_tiles",
    "datasets/roboflow",
)


@dataclass(frozen=True)
class MissionMetrics:
    tiles_processed: int
    raw_bytes_processed: int
    downlinked_bytes: int
    bytes_saved: int
    bandwidth_saved_percent: float
    compression_ratio: float
    ignored_tiles: int
    json_alerts: int
    crop_or_full_review_alerts: int
    average_latency_ms: float


@dataclass(frozen=True)
class ProofStatus:
    detector_label: str
    reasoner_label: str
    truth_fields: dict[str, Any]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class MissionProofCounts:
    detections: int
    crops_generated: int


@dataclass(frozen=True)
class CropEvidence:
    tile_id: str
    available: bool
    path: Path | None
    message: str
    source_field: str | None = None


def load_ground_station_records(
    queue_dir: Path = TRANSMISSION_QUEUE_DIR,
    telemetry_dir: Path = TELEMETRY_LOG_DIR,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    """Load payloads and telemetry from ground-station-visible folders only."""
    payloads = _load_payloads(queue_dir)
    telemetry_events = [*_load_telemetry_events(queue_dir, include_json=False), *_load_telemetry_events(telemetry_dir)]
    if not telemetry_events and telemetry_dir == TELEMETRY_LOG_DIR:
        telemetry_events = _load_telemetry_events(ALT_TELEMETRY_LOG_DIR)

    has_real_records = any(not item.get("sample_demo_data") for item in [*payloads, *telemetry_events])
    if has_real_records:
        payloads = [payload for payload in payloads if not payload.get("sample_demo_data")]
        telemetry_events = [event for event in telemetry_events if not event.get("sample_demo_data")]

    sample_data = bool(payloads or telemetry_events) and all(
        item.get("sample_demo_data") for item in [*payloads, *telemetry_events]
    )
    return payloads, telemetry_events, sample_data


def calculate_metrics(events: list[dict[str, Any]]) -> MissionMetrics:
    raw_bytes_processed = sum(_raw_bytes(event) for event in events)
    downlinked_bytes = sum(_downlinked_bytes(event) for event in events)
    bytes_saved = max(0, raw_bytes_processed - downlinked_bytes)
    bandwidth_saved_percent = 0.0 if raw_bytes_processed <= 0 else (bytes_saved / raw_bytes_processed) * 100
    compression_ratio = (raw_bytes_processed / downlinked_bytes) if downlinked_bytes else float("inf")
    ignored_tiles = sum(1 for event in events if _decision(event) == "IGNORE")
    json_alerts = sum(1 for event in events if _decision(event) == "JSON_ALERT_ONLY")
    crop_or_full_review_alerts = sum(1 for event in events if _decision(event) in REVIEW_DECISIONS)
    latencies = [_as_float(event.get("inference_latency_ms")) for event in events if event.get("inference_latency_ms") is not None]
    average_latency_ms = sum(latencies) / len(latencies) if latencies else 0.0
    return MissionMetrics(
        tiles_processed=len(events),
        raw_bytes_processed=raw_bytes_processed,
        downlinked_bytes=downlinked_bytes,
        bytes_saved=bytes_saved,
        bandwidth_saved_percent=bandwidth_saved_percent,
        compression_ratio=compression_ratio,
        ignored_tiles=ignored_tiles,
        json_alerts=json_alerts,
        crop_or_full_review_alerts=crop_or_full_review_alerts,
        average_latency_ms=average_latency_ms,
    )


def cumulative_series(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_total = 0
    downlink_total = 0
    rows: list[dict[str, Any]] = []
    for index, event in enumerate(events, start=1):
        raw_total += _raw_bytes(event)
        downlink_total += _downlinked_bytes(event)
        rows.append(
            {
                "event": index,
                "tile_id": event.get("tile_id", f"event-{index}"),
                "Raw bytes processed in orbit": raw_total,
                "Bytes downlinked": downlink_total,
            }
        )
    return rows


def received_alert_rows(payloads: list[dict[str, Any]], events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_tile = {payload.get("tile_id"): payload for payload in payloads}
    rows: list[dict[str, Any]] = []
    for event in events:
        decision = _decision(event)
        if decision == "IGNORE":
            continue
        payload = by_tile.get(event.get("tile_id"), {})
        rows.append(
            {
                "received_at": event.get("timestamp_utc", ""),
                "tile_id": event.get("tile_id", ""),
                "decision": decision,
                "payload_type": payload.get("payload_type", event.get("payload_type", "")),
                "downlinked": format_bytes(_downlinked_bytes(event)),
                "confidence": _as_percent(payload.get("confidence", event.get("confidence"))),
                "risk": _risk_label(payload, event),
                "alert": payload.get("alert", event.get("alert", "")),
            }
        )
    return rows


def safe_review_payloads(payloads: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only payloads allowed to reference imagery at the ground station."""
    return [payload for payload in payloads if _decision(payload) in REVIEW_DECISIONS]


def proof_status_summary(
    payloads: list[dict[str, Any]],
    events: list[dict[str, Any]],
    sample_data: bool = False,
) -> ProofStatus:
    items = [*payloads, *events]
    truth_fields = _truth_fields(items)
    detector_label = _detector_label(items, sample_data=sample_data)
    reasoner_label = _reasoner_label(items)
    notes = ("SAMPLE DATA",) if sample_data else ()
    return ProofStatus(
        detector_label=detector_label,
        reasoner_label=reasoner_label,
        truth_fields=truth_fields,
        notes=notes,
    )


def mission_proof_counts(
    payloads: list[dict[str, Any]],
    events: list[dict[str, Any]],
    queue_dir: Path = TRANSMISSION_QUEUE_DIR,
) -> MissionProofCounts:
    items = [*payloads, *events]
    detections = sum(1 for item in items if _is_detection(item))
    crops_generated = sum(1 for evidence in resolve_crop_evidence(payloads, events, queue_dir) if evidence.available)
    return MissionProofCounts(detections=detections, crops_generated=crops_generated)


def resolve_crop_evidence(
    payloads: list[dict[str, Any]],
    events: list[dict[str, Any]] | None = None,
    queue_dir: Path = TRANSMISSION_QUEUE_DIR,
) -> list[CropEvidence]:
    by_tile = {payload.get("tile_id"): payload for payload in payloads}
    review_items = list(safe_review_payloads(payloads))
    for event in events or []:
        if _decision(event) not in REVIEW_DECISIONS:
            continue
        if event.get("tile_id") not in by_tile:
            review_items.append(event)

    evidence: list[CropEvidence] = []
    for item in review_items:
        tile_id = str(item.get("tile_id") or "unknown")
        source_field, raw_value = _crop_reference(item)
        if raw_value is None:
            evidence.append(CropEvidence(tile_id, False, None, NO_REAL_CROP_AVAILABLE, source_field))
            continue
        crop_path = _safe_crop_path(raw_value, queue_dir)
        if crop_path is None or not crop_path.is_file() or crop_path.stat().st_size <= 0:
            evidence.append(CropEvidence(tile_id, False, None, NO_REAL_CROP_AVAILABLE, source_field))
            continue
        evidence.append(CropEvidence(tile_id, True, crop_path, str(crop_path), source_field))
    return evidence


def detector_modes(payloads: list[dict[str, Any]], events: list[dict[str, Any]]) -> set[str]:
    modes: set[str] = set()
    for item in [*payloads, *events]:
        metadata = item.get("detector_metadata")
        if isinstance(metadata, dict):
            modes.add(str(metadata.get("mode") or metadata.get("detector_type") or "").lower())
        detection = item.get("detection")
        if isinstance(detection, dict):
            modes.add(str(detection.get("detector_version", "")).lower())
        modes.add(str(item.get("detector_version", "")).lower())
        modes.add(str(item.get("detector_mode", "")).lower())
    return {mode for mode in modes if mode}


def reasoner_statuses(payloads: list[dict[str, Any]], events: list[dict[str, Any]]) -> set[str]:
    statuses: set[str] = set()
    for item in [*payloads, *events]:
        reasoning = item.get("vlm_reasoning")
        if not isinstance(reasoning, dict):
            continue
        mode = str(reasoning.get("reasoner_mode") or "").lower()
        is_real = bool(reasoning.get("reasoner_is_real"))
        if is_real:
            statuses.add("liquid-real")
        elif mode == "liquid-mock":
            statuses.add("liquid-mock")
        elif mode:
            statuses.add(mode)
    if not statuses:
        statuses.add("disabled")
    return statuses


def display_decision(item: dict[str, Any]) -> str:
    return _decision(item)


def event_downlinked_bytes(event: dict[str, Any]) -> int:
    return _downlinked_bytes(event)


def format_bytes(value: int) -> str:
    units = ["B", "KB", "MB", "GB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{size:.1f} GB"


def _load_payloads(queue_dir: Path) -> list[dict[str, Any]]:
    if not queue_dir.exists():
        return []
    payloads: list[dict[str, Any]] = []
    for path in sorted(queue_dir.glob("*.json")):
        payload = _read_json(path)
        if payload:
            payload["_source_file"] = str(path)
            payloads.append(payload)
    return payloads


def _load_telemetry_events(telemetry_dir: Path, include_json: bool = True) -> list[dict[str, Any]]:
    if not telemetry_dir.exists():
        return []
    events: list[dict[str, Any]] = []
    for path in sorted(telemetry_dir.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    event = json.loads(line)
                    event["_source_file"] = str(path)
                    events.append(event)
    if include_json:
        for path in sorted(telemetry_dir.glob("*.json")):
            loaded = _read_json(path)
            if isinstance(loaded, list):
                events.extend(loaded)
            elif loaded:
                events.append(loaded)
    return sorted(events, key=lambda event: event.get("timestamp_utc", ""))


def _read_json(path: Path) -> dict[str, Any] | list[dict[str, Any]] | None:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _decision(item: dict[str, Any]) -> str:
    explicit = item.get("triage_decision") or item.get("decision")
    if explicit:
        return str(explicit)
    if item.get("action") == "DROP_RAW_TILE" or item.get("event") == "dropped":
        return "IGNORE"
    if item.get("action") == "TRANSMIT_ALERT" or item.get("event") == "alert":
        risk = str(item.get("compliance_risk", "")).lower()
        confidence = _as_float(item.get("confidence"))
        if risk == "high" and confidence >= 0.85:
            return "FULL_DOWNLINK"
        return "CROP_OR_REVIEW"
    return ""


def _truth_fields(items: list[dict[str, Any]]) -> dict[str, Any]:
    keys = (
        "detector_mode",
        "detector_is_real",
        "simulated",
        "fallback_used",
        "fallback_reason",
        "detector_version",
        "model_path",
        "model_name",
        "confidence_threshold",
    )
    fields: dict[str, Any] = {}
    for key in keys:
        values = [item.get(key) for item in items if item.get(key) is not None]
        if values:
            fields[key] = values[0] if len(set(map(str, values))) == 1 else values
    reasoning_fields = _reasoner_truth_fields(items)
    if reasoning_fields:
        fields["vlm_reasoning"] = reasoning_fields
    return fields


def _reasoner_truth_fields(items: list[dict[str, Any]]) -> dict[str, Any]:
    keys = ("reasoner_mode", "reasoner_is_real", "model_name")
    fields: dict[str, Any] = {}
    reasonings = [item.get("vlm_reasoning") for item in items if isinstance(item.get("vlm_reasoning"), dict)]
    for key in keys:
        values = [reasoning.get(key) for reasoning in reasonings if reasoning.get(key) is not None]
        if values:
            fields[key] = values[0] if len(set(map(str, values))) == 1 else values
    return fields


def _detector_label(items: list[dict[str, Any]], *, sample_data: bool) -> str:
    if sample_data:
        return "SAMPLE DATA"
    if any(bool(item.get("fallback_used")) for item in items):
        return "FALLBACK USED"
    modes = detector_modes([], items)
    if any("yolo" in mode for mode in modes) and any(bool(item.get("detector_is_real")) for item in items):
        return "STRICT YOLO REAL"
    if any(bool(item.get("simulated")) for item in items) or any(
        "baseline" in mode or "placeholder" in mode for mode in modes
    ):
        return "BASELINE SIMULATION"
    return "DETECTOR METADATA UNKNOWN"


def _reasoner_label(items: list[dict[str, Any]]) -> str:
    statuses = reasoner_statuses([], items)
    if "liquid-real" in statuses:
        return "LIQUID LFM REAL"
    if "liquid-mock" in statuses:
        return "LIQUID MOCK"
    return "LFM DISABLED"


def _is_detection(item: dict[str, Any]) -> bool:
    if item.get("kiln_detected") is True:
        return True
    if _decision(item) in REVIEW_DECISIONS or _decision(item) == "JSON_ALERT_ONLY":
        return True
    return item.get("action") == "TRANSMIT_ALERT" or item.get("event") == "alert"


def _crop_reference(item: dict[str, Any]) -> tuple[str | None, str | None]:
    for field in CROP_REFERENCE_FIELDS:
        value = item.get(field)
        if value:
            return field, str(value)
    return None, None


def _safe_crop_path(value: str, queue_dir: Path) -> Path | None:
    normalized_value = value.replace("\\", "/")
    if normalized_value.endswith(".tile"):
        return None
    if any(fragment in normalized_value for fragment in FORBIDDEN_CROP_SOURCE_FRAGMENTS):
        return None

    queue_root = queue_dir.resolve()
    raw_path = Path(value)
    if raw_path.is_absolute():
        candidate = raw_path
    elif raw_path.parts and raw_path.parts[0] == queue_dir.name:
        candidate = raw_path
    else:
        candidate = queue_dir / raw_path
    resolved = candidate.resolve()
    try:
        resolved.relative_to(queue_root)
    except ValueError:
        return None
    return resolved


def _raw_bytes(event: dict[str, Any]) -> int:
    return _as_int(event.get("raw_bytes_processed", event.get("original_payload_bytes")))


def _downlinked_bytes(event: dict[str, Any]) -> int:
    return _as_int(event.get("downlinked_bytes", event.get("transmitted_payload_bytes")))


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _as_percent(value: Any) -> str:
    numeric = _as_float(value)
    return f"{numeric:.0%}" if numeric <= 1 else f"{numeric:.0f}%"


def _risk_label(payload: dict[str, Any], event: dict[str, Any]) -> str:
    risk_score = payload.get("compliance_risk_score", event.get("compliance_risk_score"))
    if risk_score is not None:
        return _as_percent(risk_score)
    risk_band = payload.get("compliance_risk", event.get("compliance_risk"))
    return str(risk_band or "")
