from pathlib import Path
import unittest


class GroundStationBoundaryTests(unittest.TestCase):
    def test_ground_station_does_not_import_satellite_raw_tile_modules(self):
        for path in Path("ground_station_ui").glob("*.py"):
            source = path.read_text(encoding="utf-8")
            self.assertNotIn("satellite_edge_node", source)
            self.assertNotIn("data/raw_tiles", source)
            self.assertNotIn("raw_tiles", source)


if __name__ == "__main__":
    unittest.main()
