# task7.18.4 — 结果

状态：**训练中（看门狗早停）**（2026-10-22 12:34从头启动v4两变体，见第六节；第一至五节为此前阶段的历史记录）。原状态：blocked（C′诊断未支持，v4重训未启动）。2026-10-22 09:1x用户改选方案C′（[SRC-0912](../../../../SOURCES.md#src-0912)，取代修复A）。C′已实现并通过测试/回归；150k转移诊断微调显示**不同步变体“快速失败”基本未消失**（同步部分改善但IK失败步占比回升），按任务约束停下报告，**不再改奖励，未启动v4**。执行者：Claude子Agent（claude-sonnet-5-5，推理强度未知）。实现选择登记[SRC-0920](../../../../SOURCES.md#src-0920)。

## 一、v3停止确认（事实，08:48）
- 08:43:56 STOP已在 `forem/results/task7/t7.18-v3-20261021/formal-v3-{sync,async}/`。08:48核查：worker宿主PID 3223585/3223627均已不在（`ps -p`无输出），`nvidia-smi`无compute进程，supervisor.log末行均为`worker_exit rc=1`（时刻1792630104）。
- interrupted检查点齐全（08:45–08:48写完）：`interrupted.pt`（sync 17703959155 B，async 17335031795 B）、`interrupted.actor.pt`、`interrupted.meta.json`。meta：sync action_calls 6265/env_actions 1598706/steps 1598453；async 5969/1526219/1526199。`interrupted.tmp`已不存在。**未核对账本safe_to_resume，未恢复，未删STOP。**
- GPU2/GPU3此刻空闲，本任务未使用。


## 二、修复A（已撤销）
修复A（SRC-0911）已按协调者指令撤销：core.py回退至改前快照（SHA256 b0bbf632…7419），测试与新旧对照脚本移至`forem/results/task7/t7.18.4-diag-20261022/abandoned_fixA/`保留（修复A当时13例通过、非失败步逐位相同）。

## 三、run-id t7.18.4-cprime-impl-20261022 — C′实现与测试

### 改动文件（均为局部补丁，改前重读）
- `forem/src/task7_sim/core.py`：`Core(..., failure_mode='terminal'|'cbl_continue')`，默认`terminal`；`cbl_continue`要求`execute=True`。cbl分支：失败子步不提交且本动作步不再尝试、不置done/reason；`step_kind`替代`failure_kind`计B中−10·(底盘碰撞)与G中−2；IK失败步B的(d,r)用失败尝试的`ik.position/ik.cbl`；段超时用`attempted_segment×0.05`；新增`attempt_time`（回合T_max用，不动`time`）；`failures`计失败动作步，终止阈值`failure_limit`=20（terminal仍5）；第20次失败置done、reason=2/3、terminated（mask 0）；新增`last_step_failure`。terminal路径的原表达式未改。
- `forem/src/task7_sim/env.py`：`EpisodeEnv(..., failure_mode)`透传。
- `forem/src/task7_lower/training.py`：创建训练环境时读`config.get('failure_mode','terminal')`；新增`step_failures`（按类型的失败动作步）计数与日志；`train(..., init_weights=)`（仅诊断用，只载入SAC全状态，经验池/环境/state全新）。`evaluate()`未改，仍terminal语义。
- `forem/scripts/task7_lower_train.py`（`--init-weights`）、新增`forem/scripts/task7_lower_diag_eval.py`（对检查点策略做100图验证）、`forem/scripts/task7_lower_window_stats.py`（按窗口统计）。
- `forem/config/task7/lower_train.json`：新增`"failure_mode": "cbl_continue"`（阶段L训练配置；注意该共享配置此后即启用C′）。
- 测试：新增`forem/src/task7_sim/tests/test_failure_mode.py`（15例：构造校验、底盘碰撞/IK首子步/IK次子步/半步失败的B、G、reward构成，同步奖励，20次失败终止与mask、terminal阈值仍5、尝试时间超时（含半步混合）、回合时钟、mask真值表、混合批非失败环境逐位相同、失败后到达strict为False、EpisodeEnv透传）。

### 测试与回归结果（事实）
- `test_failure_mode.py`：15 passed（CPU）。
- 默认模式逐位对照：`results/task7/t7.18.4-diag-20261022/compare_default_mode.py` → `compare_default_mode.json`：12环境、sync/async，Transition全部字段（含观测）与Core终态、以及`rollout()`（execute=False）特征均与改前core逐位相同。
- 全目录回归（GPU2，分目录执行，因同名测试文件在合并调用时收集冲突）：`task7_sim/tests` 258 passed（322 s）、`task7_lower` 18 passed、`task7_upper` 69 passed 2 skipped；均退出0。日志`regression_full.log`。
- 冒烟：C′ 32环境3000转移（init-weights路径、计数）正常（smoke-cbl-async/）。

## 四、run-id t7.18.4-diag-20261022 — C′诊断微调（150k转移）
- 设置：E256、seed 4718、150000转移、`failure_mode=cbl_continue`；网络/target/温度/优化器/更新计数取自v3 interrupted（sync步1,598,453、async步1,526,199）；**经验池与环境全新（C′数据重采）**；`warmup_transfers=0`（诊断配置`diag_config.json`，其余同v3）。sync GPU2（容器PID 3746388）、async GPU3（容器PID 3746386），均已正常结束（summary.json，墙钟2841 s/3151 s）。产物`results/task7/t7.18.4-diag-20261022/diag-{sync,async}/`（learning.jsonl、summary.json、final.pt约12.7GB等），窗口统计`window-stats.json`，验证`diag-{sync,async}-final-validation.json`。
- 所有损失/Q有限（Q_abs_max：sync 12→60，async 85→185，持续增长）。

### 窗口对照（每1000转移；v3旧奖励同期见下）
列：段/千转移｜到达/段｜超时/段｜以IK失败结束的段占比｜IK失败动作步/千转移（仅C′有）

C′ 同步：
|窗口|段/千|到达/段|超时/段|IK结束段占比|IK失败步/千|
|---|---|---|---|---|---|
|0–10k|2.1|0.571|0|0.286|133|
|10–25k|6.5|0.186|0.010|0.495|58.6|
|25–50k|9.7|0.161|0.322|0.421|37.2|
|50–75k|11.1|0.217|0.278|0.343|57.8|
|75–100k|9.8|0.135|0.298|0.363|53.1|
|100–125k|11.8|0.240|0.277|0.355|69.2|
|125–150k|11.3|0.201|0.240|0.403|78.4|

C′ 不同步：
|窗口|段/千|到达/段|超时/段|IK结束段占比|IK失败步/千|
|---|---|---|---|---|---|
|0–10k|18.2|0.071|0|0.857|371|
|10–25k|17.5|0.125|0.008|0.669|222|
|25–50k|21.4|0.090|0.021|0.759|327|
|50–75k|24.6|0.065|0.018|0.795|381|
|75–100k|26.4|0.092|0.012|0.778|414|
|100–125k|27.0|0.083|0.006|0.794|419|
|125–150k|26.8|0.076|0.018|0.773|419|

v3旧奖励（漏洞前后，节选自window-stats.json）：同步 段/千 30→34（0–1M），1.2–1.3M 58，1.4–1.5M 120，1.5–1.6M 150；超时/段0.06–0.08→0.0003；IK结束段占比0.28–0.36→0.72。不同步 段/千 8（0–1M），1.3–1.4M 138，1.5M后193；超时/段0.63–0.73→0.001；IK结束段占比0.05→0.72。

### 终止语义下100图验证（与v3同口径，`evaluate`）
|策略|段数|到达|失败|超时|IK失败|严格成功|
|---|---|---|---|---|---|---|
|v3 sync 1.598M（基线）|528|.125|.869|.006|.670|.03|
|C′续训150k sync|511|.123|.838|.039|.448|.11|
|v3 sync 750k（漏洞前）|472|.218|.689|.093|.288|.28|
|v3 async 1.526M（基线）|546|.097|.890|.013|.714|0|
|C′续训150k async|549|.093|.883|.024|.752|0|
|v3 async 1M（漏洞前）|838|.107|.178|.715|.047|.07|

### 判定（推断，依据上表）
- **不同步：漏洞未消失。**训练中IK失败动作步占转移42%（对照：v3不同步漏洞前IK失败段约0.4次/千转移），77–80%的段以“累计20次失败”结束，超时仅1–2%（漏洞前约70%），到达率无回升，验证与基线几乎相同（失败.883，IK失败.752，严格成功0）。且IK失败步占比在上升/持平而非下降，Q绝对值持续增长。
- **同步：部分缓解但不能判消失。**段数回落（11/千，但同步旧奖励下“健康”基线约30/千，因同步段较短，口径不同）、超时恢复到0.24–0.32、验证严格成功由.03升至.11、IK失败率由.67降至.45；但IK失败动作步占比由37/千回升至78/千、自碰撞失败占比升高（.14→.31）、到达率仍.12–.2低于漏洞前.22，验证失败率仍.84。
- 按任务约束：同步或不同步任一仍明显出现快速失败即停下报告。**故未启动v4，不再改奖励。**
- 局限：仅150k转移（约占v3出现漏洞所用转移的1/10），初始化自已退化策略、经验池从零重采，短窗口不能排除继续训练后恢复；亦不能反过来证明C′原理无效。未做原因定位实验（例如失败动作步奖励分量分布、IK失败残差大小、γ与Q尺度），**这些是待验证假设，不是结论**。可能线索（假设）：IK失败残差项无界，失败步付−2外还付0.5·(d/0.1)²…，但策略仍偏好失败，说明成功推进的预期回报可能低于“尽早累计失败”；异步时间惩罚对首子步失败动作步为0。需要用户/Codex决定下一步（例如先统计失败步与非失败步的平均奖励分量）。

## 五、遗留与下一步
- 状态blocked，等待决定。未做：task7.13 L.0/L.3补注训练模式（SRC-0912要求，尚未做）；v4目录`t7.18-v4-20261022`未创建、未启动训练、GPU2/3空闲。
- 注意：`config/task7/lower_train.json`已含`failure_mode=cbl_continue`，今后用该配置启动训练即为C′；若方案放弃需移除该字段（核心默认仍terminal，不影响默认行为）。
- 大文件：`diag-sync/final.pt`（12.7GB）、`diag-async/final.pt`、`smoke-cbl-async/`（726MB）为本任务产物，可按需清理，未入Git。

- 当前负责人：Claude子Agent（Sonnet5.5），blocked；日志[agent_logs](../../../../agent_logs/task7/task7.18/task7.18.4/20261022-claude-sonnet-reward-fix.md)。

## 六、再次变更：C′＋去掉不同步时间惩罚，v4从头正式训练（[SRC-0913](../../../../SOURCES.md#src-0913)）

### 6.1 代码与测试（run-id t7.18.4-v4-impl-20261022）
- 改动：`task7_sim/core.py`新增`async_time_penalty`（默认1.0，范围[0,1]；不同步奖励`B+G−dt`改为`B+G−async_time_penalty·dt`，同步忽略；`Transition.dt`仍为已提交仿真秒，计时不变）；`env.py`透传；`task7_lower/training.py`读`config.get('async_time_penalty',1.0)`，并**只加记录**：训练state/learning.jsonl新增`episode_end{fail_limit,other_terminated,truncated}`、验证json新增`episode_end_reasons`；`config/task7/lower_train.json`新增`"async_time_penalty": 0.0`（与`failure_mode=cbl_continue`同在阶段L训练配置）。新增`scripts/task7_lower_watchdog.py`。
- 测试：新增`test_async_time_penalty.py`（10例：默认1.0逐元素等于原式、=0时仅去掉dt项且B/G/dt/mask/done/reason不变、部分权重、失败步本无时间项、同步不受开关影响、EpisodeEnv透传、范围校验）、`test_watchdog.py`（5例）。回归（GPU2，分目录）：`task7_sim/tests` 268 passed（324 s）、`task7_lower` 23 passed、`task7_upper` 69 passed 2 skipped，均退出0（`regression_full_r2.log`；训练代码改动后`task7_lower`又单独重跑23 passed）。默认模式逐位对照`compare_default_mode.py`仍全部为真（含rollout）。
- 看门狗dry-run（用v3数据，`--once --dry-run`）：规则(b)对v3 async（段/千189.6>3×7.1）与sync（156.6>3×31.5）均判触发，未创建STOP。

### 6.2 v4正式训练（均无`--resume`、`initialized_from=null`、不加载任何旧检查点）
- 目录：`forem/results/task7/t7.18-v4-20261022/formal-v4-{sync,async}`；seed 4718、E256、各5M转移/4999743更新、每250k完整检查点＋100图验证（终止语义）；config含`failure_mode=cbl_continue`、`async_time_penalty=0.0`；几何schema4 `selfcoll-multisphere-v4-spherepairs-20261021`（SHA 6c41120a…）。源码/配置哈希：`source-manifest-formal-v4.json`（85个文件，SHA256 7ef40d87…6066）与各run的`training-metadata.json`、`source-manifest.json`、`launch.json`。性能门沿用v3 `formal-gate.json`（未重测，登记[SRC-0921](../../../../SOURCES.md#src-0921)，首个250k检查点后需用实测墙钟复核）。
- 启动时刻2026-10-22 12:34:09；GPU：sync GPU2、async GPU3（启动前无compute进程）。
- PID（宿主视角）：

|对象|sync|async|
|---|---|---|
|supervisor|3949059|3949105|
|worker|3949069|3949120|
|看门狗（两run共用）|3949173|—|

- 启动核查（12:3x）：两run均≥2000转移，损失/Q有限（见learning.jsonl），无Traceback，GPU2/3各有对应worker。

### 6.3 看门狗与早停判据
- 脚本`forem/scripts/task7_lower_watchdog.py`，`setsid nohup python3 -u`，日志`results/task7/t7.18-v4-20261022/watchdog.log`（.out同目录），每600 s检查，两run都有`summary.json`或`STOP`后自行退出。触发时在**对应run目录**创建`STOP`并写`WATCHDOG_STOP.json`（规则、详情、当时指标）。
- (a) 相邻两个250k验证步之间的训练回合中，因累计失败达上限（20）而结束者占已结束回合>50%，且连续两个区间都满足（每区间已结束回合≥10）；(b) 最近50k转移的段/千转移>该run 450k–500k窗口值的3倍（步数<550k不判）。解释与限制见SRC-0921：验证`evaluate`为终止语义，故(a)用训练回合计数而非验证json。
- 监控：`python3 forem/scripts/task7_lower_monitor.py forem/results/task7/t7.18-v4-20261022/formal-v4-sync`（async同理）；`tail -n 5 forem/results/task7/t7.18-v4-20261022/watchdog.log`；窗口统计`python3 forem/scripts/task7_lower_window_stats.py <run>/learning.jsonl 0,250000,...`。
- 停止：`touch <run>/STOP`（worker保存interrupted后退出）；全部停止后看门狗自行退出，或`kill 3949173`。恢复（尚未执行）：确认该run旧supervisor/worker已退出、GPU无compute，`safe_to_resume`通过（interrupted.meta/账本），移除该run的`STOP`和`WATCHDOG_STOP.json`，在forem-dev内用与launch.json相同的参数重启`scripts/task7_lower_supervise.py`（`--output`、`--gate`同上，CUDA_VISIBLE_DEVICES=2/3）；若因规则触发而停，恢复前须先由用户决定是否继续；重启看门狗：`setsid nohup python3 -u scripts/task7_lower_watchdog.py --runs <两run> --log <log> > <out> 2>&1 &`（注意被触发的run已有STOP会被视为已结束，须先移除）。
- 已执行的清理：按指令删除`diag-sync/final.pt`、`diag-async/final.pt`（各12.7GB，诊断用经验池检查点；`final.actor.pt`、summary、learning.jsonl保留）。

### 6.4 限制与待验证
- 早停判据是工程选择；触发后不自动改奖励。去掉不同步时间惩罚是否消除“主动失败”是**待验证假设**，需训练数据确认；同步变体仅用C′。
- 总耗时按v3约30 h/变体估计（未重测）；训练期共享CPU/IO竞争与失败步比例会改变速度。
- 本次写的task7.13 RESULTS注记已追加；历史第一至五节保留。

## 交接
- 当前负责人：Claude子Agent（Sonnet5.5）临时执行，额度恢复后交回Codex；日志[agent_logs](../../../../agent_logs/task7/task7.18/task7.18.4/20261022-claude-sonnet-reward-fix.md)。

## Claude更正看门狗（2026-10-22 13:48）

- 25万步时累计20失败结束回合占比同步0.61、不同步0.77（早期弱策略的正常现象），原规则(a)将在50万步误触发；新增`--share-min-step=1000000`只判≥1M步区间，重启看门狗为PID 4016803（[SRC-0914](../../../../SOURCES.md#src-0914)）。规则(b)保留，策略变好也可能使段/千转移上升，触发时须人工核对。
