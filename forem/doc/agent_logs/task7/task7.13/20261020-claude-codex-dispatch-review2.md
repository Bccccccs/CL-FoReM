# 2026-10-20 Claude：给Codex的派发提示——下层规格与回写的复核（第二轮）

- 任务ID：TASK7-LOWER-SPEC-REVIEW-20261020
- 作者：Claude（claude-opus-5-5，推理强度未知）；由用户派发，Claude不启动。
- 推荐：Codex GPT6.1sol，medium（跨文档一致性、奖励/时序/终止语义与代码口径核对）。实际模型/强度由执行方记录，无法核实写“未知”。

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7-LOWER-SPEC-REVIEW-20261020。推荐模型GPT6.1sol、推理强度medium；在日志里写明你实际的模型与强度，无法核实写“未知”。

【先读】根 AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；你上一轮的复核日志 forem/doc/agent_logs/task7/20261020-codex-lower-sac-review.md 与Claude的处理日志 forem/doc/agent_logs/task7/20261020-claude-lower-sac-review-fixes.md；Claude的规格日志 forem/doc/agent_logs/task7/task7.13/20261020-claude-lower-spec.md；forem/doc/SOURCES.md 的 SRC-0400–SRC-0408；forem/doc/DECISIONS.md 的 TASK7-LOWER-SAC-20261020、TASK7-DEFAULTS-20261020、TASK7-LOWER-SPEC-20261020。

【开工登记】在 forem/doc/PROGRESS.md“项目级记录”表加一行（写前重读，保留他人内容）：TASK7-LOWER-SPEC-REVIEW-20261020｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/task7.13/20261020-codex-lower-spec-review.md。

【背景】用户已按Claude推荐确定task7.13下层SAC规格D1–D12（SRC-0408）：下层10 Hz输出3维[u, ω, v]、单独训练后冻结；新增子目标奖励G；同步奖励沿CBL（乘u/0.3与放慢项）、G在乘法外，不同步去乘法加时间惩罚；同步上层奖励不加时间项；段超时按截断；到达容差0.10 m/0.35 rad；原地候选强制ω＝v＝0；段超时3·T_ideal＋2 s；策略/观测/渲染0.1 s、IK与碰撞0.05 s子步；上一动作无额外滞后；冻结门槛；经验池uint8；其余沿task5.5。Claude据此回写了多份文档（只改设计，未实施）。

【复核范围】forem/doc/tasks/task7/TASK.md（入口节、§2.7、§2.9、§3 U31–U39、§4、§5）；task7.13/RESULTS.md（“Claude复核”“下层规格v1”L.1–L.10与D表）；task7.4/RESULTS.md文首“2026-10-20两层SAC下的修订与标注”节及⑦/§14/§15标注；task7.5/RESULTS.md (B)开头B.R；task7.6/RESULTS.md §6R；task7.10/TASK.md状态行。检查：
1. 上一轮14项是否已按意见处理到位，有无处理后新引入的矛盾或遗漏。
2. 规格内部一致性：L.1子步流程与失败回退、Δt口径、SMDP折扣说明是否一致；L.3奖励公式中各项单位、符号、作用范围（乘法内外）、与CBL代码（SRC-0405）是否对得上；L.4段/回合与mask语义是否与task7.4“截断不当作终止”一致；L.5到达/原地/超时三类候选是否都有完成条件且推演与执行一致；L.7 f_k字段与task7.4接口/经验池（I4）是否一致。
3. 文档之间的一致性：父TASK U行、task7.4修订节、task7.5 B.R、task7.13 L节对同一事项（时序、到达、超时、奖励、阶段L、冻结门槛）的写法是否相同；仍把旧路径执行器写成主方案的残留。
4. 主张—来源：SRC-0407推导①②③的输入、公式、单位与条件是否正确（可直接核算）；SRC-0408是否只记录用户决定、没有把未定事项写成已定；把Claude建议写成用户决定或把工程选择写成证据的地方。
5. 是否有未经用户决定的语义改动（奖励、终止、动作、观测），或超出D1–D12的新增功能/实验。

【输出】只写自己的日志：按编号列出发现，每条含“位置（文件:行）—问题—建议改法—依据”，标严重程度（必须改/建议改/可选）；另列“已核对无问题”的要点。不直接修改任何task或共享文档（由Claude统一处理）；完成后PROGRESS本行改为done（交付复核意见）。

【禁止】不运行程序、容器、训练或评估；不修改代码、参考仓库和除PROGRESS本行及自己日志外的任何文件；不新增功能、实验或设计决定。
```
