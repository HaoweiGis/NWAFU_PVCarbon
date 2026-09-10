#!/usr/bin/env python
"""P02b: Site-level vector — one row per Site, with per-Site patch count and aggregates.

Companion to phases_d{d}.shp (which is Phase-level). Reads existing P01/P02 outputs
(no recompute of clustering). Runs on the server in the `pvcarbon` env.

Outputs (server, PVCropCarbon/):
  work/sites.gpkg                       layers sites_d30/50/100/200/300 (Albers)
  outputs/site_vector/sites_d{d}.shp    one row per Site
  outputs/audits/p02b_site_vector_summary.json

Card ref: docs/experiment_design/P02. Executed directly by Claude Code, user's direction.
"""
from __future__ import annotations
import json, time
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd

SUB = Path("/data/ssd/haoweimu/NWAFU_PVCarbon/PVCropCarbon")
WORK, OUT = SUB / "work", SUB / "outputs"
VEC, AUD = OUT / "site_vector", OUT / "audits"
VEC.mkdir(parents=True, exist_ok=True)
THRESHOLDS = [30, 50, 100, 200, 300]

t0 = time.time()
patches = gpd.read_file(WORK / "patches_clean.gpkg", layer="patches")   # 29,979, Albers
memb = pd.read_parquet(WORK / "site_membership.parquet")                # patch_id x thr -> site_id
print(f"patches {len(patches)}  membership {len(memb)}", flush=True)

summary = {}
for d in THRESHOLDS:
    m = memb.loc[memb.site_threshold_m == d, ["patch_id", "site_id"]]
    p = patches.merge(m, on="patch_id", how="inner")
    assert len(p) == len(patches), f"d={d}: join lost rows"

    # Site geometry = union of member patches
    geom = p.dissolve(by="site_id").geometry
    g = p.groupby("site_id")

    # area-weighted dominant prior land type + cropland fraction (vectorized)
    aw = p.groupby(["site_id", "major_type"])["pv_area_m2"].sum().reset_index()
    tot = aw.groupby("site_id")["pv_area_m2"].transform("sum")
    aw["frac"] = aw.pv_area_m2 / tot
    mode = aw.loc[aw.groupby("site_id")["pv_area_m2"].idxmax()].set_index("site_id")["major_type"].rename("mtype_mode")
    crop = aw[aw.major_type == "Cropland"].set_index("site_id")["frac"].rename("mtype_crop")

    agg = pd.DataFrame({
        "n_patch": g.size(),                              # <-- patches per Site
        "n_phase": g["inst_year"].nunique(),              # build years = number of Phases
        "year_min": g["inst_year"].min(),
        "year_max": g["inst_year"].max(),
        "parea_sum": g["pv_area_m2"].sum(),
        "offshore": g["major_type"].apply(lambda s: bool((s == "Ocean area").any())),
    }).join(mode).join(crop)
    agg["mtype_crop"] = agg["mtype_crop"].fillna(0.0)

    s = gpd.GeoDataFrame(agg, geometry=geom, crs=p.crs).reset_index()
    s["thr_m"] = d
    s["area_m2"] = s.geometry.area
    b = s.geometry.bounds
    s["hull_km2"] = s.geometry.convex_hull.area / 1e6
    s["span_km"] = np.hypot(b.maxx - b.minx, b.maxy - b.miny) / 1e3
    s["n_parts"] = np.where(s.geometry.geom_type.eq("MultiPolygon"),
                            s.geometry.apply(lambda x: len(x.geoms) if x.geom_type == "MultiPolygon" else 1), 1)
    s = s[["site_id", "thr_m", "n_patch", "n_phase", "year_min", "year_max",
           "area_m2", "parea_sum", "hull_km2", "span_km", "n_parts",
           "mtype_mode", "mtype_crop", "offshore", "geometry"]]

    s.to_file(WORK / "sites.gpkg", layer=f"sites_d{d}", driver="GPKG")
    s.to_file(VEC / f"sites_d{d}.shp", driver="ESRI Shapefile", encoding="utf-8")

    npv = s.n_patch.values
    summary[d] = dict(
        n_sites=int(len(s)), sum_n_patch=int(s.n_patch.sum()),
        n_patch={"p50": float(np.percentile(npv, 50)), "p90": float(np.percentile(npv, 90)),
                 "p99": float(np.percentile(npv, 99)), "max": int(npv.max())},
        n_single_patch=int((npv == 1).sum()), n_multi_year=int((s.n_phase > 1).sum()),
        shp=str(VEC / f"sites_d{d}.shp"),
    )
    print(f"  d={d}: sites={len(s)} Σn_patch={int(s.n_patch.sum())} "
          f"single={int((npv==1).sum())} max_n_patch={int(npv.max())}", flush=True)

json.dump(summary, open(AUD / "p02b_site_vector_summary.json", "w"), indent=2, ensure_ascii=False)
print(f"DONE {time.time()-t0:.0f}s", flush=True)
