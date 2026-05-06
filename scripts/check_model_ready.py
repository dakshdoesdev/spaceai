#!/usr/bin/env python
"""Check whether the real YOLO detector can be used without baseline fallback."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path


DEFAULT_MODEL_PATH = Path("models/brick_kiln_yolo.pt")


def check_model_ready(model_path: Path = DEFAULT_MODEL_PATH) -> dict:
    weights_exist = model_path.exists()
    ultralytics_available = importlib.util.find_spec("ultralytics") is not None
    ready = weights_exist and ultralytics_available

    missing: list[str] = []
    if not weights_exist:
        missing.append(f"weights not found at {model_path}")
    if not ultralytics_available:
        missing.append("ultralytics package is not installed")

    return {
        "model_path": str(model_path),
        "weights_exist": weights_exist,
        "ultralytics_available": ultralytics_available,
        "ready_for_strict_yolo": ready,
        "status": "real detector available" if ready else "real detector unavailable",
        "missing": missing,
    }


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

