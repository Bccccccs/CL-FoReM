# task9.11 F1/F2跨阶段集成修复

开始2026-11-03T23:11:10.673033+08:00，父Codex，实际模型/强度UNKNOWN；主修复与独立审查请求GPT6.1sol/high，兼容推荐Sonnet5.5/high（跨时间与账本前序因果审查）。用户最新授权只修F1/F2必要admission/continuation/supervise/prepare接口及专用测试、零模型零环境零真实Docker替身、独审与文档。禁止真实模型/GPU/仿真/回放/smoke/训练/test/旧run恢复/旧原件改写/预算截止重置/科学条件变更，不签实验许可。

已核根与forem AGENTS、README/PROGRESS、父及.9/.10三文档、integration-review与verification、SRC1408–1411。最大活动号.10，新增稳定.11实施与.12独审，不复用旧号；旧sol会话均已结束。工作树codex/task9-lower-improve、HEAD d198e5ca48f86071c05274f9da753f393ce058b4，原dirty全部保留。现场无task9运行；task10在独立树运行，禁止干预。

## 冻结修复合同 v1（先于实施）

沿用已测R1/R3/R5、有限job actualwait和候选控制包络、真实入口硬拒candidate；不重做设计、不批准旧C/会计/历史UNKNOWN/真实execution合同。

F1：生产新启动以可信当前时钟验证release有效期/身份/证据/预算；CLOSED历史改为验证SHA绑定的原始release与不可变reservation、outer实际wait见证的启动/完成时间、cap和绝对deadline，原令自然过期不撤销既有完成/费用，幂等不得启动/重复计费。显式revocation是独立可审事件，不重用expiry。拒绝未启动已过期/越截止/身份或SHA不符/缺时间证据。历史时间必须来自生产监督实际启动/actualwait记录及同一时钟域/可靠单调映射，禁止调用方任选clock或closure字段自证。替身时钟只经被静态绑定的temp synthetic fixture时钟服务推进，不mock准入/时钟判定/计费函数，不影响真实系统time或真实截止。

F2：静态科学/路径/身份/协议SHA不可变；动态成本以append-only有唯一事件ID、所属stage、可信source command路径+SHA、finite实测wall、嵌套父子/去重关系、允许根/格式的事件账本，和独立审核的版本化hash前序预算快照承载。下一stage release绑定最新已审snapshot及历史前序；旧protocol/release/closure逐字节不变。唯一计费、完整coverage；unreviewed、未知wall、篡改/丢失/重复/根越界/并发未完整追加/快照过期或新增费用后的stale snapshot/超限拒绝。不得忽略额外command文件或弱化hash/把UNKNOWN当0；真实旧UNKNOWN继续阻断，正向只用明确synthetic独立虚构账。若外部prepare/review命令尚在执行未闭封，其未测成本保持UNKNOWN且下一启动拒绝，不能通过忽略当前review来做fixed point。

联合验收必须真实production prepare→dispatch→worker二次load/release/prereq/resource/ledger→actualwait→CLOSED；推进fixture clock到旧令过期且总deadline前→在声明root新增合法review command/cost event→独立审核/新版snapshot/新有效stage release→下一stage成功→累计增费一次→历史读/幂等零启动零增费→旧protocol/release/closure字节hash不变。除Docker/模型/环境/底层时钟替身外，不能mock本轮验证的生产函数。故障矩阵覆盖用户所有F1/F2反例，并核已通过启动/故障监督和R1/R5按改动必要回归，旧结果仅历史不充新SHA。

唯一写者/读者：prepare冻结static protocol/config/input/允许成本schema；external command owner发布不可变原测command envelope；事件写者以exclusive append/串行锁绑定event_id/source/stage/parent和SHA；独立reviewer读全roots与events/coverage并写immutable snapshot（version/prev hash/审核身份/有效期/累计费用与剩余）；新release写者绑定该snapshot。dispatch读当前时钟、最新snapshot/release和前置资格后RESERVED；worker重复生产准入；outer实际wait后写CLOSED历史证明。活动/成本snapshot/显式revocation分开；历史闭账读取不按当前expiry重签，不允许旧FAIL/UNKNOWN变CLOSED。

并发：cost append/review/start必须共享可核generation/锁约束；snapshot完成后新事件立即stale，启动不得用旧余额。运行期资源检查纳入已审新增成本，未审/未知则有界停止或UNKNOWN；不把历史费用删除。成本nested不得既加外层又全加子层；同source/event重复拒绝或幂等引用但不重复计费（具体格式由主修复先报告，冻结补注，不降验收）。

|需求|实现|验证|证据|未解决项|
|---|---|---|---|---|
|F1历史资格|release-start与completion-proof分离、可信时钟/actualwait、revocation|时间推进后历史/后继/运行resource/幂等仍合法；过期未启/原超限/篡改/显撤拒绝|.11与.12原件|不批准真实会计合同|
|F2动态成本|静态protocol＋追加事件＋独审预算snapshot前序|新增费用一次、全roots覆盖、旧件字节不变；并发/stale/篡改/未知/越界/预算不足拒绝|.11与.12原件|真实旧UNKNOWN不核销|
|F1+F2联合|同生产调用链/同冻结SHA|旧令过期＋新增独审费用后正常下一阶段，非仅全部拒绝|.11/.12联合闭环输出|无真实性能/实验许可|

资源科学不变：旧4000smoke/980eval/formal0/test0；smoke余0，10788=196L ON+9408formal+1184final，额外C ON0；T0=2026-11-03T17:18:20+08，deadline=2026-11-06T03:18:20+08，58h/2TiB/8GiB及40GiB保存包络不重置。B1/B1-L两seed各3M，仅actor/critic LR日程变；不加包装、不升级task10。所有准备、失败、独审/等待继续计费，旧快照不是可用余额，未知不为0。

预算/可行性：本轮开始已晚于旧22:49快照，52h是原formal+final上限情景非性能承诺；实时核算后报告缺口，不能缩步/跳评估/延时/启动部分真实实验。

## 执行安排

.11单一sol/high负责F1/F2联合实现，避免跨写边界失配；只写四必要core脚本/模块、必要新stdlib时钟/成本module与专用测试及自身文档日志，不改worker/audit/科学配置/运行时算法（若必要先说明最小接口原因由父核范围）。.12另一sol/high稳定源码后只读独审，自写时间/新费用反例不改实现。父设计合同/核原始证据/来源/预算/共享文档；旧三Agent不自动继续。

所有新验证尚未执行。
