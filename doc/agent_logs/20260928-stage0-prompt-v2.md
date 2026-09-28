# STAGE0-028 启动提示词 v2（2026-09-28，Claude Opus 5.5 /ybc）

取代已作废的 `20260928-stage0-handoff-prompt.md`。以下整段交给执行 Agent。

---

你负责 Husky 世界模型闭环项目的 **Stage0 前置验证（任务 STAGE0-028）**。

**工作区已改名**：现在是 `/home/ybc/projects/CL-FoReM`（原 `/home/ybc/projects/mm_husky_ws`，15:53 改名，内容不变）。唯一开发代码在 `src/modulation_rl`。容器内仍挂载到 `/root/mm_husky_ws`。文档里残留的旧宿主路径一律按新路径理解（AGENTS/ENV 已于 16:0x 同步，常驻容器 `mmhusky-node01`/`-gz` 已按新路径重建，见 PATHSYNC-028）。开工前先 `ls` 确认新路径存在。

## 一、开工前

1. 按顺序阅读：`AGENTS.md` → `doc/README.md` → **`doc/ROADMAP.md`（唯一执行计划，本任务规格见 §4、§9）** → `doc/PROGRESS.md` 顶部看板 → `doc/DECISIONS.md`（重点 D32–D40）→ `ENV.md` → `doc/agent_logs/20260928-stage0.md`（全部历史，包括上一次执行被停止和清理的经过）→ `doc/agent_logs/20260928-logic-review.md`（L1/L2 已并入 R0-3/R0-4 判据）。
2. 在 PROGRESS“进行中”表的 STAGE0-028 行填入你的 Agent 名称，状态改为 active；在 `doc/agent_logs/20260928-stage0.md` 末尾追加接手记录。
3. 遵守 AGENTS.md 第2节：每个子任务开始、完成、失败、启动长任务时都更新日志，持续工作每30分钟至少一次。日志写明命令、容器名/PID、退出码、产物路径。追加 DECISIONS 前先查最大编号（现为 D40）。

## 二、任务（按 ROADMAP §4，先后顺序如下）

1. **R0-1**（先启动，后台运行）：使用已审查的 `doc/agent_logs/20260928-stage0-r01-launch-s22.sh` 和 `-s33.sh`（宿主路径已改为新路径，内部调用 `20260928-stage0-r01-runner.py`）。启动前：
   - 确认 GPU1、GPU2 空闲；
   - 确认 `results/p1-retrain-20260928/trainval-1000-s22|s33` 不存在；
   - 在宿主创建 `diagnostic-s22|s33` 目录。

   用法：`nohup bash doc/agent_logs/20260928-stage0-r01-launch-s22.sh > results/p1-retrain-20260928/diagnostic-s22/launch-nohup.log 2>&1 &`，s33 同理。单次约20分钟。
2. **M 失配开关**（R0-1 运行期间做）：
   - 位置：`scripts/modulation/envs/robotenv.py` 的 `step`。
   - 参数：`base_vel_gain`（固定值，或 `base_vel_gain_range` 每回合采样）、`action_delay_steps`（只作用于底盘命令）。
   - 顺序：命令值（含现有噪声和加速度裁剪）→ `_prev_base_actions_scaled` 仍存命令值 → 延迟 → 增益 → `_calculate_base_command`。
   - 随机源：用由回合种子派生的独立 RNG，不消耗环境的 `np_random`。
   - 透传：给 `p0_runner.py` 和 `collect_rollouts.py` 加参数。
   - 上一次执行留下的未完成实现备份在 `doc/agent_logs/20260928-stage0-abandoned-mismatch.patch`，可以参考。但它有一个问题必须改掉：开关关闭时也会往轨迹 npz 和 episodes.jsonl 写新字段。**关闭时不得新增任何输出字段**，只有开启时才记录增益、延迟、命令/执行速度，并在 manifest 加语义标签 `mismatch-v1`。
   - 验收：单元测试通过；policy-100k、种子 10000–10019、fixed100、确定性各跑一遍，"不带参数"与"显式默认值"两种情况都与现基线所有字段差 0；现有 Python 测试全过。在 DECISIONS 记为版本化的环境语义扩展。
