# T-2026-09-24-grid-ef-pdf-parse：电网排放因子 PDF 解析

status: ready
类型: 工程任务（非实验，无下载，解析既有 20 份 PDF）
执行者: Claude Code 直接执行（用户 2026-09-24 授权）
侦察结论：`pdftotext -layout` 可正常取出中文文本（非扫描件），2019 版结果表在"表2"
（"四、排放因子结果"章节），六个区域电网 × OM/BM 两列——结构简单，可解析。

## 目标

把 `06_electricity/china_grid_emission_factors_official/` 下 2006–2016（11 份）、2017、2018、
2019 区域电网基准线（OM/BM）+ 2021 全国平均因子（2 份）PDF 解析成统一数值表，明确区分
**边际因子（OM/BM）** 与 **平均因子**，不得混用（AGENTS 术语边界已定）。

## 交付物

- `06_electricity/china_grid_emission_factors_official/parsed/grid_ef_regional_om_bm.csv`：
  `year, region(华北/东北/华东/华中/西北/南方), ef_type(OM/BM), value_tco2_mwh, source_pdf`
- `.../parsed/grid_ef_national_average.csv`：`year, value_tco2_mwh, source_pdf`（2021 平均因子）
- `.../parsed/parse_report.md`：每份 PDF 的表格定位方式、六大电网覆盖省份清单（2019 版已确认，
  核对历年是否一致）、解析失败清单

## 步骤

1. 对每份 PDF：`pdftotext -layout` 取全文，定位"排放因子结果"章节的表格。
2. 六大区域电网名称固定：华北/东北/华东/华中/西北/南方——核对每份文件是否用同一划分
   （2019 版已确认此划分，明确**不含**西藏/香港/澳门/台湾）。
3. 抽取每个区域的 OM、BM 数值（tCO2/MWh），年份取该 PDF 标注的"减排项目年度"。
4. 2006–2016 那 11 份 PDF 按文件名/内容判断各自对应哪个年度或哪个电网分册，如实记录映射关系
   （文件名是哈希，不能直接看出年份，需读正文首段确认）。
5. 2021 平均因子 2 份 PDF 单独解析（口径与 OM/BM 不同，不并表）。
6. 输出前用"表中数字总位数/量级是否符合 tCO2/MWh 常见范围（约 0.5–1.2）"做健全性检查。

## 验收（可判定）

- [ ] 每份 PDF 至少提取到 1 组数值（或在 report 里说明为何提取不到）
- [ ] 六个区域名称在各年份统一，覆盖省份变化（如有）记入 report
- [ ] OM 与 BM 分列，不混入同一列；平均因子单独一张表，字段名标注 `average` 不用 `marginal`
- [ ] 数值健全性检查通过（0.3–1.5 tCO2/MWh 合理区间，超出的逐条复核标注）
- [ ] 2020、2022 年区域基准线**确认缺失**（不是解析遗漏），写入 report 供后续单独下载

## 失败即停

- 某份 PDF 表格版式与 2019 版差异太大、正则/布局解析拿不到数字 → BLOCKED，把该 PDF 的
  `pdftotext -layout` 原始片段贴进运行记录，交 Claude Code 人工看
- 数值健全性检查大量超出合理区间 → BLOCKED，不要"看起来合理就硬填"

## 执行记录（Claude Code 直接执行）

起止：`<…>`

### 结果

### BLOCKED / 异常
