# code/AGENTS.md

面向在 `code/` 下工作的 AI（主要是 Codex）。先读仓库根 [AGENTS.md](../AGENTS.md)。

> `PVCropCarbon/` 是既有的独立子流水线，**不受本文件管辖**，也不要把它的代码搬进 `code/`。
> 本目录只放 V1 主线（Patch→Site→Phase、稳定耕地暴露、环带、因果面板、iLUC 碳核算、
> 发电与抵消率）的代码。

## 你的职责

执行 `docs/experiment_design/E0X-<slug>.md` 的实验卡和 `docs/tasks/T-*.md` 的任务卡：
实现代码、运行、产物写入 `output/`、在同一卡片文件里填「运行记录」/「执行记录」节。

## 执行卡片的固定流程

1. `git pull`，读卡片全文 + 本文件 + 根 AGENTS.md。
2. 确认卡片「输入」里每个路径存在且规格匹配（CRS / 分辨率 / NoData / 单位）。
3. 实现或修改脚本。运行。产物落卡片「输出」指定路径。
4. 逐条核对卡片「验收门槛」，结果写进卡片的「运行记录」节。
5. 在 `output/manifests/experiment_registry.csv` 增加一行。
6. 卡片 status 改为 `done`（或 `blocked`），`commit` + `push`。

## 必须停止并报告 `BLOCKED:` 的情况（不要自行决定）

- 卡片未给出的参数值
- 输入路径不存在 / CRS / 分辨率 / 单位与卡片不符
- 任一验收门槛不通过
- 你判断卡片的方法有误或不可行
- 需要在两种都合理的做法之间做科学选择（如邻接阈值、稳定耕地口径、核算期）

报告写在卡片「运行记录」节的 `BLOCKED / 异常` 和 `给 Claude Code 的问题`，然后停。

## 你可以自主决定的

代码实现方式、函数拆分、变量命名、日志格式、用哪个库函数达成卡片指定的算法、
临时中间文件的组织（放 `output/**/_scratch/`，已 gitignore）。

## 硬约束

- **`input/` 只读**。脚本绝不写入或覆盖 `input/`，派生结果一律进 `output/`。
- 审计类脚本必须只读，产物只写 `--output` 指定目录。
- 原始数据只读，校验和记入 `00_project/manifests/` 或运行记录。
- 批量运行：在 `output/logs/` 记录参数、软件版本、起止时间、失败条目 ID；
  失败条目写 `failure_registry.csv`，不得静默跳过。
- 可复现：运行记录里写清 git commit、`code/env/` 环境哈希、输入数据版本、参数。
- 类别栅格（CLCD / CCD）重采样只用最近邻；面积统计在等面积 CRS 或逐像元真实面积下完成。

## 运行环境

计算端（`ssh -p 30383 server@8.130.68.96`，根 `/data/ssd/haoweimu/NWAFU_PVCarbon`）目前没有
GDAL / rasterio / geopandas / pyproj 环境；首个任务
[docs/tasks/T-2026-09-03-server-env.md](../docs/tasks/T-2026-09-03-server-env.md)
负责用 conda 建立并锁定（导出带精确版本的 lock，登记 sha256）。本项目不使用 Julia。
纯标准库的审计脚本不需要此环境。

- 环境隔离，不污染系统 Python，不写入 `input/`。
- `code/env/environment.yml`（conda）+ 精确版本 lock。
- 每次运行在运行记录里登记环境锁文件的 sha256。
- GDAL / PROJ 版本影响重投影结果，必须锁死并在每次运行记录里登记。

## 出图（figures/）

- 一张图一个脚本 `figures/fig_<id>_<slug>.py`，CLI 驱动（`--run <dir> --out <dir>`）。
- 复用 `figures/_style.py`（rcParams、配色、字号）。空间图公用件（投影、比例尺、图例）
  在第一张空间图时新建 `figures/_geo.py`。
- 每张图同时导出矢量（PDF/SVG）+ 300 dpi PNG，并写同名 `.yaml` sidecar：

  ```yaml
  script: code/figures/fig_E02_hotspots.py
  git_commit: <短哈希>
  run_id: <experiment_registry.csv 里的 run_id>
  inputs:
    - path: output/.../summary.csv
      sha256: <...>
  params: {cmap: cividis, dpi: 300}
  generated: 2026-01-01T00:00:00+08:00
  ```

- 确定性：固定随机种子，不依赖交互状态。
- `preview_*` 前缀的中间图已 gitignore。
- 图例与标题遵守根 AGENTS.md 的术语边界（区分 观测 / 因果归因 / 情景）。
