# TASK4-SCWM-IMPL：新版Task4（4.7–4.13）Claude主Agent实施日志

- Agent：Claude（主Agent），实际模型claude-sonnet-5-5，推理强度：会话级`--effort high`（启动参数，非本任务按需选择；常规步骤按low对待，跨模块机制核对按medium对待——如实记录：平台实际会话强度为high，无法按步骤切换）。
- 状态：active。开始 2026-10-09T10:09+08:00。
- 用户要求（2026-10-09）：接手并实施新版Task4——相同任务/观测权限/训练预算下，把SC²-WM“候选动作→预测后果→内部反馈修正→最终策略动作”接入Husky普通SAC，检验真实任务收益。授权范围内的源码/配置修改、依赖适配、构建、仿真、数据采集、训练与评估；按4.7→4.8→4.9→4.10→4.11顺序；4.12仅按文档条件作后续独立因素；4.13保留给Codex独立复核。允许委派子Agent，主Agent负责依赖控制/共享文档/核验。
- 不做：不恢复VIO，不制造误差，不压低基线，不新增传感器/实验组，不改奖励/终止语义；不修改husky/nmoma/topay/scwm参考仓库；不把旧4.1–4.6结果当新验收；不自行扩缩预算（规模：100万步、原讨论3种子、一轮完整训练+评估≤72h；有效记录若仍有总预算歧义，集中询问）。
- 已读：根AGENTS、forem/AGENTS、README、PROGRESS、SOURCES SRC0169–0182、Task4 TASK/PROCEDURE/RESULTS、task4.7–4.11 PROCEDURE（4.12/4.13后读）、task3_env.py、task3_sac_entry.py、sac.py、model.py、config/task3/*.yaml、run_task3_core.sh、husky_core.launch。

## 接手前现场核查（2026-10-09 10:09，只读）

- Git：main，根HEAD 438c5f9，工作区230项未提交改动（含大量其他Agent的未跟踪文档）；本Agent不做`git add -A`，不回滚他人改动。
- 容器：仅`forem-dev` Up，`docker top`只有docker-init与`sleep infinity`；无gzserver/roscore/python训练进程；`task4_formal`相关配置`config/task4/sac_baseline.json` enabled=false（旧VIO暂停，保持）。
- 硬件：4×RTX PRO 6000 Blackwell（各约96GiB，空闲14MiB），64逻辑CPU，约251GiB RAM；forem-dev内`nvidia-smi -L`见4卡，torch 2.7.1+cu128 `cuda.is_available()=True,device_count=4`；容器`OMP_NUM_THREADS=2`、shm 2GiB、bridge网络、`ROS_MASTER_URI=http://127.0.0.1:11311`（容器内单master，当前入口一次一个仿真，共享锁`logs/task0/.smoke.lock`）。
- 模型身份：Claude主Agent会话`--model claude-sonnet-5-5 --effort high`。Codex入口：本会话无可用Codex入口，不假装调用；4.13需用户/Codex另行启动。

## 执行记录与证据

### 2026-10-09 task4.7（完成，交review）
- 只读审计 + CPU反例：`scripts/audit_scwm_policy_tanh.py`，run-id `t4.7-contract-audit-r1`，退出码0；确认`GaussianPolicy.predict`双tanh（执行动作∈±0.7616，sample/更新为单tanh）。25个文件sha256见`results/task4/t4.7-contract-audit-r1/source_manifest.json`。合同/映射/预算表写入[task4.7 RESULTS](../../tasks/task4/task4.7/RESULTS.md)。
- 唯一待用户确认的总预算口径（不阻塞4.8）：(a)100万步按每方法每种子run；(b)共同前缀分叉；(c)最终测试实例数。

### 2026-10-09 task4.8（进行中）
- 基线探针 `t4.8-probe-r1`（经`run_task3_core.sh`，Task3旧入口，300步随机/策略混合，CUDA）：退出码0，启动6s，300步+44次更新共19.9s（含首次reset）；确认仿真栈在本会话可用。注意：这是旧Task3入口，含双tanh，不是新基线。
- 新代码（均新增，未改`forem/src`）：`scripts/scwm_policy.py`（FixedGaussianPolicy单tanh）、`scripts/scwm_sac.py`（GpuReplay uint8设备回放+ScwmSAC完整状态保存）、`scripts/scwm_env.py`（物理成功：Gazebo LinkStates wrist_3×静态变换）、`scripts/scwm_train.py`（训练入口：预算/账本/检查点/恢复/验证）、`scripts/scwm_wm.py`（WM，4.9）、`scripts/diag_scwm_obs_lag.py`（观测滞后诊断）、`scripts/bench_scwm_update.py`、`scripts/prof_scwm_update.py`。
- 测试：`tests/test_scwm_sac.py`（7项，含与参考`SAC.update_parameters`逐位一致、完整状态续训一致、回放npz往返）CPU与cuda:3均通过；`tests/test_scwm_wm.py`（5项）通过。
- 性能（GPU微基准，非端到端；有子Agent同时在跑仿真，数字略含噪声）：单次更新 参考路径31.6ms → 设备回放路径17.7ms（cudnn.benchmark 16.7ms）；profiler：GPU核时间≈5.1ms/更新、CPU/launch受限；`select_action`0.9ms；回放push 0.17ms/转移；GPU显存0.8GB+回放（100k×2×14.4KB=2.9GB）。证据：`results/task4/t4.8-perf-update-r1/`。
- 委派：task4.8.1（多实例隔离与并行吞吐），子Agent Sonnet5.5/medium，已派发，写`scripts/scwm_instance.py`及测试；三文档位于`tasks/task4/task4.8/task4.8.1/`。子Agent持`logs/task4/.sim_exclusive`期间我不启动仿真。

### 2026-10-09 用户追加指令（对话内）
“装不下也没关系，一定要按照原项目的配置跑一次。”——解释：完整规模（每方法每种子100万步、3种子）按原项目配置执行一次，**即使超过72h也要跑完**；不得为凑时限缩步数或改任务语义。因此：保持参考实时步进（不启用固定窗口）、transition_noise 0.04、奖励/终止/动作原样；仅保留4.7已记录并经用户“采样/logprob/更新一致”要求支持的双tanh公共修复。性能优化义务不变（仍须测并优化reset/更新等，但优化不得改语义）。72h可达性改为如实报告，不再作为开跑门槛。

## 交接

（待写。）

## 任务归属与委派

- 父任务：[task4](../../tasks/task4/TASK.md)；节点：task4.7–4.13 三文档在各自目录。
- 负责人：Claude主Agent；4.13独立复核Codex（未接手）。
- 子Agent：尚未派发。
