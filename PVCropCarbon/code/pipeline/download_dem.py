#!/usr/bin/env python
"""T-2026-09-24-dem-download: Copernicus GLO-30 DEM tiles intersecting China (via pilot
boundary for tile SELECTION only -- not a formal boundary product, S06 still authoritative-pending).
Public S3, no auth needed.
"""
import json, hashlib, time, zipfile
from pathlib import Path
import urllib.request
import geopandas as gpd
from shapely.geometry import box
from shapely.ops import unary_union

ROOT = Path("/data/ssd/haoweimu/NWAFU_PVCarbon/07_topography/copernicus_glo30")
RAW, META = ROOT / "raw", ROOT / "metadata"
RAW.mkdir(parents=True, exist_ok=True)
META.mkdir(parents=True, exist_ok=True)

BASE = "https://copernicus-dem-30m.s3.amazonaws.com"
PILOT_ZIP = Path("/data/ssd/haoweimu/NWAFU_PVCarbon/09_boundaries/pilot_geoboundaries_adm2_2017/geoBoundaries-CHN-ADM2-all.zip")

def tile_key(lat, lon):
    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    return f"Copernicus_DSM_COG_10_{ns}{abs(lat):02d}_00_{ew}{abs(lon):03d}_00_DEM"

# 1. candidate tiles = pilot China boundary (buffered 1 deg for safety), tile-selection use only
gdf = gpd.read_file(f"zip://{PILOT_ZIP}")
outline = unary_union(gdf.geometry.values).buffer(1.0)
minx, miny, maxx, maxy = outline.bounds
lat_range = range(int(miny) - 1, int(maxy) + 2)
lon_range = range(int(minx) - 1, int(maxx) + 2)
candidates = []
for lat in lat_range:
    for lon in lon_range:
        cell = box(lon, lat, lon + 1, lat + 1)
        if cell.intersects(outline):
            candidates.append((lat, lon))
print(f"pilot outline bounds={outline.bounds} candidate tiles={len(candidates)}", flush=True)

manifest = []
n_ok, n_404, n_fail = 0, 0, 0
t0 = time.time()
for i, (lat, lon) in enumerate(candidates):
    key = tile_key(lat, lon)
    url = f"{BASE}/{key}/{key}.tif"
    out = RAW / f"{key}.tif"
    status = "SKIP_EXISTS" if out.exists() and out.stat().st_size > 0 else None
    if status is None:
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=30) as resp:
                pass
            urllib.request.urlretrieve(url, out)
            status = "OK"; n_ok += 1
        except urllib.error.HTTPError as e:
            status = f"HTTP_{e.code}"
            if e.code == 404:
                n_404 += 1
            else:
                n_fail += 1
        except Exception as e:
            status = f"ERR_{type(e).__name__}"
            n_fail += 1
    else:
        n_ok += 1
    sha = ""
    if out.exists() and out.stat().st_size > 0:
        h = hashlib.sha256()
        with open(out, "rb") as fh_:
            for chunk in iter(lambda: fh_.read(1 << 20), b""):
                h.update(chunk)
        sha = h.hexdigest()
    manifest.append({"lat": lat, "lon": lon, "key": key, "status": status,
                     "bytes": out.stat().st_size if out.exists() else 0, "sha256": sha})
    if i % 50 == 0:
        print(f"[{i}/{len(candidates)}] ok={n_ok} 404={n_404} fail={n_fail} elapsed={time.time()-t0:.0f}s", flush=True)

json.dump(manifest, open(META / "tile_manifest.json", "w"), indent=1, ensure_ascii=False)
with open(META / "tile_manifest.csv", "w", encoding="utf-8") as fh:
    fh.write("lat,lon,key,status,bytes,sha256\n")
    for m in manifest:
        fh.write(f"{m['lat']},{m['lon']},{m['key']},{m['status']},{m['bytes']},{m['sha256']}\n")

print(f"DONE candidates={len(candidates)} ok={n_ok} 404={n_404} fail={n_fail} elapsed={time.time()-t0:.0f}s")
