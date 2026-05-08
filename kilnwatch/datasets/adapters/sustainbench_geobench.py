from __future__ import annotations

import csv
import json
from pathlib import Path

from kilnwatch.datasets.adapters.base import DatasetAdapter


class SustainBenchGeoBenchAdapter(DatasetAdapter):
    """Adapter for SustainBench/GEO-Bench brick kiln classification data.

    Expected input format:
        A CSV file (like `list_eval_partition.csv`) containing metadata.
        Expected columns: `y` (0 or 1), `hdf5_file`, `hdf5_idx`, `lon_top_left`,
        `lat_top_left`, `lon_bottom_right`, `lat_bottom_right`, `partition`
        (0=train, 1=val, 2=test).

    Expected output format:
        KilnWatch manifest JSONL.

    Geometry/labels:
        Uses bounding box coordinates and image-level binary labels.
        `image_path` points to a logical path representing the extracted HDF5 image.

    Internal mapping:
        `y` -> `kiln_detected`
        `partition` -> `split`
        Bounding coordinates -> approximated center lat/lon
    """

    name = "sustainbench_geobench"
    expected_input_format = "list_eval_partition.csv from SustainBench"
    geometry = "bounding boxes and image-level labels"
    mapping_notes = "Approximates center lat/lon from bounding box."

    def convert(self, input_path: Path, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        split_map = {"0": "train", "1": "val", "2": "test", "0.0": "train", "1.0": "val", "2.0": "test"}

        with input_path.open("r", encoding="utf-8-sig", newline="") as source, output_path.open(
            "w", encoding="utf-8"
        ) as target:
            reader = csv.DictReader(source)
            required = {"y", "partition", "hdf5_file", "hdf5_idx", "lat_top_left", "lon_top_left", "lat_bottom_right", "lon_bottom_right"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"missing required columns: {', '.join(sorted(missing))}")
                
            for row_idx, row in enumerate(reader):
                y_val = row.get("y", "0").strip()
                kiln_detected = y_val == "1" or y_val == "1.0"
                
                partition = row.get("partition", "").strip()
                split = split_map.get(partition, "unknown")
                
                hdf5_file = row.get("hdf5_file", "")
                hdf5_idx = row.get("hdf5_idx", "")
                tile_id = f"sustainbench_{hdf5_file}_{hdf5_idx}"
                
                try:
                    lat_tl = float(row["lat_top_left"])
                    lon_tl = float(row["lon_top_left"])
                    lat_br = float(row["lat_bottom_right"])
                    lon_br = float(row["lon_bottom_right"])
                    lat = (lat_tl + lat_br) / 2.0
                    lon = (lon_tl + lon_br) / 2.0
                except (ValueError, KeyError):
                    lat, lon = 0.0, 0.0
                
                record = {
                    "tile_id": tile_id,
                    "image_path": f"datasets/kilnwatch/images/sustainbench/{tile_id}.png",
                    "lat": lat,
                    "lon": lon,
                    "source": "sustainbench",
                    "split": split,
                    "label": "brick_kiln" if kiln_detected else "background",
                    "kiln_detected": kiln_detected,
                    "bbox": [lon_tl, lat_br, lon_br, lat_tl], # Approx [xmin, ymin, xmax, ymax]
                    "confidence": None,
                    "notes": f"Converted from SustainBench list_eval_partition.csv. File: {hdf5_file}, Idx: {hdf5_idx}",
                }
                target.write(json.dumps(record, sort_keys=True) + "\\n")


