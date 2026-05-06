from pathlib import Path
import unittest


class GroundStationBoundaryTests(unittest.TestCase):
    def test_ground_station_does_not_import_satellite_raw_tile_modules(self):
        for path in _ground_station_surfaces():
            source = _production_source_for_boundary_scan(path)
            self.assertNotIn("satellite_edge_node", source)
            if path == Path("kilnwatch/ground_station.py"):
                self.assertIn("FORBIDDEN_CROP_SOURCE_FRAGMENTS", source)
            for forbidden in ("data/raw_tiles", "data/final_demo_tiles", "datasets/roboflow", "raw_tiles"):
                self.assertNotIn(forbidden, source, f"{path} must not reference {forbidden}")
            if path == Path("kilnwatch/ground_station.py"):
                continue
            self.assertNotIn('".tile', source, f"{path} must not use placeholder .tile fixtures as previews")
            self.assertNotIn("'.tile", source, f"{path} must not use placeholder .tile fixtures as previews")


def _ground_station_surfaces() -> list[Path]:
    return [
        Path("app.py"),
        Path("kilnwatch/ground_station.py"),
        *sorted(Path("ground_station_ui").glob("*.py")),
    ]


def _production_source_for_boundary_scan(path: Path) -> str:
    source = path.read_text(encoding="utf-8")
    if path != Path("kilnwatch/ground_station.py"):
        return source
    marker = "FORBIDDEN_CROP_SOURCE_FRAGMENTS"
    if marker not in source:
        return source
    before, _, after = source.partition(marker)
    _, _, after_constant = after.partition(")\n")
    return before + marker + after_constant


if __name__ == "__main__":
    unittest.main()
