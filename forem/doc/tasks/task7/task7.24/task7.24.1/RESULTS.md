# task7.24.1 — 实现与针对性验证结果

**2026-10-26执行冻结：paused。** 用户已冻结task7全部后续执行，见[父冻结入口](../../TASK.md#2026-10-26-当前冻结入口)。已完成成果与下文历史状态保留；不得依旧授权自动续训、恢复或派发。当前转入task8地图迁移规划。

状态：review，2026-10-23T15:18:49.910040+08:00。交付源码/测试与下一阶段命令；等待独立监督，不代表P2/P3已经放行。实际Agent按派发为Codex gpt-6.1-sol/medium，未再派Agent、未提交Git。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（跨模块采样/随机流/预算）；科学合同监督high。[授权SRC-0971](../../../../SOURCES.md#src-0971)，本次证据拟登记SRC-0972，条目见文末待父维护全局SOURCES。

## 已完成与边界

仅改隔离工作树`/home/ybc/.codex/worktrees/task7-24-short-task/CL-FoReM/forem`下9文件，运行镜像同步后哈希逐一一致。冻结清单`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/implementation-manifest.json`，可审查patch`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/implementation-diff.patch`。不是相对旧Git HEAD审查；相对147文件dirty-main快照。全部147个原主工作树文件与基线哈希仍相同；Core/geometry/kinematics/candidates/SAC math均未改。

- EpisodeSampler新增可关闭的最终route.length闭区间过滤，默认None逐输出/RNG/原统计键与冻结原版一致。过滤在原完整合法性与碰撞/IK见证之后；记录各map/difficulty提案、接受、拒绝和accepted长度。sampling_deadline为每次sample的相对秒数，不保存绝对过期时刻；超时抛错，不替换固定地图。
- EpisodeEnv和训练只透传可选参数；保持v5同步多段训练、cbl_continue与episode_end_bootstrap。共用初始SAC文件与随机状态，初始文件sha验证，完整checkpoint配置严格恢复校验；trial identity/代码哈希写完整配置、actor与meta。初始actor也带同一identity。
- 复用既有train末尾final.pt+final.actor.pt+final.meta.json，不重复实现保存。实际基线位置`source-baseline/src/task7_lower/training.py::train`末尾已存在该行为。补pending更新循环软墙钟检查，硬上限仍由容器timeout控制。
- 固定案例生成器覆盖原100验证map×原/短两分布，固定14718的逐图stream与候选选择。完整env快照包含初态、route、扫描/grid/历史和candidate，之后每个actor按同一E=1顺序加载；只执行首段，未调用G7/D10，无replay接口。输入文件sha核验；重复/缺图清单拒绝。记录pose到达、route_end、route_end_first、old_arrival、失败、超时、原地/零时长、真实动作/尝试/提交计数、位移；reason1可同时pose到达。
- 宿主单worker预算保护先于首条容器计算建立：GPU3每次重查空闲、flock互斥、预占剩余预算、容器内timeout TERM/KILL进程组。当前保护还要求容器supervisor持久完成标记，客户端退出本身不能退款。预算所有测试/失败重跑均登记。

改动文件与sha：

|相对隔离forem路径|SHA256|
|---|---|
|`config/task7/short_task_trial.json`|`ee4513ad70f686e485944879b90924043a91ff91ae4e7f12fca2fe21c13522e1`|
|`scripts/task7_short_task_budget.py`|`5f11f2f63683bbc0d3246273921bbf5a25c87b7b14345cd9f30d3255e8b5cbd3`|
|`scripts/task7_short_task_trial.py`|`95603d1369c3f76a9b11f6e58af48403f4a1dd5f49edc29b79ed12f77bba5b40`|
|`src/task7_lower/short_task_trial.py`|`02951490f40076dd9503faaca48c5a3e45624d0d890bda70fab96f1ad1f1fbcd`|
|`src/task7_lower/tests/test_short_task_trial.py`|`e167d90d4d7f197ff15046edd881e368069bf729ccd13827f18cdb09c1929686`|
|`src/task7_lower/training.py`|`e443d2b1eb82f1237e7bada74b8a5782891c40707b01741988e3f2be84847363`|
|`src/task7_sim/env.py`|`5b281e422f9348d3e2246171860ac66442a7e703e19954ef63c0566732d022d6`|
|`src/task7_sim/episode.py`|`900dfadccbcafd843598abc00917f448aa829267c44c4d9933baeb25f0fbe179`|
|`src/task7_sim/tests/test_short_task_sampling.py`|`15b33681ba78152bbcadac92a68285d3e90f8d442ae5ddb2f0e469c045b16308`|

## 实际验证

首轮基线3pass/9fail皆缺镜像ROOT/results中的已有fixture/map读取路径；未改断言或生产科学语义。父确认后只为具体`results/task7/maps`与`t7.14-r2-20261021-0000`建立到既有产物的读取用途链接，未写目标。补路径后基线12pass。

采样RED9fail（接口缺失）→GREEN15pass（含原episode6项）。trial RED5fail→修正测试fixture自身序列化与stats完整性后，再验证meta缺失RED；元数据补齐后12pass。最终focused29pass（56.72s），涵盖真实CUDA采样/见证/default baseline parity、固定输入/RNG/零时间/分类、fullcheckpoint、exact cap与恢复、mask；非全仓库回归。exactcap测试用真实Core/几何/渲染、E2受控reset夹具、259→261转移，259时updates2、policy/replay/Adam moments在逻辑cuda:0（物理GPU3），Adam CPU计数合法保留；不是50k实际运行。后续初始actor身份与runner变更只重跑受影响用例，final-runner-identity 5pass（9.14s），不重复29项全组。所有失败原因见原始日志/下表，未隐藏失败。

预算超时实测：timeout-cleanup-final退出124，5.124s；容器完成标记也记rc124。final-cli-cleanup再次查OWNED_PIDS_FINAL对应进程状态非运行（absent/Z），并执行driver --help。lost-client RED→GREEN的两种情形：Python异常、客户端提前返回125；均无容器完成标记，保持全额30秒预占并阻止再发（隔离测试账本，不污染真实总账）。

|label|rc|wall秒|日志|
|---|---|---|---|
|baseline|1|2.784|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/baseline.log`|
|baseline-fixtures|0|13.900|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/baseline-fixtures.log`|
|sampling-red|1|2.153|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/sampling-red.log`|
|sampling-green|0|8.679|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/sampling-green.log`|
|trial-red|1|2.105|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/trial-red.log`|
|trial-green|1|15.953|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/trial-green.log`|
|trial-meta-red|1|8.482|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/trial-meta-red.log`|
|trial-meta-red-fixed-fixture|1|10.341|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/trial-meta-red-fixed-fixture.log`|
|trial-meta-green|0|19.728|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/trial-meta-green.log`|
|manifest-red|1|2.087|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/manifest-red.log`|
|final-focused|0|57.762|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/final-focused.log`|
|initial-actor-identity-red|1|4.674|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/initial-actor-identity-red.log`|
|initial-identity-final|0|9.044|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/initial-identity-final.log`|
|timeout-cleanup|124|5.092|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/timeout-cleanup.log`|
|lost-client-red|1|2.276|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/lost-client-red.log`|
|lost-client-green|0|2.081|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/lost-client-green.log`|
|cli-and-cleanup|0|1.857|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/cli-and-cleanup.log`|
|lost-client-exit-red|1|2.162|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/lost-client-exit-red.log`|
|lost-client-exit-green|0|2.145|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/lost-client-exit-green.log`|
|final-runner-identity|0|10.153|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/final-runner-identity.log`|
|timeout-cleanup-final|124|5.124|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/timeout-cleanup-final.log`|
|final-cli-cleanup|0|1.890|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/final-cli-cleanup.log`|

## 预算与恢复

本阶段累计实际容器计算 **190.473s /14400s**，剩余 **14209.527s**；真实`budget.json.active_jobs=[]`。每条command/start/end/rc/wall、预占、GPU3及新版容器完成标记都在`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/budget.json`。首版bootstrap支持无额外容器前置步骤；后续修正lost-client时补了真实失效测试与完成证据。

若宿主失联或supervisor完成标记缺失：保留整项reserved_seconds的计费与active_jobs，后续launcher拒绝启动。先等待该reservation的容器内timeout完成，再核只属于本task的进程/完成标记；仅有匹配job token且rc>=0的标记才证明内层timeout已回收。未确认时不清active或退款，不仅凭docker客户端消失恢复。需要人工恢复必须父登记核查证据，不提供自动冒险解锁。正常停止训练先在对应`original/STOP`或`short/STOP`放STOP，由原train保存interrupted；恢复必须显式--resume完整CP，原interaction ledger禁止重复回放。软墙钟保留65秒（外层cap总预留75）给持久化是待P2实测的工程选择，不保证50k大CP已验证。

## 尚未执行、风险及下一步

尚未执行：200个正式固定案例生成、E256有界1024转移计时、50k A/B、初始化/终点正式比较；无训练效果或4h可行性结论。E1逐案例推理是显存/同形状可比性的保守工程选择，性能待P2测；不同时驻留100快照。正式案例生成若某图采样超时即失败保留generation-progress，不换图；当前生成器不自动恢复半轮，必须由父在预算内裁定后续。默认合法提案后长度筛选可能昂贵、改变接受图分布，须公开stats，不暗优化科学条件。

监督先对冻结patch+manifest做read-only审查；如要求修改先登记并仅重跑受影响检查。通过后task7.24.3按下列命令做P2，利用reset/candidates/environment_step/inference/replay_sample/sac_update/IO/checkpoint实际Timings、GPU/optimizer设备及峰值、cases/eval wall，估算两组50k和三次共同评估是否在余预算内；无足够成本证据不运行P3。预检独立目录不会作为正式训练的replay/初态。下面600/1800/4400等仅为拟议操作超时上限、非承诺工期（全部合计13720秒，实际仍受剩余14400约束），监督/父依据P2可在总预算内缩紧分配，不变50000科学目标。

```bash
WORK=/home/ybc/.codex/worktrees/task7-24-short-task/CL-FoReM/forem
RUN=/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023
LOG=/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24
# All commands below are NOT EXECUTED; independent review/P2 gate first.
python3 "$WORK/scripts/task7_short_task_budget.py" --budget "$RUN/budget.json" --seconds 120 --label initialize --log "$LOG/initialize.log" -- python3 -u scripts/task7_short_task_trial.py --protocol config/task7/short_task_trial.json --output /root/mm_husky_ws/results/task7/t7.24-short-20261023 --phase initialize
python3 "$WORK/scripts/task7_short_task_budget.py" --budget "$RUN/budget.json" --seconds 600 --label preflight-original --log "$LOG/preflight-original.log" -- python3 -u scripts/task7_short_task_trial.py --protocol config/task7/short_task_trial.json --output /root/mm_husky_ws/results/task7/t7.24-short-20261023 --phase preflight --distribution original
python3 "$WORK/scripts/task7_short_task_budget.py" --budget "$RUN/budget.json" --seconds 600 --label preflight-short --log "$LOG/preflight-short.log" -- python3 -u scripts/task7_short_task_trial.py --protocol config/task7/short_task_trial.json --output /root/mm_husky_ws/results/task7/t7.24-short-20261023 --phase preflight --distribution short
python3 "$WORK/scripts/task7_short_task_budget.py" --budget "$RUN/budget.json" --seconds 1800 --label fixed-cases --log "$LOG/fixed-cases.log" -- python3 -u scripts/task7_short_task_trial.py --protocol config/task7/short_task_trial.json --output /root/mm_husky_ws/results/task7/t7.24-short-20261023 --phase cases
python3 "$WORK/scripts/task7_short_task_budget.py" --budget "$RUN/budget.json" --seconds 600 --label eval-initial --log "$LOG/eval-initial.log" -- python3 -u scripts/task7_short_task_trial.py --protocol config/task7/short_task_trial.json --output /root/mm_husky_ws/results/task7/t7.24-short-20261023 --phase evaluate --actor initial
# Only after P2 cost gate; these each still target50000, with original LR schedule.
python3 "$WORK/scripts/task7_short_task_budget.py" --budget "$RUN/budget.json" --seconds 4400 --label train-original --log "$LOG/train-original.log" -- python3 -u scripts/task7_short_task_trial.py --protocol config/task7/short_task_trial.json --output /root/mm_husky_ws/results/task7/t7.24-short-20261023 --phase train --distribution original
python3 "$WORK/scripts/task7_short_task_budget.py" --budget "$RUN/budget.json" --seconds 600 --label eval-original --log "$LOG/eval-original.log" -- python3 -u scripts/task7_short_task_trial.py --protocol config/task7/short_task_trial.json --output /root/mm_husky_ws/results/task7/t7.24-short-20261023 --phase evaluate --actor original
python3 "$WORK/scripts/task7_short_task_budget.py" --budget "$RUN/budget.json" --seconds 4400 --label train-short --log "$LOG/train-short.log" -- python3 -u scripts/task7_short_task_trial.py --protocol config/task7/short_task_trial.json --output /root/mm_husky_ws/results/task7/t7.24-short-20261023 --phase train --distribution short
python3 "$WORK/scripts/task7_short_task_budget.py" --budget "$RUN/budget.json" --seconds 600 --label eval-short --log "$LOG/eval-short.log" -- python3 -u scripts/task7_short_task_trial.py --protocol config/task7/short_task_trial.json --output /root/mm_husky_ws/results/task7/t7.24-short-20261023 --phase evaluate --actor short
```

## 交父登记的来源条目（拟SRC-0972，尚未写全局台账）

- 支撑主张：本任务隔离实现具有默认采样输出/RNG等价、最终路线弧长筛选/合法见证、固定首段快照与结束分类、共享初始化身份、受控259→261精确端点恢复，以及预算完成标记/失联保守计费的针对性测试证据；不能证明200正式案例、E256吞吐、50k学习效果或总4h可行性。
- 类型：项目代码与本次原始测试实测；操作timeout/采样秒数/评估E1/预检1024为工程选择、待P2成本验证；1–2m/每组50k/总4h沿用户授权SRC-0971。
- 作者/机构与标题：FoReM Codex，task7.24.1 isolated implementation and focused checks，2026-10-23；实际gpt-6.1-sol/medium。
- 原始证据位置：`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/implementation-manifest.json`（9改动sha、153文件冻结、main/mirror一致性）；`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/implementation-diff.patch`；`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24`下baseline-fixtures、sampling-red/green、trial-meta-red-fixed-fixture/green、final-focused、initial-actor-identity-red/initial-identity-final、lost-client-exit-red/green、final-runner-identity、timeout-cleanup-final/final-cli-cleanup；`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/budget.json`及budget-completions。run-id t7.24-short-20261023；无需假称Git commit含工作区源码。
- 精确位置：EpisodeSampler.sample/route_length_allowed/_count_group；short_task_trial.freeze_case/evaluate_cases/case_outcome/initial_weights/validate_case_manifest；training.train/save_checkpoint；task7_short_task_budget.run；各test_short_task_*.py具名行为测试与日志rc。
- 核查日期/人：2026-10-23 Codex gpt-6.1-sol/medium；独立监督尚未执行，不代填已复核。
- 原始结论与本项目采用：限于本报告实际测试范围。复用原v5几何、Core和SAC，新增已授权采样与试验外围；后续先审查再P2成本门禁，不能以此来源放行/宣称50k已完成。


# 监督round1 F1修复（2026-10-23T15:33:32.362327+08:00）

状态review；实际Codex gpt-6.1-sol/medium。已读receiving-code-review并核源码：预检/正式cfg原先相同，train在目标无账本时跳过safe_to_resume，确有跨目录加载缺口。仅落实父接受的F1，未扩大P2，不运行50k。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（跨phase/恢复状态因果）；独立监督仍high。[SRC-0972](../../../../SOURCES.md#src-0972)由父维护，本段为同来源补充证据。

## 最小修正

- `phase_training_config`在共享科学identity外增加operational `trial_run`，绑定phase(preflight/train)、distribution、run_root与规范化output；driver通过此唯一构造入口分别生成preflight-*与正式group配置。
- 带trial_identity的train在创建输出/加载checkpoint前必需有效trial_run；phase/group必须匹配目录位置与route_length_bounds。恢复CP的真实路径必须位于当前输出目录，本地interactions.jsonl必须存在且非空，meta的trial_run与trial_identity必须匹配；随后仍由原safe_to_resume核动作覆盖及完整stored config一致性。完整CP/actor/meta均保留trial_run，不改变Core/SAC或采样科学条件。
- 拒绝preflight→train、错误group/output、复制预检CP到正式目录、缺失/空本地账本；保留preflight/train两phase同目录合法恢复，以及既有259→261精确计数与SAC更新覆盖。普通非本trial的训练接口不加新约束。

## RED/GREEN证据

第一次r1-resume-red：3fail/4pass，含既有empty-ledger错误文本未匹配；修正测试接受原budget-safe错误文本，并让跨目录场景沿原同cfg调用，重现原问题。r1-resume-red-reproducer：**5fail/2pass**，实际跨preflight→train、wrong_group、wrong_output、missing_ledger未被拒绝，另phase配置构造接口缺失；copied-preflight与empty-ledger原来就被已有配置/账本检查拒绝，未冒称这些是新增发现。

修正后仅运行：

```text
python3 -m pytest -q src/task7_lower/tests/test_short_task_trial.py src/task7_lower/tests/test_recovery.py -k 'resume or fresh_groups or driver_phase or missing_or_uncovered' --basetemp /root/mm_husky_ws/results/task7/t7.24-short-20261023/unit-r1-green
```

通过预算launcher、物理GPU3、单worker执行，结果 **12 passed,7 deselected in55.03s，rc0**；未重跑无关focused29项。原recovery测试被-k明确纳入。测试仍使用受控E1/E2真实Core/几何/渲染夹具，不是正式分布训练/端到端成本证据。

|label|rc|实耗秒|日志|
|---|---|---|---|
|r1-resume-red|1|14.308|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/r1-resume-red.log`|
|r1-resume-red-reproducer|1|16.795|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/r1-resume-red-reproducer.log`|
|r1-resume-green|0|56.151|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/r1-resume-green.log`|


此次新增计算87.254s，累计 **277.728/14400s**，剩余 **14122.272s**；active_jobs=[]。原r1冻结快照/manifest未覆盖。r1→fix可审查差分`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/implementation-r1-fix.patch`；新冻结`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/implementation-manifest-r1-fix.json`，当前`implementation-manifest.json`和相对初始dirty-main的`implementation-diff.patch`已同步更新。

本轮仅4个文件有差异：

|路径|修正后sha256|
|---|---|
|`scripts/task7_short_task_trial.py`|`bbf5f80441924ba4bb6e3813c734fbb3f6c3f99d48c39c0d7ef70cfdfe153676`|
|`src/task7_lower/short_task_trial.py`|`e52946691b603baa35de7b7b24aa78e799fe4af2bbd8393c59b5017e9997cdd3`|
|`src/task7_lower/tests/test_short_task_trial.py`|`66729b99807f4b5f43a580726d61aa9378c92d1ca7b03fda7dc4394a6ee20235`|
|`src/task7_lower/training.py`|`e3eb9864fd27eb6f044083693d89eda91c9d94f58d84c7302f7fb32577e842fa`|


运行镜像全部153文件与当前隔离工作树一致；原主树147基线文件仍全部一致。未改共享SOURCES/PROGRESS或父ledger。请父将以上测试、代码位置`phase_training_config/validate_trial_run/validate_trial_resume`、四文件hash与patch追加SRC-0972，并进入复核round2。

下一步仍由独立监督放行后做P2。后续reset分布与50k真实replay持久化成本由运行阶段在同4h预算内测量，本轮没有自行增大预检转移或新加实验；先前报告中的P2/50k命令均尚未执行。因新phase/output身份，旧r1的试验配置/CP不视为可跨phase复用；当前只存在单元夹具，正式initial/preflight/train尚未启动。


# 监督round2 F1补充：等计数错账本（2026-10-23T15:41:31.646113+08:00）

状态review；实际Codex gpt-6.1-sol/medium。授权仅补原F1账本归属场景，未扩展功能或P2规模。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（归属与恢复计数跨模块核对），独立监督high。来源补充交父追加[SRC-0972](../../../../SOURCES.md#src-0972)。

前轮只校验本地ledger路径/非空、CP.meta身份及尾部计数，未校验账本自身归属。本轮新增精确测试：在两个真实受控fixture run各产生1个环境动作；保留目标`final.pt`与`final.meta.json`原字节，**只把interactions.jsonl替换为另一phase/group/run的完整账本**。三种外来账本的尾记录均明确为event=step_complete、action_calls=1、env_actions=1、steps=0，原safe_to_resume计数检查仍True。旧实现实际3fail（DID NOT RAISE，14.54s），不是因CP/meta或计数不同而拒绝。

最小修正：只对本trial fresh ledger第一行写入并fsync `trial_header`（format task7-short-interactions-v1、trial_identity、完整trial_run），先于环境交互；已有ledger不得被fresh-run追加新header覆盖归属。恢复的validate_trial_resume在原计数检查之前读取首行，核header事件/格式/科学identity与phase-group-root-output归属；等计数也不能替代归属证明。CP/meta原检查仍保留，非trial通用recovery不改。此为防止意外错用整份账本的归属校验，未扩展为防恶意篡改机制。

定向GREEN命令（通过同一预算launcher、GPU3、单worker）：

```text
python3 -m pytest -q src/task7_lower/tests/test_short_task_trial.py src/task7_lower/tests/test_recovery.py -k 'resume or fresh_groups or driver_phase or missing_or_uncovered' --basetemp /root/mm_husky_ws/results/task7/t7.24-short-20261023/unit-r2-green
```

实际 **15 passed,7 deselected in62.02s，rc0**。涵盖三种“仅错账本但相同计数”的拒绝、合法同目录preflight/train恢复且header恰有1行、259→261精确计数、共享初始化/phase配置、前轮CP来源边界，以及原recovery动作覆盖。未重跑无关29项；没有P2/E256成本测量或50k结果。

|label|rc|wall秒|日志|
|---|---|---|---|
|r2-ledger-red|1|15.597|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/r2-ledger-red.log`|
|r2-ledger-green|0|63.111|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/r2-ledger-green.log`|


本轮计算78.709s，累计 **356.436/14400s**，剩余 **14043.564s**，active_jobs=[]。容器完成标记在同budget-completions中，所有命令原文/时间/rc仍由budget.json保存。

r2→fix差分：`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/implementation-r2-fix.patch`；新冻结：`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/implementation-manifest-r2-fix.json`。当前implementation-manifest.json与相对dirty-main的implementation-diff.patch同步更新。只改3文件：

|路径|修正后sha256|
|---|---|
|`src/task7_lower/short_task_trial.py`|`26f01f3dd2e827b8b017eeccfffec3434be328992e5882d0cfcdcf59785abe07`|
|`src/task7_lower/tests/test_short_task_trial.py`|`1ea8e083bcd3b2abe38e8cb190e966ad9d1742e2049bfe49b5a25d3572097ffc`|
|`src/task7_lower/training.py`|`998d882da262281726daf1312a653c65440b710b148f0cb85a9d470903bd46ca`|


全部153运行镜像文件与隔离源码哈希一致；原主树147基线文件仍全部一致，main_differences=[]。父冻结review-r2-source未改。请父将首行账本归属机制、test_trial_resume_rejects_only_ledger_swapped_at_equal_counts、RED/GREEN日志与上述hash追加SRC-0972后复核round3；未写共享SOURCES/PROGRESS。下一步仍是监督放行后由运行阶段在同预算内评估后续reset与50k replay持久化成本，本轮未增实验、未启动P2/50k。


# 监督round3 F2：合法零动作CP仅含header的恢复（2026-10-23T15:48:54.639357+08:00）

状态review；实际Codex gpt-6.1-sol/medium。父接受F1已全修，授权只补F2。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（恢复边界与动作预算因果），监督high。来源证据仍交父追加[SRC-0972](../../../../SOURCES.md#src-0972)。

问题复现：初始化reset完成后软墙钟/STOP可保存steps=env_actions=action_calls=0的完整interrupted.pt；此时账本只有round2新增trial_header，原safe_to_resume把header当未完成step_intent拒绝。另完整科学identity首行可能超过原8192-byte尾读窗口，仅看尾段也会解析失败。新RED验证短header、12000字符identity header、真实max_wall_s=0保存CP后的合法resume，实际 **3failed/5passed**（4.87s）；三个失败分别对应以上三个合法恢复分支，非计划推断。

最小修正仅`recovery.safe_to_resume`：确认账本**恰有一行**且为已知trial_header/format时，读取完整该行，只有meta中steps/env_actions/action_calls三者全部为0才视为无环境动作初态。多任何一字节后续记录都不走此兼容分支，继续原tail/intent/count检查；header身份仍先由原validate_trial_resume独立核验。非trial空账本零动作、正常step_complete和未覆盖intent等原分支未改。

覆盖：短/超8192-byte header零动作通过；单独任一计数为1均拒绝；header+pending step_intent且meta全0仍拒绝；header+正常complete与原无header/无动作恢复不回退。真实受控E1测试用max_wall_s=0产出完整interrupted.pt，核三计数为0、仅1行header；错误身份header仍被trial校验拒绝，恢复原header后正常采集恰1条，不重复header。合法preflight/train同目录已有恢复也通过。没有新实验系统或P2/50k运行。

定向GREEN（统一预算launcher/GPU3/单worker）：

```text
python3 -m pytest -q src/task7_lower/tests/test_recovery.py src/task7_lower/tests/test_short_task_trial.py -k 'missing_or_uncovered or header_only or header_plus_pending or header_normal or zero_action_trial or bound_trial_resume_accepts' --basetemp /root/mm_husky_ws/results/task7/t7.24-short-20261023/unit-r3-green
```

实际 **11passed/19deselected in10.24s，rc0**。未重跑无关29项、259更新长用例或P2。

|label|rc|wall秒|日志|
|---|---|---|---|
|r3-header-zero-red|1|5.832|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/r3-header-zero-red.log`|
|r3-header-zero-green|0|11.268|`/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24/r3-header-zero-green.log`|


本轮计算17.100s，累计 **373.537/14400s**，剩余 **14026.463s**，active_jobs=[]。r3→fix差分：`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/implementation-r3-fix.patch`；新冻结：`/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023/implementation-manifest-r3-fix.json`。current manifest与相对dirty-main差分也更新。相对r3只3文件：

|路径|修正后sha256|
|---|---|
|`src/task7_lower/recovery.py`|`4812099cdef21e5c7ef76a58e038f9fecb6e04e814225866fa41d3921f5d5cdf`|
|`src/task7_lower/tests/test_recovery.py`|`19ef7a8cf57e35ca5ac865bb72efd7193061d2e8324a4fcfdc03a7f1db442594`|
|`src/task7_lower/tests/test_short_task_trial.py`|`d434592d99023aa5c3af1e28a76eb766c0d788031f267e3bb0e08a31d9e5114f`|


当前累计相对原dirty-main有11修改/新增文件（原9文件加recovery.py及test_recovery.py），全部153隔离文件与运行镜像逐一一致；原主树147基线文件仍全部一致。review-r3-source未改。请父追加SRC-0972并复核round4；共同SOURCES/PROGRESS未由本子Agent修改。下一步仍依独立监督放行后由运行阶段检验reset与50k实际replay保存成本；本轮没有扩大预检或启动P2/50k。
