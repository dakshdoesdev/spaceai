from pathlib import Path
import tempfile
import unittest

from kilnwatch.datasets.manifest import validate_manifest_file, validate_manifest_row


class ManifestSchemaTest(unittest.TestCase):
    def test_sample_manifest_is_valid(self):
        issues = validate_manifest_file(Path("datasets/kilnwatch/manifests/sample_demo_manifest.jsonl"))
        self.assertEqual(issues, [])

    def test_missing_required_fields_are_reported(self):
        errors = validate_manifest_row({"tile_id": "bad"})
        self.assertTrue(any("missing required fields" in error for error in errors))

    def test_invalid_bbox_is_reported(self):
        row = {
            "tile_id": "bad_bbox",
            "image_path": "datasets/kilnwatch/images/demo/bad_bbox.png",
            "lat": 29.0,
            "lon": 77.0,
            "source": "sample_demo_not_ground_truth",
            "split": "demo",
            "label": "sample",
            "kiln_detected": True,
            "bbox": [1, 2, "x", 4],
            "notes": "Sample/demo row only. Not ground truth.",
        }
        errors = validate_manifest_row(row)
        self.assertIn("bbox values must be numeric", errors)

    def test_invalid_json_line_is_reported(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            handle.write("{bad json}\n")
            path = Path(handle.name)
        try:
            issues = validate_manifest_file(path)
            self.assertEqual(len(issues), 1)
            self.assertIn("invalid JSON", issues[0].message)
        finally:
            path.unlink(missing_ok=True)

    def test_check_images_accepts_readable_png(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image_path = root / "tile.png"
            write_test_png(image_path)
            manifest_path = root / "manifest.jsonl"
            manifest_path.write_text(
                "{"
                f"\"tile_id\":\"tile\",\"image_path\":\"{image_path}\",\"lat\":29.0,\"lon\":77.0,"
                "\"source\":\"manual_image_import\",\"split\":\"demo\",\"label\":\"brick_kiln\","
                "\"kiln_detected\":true,\"notes\":\"real readable test image\""
                "}\n",
                encoding="utf-8",
            )

            self.assertEqual(validate_manifest_file(manifest_path, check_images=True), [])

    def test_check_images_rejects_placeholder_tile(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image_path = root / "tile.tile"
            image_path.write_bytes(b"placeholder")
            manifest_path = root / "manifest.jsonl"
            manifest_path.write_text(
                "{"
                f"\"tile_id\":\"tile\",\"image_path\":\"{image_path}\",\"lat\":29.0,\"lon\":77.0,"
                "\"source\":\"sample_demo_not_ground_truth\",\"split\":\"demo\",\"label\":\"sample\","
                "\"kiln_detected\":false,\"notes\":\"not ground truth placeholder\""
                "}\n",
                encoding="utf-8",
            )

            issues = validate_manifest_file(manifest_path, check_images=True)
            self.assertTrue(any("expected a real raster image extension" in issue.message for issue in issues))


def write_test_png(path: Path) -> None:
    from PIL import Image

    image = Image.new("RGB", (1, 1), color=(255, 0, 0))
    image.save(path, format="PNG")


if __name__ == "__main__":
    unittest.main()
