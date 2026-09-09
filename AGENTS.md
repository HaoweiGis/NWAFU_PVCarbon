# AGENTS.md

面向 AI 编码助手的项目说明。人类读者请先看 [README.md](README.md) 和
[CURRENT_V1.md](CURRENT_V1.md)。

## 项目概况

**NWAFU_PVCarbon** —— 在县域尺度识别建于建设前稳定耕地的地面光伏是否相对有效反事实
引致场址外额外、持续的新增耕地，量化由此产生的 iLUC 碳排放、对光伏毛减排收益的年度与
累计抵消率，以及观测期 iLUC 排放峰值年与累计碳回收年。

- 主处理链：

  ```
  PV 图斑 → Patch→Site→Phase 聚合（邻接阈值待样本定）
   → 建设前稳定耕地暴露（CLCD 2000–2025，宽松/中心/严格三口径）
   → 0–5 / 5–10 / 10–20 / 20–50 km 环带场址外首次稳定新增耕地
   → Phase–环带–年 与 县–年 面板 → 堆叠事件研究 / 三重差分 因果识别
   → 归因新增耕地按转化前地类 × EF(AGB + BGB + 0–30cm SOC) → C_iLUC(c,t)
   → B_gross(c,t) = G_PV × 边际电网 EF
   → R_iLUC 抵消率 / 观测 iLUC 峰值年 / 累计碳回收年
  双县域并行：pv_county（责任核算）+ conversion_county（属地核算）
  ```

- 当前阶段：**数据准备与结构审计**。技术路线已冻结（V1，2026-08-31），必要数据收集与
  质量审核进行中；在因果识别数据（D05–D08）与碳/发电参数（D09–D14）冻结前，只产出
  候选统计，**不发布**正式因果 iLUC、排放吨数、抵消率或碳回收年。
- 文档语言：中文（公式、字段名可用英文符号）。代码注释与标识符：英文。

## 计算与数据

本地讨论 + 服务器计算（SSH）。

| 位置 | 地址 | 内容 |
|---|---|---|
| 本地仓库（本目录，Windows） | `D:\Haowei_Papers\NWAFU_PVCarbon` | 代码、合同、文档、清单、研究区等必要小文件 |
| 计算服务器 | `ssh NWAFU5090`（=8.130.68.96:30383，公钥 `id_ed25519_NWAFU5090`）| 全部大体量栅格/矢量数据与实际计算 |

服务器路径根：`/data/ssd/haoweimu/NWAFU_PVCarbon`（SSD，主项目与 `PVCropCarbon` 子流水线）；
`/data/hdd/haoweimu/datasets`（HDD 公共数据集，CLCD `D001_CLCD_2000-2025`、
ERA5-Land `D005_ERA5_Land` 等）。本地与服务器采用**相同一级目录结构**；大数据不进本地仓库。
计算端 conda 环境 `pvcarbon`（`/home/server/Python_env/pvcarbon`）已建并锁定
（[docs/tasks/T-2026-09-03-server-env.md](docs/tasks/T-2026-09-03-server-env.md)，2026-09-08：
GDAL 3.12.3 / PROJ 9.7.1 / GEOS 3.14.1 / geopandas 1.1.4 / rasterio 1.4.4 / exactextract /
statsmodels / linearmodels / pyfixest；锁与 sha256 在 `code/env/`）。激活：
`source /home/server/miniconda3/etc/profile.d/conda.sh && conda activate pvcarbon`。

- 原始大数据（CLCD、ERA5-Land、SoilGrids、ESA CCI Biomass、PV 图斑等）保存在服务器
  `input/` 语义位置，**只读**；本地仅保留清单、校验和与路径映射。
- 本地 `data_sources/` 现有原始压缩包（省市县边界、PV 电站 2010–2022）仅作暂存，不进 git
  （`.gitignore` 已排除 `*.zip` / `*.tif` 等）。
- 所有派生结果写入 `output/`；本地不保留大产物，仅保留 `output/manifests/` 与论文图。
- `PVCropCarbon/` 是既有的**独立数据生产子流水线**（含水稻/玉米/小麦种植退出，范围大于
  V1 主线），保留原样，不并入根 `code/`；其自身的 `AGENTS` 约束见该目录 README。

## 目录结构

