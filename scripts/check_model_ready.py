#!/usr/bin/env python
"""Check whether the real YOLO detector can be used without baseline fallback."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from satellite_edge_node.yolo_detector import has_kiln_class, model_class_names


DEFAULT_MODEL_PATH = Path("models/brick_kiln_yolo.pt")


def check_model_ready(model_path: Path = DEFAULT_MODEL_PATH) -> dict:
    weights_exist = model_path.exists()
    ultralytics_available = importlib.util.find_spec("ultralytics") is not None
    model_loads = False
    class_names: list[str] = []
    kiln_class_available = False
    load_error: str | None = None

    missing: list[str] = []
    if not weights_exist:
        missing.append(f"weights not found at {model_path}")
    if not ultralytics_available:
        missing.append("ultralytics package is not installed")

    if weights_exist and ultralytics_available:
        try:
            from ultralytics import YOLO

            model = YOLO(str(model_path))
            class_names = model_class_names(model)
            kiln_class_available = has_kiln_class(class_names)
            model_loads = True
        except Exception as exc:
            load_error = str(exc)
            missing.append(f"model failed to load: {exc}")
    if model_loads and not kiln_class_available:
        missing.append("model has no explicit brick-kiln/kiln class")

    ready = weights_exist and ultralytics_available and model_loads and kiln_class_available

    return {
        "model_path": str(model_path),
        "weights_exist": weights_exist,
        "ultralytics_available": ultralytics_available,
        "model_loads": model_loads,
        "model_sha256": _sha256(model_path) if weights_exist else None,
        "class_names": class_names,
        "kiln_class_available": kiln_class_available,
        "ready_for_strict_yolo": ready,
        "status": "real detector available" if ready else "real detector unavailable",
        "missing": missing,
        "load_error": load_error,
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Check KilnWatch YOLO detector readiness.")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    result = check_model_ready(args.model_path)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif result["ready_for_strict_yolo"]:
        print(f"real detector available: {result['model_path']}")
    else:
        print(f"real detector unavailable: {', '.join(result['missing'])}")
    return 0 if result["ready_for_strict_yolo"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
