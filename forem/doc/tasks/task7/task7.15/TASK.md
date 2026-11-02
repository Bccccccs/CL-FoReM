# task7.15 — 规则候选生成器实施

状态：**done（2026-10-21 Claude复核r2通过，见[RESULTS](RESULTS.md)末节）。原：draft（2026-10-21建立；实施已授权；可立即派发，与task7.16、7.17并行）**。父任务：[task7](../TASK.md)；授权[SRC-0431](../../../SOURCES.md#src-0431)。

## 目标

按[task7.9 RESULTS](../task7.9/RESULTS.md)规则版规格（A.1–A.8）与R1–R8（[SRC-0401](../../../SOURCES.md#src-0401)）实现候选前瞻点生成器，供阶段L子目标抽样（L.4）、推演与上层选点使用。不实现生成网络（task7.9 (B)）。

## 范围

- 包含：12扇区候选与走廊检查（A.2）、不同步s_k（A.3，复用`search.py`同一规则：Δs_r＝0.05 m、IK存在性、第一段连续可达）、原地候选（A.4）、排列/掩码/K≤13（A.5）、诊断量（A.6，只进info）、A.8单元测试；GPU批量实现与CPU float64对照；有界计时。
- 信息边界：只读局部栅格（累积扫描）、本体状态、路线与变体；不读真值地图（A.1）。
- 不包含：网络、训练、回合环境封装、G7。

## 文件归属（只改这些）

`forem/src/task7_sim/candidates.py`、`forem/src/task7_sim/tests/test_candidates.py`、必要时`forem/config/task7/candidates.json`。`search.py`、`core.py`等只读调用；若R4搜索须扩展接口，停下报告。

## 交付与验收

- A.8所列测试全部通过或如实记录未通过项；“只改被遮挡真值盒子时候选输出不变”的信息边界测试；GPU float32与CPU float64对照；E×K批量吞吐与延迟分布（只记录，不设门槛）。
- 运行：forem-dev内，单条命令≤10分钟、累计容器计算≤60分钟、只用GPU1（`CUDA_VISIBLE_DEVICES=1`）；不训练、不启停容器、不提交git。
- SOURCES预留编号：SRC-0440–0449。

## 模型推荐

|Agent|模型|推理强度|理由|
|---|---|---|---|
|Codex|GPT6.1sol|medium|规则几何与IK搜索需逐条对照规格|
|Claude|Sonnet5.5|medium|同上（复核）|

推荐不等于实际配置；执行方在日志中记录实际模型与强度，无法核实写“未知”。

文档作者：Claude（claude-opus-5-5，推理强度未知），2026-10-21。
