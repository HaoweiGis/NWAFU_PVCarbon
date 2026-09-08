# T-2026-09-03-server-env：建立并锁定计算端 Python/GIS 环境

status: done            <!-- draft | ready | running | done | blocked -->
类型: 工程任务（非实验）
执行者: Claude Code 直接执行（用户 2026-09-03 授权），非 Codex

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

## 执行记录（Claude Code 直接执行）

执行者: Claude Code  ·  起止: 2026-09-08 09:46–09:48 (+08)  ·  构建脚本:
`/data/ssd/haoweimu/NWAFU_PVCarbon/00_admin/env_build/build_pvcarbon_env.sh`
（日志同目录 `build_20260908T094640.log`）

### 环境

- 位置: `/home/server/Python_env/pvcarbon`（conda env，名 `pvcarbon`；envs_dir 由 `~/.condarc` 指定）
- 大小 ~2.3 GB；单次 solve 安装（`conda create --override-channels -c conda-forge`，
  conda 26.5.3 内置 libmamba 求解，未装独立 mamba）
- 环境局部设 `channel_priority strict` + append `conda-forge`
- `pyfixest` 走 pip（conda-forge 无稳定包），其余全部 conda-forge

### 关键版本（每次运行记录须登记）

| 组件 | 版本 |
|---|---|
| python | 3.11.16 |
| GDAL | 3.12.3 "Chicoutimi" (2026/03/17)；`rasterio.__gdal_version__` = 3.12.3 |
| PROJ | 9.7.1 |
| GEOS | 3.14.1（shapely 2.1.2） |
| rasterio | 1.4.4 |
| geopandas | 1.1.4 ·  pyogrio 0.12.1 ·  fiona 1.10.1 ·  pyproj 3.7.2 |
| numpy 2.4.6 · pandas 3.0.5 · scipy 1.17.1 · pyarrow 25.0.0 | |
| exactextract | 0.3.0 (conda-forge) |
| statsmodels 0.15.0 · linearmodels 7.0 (conda-forge) · pyfixest 0.60.0 (pip) | |
| matplotlib | 3.11.1 |

> 注意 pandas 3.x / numpy 2.x —— 写 code/ 时留意 API（copy-on-write 默认开、`pd.NA` 语义）。

### 交付物（已放 `code/env/`，commit 一并提交）

| 文件 | SHA256 / 说明 |
|---|---|
| `code/env/environment.yml` | 精简（无 build 号），347 → conda 部分 + pip 段 |
| `code/env/environment.lock.yml` | 完整含 build 号 |
| `code/env/environment.lock.sha256` | `739e1c84dcccbf85b09542eda44b0d40b35b56905d0b71e967e599cadc0aeeda` |
| `code/env/pip_freeze.txt` | pip 侧完整清单 |
| `code/env/versions.txt` | 上表原始输出 |

### 验收结果

- [x] `import rasterio, geopandas, pyproj, shapely, fiona, pyogrio, exactextract, statsmodels, pyfixest, linearmodels` 全部成功
- [x] `environment.lock.yml` 每包带 `=version=build`
- [x] `environment.lock.sha256` 与本地 `sha256sum` 一致（`739e1c84…eeda`）
- [x] 冒烟 CLCD：CRS = `+proj=aea +lat_1=25 +lat_2=47 +lat_0=0 +lon_0=105 +x_0=0 +y_0=0 +datum=WGS84`，
      尺寸 **161378×135079**，transform 原点 (-2629624.7830, 5924251.5597)，pixel 30，**nodata = 0.0**
- [x] 冒烟 PV shp：**30023** 面，EPSG:4326，geom = 29896 Polygon + **127 MultiPolygon**，
      字段 `OBJECTID/PV_Area/Inst_time/Inst_year/Major_type/Lat/Lon`，重投影 Albers 后 Σ面积（未 union）3712.0 km²
- [x] `gdalinfo --version` = GDAL 3.12.3；`rasterio.__gdal_version__` = 3.12.3

### 给后续卡片的输入（P01 起用）

1. **激活**：`source /home/server/miniconda3/etc/profile.d/conda.sh && conda activate pvcarbon`
2. CLCD **nodata = 0**，故 CLCD 类别 0 = 无数据/背景（不是有效地类）——P01 网格审计据此核对值域。
3. PV 有 **127 个 MultiPolygon**——P01 记 `n_parts`，P02 距离判定按部件展开。
4. GDAL/PROJ/GEOS 版本见上表，写进每个 P0X 运行记录的"环境"行。

### BLOCKED / 异常

无。（`projinfo EPSG:4326` 的 PROJ.4 串输出为空，非阻塞——pyproj 报 PROJ 9.7.1 正常。）

### 给 Claude Code 的问题

无。P01 可起。
