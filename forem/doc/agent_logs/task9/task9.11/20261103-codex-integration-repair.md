# task9.11 集成修复与独立审核

开始2026-11-03T22:19:23.656939+08:00；负责人Codex；父实际后端/强度未知。用户指定主设计及独立审核sol/high，推荐GPT6.1sol/high、Sonnet5.5/high，因跨入口状态机、进程生命周期和预算身份需整体审查。授权仅R1–R5入口/监督/计费/续接/审计必要代码修复和零模型零环境零真实Docker替身；禁止真实实验、科学变更、旧原件修改、STOP迁移和重置预算/截止。

已读根/forem AGENTS、README、PROGRESS、ENV、父及.7/.8三文档、end-to-end-review及JSON、SRC1402–1406、旧STOP签字/原始证据。HEAD d198e5ca48f86071c05274f9da753f393ce058b4，现有dirty全部保留；活动最大子号.8，本轮新增.9集成实施（.9.1生命周期、.9.2续接）和.10独立审核。进程核查无task9任务；task10进程在另一树，禁止触碰。

## 冻结修复合同 v1（实施前）

这是本轮代码验收合同；有限会计边界及旧C替代均只是非执行候选，不应用于真实入口。所有真实入口必须拒绝execution_allowed:false候选；替身依赖注入只替换外部执行，保留生产协议、准入、依赖、计费、记录读取。不得mock这些生产函数。

生产链：prepare冻结协议/源配置身份 → supervise生产阶段清单 → dispatch串行锁/协议/准入/资源/预约 → outer实际wait(owner) → owner实际wait(guard) → guard实际wait(watcher)且收割worker → watcher核worker结果/absence或精确停止 → outer验证receipt并闭账 → 同版生产准入进入后继。worker继续二次验证release/依赖/预算。历史原件只读引用，绝不当新PASS。

状态/写者/读者：PREPARED由prepare写freeze、host/worker读；RESERVED由dispatch写不可变reservation和活动、guard/watch/准入读；RUNNING/WORKER_EXITED由guard写worker-started/result、watch读；阶段PASS/FAIL由watch写record+terminal，outer读；候选CLOSED由outer在实际wait和receipt全核后写独立closure，activity_rows读。FAILED或UNKNOWN无合法后继，旧格式PASS无closure不得接受。同已完成request只允许同namespace/protocol/code/release/reservation及closure跳过，不启动不重复计费；过期令仍拒绝。

身份贯穿run_id、phase/arm/seed、protocol SHA、code artifact SHA、release SHA、reservation nonce、PID/startticks、waiter及receipt SHA。协议与证据支持明确宿主/容器路径映射，历史引用类型与活动身份隔离，reviewer精确绑定。

有限候选会计边界：被测job从实际启动（含owner/guard/watch/worker保存和退出）至outer实际wait返回；子区间不叠加。监督前置/检查/发布/停止控制另计控制session，须显式覆盖发布成本或保持UNKNOWN，不能假造0。候选策略若使用控制包络全额收费，标工程上界/待批准，不称实测；超过包络、缺证、盘错、未收割全部UNKNOWN/FAIL。真实旧合同未接受此变更。最外层死亡须由现有watcher监测其精确身份并停止任务，无需无限新增监督层；全监督同时死亡/主机断电仅可隔离UNKNOWN，不保证写终态。

所有停止和退出在原cap内部留预算；超时/身份读取失败/读取损坏/发布失败必须有界精确停止和收割或UNKNOWN，故障证据尽力持久化，持久化失败本身不放行。

续接候选DAG：新代码G1 → 待批准的旧C科学证据+新生命周期门 → L ON196 → C4718/L4718/C4719/L4719各profile→remaining → development独立release → 一次final独立test。禁止四smoke重跑与额外C ON；旧C完整门FAIL保留，不批准则候选不可真实执行。统一prepare/protocol/evidence/prerequisites/host jobs/worker/release，不仅解一个门。

