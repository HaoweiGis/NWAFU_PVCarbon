# T-2026-09-24-nea-pv-html-parse：国家能源局光伏统计 HTML 解析

status: ready
类型: 工程任务（非实验，无下载，解析既有 8 个网页）
执行者: Claude Code 直接执行（用户 2026-09-24 授权）
侦察结论：`NEA_PV_2022.html` 抽查——数据未用 `<table>` 标签，是 CMS 排版的纯文本网格
（"省份 数字 数字 数字…"），可用正则/位置解析，不需要 OCR。

## 目标

把 `01_pv/capacity_calibration/nea_official_2015_2022/NEA_PV_{2015..2022}.html` 解析成
省—年结构化表，供后续面积—容量校准（D12）使用。

## 交付物

- `01_pv/capacity_calibration/nea_official_2015_2022/parsed/nea_pv_province_year.csv`
- `.../parsed/parse_report.md`：每年页面的列结构说明 + 解析失败/异常记录

## 步骤

1. 对每个年份 HTML：去标签取纯文本，定位数据块（"单位：万千瓦"起始，各省名后跟若干数字）。
2. 用已知 31/34 个省级行政区名称列表做锚点分列（每省后数字个数按年份可能不同，逐年记录实际列数
   与列名，不假设所有年份列结构一致）。
3. 输出长表：`province, year, metric_name, value_wan_kw`（metric_name 如
   `new_grid_connected_total` / `new_centralized` / `new_distributed` / `cumulative_total` / … ，
   按当年页面实际列名翻译，翻译表写进 report）。
4. 核对：每年"总计"行数值 = 各省数值之和（容差内）；省名集合完整（无遗漏/多余）。
5. 单位统一：万千瓦 → MW（× 10）在 `value_mw` 列另存，原始 `value_wan_kw` 保留可追溯。

## 验收（可判定）

- [ ] 8 个年份全部解析出非空表
- [ ] 每年"总计"行核对通过（容差 < 1%）或在 report 里逐年记录差异原因
- [ ] 省名集合每年核对（缺省份如实记录，不臆造）
- [ ] 长表 `province,year,metric_name,value_wan_kw,value_mw` 字段齐全

## 失败即停

- 某年页面结构与其余年份差异过大、无法用同一逻辑分列 → BLOCKED，报告该年份的原始文本片段
- "总计"核对差异 > 5% 且找不到原因 → BLOCKED

## 执行记录（Claude Code 直接执行）

起止：`<…>`

### 结果

### BLOCKED / 异常
