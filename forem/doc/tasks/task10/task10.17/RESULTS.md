# task10.17 结果
设计已交付，尚未执行。负责人待派发，审核者Codex。实际模型/强度未发生。推荐GPT6.1sol/high、Sonnet5.5/high，跨恢复/资源预算/训练合同；执行者可自主选模与先建档委派，父统一资源。
填写A核查原件及退出码、正式run信息、可恢复边界验证、实际预热/决策/更新数、保存与恢复成本、三个检查点逐回合结果、失败/缺失、总worker及global时间。禁止以16的旧结果代替本节点实测。[来源](../../../SOURCES.md#src-t10-042)

## 2026-11-03T23:03:05.521857+08:00 · 接手与CPU准备

负责人Codex父，状态active；推荐GPT6.1sol/high、Sonnet5.5/high，恢复与训练合同，实际模型/档位未知。可自主选模与先建档委派，父统一GPU/预算。保留原工作区修改。17.1正常混合边界恢复CPU最终45passed/25.38s/rc0；17.2新显式10k入口/持久监督37passed/rc0。父旧路径套件201pass/2skip/11fail，11fail均旧lower测试缺少容器artifact根配置，显式/reference后13pass/1skip/rc0。日志在forem/logs/task10/task10.17/及各子目录。仅CPU夹具，不代表真实A通过，A/B/C尚未执行。[来源](../../../SOURCES.md#src-t10-043)。


## 2026-11-03T23:30:28.721796+08:00 · A恢复通过、成本门未通过，按流程交回（当前结论）

**状态review / NOT_READY；A已结束，B/C均未启动。** 负责人Codex父。推荐GPT6.1sol/high、Sonnet5.5/high，恢复/预算/训练合同；实际平台模型/强度未知。17.1–17.3子Agent只实施CPU准备，全部GPU由父统一；本轮没有扩大预算、自动重跑、追加种子或启动task11/task12。[SRC-T10-043](../../../SOURCES.md#src-t10-043)；C/D CPU准备依据[SRC-T10-044](../../../SOURCES.md#src-t10-044)。

### 恢复原件与验收

正常batch8在64真实决策、10次明确诊断更新后保存，不等待8行全终局，也没有人为终止回合。第8批自然ended行0/1/2/3/5/6已复位，行4/7存活；保存后episode IDs=[7,5,4,4,5,6,8,7]，当前决策/历史长度=[0,0,0,0,1,0,0,1]。旧PID1678继续8条作独立shadow账本参照，退出后新PID1741恢复原collector账本再执行8条及下一诊断更新；两个分支全部计入统一A预算。

comparison.json为verified、differences=[]，before_exact/after_exact/same_start/same_deadline全True，真实下一批场景、物理/传感/grid/queue/clock、观测、候选、logits/选点、sampler/policy/global RNG、历史、回放抽样/内容、梯度/更新/Adam/target/scheduler及账本逐位一致；父从reference/branch.pt与resumed/branch.pt重新比较同样无差异。父逐原始journal核capture64+reference8+resumed8=80，原collector capture+resumed无漏重，reference/resumed身份一致。真实回放只作诊断，未调用虚假1000预热计数，未使用旧回放。

两个worker退出码0/0，supervisor外层rc0；CPU parent-review退出码1，**唯一issue为成本投影不支持48h**，不是恢复失败。80/128真实决策、12/64诊断更新；worker监督窗口1293.513658s（21m33.514s），含父CPU原件复核的A已记1355.686018s（22m35.686s），均在原1h内。原A started_epoch=1793718227.6644661、deadline_epoch=1793721827.6644661未变。现场无本轮进程，GPU compute为空；未启动持久B launcher。

### 实测成本与48h门

所有以下耗时均为CUDA同步的wall时间，不冒充GPU-event核计时；sim累计尝试642.25 row-seconds、提交628.5 row-seconds单列。采集10批（80真实决策），更新12次。

|分项|次数|均值s|P50 s|P95 s|
|---|---:|---:|---:|---:|
|初始复位|1|56.041726|56.041726|56.041726|
|每批记忆重建/选择|10|0.022803|0.019205|0.042880|
|每批真实执行|10|34.514182|36.188083|39.673128|
|每批next候选推演|10|38.675156|39.242056|53.038893|
|每批自然结束行复位/新候选|10|44.092652|43.905696|47.788210|
|每批回放搬运|10|0.049424|0.049417|0.050673|
|诊断回放抽样|12|0.000252|0.000241|0.000420|
|逐次输入整理/CPU→GPU|276|0.001708|0.001635|0.002881|
|完整诊断更新|12|0.330031|0.302594|0.479814|
|64决策完整边界保存|1|8.062141|8.062141|8.062141|
|新PID完整恢复|1|8.081951|8.081951|8.081951|

保存484035709 bytes，峰值RSS 7864380KiB（约7.500GiB）；PyTorch peak allocated 6690426880 bytes（约6.231GiB，不含driver/context/未用reserved缓存）。GPU首更原件由父CPU重新summarize_evidence，为verified_cuda；actor/双Q非零有限梯度与权重变化、Adam设备、B3 frozen/eval/no_grad及权重不变均通过。

实际采集/推演/复位/搬运/选择合计 / 80 = **14.6692771368s/决策**；更新均值0.3300314833s、P95 0.4798142881s。保存点为256倍数（到9984）加2000/5000/10000，共42个。工程保守外推：

`Σ(save64_s × max(1,d/64))`，d遍历42保存点；完整保存8.0621413365s，累计投影27295.3872624s=7.582052h。`10000×14.6692771368 + 9000×update_mean + 估算保存 + 初始复位/加载 + 120s清理` = **177134.730326s=49.204092h**；改用更新P95并加一次线性放大的恢复 = **179745.580393s=49.929328h**，均超过172800s/48h。输入、公式、单位、原始分位与每项统计均在parent-review.json。

**限制：这不证明实际10k必超48h。** 当前只有一次64决策完整保存/恢复，整次保存线性放大包含固定模型/场景状态，因而偏保守；未实测10k规模保存。B save_consistent还另写learner/actor与发布索引，其额外成本亦未在本次完整端到端测量。已有证据不足以肯定48h可行，故按用户A条件停止并交回；不能套旧约40h估价或略去保存成本放行。

### B/C/D范围与交接

B：0正式训练决策/0更新/0训练墙钟；C：0评估回合/0决策/0更新/0评估墙钟。没有新2k/5k/10k检查点、学习曲线或配对结果，不能判断学习持续改善/原地复发，不将task10.16旧结果当本轮结果。保存恢复仅对本次混合边界与下一批/下一更新可靠，未声称所有未来故障可恢复。当前不具备进入20k×3的本轮收益证据；不自动追加预算或task11。

工程准备已交付：显式long-10k配置/9000 scheduler、持久launcher/原deadline与一致检查点，以及新metadata的顺序12×3验证入口；均尚未执行正式GPU验收。子17.1 CPU45pass，子17.2 CPU37pass；父最终恢复+harness23pass、C+D33pass，旧lower artifact根配置纠正后13pass/1skip；初次缺路径的11fail日志保留。详见子三文档。

建议决策者的具体下一步（**尚未授权/未执行**）：另定独立有界保存成本核查/优化窗口，先分解固定状态与随回放增长的序列化/复制/哈希成本，用明确标注的CPU诊断扩容测256/2k/5k/10k保存与恢复、内存及完整发布成本；核是否可在保留journal一致性/原子latest/版本拒绝和42次保存频率下，减少每次全量重读与重复编码。不得据本建议自动增加A窗口、删检查、改保存频率、缩真实决策或延长48h。task12只协调既定范围，本轮未占其他GPU或启停其任务。

版本：HEAD `91f538cf2ee10bebffd6b643d5c908fa0d419ced` 加未提交修改，均保留未提交；精确本轮源/配置SHA在early-handoff.json，全部执行模块SHA在frozen-code.json及checkpoint sources，B3 actor SHA `3db11d9f00317849e35a523d66d0935ebc2e3567d82c519ccc42f3d8de42f7ae`，parent-review SHA `ec162d4702fbc874b07eae6d446432848940bbbf7cc67032d710eff50add9f3e`。原件根 `forem/results/task10/t10-17-audit-20261103-s101/`；关键文件decision-boundary.pt、save-report.json、comparison.json、reference/branch.pt、resumed/branch.pt、capture/resumed performance.json、audit-budget.json、process-exits.json、gpu-update-evidence.pt/json、parent-review.json、early-handoff.json。日志 `forem/logs/task10/task10.17/`，CPU各专项另在子目录。所有实际命令及rc见独立日志；只读复算用container CPU：`python3 -u /workspace/scripts/task10_resume_audit_report.py --run /workspace/results/task10/t10-17-audit-20261103-s101 --output <新的输出路径>`（该入口含原1h墙钟门，事后复算超过原时限时会额外如实标A复核时限，不能改原报告；差异/成本原件可逐项复算）。禁止再次运行supervise/capture/resume来覆盖本run。

本轮记录时全局墙钟（从22:51:46接手起，含CPU准备/等待/原件复核）2322.086s；串行A worker监督窗口1293.514s为已测worker成本口径，父CPU准备测试时长分列日志，不将相加的并发CPU测试时长当全局墙钟。原授权交付至此按A退出条件交回决策者，剩余B/C未执行。

## 2026-11-04T09:19:40+08:00 · 预算批准后的当前执行合同

用户已批准成本预算并限定最多两卡；本次B训练硬限改54h（194400s，执行者基于49.2–49.9h估算留余量的工程选择），C保持4.5h。仅物理GPU1顺序运行，旧48h合同/停点属于历史并保留；A恢复实测沿用，不重跑A。唯一run t10-long-20261104-s101从头初始化、10k/1000预热/9000更新及42保存点不变；原B→C→D、原epoch恢复/不自动重启等约束保持，所有时限检查/配置/收尾审计同步。推荐GPT6.1sol/high、Sonnet5.5/high；实际模型/强度未知。执行者可选模/先建档委派，父统一GPU与验收，本轮独立执行。[授权、估算与限制](../../../SOURCES.md#src-t10-budget-20261104)。启动/运行证据待本轮日志与launch/contract，不以预算批准称已完成。

## 2026-11-04T09:23:29+08:00 · B正式启动核实

状态active，run t10-long-20261104-s101；单seed101/B3-4718/batch8，从头初始化/1000预热/10k/9k/KL .35，54h。70CPU合同测试通过（9.30s）；实际初始全模型相等、GPU1设备/源码配置hash/三个截止核对通过。开始09:20:23，训练截止11-06 15:20:23，后续C仍4.5h。当前8真实/0更新，处于预热，不预宣称首更或训练完成。driver900227/launcher900228，host worker900264/container1807，日志forem/logs/task10/t10-long-20261104-s101/；launch/contract/budget与startup-verified.json可核。按既有偏好退出主动监督，独立driver顺序B→C→D且无自动重跑。推荐GPT6.1sol/high、Sonnet5.5/high，实际未知，执行者可自主选模/先建档委派，父统一预算；本轮独立。详细监控/停止/恢复方法见[本轮日志](../../../agent_logs/task10/task10.17/20261104-codex-launch.md)。[来源](../../../SOURCES.md#src-t10-budget-20261104)。


## 2026-11-04T10:15:41.248065+08:00 · B→C→D 持久收尾

状态review，交决策者原件审核；完整条件=False。推荐GPT6.1sol/high、Sonnet5.5/high，恢复/训练/原件核验；实际模型/强度未知，父统一GPU/预算/原件复算。依据[SRC-T10-044](../../../SOURCES.md#src-t10-044)。

训练run `t10-long-20261104-s101`，终态 `failed`，真实决策 256/10000，更新 0/9000。独立CPU原件审计 `incomplete_or_failed`，issues=["training did not reach complete terminal budget", "missing 10000 boundary checkpoint", "launcher exit missing/nonzero", "terminal budget differs", "fresh 1000/0 warmup missing", "first GPU update evidence missing", "missing scheduled checkpoint 256", "missing scheduled checkpoint 512", "missing scheduled checkpoint 768", "missing scheduled checkpoint 1024", "missing scheduled checkpoint 1280", "missing scheduled checkpoint 1536", "missing scheduled checkpoint 1792", "missing scheduled checkpoint 2000", "missing scheduled checkpoint 2048", "missing scheduled checkpoint 2304", "missing scheduled checkpoint 2560", "missing scheduled checkpoint 2816", "missing scheduled checkpoint 3072", "missing scheduled checkpoint 3328", "missing scheduled checkpoint 3584", "missing scheduled checkpoint 3840", "missing scheduled checkpoint 4096", "missing scheduled checkpoint 4352", "missing scheduled checkpoint 4608", "missing scheduled checkpoint 4864", "missing scheduled checkpoint 5000", "missing scheduled checkpoint 5120", "missing scheduled checkpoint 5376", "missing scheduled checkpoint 5632", "missing scheduled checkpoint 5888", "missing scheduled checkpoint 6144", "missing scheduled checkpoint 6400", "missing scheduled checkpoint 6656", "missing scheduled checkpoint 6912", "missing scheduled checkpoint 7168", "missing scheduled checkpoint 7424", "missing scheduled checkpoint 7680", "missing scheduled checkpoint 7936", "missing scheduled checkpoint 8192", "missing scheduled checkpoint 8448", "missing scheduled checkpoint 8704", "missing scheduled checkpoint 8960", "missing scheduled checkpoint 9216", "missing scheduled checkpoint 9472", "missing scheduled checkpoint 9728", "missing scheduled checkpoint 9984", "missing scheduled checkpoint 10000"]。评估顺序终态 `partial`，每检查点和缺失见 `/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-long-eval-20261104-s101/sequence.json` 与report。学习曲线CSV/PNG、同初态logit CSV位于评估根；模型固定预算终点，不按成绩选模。

A实测worker窗口 1293.5136578399688s；全任务全局墙钟 41034.60586810112s，累计测量worker阶段 4604.389427887276s（A监督窗口+训练worker+评估子进程；CPU准备/排队另在global中）。训练墙钟 3313.177893185988s，训练worker 3309.7227007448673s，评估worker 1.1530693024396896s，B→D全局 3317.7946622893214s；A另见本节点A记录，排队/CPU收尾计入global，不能把worker累计当墙钟。退出码 [{"stage": "B", "returncode": 1}, {"stage": "C", "returncode": 0}, {"stage": "D-audit", "returncode": 1}]。

学习是否持续改善：检查点或原件审计不完整，无法判断持续改善。

原地是否复发：完整曲线不足，按逐检查点原始结果报告。

保存恢复：A真实恢复证据单独见A结果；未从不完整训练反推恢复可靠。

20k×3建议：先补齐当前授权内的原件交接并交决策者裁定，本轮不自动进入20k×3。

|训练决策|更新|报告状态|严格成功/12|原地比例|对uniform配对|
|---:|---:|---|---:|---:|---|
|2000|1000|missing|missing|missing|missing|
|5000|4000|missing|missing|missing|missing|
|10000|9000|missing|missing|missing|missing|

三个检查点完整读数见handoff.json/reports及curve-summary.json。仅单种子、固定12validation场景；该曲线不能证明跨种子或test泛化，也不能单凭loss下降确认收益。20k×3须决策者结合曲线与uniform配对裁定，本轮不自动启动。任何不完整/缺失保留，不能声称完整通过。

原件：`/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-long-20261104-s101/parent-training-audit.json`、`handoff.json`、launch/worker-exit/training-budget/contract与checkpoints；评估原件 `/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-long-eval-20261104-s101`。复算：CUDA隐藏调用 `task10_long_handoff.py audit --run <container run> --output <new audit path>`；评估各report入口见17.3。完整模型/配置/代码/地图哈希在contract、checkpoint metadata、manifest、parent audit中。

## 2026-11-04T10:20:02+08:00 · 首256检查点失败复核及CPU修复

当前状态review：训练未运行，原run于2026-11-04T10:15:36+08:00 launcher rc1；256真实/0更新/未满预热，没有任何boundary checkpoint。修复了tree_equal对单元素stride13张量转字节的异常，逐字节比较规则保持（含NaN payload及正负零）。112专项/回归CPU测试passed、28.24s/rc0；真实32批256唯一journal已落盘、29184 tensor字段中24处原异常复现，修后CPU检查通过。原run49文件hash未变，初始/最终模型逐字节相同。此CPU检查不代表实际完整保存已验收。

无环境/传感/sampler/RNG完整快照，无法按原合同从256精确恢复，journal不代替恢复点。按本流程“禁止自动从头重启或创建第二训练run”，本轮不重跑。新run方案已具体准备，仍10k/1000预热/9000更新、单卡GPU1、54h训练及4.5h评估，原失败256与约55min独立保留；须用户明确批准后执行，未重置旧run预算、未开始新run。原11-06预计完成时间失效，新的估价待实际获准启动后生成。

推荐GPT6.1sol/high、Sonnet5.5/high：保存/精确恢复/运行边界；实际模型/强度未知，执行者可自主选模/先建档委派，本轮独立完成。原件与命令见logs/task10/t10-long-20261104-s101/check-failure/，修前内容已备份。0新交互/0更新/0新增GPU，GPU1空闲且不触碰0/2/3其他任务。[来源与限制](../../../SOURCES.md#src-t10-save-failure-20261104)。

## 2026-11-04T10:25:39+08:00 · 明确授权修复后r2重启

用户明确“修复并重新启动”，本次授权新run t10-long-20261104-s101-r2（评估同名前缀long-eval），54h训练+4.5h评估、原10k/1000/9000与单卡GPU1。旧失败run保持，256消费及55min另计，不称原run恢复；r2一旦创建沿其原epoch，不自动再开第三run。沿原B→C→D/恢复拒绝/固定预算终点约束。推荐GPT6.1sol/high、Sonnet5.5/high，实际未知，可自主选模/先建档委派，父统一GPU与验收；本轮独立。[授权与限制](../../../SOURCES.md#src-t10-restart-r2-20261104)。

## 2026-11-04T10:28:24+08:00 · r2正式启动核实

active：t10-long-20261104-s101-r2于10:26:12+08启动，54h/10k/9k，1000新真实均匀预热，单卡GPU1；driver969983/launcher969984/host worker970022/container1911。初始化全模型相等、CUDA设备/源码配置SHA/原截止合同均通过，账本8完成/0在途/0更新。补充完整保存→加载的非单位步长CPU回归及字节测试22passed/3.92s；此前112项回归通过，实际首256保存仍待，不提前称通过。旧失败256/0与55min保持。后续顺序C三个预定检查点与D原件审核由持久driver执行，不自动重跑。预计11-06 12:26–17:26，硬训练截止16:26:12，评估用尽则20:56:12，所有为+08。推荐GPT6.1sol/high、Sonnet5.5/high；实际未知，可自主选模/先建档委派，本轮独立。证据logs/task10/t10-long-20261104-s101-r2/{dispatch.json,startup-verified.json,prelaunch-code-sha256.json,cpu-full-save-regression.txt}及run/launch/contract/budget。监控停止恢复见[本轮日志](../../../agent_logs/task10/task10.17/20261104-codex-restart-r2.md)。[授权与限制](../../../SOURCES.md#src-t10-restart-r2-20261104)。


## 2026-11-04T14:59:20+08:00 · r2 256/1024独立CPU检查点审计

Codex，done（只读审计范围，长训仍由父负责）。推荐GPT6.1sol/medium、Sonnet5.5/medium，恢复状态交叉核对；实际平台型号/推理档位未独立核实；执行者可按授权选模与先建档委派，本轮独立，无新增交互/更新/GPU。源目录、训练账本/latest和进程未写入。依据[SRC-T10-CKPT-AUDIT-20261104](../../../SOURCES.md#src-t10-ckpt-audit-20261104)。

|历史点|实际决策/更新/回放|journal|混合行新/存活|完整性与内容|r2下一执行实测|
|---|---|---|---|---|---|
|256|256/0/256|32批256唯一身份|6/2|文件可读、SHA/计数/actor与learner一致|未执行|
|1024|1024/24/1024|128批1024唯一身份|7/1|文件可读、SHA/计数一致，85组Adam step24，scheduler24/9000|未执行|

双Q/target/actor权重、relative_uniform v1、固定alpha .35（运行float32表示.3499999940395355）、完整环境/传感/候选/时钟/RNG/历史/回放/历史ledger均核对；真实3/14个旧stride异常字段已复现并验证修后比较和内存保存加载字节一致。四最终CPU命令rc0。既有A1678→1741分支原件复算无差异，覆盖64/10混合边界下一8条与下一诊断更新；不能替代r2点的现场续跑。现场恢复仍要求ledger未变/旧PID退出/同源码runtime和boot，后续已消费不能回滚到历史点。

完整文件路径/字节数/全SHA及命令、首轮审计器alpha断言rc1修正说明、字段覆盖与限制见[独立审计报告](../../../../results/task10/t10-17-checkpoint-audit-20261104/REPORT.md)，原始JSON/日志同目录；[独立Agent日志](../../../agent_logs/task10/task10.17/20261104-codex-checkpoint-audit.md)。未发现需停训的新恢复阻断，未作现场处置；最近内容审计点1024/24，最近已有下一批跨进程实测的边界仍为A64/10。

## 2026-11-05T10:02:15+08:00 · r2运行进度与显存核查

训练仍active；09:55真实5760/10000（57.6%）、更新4760/9000，09:58:49日志4776更新、24个保存事件，最新5632/4632，2k和5k已保存。首更verified_cuda，已落盘update数值有限，无新增错误；复用11-04的256/1024只读保存审计，本轮不重复测试/hash/恢复。固定12图配对评估尚待训练结束，不以旧10/12当本轮收益。

GPU1当次65.4/95.6GiB，缓存地图在5632点已7260/10000，CUDA标签缓存张量10.46GB；按同均值剩2740图估计再增3.68GiB，若其他用量相近总约69.1GiB、余26.5GiB。当前看OOM风险较低；编码重复别名、分配器预留及未来峰值未被完全测量，不能保证绝不OOM。用户确认后继续现有单卡，不实施两卡拆分、不停训。

近期完整保存窗口外推训练约11-06清晨、随后评估约上午，非保证；现进程原54h硬配置未变。推荐GPT6.1sol/medium、Sonnet5.5/medium，跨日志/内存字段与估价核对；实际未知，可自主选模/先建档委派，本轮独立。详细计算/条件/证据见[SRC-T10-STATUS-20261105](../../../SOURCES.md#src-t10-status-20261105)及logs/task10/status-20261105/，0新交互/0诊断更新/0新GPU进程；原训练继续。


## 2026-11-06T07:31:33.715785+08:00 · B→C→D 持久收尾

状态review，交决策者原件审核；完整条件=False。推荐GPT6.1sol/high、Sonnet5.5/high，恢复/训练/原件核验；实际模型/强度未知，父统一GPU/预算/原件复算。依据[SRC-T10-044](../../../SOURCES.md#src-t10-044)。

训练run `t10-long-20261104-s101-r2`，终态 `complete`，真实决策 10000/10000，更新 9000/9000。独立CPU原件审计 `verified_complete`，issues=[]。评估顺序终态 `partial`，每检查点和缺失见 `/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-long-eval-20261104-s101-r2/sequence.json` 与report。学习曲线CSV/PNG、同初态logit CSV位于评估根；模型固定预算终点，不按成绩选模。

A实测worker窗口 1293.5136578399688s；全任务全局墙钟 203987.0389099121s，累计测量worker阶段 160181.6909855362s（A监督窗口+训练worker+评估子进程；CPU准备/排队另在global中）。训练墙钟 154055.95549781807s，训练worker 154029.40397948958s，评估worker 4858.773348206654s，B→D全局 162321.52003567293s；A另见本节点A记录，排队/CPU收尾计入global，不能把worker累计当墙钟。退出码 [{"stage": "B", "returncode": 0}, {"stage": "C", "returncode": 0}, {"stage": "D-readonly-report-10000", "returncode": 124}, {"stage": "D-audit", "returncode": 0}]。

学习是否持续改善：检查点或原件审计不完整，无法判断持续改善。

原地是否复发：完整曲线不足，按逐检查点原始结果报告。

保存恢复：A真实恢复证据单独见A结果；未从不完整训练反推恢复可靠。

20k×3建议：先补齐当前授权内的原件交接并交决策者裁定，本轮不自动进入20k×3。

|训练决策|更新|报告状态|严格成功/12|原地比例|对uniform配对|
|---:|---:|---|---:|---:|---|
|2000|1000|verified_complete|10/12|0.0|{"win": 0, "loss": 0, "tie": 12, "missing": 0}|
|5000|4000|verified_complete|9/12|0.05|{"win": 0, "loss": 1, "tie": 11, "missing": 0}|
|10000|9000|missing|missing|missing|missing|

三个检查点完整读数见handoff.json/reports及curve-summary.json。仅单种子、固定12validation场景；该曲线不能证明跨种子或test泛化，也不能单凭loss下降确认收益。20k×3须决策者结合曲线与uniform配对裁定，本轮不自动启动。任何不完整/缺失保留，不能声称完整通过。

原件：`/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-long-20261104-s101-r2/parent-training-audit.json`、`handoff.json`、launch/worker-exit/training-budget/contract与checkpoints；评估原件 `/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-long-eval-20261104-s101-r2`。复算：CUDA隐藏调用 `task10_long_handoff.py audit --run <container run> --output <new audit path>`；评估各report入口见17.3。完整模型/配置/代码/地图哈希在contract、checkpoint metadata、manifest、parent audit中。

## 2026-11-06T09:14:15.029017+08:00 · 决策者阶段审核

训练10000/9000完成，复用CPU verified_complete证据；独立从三检查点逐回合/决策JSON复算，成功10/12→9/12→9/12，原地0/18→1/20→1/22，同12初态哈希一致、合法argmax选择及唯一计数核对通过。10k完整报告由另一执行者补证中，旧300s超时保持；本轮不重复CPU报告、不重跑训练/评估，task10.17保持review待完整报告。[依据](../../../SOURCES.md#src-t10-t12-review-20261106)

没有持续学习提升或超越uniform10/12证据。5k/10k原地仅各一次，均standard_validation_00001首步，路线推进0.25、当步零失败，后续失败导致非严格完成；不判为全原地坍缩，也不直接归因原地。下一优先复用该退化场景的候选/Q/奖励/执行记录定位，不扩大20k×3，不把2k最佳点替代固定10k终点。本次仅审核，未启动新研究/训练。

负责人Codex，推荐GPT6.1sol/medium、Sonnet5.5/medium，跨行为/统计核查；实际配置未知，执行者选模/建档委派权限遵根约定。

## 2026-11-06T09:18:15+08:00 · task10.17本轮完成

**done：10k训练、36回合评估及必要原件核查均已完成。** r2于11-06 05:13:48+08结束，10000真实/1000均匀预热/9000更新、154055.955s（42h47m36s）、rc0；训练审计verified_complete/issues=[]、42个预定检查点有效，最终权重固定10k终点。无OOM，PyTorch实际分配峰值22.33GiB（不能混同nvidia-smi总占用/预留峰值）。

|真实训练决策|在线更新|严格成功/12|原地选择|对uniform胜/负/平|
|---:|---:|---:|---:|---:|
|2000|1000|10/12（83.33%）|0/18|0/0/12|
|5000|4000|9/12（75%）|1/20|0/1/11|
|10000|9000|9/12（75%）|1/22|0/1/11|

三份报告均verified_complete/issues=[]、各12完整/0缺失/0更新，36回合共60真实评估决策。10k终局9严格成功、2失败上限、1带失败完成路线，无stall_limit终止；不将合法原地选择一律称为原病态复发。uniform和旧KL200均10/12。读数10→9→9，**本单seed、固定12validation清单未观察随预算持续改善或最终超越uniform**；不推广为方法普遍无效或显著差异，不以2k较好结果挑选最终模型。暂不据这组读数直接扩大20k×3，本轮已授权终点完成，未开始task11。

10k原CPU报告300s及D补证超时记录保持；本次原入口CPU报告补证rc0、观察wall约433.7s，0新增交互/更新/GPU。report-complete-20261106.json已通过再发布report.json；原sequence partial保留，handoff.complete=true的cpu_supplement说明补证过程。原部分交接保留handoff-initial-incomplete-20261106.json，原部分曲线保留*.pre-cpu-supplement-20261106.*。现学习曲线CSV/PNG和curve-summary完整含三点。

证据：run/final-review-20261106.json、handoff.json、parent-training-audit.json；eval各checkpoint/report.json、learning-curve.csv/png；logs/task10/status-20261106/（报告命令/退出码/派生补证脚本/新汇总）。本次只对缺失报告做CPU补证，训练审计/其他适用报告直接复用，无重复训练/评估/全套测试或资产hash。推荐GPT6.1sol/medium、Sonnet5.5/medium，因需对齐报告/原件和统计口径；实际模型/强度未知，可自主选模/先建档委派，本轮独立。当前无task10进程，GPU1释放；task12等其他任务不触碰。[来源与限制](../../../SOURCES.md#src-t10-final-20261106)。
