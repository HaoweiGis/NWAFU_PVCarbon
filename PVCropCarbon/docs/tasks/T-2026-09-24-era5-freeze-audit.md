# T-2026-09-24-era5-freeze-audit：ERA5-Land 完整性核对与冻结

status: ready
类型: 工程任务（非实验，纯审计，无下载）
执行者: Claude Code 直接执行（用户 2026-09-24 授权）

## 目标

对 `/data/hdd/haoweimu/datasets/D005_ERA5_Land/raw/` 现有 2,267 个 grib 文件做完整性核对，
确认变量集与年月覆盖，产出冻结清单，供 P05–P07 的气候控制变量使用。**不下载新文件。**

## 交付物

- `D005_ERA5_Land/metadata/era5_frozen_manifest.{csv,json}`：year × month × variable 矩阵 + 每文件大小/mtime
- `D005_ERA5_Land/metadata/era5_freeze_report.md`：变量集、年份范围、缺口清单

## 步骤

1. 列出 `raw/` 全部文件，解析文件名 `ERA5Land_{year}_{month}_{var}.grib`。
2. 透视成 year × month × var 矩阵，标出缺格。
3. 对比 `legacy_partial/` 里残留的 `.part` 文件——确认是否已被 `raw/` 里的同名正式文件取代
   （若已取代，在报告里注明"遗留可忽略"，不删除、不改动 `legacy_partial/`）。
4. 抽样 5 个 grib 文件用 `rasterio`/`cfgrib` 读一次，确认可读、记录变量名/网格/时间步。
5. 写冻结清单 + 报告。

## 验收（可判定）

- [ ] 矩阵覆盖全部 `raw/` 文件，无解析失败
- [ ] 变量集合列出（预期 d2m/sp/ssrd/ssr/str/t2m/tp/u10/v10，9 个，若不同如实记录）
- [ ] 抽样 5 个文件全部可读
- [ ] 报告明确回答："2010–2022（主线观测窗口）× 建设前 5 年缓冲（即 2005–2022）是否逐月逐变量齐全"

## 失败即停

- 抽样文件不可读或变量名与预期严重不符 → BLOCKED，报告现象，不擅自重下载

## 执行记录（Claude Code 直接执行）

起止：`<…>`

### 结果

### BLOCKED / 异常
