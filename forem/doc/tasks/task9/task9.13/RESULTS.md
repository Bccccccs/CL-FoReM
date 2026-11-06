# task9.13 当前结果与交接

2026-11-06：active。完整Ray RLlib SAC已实际接入与验证，正式四run可恢复后台队列正在部署；**尚无3M训练胜负/提升结论**。负责人Codex子Agent `/root/rllib_task9_13`，实际派发gpt-6.1-sol/high。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high：需要跨训练栈、设备和恢复的因果核查。

来源：[授权](../../../SOURCES.md#src-t9-explore-20261106)、[实际源码/测试证据SRC-T9-RLLIB-EXEC-20261106](../../../SOURCES.md#src-t9-rllib-exec-20261106)。独立过程/失败成本见[执行日志](../../../agent_logs/task9/task9.13/20261106-codex-execution.md)；完整[实现栈差异表](../../../agent_logs/task9/task9.13/20261106-codex-stack-differences.md)。

## 实际实现

隔离容器`forem-t9-13-runtime`，CID `72037a4001c0cdf5c2600f91ee40a593ee8553d61b2edb891ae7a667aa9cc7f2`。GPU2 UUID `GPU-656ca5c1-681f-48a2-7d1f-a00824723f68`，cpuset24–31、最多8CPU，Torch/库线程2；Python3.10.18、Torch2.7.1+cu128、Ray2.40.0、Gymnasium1.0.0、pyarrow17.0.0。版本/容器锁在`forem/build/task9_13/{requirements-installed.txt,image-lock.txt,container-lock.txt}`。本机对应tag原生源码导出`native-{model,training,loss}-source.txt`。

实际原生调用链：`SAC.training_step → DQN._training_step_old_api_stack → synchronous_parallel_sample → MultiAgentReplayBuffer/ReplayBuffer → train_one_step → RolloutWorker.learn_on_batch → SACTorchPolicy.actor_critic_loss → 四原生Adam → 原生TargetNetworkMixin.update_target`。只替换本地worker.sample为GPU256环境批生成、按10条消费的采样桥；CNN/MLP为FoReM现有容量适配，未重写learner/loss。原生replay在CPU，抽样batch移GPU；C replay在GPU，此布局差异计入实现栈成本。

两臂共同固定合法`CUBLAS_WORKSPACE_CONFIG=:4096:8`、cudnn deterministic=True/benchmark=False；Ray2.40内部seed函数会硬写缺前导冒号的`4096:8`，故R config.seed=None，实际4718/4719由共同trainer在环境/网络前播种，不是无种子。R alpha_rule=rllib/critic_loss=huber及runtime.actual_native_config如实导出；不再继承C无效capped元数据。与旧9.11不承诺数值逐位相同。

## 已通过的必要核查

|核查|实际结果|原始证据（相对forem/）|
|---|---|---|
|最终原生小batch logprob/TD-likelihood对应loss/critic梯度|预设atol1e-6/rtol1e-5；各误差0，四模块参数均变化，4Adam参数/动量CUDA|`results/task9/task9.13-setup/native-final/native-check.json`|
|原生链真实round-robin|RR=[1,1]，首update260；合成1000/75update和75target同步；实际下一1010 update恢复精确相同|同上；合成数据证据，不冒充环境smoke|
|C最终真实环境smoke|513暂停→恢复1000有效消费/75updates|`results/task9/task9.13-smoke-C-r2/{profile-summary,smoke1000-terminal,summary}.json`|
|R最终真实环境smoke|513暂停→恢复1000有效消费/75updates；native sampled1000/trained19200/target75|`results/task9/task9.13-smoke-R-r2/{profile-summary,smoke1000-terminal,summary}.json`|
|显式环境动作合同|3显式动作×256行、54字段、最大误差0，obs/reward/mask/active/done/next state等及确定性动作重复一致|旧C`task9.13-smoke-C/environment-check.json`与最终R`task9.13-smoke-R-r2/environment-check.json`|
|非空pending/下一更新磁盘恢复，两臂|保存513，pending.cursor1/remaining255；R另有native queued3/native sampled510。恢复后各消费10，全部权重/target/optimizer最大差0，replay/RNG/cursor精确相等|`results/task9/task9.13-pending-{C,R}-r2/pending-check.json`|
|轻量observer与原环境动作/RNG不干预|各4开发回合、显式动作nextobs/reward/done精确相等；分别记录自然IK272/245次|`results/task9/task9.13-smoke-{C,R}-r2/evaluation-smoke-r4.json`及setup/observer-{C,R}-r4.log|
|报告聚合/曲线与统计管线|惰性fixture通过，顶层actual=false/evidence_kind明确为假数据；不混入正式|`results/task9/task9.13-report-fixture/`、`logs/task9/task9.13-setup/report-check-r3.log`|
|控制器导入/恢复语法|stdlib queue解析原路径；封存program导入无worker副作用；profile支持实际resume，旧失败terminal另名保留|setup日志与`freeze/scripts/{program,worker}.py`|

Observer记录原`Core._finish success/d/r`，首拒绝/原因、按动作拒绝、无拒绝且非成功的stall、原最终到达；solver raw_returned残差通过ik_pre_hold克隆取得，held_execution残差分列，不能混淆。IK CUDA events延后汇总、APIwall按environment_step/reset_or_candidate分列，不新增IK求解/策略forward/RNG抽样；observer hook开销单列。

## 正式预算、封存与自动推进

种子4718/4719；C与R各3M，共12M有效消费，从头固定3M horizon。先按C4718/R4718/C4719/R4719依次各250k profile，包含在3M；再同序恢复remaining。每250k至3M同一冻结100随机+96语义=196，四run共9408已登记开发回合；两个训练种子分别报告，不读取9.11保留测试、不挑峰值。原588终点评估已按用户澄清取消。

正式目录`forem/results/task9/task9.13-formal-20261106-r2/`，日志同run-id。`freeze/`封存本适配小包、四配置及生产worker/program/report，共15文件，inventory列精确摘要；正式通过TASK9_13_FROZEN_SRC/CONFIG/SCRIPTS从该副本读取，后续不改封存源码。task9_lr环境/控制只读导入并保留其source_contract，未复制/重新哈希历史大资产。

`queue-state.json`、`queue-identity.json`、`active-worker.json`和各phase identity/terminal给出精确容器内PID/start_ticks。每phase开始复查GPU UUID/compute、RAM/磁盘/affinity，GPU忙写WAITING_GPU等待，不抢占。完整checkpoint包括原生policy/实际GPUtarget/四optimizer/native replay/counters，以及环境/RNG/未消费batch/游标与native待插队列。250k后利用真实成熟窗口、E196和save成本自动写数值forecast；未知restore保unknown。后台程序最终校验4×3M/299975与4×12完整196，输出逐seed/域终点配对、地图簇95%区间（2000次，固定20261106统计RNG，工程选择）、同累计worker成本最近登记点、CSV/PNG曲线和成本分项，结论状态`COMPLETE_PENDING_PARENT_JUDGEMENT`。

当前成本仅工程/smoke实测；正式250k端到端成本尚待运行。训练/评估/保存恢复/安装排错分别留原件。父另采集容器cgroup CPU与I/O/GPU快照；进程CPU秒不冒充完整容器CPU成本，早期重启前未捕获部分保unknown。

## 失败与精确停止/恢复

保留早期`queue.py`遮蔽标准库导致递归worker的工程事故：已改名program.py并加main保护、定向import回归；只清理本CID并重启它。事故目录`task9.13-failed-shadow-20261106-r1`保留sampling初始化/进程树证据，非有效正式profile。旧版本smoke、C初次非确定性权重hash不一致与observer小测试装饰器误选默认196也均保留；后者实际已请求C96/R32工程开发回合，停止后正确限2+2，不删除成本。最终r2共同数值条件下，非空pending恢复张量误差0。

安全停止：在**正式根目录**创建`STOP`（本run以宿主用户1004运行，可直接写）。控制器只向自身记录且start_ticks相符的当前worker发送SIGTERM；trainer保存interrupted.pt+meta+actor，队列停止，不碰其他容器或GPU。不要kill GPU PID、不要改运行快照。

恢复：保留STOP与旧terminal/日志，先核interrupted.meta.resume_safe、完整checkpoint及最后interaction一致；消除停止原因后删除本run STOP，再以同封存program/同三环境变量重启。仅已有InterruptedError且存在interrupted.pt的phase自动从完整状态重入，旧identity/terminal另名保留；其他异常明确停下定位，无盲重试。手动定向入口为封存worker `--arm C|R --seed4718|4719 --phase profile --resume <interrupted.pt> --output <同job>`（250k前）；250k边界也会先补pending评估、保存profile后继续，250k以后用remaining。原3M horizon保持，配置与source_contract不放宽。镜像/容器和启动精确命令/宿主PID由本记录后续运行身份追加。

2026-11-06 10:15:13 +08实际后台启动确认：queue宿主PID2541557/start_ticks914007182，C4718 profile worker2541568/start_ticks914007196；容器内499/509，UID1004:1004。镜像锁ID`sha256:cb40aa39d09dcf3031bcf952265307fba29b2b06626a902cdb8e7568df0b566f`。精确命令在独立执行日志。queue-state=RUNNING，实际Torch GPU UUID与指定GPU2一致；初始GPU约11.9GiB。该身份属于启动时快照，后续以queue/worker身份文件及PID/start_ticks复核，不能按过期PID停其他进程。尚未声称250k或3M完成。

10:17:30 +08健康后台核查：当前C4718落盘11000有效消费/1075updates，全部记录loss/Q有限，3M horizon未变；250k/3M仍待运行。父另独立核过7000/675及/proc/实际GPU路径。镜像身份严格区分：**当前CID仍是从基底e674db49b815创建后在其隔离可写层安装依赖运行**；cb40aa39…是随后commit得到的可复建依赖锁定快照，并非声称当前CID由cb40重新创建。没有迁移/重建正在运行的正式worker。
