# task9.11.9 · 集成修复结果

状态done（本轮集成修复与独立工程验收交付；真实NOT_READY）；负责人Codex。请求主设计/实施/独审GPT6.1sol/high，父实际后端/强度未知；兼容推荐Sonnet5.5/high，理由为跨进程生命周期、身份和会计合同审查。授权[SRC-1407](../../../../SOURCES.md#src-1407)，证据[SRC-1408](../../../../SOURCES.md#src-1408)，成本与待决定项[SRC-1409](../../../../SOURCES.md#src-1409)。

本轮零模型、零环境、零真实Docker控制；没有仿真/回放/smoke/训练/最终test，未重启旧run、移动旧PASS、修改科学配置或旧原件。只改四入口脚本、admission、必要新continuation及专用测试。

## 需求—实现—验证—证据—未解决项

|需求|最终实现|验证/裁决（候选替身范围）|原始证据|未解决项|
|---|---|---|---|---|
|R1 G1入口冲突|worker.g1_test_command仅显式test_contract.py；rootdir/confcutdir固定，继承pytest选项/插件清除；stdlib直接python独立进程，禁导入断言不删不skip|PASS：实际argv/AST及传递导入隔离，静态预计14科学项；没有跑GPU科学套件|[父12项](../../../../agent_logs/task9/task9.11/task9.11.9/entry-final-v3-command.json)、[收集清单](../../../../agent_logs/task9/task9.11/task9.11.9/entry-final-v3-collection.json)|真实G1留获批阶段|
|R2正常无法闭账|production prepare→dispatch→owner→guard/watch→实际worker.main二次load/release/prereq/resource/ledger→actual wait；独立candidate closure完整SHA链，job与控制费用分列，旧PASS不得充closed|PASS：合法准备/完成/后继、14stage完整DAG；同请求adapter重复零启动/零重复费用；CLOSED从production activity_rows/check_resources读取|[父14项](../../../../agent_logs/task9/task9.11/task9.11.9/final-v3-lifecycle-command.json)，[.9.1 RESULTS](task9.11.9.1/RESULTS.md)|有限会计边界/控制包络只是待批准非执行候选；真实格式不放行|
|R3异常封口|outer wait异常统一停止/精确回收或UNKNOWN；原cap内预留停止尾；watcher直接监测真正outer身份；pending/rejected均拒；发布/最后unlink超包络撤销候选|PASS：四resources竞态无worker标记；outer超时/死亡、guard故障、损坏/identity失败/盘错/缺receipt；独审已持久化rejected的复合盘错反例修复后PASS|[父40项](../../../../agent_logs/task9/task9.11/task9.11.9/final-v3-supervision-command.json)、[独立反例4](../../../../agent_logs/task9/task9.11/task9.11.9/final-v3-independent-counterexamples-command.json)、[复合盘错1](../../../../agent_logs/task9/task9.11/task9.11.9/final-v3-compound-disk-command.json)|主机断电、所有监督死亡或全部deny/rejected写入及撤销都不可持久化，不能保证终态；须外部恢复隔离UNKNOWN。真实Docker尾未知|
|R4合法续接累计账|prepare/continuation→production protocol/evidence/read_release/prerequisites→host jobs/worker同schema；显式host/container映射；旧科学仅REFERENCE_ONLY；全部准备/独审根递归清单+原账继承，UNKNOWN不为0|PASS：15项与完整DAG；旧FAIL/PASS/新SHA/namespace/reviewer/过期令混用、漏外部成本、预算溢出、重跑smoke/额外C ON均拒|[15项](../../../../agent_logs/task9/task9.11/task9.11.9/final-v3-continuation-command.json)、[实际candidate CLI](../../../../agent_logs/task9/task9.11/task9.11.9/final-v3-prepare-command.json)、[实际refreeze](../../../../agent_logs/task9/task9.11/task9.11.9/final-v3-refreeze-command.json)，[.9.2 RESULTS](task9.11.9.2/RESULTS.md)|真实旧C完整门仍FAIL，历史账未闭合；执行schema/release只在决定后另签，不接受candidate true或fixture冒实账|
|R5双侧配对|paired两侧唯一；全部12checkpoint各域100/96与final200/96、预期独立冻结身份/role/source/stream检查后统计；先按filename核配置SHA再核arm/seed|PASS：双侧重复/缺失/额外/错域角色、冻结种子/manifest篡改及C/L配置替换均拒；正常全量纯JSON仍可统计|父12项及独立4反例同v3；audit.independent_release恒false|描述性audit永不替独立release；manifest预封存真实性仍由独立门负责|

## 冻结源码、最小diff及命令

HEAD d198e5ca48f86071c05274f9da753f393ce058b4加保留dirty。**最终artifact SHA256 `1ba4e9891aa0aa53814fec9eee9064300da6f23a6240a56938d75e230c9105b1`**，164文件；[完整清单](../../../../agent_logs/task9/task9.11/task9.11.9/final-source-freeze-v3.json)、逐字节snapshot `frozen-source-v3/`、[diff索引](../../../../agent_logs/task9/task9.11/task9.11.9/integration-diff-index.json)。原160保护仅6个授权文件变化，新continuation与3个专用stdlib测试；训练/环境/奖励/观测/终止/候选/动作/LR定义未改。test_contract仅把已失效prepare预期更新为候选禁止真实创建，不删科学测试项。

|生产源码|SHA256|
|---|---|
|scripts/task9_11/worker.py|`3daa37c8ba43dcdaacbf7c9be87d78795ac3756db0da1286239273bf612fb121`|
|scripts/task9_11/supervise.py|`89683a51f32b487197bd9d6996bb54770e8be83598ba60c85eeb7d89bc059ac3`|
|scripts/task9_11/prepare.py|`0e6cd5a6a7fc9099ee544022069a91f399857f5553713281e10d4f96fd87bb44`|
|scripts/task9_11/audit.py|`ee1e9ae40d32c656eb11a45edaccf5f1c117f2e0881473b1b239a06433b1faf2`|
|src/task9_lr/admission.py|`99d995f77406a8caa9bc4911610f28d9c779a5876cbb43f65e02b4b49f181281`|
|src/task9_lr/continuation.py|`8e2b308bbc292f5b9a2bf7d09c9aca7d09e559804b6b0a4c1bda876af9619bac`|

所有命令cwd `/home/ybc/projects/CL-FoReM-task9`；原命令JSON、stdout/stderr、退出码、wall及before源码清单位于 `.9/`，不是从聊天推断结果。下面均实际执行，前四合计81项，父另复跑独审5反例和兼容11项，均rc0：

```sh
python3 -B forem/src/task9_lr/tests/test_supervision_stdlib.py
python3 -B forem/src/task9_lr/tests/test_lifecycle_candidate_stdlib.py
python3 -B forem/src/task9_lr/tests/test_continuation_stdlib.py
python3 -B forem/src/task9_lr/tests/test_entrypoints_audit_stdlib.py
python3 -B forem/doc/agent_logs/task9/task9.11/task9.11.10/independent_identity_checks.py
python3 -B forem/doc/agent_logs/task9/task9.11/task9.11.10/independent_compound_disk_check.py
python3 -B forem/doc/agent_logs/task9/task9.11/test_continuation_proposal.py
```

实际运行通过 `.9/run_evidence.py LABEL 上述命令`保存，最终标签final-v3-supervision/lifecycle/continuation、entry-final-v3、final-v3-independent-counterexamples/compound-disk/proposal-compat。完整套件不经pytest/conftest；临时fixture为独立虚构账，不是把真实历史UNKNOWN填0。

独立.10直接读源码和原输出、另写反例；v1配置替换、末unlink超包络、无adapter已CLOSED候选及v2复合盘错FAIL均保留。修后v3统一重跑，不能拿v1/v2 PASS代签v3。最终独立裁决见[.10 RESULTS](../task9.11.10/RESULTS.md)及[正式JSON](../../../../agent_logs/task9/task9.11/task9.11.10/FINAL-INDEPENDENT-VERDICT.json)。父已直接核54份证据SHA、六套原stdout/stderr/rc与before/after源清单，共86项最终独立PASS；[父接受原件](../../../../agent_logs/task9/task9.11/task9.11.9/parent-independent-acceptance-v3.json)。

## 有限生命周期与状态

状态/写者/读者、身份及所有后继合同已在[实施前冻结v1](../../../../agent_logs/task9/task9.11/task9.11.9/frozen-contract-v1.md)与父日志逐项列明：prepare写PREPARED freeze；dispatch写RESERVED；guard写worker-started/result且实际收割worker；watch写PASS/FAIL record+terminal；owner实际wait guard、guard实际wait watch；outer实际wait owner并核全部receipt后写候选CLOSED。active marker的phase/arm/seed、nonce、run/protocol/code/release SHA、PID/startticks和waiter贯穿读取。失败/缺证/未闭账/旧格式PASS均阻断。CLOSED只候选有限会计政策接受；真实CLI/无adapter dispatch/DockerBackend/worker入口先拒candidate，包括已有CLOSED幂等分支。

被测job边界=紧邻owner Popen前的launch witness→实际owner.wait返回；子进程费用不叠加。预约、检查、发布和控制成本另列；候选控制session全额计其明确包络（fixture/CLI示例30s），不是实测上界或已批准真实参数。发布与最后unlink都核超额，失败保pending/rejected或撤销closure；有拒绝证据禁止后续准入。不继续新增外层以证明外层自己退出。原lifecycle.outer退出/真实发布尾UNKNOWN不删除。

## 累计预算与成本边界

[预算原件](../../../../agent_logs/task9/task9.11/task9.11.9/budget-final-v3.stdout.txt)/[命令](../../../../agent_logs/task9/task9.11/task9.11.9/budget-final-v3-command.json)，时点 **2026-11-03T22:44:06.859666+08:00**，随后继续扣减；不是release余额。脚本只读JSON/hash/stat，模型仅stat。

|项目|事实/推导及限制|
|---|---|
|科学消费|smoke4000、评估980、正式0、最终test0；smoke余0；余10788=196 L ON+9408正式+1184最终，额外C ON余0|
|worker|已知命令/区间下界4010.8964954s，其中新增集成命令369.0022770s（含失败与独审）；原208800相减仅得余额上界204789.1035046s；exact=null|
|日历/GPU|原T0/截止不变，日历余189253.1403344s；旧容器保守GPU暴露7252.5301979s，余上限201547.4698021s。本轮实际新GPU消费0|
|存储|逻辑33993041737B、唯一inode22916595649B、诊断859725837B；2TiB余2165030213815B，8GiB余7730208755B；另保原40GiB保存包络|
|可行性|4×12h正式+4h最终是原阶段上限情景187200s（52h），日历仅余2053.1403344s（约34.22min）给G1/LON/准备/独审/排队/退出和UNKNOWN。不能证明完整方案装得下；不是声称实际必耗满52h|

历史host/完整发布退出尾、未计监控及部分准备/审查会话与当前发布尾继续UNKNOWN；命令实测下界不冒充完整会话实耗，也不把未命令化Agent工作记0。全局calendar已经包含等待，新外部command inventory必须逐次补全；freeze产物后又有审查命令即过期，当前只review快照，不能充未来余额。当前worker未知与未来成熟profile/真实Docker成本缺口均真实阻断。

## 待决定、下一入口和交接

1. **旧C承接**：推荐只读保留旧C科学原件（196行/4807事件，仅该轨迹支持非干扰），结合新生命周期候选/获批真实门作为新组合验收；旧C完整门FAIL不改。此为原整门验收差异，未应用。坚持重测C ON则当前无额外196额度，不能继续。
2. **会计边界**：是否批准有限job实际wait＋另计控制session，和真实控制成本取值/上界证据。本轮30s只fixture与纯CLI示例，不是已核真实尾时或实验限额。
3. **旧UNKNOWN处置**：优先恢复原actual wait原件；不可恢复时，可请用户决定按旧C已释放cap1800s全额核销该失败尝试，替换625.185549736s下界一次（差1174.814450264s）。这是待批准记账约定，不是经证明实际wall上界/exit0；有更高实证不得下调，其余UNKNOWN不被此一核销吞并。无证据外包络的历史准备仍不能放行。
4. **真实后续**：合同处置后生成获批execution protocol/new namespace与实时累计账、独立code/release；再获派新代码G1、L ON196、各run成熟250k/profile→remaining全预算可行性，最终仍一次独立test。不能因替身PASS启动部分实验、缩步/跳评估/延时或晋级task10。当前实现刻意只接受candidate与synthetic fixture，真实execution adapter/release不签。

本轮可重复的准确纯准备入口（下列已执行的输出目录不可覆盖，重跑换新的review目录）：

```sh
python3 -B forem/scripts/task9_11/prepare.py --continuation-candidate forem/doc/agent_logs/task9/task9.11/task9.11.9/final-continuation-proposal-v2.json --output forem/doc/agent_logs/task9/task9.11/task9.11.9/final-candidate-freeze-v3 --proposed-control-envelope-s 30
python3 -B forem/scripts/task9_11/prepare.py --candidate-protocol forem/doc/agent_logs/task9/task9.11/task9.11.9/final-candidate-freeze-v3/protocol.json --output forem/doc/agent_logs/task9/task9.11/task9.11.9/final-candidate-refreeze-v3
```

这两个CLI只在review日志冻结，不创建提议真实results/logs namespace，不释放worker。候选host DAG已实现：g1 C4718→gate L4718→C4718/L4718/C4719/L4719各profile→remaining→开发独立release→四actor一次final。无四smoke重跑、无额外C ON。旧科学证据只REFERENCE_ONLY，旧PASS/STOP/release不复制。

下一派发可直接引用本整体矩阵/稳定SHA/独审原件，避免再次拆R1–R5局部修补；仍必须先定上述合同并建立获批执行schema与独立阶段令，再做真实阶段预检和成熟profile，不能承诺不需任何后续准备或直接开训。当前负责人父Codex，.9.1/.9.2已停写，.10只独审；没有本轮持续后台任务。交接读本三文档、父RESULTS最新节与.10裁决，不靠聊天恢复。

父接受补注 2026-11-03T22:48:48.791274+08:00：本轮工程集成与独立验收done，真实NOT_READY。最终统一v3 artifact `1ba4e9891aa0aa53814fec9eee9064300da6f23a6240a56938d75e230c9105b1`；父81项及独立86项、54引用SHA均从原件核验，早期版本PASS不迁移。task9.11.9 RESULTS为本次事实汇总，旧C/历史UNKNOWN/预算/截止不变。来源SRC-1408–1410，父负责共享来源登记。

## 交接末次成本快照（追加，不改历史快照）

时点 **2026-11-03T22:49:17.558635+08:00**，[原stdout](../../../../agent_logs/task9/task9.11/task9.11.9/budget-handoff-v3.stdout.txt)/[实际命令rc0](../../../../agent_logs/task9/task9.11/task9.11.9/budget-handoff-v3-command.json)。worker下界4011.0108699s，其中新增命令下界369.1166515s；余仅上界204788.9891301s，exact=null。日历余188942.4413650s，原52h阶段上限情景后仅1742.4413650s（29.04min），仍不能证明全方案可行。逻辑33993182306B/唯一inode22916736218B/诊断859866406B；输出余2165030073246B、诊断余7730068186B，原40GiB临时保存包络保持。快照自身命令及其后收尾继续发生，不按0；全部历史/完整会话UNKNOWN保留。

15份任务三文档递归/链接/source锚点与git diff --check0已核：[文档原件](../../../../agent_logs/task9/task9.11/task9.11.9/documentation-final-check-v3.json)。独审正式54引用与父接受记录均保持原SHA；源码未再改。

末次预算经独立[九项核验](../../../../agent_logs/task9/task9.11/task9.11.10/final-budget-handoff-review-v1.json)PASS，未改原正式裁决。父[最终交付完整性](../../../../agent_logs/task9/task9.11/task9.11.9/final-delivery-integrity.json)于22:50:46+08再次核统一artifact、独审verdict SHA、预算review SHA、15文档链接、gitdiff0及无替身进程，PASS；真实NOT_READY不变。
