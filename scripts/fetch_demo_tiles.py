#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kilnwatch.datasets.image_validation import (
    ImageValidationError,
    infer_image_extension,
    is_real_image_extension,
    validate_readable_image,
)
from kilnwatch.ingestion.simsat_client import SimSatClient, SimSatUnavailable


DEFAULT_COORDINATES_CSV = Path("datasets/kilnwatch/coordinates/haryana_demo_coordinates.csv")
DEFAULT_TILE_DIR = Path("data/raw_tiles")
DEFAULT_MANIFEST = Path("datasets/kilnwatch/manifests/haryana_demo_manifest.jsonl")
DEFAULT_SIMSAT_URL = "http://localhost:9005"

REQUIRED_COLUMNS = {"tile_id", "lat", "lon", "region_name", "expected_label", "source", "notes"}
POSITIVE_LABELS = {"positive", "kiln", "brick_kiln", "yes", "1", "true"}
NEGATIVE_LABELS = {"negative", "no_kiln", "control", "false_positive_control", "0", "false"}


@dataclass(frozen=True)
class CoordinateRow:
    tile_id: str
    lat: float
    lon: float
    region_name: str
    expected_label: str
    source: str
    notes: str

    @property
    def kiln_detected(self) -> bool:
        normalized = self.expected_label.strip().lower()
        if normalized in POSITIVE_LABELS:
            return True
        if normalized in NEGATIVE_LABELS:
            return False
        raise ValueError(
            f"{self.tile_id}: expected_label must be positive/kiln/brick_kiln or negative/no_kiln/control"
        )


def read_coordinate_csv(path: Path) -> list[CoordinateRow]:
    if not path.exists():
        write_sample_coordinate_csv(path)
        raise FileNotFoundError(
            f"Coordinate CSV not found: {path}. Wrote a sample template there; edit it with Haryana/India rows and rerun."
        )

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing required columns: {', '.join(sorted(missing))}")
        rows = []
        for line_number, raw in enumerate(reader, start=2):
            if not any((value or "").strip() for value in raw.values()):
                continue
            try:
                rows.append(
                    CoordinateRow(
                        tile_id=required_text(raw, "tile_id", line_number),
                        lat=float(required_text(raw, "lat", line_number)),
                        lon=float(required_text(raw, "lon", line_number)),
                        region_name=required_text(raw, "region_name", line_number),
                        expected_label=required_text(raw, "expected_label", line_number),
                        source=required_text(raw, "source", line_number),
                        notes=required_text(raw, "notes", line_number),
                    )
                )
            except ValueError as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
    return rows


def required_text(row: dict[str, str], field: str, line_number: int) -> str:
    value = (row.get(field) or "").strip()
    if not value:
        raise ValueError(f"missing {field}")
    if field == "tile_id" and not all(char.islower() or char.isdigit() or char in "_-" for char in value):
        raise ValueError("tile_id should use lowercase letters, numbers, '_' or '-'")
    return value


def write_sample_coordinate_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "tile_id": "haryana_positive_replace_001",
            "lat": "29.390900",
            "lon": "76.963500",
            "region_name": "Haryana, India",
            "expected_label": "positive",
            "source": "apad_or_manual_local_csv",
            "notes": "Replace with a real APAD/manual kiln coordinate before claiming ground truth.",
        },
        {
            "tile_id": "haryana_industrial_negative_001",
            "lat": "29.432000",
            "lon": "76.917000",
            "region_name": "Haryana industrial control",
            "expected_label": "negative",
            "source": "manual_negative_control",
            "notes": "Industrial false-positive control; verify no kiln in selected tile.",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=sorted(REQUIRED_COLUMNS))
        writer.writeheader()
        writer.writerows(rows)


def build_demo_tiles(
    rows: Iterable[CoordinateRow],
    *,
    mode: str,
    tile_dir: Path,
    manifest_path: Path,
    local_image_dir: Path | None = None,
    simsat_base_url: str = DEFAULT_SIMSAT_URL,
    width: int = 512,
    height: int = 512,
) -> list[dict]:
    tile_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    client = SimSatClient(simsat_base_url, timeout_seconds=10.0) if mode == "simsat" else None
    records: list[dict] = []
    with manifest_path.open("w", encoding="utf-8") as manifest:
        for row in rows:
            image_path = write_tile(
                row,
                mode=mode,
                tile_dir=tile_dir,
                client=client,
                local_image_dir=local_image_dir,
                width=width,
                height=height,
            )
            sidecar_path = write_sidecar(row, image_path, mode)
            record = manifest_record(row, image_path, mode, sidecar_path)
            manifest.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
            records.append(record)
    return records


