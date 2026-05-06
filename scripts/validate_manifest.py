#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kilnwatch.datasets.manifest import validate_manifest_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate KilnWatch manifest JSONL files.")
    parser.add_argument("manifest", nargs="+", type=Path)
    parser.add_argument("--check-images", action="store_true", help="also require image_path files to be readable raster images")
    args = parser.parse_args()

    failed = False
    for path in args.manifest:
        issues = validate_manifest_file(path, check_images=args.check_images)
        if issues:
            failed = True
            for issue in issues:
                print(f"{path}:{issue.line_number}: {issue.message}", file=sys.stderr)
        else:
            print(f"{path}: OK")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