```
AGENTS.md              双工具共享契约（本文件）。CLAUDE.md 仅 @AGENTS.md
code/
  AGENTS.md            Codex 执行规则（失败即停 / 环境 / 出图）
  figures/             出图脚本（matplotlib），_style.py 为公用样式
  env/                 可复现计算环境（Codex 建并锁定）
  ...                  预处理 / 分析 / 建模代码（V1 主线）
output/
  manifests/           experiment_registry.csv —— 运行登记（provenance）
  figures/             论文图：矢量 PDF/SVG + 300dpi PNG + 同名 .yaml sidecar
  logs/                批量运行日志 + failure_registry.csv
  ...                  运行产物（大文件 gitignore）
docs/
  experiment_design/   方法方案 + 每个实验一个文件 E0X-<slug>.md（卡片/运行记录/解读三节）
  tasks/               工程任务卡 T-YYYY-MM-DD-<slug>.md（非实验的一次性交接）
  paper/               论文正文、图注、参考文献（Claude Code 写）
  各主题带 INDEX.md
researchwrite/versions/v1/   V1 研究设计、证据表、论证图、章节合同、风格指南（已有）
00_project/manifests/        目录整理与文件校验记录（已有）
data_sources/                本地原始数据暂存（gitignore）
references/                  论文、来源笔记、截图（已有）
scripts/                     本地准备与审计脚本（已有）
PVCropCarbon/                独立数据生产子流水线（已有，保留）
input/                       只读输入数据（本地仅存必要小文件，主体在服务器）
```

## 硬性约定

1. **`input/` 只读**：代码绝不写入或覆盖 `input/`，所有派生结果写入 `output/`。
2. **临时文件**只进 `output/**/_scratch/` 或 `output/temp/`，通过检查后再提升为正式输出。
3. **版本管理**：同一主题的多个版本放在该主题的 `versions/` 目录；文件名里的版本号只在
   同一命名系列内比较新旧。当前有效版本**以各主题的 `INDEX.md` 为准**。新增方法版本必须
   进入 `researchwrite/versions/v2/` 等独立目录，并同步更新 `CURRENT_V1.md`。
4. **每次批量运行**在 `output/logs/` 记录参数、软件版本、起止时间、失败条目 ID；
   失败条目写 `failure_registry.csv`，不得静默跳过。
5. 原始数据只读保存，校验和记入 `00_project/manifests/` 或运行记录。

## 工作流与分工

本项目由两个 AI 角色协作，共用同一 git 仓库：

- **Claude Code** = 方法论顾问 / 审稿人 / 共同作者。讨论方案、写实验卡、解读结果、写论文。
- **Codex** = 实验工程师。读实验卡 / 任务卡，写 `code/`，运行，出图，填运行记录。

### 谁写什么

| 内容 | 负责人 |
|---|---|
| `docs/experiment_design/`（方法方案、实验卡的**卡片**节和**解读**节）、`docs/paper/`、`researchwrite/` | Claude Code |
| `code/`、`output/`、实验卡的**运行记录**节、`00_project/manifests/`（跑审计时） | Codex |
| `docs/tasks/`（任务卡：目标/验收） | Claude Code 起草；**执行记录**节由 Codex 写 |
| `AGENTS.md`、`code/AGENTS.md`、各 `INDEX.md` | 谁改结论谁更新，**结论性改动必须走版本升级** |

### 红线

- **Claude Code**：不跑重型实验、不 commit 到 `code/` 或 `output/`。代码贡献只以伪代码/原型
  写进实验卡，由 Codex 落地。
- **Codex**：不改 `researchwrite/versions/` 或 `docs/experiment_design/versions/` 的结论、
  不动术语边界、不擅自重设计方法。卡片有误或不可行 → **停下，在运行记录里写 `BLOCKED:`
  报告**，不要自行绕过。详见 [code/AGENTS.md](code/AGENTS.md)。

### 生命周期

```
① 讨论   Claude Code + 用户   迭代方法 → docs/experiment_design/E0X-<slug>.md「卡片」节 (status: draft)
② 就绪   用户确认 → status: ready → commit "spec: E0X ready"
③ 执行   Codex   读该文件 + code/AGENTS.md → 改 code/ → 运行 → 产物落 output/ →
                 填「运行记录」节 + experiment_registry.csv → status: done → commit "run: E0X"
④ 出图   Codex   code/figures/fig_E0X.py → output/figures/ + .yaml sidecar → commit "fig: E0X"
⑤ 解读   Claude Code + 用户   git pull → 读运行记录 + 图 → 填「解读」节 →
                              判断是否触发停止/降级条件 → 更新 INDEX.md 状态表 → commit "interp: E0X"
⑥ 若方法需调整 → 回 ①
```

