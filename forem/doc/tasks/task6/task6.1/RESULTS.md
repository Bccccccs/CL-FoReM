# task6.1 ScwmSAC sim组 — 结果与交接

> **当前状态（2026-10-19核对）：done（Claude复核R4）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**done（2026-10-13 Claude复核通过；遗留：3个种子场景分叉根因未查，见末尾R4）；原状态review（Claude子Agent交付；§1–§7已完成，§8按Claude门槛不启动，§9最终评估与§10汇总已完成，待Claude复核；不标done）**。执行者原为Codex，额度耗尽后由Claude子Agent（claude-sonnet-5-5，推理强度未知）临时代行，Codex恢复后接回。按[PROCEDURE](PROCEDURE.md)逐节填写。

## 阶段状态

| 阶段 | 结果 | 证据 |
|---|---|---|
| §1 开工与基线冻结 | 54/54哈希匹配 | `results/task6/t6.1-baseline/baseline_source_diff.json` |
| §2 sim模式实现与回归 | R1/D18通过；D20已实现；子Agent复核：task3 76项/3原skip通过，scwm 23项通过，task4同6项既有失败 | `logs/task6/t6.1-baseline/`、`logs/task6/t6.1-claude-verify/` |
| §3 场景等价性门槛 | r1失败（几何）；**r2通过：10/10、位置/偏航差0、160个障碍全为矩形、15/15 Task4.8 sampler哈希一致** | `results/task6/t6.1-equiv-r1/`、`results/task6/t6.1-equiv-r2/equivalence.json` |
| §4 D14对照开关与单元测试 | 通过：d14 6项、循环级缺省逐位等价（子Agent新增核验） | `tests/test_task6_d14.py`、`results/task6/t6.1-claude-verify/loop_equiv/`、`results/task6/t6.1-baseline/d14_diff.json` |
| §5 冒烟、profile与并行方案 | 完成：冒烟F0/F6通过；一类优化实测；二类未过门槛，未启用；方案见下文§5 | `results/task6/t6.1-perf-r1/`、`logs/task6/t6.1-smoke-r1-*`、`results/task6/t6.1-smoke-r1-*` |
| §6 F0三种子×100万步；F1–F6筛选 | **完成**：F0三条10-12 20:16–20:21 UTC（04:16–04:21+08:00）正常结束，筛选6条30万步正常结束，0次失败重启 | `logs/task6/t6.1-sim-plain-s*`、`logs/task6/t6.1-scr-F*-s0`、`results/task6/t6.1-summary/manifest.json` |
| §7 F0早期读数与筛选门槛 | Claude已完成（见下文“§7 筛选表与Claude门槛”）：§8暂不启动 | 下文§7 |
| §8 确认训练 | 按Claude §7门槛**不启动** | 下文§7 |
| §9 最终评估 | 完成：sim侧3条、Gazebo侧3条（s1首次因gzserver崩溃重跑为-r2）；**场景核对50种子中3个种子两侧场景不同**，已披露并做47种子敏感性 | `results/task6/t6.1-eval-sim-s*`、`results/task6/t6.1-eval-gz-s{0,1-r2,2}`；下文§9 |
| §10 汇总 | 完成，待Claude复核 | `results/task6/t6.1-summary/{comparison,manifest}.json`；下文§10 |

## F0早期读数（§6.5填写；D15评估，50种子成功率）

| 种子 | 15万步 | 30万步 |
|---|---|---|
| 0 | 32 | 25 |
| 1 | 26 | 25 |
| 2 | 28 | 25 |

**临时读数（2.5万步首次D15评估，50种子3001–3050内部成功数；2026-10-12 15:57读取，只作健康确认，不是§6.5/§7要求的15万、30万步读数，不据此下结论）**：F0 s0/s1/s2＝18/20/20；F1＝4；F2＝26；F3＝23；F4＝20；F5＝19；F6＝4（F1、F6每10步更新1次，2.5万步仅约2400次更新）。后续各检查点读数由`status.py`与`results/task6/<run-id>/screening_step*.json`获得。

## 筛选表（§7填写）

| 组 | 2.5万 … 15万 | 30万 | 与F0差（15万/30万，95%区间） |
|---|---|---|---|
| F0、F1–F6 | 见下文“§7 筛选表与Claude门槛”（Claude填写） | | |

## 交接

- 目标与授权：见[TASK](TASK.md)与父[task6](../TASK.md)。
- 当前负责人：Claude子Agent（临时，2026-10-12 15:02起）；Codex额度恢复后接回；Claude主会话负责§7门槛与复核。
- 原task6的预检证据（`results/task6/baseline_source_diff.json`、`t6-preflight-r1`、`t6-d12-preflight-r1`）作为参考保留；本节点§1须重新核查。
- 下一步：Claude复核§9–§10（尤其3个场景不一致种子）；如需确认F1/F6/F2按§8另行启动；Codex恢复后接回。

## §1–§2 实际记录（2026-10-12）

基线54项逐一重算，无差异（D13历史限制保留）。`forem-dev`仅保活，task5两容器存在，task6.2容器未出现；未操作任何其他任务进程。根main有大量既有未提交修改，保留。证据与来源登记将在本轮回归完成后同步。

修改：`scwm_env.py`、`task3_env.py`、`scwm_train.py`、`scwm_eval.py`、`scwm_instance.py`、`scwm_supervise.py`，D12仅`modulation/utils.py`两处；新增`husky_analytical.launch`与`tests/test_task6_sim.py`。原文本冻结于`results/task6/t6.1-baseline/original/`。逐处sha256/diff/理由见`source_diff_vs_task48.json`。D14尚未写入。

单测命令：`sg docker -c 'forem/docker/run.sh exec python3 -m unittest discover -s tests -p test_task6_sim.py -v'`；RED退出1（D12阈值不生效、world参数未实现），GREEN退出0（5/5）。初次尝试容器工作目录`/workspace/forem`错误退出127；直接运行run.sh无docker组权限退出1；核对真实挂载后统一`sg docker -c`。全部实际失败保留在日志，不当通过。

推荐Codex GPT6.1sol / Claude Sonnet5.5，medium（跨环境分支与逐位回归）；实际精确部署型号/强度未知。§3–§10尚未执行，无长训PID。

## §2 回归失败及交Claude（2026-10-12T09:39:33.938568+08:00）

