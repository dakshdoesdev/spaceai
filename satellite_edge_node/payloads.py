"""Payload construction and bandwidth math for the satellite edge node."""

from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .baseline_detector import DetectionResult
from .liquid_vlm_reasoner import VlmReasoning
from kilnwatch.triage import TriageDecision, compute_triage


ALERT_RISKS = {"medium", "high"}
_RISK_BAND_TO_SCORE = {"high": 0.85, "medium": 0.55, "low": 0.2}


# Transmission action taken on the satellite based on the 4-tier triage decision.
# These names appear in payload `action`, telemetry `action`, and dashboard rows.
TRANSMIT_NONE = "DROP_RAW_TILE"               # IGNORE: telemetry only, no payload
TRANSMIT_JSON_ONLY = "TRANSMIT_JSON_ONLY"     # JSON_ALERT_ONLY: compact metadata, no crop
TRANSMIT_JSON_AND_CROP = "TRANSMIT_ALERT"     # CROP_OR_REVIEW: JSON + crop PNG (legacy name)
TRANSMIT_FULL_TILE = "TRANSMIT_FULL_TILE"     # FULL_DOWNLINK: JSON + crop + raw tile copy

_DECISION_TO_ACTION = {
    "IGNORE": TRANSMIT_NONE,
    "JSON_ALERT_ONLY": TRANSMIT_JSON_ONLY,
    "CROP_OR_REVIEW": TRANSMIT_JSON_AND_CROP,
    "FULL_DOWNLINK": TRANSMIT_FULL_TILE,
}

# Tiers that produce a JSON payload (anything other than IGNORE).
_TRANSMITTING_DECISIONS = {"JSON_ALERT_ONLY", "CROP_OR_REVIEW", "FULL_DOWNLINK"}
# Tiers that need a crop artifact attached.
_CROP_REQUIRED_DECISIONS = {"CROP_OR_REVIEW", "FULL_DOWNLINK"}


def triage_label(
    detection: DetectionResult,
    vlm_reasoning: VlmReasoning | None,
    *,
    min_confidence: float = 0.25,
) -> dict[str, Any]:
    """Compute the 4-tier transmission priority that drives the satellite gate.

    Decision is derived from kiln_detected + detector confidence + risk band. The
    orbital-pass path computes this before Liquid so crop-level reasoning cannot
    retroactively change what downlinks; the `vlm_reasoning` parameter remains for
    older direct callers that explicitly want to score with a reasoner band.
    """
    risk_band = (
        vlm_reasoning.compliance_risk
        if vlm_reasoning is not None and vlm_reasoning.compliance_risk in _RISK_BAND_TO_SCORE
        else detection.compliance_risk
    )
    risk_score = _RISK_BAND_TO_SCORE.get(risk_band, 0.0)
    prediction = {
        "tile_id": detection.tile_id,
        "kiln_detected": detection.kiln_detected,
        "confidence": detection.confidence,
        "compliance_risk_score": risk_score,
        "risk_factors": list(detection.signals),
    }
    triage = compute_triage(prediction, min_confidence=min_confidence)
    return {
        "decision": str(triage.decision),
        "reason": triage.reason,
        "risk_band_used": risk_band,
        "risk_score_used": risk_score,
        "driven_by": "liquid+yolo" if vlm_reasoning is not None else "yolo-only",
    }


def transmission_action_for(decision: str) -> str:
    """Map a TriageDecision string to the on-satellite transmission action."""
    return _DECISION_TO_ACTION.get(decision, TRANSMIT_NONE)


def should_transmit_triage(decision: str) -> bool:
    """True if the triage decision produces any downlink at all."""
    return decision in _TRANSMITTING_DECISIONS


def crop_required_for(decision: str) -> bool:
    """True if the triage decision requires a crop artifact alongside the JSON."""
    return decision in _CROP_REQUIRED_DECISIONS


def full_tile_required_for(decision: str) -> bool:
    """True if the triage decision sends the full source tile down the wire."""
    return decision == "FULL_DOWNLINK"


@dataclass(frozen=True)
class CropArtifact:
    path: Path | None
    size_bytes: int
    error: str | None = None


def generate_crop_file(
    tile_path: Path,
    detection: DetectionResult,
    crops_dir: Path,
    *,
    triage_decision: str | None = None,
) -> CropArtifact:
    """Generate a bbox crop iff the triage decision needs one.

    When `triage_decision` is provided, the gate is the four-tier triage. When it is
    omitted, fall back to the legacy binary `should_transmit_alert` for backward
    compatibility with older callers.
    """
    needs_crop = (
        crop_required_for(triage_decision)
        if triage_decision is not None
        else should_transmit_alert(detection)
    )
    if not needs_crop or not detection.bbox:
        return CropArtifact(path=None, size_bytes=0)
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError:
        return CropArtifact(path=None, size_bytes=0, error="Pillow is not installed; cannot generate crop")

    try:
        with Image.open(tile_path) as image:
            crop_box = _crop_box_from_bbox(detection.bbox, image.size)
            if crop_box is None:
                return CropArtifact(path=None, size_bytes=0, error=f"invalid bbox for crop: {detection.bbox}")
            crops_dir.mkdir(parents=True, exist_ok=True)
            crop_path = crops_dir / f"{detection.tile_id}_crop.png"
            image.crop(crop_box).save(crop_path, format="PNG")
            return CropArtifact(path=crop_path, size_bytes=crop_path.stat().st_size)
    except UnidentifiedImageError:
        return CropArtifact(path=None, size_bytes=0, error=f"raw tile is not a readable image: {tile_path}")
    except OSError as exc:
        return CropArtifact(path=None, size_bytes=0, error=f"crop generation failed for {tile_path}: {exc}")


