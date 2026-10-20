# task4.8 — 普通SAC基线与有限性能先导结果与交接

> **当前状态（2026-10-19核对）：closed（随task4关闭；正式训练t4s-plain/fb已结束，不再运行；未经独立复核）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**active（先导已完成；正式普通SAC三种子×100万步已于2026-10-09 12:01+08:00启动，进行中）**。实施：Claude主Agent（claude-sonnet-5-5，会话级effort high）；子任务[task4.8.1](task4.8.1/RESULTS.md)（多实例隔离，子Agent交付review，主Agent部分复核）。独立日志：[20261009-claude-task4-scwm-impl.md](../../../agent_logs/task4/20261009-claude-task4-scwm-impl.md)。

## 1. 用户追加指令（2026-10-09 对话内）

“装不下也没关系，一定要按照原项目的配置跑一次。”——完整规模按原项目配置执行一次，**即使超过72h也跑完**；不缩步数、不改任务语义。因此：保持参考的实时步进（不启用固定仿真窗口）、`transition_noise_base=0.04`、奖励/终止/动作/观测原样；仅保留4.7记录的、由“采样/logprob/更新一致”要求支持的双tanh公共修复。72h可达性改为如实报告，不作开跑门槛。

## 2. 实现与验证（均为新增文件，`forem/src`未改）

| 文件 | 作用 |
|---|---|
| `scripts/scwm_policy.py` | `FixedGaussianPolicy`：单tanh的`predict`，与`sample`/actor损失/critic目标同一分布（4.7反例见task4.7 RESULTS） |
| `scripts/scwm_sac.py` | `GpuReplay`（设备端uint8地图，局部地图为`cost>=20`的二值图，存储精确；与参考`ReplayMemory`同一采样索引流）、`ScwmSAC`（逐行复制`SAC.update_parameters`，设备张量批；完整训练状态保存/恢复：含log_alpha、alpha优化器、LR调度器、alpha值/冻结标志） |
| `scripts/scwm_env.py` | `ScwmEnv`：包装`Task3Env`，不改观测/奖励/终止；每步记录t_obs/t_cmd/t_next等；episode结束读取Gazebo `get_link_state`（wrist_3×URDF静态变换）得独立物理末端，物理成功=位置<0.025 m、1−(qa·qb)²<0.05、0 IK失败、0碰撞（沿SRC0108），仅评估记录 |
| `scripts/scwm_train.py` | 训练入口：参考main.py循环语义（随机预热1000步→策略；`len(replay)>batch`后每步1次更新，**先更新后push**；mask=float(not done)），预算、账本（含未完成episode的`train_partial`记录）、阶段计时、完整状态检查点与续训（来源/配置hash变化则拒绝）、验证种子101–105的确定性验证与权重保存、`--pin-ckpt-steps`保留分叉点检查点 |
| `scripts/scwm_supervise.py` | 单worker长跑监督：崩溃/心跳停滞/仿真死亡→新仿真实例+续训 |
| `scripts/scwm_wm.py`、`scwm_feedback.py` | 4.9/4.10模块（见各节点） |
| `scripts/scwm_clock.py` | 固定窗口/去节流工具，**已评估并否决**（见§4，不启用） |

**测试（容器内，通过）**：`tests/test_scwm_sac.py` 7项（predict单tanh且与sample一致；`GpuReplay`与参考`ReplayMemory`取同批；3次更新后与参考`SAC.update_parameters`损失/参数/alpha一致；完整状态续训与不中断一致；npz往返；非二值地图被拒；CPU与cuda:3均通过），`tests/test_scwm_train_loop.py` 2项（FakeEnv：预算500步、账本步数=500、`train_partial`记录；**300步中断+续训到500步与不中断运行的最终策略参数、更新数逐位一致**；配置变更续训被拒）。

## 3. 观测滞后与物理成功诊断（真实仿真）

