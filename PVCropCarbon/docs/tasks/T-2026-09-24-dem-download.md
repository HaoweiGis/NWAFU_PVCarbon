# T-2026-09-24-dem-download：DEM 获取（Copernicus GLO-30）

status: ready
类型: 工程任务（非实验，新下载）
执行者: Claude Code 直接执行（用户 2026-09-24 授权）
侦察结论：Copernicus GLO-30 DEM 公开托管在 AWS S3（`s3://copernicus-dem-30m`，
`registry.opendata.aws/copernicus-dem/`），**无需账号/密钥**，COG 格式，1°×1° 分块，
2021 版。选它而非 SRTM：更新、无空洞、访问无认证门槛。**这是 S10（DEM/坡度）第一次实际下载。**

## 目标

下载覆盖中国大陆的 Copernicus GLO-30 DEM 瓦片，拼接为可用于坡度计算的栅格，
建立 `dist_road_pre` 等后续字段之外、`slope` 字段的直接数据源。

## 交付物

- `07_topography/copernicus_glo30/raw/`：中国大陆范围内的原始 1°×1° COG 瓦片
- `07_topography/copernicus_glo30/dem_china.vrt`：镶嵌 VRT（原生 EPSG:4326）
- `07_topography/copernicus_glo30/metadata/tile_manifest.csv`：瓦片名、S3 key、SHA256、下载状态
- `07_topography/copernicus_glo30/metadata/download_report.md`

## 步骤

1. 根据 CLCD 分析网格的地理范围（`analysis_grid.json` 的 bounds，重投影回 WGS84 取经纬度包络）
   生成需要的 1°×1° 瓦片列表（纬度 18–54°N、经度 73–135°E 的全部整数网格，逐格拼 S3 key，
   命名规则 `Copernicus_DSM_COG_10_N{lat}_00_E{lon}_00_DEM/...tif`，海上瓦片会 404，跳过并记录）。
2. 用 `aws s3 cp --no-sign-request` 或匿名 HTTPS 逐瓦片下载到 `raw/`（断点续传，失败重试 ≤3 次）。
3. 每个瓦片记录 SHA256、文件大小、`gdalinfo` 基本信息（尺寸/分辨率/NoData）。
4. 建 VRT 镶嵌；抽样读值做健全性检查（中国境内高程范围应在 −200~8900 m 之间，青藏高原应明显偏高）。
5. **不在本任务里算坡度**——坡度算法/方法（如 3×3 窗口、水平/垂直方向权重）留给用坡度的实验卡决定，
   本任务只交付原始高程栅格。

## 验收（可判定）

- [ ] 覆盖中国大陆的瓦片全部下载成功（陆地瓦片 0 个失败；海上瓦片 404 数量与预期陆地边界瓦片数吻合）
- [ ] 全部瓦片 SHA256 登记
- [ ] VRT 可读，抽样高程值健全（无负得离谱或正得离谱的异常值，青藏高原 > 4000 m 的抽样点符合预期）
- [ ] 总下载量记入报告（估算：1°×1° GLO-30 约 25–50 MB/瓦片，中国约 200+ 陆地瓦片，量级几 GB 到十几 GB）

## 失败即停

- S3 匿名访问被拒绝（权限变化）→ BLOCKED，报告返回的 HTTP 状态码，不要改用其它未经确认的镜像
- 连续 > 20 个陆地瓦片下载失败（非预期 404）→ BLOCKED，可能是网络/命名规则问题

## 执行记录（Claude Code 直接执行）

起止：2026-09-24 19:32 – 2026-09-25 05:16（+08，主下载 ~9.4h + 重试 ~几分钟；脚本
`code/pipeline/download_dem.py` + `retry_dem_failures.py` + `finalize_dem.py`）

### 结果

- 用 pilot 候选边界（缓冲 1°）筛出 **1,324 个候选瓦片**（比整个矩形范围少 ~43%）。
- 首轮：1,252 OK、42 个确认 404（真实无数据，多为边界外海域）、30 个瞬时网络错误
  （`URLError`/`BrokenPipeError`/`RemoteDisconnected`，**不是** 404，是可重试的传输失败）。
- 重试 30 个失败瓦片：**全部成功**。
- **最终 1,282 个瓦片全部到位，0 个未解决失败**，共 49.4 GB。
- 建好 `dem_china.vrt`（EPSG:4326，225562×136800，30m 原生分辨率）。
- 5 个抽样点高程健全性检查全过（拉萨附近 3651m、石家庄 68m、塔里木盆地 998m、
  珠峰东坡 5309m、福州 13m，均落在预期区间）。

### 产物

- `07_topography/copernicus_glo30/raw/`（1,282 个 tif，49.4 GB）
- `07_topography/copernicus_glo30/dem_china.vrt`
- `07_topography/copernicus_glo30/metadata/{tile_manifest.{csv,json}, download_report.md}`（含每瓦片 SHA256）

### BLOCKED / 异常

无（最终）。**过程中发现脚本 bug**：初版下载在网络瞬时错误时会静默计入 `fail` 但不重试，
已写 `retry_dem_failures.py` 补救——**下次类似批量下载任务应从一开始就内置重试**
（此教训已用于修复 ESA Biomass 任务的同类问题，见该卡）。

### 备注

瓦片选择基于 pilot 边界（非权威），覆盖中国及少量境外邻近区域，**不是精确国界裁剪**；
正式坡度计算前需按权威边界（S06）裁剪。坡度算法本任务不做。
