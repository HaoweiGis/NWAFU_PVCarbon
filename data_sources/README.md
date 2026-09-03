# 本地数据来源

- `pv_inventory/raw/`：中国2010–2022年光伏电站原始压缩包；
- `boundaries/raw/`：省市县边界候选原始压缩包。
- `boundaries/extracted/省市县/`：候选边界解压结果；结构审计见 `../00_project/manifests/boundary_audit_20260831.json`。

原始文件不覆盖、不改名；解压结果与处理结果应分别放入同主题的 `extracted/` 和 `processed/` 子目录。
