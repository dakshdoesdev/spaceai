"""Transparent placeholder detector for satellite-edge simulation.

This is not a trained model. It reads optional local sidecar metadata or simple
filename hints so the architecture can be exercised before a Liquid VLM or
object detector is wired in.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DETECTOR_VERSION = "baseline_detector:v0.1"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bin", ".tile", ".txt"}


@dataclass(frozen=True)
class DetectionResult:
    tile_id: str
    kiln_detected: bool
    confidence: float
    compliance_risk: str
    coordinates: dict[str, float] | None
    bbox: list[float] | None
    crop_ref: str | None
    signals: list[str]
    detector_version: str = DETECTOR_VERSION
    detector_mode: str = "baseline"
    detector_is_real: bool = False
    simulated: bool = True
    fallback_used: bool = False
    fallback_reason: str | None = None


def detect_tile(tile_path: Path) -> DetectionResult:
    """Return a deterministic placeholder detection for one raw tile."""
    metadata = _read_sidecar(tile_path)
    if metadata:
        return _from_metadata(tile_path, metadata)
    return _from_filename(tile_path)


def is_tile_file(path: Path) -> bool:
    return path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS and not path.name.endswith(".meta.json")


def _read_sidecar(tile_path: Path) -> dict[str, Any]:
    sidecar = tile_path.with_suffix(tile_path.suffix + ".meta.json")
    if not sidecar.exists():
        return {}
    with sidecar.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"sidecar metadata must be a JSON object: {sidecar}")
    return value


def _from_metadata(tile_path: Path, metadata: dict[str, Any]) -> DetectionResult:
    risk = str(metadata.get("compliance_risk", "low")).lower()
    if risk not in {"low", "medium", "high"}:
        risk = "low"

    coordinates = metadata.get("coordinates")
    if not _valid_coordinates(coordinates):
        coordinates = None

    signals = metadata.get("signals", [])
    if not isinstance(signals, list):
        signals = []

    return DetectionResult(
        tile_id=str(metadata.get("tile_id") or tile_path.stem),
        kiln_detected=bool(metadata.get("kiln_detected", False)),
        confidence=_clamp_float(metadata.get("confidence", 0.0)),
        compliance_risk=risk,
        coordinates=coordinates,
        bbox=_valid_bbox(metadata.get("bbox")),
        crop_ref=metadata.get("crop_ref") if isinstance(metadata.get("crop_ref"), str) else None,
        signals=[str(signal) for signal in signals[:5]],
    )


def _from_filename(tile_path: Path) -> DetectionResult:
    name = tile_path.stem.lower()
    kiln_detected = any(token in name for token in ("kiln", "brick", "risk", "positive"))
    high_risk = any(token in name for token in ("high", "settlement", "active"))
    medium_risk = any(token in name for token in ("medium", "possible", "cluster"))

    if high_risk:
        risk = "high"
        confidence = 0.74
    elif kiln_detected or medium_risk:
        risk = "medium" if kiln_detected else "low"
        confidence = 0.62 if kiln_detected else 0.3
    else:
        risk = "low"
        confidence = 0.08

    return DetectionResult(
        tile_id=tile_path.stem,
        kiln_detected=kiln_detected,
        confidence=confidence,
        compliance_risk=risk,
        coordinates=None,
        bbox=None,
        crop_ref=None,
        signals=["filename_hint"] if kiln_detected else [],
    )


def _valid_coordinates(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    lat = value.get("lat")
    lon = value.get("lon")
    return isinstance(lat, (int, float)) and isinstance(lon, (int, float))


def _valid_bbox(value: Any) -> list[float] | None:
    if not isinstance(value, list) or len(value) not in {4, 5, 8}:
        return None
    try:
        return [float(item) for item in value]
    except (TypeError, ValueError):
        return None


def _clamp_float(value: Any) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return 0.0
    return min(1.0, max(0.0, parsed))
