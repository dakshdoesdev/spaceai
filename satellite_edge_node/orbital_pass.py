"""Simulate an orbital pass over raw tiles."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
import shutil

from .baseline_detector import is_tile_file
from .detectors import Detector, build_detector_with_fallback
from .liquid_vlm_reasoner import LiquidReasonerError, Reasoner, build_reasoner
from .payloads import (
    attach_byte_accounting,
    build_transmission_payload,
    copy_full_tile,
    crop_required_for,
    encode_payload,
    full_tile_required_for,
    generate_crop_file,
    should_transmit_triage,
    telemetry_record,
    triage_label,
)
from .yolo_detector import DEFAULT_MODEL_PATH, YoloDetectorError


class RequiredCropUnavailable(RuntimeError):
    pass


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
    reasoner: Reasoner | None = None,
    reasoner_mode: str = "disabled",
    reset_queue: bool = False,
    require_crops: bool = False,
    write_drop_payloads: bool = False,
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
    if reasoner is None:
        reasoner = build_reasoner(reasoner_mode)

    with telemetry_path.open("a", encoding="utf-8") as telemetry:
        for tile_path in discover_tiles(raw_tiles_dir):
            original_bytes = tile_path.stat().st_size
            started = time.perf_counter()
            detection = detector.detect_tile(tile_path)
            latency_ms = (time.perf_counter() - started) * 1000

            # Compute the four-tier triage decision before Liquid. This is the
            # actual transmit gate; Liquid can annotate crop evidence after the
            # crop exists, but it must not retroactively change what downlinks.
            triage = triage_label(detection, None, min_confidence=confidence_threshold)
            decision = triage["decision"]

            # Generate crop only for tiers that need one.
            crop_artifact = generate_crop_file(
                tile_path,
                detection,
                transmission_queue / "crops",
                triage_decision=decision,
            )
            # Copy the whole tile only on FULL_DOWNLINK.
            full_tile_artifact = copy_full_tile(
                tile_path,
                detection.tile_id,
                transmission_queue / "full_tiles",
                triage_decision=decision,
            )

            if require_crops and crop_required_for(decision) and crop_artifact.path is None:
                detail = crop_artifact.error or "tier requires a crop but none was produced"
                raise RequiredCropUnavailable(f"{detection.tile_id}: {detail}")

            vlm_reasoning = None
            if reasoner is not None and detection.kiln_detected and crop_artifact.path is not None:
                vlm_reasoning = reasoner.reason(
                    image_path=tile_path,
                    detection=detection,
                    crop_path=crop_artifact.path,
                )

            output_path = None
            json_payload_bytes = 0
            transmitted_bytes = 0
            if should_transmit_triage(decision) or write_drop_payloads:
                payload = build_transmission_payload(
                    detection,
                    tile_path,
                    crop_artifact,
                    vlm_reasoning,
                    triage_min_confidence=confidence_threshold,
                    full_tile_artifact=full_tile_artifact,
                    triage=triage,
                )
                output_path = transmission_queue / f"{detection.tile_id}.json"
                payload_bytes = _finalize_payload_bytes(
                    payload,
                    original_bytes,
                    crop_artifact.size_bytes,
                    full_tile_artifact.size_bytes,
                )
                output_path.write_bytes(payload_bytes)
                json_payload_bytes = output_path.stat().st_size
                transmitted_bytes = (
                    json_payload_bytes
                    + crop_artifact.size_bytes
                    + full_tile_artifact.size_bytes
                )

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
                vlm_reasoning=vlm_reasoning,
                triage_min_confidence=confidence_threshold,
                full_tile_payload_bytes=full_tile_artifact.size_bytes,
                full_tile_path=full_tile_artifact.path,
                full_tile_error=full_tile_artifact.error,
                triage=triage,
            )
            record["requested_detector_mode"] = detector_mode
            record["requested_reasoner_mode"] = reasoner_mode
            telemetry.write(json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n")
            records.append(record)

    return records


def _finalize_payload_bytes(
    payload: dict,
    original_bytes: int,
    crop_bytes: int,
    full_tile_bytes: int = 0,
) -> bytes:
    json_bytes = 0
    transmitted_bytes = crop_bytes + full_tile_bytes
    for _ in range(8):
        attach_byte_accounting(
            payload,
            original_payload_bytes=original_bytes,
            json_payload_bytes=json_bytes,
            crop_payload_bytes=crop_bytes,
            transmitted_payload_bytes=transmitted_bytes,
            full_tile_payload_bytes=full_tile_bytes,
        )
        payload_bytes = encode_payload(payload)
        next_json_bytes = len(payload_bytes)
        next_transmitted_bytes = next_json_bytes + crop_bytes + full_tile_bytes
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
        full_tile_payload_bytes=full_tile_bytes,
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

    for sub in ("crops", "full_tiles"):
        sub_dir = transmission_queue / sub
        if sub_dir.exists() and sub_dir.is_dir():
            shutil.rmtree(sub_dir)


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulate KilnWatch satellite-edge orbital pass.")
    parser.add_argument("--raw-tiles", type=Path, default=Path("data/raw_tiles"))
    parser.add_argument("--transmission-queue", type=Path, default=Path("transmission_queue"))
    parser.add_argument("--detector", choices=("baseline", "yolo"), default="baseline")
    parser.add_argument(
        "--reasoner",
        choices=("disabled", "liquid-mock", "liquid-local"),
        default="disabled",
        help="Liquid VLM reasoner backend. 'liquid-local' runs LFM2.5-VL via transformers.",
    )
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
    parser.add_argument(
        "--require-crops",
        action="store_true",
        help="Fail if an alert cannot produce a real crop artifact.",
    )
    parser.add_argument(
        "--write-drop-payloads",
        action="store_true",
        help="Legacy/debug mode: write JSON files for dropped tiles instead of telemetry-only drops.",
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
            reasoner_mode=args.reasoner,
            reset_queue=args.reset_queue,
            require_crops=args.require_crops,
            write_drop_payloads=args.write_drop_payloads,
        )
    except YoloDetectorError as exc:
        print(f"Detector setup failed: {exc}")
        print("Use --detector baseline for explicit simulation, or --allow-baseline-fallback to opt into simulated fallback.")
        return 2
    except LiquidReasonerError as exc:
        print(f"Liquid reasoner setup/inference failed: {exc}")
        print("Use --reasoner disabled for YOLO-only mode, or --reasoner liquid-mock for explicit simulated reasoning.")
        return 3
    except RequiredCropUnavailable as exc:
        print(f"Required crop unavailable: {exc}")
        print("Use readable image tiles with detector bboxes, or rerun without --require-crops for diagnostic telemetry.")
        return 4
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
    print(f"Reasoner mode: {args.reasoner}")
    print(f"Transmission queue: {args.transmission_queue}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
