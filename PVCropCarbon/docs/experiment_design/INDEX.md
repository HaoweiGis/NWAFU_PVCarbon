# PVCropCarbon 生产阶段索引

## 当前权威方法文档

- [technical/CCD_2001_2024_技术思路_V1.md](../../technical/CCD_2001_2024_技术思路_V1.md)
  —— CCD 在子项目中的技术思路（**统计口径与正式参数尚未冻结**）
- [../../README.md](../../README.md) —— 子项目范围边界
- 字段合同：[metadata/output_fields.tsv](../../metadata/output_fields.tsv)、
  [metadata/required_extra_fields.tsv](../../metadata/required_extra_fields.tsv)
- 源状态：[metadata/source_status.tsv](../../metadata/source_status.tsv)（S01–S13）
- 阶段依赖与 status 权威表：[metadata/tasks.tsv](../../metadata/tasks.tsv)（T01–T11）

| 日期 | 文件 | 定位 | 状态 |
|---|---|---|---|
| 2026-08-31 | `technical/CCD_2001_2024_技术思路_V1.md` | 子项目数据生产技术思路 | 供审阅，口径未冻结 |

## 字段分诊（52 源字段 + 10 必需扩展键）

> 生产前必须把每个字段归入四类。**未完成——见待办**。

| 类别 | 含义 | 字段 |
|---|---|---|
| A 现在可产 | 输入齐、定义清 | 待填 |
| B 卡数据 | 定义清、缺源 | 待填 |
| C 卡定义 | 有源、口径未定 | `soil_quality`、`dist_*`、`Agrco2` 边界、`new_crop_rate` 分母范围 … |
| D 延后/删 | V1 不需要或不可行 | 待填 |

## 生产阶段卡 P01–P11

一个阶段一个文件 `P0X-<slug>.md`（模板 [`_TEMPLATE.md`](_TEMPLATE.md)）。
`P0X` ↔ `metadata/tasks.tsv` 的 `T0X` 一一对应。

| 编号 | = tasks.tsv | 目标 | 前置 | 产物 | status |
|---|---|---|---|---|---|
| P01 | T01 | 审计并冻结 S01–S13 可用源、分析坐标系与分析网格 | S01–S13 | `metadata/frozen_sources.tsv` | 未起草 (BLOCKED) |
| P02 | T02 | Patch→Site 候选（30/50/100/200/300 m），从人工样本选基线阈值 | P01, S07 | `work/site_candidates.gpkg` | 未起草 (BLOCKED) |
| P03 | T03 | Site→Phase，`phase_id` = 完整 Site + 建设年，原始图斑可追溯 | P02 | `work/phases.gpkg` | 未起草 (BLOCKED) |
| P04 | T04 | Phase×县相交，完整 Phase 保留，相交面积之和 = Phase 面积 | P03, S06 | `outputs/phase_county.parquet` | 未起草 (BLOCKED) |
| P05 | T05 | 建设前稳定主粮（水稻/玉米/小麦 + 并集，三口径） | P03, S03–S05 | `work/staple_pre.parquet` | 未起草 (BLOCKED) |
| P06 | T06 | 建设后作物持续/退出（两个完整年，类别互斥，作物替代 ≠ 主粮退出） | P05 | `outputs/crop_exit.parquet` | 未起草 (BLOCKED) |
| P07 | T07 | Phase–环带–年 面板：土地变化（环带扣 Phase、无重复、首扩 vs 复垦分开） | P03, S02, S06, S09–S11 | `outputs/ring_landchange.parquet` | 未起草 (BLOCKED) |
| P08 | T08 | 反事实归因：前趋势 / 强度梯度 / 距离衰减 / 安慰剂门槛 | P07, S07, S08 | `outputs/attributed_expansion.parquet` | 未起草 (BLOCKED) |
| P09 | T09 | 土地转化碳 `Landco2`（20/30 年、脉冲/分期两情景、质量平衡） | P08, S12 | `outputs/ring_landcarbon.parquet` | 未起草 (BLOCKED) |
| P10 | T10 | 新增农业排放 `Agrco2`（系统边界冻结、作物因子、不确定性传播） | P06, P08, S13 | `outputs/ring_agcarbon.parquet` | 未起草 (BLOCKED) |
| P11 | T11 | 汇总 T01–T04 四张表（52 源字段 + 必需扩展键，唯一/空值/量纲/核对） | P04,P06,P07,P09,P10 | `outputs/T01`–`T04` | 未起草 (BLOCKED) |

status: 未起草 → draft → ready → running → done / blocked

## 与主项目 V1 主线的共享

`P02/P03/P04/P07/P08`（Patch→Site→Phase、Phase×县、环带面板、反事实归因）与主线
`docs/experiment_design/` 的对应实验**方法一致、代码可复用**。先做子项目正好为主线打地基。
子项目的中间结果**不自动**视为主项目正式结果（见子项目 README）。

## 待办（起草任何卡片之前）

1. 完成 52+10 字段分诊表。
2. P01 讨论并冻结：分析坐标系/网格（= 主线 E00）、CCD 缺省区处理（含青海/西藏 PV 降级口径）。
3. 起草 `docs/tasks/T-2026-09-03-server-env.md` 之后（环境卡在主线根目录，子项目共用）。
