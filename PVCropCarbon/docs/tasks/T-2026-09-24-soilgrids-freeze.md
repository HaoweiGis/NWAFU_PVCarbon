# T-2026-09-24-soilgrids-freeze：SoilGrids mean 层冻结

status: ready
类型: 工程任务（非实验，纯审计，无下载）
执行者: Claude Code 直接执行（用户 2026-09-24 授权）

## 目标

冻结 `/data/ssd/haoweimu/NWAFU_PVCarbon/05_carbon/soilgrids_250m_mean_0_30cm/` 现有 216 个 tile +
8 个 VRT 镶嵌（bdod/cfvo/soc × 0–5/5–15/15–30 cm）为正式产品，评估是否需要补 5%/95% 分位数。
**不下载新文件。**

## 交付物

- `05_carbon/soilgrids_250m_mean_0_30cm/metadata/frozen_manifest.{csv,json}`：每 tile 的 SHA256、CRS、
  分辨率、值域、NoData
- `05_carbon/soilgrids_250m_mean_0_30cm/metadata/freeze_report.md`：中国范围覆盖完整性结论 +
  是否需要补不确定性分位数的建议

## 步骤

1. 逐 tile 读 CRS/分辨率/NoData/值域，核对 9 个变量-深度组合（bdod/cfvo/soc × 3 深度）tile 数一致。
2. 用现有 8 个 VRT 抽样读值，确认镶嵌无缝隙（沿瓦片边界抽几条剖面看连续性）。
3. 计算全部 tile SHA256。
4. 单位核对：SoilGrids 官方 bdod 单位 cg/cm³、soc 单位 dg/kg、cfvo 单位 cm³/dm³——在报告里写清换算到
   常用单位（kg/m³、g/kg、%）的公式，供 P09 碳核算直接引用，本任务**不做换算，只记录换算公式**。
5. 报告是否需要补 Q0.05/Q0.95（V1 要求 Monte Carlo 不确定性，最终需要；先评估工作量，不在本任务下载）。

## 验收（可判定）

- [ ] 9 个变量-深度组合 tile 数一致，缺失（若有）逐一列出
- [ ] SHA256 全部计算并登记
- [ ] VRT 镶嵌抽样连续、无明显缝隙/空洞
- [ ] 报告给出单位换算公式 + 分位数缺口的工作量估计

## 失败即停

- 任一变量-深度组合 tile 数与其余不一致且无法解释 → BLOCKED，列出差异
- VRT 镶嵌发现明显缝隙/空洞 → BLOCKED，标出坐标范围

## 执行记录（Claude Code 直接执行）

起止：`<…>`

### 结果

### BLOCKED / 异常
