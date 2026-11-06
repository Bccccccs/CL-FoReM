# task9.13 完整RLlib SAC独立执行记录

2026-11-06T09:39:41+08:00 · active · 执行负责人Codex子Agent `/root/rllib_task9_13`；实际派发请求模型GPT6.1sol（平台gpt-6.1-sol）、high，派发工具确认后父日志补记。独占写入本任务PROCEDURE白名单（含本三文档与独立日志），共享SOURCES/PROGRESS/DECISIONS及父三文档由父管理，不并发写；task9_lr现役冻结源只读。输入/交付/验收沿本三文档与用户本轮明确执行指令；候选GPU `GPU-656ca5c1-681f-48a2-7d1f-a00824723f68`，启动前复核。独立日志：[20261106-codex-execution.md](../../../agent_logs/task9/task9.13/20261106-codex-execution.md)。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨接口语义与恢复核查需high。此前未执行描述为历史，当前授权已实际派发执行。

当前状态：准备委派；接手后在此追加实际证据/版本/成本/异常，不改共享台账。

## 2026-11-06 09:40–09:49 +08 实际接手/隔离框架

- 执行者Codex `/root/rllib_task9_13`，实际派发gpt-6.1-sol/high；已读根/forem AGENTS、README、PROGRESS、ENV、本三文档及SRC-T9-EXPLORE-20261106。实际分支`codex/task9-lower-improve`，保留现场全部既有改动；写范围只限9.13白名单。
- 启动前GPU2 UUID `GPU-656ca5c1-681f-48a2-7d1f-a00824723f68`仅14MiB/无compute；GPU0/3现役、GPU1 task10 probe均未干预。宿主允许CPU0-63，8核配额24-31；内存可用约205GiB，/home余7.0TiB。
- 独立容器`forem-t9-13-runtime`，CID `72037a4001c0cdf5c2600f91ee40a593ee8553d61b2edb891ae7a667aa9cc7f2`；基镜像`mm_husky:node01`/ID`e674db49b815`，仅挂GPU2，cpuset24-31，shm8g。`/workspace`本工作树forem，`/history`原工作区forem只读；PYTHONDONTWRITEBYTECODE=1，CUDA_VISIBLE_DEVICES=0，库线程2。只在新容器安装Ray[rllib]2.40.0与pyarrow17.0.0，Python3.10.18/Torch2.7.1+cu128沿用；未升级现役容器。
- 安装原件`forem/logs/task9/task9.13-setup/install.log`。对应tag官方源码已读：`https://raw.githubusercontent.com/ray-project/ray/ray-2.40.0/rllib/algorithms/sac/sac_torch_policy.py`、`.../sac.py`、`.../utils/replay_buffers/replay_buffer.py`。本机对应源码导出`forem/build/task9_13/native-{model,training,loss}-source.txt`。
- 实际构建完整`ray.rllib.algorithms.sac.SAC` Algorithm；保留原生`SAC.training_step -> DQN._training_step_old_api_stack -> synchronous_parallel_sample -> MultiAgentReplayBuffer -> train_one_step -> RolloutWorker.learn_on_batch -> SACTorchPolicy` loss/四Adam/target同步。只将本地RolloutWorker.sample桥接已有GPU256环境生成的10条消费批；父确认该方案满足完整框架方向，继续核查。
- `probe-native.log`实证native RR=[1,1]、250前0update、260首1update、target_updates=1、4原生Adam、model/learner cuda:0。训练强度25.6为256样本/10新转移；不是声称25.6个optimizer update/转移。1000预期75更新，3M预期299975；实际smoke仍在运行。
- 差异需明确：C旧replay在消费260前只见259；RLlib批10先全部插入再更新；RLlib均匀有放回，C无放回；RLlib原生Huber/Adam eps1e-7/独立Q优化器/同时构图/连续alpha，C MSE/eps1e-8/合并Q优化器/critic更新后actor/首update将alpha从1切为exp(logα)*.35及最终.05停止。不会修改C或重写native learner以伪称纯框架差异。
- Native replay沿RLlib原生CPU存储；批量环境和网络仍GPU，回放采样批搬GPU。该CPU/GPU布局差异明确计成本；不能声称两者回放同GPU。保存native replay get_state、policy get_state（含优化器）、独立target、native counters、全局RNG与环境pending/游标。
- 用户经父明确评估澄清：每run每250k含3M终点100随机+96语义=196，四run合9408；旧300/288为三权重汇总，不创建伪588单策略manifest。本任务三文档已追加更正，保留历史。

待父合并来源条目：建议SRC-T9-RLLIB-EXEC-20261106，来源类型本机隔离安装/对应tag官方源码/定向实测。支持上述版本、原生调用链、RR与首update、框架差异；精确本地证据如上，核查人本子Agent/2026-11-06。当前尚无成功率/性能结论，native-check与实际环境smoke执行中。

