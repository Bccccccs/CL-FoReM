# task5.4 B延长训练500万步与性能优化 — 详细流程

状态：**active（T54-D1继续执行；等价性已通过，端到端profile进行中；见RESULTS）**。流程制定者/决策者：Claude；执行者：Codex（用户派发）。目标、范围与验收见[TASK](TASK.md)。

## 递归规则声明

本节点遵守根[AGENTS](../../../../../AGENTS.md)递归三文档规则：本节点及其后续拆分的task5.4.K都必须有自己的TASK.md、PROCEDURE.md、RESULTS.md；父流程列出子任务编号、顺序、依赖、负责人和验收关系，父RESULTS只汇总子RESULTS。编号稳定、不复用。当前没有计划中的子节点；如执行者挂监控子Agent，须先建`task5.4/task5.4.1/`三文档并在下表登记。

|编号|内容|负责人|依赖|验收关系|三文档|
|---|---|---|---|---|---|
|（暂无）|—|—|—|—|—|

## 冻结口径（执行者不得自行更改）

|项|值|
|---|---|
|容器|`forem-t5-husky`（task5.0创建；挂载`forem/build/task5→/forem_build`、`forem/results/task5→/forem_results`、`forem/logs/task5→/forem_logs`）|
|代码|`/forem_build/ws_husky/src/modulation_rl`（与t5.2同一副本）；不改`husky/`、`mobile-rl/`|
|训练命令（基线）|`/opt/conda/bin/python -u scripts/main_ray.py --num_gpus 0 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults --seed 40 --env husky_ur5 --total_steps 5000000`|
|环境变量/包装|同[t52_formal.sh](../../../../build/task5/t52_formal.sh)：melodic+ws_husky setup、`ROS_PACKAGE_PATH`含`/forem_build/deps/lms1xx`、`WANDB_MODE=offline`、占位`WANDB_API_KEY`（40个`0`）、`wandb offline`；`scripts/logs`软链指向本run目录|
|ROS|手动启动`n2m2_husky_analytical.launch gui:=false`（同t5.2）|
|训练中评估|原样：每75000步、50回合、1个并行评估worker、`explore=False`、eval_seed 999|
|最终评估|`evaluation_ray.py --evaluation_only --eval_execs sim --env husky_ur5 --num_gpus 0`，9任务各50回合、eval_seed 999、最终checkpoint；D10/D21/D23同task5.2（见[task5.3](../task5.3/RESULTS.md) R7/R10/R12）|
|run-id|profile：`t5.4-prof-r<N>`；正式：`t5.4-train-s40-5m`；最终评估：`t5.4-eval-r1`；重试递增r号，失败run保留|

## §0 开工与现场核查

1. 读根AGENTS、`forem/doc/PROGRESS.md`、task5父三文档、task5.2 RESULTS、task5.3 R7/R10/R12/R13、本节点TASK/PROCEDURE、SRC-0310/0311。
2. 在PROGRESS登记（任务ID `TASK5.4-B5M`、负责人、范围、开始时间），建独立日志`forem/doc/agent_logs/task5/task5.4/YYYYMMDD-codex-task5.4.md`，注明实际模型/强度（无法核实写未知）。
3. 现场核查并记录：`forem-t5-husky`内现有进程（2026-10-14 14:4x Claude只读看到task5遗留的roscore、`n2m2_husky_analytical.launch`/move_group与若干`ray::IDLE <defunct>`，无训练/评估python）；确认它们属于已done的task5，无活动客户端后，可停止该容器内的这些ROS/ray残留并以本run重新启动，记录PID与命令。**不得触碰**`forem-t6-husky-gz`（task6.2 G-B训练运行中）、`forem-dev`、`forem-t5-pr2`、`forem-t6.4-*`及其进程。
4. 记录主机资源快照：`nproc`、内存、`uptime`、各容器CPU（`docker stats --no-stream`）、GPU（本任务不用）。
5. 冻结核查：对`main_ray.py`、`modulation/myray/ray_utils.py`、`modulation/utils.py`、`configs/best_defaults_ray.yaml`、custom SAC trainer/policy相关文件记录sha256，与t5.2冻结证据（`results/task5/t5.2-train-s40/`及task5.0记录）对比；不一致即停止交Claude。

## §1 learner执行路径确认（只读或短程）

目标：确认100次/迭代的SAC更新在哪个进程、用几个线程执行。

