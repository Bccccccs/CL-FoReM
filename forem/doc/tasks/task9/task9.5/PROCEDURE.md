# task9.5 SAC优化 Implementation Plan

> For agentic workers: use superpowers:subagent-driven-development to execute the scoped steps. Root maintains shared evidence; no child delegates or edits shared documents.

**Goal:** 归档实际参数并在固定任务语义下执行U20/E15/R200三方向、两配对种子的有界训练。
**Architecture:** 独立源码快照/入口/配置/队列，不修改运行中的task7/task8文件。CPU和GPU验收通过后，待卡空闲，先smoke再将每个正式run首250k作为计入3M预算的profile门；科学limit始终3M，使用独立pause_after_consumed门保留完整pending批/cursor，随后同配置同RNG/回放恢复至3M。
**Tech Stack:** forem-dev、既有torch2.7.1+cu128与原语环境；宿主标准库调度、JSON账本/状态；无新依赖/ROS进程。
**Spec:** [TASK](TASK.md)；事实表[RESULTS](RESULTS.md)，授权/工程取值SRC-1336/1342。

## 递归规则声明

遵守根AGENTS：每层恰有TASK/PROCEDURE/RESULTS；本层以下task9.5.1/.2/.3各自三文档，独立日志按相同编号归属；父记录子结果、核验原件，不将子自报通过直接当验收。

## Global Constraints

- 观测、动作、环境奖励、终止、采样/子目标与评估协议不变；只允许TASK矩阵的SAC参数轴。
- 不修改旧task7/task8源码、19原配置或69冻结文件，不停止/重启任何既有进程；旧queue无待派且追加5M已启动，仍要每次核实。
- 新代码只在forem/src/task9_opt/；新入口/队列只用forem/scripts/task9_opt_*.py；新配置forem/config/task9/opt/；logs/results使用新run-id t9-opt-20261031。
- 旧运行源需复制到forem/src/task9_opt/frozen/（或等效独立导入根），冻结全部相关task7/task8包及sensor/robot配置，记录来源hash与真实import.__file__。不得只用PYTHONPATH却被旧入口sys.path覆盖。
- 2026-11-02T07:00:00+08:00优雅停止本任务训练；08:00汇总截止；新job预算须包含退出保存。旧任务不受新截止守护管理。
- 每卡最多一个训练；宿主、CUDA、输出目录、账户/账本、seed与run身份隔离；不复用旧输出或恢复旧3M/5M。
- 新run从头3M；每250k全196评估、每1000诊断；相同seed与B3配对；不缩预算/评估、不中途换参数，不按迁移选模。正式profile禁止传旧--transfers250000；科学limited_step剩余额始终按3M，恰消费250k并完成原定评估后受控暂停。
- 参数取值20/−1.5/200k为探索工程值，未声称最优；所有未执行步骤均标未执行。

## Review Focus

1. 新target_entropy字段真实进入SAC、metadata与恢复校验，配置出现但未生效必须失败。
2. 隔离导入/contract覆盖所有被改模块，原69 hash不变；snapshot包不得回落原源码。
3. 正式250k profile产生summary不等于3M完成；恢复同一run必须包含先前全部交互/墙钟与RNG，旧profile-summary/证据留存。
4. 多卡队列启动预检不能把已核实旧任务当自己的任务杀掉，绝对截止只停止新队列拥有的PID/输出。
5. 截止/预算需要计入等待、smoke、恢复、周期保存/评估和退出排空；外推超时不以缩3M或删失败样本解决。

## 子任务与顺序

