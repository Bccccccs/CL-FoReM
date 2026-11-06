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

## 23:15成本与分工补注

单一sol/high .11联合实现clock/动态costs及四core接口，父确认：历史release/snapshot expiry不追溯已完成；新启动/current资源检查需最新审查快照；历史用原snapshot+可靠实际启动/actualwait证据。动态成本独立reviewer身份与旧static role须明确，嵌套关系不能仅任意parent标签抹成本，事件source和event两集合coverage都核。独立.12已建立164基线/54旧引用及878原件保护/联合负例清单，未对mutable实现或未执行功能给PASS，待稳定SHA后触发。

只读预算脚本cross_stage_budget_audit复用.9旧累计下界并递归新增.11/.12命令，不漏审查准备；非命令会话和当前发布尾仍UNKNOWN。实际budget-initial rc0/wall.1143654s，时点2026-11-03T23:15:55.013795+08:00：worker下界4050.3040324s、余仅上界204749.6959676s/exactnull；calendar187344.9862053s，减原187200s阶段上限情景仅144.9862053s，之后继续扣。不能证明完整方案可行，不缩步/跳评估/延时或启动部分实验。

## 联合实现开发反馈与范围内接口检查

.11报告cross-dev05/06联合正向已通过（开发SHA，非最终）：真实prepare/dispatch/worker.main/actualwait，fixture推进3600s越旧令/旧snapshot expiry，新增实际stdlib审核命令wall/event，新snapshot＋下一stage成功，历史幂等/原件SHA不变；21项开发PASS待统一冻结重跑。父未用此自报代最终PASS，独审仍等稳定源。

父提前只读发现并发锁_DEPTH仅pid/root会令不同线程误重入，已请.11改thread-id并加真实线程/进程并发验证；又发现dispatch预约后锁外真正worker Popen的成本竞态，要求guard末次资源检查→Popen与append/review共锁或等价generation原子门，禁止只以reservation当科学worker已启动。既有R3 handshake/四资源故障仍保留不降验收。

read_release新拒caller clock会使实际G1 test_contract旧测试正常调用失配，父授权仅该专用接口断言调用调整（正常用可信默认、显式caller时间拒），不运行GPU测试、不改科学测试算法，保留14项白名单/禁导入断言。snapshot累计需生产完整资源统计，显式revocation资格阻断与已计费用分离，不删历史费用。上述均为本轮F1/F2必要接口/同类跨阶段检查，目标/预算/科学未改变。

## 首次统一冻结与独审F2漏费反例

实施v1已停改，artifact ae070d9978376fe6f9dd9213bc2b99a22dd7197e76b553b5f6f06f2ffd3e8068/167文件；父统一25+40+14+15+12=106项均PASS，独立同106＋自写联合8项亦PASS；这些不是完整验收。独审实际发现costs.review第二版snapshot记录review_started→completed .004763616s/调用.006214503s，而cumulative.worker103→103、added0，无已闭stage/controller费用覆盖，independent-review-cost-v1 rc1原FAIL留.12。

父明确这是本轮F2代码计费缺口，已同批退回.11；候选修法要求独审payload实测费用与source/event/审核及最终snapshot发布控制session分列、当前快照自身立即入账、重复生成每个独立session恰收费一次；可沿既有candidate工程包络但applied:false，不能改真实会计合同或称实测上界，不无限加监督层。控制超包络/盘错/不完整receipt必须拒绝；历史snapshot原前序/旧费用保留。独审原断言不删不降，待新冻结后复验和完整必要回归。此前版本PASS不迁移。

## 费用控制session补丁与并发截止边界

.11与.12确认v1原漏费断言不改；候选补丁三种独立publisher control session：source发布、event追加、snapshot review/publish，各新session全额沿原候选30s包络计一次，payload子进程实测wall单列。每个预约→artifact SHA→完成receipt，pending/rejected否决；当前snapshot计自身control，原history只核原snapshot/controls前序。30s仅非执行synthetic工程收费包络，applied:false，绝不当真实参数/上界或用户批准，不增加监督层。新小stdlib cost_control.py属必要F2接口。

父继续要求新controls路径canonical/禁止symlink越界，及cost.lock阻塞等待若跨global deadline须可信clock有界停止，不能等锁holder自行释放才发现过期；不新加任意真实timeout。queue等待不重置deadline，globalcalendar始终包含，未知会话worker仍UNKNOWN。本轮不改变科学/用户待决边界，新增项均落实F2完整计费、并发与绝对截止验收。

