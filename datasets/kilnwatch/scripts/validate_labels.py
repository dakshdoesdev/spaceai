#!/usr/bin/env python3
"""Validate KilnWatch JSONL label files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


DATASET_ROOT = Path(__file__).resolve().parents[1]

ALLOWED_SPLITS = {"train", "dev", "test", "seed"}
COUNT_BUCKETS = {"0", "1-3", "4-10", "10+"}
ACTIVITY_SIGNALS = {"active", "dormant", "unclear"}
RISK_LEVELS = {"low", "medium", "high"}
REQUIRED_LABEL_FIELDS = {
    "kiln_detected",
    "kiln_count_estimate",
    "activity_signal",
    "near_settlement",
    "compliance_risk",
    "confidence",
}


class ValidationError:
    def __init__(self, file_path: Path, line_number: int, message: str) -> None:
        self.file_path = file_path
        self.line_number = line_number
        self.message = message

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number}: {self.message}"


def load_jsonl(path: Path) -> tuple[list[dict[str, Any]], list[ValidationError]]:
    rows: list[dict[str, Any]] = []
    errors: list[ValidationError] = []

    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                errors.append(ValidationError(path, line_number, "blank lines are not allowed in JSONL"))
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(ValidationError(path, line_number, f"invalid JSON: {exc.msg}"))
                continue
            if not isinstance(parsed, dict):
                errors.append(ValidationError(path, line_number, "row must be a JSON object"))
                continue
            rows.append({"__line_number": line_number, "__file_path": path, **parsed})

    return rows, errors


def validate_row(row: dict[str, Any], check_images: bool) -> list[ValidationError]:
    path = row["__file_path"]
    line_number = row["__line_number"]
    errors: list[ValidationError] = []

    def err(message: str) -> None:
        errors.append(ValidationError(path, line_number, message))

    for field in ("tile_id", "image_path", "split", "label"):
        if field not in row:
            err(f"missing required field: {field}")

    tile_id = row.get("tile_id")
    if not isinstance(tile_id, str) or not tile_id:
        err("tile_id must be a non-empty string")
    elif not all(char.islower() or char.isdigit() or char in "_-" for char in tile_id):
        err("tile_id should use lowercase letters, numbers, '_' or '-'")

    image_path = row.get("image_path")
    if not isinstance(image_path, str) or not image_path:
        err("image_path must be a non-empty string")
    elif Path(image_path).is_absolute() or ".." in Path(image_path).parts:
        err("image_path must be relative to datasets/kilnwatch and must not contain '..'")
    elif check_images and not (DATASET_ROOT / image_path).is_file():
        err(f"image_path does not exist: {DATASET_ROOT / image_path}")

    split = row.get("split")
    if split not in ALLOWED_SPLITS:
        err(f"split must be one of {sorted(ALLOWED_SPLITS)}")
    elif isinstance(image_path, str) and split != "seed":
        expected_prefix = f"images/{split}/"
        if not image_path.startswith(expected_prefix):
            err(f"image_path for split '{split}' should start with '{expected_prefix}'")

    label = row.get("label")
    if not isinstance(label, dict):
        err("label must be an object")
        return errors

    missing = REQUIRED_LABEL_FIELDS - set(label)
    extra = set(label) - REQUIRED_LABEL_FIELDS
    if missing:
        err(f"label missing fields: {sorted(missing)}")
    if extra:
        err(f"label has unsupported fields: {sorted(extra)}")

    kiln_detected = label.get("kiln_detected")
    count = label.get("kiln_count_estimate")
    activity = label.get("activity_signal")
    near_settlement = label.get("near_settlement")
    risk = label.get("compliance_risk")
    confidence = label.get("confidence")

    if not isinstance(kiln_detected, bool):
        err("label.kiln_detected must be true or false")
    if count not in COUNT_BUCKETS:
        err(f"label.kiln_count_estimate must be one of {sorted(COUNT_BUCKETS)}")
    if activity not in ACTIVITY_SIGNALS:
        err(f"label.activity_signal must be one of {sorted(ACTIVITY_SIGNALS)}")
    if not isinstance(near_settlement, bool):
        err("label.near_settlement must be true or false")
    if risk not in RISK_LEVELS:
        err(f"label.compliance_risk must be one of {sorted(RISK_LEVELS)}")
    if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
        err("label.confidence must be a number from 0 to 1")
    elif not 0 <= confidence <= 1:
        err("label.confidence must be between 0 and 1 inclusive")

    if isinstance(kiln_detected, bool) and count in COUNT_BUCKETS:
        if not kiln_detected and count != "0":
            err("kiln_detected=false requires kiln_count_estimate='0'")
        if kiln_detected and count == "0":
            err("kiln_detected=true requires a nonzero kiln_count_estimate")

    notes = row.get("notes", "")
    has_notes = isinstance(notes, str) and bool(notes.strip())
    if kiln_detected is False and activity != "unclear" and not has_notes:
        err("negative samples should use activity_signal='unclear' unless notes explain otherwise")
    if kiln_detected is False and risk == "high":
        err("compliance_risk='high' is not allowed when kiln_detected=false")
    if risk == "high" and kiln_detected is True:
        escalation = activity == "active" or near_settlement is True or count in {"4-10", "10+"}
        if not escalation:
            err("high risk positives need active signal, near_settlement=true, or count bucket 4-10/10+")

    return errors


def validate_files(paths: list[Path], check_images: bool) -> list[ValidationError]:
    errors: list[ValidationError] = []
    seen_tile_ids: dict[str, tuple[Path, int]] = {}

    for path in paths:
        rows, load_errors = load_jsonl(path)
        errors.extend(load_errors)
        for row in rows:
            errors.extend(validate_row(row, check_images))
            tile_id = row.get("tile_id")
            if isinstance(tile_id, str):
                previous = seen_tile_ids.get(tile_id)
                if previous:
                    prev_path, prev_line = previous
                    errors.append(
                        ValidationError(
                            row["__file_path"],
                            row["__line_number"],
                            f"duplicate tile_id also seen at {prev_path}:{prev_line}",
                        )
                    )
                else:
                    seen_tile_ids[tile_id] = (row["__file_path"], row["__line_number"])

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jsonl", nargs="+", type=Path, help="JSONL files to validate")
    parser.add_argument("--check-images", action="store_true", help="require referenced image files to exist")
    args = parser.parse_args()

    errors = validate_files(args.jsonl, args.check_images)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        print(f"FAILED: {len(errors)} validation error(s)", file=sys.stderr)
        return 1

    print(f"OK: validated {len(args.jsonl)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
