# task5.5 cbl自写SAC GPU版sim训练500万步 — 结果与交接

> **当前状态（2026-10-20 Claude复核）：done（训练5M×3种子与最终sim评估完成，入账经独立复核通过，见[复核节](#claude独立复核2026-10-20)）——以本节点RESULTS为准。** 本文件下方的状态行和“尚未执行/进行中/review”等表述是当时的记录，以本行为准。

状态：**done（最终sim评估10-19 22:52结束；10-20 Codex只读入账，同日Claude独立复核通过）**。仅sim内部成功；Gazebo零样本评估未做，需另行授权。

## 启动记录（2026-10-14，Claude，claude-opus-5-5）

- 前置：按用户要求先停止task5.4（见[task5.4 RESULTS](../task5.4/RESULTS.md)“用户要求停止”节）；forem-dev启动前仅sleep，4块GPU均空闲。
- 17:20:23 +08:00用`logs/task5/t5.5-launch/launch.sh`启动三条，三次rc0。supervisor.log：09:20:24Z三条`supervisor start … target=5000000`，实例0/1/2 `ready`（startup 3.1 s），`trainer resume=False`（从头）。
- 早期实测（3000步时，随机预热期刚过）：每1000步约42–45 s墙钟，即约23步/秒；分阶段均值env_step约13.7 ms、update约14.8 ms、reset约504 ms/回合；GPU0/1约3.7 GB显存、利用率约19%。与task6.1 F0（约22.7步/秒）一致。
- 墙钟估计（非承诺）：5M约60 h训练，另加D15评估（约100次）与验证，约2.7天。学会后回合变长会改变reset占比。

## 训练中读数

|步数|s0|s1|s2|task6.1 F0同步数|备注|
|---|---|---|---|---|---|
|1M|23/50|21/50|21/50|F0（1M）：25/24/23|D15内部成功（50种子3001–3050）；前1M学习率日程与F0相同|
|2.5M|21/50|23/50|18/50|—||
|5M|28/50|31/50|30/50|—|最后10个D15点（4.55M–5M）均值29.9/32.8/31.1（约62%）|

2026-10-16 08:49 +08:00只读读数（Claude）：s0/s1/s2分别3.253M/3.321M/3.250M步，已跑39.5 h，窗口约25–26步/秒，supervisor无重启。D15内部成功逐点（250k/500k/1M/1.5M/2M/2.5M/3M）：s0 19/20/23/19/22/21/24；s1 22/20/21/23/24/23/28；s2 25/21/21/24/16/18/17。250k以后基本持平在约40–50%，未见随步数明显上升（单次50场景，波动约±3–4）。

## 基线核实（2026-10-19，Claude，claude-opus-5-5，只读）

- **训练完成**：三条`supervisor.log`均为`trainer ended: exit rc=0`、`done=True stop=None restarts=0`（s0 10-16 21:53Z、s1 20:56Z、s2 22:16Z）；`train_summary.json` steps=5000000、updates=4999743、episodes 21589/22181/24045、wall 60.6/59.6/60.9 h。`ckpt/policy_step05000000.pt`、`state_05000000.pt`、`replay_05000000.npz`三条均在。forem-dev内已无`scwm_`进程，GPU0–3空闲。
- **配置**：`config/task5/cbl_sac_5m.yaml` SHA256=`62d2f9a2931bc3da…0203554cbc`，与`screen_F0.yaml`逐行diff仅首行注释和`total_env_steps`。
- **与F0同配方**：逐键对比`run_manifest.json`（vs `t6.1-sim-plain-s0`），差异仅run_id、seed、device、ros_master、started、total_steps/total_env_steps、config_sha256；`sources`中全部源码哈希相同（含`scwm_train.py` 54c9b2ee…、`scwm_sac.py` 06e6335c…）。即未改代码，确为F0链路只加长步数。
- **读数复算**：上表1M/2.5M与`screening_step*.json`重新统计一致；F0 1M D15末点25/24/23与task6.1 RESULTS §9.5一致。5M行由本次补填（每条106次D15，种子3001–3050）。
- **修正10-16判断**：10-16据3M前读数写“未见明显上升”；3.5M后三条都上升：s0 24→28–33、s1 25→31–35、s2 26→30–35（3.5M–5M逐点见各run `screening_step*.json`）。5M合计89/150（59%），F0 1M合计72/150（48%）。
- **限制**：D15是训练中50种子筛选评估（3001–3050），不是task6.1 §9最终评估（`eval_task6_final.py`，种子2001–2050；F0为21/22/22，均值0.433）。两者不能直接比；5M是否超过F0须以最终评估为准。验证集101–105末5次均5/5，样本太小，仅作健康确认。

## 与CBL过往训练对照（2026-10-19，Claude，claude-opus-5-5，只读）

用户问“这个是不是正常的效果”，指明以CBL为准（N²M²不作参照）。

- **CBL原始项目自身的训练记录**：`archive/mm_husky_runtime/logs/`只有冒烟/调试日志（如`train.log`仅600步、从`sac_checkpoint_husky_ur5_4000`加载），没有CBL本人长训的成功率记录，无法用CBL本人数据对照。
- **CBL原版RLlib链路（task5.2，种子40，1M，sim simpleobstacle）**：`results/task5/t5.2-train-s40/train_eval_series.csv`训练中评估（每7.5万步50回合）：75k 0.06、150k 0.52、225k 0.68、300k 0.66、375k 0.72、450k 0.64、525k 0.82、600k–975k 0.74–0.82。即约20万步达约0.7，约50万步后平台约0.78。该链路`training_intensity` 0.1（每环境步约0.1次更新）、`tau` 0.001、lr 1e-4→1e-6。
- **cbl自写SAC（本任务，与F0同链路）训练回合内部成功**（`logs/task6/t5.5-sim-cbl5m-s*/episodes.jsonl`，随机策略，每0.5M合并）：s0 0.29/0.27/0.35/0.42/0.38/0.44/0.47/0.53/0.55/0.60；s1 0.30/0.27/0.37/0.40/0.40/0.45/0.48/0.53/0.56/0.60；s2 0.26/0.28/0.35/0.41/0.30/0.29/0.35/0.45/0.51/0.54（0–0.5M…4.5–5M）。F0-s0前1M为0.30/0.25，同步一致。以20次IK失败结束的回合占比由约0.45降到约0.31–0.37，仍是主要失败方式；s2在2–3M出现回落（IK终止升到0.60）后恢复。
- **判断**：
  1. 作为本链路的运行，结果正常：三种子无崩溃，训练回合成功与D15同向上升，1M处与F0一致，s2的中途回落属可恢复波动。
  2. 相对CBL原版RLlib，效果明显偏弱：RLlib约20万步到0.7、平台约0.78；本链路5M后D15约0.6（训练回合约0.55–0.60），达到相近水平所需步数至少多一个数量级，且尚未达到RLlib平台。这与PLAN中“约30个百分点差距来源尚未弄清”一致，5M训练只缩小了差距。
  3. 限制：两者场景不同（本链路全矩形障碍，task5.2约一半椭圆柱）、评估集与口径不同、RLlib仅1个种子；task6.1 F1–F6单因素替换（含每10步更新1次）在30万步筛选中均不显著。所以不能断言哪一项是原因，也不能把“0.6 vs 0.78”当作同口径差值。最终评估后再更新本节判断。

### 最终评估后的更新（2026-10-20，Codex追加；保留上述Claude原文）

最终2001–2050评估为32/33/30（/50，均值0.6333），F0同批sim为21/22/22（均值0.4333），三组场景均50/50逐字段一致，详见下节及[SRC-0394](../../../SOURCES.md#src-0394)。原文第1项“运行正常、后期恢复并上升”仍获训练与最终产物支持；“5M是否超过F0须以最终评估为准”现已有描述性结果：本批三条5M成功数均更高。D15使用3001–3050、训练内筛选；最终使用2001–2050、独立最终脚本，不能混用89/150与95/150，也不能用单次最终值推断整个训练曲线。

原文第2项“相对RLlib效果明显偏弱”“所需步数至少多一个数量级”“5M训练只缩小了差距”须收敛：本次仅确认自写链路在同批sim最终场景较F0的描述性成功数增加，无法据异实现/异场景/异评估口径/单种子的RLlib约0.78证明相对样本效率、量化差距或差距缩小。第3项关于场景、评估集与单种子限制仍成立，不能认定某个因素为原因。本次不重做旧筛选的显著性判断，不新增分析或实验。

## 最终评估

2026-10-20 Codex只读核对并入账，task5.5状态为 **review（待Claude/用户复核）**。三条评估已于2026-10-19 22:52 +08:00结束；本次没有新评估、训练、容器/实例操作或GPU使用。证据与推导统一登记[SRC-0394](../../../SOURCES.md#src-0394)；详细核对命令、原件哈希见[本次独立日志](../../../agent_logs/task5/task5.5/20261020-codex-final-sim-results.md)。下方历史启动记录保留。

### 完整性、退出与策略身份

三条run-id依次为 `t5.5-final-sim-s0-r1`、`t5.5-final-sim-s1-r1`、`t5.5-final-sim-s2-r1`。各自 `forem/results/task6/<run-id>/eval.json` 的声明seeds与50条episodes.seed均精确为2001–2050、无缺漏/重复；汇总字段与逐回合复算全部一致，completed/capped/errored均50/0/0。独立复算成功32/33/30、含IK失败18/17/19、碰撞0/1/1，与Claude只读速览一致，没有差异。

各 `forem/logs/task6/<run-id>/eval.out` 末尾均 `eval rc=0`、`stop rc=0`；`start.out`均ready=true、stop_rc=0、residue=[]、ros/gz端口free。实例63/64/65的 `launch.exit.json`均exit_code=0，时间分别为10-19 22:52:12、22:52:05、22:51:57 +08:00，`launch.cleanup.json` residue均空。10-20 11:49只读 `ps -eo pid,ppid,args` 未见本任务eval/实例命令，启动快照里的宿主PID844488/844496/844498均已不在；没有执行清理命令。

eval.json.policy与启动 `forem/logs/task5/t5.5-final-eval-launch-20261019/manifest.json` 的run/训练种子/策略路径逐条一致；三份launch收据returncode均0，startup-verification也对应同run。策略文件均存在，实算SHA256与启动manifest完全相同：

| 训练种子 | 最终策略原件 | SHA256 |
|---|---|---|
| s0 | `forem/results/task6/t5.5-sim-cbl5m-s0/ckpt/policy_step05000000.pt` | `83d49ae40382b2684cac6c3fe1ae599001f4dd0939f4469bd238b769b0b7a611` |
| s1 | `forem/results/task6/t5.5-sim-cbl5m-s1/ckpt/policy_step05000000.pt` | `e0a93d5b390040677405ace3a1ea6ac567c996ddb16860eb8b0c754ad189d4d0` |
| s2 | `forem/results/task6/t5.5-sim-cbl5m-s2/ckpt/policy_step05000000.pt` | `ec8005262e9014edb67d8b838b576219f465a42055bc6d1ac81150168945f2cd` |

### 与F0 §9.2逐项口径核对

F0依据为[task6.1 RESULTS §9.2/9.3及R4](../../task6/task6.1/RESULTS.md#92-评估设置)、原始三份eval.json、原脚本备份及汇总manifest；不能仅以旧文档结论代替本次核对。[SRC-0394](../../../SOURCES.md#src-0394)。

| 项目 | 判定 | 本次 / F0与证据位置 |
|---|---|---|
| 评估脚本文件版本 | **不一致** | 本次SHA256 `ba140ec7ed31e34fb5b9fa694699b1c13073b8dd0900fb116a815635608ecccb`；F0 `9989213b59a14f3bb22c1083d54d57cb26746618492a34ddbbaf3fdba91db312`。F0哈希实际已记录在 `forem/results/task6/t6.1-summary/manifest.json:eval_script`，并与 `forem/results/task6/t6.3-baseline/original/eval_task6_final.py` 实算一致。 |
| sim评估语义 | **一致（源码核对）** | 直接diff旧备份与当前脚本：仅增加Gazebo专用可选execute_style/ik_fail_thresh覆盖，以及effective_config/max_steps_per_episode和long_episode记录（[SRC-0253](../../../SOURCES.md#src-0253)）；sim环境构造入参、载入策略、核心循环、成功与分母统计不变。 |
| 启动器/覆盖参数 | **一致（现存证据）** | 同 `forem/logs/task6/t6.1-eval-launch/eval_one.sh`；当前SHA256 `fb61eaffdd7ff3a283b79c48aedd1618758e85ea5482871b9064c53a9a19cc1e`与本次启动manifest一致。F0 §9.2与summary manifest.commands指向该启动器；F0当时未单记启动器哈希，无法证明其历史文件逐字节身份。两次均未传新增覆盖项。 |
| F0启动器历史字节版本 | **无法核实** | F0汇总manifest只登记启动器路径/命令，未单存其SHA256；现存启动器可用于参数追溯，不能证明历史字节完全一致。 |
| world | **一致** | 六份eval.json.world均sim；启动器 `--world sim`。 |
| 确定性动作、每种子1回合、分母 | **一致（源码与产物）** | 新旧main均每seed调用一次 `run_eval(env,agent,[s],a.max_steps)`；同哈希 `scwm_train.py:141–158` 使用 `select_action(...,eval=True)`。每条50个2001–2050，错误保留分母；非D15。 |
| max_steps_per_episode | **一致（F0由默认值确认）** | 本次字段2000；F0无此字段，但原脚本 `--max-steps` 默认2000、启动器未覆盖，F0 §9.3也声明2000。 |
| max_close_steps | **一致** | 六份eval.json均500；启动器显式 `--max-close-steps 500`。 |
| force_rectangle_obstacles | **一致** | 六份eval.json均True；同哈希 `ScwmEnv.__init__` sim分支设True，逐episode障碍均矩形。 |
| execute_style / time_step / ik_fail_thresh / window_s | **一致（配置/源码可追溯）** | 本次effective_config为direct / 0.02 s / 20 / null。F0原脚本同sim构造，`scwm_env.py:34–55`仅覆盖world_type/init_controllers/max_close_steps；`task3_env.py:66–71`加载 `config/task3/task_contract.yaml:env_config` 中direct / 0.02 / 20，window_s缺省None。该合同与环境源码当前哈希匹配两组训练manifest.sources（详见独立日志）。 |
| F0上述默认值的运行时生效快照 | **无法核实** | F0 eval.json没有effective_config；旧脚本当时也不输出此字段。本次没有重建运行状态，配置推定不能冒充F0运行时实测。 |
| episode_spec场景 | **一致（记录精度内完全相等）** | s0/s1/s2分别50/50；逐字段比较障碍名称/几何/尺寸/位姿、goal_tip、goal_wrist、arm_joints_planned、base_tf、map_size_m，均50/50精确相等，不一致种子：无。未仅比较hash，也未用base_tf容差。spec记录为6位小数，不证明未记录精度或全部隐藏状态相同。 |
| 训练配方与总步数 | **不一致（仅已授权预算延长）** | 本次再核三组对应run_manifest：config仅budget.total_env_steps由1M→5M，全部sources一致且匹配当前；身份/时间和预算/config_sha256随run改变，未改算法/奖励/观测。lr_horizon_updates都5000001，指数日程公式未变；5M走近完整日程（4999743 updates），F0只走前约1/5（999743 updates），前1M日程相同。 |

F0 §9.4历史sim/Gazebo场景分叉种子2006/2012/2021在本次“sim 5M对sim F0”中也全部逐字段相同，故本表不排除这些种子；历史跨world分叉根因仍未查，本次未扩展调查。

### 结果与描述性对照

列定义沿F0 §9.3：内部成功=`episode_is_success`；completed为无error且done；capped为无error且未done；errored为有error。碰撞episode指nr_base_collisions>0，含IK失败episode指nr_kin_failures>0（不等于因20次IK失败终止）；计数字段可能为字符串，复算先转数值。物理成功在sim为N/A，不能把汇总physical_successes=0解释为物理验证失败。[SRC-0394](../../../SOURCES.md#src-0394)。

| 侧 | run | 内部成功/50 | Wilson 95% | 物理成功 | completed/capped/errored | 碰撞episode | 含IK失败episode | 平均步数 |
|---|---|---|---|---|---|---|---|---|
| sim（task5.5 5M） | s0 | 32/50 | [0.50, 0.76] | N/A | 50/0/0 | 0 | 18 | 247.10 |
| sim（task5.5 5M） | s1 | 33/50 | [0.52, 0.78] | N/A | 50/0/0 | 1 | 17 | 238.16 |
| sim（task5.5 5M） | s2 | 30/50 | [0.46, 0.72] | N/A | 50/0/0 | 1 | 19 | 227.00 |
| **sim均值（5M）** | 3种子 | **0.6333（95/150）** | — | N/A | — | — | — | — |
| sim（F0 1M） | s0 | 21/50 | [0.29, 0.56] | N/A | 50/0/0 | 5 | 27 | 337.54 |
| sim（F0 1M） | s1 | 22/50 | [0.31, 0.58] | N/A | 50/0/0 | 3 | 27 | 313.84 |
| sim（F0 1M） | s2 | 22/50 | [0.31, 0.58] | N/A | 50/0/0 | 2 | 26 | 317.40 |
| **sim均值（F0 1M）** | 3种子 | **0.4333（65/150）** | — | N/A | — | — | — | — |
| sim（task5.2 RLlib 1M，异口径） | s40（仅1种子） | 训练中评估平台约0.78 | — | N/A | 不套用本表口径 | — | — | — |

Wilson沿F0汇总脚本 `summarize_task6_1.py:wilson` 的n=50、z=1.96公式，区间显示2位小数；平均步数由每条50个无error回合的steps求算术均值，本表保留2位小数（F0旧表取整为338/314/317）。三种子均值为成功率算术均值，95/150与65/150仅为等分母加总说明，不为跨训练种子总体另算区间，也未做显著性检验。

同种子配对只使用场景逐字段一致的50种子；按同训练种子s0↔s0等配对，每行合计50：

| 训练种子对 | 一致场景数 | 两者都成功 | 仅5M成功 | 仅F0成功 | 两者都失败 |
|---|---|---|---|---|---|
| s0 | 50 | 19 | 13 | 2 | 16 |
| s1 | 50 | 20 | 13 | 2 | 15 |
| s2 | 50 | 18 | 12 | 4 | 16 |

描述性结论：在这批相同的sim场景上，三条5M策略的内部成功数都高于对应F0 1M，均值0.6333对0.4333；含IK失败episode较少。仅报告已有数据，不能据此宣称统计显著、算法改进或Gazebo迁移有效。

task5.2行依据 `forem/results/task5/t5.2-train-s40/train_eval_series.csv` 的 `evaluation/custom_metrics/success_mean`：525k–975k为0.82/0.76/0.82/0.78/0.74/0.76/0.76，每次50回合，只称训练中平台约0.78。它是RLlib实现，场景不同（约一半椭圆柱），评估集与口径不同，且仅1个训练种子40；**不是同口径比较，不与F0/本次直接相减，也不把约0.78冒充本次固定2001–2050最终评估。**

## Claude独立复核（2026-10-20）

- 执行：Claude（claude-opus-5-5，推理强度未知）；用户要求“核对原件哈希、逐回合计算和F0同口径对照，通过后标done”。只读结果原件、只写文档；未重跑评估/训练，未碰容器、实例或GPU。记录见[复核日志](../../../agent_logs/task5/task5.5/20261020-claude-final-sim-review.md)。
- **原件哈希**：自行`sha256sum`六份eval.json、三个5M与三个F0策略文件、新旧`eval_task6_final.py`与启动器`eval_one.sh`，15项全部与[SRC-0394](../../../SOURCES.md#src-0394)及本文件记录一致。
- **逐回合重算**：自写标准库脚本（未复用Codex代码）从episodes重算，并断言与eval.json汇总字段一致：种子2001–2050齐全有序；内部成功32/33/30（5M）、21/22/22（F0），均值0.6333/0.4333；completed/capped/errored均50/0/0（另与逐回合`capped`字段交叉一致）；碰撞episode 0/1/1、5/3/2；含IK失败episode 18/17/19、27/27/26；平均步数247.10/238.16/227.00、337.54/313.84/317.40；Wilson区间与上表一致。另做语义检查：所有`internal_success`回合都满足`ee_done`且IK失败数与底盘碰撞数为0，反向也没有“满足这三条却未判成功”的回合，6份文件均无例外。
- **场景同口径**：比Codex的6字段比对更严，直接比较每回合**完整spec字典**（含spec内hash字段）与`episode_hash`，三组均50/50相等；配对四格表19/13/2/16、20/13/2/15、18/12/4/16与上表一致。
- **评估参数**：六份eval.json的world均sim、max_close_steps均500、force_rectangle_obstacles均True；5M侧effective_config为direct/0.02 s/20/None、max_steps 2000，F0无这两个字段（旧脚本不输出）。自行diff新旧评估脚本：sim分支env构造入参不变，新增项仅Gazebo分支覆盖、effective_config只读查询与输出、长回合打印，策略加载、`run_eval`调用与统计不变。启动器第8行固定`--max-close-steps 500`、未传execute_style/ik_fail_thresh。
- **训练配方**：逐键比较三对`run_manifest.json`，差异仅`config.budget.total_env_steps`与`total_steps`（1M→5M）、`config_sha256`、`run_id`、`started`；sources全部相同。
- **结论：通过，task5.5标done。** 同意Codex的口径判定与“最终评估后的更新”对原第2项的收敛：只能说同批sim场景上5M较F0 1M内部成功数更高（描述性），不能据task5.2 RLlib约0.78（异实现、约一半椭圆柱场景、训练中评估、单种子）推出相对样本效率、量化差距或“差距缩小”。
- 沿用的限制（不阻碍done）：F0运行时effective_config与当时启动器字节未留存，只能由同哈希脚本/配置追溯；F0只走了lr衰减日程的前约1/5（两者horizon均5000001），所以5M对F0是“同配方加长训练”，不是同一检查点；未做显著性检验；仅sim内部成功，物理成功N/A；F0历史sim/Gazebo分叉种子根因仍未查（本次sim对sim无分叉）。

## 交接

- 2026-10-20 Claude复核后：task5.5 **done**。阶段一中本节点不再有待办；Gazebo零样本评估如需做，须用户另行授权。以下为Codex入账时的交接原文。
- 目标/授权：已有最终sim结果核对、汇总与入账；负责人Codex。本轮文档核对已完成；**task5.5为review，等待Claude/用户复核**，不标done。全部结果与证据[SRC-0394](../../../SOURCES.md#src-0394)、[独立日志](../../../agent_logs/task5/task5.5/20261020-codex-final-sim-results.md)。
- 已完成：三条退出/分母/种子/策略哈希、F0版本与参数追溯、50种子场景逐字段比对、结果及配对描述、task5.2异口径并列；训练和历史启动记录保留。评估已于10-19 22:52结束，无本任务残留进程，本轮无运行任务需要监控。
- 证据：`forem/results/task6/t5.5-final-sim-s{0,1,2}-r1/eval.json`；`forem/logs/task6/t5.5-final-sim-s{0,1,2}-r1/`；`forem/logs/task5/t5.5-final-eval-launch-20261019/`；F0 `forem/results/task6/t6.1-eval-sim-s{0,1,2}/eval.json` 与 `t6.1-summary/manifest.json`。
- 不一致/无法核实：脚本字节版本不同但静态diff显示sim语义不变；训练预算/日程覆盖不同；F0历史启动器哈希未单记、effective_config运行时快照缺失（只能由当时脚本/相同哈希配置追溯）。task5.2不具同口径可比性。F0历史sim/Gazebo三个分叉种子根因未查，本次sim对sim无分叉。
- 剩余与风险：待Claude/用户复核本次口径判定与入账；不将sim内部成功当物理效果或统计显著提升。是否需要Gazebo零样本评估由用户另行授权，本轮未启动。
- 下一步：复核本节、原件哈希与逐回合计算；需要额外实验时另定授权。复核推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（跨脚本版本与参数证据链），本次实际模型/强度未知。

## 最终sim评估启动（2026-10-19，Codex）

用户本轮明确授权，依据[SRC-0380](../../../SOURCES.md#src-0380)。22:48:22–23 +0800三次后台启动返回0；inst63/64/65均ready=true、startup_s=3.1，随后list核实alive/master_reachable/ready均true。使用训练s0/s1/s2的最终5M策略，对应cuda:0/1/2；每条50场景2001–2050，确定性动作，max_steps=2000、max_close_steps=500。

- run-id：`t5.5-final-sim-s0-r1`、`t5.5-final-sim-s1-r1`、`t5.5-final-sim-s2-r1`。
- 启动证据、完整命令与SHA256：`forem/logs/task5/t5.5-final-eval-launch-20261019/manifest.json`及各`*-launch.json`。
- 日志：`forem/logs/task6/<run-id>/{start.out,eval.out}`；评估产物：`forem/results/task6/<run-id>/eval.json`（完成后写入）。实例细节/子进程收据在同日志目录`inst63/64/65/`。
- 代码核对：三条训练manifest所有sources与当前文件一致。评估脚本沿用task6.3记录的ba140ec7…版本，区别于task6.1原版的改动只涉及Gazebo可选覆盖和配置/长回合记录（SRC-0253），本次不传额外覆盖。
- 停止/恢复：先核对注册run-id与评估进程PID，只SIGTERM本条评估，再通过`scwm_instance.py stop --inst K`按身份清理；失败保留run证据，不自行改配置或覆盖结果。
- 状态active，尚不能声明评估通过。完成后检查三条eval rc及stop rc、固定分母与错误项，按同口径对照F0。Codex GPT6.1sol/medium、Claude Sonnet5.5/medium为推荐（评估与隔离核查）；本会话实际型号/强度未知。

启动后核实（2026-10-19T22:49:44+08:00）：三条已产生逐回合输出、无Traceback；GPU评估进程宿主PID844488/844496/844498，各708 MiB。快照见启动证据目录`startup-verification.json`、`gpu.txt`、`processes.txt`。此为运行证据，最终结果待评估完成。
