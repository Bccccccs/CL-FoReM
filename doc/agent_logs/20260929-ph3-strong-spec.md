# PH3-STRONG 设计说明：更强的非全局版本（实验 3.2，诊断）

- 编写：Claude Opus 5.5 /ybc（协调方，只写流程），2026-09-29 约16:50。
- 执行：Claude Sonnet 5.5 子 Agent。
- 判据与选择规则：**D65**（已预登记，实现与运行中不得修改）。背景：PH3 3.1 诊断几乎无伤害（[报告](20260929-ph3-obsmap-report.md)）；ROADMAP §5。
- 任务日志：[20260929-ph3-strong.md](20260929-ph3-strong.md)；报告：`20260929-ph3-strong-report.md`（执行 Agent 生成）。

## 0. 最重要的约束：不要干扰正在跑的 PH4.1 流水线

- `results/ph4-train/` 的编排器（PID 236767，容器 `mmhusky-node01`）会在训练结束后不断启动新的 `p0_runner.py` 进程，它们从**主工作区** `src/modulation_rl/scripts/` 重新 import 代码。**主工作区里被 import 的任何 `.py` 都不许改**（包括 `p0_runner.py`、`modulation/envs/*.py`、`observed_map.py`、`ph4_*.py`、`screen_pipeline.py` 等）。
- 因此在独立 git worktree 中开发：`git worktree add worktrees/ph3-strong -b ph3-strong ph3-obsmap`（`/worktrees/` 已加入 `.gitignore`）。容器内对应路径 `/root/mm_husky_ws/worktrees/ph3-strong`。测试与评测时把 `PYTHONPATH` 中主包 `scripts/` 替换为 worktree 的 `src/modulation_rl/scripts`，并在日志里核实实际导入路径（manifest 的 `module_paths` / `source_sha256`）。catkin 的 C++ 插件、launch 文件与主工作区共用（本任务不改它们）。
- 不停止、不重启任何现有进程或 ROS 栈（默认 11311，训练用 11421–11427，评测用 11431–11434）。3.2 的评测另起自己的 ROS 栈（端口 11441–11442 之类，仿照 `fb5f4e8` 的做法），用完后停掉**自己起的**栈并记录。
- 资源：3.2 评测 worker ≤16；启动前 `free -g` 可用 ≥60 GiB；训练优先，发现训练步速明显下降（对比 `results/ph4-train/train/*/a*.log` 的 TRAIN 行）就降低并发。
- 不修改 D60/D62/D64/D65；不删除任何 results 产物；不 push、不合并 main、不删分支；只按路径 `git add`（在 worktree 里提交到 `ph3-strong` 分支）。

## 1. 新开关（均默认关闭，关闭时输出逐字段不变）

### 1.1 `--obsmap-policy-map`（语义标签 `observed-map-v1+policy`）

- 需同时有 `--obsmap-radius > 0`，否则报错。eval 与 train 都支持（将来可能训练）。
- SAC 输入的局部地图（observation 的 120×120 地图）改为从**同一张已观测地图**裁剪：用与真值局部图相同的旋转裁剪（`Map._get_local_map_gt` 的逻辑），但底图换成已观测地图（未观测=空地，跨步累积，视角/半径/遮挡同规划器）。
- **碰撞判定、奖励、终止仍用真值局部地图**。接入点：`CombinedEnv.step` 里 `local_map = self.get_local_map(...)` → `check_collision(local_map)`（`combined_env.py:369-371`，行号以 worktree 为准）必须继续用真值；只替换传给 `_to_agent_obs` 的那张。回合开始 `set_ee_planner` → `_to_agent_obs(..., local_map=None)` 会自己调 `get_local_map`，也要换成已观测版本。
- 验证：`--obsmap-radius 100 --obsmap-fov-deg 360 --obsmap-occlusion-height 100 --obsmap-policy-map` 时（全可见）轨迹与基线逐位一致；小半径时观测地图中不出现未观测障碍（单测）；碰撞计数与只开规划器版本在同一轨迹上的计算方式一致（单测：同一状态下 `base_collision` 用真值）。

### 1.2 `--obstacle-spacing S`（语义标签 `layout-spacing-v1`）