|节点|依赖/职责|负责人|三文档|
|---|---|---|---|
|9.5.1|参数/设计/截止容量独立预审，只读代码|独立Codex GPT6.1sol/high|[TASK](task9.5.1/TASK.md) / [PROCEDURE](task9.5.1/PROCEDURE.md) / [RESULTS](task9.5.1/RESULTS.md)|
|9.5.2|预审后隔离实现/测试/队列与smoke/profile/训练执行|另一Codex GPT6.1sol/high|[TASK](task9.5.2/TASK.md) / [PROCEDURE](task9.5.2/PROCEDURE.md) / [RESULTS](task9.5.2/RESULTS.md)|
|9.5.3|.2代码交付后独立spec+quality验收/分阶段放行建议，最终训练结果核验|≠.2的Codex GPT6.1sol/high|[TASK](task9.5.3/TASK.md) / [PROCEDURE](task9.5.3/PROCEDURE.md) / [RESULTS](task9.5.3/RESULTS.md)|
|9.5.4|现有GPU/CPU/IO与完整run计时性能审计；只读并行，不干扰5M|Codex GPT6.1sol/medium|[TASK](task9.5.4/TASK.md) / [PROCEDURE](task9.5.4/PROCEDURE.md) / [RESULTS](task9.5.4/RESULTS.md)|

### Task 1: Archive and preflight (root +9.5.1)

Files: task9.5 RESULTS + logs/task9/t9-opt-design-20261031/parameter-inventory.json; .1 writes only own RESULTS/log and preflight report.
- [x] Read code/config/runtime/results; produce source-reviewed constants with full JSON/config/hash snapshot.
- [x] Independently verify key fields, exact update counts, default-equivalence prerequisites, scientific contract, deadline/parallelism feasibility. (SRC-1343; feasibility remains conditional.)
- [x] Resolve findings in parent spec/ledger before implementation; no experiment modifications from reviewers. (F1–F4 adopted.)

### Task 2: Isolated runtime and tests (9.5.2)

