from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class DatasetAdapter(ABC):
    """Base class for local-file dataset adapters."""

    name: str
    expected_input_format: str
    expected_output_format: str = "KilnWatch manifest JSONL"
    geometry: str
    mapping_notes: str

    @abstractmethod
    def convert(self, input_path: Path, output_path: Path) -> None:
        """Convert a local input file into a KilnWatch manifest JSONL file."""


class AdapterNotImplementedError(NotImplementedError):
    """Raised when an adapter documents a resource but conversion is not wired yet."""

