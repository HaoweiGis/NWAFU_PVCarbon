#!/usr/bin/env python
"""T-2026-09-24-ccd-extract-audit: extract CCD zip (read-only source), audit coverage."""
import json, zipfile, re
from pathlib import Path
from collections import defaultdict
import rasterio

ROOT = Path("/data/hdd/haoweimu/datasets/D010_CCD_2001-2024")
ZIP = ROOT / "raw" / "9df1ab40944b4ce58eec7265462b4247_V1.zip"
EXTRACTED = ROOT / "extracted"
META = ROOT / "metadata"
EXTRACTED.mkdir(exist_ok=True)
META.mkdir(exist_ok=True)

ALL_34 = ["北京","天津","河北","山西","内蒙古","辽宁","吉林","黑龙江","上海","江苏","浙江","安徽",
          "福建","江西","山东","河南","湖北","湖南","广东","广西","海南","重庆","四川","贵州",
          "云南","西藏","陕西","甘肃","青海","宁夏","新疆","台湾","香港","澳门"]
EXPECTED_MISSING = {"北京", "青海", "西藏", "台湾", "香港", "澳门"}

print("extracting...", flush=True)
with zipfile.ZipFile(ZIP) as z:
    names = z.namelist()
    tifs = [n for n in names if n.lower().endswith(".tif")]
    assert len(tifs) == 672, f"expected 672 tif, got {len(tifs)}"
    z.extractall(EXTRACTED)
print(f"extracted {len(tifs)} tif", flush=True)

files = sorted(EXTRACTED.rglob("*.tif"))
assert len(files) == 672, f"post-extract count {len(files)}"

# infer province from top-level dir name (pinyin or code likely) and year from filename
province_dirs = sorted({f.relative_to(EXTRACTED).parts[0] for f in files})
year_pat = re.compile(r"(20[0-2]\d)")

by_prov_year = defaultdict(set)
bad_reads = []
value_domains = defaultdict(set)
crs_set, nodata_set, pxsize_set = set(), set(), set()
for f in files:
    parts = f.relative_to(EXTRACTED).parts
    prov = parts[0]
    ym = year_pat.search(f.name)
    year = ym.group(1) if ym else None
    by_prov_year[prov].add(year)
    try:
        with rasterio.open(f) as ds:
            crs_set.add(str(ds.crs))
            nodata_set.add(ds.nodata)
            pxsize_set.add((round(ds.transform.a, 4), round(-ds.transform.e, 4)))
            # sample a decimated read for value domain (avoid reading all 672 full-res)
            data = ds.read(1, out_shape=(1, max(1, ds.height // 20), max(1, ds.width // 20)))
            vals = set(int(v) for v in set(data.ravel().tolist()) if v is not None)
            value_domains[prov] |= vals
    except Exception as e:
        bad_reads.append((str(f), str(e)))

n_prov_dirs = len(province_dirs)
report = [
    "# CCD 解压与覆盖审计报告", "",
    f"- ZIP 内 TIFF 数: {len(tifs)} · 解压后文件数: {len(files)} · 顶层目录（省级）数: {n_prov_dirs}",
    f"- CRS 集合: {crs_set}", f"- 像元大小集合(度): {pxsize_set}", f"- NoData 集合: {nodata_set}",
    f"- 不可读文件数: {len(bad_reads)}",
    "", "## 顶层目录（省级标识）清单", "",
    ", ".join(province_dirs),
    "", "## 与中国 34 个省级行政区全集比对", "",
]
matched = [p for p in ALL_34 if any(p in d or d in p for d in province_dirs)]
unmatched_dirs = [d for d in province_dirs if not any(p in d or d in p for p in ALL_34)]
missing_provinces = [p for p in ALL_34 if p not in matched]
report += [
    f"- 目录名与省份中文名可直接模糊匹配上的: {len(matched)} 个: {matched}",
    f"- 目录名无法直接匹配省份中文名的（可能是拼音/代码，需要人工核对映射表）: {unmatched_dirs}",
    f"- 按此粗略匹配法「缺失」的省份: {missing_provinces}",
    f"- 用户此前给出的预期缺省清单: {sorted(EXPECTED_MISSING)}",
    f"- 两者是否一致: {'一致' if set(missing_provinces) == EXPECTED_MISSING else '不一致，见上，需人工复核目录命名映射'}",
    "", "## 不可读文件", "",
] + [f"- {p}: {e}" for p, e in bad_reads] + [
    "", "## 每省覆盖年份数（应各 24 年：2001-2024）", "",
] + [f"- {p}: {len(y)} 年" for p, y in sorted(by_prov_year.items())] + [
    "", "## 建议 coverage_missing 处理规则", "",
    "- 上述「缺失省份」在 P05/P06 作物统计中不产出正式数值，字段编码为 `coverage_missing`，"
    "**不得填 0**（CCD 类别 0 = 非目标作物/背景，两者语义不同）。",
    "- 落在缺省区的 PV Phase 若需要作物退出统计，走 CLCD-only 降级口径（另行设计）或标记不可评估。",
]
(META / "ccd_extract_report.md").write_text("\n".join(report), encoding="utf-8")

with open(META / "coverage_audit.csv", "w", encoding="utf-8") as fh:
    fh.write("province_dir,n_years,value_domain\n")
    for p, y in sorted(by_prov_year.items()):
        fh.write(f"{p},{len(y)},\"{sorted(value_domains[p])}\"\n")

json.dump({"n_tif": len(tifs), "n_extracted": len(files), "n_prov_dirs": n_prov_dirs,
           "crs": list(crs_set), "pxsize": list(pxsize_set), "nodata": list(map(str, nodata_set)),
           "bad_reads": len(bad_reads), "matched_provinces": matched,
           "missing_by_fuzzy_match": missing_provinces}, open(META / "coverage_audit.json", "w"),
          indent=2, ensure_ascii=False)
print("DONE. province dirs:", province_dirs)
print("missing by fuzzy match:", missing_provinces)
print("bad reads:", len(bad_reads))