- `t4.8-obslag-r1`（`scripts/diag_scwm_obs_lag.py`）：观测里的底盘位姿在`env.step(a_t)`发出指令的时刻读取（C++`step`先发命令后立即读TF），因此**`o_{t+1}`不含`a_t`对底盘/地图的物理影响**；底盘对转速指令还有约2步的加速斜坡。拟合的观测—真值滞后0.008 s（真值取step返回后），转动在真值与观测中均于第19步开始。推论：`F(z_t,a_t)→z_{t+1}`能学到的主要是**规划/IK路径与上一动作字段**的后果；动作对底盘/局部地图的物理后果在`o_{t+2}`及以后才出现。这是原基准的固有时序，不修改；已在4.9提示。
- 先导中同一episode集合上**内部成功与物理成功明显不同**：`t4.8-par-s0/1/2`（各6000步）共117个已完成episode，内部成功1/3/5，物理成功0/0/1——证实不能用规划到达替代实际末端成功（SRC0161）。

## 4. 性能与耗时（实测，真实仿真，plain SAC，CUDA）

| 项 | 结果 | 证据 |
|---|---|---|
| 单次SAC更新（batch 256） | 参考路径31.6 ms → 设备回放路径17.7 ms（cudnn.benchmark 16.7 ms）；profiler：GPU核时间≈5.1 ms/更新，**CPU/launch受限** | `results/task4/t4.8-perf-update-r1/` |
| 实际循环中各阶段 | select 1.4 ms，env.step 16.4 ms，update 22–24 ms，push 0.4 ms；**reset 20–25 s/episode**；平均episode约140–150步 | `t4.8-pilot-rt1`、`t4.8-par-s{0,1,2}`的progress.jsonl |
| 端到端吞吐 | 约5 steps/s/worker（含reset）；3个worker并行互不拖慢（5.3–5.5 vs 单worker 4.3–5.3）；sim/wall≈0.5 | 同上 |
| 决策间隔（实时模式） | “思考”仿真时间≈23 ms（策略推理+更新），step≈14.5 ms，总间隔≈38 ms | progress.jsonl `sim_*` |
| reset构成 | `map_reset`≈15 s（delete_model每个固定约0.4 s×16、重复的pause/unpause、spawn约4 s），机械臂复位C++≈13 s；Gazebo `pause_physics`服务自身耗时0.3–2.5 s（不稳定） | `t4.8-reset-prof-r1`、`t4.8-spawn-probe-r1.json`、`probe_scwm_pause.py` |
| 已否决的提速 | ①reset期间取消物理循环墙钟节流：场景与首个观测与慢速**逐位一致**，但墙钟反而更慢（26→35–50 s，sim时间增加，因其余等待是墙钟型）；②线程并发spawn/delete：无收益（delete服务固定0.4 s/个）；③固定仿真窗口：每步需`pause_physics`，其延迟0.3–2.5 s，不可行 | `t4.8-fast-reset-r1`、`t4.8-spawn-probe-r1.json` |
| 多实例（子Agent 4.8.1，自报，主Agent抽查bench.json一致） | K=1…12每实例约57–62 steps/s（随机动作、无学习），每实例约2.2核，K≥24衰减；NUMA绑核增益≤0.8% | [4.8.1 RESULTS](task4.8.1/RESULTS.md) |

**72h可达性估计（如实）**：每个worker约5 steps/s（reset占约80%墙钟）→ 1M步≈55 h/run；三种子并行，故“前缀＋分叉”方案总墙钟约60 h量级加WM/评估；**未经全程实测，不作承诺**。reset是主要瓶颈，可行优化已评估三项均无效；剩余候选（去除`map_reset`/`clear`中冗余pause/unpause）预计省约数秒/次，需修改`forem/src`，暂未采用。按用户指令，不因时限改变配置。

## 5. 正式运行（进行中）