Files: create src/task9_opt/**, scripts/task9_opt_*.py, config/task9/opt/**; no edit old production modules. Tests owned under src/task9_opt/tests/.
Interfaces: consumes full frozen B3 config + one variant difference; produces frozen import root, config manifest, validation/restore/readiness evidence and scheduler executable.
- [x] Snapshot actual dirty dependencies, not HEAD alone; record origin hashes and artifact versions.
- [x] Add only optional target_entropy override in isolated SAC copy, default−3; use existing UTD/replay fields unchanged. Ensure runtime/full config documents effective algorithm constants.
- [x] Meaningful fail-first tests: E15 actually changes α gradient at fixed batch/RNG; invalid/nonfinite entropy rejected; U20 exact update_due/count; replay200k capacity/sampling/storage shape; default B0/B3 update/action/save+restore equal; no scientific contract drift. No optimizer step on active GPUs.
- [x] Default-equivalence CPU checks and nonaligned-vector split/resume test: pause_after_consumed does not change limited_step scientific budget; preserve pending.ids/cursor/transition, action/transfer ledgers, full RNG/replay/network/optimizer/target/α/LR and env/candidate state. Then dedicated GPU G1 on a verified free card≤1800s; deterministic settings test-only, production unchanged.
- [x] Generate six formal configs from exact B3 template; diff whitelist {group,seed,update_every_transfers or target_entropy or replay_capacity}; retain total_transfers3M and shared hashes/metadata.
- [x] Write manifest/report/review diff under new logs and report own RESULTS; no commit/push without root.

### Task 3: Scheduler, deadline and independent code release (9.5.2→9.5.3→root)

Files: scripts/task9_opt_queue.py, task9_opt_monitor.py (names may be equivalent), config matrix/manifest; logs/task9/t9-opt-20261031/.
- [x] Staged authorization: CPU/static code+quality review by .3 → root release-g1.json (hash-bound G1 only≤1800s) → actual G1 evidence review by .3/root → root release-training-policy.json (hash-bound smoke/profile, deterministic automatic per-group/per-run admission rules). A G1 token cannot authorize training. Autonomous validators execute only independently-reviewed policy; their machine checks remain execution checks, not final independent result acceptance. Background Python -u; no GPU test beforeG1 token, no smoke/profile beforetraining-policy token.
- [x] Disjoint output dirs and per-GPU lock; detect only truly free GPU with CUDA apps/docker top. Expected old PIDs are observers only; don't kill them.
- [x] Sequential groups' smoke per TASK: two seeds, 512→save→restore→1000→full196; each group≤4300 worker seconds, preserve scripts/params/checkpoint/ledger; fail no retry and quarantine affected group.
- [x] Each formalrun first250k is bounded profile within same3M budget; scientificlimit3M throughout. Use new --pause-after-consumed250000, not old--transfers. At the ordinary250k eval boundary save profile.pt plus profile-summary.json with full pending cursor and state/RNG; do not mark full run done. Phase2 resumes exact profile.pt with pause gate omitted. All already-produced env_actions beyond consumed250k remain charged/pending, never discarded/reexecuted. CUDA policy/replay/optimizer state, mature R200 memory, periodic checkpoint/eval/save/resume costs recorded.
- [x] Admission builds explicit per-GPU discrete schedule from observed old task releases (H now user-stop requested;5M protected), G1/smoke/profile phase reservations, measured group costs and save allowance. Check fullrun fits before starting profile, then re-evaluate after250k mature measurements before remaining2.75M.6runs is target not guarantee; if cannot finish before07:00 with safe save allowance, marknot_started_deadline/NOT_READY, never shrink3M or extenddeadline. At least two12h lanes would need firstwave beforeSun07:00 if sixrun plan uses two waves; do not infer that merely72workerh fits.
- [x] Absolute stop sets STOP only in new owned outputs early enough to save; track unresolved save at07:00 and report, no unverified global PID kill. Old runs untouched.
- [x] Parent gets prepare report + complete diff; .3 checks spec AND quality against evidence; parent checks hashes/processes and writes release if pass. Reviewer doesn't re-run identical tests unnecessarily.

### Task 4: Execute and hand off (9.5.2, root)

- [x] Start bounded autonomous orchestrator after .3 release, record host/container PIDs, logs, per-group ledgers and deadlines. Immediate waiting-on-GPU is not reported as training started.
- [x] Verify first actual process/diagnostic when slot frees, root records status. Start only branches that passed smoke; no retry after experimental failure.
- [x] Complete per-run3M or honest interrupted/diverged status; report final/last3 success, per-difficulty, all seeds, cost/resources, failed groups; external deadline monitor or queue's guard should persist after chat ends.
- [x] Independent final results review .3 after all new runs end; parent SOURCES/PROGRESS/RESULTS and experiment/paper cross-links updated.

## Budget and selection

G1≤1800s; smoke eachgroup≤4300s, total≤12900 worker s; newformalrun≤3M and within absolute deadline, normal onecard reference12h/run conditional. These are local authorized engineering bounds, not shared new project rules. Profile transfers count toward3M; smoke transfers/cost separately accounted. If total six cannot fit, deterministic priority U20→E15→R200, within each first4718 then4719, but avoid claiming group improvement from one seed. No extra groups/combination/seed or5M automatically spawned.

Monitor state must distinguish prepared, waiting_review, waiting_gpu, g1, smoke, profile250k, training, done/diverged/interrupted/not_started_deadline. Record worker wall separately from global elapsed. Stop methods refer exact own output STOP and queue PID; no blind docker restart.

## Model recommendations

Codex GPT6.1sol/high、Claude Sonnet5.5/high for implementation/review; monitoring medium. Parent actual unknown; child actual recorded per dispatch.

2026-11-02验收收尾：上述本轮实施/执行/最终审查已完成，依据[SRC-1351](../../../SOURCES.md#src-1351)、[SRC-1352](../../../SOURCES.md#src-1352)。绝对截止守护为已配置且路径经静态/mock审查，实际因全部提前结束未触发，不把该checkbox解释为已实测真实超时落盘。新方向无观察改善，未开展后续实验。
