"""Simulate an orbital pass over raw tiles."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
import shutil

from .baseline_detector import is_tile_file
from .detectors import Detector, build_detector_with_fallback
from .payloads import attach_byte_accounting, build_transmission_payload, encode_payload, generate_crop_file, telemetry_record
from .yolo_detector import DEFAULT_MODEL_PATH, YoloDetectorError


def discover_tiles(raw_tiles_dir: Path) -> list[Path]:
    return sorted(path for path in raw_tiles_dir.rglob("*") if is_tile_file(path))


def simulate_orbital_pass(
    raw_tiles_dir: Path,
    transmission_queue: Path,
    *,
    detector: Detector | None = None,
    detector_mode: str = "baseline",
    model_path: Path = DEFAULT_MODEL_PATH,
    confidence_threshold: float = 0.25,
    allow_baseline_fallback: bool = False,
    reset_queue: bool = False,
) -> list[dict]:
    if reset_queue:
        _reset_transmission_queue(transmission_queue)
    transmission_queue.mkdir(parents=True, exist_ok=True)
    telemetry_path = transmission_queue / "telemetry.jsonl"
    records: list[dict] = []
    fallback_reason = None
    if detector is None:
        detector, fallback_reason = build_detector_with_fallback(
            detector_mode,
            model_path=model_path,
            confidence_threshold=confidence_threshold,
            fallback_to_baseline=allow_baseline_fallback,
        )

    with telemetry_path.open("a", encoding="utf-8") as telemetry:
        for tile_path in discover_tiles(raw_tiles_dir):
            original_bytes = tile_path.stat().st_size
            started = time.perf_counter()
            detection = detector.detect_tile(tile_path)
            latency_ms = (time.perf_counter() - started) * 1000

            crop_artifact = generate_crop_file(tile_path, detection, transmission_queue / "crops")
            payload = build_transmission_payload(detection, tile_path, crop_artifact)
            output_path = transmission_queue / f"{detection.tile_id}.json"
            payload_bytes = _finalize_payload_bytes(payload, original_bytes, crop_artifact.size_bytes)
            output_path.write_bytes(payload_bytes)
            json_payload_bytes = output_path.stat().st_size
            transmitted_bytes = json_payload_bytes + crop_artifact.size_bytes

            record = telemetry_record(
                tile_path=tile_path,
                detection=detection,
                inference_latency_ms=latency_ms,
                original_payload_bytes=original_bytes,
                transmitted_payload_bytes=transmitted_bytes,
                json_payload_bytes=json_payload_bytes,
                crop_payload_bytes=crop_artifact.size_bytes,
                crop_path=crop_artifact.path,
                crop_error=crop_artifact.error,
                output_path=output_path,
            )
            record["requested_detector_mode"] = detector_mode
            telemetry.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
            records.append(record)

    return records


def _finalize_payload_bytes(payload: dict, original_bytes: int, crop_bytes: int) -> bytes:
    json_bytes = 0
    transmitted_bytes = crop_bytes
    for _ in range(8):
        attach_byte_accounting(
            payload,
            original_payload_bytes=original_bytes,
            json_payload_bytes=json_bytes,
            crop_payload_bytes=crop_bytes,
            transmitted_payload_bytes=transmitted_bytes,
        )
        payload_bytes = encode_payload(payload)
        next_json_bytes = len(payload_bytes)
        next_transmitted_bytes = next_json_bytes + crop_bytes
        if next_json_bytes == json_bytes and next_transmitted_bytes == transmitted_bytes:
            return payload_bytes
        json_bytes = next_json_bytes
        transmitted_bytes = next_transmitted_bytes
    attach_byte_accounting(
        payload,
        original_payload_bytes=original_bytes,
        json_payload_bytes=json_bytes,
        crop_payload_bytes=crop_bytes,
        transmitted_payload_bytes=transmitted_bytes,
    )
    return encode_payload(payload)


def _reset_transmission_queue(transmission_queue: Path) -> None:
    if not transmission_queue.exists():
        return

    for payload_path in transmission_queue.glob("*.json"):
        if payload_path.is_file():
            payload_path.unlink()

    telemetry_path = transmission_queue / "telemetry.jsonl"
    if telemetry_path.exists() and telemetry_path.is_file():
        telemetry_path.unlink()

    crops_dir = transmission_queue / "crops"
    if crops_dir.exists() and crops_dir.is_dir():
        shutil.rmtree(crops_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate KilnWatch satellite-edge orbital pass.")
    parser.add_argument("--raw-tiles", type=Path, default=Path("data/raw_tiles"))
    parser.add_argument("--transmission-queue", type=Path, default=Path("transmission_queue"))
    parser.add_argument("--detector", choices=("baseline", "yolo"), default="baseline")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL_PATH)
    parser.add_argument("--confidence-threshold", type=float, default=0.25)
    parser.add_argument(
        "--reset-queue",
        action="store_true",
        help="Delete generated payload JSON, telemetry, and crops in the selected queue before processing.",
    )
    parser.add_argument(
        "--allow-baseline-fallback",
        action="store_true",
        help="Allow YOLO setup failures to fall back to the simulated baseline detector.",
    )
    args = parser.parse_args()

    try:
        records = simulate_orbital_pass(
            args.raw_tiles,
            args.transmission_queue,
            detector_mode=args.detector,
            model_path=args.model_path,
            confidence_threshold=args.confidence_threshold,
            allow_baseline_fallback=args.allow_baseline_fallback,
            reset_queue=args.reset_queue,
        )
    except YoloDetectorError as exc:
        print(f"Detector setup failed: {exc}")
        print("Use --detector baseline for explicit simulation, or --allow-baseline-fallback to opt into simulated fallback.")
        return 2
    total_raw = sum(record["original_payload_bytes"] for record in records)
    total_transmitted = sum(record["transmitted_payload_bytes"] for record in records)
    saved = max(0, total_raw - total_transmitted)
    ratio = "inf" if total_transmitted == 0 and total_raw > 0 else f"{(total_raw / total_transmitted) if total_transmitted else 1.0:.2f}x"

    print(f"Processed tiles: {len(records)}")
    if records and records[0].get("fallback_reason"):
        print(f"Detector fallback: {records[0]['fallback_reason']}")
    print(f"Original bytes: {total_raw}")
    print(f"Transmitted bytes: {total_transmitted}")
    print(f"Bandwidth saved: {saved} bytes")
    print(f"Compression ratio: {ratio}")
    print(f"Transmission queue: {args.transmission_queue}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