def write_tile(
    row: CoordinateRow,
    *,
    mode: str,
    tile_dir: Path,
    client: SimSatClient | None,
    local_image_dir: Path | None,
    width: int,
    height: int,
) -> Path:
    if mode == "placeholder":
        path = tile_dir / f"{row.tile_id}.tile"
        payload = (
            f"KILNWATCH_PLACEHOLDER_TILE\n"
            f"tile_id={row.tile_id}\n"
            f"lat={row.lat:.6f}\n"
            f"lon={row.lon:.6f}\n"
            f"expected_label={row.expected_label}\n"
            "This is not satellite imagery. Replace with a real SimSat/Sentinel tile.\n"
        )
        path.write_bytes(payload.encode("utf-8"))
        return path

    if mode == "local-import":
        if local_image_dir is None:
            raise ValueError("--local-image-dir is required for local-import mode")
        source_path = find_local_image(local_image_dir, row.tile_id)
        validate_readable_image(source_path)
        target_path = tile_dir / source_path.name
        if source_path.resolve() != target_path.resolve():
            shutil.copy2(source_path, target_path)
        validate_readable_image(target_path)
        return target_path

    if mode != "simsat":
        raise ValueError(f"unknown mode: {mode}")
    if client is None:
        raise ValueError("SimSat client is required for simsat mode")

    try:
        response = client.fetch_sentinel_tile(row.lat, row.lon, width=width, height=height)
    except SimSatUnavailable as exc:
        raise RuntimeError(
            "SimSat is not running or no Sentinel image endpoint matched. "
            f"Start the local SimSat service at {client.base_url.rstrip('/')} or rerun with --mode placeholder. "
            f"Detail: {exc}"
        ) from exc

    extension = infer_image_extension(response.body, response.content_type)
    if extension is None:
        raise RuntimeError(
            "SimSat returned non-image bytes. Real mode only accepts PNG, JPEG, or TIFF image responses; "
            f"content_type={response.content_type!r}, bytes={len(response.body)}."
        )
    path = tile_dir / f"{row.tile_id}{extension}"
    path.write_bytes(response.body)
    try:
        validate_readable_image(path)
    except ImageValidationError as exc:
        path.unlink(missing_ok=True)
        raise RuntimeError(f"SimSat response was saved but is not a readable image: {exc}") from exc
    return path


def find_local_image(local_image_dir: Path, tile_id: str) -> Path:
    candidates = [local_image_dir / f"{tile_id}{extension}" for extension in sorted({".png", ".jpg", ".jpeg", ".tif", ".tiff"})]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        f"No readable image candidate found for tile_id={tile_id} in {local_image_dir}. "
        "Expected one of .png, .jpg, .jpeg, .tif, .tiff with the filename matching tile_id."
    )


def write_sidecar(row: CoordinateRow, image_path: Path, mode: str) -> Path:
    sidecar_path = image_path.with_suffix(image_path.suffix + ".meta.json")
    risk = "medium" if row.kiln_detected else "low"
    payload = {
        "tile_id": row.tile_id,
        "kiln_detected": row.kiln_detected,
        "confidence": 0.5 if mode == "placeholder" else 0.7,
        "compliance_risk": risk,
        "coordinates": {"lat": row.lat, "lon": row.lon},
        "signals": ["coordinate_manifest_label"],
        "region_name": row.region_name,
        "source": row.source,
        "mode": mode,
        "notes": row.notes,
    }
    sidecar_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sidecar_path


def manifest_record(row: CoordinateRow, image_path: Path, mode: str, sidecar_path: Path) -> dict:
    source = "sample_demo_not_ground_truth" if mode == "placeholder" else row.source
    notes = row.notes
    if mode == "placeholder" and "not ground truth" not in notes.lower():
        notes = f"{notes} Placeholder tile only; not ground truth."
    if mode != "placeholder" and not is_real_image_extension(image_path):
        raise ValueError(f"real mode produced a non-image path: {image_path}")

    return {
        "tile_id": row.tile_id,
        "image_path": str(image_path),
        "lat": row.lat,
        "lon": row.lon,
        "source": source,
        "split": "demo",
        "label": "brick_kiln" if row.kiln_detected else "negative_control",
        "kiln_detected": row.kiln_detected,
        "bbox": None,
        "confidence": 0.5 if mode == "placeholder" else 0.7,
        "notes": f"{notes} sidecar={sidecar_path}",
        "region_name": row.region_name,
        "expected_label": row.expected_label,
        "data_mode": mode,
        "is_placeholder": mode == "placeholder",
        "is_real_imagery": mode != "placeholder",
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build KilnWatch demo tiles and a validator-compatible manifest.")
    parser.add_argument("--coordinates-csv", type=Path, default=DEFAULT_COORDINATES_CSV)
    parser.add_argument("--tile-dir", type=Path, default=DEFAULT_TILE_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--mode", choices=("placeholder", "simsat", "local-import"), default="placeholder")
    parser.add_argument("--local-image-dir", type=Path, help="folder containing real images named <tile_id>.png/.jpg/.jpeg/.tif")
    parser.add_argument("--simsat-base-url", default=DEFAULT_SIMSAT_URL)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        rows = read_coordinate_csv(args.coordinates_csv)
        records = build_demo_tiles(
            rows,
            mode=args.mode,
            tile_dir=args.tile_dir,
            manifest_path=args.manifest,
            local_image_dir=args.local_image_dir,
            simsat_base_url=args.simsat_base_url,
            width=args.width,
            height=args.height,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    positives = sum(1 for record in records if record["kiln_detected"])
    negatives = len(records) - positives
    print(f"Wrote {len(records)} manifest rows: {args.manifest}")
    print(f"Wrote local tile files and sidecars under: {args.tile_dir}")
    print(f"Positive rows: {positives}; negative controls: {negatives}; mode: {args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