预算不变：已4000smoke/980评估，正式0/test0；smoke余额0；10788=196+9408+1184，无额外C ON；原T0 2026-11-03 17:18:20+08、deadline 2026-11-06 03:18:20+08、58h/2TiB/8GiB及40GiB保存包络继承。全部新准备/审查成本追加，未知不作0；成熟profile/真实GPU/Docker验证留后续获批阶段。

|需求|实现/责任|验证|证据位置|未解决项|
|---|---|---|---|---|
|R1 G1隔离|父worker白名单/独立stdlib入口|AST实际argv/conftest/传递导入与收集清单|.9 integration evidence|真实G1不执行|
|R2正常闭账|.9.1 supervise/admission|生产dispatch/准入/计费正常完成→下一阶段；幂等|.9.1与.10原输出|会计候选真实接受待决定|
|R3异常封口|.9.1 supervise|outer超时/最外层死/守卫故障/损坏/身份失败/盘错/缺receipt；启动四竞态|.9.1与.10原输出|全监督死亡不保证终态；真实Docker尾未知|
|R4合法续接累计账|.9.2 prepare/continuation接口，.9.1接入admission/supervise，父worker|同生产链路径/SHA/reviewer/依赖/旧账/预算/漏外部成本拒绝|.9.2及最终E2E|旧C及历史UNKNOWN须用户决定|
|R5双侧配对|父audit|JSON重复/缺失/额外/域/角色/固定身份集合|.9 audit evidence及.10|描述性audit不签release|

## 待决定（本轮不应用）

1. 建议用旧C科学非干扰原证据只读引用+新版本生命周期替身及后续真实G1验证承接C门；影响是验收组合变化，旧完整门仍FAIL；替身不证明真实Docker生命周期。坚持原整门则无C ON余额，不能执行。
2. 建议接受有限job-wait边界与另列控制session的候选成本协议；历史缺失exit和未定时准备继续UNKNOWN。历史成本须额外原始证据或用户明确保守计费政策，不能由实现者填0。
3. 本轮不签真实实验许可；待上述决定后需独立release及真实资源/profile可行性审核。

变更目标必须追加说明并保留本冻结版本，不边修边降低验收。证据尚未执行。

## 首轮父实现验证 22:24 +08

R1 worker显式test_contract.py白名单，rootdir/confcutdir固定，禁外部pytest插件及继承ADDOPTS/PLUGINS；stdlib禁导入断言保留。发现原G1科学测试内prepare用例仍期待已禁用入口，更新为候选不能create的断言，实际正路径由stdlib替身覆盖。R5配对双侧去重，每个checkpoint/域固定分母、独立冻结seed输入身份、final manifest和role/source/stream核验后才统计，仍描述性不发release。

entry-attempt01 runner根路径计算多一层，cwd错误导致python找不到文件，rc2/wall0.016018s；未运行测试，原失败/source空清单保留。修runner为workspace路径后entry-attempt02十项stdlib测试PASS/rc0/wall0.6150446s（含40个域错误subcase），静态预测科学收集14项，没有运行科学GPU套件。当前代码仍在并行修改，此PASS仅开发反馈，最终同冻结SHA另跑。原命令/stdout/stderr在.9目录。旧STOP/七引用及原始非干扰JSON读取核SHA一致，旧模型仅stat；历史保护清单见historical-evidence-protection.json。

## 集成补齐与候选处置建议（22:33 +08）

.9.1首版实际dispatch链13项开发PASS含完整14stage DAG；为满足用户“合法准备→启动”单链，.9.2新增生产freeze_candidate_protocol/--candidate-protocol，make_fixture改为真实prepare冻结而非手写freeze，仍只temp JSON/四配置与源身份；真实candidate只review目录不可执行。会计job起点将精确放Popen调用前，至actual owner.wait返回；预约/spec及outer检查归control，不扩大child absolute cap。只有待批准candidate包络，不声称外层发布尾实测闭合。

