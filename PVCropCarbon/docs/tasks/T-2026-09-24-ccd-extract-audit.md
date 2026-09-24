# T-2026-09-24-ccd-extract-audit：CCD 解压与覆盖审计

status: ready
类型: 工程任务（非实验）
执行者: Claude Code 直接执行（用户 2026-09-24 授权）

## 目标

解压已验证的 CCD 官方 ZIP（`9df1ab40944b4ce58eec7265462b4247_V1.zip`，10,163,712,508 字节，
672 TIFF，28 省 × 24 年，`verify_ccd_archive.py` 已过），逐文件核对 CRS/值域/NoData，
核对实际覆盖的省级区域是否等于预期缺省清单（北京、青海、西藏、台湾、香港、澳门），
缺省地区编码 `coverage_missing`（不得填类别 0）。

## 交付物

- `D010_CCD_2001-2024/extracted/`（672 个 TIFF，只读解压产物）
- `D010_CCD_2001-2024/metadata/coverage_audit.{csv,json}`：province × year 存在性矩阵
- `D010_CCD_2001-2024/metadata/ccd_extract_report.md`

## 步骤

1. 解压 zip 到 `extracted/`（不改动 `raw/` 原始 zip）。
2. 断言文件数 = 672；逐文件读 CRS（预期 EPSG:4326）、像元大小（名义 30 m）、值域
   （预期 `{0,1,2,3,4,5,6,9}` 及已声明 NoData）。
3. 从文件名/目录名解析省级区域标识，列出实际覆盖的 28 个区域清单。
4. 与中国 34 个省级行政区全集比对，得到缺省清单；与用户此前给出的"北京、青海、西藏、台湾、
   香港、澳门"核对是否一致——**如实报告，不假设一致**。
5. 写 `coverage_missing` 标记规则说明（供后续 P05/P06 用：这些地区的 PV Phase 不能用 CCD 产出
   作物退出统计，需要 CLCD-only 降级口径或标记为不可评估）。

## 验收（可判定）

- [ ] 解压后 672 个 TIFF 全部可读
- [ ] CRS/像元大小/值域逐文件核对通过（或列出异常文件清单）
- [ ] 实际覆盖 28 省清单写入报告，与预期缺省清单对比结果如实记录
- [ ] `coverage_missing` 编码规则写清楚，`extracted/` 不覆盖 `raw/`

## 失败即停

- 解压后文件数 ≠ 672，或任一文件 CRS/值域与预期严重不符 → BLOCKED
- 磁盘空间不足（HDD 当前剩余约 5.3 TB，理论够用，若解压中报错立即停）→ BLOCKED

## 执行记录（Claude Code 直接执行）

起止：2026-09-24（脚本 `code/pipeline/extract_audit_ccd.py`，解压+审计约十几分钟）

### 结果

- 解压 672 个 TIFF 全部成功（`D010_CCD_2001-2024/extracted/`），**0 个不可读文件**。
- CRS、像元大小、NoData 集合均为单一值（逐文件核对通过）。
- 28 个顶层目录是**英文/拼音**命名（Anhui, Chongqing, … 非中文省名）——首轮自动模糊匹配脚本
  因此全部落空（bug，非真实覆盖问题），已手工建立拼音-中文映射表核对，见更正记录。
- **实际覆盖 28 省，缺失 6 省 = 北京、西藏、青海、台湾、香港、澳门 —— 与用户此前给出的预期
  缺省清单完全一致 ✓**。
- 发现目录名 `Shannxi`（陕西，非标准拼音）容易与 `Shanxi`（山西）混淆，写进已知问题，
  后续代码引用目录名时必须用映射表，不能靠拼音猜测。

### 产物

- `D010_CCD_2001-2024/extracted/`（672 TIFF）
- `D010_CCD_2001-2024/metadata/coverage_audit.{csv,json}`、`ccd_extract_report.md`（含更正记录）

### BLOCKED / 异常

无。`coverage_missing` 编码规则已写入报告：缺省 6 省的 PV Phase 在 P05/P06 不产出正式 CCD 作物
统计，编码 `coverage_missing`，不得填类别 0；需要为这些 Phase 设计 CLCD-only 降级口径（留给
P05 卡片决定）。
