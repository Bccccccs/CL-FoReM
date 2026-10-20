# task5.2 Husky原版`main_ray.py` + husky_ur5：sim训练与验证 — 结果与交接

> **当前状态（2026-10-19核对）：done（task5.3 R13最终复核通过）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**done（2026-10-14 Claude task5.3 R13最终复核通过）**。原状态：**review（D21/D22/D23最终9任务评估及证据交付，待Claude5.3独立复核）**。由执行者（Codex）按[PROCEDURE](PROCEDURE.md)逐节填写，不得把计划写成结果。

## 1. 构建与环境

见[task5.0 RESULTS](../task5.0/RESULTS.md)，本节点只记录使用的工作区与补丁清单版本：尚未执行。

## 2. ROS与冒烟（t5.2-smoke-r1）

尚未执行。需记录：launch节点/参数、吞吐、预计时长、9任务可运行性。

## 3. 正式训练（t5.2-train-s40）

尚未执行。需记录：命令、PID、起止、退出码、与5.1生效配置的逐项差异（预期只有env及husky_ur5 best_defaults段差异）。

## 4. 训练中评估序列

尚未执行。

## 5. 最终9任务sim评估（t5.2-eval-r1）

|任务（表III名称）|代码任务名|episode数|成功率|能否运行/原因|
|---|---|---|---|---|
|rnd obstacle|simpleobstacle|—|尚未执行||
|p&p|picknplace|—|尚未执行||
|bookstore p&p|bookstorepnp|—|尚未执行||
|dynamic obstacle|dynobstacle|—|尚未执行||
|dynamic p&p|picknplacedyn|—|尚未执行||
|cabinet|door|—|尚未执行||
|drawer|drawer|—|尚未执行||
|door|roomdoor|—|尚未执行||
|spline|spline|—|尚未执行||

## 6. 偏差清单与限制

尚未执行。

## 交接

尚未执行。

## Agent模型与推理强度

推荐：Codex GPT6.1sol/medium（卡住条件满足时才用gpt-6-astra/high）；Claude替代Sonnet5.5/medium。实际：待执行者记录。

## 接手 2026-10-11T22:38:51.734475+08:00

已核查5.0通过R4/URDF D4/就绪；使用forem-t5-husky及ws_husky，不另构建。GPU0/offline D8，D9地图来自SRC0217/实测SRC0218，D5原样。指定gpt-6.1-sol/medium，实际不可独立核实；Claude推荐Sonnet5.5/medium。A正式已启动，B可以冒烟/通过后并行正式。

### r1运行包装失败（非新构建问题），重跑r2

