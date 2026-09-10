# PVCropCarbon 生产阶段索引

## 当前权威方法文档

- [technical/光伏建设批次基础数据表_技术思路_V1.md](../../technical/光伏建设批次基础数据表_技术思路_V1.md)
  —— **T01 Patch→Site→Phase→县 方法说明 V1**（2026-09-10；Site 阈值临时基线 100 m）
- [technical/CCD_2001_2024_技术思路_V1.md](../../technical/CCD_2001_2024_技术思路_V1.md)
  —— CCD 作物部分技术思路（**统计口径与正式参数尚未冻结**）
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
| [P01](P01-源审计与网格冻结.md) | T01 | 冻结分析网格(CLCD Albers) + PV 图斑审计（候选县界审计 + frozen_sources.tsv 顺延 P04 前） | env done ✓ | `metadata/analysis_grid.json`、`work/patches_clean.gpkg`（29,979 patch） | **done（部分）** 2026-09-09 |
| [P02](P02-Patch到Site候选.md) | T02 | Patch→Site 候选（5 阈值全产）+ 巨型 Site 诊断 | P01 | `work/site_membership.parquet`（149,895 行） | **done** 2026-09-09 |
| [P03](P03-Site到Phase.md) | T03 | Site→Phase：5 阈值完整 Phase 几何 → **建设批次矢量 shp** | P02 | `work/phases.gpkg`、`outputs/phase_vector/phases_d{30,50,100,200,300}.shp` | **done** 2026-09-09 |
| P04 | T04 | Phase×县相交 → T01 表：跨县多行、`phase_id` 不变、加 `intersection_pct` + `is_primary_county`（面积最大县） | P03, S06 | `outputs/phase_county.parquet` | 未起草 (BLOCKED: S06) |
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

## T01 批次表的构建决策（2026-09-03 讨论定）

- 粒度：**一行 = 一个 `phase_county`**（Phase×县）。跨县多行，`phase_id` 不变。
- 跨县：加 `intersection_pct`（该行相交面积 / 完整 `phase_area`，同 `phase_id` 各行之和=1）
  与 `is_primary_county`（相交面积最大的县 = true），见 `required_extra_fields.tsv`。
- Patch→Site = 边界间距 ≤ 阈值的连通分量（Albers 下量）；5 阈值全产，基线选定等 S07。
- 巨型 Site（连片光伏基地）处理：**看 P02 诊断分布再定**（接受基地=一个 Site vs 加直径/面积上限）。
- 全部 patch 进（含非耕地、含 `Ocean area`；海上 Phase 打 `offshore`）。**调整**：P01 发现 43 组
  完全重复几何（87 patch），去 44 个 → **29,979 patch**（"全进"= 全部去重后 patch）。
- Phase 分年按修正后 `inst_year`；精确 `inst_date` 留字段供 pre/post 窗口。

## P01–P03 结果（2026-09-09，Claude Code 直接执行；报告 `outputs/audits/p01_p03_report.md`）

- **分析网格冻结**：`metadata/analysis_grid.json` = CLCD v01 原生 Albers 网格（26 幅一致）。
- **`PV_Area` 单位 = km²**（比值中位数 1.0000 确认）；3 条日期异常已在派生层修正。
- **链式合并不是问题**：30–200 m 下 0 个 >50 km² 的巨型 Site；300 m 才 2 个（真实基地）。
  → 采用**方案 a：连通分量直接作 Site**，不加直径/面积上限。
- **建设批次矢量已出**：`outputs/phase_vector/phases_d{30,50,100,200,300}.shp`（16 字段，
  按 `phase_id` 加下游属性）。Phase 数 30m→300m = 26688 / 22414 / 18059 / 15154 / 14048。
- **临时基线 = 100 m**（S07 前工作默认；筛选规则见下）。主敏感性 50 / 200 m；30 / 300 m 仅极端边界附录。
  下游属性统计先用 `phases_d100.shp`。

### 阈值筛选规则

规则 R1–R6 与打分表见方法说明
[technical/光伏建设批次基础数据表_技术思路_V1.md](../../technical/光伏建设批次基础数据表_技术思路_V1.md) §6。
要点：100 m 唯一同时通过"拒过碎(R1)"+"拒过并(R2)"+"边际拐点(R3)"；50 m 过碎但作保守下界；
200 m 现过并苗头；300 m 明确过并。**R6**：S07 到手后按人工/算法标签一致性重选。

## 待办

1. ~~服务器 GIS 环境~~ ✓ · ~~P01/P02/P03~~ ✓ · ~~网格冻结转正~~ ✓ · ~~阈值临时基线 100 m~~ ✓（2026-09-10）。
2. 完成 52+10 字段分诊表（骨架在上）。
4. **S07** Site 阈值人工样本任务卡（基线阈值 + 少数远距离 2-patch Site 误并核对）——待用户确认抽样设计。
5. **S06** 权威县界获取任务卡——待用户选定来源（国家基础地理信息中心 / RESDC / 民政部代码表）。
6. P04 卡片——S06 决策后起草；一并补候选县界审计 + `frozen_sources.tsv` + CLCD SHA-256 比对。
