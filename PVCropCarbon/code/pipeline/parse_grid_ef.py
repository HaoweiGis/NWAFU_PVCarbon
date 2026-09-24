#!/usr/bin/env python
"""T-2026-09-24-grid-ef-pdf-parse: extract regional grid OM/BM tables from MEE PDFs."""
import re, json, subprocess
from pathlib import Path

ROOT = Path("/data/ssd/haoweimu/NWAFU_PVCarbon/06_electricity/china_grid_emission_factors_official")
OUT = ROOT / "parsed"
OUT.mkdir(exist_ok=True)

REGIONS = ["华北区域电网", "东北区域电网", "华东区域电网", "华中区域电网", "西北区域电网",
           "南方区域电网", "海南省电网"]
num_pat = re.compile(r"-?\d+\.\d+")

def pdftotext(p: Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, text=True).stdout

def find_title_year(txt: str) -> int | None:
    m = re.search(r"(20\d{2})\s*年度?\s*(?:减排项目)?中国区域电网", txt)
    return int(m.group(1)) if m else None

def find_actual_data_years(txt: str) -> str | None:
    m = re.search(r"OM\s*为\s*(20\d{2}(?:[-–]20\d{2})?)\s*年", txt)
    return m.group(1) if m else None

rows = []
skipped = []
regional_files = sorted(ROOT.glob("MEE_200*/*.pdf")) + sorted(ROOT.glob("MEE_2017*/*.pdf")) + \
                  [ROOT / "MEE_2018_regional_grid_baseline" / "01_W020201229606779361068.pdf",
                   ROOT / "MEE_2019_regional_grid_baseline" / "01_W020201229610353340851.pdf"]

for f in regional_files:
    if not f.exists():
        continue
    txt = pdftotext(f)
    title_year = find_title_year(txt)
    actual_years = find_actual_data_years(txt)

    # locate results table: prefer the "EFgrid,OM ... EFgrid,BM" header; fall back to the section
    # marker "排放因子数值/结果" (some early-vintage PDFs render the header symbols oddly and
    # pdftotext drops them, but the section marker + region rows are still plain text).
    hdr = re.search(r"EFgrid.{0,3}OM.{0,40}EFgrid.{0,3}BM", txt)
    if not hdr:
        hdr = re.search(r"排放因子(?:数值|结果)", txt)
    matched_regions = []
    if hdr:
        tail = txt[hdr.end(): hdr.end() + 2000]
        for region in REGIONS:
            m = re.search(re.escape(region) + r"\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)", tail)
            if m:
                matched_regions.append((region, float(m.group(1)), float(m.group(2))))
    if not matched_regions:
        skipped.append({"file": str(f), "reason": "no EFgrid,OM/BM header + region rows matched",
                        "title_year": title_year})
        continue
    for region, om, bm in matched_regions:
        rows.append({"file": f.name, "dir": f.parent.name, "title_year": title_year,
                     "actual_data_years": actual_years, "region": region, "om_tco2_mwh": om,
                     "bm_tco2_mwh": bm})

# 2021 national average factor (different structure, parsed separately)
avg_rows = []
avg_f = ROOT / "MEE_2021_average_grid_factor" / "01_W020240412827267102800.pdf"
if avg_f.exists():
    txt = pdftotext(avg_f)
    for m in re.finditer(r"(全国|化石能源电力|除市场化交易[^\n]{0,20})\s+(-?\d+\.\d+)", txt):
        avg_rows.append({"file": avg_f.name, "label": m.group(1).strip(), "value_kgco2_kwh": float(m.group(2))})

with open(OUT / "grid_ef_regional_om_bm.csv", "w", encoding="utf-8") as fh:
    fh.write("file,dir,title_year,actual_data_years,region,om_tco2_mwh,bm_tco2_mwh\n")
    for r in rows:
        fh.write(f"{r['file']},{r['dir']},{r['title_year']},{r['actual_data_years']},"
                 f"{r['region']},{r['om_tco2_mwh']},{r['bm_tco2_mwh']}\n")

with open(OUT / "grid_ef_national_average.csv", "w", encoding="utf-8") as fh:
    fh.write("file,label,value_kgco2_kwh\n")
    for r in avg_rows:
        fh.write(f"{r['file']},{r['label']},{r['value_kgco2_kwh']}\n")

# sanity check: OM/BM in plausible 0.3-1.5 tCO2/MWh range
out_of_range = [r for r in rows if not (0.3 <= r["om_tco2_mwh"] <= 1.5 and 0.1 <= r["bm_tco2_mwh"] <= 1.5)]

report = [
    "# 电网排放因子 PDF 解析报告", "",
    f"- 尝试解析文件数: {len(regional_files)} · 成功提取表格: {len(regional_files) - len(skipped)} · 跳过: {len(skipped)}",
    f"- 提取到的 (年份,区域) 记录数: {len(rows)}",
    f"- 数值超出合理区间 (OM 0.3-1.5 / BM 0.1-1.5 tCO2/MWh) 的记录: {len(out_of_range)}",
    "", "## 跳过的文件（未匹配到表格结构）", "",
] + [f"- {s['file']}（标题年份猜测 {s['title_year']}）：{s['reason']}" for s in skipped] + [
    "", "## 区域覆盖省份变化提示", "",
    "- 早期文件（如 2010 版数据）额外单列「海南省电网」，2017 年起海南并入南方区域电网——"
    "解析时两种格式都识别，下游使用时注意 2017 年前后海南口径不同，不能直接拼接时间序列。",
    "", "## 2021 全国平均因子", "",
] + [f"- {r['label']}: {r['value_kgco2_kwh']} kgCO2/kWh" for r in avg_rows] + [
    "", "## 数值健全性异常（如有，逐条复核）", "",
] + [f"- {r}" for r in out_of_range] + [
    "", "## 结论：2020、2022 年区域基准线", "",
    "- 本任务解析范围内（2006–2019 各版）**不含** 2020、2022 年区域 OM/BM——源文件本就没有，"
    "确认是缺口而非解析遗漏，需另行下载/查找官方是否发布过。",
]
(OUT / "parse_report.md").write_text("\n".join(report), encoding="utf-8")
print(f"extracted={len(rows)} skipped={len(skipped)} out_of_range={len(out_of_range)}")
for s in skipped:
    print("SKIP:", s["file"], s["reason"])
