# task5.1 上游N²M² + PR2：sim训练与验证 — 结果与交接

> **当前状态（2026-10-19核对）：done（task5.3 R13最终复核通过）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**done（2026-10-14 Claude task5.3 R13最终复核通过）**。原状态：**review（D21/D22/D23最终9任务评估及证据交付，待Claude5.3独立复核）**。更早的状态：D8决策后重跑r3。原状态：blocked（冒烟W&B离线API key检查失败）。由执行者（Codex）按[PROCEDURE](PROCEDURE.md)逐节填写。不得把计划写成结果。

## 1. 环境

见[task5.0 RESULTS](../task5.0/RESULTS.md)，本节点只填写实际使用的GPU口径与并行方式：尚未执行。

## 2. 冒烟（t5.1-smoke-r1）

尚未执行。需记录：ray/wandb输出位置、吞吐（env步/秒）、100万步预计时长、9任务评估冒烟结果。

## 3. 正式训练（t5.1-train-s40）

尚未执行。需记录：容器、PID、命令、起止时间、退出码、生效配置比对结果、监控记录。

## 4. 训练中评估序列

尚未执行。

## 5. 最终9任务sim评估（t5.1-eval-r1）

|任务（表III名称）|代码任务名|episode数|成功率|原文PR2|
|---|---|---|---|---|
|rnd obstacle|simpleobstacle|—|尚未执行|86.0|
|p&p|picknplace|—|尚未执行|97.6|
|bookstore p&p|bookstorepnp|—|尚未执行|70.0|
|dynamic obstacle|dynobstacle|—|尚未执行|84.4|
|dynamic p&p|picknplacedyn|—|尚未执行|81.6|
|cabinet|door|—|尚未执行|97.2|
|drawer|drawer|—|尚未执行|97.6|
|door|roomdoor|—|尚未执行|98.4|
|spline|spline|—|尚未执行|80.8|
|平均|—|—|尚未执行|88.2|

