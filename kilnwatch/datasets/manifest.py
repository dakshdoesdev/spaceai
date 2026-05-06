from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from kilnwatch.datasets.image_validation import ImageValidationError, validate_readable_image


REQUIRED_FIELDS = {
    "tile_id",
    "image_path",
    "lat",
    "lon",
    "source",
    "split",
    "label",
    "kiln_detected",
    "notes",
}

ALLOWED_SPLITS = {"train", "dev", "val", "test", "seed", "unlabeled", "demo", "external"}


@dataclass(frozen=True)
class ManifestIssue:
    line_number: int
    message: str


def validate_manifest_row(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - row.keys())
    if missing:
        errors.append(f"missing required fields: {', '.join(missing)}")

    if "tile_id" in row and not isinstance(row["tile_id"], str):
        errors.append("tile_id must be a string")
    if "image_path" in row and not isinstance(row["image_path"], str):
        errors.append("image_path must be a string")
    if "source" in row and not isinstance(row["source"], str):
        errors.append("source must be a string")
    if "label" in row and not isinstance(row["label"], str):
        errors.append("label must be a string")
    if "notes" in row and not isinstance(row["notes"], str):
        errors.append("notes must be a string")
    if "kiln_detected" in row and not isinstance(row["kiln_detected"], bool):
        errors.append("kiln_detected must be true or false")
    if "split" in row and row["split"] not in ALLOWED_SPLITS:
        errors.append(f"split must be one of {sorted(ALLOWED_SPLITS)}")

    for field in ("lat", "lon"):
        if field in row and not isinstance(row[field], int | float):
            errors.append(f"{field} must be numeric")
    if isinstance(row.get("lat"), int | float) and not -90 <= row["lat"] <= 90:
        errors.append("lat must be between -90 and 90")
    if isinstance(row.get("lon"), int | float) and not -180 <= row["lon"] <= 180:
        errors.append("lon must be between -180 and 180")

    if "bbox" in row and row["bbox"] is not None:
        bbox = row["bbox"]
        if not isinstance(bbox, list) or len(bbox) not in {4, 5, 8}:
            errors.append("bbox must be null or a list of 4, 5, or 8 numeric values")
        elif not all(isinstance(value, int | float) for value in bbox):
            errors.append("bbox values must be numeric")

    if "confidence" in row and row["confidence"] is not None:
        confidence = row["confidence"]
        if not isinstance(confidence, int | float) or not 0 <= confidence <= 1:
            errors.append("confidence must be null or a number between 0 and 1")

    if row.get("source") == "sample_demo_not_ground_truth":
        notes = str(row.get("notes", "")).lower()
        if "not ground truth" not in notes:
            errors.append("sample/demo rows must say 'not ground truth' in notes")

    return errors


def validate_manifest_file(path: Path, check_images: bool = False) -> list[ManifestIssue]:
    issues: list[ManifestIssue] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                issues.append(ManifestIssue(line_number, f"invalid JSON: {exc.msg}"))
                continue
            if not isinstance(row, dict):
                issues.append(ManifestIssue(line_number, "row must be a JSON object"))
                continue
            issues.extend(ManifestIssue(line_number, error) for error in validate_manifest_row(row))
            if check_images:
                image_path = row.get("image_path")
                if isinstance(image_path, str):
                    try:
                        validate_readable_image(Path(image_path))
                    except ImageValidationError as exc:
                        issues.append(ManifestIssue(line_number, str(exc)))
    return issues
