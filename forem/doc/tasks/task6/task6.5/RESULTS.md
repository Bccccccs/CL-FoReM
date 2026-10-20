# task6.5 用原作者预训练模型复现N²M²的sim与Gazebo结果 — 结果与交接

> **当前状态（2026-10-19核对）：阶段一review（待Claude复核）；阶段二未放行。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**review（阶段一review，2026-10-14：sim43/50，Gazebo26/50；数据核验完成，停止交Claude）**。此前active/blocked及包装错误保留为历史，当前以本次末节为准；阶段二尚未放行、未执行。计划见[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)。

## 阶段状态

|阶段|结果|证据|
|---|---|---|
|§1 开工|已核容器/源码/模型副本/config与资源|[本轮来源](../../../SOURCES.md#src-0272)|
|§2 阶段一（原作者PR2，simpleobstacle sim＋Gazebo）|sim43/50已Claude R1通过；Gazebo新r2 26/50已核，阶段一review|[manifest](../../../../results/task6/t6.5-summary/manifest.json)|
|§3 阶段二（须Claude放行）|尚未执行||
|§4 汇总|阶段一对照/逐回合对象/manifest已交付；阶段二未执行|[comparison](../../../../results/task6/t6.5-summary/comparison.json)|

## 结果表（§4填写；simpleobstacle，成功率）

|模型|sim|Gazebo|原文sim（Table III）|原文Gazebo（Table VI）|
|---|---|---|---|---|
|原作者PR2|43/50=86%|26/50=52%（r2）|86.0%|81.6%|
|我们训练的A（PR2，task6.4/task5）|0.78（task5 r1）|0.32（task6.4阶段一）|同上|同上|
|原作者TIAGo（阶段二）|尚未执行|尚未执行|61.2%|56.0%|
|F0（Husky，ScwmSAC，task6.3）|0.433|0.160/0.200|—|—|
|我们训练的B（Husky，N²M²原版方法，task6.4）|0.78|0.72|—|—|

## 交接

- 目标与授权：见[TASK](TASK.md)，[SRC-0269](../../../SOURCES.md#src-0269)。
- 当前负责人：Claude（流程已交付）；执行由用户派发Codex。
- 下一步：task6.4的A正式评估已于2026-10-14结束（容器空闲），执行者可从§1开始。


## 2026-10-14T11:17:21.329562+08:00 Codex执行记录与异常交接

**阶段一尚未完成，blocked；不标“阶段一review”。** 当前负责人Codex停止交Claude。用户授权§1→§2原作者PR2 sim50＋Gazebo50；阶段二须Claude放行。依据[SRC-0272](../../../SOURCES.md#src-0272)；原文/模型说明沿[SRC-0269](../../../SOURCES.md#src-0269)，T64-D3沿[SRC-0265](../../../SOURCES.md#src-0265)，D21沿[SRC-0243](../../../SOURCES.md#src-0243)，D23 stdout主口径沿task5.3 R12/[SRC-0264](../../../SOURCES.md#src-0264)。

### 位置、输入与实际命令

复用空闲`forem-t6.4-pr2`，镜像`sha256:42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915`；接手top仅sleep，sim后仅sleep，再串行Gazebo。不新建容器，不触碰task5两个容器和G-B。独立产物逻辑路径results/task6/t6.5-pr2-{sim,gz}是指向既有rw挂载t6.4-preflight/A/同run的软链，容器路径`/t64_results/<run>`；原作者目录逐字节复制到每run/model，四文件sha完全一致。恢复metadata只写副本，mobile-rl没有写入。[输入/终检](../../../../results/task6/t6.5-preflight/final_verification.json)。

|原模型键|保存值|评估采用|
|---|---|---|
|env / task|pr2 / simpleobstacle|相同|
|learn_torso|true|相同|
|ik_fail_thresh_eval|100|显式CLI 50，按TASK主口径|
|execute_style / time_step|track / 0.02 s|相同|
|nr_evaluations / eval_seed|50 / 999|相同（显式传入）|
|seed|41|模型训练seed，不是评估seed|

`utils.py` model_file分支仅对显式CLI键覆盖保存config，故必须显式传50才能落实主口径；offline config仍为保存训练配置，生效值看commands和evaluation_ray覆盖链。未改上游。README例子的picknplace/vis_env按本次授权simpleobstacle/headless；num_gpus0沿流程，TorchPolicy真实CPU日志已确认。

```sh
# 宿主：先sim后Gazebo
python3 -u forem/scripts/run_task6_5_eval.py --mode sim --run t6.5-pr2-sim --episodes 50
python3 -u forem/scripts/run_task6_5_eval.py --mode gazebo --run t6.5-pr2-gz --episodes 50
# sim容器实际评估（Gazebo尚未走到评估命令）
/opt/conda/bin/python -u scripts/evaluation_ray.py --evaluation_only --eval_execs sim --env pr2 --eval_tasks simpleobstacle --model_file /t64_results/t6.5-pr2-sim/model/checkpoint-1000 --num_gpus 0 --ik_fail_thresh_eval 50 --nr_evaluations 50 --eval_seed 999
```

准确shell环境/ROS/Gazebo路径、起止/退出码在[sim commands](../../../../results/task6/t6.5-pr2-sim/commands.json)与[gz commands](../../../../results/task6/t6.5-pr2-gz/commands.json)。新包装run_task6_5_eval.py、monitor_task6_5_eval.py、summarize_task6_5_eval.py由task6.4副本派生，只处理启动/模型复制/日志/汇总/清理；未改task6.4包装。最外层语法检查通过，但没有检查内嵌health字符串生成后的语法，导致下述包装错误。

### sim实测与模型封存

|项|sim50|
|---|---|
|success / goal_reached|43/50=86% / 44/50=88%|
|success_nojumps|43/50=86%|
|IK失败回合 / 达50回合 / 平均次数|4 / 3 / 3.24|
|底盘碰撞回合 / Collision打印|0 / 0（每回合对象表为空）|
|上游selfcollision回合|5/50|
|总步数 / 平均 / 范围|14388 / 287.76 / 61–1020|
|eval退出码 / runner墙钟|0 / 218.232 s|
|事后success且IK≤100|43/50（同50阈值rollout筛选，非100阈值重跑）|

50个seed999–1048各一次完整Eval ep行，离线文件run-1k4bold5.wandb单文件导出rc0；success、平均步数、IK与碰撞比例全部与stdout一致，按T64-D3数据完整。逐回合成功/步数/IK/碰撞/对象/原行号与时间在[verified_eval](../../../../results/task6/t6.5-pr2-sim/verified_eval.json)，原始指标[offline_raw_export](../../../../results/task6/t6.5-pr2-sim/offline_raw_export.json)，stdout[eval.log](../../../../logs/task6/t6.5-pr2-sim/eval.log)。无超长episode或D21拼接，无排除失败。

四文件SHA在[model_source_sha256](../../../../results/task6/t6.5-preflight/model_source_sha256.json)；checkpoint为`a4d24df66107ba4cd90cdbbaed99d7d99a84c1ade8c1a3fc009b718add66f49d`，两个run的model_copy_verification记录逐文件一致，结束后原目录与复制原文件再次一致（允许副本新增恢复metadata）。sim86%数值与论文86%相同，但只发布模型一训练seed、50回合，不宣称原文多种子统计或Gazebo已复现。

### Gazebo异常、停止与清理

`t6.5-pr2-gz`上游PR2启动器退出0且打印All launchfiles started，仍原30 s等待＋设置0.002 s流程。之后包装生成的health.py第2行`from gazebo_msgs.srv import GetPhysicsProperties`前多一个空格，`IndentationError: unexpected indent`/rc1；来源是我在把health块置于mode条件下时，将字符串内容也整体缩进了。证据[health.log](../../../../logs/task6/t6.5-pr2-gz/health.log)、[生成脚本](../../../../results/task6/t6.5-pr2-gz/health.py)、包装L85–102。不是缺包、模型加载或物理失败；模型尚未加载，eval.log尚不存在，Gazebo0完成回合，成功率N/A。没有health.json，**物理实际值和controller状态未完成独立核验**，启动器意图不能替代实测。

按用户与PROCEDURE异常规则立即停止：没有修复包装或新run重跑；保留错误原脚本/日志，交Claude决定修复和继续范围。status error/rc1，runner53.275 s。两个run均身份标记T64_RUN＋PID start ticks清理，cleanup after=[]，末次forem-t6.4-pr2仅sleep。CPU监控会话48488按自己monitor.stop退出0；sim会话2806退出0、Gazebo会话70250退出1，均无后台任务需恢复。CPU66×约5秒样本峰18.094核、均11.536核、>56样本0，不证明未观测短瞬时峰。task5首尾只读top原ROS PID保留，G-B无进入/信号/配置改动。[终检](../../../../results/task6/t6.5-preflight/final_verification.json)。

### 交Claude的具体下一步

先复核sim50完整性与config50覆盖，再检查包装health字符串的多余缩进。建议放行后只修本任务包装（不改上游），对生成health.py做编译检查，以新run-id重做Gazebo50并保留本失败run；sim50不必重跑。此建议**尚未执行且不构成放行**。仍需Gazebo逐回合指标/碰撞对象及完整阶段一sim→Gazebo对照，才能标阶段一review。阶段二、其他机器人/任务、诊断实验、训练均未执行。

部分对照/manifest已写[comparison](../../../../results/task6/t6.5-summary/comparison.json)/[manifest](../../../../results/task6/t6.5-summary/manifest.json)，Gazebo明确null/0回合，不伪造0%失败。task6.4 A sim78%/Gazebo32%、B78%/72%引用[SRC-0270](../../../SOURCES.md#src-0270)，F0 sim43.3%/Gazebo16%或20%引用[SRC-0256](../../../SOURCES.md#src-0256)，仅并列，不作原因判断。

推荐Codex GPT6.1sol / Claude Sonnet5.5，low/默认（明确流程/整理），跨模块排错需要时medium；实际模型/推理强度未知，未切换、未委派。独立日志[20261014-codex-task6.5.md](../../../agent_logs/task6/task6.5/20261014-codex-task6.5.md)。


## Claude复核R1（2026-10-14 11:2x）

- **sim通过**：Claude从`logs/task6/t6.5-pr2-sim/eval.log`读50条“Eval ep”，最终43/50＝**0.86**，与原文Table III PR2 rnd obstacle 86.0%一致；sim中0条碰撞记录。说明原作者PR2模型在我们的sim环境中完全复现。
- **Gazebo停止原因**：执行者自写包装`run_task6_5_eval.py`生成的`health.py`第2行多一个空格（IndentationError），发生在评估开始前，0回合。上游启动器本身退出0。停止判断符合异常规则。
- **T65-D1**：这是本任务包装脚本的缺陷，修正属于已授权的“评估包装脚本”范围，不涉及上游代码与评估参数。放行：修正缩进（及同一生成块中同类问题），记录diff与sha；用新run-id `t6.5-pr2-gz-r2`直接运行Gazebo 50回合（启动方式与task6.4 A相同，其冒烟已验证）；原`t6.5-pr2-gz`证据保留、不计入。若health核查仍失败或出现其他异常，照常停止交Claude。
- 完成后RESULTS标“阶段一review”并停止。依据[SRC-0273](../../../SOURCES.md#src-0273)。


## 2026-10-14T12:14:01.852764+08:00 T65-D1执行与阶段一review交接

**阶段一review，Codex已停止；Claude独立复核后决定阶段二。** sim沿R1已通过43/50，不重跑；Gazebo用`t6.5-pr2-gz-r2`完整50回合26/50。授权[T65-D1 / SRC-0273](../../../SOURCES.md#src-0273)，本次实测与适用限制[SRC-0309](../../../SOURCES.md#src-0309)。旧`t6.5-pr2-gz`0回合异常证据保留，未计入分母/成功数。

### 修正、SHA与冻结输入

只修本任务包装`run_task6_5_eval.py`的health字符串整体多余一空格；同块生成的observer/launcher/cleanup也检查，未发现同类语法错误。旧health编译重现IndentationError；修后四生成块host compile通过，容器实际Python2检查health/observer/launcher与conda Python3检查cleanup全rc0。外层评估参数、启动器与上游源码未改。包装before SHA `97103e8f82c1f09b472abf8e879c2f5b7f8e8930c2ae26aabed14f1efcbef6fc`，after `74737b71f4e18b532b88c463ddcf0191c931760e581167bd930f79f8a62944a7`；[diff](../../../../results/task6/t6.5-R2/wrapper.diff)/[核验](../../../../results/task6/t6.5-R2/fix_verification.json)。监控仅run-id/输出目录改为R2，有[独立diff](../../../../results/task6/t6.5-R2/monitor.diff)与sha；旧监控证据不覆盖。

继续复用空闲forem-t6.4-pr2/同task6.4镜像。四原模型文件逐字节复制到新run/model，复制前后、结束原目录与副本原文件sha一致，checkpoint仍`a4d24df66107ba4cd90cdbbaed99d7d99a84c1ade8c1a3fc009b718add66f49d`。上游五入口SHA首尾一致；旧失败gz已登记证据末检不变。[冻结/清理终检](../../../../results/task6/t6.5-R2/final_verification.json)。模型/配置不写mobile-rl，仅副本新增恢复metadata。

### 准确运行与设置

```sh
# 宿主（会话35670，自然退出134）
python3 -u forem/scripts/run_task6_5_eval.py --mode gazebo --run t6.5-pr2-gz-r2 --episodes 50
# 容器 /root/catkin_ws_pr2/src/modulation_rl 中的评估
/opt/conda/bin/python -u scripts/evaluation_ray.py --evaluation_only --eval_execs gazebo --env pr2 --eval_tasks simpleobstacle --model_file /t64_results/t6.5-pr2-gz-r2/model/checkpoint-1000 --num_gpus 0 --ik_fail_thresh_eval 50 --nr_evaluations 50 --eval_seed 999
```

[commands](../../../../results/task6/t6.5-pr2-gz-r2/commands.json)记录准确shell/env/起止/每条退出码；PR2原启动器`--pure_analytical no --algo rl --task simpleobstacle --bioik`与task6.4 A相同，30 s后physics独立实测0.002 s/500 Hz/unpaused、九控制器running，[health](../../../../results/task6/t6.5-pr2-gz-r2/health.json)与health.log rc0。learn_torso true、track、policy time_step0.02、确定性seed999–1048；IK评估50显式覆盖保存100，num_gpus0/CPU真实TorchPolicy日志保留；自由运行，Gazebo上限100000步，无fallback、动作缩放或固定每步时长。

### 结果与失败形式

|项|sim（已R1复核）|Gazebo r2|
|---|---|---|
|success / goal_reached|43/50 / 44/50|26/50 / 26/50|
|success_nojumps|43/50|21/50|
|底盘碰撞回合 / 计数总和|0 / 0|23 / 1150（各50）|
|非成功回合中有碰撞 / 无碰撞|0 / 7|23 / 1|
|IK失败回合 / 次数总和 / 均值|4 / 162 / 3.24|1 / 1 / 0.02|
|IK达到50的回合|3|0|
|selfcollision上游二元指标|5/50|4/50|
|max_close_steps_reached|3/50|1/50|
|平均步数 / 总步数 / 范围|287.76 / 14388 / 61–1020|1118.42 / 55921 / 245–2706|
|事后success且IK≤100|43/50|26/50|
|原评估退出码|0|134（T64-D3偏差）|
|runner墙钟|218.232 s|2783.387 s（46.390 min）|

Gazebo24个非成功回合里23个达到底盘碰撞50次；另一个seed1033（ep34）无底盘碰撞、IK0且上游max_close_steps_reached。这些是日志描述，不把IK/selfcollision/碰撞重叠指标当互斥因果分解。事后IK≤100只筛同50终止阈值rollout，**不等于100阈值重跑**，无法挽回已在50停止的sim回合。

50个seed各一次Eval ep完整；W&B唯一run-1agru0to.wandb导出rc0，success/epoch_len/ik_fails/base_collision比例与stdout一致：[逐回合verified_eval](../../../../results/task6/t6.5-pr2-gz-r2/verified_eval.json)/[原始指标](../../../../results/task6/t6.5-pr2-gz-r2/offline_raw_export.json)/[stdout](../../../../logs/task6/t6.5-pr2-gz-r2/eval.log)。134发生于全50回合、汇总和W&B写出后，末尾有卸载警告；按T64-D3认定评估有效，保留退出134，不把警告关联当已查明根因。无D21超限、续跑或拼接，无失败样本删除。

Collision打印879条，机器人侧全部为`pr2::base_footprint::base_footprint_fixed_joint_lump__base_link_collision_1`，环境侧16种障碍物字符串；每回合对象、事件/计数/成功/步数/IK/原行号在[PR2_collision_objects](../../../../results/task6/t6.5-summary/PR2_collision_objects.json)。按前一条Eval ep之后至本条之前分配，包含reset/rollout；print事件数与上游计数分别保存，不要求相等、不判检测器错误。任务前/结束后未分配事件均0。

### 对照、资源与限制

[comparison](../../../../results/task6/t6.5-summary/comparison.json)：原作者PR2 sim86%→Gazebo52%，下降34个百分点；Gazebo低于论文81.6%约29.6个百分点，未达到论文Gazebo量级。原作者发布模型在当前本栈仍较低，不能把本地PR2低成功率仅归于我们的A训练；本轮未做环境/代码/感知/控制时序的因果拆分。论文为多训练seed均值，本次单个发布模型/50回合，sim与Gazebo场景几何/感知不完全一致，上游success不是独立物理验收。已有A78%→32%、B78%→72%沿[SRC-0270](../../../SOURCES.md#src-0270)，F0沿[SRC-0256](../../../SOURCES.md#src-0256)，只并列，不当单因素比较。

有效sim+gz两个runner累计3001.619 s（50.027 min），不含用户交接间隔与旧失败启动，不是全局项目墙钟/CPU时间。R2 CPU监控563个约5秒主机CPU-time样本，均7.412核、峰20.934核、>56样本0；不证明更短瞬态峰。[CPU证据](../../../../results/task6/t6.5-R2/cpu_sampling_summary.json)。监控会话32827按自身monitor.stop退出0。

### 清理、范围和交接

r2 cleanup after=[]，forem-t6.4-pr2末次仅sleep，11311/11345无监听；评估/观察/监控均退出，无本任务后台任务需恢复。task5两容器只读top与开工完全相同，未发信号/重启/改源；G-B未进入/操作。[终检](../../../../results/task6/t6.5-R2/final_verification.json)。没有训练、上游补丁、依赖安装/构建、其他机器人/任务、诊断实验或阶段二。

当前负责人Codex已停止并交Claude。复核顺序：本节→[manifest](../../../../results/task6/t6.5-summary/manifest.json)与comparison→r2原stdout/W&B、逐回合对象、diff/sha→health/cleanup/CPU。旧partial comparison/manifest另存`.blocked-r1.json`，旧失败run继续保留，不重复计数。Claude先独立复核，再按§3决定后续分支；本次不自动开展差异排查或其余任务。

推荐Codex GPT6.1sol / Claude Sonnet5.5，执行/汇总low或默认，必要跨链路/指标复核medium。实际Codex GPT-6系列（系统仅披露系列、精确型号未知），实际推理档位未知，未切换/委派；推荐不当实际配置。日志续写[既有20261014-codex-task6.5.md](../../../agent_logs/task6/task6.5/20261014-codex-task6.5.md)。