## 09:52–09:57 排错事故与真实环境C smoke

- 工程错误：新调度脚本原名`scripts/task9_13/queue.py`遮蔽Python标准库`queue`，且当时顶层启动逻辑未加main保护；`check_environment.py`/C续smoke导入Torch期间意外执行该脚本，递归启动自身worker。父与本Agent核PPID链一致，非外部任务。
- 已改名`program.py`并加`if __name__=='__main__'`保护；随后把mkdir/signal注册也移入main。只在本CID内按精确已核python脚本身份清理递归树，再重启该独立容器回收zombie。未干预GPU0/1/3或其他容器。保留失败目录`results/task9/task9.13-failed-shadow-20261106-r1`和同名logs、进程身份原件`results/task9/task9.13-setup/queue-shadow-failure-processes.json`。父观测GPU进程进入reset；失败目录确有sampling-started而无任何interactions.jsonl，即未到该版本动作写前intent；按无可认定正式转移/初始化排错成本保留，不算正式250k，正式run将用r2新目录。不把其墙钟或CPU成本删去；进程深链导致的累计CPU成本尚待完整/proc已存快照推定，不能伪造精确值。
- 修复导入回归：容器内`import queue,torch`解析标准库queue；加载program模块未启worker。源脚本再无queue.py。此问题属于工程准备，并未影响先前已完成C512有效checkpoint。
- C真实环境smoke已实际完成：512有效消费/512生成/26updates，初始256环境reset59.6693s、首save22.5104s、总90.7157s；重启后实际从该完整checkpoint续至1000/1000生成/75updates，续阶段32.3338s，policy/replay/optimizer CUDA（Adam step标量CPU）。原件`task9.13-smoke-C/{profile-summary.json,smoke1000-terminal.json,summary.json}`。
- C显式环境合同：`environment-check.json`通过，恢复512时pending.cursor256/remaining0，三条显式动作、256行、54字段（obs/reward/mask/active/done/action/attempt/commit/reason/dt和下一观测/状态）最大误差0，预登记float32 atol1e-5/rtol1e-5，整数/布尔精确；确定性动作重复相等。第一次恢复脚本的通用digest不支持NumPy RNG数组，已只在测试脚本将数组转list，保留r2失败日志，r3通过；不是环境/RNG数值错误。
- 父指出上述512处pending恰好耗尽，现额外针对非空pending测试：C生成一个新真实256批、只消费1保存513再分别前后恢复消费10，比较下一更新全部权重/target/全部优化器/replay样本/RNG/cursor。R主smoke暂停在513，保留255未消费环境转移和3条待插native replay队列，再恢复至1000。新增工程生成/消费独立记账，不计正式。
- 评估改为轻量只读MetricsObserver：沿原Core._finish success/d/r，记录首次拒绝原因、按动作拒绝数、无拒绝停滞、原定义最终到达、IK残差RMS/峰值；自然solve_world单次包装CUDA events/API wall，后置收集，不新增求解、不抽RNG。两臂同评估包装和开销，独立记录observer hook成本。该增补只改evaluation.py/新增observer.py，C旧smoke恢复工程检查以显式两文件范围bridge校验，其余训练/环境哈希仍严格相等，正式loader无放宽。

## 10:00–10:16 最终验证、封存与正式部署

