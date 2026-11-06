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
