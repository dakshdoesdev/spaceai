from __future__ import annotations

from pathlib import Path

from kilnwatch.datasets.adapters.base import AdapterNotImplementedError, DatasetAdapter


class SustainBenchGeoBenchAdapter(DatasetAdapter):
    """Adapter stub for SustainBench/GEO-Bench brick kiln classification data.

    Expected input format:
        Local processed SustainBench or GEO-Bench brick-kiln classification
        files with image paths, split names, and class labels.

    Expected output format:
        KilnWatch manifest JSONL.

    Geometry/labels:
        Uses image tiles and image-level labels. Bounding boxes and precise
        coordinates may not be present.

    Internal mapping:
        Class label -> `kiln_detected`; source split -> `split`; image path ->
        `image_path`; bbox/confidence -> null unless explicitly present.
    """

    name = "sustainbench_geobench"
    expected_input_format = "Local classification dataset with image paths, splits, labels"
    geometry = "image tiles and image-level labels"
    mapping_notes = "Useful for classification validation; not bbox-aware."

    def convert(self, input_path: Path, output_path: Path) -> None:
        raise AdapterNotImplementedError(
            "SustainBench/GEO-Bench conversion is stubbed until local processed files are present."
        )

