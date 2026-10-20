# task5.4 B延长训练500万步与性能优化 — 结果与交接

> **当前状态（2026-10-19核对）：paused（2026-10-14用户要求停止，正式5M未启动；不要恢复）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**paused（2026-10-14 17:1x+08:00用户明确指令“停掉task5.4”，改用cbl自写SAC的GPU版5M，见[task5.5](../task5.5/TASK.md)；正式5M未启动，见文末“用户要求停止”节）**。此前状态：active（T54-D1接手；新等价性通过，30k×2端到端profile进行中）。目标与流程见[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)。

## §0 开工与现场核查

2026-10-14 Codex接手；实际模型/强度未知，推荐GPT6.1sol/medium、Claude Sonnet5.5/medium（跨模块性能/等价性核查）。完整登记见独立日志。

冻结147个源码/配置文件SHA与t5.2最终保存证据全部一致，包含入口、ray_utils、utils、best_defaults、custom_sac和ray_wandb。证据：`forem/results/task5/t5.4-preflight-r1/freeze_check.json`。现场完整快照同目录；64逻辑核、充足内存与磁盘。确认本容器无训练/评估客户端后，仅重启forem-t5-husky清理旧ROS/ray/zombie；重启后仅sleep。其他容器不操作。

§1在ray_wandb副本新增默认关闭只读探针，仅FOREM_T54_PROBE=1时调用，未设时直接返回；before/diff/SHA与关闭探针测试红→绿证据在preflight目录。未改科学合同或参考仓库。

## §1 learner执行路径