- 默认不设 = 现有硬编码 3.0 m（`SimpleObstacleMap.__init__`，`map.py:837`，`self._obstacle_spacing = 3.0`），行为不变。设置时改为 S；偏移标准差 `offset_std` 保持 0.8 不变。仅 simpleobstacle。
- 需要从 `p0_runner.py` 经 `config` 传到 `SimpleObstacleMap`（`utils.py:506` 已有 `simpleobstacle_spacing` 通道但被硬编码覆盖——不要改变默认路径，只在显式给出新参数时生效）。
- 验证：默认关闭回归逐位一致；S=2.0 时障碍数量约为 3.0 时的 (3/2)² ≈ 2.25 倍（单测数一下 `get_varying_scene_objects`）；起点/目标采样在 S=2.0 下 20 个种子都能成功。

### 1.3 共同要求

- 所有新参数只在非默认时写入 manifest / 转发给逐回合 worker；episodes.jsonl 不新增字段（除已有的 `obsmap_*` 统计）。
- 新增单测放 `tests/test_ph3_strong.py`；worktree 内全量 pytest 通过（当前 267 项 + 新增）。

## 2. 实验 3.2（D65）

policy-100k（`results/p1a-20260923/policy-100k.pt`）确定性，`--ik-mode fixed --ik-iterations 100`，种子 10000–10099，同种子配对，各 100 回合：

| 版本 | 参数 | 对比的名义 |
|---|---|---|
| V1 | `--obsmap-radius 3 --obsmap-policy-map` | PH3 名义（`results/ph3-obsmap/nominal`，SR 0.70，可直接复用，不重跑） |
| V2 | `--obsmap-radius 1.5 --obsmap-policy-map` | 同上 |
| V3 | `--obsmap-radius 1.5` | 同上 |
| V4 | `--obstacle-spacing 2.0 --obsmap-log-reroutes` | —（V5 的名义） |
| V5 | `--obstacle-spacing 2.0 --obsmap-radius 3 --obsmap-policy-map` | V4 |

视角 270°、遮挡高度 0.5 m 取默认。输出 `results/ph3-strong/{V1..V5}/`。

**报告**（`doc/agent_logs/20260929-ph3-strong-report.md`，先写点估计再写 CI）：每版本 SR、perfect、IK 失败/碰撞回合比例、失败原因分布、改道统计（沿用 `obsmap_*`）；相对各自名义的配对差与 95% CI（10000 次、种子 0）；D65 伤害口径是否满足；按 D65 顺序 V1→V2→V3→V5 指出“第一个通过的版本”。**不启动任何训练**，训练设定等 PH4.1 结果与用户确认。

## 3. 验证顺序（全部通过才跑 §2）

1. worktree 里先跑干净基线（worktree 刚建好、未改代码时；种子 10000–10019，`--device cpu`，用自己的 ROS 栈）。
2. 实现 §1，默认关闭回归逐位一致（episodes.jsonl 除计时字段、trajectory npz、tail.json）。
3. 全可见等价性（§1.1）。
4. 单测与全量 pytest。
5. 冒烟：V2、V5 各 5 回合。

## 4. 协作要求（AGENTS.md §2）

- 日志 `doc/agent_logs/20260929-ph3-strong.md`：开头原样记录任务提示词，写执行计划；关键节点与每 30 分钟更新；记录命令、退出码、产物路径、实际导入路径。
- 日志与报告写在**主工作区**的 `doc/`（文档不被 import，安全），但提交在 worktree 分支里进行时注意文件路径；推荐：代码在 worktree 提交到 `ph3-strong`；文档在主工作区按路径提交到当前分支 `ph3-obsmap`。
- PROGRESS 只改 PH3-STRONG 行。新决策编号从 D66 起（写前重读）。
- 与本说明或 D65 冲突、或会影响正在跑的流水线时：停下，写日志，回复协调方。

## 5. 完成标准

§3 全部通过、§2 五个版本评测完成、报告写好、代码与文档提交、自己起的 ROS 栈已停止并记录；PROGRESS 行改 `review`。最终回复给协调方：验证结果、各版本 SR 与 CI、D65 判定与“第一个通过的版本”、提交哈希、偏离与未解决问题。
