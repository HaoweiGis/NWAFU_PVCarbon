#!/usr/bin/env python3
"""Read-only preflight for PVCropCarbon production."""

from __future__ import annotations

import csv
import os
from pathlib import Path
import sys


ROOT = Path(os.environ.get("PVCROP_ROOT", Path(__file__).resolve().parents[1]))
STATUS_FILE = ROOT / "metadata" / "source_status.tsv"
REQUIRED_DIRS = {
    "PV_SOURCE": Path(os.environ.get("PV_SOURCE", "/data/ssd/haoweimu/NWAFU_PVCarbon/01_pv/pv_power_plants_china_2010_2022")),
    "CLCD_SOURCE": Path(os.environ.get("CLCD_SOURCE", "/data/hdd/haoweimu/datasets/D001_CLCD_2000-2025")),
    "ERA5_SOURCE": Path(os.environ.get("ERA5_SOURCE", "/data/hdd/haoweimu/datasets/D005_ERA5_Land")),
    "CROP_SOURCE": Path(os.environ.get("CROP_SOURCE", "/data/ssd/haoweimu/NWAFU_PVCarbon/03_crop")),
    "CARBON_SOURCE": Path(os.environ.get("CARBON_SOURCE", "/data/ssd/haoweimu/NWAFU_PVCarbon/05_carbon")),
    "BOUNDARY_SOURCE": Path(os.environ.get("BOUNDARY_SOURCE", "/data/ssd/haoweimu/NWAFU_PVCarbon/09_boundaries")),
}


def main() -> int:
    failures: list[str] = []
    for label, path in REQUIRED_DIRS.items():
        state = "OK" if path.is_dir() else "MISSING"
        print(f"PATH\t{state}\t{label}\t{path}")
        if state != "OK":
            failures.append(f"missing path: {label}")

    if not STATUS_FILE.is_file():
        print(f"STATUS\tMISSING\t{STATUS_FILE}")
        return 2

    with STATUS_FILE.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream, delimiter="\t"))
    blocking = [row for row in rows if "CRITICAL" in row["status"]]
    for row in blocking:
        print(f"BLOCKER\t{row['id']}\t{row['status']}\t{row['blocking_reason']}")
    failures.extend(f"{row['id']}: {row['status']}" for row in blocking)

    if failures:
        print(f"PRODUCTION_BLOCKED\t{len(failures)}")
        return 3
    print("PREFLIGHT_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
