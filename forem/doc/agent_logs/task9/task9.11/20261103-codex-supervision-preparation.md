# task9.11 监督修复与续跑准备

开始 2026-11-03T20:34:10.701664+08:00；负责人 Codex（父实际模型/强度未知）。最新用户仅授权必要只读、F白名单最小监督/预算修复、零模型零环境替身验证与文档交接。禁止模型、真实环境、旧run重启、原件修改、历史exit补造、预算/截止重置、科学合同变更、task10晋级。推荐 GPT6.1sol/high、Sonnet5.5/high：跨进程退出竞争与预算恢复需要高强度审查。

已读根/forem AGENTS、README、PROGRESS、父三文档尤其H、.3/.4三文档、STOP审核与重交接。分支 codex/task9-lower-improve，HEAD d198e5ca48f86071c05274f9da753f393ce058b4；全部既有dirty保留。最大活动子编号.4，新增.5最小实现、.6独立审查；不复用旧.3/.4身份。父负责来源、总账核查和交接；实现仅supervise.py/admission.py及专用纯标准库测试；审查者仅自身三文档/日志。

现场 task9.11 容器 forem-task9-lr-171820 exited(137)，task10 PID325288/GPU-baaca86e-0491-44bf-4294-e64ffe4934e9仍运行；未启停任何既有进程。STOP7引用待自动核对；已确认 host started 无终态，仅inner完整；未知原因不推定。

## 原账本与准备核查

STOP原7引用SHA全部一致（preparation-stop-sha-check.json）。所有461既有源码/配置/审计JSON建立保护快照。实际测试conftest会activate并import torch；本轮不运行该pytest收集，仅专用标准库unittest脚本。

父预算审计v1/v2诊断口径错误：仅按后缀排除模型会漏掉诊断和审计中的.pt；原件保留且该诊断余额作废。v3改为guarded_size路径口径，全部外部日志计入，原stdout/命令/SHA保存；未读模型字节。v3数值及公式登记SRC-1401，worker余额仅上界，UNKNOWN保留。只读报表首读FINAL-STOP-HANDOFF.md不存在（实际是.json），随后按实际.json核查，不把cat混合命令尾返回值当所有读均成功。

CLI核查证明旧F设计命令不能直接续跑。当前停止run不恢复，建议恢复次序先解决STOP处置/累计旧账与namespace→重新冻结/独立代码审查→新G1纯合成→未执行L ON门→四个从头250k与各profile/remaining；前提尚未成立，所有真实命令尚未执行。任何C ON重测会占用未授权额外196，不可偷偷从正式评估挪用。

## 续跑方案草案（尚未执行，等待.6独立核验）

建议恢复起点是“STOP处置与累计账本/新续接身份封存”，不是训练、不是旧run恢复。原run全部只读保留，旧FAIL绝不改PASS。新源码独立代码审查与新G1必须重测；四smoke消费已用满，不能重跑四组。旧四smoke/完整checkpoint/4000与980成本、C4718 OFF/ON原件及科学合同可供只读引用；旧源码PASS/G1/阶段release不自动转移到新SHA。

C4718这次的科学非干扰证据可以保留引用，但host完整性FAIL继续保留；独立审查须另给“证据复用＋新执行完整性合同”裁决，不取消独立验收。若该裁决要求再跑C ON，应先明确原10584开发/11768总评估中没有额外196空白额度（L ON196和正式9408仍必须保留），当前不得挪用、取消或补跑，应继续NOT_READY并交用户决策。

未执行L ON196仍须完整验收；随后每个arm/seed从头250k成熟profile→各自审核→remaining至3M；四run共12M不变，250k计在3M内。L不能借C的profile；前一run成功不构成后者验收。开发判据通过且四final/manifest/泄漏核查/预算封存后才一次独立1184测试，不能用于选方案或晋级task10。

当前protocol_read固定旧run，prepare拒绝已存在输出，旧未闭活动拒绝跨阶段，新SHA拒旧release。要开新续接namespace并挂接原累计账本，需要另派明确合同/窄范围配置准入适配与独立审查；本轮不实现此新身份机制，不提供绕过旧STOP的可执行实验命令。预算T0/截止不变；旧未知worker不能作0。真正派发前仍须按原1.508TiB历史代理、40GiB临时预留、成熟profile/退出尾及当时剩余日历预算再核可行；代理不能替代新实测。

实际CLI（AST核查，以下仅列出，不执行）：

