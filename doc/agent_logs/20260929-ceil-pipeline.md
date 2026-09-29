# CEIL-028 SAC 上限摸底：实现与无人值守流水线

- 任务 ID：CEIL-028
- 执行 Agent：Claude Sonnet 5.5 /ybc（实现与启动）；设计与预登记：Claude Opus 5.5 /ybc（协调方，仅文档）
- 开始：2026-09-29T11:24+08:00
- 状态：active
- 用户要求：按 [设计说明](20260929-ceil-spec.md) §3、§6 实现默认关闭的 `--policy-override {random,mean,slow-ee}`、编排脚本 `ceil_pipeline.py`、宿主启动脚本 `20260929-ceil-launch.sh`、自动报告 `20260929-ceil-report.md`；启动前做默认关闭回归、单元测试、冒烟；提交后一次性启动无人值守流水线，确认两个 30 万步训练进程与 E2 评测已运行后汇报并结束，不守候（预计 11–14 h）。
- 判据：D57（[DECISIONS](../DECISIONS.md)）预登记，本任务不得修改。
- 分支：`ceil-028`，自 `screen-028`（HEAD `8834339`）新建；只按路径 `git add`；不 push、不合 main、不用 `git stash`。
- 硬约束：不从 policy-100k 续训（从零训练预算 300000 步，其余配置同 policy-100k）；新代码放 `scripts/` 顶层，不放进/不修改 `scripts/wm/`；新行为默认关闭，关闭时输出逐字段不变；评测 `--ik-mode fixed --ik-iterations 100`；统计先写点估计再算 CI；种子：训练 11/22，评测 10000–10099，20000–20299 不得使用；worker ≤64、可用内存 ≥60 GiB 才启动新批次；不停止/重建他人容器与进程。

## 已读文档（2026-09-29 11:00–11:24）

`20260929-ceil-prompt.md`、`AGENTS.md`（含第 2 节）、`20260929-ceil-spec.md`、`DECISIONS.md` D55–D57、`20260929-screen-pipeline.md`、`ENV.md`、`PROGRESS.md`；代码 `p0_runner.py`、`sac.py`、`checkpointing.py`、`screen_pipeline.py`、`screen_stats.py`、`rollouts.py`。

## 接手记录（2026-09-29T11:24+08:00）

- 现场核查：分支 `screen-028`，工作区干净（HEAD `8834339`）；`docker ps`：`mmhusky-node01`、`mmhusky-node01-gz` 均 Up 19 h；`nvidia-smi` 4 卡各 14 MiB；`free -g` 可用 234 GiB；容器内仅 roslaunch analytical（PID 160/201）在运行，无 `screen_pipeline`/`p0_runner`/`ceil` 进程。
- 已在 `PROGRESS.md` 登记本任务行；已建分支 `ceil-028`。

## 设计核实（实现前）

