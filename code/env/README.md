# 计算环境

计算端（`ssh NWAFU5090`）的可复现 conda 环境。由
[docs/tasks/T-2026-09-03-server-env.md](../../docs/tasks/T-2026-09-03-server-env.md)
建立并锁定（2026-09-08，Claude Code 直接执行）。**无 Julia。**

## 文件

| 文件 | 用途 |
|---|---|
| `environment.yml` | 精简定义（channel + 版本，无 build 号）——跨机重建用 |
| `environment.lock.yml` | 完整锁（`=version=build`）——精确复现用 |
| `environment.lock.sha256` | lock 文件 sha256，每次运行记录登记 |
| `pip_freeze.txt` | pip 侧完整清单（`pyfixest` 及其依赖走 pip） |
| `versions.txt` | 构建时的版本快照原始输出 |

## 关键版本（写进每个 P0X 运行记录的"环境"行）

- python 3.11.16 · **GDAL 3.12.3** · **PROJ 9.7.1** · **GEOS 3.14.1**
- rasterio 1.4.4 · geopandas 1.1.4 · pyogrio 0.12.1 · fiona 1.10.1 · pyproj 3.7.2 · shapely 2.1.2
- numpy 2.4.6 · pandas 3.0.5 · scipy 1.17.1 · pyarrow 25.0.0
- exactextract 0.3.0 · statsmodels 0.15.0 · linearmodels 7.0 · pyfixest 0.60.0
- ⚠ pandas 3.x / numpy 2.x：copy-on-write 默认开，注意链式赋值与 `pd.NA` 语义。

## 约定

- 环境隔离，不污染系统 Python，不写入 `input/` / 源数据目录。
- 每次运行在运行记录里登记 `environment.lock.sha256` 与 GDAL/PROJ/GEOS 版本。
- 类别栅格重采样只用最近邻；重投影结果对 GDAL/PROJ 版本敏感，锁死。
- 纯标准库审计脚本不需要此环境。

## 激活（服务器）

```bash
source /home/server/miniconda3/etc/profile.d/conda.sh
conda activate pvcarbon          # = /home/server/Python_env/pvcarbon
```

## 从锁重建（换机 / 灾备）

```bash
conda env create -n pvcarbon -f code/env/environment.lock.yml
conda activate pvcarbon
pip install -r <(grep -A99 '^# pip' code/env/pip_freeze.txt)   # 若 lock 的 pip 段未自动装
```