来源：[SRC-0230](../../../SOURCES.md#src-0230)。

实际命令：容器入口均为`sg docker -c 'forem/docker/run.sh exec bash -c "OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python3 -m unittest discover -s tests -p test_task3\*.py -v"'`（task4/scwm分别替换pattern）。只为短回归限制库线程，未据此选择正式训练线程或宣称优化收益。

|回归|实际退出码|结果|日志|
|---|---|---|---|
|task3|1|76 tests；1 failure；3 skips|`logs/task6/t6.1-baseline/regress_task3.log`|
|task4|1|159 tests；2 failures；4 errors；1 skip|`logs/task6/t6.1-baseline/regress_task4.log`|
|scwm|0|23 tests，全通过|`logs/task6/t6.1-baseline/regress_scwm.log`|

具体失败（未修改或绕过）：

- `test_contract_covers_create_env_keys`：`audit_task3_core.py::OPTIONAL_SOFT_KEYS`不含已批准D12的`max_close_steps`，断言剩余集合`{'max_close_steps'}`。这是审计合同失败，不能说Gazebo运行行为已失败或通过。
- `test_original_101_and_102_supply_official_disparity_windows`：seed101/102两个子断言缺`results/task4/t4.3.1-tracker-evidence/probe-histogram`及/或旧exact_manifest。
- `test_actual_six_rpy_command_normalized_without_changing_command`：缺`t4.3.1-init-r2/public_draws.json`。
- `test_real_immutable_baseline_and_declared_delta`、`test_acceptance_and_all_330_hashes`：缺`t4.1-protocol-20261007-r1/task3_accepted_freeze.json`。
- `test_imu_absolute_orientation_not_used`：缺`t4.1-protocol-20261007-r1/references/open_vins/ov_msckf/src/ros/ROS1Visualizer.cpp`。

Claude下一步须决定：D12审计可选键的必要适配是否放行；旧VIO/接受freeze证据依赖如何处理，以及哪些回归属于本门槛。Codex不自行删测试、skip、修改合同或恢复旧证据。实现保留可审阅diff；D14、sim启动、等价性、冒烟/profile及正式训练均尚未执行。无本任务长训监控/停止操作。父task6和task6.2文档未修改。

2026-10-12T09:40:09.186154+08:00 scwm回归已退出0，23 tests通过（含FakeEnv预算/续训、SAC与WM单元测试；这是原测试范围，不是新WM实验）。完整命令/日志sha256/当前源码sha256收据：`results/task6/t6.1-baseline/regression_receipt.json`。临时单测run-id（如full/part）由既有测试使用，位于容器`/tmp/scwm_loop_*`，不是正式训练或task6证据run-id。§2仍不通过；没有sim/Gazebo启动、profile或正式run。


## Claude审核 R1（2026-10-12）

- §1–§2实现审核通过：sim分支门控正确，Gazebo缺省路径不变，D12两处实现符合R2。
- 决策见[TASK D18/D19](TASK.md#claude审核r1决策2026-10-12d18回归门槛d19安全性能优化)：放行`audit_task3_core.py`的`max_close_steps`可选键；task4的6项旧证据失败用`original/`源码重跑核对后记为既有环境失败；性能优化按D19三类执行（D17作废）。[SRC-0232](../../../SOURCES.md#src-0232)
- 放行：完成D18后继续§2回归→§3→§4→§5。

## D18实际复核 2026-10-12T09:49:37.026739+08:00

按[SRC-0232](../../../SOURCES.md#src-0232)将audit_task3_core.py OPTIONAL_SOFT_KEYS加max_close_steps并注明D12缺省规则。task3回归退出0：76 tests，3原skip。完整task4套件在当前树和临时副本各跑159项，均退出1：2 failures、4 errors、1原skip；6项错误栈只归一化临时根路径后完全相同（包含缺失证据路径），其余测试通过。没有删除/skip任何测试，没有恢复旧证据。临时副本复制scripts/tests/config/src，并以original/冻结源码覆盖；results仅只读引用现有树。命令、临时路径、sha256见d18_original_receipt.json；逐项错误栈见d18_task4_comparison.json，日志regress_task3_D18.log、task4_{original,current}_D18.log。§2按D18通过，允许进入§3。新来源条目在本阶段结束登记。

## §3 实际结果与交接（2026-10-12T09:51:58.861198+08:00）

依据：[SRC-0233](../../../SOURCES.md#src-0233)。D18实测及§3命令、退出码、sha256统一见`results/task6/t6.1-equiv-r1/receipt.json`。

- 启动容器`forem-dev`本任务实例k10，ROS11410，run-id `t6.1-equiv-r1`；启动退出0，3.1秒ready，仅analytical MoveIt，无Gazebo/控制器/costmap/pose_bridge。启动身份supervisor容器PID2408006、root2408007（历史，已停止），记录`logs/task6/t6.1-equiv-r1/inst10/launch.json`。
- 原参考实例hash与Task4.8三种子最终验证101–105共15条episode_hash全部一致；比较数据见equivalence.json的task48_sampler_crosschecks。
- 101–110各reset一次：目标tip/wrist、规划关节、障碍名称/尺寸/位姿一致；底盘位置和yaw差均0；**10/10障碍几何不一致**。差异仅geometry：sim中部分`ObjectGeometry.CYLINDER`，Gazebo参考为`RECTANGLE`。seed101共6个差异/16障碍；全seed数量见receipt.json，逐字段见obstacle_diff.json。采集/比较进程退出1，不能标通过。
- 根因静态核查：`map.py:871–876`的原始分支让Gazebo强制矩形，sim按已抽random选择矩形/圆柱。文件未改。不是浮点取整/起点物理偏差，也没有把几何字段从比较中排除。
- 按§3门槛停止：§4 D14尚未写入、§5 D19各类实测尚未执行、§6–§10未开始。没有F0/筛选训练、没有优化收益或工期结论。
- 已按身份仅停止自己的k10：stop退出0，residue=[]，ROS/Gazebo保留端口释放。最终forem-dev只init/sleep。未改父task6、task6.2文档，未操作它们及task5容器/进程。

Claude下一步：决定本对照应如何保持障碍几何一致，并明确最小允许改动与合同；Codex不自行改抽样器、开fake_gazebo或放宽场景等价门槛。已交付D18审计必要改动与实测收据，保留先前失败历史，未提交/推送。推荐GPT6.1sol/Sonnet5.5 medium（跨world场景语义核对），实际配置未知。


## Claude审核 R2（2026-10-12）

- D18复核与§3执行审核通过：task4六项错误栈在原始源码下逐项相同，按D18记为既有环境失败；§3几何失败的根因判断正确（上游`map.py` L871–876），没有放宽门槛，处理正确。
- 决策见[TASK D20](TASK.md#claude审核r2决策2026-10-12d20障碍几何)：sim中通过ROS参数`/forem/force_rectangle_obstacles`强制矩形障碍，`random()`保持第一个操作数；配单元测试；用`t6.1-equiv-r2`重做§3。[SRC-0235](../../../SOURCES.md#src-0235)
- 放行：实现D20 → §2回归（含Gazebo路径）→ §3 r2 → §4 → §5。

---

## Claude子Agent接手记录（2026-10-12T15:02起；日志[20261012-claude-task6.1.md](../../../agent_logs/task6/task6.1/20261012-claude-task6.1.md)）

实际执行者：claude-sonnet-5-5（Claude子Agent，由Claude主会话派发；推理强度未知）。原因：Codex额度耗尽（用户通知）。推荐模型/强度仍按[TASK](TASK.md#模型与推理强度推荐)（GPT6.1sol/Sonnet5.5，medium），推荐不等于实际配置。

### 对Codex在R2之后（约10:50–11:01）完成但未写入RESULTS的工作的复核

复核方式：对照`results/task6/t6.1-baseline/original/`冻结文本读完整diff；在forem-dev重跑全部相关测试；做一项新增的循环级逐位核验。结论按项如下（全部为子Agent实测，待Claude主会话复核）。

|项|复核结果|证据|
|---|---|---|
|D20（map.py L54、L872；scwm_env/scwm_train/scwm_eval写manifest、`--world sim`设参数、Gazebo断言）|与TASK D20一致：`random() < 0.5`仍是`or`链第一个操作数（RNG消耗不变）；新参数`/forem/force_rectangle_obstacles`缺省False；`ScwmEnv`在sim分支创建env前`rospy.set_param(...,True)`并在manifest写`force_rectangle_obstacles: true`；Gazebo分支断言参数不存在或为False，不设置参数。冻结的`original/map.py`与`husky/`快照`map.py`一致（`diff`无差异）。|diff读取；`tests/test_task6_geometry.py`4/4；`logs/task6/t6.1-claude-verify/geometry.log`|
|D14缺省与原行为逐位等价|(a) 单元：`test_default_bitwise_frozen_updates`比较当前`ScwmSAC`与冻结`original/scripts/scwm_sac.py`在相同输入的5次更新，输出与完整训练状态逐位相同；(b) **子Agent新增的循环级核验**：分别用当前脚本与`original/`冻结脚本，在CPU、FakeEnv、`plain.yaml`缩小预算、种子3下训练500步，250/500步检查点的agent状态（网络、优化器、α、调度器、RNG、计数）、replay全部数组、验证记录逐位相同。|`tests/test_task6_d14.py`；`results/task6/t6.1-claude-verify/loop_equiv/`（compare.py输出：state与replay identical，validation true）|
|D14开关数学行为|`update_every_env_steps=10`：1000个环境步恰好100个更新时机（实际更新仍受`len(replay)>batch`约束）；`alpha_rule=rllib`：初值α=1.0，无上限、不冻结，熵优化器学习率在0、50万、100万环境步为1e-4、5.05e-5、1e-6；`lr_schedule=linear_env_steps`：actor/critic同一线性规则；开启后不再步进指数调度器；`random_warmup_steps: 0`经协议直接生效；F5经D12键`max_close_steps: 50`。F2/F3/F6的视界固定1,000,000环境步（代码常量，筛选只跑30万步，前30万步与B一致）。|`tests/test_task6_d14.py`；`results/task6/t6.1-baseline/d14_diff.json`（含与B源码位置的对应及已知差异）|
|协议文件`config/task6/screen_F0..F6.yaml`|与`config/task4_scwm/plain.yaml`逐文件`diff`：除添加`max_close_steps`、D15 `screening`块（25000步一次、30万步后每5万步、种子3001–3050）外，F0无训练项改动；F1仅`update_every_env_steps: 10`；F2仅`alpha_rule: rllib`；F3仅`lr_schedule: linear_env_steps`；F4仅`random_warmup_steps: 0`；F5仅`max_close_steps: 50`；F6为F1–F5全部（`update_every_env_steps: 10`、`rllib`、`linear_env_steps`、`random_warmup_steps: 0`、`max_close_steps: 50`）。|`diff`输出；`config/task6/`|
|续训测试中被Codex改动的断言|`test_full_loop_all_switches_resume_with_d15`：首轮因replay元数据`meta_t_obs/meta_t_cmd/meta_t_next`失败，Codex改为这三个时间戳数组不比较。**子Agent判断：接受。**理由：这三列是FakeEnv自身的仿真时钟，续训重启后新FakeEnv时钟从0开始，与真实续训时新ROS实例的时钟同样重新计时；plain训练不读取它们（更新只用地图、机器人状态、动作、回报、mask）；测试仍逐位比较agent全部状态（网络、优化器、α、调度器、RNG）、更新计数、`next_screen`、以及replay的其余全部数组（地图、状态、动作、回报、mask、episode_id、step_in_episode、epoch、done）和3个screening文件；因此没有掩盖训练相关差异。首轮失败日志`logs/task6/t6.1-baseline/d14_full_loop.log`保留。|测试源码；`logs/task6/t6.1-claude-verify/d14.log`6/6 OK|
|回归|子Agent在forem-dev重跑：test_task6_sim 5/5；test_task6_geometry 4/4；test_task6_d14 6/6；scwm 23项（129 s）；task3 76项（3原skip）；task4 159项仍为2 failures+4 errors+1 skip，错误名称与D18清单完全相同（缺失旧VIO/接受freeze证据路径），按D18记为既有环境失败。未删除/skip测试。|`logs/task6/t6.1-claude-verify/{sim,geometry,d14,scwm,task3,task4}.log`|
|`t6.1-equiv-r2`|已完整：`equivalence.json` `all_pass: true`。10个种子（101–110）每个：障碍（名称、几何、尺寸、位姿，6位小数）、`goal_tip`、`goal_wrist`、规划臂初始关节与Gazebo参考完全一致，基座位置差0 m、偏航差0 rad；160个障碍几何全部为矩形；15/15（Task4.8三种子最终验证101–105）`episode_hash`与Task3参考一致；D20开/关对照10/10（除几何外位置、尺寸、目标、起点及采样后的RNG状态逐位相同）。|`results/task6/t6.1-equiv-r2/equivalence.json`；`logs/task6/t6.1-equiv-r2/`|
|遗留进程|Codex遗留的实例k=10（ROS 11410，run `t6.1-equiv-r2`，roslaunch/rosmaster/rosout/move_group共约6个空闲进程）仍在forem-dev运行。子Agent尝试用`scwm_instance.py stop --inst 10`停止，被自动模式权限分类器拒绝，未绕过。不影响本任务（本任务用实例0–8；性能测试用20–44，已停止）。需主会话/用户决定是否停止。|`docker top forem-dev`|

### 源码哈希（训练run实际使用）

`results/task6/t6.1-baseline/source_diff_r2_claude.json`：F0-s0 `run_manifest.json`中19个sources与Task4.8 plain-s0 manifest逐项比对，**仅6个文件不同**：`scripts/scwm_env.py`、`scwm_sac.py`、`scwm_train.py`、`scripts/task3_env.py`、`modulation/envs/map.py`、`modulation/utils.py`，均已复核（sim分支、D14、D12、D20）；其余13个相同（`config/task3/{sac,task_contract}.yaml`、`scwm_clock/feedback/policy/wm`、`model.py`、`combined_env.py`、`eeplanner.py`、`robotenv.py`、`sac.py`、`robot_env.cpp`、`husky_core.launch`）。注意：Codex生成的`source_diff_vs_task48.json`、`d14_diff.json`中的`after_sha256`早于其11:01的最后一次`scwm_train.py`修改，不再对应当前文件；以训练run的manifest和上述新文件为准。

## §5 冒烟、profile与并行方案（子Agent，2026-10-12 15:05–15:34）

### 冒烟（`t6.1-smoke-r1-F0`、`-F6`）

种子0，`--world sim`，F0/F6各5000步（分两段：先2600步，再`--resume`到5000步），D15评估间隔临时2500步，F0用cuda:0、F6用cuda:1，验证每5000步。协议为`logs/task6/t6.1-smoke-r1/F{0,6}_smoke.yaml`（与`screen_F{0,6}.yaml`仅screening间隔不同）。结果：均走到5000步，退出码0，`train_summary.json` steps=5000（F0 updates 4743）；D15评估50 episode各执行2次（2500与5000步；resume后`next_screen`正确恢复），无error；记录的`physical`为`{valid:false, success:null, reason:"sim: no physics"}`；train.out中"gazebo"出现0次（无Gazebo服务调用）；manifest含`world: sim`、`force_rectangle_obstacles: true`、`resumed`；种子101首个验证episode的`episode_hash`与Task4.8一致（41148eed…）。F0 5000步内部成功：D15 5/50、6/50，F6：2/50、4/50（未训练的早期读数，只作冒烟，不作结果）。

### profile（`results/task6/t6.1-perf-r1/*.json`；脚本`scripts/bench_task6_perf.py`）

方法：协议为F0/F1去掉D15评估的版本（`protocol_F{0,1}_noscreen.yaml`），监督运行4000步，取第2–4个1000步窗口（丢弃首窗口）的步/秒与分阶段耗时；每run的CPU核数＝训练进程及其ROS进程树的`/proc` utime+stime之和除以测量墙钟。多个案例在不同GPU上同时测，彼此共享主机CPU（当时主机负载约10–18）；每个案例仅1个样本，run-to-run波动约±2%（K=1重复三次23.1–23.5）。

|案例|每GPU条数|每run步/秒|总步/秒|每run CPU核|update ms/步|env_step ms|reset ms/episode|
|---|---|---|---|---|---|---|---|
|F0 K=1，默认线程（容器环境`OMP_NUM_THREADS=2`）|1|23.1|23.1|1.71|19.3|14.7|566|
|F0 K=1，线程=1|1|23.5|23.5|1.72|19.0|14.5|573|
|F0 K=1，线程=2|1|23.5|23.5|1.72|19.3|14.4|562|
|F0 K=1，ROS进程绑核8–11|1|24.4|24.4|1.73|17.7|14.4|563|
|F0 K=1，`--cudnn-benchmark`|1|23.7|23.7|1.72|18.4|14.5|561|
|F0 K=2同GPU|2|22.4/23.1|45.4|1.69/1.72|20.0|14.5|531–570|
|F0 K=3同GPU|3|21.1/21.4/21.0|63.5|1.66|22.5|14.5|529–567|
|F0 K=4同GPU|4|18.8/19.2/19.1/19.1|76.1|1.60|26.8|14.5|532–565|
|F1 K=1（每10步更新1次）|1|39.0|39.0|2.18|2.0（含无更新步）|14.4|564|

其余阶段：select 1.1 ms（K=1）…2.8 ms（K=4）、push 0.3…1.0 ms。K=1单步约43 ms：update 19（44%）、env_step 14.5（34%）、reset均摊约10（22%，约58步/episode时）。

update路径微基准（`scripts/bench_task6_update.py`、`prof_task6_update_ops.py`，合成数据，真实网络尺寸，`update_micro_*.json`、`update_ops_profile.json`）：eager每次更新中位17.3–17.8 ms；torch.profiler显示每次更新约1029次`cudaLaunchKernel`（CPU端约4.3 ms，profiler下）；GPU核时间约5 ms，即CPU发射受限（与Task4.8的profile结论一致）。

### D19逐项结论

|类|项|实测|结论|
|---|---|---|---|
|一类|同GPU打包|见上表：2条每run−3%，3条−10%，4条−19%；总吞吐随条数增加（45→64→76）|采用，但F0每GPU只放1条F0＋至多1条筛选run；第4块GPU放3条较轻的筛选run|
|一类|线程数|1/2/默认(2)：23.5/23.5/23.1 步/秒，差异在波动内；CPU/run约1.7核|不改线程；沿用容器默认（`OMP_NUM_THREADS=2`）|
|一类|CPU亲和|ROS进程绑核8–11：+3.7%（24.4 vs 23.5），仅1个样本且与其他案例同时运行|不采用：增益不超出竞争波动；固定绑核可能与同机task5/6.2的进程争用同一批核|
|一类|去掉GPU→CPU同步（`update_from_batch`不转float）|微基准17.25 vs 17.34 ms（0.5%）|不采用：无实质收益|
|一类|检查点/replay落盘降频或异步|`checkpoint`事件`wall_s`：5000步时0.55 s（replay npz约20 MB）；按线性外推100k步约11 s/20k步，占墙钟约1%|不采用：<1%，且降频会增加崩溃后重做量；默认每2万步存盘|
|一类|D15评估异步（独立sim实例）|**实测评估开销**：冒烟82–130 s/次；真实训练25000步的首次D15评估：F0三条214–238 s，F3 205 s，F5 214 s，F1 101 s，F6 82 s（策略开始成功后episode更长）。按此，F0全程26次评估≈1.7 h（约12%），30万步筛选12次≈0.7 h（15–18%，F1/F6≈11%）。**一次性等价核验**（`logs/task6/t6.1-claude-verify/async_eval_check.sh`）：取F1筛选run的25027步D15快照`screen_policy_step00025027.pt`，在独立sim实例（inst 50，cuda:3）用`scwm_eval.py --world sim`对同样50个种子评估，与训练内联结果比较：50个episode的steps、done、capped、internal_success、ee_done、IK失败、碰撞、truncated、episode_hash全部相同（0项差异，内部成功均为4/50）；仅`return_`有浮点差异（最大相对3.1e-4，GPU非逐位确定）。评估外移本身可行|**核验可行，但对本批run未启用**：训练run已于15:35启动，启用需新增“只存快照”开关（改`scwm_train.py`→源码哈希变化→不能续训，须新run-id重开）与常驻评估器，实现加验证约1–1.5 h，而此时重启会丢掉同等进度，净收益≈0。建议在§8确认训练或后续长训开始前由Codex/Claude决定是否实现；评估位置不改变训练（RNG已被D15保存恢复）。|
|二类|`torch.compile`（default，critic/critic_target的forward与`policy.sample`）|update中位16.7 ms vs eager 17.8 ms（−6%）；更新0的损失相对差0.667（编译后的采样随机数流与eager不同），200次更新后最大损失相对差0.667、动作差0.12|未过等价门槛，且提速远低于15%：不启用|
|二类|`cudnn.benchmark`|更新微基准17.54 vs 17.55 ms；端到端23.7 vs 23.1–23.5（≈+1%）|提速远低于15%：不启用|
|二类|CUDA Graph|未实施。原因：①`update_from_batch`含主机端数据相关分支（`self.alpha <= self.min_alpha`）和逐次`float()`；②Adam须改`capturable=True`，其`step`以张量计算，舍入与现行Python标量路径不同；③F3每步改学习率需重捕获|不启用|
|三类|AMP、TF32、改步长/批大小/更新次数/观测/奖励/终止、减评估|未触碰|—|

**发现（需Claude知晓）：D19二类的字面等价门槛“同一初始状态和同一串256批数据连续200次更新，各步损失和最终参数最大相对差≤1e-4”在现行eager路径上本身无法满足。** 同一输入下两次eager运行（`base`与`base_repeat`）：第0次更新损失相对差约8e-8–1e-7，但200次更新后损失相对差0.4%–0.6%，参数逐张量相对L2差0.3–0.5，动作最大绝对差0.019–0.026（cudnn卷积反向非逐位确定，随更新数混沌放大）。`nofloat`和`cudnn.benchmark`与eager的差异在同一量级。因此该门槛只能用逐位确定的参考来评价；我没有放宽门槛，也没有为通过而改变测试。二类优化均因提速不足而未启用，该门槛问题没有影响任何运行。

### 并行方案与时长估计

- 每GPU：g0＝F0-s0＋F2；g1＝F0-s1＋F3；g2＝F0-s2＋F4；g3＝F1＋F5＋F6（F1、F6每10步更新一次，GPU负载轻）。实例号：F0为0/1/2；F1…F6为3…8。线程、亲和不设置（容器默认）。
- 主机CPU：9条run合计预计约16–17核（F0≈1.7核/条，F1/F6≈2.2核/条），低于56核预算；启动时主机负载约10–12核（task5 trainer、task6.2遗留及他人进程）。
- 墙钟估计（训练速度来自随机策略早期窗口，D15评估开销来自首次真实评估214–238 s/次；学会后episode变长会改变reset占比；到15万步前不作承诺）：F0每条约22.7步/秒→100万步≈12.2 h，加D15评估约1.7 h、验证与存盘约0.2 h，**约14 h**；F1/F6约2.6 h；F2/F3/F4/F5约4.4 h（每步更新，同GPU两条）。F0三条与筛选同时开跑。
- 未来的确认训练（§8）：同一方案，每组3条×100万步，估计约13 h（若各占一块GPU）。

## §6 启动与监控（2026-10-12）

启动命令（宿主，`logs/task6/t6.1-launch/launch.sh RUN_ID INST SEED GPU STEPS 协议名`，内部为`sg docker -c 'docker/run.sh bg python3 -u scripts/scwm_supervise.py --world sim --inst INST --run-id RUN_ID --seed SEED --device cuda:GPU --steps STEPS -- --config /root/mm_husky_ws/config/task6/协议名.yaml'`，由`docker exec -d`脱离当前shell，监督器管理实例与续训）：

|run-id|协议|种子|GPU|实例/ROS端口|步数|启动（+08:00）|
|---|---|---|---|---|---|---|
|`t6.1-sim-plain-s0`|screen_F0|0|cuda:0|0 / 11400|1,000,000|15:34:53|
|`t6.1-sim-plain-s1`|screen_F0|1|cuda:1|1 / 11401|1,000,000|15:34:53|
|`t6.1-sim-plain-s2`|screen_F0|2|cuda:2|2 / 11402|1,000,000|15:34:53|
|`t6.1-scr-F2-s0`|screen_F2|0|cuda:0|4 / 11404|300,000|15:35:17|
|`t6.1-scr-F3-s0`|screen_F3|0|cuda:1|5 / 11405|300,000|15:35:17|
|`t6.1-scr-F4-s0`|screen_F4|0|cuda:2|6 / 11406|300,000|15:35:17|
|`t6.1-scr-F1-s0`|screen_F1|0|cuda:3|3 / 11403|300,000|15:35:17|
|`t6.1-scr-F5-s0`|screen_F5|0|cuda:3|7 / 11407|300,000|15:35:17|
|`t6.1-scr-F6-s0`|screen_F6|0|cuda:3|8 / 11408|300,000|15:35:17|

除`--config`外未加训练参数（Task4.8 plain的manifest显示`window_s`为空、无fork，协议为默认`plain.yaml`；其监督命令行本身未留存，未发现额外训练参数的记录）；检查点每2万步（默认），验证（101–105）每10万步（默认），D15评估见协议。F0的D15评估在30万步内每2.5万步、之后每5万步；筛选run同样（只到30万）。

监控：宿主`python3 logs/task6/t6.1-launch/status.py`（只读，列出每条run的步数、步/秒、最近D15/验证结果、重启次数）；原始：`logs/task6/<run-id>/{progress,events,episodes}.jsonl`、`supervisor.log`、`train.out`；结果`results/task6/<run-id>/`（`screening_step*.json`为D15逐episode记录；`validation_step*.json`；`ckpt/`）。
停止：对监督器进程发SIGTERM（`sg docker -c 'docker exec forem-dev pkill -TERM -f "scwm_supervise.py.*--run-id <run-id>"'`），训练器会存检查点后退出，监督器随后停实例；**只停自己的run，不碰其他容器**。恢复：用同一启动命令重新运行`launch.sh`（监督器见到manifest自动`--resume`；源码、配置哈希必须不变，否则拒绝续训）。**运行期间不得修改`scripts/scwm_{env,sac,train}.py`、`task3_env.py`、`map.py`、`utils.py`、`config/task6/screen_F*.yaml`。**



## Claude审核 R3（2026-10-12 16:0x，子Agent交付后）

- **核实结论接受**：Codex在R2后的D20/D14未记录工作经子Agent逐项diff与重跑复核，结论成立；新增的500步循环级逐位核验加强了D14缺省等价的证据。续训测试中不再比较FakeEnv时钟元数据`meta_t_*`的改动可以接受（plain训练不读这三列，其余训练数组/RNG/计数仍逐位比较）。`t6.1-equiv-r2` all_pass，§3通过。
- **§5与运行**：一类优化只采用同GPU打包（每GPU一条F0加至多一条筛选，第4块GPU放F1/F5/F6），其余实测无显著收益未采用，处理正确。9条run 16:01核查均在推进、0重启；主机负载约30核，在56核预算内。
- **D19二类门槛**：子Agent发现字面门槛（200次更新后相对差≤1e-4）连现行eager路径自身两次运行都满足不了（cudnn反向非逐位确定，被训练放大）。本批二类均因提速不足未启用，对运行无影响。决定：本阶段不追CUDA Graph；若§8需要压工期，再把门槛改为“与eager自身重复运行的差异同量级”并另行审核。
- **异步D15评估**：等价核验已完成（离散结果0差异），但启用要改源码，会使正在运行的run无法续训。推迟到§7门槛时，与§8确认训练一并决定。
- **知悉**：子Agent列出的不在F1–F6内的剩余差异（Adam eps 1e-8对1e-7、critic MSE对Huber、单进程replay对20 worker）作为F6也救不活时的候选，届时由Claude设计并须用户同意。
- **2.5万步健康读数**（只作健康确认，不是§7读数）：F0三种子18/20/20（/50），F1与F6各4，F2–F5为19–26。F1/F6按环境步计的更新次数只有十分之一，早期偏低属预期。F0在sim中2.5万步已有约四成内部成功，而Task4.8在Gazebo中100万步内训练成功率一直约6–7%；这一对比须到15万/30万步再判断。
- **遗留实例k=10**（Codex的`t6.1-equiv-r2`，ROS 11410，空闲）：子Agent停止时被权限拦截，未绕过。是否停止交用户决定。
- 下一步：Claude在F0到15万步（约6.5 h后）时读数；筛选全部完成后做§7门槛。


## §7 筛选表与Claude门槛（2026-10-12 21:1x，Claude主会话）

数据：各run的`results/task6/<run-id>/screening_step*.json`（D15，50个固定种子3001–3050，内部成功数/50），Claude重新统计。筛选6条均正常跑完30万步、退出码0（`supervisor.log`：restarts=0；`status.py`显示的restarts=1是结束计数的显示问题）。

| 步数 | F0-s0 | F0-s1 | F0-s2 | F1 | F2 | F3 | F4 | F5 | F6 |
|---|---|---|---|---|---|---|---|---|---|
| 2.5万 | 18 | 20 | 20 | 4 | 26 | 23 | 20 | 19 | 4 |
| 5万 | 22 | 24 | 25 | 6 | 17 | 20 | 21 | 22 | 6 |
| 7.5万 | 23 | 21 | 23 | 12 | 17 | 22 | 22 | 20 | 9 |
| 10万 | 23 | 20 | 24 | 18 | 23 | 23 | 25 | 20 | 20 |
| 15万 | 32 | 26 | 28 | 27 | 22 | 29 | 28 | 23 | 30 |
| 20万 | 22 | 20 | 32 | 29 | 18 | 29 | 24 | 22 | 33 |
| 25万 | 25 | 21 | 23 | 29 | 13 | 24 | 23 | 19 | 28 |
| 30万 | 25 | 25 | 25 | 23 | 12 | 19 | 23 | 21 | 28 |
| 22.5–30万均值 | 0.52 | 0.45 | 0.48 | 0.57 | 0.29 | 0.49 | 0.46 | 0.40 | 0.58 |

D16（相对F0-s0，Newcombe 95%区间）：15万步F1 −0.10 [−0.28, 0.09]、F2 −0.20 [−0.37, −0.01]、F3 −0.06、F4 −0.08、F5 −0.18 [−0.36, 0.01]、F6 −0.04；30万步F1 −0.04、F2 −0.26 [−0.43, −0.07]、F3 −0.12、F4 −0.04、F5 −0.08、F6 +0.06 [−0.13, 0.25]。

**结论（单种子筛选，只作诊断）**：
1. **F0在sim中学得会**：Task4.8训练器原样放到sim（全矩形障碍、`max_close_steps` 500），三个种子15万步起内部成功约0.45–0.65，平台约0.5。Task4.8在Gazebo中100万步训练成功一直约6–7%、最终验证0/15。按TASK解读表，训练参数不是Task4.8失败的主因，主因在Gazebo执行条件。
2. **没有哪个B参数能显著提升**：F1（每10步更新）与F6（全部换成B）后期均值约0.57–0.58，略高于F0的0.45–0.52，但区间都含0；F1/F6早期慢，是按环境步计更新次数只有十分之一。
3. **F2（只换B的α规则）明显更差**：15万、30万步的区间都不含0，且越训越差（0.24）。单独用B的α规则在ScwmSAC中有害；与F6对比说明它要与B的其他设置（如更新频率）配合。
4. F0平台约0.5，低于R-B的0.76–0.82；两者场景（全矩形对约一半椭圆柱）和评估口径都不同，不能直接相减。

**门槛决定**：§8确认训练暂不启动。理由：本任务要回答“哪个训练参数导致Task4.8失败”，筛选已表明F0本身在sim中就能学会，确认F1–F6的细小差异对这个问题帮助有限。F0三种子继续跑到100万步，并按§9做两侧最终评估。若用户希望确认F1/F6的小幅提升或F2的退化，再按§8启动对应组。


---

## §8 确认训练

按Claude §7门槛决定**不启动**，无`t6.1-conf-*` run。

## §9 最终评估（Claude子Agent，2026-10-13 10:08–11:10+08:00；run-id `t6.1-eval-sim-s{0,1,2}`、`t6.1-eval-gz-s{0,2}`、`t6.1-eval-gz-s1-r2`）

### 9.1 F0三条的最终状态（核实）

三条的`supervisor.log`均为1次`trainer ended: exit rc=0`、`supervisor end: done=True stop=None`；`train_summary.json` steps=1,000,000、updates=999,743、episodes 3855/3869/3842、wall约12.7 h；`ckpt/policy_step01000000.pt`存在；manifest的19个sources哈希与当前文件一致，无`resumed`（从未续训），配置哈希4cbb1dad…。`status.py`的“restarts=1”是对“trainer ended”行的计数（正常结束那一次），实际失败重启0。核实时`docker top forem-dev`只剩init/sleep，监督器和sim实例均已退出。同样核实筛选6条：各1次rc=0正常结束，0失败重启。

### 9.2 评估设置

- 脚本`scripts/eval_task6_final.py`（新增；评估循环与`scwm_eval.py`相同，复用`scwm_train.run_eval`，确定性动作，每种子1个episode，另存每个episode的`episode_spec`；错误种子仍留在分母中）。启动`logs/task6/t6.1-eval-launch/eval_one.sh`。种子2001–2050，分母固定50。
- sim侧：策略`results/task6/t6.1-sim-plain-s{0,1,2}/ckpt/policy_step01000000.pt`，`--world sim`（D20矩形障碍、`max_close_steps 500`，与训练一致），inst 63–65、cuda:0–2。
- Gazebo侧：`results/task4/t4s-plain-s{0,1,2}/ckpt/policy_step01000000.pt`，`--world gazebo`（默认路径，未设置`/forem/force_rectangle_obstacles`，`ScwmEnv`断言其缺省/False），inst 60–62。Gazebo实例日志在`logs/task4/t6.1-eval-gz-*/inst*`（`scwm_instance.py`默认路径）。
- **失败与重跑**：`t6.1-eval-gz-s1`的gzserver在第6个种子附近段错误（exit 139，`logs/task4/t6.1-eval-gz-s1/inst61/launch.log`），评估卡在`set_model_state_client_ failed`；已`kill -9`自己的评估进程，整个s1用新run-id `t6.1-eval-gz-s1-r2`重跑，首次尝试不计入（未完成、无`eval.json`，证据保留）。其余5条首次即完成，errored=0。

### 9.3 最终50-episode结果（种子2001–2050；内部成功＝`episode_is_success`；completed＝episode正常终止，capped＝跑满2000步未终止，errored＝异常）

| 侧 | run | 内部成功/50 | Wilson 95% | 物理成功 | completed/capped/errored | 碰撞episode | 含IK失败episode | 平均步数 |
|---|---|---|---|---|---|---|---|---|
| sim（F0） | s0 | 21 | [0.29,0.56] | N/A | 50/0/0 | 5 | 27 | 338 |
| sim（F0） | s1 | 22 | [0.31,0.58] | N/A | 50/0/0 | 3 | 27 | 314 |
| sim（F0） | s2 | 22 | [0.31,0.58] | N/A | 50/0/0 | 2 | 26 | 317 |
| **sim均值** | | **0.433** | | | | | | |
| Gazebo（Task4.8） | s0 | 2 | [0.01,0.13] | 0 | 50/0/0 | 0 | 48 | 406 |
| Gazebo（Task4.8） | s1（-r2） | 1 | [0.00,0.11] | 0 | 50/0/0 | 0 | 49 | 419 |
| Gazebo（Task4.8） | s2 | 5 | [0.04,0.21] | 3 | 50/0/0 | 0 | 45 | 455 |
| **Gazebo均值** | | **0.053** | | 0.020 | | | | |

同一策略类、同一训练器，在sim中训练并评估约0.43，在Gazebo中训练的策略在Gazebo评估约0.05（物理成功0.02）。这是描述性数字，样本为每侧3个种子×50个episode，不含显著性检验。

### 9.4 两侧场景一致性核对（`results/task6/t6.1-summary/comparison.json` `scene_consistency`）

比对方法同§3：障碍（名称、几何、尺寸、位姿，6位小数）、`goal_tip`、`goal_wrist`、规划臂初始关节完全一致，`base_tf`位置差≤0.02 m、偏航差≤0.02 rad；每侧三条评估各自的场景哈希在50个种子上完全相同（sim三条互同，Gazebo三条互同）；两侧障碍几何全部为`RECTANGLE`。

- **47/50个种子两侧场景完全一致**（基座位置差、偏航差0）。
- **3个种子（2006、2012、2021）两侧场景完全不同**：障碍（连第一个障碍的尺寸和位置）、目标、基座起点都不同，只有规划臂初始关节相同。这三个种子在sim与Gazebo各自重复评估时哈希稳定（sim三次一致，Gazebo三次一致），所以是“种子×world”的确定性差异，不是随机性。探针`scripts/probe_task6_scene_divergence.py`（`results/task6/t6.1-eval-probe-{sim,gazebo}.json`）重置这些种子，两侧`map_reset`/`draw_startpose_and_goal`调用次数都是1，哈希与评估中记录一致（2005、2007两侧相同，2006/2012/2021不同）。**根因未查明**：从障碍场的第一个障碍起就不同，说明这些种子上抽样随机数流在map生成之前或之中就已分叉；`map.py`中`np_random`被世界相关的分支影响的位置我只静态读过，没有找到确定原因。§3（种子101–110）10/10一致，本次约6%（3/50）不一致，属抽样器按world的差异，与D20（几何）无关（两侧几何都是矩形，开关开/关时随机数流在§3已证明逐位相同）。
- **敏感性**（只用47个两侧场景一致的种子）：sim三条内部成功20/47、20/47、22/47（均值0.440），Gazebo三条2/47、1/47、5/47（均值0.057），物理成功0/0/3；与50种子结论相同。详见`matched_scene_sensitivity`。
- 此项属PROCEDURE异常处理中的“场景不一致”，本次不影响训练（训练在sim用种子范围[1000,2³⁰)抽样），只影响最终评估两侧的可比性；是否追查根因、是否要求两侧场景逐种子相同由Claude决定。

### 9.5 F0与Task4.8逐点5种子验证（种子101–105，每10万步，内部成功/5；Gazebo格为“内部/物理”）

|步|F0-s0|F0-s1|F0-s2|T4.8-s0|T4.8-s1|T4.8-s2|
|---|---|---|---|---|---|---|
|10万|2|1|2|0/0|1/1|0/0|
|20万|3|3|2|0/0|0/0|0/0|
|30万|3|1|1|1/1|1/1|2/2|
|40万|2|2|4|0/0|2/1|1/1|
|50万|2|4|4|1/1|0/0|0/0|
|60万|0|3|0|0/0|0/0|0/0|
|70万|0|2|3|0/0|0/0|1/1|
|80万|0|2|3|0/0|0/0|0/0|
|90万|1|3|2|1/0|0/0|0/0|
|100万|1|3|2|0/0|0/0|0/0|

（5个种子样本太小，每格只能说明量级；Gazebo三条各10个检查点合计内部成功11/150，sim三条合计61/150。）F0的D15 50种子曲线（种子3001–3050；30万步内每2.5万步、之后每5万步，共26点）：s0 18,22,23,23,28,32,23,22,27,25,26,25,22,31,21,27,23,17,19,20,18,18,21,26,21,25；s1 20,24,21,20,26,26,27,20,21,21,23,25,22,19,21,22,22,20,22,20,22,19,19,20,25,24；s2 20,25,23,24,25,28,29,32,24,23,25,25,22,20,20,27,23,28,25,26,24,21,17,24,26,23（完整数据见`comparison.json` `d15_50seed_f0`）。F0的50种子读数在15万步后基本为20–30/50的平台，没有随训练上升的趋势；100万步最终2001–2050评估（21/22/22）与此一致。

## §10 汇总与交付（2026-10-13）

- `results/task6/t6.1-summary/comparison.json`（最终评估、场景一致性、47种子敏感性、5种子验证曲线、D15曲线）和`manifest.json`（9条训练run的源码sha256、配置sha、起止与监督器记录、重启次数0、协议文件sha、评估脚本sha、评估策略sha256、命令、GPU打包、偏差清单）由`scripts/summarize_task6_1.py`（容器内运行）生成。
- 源码与Task4.8的差异清单：`results/task6/t6.1-baseline/source_diff_r2_claude.json`（仅`scwm_env`、`scwm_sac`、`scwm_train`、`task3_env`、`map.py`、`utils.py`六处，均为sim、D12、D14、D20，Gazebo缺省路径不变）。
- 偏差清单：①D20使sim障碍全为矩形，与R-B（task5.2，约一半椭圆柱）不同；②sim下`max_close_steps`取500（D12）；③D15评估在训练进程内联执行（异步核验已完成但未启用）；④Gazebo评估实例日志位于`logs/task4/`下（`scwm_instance.py`默认路径）；⑤`t6.1-eval-gz-s1`因gzserver崩溃重跑为`-r2`；⑥3个种子（2006、2012、2021）两侧场景不一致（9.4）；⑦D19二类字面门槛对eager自身不可满足（见§5）。
- 资源：评估阶段最多同时6个实例（3个sim约1.7核/个、3个Gazebo约2核/个，合计约11–12核），评估时主机忙核约18，task6.2正式训练若启动（约30核）合计低于56核；评估全部结束后`forem-dev`只剩init/sleep。
- 新增论据见[SRC-0246](../../../SOURCES.md#src-0246)。未标done，等待Claude复核。


## Claude复核 R4（2026-10-13，§9–§10）

- **独立复算通过**：Claude从6份`eval.json`重新统计，结果与子Agent一致：sim F0内部成功21/22/22（/50，均值0.433）；Gazebo Task4.8内部成功2/1/5（均值0.053）、物理成功0/0/3（均值0.020）。另统计因20次IK失败终止的episode数：sim 18/21/20，Gazebo 48/49/45。三条F0退出码0、100万步、源码哈希一致，核实接受。Gazebo s1首次评估因gzserver段错误作废、以r2重跑，处理正确。
- **主口径**：以50个种子为主口径，47个两侧场景一致的种子作为敏感性分析（sim 0.440、Gazebo 0.057），两种口径结论相同。
- **遗留**：种子2006、2012、2021两侧场景从第一个障碍起就不同，根因未查。它不改变结论（3/50，敏感性分析一致），本任务不再追查；登记为待查问题，若后续实验需要逐种子配对的sim/Gazebo比较，须先查清。
- **结论**：同一组50个种子上，Task4.8训练器在sim中训练并在sim中评估，内部成功约43%；在Gazebo中训练并在Gazebo中评估，约5%（物理成功2%），且绝大多数episode因连续IK失败终止。训练参数筛选（§7）无显著影响。**Task4.8失败的主因在Gazebo执行条件，不在训练参数。**具体是Gazebo中的哪一项（每步时长约0.04 s、观测滞后、底盘加速斜坡、激光局部地图等），本任务未拆分。
- 状态：task6.1 done（单种子筛选与三种子确认的结论只用于诊断）。§8按门槛未启动。
