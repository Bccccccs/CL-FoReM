# task6.3 sim训练策略的Gazebo零样本迁移 — 结果与交接

> **当前状态（2026-10-19核对）：done（Claude复核R3）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**done（2026-10-13 Claude复核R3通过）**；原状态review（§3 r2冒烟及§4–§5已执行并核验）。计划见[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)。以下各节由执行者按实际运行填写；未执行的步骤保持“尚未执行”。

## 阶段状态

|阶段|结果|证据|
|---|---|---|
|§1 开工与上游配置核对|冻结核查通过；发现episode上限/超限处理差异，停止交Claude|[SRC-0251](../../../SOURCES.md#src-0251)|
|§2 评估脚本改动与回归|19项测试通过；默认Gazebo五种子场景5/5一致；运行rc0|t6.3-baseline/test_green_ros.log；t6.3-regression-r1/comparison.json|
|§3 冒烟|r2通过：direct/IK50，运动>0、IK49非终止、0errored；r1失败保留不计入|[SRC-0255](../../../SOURCES.md#src-0255)；smoke_r2_checks.json|
|§4 正式评估|六条首次完成，各50种子，start/eval/stop均0，0errored|[SRC-0255](../../../SOURCES.md#src-0255)|
|§5 汇总|50/47种子、Wilson、物理/内部、上限与IK分布复算通过|results/task6/t6.3-summary/{comparison,manifest,verification}.json|

## 上游Gazebo评估配置核对表（§1填写）

|项|上游位置|上游取值|本项目取值（Z-A）|一致/偏差|
|---|---|---|---|---|
|time_step / world / init_controllers|evaluation_ray.py:29–37，utils.py:106、249–251|0.02 / gazebo / true|现有契约0.02 / gazebo / true|静态一致；本轮未启动|
|IK阈值|evaluation_ray.py:36，utils.py:109|取ik_fail_thresh_eval=50|Z-A实际50；Z-B20|六份effective_config已核验|
|execute_style|evaluation_ray.py:81–85，utils.py:148；robot_env.cpp:240|parser track；TIAGo差速强制direct|T63-D2：Z-A/Z-B实际direct|与上游差速行为一致（代码推导，SRC0254）|
|perception_style / exec_action_*|utils.py:145–149|base / None|契约base / null|静态一致|
|评估数量 / 种子|utils.py:139、144|50 / eval_seed=999|计划50 / 2001–2050|数量一致，种子按本任务冻结|
|异步执行 / dt_exec|robotenv.py:257–260|rate.sleep注释；dt_exec=rate.sleep_dur|迁移源码相同路径，time_step=0.02|静态一致；window_s计划None|
|规划dt|eeplanner.py:163–176、225–239|真实ROS流逝时间，上限0.5 s|迁移同路径|静态一致|
|max_close_steps|utils.py:450|非解析500（有ikslack时）|契约有效500|静态一致|
|动作确定性|evaluation.py:182–195、248、260、339–348|deterministic=True，deterministic_sample，无梯度|run_eval确定性动作|静态一致|
|episode步数上限/超限处理|evaluation.py:224–227、259|Gazebo max_len=100000；超过上限抛断言；sim为20000|T63-D1：Z-A 100000，Z-B 2000；capped计失败继续|Claude R1已决定；披露超限处理偏差|
|物理步长|handle_launchfiles.py:143–146；modulation_tasks.world:20–21|PR2且非moveit/bi2rrt覆写0.002 s；该world文件为0.0005 s/2000 Hz|husky_empty.world:29–30为0.0005 s/2000 Hz|与PR2覆写有偏差，与该world静态值一致；不改|
|Husky track底盘链|本项目robot_env.cpp:243–251，robot_husky.cpp:78–88，myutils.cpp:432|调用calcDesiredBaseCommandDiffDrive，但实现无条件throw|Z-A三次RuntimeError，未返回step|**冒烟失败**，此前只证实调用链的结论不足|

## 结果表（§5填写；种子2001–2050，分母50）

|组|策略（训练环境）|评估环境/配置|内部成功（三种子）|均值|物理成功|因IK失败终止|
|---|---|---|---|---|---|---|
|Z-A|F0（sim）|Gazebo，T63-D2 direct/IK50，上限100000|8/13/9|0.200|3/7/5（0.100）|37/34/38|
|Z-B|F0（sim）|Gazebo，direct/IK20，上限2000|7/10/7|0.160|5/5/2（0.080）|39/38/36|
|F0 sim侧|F0（sim）|sim|21/22/22|0.433|N/A|18/21/20|
|R-48|Task4.8（Gazebo）|Gazebo，task6.1同口径|2/1/5|0.053|0/0/3|48/49/45|

本轮两行：[SRC-0255](../../../SOURCES.md#src-0255)；后两行来自task6.1 §9与R4复核（[SRC-0246](../../../SOURCES.md#src-0246)），本轮从原始JSON重算。

## 交接

- 目标与授权：见[TASK](TASK.md)，[SRC-0248](../../../SOURCES.md#src-0248)。
- 当前负责人：Codex /root已交付§3 r2及§4–§5；状态review，等待Claude独立复核。
- 派发提示词：[20261013-claude-task6.3-plan.md](../../../agent_logs/task6/task6.3/20261013-claude-task6.3-plan.md)。
- 下一步：Claude从最新结果、原始eval.json与manifest独立复算并审核T63-D1/D2口径；通过前不标done。没有本任务后台进程，不自动启动后续实验。


## Codex §1实际记录与停止交接（2026-10-13T15:15:41.963878+08:00）

依据：[SRC-0251](../../../SOURCES.md#src-0251)。目标/授权仍为本TASK与用户本次指令；没有增加条件。推荐Codex GPT6.1sol、Claude Sonnet5.5，核对/脚本medium，执行/汇总low或默认；实际精确模型及推理强度未知，未切换模型、未派发Agent。

- 接手时间：2026-10-13T15:12附近+08:00（精确时间以[独立日志](../../../agent_logs/task6/task6.3/20261013-codex-task6.3.md)为准）；根Git分支main，既有大量修改/未跟踪文件，未覆盖它们。
- 实际执行：只读cat/sed/rg、git status/branch、docker top forem-dev、nvidia-smi、ps、Python sha256与/proc/stat两秒采样，最终核查命令退出0。两次rg/sed因猜测的上游launch路径不存在退出2，随后用rg --files定位handle_launchfiles.py，未修改源码。
- forem-dev核查只有docker-init/sleep，未启动本任务实例。GPU0–3快照利用率0%、每卡14 MiB；64逻辑CPU，两秒全主机忙核约5.963（公式与原始范围见host_cpu.json），不能代替持续profile。host进程可见task6.2训练/11个Gazebo实例，未对其容器执行任何命令，未停止任何进程。
- SHA证据：[hash_check.json](../../../../results/task6/t6.3-baseline/hash_check.json)列出7个完整sha与expected，全部match=true；上游/本项目静态核查源sha：[upstream_audit_sources.json](../../../../results/task6/t6.3-baseline/upstream_audit_sources.json)。原始开工记录在forem/logs/task6/t6.3-baseline/。
- **停止原因**：上游非解析评估max_len=100000，本项目2000；且上游超限断言，本项目capped。PROCEDURE §4规定“max_steps_per_episode沿用2000（若§1发现上游不同，按Claude决定）”。该决定尚无记录；执行者不能自行将其解释为已批准的等价原论文配置，故停止待Claude确认口径。不是哈希失败，也不是动态track失败。
- 尚未执行：§2脚本改动/备份diff/单元测试与运行回归、§3冒烟、§4六条正式评估、§5汇总。无新eval.json、无结果结论；源码及参数保持原状。实例/GPU分配、评估命令与退出码均N/A（未启动）。
- 限制：上游论文定量说法未在本轮重核；表中一致仅静态核对。max_close_steps=500（近目标阈值）与episode总步数上限是不同机制，不能混用。
- 交接给Claude：先核对上述代码和证据，再写明上限/记账决定、更新有效PROCEDURE。之后执行者复查冻结文件及运行占用，从§2继续；本轮没有后台任务可监控/停止。状态blocked，不标review完成或done。


## Claude复核R1（2026-10-13）

- **§1通过**：核对表与证据核实。7个冻结文件sha256全部一致（`hash_check.json`）；上游`evaluation.py` L259（sim 20000、非解析100000）与L222–224（超限断言）由Claude重读确认。停止判断正确：PROCEDURE写明此项“按Claude决定”。
- **更正Claude文档**：SRC-0249与原TASK写“上游Gazebo物理步长与本项目不同”不准确。Codex核实上游0.002 s覆写只用于PR2，`modulation_tasks.world`为0.0005 s/2000 Hz，与本项目`husky_empty.world`相同。TASK已改，SRC-0249加更正注。
- **T63-D1（episode上限与超限记账）**：
  - Z-A用`--max-steps 100000`（上游取值）。超过上限时，上游抛断言中断整个评估；本项目沿用task5 D21与用户已确认的规则（“超长episode算失败”，SRC-0243），记capped、计为失败、继续下一种子。这是对上游中断行为的已披露偏差。
  - Z-B保持2000：须与task6.1 §9 R-48完全相同。R-48三条均capped 0（平均步数406–455），上限未起作用。
  - §5中Z-A另报步数>2000的episode数及其中成功数，以及“2000步内成功”的事后口径。
  - 不需要改代码：`eval_task6_final.py`已有`--max-steps`参数（L33），§2的代码改动范围不变。
  - 墙钟风险：Gazebo每步墙钟约17 ms，1个100000步的episode最坏约30分钟。任何episode超过20000步时在日志记录，不停止；单条run墙钟超过6 h时报告Claude（工程选择）。
- **其余**：`track`在Husky上的动态运动在§3冒烟验证（已在PROCEDURE中）。
- 放行：Codex从§2继续执行到§5。依据[SRC-0252](../../../SOURCES.md#src-0252)。


## Codex §2实际改动、回归与§3失败交接（2026-10-13T16:56:37.305688+08:00）

依据：[SRC-0252](../../../SOURCES.md#src-0252)、[SRC-0253](../../../SOURCES.md#src-0253)。推荐GPT6.1sol / Sonnet5.5，§2 medium（跨Python/C++环境合同），§3–§5 low/默认；实际精确模型/强度未知，未切换、未委派。

### §2证据

- 原脚本：[original/eval_task6_final.py](../../../../results/task6/t6.3-baseline/original/eval_task6_final.py)，原sha9989213b59a14f3bb22c1083d54d57cb26746618492a34ddbbaf3fdba91db312。
- 修改仅forem/scripts/eval_task6_final.py，新增forem/tests/test_task6_eval.py；[diff](../../../../results/task6/t6.3-baseline/eval_task6_final.diff)、[code_manifest](../../../../results/task6/t6.3-baseline/code_manifest.json)。脚本当前sha `ba140ec7ed31e34fb5b9fa694699b1c13073b8dd0900fb116a815635608ecccb`；测试sha `50b76aee7fe00491aaf2479fc997167f778e668853ad953146f84559797d5f03`。
- 两CLI选项None缺省；无参数Gazebo仍调用ScwmEnv(seed=0)，sim路径不接收两个overrides。显式Gazebo传参只改execute_style、ik_fail_thresh。effective_config读取实际core._robot.execute_style/core._ik_fail_thresh/rate.sleep_dur/包装器_max_close_steps；window_s本任务None。新增episode>20000步完成后日志行；本轮没有此类episode。
- 单元red：原脚本不识别CLI、缺元数据，日志test_red.log；green：完整19项通过（20.527秒），test_green_ros.log。第一次test_green.log有6个ROS导入错误（调用未加载ROS），随后修正调用，未改依赖/实现。实际命令：容器bash source /opt/ros/noetic/setup.bash与devel/setup.bash，python3 -W ignore::ResourceWarning -m unittest discover -s tests -p 'test_task6_*.py'。
- 运行回归t6.3-regression-r1（inst60/cuda0）：entrypoint→scwm_instance exec→python3 -u -W ignore scripts/eval_task6_final.py --world gazebo --device cuda:0 --policy results/task4/t4s-plain-s0/ckpt/policy_step01000000.pt --seeds 2001,2002,2003,2004,2005 --out results/task6/t6.3-regression-r1/eval.json。eval rc0、stop rc0/residue=[]。5/5 hash一致，done/internal_success全部一致；前4个episode步数变化，最后2005一致，详见[comparison.json](../../../../results/task6/t6.3-regression-r1/comparison.json)。

### §3失败与清理

|run|实例/GPU|实际设置|结果|退出/清理|
|---|---|---|---|---|
|t6.3-smoke-r1-A|60/cuda0|track、IK50、max_steps100000；time_step.02、max_close500、windowNone|2001–2003均RuntimeError('Not implemented for diff-drive yet')，errored3，无有效step|eval rc0（异常捕获）；start/stop rc0，residue=[]|
|t6.3-smoke-r1-B|61/cuda1|direct、IK20、max_steps2000；其余同上|仅完成2001/2002的轨迹记录；第三回合期间因A失败停止|eval rc15（SIGTERM），start/stop rc0，residue=[]|

- 实际启动/评估/停止命令在logs/task6/t6.3-smoke-r1-{A,B}/launch.sh；F0-s0，种子2001–2003，测量入口logs/task6/t6.3-smoke-r1/probe.py。只读取既有step info的base_tf_obs/nr_kin_failures/done，不改观测、动作或奖励，也不额外调用ROS服务。
- Z-A eval.json保留3个错误分母（n3/completed0/capped0/errored3），不能把进程rc0当冒烟成功；smoke_trace没有Z-A有效轨迹。底盘运动和IK>20非终止门槛未通过。
- Z-B smoke_trace.json只有两个完整回合，2001 772步、底盘最大位移0.759913 m，内部成功true、物理false；2002 2000步、最大位移3.311571 m、IK0。无完整eval.json，不计算正式成功率。
- 根因：myutils.cpp:432无条件throw；RobotHusky::calcDesiredBaseCommand只是转发，throw后差速计算代码不可达。Husky参考和mobile-rl同句只读核对存在。此前§1只检查调用链，没有核查实现体，是核查遗漏；本次明确纠正，不把该链当已实现/可用。
- 检测异常后停止推进：身份核验B probe精确argv、输出路径及IGN_PARTITION=forem_inst61，容器PID2452508发SIGTERM，退出15；监督launch.sh随后只停止自有inst61。A已完成并自清理。宿主/root权限限制使首次/proc环境筛选未找到PID，未发任何信号；改在forem-dev内核验后仅发本任务进程。后续SIGKILL核验时PID已不存在，**没有发送SIGKILL**。证据smoke_stop.json。
- 最终docker top forem-dev仅init/sleep；inst60/61 stop各rc0、residue=[]、ROS/Gazebo端口free。没有触碰forem-t6-husky-gz/G-B或其他非本任务进程。GPU采样本任务A/B对应GPU0/1各690 MiB计算进程；无性能收益结论。

### 交接与剩余

- §4正式六条及§5汇总均尚未执行，不生成伪comparison，不下迁移成功率结论。原结果表“尚未执行”保持。
- 其他6个冻结文件sha重新核查仍一致；[execution_manifest.json](../../../../results/task6/t6.3-baseline/execution_manifest.json)含实际run/退出码/sha/偏差；myutils.cpp没有修改，sha `33f48910935a16ff5108760e0648fe961aaa3d95961e0d53f8d98263fd56c5a9`。
- Claude先复核根因及§2改动，再决定是否另行申请/登记C++修复或其他路线。当前授权不允许修改其实现或将Z-A悄然改成direct。
- 当前负责人Codex；状态blocked，等待Claude决定。无本任务后台运行进程，无监控/恢复任务；恢复时先读本节及独立日志、重核占用/冻结文件。


## Claude复核R2（2026-10-13）

- **§2通过**：diff只改`eval_task6_final.py`的两个可选参数和配置记录；缺省路径不变；19项单元测试通过。运行回归5/5场景哈希、done、内部成功一致；前4个episode步数不同，属于Gazebo自由运行的非确定性（PROCEDURE已规定不作失败判据）。
- **§3失败根因核实**：Claude重读`mobile-rl/src/myutils.cpp` L424–432：`calcDesiredBaseCommandDiffDrive`在计算前无条件`throw runtime_error("Not implemented for diff-drive yet")`，上游与本项目相同。这是Claude在TASK中把`track`写成Z-A配置的错误：§1只核到调用链，Claude也没有核实现体。
- **上游对差速底盘的实际做法**：上游唯一的差速机器人是TIAGo（`robotenv.py` L142–146 `drive="diff"`）。`robot_env.cpp` L240：`if ((execute_style == "direct") || (robot_config_.name == "tiago"))`，即TIAGo无论`execute_style`取何值都走`direct`。所以原论文项目中差速底盘的Gazebo测试实际执行方式是`direct`；`track`只用于全向底盘（PR2、HSR）。
- **T63-D2**：Z-A改为`execute_style=direct`，其余不变（`ik_fail_thresh=50`、`--max-steps 100000`、超限计失败、自由运行）。这与上游对差速底盘的实际行为一致，不改C++，不是“悄然改成direct”，已在TASK中标注。Z-A与Z-B现在只差评估IK阈值（50/20）和episode上限（100000/2000）。
- **冒烟重做**：新run-id `t6.3-smoke-r2-{A,B}`，F0-s0，种子2001–2003。r1证据保留，不计入。Z-A检查：底盘运动，IK失败超过20时episode不终止，无errored。
- 注意：r1中Z-B种子2002跑满2000步（capped）。R-48在task6.1中capped为0，F0策略在Gazebo中可能跑得更久；§5须报告Z-B的capped数，并与Z-A“2000步内成功”口径并列。
- 放行：§3重做（r2）→§4→§5。依据[SRC-0254](../../../SOURCES.md#src-0254)。


## Codex R2接回：§3 r2 → §4 → §5最终交付（2026-10-13T18:55:37.246739+08:00）

依据：[SRC-0254](../../../SOURCES.md#src-0254)、[SRC-0255](../../../SOURCES.md#src-0255)。推荐Codex GPT6.1sol、Claude Sonnet5.5，执行/汇总low或默认（步骤明确）；实际精确模型及强度未知。本轮不改源码/测试/C++，不训练、不改任务/奖励/物理步长、不触碰G-B。r1证据保留不计入。

### r2门槛

A direct/IK50：655/2344/761步，0errored，最大底盘位移>0；种子2002非终止IK49、最终IK50，满足>20仍继续的门槛。B direct/IK20：651/2000/362步、0errored、capped1。两条start/eval/stop均0，清理无残留；[smoke_r2_checks.json](../../../../results/task6/t6.3-baseline/smoke_r2_checks.json)。

### 正式结果（每run分母50）

|run|实例/GPU|内部成功|Wilson95%|物理成功|completed/capped/errored|碰撞episode|含IK失败episode|IK阈值终止|平均步数|
|---|---|---|---|---|---|---|---|---|---|
|t6.3-zs-A-s0|60/cuda:0|8/50|[0.083,0.285]|3/50|50/0/0|2|41|37|1074.16|
|t6.3-zs-A-s1|61/cuda:1|13/50|[0.159,0.396]|7/50|50/0/0|2|36|34|1128.18|
|t6.3-zs-A-s2|62/cuda:2|9/50|[0.098,0.308]|5/50|50/0/0|3|40|38|1166.82|
|t6.3-zs-B-s0|63/cuda:0|7/50|[0.070,0.262]|5/50|47/3/0|0|41|39|755.50|
|t6.3-zs-B-s1|64/cuda:1|10/50|[0.112,0.330]|5/50|48/2/0|0|39|38|777.66|
|t6.3-zs-B-s2|65/cuda:3|7/50|[0.070,0.262]|2/50|46/4/0|2|39|36|893.56|

### 步数上限与IK分布（T63-D1/D2）

|Z-A run|>2000步回合|其中内部成功|2000步内内部成功/50|IK次数0 / 1–19 / 20–49 / >=50|
|---|---|---|---|---|
|t6.3-zs-A-s0|5|1|7/50|9 / 2 / 2 / 37|
|t6.3-zs-A-s1|8|2|11/50|14 / 0 / 2 / 34|
|t6.3-zs-A-s2|8|0|9/50|10 / 0 / 2 / 38|

Z-A完整内部成功均值0.200，2000步内口径7/11/9，均值0.180；Z-B完整7/10/7，均值0.160，capped3/2/4共9（仍计失败）。Z-A >2000步共21回合，其中内部成功3，不能把Z-A全部收益归因于IK阈值。两组同为direct，实际差异是IK阈值与回合上限；within2000只是终点结果事后筛选，不是新的配对重跑。精确IK计数直方图在comparison.json。所有正式回合均未超过20000步，最大3865；无6h报告线触发。

### 47种子敏感性及场景

|组|内部成功（三条，各/47）|均值|物理成功（三条，各/47）|
|---|---|---|---|
|Z-A|8/13/9|0.212766|3/7/5|
|Z-B|7/10/7|0.170213|5/5/2|
|F0 sim|20/20/22|0.439716|N/A|
|R-48|2/1/5|0.056738|0/0/3|

本轮六份与R-48旧三份Gazebo场景哈希在50个种子上全一致；和sim仍只有既知2006/2012/2021分叉，未查根因。47种子口径中Z-B capped为2/1/4（50种子主口径为3/2/4），完整计数见comparison.json。

### 命令、版本、资源与清理

- 六条原始[eval.json目录](../../../../results/task6/)：t6.3-zs-{A,B}-s{0,1,2}；原始评估日志在logs/task6同run/；ROS/Gazebo实例日志按现有入口在logs/task4/<run>/instN（已披露，不改启动器）。各run的launch.sh是准确命令事实来源。
- 实际命令共同部分：forem-dev entrypoint → scwm_instance.py start/exec/stop；python3 -u -W ignore scripts/eval_task6_final.py --world gazebo --device cuda:G --policy results/task6/t6.1-sim-plain-sS/ckpt/policy_step01000000.pt --seeds 2001,...,2050 --execute_style direct --ik_fail_thresh T --max-steps M --out results/task6/RUN/eval.json。A T50/M100000，B T20/M2000；全部确定性动作，每种子一个episode。
- 实例60–62 / GPU0–2为A-s0–s2；实例63–65 / GPU0/1/3为B-s0–s2。六条start/eval/stop各0、首次完成，无正式失败重跑；每实例residue=[]、两端口free。六个Python计算进程真实GPU占用各约708 MiB，进程映射在formal_gpu_processes.txt/formal_docker_top.txt；没有将cuda可用性当吞吐收益。
- 源码/策略sha、逐run有效配置、准确命令/启动脚本sha、原始eval.sha、实例/GPU、起止时间及偏差：[manifest.json](../../../../results/task6/t6.3-summary/manifest.json)。本轮首尾冻结哈希全部一致，复用§2脚本，无再次改码。镜像ID在logs/task6/t6.3-baseline/forem_dev_image.txt，未重建环境。
- 全局runner墙钟2079 s（34.65 min），累计runner 11285 s（3.135 h），累计逐episode评估段11126.49 s；包含范围不同，runner含启动/清理，评估段含reset/rollout，不作训练规模/性能承诺。
- 最终forem-dev仅docker-init/sleep，见final_docker_top.txt；不对forem-t6-husky-gz执行任何命令、不干预G-B、不停止非本任务进程。当前无本任务后台工作。

### 核验、结论与交接

- 从12份原始eval.json重算50/47分母，逐run与eval.json的内部成功/碰撞/IK/capped汇总交叉核对；六份配置、种子列表、episode_hash与spec.hash一致；冻结源码与策略sha复核通过；清理逐run核查通过。[comparison.json](../../../../results/task6/t6.3-summary/comparison.json)与[verification.json](../../../../results/task6/t6.3-summary/verification.json)。
- 首次统计因历史sim碰撞计数为数字字符串发生TypeError，读取全部相关字段类型后用int转换；不修改原始数据或评估源码。第二次生成及独立计数交叉验证通过。
- Wilson95为每run的描述区间，公式/输入见SRC0255；三种子均值不当150独立场景，不做显著性检验。物理成功单列；6正式run正常终止回合均有valid物理反馈，capped仍失败，不将规划状态代实际反馈。
- **结果解读**：同一批F0策略在sim内部成功均值0.433，Gazebo Z-B0.160、Z-A0.200，分别低27.33、23.33个百分点；47种子口径方向相同。sim策略能在部分Gazebo任务中成功，但本次未保持sim水平。符合TASK两组均较低的描述性分支：更宽评估IK阈值/上限没有消除执行环境差异。Z-B比R-48高10.67个百分点，但不能据此把Task4.8失败全部归因于训练环境。
- **限制**：Z-A/Z-B同时差IK阈值和episode上限，自由运行不保证逐位确定；没有拆分具体执行因素、没有证明哪项产生多少损失；上游机器人/任务与Husky不同，direct来自TIAGo代码推导，不能称论文完整复现。历史3场景分叉保留，不越范围调查；不实施任何额外对照、WM或训练。
- **交接**：Codex交付§5，RESULTS review；Claude从本节、原始JSON、源码sha及T63-D1/D2独立复核。通过后才能标done；本轮不自动开展后续工作。


## Claude复核R3（2026-10-13，§3 r2–§5）

- **独立复算通过**：Claude从6份原始`eval.json`重新统计，与Codex一致：Z-A内部成功8/13/9（均值0.200）、物理3/7/5、capped 0、errored 0、>2000步5/8/8、2000步内成功7/11/9、最长3865步；Z-B内部7/10/7（0.160）、物理5/5/2、capped 3/2/4、errored 0。50个种子2001–2050齐全；六份`effective_config`与T63-D1/D2一致（全部direct，A为IK50，B为IK20，window None）；策略sha256与task6.1 F0一致。47种子口径结果相同（3个分叉种子在这6条中均未成功）。
- **补充配对统计**（47个两侧场景一致的种子，F0 sim对Z-B）：两侧都成功4/6/5，只在sim成功16/14/17，只在Gazebo成功3/4/2。损失主要来自sim中能成功的场景在Gazebo中失败，不是噪声互换。
- **结论**（同一组种子，三种子均值，内部成功）：
  1. **sim策略能部分迁移，但损失很大**：sim 0.433 → Gazebo 0.160（Z-B）/0.200（Z-A），下降23–27个百分点，远大于N²M²原文的0.3–9个百分点（SRC-0249，机器人与任务不同，只作量级参考）。按TASK解读表属第三种情况：**Gazebo执行本身让同一策略明显失效**。IK失败终止从sim的18/21/20升到Gazebo的39/38/36（Z-B），是主要失败形式。
  2. **在Gazebo里训练又带来额外损失**：评估配置完全相同时，sim训练的策略0.160（Z-B），Gazebo训练的Task4.8策略0.053（R-48），差约11个百分点。
  3. **原论文的宽松评估设置帮助有限**：IK阈值50与100000步上限使成功率从0.160到0.200；按2000步内口径为0.180。
  4. 合起来：Task4.8失败是**两部分叠加**——Gazebo执行条件使同一策略损失约27个百分点，在Gazebo中训练再损失约11个百分点。具体是哪一项执行因素（观测滞后、底盘加速斜坡、机械臂跟踪、激光局部地图、每步时长等）导致IK失败增加，本任务未拆分。
- **限制**：每侧3个种子×50个episode，无显著性检验；Z-A/Z-B同时差两项；Gazebo自由运行不逐位确定；Husky不是原文机器人，direct来自TIAGo代码推导。
- **状态**：task6.3 done。按TASK解读表，下一步拆分执行因素须另行请示用户，本轮不自动开展。依据[SRC-0256](../../../SOURCES.md#src-0256)。
