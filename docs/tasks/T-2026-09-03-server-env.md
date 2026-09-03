# T-2026-09-03-server-env：建立并锁定计算端 Python/GIS 环境

status: draft            <!-- draft | ready | running | done | blocked -->
类型: 工程任务（非实验）

一个任务一个文件。Claude Code 起草 → 用户批准 → Codex 执行并在下方「执行记录」填写。

---

## 目标

在计算服务器上建立一个隔离、可复现的 conda 环境，供 V1 主线的栅格 / 矢量处理与因果分析
使用，并把精确版本锁死。此任务完成前，所有需要 GDAL / rasterio / geopandas 的实验卡都
阻塞。

## 交付物

- `code/env/environment.yml` —— conda 环境定义（带 channel、不带精确版本）
- `code/env/environment.lock.yml` —— `conda env export` 的完整精确版本锁（含 build 号）
- `code/env/environment.lock.sha256` —— lock 文件的 sha256（单行）
- `code/env/README.md` 的「激活」节补全为实际命令与环境名
- 本文件「执行记录」节填写

## 步骤

1. `ssh -p 30383 server@8.130.68.96`，在 `/data/ssd/haoweimu/NWAFU_PVCarbon` 下操作。
2. 用 miniconda / mamba 新建环境（建议名 `pvcarbon`），Python 3.11。
3. 安装（conda-forge channel）：`gdal rasterio geopandas pyproj shapely fiona rtree
   numpy pandas scipy pyogrio matplotlib pyyaml`；因果估计所需的
   `linearmodels statsmodels`（事件研究 / 面板）也一并装上。
4. 记录 `gdalinfo --version`、`proj` 版本、`python -c "import rasterio; print(rasterio.__gdal_version__)"`。
5. `conda env export --no-builds > code/env/environment.yml` 的手写精简版；
   `conda env export > code/env/environment.lock.yml` 的完整版。
6. 计算 lock 的 sha256 写入 `code/env/environment.lock.sha256`。
7. 冒烟测试：读一景 CLCD GeoTIFF（`/data/hdd/haoweimu/datasets/D001_CLCD_2000-2025` 下任一年）
   打印 CRS / transform / 值域；用 geopandas 读候选县界 shp 打印要素数与 CRS。
8. `git add code/env/ docs/tasks/T-2026-09-03-server-env.md`，`commit -m "env: 建立并锁定计算端 pvcarbon 环境"`，`push`。

## 验收（可判定）

- [ ] `conda activate pvcarbon` 后 `python -c "import gdal_or_osgeo, rasterio, geopandas, pyproj, statsmodels"` 全部成功
- [ ] `code/env/environment.lock.yml` 存在且每个包都带精确版本（`=x.y.z=build`）
- [ ] `code/env/environment.lock.sha256` 与 lock 文件实际 sha256 一致
- [ ] 冒烟测试：CLCD GeoTIFF 成功读出 CRS 与 transform；县界 shp 读出要素数（省/市/县 ≈ 34/375/2891）
- [ ] `gdalinfo --version` 与 `rasterio.__gdal_version__` 记入执行记录

## 失败即停（写 BLOCKED，不要自行决定）

- 服务器无法安装 conda / 无网络 / 无写权限
- GDAL 与 rasterio 版本不匹配且无法在 conda-forge 内解决
- CLCD 或县界路径与根 AGENTS.md 记录不符

## 备注

Codex 不读聊天记录。上下文：本项目本地在 Windows，只做讨论与出图；服务器做全部计算。
不使用 Julia。环境隔离，不污染系统 Python，不写入 `input/`。GDAL/PROJ 版本会影响重投影
结果，必须锁死并在每次运行记录里登记。

---

## 执行记录（Codex）

commit: `<短哈希>`  ·  起止: `<…>`

- 装了什么 / 改了什么（含精确版本、SHA256）
- 验收结果逐条
- BLOCKED / 异常
- 给 Claude Code 的问题