```bash
python3 -B -u /home/ybc/projects/CL-FoReM-task9/forem/scripts/task9_11/prepare.py --protocol /home/ybc/projects/CL-FoReM-task9/forem/config/task9/task9_11/protocol.json --output /home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-lr-20261103T171820+0800/freeze
python3 -B -u /home/ybc/projects/CL-FoReM-task9/forem/scripts/task9_11/supervise.py --protocol /home/ybc/projects/CL-FoReM-task9/forem/config/task9/task9_11/protocol.json --phase smoke-and-gates
python3 -B -u /home/ybc/projects/CL-FoReM-task9/forem/scripts/task9_11/supervise.py --protocol /home/ybc/projects/CL-FoReM-task9/forem/config/task9/task9_11/protocol.json --phase train
python3 -B -u /home/ybc/projects/CL-FoReM-task9/forem/scripts/task9_11/audit.py --run /home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.11-lr-20261103T171820+0800 --phase development --output /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/future-development-descriptive
```

这些是精确的**现CLI阻断对照命令，不是获准续跑命令**：第一条旧freeze已存在应拒绝；第二/第三条原started与新SHA令不匹配应拒绝；第四条formal数据缺失应拒绝。均未执行，不用真实入口来证明拒绝。现CLI没有可直接使用的新namespace/单阶段host参数，不编造`--phase gate-evaluate`给host。worker实际单阶段合同：`python3 -B -u /workspace/scripts/task9_11/worker.py --arm L --seed 4718 --phase gate-evaluate --protocol /output/freeze/protocol.json --output /output/smoke-L-seed4718`，只能由经审host守卫在**未来授权的新续接身份**及对应`/output/releases/gate-evaluate-L-4718.json`下调用，当前禁止直接调用。准确protocol/output/release绑定尚缺，故不存在当前可执行的正式续跑命令，不能冒充READY。

F历史`supervise --phase final-test --release /review/development/release.json`中的通用--release不构成最终放行；实际每arm/seed worker读取各自releases令。audit输出是新目录且工具仅描述，不签独立PASS。以上差异待.6核。

## 准备交付 2026-11-03T20:55:44.145054+08:00

.5最终专用30项通过；.6从实际源码和原stderr独立复跑30项、自写7项，最终37项PASS。父已读正式FINAL-INDEPENDENT-VERDICT.json及其原命令/输出，核稳定源码71a2/0507/c9ee、全artifact ea27ea57…。阶段持久性/准入PASS与完整host/真实Docker尾UNKNOWN分开；原STOP不变、执行NOT_READY。本轮只完成准备和独立审查，等待正式执行派发，没有真实release。

独立FAIL原慢quiet→stop越cap与.5全部7次尝试保留；fixture自身清理误杀unittest rc−9亦原样留存。修复排他JSON半写可见竞争、路径/嵌套计费和完整25s固定timeout链，不把工程预留当真实OS/fsync上界。详SRC-1400。

父按最新原件补SOURCES1399–1401，更新父三文档当前状态、RESULTS §9预算、PROCEDURE J完整CLI/恢复合同。最小代码diff仅supervise/admission及新增纯标准库test，科学四配置/worker/训练/记录器/环境未改。旧4000/980与缺失历史退出/full wall原样保留；不把该失败当科学阴性。

预算最终时点20:51:20：worker下界3548.416307s、余仅上界205251.583693s；calendar余196019.629464s并继续减少，截止仍11-06 03:18:20+08。正式剩12M、smoke0、评估10788，存储/诊断按原硬限扣本轮输出，快照后的文档/核查成本另计而非0；原UNKNOWN仍在。详preparation-audit-final.stdout.json。

下一步：先明确完整host/prepare/续接身份及累计账本合同，独立裁决C科学原件复用而旧整门FAIL不改；没有合法新namespace绑定，当前不存在可以诚实交付的可运行正式续跑命令。未来实际G1/L ON/各自成熟profile/训练/一次test仍需正式派发和独立门；若要求C重测，现无额外196额度，不能挪评估。

最终必要保护/源码/原测试证据/三文档链接/进程/容器核验见preparation-final-verification.stdout.json及其-command.json（下步只读执行；此句写入时尚未执行，不预称通过）。没有本轮后台任务，不启停其他进程。

最终只读验收实际已执行 2026-11-03T20:56:39.613797+08:00：preparation_final_verify.py rc0/wall0.14220333099s；461旧保护项中仅授权2实现变化，160文件artifact一致；STOP7与独立裁决13证据SHA一致，原30/30/7结果核真；9文档本地链接无缺失、git diff --check0，无替身/本任务worker，旧容器仍exited/Pid0。此后仅补共享文档与.5父接受状态，不再改源码/证据。两子均结束，.5/.6准备done，父review等待派发，真实NOT_READY。全部实际写入：2实现+1纯stdlib测试；父及.5/.6三文档、PROGRESS、SOURCES、所属日志/原测试/审计/diff；不触碰其他任务。没有后台任务需停止或恢复。
