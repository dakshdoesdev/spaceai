import tempfile
import unittest
from pathlib import Path

from kilnwatch.datasets.manifest import validate_manifest_file
from kilnwatch.ingestion.simsat_client import SimSatResponse
from scripts.fetch_demo_tiles import build_demo_tiles, read_coordinate_csv, write_tile


class FetchDemoTilesTests(unittest.TestCase):
    def test_csv_to_manifest_conversion_writes_tiles_and_sidecars(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "coords.csv"
            tile_dir = root / "raw_tiles"
            manifest_path = root / "manifest.jsonl"
            csv_path.write_text(
                "tile_id,lat,lon,region_name,expected_label,source,notes\n"
                "haryana_positive_001,29.39,76.96,Haryana India,positive,manual_test,reviewed positive\n"
                "haryana_negative_001,29.40,76.97,Haryana India,negative,manual_test,reviewed negative\n",
                encoding="utf-8",
            )

            rows = read_coordinate_csv(csv_path)
            records = build_demo_tiles(rows, mode="placeholder", tile_dir=tile_dir, manifest_path=manifest_path)

            self.assertEqual(len(records), 2)
            self.assertTrue((tile_dir / "haryana_positive_001.tile").exists())
            self.assertTrue((tile_dir / "haryana_positive_001.tile.meta.json").exists())
            self.assertTrue(records[0]["kiln_detected"])
            self.assertFalse(records[1]["kiln_detected"])
            self.assertTrue(records[0]["is_placeholder"])
            self.assertFalse(records[0]["is_real_imagery"])

    def test_missing_csv_writes_template_and_raises_clear_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / "missing" / "coords.csv"
            with self.assertRaises(FileNotFoundError) as context:
                read_coordinate_csv(csv_path)

            self.assertTrue(csv_path.exists())
            self.assertIn("Wrote a sample template", str(context.exception))

    def test_generated_manifest_passes_existing_validator(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "coords.csv"
            manifest_path = root / "manifest.jsonl"
            csv_path.write_text(
                "tile_id,lat,lon,region_name,expected_label,source,notes\n"
                "haryana_positive_001,29.39,76.96,Haryana India,positive,manual_test,reviewed positive\n"
                "haryana_negative_001,29.40,76.97,Haryana India,negative,manual_test,reviewed negative\n",
                encoding="utf-8",
            )

            build_demo_tiles(
                read_coordinate_csv(csv_path),
                mode="placeholder",
                tile_dir=root / "raw_tiles",
                manifest_path=manifest_path,
            )

            self.assertEqual(validate_manifest_file(manifest_path), [])

    def test_local_import_mode_requires_readable_real_images(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "coords.csv"
            local_images = root / "manual_images"
            local_images.mkdir()
            manifest_path = root / "manifest.jsonl"
            csv_path.write_text(
                "tile_id,lat,lon,region_name,expected_label,source,notes\n"
                "haryana_positive_001,29.39,76.96,Haryana India,positive,manual_image_import,real local image\n",
                encoding="utf-8",
            )
            write_test_png(local_images / "haryana_positive_001.png")

            records = build_demo_tiles(
                read_coordinate_csv(csv_path),
                mode="local-import",
                tile_dir=root / "raw_tiles",
                manifest_path=manifest_path,
                local_image_dir=local_images,
            )

            self.assertEqual(records[0]["image_path"], str(root / "raw_tiles" / "haryana_positive_001.png"))
            self.assertFalse(records[0]["is_placeholder"])
            self.assertTrue(records[0]["is_real_imagery"])
            self.assertEqual(validate_manifest_file(manifest_path, check_images=True), [])

    def test_bad_local_image_bytes_fail_real_import(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            csv_path = root / "coords.csv"
            local_images = root / "manual_images"
            local_images.mkdir()
            csv_path.write_text(
                "tile_id,lat,lon,region_name,expected_label,source,notes\n"
                "haryana_positive_001,29.39,76.96,Haryana India,positive,manual_image_import,bad local image\n",
                encoding="utf-8",
            )
            (local_images / "haryana_positive_001.png").write_bytes(b"not an image")

            with self.assertRaisesRegex(ValueError, "readable image"):
                build_demo_tiles(
                    read_coordinate_csv(csv_path),
                    mode="local-import",
                    tile_dir=root / "raw_tiles",
                    manifest_path=root / "manifest.jsonl",
                    local_image_dir=local_images,
                )

    def test_simsat_non_image_bytes_fail_real_mode(self):
        class BadImageClient:
            base_url = "http://localhost:9005/"

            def fetch_sentinel_tile(self, lat, lon, width=512, height=512):
                return SimSatResponse("/sentinel-2/image", "http://localhost:9005/sentinel-2/image", "text/plain", b"nope")

        with tempfile.TemporaryDirectory() as temp_dir:
            row = read_coordinate_csv(_write_one_row_csv(Path(temp_dir) / "coords.csv"))[0]
            with self.assertRaisesRegex(RuntimeError, "non-image bytes"):
                write_tile(
                    row,
                    mode="simsat",
                    tile_dir=Path(temp_dir),
                    client=BadImageClient(),
                    local_image_dir=None,
                    width=512,
                    height=512,
                )


def _write_one_row_csv(path: Path) -> Path:
    path.write_text(
        "tile_id,lat,lon,region_name,expected_label,source,notes\n"
        "haryana_positive_001,29.39,76.96,Haryana India,positive,manual_test,reviewed positive\n",
        encoding="utf-8",
    )
    return path


def write_test_png(path: Path) -> None:
    from PIL import Image

    image = Image.new("RGB", (1, 1), color=(255, 0, 0))
    image.save(path, format="PNG")


if __name__ == "__main__":
    unittest.main()
