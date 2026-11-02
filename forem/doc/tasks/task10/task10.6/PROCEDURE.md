# task10.6 流程

递归规则：当前无子节点；拆分稳定继承编号，每层恰有TASK/PROCEDURE/RESULTS，登记依赖/顺序/负责人/父验收。

执行者可按难度选模与强度、独立执行或自行委派；再派前建档，所有Agent共父授权/预算/截止。
1. 先读TASK与父审核，核实旧证据；先写确定性失败夹具再实现必要修复。
2. 仅在独占文件处理；新有界测量先声明输入、最大样本数及墙钟，父统一GPU启动。CPU小夹具与静态检查可自行执行，禁止新采集/长训/重启旧run。
3. 记录命令/退出码/模型/原始证据/限制，交父复跑与签收。

推荐GPT6.1sol/high、Sonnet5.5/high；跨模块计时/恢复一致性需高强度。实际派发gpt-6.1-sol/high。沿用默认模型。

## 已交API与父测量入口

`task10.recovery.verify_learner_checkpoint(path, learner, replay, config, counters, learner_factory=None, next_update=None)`：保存完整learner/replay；用`min(32,len(replay))`验证非空下一样本的episode key/start/实际来源身份，并比对Python/NumPy/CPU/CUDA RNG、全部learner/optimizer/target/scheduler/temperature/counters。空池明确`not_verified`。验证finally恢复调用方replay与global RNG；只有已更新optimizer才能验next_update。正式`update_sequences`的batch32/1000预热不改。

`save_episode_boundary(path, learner, replay, *, environment, policy_generator, budget, config, counters, journal_paths)`：要求全batch自然终局、prepare_next完成、最后transition已入replay且相同run/env/episode/decision identity有durable journal、ledger reserved=completed且in_flight=0。保存各purpose RNG、run/episode IDs、全局counter（调用方若有epoch counter也原样保留）、policy generator、replay/learner、sampler累计统计、sensor totals、pool/constructor来源、journal/ledger哈希。环境无现成epoch计数，不伪造额外epoch。

`load_episode_boundary(path, learner, replay, *, environment_factory, config, test_only_allow_same_pid=False)`：fresh构造（不能已reset），取得flock后才核验ledger/journal/PID/原deadline；任何异常close锁。默认拒绝same PID、旧collector PID仍存活/不同boot/更改ledger或journal/并发恢复；CPU同进程合成fixture必须显式test_only_allow_same_pid=True。使用原monotonic deadline，不重置预算。重建下一episode，episode_count=旧+1、totals累加；返回dict含counters/environment/policy_generator/budget/histories。无环境pickle，绕开继承层`__setstate__`禁止恢复。仅同一namespace原账本续计；调用方独占原collector，不能同时运行旧对象。重启系统跨boot恢复明确不支持。

父GPU fixture（尚未执行，必须由父统一ledger/超时包装启动）：
```bash
python3 -u /workspace/scripts/task10_recovery_probe.py --source /workspace/results/task10/t10-smoke-20261102-s101/offline-learner.pt --output /workspace/results/task10/NEW-fixture --fixture-updates 1
```
旧16真实回放身份核对后，把整回合复制为明确`derived-replay-copy`夹具达到32anchors；保存来源episode/link/decision/copy_index且counts_as_real_decision=false。直接调用底层sequence_outputs/loss，不伪造1000预热或增加真实decisions。默认1预更新+2下一更新分支共3次update，上限8、父外层300s含imports；与正式在线训练严格分开。

父有界在线边界入口（尚未执行）：上述命令改新output并加`--online-boundary --online-decisions 4`，父外层360s含imports。batch1/最多4新真实决策/0更新；默认orchestrator串行启动两个子进程，共第一进程启动前记录的原monotonic started+360 deadline。save子进程自然终局commit/save后做control reset，把下一场景/观测/候选/episodeID/RNG/generator/selected存expected-reference.pt，旧collector退出（不再flush已绑定ledger）；new PID resume子进程fresh重建并逐项对照，提交1个恢复后真实决策后释放锁，再读旧snapshot须ledgerchanged拒绝，不追加交互。预算内未自然终局输出not_verified，终局耗尽真实决策预算则仅boundary_verified_no_post_resume_budget，不强制截断。显式`--resume PATH/natural-boundary.pt`可同目录续原账本，已变化账本拒绝旧snapshot。不得指向旧failed16run输出。

恢复依据与本轮证据预留[SRC-T10-013](../../../SOURCES.md#src-t10-013)（父待实测后统一登记；当前CPU已测、GPU及在线待测）。

诊断扩展：首GPU fixture失败时，不再做初始更新；父原phase deadline内用`--diagnose-checkpoint /workspace/results/task10/t10-cost-recovery-20261102/recovery-fixture/derived-fixture.pt`与新的`--output`，其余`--source`仍指旧真实16。每次恰2个next-update分支，输出`diagnosis.json`中逐叶精确差异；无deterministic/有deterministic各最多一次，总首attempt3+2+2=7≤8。后者进程启动前设置`CUBLAS_WORKSPACE_CONFIG=:4096:8`并加`--deterministic`；不得改变原300s绝对deadline或放宽相等容差。GPU首失败及诊断原始证据仍挂[SRC-T10-013](../../../SOURCES.md#src-t10-013)，父统一登记。