每次开工前 `git pull`。commit 前缀：`spec:` `task:` `run:` `fig:` `method:` `interp:` `data:` `env:` `chore:`。

### 卡片是唯一接口

Codex 不读聊天记录。可执行的卡片必须：参数全部落地为具体值或显式网格、每个输入有绝对路径 +
版本、每个输出有路径 + 命名、验收门槛可判定、列出「失败即停」条款。模板：
[docs/experiment_design/_TEMPLATE.md](docs/experiment_design/_TEMPLATE.md)、
[docs/tasks/_TEMPLATE.md](docs/tasks/_TEMPLATE.md)。

## 冻结决策（改动必须新建 versions/ 文档 + 更新 INDEX.md，不得静默修改）

当前权威方法文档：[researchwrite/versions/v1/exports/V1_研究设计与数据需求.md](researchwrite/versions/v1/exports/V1_研究设计与数据需求.md)
（配套 [V1_最小必要数据与下载方案.md](researchwrite/versions/v1/exports/V1_最小必要数据与下载方案.md)）。
子流水线 CCD 部分见
[PVCropCarbon/technical/CCD_2001_2024_技术思路_V1.md](PVCropCarbon/technical/CCD_2001_2024_技术思路_V1.md)（统计口径尚未冻结）。

1. **观测窗口**：PV 建设年 2010–2022；CLCD 年度土地覆盖 2000–2025；CCD（子线）2001–2024。
   2023 年以后仅情景模拟，不外推确定回收年。
2. **分析坐标系 / 分析网格 / 分辨率**：**已冻结**（P01 核对 26 幅 CLCD 一致，2026-09-09；
   定义见 `PVCropCarbon/metadata/analysis_grid.json`）。CLCD v01 原生网格 ——
   Albers Equal Area（`+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +x_0=0 +y_0=0
   +datum=WGS84 +units=m`），30 m，栅格 161378×135079，左上角原点
   (X=-2629624.783, Y=5924251.560)，**nodata = 0**（CLCD 类别 0 = 无数据/背景，非有效地类）。
   CCD（EPSG:4326）与 PV 图斑（WGS84）重投影到此网格；类别栅格重采样只用最近邻；
   面积/距离统计在此等面积系下完成。
3. **研究区**：中国大陆含地面光伏的县域子集。CCD 缺省地区（北京、青海、西藏、台湾、香港、
   澳门，须用下载文件树逐项核验）编码 `coverage_missing`，禁止填类别 0。
4. **权威县—市—省边界与稳定行政代码 + 2010–2022 行政区划变更对照表**：**待冻结 (E00, D05)**。
   现有候选边界（省/市/县 34/375/2891）仅供试算。
5. **Patch→Site→Phase 邻接阈值**：候选 30 / 50 / 100 / 200 / 300 m，主阈值**待冻结**
   （依距离分布 + 分层高分影像样本 D06），其余作敏感性。`phase_id` 恒由完整
   `Site + 建设年份` 生成；先构造完整 Phase / 完整环带，再与县界相交。
6. **建设前稳定耕地口径**：宽松（前 3 年 ≥2 年耕地）、中心（前 5 年 ≥4 年，**主口径**）、
   严格（前 5 年连续）。主处理强度 = Phase 与建设前稳定耕地重叠面积，称"稳定耕地暴露/占用"。
7. **场址外环带**：标准 0–5 / 5–10 / 10–20 / 20–50 km；近距离敏感性 0–1 / 1–2 / 2–5 km。
   新增耕地须 CLCD 确认非耕地→耕地且连续保持 ≥2 年；首次扩张与复垦分开标记。
8. **双县域核算并行发布**：`pv_county`（责任）与 `conversion_county`（属地），保留县际土地
   压力转移矩阵；两套结果差异必须保留，不得只选更有利的一套。
9. **iLUC 碳核算期**：20 年与 30 年并行；单次脉冲释放与分期释放曲线作为两种情景，不混用；
   EF 至少覆盖地上/地下生物量碳 + 0–30 cm SOC；报告产品/参数敏感性与 Monte Carlo 区间。
10. **电网排放因子**：主情景 = 官方区域电网 OM（边际）；官方平均因子仅作标注清楚的敏感性；
    2020–2022 连续官方区域 OM **待补齐/冻结 (D14)**；主文必须区分边际与平均因子。
