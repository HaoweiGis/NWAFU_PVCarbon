#!/usr/bin/env python
"""T-2026-09-24-soilgrids-freeze: freeze SoilGrids mean tiles, no download."""
import json, hashlib, re
from pathlib import Path
import rasterio
import numpy as np

ROOT = Path("/data/ssd/haoweimu/NWAFU_PVCarbon/05_carbon/soilgrids_250m_mean_0_30cm")
TILES, META = ROOT / "tiles", ROOT / "metadata"
META.mkdir(parents=True, exist_ok=True)

pat = re.compile(r"(\w+)_(\d+-\d+cm)_mean_W(\d+)_E(\d+)_S(\d+)_N(\d+)\.tif$")
rows = []
for f in sorted(TILES.glob("*.tif")):
    m = pat.match(f.name)
    if not m:
        rows.append({"name": f.name, "parsed": False}); continue
    var, depth, w, e, s, n = m.groups()
    rows.append({"name": f.name, "var": var, "depth": depth, "w": w, "e": e, "s": s, "n": n, "parsed": True})

by_vd = {}
for r in rows:
    if r["parsed"]:
        by_vd.setdefault((r["var"], r["depth"]), []).append(r["name"])
counts = {f"{v}_{d}": len(files) for (v, d), files in by_vd.items()}

# checksum + crs/nodata/resolution audit (sample-based for speed: all files, but only read header not full pixels)
manifest_rows = []
crs_set, res_set, nodata_set = set(), set(), set()
for f in sorted(TILES.glob("*.tif")):
    h = hashlib.sha256()
    with open(f, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    with rasterio.open(f) as ds:
        crs_set.add(str(ds.crs))
        res_set.add((round(ds.transform.a, 6), round(-ds.transform.e, 6)))
        nodata_set.add(ds.nodata)
        manifest_rows.append((f.name, h.hexdigest(), str(ds.crs), ds.width, ds.height, ds.nodata))

with open(META / "frozen_manifest.csv", "w", encoding="utf-8") as fh:
    fh.write("file,sha256,crs,width,height,nodata\n")
    for row in manifest_rows:
        fh.write(",".join(str(x) for x in row) + "\n")

# The 8 pre-existing .vrt at ROOT are SoilGrids' OWN global reference VRTs (Homolosine, pointing at
# their remote tileSG-*/*.tif scheme) -- NOT a local mosaic of our China tiles/, and NOT readable
# (broken relative paths). Record this finding, then build OUR OWN vrt per var-depth from tiles/.
existing_vrt_note = []
for vrt in sorted(ROOT.glob("*.vrt")):
    try:
        with rasterio.open(vrt) as ds:
            existing_vrt_note.append(f"{vrt.name}: OPENS size={ds.width}x{ds.height} crs={ds.crs}")
    except Exception as e:
        existing_vrt_note.append(f"{vrt.name}: BROKEN ({type(e).__name__}) -- this is SoilGrids' own "
                                 f"upstream global VRT (Homolosine, remote tileSG-* paths), not a local mosaic")

vrt_report = []
built_dir = ROOT / "mosaics_china"
built_dir.mkdir(exist_ok=True)
import subprocess
for (var, depth), files in sorted(by_vd.items()):
    out = built_dir / f"{var}_{depth}_mean_china.vrt"
    paths = [str(TILES / n) for n in files]
    subprocess.run(["gdalbuildvrt", "-q", str(out)] + paths, check=True)
    with rasterio.open(out) as ds:
        mid = ds.height // 2
        row = ds.read(1, window=((mid, mid + 1), (0, ds.width))).astype("float64").ravel()
        nodata = ds.nodata
        valid = row[row != nodata] if nodata is not None else row
        frac_valid = float((row != nodata).sum()) / len(row) if nodata is not None and len(row) else 1.0
        vrt_report.append(f"{out.name}: n_tiles={len(files)} size={ds.width}x{ds.height} crs={ds.crs} "
                          f"mid-row valid_frac={frac_valid:.3f} "
                          f"sample_range=[{valid.min() if len(valid) else 'NA'},{valid.max() if len(valid) else 'NA'}]")

unit_formulas = {
    "bdod": "cg/cm3 -> kg/m3: value * 10",
    "cfvo": "cm3/dm3 -> % (volume fraction): value / 10",
    "soc": "dg/kg -> g/kg: value / 10  (then g/kg -> fraction: /1000)",
}

report = [
    "# SoilGrids mean 层冻结报告", "",
    f"- tile 总数: {len(rows)}（未解析命名: {sum(1 for r in rows if not r['parsed'])}）",
    f"- 变量-深度组合 tile 数: {json.dumps(counts, ensure_ascii=False)}",
    f"- CRS 集合: {crs_set}", f"- 分辨率集合(度): {res_set}", f"- NoData 集合: {nodata_set}",
    "", "## 既有 8 个 .vrt 的真实身份（重要更正）", "",
    "**此前认为这 8 个 .vrt 是本地已建好的中国镶嵌——错误。** 实际是 SoilGrids 官方全球产品自带的"
    "参考 VRT（Interrupted Goode Homolosine 投影，指向其远程 `tileSG-*` 分块方案），本地没有对应"
    "全球瓦片，**无法读取**。真正可用的是 `tiles/` 下 216 个中国范围 GeoTIFF。本任务已用"
    "`gdalbuildvrt` 在 `mosaics_china/` 下重新构建了 9 个变量-深度组合各自的中国镶嵌。", "",
] + [f"- {v}" for v in existing_vrt_note] + [
    "", "## 新建本地镶嵌抽样（中间行）", "",
] + [f"- {v}" for v in vrt_report] + [
    "", "## 单位换算公式（供 P09 引用，本任务不做换算）", "",
] + [f"- {k}: {v}" for k, v in unit_formulas.items()] + [
    "", "## 5%/95% 分位数缺口评估", "",
    "- 当前只有 mean 层；SoilGrids 官方同时提供 Q0.05/Q0.95，用于 Monte Carlo 不确定性传播（P09 要求）。",
    "- 工作量估计：每变量-深度组合再下 2 个分位数 = 9 x 2 = 18 组，按 mean 层同等 tile 数量级，"
    "预计数据量与下载时间与 mean 层相当（约 2 GB / 组量级，视变量而定）。建议列入第一层后续批次。",
]
(META / "freeze_report.md").write_text("\n".join(report), encoding="utf-8")
json.dump({"counts": counts, "crs": list(crs_set), "res": list(res_set), "nodata": list(map(str, nodata_set))},
          open(META / "frozen_manifest.json", "w"), indent=2, ensure_ascii=False)
print("counts:", counts)
print("crs:", crs_set, "res:", res_set, "nodata:", nodata_set)
