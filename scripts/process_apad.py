#!/usr/bin/env python
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from kilnwatch.datasets.adapters.apad_igp import ApadIgpAdapter


def main() -> int:
    adapter = ApadIgpAdapter()
    
    csv_files = [
        Path("datasets/Brick_Kilns/Brick_Kilns_IND-Main_coal.csv"),
        Path("datasets/Brick_Kilns/Brick_Kilns_PK-Main_coal.csv"),
        Path("datasets/Brick_Kilns/Brick_kilns_BAN-Main_coal.csv"),
    ]
    
    out_dir = Path("datasets/kilnwatch/manifests")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    for csv_file in csv_files:
        if not csv_file.exists():
            print(f"Skipping {csv_file}, does not exist.")
            continue
            
        out_file = out_dir / f"apad_igp_{csv_file.stem}.jsonl"
        print(f"Converting {csv_file} -> {out_file}")
        try:
            adapter.convert(csv_file, out_file)
            print(f"Successfully converted to {out_file}")
        except Exception as e:
            print(f"Failed to convert {csv_file}: {e}")
            return 1
            
    print("Done generating APAD IGP manifests.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
