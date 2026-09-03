# PVCropCarbon/code/AGENTS.md

面向在 `PVCropCarbon/code/` 下工作的 AI（主要是 Codex）。先读：
仓库根 [../../AGENTS.md](../../AGENTS.md) → 子项目 [../AGENTS.md](../AGENTS.md) → 本文件。

## 你的职责

执行 `PVCropCarbon/docs/experiment_design/P0X-<slug>.md`（生产阶段卡，= `metadata/tasks.tsv`
的 T0X）和 `PVCropCarbon/docs/tasks/T-*.md`（一次性工程任务卡）：实现代码、在服务器运行、
产物写入 `outputs/`、在同一卡片文件里填「运行记录」/「执行记录」节。

## 代码放哪

- **`PVCropCarbon/code/`**：卡片驱动的流水线阶段实现（新建，可按 `preprocess/ site_phase/
  crop/ ring/ attribution/ carbon/` 分子目录）。
- **`PVCropCarbon/scripts/`**：既有独立工具（`download_ccd_sciencedb.sh`、`preflight.py`、
  `verify_ccd_archive.py`、`run_pipeline.sh`）。**勿并入 `code/`，勿重写**；如需扩展，加新文件。

## 执行卡片的固定流程

1. `git pull`，读卡片全文 + 本文件 + 子项目 AGENTS.md + 根 AGENTS.md。
2. 确认卡片「输入」里每个路径存在且规格匹配（CRS / 分辨率 / NoData / 类别值域 / 单位）。
   源是否可用以 `metadata/source_status.tsv` 和卡片为准，不要自己放宽。
3. 实现或修改脚本。在服务器运行。中间结果落 `work/`，校验通过的正式产物落 `outputs/`。
4. 逐条核对卡片「验收门槛」，结果写进卡片的「运行记录」节。
5. 在 `outputs/manifests/experiment_registry.csv` 增加一行。
6. 卡片 status 改为 `done`（或 `blocked`）；同步更新 `metadata/tasks.tsv` 对应行的 `status`；
   `commit` + `push`。

## 必须停止并报告 `BLOCKED:` 的情况（不要自行决定）

- 卡片未给出的参数值（作物年份窗口、邻接阈值、核算期、资格掩膜规则、系统边界……）
- 输入路径不存在 / CRS / 分辨率 / 类别值域 / 单位与卡片不符
- 任一验收门槛不通过（面积核对、唯一性、空值、量纲、跨县相交之和 ≠ 完整 Phase 面积）
- CCD 缺省地区处理方式卡片没写清
- 你判断卡片的方法有误或不可行
- 需要在两种都合理的做法之间做科学选择

报告写在卡片「运行记录」节的 `BLOCKED / 异常` 和 `给 Claude Code 的问题`，然后停。

## 你可以自主决定的

代码实现方式、函数拆分、变量命名、日志格式、用哪个库函数达成卡片指定的算法、
`work/` 下中间文件的组织。

## 硬约束

- **源数据只读**（服务器上经 `source_links/` 符号链接引用）。脚本绝不写入或覆盖源目录。
- 审计类脚本必须只读，产物只写 `--output` 指定目录。
- 类别栅格（CLCD / CCD）重采样**只用最近邻**；面积统计在等面积 CRS 或逐像元真实面积下完成。
- 边界像元用面积权重或经验证的高倍超采样，不能只用像元中心法。
- 批量运行：在 `logs/` 记录参数、软件版本、起止时间、失败条目 ID；失败条目写
  `failure_registry.csv`，不得静默跳过。
- 可复现：运行记录里写清 git commit、环境锁文件 sha256、输入数据版本、参数。

## 运行环境

与主线共用服务器 conda 环境（根 `code/env/`，由
[../../docs/tasks/T-2026-09-03-server-env.md](../../docs/tasks/T-2026-09-03-server-env.md) 建立并锁定）。
GDAL / rasterio / geopandas / pyproj，无 Julia。纯标准库脚本（`preflight.py`、
`verify_ccd_archive.py`）不需要此环境。每次运行在运行记录里登记环境锁文件 sha256 与
GDAL/PROJ 版本。

## 出图（figures/）

一张图一个脚本 `figures/fig_<id>_<slug>.py`，CLI 驱动，复用 `figures/_style.py`；
同时导出矢量 PDF/SVG + 300 dpi PNG + 同名 `.yaml` sidecar（含 script / git_commit / run_id /
inputs+sha256 / params / generated）。图例与标题遵守术语边界。