3. **R0-3 失配敏感性扫描**：按 ROADMAP §4 表格，先把配置和判据写入 DECISIONS。15 个配置 × 100 回合（种子 10000–10099），policy-100k 确定性。同时记录底盘/末端跟踪误差、参考进度和 IK 失败前兆，用来区分失败原因。
4. **R0-4 在线更新信号**：新写 `scripts/wm/residual_probe.py` 及测试，复用现有 FeatureCache/WindowSource，内存有界。
   - 采数：7 个条件 × 100 回合（种子 9600–9699，stochastic，`--save-observations`）。
   - 协议：先预测后更新，只在**未用于更新的后续步**上评估；每回合重置；lr ∈ {1e-5,1e-4,1e-3} × 每 k 步 ∈ {1,5}；对照为冻结模型和 copy；robot/map 分块、按状态分层报告。判据见 ROADMAP。
5. **R0-2 独立 test**（R0-1 完成后）：
   - 先审计种子 9901–9999 在 `results/` 全部 manifest 和 doc 中是否被用过。
   - 未用过：先在 DECISIONS 登记"P1 独立 test v1"，再按 protocol-1000 同协议采 99 回合，seed11/22/33 的 action/no_action 模型各评一次（`wm/evaluate_prediction.py --split test`，特征缓存用新目录）。
   - 用过：停下来问用户。
6. **R0-5 Gazebo 对齐**（工程，限时约1天）：
   - 新增默认关闭的 `--gz-time-step`（目标 0.1s，映射到 config `time_step`，现默认 0.02，见 `modulation/utils.py:106`）和 `--gz-deadline-wait`（把 `src/robot_env.cpp:257–258` 的固定 `ros::Duration(dt_exec).sleep()` 改为从上次下发命令起按仿真时间睡到 +dt_exec）。
   - 容器内 catkin 重编译，C++/Python 回归，确认 analytical gate 差 0。
   - 先确认 simpleobstacle 在 Gazebo 下能否生成障碍，不能就两边都用 picknplace。
   - 按 ROADMAP §4 做 20+20 回合对比和残差检查。

## 三、硬约束

- 不改 SAC、奖励、终止、IK 语义；评测一律带 `--ik-mode fixed --ik-iterations 100`；新行为默认关闭，关闭时与基线逐元素一致。
- 种子只用 ROADMAP §9 登记的范围。20000–20299 在 Stage2 之前不得使用；旧 test 9000–9199、旧 val 8000–8099 不得当未见测试。
- 判据先写入 DECISIONS，事后不放宽。
- docker 用 `sg docker -c`，新容器名加 `mmhusky-r0-` 前缀，后台 Python 用 `python3 -u`。**不得停止、重启或重建** `mmhusky-node01`、`mmhusky-node01-gz`：它们的挂载源还登记为旧路径，重启会失败。需要 ROS/Gazebo 时，用 `docker/run.sh` 在新路径下另建 `mmhusky-r0-*` 容器。
- 不实现 P2/P4，不训练 SAC，不进入 Stage1。未经用户要求不 git commit，保留他人未提交的改动（`src/modulation_rl` 中 `wm/*` 等属于 P1-FIX-028）。

## 四、完成标准

- 在 `doc/agent_logs/20260928-stage0.md` 写出 G0 判定表：M、R0-1、R0-2、R0-3、R0-4 各自是否通过，附证据路径；R0-5 作为参考项。
- 按 R0-3 结果建议 F1 用的训练随机化范围和留出测试档位。
- 更新 PROGRESS（全部验证完才能标 done）。
- 向用户汇报 G0 结论。任一项不通过就停下，说明原因和备选方案，不进入 F1 或 Stage1。
