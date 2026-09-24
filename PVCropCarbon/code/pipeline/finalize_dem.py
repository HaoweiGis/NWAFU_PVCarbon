#!/usr/bin/env python
"""Build final DEM mosaic + sanity checks after all tiles downloaded."""
import json, subprocess
from pathlib import Path
import rasterio
import numpy as np

ROOT = Path("/data/ssd/haoweimu/NWAFU_PVCarbon/07_topography/copernicus_glo30")
RAW, META = ROOT / "raw", ROOT / "metadata"

tifs = sorted(RAW.glob("*.tif"))
vrt = ROOT / "dem_china.vrt"
subprocess.run(["gdalbuildvrt", "-q", str(vrt)] + [str(f) for f in tifs], check=True)

with rasterio.open(vrt) as ds:
    info = dict(crs=str(ds.crs), width=ds.width, height=ds.height, nodata=ds.nodata,
               res=(ds.transform.a, -ds.transform.e))
    # sanity samples: (name, lon, lat, expected_range)
    samples = [
        ("青藏高原(拉萨附近)", 91.1, 29.65, (3000, 6000)),
        ("华北平原(石家庄附近)", 114.5, 38.0, (0, 200)),
        ("塔里木盆地", 83.0, 40.0, (500, 1200)),
        ("珠峰东坡附近(高值)", 87.0, 28.0, (3000, 8900)),
        ("东南沿海低地(福州)", 119.3, 26.1, (0, 150)),
    ]
    sample_report = []
    for name, lon, lat, (lo, hi) in samples:
        row, col = ds.index(lon, lat)
        try:
            val = ds.read(1, window=((row, row + 1), (col, col + 1)))[0, 0]
            ok = lo <= val <= hi
            sample_report.append(f"{name} ({lon},{lat}): {val:.0f} m, 预期[{lo},{hi}] -> {'OK' if ok else '异常'}")
        except Exception as e:
            sample_report.append(f"{name}: 读取失败 {e}")

manifest = json.load(open(META / "tile_manifest.json"))
statuses = {}
for m in manifest:
    statuses[m["status"]] = statuses.get(m["status"], 0) + 1
n_land_ok = sum(v for k, v in statuses.items() if k in ("OK", "OK_RETRY", "SKIP_EXISTS"))
total_bytes = sum(f.stat().st_size for f in tifs)

report = [
    "# Copernicus GLO-30 DEM 下载报告", "",
    f"- 候选瓦片: {len(manifest)} · 成功: {n_land_ok} · 确认无数据(404): {statuses.get('HTTP_404',0)} · "
    f"最终失败: {statuses.get('FAILED_AFTER_RETRY',0)}",
    f"- 状态分布: {statuses}",
    f"- 实际下载瓦片数: {len(tifs)} · 总大小: {total_bytes/1e9:.1f} GB",
    f"- VRT: {vrt.name} · CRS {info['crs']} · {info['width']}x{info['height']} · "
    f"分辨率 {info['res']} 度 · nodata {info['nodata']}",
    "", "## 抽样高程健全性检查", "",
] + [f"- {s}" for s in sample_report] + [
    "", "## 说明", "",
    "- 瓦片选择范围基于 pilot 候选边界（09_boundaries 的 geoBoundaries，非权威，仅供选片）缓冲 1 度，"
    "覆盖中国及邻近少量境外区域，不是精确中国国界裁剪——正式坡度计算前应按权威边界（S06）裁剪。",
    "- 坡度算法本任务不做，留给使用坡度的实验卡决定窗口/方法。",
]
(META / "download_report.md").write_text("\n".join(report), encoding="utf-8")
print("\n".join(report))