- 修正Ray2.40 `ray.rllib.utils.debug.update_global_seed_if_necessary`源码格式错误：其Torch分支写`CUBLAS_WORKSPACE_CONFIG='4096:8'`而非合法`:4096:8`，并设cudnn.deterministic=True。最终两臂共同合法值/确定性True/benchmarkFalse；R内部config.seed=None，由共同trainer实际4718/4719播种。未改现役或native loss/optimizer。旧C hash不等尚未看数值即先固定预登记atol1e-6/rtol1e-5，最终版下C/R非空pending恢复全部tensor误差0。
- 最终版独立重验：`task9.13-smoke-C-r2`和`task9.13-smoke-R-r2`均513暂停后恢复1000有效消费/75updates。R raw alpha约0.9999249，C capped alpha约0.3499737，与预登记差异相符，不能将该工程smoke当效果比较。R原生counters sampled1000/trained19200/target75。
- `task9.13-pending-{C,R}-r2/pending-check.json`均PASS：513处pending.cursor1、remaining255，R queue3/native sampled510，磁盘保存恢复后再消费10的全部模型/target/optimizer最大差0，replay/RNG/cursor精确一致；两分支20条工程消费另记。
- 最终原生数学/梯度复验`task9.13-setup/native-final/native-check.json`PASS：最终合法数值环境下，小batchlogprob/四loss/critic梯度差0，真实4原生Adam与target在CUDA；合成1000→1010磁盘恢复参数差0。未再全量重测。
- 指标小修并核验：原生solve_tcp_in_arm在拒绝后hold会覆写result残差，轻量observer现在ik_pre_hold克隆raw_returned，held_execution分列。no_rejection_stall明确非成功。observer-r4两臂各2随机+2语义开发回合、显式动作/nextobs/RNG parity通过；C38.7180072963s/272自然IK，R35.5990128759s/245自然IK。IK按environment_step/reset_or_candidate scope分列。该小修只影响记录，SAC/环境接受语义未变；旧smoke工程加载仅容许evaluation/observer两文件变更，正式loader严格。
- observer测试最初错替换torch.no_grad装饰wrapper的globals，实际起默认196；后已仅停止本CID内两个工程评估进程并修`__wrapped__`。最终原件统计该误尝试已请求C96/R32开发回合（此前32/32是中间快照），无完整196结果，不将其当正式评估/丢弃成本。正确r3/r4各臂4回合均保留。
- 惰性报告fixture通过，目录明确`task9.13-report-fixture`，JSON `evidence_kind='synthetic_inert_fixture_not_real_training', actual=false`、sentinel及PNG红字标签；不纳入真实12M。自动报告验证真实4×3M/299975及12×196，保留原逐回合行、按map簇paired95%区间（2000重采样，统计RNG20261106工程选择）、逐seed/domain曲线/终点和同worker成本最近登记点。失败/中断worker成本与实际episodes-started含重试请求另列，不把计划9408伪成已消费。
- 10:15:13 +08正式队列健康部署，目录`results/task9/task9.13-formal-20261106-r2`，logs同run-id。本适配包/4配置/生产脚本封存15文件于freeze，`inventory.json`列摘要；正式从TASK9_13_FROZEN_SRC/CONFIG/SCRIPTS导入封存副本，不再改封存源码。依赖锁镜像`forem/task9-rllib:ray2.40-torch2.7.1-20261106`，ID`sha256:cb40aa39d09dcf3031bcf952265307fba29b2b06626a902cdb8e7568df0b566f`，原始基镜像e674...仍未升级。CID72037a4001c0...不变，Docker重启后自身PID namespace重建，旧PID仅历史。
- 实际启动命令：`sg docker -c 'docker exec -d --user 1004:1004 -w /workspace -e TASK9_13_FROZEN_SRC=/workspace/results/task9/task9.13-formal-20261106-r2/freeze/src -e TASK9_13_FROZEN_CONFIG=/workspace/results/task9/task9.13-formal-20261106-r2/freeze/config -e TASK9_13_FROZEN_SCRIPTS=/workspace/results/task9/task9.13-formal-20261106-r2/freeze/scripts -e TASK9_13_GPU_UUID=GPU-656ca5c1-681f-48a2-7d1f-a00824723f68 -e CUBLAS_WORKSPACE_CONFIG=:4096:8 forem-t9-13-runtime bash -c "exec python3 -B -u /workspace/results/task9/task9.13-formal-20261106-r2/freeze/scripts/program.py > /workspace/logs/task9/task9.13-formal-20261106-r2/queue.log 2>&1"'`。
- 宿主queue PID2541557/start_ticks914007182（容器499），当前C4718 profile worker PID2541568/start_ticks914007196（容器509），UID1004:1004使本run STOP可宿主直接写。Torch实际GPU UUID与指定GPU2一致（device_properties.uuid去/补GPU-前缀后比较）。源identity与resources原件在正式根/当前job，GPU2网络/回放CUDA。
- 唯一新warning：UID1004无HOME使Torch kernel cache默认`//.cache/torch/kernels`不可创建，只禁磁盘kernel cache，无CPU计算fallback。当前有效profile不打断/改快照；注明初始化工程开销限制。父采集容器cgroup完整CPU/I/O/内存/GPU资源日志，当前未将线程数或进程CPU秒冒充真实累计CPU成本。
- 监控：读queue-state/active-worker、当前job/learning.jsonl、logs/profile-C-4718.log；STOP仅正式根，控制器核worker start_ticks后SIGTERM并等待完整interrupted。移除本run STOP后同封存program重启，仅InterruptedError自动恢复；其他异常定位后再手动重入，无盲重试。250k边界恢复可先补pending评估生成profile再进入remaining，3M horizon不改。现无训练成效结论，待250k真实成本与后续完整结果。

10:17:30 +08交接：C4718已落盘11000/1075updates，finite，queue/worker精确身份未变；父已独立核7000/675、GPU与/proc/cgroup，允许作为active健康后台交接，不等250k重复放行。当前CID来源仍为e674基镜像＋本隔离层实际安装，cb40是commit依赖锁快照，未以cb40重建当前CID。下一步自动完成四250k，写真实profile成本，再逐run续3M；最终由report汇总、父科学验收。剩余风险是尚未取得原生100k容量/250k真实端到端成本，GPU忙只等待，不因短程成功率选seed/停臂；真实异常先保原件定位。后续状态可由父直接读取相同目录，不需聊天恢复。
