from pathlib import Path
import re
import unittest


_IMPORT_RE = re.compile(r"^\s*(?:from\s+satellite_edge_node|import\s+satellite_edge_node)", re.MULTILINE)


class GroundStationBoundaryTests(unittest.TestCase):
    def test_ground_station_does_not_import_satellite_raw_tile_modules(self):
        # The architectural commitment is "no imports of, and no reads from,
        # the onboard side". Mentioning the module name or a path in a
        # user-facing help string is fine — that's documentation, not a
        # dependency. The runtime guard for the read-path is
        # `FORBIDDEN_CROP_SOURCE_FRAGMENTS` inside `kilnwatch/ground_station.py`.
        for path in _ground_station_surfaces():
            source = _production_source_for_boundary_scan(path)
            code_only = _strip_help_strings(source)
            self.assertIsNone(
                _IMPORT_RE.search(code_only),
                f"{path} must not import satellite_edge_node",
            )
            if path == Path("kilnwatch/ground_station.py"):
                self.assertIn("FORBIDDEN_CROP_SOURCE_FRAGMENTS", source)
            for forbidden in ("data/raw_tiles", "data/final_demo_tiles", "datasets/roboflow"):
                self.assertNotIn(
                    forbidden,
                    code_only,
                    f"{path} must not reference {forbidden} outside help/docstring text",
                )
            if path == Path("kilnwatch/ground_station.py"):
                continue
            self.assertNotIn('".tile', code_only, f"{path} must not use placeholder .tile fixtures as previews")
            self.assertNotIn("'.tile", code_only, f"{path} must not use placeholder .tile fixtures as previews")


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


_HTML_BLOB_RE = re.compile(
    r'(?:st\.markdown|_html)\s*\(\s*(?:f?"""|f?\'\'\').*?(?:"""|\'\'\')\s*,?',
    re.DOTALL,
)
# Triple-quoted help/HTML blocks rendered into the dashboard via st.markdown
# or the local _html() helper. Strip them so command examples
# (e.g. `python -m satellite_edge_node...`) don't trip the substring scan;
# those are documentation, not code paths.


def _strip_help_strings(source: str) -> str:
    return _HTML_BLOB_RE.sub("", source)


if __name__ == "__main__":
    unittest.main()
