#!/usr/bin/env python3
"""Verify CCD V1 archive structure without extracting it."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import sys
import zipfile


EXPECTED_BYTES = 10_163_712_508
EXPECTED_TIFS = 672
YEARS = {str(year) for year in range(2001, 2025)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    archive = args.archive

    if archive.stat().st_size != EXPECTED_BYTES:
        raise RuntimeError(f"unexpected bytes: {archive.stat().st_size}")

    with zipfile.ZipFile(archive) as bundle:
        bad = bundle.testzip()
        if bad:
            raise RuntimeError(f"CRC failure: {bad}")
        tifs = [item for item in bundle.infolist() if item.filename.lower().endswith(".tif")]
        if len(tifs) != EXPECTED_TIFS:
            raise RuntimeError(f"expected {EXPECTED_TIFS} GeoTIFFs, found {len(tifs)}")
        year_counts: Counter[str] = Counter()
        top_dirs: set[str] = set()
        for item in tifs:
            parts = [part for part in item.filename.split("/") if part]
            if len(parts) > 1:
                top_dirs.add(parts[0])
            matches = set(re.findall(r"(?<!\d)(20(?:0[1-9]|1\d|2[0-4]))(?!\d)", item.filename))
            for year in matches:
                year_counts[year] += 1

    missing_years = sorted(YEARS - set(year_counts))
    print(f"ARCHIVE_BYTES\t{archive.stat().st_size}")
    print(f"TIFF_COUNT\t{len(tifs)}")
    print(f"TOP_LEVEL_DIRS\t{len(top_dirs)}")
    print("YEAR_COUNTS\t" + ";".join(f"{year}:{year_counts[year]}" for year in sorted(year_counts)))
    if missing_years:
        print("YEAR_NAME_WARNING\t" + ",".join(missing_years))
        return 3
    print("ARCHIVE_STRUCTURE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
