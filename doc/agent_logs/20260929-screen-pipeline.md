# SCREEN-028 前瞻场景筛选：实现与无人值守流水线

- 任务 ID：SCREEN-028
- 执行 Agent：Claude Sonnet 5.5 /ybc（实现与启动）；设计与预登记：Claude Opus 5.5 /ybc（协调方，仅文档）
- 开始：2026-09-29T09:45+08:00
- 状态：active
- 用户要求：按 [设计说明](20260929-screen-spec.md) §3、§4、§6 实现默认关闭的 latency-v1 / dynmap-v1、训练与评测支持、L3 世界模型补偿臂、编排脚本 `screen_pipeline.py`、宿主启动脚本、自动报告；启动前做默认关闭回归、单元测试、小规模冒烟；一次性启动流水线后汇报并结束，不守候（预计 5–7 h）。
- 判据：D52–D54（[DECISIONS](../DECISIONS.md)）已预登记，本任务不得修改。
- 分支：`screen-028`，自 `followup-028` 新建；只按路径 `git add`；不 push、不合 main、不用 `git stash`。
- 硬约束：新代码不放进/不修改 `scripts/wm/`；新行为默认关闭；只改策略输入，不改奖励/终止/碰撞/IK；评测一律 `--ik-mode fixed --ik-iterations 100`；统计先写点估计再算 CI；种子只用设计说明登记范围（训练 11/22，评测 10000–10099）；worker ≤64、可用内存 ≥60 GiB 才启动新批次。

## 已读文档（2026-09-29 09:46–10:10）

`AGENTS.md`（含第 2 节）、[设计说明](20260929-screen-spec.md) 全文、`DECISIONS.md` D45–D54、[FOLLOWUP 日志](20260928-followup-pipeline.md)（含统计阶段超时教训）、`ENV.md`、`PROGRESS.md`；代码：`p0_runner.py`、`followup_pipeline.py`、`foresight.py`、`shield.py`、`model.py`、`sac.py` 片段、`replay_memory.py`、`checkpointing.py`、`modulation/envs/{combined_env,tasks,map,simulator_api}.py`、`modulation/utils.py:create_env`、`wm/{encoder,dynamics}.py`、`residual_probe.load_model`。

## 接手记录（2026-09-29T09:53+08:00）

- 起点：`followup-028` HEAD `aed9c2b`；工作区有协调方留下的未提交纯文档改动（`DECISIONS.md` D52–D54、`PROGRESS.md` FOLLOWUP 行改 done、`20260928-followup-pipeline.md` 核查段、`20260928-followup-report.md`、`20260929-screen-spec.md`），判断为协调方产物，作为分支首个文档提交并入 `screen-028`（与 FOLLOWUP-028 接手时的做法一致）。
- 环境核查（09:46 实测）：4×GPU 空闲（14 MiB）；`free -g` 可用 234 GiB；容器 `mmhusky-node01` / `-gz` Up 18 h；容器内 `OMP_NUM_THREADS=2`、`nproc=4` 仅 exec 环境，宿主 64 逻辑 CPU。
- 已在 `PROGRESS.md` 登记本任务行。

## 早期实测发现（影响设计，非计划）

1. `p0_runner.py train --task dynobstacle --steps 300`（batch 16）在 analytical 下可运行：episodes 正常推进，约 0.2 s/步（含更新），输出 `results/screen-028-probe/d0-try1`。`--task` 经 `str.lower` 后 `dynobstacle` 有效，`p0_runner` 无需新增任务参数。
2. 观测结构：`(list[41], bool ndarray (120,120,1))`，`concat_prev_action=True`（41 维已含上一步动作均值，`PrevAction.max_size=1`）。局部地图取自 `_floorplan_img`（障碍为外轮廓环，非实心）；`step()` 内**先**取局部地图与做碰撞检查、**后**调用 `map.update` 移动障碍，因此第 k 步观测里的障碍位置是 `map.update` 之前的 P_{k−1}（重置时为 P_0）。dynmap-v1 的"当前"以观测里实际出现的位置为准（见下）。
3. 16 个障碍共用同一个 `RandomState`（`env.np_random`）；`RobotEnv` 另有独立 RNG，回合内只有障碍到达目标后重采样目标会消耗它，故对整个障碍列表做一次 `copy.deepcopy`（共享 memo）得到的副本共用一份被复制的 RNG，向前推 n 步与真实未来完全一致，且不触碰真实 RNG。
4. 障碍圆柱直径 0.3 m（12 px），速度 0.10–0.15 m/s，0.5 s 内位移仅 5–7.5 cm（2–3 px）。预登记的 5 步预览信息量因此很小，D 线开卷提升可能有限；这是设计事实，如实记录，不改设计。
5. 100k 步 SAC 的 replay 以 float32 存图，单个 checkpoint 约 11.7 GB、进程内约 11.5 GB；12 个进程并行会有约 140 GB 常驻加保存时 pickle 缓冲的瞬时峰值，逼近 251 GiB。见 D55：新增默认关闭的 `--replay-compact-maps`（地图以 bool 存储，采样时还原 float32，数值逐位相同），所有 SCREEN 训练均开启。