## 第二次统一冻结 2026-11-03T23:39:40.010258+08:00

v2 artifact c8523c9aecc314ce7ae0e71fd16e41ad9531aaf4e3e1315576ecd4d7411ef177/168文件，source-freeze-v2与逐字节snapshot已封存；.11停止代码，仅文档，.12已触发稳定v2审查。新增cost_control三类source/event/review发布控制session完整包络当前入账，原独审漏费断言不改复验通过（133→163新增30），真实会计仍pending/applied:false。35项专用加40/14/15/12必要回归共116项由父同SHA进行，独立再复跑并新增反例；不迁移v1 PASS。现有改动5个源码/专用测试，其他科学/worker/audit/配置与旧证据保护；均在本轮必要接口范围。成本锁线程与进程、真正worker Popen原子区、持锁跨deadline、event journal和snapshot prefix历史隔离纳入同一验收，不额外功能。

## 父最终同源接受 2026-11-03T23:51:55.893811+08:00

168源c8523c9a…11ef177保持；父116项、独立130＋1归档执行全部rc0，正式裁决e93698b5…32636c/158refs核真。101全联合原字节文件（原temp路径→归档只读映射）SHA全部匹配；59历史证据、独立878保护及原输出688项stat不变，159旧源码不变，最小diff仅5改＋4新。parent-acceptance-v2因before路径误用rc1，v2a修汇总脚本后rc0；未改实现，两个原输出都保留并记账。主表/状态/角色/实际命令/剩余决定已入父三文档§15与.11/.12。模型推荐sol/high与Sonnet5.5/high，实际UNKNOWN。仍无真实实验许可，候选30s控制政策pending/applied:false，历史UNKNOWN不核销；最终预算时点另附。

## 交接时点预算与责任 2026-11-03T23:54:39.967393+08:00

budget-handoff-v2-command rc0/0.1645959634s，同168源未变；23:53:06.244426+08快照208组件/50新runner，worker已知下界4441.072344993s、余额至多204358.927655007s、exactnull；日历185113.755574465s，原52h上限情景差−2086.244425535s（−34.770740min），不等于实际必需52h，不证明可行。3归档nested仅经manifest/outer证明去重，虚构2/3s不混实际账；新预算/验证及文档发布尾仍UNKNOWN，不无穷追加自证层。原58h/2TiB/诊断8GiB/40GiB预留、4000/980/formal0/test0/10788分配/deadline不变。准备、独审、等待持续计。

已更新父与.11三文档、SOURCES1413–15、PROGRESS；.12独审自写三文档和正式裁决不由父改。父纯证据汇总v2a PASS，独审成本补充首轮因ISO微秒舍入4.768e-7s误差错误判FAIL，保原件；仅明确序列化1µs容差，不改费用/hash/source验证。最终补充另核。待决：旧C门组合、有限job/control政策及真实取值、历史UNKNOWN处置、execution协议/许可；真实入口刻意未接通，准确只读重核命令见PROCEDURE N。无需重开F1F2局部准备，但合同变化可能需要定点适配；G1/成熟profile/真实Docker尾仍须之后获批实测。未重启旧run/未触摸task10/未推送合并。

## 最终完整性封口 2026-11-03T23:55:55.826961+08:00


最终交接完整性封口（2026-11-03T23:55:55.826961+08:00）：[final-handoff-integrity-v2.json](task9.11.11/final-handoff-integrity-v2.json) rc0，源168、正式158引用、旧59/878引用及688输出stat均匹配，90处当前交付本地链接有效、git diff --check rc0，本轮替身进程0；未停止其他任务。最终预算补审SHA `008575c306b072ddc7959751645e1c2c09bac13d60604f198b35736ea8ec2eb6`。23:53快照后已有闭合runner另计0.392825851s，已知worker下界增至4441.465170844s；本次最终检查自身0.1645327061s另有原command，文档/当前完整会话及退出发布尾仍UNKNOWN，不声称精确余额。上述时点账不作为当前可用余额。[SRC-1415](../../../SOURCES.md#src-1415)。

最终.11/.12与父工程交付done，真实NOT_READY。已测F1/F2无待修复可复现项；有限会计/旧C/历史UNKNOWN/真实许可集中待用户决定，主任务停在本轮交付。
