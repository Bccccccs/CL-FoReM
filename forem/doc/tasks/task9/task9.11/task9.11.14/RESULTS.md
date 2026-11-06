# task9.11.14 · 结果

当前done（独立候选工程验收；真实NOT_READY）。以下尚未执行/active文字保留历史准备时点，以文末最终同SHA裁决为准。

负责人Codex独审；开始2026-11-04T09:23:00.481592+08:00。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因设备区间、跨阶段费用与准入因果核验；本次委派请求GPT6.1sol/high，实际后端/强度无法独立核验，记UNKNOWN。授权来源[SRC-1419](../../../../SOURCES.md#src-1419)。

范围：仅自身三文档、日志、独立stdlib检查；生产代码与其他节点只读。仅CPU/替身时钟/占位进程，不加载模型、不控制真实Docker、不运行GPU/仿真/回放/smoke/训练/最终测试。旧STOP、C FAIL、UNKNOWN、58h/2TiB及原截止不变。

输入旧artifact c8523c9aecc314ce7ae0e71fd16e41ad9531aaf4e3e1315576ecd4d7411ef177/168文件；新SHA待冻结，旧通过不可移作新验收。

## 首冻独审（不是最终验收）

`db02314ef8bb6e92e31755db9ece7a7db1d0b328d56df60111ec2d9f91175b7a` /170源下，旧F1/F2独立8、审核费1、控制故障5与GPU生产12项通过，但独立已审container证据反例FAIL：start后移5s使GPU119.9999997616→114.9999997616仍被接受；缩短Stopped、删record、双改allocation CPU[]均未拒。原expected-reject断言/raw/脚本快照及完整fixture全部保留，**首冻不通过**。见[反例命令](../../../../agent_logs/task9/task9.11/task9.11.14/container-tamper-v1-command.json)、[三变体](../../../../agent_logs/task9/task9.11/task9.11.14/container-tamper-variants-v1-command.json)、[记录](../../../../agent_logs/task9/task9.11/task9.11.14/20261104-codex-gpu-accounting-review.md)。来源[SRC-1421](../../../../SOURCES.md#src-1421)。

own13另有三种fixture ERROR，未当实现失败：已过期snapshot expiry、active读缺原nonce、release预算超过已审snapshot余额；均只修自身setup、保原断言/失败。中间源beb59123非最终冻结，另复现staticlegacy缺immutable时间基底未UNKNOWN，已交父集中修复。最终20独立GPU项及旧14独立断言、生产GPU套件需同新冻结SHA统一重跑，不拼版本；当前仍active、真实NOT_READY。

## 最终独立裁决（v3源，2026-11-04）

**候选工程验收PASS；真实NOT_READY。** 冻结170源`0bbda355c9eaf3018b7f73a27fc033e346dc06d7c0b2b940d1334fce7476c1a9`，五组53项及1项拒绝审核费补核全部rc0且sourcebefore=sourceafter=该SHA。正式[裁决](../../../../agent_logs/task9/task9.11/task9.11.14/FINAL-INDEPENDENT-VERDICT.json)与[独立hash/费用核验](../../../../agent_logs/task9/task9.11/task9.11.14/final-verification.json)由父逐件复核；依据[SRC-1421](../../../../SOURCES.md#src-1421)。请求GPT6.1sol/high，实际后端/强度UNKNOWN；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因为跨进程时间域、历史资格与GPU区间去重必须联合推导。

|本日志目录原件标签|项数|rc|wall s|
|---|---:|---:|---:|
|gpu-independent-final-v5|23|0|14.735414967|
|prior-f1f2-final-v3|8|0|8.425948063|
|review-cost-final-v3|1|0|0.264324769|
|control-final-v3|5|0|1.015486691|
|gpu-production-final-v3|16|0|9.728261724|
|denial-reconciliation-final-v3（原归档补核）|1|0|0.164298613|

每组`*-command.json`含exact argv/cwd、sourcebefore/after、脚本副本、raw stdout/stderr SHA/rc/wall。own23最终原始树在`raw-fixtures/gpu-independent-final-v5/`，每项单独manifest保SHA与原绝对路径；旧F1/F2正向另归档101件。父132标准/专用回归独立核验，不能拿本节点重复专用16冒新增科学证据。

|场景|worker已用 s|GPU已用 s|GPU预留 s|实际核对结果|
|---|---:|---:|---:|---|
|CPU联合首stage闭账|163.916344944|110|0|原protocol/release/closure/snapshot四件SHA不变|
|旧令过期后真实CPU审核＋source/event/新snapshot|253.929333551|110|0|增90.012988606＝payload0.012988606＋三control90；GPU未增|
|新release后actual worker后继闭账|284.945996674|110|0|两stage生产二次准入/资源检查/ledger/CLOSED齐全；幂等启动0、重读不增费|
|GPU持有运行中active|163.654637575|115.739117146|3.345362425|worker余预留33.345362425，差30为CPU control；cap4没有丢失|
|原余额边界新CPU后|2043.980023175|206801.428753376|拟申请4|worker拟申请34；旧式208858.441374越208800，新式及后继通过|
|新发生500s GPU事件、拒绝审核前|875.096860116|208958.788191080|未放行|该行worker尚未包含拒绝审核自身费用|
|拒绝审核完整封口后|905.096860116|拒绝区间208958.789286–208958.927470|未放行|额外snapshot-review30恰计一次；精确GPU cap拒绝|

CPU联合首stage/新审核/后继的worker余额依次208636.083655056/208546.070666449/208515.054003326，GPU余额均208690。边界旧式在新CPU费用前208768.197382212＜208800、加费后208858.441373557＞208800；更正后当次GPU余额1998.571246624，原cap4申请后1994.571246624。每个snapshot还分别核`cumulative`、`reserved_resource_budget`、`remaining_resource_budget`、`remaining_after_reservations`，running窗口用其可信resource_observed_epoch精确复算；GPU随真实持有墙钟自然增长，CPU费用没有再叠加卡时。

区间反例：同卡container5s与20s command仅GPU5s区间及区间重复，GPU115不增加；另独立GPU2s后才117；再次review/reader GPU仍117。继承110可由两个不相邻区间构成，标量须与union相等。显式CPU/缺device/CPU却有interval/越scope/未知卡/Count-all/篡改source均核。新500s发生费用压力使用**显式虚构的原T0之前继承/新增区间**，为单卡58h原上限算术输入，不能当真实项目卡时；原限额/截止没有改，完整两stage仍走生产入口，原件明确synthetic/no-execution。

原实质FAIL均已用相同拒绝要求在最终源复验：已审record.start后移/删除、Stopped缩短或整体平移同标量、allocation重标CPU、running伪早停、首review record/current与sealed Id矛盾或sealed Id缺失均拒准入与重审；合法running→Stopped保全已审窗口仍通过。static legacy缺immutable container时间基底明确UNKNOWN；真实外部命令API无设备归属凭据明确UNKNOWN，任意CPU标签不能取得真实零GPU结论。

失败历史继续保留：db023四类已审basis篡改FAIL；c53首identity矛盾FAIL；中间beb legacy FAIL；自身expiry/nonce/release-budget、近deadline release expiry、ISO微秒取整及短release不容原1800s save等fixture问题均保原命令/脚本/raw，修setup后整套同最终源重跑。旧PASS不搬作最终验收；没有放宽GPU拒绝、原cap或保存预留。

交接：父核正式裁决/evidence全部SHA、最终170源与最小diff、旧保护原件及全局预算；本节点只写自身三文档/日志/stdlib证据，不改生产/共享/旧原件。旧STOP、C FAIL、历史UNKNOWN、未获批有限会计取值、真实执行许可、58h/2TiB/原T0和截止均保留；本轮没有模型/真实Docker控制/GPU/仿真/回放/smoke/训练/最终科学test。剩余是父复核与真实合同，不能用本synthetic通过解除。

### 拒绝审核自身费用补核

保持final-v5原23项/raw逐字节不变，另以同0bb源运行1项独立归档审核：只恢复本审核自己已清理的原tmp树原字节，调用生产`costs.inventory`后立即清理，不另执行review/模型/实验。原拒绝control receipt为CLOSED，operation=snapshot-review、charged30、applied:false，SHA绑原`ValueError('cumulative GPU cap')` denial；累计worker从拒绝前875.096860116补为**905.096860116**，差30恰一次；raw外部费用743.012717912与生产inventory同值。GPU event本身500不变；容器仍持有，GPU在原拒绝起讫receipt区间为208958.789285898–208958.927470207，不能将拒绝前208958.788191误称封口后精确GPU。证据[补核JSON](../../../../agent_logs/task9/task9.11/task9.11.14/denial-reconciliation.json)、[命令](../../../../agent_logs/task9/task9.11/task9.11.14/denial-reconciliation-final-v3-command.json)，计53＋1＝54项同SHA工程核验。[SRC-1421](../../../../SOURCES.md#src-1421)。
