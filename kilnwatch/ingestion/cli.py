from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from kilnwatch.ingestion.dataset import write_smoke_report, write_tile_dataset
from kilnwatch.ingestion.regions import HARYANA_INDIA
from kilnwatch.ingestion.simsat_client import (
    DEFAULT_POSITION_ENDPOINTS,
    DEFAULT_SENTINEL_ENDPOINTS,
    SimSatClient,
    SimSatUnavailable,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch one Haryana, India Sentinel-style tile from local SimSat.")
    parser.add_argument("--base-url", default="http://localhost:9005")
    parser.add_argument("--dataset-root", default="data")
    parser.add_argument("--timeout-seconds", type=float, default=10.0)
    parser.add_argument("--width", type=int, default=512)
    parser.add_argument("--height", type=int, default=512)
    parser.add_argument("--position-endpoint", action="append", default=[])
    parser.add_argument("--image-endpoint", action="append", default=[])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_root = Path(args.dataset_root)
    client = SimSatClient(args.base_url, timeout_seconds=args.timeout_seconds)
    position_endpoints = tuple(args.position_endpoint) or DEFAULT_POSITION_ENDPOINTS
    image_endpoints = tuple(args.image_endpoint) or DEFAULT_SENTINEL_ENDPOINTS

    try:
        position = client.get_current_position(position_endpoints)
        print("SimSat current position:")
        print(json.dumps(position, indent=2))
    except SimSatUnavailable as exc:
        report = write_smoke_report(str(exc), dataset_root)
        print(f"SimSat is not reachable. Wrote fallback smoke report: {report}")
        return 0

    try:
        response = client.fetch_sentinel_tile(
            latitude=HARYANA_INDIA.latitude,
            longitude=HARYANA_INDIA.longitude,
            width=args.width,
            height=args.height,
            endpoints=image_endpoints,
        )
    except SimSatUnavailable as exc:
        report = write_smoke_report(str(exc), dataset_root)
        print(f"SimSat responded, but no Sentinel-2 image endpoint matched. Wrote fallback smoke report: {report}")
        return 0

    record = write_tile_dataset(response, HARYANA_INDIA, dataset_root)
    print("Wrote tile metadata:")
    print(json.dumps(asdict(record), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
