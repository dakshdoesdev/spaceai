from __future__ import annotations

from pathlib import Path

from kilnwatch.datasets.adapters.base import AdapterNotImplementedError, DatasetAdapter


class Kdd24ReferenceAdapter(DatasetAdapter):
    """Reference-only adapter for rishabh-mondal/kdd24_brick_kilns.

    Expected input format:
        A license-compatible local export prepared by the user, ideally JSONL/CSV
        with image_path, lat, lon, split, and label fields.

    Expected output format:
        KilnWatch manifest JSONL.

    Geometry/labels:
        Could use image tiles and image-level labels. Bounding boxes are not assumed.

    Internal mapping:
        Map local tile identifiers to `tile_id`, local images to `image_path`,
        source to `kdd24_local_export`, and label fields to `kiln_detected`.

    License/API warning:
        The inspected GitHub repo did not expose a license file and its download
        notebook references Google Static API. Do not auto-download or copy code.
    """

    name = "kdd24_reference"
    expected_input_format = "User-prepared local CSV/JSONL export with image_path, lat, lon, label"
    geometry = "image tiles and labels if provided by a license-compatible local export"
    mapping_notes = "Reference-only until license-compatible local export exists."

    def convert(self, input_path: Path, output_path: Path) -> None:
        raise AdapterNotImplementedError(
            "KDD24 conversion is intentionally stubbed until a license-compatible local export is provided."
        )