1. **`num_steps` 取自 `--steps`**：`p0_runner.py:496` `SAC(..., args.steps)`；`sac.py:29/45` 学习率 `lr_end/lr_start ** (step/num_steps)`，故 `--steps 300000` 使学习率在 30 万步才衰减到底。续训协议 `protocol['total_steps']=args.steps` 被 `load_training` 比较，续训时必须传同样的 `--steps 300000`（流水线固定）。
2. **policy-100k 训练配置**（`results/p1a-20260923/sac-screen-100k/manifest.json`、`screen.sh`）：`--steps 100000 --save-interval 20000 --batch 256 --replay-capacity 100000 --random-steps 1000 --ik-mode fixed --ik-iterations 100`、seed 11、simpleobstacle、`max_episode_steps 2000`；agent config gamma .99/tau .001/initial_alpha 1.0/hidden [256,256]。本任务除 `--steps 300000`、`--save-interval 50000`、`--replay-compact-maps`（D55，采样逐位相同）、`--eval-interval 0` 外与之一致。
3. **基线来源**：spec 所称“R0-3c 名义 100 回合”= `results/stage0-028-r03c/gain1.0_delay0/`（policy-100k，种子 10000–10099，SR 70/100）。与 `results/screen-028/s1-l1/nominal` 的 100 个 `trajectory_sha256` 逐个相同（2026-09-29 11:2x 容器内实测），故基线 SR/回合数据直接复用，不重评。
4. **mean 动作**：由上述 100 回合轨迹 `episode-*-trajectory.npz` 的 `actions`（共 25923 步，各步等权）逐维平均得出，写入 `results/ceil-028/s0-preflight/mean-action.json`（约 [-0.309, 0.011, 0.264]，运行时以文件为准）；不手调。
5. **C-learn 读法（须如实说明）**：D57 原文“两个 300k 末端检查点的成功率相对 policy-100k 提升≥0.10，且‘训练种子×回合’分层 bootstrap 的 95% CI 下界>0”。实现为：a=(2,100)（分层=训练种子）、b=policy-100k 的 100 回合复制到两层，同下标重采样，点估计=两个末端检查点 SR 的平均−SR(policy-100k)，CI 为该分层 bootstrap 的 95% 百分位区间（`screen_stats.diff_with_ci`）。这是与“单个 CI”相容的唯一读法；报告中另列“每个种子各自”的点估计与 CI（仅描述，非判据），以便用户看到更严格读法下的结果。CI 只反映评测回合与训练种子的抽样波动，不含 policy-100k 自身训练随机性（基线只有一个种子）。

## 实现（2026-09-29 11:30–12:00，分支 `ceil-028`）

新增/修改（均在 `src/modulation_rl/scripts/` 顶层，未触碰 `scripts/wm/`）：

| 文件 | 内容 |
|---|---|
| `policy_override.py`（新） | `--policy-override` 的动作生成：random（`np.random.default_rng([回合种子, 0xCE11])`，均匀 [-1,1]，float32，与环境/BioIK 随机流无关）；mean（`mean_action_from_trajectories`：R0-3c 名义 100 回合 `actions` 逐步等权的逐维平均，附来源与动作哈希）；slow-ee（策略确定性动作，第 0 维固定 −1，不改输入） |
| `p0_runner.py`（改） | 新增默认关闭的 `--policy-override {random,mean,slow-ee}`、`--policy-override-mean-file`；仅在开关打开时才惰性导入 `policy_override`、在 episodes.jsonl 增加 `policy_override` 字段；`ceil_flags` 仅在开启时转发给逐回合 worker（默认命令行与之前逐字相同）；仅限 eval，且不可与 `--latency-wm-comp`/`--shield-config` 组合，mean 必须带文件 |
| `ceil_analysis.py`（新） | D57 判据、点估计→CI（点估计先写 `s4-report/point.json` 并先写草稿报告）、报告构建、预登记映射表 |
| `ceil_pipeline.py`（新） | 编排 S0–S4（见文件头）；复用 `screen_pipeline` 的资源池/评测队列/训练监督/导出；S3 边训练边评测，检查点一出现即导出仅策略权重并评测 |
| `screen_pipeline.py`（改） | 仅让任务号可由 `cfg.task_id` 覆盖（默认仍 `SCREEN-028`），使 CEIL 的 manifest 记为 `CEIL-028` |
| `tests/test_policy_override.py`、`tests/test_ceil_pipeline.py`（新） | 34 项 |
| `doc/agent_logs/20260929-ceil-launch.sh`（新） | 宿主启动脚本 |

流水线参数（与设计一致）：训练 `--steps 300000 --save-interval 50000 --batch 256 --random-steps 1000 --replay-capacity 100000 --ik-mode fixed --ik-iterations 100 --eval-interval 0 --replay-compact-maps`，seed 11/22 并行（GPU 0/1），训练超时 20 h，每次评测 1 h（超时则该检查点标 FAILED、其余继续），最多 4 次续训尝试（`--resume` 最新检查点，`--steps` 不变）；评测种子 10000–10099；`--max-workers 64`；启动新批次前可用内存 ≥60 GiB、<40 GiB 不新启进程；S0 另要求可用磁盘 ≥300 GiB 与 analytical 在线。