原文数值来自表III，是5个种子的平均（[SRC-0198](../../../SOURCES.md#src-0198)）。本项只有单种子，不能当作复现结论。

## 6. 偏差清单与限制

尚未执行。

## 交接

尚未执行。

## Agent模型与推理强度

推荐：Codex GPT6.1sol/medium；Claude替代Sonnet5.5/medium。实际：待执行者记录。

## 开工 2026-10-11T21:56:25.112956+08:00

Claude R4已核验5.0 done；使用forem-t5-pr2，GPU0/offline、D2已替换；D3暂默认先后，待5秒CPU实测。指定gpt-6.1-sol/medium，实际不可独立核实（未知）；Claude推荐Sonnet5.5/medium。开工三个容器仅保活，未触碰其他容器。

### 冒烟r1失败 / D7执行

训练初始化退出1，learning_starts=None触发replay_buffer.py的NoneType // int。已按D7改容器内ray_utils.py为0，前后源码/SHA/diff保存在results/task5/t5.1-smoke-r1/{ray_utils.before.py,ray_utils.after.py,d7.diff,d7_manifest.json}。r1未训练，无checkpoint；主机采样器首次未存活、无有效样本，不用于D3，修正运行包装后重跑t5.1-smoke-r2。参考mobile-rl不改。依据[SRC-0213](../../../SOURCES.md#src-0213)，实际生效0待r2验证。r2包装启动首次缺脚本（前置汇总失败，尚未启动训练），失败stdout保留。

## 最终停止与交Claude（2026-10-11T22:00:36.774146+08:00）

状态：blocked（明确依赖Claude对未覆盖W&B问题决策；未通过冒烟，不进入§3）。来源：[SRC-0214](../../../SOURCES.md#src-0214)。

- r1退出1：learning_starts=None；D7已执行，SHA/diff及原源码保留r1。
- r2退出1：learning_starts实际生效**0**（trial params.json）；`ray_wandb.py:68 → ray/tune/integration/wandb.py:178 _set_api_key`报`ValueError: No WandB API key found`。WANDB_MODE=offline未绕过该检查。没有新增key、登录/上传或修改W&B代码。
- r2主机CPU每5秒：5样本，峰值9.735核，均值4.879核。**D3结论：未建立**；这只是初始化失败前后的采样，没有训练负载，不可据≤32核放行5.2并行。默认先后口径保留；5.2未启动。
- 未检出CUDA运行错误；存在sm120不兼容警告（沿5.0），初始化在训练前失败，不能宣称完整CPU训练路径已验收。
- 有效训练步0，无checkpoint；吞吐/百万步预计时长、训练中评估、9任务model_file冒烟均未获得。正式t5.1-train-s40及最终评估尚未执行。

证据：`forem/results/task5/t5.1-smoke-r{1,2}/`及`forem/logs/task5/t5.1-smoke-r{1,2}/train.log`，r2 `smoke_summary.json`、`ray_wandb_key_check.txt`；原trial输出保留。完整命令保存在`forem/build/task5/t51_smoke.sh`和`t51_r2_smoke.sh`；容器内train PID分别1308、3587，exit_code.txt均1；主机CPU监控PID 2081725已在检测exit文件后退出。

容器保留，未停止任何容器。ROS自动启动的本任务roscore/analytical节点仍在，具体PID见r2 final_docker_top.txt；训练主进程已退出。没有正在运行训练，无需续训；Claude决策后用新冒烟run-id保留失败历史。后续命令launch_ros会检测已有ROS，不必重启容器。

交接：当前负责人Codex（停止交付），Claude需决策离线W&B集成如何通过API key前置检查，并明确允许偏差。收到新授权后重跑完整5000步冒烟/CPU/评估加载，门槛通过后直接正式百万步。

## R5/D8接手 2026-10-11T22:11:34.061665+08:00

用户授权清理本任务ROS后重跑r3；D7保留，D8三项离线，不改W&B/ray代码。依据[SRC-0215](../../../SOURCES.md#src-0215)。Codex指定gpt-6.1-sol/medium，实际不可独立核实；Claude推荐Sonnet5.5/medium（跨配置/本地恢复核查）。

### r3训练冒烟完成（九任务评估仍进行中）

训练达到5000步，退出0；checkpoint-5保存，2000/4000步各2 episode评估成功执行，成功率均0。D7实际learning_starts=0，GPU0，D8本地offline目录/日志已确认，无CUDA运行错误；api.wandb.ai连接核查仍待评估完成汇总。

**D3：训练阶段52个5秒样本，峰值10.351核，均值2.953核，峰值≤32核，满足Claude D3允许A/B并行的CPU条件。是否放行5.2由Claude决定，本Agent不启动5.2。**筛选起点按最终result timestamp减time_total_s，包含训练/评估及末尾退出采样；完整主机CPU记录保留，覆盖全部主机进程。

吞吐5000/247.451=20.206 env步/s，线性百万步约13.747小时；含本次Tune初始化/收尾265.63秒时按比例约14.757小时。是冒烟推算，不是工期承诺；正式50 episode评估、100k replay填满、周期checkpoint等成本尚未完整测量，可能变化。证据results/task5/t5.1-smoke-r3/training_smoke_summary.json与原始result.json/progress.csv/train.log。九任务model_file验证通过前不正式训练。依据[SRC-0215](../../../SOURCES.md#src-0215)，实测来源[SRC-0216](../../../SOURCES.md#src-0216)。

## r3最终交接 2026-10-11T22:22:38.752550+08:00

**blocked：roomdoor地图资源缺失，九任务门槛未通过。正式训练t5.1-train-s40未启动。**依据[SRC-0216](../../../SOURCES.md#src-0216)。

|冒烟任务|episode口径|退出码/结果|
|---|---|---|
|simpleobstacle|1|0/链路通过|
|picknplace|上游两朝向各1|0/链路通过|
|bookstorepnp|上游两朝向各1|0/链路通过|
|dynobstacle|1|0/链路通过|
|picknplacedyn|1|0/链路通过|
|door|1|0/链路通过|
|drawer|1|0/链路通过|
|roomdoor|环境创建失败，未完成episode|1/失败|
|spline|尚未执行（顺序入口遇错退出）|—|

失败链：`evaluation_ray → evaluate_on_task → RoomDoorChainedTask → ObstacleConfigMap → SceneMap → Map.load_map → assert Path(map).exists()`。`gazebo_world/worlds/modulation_tasks.yaml`存在，其image为`modulation_tasks.png`；容器对应PNG缺失，参考mobile-rl也缺失。只读证据`roomdoor_map_evidence.txt`和`eval-roomdoor.log`；未修改任务、未创建占位图、未替换地图。交Claude决定如何取得正确原始资源或其他明确方案。

D8：三项均已设置（40个0占位key），`wandb offline`输出只本地写metadata；生成训练/评估offline-run并有mode offline日志。训练5秒IPv4 TCP快照无remote443，全部本地W&B/train/eval日志未见api.wandb.ai连接尝试/成功/错误。观测结论为**未观察到连接尝试或成功连接**，无抓包，不能排除采样间短连接/IPv6。未登录、未上传、不改W&B/ray代码。

D7实际值0；训练与已跑评估未检出CUDA运行错误。训练5000步退出0（容器PID5839），checkpoint-5保存；两次训练中评估成功执行（成功率均0），不表示学习效果通过。

**D3有效结论仍为通过CPU条件：训练52个5秒样本峰10.351核/均2.953核，≤32核；是否放行5.2由Claude决定，当前未开始5.2。**吞吐20.206步/s、百万步13.747h（仅线性估计），Tune总时间比例14.757h；正式评估/回放填满/周期检查点成本限制同上。

本地加载文件在`results/task5/t5.1-smoke-r3/local_model/`；offline无原config.yaml，按5.0 §10已批准方式从该trial原始params.json逐项导出value格式，config_provenance.json记录来源。原始checkpoint/trial/offline记录保留；完整train/eval命令在`forem/build/task5/t51_r3_{smoke,eval}.sh`，日志`logs/task5/t5.1-smoke-r3/`。

清理r2记录：容器PID1321/1331/1342/1349/1367，分别roscore/rosmaster/rosout/roslaunch/move_group，SIGINT后只剩sleep；主机PID对应上一run top中的2078678/2078688/2078699/2078745/2078793。证据cleanup.json；未停止任何容器。r3结束本任务ROS仍在（final_docker_top.txt），无训练/评估进程。CPU采样器已在训练exit文件产生后自动退出。

下一步：Claude决策roomdoor缺失PNG；收到明确授权后补完九任务冒烟及其门槛，再直接正式训练，§4/5/6尚未执行，不提前置review。

## R6/D9接手 2026-10-11T22:34:36.096818+08:00

范围按用户最新授权，地图只读git show，不改参考仓库；GPT6.1sol/medium、Claude Sonnet5.5/medium（跨资源/合同核查），实际平台精确型号/强度未知。[SRC-0217](../../../SOURCES.md#src-0217)。

D9地图已补两位置，六墙叠加视觉吻合，无明显偏差；SHA/source/overlay见r4。源依据SRC0217、实测[SRC-0218](../../../SOURCES.md#src-0218)。r4仅roomdoor/spline加载r3模型，其他沿r3。首次r4包装尚未创建，docker exec-d返回未代表执行成功；缺脚本未启动评估，无覆盖证据。

### r4冒烟门槛通过，正式启动 2026-10-11T22:38:12.461553+08:00

roomdoor/spline各1episode退出0，结合r3七任务，全部九任务本地模型链通过。t5.1-train-s40已启动forem-t5-pr2，冻结1M/seed40/GPU0/20worker/TI.1，D7/D8/D9保留。完整命令launch.json与forem/build/task5/t51_formal.sh，日志logs/task5/t5.1-train-s40/train.log，PID文件results/task5/t5.1-train-s40/train.pid；结束前不声明验收。依据[SRC-0218](../../../SOURCES.md#src-0218)，训练新实测后续登记。

正式生效配置：effective_config_check.json通过冻结显式值；nr_evaluations=50/eval_seed999/evaluation_frequency75000，D7=0。监控脚本forem/build/task5/monitor_task5_train.py，主机PID见monitor.pid，每5秒host_cpu_5s.jsonl、每30分钟monitor_30min.jsonl及独立agent日志。对“持续>56核”采用保守连续两次5秒样本判定（不是科学参数/性能验收阈值变更）；触发后SIGINT本任务A/B train PID、写cpu_over56_alert.json并报告，不减worker，不停止容器/外部任务。无自动续训。当前未触发。正式训练在运行，§4–6待完成后执行。

正式启动/配置/监控实测依据[SRC-0219](../../../SOURCES.md#src-0219)。

2026-10-11T22:50:37.552155+08:00 后处理监督器已就绪；等待训练正常退出，不续训、不提前评估。

2026-10-11T22:51:59.584919+08:00 后处理监督器已就绪；等待训练正常退出，不续训、不提前评估。

### 2026-10-11T22:55:17.639695+08:00 长训监督/状态

A继续active，不因B冒烟采样失败自行停止A。train PID34861、host monitor2140918、posttrain2203635均存活，约18k/1M；最新精确进度以原trial与monitor记录为准。task5.1.1子Agentgpt-6.1-sol/low已登记并核查运行。父已部署后处理脚本等待exit0且>=1M，再导出训练中评估、最终九任务默认50episode并核对原始W&B指标与stdout成功计数，冻结manifest后review；失败则停止写blocked状态、不自动重训/续训。源依据[SRC0219](../../../SOURCES.md#src-0219)，B停止依据[SRC0220](../../../SOURCES.md#src-0220)。本条是运行安排，不把未来步骤当实测完成。

2026-10-11T23:05:54.995537+08:00 后处理监督器已就绪；等待训练正常退出，不续训、不提前评估。

## D11优先纠正（覆盖此前自动中止规则）

23:04:04+08新CPU监控2238780，命令`python3 -u forem/build/task5/monitor_task5_train.py t5.1-train-s40 forem-t5-pr2 task5.1`；old2140918仅监控进程已终止，A训练34861保持不变。规则连续5min时间加权均值>56，只alert/日志/RESULTS，不向任何训练发信号。A后处理新2243657也取消CPU告警失败门。变更SHA/生效时间/命令/PID与静态核查在monitor_D11_change.json/D11_verification.json，依据[SRC-0221](../../../SOURCES.md#src-0221)。历史双5秒自动SIGINT是过度解读，不再生效；此前没有超限触发停止训练。

2026-10-12T14:48:09.292652+08:00 训练退出0，1000000步；训练评估序列已导出，最终本地模型/forem_results/t5.1-train-s40/local_model/checkpoint-1000。开始默认50episode/seed999九任务评估。

2026-10-12T14:51:21.390605+08:00 最终评估simpleobstacle退出0，保留原stdout/offline数据。

2026-10-12T15:00:31.309311+08:00 最终评估picknplace退出0，保留原stdout/offline数据。

2026-10-12T15:47:26.345987+08:00 最终评估bookstorepnp退出0，保留原stdout/offline数据。

2026-10-12T16:09:38.258319+08:00 最终评估dynobstacle退出0，保留原stdout/offline数据。

2026-10-12T16:33:21.194033+08:00 最终评估picknplacedyn退出0，保留原stdout/offline数据。

2026-10-12T16:40:01.106930+08:00 后处理停止，待Claude决策：AssertionError('final evaluation door failed rc=1')

2026-10-12T17:12:58+08:00 Claude决策D21（用户授权“帮我做决策”）：door第39回合超限记为失败；先做确定性核查，再补跑种子1038–1048共11回合，拼接为50回合；然后继续drawer/roomdoor/spline。执行尚未开始，待派发。详见[task5.3 R10](../task5.3/RESULTS.md)、[SRC-0243](../../../SOURCES.md#src-0243)。

## D21补评估 t5.1-eval-r2 — blocked（2026-10-14T00:29:59.339239+08:00）

范围：用户最新授权按Claude D21/R11补最终sim评估，不改源码、模型、任务、world、max_len及seed协议，原r1保留。实际模型/强度未知；推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，原因是逐回合确定性/拼接合同核对，监控/文档low或默认。

第2(a)条运行自然退出0，stdout与离线W&B均为8/8成功，但以下步数不符，因此**按D21停止，不拼接**。原seed1029–1036步数：614、585、483、603、534、484、489、583；本次：605、512、483、603、507、484、489、583。不同种子为1029、1030、1033，其余5回合步数和全部成功标记一致。[SRC-0260](../../../SOURCES.md#src-0260)

完整命令、起止时间、退出码与日志：`results/task5/t5.1-eval-r2/commands.json`；逐回合核对：`determinism_check.json`；原始日志：`logs/task5/t5.1-eval-r2/check-door-seed1029-n8.log`；离线原始指标：`offline_raw_export.json`与`episode_metric_checks.json`。软链前后记录`output-link.log`：从`/forem_results/t5.1-eval-r1`改为`/forem_results/t5.1-eval-r2`，当前保持r2以避免后续误写r1。源/模型/r1前后82文件SHA相同，`source_model_r1_unchanged.json` changed=[]。

未执行：A第2(b)种子1037、door1038–1048、drawer/roomdoor/spline、最终9任务汇总。没有生成最终summary，不把核查8回合当新正式样本。训练退出0/1M及旧blocked posttrain_status历史均保留不覆盖。交接：Claude先决定确定性门槛失败的下一步；原因未诊断，本执行者不放宽门槛、不重跑/修码。B种子999已并行启动，仍在复现；未提前进入B49回合补跑。

2026-10-14T00:57:15.939110+08:00 D21本轮收尾：A仍blocked不拼接；B独立补齐spline后因r1指标checksum断言blocked。两task5容器无评估进程，原ROS保留。CPU监控退出0，300个5秒样本峰22.199核/均9.364核/>56为0，统计在A r2 `cpu_sampling_summary.json`。两子任务交Claude，不置review/done。[SRC-0263](../../../SOURCES.md#src-0263)

## 2026-10-14T08:36:26.639026+08:00 R12/D22/D23实际继续

已按用户授权接手；D22逐成功标记8/8通过，原3/8步数差异保留不改判据。1037复跑再次20001步assert/rc1，`d22-check-door-seed1037-n1.log`；计分固定原r1失败，`door_seed1037_d22_diagnostic.json`单列诊断。door1038起11回合已启动，后续drawer/roomdoor/spline各50按D21逐seed超限续跑；补充脚本`python3 -u forem/build/task5/task5_d22_complete_a.py`，exec会话90725，容器评估调用PID/完整命令/起止/log以r2 commands.json为准，日志`d22-<task>-seed<seed>-n<count>.log`。CPU监控`python3 -u forem/build/task5/task5_d22_cpu.py`，host PID在r2 cpu_d22.pid，每5秒数据host_cpu_d22_5s.jsonl，停止自身监控使用cpu_d22.stop文件；不对训练发信号。任一未覆盖异常停止，不静默重启/覆盖日志。来源[SRC-0264](../../../SOURCES.md#src-0264)。实际模型/强度未知；推荐GPT6.1sol/Sonnet5.5 medium（逐行/拼接核对），文档/监控low默认。B已按D23交付review（SRC0267），整体最终复核仍等A。

## 2026-10-14T08:54:42.608553+08:00 D22/D23最终交付 — review，交Claude

最终结果：`results/task5/t5.1-eval-r2/final_eval_summary.json`；stdout为主口径，逐回合累计成功差分及seed账本重新核对；W&B逐文件可读则核对，错误完整披露，不修复/截断。原r1与旧r2记录保留。[SRC-0268](../../../SOURCES.md#src-0268)

|标准任务|成功数|分母|成功率(%)|
|---|---|---|---|
|simpleobstacle|39|50|78.0|
|picknplace|48|50|96.0|
|bookstorepnp|37|50|74.0|
|dynobstacle|39|50|78.0|
|picknplacedyn|37|50|74.0|
|door|49|50|98.0|
|drawer|50|50|100.0|
|roomdoor|46|50|92.0|
|spline|40|50|80.0|

可运行任务均值：85.555556%；9任务均值：85.555556%。B八可运行均值24.75%，完整9均值N/A、覆盖8/9，不把bookstorepnp当0。A完整九任务均值是标准朝向均值；fwdO单列：

- picknplace fwdO：49/50。
- bookstorepnp fwdO：35/50。

拼接/超限seed/原始指标及逐文件错误见JSON splice/metric_checks/WandB_unreadable_files。A door38+11=49/50，1037按原r1失败固定计分，复跑结果仅诊断；8回合门槛只按D22成功标记通过，不重复计入最终50。B spline0/50沿上一轮47自然失败+三超限，不重跑。assert中断段没有上游汇总指标，stdout-only如实披露。[SRC-0268](../../../SOURCES.md#src-0268)

交付证据：commands.json（命令/起止/rc/log/pid）；逐seed账本与段收据；d23_offline_file_report.json/d23_exports/（每文件原始数据或完整错误）；d23_episode_metric_checks.json（可用success均一致）；source_model_r1_d22_d23_unchanged.json；handoff_verification_d22_d23.json/evidence_d22_d23_sha256.json。登记A82/B210文件SHA未变。新软链仍r2，无写入r1；原训练posttrain_status历史不覆盖。

CPU续跑274样本峰25.392核/均12.635核，>56为0，A r2 cpu_d22_sampling_summary.json；监控已停止，仅自己的stop文件，不干预训练/外部容器。无活动评估，原ROS保留。负责人Codex交Claude5.3，下一步独立复核上述表/拼接/朝向/错误/限制后才可done；本执行者不标done。实际模型/强度未知，GPT6.1sol/Sonnet5.5 medium推荐、文档low/默认。[SRC-0268](../../../SOURCES.md#src-0268)
