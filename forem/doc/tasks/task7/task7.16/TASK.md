# task7.16 — A类程序化长方体地图生成器与地图池

状态：**draft（2026-10-21建立；实施已授权；可立即派发，与task7.15、7.17并行）**。父任务：[task7](../TASK.md)；授权[SRC-0431](../../../SOURCES.md#src-0431)。

## 目标

在forem内实现A类程序化随机长方体地图生成器（纯numpy、带种子、纯函数，不调用LLM/API），并生成训练池与固定验证/测试集。2026-10-21用户决定写成forem模块、mapgen不动（[SRC-0431](../../../SOURCES.md#src-0431)）。

## 规格（依据，不在此另写一套）

- [mapgen需求文档](../../../../../mapgen/docs/husky_ur5_map_requirements.md) §3共同规格（10×10 m、角点＋theta坐标约定、墙写入JSON 0.15 m×1.6 m、不裁剪、尺寸下限、不重叠、元数据）、§4 A类参数与稀疏/标准两档、§5自动检验与合格条件、§7输出结构、§10验收第1–3条。其中“mapgen仓库commit”元数据改记forem生成器版本（源文件SHA256＋根HEAD）。
- 数量：验证集每档50张、测试集每档100张（[SRC-0364](../../../SOURCES.md#src-0364)）；**训练池每档约5000张**（[SRC-0431](../../../SOURCES.md#src-0431)）。训练/验证/测试种子范围互不重叠，写入index.json。
- 读取兼容：输出JSON必须能被`task7_sim.geometry`现有读取器原样读入（task7.5 A.8格式）；增加一条往返测试。
- 可复制mapgen `mapgen/map_builder.py`中需要的几何函数（SAT、PCD导出），注明来源（mapgen git `765e064`）；不修改mapgen。

## 文件归属（只改这些）

`forem/src/task7_sim/mapgen_a.py`、`forem/src/task7_sim/tests/test_mapgen_a.py`、`forem/config/task7/mapgen_a.json`；地图产物`forem/results/task7/maps/a/<UTC时间戳>/`（不入git），日志`forem/logs/task7/t7.16-<run-id>/`。

## 交付与验收

- §10第1条单元测试（同种子逐位复现、角点旋转、越界/重叠拒绝、原点净空、墙写入JSON）与读取器往返测试通过；§5检验报告齐全；随机抽10张俯视图与JSON一致性（Claude复核时人工核对）。
- 合格率、拒绝原因分布、两档的连通性/通道净空/掉头空间/高度分层统计；若某档合格率过低或检验条件互相冲突，报告并停下该档，不自行放宽合格条件。
- 运行：forem-dev内（宿主缺numpy）；纯CPU，不用GPU；并行进程数≤16；生成批次可后台运行，单条命令≤30分钟、累计≤120分钟；不训练、不启停容器、不提交git。
- SOURCES预留编号：SRC-0450–0459。

## 模型推荐

|Agent|模型|推理强度|理由|
|---|---|---|---|
|Codex|GPT6.1sol|medium|几何检验与种子/复现性需仔细核对；生成本身是常规执行|
|Claude|Sonnet5.5|medium|同上（复核）|

推荐不等于实际配置；执行方在日志中记录实际模型与强度，无法核实写“未知”。

文档作者：Claude（claude-opus-5-5，推理强度未知），2026-10-21。
