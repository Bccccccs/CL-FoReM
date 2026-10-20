# Task6 重新开始：派发提示词（Claude编写，用户派发给Codex）

两个子任务各开一个Codex会话。推荐配置：**gpt-6.1-sol（GPT6.1sol），推理强度medium**；长训监控子Agent用gpt-6.1-sol/low。只有某实现环节已记录至少两种不同思路都失败且原因不明时，才改用gpt-6-astra/high，并在日志写明理由。

如果原task6的Codex会话还开着，请先告诉它：“task6已重新开始并拆分为task6.1/task6.2，原流程作废，停止原task6的工作，不要应用任何未完成的改动”，然后用提示词一开新会话（或在原会话中继续，但须先重读文档）。

---

## 提示词一：task6.1（ScwmSAC sim组）

```text
你是Codex，负责执行FoReM项目的task6.1：Task4.8训练器在sim中的基线F0与F1–F6训练参数对照。决策者和流程制定者是Claude，你按流程执行，不自行改动口径。工作目录：/home/ybc/projects/CL-FoReM。

背景：task6已于2026-10-12重新开始，原task6与task7合并为一个对照组，拆成task6.1（本任务）和task6.2（另一个Codex会话负责）。原task6的流程和run-id作废；原预检证据（results/task6/baseline_source_diff.json、t6-preflight-r1、t6-d12-preflight-r1）只作参考，须重新核查。

开工前必须阅读：
1. 根 AGENTS.md（全部规则，尤其：功能范围硬性约束、SOURCES登记、递归三文档、日志与PROGRESS登记、性能优化共同要求）
2. forem/doc/PROGRESS.md 末尾“task6 重新开始”段
3. forem/doc/tasks/task6/TASK.md、PROCEDURE.md（父任务：对照结构、资源与优先级）
4. forem/doc/tasks/task6/task6.1/TASK.md、PROCEDURE.md、RESULTS.md
5. forem/doc/SOURCES.md 的 SRC-0222 至 SRC-0226、SRC-0228、SRC-0229

任务：按task6.1 PROCEDURE §1→§10执行。
- §1基线冻结 → §2 sim模式与D12两处改动及回归 → §3场景等价性门槛 → §4 D14对照开关（缺省必须与当前代码逐位等价，有单元测试）→ §5冒烟、profile与并行方案。
- §5必须实测：分阶段耗时（F0与F1两种更新负载）、每条run的CPU/GPU/内存、同GPU打包1/2/3条的吞吐、线程数影响、落盘开销；可选优化只有同输入实测有收益才启用。禁止改变步长/动作时长/观测/奖励/终止/更新语义，禁止TF32/AMP等改变数值的设置。
- §6先启动F0三种子×100万步（t6.1-sim-plain-s{0,1,2}），再按剩余容量启动F1–F6筛选（t6.1-scr-F{1..6}-s0，各30万步）。资源优先级按父PROCEDURE：F0 > task6.2正式训练 > 筛选。
- F0任一种子到15万、30万步时，立即把D15评估结果写入task6.1 RESULTS并在PROGRESS记一条，训练不停。
- 筛选全部完成后写t6.1-summary/screening.json和筛选表，停下等Claude的§7门槛；F0继续跑。

硬性约束：
- 不得触碰 forem-t5-pr2、forem-t5-husky（task5）和 forem-t6-husky-gz（task6.2）的容器与进程；只能停止自己启动的进程。
- CPU合计持续不超过56核，只告警不停训练；启动前读取task6.2的RESULTS/监控，按父PROCEDURE“资源与优先级”协调。
- 不修改 husky/、mobile-rl/；源码只允许sim相关内容和D14开关。
- run-id一律以t6.1-开头，不覆盖原t6-前缀证据。
- 遇到PROCEDURE“异常处理”所列情况：停下，写入RESULTS和日志，交给Claude。

记录要求：
- 在PROGRESS登记task6.1负责人（Codex）、状态和开始时间。日志写在 forem/doc/agent_logs/task6/task6.1/YYYYMMDD-codex-task6.1.md，写明实际使用的模型和推理强度。
- 只更新task6.1自己的RESULTS和日志，不修改父task6或task6.2的文档。
- 按PROCEDURE逐节填写RESULTS：实际命令、sha256、退出码、日志与产物路径、失败记录。计划内容不得写成结果。
- 长任务写明容器、PID、日志、监控方式和停止方法；持续工作期间至少每30分钟更新一次日志。新的实测论据登记SOURCES。
- 如果挂子Agent：先建子节点三文档（如task6.1.1）并登记；子Agent自报完成不能直接当作通过。

完成标准：F0与确认训练达到100万步（或如实记录失败），筛选表、两侧最终评估齐全，manifest已写，RESULTS状态改为review。不要自行标done。
```

