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

1. `ssh NWAFU5090`。conda 在 `/home/server/miniconda3`（含 mamba）；自定义 envs 目录
   `/home/server/Python_env/`（已有 `haoweimu` `miaomu` `sam3` `wtdd_Solver`，均无地理栈）。
   `source /home/server/miniconda3/etc/profile.d/conda.sh`。
2. 新建环境 `/home/server/Python_env/pvcarbon`（`conda create -p ... python=3.11`），
   与现有 envs 同一约定。
3. 安装（conda-forge channel，用 mamba）：`gdal rasterio geopandas pyproj shapely fiona
   rtree pyogrio exactextract numpy pandas scipy pyarrow matplotlib pyyaml tqdm`；
   因果估计所需的 `statsmodels linearmodels pyfixest` 也一并装上。
4. 记录 `gdalinfo --version`、`projinfo EPSG:4326 | head`、
   `python -c "import rasterio; print(rasterio.__gdal_version__, rasterio.__version__)"`、
   `python -c "import geopandas, pyogrio; print(geopandas.__version__)"`。
5. `conda env export -p /home/server/Python_env/pvcarbon --no-builds > code/env/environment.yml`（精简）；
   `conda env export -p /home/server/Python_env/pvcarbon > code/env/environment.lock.yml`（完整含 build）。
6. 计算 lock 的 sha256 写入 `code/env/environment.lock.sha256`。
7. 冒烟测试：
   - `rasterio` 读 `/data/hdd/haoweimu/datasets/D001_CLCD_2000-2025/raw/CLCD_v01_2015_albert.tif`
     打印 CRS(应为 aea 25/47/105 WGS84) / transform / 尺寸(161378×135079) / nodata / 值域。
   - `geopandas` 读
     `/data/ssd/haoweimu/NWAFU_PVCarbon/01_pv/pv_power_plants_china_2010_2022/raw/PV power plants of China from 2010 to 2022/*.shp`
     打印要素数(应 30023) / CRS(WGS84) / geom_type；`to_crs` 到 CLCD Albers 后打印总面积 km²。
   - `exactextract` 对一小块 CLCD 做一次面积权重分区统计，确认可用。
8. `git add code/env/`，`commit -m "env: 建立并锁定计算端 pvcarbon 环境"`，`push`。

## 验收（可判定）

- [ ] `conda activate /home/server/Python_env/pvcarbon` 后 `python -c "import rasterio, geopandas, pyproj, shapely, fiona, pyogrio, exactextract, statsmodels, pyfixest"` 全部成功
- [ ] `code/env/environment.lock.yml` 存在且每个包都带精确版本（`=x.y.z=build`）
- [ ] `code/env/environment.lock.sha256` 与 lock 文件实际 sha256 一致
- [ ] 冒烟测试：CLCD 读出 CRS = Albers(25/47/105, WGS84)、尺寸 161378×135079；PV shp 读出 30023 面
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
