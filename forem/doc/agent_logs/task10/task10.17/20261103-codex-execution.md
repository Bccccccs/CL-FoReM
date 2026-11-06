# task10.17 执行记录

开始 2026-11-03T22:51:46.639755+08:00（主机时间；用户时区Asia/Shanghai），负责人Codex，实际模型平台未提供可核实名称/强度，未知。推荐GPT6.1sol/high、Sonnet5.5/high：恢复/预算/训练合同核查。执行者有选模和先建档委派权限。

用户授权：严格A→B→C→D；A共享128真实/64诊断更新/1小时，先CPU；通过并支持48h才唯一seed101/B3 4718/batch8、10k/9k新KL训练；顺序3×12验证；不追加预算/种子/task11。保留现有未提交修改。

已读根AGENTS、ENV、README、最新PROGRESS、17三文档及16最终验收。分支codex/task10-upper-wm；容器forem-task10-runtime /workspace精确挂载本worktree，参考只读。四GPU空闲，未见task10/task12计算worker。既有恢复仅全8自然终局，不能满足A。准备改动task10恢复、显式10k入口/launcher、新评估wrapper与专项测试；共享文档父独占。

子任务17.1恢复与CPU夹具、17.2训练入口持久监督、17.3三检查点评估适配已建三文档，依赖/写入范围详见各PROCEDURE。子Agent不得使用GPU/启动训练或评估。父统一A harness、GPU与证据。真实A预算尚未启动。

2026-11-03T23:03:05.521857+08:00 · CPU实现交付：17.1最终45passed/25.38s，17.2 37passed；父全task10为201passed/2skip/11fail，失败全因test_lower默认容器不存在的宿主artifact根，显式/reference重跑13pass/1skip/rc0。父最后恢复+harness新19+4项复测中。子17.1/17.2已冻结src。父A harness独立共享账本，在自然混合边界（目标64，最晚112真实）保存，原PID继续8作独立shadow参照，新PID沿原ledger再8，共≤128；当前真实回放仅作诊断，正式B另从头。全部CPU/GPU设备及模型/梯度证据分开，不把CPU称实测通过。SOURCES登记SRC-T10-043。

2026-11-03T23:07:56.259637+08:00 · 唯一A已启：run t10-17-audit-20261103-s101，容器supervisor1677/capture1678，宿主worker577058；原epoch1793718227.6644661、硬截止1793721827.6644661，3600s。functions exec session86197（仅交互跟踪；容器内预算监督独立），stdout/stderr在forem/logs/task10/task10.17/audit-supervisor.*及run/capture.*。原共享审计预算包含全部capture/reference/resume/诊断，真实回放只用于诊断，不作为B预热。完整命令为docker exec --user1004:1004、CUDA_VISIBLE_DEVICES=0、CUBLAS_WORKSPACE_CONFIG=:4096:8、PYTHONPATH=/workspace/src、OMP_NUM_THREADS=2、TASK10_PHYSICAL_GPU=1，timeout3600 python3 -u -m task10.resume_audit supervise --output /workspace/results/task10/t10-17-audit-20261103-s101。先CPU父最终23pass/20.08s，C父25pass/1.54s，GPU预算从supervisor创建总账开始；A尚未通过。

2026-11-03T23:19:58.928429+08:00 · A进行中，实际完成56真实/8诊断更新，下一批64已预留；首诊断更新原件gpu-update-evidence.json为verified_cuda/issues=[]，B3不变、actor/q1/q2及Adam设备和变化核实。计入统一原3600s预算，未启B。父审查17.3发现组内CPU report只受global截止，已让原子修正为min(group90min,global4.5h)；新4截断case，父评估+handoff测试33pass/4.29s/rc0，logs/task10/task10.17/parent-final-scripts.txt。D持久driver现有训练原件复算/训练loss原始CSV及明确100更新平滑图/配对曲线交接，均未运行B/C；组内report到限缺失允许D只读CPU report-D补证，原C记录保留，不增加GPU交互。父独占scripts/task10_long_handoff.py、task10_resume_audit_report.py及其测试，未改A冻源。源与预算见SRC-T10-043/044。


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