`t5.4-prof-r1`已完成（20000步，从头、其他冻结值同t5.2；退出0）。容器训练PID144/宿主669335，learner容器PID417；Torch intra-op=1、interop=32，模型/optimizer全部cpu，OMP_NUM_THREADS=1、MKL未设。20 rollout worker各Torch1线程；探针仅初始化执行一次，计时不含初始化。实际OS线程25、主线程约100% CPU（不将OS线程总数当intra-op数）。`learner_threads_top.txt`及train.log探针保存证据。10迭代时复算：丢弃前3迭代，中位52.7916s，learn_time_ms中位414.624ms×100更新≈41.4624s，占比78.5398%≥50%，§1门槛通过。r1已正常20k退出0。最终丢弃前3后中位53.604544s、P90 54.943775s，单次learn计时中位422.727ms、learner合计中位42.2727s，占比中位79.4968%；20迭代time_total_s=1059.081788（17.651分钟，不含ROS/Ray初始化墙钟）。最终主机CPU采样峰8.1244核，监控最早阶段缺样本限制保留。原checkpoint_000020存在，仅profile结果。依据[SRC-0313](../../../SOURCES.md#src-0313)。

ROS容器PID见run目录roscore.pid/roslaunch.pid；完整包装t54_ros.sh/t54_prof_r1.sh，监控源码t54_profile_monitor.py/monitor.pid/launch.json。停止仅本run训练PID SIGINT；监控见exit_code自然退出。不停止其他容器。
规划依据（t5.2既有数据推导，非新测量）见[SRC-0311](../../../SOURCES.md#src-0311)。

## §2 性能核查与采用的优化

O1默认关闭开关已实现，只在WandbSACTrainer learner的原初始化完成后调用torch.set_num_threads，环境变量FOREM_LEARNER_THREADS未设则直接返回；不改OMP/MKL全局环境，不改rollout/评估worker。源码前后SHA/diff为preflight/O1_sha.json/O1.diff，3项隔离测试红→绿加探针关闭测试通过。候选4/8/16尚未采用，必须待等价性与端到端重复测试。

固定权重/batch256/RNG等价性脚本t54_equivalence.py已调用一次，退出1；读r1最终checkpoint的worker元数据时即`ValueError: unsupported pickle protocol: 5`（第16行）。脚本误用标准pickle，容器Python3.7.13最高protocol4，而RLlib RolloutWorker.save用ray.cloudpickle，现有loads来自pickle5._pickle。完整Traceback在`forem/logs/task5/t5.4-preflight-r1/equivalence.log`，只读核查在preflight/pickle_protocol_readonly.txt。尚未构造policy/batch，未执行SAC更新、无loss/参数/RNG等价性结果，无equivalence_inputs.pkl；不属于N=4/8/16数值测试不通过。依异常规则停止，不修复、不重跑。[SRC-0313](../../../SOURCES.md#src-0313)。

有界序列脚本t54_profile_sequence.py宿主PID714356已自动在equivalence非零退出后停止，status=blocked；r2–r7尚未启动（只有包装脚本准备，没有run数据）。O1未采用，O2未测试；GPU不测试沿冻结torch1.7.1/num_gpus0，不改TI/batch/workers/评估/检查点。r1尚未探测评估worker实际Torch线程，后续候选探针代码已准备但未运行。


|配置|N（learner线程）|中位迭代s|P90|learn_time_ms|主机CPU|等价性|采用|
|---|---|---|---|---|---|---|---|
|§1 r1（20k路径核查，非§2重复基线）|1|53.604544|54.943775|422.727|峰8.1244核（最早缺样本）|尚未构造|无优化|
|§2基线30k×2|原样|待测|待测|待测|待测|—|未执行|

## §3 正式训练`t5.4-train-s40-5m`

尚未执行。

|步数|t5.4 success|t5.2同步数 success|备注|
|---|---|---|---|
|1M|待填|0.76（975k）|lr/噪声日程不同|
|2.5M|待填|—||
|5M|待填|—||

## §4 最终评估`t5.4-eval-r1`

尚未执行。

## §5 汇总与交接

本节正式比较尚未执行，当前为异常交接，状态blocked；不生成假comparison，不标review/done。

- 目标与授权：B原版SAC从头5M及文档限定性能优化/9任务sim评估；Codex执行、Claude决策/独立复核。
- 已完成：§0现场与147文件冻结一致；§1正常20k，实际CPU设备/learner线程与约79.5%开销门槛；§2默认关闭learner开关和隔离单测通过，完整before/diff/SHA落盘。等价性调用在读取元数据时失败，未发生数值更新。
- 证据：`forem/results/task5/t5.4-preflight-r1/`的freeze_check、O1.diff/O1_sha、pickle_protocol_readonly、profile_sequence_status、final_source_check/evidence_sha256；`forem/results/task5/t5.4-prof-r1/`完整ray/checkpoint/progress/launch/profile_summary与监控；两run日志目录；依据[SRC-0313](../../../SOURCES.md#src-0313)。
- 实际修改：仅ws_husky/scripts/modulation/myray/ray_wandb.py（默认关闭hook/只读探针）及task5.4专属t54_*.py/sh/包装脚本、三文档状态、独立日志、PROGRESS/SOURCES追加。final_source_check核实其余146冻结文件不变；未提交/推送，既有工作区修改保留。
- 清理与运行状态：r1 train容器144/宿主669335正常退出0；监控宿主680802和序列714356均退出。按身份SIGINT自身ROS107/175，最新docker top仅sleep；没有仍运行的本任务作业。不操作forem-t6-husky-gz、forem-dev、forem-t5-pr2或forem-t6.4-*。
- 剩余：Claude核查执行脚本兼容异常并决定是否放行修正；之后从§2等价性开始（r1只读沿用元数据），候选与基线30k重复门槛、选择/估计、清理，再§3独立5M→§4九任务→§5比较与Claude复核。无5M权重/数据，不能从t5.2续训。
- 建议（未实施/不构成授权）：仅将自有等价性脚本的加载器与RLlib现有ray.cloudpickle对应，不安装依赖、不改镜像/torch；需Claude放行后再执行。当前脚本未改，保留失败现场。
- 风险：候选尚无数值等价性/性能证据；默认关闭语义仅单测，不能声称优化通过。正式时间估计待候选profile，沿旧86h仅规划依据，不承诺新工期。独立复核尚未执行。

模型推荐仍为Codex GPT6.1sol/medium、Claude Sonnet5.5/medium；此执行会话实际模型/强度未知。

## Claude复核

### R1 — §0–§2阻塞审批（Claude，2026-10-14）

用户：“审批”。Claude只读复核Codex交付（[SRC-0314](../../../SOURCES.md#src-0314)）：

- §0冻结147文件一致、§1 r1结论（learner在trainer进程、intra-op=1、CPU，learner约79.5%）**通过**，与SRC-0311推导一致（本次单独运行每迭代约53.6 s）。
- O1 diff核查：`_forem_learner_threads()`在`WandbSACTrainer.__init__`末尾调用，环境变量未设直接返回；只作用于trainer（learner/本地worker）进程，20个rollout worker与评估worker是远程actor不受影响；`_forem_learner_probe`默认关闭。**接受**。
- 阻塞原因核实：失败在执行者自写的`t54_equivalence.py:16`用标准`pickle`读RLlib checkpoint（由`ray.cloudpickle`/pickle5写出，protocol 5），不是候选线程设置的数值问题，也不涉及训练语义。
- **T54-D1**：放行只修该脚本的加载器——checkpoint与`ray_config.pkl`一律用`ray.cloudpickle`（或RLlib自带加载路径）读取；不装依赖、不改镜像/torch/ray。脚本仍只从checkpoint取spaces/config，用固定种子的新随机权重与固定合成batch，不加载t5.2任何东西。修正后用新run-id `t5.4-equiv-r1`输出（preflight-r1失败现场保留），再按PROCEDURE §2继续：N=1对N∈{4,8,16}等价性→基线与候选30k×2端到端→选择/估计→清理→§2通过即直接进入§3正式5M→§4→§5。
- 补充要求：等价性须在“N=1”与“N”两个独立进程（或同进程内切换线程数后各自从同一初始state重建policy）下比较，并记录三项loss与全部参数最大绝对差；等价性通过但端到端收益<10%的N也不采用。

§0/§1新实测依据：[SRC-0312](../../../SOURCES.md#src-0312)（短程限制见条目）。


## 2026-10-14T16:01:17.905526+08:00 T54-D1继续§2（新事实优先；上方blocked交接保留为历史）

只修加载器，before/after/diff/SHA在`results/task5/t5.4-equiv-r1/`；147项SHA相对Claude R1批准现场全部一致，其他科学合同、镜像/依赖未改，旧preflight-r1失败证据保留。

|N|actor/critic/alpha相对差|参数最大绝对差|RNG一致|等价性|
|---|---|---|---|---|
|4|0 / 0 / 0|7.4505805969e-9|是|通过|
|8|0 / 0 / 0|2.2351741791e-8|是|通过|
|16|0 / 0 / 0|9.6857547760e-8|是|通过|

依据[SRC-0315](../../../SOURCES.md#src-0315)；fresh固定权重/合成batch256，完整四优化器和target更新，不载入t5.2权重。单次微测不代替整体性能。

端到端顺序（用户本轮明确全部候选两次，不只最佳重复）：r2基线1、r3 N4-1、r4 N8-1、r5 N16-1、r6基线2、r7 N4-2、r8 N8-2、r9 N16-2，均30k、丢弃前3迭代。基线与候选总中位下降≥10%且两次方向一致，候选相差<5%取较小N。只作用learner；远程rollout/eval保持1。r2已启动，其他待运行。

当前宿主序列PID775917、源`t54_profile_sequence.py`、日志`logs/task5/t5.4-equiv-r1/profile_sequence.log`、状态`results/task5/t5.4-equiv-r1/profile_sequence_status.json`；各run monitor.pid/train.pid/launch.json/日志单独记录。预执行核查修正观察器候选判断为原门槛及区分eval worker_index0本地learner与远程eval，重启自有host观察器，r2 detached训练未停止/重启。相应脚本diff保留新run。只重启已无活动客户端的本任务forem-t5-husky以隔离各profile；其他容器不操作。

正式5M仍未启动，选定配置/时间估计待完整profile。模型推荐GPT6.1sol/Sonnet5.5 medium，实际本会话模型/强度未知。


### R2 — 用户要求learner加到32线程（Claude，2026-10-14 16:5x）

用户：“能加大一些吗”“加到32核心”（[SRC-0316](../../../SOURCES.md#src-0316)）。Claude只读核查：主机2×Xeon Gold 6530，64物理核、无超线程、2个NUMA节点（0–31、32–63）；16:54 load约16。r2–r5首轮中位：基线54.9 s、N4 27.0 s、N8 21.5 s、N16约17.8 s（11/30迭代）；非learner部分约11 s/迭代（采样+开销），N32理论上限约比N16再快10–20%。

**T54-D2**：
1. O1候选加入N=32：开关允许值改为{4,8,16,32}（默认关闭不变，保存diff/SHA）；N=32做同口径等价性（loss相对差≤1e-5、参数最大绝对差≤1e-6）。
2. N=32两次30k端到端profile（新r号接在现有序列后），与基线/N16同口径比较。
3. 选择规则按用户偏好覆盖原“差<5%取较小N”：N=32等价性通过、两次中位均比基线下降≥10%、且不比N=16慢超过5%（两次一致）时，**采用N=32**；否则采用原规则选出的N并报告N=32数据。
4. 正式5M须等N=32测试完成后才启动；若自动启动器先于N=32测试触发，先停自己的启动器（只停本任务进程），不得以16线程开正式run后再改。
5. CPU：learner 32线程＋20 worker＋ROS＋G-B，主机合计>56核仍只告警（D11），记录实际峰值；不做NUMA绑核，除非N=32比N=16慢，再按O2测试“learner绑单NUMA节点”并报告。


## 2026-10-14T17:07:53.873664+08:00 当前后台执行交接（active，不是最终验收）

第一轮基线r2/N4-r3都正常30k退出0：中位54.918678→26.999634秒（下降50.8371%）；远程20 rollout/1 eval均1线程，CPU峰14.2744/12.6968核。单次结果尚不满足最终两轮门槛，N4未正式采用。依据[SRC-0317](../../../SOURCES.md#src-0317)。

当前执行`t5.4-prof-r6`，N=None；控制器和启动器已脱离会话继续运行，不依赖本次聊天保持连接。正式5M当前尚未启动，不将待启动写成结果。

- 序列：宿主PID 862072，`python3 -u forem/build/task5/t54_profile_sequence.py`，每配置30k×2，r2/r6基线、r3/r7 N4、r4/r8 N8、r5/r9 N16；日志`forem/logs/task5/t5.4-equiv-r1/profile_sequence.log`，状态`profile_sequence_status.json`。
- 启动器：宿主PID 862073，`python3 -u forem/build/task5/t54_start_formal.py`，状态`formal_launcher_status.json`当前waiting_profile_gates。等完整profile符合冻结门槛，自动记录结果/SOURCES、清理已结束profile的本容器ROS/Ray，检查无活跃客户端、启动t54_formal.sh；不等待新的Claude放行。
- 当前容器训练PID 192（只属t5.4-prof-r6；以后每run读train.pid/monitor.pid/launch.json）；日志`forem/logs/task5/t5.4-prof-r6/train.log`。所有后台host进程由start_new_session分离，容器训练由docker exec -d分离。
- 正式运行后事实：`forem/results/task5/t5.4-train-s40-5m/launch.json`会写实际容器/宿主训练PID、learnerPID、monitor/posttrain PID及progress.csv绝对路径；当前这些正式产物不存在。生效对照仅四项total_steps派生变化，选定FOREM_LEARNER_THREADS只作用learner。
- 正式监控：落盘`t54_monitor_train.py`，CPU5秒、进度30分钟、56核5分钟均值仅告警，不发训练信号、不自动改RESULTS/SOURCES；原始数据包括worker CPU秒与观察到的worker进程生命秒，两者分开，5秒采样边界有误差。cgroup只读权限已核查。
- 后处理：`t54_posttrain.py`已落盘并通过离线5项计数检查，启动器在正式配置/设备核查后将其分离启动。训练非零退出/不达5M不评估，记录实际步数/最后checkpoint；正常结束则导出训练序列/1M、2.5M、5M原样评估（实际975k、2475k、4950k）和t5.2四项并列表，说明lr/噪声日程差异，再9任务sim（D10/D21/D23、R12/D22确定性门槛），逐文件W&B核验、comparison.json、review交Claude。若双朝向任务先分支超限而无法用原入口完成另分支，保留现场交Claude，不臆造未跑分支。
- 停止本执行链：先按cmdline身份停止宿主启动器862073和序列862072（只停止未来推进）；再确认当前run/train.pid后在forem-t5-husky给该PID SIGINT。监控会随exit文件退出。不得停止整个容器/其他进程。正式开始后只对正式launch记载的训练PID SIGINT，不能续训；新r号从头重跑须Claude决定。
- 下一步：后台继续全部两轮profile→选配置→直接5M；正常完成后§4/§5；异常只保留/登记/交Claude。当前所有受保护容器及参考目录未操作；未提交/推送其他人的改动。模型推荐GPT6.1sol/Sonnet5.5 medium；实际本会话模型/强度未知。


## 用户要求停止（2026-10-14 17:1x+08:00，Claude执行）

- 用户明确指令：task5.4的RLlib CPU版5M“停掉task5.4”，改为“用cbl写的那个sac做，然后改成在gpu跑”（用已迁移链路、sim、Codex执行）。执行者：Claude（会话“世界模型与强化学习文献”，claude-opus-5-5）。
- 操作（只停本任务自有进程，不停容器）：主机SIGTERM `build/task5/t54_profile_sequence.py`（PID 862072）与正式启动器`build/task5/t54_start_formal.py`（PID 862073），均已退出——正式5M不会再自动启动；容器内对`t5.4-prof-r6`的`main_ray.py`发SIGINT，Tune报告“Trials did not complete…Experiment has been interrupted”后退出；再按`/forem_results/t5.4-prof-r6/roslaunch.pid`、`roscore.pid`发SIGINT停止该run的ROS。之后forem-t5-husky仅`sleep infinity`（与若干历史僵尸），主机无t54_*进程。
- 已有数据保留：r1–r5及equiv-r1全部产物原样保留；r6（第二轮基线）中途停止，不完整、不计入。首轮中位迭代：基线54.9 s、N4 27.0 s、N8 21.5 s、N16约17.8 s（见R2节）；N32未测。§3正式5M、§4评估均未执行。
- 恢复须用户另行明确指令；Codex接手前请先读本节。