1. 用基线命令以`--total_steps 20000`启动一次短程run（`t5.4-prof-r1`；`total_steps`只影响lr/噪声日程斜率，不影响计时），运行至少10个迭代。
2. 记录：Tune trainable（learner）进程PID与命令行、`/proc/<pid>/status`中`Threads`、该进程`OMP_NUM_THREADS`/`MKL_NUM_THREADS`（`/proc/<pid>/environ`）、`top -H -p <pid>`或`pidstat -t`的线程CPU分布、rollout worker与评估worker的同项。可在learner进程内用最小只读探针（例如短程run里额外打印一次`torch.get_num_threads()`，默认关闭开关）确认torch线程数；不安装新包，若`py-spy`等工具不存在则不装。
3. 从该run `progress.csv`复算每迭代分解：`time_this_iter_s`、`timers/learn_time_ms`×更新次数、采样时间（迭代时间−learner合计）、`sampler_perf/*`。与[SRC-0311](../../../SOURCES.md#src-0311)对照（t5.2与A并行，本次单独运行，差异如实记录）。
4. 结论写入RESULTS §1：learner进程、实际线程数、learner占比。若learner并非瓶颈（占比<50%），停止§2候选测试，记录原因并交Claude决定。

## §2 候选优化：等价性与端到端收益

### O1 learner intra-op线程数

1. 实现：只对learner所在进程设置torch intra-op线程数`N`，由环境变量（如`FOREM_LEARNER_THREADS`）控制，**未设置时行为与原版逐字等价**；rollout/评估worker保持原设置（不得全局设`OMP_NUM_THREADS`导致20个worker各开多线程）。优先用不改源码的方式（包装/Ray配置）；必须改`ws_husky`副本源码时，只加默认关闭的开关，保存前后sha256与diff到`results/task5/t5.4-prof-r*/`，并说明t5.2复现不受影响（开关未设时等价）。
2. 等价性（工程选择，[SRC-0311](../../../SOURCES.md#src-0311)登记理由）：固定同一组网络权重、同一个256样本batch、同一RNG状态，分别在`N=1`与候选`N`下执行一次完整SAC更新（actor/critic/alpha），比较三项loss与更新后全部参数。判据：loss相对差≤1e-5、参数最大绝对差≤1e-6（浮点归约顺序差异量级）；超出即该`N`不采用。另核对线程设置不改变RNG序列、batch采样与更新计数。
3. 端到端收益：候选`N∈{4,8,16}`（按§1现场空闲核数取舍，learner线程数+20 worker+评估worker+ROS的总占用须让主机合计≤56核），每个配置短程run（`t5.4-prof-r<N>`，`--total_steps 30000`），丢弃前3个迭代，取其余迭代`time_this_iter_s`中位数；基线与最佳候选各重复2次。采用门槛（工程选择）：中位迭代时间较基线下降≥10%且两次重复方向一致。选收益最大的`N`；若多个`N`差异<5%，取较小者。
4. 记录每个`N`：迭代中位/P90、learn_time_ms、learner进程CPU%、主机CPU合计、是否采用及原因。

### O2 CPU亲和（可选）

只在O1后观察到learner与worker/其他容器争用（learner线程CPU%明显低于`N×100%`且主机繁忙）时测试；同O1的收益门槛。不采用时记录“未测试/无收益”。

### 不测试/不采用（写入RESULTS并注明原因）

- GPU learner：torch 1.7.1不支持Blackwell，父流程允许偏差1禁止换栈。
- 改worker数、TI、batch、`timesteps_per_iteration`、评估worker数/回合数、checkpoint频率：改变科学或评估口径。
- 训练中评估本身的耗时（约每次190–250 s）计入总时长，不压缩。

### §2出口

- 把选定配置（基线或O1/O2）的最终命令、环境变量、diff写入RESULTS §2，并用实测中位迭代时间估算5M墙钟：`5000×中位迭代时间 + 66×(评估迭代额外耗时)`，评估额外耗时取本次profile或t5.2实测（约150 s），标明为推导。
- 不需要等Claude放行：等价性与收益门槛满足就采用，不满足就用基线，直接进入§3。§1发现learner不是瓶颈、或冻结核查失败时才停下。
- 清理所有profile run的ray/ROS进程，确认无残留后再开正式训练。

## §3 正式训练`t5.4-train-s40-5m`

1. 以§2选定配置启动（包装脚本`forem/build/task5/t54_formal.sh`，参照t52_formal.sh，只改run-id、`--total_steps 5000000`与§2选定的线程开关）。写`launch.json`（完整命令、环境变量、开始时间、容器、PID）与`effective_config_check.json`（params.json逐项与t5.2对比，差异只能是`total_steps`派生项：lr_schedule终点、`scale_timesteps`、ASHA `max_t/grace_period`、stop条件，以及§2设置）。
2. 监控：主机5秒CPU采样与30分钟进度摘要（可复用`forem/build/task5/monitor_task5_train.py`的做法，新文件放`forem/build/task5/`，源码落盘，不用`python3 -u -`）。CPU连续5分钟均值>56核**只告警**（D11），不自动停训练。监控不自动改RESULTS/SOURCES。
3. 读数节点（不停训练）：1M、2.5M、5M的训练中评估（success、goal_reached、ik_fails、episode_len）写入RESULTS §3，并与t5.2同步数值并列，注明lr/噪声日程不同。另记录实测吞吐与剩余时间估计。
4. 训练正常退出且≥5,000,000步后，导出`train_eval_series.csv`、`offline_training_export.json`，确认最终checkpoint存在（预期`checkpoint_005000`）。
5. 磁盘：预期约50个checkpoint，按t5.2（10个约368 MB）估算约1.8 GB，开工时确认余量。

## §4 最终评估`t5.4-eval-r1`

1. 加载最终checkpoint，按task5.2同一入口与参数评估9任务：`simpleobstacle picknplace bookstorepnp dynobstacle picknplacedyn door drawer roomdoor spline`，各50回合、eval_seed 999、`--num_gpus 0`，W&B离线。
2. 口径沿task5：D10（bookstorepnp原入口一次、保留10次reset重试、`timeout --signal=KILL 1800`，采样耗尽则N/A）；D21（单回合超过上游20000步上限记失败，从下一个种子续跑剩余回合数）；D23（stdout“Eval ep”逐回合计数为主口径，W&B逐文件核验并披露）。可复用`forem/build/task5/task5_posttrain.py`、`task5_d21_*`、`task5_d23_*`的逻辑，新run-id，不写入t5.2目录。
3. 输出`results/task5/t5.4-eval-r1/final_eval_summary.json`：每任务成功数/分母、成功率、拼接说明、picknplace/bookstorepnp fwdO原始指标单列；“8可运行平均”与“9任务含N/A”两种口径。

## §5 汇总与交接

1. `results/task5/t5.4-summary/comparison.json`：t5.2（1M）与t5.4（5M）的训练中评估曲线（按步数）、最终9任务，以及性能数据（优化前后中位迭代时间、总墙钟、累计耗时）。
2. RESULTS写完整交接（目标、负责人、完成事项、证据路径、剩余、风险、下一步）；新的实测论据登记SOURCES（编号取当前最大+1，写入前复核）。
3. 状态改为review，停下交Claude复核。不自行标done。

## 异常处理

- 冻结核查不一致、§1发现learner不是瓶颈、等价性测试无法构造：停下，保留证据，写RESULTS，交Claude。
- 正式训练崩溃：不续训（上游不支持，replay不保存）。记录已到步数、最后checkpoint、错误；checkpoint只能用于评估。停下交Claude决定是否以新r号从头重跑。
- worker反复死亡/内存不足：记录现象，不减worker，交Claude。
- 最终评估遇到D10/D21/D23未覆盖的失败（地图缺失、采样失败、进程异常）：停下交Claude。
- 训练时长：不设截止时间，不为赶时间改口径；估计时长写入RESULTS即可。

## 监控与停止

RESULTS须写清：容器、启动命令、训练PID（容器内与主机）、监控PID、日志`forem/logs/task5/t5.4-train-s40-5m/train.log`、`progress.csv`路径。停止：对本run训练PID发SIGINT（只停自己启动的进程，不停容器）；恢复：新r号从头重跑。持续工作期间至少每30分钟更新日志；长训期间可在里程碑与异常时更新。

## 模型与推理强度

见[TASK](TASK.md#模型与推理强度推荐)：Codex GPT6.1sol/medium，Claude替代Sonnet5.5/medium，监控子Agent low。实际使用的模型和强度由执行者记录。