r1训练初始化退出1，launch日志resource not found lms1xx，kinematics缺失。本Agent遗漏5.0就绪运行的ROS_PACKAGE_PATH=/forem_build/deps/lms1xx:$ROS_PACKAGE_PATH；依赖已在5.0准备且就绪验证，不新装/构建/改源码。仅补回已批准路径并加包装的参数存在检查，r2从头冒烟。r1失败保留，自身roscore SIGINT（PID见cleanup.json），没有停止容器或A。来源[SRC-0212](../../../SOURCES.md#src-0212)的r4_launch_husky.py与r1 analytical/train.log。

B首轮失败与r2已有路径复用的实测依据[SRC-0219](../../../SOURCES.md#src-0219)。

### r2训练冒烟通过，九任务评估进行中

5000步退出0，耗时263.329s，吞吐18.988步/s，百万步线性约14.629h（与A正式并行时的短程测量，不承诺长期吞吐）。2000/4000步评估执行，成功率见training_smoke_summary.json。D6：无CLUB Saved、无club_checkpoints文件、无CUDA/AttributeError错误；learning_starts0。runtime_config.json实际新建环境只核查配置（未reset/采集/训练）确认spacing3.0/offset_std.8，与env_config中传入1.75/.4375区别披露，不改D5原样行为。D8 offline目录/日志有，D9地图保留。评估使用本run local_model/checkpoint-5；九任务通过前不启动正式B。来源[SRC-0219](../../../SOURCES.md#src-0219)。

## r2冒烟最终停止与交Claude 2026-10-11T22:55:17.639695+08:00

**blocked：bookstorepnp首reset无法采出无碰撞起始/目标，九任务门槛未通过；t5.2-train-s40尚未启动。**依据[SRC-0220](../../../SOURCES.md#src-0220)。

B r2训练5000步正常退出0、learning_starts0、真实spacing3.0/offset_std.8，D6无CLUB Saved/CLUB文件/CUDA/AttributeError。吞吐18.988步/s，1M线性14.629h（A同时训练的短程推导）。simpleobstacle评估1episode退出0、picknplace上游两朝向各1episode退出0。bookstorepnp在首次reset累积10000/20000/30000次采样，第一次reset报RuntimeError Could not draw a goal without collision并进入原版10次reset重试；未进入episode。

按用户“未覆盖问题停止报告”，停止本任务评估PID24187，未继续完成全部reset重试，不改任务/地图/碰撞/目标/种子。不启动B正式，后续dynobstacle/picknplacedyn/door/drawer/roomdoor/spline未执行。完整日志eval-bookstorepnp.log、停止收据eval-bookstorepnp-stop.json、退出文件（产生后）eval-bookstorepnp.exit；容器仍保留。

地图aws_bookstore.png存在，区别于A先前roomdoor缺图；D9的modulation_tasks.png已补且墙叠加合理。尚未区分失败来自底盘/EE/路径/目标碰撞或可达条件，不凭日志认定单一原因；只读源对应map.py draw_startpose_and_goal及combined_env.reset。Claude决定下一步诊断/允许偏差前，不调整原样合同。

A t5.1-train-s40继续授权运行，主机CPU峰约17.352核（当前观测，不是B正式并行验收）；A CPU/30分钟记录与已批准§4–6后处理监督继续，monitor/posttrain PID见A目录，task5.1.1子Agent低强度监控。没有停止任何容器或非本任务进程。

交接：负责人Codex停止B并交Claude；先审bookstorepnp起始采样失败与原样D5合同，明确后续授权后使用新run或追加评估证据，不覆盖r1/r2失败。A仍active，Bblocked，不提前置review/done。

停止最终收据：B评估PID24187 SIGINT未退出reset循环，随后SIGTERM退出143（主动停止，不是自然跑完重试）；包装遇非零退出，后续任务未启动。未使用SIGKILL、未停止ROS或容器。停止收据与最新docker top核验保留r2。

## R7/D10/D11接手 2026-10-11T23:06:49.080675+08:00

用户授权bookstorepnp不作为冒烟门槛；r3只六任务，各1episode，加载r2 local_model/checkpoint-5，r2训练/D6/两已评估任务沿用；通过后B正式1M/seed40/GPU0/20worker与A并行。最终bookstore原版完整入口一次、保留10reset重试，墙钟最多1800秒，不改任务/碰撞；失败N/A、不入成功率，8可运行平均及9任务含N/A口径均报告。CPU D11只告警，任何情况下不自动停止训练。模型指定GPT6.1sol/medium，实际精确型号/强度未知；Claude推荐Sonnet5.5/medium（跨运行合同），监控子AgentGPT6.1sol/low。

R7/D10/D11当前授权与运行包装依据[SRC-0221](../../../SOURCES.md#src-0221)，旧自动中止条款撤销；最终bookstore不可运行不填0，9任务含N/A口径与8平均分开。

### r3六任务门槛通过，B正式启动 2026-10-11T23:09:53.221330+08:00

六任务各1episode退出0，smoke_gate.json；bookstore依D10不挡门槛，r2训练及两已跑任务沿用。t5.2-train-s40正式启动，冻结1M/seed40/20worker/GPU0/TI.1，LMS路径保留，D5/6/8/9/10/11不改变训练科学合同。完整命令launch.json/t52_formal.sh，日志logs/task5/t5.2-train-s40/train.log，train.pid容器PID；D11监控主机PID2264737、生效时间2026-10-11T23:09:53.221330+08:00、命令python3 -u forem/build/task5/monitor_task5_train.py t5.2-train-s40 forem-t5-husky task5.2，CPU只告警。A继续不重启。后续§4–6仍未完成；来源[SRC0221](../../../SOURCES.md#src-0221)。

2026-10-11T23:10:26.359807+08:00 后处理监督器已就绪；等待训练正常退出，不续训、不提前评估。

2026-10-11T23:13:10.696622+08:00 后处理监督器已就绪；等待训练正常退出，不续训、不提前评估。

### 正式生效配置与监督 2026-10-11T23:15:17.578172+08:00

train容器PID36511；主机D11 monitor2264737、生效23:09:53，后处理posttrain2282978。`effective_config_check.json`显式冻结值通过（1M/seed40/20worker/GPU0/TI.1/nr_eval50/eval_seed999/learning_starts0），与A完整原始配置差异为env/learn_torso/logpath/group及moveit_max_waypoint_distance/moveit_range/articulated_jv_delta，best_defaults_A_B_diff.json逐项原值；B默认10M由命令覆盖1M。不调整快照语义。

父后处理命令`python3 -u forem/build/task5/task5_posttrain.py task5.2 forem-t5-husky husky_ur5 /forem_build/ws_husky`，等待训练正常退出且≥1M，才执行§4–6；D10 bookstore命令前缀`timeout --signal=KILL 1800`，保留原版reset重试不变；只在原版10reset采样耗尽或墙钟超限且已知采样失败时记不可运行，其他错误停止报告。8个可运行标准分支均值，9任务表含N/A/覆盖8/9，完整9均值N/A，不把不可运行当0。额外pnp朝向单列原始指标。

监控子Agenttask5.2.1 gpt-6.1-sol/low已核查训练/监控/后处理存活，按30min继续独立记录；A不重启。当前§4–6尚未实际完成，状态active。来源[SRC-0221](../../../SOURCES.md#src-0221)。

2026-10-12T15:53:12.362000+08:00 训练退出0，1000000步；训练评估序列已导出，最终本地模型/forem_results/t5.2-train-s40/local_model/checkpoint-1000。开始默认50episode/seed999九任务评估。

2026-10-12T15:56:35.509678+08:00 最终评估simpleobstacle退出0，保留原stdout/offline数据。

2026-10-12T16:08:50.540259+08:00 最终评估picknplace退出0，保留原stdout/offline数据。

2026-10-12T16:38:50.785584+08:00 D10 bookstorepnp原版完整入口运行一次失败/30min上限终止，记不可运行，不计成功率；继续其他已授权任务。

2026-10-12T17:07:57.021457+08:00 最终评估dynobstacle退出0，保留原stdout/offline数据。

2026-10-12T17:48:33.724284+08:00 最终评估picknplacedyn退出0，保留原stdout/offline数据。

2026-10-12T17:54:37.523736+08:00 最终评估door退出0，保留原stdout/offline数据。

2026-10-12T17:59:48.435570+08:00 最终评估drawer退出0，保留原stdout/offline数据。

2026-10-12T18:07:31.033316+08:00 最终评估roomdoor退出0，保留原stdout/offline数据。

2026-10-12T18:12:14.190327+08:00 后处理停止，待Claude决策：AssertionError('final evaluation spline failed rc=1')

## D21/R11补评估 t5.2-eval-r2 接手/复现（2026-10-14T00:34:59.579524+08:00）

用户授权按Claude D21/R11使用新r2补B spline；B其他完成任务不重跑，bookstorepnp按D10 N/A。实际模型/强度未知；推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（逐回合确定性、拼接/原始指标核对），监控/文档low或默认。

种子999单回合已自然退出1，再次20001步触发同一assert，无Eval ep完成行，R11核查符合；i=0按既定口径记失败。原始log：`logs/task5/t5.2-eval-r2/check-spline-seed999-n1.log`，完整命令、起止、rc1与pid在`results/task5/t5.2-eval-r2/commands.json`，空回合列表`check-spline-seed999-n1-episodes.json`。[SRC-0261](../../../SOURCES.md#src-0261)

B独立补跑已启动seed1000、nr_evaluations49；A因第2(a)步数3/8不一致停止，不推进A后续。补充脚本`build/task5/task5_d21_eval.py`、`task5_d21_complete_b.py`；脚本stdout由本聊天exec会话86797监控，逐调用命令/host_sg_pid/日志以commands.json为准（不可把会话号当容器PID）。监控：`tail logs/task5/t5.2-eval-r2/continue-spline-seed1000-n49.log`；CPU只读监控`build/task5/task5_d21_cpu_monitor.py`，host PID见A r2 `cpu_monitor.pid`，每5秒数据A r2 `host_cpu_5s.jsonl`。不发送信号给训练；发现未覆盖异常不续跑。恢复须先Claude决策，当前脚本不允许覆盖已有同名log。

软链切换前后在`output-link.log`：原`/forem_results/t5.2-eval-r1`→新`/forem_results/t5.2-eval-r2`；保留新链接以避免写r1。最终结果/汇总尚未完成，不标review或done。

## D21补评估收尾 — blocked（2026-10-14T00:57:15.939110+08:00）

**B spline已按D21补齐50回合，0/50成功；最终9任务交付未完成，不置review/done。** 47自然结束回合均失败；999、1000、1036三超限各计一次。r1 i=0和r2 seed999复现不重复计数。[SRC-0263](../../../SOURCES.md#src-0263)

|eval_seed|nr_evaluations|开始(+08)|结束(+08)|退出码|日志（logs/task5/t5.2-eval-r2/）|
|---|---|---|---|---|---|
|999|1|2026-10-14T00:27:27.092996+08:00|2026-10-14T00:32:08.941509+08:00|1|`check-spline-seed999-n1.log`|
|1000|49|2026-10-14T00:33:56.612792+08:00|2026-10-14T00:38:37.104248+08:00|1|`continue-spline-seed1000-n49.log`|
|1001|48|2026-10-14T00:38:37.110042+08:00|2026-10-14T00:48:54.130152+08:00|1|`continue-spline-seed1001-n48.log`|
|1037|12|2026-10-14T00:48:54.138341+08:00|2026-10-14T00:51:34.633779+08:00|0|`continue-spline-seed1037-n12.log`|

拼接：i=0/seed999超限（r1保留/r2复现）；i=1/1000超限；i=2–36/1001–1035共35自然失败；i=37/1036超限；i=38–49/1037–1048共12自然失败。末段stdout0/12与`continue-spline-seed1037-n12-offline.json`的`spline/success=0.0`一致；assert中断段在汇总前退出，没有原始汇总，完整回合按Eval ep保留，不能伪称缺失指标已核验。

证据：r2 `commands.json`完整shell命令、起止、rc、pid、log；`spline_episode_ledger.json`逐seed账本；`spline_segments.json`段收据/末段raw指标；`spline_completion_check.json`重新50行核查。[SRC-0263](../../../SOURCES.md#src-0263)

**未覆盖异常：** 补齐后原`export_wandb_offline.py`读取原r1、输出目标新r2，退出1，`offline_r1_raw_export.log`显示DataStore checksum断言失败。具体源文件未定位，未重新尝试/跳过/截断/修复，导出器不改。因此原r1九任务指标/fwdO交叉核验、8可运行均值与9任务含N/A口径、最终`final_eval_summary.json`均尚未交付。无最终JSON，不将未核验结果包装完成。

仅供Claude核查的旧stdout（**未完成r1 W&B交叉核验**）：simpleobstacle39/50、picknplace标准8/50（fwdO4/50）、dynobstacle22/50、picknplacedyn7/50、door13/50、drawer10/50、roomdoor0/50；bookstorepnp按D10 N/A。父2026-10-13粗读picknplace0.08为fwdO，不能当标准分支。正式均值未交付。[SRC-0263](../../../SOURCES.md#src-0263)

B登记源/配置/模型/r1集合210文件、A82文件SHA前后一致，`source_model_r1_unchanged.json` changed=[]。新软链保持r2，r1及训练posttrain_status历史不覆盖。CPU监控通过自身stop文件自然退出0，300样本峰22.199核/均9.364核/>56为0，证据在A r2 `host_cpu_5s.jsonl`/`cpu_sampling_summary.json`。最后两task5容器无评估进程，只有原ROS；不清理ROS/容器，不触碰task6.2/forem-dev。

交接：Codex停止推进；Claude先决定B旧离线数据核验异常及A确定性门槛失败的处理。B无需重跑已补齐spline（仅为交接建议，不构成新重试授权）；剩余九任务原始指标/朝向/均值与最终汇总，随后才置review交5.3。实际模型/强度未知；推荐GPT6.1sol/Sonnet5.5 medium（跨日志/指标合同核对），常规文档low/默认。

## D23最终汇总 — review（2026-10-14T08:35:49.530624+08:00）

遵循R12/D23，原B评估不重跑。最终文件 `results/task5/t5.2-eval-r2/final_eval_summary.json`，9任务标准成功数依序39/50、8/50、N/A、22/50、7/50、13/50、10/50、0/50、0/50；8可运行均值24.75%，9任务表覆盖8/9、bookstorepnp N/A、完整9均值N/A。pnp fwdO4/50单列，不与标准8/50混用；bookstore两朝向无完成回合N/A。[SRC-0267](../../../SOURCES.md#src-0267)

D23逐文件导出13个，12可读；唯一不可读 `run-1peniqus.wandb`（完整位置见summary），checksum AssertionError，原wandb-metadata.json args关联bookstorepnp。该任务依D10 N/A；未修复/截断/使用部分记录。七个已完成r1任务与fwdO原始success全部与逐行stdout一致，spline末段12回合success0.0一致；前35回合因上游assert没有汇总，stdout-only披露，三个超限按D21记失败。文件报告`d23_offline_file_report.json`、逐文件`d23_exports/`、核对`d23_episode_metric_checks.json`及完整收据`commands.json`。[SRC-0267](../../../SOURCES.md#src-0267)

本状态覆盖此前checksum整体读取blocked，保留历史失败。推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（逐文件指标合同核对），实际模型/强度未知。B交付review，不标done；A补跑仍执行，整体待A完成后交Claude5.3。

## 2026-10-14T08:54:42.608553+08:00 D22/D23最终交付 — review，交Claude

最终结果：`results/task5/t5.2-eval-r2/final_eval_summary.json`；stdout为主口径，逐回合累计成功差分及seed账本重新核对；W&B逐文件可读则核对，错误完整披露，不修复/截断。原r1与旧r2记录保留。[SRC-0268](../../../SOURCES.md#src-0268)

|标准任务|成功数|分母|成功率(%)|
|---|---|---|---|
|simpleobstacle|39|50|78.0|
|picknplace|8|50|16.0|
|bookstorepnp|N/A|N/A|N/A|
|dynobstacle|22|50|44.0|
|picknplacedyn|7|50|14.000000000000002|
|door|13|50|26.0|
|drawer|10|50|20.0|
|roomdoor|0|50|0.0|
|spline|0|50|0.0|

可运行任务均值：24.750000%；9任务均值：N/A。B八可运行均值24.75%，完整9均值N/A、覆盖8/9，不把bookstorepnp当0。A完整九任务均值是标准朝向均值；fwdO单列：

- picknplace fwdO：4/50。
- bookstorepnp fwdO：N/A（无完成回合）。

拼接/超限seed/原始指标及逐文件错误见JSON splice/metric_checks/WandB_unreadable_files。A door38+11=49/50，1037按原r1失败固定计分，复跑结果仅诊断；8回合门槛只按D22成功标记通过，不重复计入最终50。B spline0/50沿上一轮47自然失败+三超限，不重跑。assert中断段没有上游汇总指标，stdout-only如实披露。[SRC-0268](../../../SOURCES.md#src-0268)

交付证据：commands.json（命令/起止/rc/log/pid）；逐seed账本与段收据；d23_offline_file_report.json/d23_exports/（每文件原始数据或完整错误）；d23_episode_metric_checks.json（可用success均一致）；source_model_r1_d22_d23_unchanged.json；handoff_verification_d22_d23.json/evidence_d22_d23_sha256.json。登记A82/B210文件SHA未变。新软链仍r2，无写入r1；原训练posttrain_status历史不覆盖。

CPU续跑274样本峰25.392核/均12.635核，>56为0，A r2 cpu_d22_sampling_summary.json；监控已停止，仅自己的stop文件，不干预训练/外部容器。无活动评估，原ROS保留。负责人Codex交Claude5.3，下一步独立复核上述表/拼接/朝向/错误/限制后才可done；本执行者不标done。实际模型/强度未知，GPT6.1sol/Sonnet5.5 medium推荐、文档low/默认。[SRC-0268](../../../SOURCES.md#src-0268)
