from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    slug: str
    name: str
    latitude: float
    longitude: float


HARYANA_INDIA = Region(
    slug="haryana_india",
    name="Haryana, India",
    latitude=29.3909,
    longitude=76.9635,
)
