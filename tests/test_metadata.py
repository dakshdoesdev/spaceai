import unittest

from kilnwatch.ingestion.dataset import extension_for_content_type, safe_timestamp


class MetadataHelpersTest(unittest.TestCase):
    def test_safe_timestamp_is_filename_friendly(self):
        self.assertEqual(safe_timestamp("2026-05-05T12:00:00Z"), "2026-05-05T12-00-00Z")

    def test_extension_for_common_image_content_types(self):
        self.assertEqual(extension_for_content_type("image/png"), ".png")
        self.assertEqual(extension_for_content_type("image/jpeg; charset=binary"), ".jpg")
        self.assertEqual(extension_for_content_type("application/octet-stream"), ".bin")


if __name__ == "__main__":
    unittest.main()
