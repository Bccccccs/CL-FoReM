# 正式四run＋final1184同冻结最小patch文本（仅草案，尚未应用）

当前授权：[SRC-1435](../../../../../SOURCES.md#src-1435)及父本轮明确派发“只在本子日志准备具体patch，不改active生产；LON完整闭合且全案预算通过后才应用”。当前LON生产仍182源`26308d91fd299ff55d2cdc84b21172210e5df59826aa870aaafb7bd93d87dd0d`，未修改其任何源文件；没有模型/GPU/环境实验，没有创建正式namespace、没有正式/最终令。本草案不是已实现或可启动入口。

推荐GPT6.1sol/high、Sonnet5.5/high：固定源码合同、完整恢复/RNG、阶段DAG与累计资源因果；实际平台型号/强度未独立核实。涉及的固定参数/顺序/验收沿task9.11原协议[SRC-1387–1390](../../../../../SOURCES.md#src-1387)、当前授权SRC-1435；当前G1真实通过仅[SRC-1441](../../../../../SOURCES.md#src-1441)。以下精确代码位置为本项目只读审计/推导，来源登记由父同步，不是新实验结果。

## 应用的两个硬前提

1. 独立LON完整验收：196/科学dict/OFF–ON parity、实际恢复设备、完整root/owner/guardian/watcher/client退出、exactStopped与费用。旧C完整门FAIL永留；其有限科学承接只绑定独立组合验收原件，不能将旧活动改PASS。
2. 独立全案可行性PASS：原T0/2026-11-07 03:18:20+08/各58h/2TiB/8GiB不变；全部已发生费用、正式4×3M/9408周期评估、额外profile保存及两次完整恢复、最终1184与所有控制/发布/独审尾都容纳。若缺证或不容纳，本草案不应用，报告具体证据/资源缺口，不先跑正式250k试运气。

## 一次冻结的文件边界

必要源仅改`real_batch.py`模块/CLI、`real_g1.py`通用真实链、`admission.py`真实分支、`real_receipts.py`实际phase白名单、`worker.py`资源/最终证据路由；新增`real_program.py`和专用stdlib测试。保151科学/config/runtime/诊断字节，既过F1/F2/GPU两账/SRC1423不重做。正式first-profile前必须把最终manifest读取、held-out任务检查、四final哈希冻结与final worker实际路由一并实现/独审/冻结。之后**任何artifact_files纳入的源码、科学配置、测试文件均不得改/增**；否则full checkpoint内source_contract失配，不能用LON的旧合同桥为正式救场。全部后续stage令、预算快照、final manifest/model bundle放doc/agent_logs或结果目录，不能后来新增到`config/task9/task9_11/`或src/tests导致source漂移。

下文是集中实现时逐项应产生的最小diff合同；代码片段定义确切接口/分支与拒绝行为，不将未写出的通用调度壳当已经实现。无需新增科学算法或改变train/evaluate。

## 1. 固定program stage解析与额度

新增`src/task9_lr/real_program.py`，stage表代码固定如下；不把active stage写入/修改已封protocol：

```diff
+++ src/task9_lr/real_program.py
+ORDER = (('C',4718), ('L',4718), ('C',4719), ('L',4719))
+ADAPTER = 'REAL_FORMAL_FINAL_ONLY_V1'
+
+def stages():
+    result = []
+    previous = None  # first profile separately requires completed LON/limited-C/full feasibility
+    for arm, seed in ORDER:
+        for phase, transfers, episodes in (('profile',250000,196),
+                                           ('remaining',2750000,2156)):
+            name = f'{phase}-{arm}-{seed}'
+            result.append(dict(name=name, phase=phase, arm=arm, seed=seed,
+                               transfers=transfers, evaluation_episodes=episodes,
+                               previous=previous, folder=f'formal-{arm}-seed{seed}'))
+            previous = name
+    for arm, seed in ORDER:
+        name = f'final-test-{arm}-{seed}'
+        result.append(dict(name=name, phase='final-test', arm=arm, seed=seed,
+                           transfers=0, evaluation_episodes=296,
+                           previous=previous, folder=f'test-{arm}-seed{seed}'))
+        previous = name
+    return result
+
+def stage(protocol, phase, arm, seed):
+    # require exact program marker and exactly one match in immutable fixed list;
+    # all G1/smoke/C-ON/L-ON or different seeds/arms are refused here.
+    ...
```

这一张表算术必须定点核：8训练stage共12,000,000；每run 250,000+2,750,000=3,000,000，12×196=2352周期评估；4run共9408；4final×296=1184。profile的196就是该run普通250k周期评估，不再预热/重开；remaining从profile.pt后继续另11×196，不重评250k。

`real_batch.build(..., program_refs=...)`新增program marker分支，仍保原baseline/历史input/科学4配置/原T0/58h/日历/字节限及旧C FAIL。program_refs只接受实际独立LON完整裁决、限定C承接、全案预算PASS，原件路径/哈希及status精确核。原consumed980保为历史账事实；另program entry admission固定扣已完成LON196，实际已消费总1176，留后续新量10592=9408+1184，不把LON196再留一次预算。新source/新protocol/新正式namespace一并封，不复用已消费LON身份。

## 2. 真实链显式接stage，不改protocol

`real_g1.py`当前单门`b.stage(p)`硬编码，应集中变为`resolve_stage(p, phase, arm, seed)`：G1/LON旧路由保各自单门，program只按上表。`release`、`source_review`、`checked_budget`、`resources`、`spec_gate`、`inner`均接同一显式stage；宿主CLI/worker argv/guard record必须彼此等同。**不能仅从调用者传入release内容自行推导/放宽stage**。

```diff
--- src/task9_lr/real_g1.py
+++ src/task9_lr/real_g1.py
-def release(path,p,*,infrastructure=False,arm=None,seed=4718):
-    mode=b.stage(p)
+def release(path,p,*,phase=None,arm=None,seed=None,infrastructure=False):
+    mode=resolve_stage(p,phase,arm,seed)
+    # existing exact issuer/path/SHA, source digest, sealed protocol, immutable
+    # CID/image/UUID, actual lease and expiry checks remain fail-closed.
+    # infrastructure token additionally binds intended_activity=mode['name'];
+    # scientific token stage/arm/seed must equal mode exactly.
+    # program: max cap <= reviewed original stage/run remainder, not G1's 1800.
+    # per-run profile+remaining enclosing job cap <=43200; all final jobs <=14400;
+    # aggregate original worker/GPU caps still208800, source budget review rolling.

-def inner(p):
-    mode=b.stage(p)
+def inner(p,phase=None,arm=None,seed=None):
+    mode=resolve_stage(p,phase,arm,seed)
+    # call existing real owner/guardian/watcher chain with identical explicit mode;
+    # same no retry, exact identity, write-before-launch and actual wait witnesses.
```

不得直接调用旧`supervise.dispatch`真实路径：它仍`continuation.assert_execution_allowed`且尾部故意报UNKNOWN，原name/旧会计不能被当修后完整路径。只复用其中已验owner/guardian/watcher/actual outer_wait/DockerBackend，动态实际stage release与独立session/budget裁决保持。

### 一个program root，每stage独立allocation

现`prepare()`只适单阶段且root一旦存在拒绝。应拆两步，保原分配机制：

```diff
+init_program_namespace(protocol, independent_program_admission)
+    # exclusively create root/log/freeze/protocol+4 configs once; no GPU allocation.
+    # hash exactly matches sealed protocol; original never overwritten.
+
+prepare_activity(protocol, phase, arm, seed, infrastructure_release)
+    # main root must match frozen protocol/source; same supervisor lock.
+    # exact predecessor independently completed; no consumed activity/ledger.
+    # create allocations/<activity>/ exclusively (failed namespace remains consumed).
+    # same exact image/UUID/read-only workspace/history/write-only batch output.
+    # receipt_root = commands/<runid>/<activity>/infrastructure-{launch,inspect}.
+    # allocation lease/container.json/container-inspect.json belong to this activity,
+    # never overwrite preceding stage's allocation or root metadata.
```

每阶段独立有限lease，创建后独审CID的时间明确预留，完整lease入GPU准入预留直到exactStopped；job cap/save/control/审核尾由相应独审令给值，不新增固定经验常量。profile执行结束精确停该容器，独审完成再为remaining分配；checkpoint在同program root持久目录中保留。每run记录从头profile与本run remaining，禁止用上一run checkpoint或旧L1000桥。

`resources/spec_gate`按`spec.record.phase/arm/seed`解析mode，读取`allocations/<activity>/...`，host与container都保canonical HOST ref。Docker Mounts继续全字段canonical排序；source/预算到期后仍能对原sealed CID精确cleanup，但不能新启动。完整lease/stage预算拒绝后不改cap抢跑、不重启旧容器。

## 3. worker复用正式科学路径＋原生严格合同

```diff
--- scripts/task9_11/worker.py
+++ scripts/task9_11/worker.py
+    is_real_program = real_program.enabled(protocol)
+    # real admission requires exactly phase/arm/seed in program table;
+    # verify source, predecessor, stage token and quota before activate/model load.
+    resource_protocol = real_program.resource_view(protocol,token) if is_real_program else ...

     elif a.phase=='profile':
         value=train(config,out,max_wall_s=active_budget,pause_after_consumed=250000,
                     evaluator=evaluator,resource_guard=...)
         ... load_checkpoint(out/'profile.pt','cuda') ...
+        # native unchanged strict full source contract MUST match current frozen program;
+        # no limited_loader/old-contract bridge here.
+        # store existing full profile-restore evidence + read-only actual_devices of
+        # restored policy/critic/target/logalpha/replay and optimizer fields (CPU step allowed).
+        # steps250000, config3M, updates, pending ledger and full RNG/env restored.

     elif a.phase=='remaining':
         ... original validate_profile + save_readiness ...
         value=train(config,out,max_wall_s=active_budget,resume=out/'profile.pt',...)
+        # verify this run steps3M/updates299975 and12 complete196 periodic records;
+        # fixed final.pt/full actor/config/meta refs belong to this run only.

     elif a.phase=='final-test':
+        real_program.final_admission(protocol,token,a.arm,a.seed)
         manifest = read exact independently sealed test_manifest
         checkpoint = exact token.final_checkpoint  # full final3M file, not chosen peak checkpoint
         sac,...,stored = load_checkpoint(checkpoint,'cuda')
+        # native full source equality; storedconfig exact frozen scientific config;
+        # state.steps/sac.env_steps3000000; same read-only restored actualdevices.
         evaluate(...,recording=True,final_manifest=manifest,...)
+        # exactly200 held-out random +96 fresh semantic=296; no old196 entry substitute.
```

原生load检查`runtime/src/task8_lower/training.py:105–127`全部保留；source_contract包含测试文件/新增源，故所有上述分支和对应新stdlib测试必须在first profile前同一次冻结。final所需manifest读取/碰撞核验/test_jobs/证据解析亦在此时接完，不能等四个checkpoint产生后再改代码。

`real_batch.worker_argv`修正final目录：

```diff
- folder = 'g1' if stage=='g1' else f'{"smoke" if stage=="gate-evaluate" else "formal"}-{arm}-seed{seed}'
+ folder = ('g1' if stage=='g1' else
+           f'{"smoke" if stage=="gate-evaluate" else "test" if stage=="final-test" else "formal"}-{arm}-seed{seed}')
```

## 4. 独立stage原件与当前预算/前序裁决

新增program token schema必须在冻结前明确：

- `format=task9-lr-real-program-release-v1`，`status=PASS`，reviewer为.18.2；exact run/source/protocol/CID/image/UUID/phase/arm/seed/issuer原件SHA，与既有严格规范相同。
- `stage=profile|remaining|final-test`；infra stage另为infrastructure但`intended_activity`精确绑定待执行项。max_worker/max_gpu/control/save/lease/evaluation_reservation均数值明确，原表quota固定；expiries不越原截止，完整cap+控制/保存/停止必须可容纳。
- `predecessor_review`是原独审完整裁决ref，不只activity.status自报PASS；profile第一项还需LON完整/旧C限定组合/整案可行性，其后profile依前run remaining完整；remaining依own profile完整。
- remaining须pin own profile.pt / profile-summary / validation-0250000 / profile-restore / raw checkpoint-costs / interactions / diagnostics字节账与成熟窗口/全案余量审查。profile摘要损失下降不当task验收，source/实际设备/RNG/pending/full恢复/资源均必须核。
- final须pin同一个完整独立开发验收裁决、四run checkpoint冻结bundle和同一个独立test manifest，见下一节。令不能从actor分数自动挑模型。
- source review一次签完整program source（含final全部路由），各阶段仍有自己的独立budget/阶段令；review不等执行令。缺令返回NEEDS_INDEPENDENT_REVIEW，父授权内发原件给独审后自动续，不逐门向用户再问。FAIL/UNKNOWN保留且不重试，不用新namespace重复科学预算。

## 5. final在初训前写齐，实际放行留到开发验收后

`real_program.final_admission`必须同stage表一起实现且定点测试：

1. 四run remaining全部完整独裁PASS；对应full final.pt的3000000边界、配置/原生合同、full actor/元数据同一身份，各自唯一记录。
2. 独立开发B–E验收实际PASS（固定成功/非劣/成本/自然推理匹配批次等原标准）；不重测开发回合凑PASS，不改成功/碰撞/终止语义。
3. 独立模型bundle固定四个**3M final** full checkpoint与actor、配置SHA；每final token选自身arm/seed对应项，不能选其它run/best checkpoint。fullfileSHA是load前实际核验的必要路径；不得把发送目标或actor文件当full恢复。
4. 独立manifest schema保持既有`task9-lr-final-manifest-v1`、200原held-out随机task+96新semantic task；旧episode/proposal seeds碰撞审计原件、最小nonce、role/source_split/stream_index均沿现`admission.test_jobs`，不能沿旧196入口。
5. 四final token绑定同一bundle/manifest exactSHA，单个296、总1184；一次性identity，任一不足/失败保全write-ahead消费，不补跑。无任何模型/超参/源变化后再看test；final不能回流修改开发门。

manifest/bundle实际产生时放`.18.2`独立日志原件或program结果freeze，不入artifact_files扫描的src/config/scripts。只增加外部ref，不改封存program协议字节；token绑定原件，保证四full checkpoint原生source合同继续一致。

## 6. 原子写前额度、诊断与时间/保存账

`program.resource_view`只作资源剩余映射，不改模型/科学配置：

```diff
+history_evaluations = 980 + 196  # actual completed LON needs exact independent proof
+remaining_global = protocol['max_evaluation_episodes'] - history_evaluations
+assert remaining_global == 10592
+expected_before = sum(s['evaluation_episodes'] for s in stages_before(current))
+assert actual_prior_complete_started_count == expected_before
+assert token['expected_evaluation_before'] == expected_before
+assert token['evaluation_reservation'] == current['evaluation_episodes']
+view['max_evaluation_episodes'] = min(remaining_global, expected_before + current_quota)
+view['max_output_bytes'] = original_total - reviewed_historical_total_upper
+view['max_diagnostic_log_bytes'] = original_diagnostic - reviewed_historical_diag_upper
```

worker内base evaluate每个batch仍先原durable_event再执行；同program root全量episodes-started扫描，guard再核当前stage未超过quota、历史1176+全部新记录不超11768。expected_before不能用“现有文件数”自适应改大；先前FAIL/UNKNOWN不允许绕过。同一阶段view上限从固定前序+当前quota计算，不因重复调用resource_view随已启动数滚动放宽。

诊断8GiB包括`any('diagnostics' in part for part in path.parts)`下*.pt、events/parity、logs及agent_logs/源快照；不能仅2TiB total覆盖。旧上界沿同口径入账，不因新扫描口径更小扣旧费用。原OutputBudget写前检查、256MiB现有日志储备/40GiB full-save临时预留保留，不能删轨迹/失败样本省预算。profile完整100k replay/full-save峰值与remaining实际空间每门核，不以LON约250MB/196外推所有周期/恢复/模型总空间。

### 250k与保存必须按物理实际一次计费

只读原科学源码`runtime/src/task8_lower/training.py:298–311`：250k普通周期先`checkpoint-0250000.pt`→唯一validation-0250000(196)；profile_pause在228–248另写`profile.pt`，其validation_pending已清，再由worker完整load一次验证。remaining从profile.pt原生加载，不重开250k评估。

父已明确计费解释：历史完整B1 wall已含每run13个普通周期/final full-save、12×196，不再将这些整包重复加。新增只有每run一次profile.pt实际写入、profile核验restore及remaining续接restore（两次不同真实恢复各一次）、必要新控制/交接。250k转移属于该run3M，250k的196属于9408，不增加科学预算。两次250k物理保存不能隐掉第二次，也不能改151原科学删save。

可从实际`interactions`在100k replay fill以后至250k前的尾窗派生成熟非周期吞吐（明确输入文件SHA/相邻step、wall、样本数和单位）；已有200k→250k profile mature_window亦可交叉重算。另列250k普通save、extra profile save、196评估、完整restore各实际时间/字节和全raw enclosing wait，嵌套不相加。禁止简单12×整段profile wall：它含初始化/warmup/两个保存/评估，会重复计算额外profile开销或错误外推未成熟段。

原`admission.validate_profile`的remaining proxy公式保持使用条件明确：非周期成熟成本/50000×2750000＋11×(ordinary checkpoint+196评估)＋final save；恢复/独审/控制/发布尾另核一次。预算估计不是已测必需下限；旧完整B1经验与新实际成熟证据类别区分，不承诺工期。profile/remaining两stage实际 enclosing成本累计不越每run43200原门，allfinal不越14400；都包含于全局58h限，不能把旧fullwall与同一checkpoint/评估拆项再相加。

## 7. 同冻结前必要host定点验证（尚未执行）

- 固定12stage顺序、exact arm/seed/前序；拒跨run checkpoint、重开G1/smoke/C ON/LON、profile 250k计作额外预算、final test提前进入。
- 同program root两不同activity独立allocation/receipt/supervision目录，旧stage原件不覆盖；同stage消费后拒重；HOST↔container refs、24 Mounts排列/字段/重复项保已有结果，仅验证新路由必要增量，不重跑旧GPU矩阵。
- 真实worker inert路由profile只从头一次、remaining仅own profile原生恢复、final仅四冻结final和独立manifest；用原loader source惯例验证source drift拒绝，不启用旧LON bridge。
- 写前1176+10592额度及每stage196/2156/296准确边界，重复view不放宽；诊断*.pt与重复计费/间接ledger篡改反例。
- 同一源hash/mock checkpoint合同从profile→remaining→final保持；final manifest/bundle追加在外部原件目录不变artifact digest；测试文件/源码/config有任何改动则原生source_contract拒绝。
- full program独审后一次封source/protocol/完整CLI；首个实际profile前不得再说final等以后补实现。真实profile/restore/成熟/后续final按门才执行，无额外GPU smoke或回合。

## 交接与当前状态

本文件仅已授权未来范围的具体patch规范，**所有生产diff尚未应用、上述新stdlib也尚未执行**。当前active LON源码仍26308d91…，未碰其namespace/进程/设备/令；LON实际状态由父监控/独审原件为准。本草案不能签令或使正式可运行。LON实际完整PASS＋全案可行性PASS之后才一次落实/独审/冻结；若后者不容纳，则保本草案并集中交具体阻断，不实现或启动无可行预算的正式任务。
