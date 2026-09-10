# PVCropCarbon/AGENTS.md

`NWAFU_PVCarbon` 下的**数据生产子项目**。先读仓库根 [../AGENTS.md](../AGENTS.md)——
双工具分工、生命周期、commit 前缀、术语边界的总规则都在那里，本文件只写子项目差异。
人类读者看 [README.md](README.md)。

## 子项目概况

**目标**：把《[数据清单.docx](数据清单.docx)》定义的四张结果表（T01–T04，共 52 个源字段 +
[metadata/required_extra_fields.tsv](metadata/required_extra_fields.tsv) 的 10 个必需扩展键）
转化为**可重复、可审核**的数据流水线。

- 范围**大于主项目 V1**：含水稻/玉米/小麦三类主粮的种植退出（T02）与新增农业排放（T04 `Agrco2`）。
- 主处理链（对应 [metadata/tasks.tsv](metadata/tasks.tsv) 的 T01–T11）：

  ```
  T01 源审计与冻结  → T02 Patch→Site → T03 Site→Phase → T04 Phase×县相交
   → T05 建设前稳定主粮 → T06 建设后作物持续/退出
   → T07 Phase–环带–年 面板（土地变化）→ T08 反事实归因
   → T09 土地转化碳(Landco2) → T10 新增农业排放(Agrco2)
   → T11 汇总为 T01–T04 四张表
  ```

- 当前阶段：**数据获取与结构审计**。计算环境已就绪（`pvcarbon`，2026-09-08）；
  P01（源审计+网格冻结）、P02、P03 可跑，**不阻塞在 S06/S07**。P04 及之后仍 BLOCKED：
  关键缺失 S06（权威县界）、S07（Site 阈值样本）、S08（土地变化样本）、S13（农业排放因子）；
  进行中 S03–S05（CCD）、S09（ERA5）、S12（土壤/植被碳）。
  **统计口径尚未冻结**（见 [technical/CCD_2001_2024_技术思路_V1.md](technical/CCD_2001_2024_技术思路_V1.md)
  §"状态"）。

## 计算与数据

服务器：`ssh NWAFU5090`，子项目根
`/data/ssd/haoweimu/NWAFU_PVCarbon/PVCropCarbon`。路径见
[config/paths.server.env](config/paths.server.env)。共享源数据**不复制**，通过 `source_links/`
的符号链接**只读**引用主项目与 HDD 数据集。

本地只保存代码、合同、清单、日志；原始大数据与生产结果留在服务器。

## 目录结构（子项目内）

```
AGENTS.md              子项目契约（本文件）
README.md              人类入口
数据清单.docx          四张结果表的原始定义（勿改）
metadata/              字段合同与源状态（tsv，Claude Code + 用户维护）
  output_fields.tsv        52 个源字段的规范定义
  required_extra_fields.tsv 清单缺失但必需的 10 个键
  source_status.tsv        S01–S13 源现状与阻塞条件
  tasks.tsv                T01–T11 生产阶段、依赖、验收、status
  CCD_2001_2024_source.tsv  CCD 数据集身份（已核实事实）
technical/             方法思路（口径未冻结）
code/
  AGENTS.md            Codex 执行规则（子项目）
  figures/_style.py    出图公用样式
  ...                  卡片驱动的流水线代码（T01–T11 实现，新建）
scripts/               既有独立工具（下载 / 预检 / 校验，勿并入 code/）
docs/
  experiment_design/   生产阶段卡 P01–P11（= tasks.tsv 的 T01–T11）+ _TEMPLATE + INDEX
  tasks/               一次性工程任务卡 T-YYYY-MM-DD-<slug>
work/                  服务器中间结果（gitignore；相当于根约定的 output/_scratch/）
outputs/               服务器正式输出，仅校验后写入（gitignore，除 manifests/）
  manifests/experiment_registry.csv   运行登记（进版本库）
logs/                  服务器运行日志（gitignore）
```

**与根约定的目录名映射**：根用 `output/**/_scratch/` 与 `output/`，子项目沿用既有的
`work/`（中间）与 `outputs/`（正式）。含义相同，不重命名既有目录。

## 卡片编号

生产阶段卡 `P01`–`P11`，与 [metadata/tasks.tsv](metadata/tasks.tsv) 的 `T01`–`T11` **一一对应**
（用 `P` 前缀避免与 `docs/tasks/` 里 `T-YYYY-MM-DD` 的一次性工程任务卡混淆）。
`tasks.tsv` 是阶段依赖与 status 的权威表；`docs/experiment_design/INDEX.md` 汇总卡片指针。

## 冻结决策（子项目专属；改动走 versions/ + 更新 INDEX）

当前权威方法文档：
- [technical/光伏建设批次基础数据表_技术思路_V1.md](technical/光伏建设批次基础数据表_技术思路_V1.md)
  —— T01（Patch→Site→Phase→县）方法说明。Site 邻接阈值临时基线 **100 m**，正式冻结待 S07。
