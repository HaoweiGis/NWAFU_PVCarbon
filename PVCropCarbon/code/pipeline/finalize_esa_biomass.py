#!/usr/bin/env python
"""Sanity-check ESA CCI Biomass v7 downloads: readability, value ranges, per-year counts."""
import json
from pathlib import Path
from collections import defaultdict
import rasterio
import numpy as np

ROOT = Path("/data/ssd/haoweimu/NWAFU_PVCarbon/05_carbon/esa_cci_biomass_v7_china")
RAW, META = ROOT / "raw", ROOT / "metadata"

tifs = sorted(RAW.glob("*.tif"))
by_year_var = defaultdict(int)
bad = []
sample_stats = []
import random
random.seed(1)
sample_files = random.sample(tifs, min(10, len(tifs)))

for f in tifs:
    parts = f.stem.split("-")
    # filename: {tile}_ESACCI-BIOMASS-L4-{VAR}-MERGED-100m-{year}-fv7.0
    tile_and_var = f.stem.split("_ESACCI")[0]
    year = f.stem.split("-")[-2]
    var = "AGB_SD" if "AGB_SD" in f.name else "AGB"
    by_year_var[(year, var)] += 1

for f in sample_files:
    try:
        with rasterio.open(f) as ds:
            data = ds.read(1, out_shape=(1, min(500, ds.height), min(500, ds.width)))
            nodata = ds.nodata
            valid = data[data != nodata] if nodata is not None else data[~np.isnan(data)]
            sample_stats.append(f"{f.name}: crs={ds.crs} size={ds.width}x{ds.height} "
                                f"nodata={nodata} sample_range=[{valid.min():.1f},{valid.max():.1f}] "
                                f"(n_valid={valid.size})")
    except Exception as e:
        bad.append(f"{f.name}: {e}")

total_bytes = sum(f.stat().st_size for f in tifs)
year_var_table = sorted(by_year_var.items())

report = [
    "# ESA CCI Biomass v7 下载与核对报告", "",
    f"- 文件数: {len(tifs)} · 总大小: {total_bytes/1e9:.1f} GB",
    f"- 年份 x 变量 文件数（应各 25，对应 25 个候选 10°瓦片）:", "",
] + [f"  - {y} {v}: {n}" + ("" if n == 25 else " ⚠ 不等于 25，需核对是否有海域瓦片本就无数据")
     for (y, v), n in year_var_table] + [
    "", "## 抽样 10 个文件读取 + 数值范围（decimated 500x500 读取）", "",
] + [f"- {s}" for s in sample_stats] + [
    "", "## 异常", "",
] + ([f"- {b}" for b in bad] if bad else ["- 无"]) + [
    "", "## 已知问题（记录，不在本任务修复）", "",
    "- 首次下载中 1 个文件（`N40E100_...2017...AGB...tif`）因连接中断产生**部分文件**"
    "（16.3MB，应为 58.7MB），而脚本的存在性检查只判断文件是否存在+非空，**不判断是否完整**，"
    "若不是人工复核会被误判为已下载成功。已手工删除重下并核实。"
    "**建议后续下载脚本改为按 `Content-Length` 校验实际大小，而不是只看是否存在。**",
]
(META / "download_report.md").write_text("\n".join(report), encoding="utf-8")
print("\n".join(report))
