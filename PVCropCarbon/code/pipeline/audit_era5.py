#!/usr/bin/env python
"""T-2026-09-24-era5-freeze-audit: audit ERA5-Land raw grib files, no download."""
import json, re, hashlib
from pathlib import Path
from collections import defaultdict

ROOT = Path("/data/hdd/haoweimu/datasets/D005_ERA5_Land")
RAW, META = ROOT / "raw", ROOT / "metadata"
META.mkdir(parents=True, exist_ok=True)

pat = re.compile(r"ERA5Land_(\d{4})_(\d{2})_([a-z0-9]+)\.grib$")
rows = []
bad = []
for f in sorted(RAW.glob("*.grib")):
    m = pat.match(f.name)
    if not m:
        bad.append(f.name); continue
    y, mo, var = m.groups()
    rows.append((int(y), int(mo), var, f.stat().st_size))

years = sorted({r[0] for r in rows})
vars_ = sorted({r[2] for r in rows})
matrix = defaultdict(set)
for y, mo, var, sz in rows:
    matrix[(y, var)].add(mo)

print(f"files={len(rows)} unmatched={len(bad)} years={years[0]}-{years[-1]} n_years={len(years)} vars={vars_}")

# completeness: for each year x var, expect 12 months (except possibly current/boundary years)
gap_lines = []
for y in years:
    for v in vars_:
        months = matrix.get((y, v), set())
        if len(months) != 12:
            missing = sorted(set(range(1, 13)) - months)
            gap_lines.append(f"{y} {v}: {len(months)}/12, missing months={missing}")

with open(META / "era5_frozen_manifest.csv", "w", encoding="utf-8") as fh:
    fh.write("year,month,var,bytes\n")
    for y, mo, var, sz in sorted(rows):
        fh.write(f"{y},{mo},{var},{sz}\n")

manifest = {
    "n_files": len(rows), "n_unmatched": len(bad), "unmatched_names": bad[:50],
    "year_min": years[0], "year_max": years[-1], "n_years": len(years),
    "variables": vars_, "n_gap_year_var": len(gap_lines),
}
json.dump(manifest, open(META / "era5_frozen_manifest.json", "w"), indent=2, ensure_ascii=False)

# legacy_partial cross-check
legacy = list((ROOT / "legacy_partial").glob("*.part")) if (ROOT / "legacy_partial").exists() else []
legacy_note = []
for lp in legacy:
    m = re.match(r"ERA5Land_(\d{4})_(\d{2})_(.+)\.grib\.part$", lp.name)
    if m:
        y, mo, tag = m.groups()
        covered = any(r[0] == int(y) and r[1] == int(mo) for r in rows)
        legacy_note.append(f"{lp.name}: year={y} month={mo} tag={tag} superseded_by_raw={covered}")
    else:
        legacy_note.append(f"{lp.name}: unparsed")

# sample 5 files readability via rasterio (grib driver)
sample_report = []
try:
    import rasterio
    import random
    random.seed(0)
    sample = random.sample(rows, min(5, len(rows)))
    for y, mo, var, sz in sample:
        fn = RAW / f"ERA5Land_{y}_{mo:02d}_{var}.grib"
        try:
            with rasterio.open(fn) as ds:
                sample_report.append(f"{fn.name}: OK crs={ds.crs} size={ds.width}x{ds.height} count={ds.count} dtype={ds.dtypes[0]}")
        except Exception as e:
            sample_report.append(f"{fn.name}: FAIL {e}")
except Exception as e:
    sample_report.append(f"rasterio import/sample failed: {e}")

report = [
    "# ERA5-Land 冻结审计报告", "",
    f"- 文件数: {len(rows)}（未解析命名 {len(bad)} 个: {bad[:20]}）",
    f"- 年份范围: {years[0]}–{years[-1]}（{len(years)} 年）",
    f"- 变量集: {vars_}",
    f"- 年x变量 应有 12 个月，缺口条目数: {len(gap_lines)}",
    "", "## 缺口明细（若有）", "",
] + [f"- {g}" for g in gap_lines] + [
    "", "## legacy_partial 交叉核对", "",
] + [f"- {n}" for n in legacy_note] + [
    "", "## 抽样可读性（5 个文件）", "",
] + [f"- {s}" for s in sample_report] + [
    "", "## 结论：2010–2022（观测窗口）+ 2005–2022（含建设前5年缓冲）逐月逐变量是否齐全", "",
    f"- 2005-2022 覆盖: {'完整' if all((y,v) in matrix and len(matrix[(y,v)])==12 for y in range(2005,2023) for v in vars_) else '有缺口，见上表'}",
]
(META / "era5_freeze_report.md").write_text("\n".join(report), encoding="utf-8")
print("DONE, gaps:", len(gap_lines))
