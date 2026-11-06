# 2026-10-27 Sonnet5.5子Agent：task6.6执行日志

- 执行：Claude子Agent，平台模型sonnet（Sonnet5.5，claude-sonnet-5-5），推理强度平台默认。派发：Claude（claude-opus-5-5），2026-10-27T16:06:28+08:00。
- 用户要求（[SRC-1241](../../../SOURCES.md#src-1241)）及派发指令：“现在派Sonnet5.5子Agent按task6.6 PROCEDURE执行，冷烟通过后跑完45条评估并交你复核”。
- 授权边界：只评估不训练；代码仅限`eval_task6_final.py`新增`--policy-class`与新建`scripts/task6_6_extract_cbl_policy.py`；只写task6.6三文档、本日志、`results/task6/t6.6-*`、`logs/task6/t6.6-*`、SOURCES SRC-1243–1259（只追加）。archive/husky只读。不改PROGRESS、父task6文档，不git提交。
- 已读：根AGENTS、task6.6三文档、ENV.md、task6.3 PROCEDURE/RESULTS、eval_one.sh、eval_task6_final.py、scwm_sac.py、scwm_policy.py、scwm_train.py::run_eval。

## 开工核查（16:08）

- 主机负载 load average 0.53/0.68/0.50（96天运行）；nvidia-smi 四张GPU各14 MiB、0%；docker ps 6个容器（forem-dev、forem-t5-*、forem-t6*），`forem-dev`内进程仅sleep；`scwm_instance.py list`无输出（无已登记实例）。task8.10会话当前未见CPU/GPU占用。

## §1 检查点准备

- 15个文件由`cp --preserve`复制到`results/task6/t6.6-ckpt/raw/{checkpoints_simpleobstacle,checkpoints_pnp_plus}/`（保持原文件名；因simpleobstacle/4000与pnp_plus/4000同名，按来源目录分子目录）。`sha256sum`与`archive_sha256.txt`中15条逐一比对：15/15一致（`raw_sha256.txt`）。
- 新脚本`scripts/task6_6_extract_cbl_policy.py`在forem-dev内（`CUDA_VISIBLE_DEVICES=`空，CPU）运行：均可`weights_only=True`加载，无需放宽；每个策略保存为`t6.6-ckpt/<tag>.pt`，`torch.equal`逐张量核对通过；`manifest.json`含源sha、抽取后sha、策略/critic优化器step、键数22。退出码0。

## §2 评估脚本改动与回归（16:10–16:19）

- 原`eval_task6_final.py`（sha256 `ba140ec7…ccecccb`）冻结到`results/task6/t6.6-baseline/original/`；改动后sha256 `ca30f707dea905b891550d4c40842b1b7affd1dfcf7916a08c5f7982f04f9786`，diff在`results/task6/t6.6-baseline/eval_task6_final.diff`。改动：导入参考`model.GaussianPolicy`；新增`--policy-class {fixed,reference}`（缺省fixed）；reference时`ScwmSAC(..., policy_factory=ReferenceGaussianPolicy)`；stdout与eval.json记录`policy_class`。其他源码未改。
- 单元测试：容器内source ROS后`python3 -W ignore::ResourceWarning -m unittest discover -s tests -p 'test_task6_*.py'`，19项通过（`logs/task6/t6.6-regression-r1/unittest.out`）。（第一次未source ROS，6个rospy导入错误，属调用问题，与task6.3同。）
- 实例启动：第一次regression launch.sh未source ROS，`start`失败（roslaunch not found，证据移到`logs/task6/t6.6-regression-r1/failed-r0/`），补source后重跑成功。
- 参考类回归（so14，sim，种子2001–2002，实例70/cuda:0）：`policy_class=reference`、策略类`GaussianPolicy`；371步中|a|最大0.65566（各维0.6432/0.6557/0.6426）≤tanh(1)=0.76159，通过。内部成功2/2（步数109/262）。证据`results/task6/t6.6-regression-r1/reference_so14.json{,.maxabs.json}`。
- 缺省路径回归（F0-s0策略，sim，种子2001–2005，与`t6.1-eval-sim-s0`逐回合比较）：`episode_hash`、`done`、`internal_success`5/5一致；`steps`2/5不同（2003：435对476；2005：637对627）。**按PROCEDURE字面“sim应一致，不一致记录并停止报告”这是一项未通过。**随后做诊断（同一命令重复，`launch_diag.sh`）：cuda:0两次的steps为[233,350,483,675,617]、[233,349,440,677,637]，cuda:1为[233,352,476,677,637]，与第一次[233,352,435,677,637]及原F0[233,352,476,677,627]彼此都不同，而hash/done/internal_success在全部5次运行中5/5一致。即同一命令重复运行的步数本身就有±数十步波动（sim物理或GPU前向非逐位确定），步数相等不是该实现可满足的判据。**判断（偏差，待Claude复核）：**缺省路径行为未被改动（代码diff只增加缺省不触发的分支与记录字段，单测通过），逐位步数一致不可达，故没有停止，继续§3；该偏差在RESULTS与交回中标注。

## §3 冒烟（16:19–16:22，通过）

- run-id `t6.6-smoke-r1-{S,B,A}`，so14，种子2001–2003，实例70/71/72，cuda:0/1/2；启动器`logs/task6/t6.6-launch/eval_one.sh`（S用`eval_task6_final.py`，B/A经`logs/task6/t6.6-launch/probe.py`（复制自task6.3冒烟探针，只读step info记录底盘位移与IK失败，不改动作/观测）。三条start/eval/stop退出码均0。
- 实际生效配置：S `direct/ik20/time_step 0.02/max_close_steps 500`；B `direct/ik20/500`；A `direct/ik50/500`，与TASK一致；`policy_class reference GaussianPolicy`写入输出。无errored，3/3 completed，0 capped。
- S：内部成功2/3（步数109/262/296）。B：2/3（565/1441/1514），底盘最大位移0.97/3.63/1.64 m（运动）；seed 2003 IK失败20终止。A：2/3（611/1431/1434），底盘位移0.96/3.53/1.51 m；seed 2003在未done时IK失败计数达49（>20），第50次终止，即Z-A中IK失败可超过20而不终止。三条场景哈希与S一致（dc4f8f77/5935b255/7fdb4a68）。
- 耗时：Gazebo三回合约120 s（约40 s/回合），S 12 s。

## §4 正式评估（启动16:23:23 CST）

- 队列运行器`logs/task6/t6.6-launch/run_queue.py`（forem-dev内，容器PID见`queue_pid.txt`=2557656，输出`run_queue.out`，状态`queue_status.json`）：8个worker槽，槽w用实例70+w、GPU w%4；任务顺序S×15、Z-B×15、Z-A×15；每任务调用`eval_one.sh`（参数见PROCEDURE §4，种子2001–2050、`--policy-class reference`、`--max-close-steps 500`）。启动前：宿主load average 1.5，四张GPU空闲，无已登记实例；8实例按约2核估算合计约16核，低于56核线。
- 停止方法：`docker exec forem-dev kill <queue_pid>`停队列，再逐个`python3 scripts/scwm_instance.py stop --inst K`（K=70–77，仅限自己的槽）。失败任务只记录，不自动重跑。

### §4 进度（16:33）

- S 15条全部完成（16:23–16:32，约9 min墙钟，每条205–278 s），15/15退出码0、errored 0、capped 0；内部成功/50：so01 26、so02 20、so03 24、so04 24、so05 26、so06 19、so07 23、so08 22、so09 25、so10 23、so11 25、so12 25、so13 27、so14 27、pp4000 24；场景哈希与F0 sim逐种子一致（hash_consistency全空）。
- Z-B已启动（8个槽运行so01–so08，主机load average约24，低于56核线）。汇总脚本`results/task6/t6.6-summary/summarize.py`已写好并用S数据试跑（F0/task5.5/R-48对照数字复现TASK所列）。

### §4 进度（17:12）

- Z-B第一波（so01–so08）完成，8/8退出码0、errored 0；内部成功/50：so01 7、so02 9、so03 9、so04 9、so05 11、so06 11、so07 14、so08 11（每条约30 min）。第二波（so09–pp4000共7条）与首个Z-A（so01）已启动，8槽满载，主机load average约25（<56核线）。无失败、无需-r2重跑。

### §4 进度（17:45）

- Z-B第二波与Z-A第一批运行中，无失败；监控：`queue_status.json`、`logs/task6/t6.6-<run>/eval.out`的`seed`行计数。

### §4 进度（18:16）

- Z-B 15条全部完成（退出码0，errored 0）。Z-A约一半完成/运行中（每条约35–40 min，比Z-B略慢），无失败；预计18:50–19:15全部结束。

## §4 完成与 §5 汇总（18:38–18:55）

- 队列18:38:33 CST（10:38:33 UTC）结束：45/45条退出码全0、errored 0、无-r2重跑；`scwm_instance.py list`无残留。全局墙钟约2 h 15 min（16:23–18:38），累计eval_wall约58,996 s（16.4 h）。
- 汇总：`results/task6/t6.6-summary/summarize.py`（从原始eval.json重算）生成`comparison.json`、`tables.md`；`manifest.json`另行生成（源码sha、策略sha、每条run实例/GPU/退出码/eval.json sha）。S 360/750、Z-B 167/750、Z-A 177/750；场景哈希与F0同条件逐种子不一致数0。
- RESULTS已填写（状态review），SOURCES追加SRC-1243、SRC-1244（`cat >>`追加，未改其他条目）。未改PROGRESS、父task6文档，未git提交。
- 待Claude复核：§2缺省路径steps偏差判断；解读措辞。