- 配置：`config/task4_scwm/plain.yaml`（参考默认：batch 256、buffer 10万、warmup 1000、每步1更新、LR视界5000001；验证每10万步用种子101–105；检查点每2万步，保留10万步分叉检查点）；训练场景种子从[1000,2³⁰)随机抽（与验证101–105、测试106–110不相交）。
- 运行：`t4s-plain-s0/s1/s2`，seed 0/1/2，cuda:0/1/2，仿真实例0/1/2（ROS 11400+k），由`scwm_supervise.py`监督，开始2026-10-09 04:01 UTC（12:01 +08）。日志`logs/task4/t4s-plain-s*/`，产物`results/task4/t4s-plain-s*/`。监控：`progress.jsonl`（每1000步）、`episodes.jsonl`、`events.jsonl`、`supervisor.log`；停止：向supervisor进程发SIGTERM（训练器写检查点后退出）；恢复：重新启动同一supervisor命令（自动`--resume`）。
- 监督器测试：`t4.8-par-s2`在3000步处手动`kill -9`训练进程→10 s内新仿真实例+从2000步检查点续训→完成6000步（`restarts=1`）。

## 6. 剩余与风险

- 基线是否能学到成功尚属未知（先导仅6000步，物理成功0–1次）；负结果也照实保留。
- 双tanh公共修复使本基线不同于“原样”参考行为（任务/奖励/终止/动作语义未改，动作分布变为与训练一致）。
- 未做：正式运行的阶段性验收、复位冗余调用优化、WM/反馈阶段（4.9–4.11）。
- 总预算口径(a)(b)(c)待用户确认（见task4.7）；plain三种子正式运行不依赖(b)(c)。

## 负责人、模型与来源

Claude主Agent实施；4.13独立复核拟Codex。推荐Claude Sonnet5.5（常规low、跨模块medium）；实际：claude-sonnet-5-5，会话级effort high（平台启动参数，无法按步切换）。依据：[SRC0178](../../../SOURCES.md#src-0178) · [SRC0179](../../../SOURCES.md#src-0179) · [SRC0180](../../../SOURCES.md#src-0180) · [SRC0181](../../../SOURCES.md#src-0181)。


## 7. 基线学得慢的单因素对照（诊断，非正式；2026-10-10）

动机：正式plain/feedback在45万步仍无可观察提升（物理成功率1–2%，约90% episode因累计20次IK失败终止，结束时末端平均离目标2–3 m）。在空闲GPU 3上以独立脚本`scripts/scwm_train_diag.py`（正式运行用的`scwm_train.py`未改）各做**一个单因素**、种子0、6万步的对照（运行`t4.8-diag-ik50`、`t4.8-diag-legacytanh`；对照基准=正式`t4s-plain-s0/1/2`前6万步同口径统计，种子间本身有波动）。汇总文件`results/task4/t4.8-diag-comparison.txt`。

| 6万步内（物理有效episode） | episode长度中位 | 结束时离目标中位(m) | 到达目标 | 物理成功 |
|---|---|---|---|---|
| 正式plain s0/s1/s2（IK阈值20，单tanh） | 133/143/139 | 2.60/2.14/2.29 | 8.9/10.9/9.2% | 1.5/1.9/1.1% |
| 对照：`ik_fail_thresh=50`（参考的评估默认值） | **177** | 2.72 | 10.4% | 1.0% |
| 对照：恢复参考双tanh | 142 | 2.57 | 10.2% | 1.8% |

结论（仅限单种子/6万步）：①把IK失败阈值提到50使episode更长，但末端并没有更接近目标，到达/成功率无提升，也就是**失败额度不是主要限制**；阈值50时episode中位只有177步（若失败率保持14.6%/步应约340步），说明一旦进入够不着的构型就几乎每步失败，失败是持续状态而非零星事件。②双tanh修复与否在此规模下**没有可见差别**（与三条正式运行一致）。③基线低成功率不能归因于这两项；原因仍未知（候选：需要远多于45万步、每步仿真间隔与原项目训练条件不同、策略尚未学会把底盘开向目标）。限制：单种子、6万步，不外推到100万步。
