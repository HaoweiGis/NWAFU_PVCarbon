#!/usr/bin/env python
"""T-2026-09-24-nea-pv-html-parse: parse NEA yearly PV pages into a province x year table."""
import re, json
from pathlib import Path

ROOT = Path("/data/ssd/haoweimu/NWAFU_PVCarbon/01_pv/capacity_calibration/nea_official_2015_2022")
OUT = ROOT / "parsed"
OUT.mkdir(exist_ok=True)

PROVINCES = ["北京","天津","河北","山西","内蒙古","辽宁","吉林","黑龙江","上海","江苏","浙江",
             "安徽","福建","江西","山东","河南","湖北","湖南","广东","广西","海南","重庆","四川",
             "贵州","云南","西藏","陕西","甘肃","青海","宁夏","新疆"]

num_pat = re.compile(r"-?\d+(?:\.\d+)?")

def strip_tags(html: str) -> str:
    txt = re.sub(r"<[^>]+>", " ", html)
    txt = re.sub(r"&nbsp;", " ", txt)
    txt = re.sub(r"[ \t　]+", " ", txt)
    return txt

rows_all = []
report = []
for year in range(2015, 2023):
    f = ROOT / f"NEA_PV_{year}.html"
    if not f.exists():
        report.append(f"{year}: 文件不存在"); continue
    html = f.read_text(encoding="utf-8", errors="ignore")
    txt = strip_tags(html)

    # Anchor 1: "总计" (table summary row) if present.
    total_idx = txt.find("总计")
    # Anchor 2 (fallback for years without "总计", e.g. 2017/2020): first place where two provinces
    # in the FIXED government reporting order (北京 then 天津) appear within a short span of each
    # other -- this distinguishes the real table from a stray mention in prose/footer.
    seq_idx = -1
    for m in re.finditer("北京", txt):
        near = txt[m.start(): m.start() + 60]
        if "天津" in near:
            seq_idx = m.start(); break

    block_start = total_idx if total_idx > 0 else seq_idx
    if block_start < 0:
        report.append(f"{year}: 未找到可靠的表格起点（总计/北京-天津连续序列均未命中），跳过"); continue

    # Bound the END of the block: find the last province in PROVINCES (in report order) that occurs
    # after block_start within a growing window, stop extending once no further province follows
    # within 400 chars of the previous match (leaves prose/footer out).
    pos = block_start
    last_end = block_start
    while True:
        # find nearest next province occurrence after pos+1
        next_hits = [(txt.find(p, pos + 1), p) for p in PROVINCES]
        next_hits = [(i, p) for i, p in next_hits if i > 0]
        if not next_hits:
            break
        i, p = min(next_hits)
        if i - last_end > 400:
            break
        last_end = i
        pos = i
    block_end = min(last_end + 300, block_start + 5000)
    block = txt[block_start:block_end]

    # Walk through block: split on province names, each segment's leading numbers belong to that province
    # Build a regex alternation ordered so multi-char provinces match before substrings (内蒙古 before 蒙古 etc. -- not an issue here)
    prov_alt = "|".join(sorted(PROVINCES, key=len, reverse=True))
    tokens = re.split(f"({prov_alt})", block)
    # tokens alternate: [prefix, prov, text_until_next_prov, prov, text, ...]
    year_rows = []
    i = 1
    while i < len(tokens) - 1:
        prov = tokens[i]
        following = tokens[i + 1]
        # numbers up to the next province name (already split) belong to this province
        nums = num_pat.findall(following)
        # stop collecting once we've hit a clearly-too-long run (defensive: cap at 10)
        nums = nums[:10]
        year_rows.append((prov, [float(x) for x in nums]))
        i += 2

    ncols = {len(v) for _, v in year_rows}
    max_cols = max((len(v) for _, v in year_rows), default=0)
    for prov, vals in year_rows:
        rows_all.append({"year": year, "province": prov, "n_values": len(vals), "values": vals})
    report.append(f"{year}: {len(year_rows)} 省份行，值个数分布 {sorted(ncols)}，取列数上限 {max_cols}")

json.dump(rows_all, open(OUT / "nea_pv_raw_extract.json", "w"), indent=1, ensure_ascii=False)

with open(OUT / "nea_pv_province_year.csv", "w", encoding="utf-8") as fh:
    fh.write("year,province,n_values,values_wan_kw\n")
    for r in rows_all:
        fh.write(f"{r['year']},{r['province']},{r['n_values']},\"{r['values']}\"\n")

(OUT / "parse_report.md").write_text(
    "# NEA 光伏统计 HTML 解析报告\n\n" + "\n".join(f"- {l}" for l in report) +
    "\n\n注：每省数值列表按原文顺序保留，未强行按统一列名分列（不同年份列结构不一定相同，"
    "列名映射需人工核对每年页面表头后在下一步补充，本任务只做到位置提取 + 省份锚点校验）。\n",
    encoding="utf-8")
print("\n".join(report))
