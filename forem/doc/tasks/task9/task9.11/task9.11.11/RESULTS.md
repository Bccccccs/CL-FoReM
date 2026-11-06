# task9.11.11 · 结果

> 最新为v2控制费用集中修复，artifact `c8523c9aecc314ce7ae0e71fd16e41ad9531aaf4e3e1315576ecd4d7411ef177` /168文件。独审发现v1 snapshot审核/发布漏费，原FAIL保留；v2专用35项及原反例同断言复跑PASS，父116项同源回归、独立130项加1次归档联合执行已核通过。下方旧v1 25项与8文件是历史，不再当最终整体通过；最新见本文末节。[SRC-1413](../../../../SOURCES.md#src-1413)。

状态 **done：父同SHA必要回归与.12独审原件已核；仅候选工程，真实NOT_READY**，本节点不自签最终通过。负责人Codex，请求GPT6.1sol/high，实际模型/推理后端UNKNOWN；Claude兼容推荐Sonnet5.5/high，因跨时间/前序/并发启动因果核验。授权沿[SRC-1412](../../../../SOURCES.md#src-1412)，方法与原件由父统一登记[SRC-1413](../../../../SOURCES.md#src-1413)；独审另归SRC-1414、真实预算/待决另归SRC-1415，不以台账替本三文档。[完整实施记录](../../../../agent_logs/task9/task9.11/task9.11.11/20261103-codex-cross-stage-implementation.md)。

## 版本与范围

稳定artifact `ae070d9978376fe6f9dd9213bc2b99a22dd7197e76b553b5f6f06f2ffd3e8068`、167文件。父freeze v1已核一致。原件：[implementation-ready.json](../../../../agent_logs/task9/task9.11/task9.11.11/implementation-ready.json)，含全部SHA与8个逐文件diff。

仅改admission.py、continuation.py、supervise.py、prepare.py；新增stdlib clock.py/costs.py与test_cross_stage_stdlib.py；按父明确补充授权，仅改test_contract既有deadline测试的clock接口兼容。worker/audit/runtime算法/科学配置未改。未运行真实Docker/GPU/模型/环境/仿真/回放/smoke/训练/科学test，科学G1仍14项但本轮不执行。

**legacy静态库存严格兼容**：新command仍拒绝；只有首prepare前显式冻结dynamic policy的新候选支持追加events/snapshot，不自动迁移原protocol或既有stage。新dynamic policy冻结允许根/schema/写者/独立budget reviewer，静态科学与路径身份不变；真实candidate仍false-execution。

## F1/F2实现关系

|需求|实现与本节点验证|限制/状态|
|---|---|---|
|新启动可信当前clock|生产admission默认clock服务；dynamic与真实原protocol拒caller clock；底层legacy synthetic纯parser测试入口保留|无任意caller时间授权生产启动|
|自然expiry不追溯CLOSED|原release SHA＋不可变reservation admission_capture＋outer实际wait completion_capture，核boot/generation/单调映射、原cap/expiry/绝对deadline/原累计stage额度；历史只读原snapshot及前序|不重签/改旧release/closure；新增坏snapshot不抹原闭账费|
|显式撤销单列|独立revoke事件，带原releaseSHA/reviewer/reason/issued_capture；资格拒绝，resource仍保留原CLOSED收费|不会用expiry当revocation，不删除原费用|
|时钟推进|fixture clock anchor在prepare前冻结，仅temp canonical false-execution可用；跨进程append-only generation/hash前序正向推进|真实系统time/deadline未改|
|动态费用|实际stdlib子进程wait测wall；source argv/实际exit/闭封起讫capture，event唯一ID/stage/source path+SHA/finitewall；journal保护追加记录|未审/UNKNOWN/缺失/extra/篡改/越界/重复/未闭封拒绝，不以0核销|
|nested去重|同run/stage，父子完整时间区间包含且无循环/缺父；仅最外层charge|明确synthetic嵌套样例，不外推真实历史成本|
|独审snapshot|固定预算reviewer `task9.11.12-cost-reviewer`，不同writer；version/prev hash/commit、review起讫/expiry、全roots与事件journal coverage、生产全资源核算；release绑最新hash|原release证据reviewer仍沿旧`.10`，角色不同；无真实release|
|追加/审核/启动竞争|thread-aware重入＋跨进程flock；dispatch reservation与guard最后实际worker.Popen临界区共锁；guard锁内重验release/current snapshot/resources/launch，随后Popen+started|不跨worker wait；原worker.main重复生产准入；运行检查读current费用|
|协议/旧件不可变|追加独审费用、新snapshot及下一有效release后，protocol/旧release/旧closure SHA全部原样；幂等零启动/零增费|不自动放行旧C/历史UNKNOWN/控制包络|

## 原始验证

[开发同SHA25项命令](../../../../agent_logs/task9/task9.11/task9.11.11/cross-dev09-command.json)，argv `python3 -B forem/src/task9_lr/tests/test_cross_stage_stdlib.py`；rc0、wall **9.1771049686s**，source_before=source_after且对应上述artifact。原[stdout](../../../../agent_logs/task9/task9.11/task9.11.11/cross-dev09.stdout.txt)/[stderr](../../../../agent_logs/task9/task9.11/task9.11.11/cross-dev09.stderr.txt)。这不是科学test，也不代替父同SHA完整回归与独审。

联合正向实际走生产prepare→dispatch→实际worker.main二次load/release/prereq/resource/ledger→actualwait/CLOSED；fixture clock推进3600s，越旧release 2400s有效期与旧snapshot 600s有效期但仍在原总deadline内；实际有界stdlib独审核子进程wait wall **0.0735155977s**、exit0，source与event登记，旧snapshot stale拒绝；独立预算角色审核发布第二版snapshot，新有效stage release后gate-evaluate-L成功；累计费用新增一次。历史读取/幂等返回不inspect、不启动、不重复收费；原protocol/release/closure SHA不变。原临时目录已由fixture清理，永久raw保存SHA与收费摘要，不将已清理temp路径冒永久原件。

25项另覆盖：过期未启动/caller假clock、closure completion映射篡改/原stage原finish越界、显撤但保费、额外command未event/未审、event/source双重唯一、缺wall/未知/改源/丢失、根越界、snapshot expiry/缺代/改值、未审extra event及event+source双删、nested包含和越界、总deadline/预算不足、未闭command pending阻断、真实CLI拒candidate。线程同source并发只有一个成功且仅一次收费；真实子进程持cost.lock与dispatch竞争，新费提交后stale拒启动。RaceBackend确定性在原最后resources后、launch-ack前添费，最终guard拒绝：ack存在，worker-started/launched不存在，精确stopped、无CLOSED。

原失败全部append-only保留：cross-dev01/02因fixture短release不容原1800s save reserve各3 ERROR；dev04真实review子进程导入路径缺失exit1造成1 FAIL，后补显式src路径。dev03/dev05–08均是不同开发源PASS，不拼为最终证据。lifecycle-dev01旧14项开发PASS但最初自写runner source摘要路径有误为空，**不作最终同SHA证明**；后续由父run_evidence保存完整before/after。完整失败列表/命令/rc/wall见实施记录和本节点原件目录。

## 交接与剩余事项

父负责统一freeze v1及25+40+14+15+12必要标准库回归，.12稳定源后独立自写反例，父直接核raw/证据/单文件SHA，不以本节点自报通过；若发现同范围FAIL由父集中派回，本节点重新修、重新统一freeze。本节点现只写文档，不改稳定源码。

真实历史UNKNOWN/旧C完整性FAIL、有限会计边界与控制包络、真实获批execution protocol/release仍待用户决定；旧4000smoke/980eval/formal0/test0、smoke余0、10788=196 L ON+9408formal+1184final、extra C ON0、原T0/58h/2TiB与绝对deadline不变。本轮fixture完全独立虚构账，不能核销真实UNKNOWN，也不证明真实预算/工期可行。所有真实准备/审核/等待仍由父原始成本快照累计。[SRC-1415](../../../../SOURCES.md#src-1415)。

## v2 · 独审F2漏费集中修复

独审原件[review-cost-v1命令](../../../../agent_logs/task9/task9.11/task9.11.12/independent-review-cost-v1-command.json)、[原反例脚本](../../../../agent_logs/task9/task9.11/task9.11.12/independent_review_cost_check.py)保留：v1没有stage，review自身实际正墙钟却cumulative.worker103→103，不能由不存在的stage control包络覆盖。父集中派回此同范围修复；没有改原FAIL断言。v1旧106项PASS只是历史局部回归，不再声称F2整体完成。

v2仅在既有范围新增stdlib `cost_control.py`，总9必要文件diff，原稳定v1原件不覆盖。[v2 manifest](../../../../agent_logs/task9/task9.11/task9.11.11/implementation-ready-v2.json)记录artifact `c8523c9aecc314ce7ae0e71fd16e41ad9531aaf4e3e1315576ecd4d7411ef177` /168文件及v2逐文件diff。源码停止修改，父统一freeze v2与必要回归、独审进行中。

三个独立控制session明确分列：`source-publish`、`event-append`、`snapshot-review`（含校验、snapshot/commit发布与尾）。各沿**既有候选30s包络全额收费一次**，不是将实测微秒包装上界；每项明确`engineering-upper-bound-pending-approval`、`applied:false`。payload实际子进程wait墙钟另列；nested payload按原完整包含关系计最外层一次。初次review无stage也收30，第二版review自身费用直接计入该版，不推给下版。既有stage控制session仍独立，不拿stage费补元数据漏项。

控制证明为immutable reservation/control-journal→SHA绑定source/event/snapshot或明确denial artifact→completion receipt。当前完整库存累计每个全额控制reservation，pending/rejected/缺证据/盘错/超包络不作0；控制目录整体丢失仍由journal拒绝。普通审核校验拒绝可封一个有限denial session并保费，source/event未知仍阻断；publication开始后的失败保pending UNKNOWN，不把不确定snapshot补作完成。真实睡眠注入超包络、snapshot写失败/commit后失败、source/event发布失败均拒；旧snapshot前序及原费用仍可历史读取，坏新版本不能抹旧费用。

新增路径沿旧root规则核canonical：control根/目录/文件与artifact引用均拒symlink/越界，写前核source/event/snapshot允许根；不是另设安全系统。cost.lock采用LOCK_NB轮询原绝对deadline减原save reserve，保同线程递归与跨进程串行；已实际另一进程持锁且不释放，等待dispatch期间fixture推进60h，等待方在1s内退出拒绝而holder仍活着。没有改总deadline/保存预留或新增真实timeout参数。可立即取得历史锁时，历史快照读不因当前deadline追溯失效。

[最终开发同源35项](../../../../agent_logs/task9/task9.11/task9.11.11/cross-dev16-command.json)rc0、wall **11.4302352127s**，source_before=source_after并对应v2 artifact；[stdout](../../../../agent_logs/task9/task9.11/task9.11.11/cross-dev16.stdout.txt)/[stderr](../../../../agent_logs/task9/task9.11/task9.11.11/cross-dev16.stderr.txt)。联合正向保持完整生产链/fixture推进/旧件SHA不变，新增payload实际wait **0.0755483657s**，source/event/review三个独立metadata控制费用合计**90s**，各一次；下一stage自身原job＋stage control另计。仅改必要费用期望，仍明确核每个receipt、operation和snapshot总账，未放宽为仅大于某下限。

原独审脚本未改的[同断言复跑](../../../../agent_logs/task9/task9.11/task9.11.11/independent-review-cost-recheck-v2b-command.json)rc0、wall **0.2646293454s**。原[stdout](../../../../agent_logs/task9/task9.11/task9.11.11/independent-review-cost-recheck-v2b.stdout.txt)记录：无stage/无event，review实际区间0.0111560151s、整调用0.0147615317s，cumulative.worker **133→163，增30s**，不是0。该30为未批准工程候选全包络，不称实际耗时。

开发失败保留：cross-dev10有2 ERROR（nested helper变量名与新拒绝review费用状态适配），dev11后25 PASS，dev12 31 PASS、dev13/14 34 PASS、dev15 35 PASS均开发信息；最终只用dev16同源35与原反例v2b，父后续同SHA回归/独审另核。不拼不同源码PASS。所有真实禁止、旧C FAIL/历史UNKNOWN、原分配与总期限均沿上文不变。[SRC-1413](../../../../SOURCES.md#src-1413) · [SRC-1414](../../../../SOURCES.md#src-1414) · [SRC-1415](../../../../SOURCES.md#src-1415)。

## 父最终验收（v2，同一冻结源）

父已逐件读生产调用链/原输出，接受.12正式裁决158引用、101份全联合原件SHA和168稳定源。正式裁决SHA `e93698b5e58752829e2066a0990e077f5904f7b1f9870a93f9f426f0ce32636c`；父116项rc0、独立130项rc0加一次归档联合执行，全部before/after对应c8523c9a…11ef177。见[父核验清单](../../../../agent_logs/task9/task9.11/task9.11.11/parent-independent-acceptance-v2.json)、[最小diff](../../../../agent_logs/task9/task9.11/task9.11.11/minimal-v2.patch)、[独立RESULTS](../task9.11.12/RESULTS.md)及[父最终矩阵/预算/剩余合同§15](../RESULTS.md#15-f1f2跨阶段联合修复与独立交付2026-11-03)。本节点done仅指工程交付，无真实许可。旧版本进行中/待核文字是历史时点。

精确回归argv/源码before-after/raw/rc见本日志目录final-v2-cross/supervision/lifecycle/continuation/entry-audit-command.json；相应项数35/40/14/15/12，wall12.1319039/10.2783379/38.7688702/1.1161295/.6650919s。初次父汇总路径错误rc1后仅汇总脚本修正rc0，原失败保留。真实预算/UNKNOWN与用户合同集中见父§15和SRC-1415，不能用虚构账替真实核销。[SRC-1413](../../../../SOURCES.md#src-1413) · [SRC-1414](../../../../SOURCES.md#src-1414)。
