# task9.11.18.2 独立预算与准入审查结果

> 当前接续状态（2026-11-05）：active。2969467 原生恢复已真实加载并达3M保存，末周期尚在完成；两卡独立run外部入口正做最后定点接线核查。原160h/16GiB/2TiB与真实截止及统一52h共享分配生效，[SRC-1461](../../../../../SOURCES.md#src-1461)。下文早期状态与额度均为保留的历史记录。

状态 **review / 真实阶段尚未放行**。负责人Codex独审；推荐GPT6.1sol/high、Sonnet5.5/high，因涉及旧会话、嵌套执行、设备及控制费用的跨阶段因果核验。委派标称sol/high，平台实际型号/强度无法独立核实，记未知。授权为[SRC-1433](../../../../../SOURCES.md#src-1433)：原T0不改，截止2026-11-07 03:18:20+08，仅日历延期；worker/GPU各58h、2TiB及科学预算不增，不核销其他UNKNOWN。

## 已完成的独立核查

[独审原件v3](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/independent-budget-precheck-v3.json)及[只读审核脚本](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/independent_budget_precheck.py)记录精确引用、SHA、原命令/活动包含关系、现场Docker/GPU查询及失败记录。来源登记[SRC-1434](../../../../../SOURCES.md#src-1434)；本条审查原件尚不是独立阶段许可。旧准备与政策事实沿[SRC-1430](../../../../../SOURCES.md#src-1430)、[1431](../../../../../SOURCES.md#src-1431)。

父冻结host-turn-envelope-v2及提取器：包含本工作树全部数据库线程及跨cwd子关系、archived线程，共40线程/69时段，无解析缺失；向外整秒取整的时段和47519s。独审未读取历史会话文本。280份可定位时段的直接原command都至少被一个完整turn包含，无越界；14份缺绝对时钟，其中12份实测wall共62.853658770s可全额另预留，允许重复计费；两份为旧C无终态launch及实施收尾失败final-accounting-first。前者沿已批准C1800s局部政策；后者由原实施收尾记录归属原lr_implementation turn，但无单独原始绝对时钟，不能声称已独立恢复历史实测。

旧10份activities的启动/已知完成均处原实施turn 1793697605–1793707453内。旧容器同ID `70c66…d27`，原start至stop `FinishedAt`为7252.530197859s，stop前top仅sleep，全部位于该turn；可包围旧后台容器费用，不与turn重复相加。仅证明该已知容器，不能把host准备命令的GPU未知归属改成CPU。

## 两种准入分开裁决

候选保守已耗worker为 `47519 + 62.853658770 + (1800 − 618.796192884) = 48763.057465885s`，剩余下界候选 `208800 − 48763.057465885 = 160036.942534115s = 44.454706259h`。额外C政策增额1181.203807116s与完整turn同时保留，以避免冲掉批准局部计费；可能保守重复，非精确实际总时。此数仅截至冻结快照，当前三个开放会话的后续增量及未来控制/发布尾仍须扣除；元数据包围全集、无遗漏后台及原政策的应用边界仍须在执行协议中封存。

1. **新G1与随后L ON196的预算数值：条件通过。** 新G1最多1800s，L ON最多1800s（原记录门合计3600s扣历史C政策1800s），两门合3600s后候选worker仍余156436.942534115s，另扣当前增量及所有CPU控制、准备、保存/退出。真实源/执行合同、设备归属、有限控制数额及阶段独立准入先通过，才能实际签令；G1通过后才能签L ON。正式全案工期门不前移阻断这两项已授权有界前门。
2. **正式训练：现在不通过、不签令。** 原正式48h＋test4h上限占额不能装入候选44.455h，历史主体42.716–43.131h只是参照，尚缺全部Q及实际成熟路径。G1、L ON实测后再做全案预算门；首250k包含原3M且只有前置全案可行通过才能启动，profile实测再审remaining，不能用试训代替预算门。

## 下一次审核输入与交接

等待.18.1实际稳定交付；未预签代码、G1、L ON、训练或test许可。实施者应交：完整源manifest/四科学配置不变、原T0与新deadline、旧消费/政策与候选上界的显式冻结引用、新namespace/精确container ID/镜像/挂载/设备UUID、真实wait与独立发布退出链、可观测且有限的CPU control规则/数额、全部历史及新增成本库存、当前开放会话增量和资源预留、实际生产CLI的拒绝与失败封口证据。独审按该稳定版本定点复核，然后只签对应单门；通过一门在本派发内继续。

本节点未改生产源、未加载模型/环境、未启动训练/真实Docker控制或真实GPU工作。只读Docker/GPU查询已记录，不影响task10。首次工具内审核因宿主不接受Docker九位纳秒datetime而失败；v2的Docker ps格式未正确shell引用而rc1，v3改为直接docker ps -a并成功，失败均保留不计0。当前完整会话/文档与发布退出尾计入父后续metadata增量。父维护共享PROGRESS/SOURCES；下一步依赖.18.1稳定原件，若不能闭合则直接报具体缺口。

## 未知GPU归属的有界前门准入预留

依据[SRC-1434](../../../../../SOURCES.md#src-1434)，补充[保守预算独审原件](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/conservative-pregate-budget-review-v1.json)状态为 **CONDITIONAL_BOUNDED_PREGATE_BUDGET_PASS_NO_RELEASE**。只作G1/L ON前门预算，不是阶段令。核父新精确ID真实inspect与旧原stop同容器、Stopped、RestartCount0；独立查询实际4个物理GPU UUID。

为避免把host准备GPU未知归属记CPU/0，按4卡全部占用作**准入最坏预留**：69个已核turn的时间并集25842s，另加无定位已测payload62.853658770s及C局部政策增额1181.203807116s，`4 × (25842 + 62.853658770 + 1181.203807116) = 108344.229863540 GPU秒`。其中原有真实容器保守暴露7252.530197859s，新增未知归属准入预留101091.699665682s，分列不混；旧容器整个处turn并集，不能再次叠加。该值是为准入占额作的保守计费，**不是历史真实GPU使用量**，不消除原UNKNOWN。

同冻结点GPU58h余100455.770136460s；G1/L ON合3600s后余96855.770136460s，数值可容纳有界前门。依赖旧活动全集/已知后台原件范围完整；280份可定位原命令0越界、旧全部activities和实际容器被包围，12条无定位实测wall全额额外预留，C失终态依获批局部政策，失败cleanup仅原实施收尾记录归属。发现任何未覆盖独立后台或额外allocation，须追加完整预留并重审，不能隐去。当前开放会话增量、控制及保存退出仍须在真实守卫中滚动扣费，不把此旧快照当永久余额。准备3源尚未冻结，独审未无因重复验证，将等实际G1稳定交付按新manifest审查。


2026-11-04T11:35:01.586652+08:00 · 新正式派发 SRC-1435 · active，取代撤回的SRC-1433执行授权，历史事实与停止记录保留。本次完整合同见新授权原件及父直接派发日志。父Codex协调；.18.1实施（sol/high）、.18.2独审（sol/high），先稳定源和前门预算，再逐门签令。推荐GPT6.1sol/high、Sonnet5.5/high，因跨进程/设备/预算审计；实际型号强度未知。

## SRC1435正式派发后的独立刷新（2026-11-04）

独审接任active；[SRC1435授权](../../../../../SOURCES.md#src-1435)取代撤回许可，旧停止记录保留。[刷新原件](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/current-pregate-budget-review-v1.json)是**NUMERIC_PASS_NO_STAGE_RELEASE**，由[只读脚本](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/refresh_budget_review.py)实际rc0生成；父维护新增来源登记。旧[SRC1434](../../../../../SOURCES.md#src-1434)两份审查JSON中直接列出的引用hash核真（非跨文件传递核当前生产源）、新元数据43线程73时段、现3open身份，旧spans无缩短。新准备/会话/审核包围增2706s；worker准入上界51469.057465885s。未定位实测62.853658770s、C政策增额1181.203807116s及GPU四卡最坏预留112380.229863540s继续分列，均不伪称历史精确实际总费用，不核销UNKNOWN/FAIL。

分别：G1最多1800s后余worker155530.942534115/GPU94619.770136460s；再L ON196最多1800s后余153730.942534115/92819.770136460s，控制、保存、退出及此后滚动增量另扣。两项有界门数值可容纳，正式训练须之后独立审全案，不因成熟性能未测前移阻断前门。稳定SRC1435生产源/协议、实际命令/设备/容器、真实wait/有限控制退出及失败allocation守卫尚待.1交付；本节点未签令、未启动实验。若长infra租约失败尾未停止，其剩余allocation须全预留，不能用短G1 cap代替。

新存储logical34068176639B；当前诊断扩展名扫描690133365B小于旧924662935B且口径未证同，准入不得据此缩紧，保较大旧值追加增量。推荐GPT6.1sol/high、Sonnet5.5/high，因跨进程/真实预算审核；委派标称sol/high，实际后端档位无法独立核实。task10 PID970022未操作。

## 稳定G1源审及基础设施单门令

独审核真180当前/冻结源SHA `4b69383c0f96ed2951248c7fc27648a0de00d11b7e2dd48355526beaf253ad93`；相对.17，171旧源不变、4改5增。实施5次实际wait和原source快照核真，首次失败保留，末版50项rc0；独立新增[10项检查](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/independent-g1-tests-v1-command.json)rc0，180源前后相同，未导入模型/环境。已修审核发现的宿主/output lease引用跨域问题；不是复跑既有F1/F2/SRC1423。

[稳定源审](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/G1-source-review-direct-v2.json)仅限REAL_G1_ONLY，绑定[详细核验](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/G1-source-direct-v2-verification.json)。[前门预算v2](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/G1-budget-admission-direct-v2.json)封当前4实际open身份，metadata至发布及此后4worker/4GPU每秒滚动预留；时点worker53067.563298557/GPU114139.735696213s保守上界，不核销UNKNOWN。诊断沿旧较大924662935B追加全部.18，不据低扫描缩紧；40GiB保存预留不改。此前数值刷新来源见[SRC1436](../../../../../SOURCES.md#src-1436)，新源审/签令由父补来源登记。

**仅独立基础设施创建令已签**：[infrastructure-direct-v2.json](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/releases/infrastructure-direct-v2.json)，SHA `76ac96a1ae6f1fc4ee4b667ef2c078e8ead62f052f5d9cb0814e0adf6c1c10ff`。绑定新SRC1435协议/源/run/固定GPU UUID/image，1800s cap＋120s control，完整1920s GPU allocation预留；这些是准入工程预留，非实测完整控制最大值。原schema读取实核通过，未授G1/LON/formal/test。下一步核新精确CID/actual-wait/分配/lease再签单G1（拟120s，尚未签），失败allocation未封前保完整lease费用及UNKNOWN，不自动retry。父仍须自行直接核原件，本节点不声称父已验收。

## 真实分配审核发现与暂停新准入

基础设施创建后、G1签令前，独审实际查询唯一CID `ca9a26c96080722913bc92a7424f6ecddeac9e5be33169d819e95af47981fc74`。第一次审核rc1（0.179377616s）因身份列表比较失败；[第二次原查询](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/exact-infrastructure-query-attempt2.json)rc0保inspect/top/GPU输出：容器只有有限sleep，GPU0无compute；Docker自然返回的Mounts数组顺序与sealed不同，但Destination映射字段完全一致。当前container_identity按原数组顺序比较，真实inner与cleanup会误拒，须canonical排序保全部字段并新源审。合成源审不代替此真实发现，**G1令尚未签，G1尚未执行**。

另.18.3发现3历史真实PTY session缺终态，可能越出旧turn-only包围前提，旧4卡准入预留的条件完整性须重审。父决定先精确停止上述唯一新CID，保旧令/源/协议，不迁移同allocation；实施只修源新冻，先不新分配。当前暂停新allocation/G1科学准入，等待历史PTY原wrapper/终态或保守上界及此次实际stop/wait/inspect证据；不归零未知尾，也不声称已证实必然超预算。此次基础设施实际分配/控制成本继续扣原预算，消费仍4000smoke/980评估，不算已执行G1或新增科学回合。父尚需登记本发现来源。

父停止后，独立fresh inspect确认exact stopped，原wait137、StartedAt/FinishedAt及完整语义身份均同。[费用核验](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/infrastructure-stop-cost-review-v1.json)：实际GPU分配132.722388983s，原1920s准入预留保历史；该区间已处当前4卡turn并集，不在包围总额上重复叠加。尚无G1/科学消费。

Mounts修复后180源 `71478d445f2c8e8f06ffa43e95d7f46d8eb46127020a6280f388f245487cefc0` 当前/冻结全一致，2改178同；14回归原件核真，独审另测实际Docker输入24排列/24字段逐项变异/重复项保留及旧协议漂移拒绝。[修复独审v2](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/mount-canonical-independent-review-v2.json)仅**PASS_SOURCE_FIX_ONLY_NO_RELEASE**；v1误写28字段的文字计数原件保留，v2明确实际6×4=24，测试循环未改。等待.18.3三历史PTY原wrapper/实际终态或可证上界后重裁预算，不先新分配。

## 三历史PTY独立裁决与前门余量

[独审worker原件](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/three-historical-roots-independent-v1.json)核477原frozen源码及3child实际exit0，精确root历史退出仍UNKNOWN。独立当前同UID /proc扫描120进程0错，三精确wrapper label/相关fixture argv均不存在，原源无改argv/自重启，故每根原启动→现场全窗47589.150904655s，额外worker142767.452713966s不扣既有turn交叠。加新turn后worker上界197406.510179851、余11393.489820149；G1/LON各1800后仍余7793.489820149s，新控制/滚动另扣。仅证明两前门数值可容，正式另门。

[具体GPU排除独裁v2](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/specific-three-root-source-adjudication-v2.json)核原wrapper/10源/6原流与17产物manifest：可达payload仅stdlib fixture/sleep/signal，worker adapter在GPU分支前return、真实CLI先NOT_READY，可据源码排这三根及所列后代GPU，不据CPU标签或空采样。rootexit仍UNKNOWN，保全窗worker预留；完整历史GPU不缩，131根退出不当全部detached已退出。v1引用过调查者首次称stable的16项manifest，随后调查者同名修改使该旧绑定失效；v1保留、v2重核新17项并明确跨thread session registry限制，实际source/数值未变。后续来源登记由父维护。

当前22434处.1开放turn内准备，完整turn已包围，父取原成功poll原件而不重跑。待修后fresh协议，才冻结新预算/单infra；当前无新allocation/G1/LON/formal/test令。

## 原服务器外层终态恢复及r2基础设施单门

三旧root原终态已由[独审原行副本及核验](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/three-old-root-actual-terminal-recovery-v1.json)恢复：原rollout572/574/587行均CommandExecution item_completed/statuscompleted/exit0，精确processID/argv/时间齐。原callstart→最晚serverend全部处原已计turn，故先前额外142767.452713966worker全窗是**候选未用预留**，现由真实终点替代为0新增，非政策核销，不覆盖历史保守原件。servermetadata差分只是该域时段，不声称完整精确rootwall；innerwait不重复加。22434同类原server终态/成功poll已核原prefix字节，完整准备/发布turn继续计。

[三根具体源码独裁v3](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/specific-three-root-source-adjudication-v3.json)仅绑稳定原477快照/10源/6流/wrapper/本节点server原件，避开调查者冻结后覆盖再恢复的汇总引用。全局GPU仍保四卡turn准入预留，不以rootexit自证所有detached已停。旧FAIL和其他UNKNOWN不核销。

fresh r2协议SHA1b88c858…32a591、run t9.11-real-direct-20261104-r2、当前180源71478d44…/冻结全一致。[新源审](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/G1-source-review-direct-v3-r2.json)/[新预算](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/G1-budget-admission-direct-v3-r2.json)：当前3open身份、仍4worker4GPU/s，worker55964.350850437/GPU117454.523248092s保守上界。[新基础设施单门令](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/releases/infrastructure-direct-v3-r2.json)SHA0c2efda5207cec7e233e4f2f785f4806d33059f116960897f67ab6e90be0cf82已签且生产读取通过；1920完整lease/1800cap/120control/save10。只有基础设施许可，未签G1/LON/formal/test，等新精确CID/actualwait/设备/lease独审后续门。新增来源仍由父维护。

## r2预启动失败与r3收据隔离修复

[r2独审核验](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/r2-prelaunch-failure-review-v1.json)确认固定r1收据目录碰撞：原冻结wait_command line89 mkdir在line110Popen前拒绝，r2无cid/容器，仅RESERVED/lease/冻结协议；无新GPU allocation/G1/科学消费，宿主准备未知GPU仍在四卡turn预留，完整失败turn扣费。r2身份不复用，原令和失败保留。

[必要隔离修复独审](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/receipt-run-isolation-independent-v1.json)核当前/冻结180源fda8ddf6109b587b91b2d423dad39a54b9d104767d9f17a0c4ec451307af8a37、5改175同，55原测试/actualwait/source快照通过；独测跨run三阶段收据隔离、非法/逃逸runid与跨run control/waitreader前置拒绝，无真实外部操作。不重跑既有矩阵。依据[SRC1440](../../../../../SOURCES.md#src-1440)。

fresh-r3协议SHA2f6b83b2…beb19b，[源审](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/G1-source-review-direct-v4-r3.json)/[预算](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/G1-budget-admission-direct-v4-r3.json)：当前2open身份仍4worker4GPU/s，worker56760.431349132/GPU118594.603746788s保守上界。[r3单infra令](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/releases/infrastructure-direct-v4-r3.json)SHA5f29580781da9a358e68ffced10c32c03029c7c73aef1d6ff94e0ed1b33408e1已签且生产读过，1920lease/1800cap/120control/save10；无G1/LON/formal/test许可，待新CID/wait/设备/lease独审。

## 真实G1完整门通过

[真实G1独裁原件](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/REAL-G1-r3-INDEPENDENT-VERDICT-v1.json)SHA75347054af33b3d10cbd4a66d83f2ef0209cf90d985b7bbc8c7fa4a0b23ce2f5为**PASS_COMPLETE_REAL_G1_ONLY**。新精确CID/实际181源launch与outer-wait前后快照、source/protocol/原令副本/nonce/record/ledger/reservation/所有chain哈希和命令已核真；14pytest pass，policy/replay及actor/critic/alpha optimizer实际cuda:0，0真实环境/回合。owner/guardian/watcher/exec/inner精确PID+start_ticks均退出，各实际wait exit0，另直接核父原CommandExecution --execute-g1服务器外层completed/exit0原行，未只信内部PASS。

outer-inner actualwait10.329140872s、ownerwait9.778316379s、workerledger8.471122546s嵌套不相加；Agent/control/发布尾继续完整turn上界。fresh exactCID已Stopped，实际GPU分配92.855407s；原1920计划保历史，实际区间在四卡turn union不重加。内部UNKNOWN原文不回填。只读kernel cache警告不影响正确性，不作为成熟性能通过。科学消费仍4000/980，旧C FAIL保留。

只有G1通过；尚无LON/formal/test令。实施者按父既授权开始最小LON196适配，稳定源/旧checkpoint/config/OFF/parity/G1组合/单门预算与实际设备链需另审。LON拟cap1800/save120沿旧参数、owncontrol120；infra拟1800+420=2220给创建后300s审核窗，420为两次实际准备墙钟参照加余量的工程预留，非已证最大值，等稳定协议后再裁。父另令.18.3只做必要历史host GPU可达归属证据收紧，原四卡turn预留在新独裁前不缩，不重跑既过门或科学试验。

LON[静态先验独核](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/LON-legacy-input-science-independent-v1.json)已过：5旧输入实际bytes/流式SHA全符，checkpoint2635371606B（9f6e7773…ebb8c），151科学/config/recorder/runtime当前与原artifact549b…快照逐字节同。旧L OFF complete、step1000/wall545.795874471s、smoke limit1000、75updates、parity4568条；只读核查2.464s无模型/GPU/环境，仅先验非新LON令。新源/196实际回合/精确parity/设备/退出和预算仍另审。

## LON182源审核与196单门放行

[LON源码独审](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/LON-source-independent-review-v2.json)通过：182当前/冻结源26308d91…87dd0d，相对G1v4六改2增174同，151科学不变；6实际wait/冻结快照核真（72.0866s、嵌套在turn内），各版本69/15/16项测试范围按原件。初版缺真实恢复设备观测已最小补入v2，仅读模型/replay/optimizer实际设备，原loader特意CPU step不改。私有一次loader只钉精确旧159 manifest的_contract，原字节码、format/obs/action/map/pool/unsafe/RNG检查及原global保留。[独审8项](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/independent-lon-boundary-v1-command.json)rc0/3.510s，全182源前后同，包含真实原loader AST在显式inert对象下拒错和RNG恢复；无真实模型/GPU/环境。

[LON预算](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/LON-budget-admission-v2.json)仅前门：worker61043.509843204/GPU123310.682240860s保守上界，4open/4worker4GPU每秒，diag上界1060853549B；旧980全扣、新仅196，不采未独裁的GPU缩紧候选。infra1800+control420=2220，LON cap1800/save120/owncontrol120；300s审核窗属有参照工程预留非实测硬最大值。

新CID22068d0…6ccf9d经[独立实际分配审核](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/exact-LON-infrastructure-review-v2.json)核全身份/设备/4mount/StartedAt/RestartCount/readonly/network、183真实launch源前后快照及exit0，lease余2163.633>1920。已签[唯一LON196令](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/releases/gate-evaluate-L-4718-LON-v2.json)SHA4b0fcb9039c47789a5f36a8c1affd07a4e2d84f4f089ff97bd2e8af0e5e46bdd，生产读取通过。执行后仍须actualdevices/196精确parity/完整外层退出/Stopped独裁；当前未宣称LON实际通过，未签formal/final/额外C/smoke。

### 真实 L ON196 独立完整验收（2026-11-04）

仅 `t9.11-real-l-on-20261104-r1` 通过，独立原件 [REAL-LON-INDEPENDENT-VERDICT-v1](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/REAL-LON-INDEPENDENT-VERDICT-v1.json)，SHA `71bdb0802f747daf863cb5c0adf69ee202deef434fff24ee4f8af13edb40d06e`。源 `26308d91…dd0d` 的183项（182源+协议）实际 outer-wait 前后原件/快照与当前逐hash一致；独立令复制相同、旧 checkpoint 流式全SHA重核。原server事件1745证实87420 completed/exit0，owner/guardian/watcher/exec/inner身份全部不再存活；fresh exact-CID inspect 证实退出，完整 Config/HostConfig/Mounts 无漂移。原内部 UNKNOWN 字段保留，外部闭账证据另列。

写前实际196=validation100+transfer96；全部旧公共字段及196条有序科学rows逐项精确等于旧OFF，ON额外8个诊断字段独立核，不误称整个原始rows字典字节相同。4568条 parity 原字节完全相同。实际网络、replay、优化器参数和矩张量均 cuda:0；原非capturable/fused优化器step CPU标量保留。严格成功8/100及10/96只是该旧step1000 checkpoint结果，不推导L优于C或成熟有效。

ON wall606.979549948s，OFF545.795874471s，此一对实测差61.183675477s不是通用开销上界。worker618.587798173s、owner wait621.588849258s、inner实际wait622.152837617s、原server duration622.378122078s为嵌套/不同时钟域，不相加。实际GPU allocation 04:23:57.628523273Z→04:36:05.802859425Z共728.174335957s；原2220s预留历史保留，此actual区间在旧四卡turn union内不重复加。新诊断252740358B，519个pt窗口=173拒绝×3；new output254152959B、logs482B，均为验收读取时点值。

独审检查器首轮错误要求OFF含ON新增诊断字段、次轮宿主Python3.10不接受9位ISO秒小数，两个真实rc1分别保留在`LON-independent-check-attempt1/2.json`；修正比较范围和解析器后rc0，没有重跑科学试验，也不将检查器故障记成科学FAIL。此次所有读核时间继续计当前turn。模型推荐仍Codex GPT6.1sol/high、Claude Sonnet5.5/high（跨源、时钟、费用与设备链审查）；实际运行模型/强度无法从本原件独立核实，记未知。

旧C FAIL、旧UNKNOWN及C1800政策原账不变。累计eval消费1176=980+196，后续周期9408及独立final1184仍待执行。仅限定G1和LON门通过；全案资源裁决及正式/final源审尚未完成，未发任何正式/final阶段令。依据沿SRC1435本批授权及SRC1436/1439/1440后父登记真实原件，不以子报告代父核。

### 原历史fixture局部归属与正式诊断门（2026-11-04）

[98实际根局部独审v2](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/fixture-98-actual-root-review-v2.json)，SHA `df5467e80302ea167d05523472289dcbae29525004a3f18763cc125942775505`，通过**仅这98根无越root GPU后代**性质。116个实际原source版本与原origin/terminal/完整metadata/输入快照已读核；11个有限wrapper历史版本的5条路径、原来源与未支持编辑定点目标均核。v6曾误把14根实际sed后wrapper绑创建版，v7改正至独立重建的9675完整SHA，原候选/hold保留，新v2解除hold。19根原runnerSHA直接匹配；其它按完整有限版本集合所有分支相同纯stdlib与同步具体argv性质排除GPU逃逸，不把未知具体版本填成精确SHA。其余40 missing/其它helpers未过；每实际root仍全4卡，整turn只能在其它全部可能escape也被核后撤预留，精确UUID allocation与未定位/C1800政策额外仍保留。该局部件不是global GPU预算令。

[正式诊断预算独审v1](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/FORMAL-DIAGNOSTIC-BUDGET-REVIEW-v1.json)，SHA `4902ba44df1471da2e19b4293947f43839912655ee7e36ff6896af6e03fec3ba`，**NOT_READY_NO_FORMAL_RELEASE**。独立读24份原B1评估、各原hash、LON真实7类events逐行字节与519窗口stat，按两臂同B1的中性假设得future10592=1969852动作/20616段/4774拒绝，窗口6714508504.127B、events1528468827.992B、评估JSON61531413.878B、其它training日志25281444B，共8329790189.997B，等父v2。LON196已消费不再列未来，普通periodic/final parityFalse不重复列LON parity。未来heldout按旧validation100→200/transfer96→96只是经验代理，非未来下限或保证，不假设L改善。

同时发现并明确保留旧扫描缺陷：`refresh_budget_review_v2.py`仅按输出扩展名，漏计diagnostics目录内.pt。原件不改；新完整actual stat manifest计所有diagnostic路径文件，读时点past保守分类1415215541B，旧不完整公式927167402B，差488048139B为漏窗口。该分类将全部task9.11证据保守纳diag，不冒称最小精确旧费。原前门实际仍远低8GiB，无需重做已验G1/LON。

8GiB原cap=8589934592B，原unmetered reserve256MiB=268435456B，所以tracked writer阈值8321499136B。当前past+未来中性proxy+reserve名义10013441186.997B=9.325743827GiB，名义差1423506594.997B=1.325743827GiB，另futurecontrol超过预留部分与proxy不确定性未含；新独审manifest/verdict自身是scan后增长，保留控制预留不能记零。该差额是工程参考缺口，**不是已经发生的超额/未来必超的硬下限**。在没有可证全案容纳或用户明确改合同前，不签formal/final；不删诊断、不降低科学规模、不改8GiB。8→10GiB仅可向用户提出工程选择，未实施或获批。worker/GPU/日历/存储还须当前单独核算。依据父新SOURCES登记此原件；不自称父已验。

### 正式资源证据集中交接（2026-11-04，本轮 review）

[FORMAL-RESOURCE-EVIDENCE-REVIEW-v1](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/FORMAL-RESOURCE-EVIDENCE-REVIEW-v1.json)，SHA `2891d37534ee4feba48783fb70226979eb20b352a68551bffae8f0dee9cd30d2`，**NOT_READY_NO_FORMAL_OR_FINAL_RELEASE**。独立重算调查者已有局部混合候选：1824根并集6060s/根和6866s；每物理UUID分别合root、未知turn、rolling与4个精确已停CID，再保未定位62.853658770s与C1800增量1181.203807116s的4卡4976.229863540s。35+98已过、其它helper fallback的条件GPU候选114995.760124580s，58h内条件剩93804.239875420s；假使额外52helper全部通过（实际未采用）候选106421.760124580s、条件剩102378.239875420s。两者都**不能作global上界或可支用余额**：252/200未闭root后代可能越turn，纯语法筛查亦未整体独核，根wall和不能替代完整worker会话。对42.7h=153720s这个四舍五入历史参考的名义GPU差59915.760/51341.760s不是未来必需资源下限，不证明实际科学必超。

新当前turn原库存asof1793768387.743075，原raw66821s扣已证明2条fork重放1303s，再加未定位/C政策额外，旧保守模型worker66762.057465885s、4卡GPU130640.229863540s，分别模型候选余142037.942534115s/78159.770136460s。当前所有准备/独审/发布尾仍持续计费；这些是准入保额模型，不是实际GPU占用或任意未知后台已闭合的证明。[历史原出处与局部证明 SRC-1443](../../../../../SOURCES.md#src-1443)。独审算术检查初次750ef6 rc1因list/tuple混排比较，改为端点key后9a4e59 rc0，不重跑科学/控制，不抹失败成本。

最小未满足事项是完整历史GPU/worker尾可证包围，及完整未来规模的工期/资源（含保存、恢复、控制、诊断不确定性）在原合同内可容的证据，或用户明确合同决定。无关未知不必全部清零，但不能把未闭尾截到turn结束。现诊断独立门也未ready。调查在已有局部结论与明确欠证处收束，不新开250k或分配。G1/LON完整PASS保持，旧C FAIL/UNKNOWN/政策债保持，task10 PID970022未控制。当前只是本轮独审交付review，父仍须直接核原件汇总；未自称父验。

最终来源与交接：真实LON完成登记[SRC-1444](../../../../../SOURCES.md#src-1444)，上述逐类诊断预算及原扫描纠错登记[SRC-1445](../../../../../SOURCES.md#src-1445)；历史局部原件沿[SRC-1443](../../../../../SOURCES.md#src-1443)。父要求本轮停止扩展审计，三文档和原件封存，状态review交父直接验。无正式/final令、无正式训练、新科学工作未启动。后续唯一依赖为明确合同/完整可行性证据与稳定生产交付的重新独审；旧FAIL/UNKNOWN与全部历史成本保留。


2026-11-04T14:51:06.143514+08:00 · 当前续接 active，沿SRC-1446新10GiB/原2TiB及58h/截止/T0，全部历史保留。Codex独审资源及随后formal/final同冻结源码；与.18.1实现、.18.3关键尾段证据并行。仅本子三文档/日志/独审令，父独占共享文档。输入最新集中交接/原独裁/新授权，交付全资源已用-预留-预测-余量决策表、可靠保守上界和精确引用；UNKNOWN不能置零，资源PASS后才签C4718令。推荐GPT6.1sol/high、Sonnet5.5/high，因历史后代/多域准入因果；实际未知。递归三文档规则保持，本次不建新子节点。

当前续接中间证据：[资源日志](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/resume-v1/20261104-codex-resource-resume.md)；[SRC-1447](../../../../../SOURCES.md#src-1447)待父登记。尚未独审全案PASS，不签令。


2026-11-04T15:14:40.065072+08:00 · 当前active，SRC1451/1452新授权后有限资源方案独裁PASS；历史96h worker为明确工程专项预留，不是完整物理证明或实耗，GPU历史按4物理卡×原T0至asof全窗保守预留。总worker/GPU160h、诊断16GiB计原2TiB、单卡、原日历不变；旧58h下NOT_READY原件保留但不继续作为当前阻断。新AGENTS#budget-review已读取，准备/排错/审核与有效训练分账，采用当前更保守既签额度不重置历史。

完整formal/final入口v2独审[SRC1448](../../../../../SOURCES.md#src-1448)在已检查范围内PASS，184当前/冻结源一致、151科学字节保留；最终原生checkpoint加载、test_jobs/四final模型与独立开发门均已同源冻结。v1 active-time重复预留疑点已定向修复，13独写边界及复用2个生产resources/单卡路径rc0/实际wait0.765721s；实施原89项证据复用，无新G1/LON/GPU试验。

独裁原件：agent_logs对应本节点resume-v1/PROGRAM-SOURCE-PASS-v2.json、FINITE-RESOURCE-POLICY-REVIEW-v1.json、resource-envelope-v1.json、program-budget-admission-v2.json。C4718基础设施令已签（releases/infrastructure-profile-C-4718-program-v2.json），生产准入stdlib实核通过；真实Docker由父执行，拿exactCID后签首次profile必要令。source通过不等科学完成，当前正式尚待父launch。后续只核新增实际吞吐/完整保存恢复/诊断增长和计数，不机械重复全套或政策审计。


2026-11-04T15:21:17.096674+08:00 · r1失败与必要恢复：r1在read_release租约HOST与/output ref比较处、activate/模型之前失败，输出无ledger/episodes-started/profile/summary，0正式转移0评估；现场exactCID837299…a3c57 exited137/PID0，实际allocation128.111202651s，原件program-r1-exact-stop-v1.json保留。必要修复仅real_program.allocation_reference发布HOST证据路径+专用双域回归，freeze v3与v2仅2源改/182同，四项定向实测rc0；复用完整v2 source及前门，不重全suite。

PROGRAM-SOURCE-PASS-v3.json定点独审PASS；新r2协议/source93349324…bc9d3b，新program-budget-admission-v3-r2.json保历史/UNKNOWN和同finite plan，GPUphysical全窗含r1实际区间不再重复加。r2infra准入PASS后父已真实prepare，exactCID3d6967fcf4f113a8e2bb35b149f7ff84a0001edd589291f3eae12c4962324fea；独审单UUID/image/lease6420实际原件后签releases/profile-C-4718-program-v3-r2.json，并copy out/releases/profile-C-4718.json，生产release准入rc0。父即真实execute；本记录不冒称已完成250k/3M。推荐GPT6.1sol/high、Sonnet5.5/high，跨HOST/container恢复必要因果；实际未知。


2026-11-04T15:38:58.268909+08:00 · 按用户“长训练无问题则退出监督”，后台driver已由父确认PID1201603/PPID1、OBSERVING_EXISTING_STAGE，原worker1186191继续。外部reviewer脚本forem/scripts/task9_11_program_review.py（native artifact glob之外）授权SHA0d77d3feec887ff5af79e7f8b1b0d3e2a516bc8c7b952ca195695d42dd16a06f，四fixture定向通过：profile196边界、原12h cap、安全issuer目录、完整native prerequisites JSON-only证据/原JSONL追加后快照不漂移。8训练stage按现有schema自动增量签令/关闭，final明确NEEDS_FINAL_SCIENTIFIC_ACCEPTANCE，不能把描述性audit能力门当完整B–E。模型源仍93349324冻结。授权原件resume-v1/external-reviewer-authorization-v1.json。

辅助只读monitor精确PID1192006已SIGTERM，session16956终态143；停止证据readonly-monitor-detached-v1.json。仅停止该脚本，不停daemon/训练/owner。末次monitor169000步/16875updates/replay100000，elapsed1012.438s，无Q_bound_exceeded；250k保存恢复及196评估尚未发生，不预称通过。实际mature参考103k→169k为66000/(1012.438-651.874)=183.047 transfers/s，仅非周期实测，不含250k普通save、extra profile.save、196评估或恢复。后台每stage读取真实新facts更新预算，不需人类LLM轮询。接回时先读program-driver/status.json/events.jsonl及独裁指针，不重复前门。


2026-11-04T16:26:17.210058+08:00 · r2真实250k失败恢复独审：profile与ordinary250k两个full各13.523GB，ZIP64声明payload21.605GB；只读末3MB central得缺payload至少8.082GB，逻辑/物理central实际差恰等三个>2GiB存储写入各仅0x7ffff000字节后的总缺口。不能仅改ZIP目录恢复8GB tensor/replay/optimizer，actor不当full。原件resume-v1/r2-checkpoint-recoverability-v2.json，不加载坏模型、不修改坏文件。

真实CPUtorch31.508832s原wait/结果已独核：旧raw callback2147549184请求只返回2147479552，torch.load失败；新实际BudgetFile循环write-all后完整torch.equal通过（CUDA不可用/无nvidia设备）。原151兼容组仅diagnostics.py旧71197199…→新55cdcc89…必要字节写全，其余150同；独裁IO-WRITE-REPAIR-PASS-v1.json PASS_IO_ONLY，非真实21GB native full恢复验收。依据[SRC1456](../../../../../SOURCES.md#src-1456)，首r3正确fullsave/native restore仍需实际核。

r2失败实际记consumed250000、physical250213（pending213）、updates24975、周期评估196完成；新历史eval1372，新global allowance11964，r3有效未来仍10592（9408+1184）与四3M不减。必要同seed/config从头r3，不冒称精确续训。新envelope resource-envelope-v2-r3.json绑定IO独裁/失败原件/历史计数，54h工程forecast、原160h/16GiB/2TiB及真实截止保持。外部reviewer改run-specific context绑定新source/budget、future从初始budget动态取54h，不再硬58h；尚待r3源冻结后重签控制面。


2026-11-04T16:32:44.452229+08:00 · 必要修复收尾/恢复后台：r3 source b8f3d63b…154c05（184源；相对r2仅BudgetFile write-all、精确150+1兼容/1372历史及11964全局额度三源改，181同）已定点独审PASS；新r3程序协议save-repair-v1/real-contract-program-r3-v1.json，首infra已签。外部reviewer实际review-allocation CLI在r3 exactCIDf9a2d1be788c3900eb4db17134027b577caf289a1d097be6af15eb0ceed54333返回PASS并copy阶段令，父已execute/采用后台。

外部reviewer现SHA497f8277d7f916b4c7198df7ee2a58fbfe17753d531cae8ec1e4346e6aa51d2d，授权external-reviewer-authorization-r3-v1.json，run-context绑定当前source_review/初始54h budget原件，未来总有效回合按stage总数10592、不从失败196减；父确认新daemon1242328/PPID1已OBSERVING_EXISTING_STAGE，worker1241380/GPUe2eab186…d587继续。旧r2 reviewer原0d77SHA精确恢复为external-reviewer-r2-archived-v1.py，旧失败不覆盖。最终B–E与final仍需用户回来后实际验收，后台八stage自动推进；不新开只读轮询。

r2失败最终实账r2-failed-profile-final-accounting-v1.json：exactCID3d6967…24fea exited137/PID0，Started07:20:35.429573489Z→Finished08:13:49.573959826Z，actualGPU allocation3194.144386337s；actualrootwait3150.660100661s/exit1；paused profile wall3110.388251087s。三者嵌套分列不相加，GPU已含r3初始化历史物理全窗保额不重复扣。失败consumed250000/physical250213/updates24975/eval196均保；旧新总科学消费分开，r3从头同种子配方有效3M、不叫精确续训。修复准备/CPU回环按AGENTS独立成本记，不占有效训练预算。


2026-11-04T22:32:00.651248+08:00 · r3外工具等待丢失后的定点恢复：原app工具outer writer消失且wait-receipt未发布，事实保持MISSING_KEEP_UNKNOWN，不制造outerexit0。复用实际native owner/guardian/watcher退出0/chainPASS、profile-worker PASS、exactCIDStopped/PID0、原生完整restore250k/24975updates/3Mlimit/pending206及CUDA参数/replay/moments。full profile.pt 21553028319B完整有效；普通save163.568574s、extra profile save166.464205s、native restore27.581371s。只读校验与一次必要fullprofile引用签名；首次external日期解析因hostPython3.8不支持Docker9位小数失败，修外部整数纳秒解析与小snapshot幂等后恢复成功，未修改native/checkpoint合同、未训练新250k或重评196。

独立恢复授权authorized-native-recoveries/t9.11-real-program-20261104-r3/profile-C-4718.json；独裁automation-r3/profile-C-4718/review-stage/profile-C-4718-verdict.json SHA c872bfa1b1505aa0feec41f582f0f9d57f98f4062ce7dba7ac6438f075b1e70d，out/reviews已写指针。actual ownerwait3075.716874s、workerwall3046.962832s、GPUallocation3138.495394s；worker_enclosing_upper5520仅批准cap+tail政策预留，分列而非实测/吞吐。mature50k非周期275.578267s，remaining proxy30689.661461s；用实际owner/profile与成熟成本推全余174586s=48.496h（5%工程工作量变化+原final4h/control6h），不机械沿旧54h。工程预计非物理硬上界，stage原实际cap/截止仍守。

仅外部reviewer增加须独立授权的native闭合fallback、纳秒日期兼容、基于actual成本forecast；4定向fixtures通过（缺授权拒绝、保outerUNKNOWN、native前序JSON可读、固定quota与issuer）。最终reviewer SHAed764a7d57d552897087e7af89aa44b24338976bfc8c68f133e274a7b4fa47aa与external-reviewer-recovery-authorization-v1.json已交父；native源b8f3不动。formal_entry外部driver修持有独立子进程/缺outer时只在native证据闭合后交独审。父可--resume直接remaining，确认实际步数大于250k后按用户原意退出监督。最终B–E及final仍待实际验收，不伪PASS。推荐GPT6.1sol/high、Sonnet5.5/high（恢复因果），实际未知。


2026-11-05 · 2250k完整状态恢复，旧FAIL/22789.560684s与签字竞态0科学消费均保；最终attempt2授权/bridge/自动aggregate/有限38.718h forecast已交。详见[本次独审](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/20261105-codex-2250k-recovery.md)。native b8f3不改；后台实际loader与待评2250k进度由父现场确认，未宣称已完成3M/final。推荐GPT6.1sol medium、Sonnet5.5 medium，实际未知。


2026-11-05T10:23:06.439911+08:00 · 2250k恢复已真实启动，后台active（不代表3M/final完成）。父现场确认attempt2/restore.json PASS_NATIVE_FULL_RESTORE，原生一次load64.117379s：steps2250000/up224975/env2250192/pending192/validation_pending2250k/config原冻结；network/replay/optimizer moments CUDA0，原CPU optimizer step保持。待评2250k已实际开始，新writeahead16/own1584，events约1.4MB持续增长；旧8周期1568没有重跑、没有回退250k。后台hostworker1760315、control1760146、PPID1独立runner1760145，GPUe2eab186…d587。

最终授权recovery-2250-v1/resume-authorization-v3.json（4241c0fb…cb566），attempt2目录与restore/worker.txt/bridge每PID安装日志可核；14400含save1800/control120，lease14640。自动完成后仅外部review-recovery聚合oldFAIL22789.560684与newPASS实际，2352/3M299975/12周期符合才签原remaining综合PASS并driver --resume继续L；旧attempt/FAIL、pre-model0科学失败与18.686824sGPU费用保留。模型源b8f3/protocol/checkpoint原字节不改，作用仅已授权3reader bounded ENOENT重扫及readonly loader结果观测；最终B–E/final仍待独立科学验收。父按用户原意交接后退出主动监督，无新增人工轮询。

范围/负责人：本子继续保最终结论职责，日常由已签独立外部validator/issuer与driver执行；三文档递归规则不变，无新增下层任务。推荐GPT6.1sol medium、Sonnet5.5 medium（恢复因果核对），实际模型/强度未知。


2026-11-05 2969467 收尾恢复：状态 active。推荐 GPT6.1sol/high、Sonnet5.5/high（跨进程恢复及并发资源隔离）；实际平台型号/强度未知。仅新外部控制/独立聚合，native b8f3 与 sealed r3 科学合同不改。统一资源政策位于本子日志 recovery-2969-v1/unified-resource-policy-v1.json，52h 唯一共享分配，不重复领取余额；96h 历史 worker 为政策预留，非实测。新恢复授权 resume-authorization-v1.json 从原 interrupted2969467 一次原生加载，2156 既有评估保留，仅余30533转移和196周期；前 nativeFAIL、recovery2FAIL 成本按不重叠真实 envelope 保留。C 结束后独立 aggregate，再等待已签两卡分派。依据沿用户 [预算审核授权](../../../../../SOURCES.md#src-budget-review-20261104)，新统一政策原件已交父登记来源，未把工程预测当实耗或精确历史。

本轮来源已统一登记 [SRC-1461](../../../../../SOURCES.md#src-1461)（三文档相对路径适用；独立日志引用 forem/doc/SOURCES.md#src-1461）：统一政策、恢复授权、成本分类、实际恢复与新增并行定点核查。15:21 父读取实际已保存3M/299975/env3M，末周期已开但尚未完整，不能提前标run PASS；旧stop_reason为保存的历史字段，以当前进程终态/评估完整证据为准。


2026-11-05 15:34 · 自动接续部署 ready / 原训练仍 active。依据 [SRC-1461](../../../../../SOURCES.md#src-1461)，本轮仅核恢复与外部并发控制受影响路径：

- C2969467真实原生恢复 PASS，末3M训练保存已发生，末周期尚未完整，未提前宣称 run PASS。原 native/source/protocol 与所有先前 FAIL/UNKNOWN 均保留。
- `parallel-run-v1/budget-review-v1.json` 将当前C已签10800秒作为 POLICY_NOT_ACTUAL 计入上界一次，future由52h减为49h；总分配不变。worker/GPU上界397590.857310/383181.065793秒，未来176400秒，仍分别低于160h；16GiB诊断与2TiB、真实截止不变。
- `parallel-run-v1/authorization-v1.json` SHA ed862a67567636e054fd04a066ee45e019cd53b4e9154575aa4048b034e5a175；`dispatch-ready.json` SHA 791f8ea43a811b78df31e92544b8dc7569729aa57748f476158b2e332d668bed。无需LLM等待C实际终态再签，原C controller会在其真实aggregate PASS后读已签dispatch。
- 新外部 `task9_11_program_shards.py` SHA 3bf240b99b35c680a19f892f36698b1b2a2d302365ea0899220a2bb70c000e42；独立 `task9_11_parallel_review.py` SHA 691dacfe042a3ccf17a711075c203273286afb9b36794e8605294ad2ba88aede。共同冻结后不再改。
- 已复用实施3项metadata定向：HOST可读container refs、GPU0/2原序调度及14h共额、Docker创建后Popen失败仍exact-owned cleanup与成本；独立fixture核profile/remaining证据、2352自有回合、拒错误UUID/结果漂移与有序发布。实际 load_context/check_authority/PASS callback已运行，当前诚实等待 remaining-C-4718，未伪造结果。
- GPU0=L4718、GPU2=C4719，空卡续L4719；每run profile与remaining实际outer共扣50400秒，不给两阶段各取14h。controller唯一全局扫描并保2×40GiB保存空间，各worker仅ownformal及ownlog扫描。每job2352周期回合，四有效run各3M不变。泛 evidence 仅JSON，小JSONL快照和大profile SHA放专用 profile_evidence，避免后续append漂移或JSONL误读。
- 停止：仅本批控制 STOP 为 out/parallel-shards/STOP，controller有界要求own workers保存并核本批immutableCID stop；不动其他任务/GPU1。各独立worker沿原 ownformal/STOP 与真实deadline。异常保失败/真实cost不自动盲重试。C controller相关状态见 out/recovery/continue-2969467-attempt1/status.json；并发接管后见 out/parallel-shards/state.json、out/shards/JOB/PHASE/result.json。
- 所有四run完成后明确 THREE_RUNS_COMPLETE_REQUIRES_SCIENTIFIC_ACCEPTANCE，最终B–E验收及1184 heldout测试仍按原协议，不能假PASS或提前偷跑测试。退出LLM持续监督不停止真实训练。

推荐GPT6.1sol/high、Sonnet5.5/high（跨恢复/设备/预算交叉核查）；实际平台型号强度未知。

2026-11-05 当前修复增量独审派发：负责人Codex独立reviewer，推荐/请求GPT6.1sol high（用户允许sol/terra/luna；复杂恢复边界），Claude推荐Sonnet5.5 high。仅审核.18.4两个外部脚本、定向测试及零步恢复证据；输入.18.4/RESULTS与authorization-candidate。只写自身独审子目录与日志，禁止修改实现、共享SOURCES/PROGRESS、启动模型或训练。通过后另存授权新版本/增量结论，保留旧授权与原始证据；有问题先报父，不签通过。实际执行尚未开始。递归规则仍保持，父核交付和受影响路径。


2026-11-05 shard修复增量独审：Codex/delta_review active，12项无模型控制测试PASS；独立copy/save注入发现prepare_zero_retry准备异常后不可重入，save失败先清STOP，已交父修复，尚未签新授权。证据与授权边界见[本轮独审日志](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/20261105-codex-shard-repair-v2.md)，依据[SRC-1462](../../../../../SOURCES.md#src-1462)。推荐GPT6.1sol/high、Sonnet5.5/high（恢复准备/成本证据），实际平台ID及强度未知；递归规则及原最终验收职责保持。


2026-11-05 shard修复增量独审完成：done（仅外部控制受影响路径）。依据[SRC-1462](../../../../../SOURCES.md#src-1462)，原copy/save准备不可重入与先清STOP问题已修，独立注入复验成功；后续发现新同空内容STOP误删，已改原token size/mtime/inode+SHA核对并复验保留新STOP。15项当前控制测试实际退出0；既有3项wiring沿父有效证据复用，未由本独审重复。独立费用fixture核60000s失败费超14h拒绝，18.7s失败费/证据在profile与remaining各保一次。

新独审[结论](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/shard-repair-v2/delta-verdict-v2.json)及[外部授权v2](../../../../../agent_logs/task9/task9.11/task9.11.18/task9.11.18.2/shard-repair-v2/authorization-v2.json)保持reviewer task9.11.18.2 / PASS_PARALLEL_SHARDS，两callback均指新授权自身；授权SHA `eb79300b873d4fcd0b1bcebba87798b81f6539fa96e481fcd339f42ad14a159f`。两修改脚本实际冻结SHA：shards `5749cdffc3a055c311b7533a0241f5a23bc336c762b3cf027ba92d4c666146b1`，parallel_review `aa46f610b5ef74a0c85dc55777faf7f16b0518b697a630c464b0b62776e3fef7`。其他协议/策略/配置/预算/未改适配器引用与旧授权逐项比对相同并直接复用，未全量哈希资产。

当前C4718实际3M的既有证书保留，L4718真实旧零步失败及18.707820415496826秒费用保留；本独审没有对真实run执行prepare、原生加载、仿真或训练。通过仅表明所核本次控制路径未发现遗留具体问题，不代表实际零步full恢复、科学提升、四run或最终B–E/heldout验收完成。交付父执行者且按最新用户要求仅交付不启动。最终科学验收仍由原task9.11.18.2角色负责。推荐GPT6.1sol/high、Sonnet5.5/high（恢复/停止/费用交叉核对）；实际父派发GPT6.1sol，平台model ID与继承强度未独立暴露。递归规则保持，无新子节点。
