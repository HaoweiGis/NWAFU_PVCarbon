# PVCropCarbon

`PVCropCarbon` 是 `NWAFU_PVCarbon` 下的数据生产子项目，核心任务是把根目录
《数据清单.docx》定义的四类结果表转化为可重复、可审核的数据流水线。

## 范围边界

- 本子项目包含水稻、玉米、小麦种植退出与农业排放，范围大于主项目当前 V1；
- 不修改主项目 V1 的冻结技术路线，不把本子项目的中间结果自动视为主项目正式结果；
- `phase_id` 始终由完整 `Site + 建设年份` 生成；`phase_county_id` 仅用于完整 Phase
  与县界相交后的统计，不参与 Site/Phase 构造；
- “场址外新增耕地”在反事实识别通过前只能称为观测新增或空间关联，不能称为诱发/iLUC；
- 本地只保存代码、合同、清单和日志；原始大数据与生产结果保留在服务器。

## 目录

- `config/paths.server.env`：服务器路径配置；
- `metadata/output_fields.tsv`：四张结果表的规范字段合同；
- `metadata/required_extra_fields.tsv`：原清单缺失但为唯一识别和科学解释所必需的键；
- `metadata/source_status.tsv`：源数据现状与阻塞条件；
- `metadata/tasks.tsv`：生产阶段、依赖和验收标准；
- `scripts/preflight.py`：生产前只读检查；
- `scripts/run_pipeline.sh`：服务器统一入口，目前在阻塞项清零前只执行预检并停止；
- `work/`：服务器中间结果；
- `outputs/`：服务器正式输出，仅允许经校验后写入；
- `logs/`：服务器运行日志。

## 服务器位置

`/data/ssd/haoweimu/NWAFU_PVCarbon/PVCropCarbon`

共享源数据不复制，通过 `source_links/` 中的符号链接只读引用主项目和 HDD 数据集。

## 当前结论

项目骨架可运行，但完整生产尚未具备条件。Science Data Bank 官方 CCD V1（2001—2024）
正在服务器获取，可作为水稻、玉米、小麦及轮作类别的候选统一数据源；在 ZIP 完整性、
672 个 TIFF 清单、年份/区域覆盖、类别值域、NoData 和空间对齐验收完成前仍视为阻塞。
此外还缺少冻结的县界/行政代码、Site 阈值人工样本、土地变化人工样本、碳与农业排放
参数。预检必须对这些条件返回非零状态。

原清单的 `year` 是建设年，无法唯一标识环带逐年记录；正式生产还必须增加观测年、
环带、县域相交面积、责任县/转化发生县以及碳核算情景等键。具体见
`metadata/required_extra_fields.tsv`。