11. **因果解释门槛**：仅当 ①建设前趋势近零 ②效应随暴露强度增 ③效应随距离衰减
    ④非耕地 PV 无同幅效应 ⑤通过虚假建设年/场址/阈值/环带安慰剂 —— 五条同时满足，
    才用"引致 / iLUC"。

## 术语边界（写代码、命名输出、写报告时都适用）

允许：引致新增耕地、责任县、属地县、iLUC 排放、抵消率（R_iLUC）、观测 iLUC 峰值年、
累计碳回收年、稳定耕地暴露/占用、观测新增耕地、空间关联、"退出水稻/小麦/玉米或退出主粮
类别"。始终区分：观测 / 因果归因 / 情景外推。

禁止（直到拿到对应验证数据）：县域碳达峰、县域碳中和、已证明诱发、"所有新增耕地"、
实现达峰、有效耕地损失、绝对风险/确定因果类断言。反事实识别通过前，场址外新增耕地只能称
"观测新增"或"空间关联"，不得称"诱发 / iLUC"；未在研究期内转正的县报告"未回收"，不得
外推确定年份；CCD 类别 0 不能单独证明"退出全部耕作"。

## 代码风格

- Python 为主（3.x）。GIS 依赖：GDAL / rasterio / geopandas / pyproj / shapely；
  数值 numpy / pandas；出图 matplotlib。无 Julia。
- 审计与完整性检查脚本尽量**纯标准库且只读**，产物只写 `--output` 指定目录。
- 重投影须锁定 GDAL / PROJ 版本并在每次运行记录登记；类别栅格重采样只用最近邻。
- 英文标识符与注释；函数拆分、日志格式由 Codex 自定。
- 出图脚本约定见 [code/AGENTS.md](code/AGENTS.md)。

## 已知数据问题（勿"修复"原始文件）

- 主 PV 图斑（陈月红，30,023 面，WGS84 地理，字段 `OBJECTID / PV_Area(km², 已确认) /
  Inst_time(YYYYMMDD) / Inst_year(2010–2022) / Major_type / Lat / Lon`）：
  - **3 条建设日期异常**，派生层修正（不改原始 shp）：`OBJECTID=21400`（`Inst_time=201650831` 月份非法 → 用年中占位）、
    `20046`（`20170721` vs `Inst_year=2018` → 以 Inst_time 为准改年）、`20048`（`20190321` vs 2018 → 同）。
  - **43 组完全重复几何（87 patch，属性亦一致，数字化重复）**，P01 每组保留 `patch_id` 最小者、去 44 个 →
    派生 patch 层 **29,979 面**（审计 `PVCropCarbon/outputs/audits/p01_duplicate_patches.csv`）。
  - 144 个源无效几何 `make_valid` 修复；127 个 MultiPolygon（P02 距离判定按部件）。
  - 95 面 `Major_type=Ocean area`（海上光伏，可能无所属县）。
- ERA5-Land 有未完成 / `.part` 文件，仍在下载；冻结变量与年份后再核完整清单。
- D03 Agrivoltaics V3 经纬度字段名有误，在派生层更正，报告与主 PV 图斑的空间—年份匹配率。
- 候选县界仅有 `name` / `gb` 字段，缺权威来源元数据、历史有效期、上级代码与行政区划变更表
  —— 只能试算。
- CCD 缺省地区须用下载文件树逐项核验，编码 `coverage_missing`，禁止填类别 0。
- SoilGrids（中国分块约 41/252）、ESA CCI Biomass v7（尚未开始）仍缺；未冻结前不得报告
  iLUC 吨数。

## 常用命令

```bash
python scripts/audit_boundary_shapefiles.py --help      # 本地：候选县界只读审计
python PVCropCarbon/scripts/preflight.py                 # 服务器：PVCropCarbon 生产前只读检查
bash   PVCropCarbon/scripts/run_pipeline.sh              # 服务器：统一入口（阻塞项清零前仅预检即停）
bash   PVCropCarbon/scripts/download_ccd_sciencedb.sh    # 服务器：CCD 官方 ZIP 获取
python PVCropCarbon/scripts/verify_ccd_archive.py        # 服务器：CCD ZIP / TIFF 完整性校验
```

---

本仓库是 git 仓库（远程 `https://github.com/HaoweiGis/NWAFU_PVCarbon`）。同步：本地与计算端
各一个 clone，靠 push/pull 传递方案与结果；大数据经 `.gitignore` 排除。