## 进度记录

- 2026-09-29T10:35+08:00 收到协调方会话（“项目文档阅读”）跨会话消息：D 线 future/past 时长 5 步 → **20 步（2.0 s）**，用户已同意，已写入 DECISIONS **D56** 与设计说明 §1/§4；核对磁盘上 D56 与 spec 修改内容与消息一致。**已采用 D56**：`DYN_HORIZON=20`，`--dyn-map-horizon` 默认 20；测试改为 20 步并覆盖前推期间重采样目标；past 保留最近 20 步位置（历史列表按时间索引）。`--replay-compact-maps` 决策登记为 **D55**（保留 D56 未覆盖）。
- 10:15–10:45 已实现并通过单测（容器内）：`policy_input.py`（延迟线、动作历史、future/past/freeze、outermost wrapper）、`latency_comp.py`（L3）、`screen_stats.py`（向量化分层 bootstrap，点估计先行）、`screen_analysis.py`、`screen_pipeline.py`；`p0_runner.py` 新增默认关闭开关 `--obs-latency-steps/--map-latency-steps/--obs-action-history/--dyn-map-mode/--dyn-map-horizon/--dyn-freeze/--latency-wm-comp/--replay-compact-maps`；`replay_memory.py` 增加 `compact_maps`。新增 3 个测试文件共 44 项（含环境级：future/past 不改变真实障碍位置、RNG 序列、奖励与当前地图；h=0 叠加图逐位等于原观测；freeze；latency wrapper 不改奖励）全部通过。

## 改动与验证

| 时间 | 文件/命令 | 预期 | 实际结果/退出码 | 证据路径 |
|---|---|---|---|---|
| 10:45 | 容器内 `python3 -m pytest tests/ -q`（含新增 `test_policy_input.py` 25、`test_latency_comp.py` 5、`test_screen_stats.py` 13、`test_screen_pipeline.py` 13、共 56 项+参数化） | 全部通过 | **189 passed**（0 failed；此前基线 132） | `results/screen-028-probe/full-tests-1.log` |
| 10:50 | 默认关闭回归：`results/screen-028-regression/launch.sh`；基线=`f7a6427` 的 `p0_runner.py`（临时副本，已删除，未提交）；policy-100k、`--ik-mode fixed --ik-iterations 100`、确定性、`--device cpu`；simpleobstacle 种子 10000–10019 三组（改动前 / 新代码无开关 / 新代码显式默认值）、dynobstacle 种子 10000–10009 两组（改动前 / 新代码无开关） | 除计时字段外 episodes.jsonl 全部键与值、trajectory npz、tail.json 逐位一致 | `compare.py`（容器内）：三项比较 mismatches=0，**ALL PASS** | `results/screen-028-regression/{baseline,no-args,explicit-defaults,dyn-baseline,dyn-no-args}/`，`compare.py` |
| 10:17–10:35 | 冒烟：`screen_pipeline.py --output-root results/screen-028-smoke --train-steps 2000 --save-interval 1000 --random-steps 200 --eval-seeds 10000:10004 --d0-steps 2000 --smoke-force-l1 full:3 --train-timeout-hours 2`（12 训练 + D0 + L1 七配置 + L3 + D2/L2 评测 + 报告） | 全流程跑通并生成报告 | S0–S8 全部 done（约 18 min）；28 个评测臂共约 120 回合、0 异常；12 个训练均 2000 步完成并导出仅策略 checkpoint；报告生成。冒烟结论（SR 全 0 等）无意义，L1 结论被 `--smoke-force-l1` 强制覆盖，已在报告标注 | `results/screen-028-smoke/`（`report.md`、`status.json`、`pipeline.log`） |

**冒烟实测的训练吞吐（12 进程并行、batch 256）**：`dynobstacle` 约 4.1–4.4 步/s（约 0.24 s/步，L-线仅 20 s⁻¹ 量级但早期回合极短，不代表 100k 步全程），据此 `dynobstacle` 100k 步需约 6.6 h，超过设计说明的 6 h 训练超时；故 `--train-timeout-hours` 默认改为 10（超时前可续训，判据不变）。这是运行参数，不是判据；如实记录。

**冒烟发现并已修复**：容器内 git “dubious ownership” 使报告与预检 manifest 里 git 信息为空 → `screen_pipeline._git_status` 用私有 HOME 的 `.gitconfig`（容器 git 版本旧，无 `GIT_CONFIG_GLOBAL`）。

## 长任务

未启动。

## 审查与问题

（随实现补充）

## 交接

（结束前补充）
