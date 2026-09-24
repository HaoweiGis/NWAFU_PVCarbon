#!/usr/bin/env python
"""T-2026-09-24-esa-biomass-download: ESA CCI Biomass v7.0 AGB + AGB_SD, China-intersecting
10x10deg tiles, years 2010-2012 + 2015-2022 (V1 minimum requirement). CEDA anonymous HTTPS,
no auth needed (probed 2026-09-24: dap.ceda.ac.uk/neodc/esacci/biomass/... returns 200 anonymously).
"""
import json, hashlib, time
from pathlib import Path
import urllib.request
import geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union

ROOT = Path("/data/ssd/haoweimu/NWAFU_PVCarbon/05_carbon/esa_cci_biomass_v7_china")
RAW, META = ROOT / "raw", ROOT / "metadata"
RAW.mkdir(parents=True, exist_ok=True)
META.mkdir(parents=True, exist_ok=True)

BASE = "https://dap.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/v7.0/geotiff"
PILOT_ZIP = Path("/data/ssd/haoweimu/NWAFU_PVCarbon/09_boundaries/pilot_geoboundaries_adm2_2017/geoBoundaries-CHN-ADM2-all.zip")
YEARS = [2010, 2011, 2012, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022]
VARIANTS = ["AGB", "AGB_SD"]

def tile_prefix(lat, lon):
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"{ns}{abs(lat):02d}{ew}{abs(lon):03d}"

gdf = gpd.read_file(f"zip://{PILOT_ZIP}")
outline = unary_union(gdf.geometry.values).buffer(1.0)
minx, miny, maxx, maxy = outline.bounds
lat0 = (int(miny) // 10) * 10 - 10
lat1 = (int(maxy) // 10) * 10 + 10
lon0 = (int(minx) // 10) * 10 - 10
lon1 = (int(maxx) // 10) * 10 + 10
candidates = []
for lat in range(lat0, lat1 + 1, 10):
    for lon in range(lon0, lon1 + 1, 10):
        cell = box(lon, lat, lon + 10, lat + 10)
        if cell.intersects(outline):
            candidates.append((lat, lon))
print(f"outline bounds={outline.bounds} candidate 10x10 tiles={len(candidates)} "
      f"years={len(YEARS)} variants={len(VARIANTS)} -> up to {len(candidates)*len(YEARS)*len(VARIANTS)} files",
      flush=True)

manifest = []
n_ok, n_404, n_fail, total_bytes = 0, 0, 0, 0
t0 = time.time()
i = 0
total_planned = len(candidates) * len(YEARS) * len(VARIANTS)
for lat, lon in candidates:
    prefix = tile_prefix(lat, lon)
    for year in YEARS:
        for var in VARIANTS:
            i += 1
            fname = f"{prefix}_ESACCI-BIOMASS-L4-{var}-MERGED-100m-{year}-fv7.0.tif"
            url = f"{BASE}/{year}/{fname}"
            out = RAW / fname
            if out.exists() and out.stat().st_size > 0:
                status = "SKIP_EXISTS"; n_ok += 1
            else:
                try:
                    urllib.request.urlretrieve(url, out)
                    status = "OK"; n_ok += 1
                except urllib.error.HTTPError as e:
                    status = f"HTTP_{e.code}"
                    if e.code == 404:
                        n_404 += 1
                    else:
                        n_fail += 1
                except Exception as e:
                    status = f"ERR_{type(e).__name__}"; n_fail += 1
            sz = out.stat().st_size if out.exists() else 0
            total_bytes += sz
            manifest.append({"lat": lat, "lon": lon, "year": year, "variant": var,
                             "file": fname, "status": status, "bytes": sz})
            if i % 40 == 0:
                print(f"[{i}/{total_planned}] ok={n_ok} 404={n_404} fail={n_fail} "
                      f"GB={total_bytes/1e9:.1f} elapsed={time.time()-t0:.0f}s", flush=True)

json.dump(manifest, open(META / "tile_manifest.json", "w"), indent=1, ensure_ascii=False)
with open(META / "tile_manifest.csv", "w", encoding="utf-8") as fh:
    fh.write("lat,lon,year,variant,file,status,bytes\n")
    for m in manifest:
        fh.write(f"{m['lat']},{m['lon']},{m['year']},{m['variant']},{m['file']},{m['status']},{m['bytes']}\n")

years_present = {}
for m in manifest:
    if m["status"] in ("OK", "SKIP_EXISTS"):
        years_present.setdefault(m["year"], 0)
        years_present[m["year"]] += 1

print(f"DONE candidates={len(candidates)} ok={n_ok} 404={n_404} fail={n_fail} "
      f"total_GB={total_bytes/1e9:.1f} elapsed={time.time()-t0:.0f}s")
print("per-year file counts:", years_present)
