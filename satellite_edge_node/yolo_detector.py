"""Ultralytics YOLO detector integration for satellite-edge simulation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .baseline_detector import DetectionResult


DETECTOR_VERSION = "yolo_ultralytics:v0.1"
DEFAULT_MODEL_PATH = Path("models/brick_kiln_yolo.pt")
KILN_CLASS_NAMES = {
    "brick kiln",
    "brick-kiln",
    "brick_kiln",
    "brickkiln",
    "kiln",
}


class YoloDetectorError(RuntimeError):
    pass


class YoloModelUnavailable(YoloDetectorError):
    pass


class YoloDetector:
    """Load a local Ultralytics YOLO model and normalize results."""

    def __init__(self, model_path: Path = DEFAULT_MODEL_PATH, confidence_threshold: float = 0.25):
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        if not self.model_path.exists():
            raise YoloModelUnavailable(f"YOLO model weights not found: {self.model_path}")
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise YoloModelUnavailable(
                "ultralytics is not installed. Install it locally with `pip install ultralytics` "
                "or run the baseline detector."
            ) from exc
        try:
            self.model = YOLO(str(self.model_path))
        except Exception as exc:  # Weight loading can fail on corrupt or incompatible local files.
            raise YoloModelUnavailable(f"YOLO model could not be loaded from {self.model_path}: {exc}") from exc
        self.class_names = model_class_names(self.model)
        if not has_kiln_class(self.class_names):
            names = ", ".join(self.class_names) or "none"
            raise YoloModelUnavailable(
                f"YOLO model at {self.model_path} does not expose a brick-kiln class; classes={names}"
            )

    def detect_tile(self, tile_path: Path) -> DetectionResult:
        try:
            results = self.model.predict(str(tile_path), conf=self.confidence_threshold, verbose=False)
        except Exception as exc:  # Ultralytics raises several backend-specific exceptions.
            raise YoloDetectorError(f"YOLO inference failed for {tile_path}: {exc}") from exc

        detection = normalize_yolo_results(
            tile_id=tile_path.stem,
            results=results,
            confidence_threshold=self.confidence_threshold,
        )
        return detection


def detect_tile(
    tile_path: Path,
    model_path: Path = DEFAULT_MODEL_PATH,
    confidence_threshold: float = 0.25,
) -> DetectionResult:
    return YoloDetector(model_path=model_path, confidence_threshold=confidence_threshold).detect_tile(tile_path)


def normalize_yolo_results(
    *,
    tile_id: str,
    results: Any,
    confidence_threshold: float = 0.25,
) -> DetectionResult:
    detections = _extract_detections(results, confidence_threshold)
    if not detections:
        return DetectionResult(
            tile_id=tile_id,
            kiln_detected=False,
            confidence=0.0,
            compliance_risk="low",
            coordinates=None,
            bbox=None,
            crop_ref=None,
            signals=["yolo_no_detection"],
            detector_version=DETECTOR_VERSION,
            detector_mode="yolo",
            detector_is_real=True,
            simulated=False,
        )

    best = max(detections, key=lambda item: item["confidence"])
    confidence = float(best["confidence"])
    risk = "high" if confidence >= 0.85 else "medium"
    class_name = str(best.get("class_name") or "brick_kiln")
    return DetectionResult(
        tile_id=tile_id,
        kiln_detected=True,
        confidence=round(confidence, 4),
        compliance_risk=risk,
        coordinates=None,
        bbox=[round(float(value), 3) for value in best["bbox"]],
        crop_ref=None,
        signals=[f"yolo_detection:{class_name}", f"detections={len(detections)}"],
        detector_version=DETECTOR_VERSION,
        detector_mode="yolo",
        detector_is_real=True,
        simulated=False,
    )


def _extract_detections(results: Any, confidence_threshold: float) -> list[dict[str, Any]]:
    if results is None:
        return []
    result_items = list(results) if isinstance(results, (list, tuple)) else [results]
    detections: list[dict[str, Any]] = []
    for result in result_items:
        names = getattr(result, "names", {}) or {}
        boxes = getattr(result, "boxes", None)
        if boxes is None:
            continue
        xyxy_values = _to_python_list(getattr(boxes, "xyxy", []))
        confidence_values = _to_python_list(getattr(boxes, "conf", []))
        class_values = _to_python_list(getattr(boxes, "cls", []))
        for index, bbox in enumerate(xyxy_values):
            confidence = _safe_float(_value_at(confidence_values, index), default=0.0)
            if confidence < confidence_threshold:
                continue
            class_id = int(_safe_float(_value_at(class_values, index), default=0.0))
            class_name = _class_name_for_id(names, class_id)
            if not is_kiln_class_name(class_name):
                continue
            detections.append(
                {
                    "bbox": [float(value) for value in bbox[:4]],
                    "confidence": confidence,
                    "class_id": class_id,
                    "class_name": class_name,
                }
            )
    return detections


def model_class_names(model: Any) -> list[str]:
    names = getattr(model, "names", {}) or {}
    if isinstance(names, dict):
        return [str(value) for _, value in sorted(names.items(), key=lambda item: str(item[0]))]
    if isinstance(names, (list, tuple)):
        return [str(value) for value in names]
    return []


def has_kiln_class(names: list[str]) -> bool:
    return any(is_kiln_class_name(name) for name in names)


def is_kiln_class_name(name: Any) -> bool:
    normalized = str(name or "").strip().lower().replace("_", " ")
    normalized = " ".join(normalized.replace("-", " ").split())
    return normalized in {_normalize_class_name(value) for value in KILN_CLASS_NAMES}


def _normalize_class_name(name: str) -> str:
    return " ".join(name.lower().replace("_", " ").replace("-", " ").split())


def _class_name_for_id(names: Any, class_id: int) -> str:
    if isinstance(names, dict):
        return str(names.get(class_id, names.get(str(class_id), "")))
    if isinstance(names, (list, tuple)) and 0 <= class_id < len(names):
        return str(names[class_id])
    return ""


def _to_python_list(value: Any) -> list:
    if hasattr(value, "detach"):
        value = value.detach()
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    if hasattr(value, "tolist"):
        value = value.tolist()
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _value_at(values: list, index: int) -> Any:
    if index >= len(values):
        return None
    value = values[index]
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    return value


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
