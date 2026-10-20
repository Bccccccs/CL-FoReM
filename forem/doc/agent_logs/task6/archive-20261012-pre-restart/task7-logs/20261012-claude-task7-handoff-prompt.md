# Task7 交接提示词（Claude编写，用户派发给Codex）

推荐派发配置：**模型gpt-6.1-sol（GPT6.1sol），推理强度medium**。长训监控子Agent用gpt-6.1-sol/low。只有多实例隔离已记录至少两种不同思路都失败且原因不明时，才改用gpt-6-astra/high，并在日志写明理由。

工作目录：`/home/ybc/projects/CL-FoReM`。需要docker权限（`sg docker -c '...'`）和长时间后台运行。

---

## 可复制提示词

```text
你是Codex，负责执行FoReM项目的task7：把Task5 B（Husky原版RLlib配方）原样改在Gazebo中训练。决策者和流程制定者是Claude，你按流程执行，不自行改动口径。工作目录：/home/ybc/projects/CL-FoReM。

开工前必须阅读：
1. 根 AGENTS.md（全部规则，尤其：功能范围硬性约束、SOURCES登记、递归三文档、日志与PROGRESS登记、性能优化不得改动科学条件）
2. forem/doc/PROGRESS.md 中的task5、task6、task7段
3. forem/doc/tasks/task7/TASK.md、PROCEDURE.md、RESULTS.md
4. forem/doc/tasks/task5/task5.2/RESULTS.md、task5.3/RESULTS.md（B的命令、生效配置和已批准偏差）
5. forem/doc/tasks/task4/task4.8/task4.8.1/RESULTS.md（多实例隔离做法）
6. forem/doc/SOURCES.md 中的 SRC-0227
7. forem/doc/agent_logs/task7/20261012-claude-task7-plan.md

任务：按PROCEDURE §1→§7执行。
- §1–§4（基线冻结、新容器forem-t7-husky与工作区副本、单实例Gazebo就绪、多实例隔离与回归、冒烟/profile/确定N）可以现在开始。
- §5正式训练须在task5的A/B训练进程退出后才能启动（除非Claude明确放行并行），并且要把task6正在占用的CPU计入预算（task6优先）。N=20且CPU预算满足时直接启动；否则停下报告。

硬性约束：
- 训练命令与 forem/results/task5/t5.2-train-s40/launch.json 逐字相同，只加 --world_type gazebo，并按§4设置 --num_workers。种子40、100万步、training_intensity 0.1、num_gpus 0、评估频率/episode数/eval_seed一律不改。
- 只能在 forem/build/task7/ws_husky 副本的 env_creator 中加入worker→实例环境变量映射。不得修改 husky/、mobile-rl/、forem/src、forem/build/task5 及task5的任何文件。
- 不得调用 launch_ros（会kill已有ROS和gzserver）。
- 不得触碰 forem-t5-pr2、forem-t5-husky、forem-dev 容器及其中的进程。只能停止你自己启动的进程和容器。
- 不做物理成功测量、不做B策略的Gazebo零样本评估、不做9任务Gazebo评估、不做多种子、不改奖励/观测/任务/终止/训练器。
- 上游代码不支持续训。训练或实例崩溃：保留证据，停下报告，不自动重训。
- 遇到PROCEDURE“异常处理”所列情况：停下，写入RESULTS和日志，交给Claude决策。

记录要求：
- 在PROGRESS登记task7负责人（Codex）、状态和开始时间。日志写在 forem/doc/agent_logs/task7/YYYYMMDD-codex-task7.md，写明你实际使用的模型和推理强度。
- 按PROCEDURE逐节填写RESULTS：实际命令、digest/sha256、退出码、日志与产物路径、失败记录。计划内容不得写成结果。
- 原始日志放 forem/logs/task7/<run-id>/，产物放 forem/results/task7/<run-id>/。
- 长任务写明容器、PID、日志、监控方式和停止方法；持续工作期间至少每30分钟更新一次日志。
- 新的实测论据（Gazebo就绪、隔离回归、profile、N的依据）登记到SOURCES。
- 如果挂子Agent：先建子节点三文档（如task7.1）并登记；子Agent自报完成不能直接当作通过。

完成标准：
- 正式训练达到100万步（或如实记录失败），训练中评估序列和最终Gazebo评估齐全，manifest已写，RESULTS状态改为review。
- 保留容器forem-t7-husky供Claude复核。不要自行标done。
```
