# task10.2 结果

2026-11-02 15:20 +08:00，负责人 `learning_contract`，**review（待父复跑与集成验收）**。实际模型为派发的 gpt-6.1-sol/high；未独立读取平台内部模型标识。推荐 GPT6.1sol/high、Sonnet5.5/high，理由：终局折扣、变长回放和恢复计数需要跨处因果核对。

## 范围与依据

目标与授权为父task10 B/C合同及子任务TASK：[SRC-T10-001](../../../SOURCES.md#src-t10-001)、[SRC-T10-002](../../../SOURCES.md#src-t10-002)。只修改本节点独占 `forem/src/task10/learning.py`、`forem/src/task10/tests/test_learning.py`、本节点三文档和独立日志。未改task7_upper共享模块，未写主仓results，未训练、配对、新采集、提交或推送。父维护PROGRESS与全局SOURCES。

工作树 `/home/ybc/projects/CL-FoReM-task10`，分支 `codex/task10-upper-wm`，起始HEAD `7b705c1a802aee0e53fb0bb1025ed7232f2dc4a0`。测试使用父创建的 `forem-task10-exec`，`/workspace` 为工作树forem可写挂载，`/reference/results` 主仓产物只读。torch `2.7.1+cu128`；本次网络、样本、优化器均CPU。测试命令明确设置 `OMP_NUM_THREADS=1/MKL_NUM_THREADS=1`，仅限制本测试进程，不是性能选型或固定工程参数。

## 实际交付

- `attempt_reward`：尝试子步×0.05 s形成dt，`g=.99^(dt/.1)`；基础奖励为首次严格成功终局事件，终局下一势函数归零，任务内终止/截断bootstrap_mask=0。中间势函数采用进展/总弧长。拒绝负dt及无效路线长度；Core.begin零尝试inplace停滞保留dt=0、g=1，不虚增时钟；提交时间不参与此奖励。对应父B定义。
- `Stage1Learner`：复用UpperModel stage1和DiscreteSAC的参数路由、温度、调度、裁剪10、tau .001。原始结束标志保留，独立bootstrap_mask进入Bellman；critic只使用gather出的所选Q，actor仍按有效槽期望。包装函数 `bellman` 用显式mask提供手算核验。
- `EpisodeReplay`：每个真实决策均可成为采样起点；Fragment有完整同回合prefix、最多4步burn-in、最多8步真实loss steps；短回合和首段参与loss。采样不拼回合、不填虚假loss位置。默认容量100000，容量淘汰整回合而非丢弃初态历史；单回合超过容量报错。终局后相同key不可继续写。回放保持CPU精确字段/uint8栅格，不缓存latent。
- `sequence_outputs/update_sequences`：变长批次使用稳定fragment ID，完整无梯度重建同回合历史，对真实loss步反向传播；临时next-state递归后恢复当前历史，online/target各自独立递归。更新前后保留runner原有VCM运行状态。`loss_transitions`报告实际loss位置数；profile可记录采样与adapter搬运时间。
- 恢复：兼容既有 `task7_upper.stages.save_checkpoint/load_checkpoint`，包含新回放格式/RNG与学习器更新数；仅学习器检查点不伪称环境可中途恢复。

完整API及输入输出见本节点 [PROCEDURE](PROCEDURE.md#实际实现接口与验收顺序)。

## 实际命令与结果

1. 测试先写。初次 `sg docker -c 'docker exec -e PYTHONPATH=/workspace/src forem-task10-exec python3 -m pytest -q /workspace/src/task10/tests/test_learning.py'`，退出码2；因为尚无 `task10.learning` 导入失败，确认新增模块未实现。此为缺失模块的RED，未声称已得到断言级RED。另有pytest cache无写权限警告，后续禁用cache provider，不改工作树权限。
2. 实现后执行 `sg docker -c 'docker exec -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=1 -e MKL_NUM_THREADS=1 forem-task10-exec python3 -m pytest -q -p no:cacheprovider /workspace/src/task10/tests/test_learning.py'`，退出码0，**12 passed in 3.19s**。
3. 增补变长回合身份/无padding与错误mask/dt不改参数后执行：

```bash
sg docker -c 'docker exec -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=1 -e MKL_NUM_THREADS=1 forem-task10-exec python3 -m pytest -q -p no:cacheprovider /workspace/src/task10/tests/test_learning.py /workspace/src/task7_upper/tests'
```

退出码0，**83 passed, 2 skipped in 13.22s**；本次本节点14项，其余为原task7_upper回归。2项为未设置 `TASK722_GPU=1` 的既有GPU专用测试，本次未申请GPU测试。覆盖：单有效槽手算target；零提交但尝试dt>0；严格成功、普通任务终止、任务截断；塑形项整回合折扣求和；1步回合与前四步loss；完整前缀重建；跨回合身份与变长批无padding；只有selected Q有critic梯度；stage1可训练分支变动、冻结分支不变；非合法mask/dt无参数更新；恢复Python/NumPy/torch RNG、下一采样、更新次数、下一更新指标和全部模型参数逐项一致。
4. `git diff --check` 退出码0。独占新源码为untracked，尚未提交；父需在交付前纳入其审查/版本管理。未运行全仓所有任务测试；本次范围为确定性task10.2与其复用的task7_upper回归。

## 限制、剩余与交接

父负责人需独立重跑，核查真实env提供的是复位前next_observation/candidates及非空mask，使用尝试数而非提交数，严格成功事件只记一次。下一步由父把本模块接入runner并按父C预算启动，不由本子任务自行采集。尚无真实闭环、GPU梯度/设备、冻结下层前后hash或端到端性能实测；本测试通过不支持任务表现或正式训练可行性结论。默认容量下仅覆盖父单回合≤150次决策合同；多环境活跃回合容量管理不在本子任务验收范围。

## 待父登记的来源条目草稿

建议来源ID由父分配；本节点不修改共享SOURCES。以下系项目源码/确定性夹具证据，不能登记成外部研究支持或真实任务实验：

- 支撑主张：独立bootstrap_mask、短回合/首段loss、完整同回合历史重建、所选Q标签、CPU完整恢复满足父B/C学习合同。
- 类型：项目源码静态核查与CPU确定性测试；方法/参数来自已登记[SRC-T10-001](../../../SOURCES.md#src-t10-001)的工程选择，无新参数或新算法授权。
- 作者/标题/年份：Codex learning_contract，task10.2 learning contract，2026-11-02。
- 本地路径：`forem/src/task10/learning.py`（符号 `attempt_reward/bellman/Stage1Learner/EpisodeReplay/sequence_outputs/update_sequences`）；`forem/src/task10/tests/test_learning.py`（全部15项）；本RESULTS实际命令与退出码；独立日志 `forem/doc/agent_logs/task10/task10.2/20261102-codex-contract.md`。
- 版本：起始HEAD `7b705c1a802aee0e53fb0bb1025ed7232f2dc4a0` 加工作树新增文件；父提交后补最终commit及文件hash。运行标识 `task10.2-cpu-contract-20261102`，无训练run。
- 精确位置：前述函数及测试函数名；全套命令在本RESULTS“实际命令与结果”第3项。
- 核查日期/人：2026-11-02，Codex子Agent learning_contract，实际派发gpt-6.1-sol/high。
- 原始结果：最终84 passed、2既有GPU专用skipped、退出码0、13.08 s；15项为本节点测试。初次缺失模块退出码2记录保留。
- 采用与限制：只支持学习合同确定性核查；不代表真实观测/B3、GPU、成功率、性能或任意环境中途恢复通过；父需独立复核并补全外部集成证据。


## 2026-11-02 15:23 +08:00 · 父环境审计修正零尝试合同

父核实 `Core.begin` 对无进展inplace可立即结束段，零尝试仍计真实决策与stall。因此不应强制dt>0。新增 `test_zero_attempt_stall_preserves_clock_and_terminal_does_not_bootstrap` 后先运行单测：退出码1、1 failed/14 deselected，明确在 `attempt_reward(...,attempted_steps=0)` 被旧正数校验拒绝；随后仅将尝试数与dt校验改为非负，并让回放接受dt=0。零尝试继续状态奖励0、g=1；终局势函数归零且bootstrap_mask=0，不伪造0.05秒。负数仍拒绝。

复跑第3项同一完整命令，**84 passed, 2 skipped in 13.08s / rc0**（本节点15项＋原task7_upper回归），并 `git diff --check`、`python3 -m py_compile forem/src/task10/learning.py forem/src/task10/tests/test_learning.py` 均rc0。此前83项是修正前历史结果。`update_sequences` 返回值包含 `updated`（true/false）；成功路径其余loss/alpha/norm为float、updates/loss_transitions为int，profile的timing只含float秒与int调用次数，可直接JSON记录，无tensor。来源草稿的最终计数以上述84/15为准。

父统一登记来源：[SRC-T10-004](../../../SOURCES.md#src-t10-004)。父集成复跑与签收以父RESULTS后续记录为准。

2026-11-02父签收：done（本节点确定性实现/审查交付）；父最终组合120passed/2既有条件skipped/rc0，唯一试训16/0及配对0/4对3/4按[父RESULTS](../RESULTS.md)如实保留。正式门NOT_READY，未将子自报作为总通过。最终证据见[SRC-T10-009](../../../SOURCES.md#src-t10-009)。
