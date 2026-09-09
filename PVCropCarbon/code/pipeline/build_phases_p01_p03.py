#!/usr/bin/env python
"""P01+P02+P03: PV patch audit -> Site clustering (5 thresholds) -> Phase (construction-batch) geometry.

Runs on the compute server in the `pvcarbon` conda env. Read-only on source data.

Outputs (server, under PVCropCarbon/):
  metadata/analysis_grid.json
  work/patches_clean.gpkg           layer `patches`   (Albers, all 30023)
  work/site_membership.parquet      patch_id x threshold -> site_id  (150115 rows)
  work/phases.gpkg                  layers phases_d30/50/100/200/300  (Albers)
  outputs/phase_vector/phases_d{d}.shp   construction-batch vector for downstream attribute joins
  outputs/audits/p01_p03_report.md  + p01_pv_audit.json / p01_clcd_grid_audit.json
                                    + p02_site_diagnostics.json / p03_phase_summary.json

Card refs: PVCropCarbon/docs/experiment_design/P01,P02,P03.
Executed directly by Claude Code at user's direction, 2026-09-09.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
import shapely
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path("/data/ssd/haoweimu/NWAFU_PVCarbon")
SUB = ROOT / "PVCropCarbon"
PV_SHP = ROOT / "01_pv/pv_power_plants_china_2010_2022/raw/PV power plants of China from 2010 to 2022/PV power plants of China from 2010 to 2022.shp"
CLCD_DIR = Path("/data/hdd/haoweimu/datasets/D001_CLCD_2000-2025/raw")
ALBERS = ("+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +x_0=0 +y_0=0 "
          "+datum=WGS84 +units=m +no_defs")
THRESHOLDS = [30, 50, 100, 200, 300]

META, WORK, OUT = SUB / "metadata", SUB / "work", SUB / "outputs"
AUD, VEC = OUT / "audits", OUT / "phase_vector"
for p in (META, WORK, AUD, VEC):
    p.mkdir(parents=True, exist_ok=True)

LOG: list[str] = []
def log(m):
    s = f"[{time.strftime('%H:%M:%S')}] {m}"
    print(s, flush=True)
    LOG.append(s)

def qd(x, ps=(50, 90, 99)):
    x = np.asarray(x, float)
    d = {f"p{p}": float(np.percentile(x, p)) for p in ps}
    d["max"] = float(x.max())
    return d

t0 = time.time()

# ============================================================ P01a  analysis grid
log("P01a CLCD grid")
clcd = sorted(CLCD_DIR.glob("CLCD_v01_*_albert.tif"))
assert len(clcd) == 26, f"CLCD files: {len(clcd)}"
profs = []
for f in clcd:
    with rasterio.open(f) as ds:
        profs.append(dict(name=f.name, crs=ds.crs.to_wkt(), width=ds.width, height=ds.height,
                          transform=[round(v, 6) for v in list(ds.transform)[:6]],
                          nodata=ds.nodata, dtype=ds.dtypes[0]))
r0 = profs[0]
consistent = all(p[k] == r0[k] for p in profs for k in ("crs", "width", "height", "transform", "nodata", "dtype"))
with rasterio.open(clcd[0]) as ds:
    grid = dict(source=clcd[0].name, crs_wkt=ds.crs.to_wkt(), crs_proj4=ds.crs.to_proj4(),
                width=ds.width, height=ds.height, transform=list(ds.transform)[:6],
                pixel_size=[ds.transform.a, -ds.transform.e], nodata=ds.nodata,
                dtype=ds.dtypes[0], bounds=list(ds.bounds), all_26_consistent=bool(consistent))
(META / "analysis_grid.json").write_text(json.dumps(grid, indent=2, ensure_ascii=False))
json.dump(profs, open(AUD / "p01_clcd_grid_audit.json", "w"), indent=2, ensure_ascii=False)
log(f"  {grid['width']}x{grid['height']} nodata={grid['nodata']} consistent={consistent}")

# ============================================================ P01b  PV patch audit + clean
log("P01b PV patches")
g = gpd.read_file(PV_SHP)
assert len(g) == 30023
g = g.rename(columns={c: c.lower() for c in g.columns})
g = g.sort_values(["lon", "lat", "objectid"], kind="stable").reset_index(drop=True)
g["patch_id"] = [f"P{i:06d}" for i in range(len(g))]

valid_src = g.geometry.is_valid.values
g["geometry"] = g.geometry.make_valid()
g["geom_fixed"] = ~valid_src

ga = g.to_crs(ALBERS)
ga["pv_area_m2"] = ga.geometry.area
ga["pv_area_km2_src"] = pd.to_numeric(g["pv_area"], errors="coerce")
ratio = (ga["pv_area_km2_src"] / (ga["pv_area_m2"] / 1e6)).replace([np.inf, -np.inf], np.nan)
ratio_med = float(ratio.median())

def resolve(objectid, inst_time, inst_year):
    yr = int(inst_year)
    try:
        s = f"{int(round(float(inst_time))):08d}"
        if len(s) == 8:
            y, m, dd = int(s[:4]), int(s[4:6]), int(s[6:8])
            if 2009 <= y <= 2023 and 1 <= m <= 12 and 1 <= dd <= 31:
                return (s, yr, "ok") if y == yr else (s, y, "year_from_time")
    except Exception:
        pass
    return f"{yr}0701", yr, "fixed_missing"

res = [resolve(r.objectid, r.inst_time, r.inst_year) for r in ga.itertuples()]
ga["inst_date"] = [x[0] for x in res]
ga["inst_year"] = [int(x[1]) for x in res]
ga["inst_date_flag"] = [x[2] for x in res]
anom = ga.loc[ga.inst_date_flag != "ok",
              ["objectid", "patch_id", "inst_time", "inst_year", "inst_date", "inst_date_flag"]]

ga["n_parts"] = np.where(ga.geometry.geom_type.eq("MultiPolygon"),
                         ga.geometry.apply(lambda x: len(x.geoms) if x.geom_type == "MultiPolygon" else 1), 1)
ga["geom_md5"] = [hashlib.md5(shapely.to_wkb(x)).hexdigest() for x in ga.geometry.values]
dgrp = ga.groupby("geom_md5").size()
dup_groups = int((dgrp > 1).sum())
dup_patches = int(dgrp[dgrp > 1].sum())

# exact-duplicate geometries: keep lowest patch_id per md5, record the rest (audit trail).
ga = ga.sort_values("patch_id", kind="stable")
is_dup = ga.duplicated("geom_md5", keep="first")
dropped = ga.loc[is_dup, ["patch_id", "objectid", "inst_year", "inst_date", "major_type",
                          "pv_area_m2", "geom_md5"]].copy()
keep_map = ga.loc[~is_dup].set_index("geom_md5")["patch_id"]
dropped["kept_patch_id"] = dropped["geom_md5"].map(keep_map)
dropped.to_csv(AUD / "p01_duplicate_patches.csv", index=False)
n_dropped = int(is_dup.sum())
ga = ga.loc[~is_dup].reset_index(drop=True)

patches = ga[["patch_id", "objectid", "inst_year", "inst_date", "inst_date_flag", "major_type",
              "pv_area_m2", "pv_area_km2_src", "n_parts", "geom_fixed", "geom_md5", "lon", "lat",
              "geometry"]].copy()
patches.to_file(WORK / "patches_clean.gpkg", layer="patches", driver="GPKG")
N_PATCH = len(patches)  # 30023 - n_dropped

p01 = dict(
    n_src=30023, n_records=int(len(patches)), n_dropped_duplicates=n_dropped,
    src_crs=str(g.crs), analysis_crs=ALBERS, geom_invalid_src=int((~valid_src).sum()),
    area_unit_ratio_median=ratio_med, area_unit_is_km2=bool(0.9 <= ratio_med <= 1.1),
    pv_area_m2_sum=float(ga.pv_area_m2.sum()), pv_area_km2_src_sum=float(ga.pv_area_km2_src.sum()),
    duplicate_geom_groups=dup_groups, duplicate_patches=dup_patches,
    n_multipolygon=int((ga.n_parts > 1).sum()), n_offshore=int((ga.major_type == "Ocean area").sum()),
    inst_date_anomalies=anom.to_dict("records"),
    major_type_counts={k: int(v) for k, v in ga.major_type.value_counts().items()},
    inst_year_counts={int(k): int(v) for k, v in ga.inst_year.value_counts().sort_index().items()},
)
json.dump(p01, open(AUD / "p01_pv_audit.json", "w"), indent=2, ensure_ascii=False, default=str)
log(f"  n={len(patches)} unit_ratio={ratio_med:.4f} dup_groups={dup_groups} "
    f"multipoly={p01['n_multipolygon']} anomalies={len(anom)}")

# ============================================================ P02 + P03 per threshold
pa = patches.reset_index(drop=True)
n = len(pa)
pos = {pid: i for i, pid in enumerate(pa.patch_id)}
left = pa[["patch_id", "geometry"]]

memb, p02, p03 = [], {}, {}
for d in THRESHOLDS:
    log(f"P02 d={d} edges")
    buf = gpd.GeoDataFrame({"pl": pa.patch_id.values}, geometry=pa.geometry.buffer(d), crs=pa.crs)
    pr = gpd.sjoin(left, buf, predicate="intersects", how="inner")
    ai = pr.index.values
    bi = pr["pl"].map(pos).values
    m = ai != bi
    log(f"  edges={int(m.sum())}")
    adj = coo_matrix((np.ones(int(m.sum()), np.int8), (ai[m], bi[m])), shape=(n, n))
    adj = adj + adj.T
    ncomp, labels = connected_components(adj, directed=False)
    first = pd.Series(np.arange(n)).groupby(labels).min().sort_values()
    remap = {old: i for i, old in enumerate(first.index)}
    seq = np.fromiter((remap[l] for l in labels), int, n)
    sid = np.array([f"S{d:03d}_{s:06d}" for s in seq])
    pa["_site"] = sid
    memb.append(pd.DataFrame({"patch_id": pa.patch_id.values, "site_threshold_m": d, "site_id": sid}))

    # ---- site diagnostics (one dissolve) ----
    sd = pa.dissolve(by="_site")
    site_np = pa.groupby("_site").size()
    site_ny = pa.groupby("_site")["inst_year"].nunique()
    hull_area = sd.geometry.convex_hull.area
    b = sd.geometry.bounds
    span = np.hypot(b.maxx - b.minx, b.maxy - b.miny)
    cll = sd.geometry.centroid.to_crs(4326)
    big = pd.DataFrame({"patch_count": site_np, "hull_km2": hull_area / 1e6, "span_km": span / 1e3,
                        "n_years": site_ny, "lon": cll.x, "lat": cll.y}).sort_values("hull_km2", ascending=False)
    p02[d] = dict(
        n_sites=int(ncomp), n_single_patch=int((site_np == 1).sum()),
        patch_count=qd(site_np), hull_km2=qd(hull_area / 1e6), span_km=qd(span / 1e3),
        n_sites_ge3y=int((site_ny >= 3).sum()), n_sites_ge5y=int((site_ny >= 5).sum()),
        n_mega_gt50km2=int((hull_area > 5e7).sum()), n_mega_gt10km_span=int((span > 1e4).sum()),
        top25=big.head(25).round(3).reset_index().rename(columns={"_site": "site_id"}).to_dict("records"),
    )
    log(f"  sites={ncomp} single={int((site_np==1).sum())} mega>50km2={int((hull_area>5e7).sum())} "
        f"maxhull={hull_area.max()/1e6:.1f}km2")

    # ---- P03 Phase = (site_id, year) ----
    log(f"P03 d={d} dissolve phases")
    pa["year"] = pa.inst_year.astype(int)
    pgeom = pa.dissolve(by=["_site", "year"]).geometry
    grp = pa.groupby(["_site", "year"])
    agg = pd.DataFrame({
        "patch_cnt": grp.size(), "parea_sum": grp["pv_area_m2"].sum(),
        "date_min": grp["inst_date"].min(), "date_max": grp["inst_date"].max(),
        "offshore": grp["major_type"].apply(lambda s: bool((s == "Ocean area").any())),
    })
    aw = pa.groupby(["_site", "year", "major_type"])["pv_area_m2"].sum().reset_index()
    tot = aw.groupby(["_site", "year"])["pv_area_m2"].transform("sum")
    aw["frac"] = aw.pv_area_m2 / tot
    mode = aw.loc[aw.groupby(["_site", "year"])["pv_area_m2"].idxmax()].set_index(["_site", "year"])["major_type"].rename("mtype_mode")
    crop = aw[aw.major_type == "Cropland"].set_index(["_site", "year"])["frac"].rename("mtype_crop")
    mstat = pd.concat([mode, crop], axis=1)
    mstat["mtype_crop"] = mstat["mtype_crop"].fillna(0.0)

    ph = gpd.GeoDataFrame(agg.join(mstat), geometry=pgeom, crs=pa.crs).reset_index()
    ph = ph.rename(columns={"_site": "site_id"})
    ph["thr_m"] = d
    ph["phase_id"] = ph.site_id + "_" + ph.year.astype(str)
    ph["area_m2"] = ph.geometry.area
    ph["overlap_r"] = (1.0 - (ph.area_m2 / ph.parea_sum)).clip(lower=0.0)
    ph["n_parts"] = np.where(ph.geometry.geom_type.eq("MultiPolygon"),
                             ph.geometry.apply(lambda x: len(x.geoms) if x.geom_type == "MultiPolygon" else 1), 1)
    ph["site_np"] = ph.site_id.map(site_np.to_dict())
    ph["site_ny"] = ph.site_id.map(site_ny.to_dict())
    ph = ph[["phase_id", "site_id", "thr_m", "year", "patch_cnt", "area_m2", "parea_sum", "overlap_r",
             "n_parts", "date_min", "date_max", "mtype_mode", "mtype_crop", "offshore",
             "site_np", "site_ny", "geometry"]]
    ph.to_file(WORK / "phases.gpkg", layer=f"phases_d{d}", driver="GPKG")
    ph.to_file(VEC / f"phases_d{d}.shp", driver="ESRI Shapefile", encoding="utf-8")

    a = ph.area_m2.values
    p03[d] = dict(
        n_phases=int(len(ph)), sum_patch_cnt=int(ph.patch_cnt.sum()),
        phase_area_km2={**{k: v / 1e6 for k, v in qd(a).items()}, "total": float(a.sum()) / 1e6},
        n_single_patch=int((ph.patch_cnt == 1).sum()), n_multi_part=int((ph.n_parts > 1).sum()),
        n_offshore=int(ph.offshore.sum()), max_overlap_r=float(ph.overlap_r.max()),
        n_overlap_gt5pct=int((ph.overlap_r > 0.05).sum()),
        mtype_mode_counts={k: int(v) for k, v in ph.mtype_mode.value_counts().items()},
        n_crop_dominant=int((ph.mtype_crop >= 0.5).sum()), shp=str(VEC / f"phases_d{d}.shp"),
    )
    log(f"  phases={len(ph)} single={p03[d]['n_single_patch']} crop_dom={p03[d]['n_crop_dominant']} "
        f"max_overlap={ph.overlap_r.max():.3f}")

pd.concat(memb, ignore_index=True).to_parquet(WORK / "site_membership.parquet")
json.dump(p02, open(AUD / "p02_site_diagnostics.json", "w"), indent=2, ensure_ascii=False, default=str)
json.dump(p03, open(AUD / "p03_phase_summary.json", "w"), indent=2, ensure_ascii=False, default=str)

# ============================================================ report
def tbl(rows, hdr):
    return "\n".join(["| " + " | ".join(hdr) + " |", "|" + "|".join(["---"] * len(hdr)) + "|"]
                     + ["| " + " | ".join(str(x) for x in r) + " |" for r in rows])

L = [f"# P01–P03 运行报告", "",
     f"生成 {time.strftime('%Y-%m-%d %H:%M')} (+08) · 用时 {time.time()-t0:.0f}s · env `pvcarbon` · 直接执行",
     "", "## P01 分析网格", "",
     f"- CLCD 26 幅一致: **{consistent}** · {grid['width']}×{grid['height']} · nodata {grid['nodata']} · "
     f"pixel {grid['pixel_size']} · origin ({grid['transform'][2]:.3f}, {grid['transform'][5]:.3f})",
     f"- `{grid['crs_proj4']}`", "", "## P01 PV 图斑审计", "",
     f"- 源 30023 → 去重 {n_dropped} → **{p01['n_records']}** patch · 源 CRS {p01['src_crs']} · make_valid 修 {p01['geom_invalid_src']} 个无效几何",
     f"- 面积单位比值中位数 **{ratio_med:.4f}** → PV_Area 为 km²: **{p01['area_unit_is_km2']}** "
     f"(Σ源 {p01['pv_area_km2_src_sum']:.0f} vs Σ重算 {p01['pv_area_m2_sum']/1e6:.0f} km²)",
     f"- 完全重复几何组 {dup_groups}（{dup_patches} patch，每组保留 patch_id 最小者，其余记 `p01_duplicate_patches.csv`）"
     f" · MultiPolygon {p01['n_multipolygon']} · 海域面 {p01['n_offshore']}",
     "", f"- 建设日期异常 {len(anom)}:", "",
     tbl([[r["objectid"], r["patch_id"], r["inst_time"], r["inst_year"], r["inst_date"], r["inst_date_flag"]]
          for r in p01["inst_date_anomalies"]],
         ["objectid", "patch_id", "inst_time源", "inst_year源", "inst_date修", "flag"]),
     "", "- Major_type: " + " · ".join(f"{k} {v}" for k, v in p01["major_type_counts"].items()),
     "- inst_year: " + " ".join(f"{k}:{v}" for k, v in p01["inst_year_counts"].items()),
     "", "## P02 Site 诊断（5 阈值）", "",
     tbl([[d, p02[d]["n_sites"], p02[d]["n_single_patch"], int(p02[d]["patch_count"]["max"]),
           round(p02[d]["hull_km2"]["p99"], 2), round(p02[d]["hull_km2"]["max"], 1),
           round(p02[d]["span_km"]["max"], 1), p02[d]["n_sites_ge5y"], p02[d]["n_mega_gt50km2"]]
          for d in THRESHOLDS],
         ["阈值m", "Site数", "单patch", "maxPatch", "hull p99 km²", "hull max km²", "span max km", "Site≥5年", "巨型>50km²"]),
     "", "### 各阈值 Top5 巨型 Site（可去影像核对是否连片基地）", ""]
for d in THRESHOLDS:
    L += [f"**d={d}m**",
          tbl([[r["site_id"], r["patch_count"], r["hull_km2"], r["span_km"], r["n_years"], r["lon"], r["lat"]]
               for r in p02[d]["top25"][:5]],
              ["site_id", "patch", "hull km²", "span km", "年数", "lon", "lat"]), ""]
L += ["## P03 Phase（建设批次）汇总", "",
      tbl([[d, p03[d]["n_phases"], p03[d]["sum_patch_cnt"], p03[d]["n_single_patch"],
            round(p03[d]["phase_area_km2"]["p99"], 2), round(p03[d]["phase_area_km2"]["max"], 1),
            round(p03[d]["phase_area_km2"]["total"], 0), p03[d]["n_multi_part"],
            p03[d]["n_overlap_gt5pct"], p03[d]["n_crop_dominant"], p03[d]["n_offshore"]]
           for d in THRESHOLDS],
          ["阈值m", "Phase数", "Σpatch", "单patch", "area p99 km²", "area max km²", "Σarea km²",
           "多部件", "重叠>5%", "耕地主导", "海上"]),
      "", f"- 源 30023 patch，去 {n_dropped} 个完全重复几何（见 `p01_duplicate_patches.csv`）→ {len(patches)} patch",
      f"- Σpatch 应恒 = {len(patches)}: {[p03[d]['sum_patch_cnt'] for d in THRESHOLDS]}",
      "", "## 产物", "",
      f"- `work/patches_clean.gpkg`（{len(patches)} patch, Albers）· `work/site_membership.parquet`（{len(patches)*5} 行）",
      "- `work/phases.gpkg`（layers phases_d30/50/100/200/300）",
      "- `outputs/phase_vector/phases_d{30,50,100,200,300}.shp`  ← 建设批次矢量，下游按 `phase_id` 加属性",
      "  字段: phase_id site_id thr_m year patch_cnt area_m2 parea_sum overlap_r n_parts date_min date_max "
      "mtype_mode mtype_crop offshore site_np site_ny",
      "", "## 待定", "- 基线阈值（等 S07 人工样本）· 巨型 Site 是否加约束（看上表）· 县代码列（等 S06）",
      "", "---", "", "```", *LOG, "```"]
(AUD / "p01_p03_report.md").write_text("\n".join(L), encoding="utf-8")
log(f"DONE {time.time()-t0:.0f}s")
