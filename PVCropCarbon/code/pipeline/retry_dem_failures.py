#!/usr/bin/env python
"""Retry the ~30 DEM tiles that failed with transient network errors (not 404)."""
import json, hashlib, time
from pathlib import Path
import urllib.request

ROOT = Path("/data/ssd/haoweimu/NWAFU_PVCarbon/07_topography/copernicus_glo30")
RAW, META = ROOT / "raw", ROOT / "metadata"
BASE = "https://copernicus-dem-30m.s3.amazonaws.com"

manifest = json.load(open(META / "tile_manifest.json"))
to_retry = [m for m in manifest if m["status"] not in ("OK", "SKIP_EXISTS", "HTTP_404")]
print(f"retrying {len(to_retry)} tiles")

for m in to_retry:
    key = m["key"]
    url = f"{BASE}/{key}/{key}.tif"
    out = RAW / f"{key}.tif"
    ok = False
    for attempt in range(4):
        try:
            urllib.request.urlretrieve(url, out)
            ok = True
            break
        except Exception as e:
            print(f"  {key} attempt {attempt+1} failed: {e}")
            time.sleep(5 * (attempt + 1))
    if ok:
        h = hashlib.sha256()
        with open(out, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        m["status"] = "OK_RETRY"
        m["bytes"] = out.stat().st_size
        m["sha256"] = h.hexdigest()
        print(f"  {key}: OK ({m['bytes']} bytes)")
    else:
        m["status"] = "FAILED_AFTER_RETRY"
        print(f"  {key}: STILL FAILING after 4 attempts")

json.dump(manifest, open(META / "tile_manifest.json", "w"), indent=1, ensure_ascii=False)
with open(META / "tile_manifest.csv", "w", encoding="utf-8") as fh:
    fh.write("lat,lon,key,status,bytes,sha256\n")
    for m in manifest:
        fh.write(f"{m['lat']},{m['lon']},{m['key']},{m['status']},{m['bytes']},{m['sha256']}\n")

still_failing = [m for m in manifest if m["status"] == "FAILED_AFTER_RETRY"]
print(f"DONE. still failing: {len(still_failing)}")
for m in still_failing:
    print(" ", m["key"])
