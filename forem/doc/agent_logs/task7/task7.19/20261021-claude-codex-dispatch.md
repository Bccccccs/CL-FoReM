# 2026-10-21 Claude：task7.19 G7实现 Codex派发提示

- 作者：Claude（claude-opus-5-5，推理强度未知）；由用户派发，Claude不启动。
- **派发前提**：task7.15（候选生成器）与task7.17（回合环境）已由Claude复核done。可与task7.18阶段L训练并行（本任务用GPU3）。本提示只覆盖实现与测试，不含D10验收运行（D10需task7.18检查点，预算按本阶段计时另写）。
- 推荐：Codex GPT6.1sol，medium。

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.19-G7-IMPL-20261021（G7规则路径执行器与D10配对验收工具实现）。推荐GPT6.1sol / medium；日志写明实际模型与强度，无法核实写“未知”。

【授权】用户已授权（forem/doc/SOURCES.md SRC-0431；设计SRC-0434）。授权边界、预算、GPU与文件归属以 forem/doc/tasks/task7/task7.19/TASK.md 为准；超出即停下报告。不训练、不运行D10正式验收、不启停或重建容器、不改阶段一代码与参考仓库（husky/、nmoma/、scwm/、mobile-rl/、archive/、mapgen/）、不提交git。

【并行】task7.18可能同时由别的Codex会话执行（训练，占用其他GPU）。只改TASK“文件归属”列出的文件；其他task7_sim模块只读调用。快照/恢复若须改env.py或core.py，只做加法式接口、不改既有语义，并保证既有测试全部通过；若需要改动超出这一点，停下报告。PROGRESS只改自己那一行、写前重读、定点编辑。SOURCES新条目只用SRC-0480–0489，写前重读。

【先读】根AGENTS.md（“功能范围硬性约束”“论据与引用来源”“性能优化共同要求”）；forem/AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；forem/ENV.md；task7.19三文档（RESULTS中“G7-1–G7-4设计”节为本任务规格）；task7.5 RESULTS的B.9、B.10、B.11、B.14与B.R；task7.4 RESULTS“2026-10-20 合同缺口决定”（⑦⑧⑨）；task7.13 RESULTS的L.0、D5、D7、L.9；task7.14、7.15、7.17的RESULTS（内核、候选生成器、回合环境现状与复核意见）。

【开工】PROGRESS“项目级记录”加一行：TASK7.19-G7-IMPL-20261021｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/task7.19/20261021-codex-g7-impl.md，先写开工核查（task7.15、7.17是否done、GPU3是否空闲、既有测试数）。长任务写PID与停止方式，后台Python用python3 -u。

【要做的事】
1. g7.py：G7-1路径族（7条底盘路径、不同步两种末端推进、同步恒速0.1 m/s、原地候选1条、退化路径掩码、段时长取整到0.05 s整数倍）；按B.9逐子步评估（LocalCollision、同一IK合同N1、间隙、残差、f_k字段与⑨的不可行前段规则）；G7-2分层排序；G7-3执行器（每0.5 s对同一世界系c*重规划、TruthCollision判失败、超时用T_seg、到达按⑦）。评估为纯函数，不改环境状态与随机数流。
2. d10_eval.py：G7-4配对验收工具（快照→下层策略执行→恢复→G7执行→沿策略结果继续；分母、到达/失败/超时归类、Wilson区间与按回合bootstrap、分档/分扇区/原地分项）。策略用可调用对象传入；测试用脚本策略，不加载训练检查点。
3. 测试：TASK“交付与验收”所列各项；快照恢复后逐元素一致；配对两次执行起点相同；GPU float32与CPU float64对照；既有测试不回退。
4. 有界计时：每候选N条评估、一次重规划、一次完整G7决策执行的E扩展计时（只记录，不设门槛），并据此推算D10一次完整验收（两变体、每变体≥1000对）的墙钟，写入RESULTS供下一次派发定预算。

【遇到规格问题】不发起文档复核轮次。歧义、冲突或缺数值时只停该部分，日志“待决定”列出位置、冲突与可选理解，其余继续；不自行补阈值、新语义或新功能。

【硬约束】评估端不得访问真值几何（信息边界测试）；“被评分即执行”逐子步一致；不为提速改变步长、子步、观测、奖励、终止或评分语义。

【输出】RESULTS按run-id追加：改动文件、每项测试命令/退出码/日志/结果、计时与D10墙钟推算、未通过项、已知限制、待决定问题。完成后PROGRESS本行改为review交Claude复核；做不完或预算用尽如实交接，不标完成。
```
