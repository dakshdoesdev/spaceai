"""Payload construction and bandwidth math for the satellite edge node."""

from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .baseline_detector import DetectionResult


ALERT_RISKS = {"medium", "high"}


@dataclass(frozen=True)
class CropArtifact:
    path: Path | None
    size_bytes: int
    error: str | None = None


def generate_crop_file(tile_path: Path, detection: DetectionResult, crops_dir: Path) -> CropArtifact:
    if not should_transmit_alert(detection) or not detection.bbox:
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


def should_transmit_alert(detection: DetectionResult) -> bool:
    return detection.kiln_detected and detection.compliance_risk in ALERT_RISKS


def action_for_detection(detection: DetectionResult) -> str:
    if should_transmit_alert(detection):
        return "TRANSMIT_ALERT"
    return "DROP_RAW_TILE"


def build_transmission_payload(
    detection: DetectionResult,
    tile_path: Path,
    crop_artifact: CropArtifact | None = None,
) -> dict[str, Any]:
    truth = _truth_metadata(detection)
    if not should_transmit_alert(detection):
        return {
            "event": "dropped",
            "tile_id": detection.tile_id,
            "action": "DROP_RAW_TILE",
            **truth,
        }

    crop_ref = str(crop_artifact.path) if crop_artifact and crop_artifact.path else None
    crop_error = crop_artifact.error if crop_artifact else None
    return {
        "event": "alert",
        "tile_id": detection.tile_id,
        "source_tile_name": tile_path.name,
        "coordinates": detection.coordinates,
        "confidence": detection.confidence,
        "compliance_risk": detection.compliance_risk,
        "bbox": detection.bbox,
        "crop_ref": crop_ref,
        "crop_error": crop_error,
        "signals": detection.signals,
        **truth,
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
    output_path: Path,
) -> dict[str, Any]:
    return {
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
        "transmitted_payload_bytes": transmitted_payload_bytes,
        "bandwidth_saved_bytes": bandwidth_saved_bytes(original_payload_bytes, transmitted_payload_bytes),
        "compression_ratio": compression_ratio(original_payload_bytes, transmitted_payload_bytes),
        "action": action_for_detection(detection),
        "kiln_detected": detection.kiln_detected,
        "confidence": detection.confidence,
        "compliance_risk": detection.compliance_risk,
        "output_path": str(output_path),
        "crop_path": str(crop_path) if crop_path else None,
        "crop_error": crop_error,
        "detection": asdict(detection),
    }


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
