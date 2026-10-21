# 2026-10-20 Claude：给Codex的派发提示——task7规格冻结前的整体复核（第三轮）

- 任务ID：TASK7-SPEC-FREEZE-REVIEW-20261020
- 作者：Claude（claude-opus-5-5，推理强度未知）；由用户派发，Claude不启动。
- 推荐：Codex GPT6.1sol，medium（跨文档一致性、与三个原项目源码的对应、奖励/时序/终止语义）。实际模型/强度由执行方记录。

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7-SPEC-FREEZE-REVIEW-20261020。推荐模型GPT6.1sol、推理强度medium；在日志里写明你实际的模型与强度，无法核实写“未知”。

【先读】根 AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；你上一轮复核日志 forem/doc/agent_logs/task7/task7.13/20261020-codex-lower-spec-review.md 与Claude处理日志 forem/doc/agent_logs/task7/task7.13/20261020-claude-lower-spec-review-fixes.md；forem/doc/SOURCES.md 的 SRC-0407–SRC-0417；forem/doc/DECISIONS.md 中 2026-10-20 的各条（TASK7-LOWER-SPEC、TASK7-FAITHFUL、TASK7-UPPER-SPEC、TASK7-FP-SPEC、TASK7-NUMBERS）。

【开工登记】在 forem/doc/PROGRESS.md“项目级记录”表加一行（写前重读，保留他人内容）：TASK7-SPEC-FREEZE-REVIEW-20261020｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/20261020-codex-spec-freeze-review.md。

【背景】用户要求设计“忠于三个原项目”：CBL的Husky+UR5项目（task5.5所用自写SAC链路）、N²M²、SC²-WM。今天已由用户确定：task7.13下层规格D1–D20（含按原则改取CBL做法的D17/D18/D19）、一致性表#5改回CBL时序、task7.10上层T1–T9（候选间Transformer、两套头A/B）、task7.11 f_p F1–F9（预测到达后观测编码、1−cos、测试期适应更新f_p＋候选编码器、KL中位数触发）、剩余数值与预算N1–N12（IK改为沿CBL近似解语义等）。Claude据此回写了多份文档（只改设计，未实施）。设计即将冻结，之后请用户授权环境核心实施。

【复核范围】forem/doc/tasks/task7/TASK.md（两层SAC入口、“与三个原项目的一致性”表、§2.2、§2.7、§2.9、§3 U行、§4、§5）；task7.4/RESULTS.md文首“数值与预算”节与“两层SAC下的修订与标注”节；task7.5/RESULTS.md B.R；task7.7、task7.8 RESULTS已定项；task7.10/RESULTS.md；task7.11/RESULTS.md；task7.13/RESULTS.md（L.1–L.10、D表、接口补充D13–D20）。检查：
1. 上一轮14项是否已按意见处理到位，处理后有无新矛盾。
2. 一致性表：每一行“原项目做法”是否与源码/原文一致（直接打开 forem/src/modulation_rl、forem/scripts、scwm/ 中对应文件核对，N²M²引用已有来源）；标“一致”的是否真的一致；有无漏列的重要偏离（例如CBL的ikslack近似解语义、奖励各项、观测字段、SAC超参；SC²-WM的两头、世界模型输入、适应范围与触发）。
3. 规格之间的接口：f_k字段（D20）、候选编码输入（T1/U27）、f_p输入（T8）、经验池（I4）、阶段与冻结范围（L→1→2→3、适应期）、奖励与折扣（D1–D3、D18–D19、N3、N7）、时序与结束判定（D8、D13–D16）在各文档的写法是否一致、能否直接据此实现。
4. N1 IK语义：与CBL代码（robot_env.cpp findIk/BioIK近似解、ikslack判据）的对应是否准确；与B11失败合同、D8子步、推演/执行一致性有无冲突；DLS细节缺什么才能实现。
5. 主张—来源：SRC-0412、0414、0416的代码行号与推导是否属实；有无把Claude解释写成用户原话、把工程选择写成证据、把未定写成已定。
6. 是否有未经用户决定的语义改动或新增功能/实验。

【输出】只写自己的日志：按编号列出发现，每条含“位置（文件:行）—问题—建议改法—依据”，标严重程度（必须改/建议改/可选）；另列“已核对无问题”的要点，并单列“实现前必须补的接口缺口”（如有）。不直接修改任何task或共享文档（由Claude统一处理）；完成后PROGRESS本行改为done（交付复核意见）。

【禁止】不运行程序、容器、训练或评估；不修改代码、参考仓库和除PROGRESS本行及自己日志外的任何文件；不新增功能、实验或设计决定。
```