---

## 提示词二：task6.2（RLlib Gazebo组，原task7）

```text
你是Codex，负责执行FoReM项目的task6.2：把Task5 B（Husky原版RLlib配方）原样改在Gazebo中训练。决策者和流程制定者是Claude，你按流程执行，不自行改动口径。工作目录：/home/ybc/projects/CL-FoReM。

背景：task6已于2026-10-12重新开始，原task6与task7合并为一个对照组，拆成task6.1（另一个Codex会话负责）和task6.2（本任务，即原task7）。task7编号已取消。

开工前必须阅读：
1. 根 AGENTS.md（全部规则，尤其：功能范围硬性约束、SOURCES登记、递归三文档、日志与PROGRESS登记、性能优化共同要求）
2. forem/doc/PROGRESS.md 中的task5段和末尾“task6 重新开始”段
3. forem/doc/tasks/task6/TASK.md、PROCEDURE.md（父任务：对照结构、资源与优先级）
4. forem/doc/tasks/task6/task6.2/TASK.md、PROCEDURE.md、RESULTS.md
5. forem/doc/tasks/task5/task5.2/RESULTS.md、task5.3/RESULTS.md（B的命令、生效配置和已批准偏差）
6. forem/doc/tasks/task4/task4.8/task4.8.1/RESULTS.md（多实例隔离做法）
7. forem/doc/SOURCES.md 的 SRC-0227、SRC-0229

任务：按task6.2 PROCEDURE §1→§7执行。
- §1–§4（基线冻结、新容器forem-t6-husky-gz与工作区副本forem/build/task6.2、单实例Gazebo就绪、多实例隔离与回归、冒烟/profile/确定N）可以现在开始。
- §5正式训练须在task5的A/B训练进程退出后才能启动（除非Claude明确放行并行）。资源优先级按父PROCEDURE：task6.1的F0 > 本任务正式训练 > task6.1筛选。N=20且CPU预算满足时直接启动；否则停下报告，不自行减少worker。

硬性约束：
- 训练命令与 forem/results/task5/t5.2-train-s40/launch.json 逐字相同，只加 --world_type gazebo，并按§4设置 --num_workers。种子40、100万步、training_intensity 0.1、num_gpus 0、评估频率/episode数/eval_seed一律不改。
- 只能在 forem/build/task6.2/ws_husky 副本的 env_creator 中加入worker→实例环境变量映射。不得修改 husky/、mobile-rl/、forem/src、forem/build/task5 及task5的任何文件。
- 不得调用 launch_ros（会kill已有ROS和gzserver）。
- 不得触碰 forem-t5-pr2、forem-t5-husky、forem-dev 容器及其中的进程。只能停止你自己启动的进程和容器。
- 产物只写 forem/results/task6/t6.2-*、forem/logs/task6/t6.2-*，run-id一律以t6.2-开头。
- 不做物理成功测量、不做B策略的Gazebo零样本评估、不做9任务Gazebo评估、不做多种子、不改奖励/观测/任务/终止/训练器。
- 上游代码不支持续训。训练或实例崩溃：保留证据，停下报告，不自动重训。
- 遇到PROCEDURE“异常处理”所列情况：停下，写入RESULTS和日志，交给Claude决策。

记录要求：
- 在PROGRESS登记task6.2负责人（Codex）、状态和开始时间。日志写在 forem/doc/agent_logs/task6/task6.2/YYYYMMDD-codex-task6.2.md，写明实际使用的模型和推理强度。
- 只更新task6.2自己的RESULTS和日志，不修改父task6或task6.1的文档。
- 按PROCEDURE逐节填写RESULTS：实际命令、digest/sha256、退出码、日志与产物路径、失败记录。计划内容不得写成结果。
- 长任务写明容器、PID、日志、监控方式和停止方法；持续工作期间至少每30分钟更新一次日志。新的实测论据（Gazebo就绪、隔离回归、profile、N的依据）登记SOURCES。
- 如果挂子Agent：先建子节点三文档（如task6.2.1）并登记；子Agent自报完成不能直接当作通过。

完成标准：正式训练达到100万步（或如实记录失败），训练中评估序列和最终Gazebo评估齐全，manifest已写，RESULTS状态改为review。保留容器forem-t6-husky-gz供Claude复核。不要自行标done。
```
