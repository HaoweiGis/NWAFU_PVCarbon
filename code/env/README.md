# 计算环境

计算端的可复现环境。由 Codex 通过 `docs/tasks/` 的环境卡建立并锁定。

## 计划内容

| 文件 | 用途 |
|---|---|
| `environment.yml` | conda 环境（导出带精确版本的 lock） |
| `julia/Project.toml` + `julia/Manifest.toml` | 如用到 Julia（Omniscape.jl 等），锁版本 |

## 约定

- 环境隔离，不污染系统 Python，不写入 `input/`。
- 每次运行在运行记录里登记锁文件的 sha256。
- GDAL/PROJ 版本影响重投影结果，必须锁死并在每次运行记录里登记。
- 纯标准库脚本不需要此环境。

## 激活（待任务完成后补全）

```bash
# conda env create -f code/env/environment.yml
# conda activate <env-name>
```
