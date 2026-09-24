# T-2026-09-24-esa-biomass-download：ESA CCI Biomass v7 下载（中国范围）

status: ready
类型: 工程任务（非实验，新下载，**风险最高的一项**）
执行者: Claude Code 直接执行（用户 2026-09-24 授权）
侦察结论：数据在 CEDA Archive（`https://dap.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/`），
v7.0 覆盖 2005–2024 多年（2007/2010/2015–2024）。CEDA 部分数据集允许匿名 `wget --mirror`，
但**不确定本数据集是否需要免费注册的 CEDA 账号**——本任务第一步先探测，探测结果决定后续走向。

## 目标

获取覆盖中国的 ESA CCI Biomass v7 AGB（地上生物量）+ AGB 标准差栅格，年份至少含
V1 设计要求的 2010–2012 及 2015–2022（`researchwrite/versions/v1/exports/V1_最小必要数据与
下载方案.md` §1.B）。**这是 S12 里唯一仍是 0 文件的部分。**

## 交付物（若探测通过）

- `05_carbon/esa_cci_biomass_v7_china/raw/`：中国相交瓦片的 AGB + AGB_SD GeoTIFF
- `05_carbon/esa_cci_biomass_v7_china/metadata/{tile_manifest.csv, ceda_md5_check.csv, download_report.md}`

## 步骤

1. **探测访问方式**（先做这步，再决定要不要继续）：
   `curl -I https://dap.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/` 看返回码；
   若 200/301 且能列目录 → 匿名可行，继续步骤 2；
   若 401/403 → 需要 CEDA 账号（免费注册，但**需要人工完成注册**，本任务在此 BLOCKED，
   把注册链接和所需信息写进运行记录，交用户注册后再继续）。
2. 列出 v7.0 目录下的年份/瓦片结构，按中国大陆经纬度范围（18–54°N、73–135°E）筛出相交瓦片
   （ESA CCI Biomass 通常以 10°×10° 或 更大网格分块，具体以实际目录结构为准，不臆测）。
3. 下载 AGB 主产品 + AGB 标准差（不确定性）两个变量，年份覆盖 V1 要求的 2010–2012、2015–2022
   （能拿到多少年拿多少，缺年份如实记录，不用相邻年份替代）。
4. 按 CEDA 提供的 MD5/checksum 校验（若有）；否则本地计算 SHA256 存档。
5. 写下载报告：实际覆盖年份、中国瓦片数、总数据量、访问方式（是否需要账号）。

## 验收（可判定）

- [ ] 步骤 1 的探测结果明确记录（可匿名 / 需账号 / 完全不可达）
- [ ] 若可下载：AGB + AGB_SD 至少覆盖 2010–2012 与 2015–2022 中能拿到的年份，每年份文件可读
- [ ] 所有文件有 MD5（CEDA 提供）或 SHA256（本地计算）
- [ ] 报告如实说明是否达成 V1 要求的年份覆盖，未达成的年份原样列出（不用相邻年代替）

## 失败即停

- CEDA 需要账号注册 → **不要自行注册**（涉及账户凭据），BLOCKED，把注册页面链接和所需字段
  写进运行记录交用户处理
- 中国瓦片下载量异常巨大（超出 HDD 剩余 5.3 TB 的合理预算，如单次任务 > 500 GB）→ BLOCKED，
  先报告预估总量，等确认再下载

## 执行记录（Claude Code 直接执行）

起止：`<…>`

### 结果

### BLOCKED / 异常
