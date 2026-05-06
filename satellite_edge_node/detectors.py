"""Detector routing for satellite-edge orbital passes."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from . import baseline_detector
from .baseline_detector import DetectionResult
from .yolo_detector import DEFAULT_MODEL_PATH, YoloDetector, YoloModelUnavailable


class Detector(Protocol):
    name: str

    def detect_tile(self, tile_path: Path) -> DetectionResult:
        ...


@dataclass(frozen=True)
class BaselineDetector:
    name: str = "baseline"

    def detect_tile(self, tile_path: Path) -> DetectionResult:
        return baseline_detector.detect_tile(tile_path)


def build_detector(
    mode: str = "baseline",
    *,
    model_path: Path = DEFAULT_MODEL_PATH,
    confidence_threshold: float = 0.25,
) -> Detector:
    normalized = mode.lower()
    if normalized == "baseline":
        return BaselineDetector()
    if normalized == "yolo":
        return YoloDetector(model_path=model_path, confidence_threshold=confidence_threshold)
    raise ValueError("detector mode must be 'baseline' or 'yolo'")


def build_detector_with_fallback(
    mode: str = "baseline",
    *,
    model_path: Path = DEFAULT_MODEL_PATH,
    confidence_threshold: float = 0.25,
    fallback_to_baseline: bool = False,
) -> tuple[Detector, str | None]:
    try:
        return build_detector(mode, model_path=model_path, confidence_threshold=confidence_threshold), None
    except YoloModelUnavailable as exc:
        if mode.lower() == "yolo" and fallback_to_baseline:
            return FallbackBaselineDetector(str(exc)), str(exc)
        raise


@dataclass(frozen=True)
class FallbackBaselineDetector:
    reason: str
    name: str = "fallback"

    def detect_tile(self, tile_path: Path) -> DetectionResult:
        detection = baseline_detector.detect_tile(tile_path)
        return replace(
            detection,
            detector_mode="fallback",
            detector_is_real=False,
            simulated=True,
            fallback_used=True,
            fallback_reason=self.reason,
        )
