from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from kilnwatch.ingestion.regions import Region
from kilnwatch.ingestion.simsat_client import SimSatResponse


@dataclass(frozen=True)
class TileRecord:
    tile_id: str
    latitude: float
    longitude: float
    timestamp: str
    source: str
    region_name: str
    request: dict
    artifact: dict


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_timestamp(timestamp: str) -> str:
    return timestamp.replace(":", "-")


def extension_for_content_type(content_type: str) -> str:
    normalized = content_type.split(";")[0].strip().lower()
    if normalized == "image/png":
        return ".png"
    if normalized in {"image/jpeg", "image/jpg"}:
        return ".jpg"
    if normalized in {"image/tiff", "image/geotiff", "application/geotiff"}:
        return ".tif"
    if normalized == "application/json":
        return ".json"
    return ".bin"


def write_tile_dataset(
    response: SimSatResponse,
    region: Region,
    dataset_root: Path = Path("data"),
    timestamp: str | None = None,
) -> TileRecord:
    observed_at = timestamp or utc_now_iso()
    tile_id = f"{region.slug}_{region.latitude:.4f}_{region.longitude:.4f}_{safe_timestamp(observed_at)}"
    extension = extension_for_content_type(response.content_type)

    raw_dir = dataset_root / "raw" / "simsat" / region.slug
    metadata_dir = dataset_root / "metadata" / "simsat" / region.slug
    raw_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / f"{tile_id}{extension}"
    metadata_path = metadata_dir / f"{tile_id}.json"
    raw_path.write_bytes(response.body)

    record = TileRecord(
        tile_id=tile_id,
        latitude=region.latitude,
        longitude=region.longitude,
        timestamp=observed_at,
        source="simsat-sentinel-2",
        region_name=region.name,
        request={
            "base_url": response.url.split(response.endpoint.lstrip("/"), 1)[0].rstrip("?"),
            "endpoint": response.endpoint,
            "url": response.url,
        },
        artifact={
            "path": str(raw_path),
            "content_type": response.content_type,
            "size_bytes": len(response.body),
        },
    )
    metadata_path.write_text(json.dumps(asdict(record), indent=2) + "\n", encoding="utf-8")
    return record


def write_smoke_report(message: str, dataset_root: Path = Path("data")) -> Path:
    smoke_dir = dataset_root / "smoke"
    smoke_dir.mkdir(parents=True, exist_ok=True)
    path = smoke_dir / f"simsat_unreachable_{safe_timestamp(utc_now_iso())}.json"
    payload = {
        "status": "simsat_unreachable",
        "timestamp": utc_now_iso(),
        "message": message,
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path

