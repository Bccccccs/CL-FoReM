# 给Codex的派发提示（task5.5最终sim评估结果入账与F0同口径对照）

- 编写：2026-10-20，Claude（claude-opus-5-5，推理强度未知），应用户要求“写一段派发提示给Codex：把task5.5最终sim评估结果写入RESULTS、更新PROGRESS并与F0同口径对照”。
- 状态：已写好，由用户转交；Claude未派发。下面代码块为可直接粘贴的正文。
- 背景：Claude 2026-10-20复查发现三条评估已于2026-10-19 22:51–22:52结束（eval rc=0、stop rc=0），但结果未写入task5.5 RESULTS，PROGRESS仍为active，见[核查记录](../../task7/20261019-claude-codex-supervision.md)“2026-10-20 复查”节。

```text
你在 /home/ybc/projects/CL-FoReM 工作。本次只做“已有结果的核对、汇总与入账”：只读现有评估产物与日志、写文档。不重跑或新增任何评估，不训练，不做Gazebo评估，不启动、停止或重建任何容器/实例/进程，不占用GPU，不修改 forem/src、forem/config、forem/scripts 和任何 eval.json/日志原件，不修改参考仓库。推荐模型 GPT6.1sol，推理强度 medium（需核对评估口径与脚本版本是否一致）；在日志里写明实际模型和强度，无法核实写“未知”。

注意并发：Claude会话可能在写 forem/doc 下的共享文件。每次写共享文件前重读；向 SOURCES.md 追加条目前先看文件末尾当前最大编号（目前到 SRC-0393），从下一个编号开始，写入时确认文件在你读取后没有被改过。不要 git add -A，不要提交。

开工前必读：根 AGENTS.md（来源登记、任务组织、未经验证不得标完成）、forem/AGENTS.md、forem/doc/README.md、forem/doc/PROGRESS.md；task5.5 三文档 forem/doc/tasks/task5/task5.5/{TASK,PROCEDURE,RESULTS}.md；你上次的启动日志 forem/doc/agent_logs/task5/task5.5/20261019-codex-final-sim-eval.md；F0 最终评估 forem/doc/tasks/task6/task6.1/RESULTS.md §9（9.2 评估设置、9.3 结果表、R4 Claude复核）。在 PROGRESS.md 登记本次任务（负责人Codex、状态active、开始时间、记录路径），新建独立日志 forem/doc/agent_logs/task5/task5.5/20261020-codex-final-sim-results.md，并在旧启动日志末尾加一行指向它。

== 输入 ==
- 本次三条：forem/results/task6/t5.5-final-sim-s{0,1,2}-r1/eval.json；forem/logs/task6/t5.5-final-sim-s{0,1,2}-r1/{start.out,eval.out}（末尾应有 eval rc / stop rc）；启动证据 forem/logs/task5/t5.5-final-eval-launch-20261019/（manifest.json、各 *-launch.json、startup-verification.json）。
- F0 三条：forem/results/task6/t6.1-eval-sim-s{0,1,2}/eval.json；启动脚本 forem/logs/task6/t6.1-eval-launch/eval_one.sh。
- Claude 2026-10-20 只读速览（仅供你交叉核对，必须独立复算，不得照抄）：三条 n=50、completed 50、capped 0、errored 0，internal_successes 32/33/30，ik_failure_episodes 18/17/19，collisions 0/1/1。若你复算结果不同，以原件为准并在日志写明差异。

== 步骤 ==
1. 完整性核对：三条 eval rc 与 stop rc；分母固定50、种子2001–2050齐全无重复；completed/capped/errored；每条使用的策略确为对应训练 run 的 ckpt/policy_step05000000.pt（核对路径与文件存在，能核哈希就记哈希）；只读核实 inst63/64/65 对应的评估进程已退出、无本任务残留进程（用 ps 或已有日志，不调用会改变状态的命令）。
2. 同口径核对（与 F0 的 §9 设置逐项比较，逐项写“一致/不一致/无法核实”）：
   - 评估脚本：F0 用的 scripts/eval_task6_final.py 版本与本次所用版本（你启动日志记为 ba140ec7…，改动见 SRC-0253）。说明差异是否只涉及 Gazebo 可选覆盖与记录字段，对 sim 评估语义有无影响；F0 当时的脚本哈希若未记录，写明依据何种证据判断。
   - 评估参数：world=sim、确定性动作、每种子1回合、max_steps_per_episode、max_close_steps=500、force_rectangle_obstacles=True、time_step、ik_fail_thresh 等（本次 eval.json 有 effective_config，F0 的 eval.json 没有该字段，需从脚本默认值或启动参数确认）。
   - 场景：逐种子比较本次与 F0 sim 侧的 episode_spec（障碍几何与位姿、goal_tip/goal_wrist、规划臂初始关节、base_tf），给出50个种子中完全一致的个数；不一致的列出种子号。
   - 训练配方差异：只有总步数1M→5M（task5.5 RESULTS 已核 manifest），学习率日程随总步数不同（5M 时走完整个衰减日程，F0 只走前1/5），写明这一点。
3. 结果表：按 task6.1 RESULTS §9.3 同样的列写三条本次结果（内部成功/50、Wilson 95%、completed/capped/errored、碰撞 episode、含IK失败 episode、平均步数），再并列 F0 的三条与均值。只做描述性对照，不做显著性检验，不新增分析口径。若场景逐种子一致，可再并列给出“同一种子上两者都成功/仅一方成功/都失败”的计数（这是同一批数据的描述，不是新实验）；若场景不一致，只用一致的种子做该计数并注明。
4. 按 task5.5 TASK“交付与验收”的要求，再把 task5.2（RLlib 1M，sim simpleobstacle 训练中评估约0.78）并列一行，但明确写出：实现不同、场景不同（约一半椭圆柱）、评估集与口径不同、仅1个种子，不是同口径比较。不要把它和 F0/本次的数字直接相减。
5. 写入文档：
   - task5.5 RESULTS：把“## 最终评估”节从“运行中”改为实际结果（步骤1–4），保留原启动记录；在“与CBL过往训练对照”节末尾**追加**一段“最终评估后的更新”，说明 D15（3001–3050）与最终评估（2001–2050）口径不同，原判断哪些仍成立、哪些需修正；不要改写 Claude 原文。更新交接。
   - task5.5 TASK、PROCEDURE 顶部“当前状态”行同步。
   - 状态：结果入账与核对完成后，task5.5 标为 review（待 Claude/用户复核），不要直接标 done。
   - PROGRESS：把“运行中”表里 task5.5 那一行改为已结束（或移出运行中并在阶段一表中更新 5.5 状态与待办）；把你的 TASK5.5-FINAL-SIM-EVAL-20261019 行改为 done（写明评估已于 10-19 22:52 结束、结果于本次入账）；登记本次任务行。
   - SOURCES：新增一条项目实测条目（task5.5 最终 sim 评估结果与同口径核对），写清 run-id、eval.json 路径与哈希、脚本版本、核对结论与限制。
6. 完成后在独立日志“交接”节写明：已完成、证据路径、口径核对中“不一致/无法核实”的项、未解决问题（例如 F0 场景分叉种子是否影响、是否需要 Gazebo 零样本评估——后者须用户另行授权，你不要启动）、下一步。

== 验收 ==
- 所有数字可由 eval.json 原件复算；每个“同口径”判断都有证据位置或明确写“无法核实”。
- 没有新运行任何评估/训练/容器操作；没有修改结果原件。
- task5.5 状态为 review，PROGRESS 不再显示“评估运行中”。
```