@dataclass(frozen=True)
class FullTileArtifact:
    """Bytes-on-disk record for a FULL_DOWNLINK source-tile copy."""

    path: Path | None
    size_bytes: int
    error: str | None = None


def copy_full_tile(
    tile_path: Path,
    tile_id: str,
    full_tiles_dir: Path,
    *,
    triage_decision: str | None,
) -> FullTileArtifact:
    """Materialize the FULL_DOWNLINK 'send the whole tile' semantics on disk."""
    if not full_tile_required_for(triage_decision or ""):
        return FullTileArtifact(path=None, size_bytes=0)
    try:
        from shutil import copyfile

        full_tiles_dir.mkdir(parents=True, exist_ok=True)
        suffix = tile_path.suffix or ".bin"
        target = full_tiles_dir / f"{tile_id}_full{suffix}"
        copyfile(tile_path, target)
        return FullTileArtifact(path=target, size_bytes=target.stat().st_size)
    except OSError as exc:
        return FullTileArtifact(path=None, size_bytes=0, error=f"full-tile copy failed for {tile_path}: {exc}")


def should_transmit_alert(detection: DetectionResult) -> bool:
    """Legacy binary gate kept for backward compatibility.

    The runtime gate is now the 4-tier triage in `triage_label()` →
    `should_transmit_triage()`. This binary helper still answers the old question
    (medium/high risk + kiln) and is used by older payload helpers.
    """
    return detection.kiln_detected and detection.compliance_risk in ALERT_RISKS


def action_for_detection(detection: DetectionResult) -> str:
    if should_transmit_alert(detection):
        return TRANSMIT_JSON_AND_CROP
    return TRANSMIT_NONE


