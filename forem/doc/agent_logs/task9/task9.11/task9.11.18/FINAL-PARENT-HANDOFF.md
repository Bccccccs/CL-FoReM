# task9.11.18 本轮集中交接

封存时间：2026-11-04T13:04:11.227145+08:00。负责人Codex；状态 **blocked：正式全案资源门**。本轮已真实完成两前门，未交付四run科学对比，不标done。推荐GPT6.1sol/high、Sonnet5.5/high，因跨阶段/设备/累计预算与科学非干扰审计；实施/独审委派sol/high，实际后端强度未知。

## 授权与已完成事项

本次用户正式派发[SRC-1435](../../../../SOURCES.md#src-1435)，原件[direct-dispatch-authorization](direct-dispatch-authorization-20261104.json)，取代误派撤回SRC1433，全部旧记录保留。日历2026-11-07 03:18:20+08，worker/GPU各58h，2TiB，诊断日志8GiB；不重置原T0/消费、不擅自改变科学条件。旧C1800s局部政策不泛化，旧C完整性FAIL不覆盖。

- 真实G1 r3：14项GPU科学白名单通过；[独裁](task9.11.18.2/REAL-G1-r3-INDEPENDENT-VERDICT-v1.json)、[父接收](parent-G1-r3-independent-acceptance.json)，见[SRC1441](../../../../SOURCES.md#src-1441)。run=t9.11-real-direct-20261104-r3，actualGPU92.855407s，outerwait10.329141s，0环境/转移/评估。
- 真实L ON：run=t9.11-real-l-on-20261104-r1，[独裁](task9.11.18.2/REAL-LON-INDEPENDENT-VERDICT-v1.json)、[父接收](parent-LON-independent-acceptance-v1.json)、[原始对比](parent-LON-actual-raw-check-v1.json)，见[SRC1444](../../../../SOURCES.md#src-1444)。100随机/96语义严格8/100及10/96，旧step1000模型，仅门测试；196公共行OFF完全一致，4568parity字节相同，实际设备CUDA0，原CPU optimizer step标量保留。ON606.980s，OFF545.796s，实际GPU728.174336s，outerwait622.152838s；内外嵌套不相加。诊断252740358B，output254152959B、log482B。
- 累计4000smoke转移、1176评估；余10592严格分9408周期+1184一次最终。**正式C4718/L4718/C4719/L4719均未启动，250k及独立final未运行。**
- 入口已把独立阶段令/授权/实际source、精确CID/UUID、宿主与容器准入、owner/guardian/watcher、actual wait/退出收据/预算接同一链。r1 Mounts顺序误拒、r2 receipt目录碰撞保留并已必要修复独审；不重做F1/F2/GPU两账/SRC1423或已有smoke。旧L合同/五输入/科学151文件先核再加载；有限loader桥保原loadercode和原合同校验。

## 具体阻断与缺口

[全资源独裁](task9.11.18.2/FORMAL-RESOURCE-EVIDENCE-REVIEW-v1.json)与[诊断独裁](task9.11.18.2/FORMAL-DIAGNOSTIC-BUDGET-REVIEW-v1.json)均NOT_READY，无正式/final令；[父接收](parent-formal-resource-NOT-READY-acceptance-v1.json)直接核35引用原件hash。依据[SRC1445](../../../../SOURCES.md#src-1445)。

|项目|证据与裁决|
|---|---|
|诊断日志|过去点时1415215541B＋未来中性外推8329790189.997B＋原256MiB预留=9.325743827GiB；对8GiB名义缺1.325743827GiB，另有未来控制/预测不确定性。不是未来实耗或必超下界。|
|过去扫描纠错|旧公式漏diagnostics/*.pt共488048139B；保原旧scanner和签字，不再称完整上界。两前门实际仍远低8GiB，不重跑。|
|历史GPU/worker|已核35+98局部根、三旧server terminal、实际CID、fork重复回放；仍252根后代尾未闭。候选GPU条件余93804.240s不是可用余额；假采另52helper后余102378.240s仍非全局上界。42.7h历史规划参考153720s分别大59915.760/51341.760s，但参考非未来硬下限，不能据此宣称必超。|
|完整turn保额旧模型|asof独审原件worker66762.057s、GPU130640.230s，非实际使用；尚非任意历史逃逸后代全局包围。后续准备/审核继续计，不能冻结时点后填0。|
|阶段view重复旧证据|past已扣一次，旧externalroots再次扫描589516469B；额外保守收费而非新实际字节。正式view须证明只扣一次或明确留额，不能直接用阶段余额充当全局余额。|
|2TiB|点时logical34663734565B，当前不是瓶颈；不等同未来全案全资源PASS。|

未来外推采用两seed历史B1完整run和24周期JSON，双方均沿原B1计数、不假定L有效；逐类动作/片段/拒绝记录字节估计，剩余周期9408+final1184，不重复LON、parity、首250k周期评估或历史13保存。历史完整wall36580.255/36953.448s已包含周期和保存；额外profile完整保存/恢复及退出成本尚须正式可行性核。所有参数/公式与限制在SRC1445及[颗粒化v2](full-program-history-LON-diagnostic-proxy-v2.json)。

## 用户需决定的最小事项

是否把诊断/日志合同从8GiB改为10GiB，其他合同不变；这是工程建议，**未应用，非保证足够**。若维持8GiB，当前方案无已证全案可行性，维持停止。提高诊断额度也不能直接开训：历史全局GPU/worker尾段及未来可行性仍缺证，需要完整保守包围或用户明确到具体缺口的政策，不能把任意UNKNOWN核销为0。本轮不请求笼统增加58h、不删诊断/缩规模、不跑250k代替全案门。

## 剩余实现与恢复顺序

真实G1/LON源182文件SHA26308d91fd299ff55d2cdc84b21172210e5df59826aa870aaafb7bd93d87dd0d，protocol3ef796fd…67cb，冻结保留。正式/final仅[必要补丁规格](task9.11.18.1/20261104-codex-formal-final-minimal-patch.md)，尚未实施；不是训练入口完成声明。恢复先读本交接及.18.1/.2/.3三文档，核当前源与用户新合同。先补必要formal/final入口并整体冻结，含四个自身250k的原3M预算内分段/恢复和最终冻结四final测试；checkpoint绑定完整源，不能开训后再补final代码。然后独立审查完整费用尾段/全案资源与阶段令。全案门通过才按C4718→L4718→C4719→L4719，每个自身250k实测可行后续3M；开发验收通过才一次独立最终测试。已过真实G1/LON原件可按科学/source适用性复用，不能借新授权重做消费。

## 进程、版本与证据

[最终进程/Git原件](parent-final-process-git-check-v1.json)：r1 CIDca9a26c96080…81fc74、G1 r3 CIDaceae3f432a9…97d77d2、LON CID22068d0d9d1c…cf9d全部exited/PID0。本批没有待停实验。GPU查询仅task10原GPU-baaca86e-0491-44bf-4294-e64ffe4934e9/PID970022，未影响该任务。不得恢复旧run。

Git HEAD d198e5ca48f86071c05274f9da753f393ce058b4，分支codex/task9-lower-improve；保既有多人改动，无commit/push/merge。git diff --check通过（最终新增交接为普通Markdown，另核链接）。代码/配置/产物在forem边界内；历史恢复脚本仅证据、不执行旧模块。子交接：[独审](task9.11.18.2/FINAL-INDEPENDENT-HANDOFF-v1.json)、[历史库存](task9.11.18.3/stage2-v1/STAGE2-HANDOFF-v1.json)、父[执行全记录](20261104-codex-direct-dispatch.md)。原件各版本、原失败、UNKNOWN、旧费用与政策全部保留；历史条件预算不当作已验收全局事实。

末次独审快照后的准备/审阅/落文费用另见[父尾段计费](parent-post-snapshot-control-tail-v1.json)：至epoch 1793768673.013，保守把三个参与者均继续视为open，补worker 855.810s、四卡union 1141.080s；即使子已结束也不减，非实际GPU使用。发布尾另暂留180s工程余量（非OS硬界）。仍不形成可用余额/历史全局闭合证书，后续不得把该时点后的工作记0。
