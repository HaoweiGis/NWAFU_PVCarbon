# P02 Patch → Site 候选构建

status: draft            <!-- draft | ready | running | done | blocked -->
前置依赖: P01（`patches_clean.gpkg` + `analysis_grid.json` 已 done）；T-2026-09-03-server-env done
= metadata/tasks.tsv 的 T02

**卡片** = Claude Code 写 → 用户批准 → **运行记录** = Codex 写 → **解读** = Claude Code 写。

---

## 卡片（Claude Code）

### 1. 目标（一句话）

对全部 30,023 个清洗后 patch，用"边界间距 ≤ 阈值"的连通分量在 **5 个候选阈值
（30/50/100/200/300 m）下各生成一套 `site_id`**，并产出足以判断"是否存在巨型 Site、
基线阈值取哪个"的诊断分布——**不在本卡选定基线阈值**（等 S07 人工样本）。

### 2. 输入（绝对路径 + 期望规格）

| 数据 | 版本 | 路径（服务器） | 期望 |
|---|---|---|---|
| 清洗后 patch 层 | P01 产出 | `PVCropCarbon/work/patches_clean.gpkg`（layer `patches`） | 30,023 面；CRS = analysis_grid（CLCD Albers）；字段含 `patch_id, objectid, inst_year, inst_date, major_type, pv_area_m2_albers, n_parts` |
| 分析网格定义 | P01 产出 | `PVCropCarbon/metadata/analysis_grid.json` | Albers `+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +datum=WGS84 +units=m` |
| 环境 | server-env | `/home/server/Python_env/pvcarbon` | geopandas / shapely / pyogrio / scipy |

### 3. 步骤（有序、无歧义）

1. 读 `patches_clean.gpkg`，断言记录数 = 30,023、CRS = analysis_grid、`patch_id` 唯一。
2. 建 patch 的 STRtree 空间索引。**对每个阈值 d ∈ {30, 50, 100, 200, 300}**：
   a. 用 `patches.sjoin_nearest(patches, max_distance=d, distance_col="d")` 或
      `bbox 膨胀 d + 逐对 shapely.distance`，得到所有满足 **边界间距 ≤ d** 的无序 patch 对
      （排除自身对；`is_valid` 已在 P01 保证）。
   b. 以 patch 为节点、上述对为边，用 `scipy.sparse.csgraph.connected_components`
      求连通分量；每个分量 = 一个 Site。
   c. `site_id` 赋值：分量内 `patch_id` 的最小值决定分量顺序，按该顺序升序编号，
      `site_id = f"S{d:03d}_{seq:06d}"`（如 `S100_000042`）。保证重跑逐字节一致。
3. 产出 **长表** `site_membership.parquet`：`patch_id, site_threshold_m, site_id`
   （30,023 × 5 = 150,115 行）。
4. 产出 **Site 层几何** `site_candidates.gpkg`，每阈值一个 layer `sites_d{d}`：
   `site_id, site_threshold_m, patch_count, patch_area_sum_m2`（Σ patch 面积，非并集）,
   `hull_area_m2`（convex hull 面积）, `bbox_diag_m`（外接矩形对角线）,
   `span_max_m`（Site 内任意两 patch 边界最大间距，用 hull 顶点近似即可）,
   `n_inst_years`（分量内不同 `inst_year` 数）, `crosses_prov`（bbox 是否跨省，用候选省界粗判）,
   `has_offshore`（是否含 `major_type == "Ocean area"`）。
5. 诊断报告 `p02_site_diagnostics.md` + `.json`，每个阈值给：
   - Site 数、单 patch Site 占比；
   - `patch_count` 分布（P50/P90/P99/max）；
   - `hull_area_m2` 分布（P50/P90/P99/max，单位 km²）；
   - `span_max_m` 分布（P90/P99/max）；
   - `n_inst_years` 分布（多少 Site 跨 ≥3 年、≥5 年）；
   - **Top 20 巨型 Site**：`site_id, patch_count, hull_area_km2, span_max_km, n_inst_years,
     bbox 中心经纬度`（人工可去影像上核对是不是塔拉滩/库布其这类基地）；
   - 阈值间 Site 数与合并度的变化曲线（30→300 合并了多少）。