R3父读首版提前识别closure发布后fsync异常仍可能留可读CLOSED及慢发布超包络；.9.1已以pending拒绝marker、发布后成本检查和完整证据key集合修复并新增反例。marker失败保留拒绝，避免无限外层。全部开发结果最终统一SHA另跑，独立审只接最终版。

进一步具体建议（未应用）：若旧C原actual wait日志无法恢复，可请用户批准按原已释放cap1800s全额核销该失败尝试，替换当前outer→inner已知625.185549736s下界（差1174.814450264s），分类工程会计选择，不能称实际wall上界或actual exit，不改变旧FAIL。来源旧activity gate-evaluate-C-4718 cap_s1800和原launch/inner时间差，仅拟议，不计入当前余额。其余历史监控/父准备须逐项有可核起讫/并行度外包络，否则仍UNKNOWN阻断；不建议随意填统一余量。旧C科学证据复用、新有限成本边界及续接实验许可分别待决定。

新预算脚本仅新增.9/.10递归命令实测下界，所有非命令准备与审查会话尾明确UNKNOWN；全局日历持续扣减。22:30:33快照calendar余190066.155s，按原formal+test阶段52h上限情景余2866.155s给G1/LON/准备/独审/退出及UNKNOWN，不构成可行性证明。

## 独审v1反例与集中v2修复（22:36 +08）

统一v1 artifact cac60c826133647e7ca515a32cc65bc5b2d3f644784decbd7c9e645e767f8c05/164文件，父与独立各自40+13+15+11均rc0；这不等于整体验收。独审另写反例发现：1 audit读C路径后按内容中的L身份选择另一文件hash，C/L冻结替换被接受；2 最后pending.unlink耗时越控制包络仍CLOSED；3 candidate已有CLOSED时无adapter生产dispatch在拒绝门前返回already_passed。全部原FAIL留.10。父已修audit为先按预期filename hash再parse且group/seed精确对齐；.9.1集中修后两项。

另补实际worker二次准入：Python-only execution_adapter仅接受temp synthetic候选；真实CLI无此参数，仍拒candidate；替身在production worker.main的protocol/release/prereqs/resources/ledger后才运行，callback仅marker/等待/返回，真实GPU/模型/环境代码不进入。以此替换旧仅marker worker，避免正向测试绕过实际worker入口。v1所有原件保留，不挪作v2最终PASS；v2需同新artifact完整必要回归与独审反例复验。冻结合同目标/预算/科学/真实禁止边界不变。

## 最终代码与独立原件接受 2026-11-03T22:48:48.791274+08:00

.10最终正式裁决e284186e…b3547，父已核54引用SHA、86项原输出/rc/source前后一致，与本地最终artifact1ba4e989…9105b1/164文件一致。父同v3四套81项及独立5反例/兼容11项通过；final_protection核160旧保护只6授权改变、48历史证据与688旧产物stat均未变。v2复合盘错rejected被忽略反例已修为pending/rejected均拒，原FAIL保留；源码已停改。

最终事实汇总写.9 RESULTS与父RESULTS§13、SOURCES1408–1410/PROGRESS/DECISIONS。预算22:44快照worker下界4010.8965s、exact null、calendar余189253.1403s；后续文档/独审继续扣，交接末时点另补。所有未知保留，无真实Docker/GPU/模型/环境/回放/smoke/训练/test；不签真实实验许可。

交接末时点2026-11-03T22:49:17.558635+08:00：worker下界4011.0108699s、余仅上界204788.9891301s，calendar余188942.4413650s，原52h情景后仅1742.4413650s；exactnull/UNKNOWN保留。15任务文档递归/链接与gitdiff0已核。所有代码停改，本轮done仅集成修复/独审交付；真实仍NOT_READY。

末核22:50:46+08：.10预算九项PASS补注SHA60ad5cd3…17c8e，正式verdict原SHA未改；final-delivery-integrity.json核最终source/54引用接受裁决/15文档链接/gitdiff0及零替身残留通过。最终交付done，真实NOT_READY，没有本轮后台任务；不运行真实实验。后续收尾成本继续未知/日历扣减，不当0。
