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

起止：2026-09-24 20:19 – 2026-09-25 06:xx（+08，含一次因 bug 中断重启；脚本
`code/pipeline/download_esa_biomass.py` + `finalize_esa_biomass.py`）

### 步骤 1 探测结果

**匿名可行**：`https://dap.ceda.ac.uk/neodc/esacci/biomass/data/agb/maps/v7.0/` 返回 200，
可直接列目录、下载，**不需要 CEDA 账号注册**。

### 结果

- 用 pilot 候选边界筛出 **25 个 10°×10° 候选瓦片**，年份 2010/2011/2012/2015–2022（11 年，
  达成 V1 §1.B 要求的全部年份），AGB + AGB_SD 两变量 = 550 个目标文件。
- **550/550 全部到位**，25.7 GB，25×22（每年每变量 25 瓦片）核对齐全，无一缺失。
- 抽样 10 个文件读取正常，CRS 统一 `EPSG:4326`，数值范围 0–515（AGB/AGB_SD 常见量级，
  健全）。

### BLOCKED / 异常（过程中的两个插曲，均已解决）

1. **下载脚本无 socket 超时导致静默挂起**：首次运行卡在某个文件上 **8.5 小时**无任何进展、
   无报错、无中断——`urllib.request.urlretrieve` 默认不设超时，一个死连接会永远等下去。
   已加 `socket.setdefaulttimeout(60)` 修复，杀掉旧进程后断点续传重启（已下载的 200 个
   文件自动跳过，未重复下载）。
2. **存在性检查未验证文件完整性**：1 个文件因连接中断产生 16.3 MB 的**部分文件**（应为
   58.7 MB），脚本的"存在即跳过"逻辑会把它误判为已完成。人工发现后删除重下并核实。
   **教训记入 DEM 卡与本卡**：批量下载脚本应比对 `Content-Length` 或至少记录预期大小区间，
   不能只判断"文件存在"。

### 产物

- `05_carbon/esa_cci_biomass_v7_china/raw/`（550 个 tif，25.7 GB）
- `.../metadata/{tile_manifest.{csv,json}, download_report.md}`

### 给 Claude Code 的问题

无。年份覆盖已达成 V1 最低要求（2010–2012 + 2015–2022）；2013/2014 未下载（V1 设计本就不要求）。
