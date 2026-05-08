from __future__ import annotations

import csv
import json
from pathlib import Path

from kilnwatch.datasets.adapters.base import DatasetAdapter


class ApadIgpAdapter(DatasetAdapter):
    """Adapter for local APAD/Zenodo Indo-Gangetic Plain (IGP) coordinate CSV exports.
    Handles Pakistan, India, and Bangladesh datasets.

    Expected input format:
        CSV with at least `id`, `lat`, and `lon`. Optional columns include
        `type`, `state`, `country`, `schools1km`, `hosp1km`, `pop1km`, and emissions fields.

    Expected output format:
        KilnWatch manifest JSONL.

    Geometry/labels:
        Uses coordinates and positive kiln-site labels. It does not provide image
        tiles or bounding boxes, so `image_path` is a downstream placeholder until
        a local SimSat/Sentinel tile is fetched for each coordinate.

    Internal mapping:
        `id` -> tile_id suffix, `lat`/`lon` -> coordinates, `type` -> label,
        proximity/emissions columns -> notes.
    """

    name = "apad_igp"
    expected_input_format = "CSV with id, lat, lon, type/state/country/proximity/emissions columns"
    geometry = "coordinates and labels"
    mapping_notes = "Coordinates become positive kiln records; bbox is unavailable."

    def convert(self, input_path: Path, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with input_path.open("r", encoding="utf-8-sig", newline="") as source, output_path.open(
            "w", encoding="utf-8"
        ) as target:
            reader = csv.DictReader(source)
            required = {"id", "lat", "lon"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"missing required columns: {', '.join(sorted(missing))}")
            for row in reader:
                country = row.get("country", "unknown").lower().replace(" ", "_")
                source_val = f"apad_igp_{country}_local_csv"
                tile_id = f"apad_igp_{country}_{row['id']}"
                record = {
                    "tile_id": tile_id,
                    "image_path": f"datasets/kilnwatch/images/external/{tile_id}.png",
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"]),
                    "source": source_val,
                    "split": "external",
                    "label": row.get("type") or "brick_kiln",
                    "kiln_detected": True,
                    "bbox": None,
                    "confidence": None,
                    "notes": _notes_from_row(row),
                }
                target.write(json.dumps(record, sort_keys=True) + "\n")


def _notes_from_row(row: dict[str, str]) -> str:
    parts = ["Converted from local APAD/Zenodo IGP CSV; image tile not bundled."]
    for field in ("state", "country", "schools1km", "hosp1km", "pop1km"):
        value = row.get(field)
        if value:
            parts.append(f"{field}={value}")
    return " ".join(parts)