6. 出一张诊断图 `fig_P02_site_size.pdf/png`（复用 `figures/_style.py`）：x = 阈值，
   y = `hull_area` 各分位数；叠加 max 曲线。

### 4. 参数（具体值 / 显式网格，不留空）

- 阈值网格 = {30, 50, 100, 200, 300} m，全部产出，无基线选定。
- 距离定义 = 多边形**外环边界之间**的最短平面距离（Albers）；相接（距离 0）算连通。
- 多部件 patch：每个部件参与距离判定，但连通分量以 `patch_id` 为节点（一个 patch 整体归一个 Site）。
- 连通分量含单 patch 也算一个 Site。
- `巨型 Site` 报告阈值：`hull_area_m2 > 5e7`（50 km²）或 `span_max_m > 10000`（10 km）
  的 Site 全部进 Top 列表（不止 20 个则全列到 json）。
- 不做任何 Site 切分 / 直径上限（那是看完诊断后的决策，见失败即停第 3 条不是——见"给 Claude Code 的问题"）。

### 5. 输出

| 产物 | 路径 | 格式 |
|---|---|---|
| patch↔site 长表 | `PVCropCarbon/work/site_membership.parquet` | Parquet（150,115 行） |
| Site 候选几何 | `PVCropCarbon/work/site_candidates.gpkg`（layer `sites_d30/50/100/200/300`） | GPKG（Albers） |
| 诊断报告 | `PVCropCarbon/outputs/audits/p02_site_diagnostics.{md,json}` | md + json |
| 诊断图 | `PVCropCarbon/outputs/figures/fig_P02_site_size.{pdf,png,yaml}` | PDF/PNG + sidecar |

### 6. 验收门槛（可判定）

- [ ] `site_membership.parquet` = 150,115 行；每个 `(patch_id, site_threshold_m)` 唯一；
      每个阈值下 patch 全覆盖（30,023）。
- [ ] 阈值越大，Site 数单调不增（30 m Site 数 ≥ 50 m ≥ … ≥ 300 m）。
- [ ] 每个 Site 的 `patch_count` 之和 = 30,023（各阈值分别核对）。
- [ ] `site_id` 两次独立运行结果 diff 为空（确定性）。
- [ ] 诊断报告含 5 个阈值的全部分位数 + Top 巨型 Site 列表 + 阈值合并曲线。
- [ ] 诊断图生成且带 `.yaml` sidecar。

### 7. 失败即停（写进运行记录的 BLOCKED，不要自行解决）

- `patches_clean.gpkg` 记录数 ≠ 30,023 或 CRS 不是 analysis_grid。
- 任一阈值下 `sjoin_nearest` 边数异常（如某 patch 与 > 2000 个 patch 在 30 m 内——
  提示几何或投影错误）。
- 内存不足以在服务器完成 300 m 阈值的逐对距离（报告峰值内存与建议方案）。
- 环境 `/home/server/Python_env/pvcarbon` 不可用。

---

## 运行记录（Codex）

卡片 commit: `<短哈希>`  ·  环境: `code/env/` @ sha256 `<…>`  ·  起止: `<…>`

### 实际参数（与卡片的差异必须标注）

### 产物

| 文件 | SHA256 | 行数/尺寸 |
|---|---|---|

### 验收门槛结果

- [ ]

### BLOCKED / 异常

### 给 Claude Code 的问题

1. 巨型 Site 分布如何？是否需要在 P03 前引入 Site 直径/面积上限或二次切分（决策 #2「看了再定」）。

> 完成后：`experiment_registry.csv` 加一行；本文件 status 改 done/blocked；同步 `tasks.tsv` T02。

---

## 解读（Claude Code）

### 回答了什么

<对照 §1：5 阈值 Site 候选是否干净；巨型 Site 严重程度。>

### 是否触发停止/降级条件

- [ ] 巨型 Site 可接受 → P03 直接用连通分量（方案 a）
- [ ] 巨型 Site 过多 → 先补一张"Site 切分规则"卡片（方案 b），再 P03

### 下一步

- [ ] 起草 P03（Site→Phase）
- [ ] 催 S07 人工样本（基线阈值选定的前置）
