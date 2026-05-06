from __future__ import annotations

from pathlib import Path

from kilnwatch.datasets.adapters.base import AdapterNotImplementedError, DatasetAdapter


class SentinelKilnDbAdapter(DatasetAdapter):
    """Adapter stub for SentinelKilnDB local downloads.

    Expected input format:
        Local SentinelKilnDB dataset root with split folders, RGB Sentinel-2
        tiles, and DOTA / YOLO-OBB / YOLO-AA annotation text files.

    Expected output format:
        KilnWatch manifest JSONL.

    Geometry/labels:
        Uses image tiles, train/val/test splits, labels, and oriented bounding
        boxes. Coordinates may need sidecar metadata if not present in filenames.

    Internal mapping:
        Image path -> `image_path`; split folder -> `split`; OBB annotation ->
        `bbox`; any kiln class -> `kiln_detected=true`; missing/negative labels
        -> `kiln_detected=false` if the official split includes negative tiles.

    License warning:
        Dataset README lists CC BY-NC-SA 4.0. Confirm non-commercial/share-alike
        compatibility before bundling or publishing derived manifests.
    """

    name = "sentinelkilndb"
    expected_input_format = "Local SentinelKilnDB root with images and DOTA/YOLO-OBB labels"
    geometry = "image tiles, oriented bounding boxes, labels, splits"
    mapping_notes = "Best bbox-aware target, but needs manual download and license acceptance."

    def convert(self, input_path: Path, output_path: Path) -> None:
        raise AdapterNotImplementedError(
            "SentinelKilnDB conversion is stubbed until local folder layout is confirmed after download."
        )