- [technical/CCD_2001_2024_技术思路_V1.md](technical/CCD_2001_2024_技术思路_V1.md)
  —— 作物（CCD）部分（**统计口径与正式分析参数尚未冻结**）。

**已核实并冻结（数据身份，见 CCD_2001_2024_source.tsv）**：

1. CCD 数据集：DOI `10.57760/sciencedb.32361`，V1，CC BY 4.0，672 个 GeoTIFF，
   ZIP `10163712508` 字节，EPSG:4326，名义 30 m，2001–2024 逐年，28 个主要农业省级区域。
2. CCD 类别体系 `{0,1,2,3,4,5,6,9}`：0 非目标/背景、1 单季稻、2 双季稻、3 冬小麦、
   4 冬小麦—单季稻轮作、5 甘蔗、6 玉米、9 冬小麦—玉米轮作。
3. 时间窗口口径：建设年 `y` 排除；建设前 宽松（`y-3..y-1` ≥2 年）/ 中心（`y-5..y-1` ≥4 年）/
   严格（`y-5..y-1` 连续）；建设后持续 = `y+1` 且 `y+2`。
4. `phase_id` 恒由完整 `Site + 建设年份` 生成；先构造完整 Phase / 完整环带，再与县界相交；
   环带只计算一次，跨县 Phase 不按县分片缓冲。
5. 标准环带 0–5 / 5–10 / 10–20 / 20–50 km；近距离敏感性 0–1 / 1–2 / 2–5 km。

**待冻结（不得由 Codex 自行决定，须先出卡片讨论）**：

6. 分析坐标系 / 分析网格 / 分辨率 —— **P01 冻结**，与主线 E00 同一决策。拟采用 CLCD 原生
   网格：Albers（`+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +datum=WGS84 +units=m`），
   30 m，161378×135079，原点 (X=-2629624.783, Y=5924251.560)。CCD（4326）与 PV 图斑最近邻/
   重投影到此网格；面积在此等面积系下。
7. CCD 缺省地区（北京、青海、西藏、台湾、香港、澳门）—— **须用下载文件树逐项核验**，
   编码 `coverage_missing`，**禁止填类别 0**。青海、西藏是地面光伏大省，落在缺省区的 Phase
   是否走 CLCD-only 降级口径 —— P01 讨论。
8. 权威县界与稳定行政代码 + 2010–2022 变更表（S06）—— **待冻结**，与主线 D05 同源。
9. Site/Phase 主邻接阈值（S07）—— **待冻结**，候选 30/50/100/200/300 m。
10. `soil_quality` 指标定义 —— **未定义，禁止直接生产**。
11. 全部 `dist_*` 字段的道路/城市/电网等级与年份基准（S10/S11）—— **待冻结**。
12. `Agrco2` 系统边界（S13）—— **待冻结**。主线 V1 把"新增农业排放"排除在 iLUC 主抵消率
    分子外只作扩展；子项目是否一致 —— P10 讨论。
13. `Landco2` 核算期与释放曲线 —— 20/30 年并行、脉冲 vs 分期两情景，不混用。

## 术语边界（在根 AGENTS.md 基础上补充）

允许："退出水稻/小麦/玉米"、"退出主粮类别（staple_union）"、"观测新增耕地"、"空间关联"。

禁止：仅凭 CCD 类别 0 断言"退出农业/退出全部耕作"（类别 0 只映射若干目标作物，须结合
CLCD 与其他证据）；反事实识别（P08）通过前，环带新增耕地不得称"诱发 / iLUC"；
把"作物替代"当"主粮退出"（4→3 是水稻退出但小麦持续，9→6 是小麦退出但玉米持续，须分开）。

## 已知数据问题（勿"修复"原始文件）

- CCD 缺省地区须逐项核验，编码 `coverage_missing`。
- CCD 类别 0 语义歧义（见术语边界）。
- 主 PV 图斑 3 条建设日期异常（`OBJECTID` 21400 / 20046 / 20048）；95 面 `Major_type=Ocean area`；
  无 Site/Phase 字段、无稳定 patch ID（仅 `OBJECTID` 0..30022）。D03 Agrivoltaics 经纬度字段名有误。
  详见根 [../AGENTS.md](../AGENTS.md) 已知数据问题。
- ERA5-Land 有未完成 / `.part` 文件。
- 主项目未找到 DEM / 坡度（S10）与道路/城市/电网历史图层（S11）来源。
- SoilGrids / ESA Biomass 获取与参数冻结未完成（S12）。

## 常用命令

```bash
python scripts/preflight.py              # 生产前只读检查（关键源未清零返回非零）
python scripts/verify_ccd_archive.py <zip>   # CCD ZIP / 672 TIFF 结构校验，不解压
bash   scripts/download_ccd_sciencedb.sh # CCD 官方 V1 ZIP 获取（aria2）
bash   scripts/run_pipeline.sh           # 统一入口：先跑 preflight，阻塞项清零前即停
```