def build_transmission_payload(
    detection: DetectionResult,
    tile_path: Path,
    crop_artifact: CropArtifact | None = None,
    vlm_reasoning: VlmReasoning | None = None,
    *,
    triage_min_confidence: float = 0.25,
    full_tile_artifact: FullTileArtifact | None = None,
    triage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    truth = _truth_metadata(detection)
    resolved_triage = _resolved_triage(
        detection,
        vlm_reasoning,
        triage=triage,
        min_confidence=triage_min_confidence,
    )
    decision = resolved_triage["decision"]
    action = transmission_action_for(decision)

    # IGNORE — drop, no payload (this branch is normally not reached because
    # the orbital-pass loop short-circuits IGNORE before constructing a payload,
    # but kept here for callers that still build payloads for dropped tiles).
    if not should_transmit_triage(decision):
        payload = {
            "event": "dropped",
            "tile_id": detection.tile_id,
            "action": action,
            "triage_decision": decision,
            "triage": resolved_triage,
            **truth,
        }
        _attach_vlm_reasoning(payload, vlm_reasoning)
        return payload

    # JSON_ALERT_ONLY / CROP_OR_REVIEW / FULL_DOWNLINK — build alert payload.
    crop_ref = str(crop_artifact.path) if crop_artifact and crop_artifact.path else None
    crop_error = crop_artifact.error if crop_artifact else None
    full_tile_ref = (
        str(full_tile_artifact.path)
        if full_tile_artifact and full_tile_artifact.path
        else None
    )
    full_tile_error = full_tile_artifact.error if full_tile_artifact else None

    payload: dict[str, Any] = {
        "event": "alert",
        "tile_id": detection.tile_id,
        "source_tile_name": tile_path.name,
        "action": action,
        "triage_decision": decision,
        "triage": resolved_triage,
        "coordinates": detection.coordinates,
        "confidence": detection.confidence,
        "compliance_risk": detection.compliance_risk,
        "bbox": detection.bbox,
        "signals": detection.signals,
        **truth,
    }
    # Attach crop only when this tier carries crop evidence.
    if crop_required_for(decision):
        payload["crop_ref"] = crop_ref
        payload["crop_error"] = crop_error
    # Attach full-tile reference only on FULL_DOWNLINK.
    if full_tile_required_for(decision):
        payload["full_tile_ref"] = full_tile_ref
        payload["full_tile_error"] = full_tile_error

    _attach_vlm_reasoning(payload, vlm_reasoning)
    return payload


def attach_byte_accounting(
    payload: dict[str, Any],
    *,
    original_payload_bytes: int,
    json_payload_bytes: int,
    crop_payload_bytes: int,
    transmitted_payload_bytes: int,
    full_tile_payload_bytes: int = 0,
) -> None:
    payload["byte_accounting"] = {
        "original_payload_bytes": original_payload_bytes,
        "json_payload_bytes": json_payload_bytes,
        "crop_payload_bytes": crop_payload_bytes,
        "full_tile_payload_bytes": full_tile_payload_bytes,
        "transmitted_payload_bytes": transmitted_payload_bytes,
        "bandwidth_saved_bytes": bandwidth_saved_bytes(original_payload_bytes, transmitted_payload_bytes),
    }


def encoded_payload_size(payload: dict[str, Any]) -> int:
    return len(encode_payload(payload))


def encode_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compression_ratio(original_bytes: int, transmitted_bytes: int) -> float:
    if transmitted_bytes <= 0:
        return float("inf") if original_bytes > 0 else 1.0
    return original_bytes / transmitted_bytes


def bandwidth_saved_bytes(original_bytes: int, transmitted_bytes: int) -> int:
    return max(0, original_bytes - transmitted_bytes)


def telemetry_record(
    *,
    tile_path: Path,
    detection: DetectionResult,
    inference_latency_ms: float,
    original_payload_bytes: int,
    transmitted_payload_bytes: int,
    json_payload_bytes: int,
    crop_payload_bytes: int,
    crop_path: Path | None,
    crop_error: str | None,
    output_path: Path | None,
    vlm_reasoning: VlmReasoning | None = None,
    triage_min_confidence: float = 0.25,
    full_tile_payload_bytes: int = 0,
    full_tile_path: Path | None = None,
    full_tile_error: str | None = None,
    triage: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_triage = _resolved_triage(
        detection,
        vlm_reasoning,
        triage=triage,
        min_confidence=triage_min_confidence,
    )
    decision = resolved_triage["decision"]
    action = transmission_action_for(decision)
    record = {
        "tile_id": detection.tile_id,
        "tile_file": str(tile_path),
        "detector_version": detection.detector_version,
        "detector_mode": detection.detector_mode,
        "detector_is_real": detection.detector_is_real,
        "simulated": detection.simulated,
        "fallback_used": detection.fallback_used,
        "fallback_reason": detection.fallback_reason,
        "inference_latency_ms": round(inference_latency_ms, 3),
        "original_payload_bytes": original_payload_bytes,
        "json_payload_bytes": json_payload_bytes,
        "crop_payload_bytes": crop_payload_bytes,
        "full_tile_payload_bytes": full_tile_payload_bytes,
        "transmitted_payload_bytes": transmitted_payload_bytes,
        "bandwidth_saved_bytes": bandwidth_saved_bytes(original_payload_bytes, transmitted_payload_bytes),
        "compression_ratio": compression_ratio(original_payload_bytes, transmitted_payload_bytes),
        "action": action,
        "triage_decision": decision,
        "triage": resolved_triage,
        "kiln_detected": detection.kiln_detected,
        "confidence": detection.confidence,
        "compliance_risk": detection.compliance_risk,
        "output_path": str(output_path) if output_path else None,
        "crop_path": str(crop_path) if crop_path else None,
        "crop_error": crop_error,
        "full_tile_path": str(full_tile_path) if full_tile_path else None,
        "full_tile_error": full_tile_error,
        "detection": asdict(detection),
    }
    _attach_vlm_reasoning(record, vlm_reasoning)
    return record


def _truth_metadata(detection: DetectionResult) -> dict[str, Any]:
    payload = {
        "detector_mode": detection.detector_mode,
        "detector_is_real": detection.detector_is_real,
        "simulated": detection.simulated,
        "fallback_used": detection.fallback_used,
        "detector_version": detection.detector_version,
    }
    if detection.fallback_reason:
        payload["fallback_reason"] = detection.fallback_reason
    return payload


def _resolved_triage(
    detection: DetectionResult,
    vlm_reasoning: VlmReasoning | None,
    *,
    triage: dict[str, Any] | None,
    min_confidence: float,
) -> dict[str, Any]:
    if triage is not None:
        return dict(triage)
    return triage_label(detection, vlm_reasoning, min_confidence=min_confidence)


def _attach_vlm_reasoning(payload: dict[str, Any], vlm_reasoning: VlmReasoning | None) -> None:
    if vlm_reasoning is not None:
        payload["vlm_reasoning"] = vlm_reasoning.to_payload()


def _crop_box_from_bbox(bbox: list[float], image_size: tuple[int, int]) -> tuple[int, int, int, int] | None:
    width, height = image_size
    if len(bbox) == 4:
        xs = [bbox[0], bbox[2]]
        ys = [bbox[1], bbox[3]]
    elif len(bbox) == 8:
        xs = bbox[0::2]
        ys = bbox[1::2]
    else:
        return None
    left = max(0, min(width, int(min(xs))))
    upper = max(0, min(height, int(min(ys))))
    right = max(0, min(width, int(max(xs))))
    lower = max(0, min(height, int(max(ys))))
    if right <= left or lower <= upper:
        return None
    return left, upper, right, lower
