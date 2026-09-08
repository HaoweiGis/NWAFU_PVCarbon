# P03 Site → Phase（完整批次几何）

status: draft            <!-- draft | ready | running | done | blocked -->
前置依赖: P02 done（`site_membership.parquet` + `site_candidates.gpkg`）
= metadata/tasks.tsv 的 T03
后续 P04 用本卡产出的**完整 Phase** 与权威县界相交，才得到 T01 批次基础数据表。

**卡片** = Claude Code 写 → 用户批准 → **运行记录** = Codex 写 → **解读** = Claude Code 写。

---

## 卡片（Claude Code）

### 1. 目标（一句话）

按 `Phase = (site_id, 修正后建设年)` 把 patch 聚成建设批次，为 **5 个候选阈值各生成一套
完整 Phase 几何**（并集），带 `patch_count / phase_area / n_patch_parts`，并保留
`phase_id ↔ patch_id` 明细，供 P04 与县界相交。**不做县相交、不筛地类**（全部 30,023 patch
形成的 Phase 都进）。

### 2. 输入（绝对路径 + 期望规格）

| 数据 | 版本 | 路径（服务器） | 期望 |
|---|---|---|---|
| patch↔site 长表 | P02 产出 | `PVCropCarbon/work/site_membership.parquet` | 150,115 行；`patch_id, site_threshold_m, site_id` |
| 清洗后 patch 层 | P01 产出 | `PVCropCarbon/work/patches_clean.gpkg`（`patches`） | 30,023 面；`patch_id, inst_year, inst_date, inst_date_flag, major_type, pv_area_m2_albers, geom(Albers)` |
| 分析网格 | P01 | `PVCropCarbon/metadata/analysis_grid.json` | Albers |

### 3. 步骤（有序、无歧义）

1. join `site_membership` × `patches_clean`（on `patch_id`）。断言每阈值 30,023 patch。
2. **对每个阈值 d**：
   a. 按 `(site_id, inst_year)` 分组 → 每组一个 Phase。
   b. `phase_id = f"{site_id}_{inst_year}"`（如 `S100_000042_2016`）。
   c. Phase 几何 = 组内 patch 几何的 `unary_union`（并集，dissolve 内部缝隙）。
   d. 字段：
      - `phase_id, site_id, site_threshold_m, year(=inst_year)`
      - `patch_count`（组内 patch 数）
      - `phase_area`（并集面积 m²，Albers）
      - `patch_area_sum_m2`（Σ 单 patch 面积；与 `phase_area` 的差 = 重叠/缝隙量）
      - `n_geom_parts`（并集的多面部件数——反映"同年分块建"）
      - `inst_date_min, inst_date_max`（组内精确日期范围，供后续 pre/post 窗口用）
      - `major_type_mode`（组内按面积加权的主导建设前地类）
      - `major_type_mix`（组内各 `major_type` 面积占比，json 字符串）
      - `is_offshore`（组内是否含 `major_type == "Ocean area"`）
3. 产出 **Phase 层几何** `phases.gpkg`，每阈值一个 layer `phases_d{d}`。
4. 产出 **Phase↔patch 明细** `phase_patch_map.parquet`：
   `phase_id, site_threshold_m, patch_id, objectid, inst_date, pv_area_m2_albers`。
5. 产出报告 `p03_phase_summary.md` + `.json`，每阈值给：Phase 数、
   `patch_count` 分布、`phase_area` 分布（P50/P90/P99/max，km²）、
   单 patch Phase 占比、跨年 Site 的 Phase 展开情况（一个 Site 平均几个 Phase）、
   `is_offshore` Phase 数、`major_type_mode` 分布（多少 Phase 主导地类是 Cropland）。
6. 诊断图 `fig_P03_phase_by_year.pdf/png`：x = 建设年 2010–2022，y = Phase 数与
   Σ`phase_area`（双轴），按基线候选阈值（先用 100 m 画，最终基线定后重画）。

### 4. 参数（具体值 / 显式网格，不留空）

- 阈值网格 = {30, 50, 100, 200, 300} m，全部产出。
- 建设年 = P01 修正后的 `inst_year`（3 条异常已在 P01 处理）。
- Phase 几何 = `unary_union`；不 simplify、不 buffer。
- `major_type_mode` = 组内按 `pv_area_m2_albers` 加权众数；并列时取字典序最小。
- 全部 30,023 patch 参与，**不按 `major_type` 过滤**（非耕地 PV 是后续对照组；海上 PV 打 flag 保留）。
- 空间上分离但 `(site_id, year)` 相同 → 仍是一个 Phase（`n_geom_parts > 1`）。

### 5. 输出

| 产物 | 路径 | 格式 |
|---|---|---|
| Phase 候选几何 | `PVCropCarbon/work/phases.gpkg`（layer `phases_d30/50/100/200/300`） | GPKG（Albers） |
| Phase↔patch 明细 | `PVCropCarbon/work/phase_patch_map.parquet` | Parquet |
| Phase 汇总报告 | `PVCropCarbon/outputs/audits/p03_phase_summary.{md,json}` | md + json |
| 诊断图 | `PVCropCarbon/outputs/figures/fig_P03_phase_by_year.{pdf,png,yaml}` | PDF/PNG + sidecar |

### 6. 验收门槛（可判定）

- [ ] 每个阈值下：Σ `patch_count`（所有 Phase）= 30,023；`phase_patch_map` 每
      `(patch_id, site_threshold_m)` 恰好属于 1 个 `phase_id`。
- [ ] `phase_id` 唯一；`phase_id` 拆解回 `(site_id, year)` 与 `site_membership` 一致。
- [ ] 每个 Phase：`phase_area ≤ patch_area_sum_m2`（并集不大于求和），且
      `(patch_area_sum_m2 - phase_area) / patch_area_sum_m2 < 0.05`（重叠很小；否则报告哪些 Phase）。
- [ ] Σ 所有 Phase 的 `phase_area`（阈值内）在阈值间应**单调不增或持平**
      （大阈值合并更多、并集内部缝隙被填 → 总并集面积略增也可接受，差 < 1%）。
- [ ] 报告含 5 阈值全部分位数；诊断图带 sidecar。
- [ ] `year` 取值全部 ∈ [2010, 2022]。

### 7. 失败即停（写进运行记录的 BLOCKED，不要自行解决）

- 任一 patch 在某阈值下未落入任何 Phase，或落入 > 1 个。
- 某 Phase `phase_area > patch_area_sum_m2`（几何/投影错误）。
- 重叠量 ≥ 5% 的 Phase 超过总数 1%（提示 patch 层有大量重复几何——回 P01）。
- `unary_union` 在最大 Phase 上超时/超内存（报告规模与建议）。

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

1.

> 完成后：`experiment_registry.csv` 加一行；本文件 status 改 done/blocked；同步 `tasks.tsv` T03。

---

## 解读（Claude Code）

### 回答了什么

<完整 Phase 是否成型；跨年 Site 展开是否合理；主导地类为 Cropland 的 Phase 占比。>

### 是否触发停止/降级条件

### 下一步

- [ ] 边界源决策后起草 P04（Phase×县 → T01 表）
- [ ] Phase footprint 已可作为主线环带（P07）的输入前体