## 改动与验证

| 时间 | 文件/命令 | 预期 | 实际结果/退出码 | 证据路径 |
|---|---|---|---|---|
| 11:40 | 容器内 `python3 -m pytest tests/test_policy_override.py tests/test_ceil_pipeline.py -q` | 全部通过 | **34 passed**（random 可复现/同种子同序列/不动全局 RNG；mean 为步等权逐维均值，非回合均值的均值；slow-ee 只改第 0 维、不改输入；CLI 转发与非法组合被拒；用假环境跑 `p0_runner.evaluate`：默认关闭无新字段且用策略，random/mean 不调用策略并打 `policy_override` 标签，slow-ee 调用策略并覆盖第 0 维；D57 C-policy 阈值含等号、C-learn 点估计/CI 双闸门、两种子池化读法与严格读法并列、映射四格、缺数据不补、点估计先于 CI 落盘、S3 增量发现检查点/续跑不重评/失败臂不阻塞；`num_steps=--steps` 学习率曲线：30 万预算在 10 万步 lr≈2.15e-5，10 万预算在 10 万步=1e-6） | `tests/test_policy_override.py`、`tests/test_ceil_pipeline.py` |
| 11:55 | 容器内 `python3 -m pytest tests/ -q -p no:warnings`（全部测试；提交前再跑一次） | 全部通过 | **223 passed**（此前 189，新增 34；两次运行均 223 passed，约 95 s） | 终端输出 |
| 11:30–11:38 | 默认关闭回归：`results/ceil-028-regression/launch.sh`；基线=`git show HEAD:…/p0_runner.py`（HEAD `8834339`，临时副本 `p0_runner_baseline.py`，已删除、未提交）；policy-100k、simpleobstacle、种子 10000–10019、`--ik-mode fixed --ik-iterations 100`、确定性、`--device cpu`；改动前 vs 新代码（无新开关） | 除计时字段外 episodes.jsonl 全部键与值、trajectory npz、tail.json 逐位一致 | `compare.py`（容器内）：**mismatches=0，ALL PASS**（20 回合）。另有一条仅供参考的对比：本次 CPU 结果与存档的 R0-3c 名义（CUDA）成败 20/20 一致、`trajectory_sha256` 因设备浮点差异不同（历史上同设备的 SCREEN 名义与 R0-3c 为 100/100 相同），不作判据 | `results/ceil-028-regression/{baseline,no-args}/`、`compare.py`、`compare.log` |
| 11:32–11:35 | 冒烟：`results/ceil-028-smoke-launch/smoke.sh` → `ceil_pipeline.py --output-root results/ceil-028-smoke --train-steps 2000 --save-interval 500 --random-steps 200 --eval-seeds 10000:10004 --report-path results/ceil-028-smoke/report.md --train-timeout-hours 2`（2 个训练 + E2 三臂各 4 回合 + 8 个检查点各 4 回合 + 报告） | 全流程跑通并生成报告 | S0–S4 全部 done（约 2.5 min），`PIPELINE DONE`；异常 0；E2 各臂动作核实（random 在 [-1,1] 且均值≈0；mean 与 `mean-action.json` 一致 [-0.3087, 0.0112, 0.2638]；slow-ee 第 0 维恒 −1）；报告含点估计草稿→终稿、判据、映射、学习曲线、耗时表；worker/训练 manifest 的 `task_id=CEIL-028`，训练 protocol 记录 `replay_compact_maps`；2000 步检查点 72 MB（10 万容量 replay 估计约 3.6 GB/个）。冒烟里的 SR 无意义（2000 步、4 回合） | `results/ceil-028-smoke/`（`report.md`、`status.json`、`pipeline.log`） |

冒烟发现并已修复的小问题：报告的检查点标签对 500 步取整成 0k（改为 `%g`k）；训练目录数把 `a0.log` 也算进去（改为只数目录）。修复后已重跑全部测试（223 passed）。冒烟输出保持修复前的样子，仅作证据。
