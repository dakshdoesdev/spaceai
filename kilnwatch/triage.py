"""Bandwidth-aware triage for the KilnWatch demo."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class TriageDecision(StrEnum):
    IGNORE = "IGNORE"
    JSON_ALERT_ONLY = "JSON_ALERT_ONLY"
    CROP_OR_REVIEW = "CROP_OR_REVIEW"
    FULL_DOWNLINK = "FULL_DOWNLINK"


@dataclass(frozen=True)
class BandwidthEstimate:
    raw_tile_mb: float
    crop_mb: float
    json_alert_kb: float
    chosen_payload_mb: float
    savings_percent: float


@dataclass(frozen=True)
class TriageResult:
    decision: TriageDecision
    reason: str
    confidence: float
    risk_score: float
    kiln_detected: bool
    bandwidth: BandwidthEstimate
    alert: str


def risk_band(risk_score: float) -> str:
    if risk_score >= 0.75:
        return "high"
    if risk_score >= 0.45:
        return "medium"
    return "low"


def compute_triage(prediction: dict[str, Any]) -> TriageResult:
    """Convert model output into a satellite-side downlink decision."""
    detection = _primary_detection(prediction)
    confidence = _as_float(detection.get("confidence", prediction.get("confidence", 0.0)))
    risk_score = _as_float(prediction.get("compliance_risk_score", prediction.get("risk_score", 0.0)))
    kiln_detected = bool(detection.get("kiln_detected", prediction.get("kiln_detected", False)))

    if not kiln_detected or confidence < 0.45:
        decision = TriageDecision.IGNORE
        reason = "No kiln or low-confidence kiln signal."
    elif confidence >= 0.85 and risk_score >= 0.75:
        decision = TriageDecision.FULL_DOWNLINK
        reason = "High-confidence kiln with high compliance risk."
    elif risk_score >= 0.45:
        decision = TriageDecision.CROP_OR_REVIEW
        reason = "Kiln detected with medium/high risk; send crop or queue analyst review."
    else:
        decision = TriageDecision.JSON_ALERT_ONLY
        reason = "Kiln likely, but risk is low enough for compact metadata alert only."

    bandwidth = estimate_bandwidth(decision, prediction)
    alert = build_alert(prediction, decision, confidence, risk_score, reason)
    return TriageResult(
        decision=decision,
        reason=reason,
        confidence=confidence,
        risk_score=risk_score,
        kiln_detected=kiln_detected,
        bandwidth=bandwidth,
        alert=alert,
    )


def estimate_bandwidth(decision: TriageDecision, prediction: dict[str, Any]) -> BandwidthEstimate:
    estimates = prediction.get("bandwidth_estimate", {})
    raw_tile_mb = _as_float(estimates.get("raw_tile_mb", 12.0))
    crop_mb = _as_float(estimates.get("crop_mb", 1.2))
    json_alert_kb = _as_float(estimates.get("json_alert_kb", 4.0))

    if decision == TriageDecision.FULL_DOWNLINK:
        chosen_payload_mb = raw_tile_mb
    elif decision == TriageDecision.CROP_OR_REVIEW:
        chosen_payload_mb = crop_mb
    elif decision == TriageDecision.JSON_ALERT_ONLY:
        chosen_payload_mb = json_alert_kb / 1024
    else:
        chosen_payload_mb = 0.0

    savings_percent = 100.0 if raw_tile_mb <= 0 else max(0.0, (1 - chosen_payload_mb / raw_tile_mb) * 100)
    return BandwidthEstimate(
        raw_tile_mb=raw_tile_mb,
        crop_mb=crop_mb,
        json_alert_kb=json_alert_kb,
        chosen_payload_mb=chosen_payload_mb,
        savings_percent=savings_percent,
    )


def build_alert(
    prediction: dict[str, Any],
    decision: TriageDecision,
    confidence: float,
    risk_score: float,
    reason: str,
) -> str:
    tile_id = prediction.get("tile_id", "unknown-tile")
    location = prediction.get("location", {})
    lat = location.get("lat")
    lon = location.get("lon")
    coords = f" near {lat:.5f}, {lon:.5f}" if isinstance(lat, int | float) and isinstance(lon, int | float) else ""
    signals = prediction.get("risk_factors", [])
    signal_text = ", ".join(signals[:3]) if signals else "visual kiln indicators"
    return (
        f"{decision}: {tile_id}{coords}. "
        f"Kiln confidence {confidence:.0%}; compliance risk {risk_score:.0%} ({risk_band(risk_score)}). "
        f"Signals: {signal_text}. {reason}"
    )


def _primary_detection(prediction: dict[str, Any]) -> dict[str, Any]:
    detections = prediction.get("detections")
    if isinstance(detections, list) and detections:
        kiln_detections = [d for d in detections if isinstance(d, dict) and d.get("class") in {"kiln", "brick_kiln"}]
        if kiln_detections:
            return max(kiln_detections, key=lambda d: _as_float(d.get("confidence", 0.0)))
    return prediction


def _as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0

