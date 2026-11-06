# task9.11.13 · GPU两账修复结果

状态done，v3同SHA父132项/独立54项及5689引用原件已接收；真实执行NOT_READY。负责人Codex；推荐GPT6.1sol/high、Sonnet5.5/high，因设备区间/累计费用/跨阶段身份核验；委派请求sol/high，实际模型/强度未知。[SRC-1419](../../../../SOURCES.md#src-1419)授权；实现与实测关联[SRC-1420](../../../../SOURCES.md#src-1420)。

## 当前交付与历史失败

**当前最终v3** artifact **0bbda355c9eaf3018b7f73a27fc033e346dc06d7c0b2b940d1334fce7476c1a9 /170文件**，[source-freeze-v3](../../../../agent_logs/task9/task9.11/task9.11.13/source-freeze-v3.json)、[完整源](../../../../agent_logs/task9/task9.11/task9.11.13/final-source-v3)、[最小diff](../../../../agent_logs/task9/task9.11/task9.11.13/minimal-v3.patch) SHA256 da936d088c92913e383339546d1be02c806cb7894ff0141674356b64e993f104。v3仅在v2基础补首basis身份三方一致/非空必要核验及4个缺失/矛盾fixture反例；专用16项。以下v1/v2数据均保留为历史，不能迁移为v3通过。

v2（历史）artifact **c53aa98688aa69b058b36bdae3113b5ca500213b91f83ba0abc614945798aff7 /170文件**，由与原版相同的runtime.artifact_files/digest方案冻结所有相关源码、脚本、配置及测试；[source-freeze-v2](../../../../agent_logs/task9/task9.11/task9.11.13/source-freeze-v2.json)、[完整源快照](../../../../agent_logs/task9/task9.11/task9.11.13/final-source-v2)、[最小diff](../../../../agent_logs/task9/task9.11/task9.11.13/minimal-v2.patch)（SHA256 2b6007218c7b6584081156c6a68b92552e7f32073554d85c6348946d8ca14527）。原168源160不变、8必要修改、2新增、0删除。工作区原dirty和用户/其他Agent改动保留。

v1 db02314e…1175b7a的12项专用与父回归曾通过，独立原反例证明已审container start可改晚/stop可改短/record可删/设备可共同改CPU而减少GPU。原v1冻结、所有PASS、独立FAIL原件均保留，不能当作v2通过。v2修已审basis绑定并补正/反例；独审随后确认首次record/current共同改alien而sealed保持原Id仍可被初审采纳，原FAIL保留；v3加三方Id严格核验。静态legacy容器没有固定时序basis改为UNKNOWN，原旧5s正例仅保历史；等价的dynamic独立已审5s idle正例保留GPU完整窗口计费。没有放宽独立负例。

## 最小实现与全部账路

|生产者/消费者|处理与边界|
|---|---|
|inherited_accounting|保留原worker/GPU aggregate；新增GPU完整区间证据与aggregate一致性核验；缺证UNKNOWN，已包含command区间必须在历史并集内|
|static validate_external_costs|原冻结完整库存/原件SHA不变；每项包括已包含command也核GPU证据，worker只加未继承项，GPU回传区间以便全局去重|
|dynamic costs.inventory|原source/event/journal/parent/control完整性合同保留；worker=非继承base+最外层payload+原control，GPU=全部已证interval并集，不加CPUcontrol|
|measured_command/publish_source|measured_command须显式gpu_devices；只支持已说明的inert synthetic归属，实际start/actualwait终点绑定source。真实归属API尚缺，UNKNOWN；publish_source不认证真实payload|
|container current/stopped/idle|原inspect精确Id/授权DeviceIDs；Count/all/未知拒；持有窗口完整算GPU，与历史/事件取并集。v2约束独审原basis，不能改start/设备/已停end或丢record|
|admission.check_resources|同production入口合并所有GPU区间，保持worker原账；reserved_gpu_seconds/proposed_gpu_seconds/resource_reservations分列，原reserved_worker_seconds仍仅active余cap+control，proposed_worker_seconds另列|
|supervise/actual worker|supervise新申请worker=cap+CPUcontrol、GPU=cap；worker原main未改，再读新release/先决/资源及写前ledger；其已有host cap不重复预约|
|costs.review/snapshots|同resource私有核算；snapshot保留真实核算时点、完整GPU并集与容器原始basis；已用、预留、limit-used、扣预留后余额分列。历史snapshot/release/closure不改|
|release/remaining/next stage|原独立release绑定当前snapshot、预算和时钟；未审新费/stale拒；新snapshot后续行；历史合格closure自然到期保资格/保费用；显撤原合同不改|

`gpu_costs.py`与专用test为2新增；8修改为admission/continuation/costs/supervise及四份stdlib fixture（continuation/cross/lifecycle/supervision）。fixture只补明确synthetic归属、measured_command显式CPU输入及可信观察时间；唯一旧正例语义收紧为无basis旧容器UNKNOWN。cost_control/worker/runtime/audit、科学配置和原实验数据不改。

## 同源验证与原件

历史v2专用命令及结果以[final-v2-gpu-command.json](../../../../agent_logs/task9/task9.11/task9.11.13/final-v2-gpu-command.json)、[stdout](../../../../agent_logs/task9/task9.11/task9.11.13/final-v2-gpu.stdout.txt)、[stderr](../../../../agent_logs/task9/task9.11/task9.11.13/final-v2-gpu.stderr.txt)为准；父同源回归与.14独立结果尚待追加，不把先前开发PASS拼入最终验收。

所有开发失败的dev-*/dev-v2-* command/raw均保留：首轮fixture时钟/未知real路径/过度整字典比较，legacy fixture过早false-execution拒绝，stop ISO微秒舍入，近余额release预算/expiry，以及新增篡改测试复用带denial费用namespace导致stale。修相应fixture输入，不放宽生产判断。v1真实实现缺口由独审提出并在v2修复，与这些测试输入错误分别记录。

专用验收含CPU实际独立审核：原stage CLOSED→clock+3600越旧token/snapshot→真实stdlib审核command actualwait→source/event→新独立snapshot→新release→后继实际worker.main，旧protocol/release/closure字节一致，重复请求不新建worker、不新增费用。GPU-held实际链另验证idle完整持有费用随时间推进，而非CPU/control；partial/disjoint/duplicate按设备独立原区间核算。

近余额case保持原58h/save1800：可信fixture钟推进原deadline-2000，容器从原T0持有，与继承110s重叠。新增CPU1900s是人工synthetic账源，非真实耗时；worker加1900+三control90，GPU仅持有窗口新增时间。**旧原式=container_duration+inherited_scalar110+external.worker_seconds+拟worker申请34**；因继承110完全落在容器内，新并集只计一次。旧式误拒，新式作业GPU申请4可走实际worker，真实GPU申请超余额拒。另legacy显式synthetic GPU5s/isolated cap4s验证实际used越额拒。所有数字均仅用于工程反例，不是实际预算或性能结论。

[joint-v2归档](../../../../agent_logs/task9/task9.11/task9.11.13/joint-v2)保留四组完整原件（CPU/GPU-held/union/near-balance）及original_path→archive/SHA映射。归档内1900s/20s/3s与继承110s均为runner内生成的synthetic输入，不进入真实项目预算；只有外层actual runner wall属于真实已知CPU下界。旧原件不迁移为新执行。

## 限制与交接

真实external命令API没有可核实的GPU/CPU归属receipt，因此不能仅凭devices=[]自报CPU；本次只接受显式inert synthetic证据，真实缺证UNKNOWN。静态旧容器没有独立固定时序basis同样UNKNOWN，不新增legacy schema或自动迁移。首次dynamic synthetic独审建立basis；之后每个resource/read/review绑定前次已审内容并约束时序，不能把源文件改短再重新签一份snapshot。

原控制包络仍工程候选applied:false，未证真实取值、会话尾或完整历史成本。原旧C完整门FAIL、历史UNKNOWN、真实G1/成熟profile/Docker尾/正式执行许可及截止可行性仍待；未跑真实GPU/环境/模型/科学实验。旧STOP、4000smoke/980评估/正式0/test0、58h/2TiB和2026-11-06 03:18:20+08截止不变。

下一步：父以本v3 SHA跑必要回归，.14独立复跑原expected-reject反例和新联合原件，父直接核源码/原命令/归档及旧保护清单后交付。任何必要源码变更重新冻结，不以本节点自报代替独审。

### v2历史专用实测追加

同c53aa986…798aff7，15项rc0、外层实测9.227331739s，source-before/after/当前源三者一致；[汇总与四组原件SHA核验](../../../../agent_logs/task9/task9.11/task9.11.13/implementation-evidence-summary-v2.json)核351份归档文件一致。CPU联合worker 163.816262925→253.894756652s（payload0.078493727s＋90s候选control），GPU始终110s；后继实际worker后worker284.961544234s，GPU仍110s。GPU-held当前观察累计121.018592596→3722.455906153s，由完整持有窗口推进构成，CPUcontrol不另计GPU。union case130.000000477→重复后不变→独立3s后133.000000477s。near-balance currentGPU约206800.099130s、worker2153s；GPU申请4、worker申请34可准入并完成actual worker；超GPU余额申请拒。该组raw endpoint分别记录，不能把不同观察时点当同一墙钟。

以上均仅synthetic工程证据，不是项目真实GPU/worker预算；父同SHA相关回归及.14独立签字仍需读各自原件，不能由此15项替代。[SRC-1420](../../../../SOURCES.md#src-1420)。

### v3最终同源专用交付

最终0bbda355…7476c1a9，同源16项rc0、actual runner wall 9.728704695s，exact argv/cwd/env/raw及170源前后记录见[final-v3-gpu-command](../../../../agent_logs/task9/task9.11/task9.11.13/final-v3-gpu-command.json)、[stdout](../../../../agent_logs/task9/task9.11/task9.11.13/final-v3-gpu.stdout.txt)、[stderr](../../../../agent_logs/task9/task9.11/task9.11.13/final-v3-gpu.stderr.txt)。[汇总](../../../../agent_logs/task9/task9.11/task9.11.13/implementation-evidence-summary-v3.json)核冻结/前/后/当前源一致，核[joint-v3](../../../../agent_logs/task9/task9.11/task9.11.13/joint-v3)四组351原件SHA全部匹配。

CPU联合：worker 163.866189202→253.944023727s，增量为actual CPU payload 0.077834524s＋原候选control90s；GPU保持110s。后继actual worker成功，旧证据逐字节不变。GPU-held/union/near-balance原区间及新申请/已用分列亦在汇总，独立oracle应读各次精确resource_observed_epoch，不能把先后观察时间当同一瞬间。v3四个首次identity缺失/矛盾case与v2的history篡改、静态无basisUNKNOWN全部同源覆盖。

父116相关回归与.14独立裁决仍以各自原件/父接收为准，本节点不代签。所有v1/v2结果和FAIL保留；当前没有真实实验许可或后台任务。[SRC-1420](../../../../SOURCES.md#src-1420)。

## 父最终接收

父核最终170源/final-source-v3、132回归及.14正式54项同SHA/5689引用，通过；旧878/59/158/101原件及688输出stat不变。最小patch父独算SHA f7559549…438f4d，实施版路径标签不同但文件内容diff相同。预算与剩余合同集中见[父RESULTS §17](../RESULTS.md#17-src-1417-p1-gpu两账修复最终交付2026-11-04)与[SRC-1422](../../../../SOURCES.md#src-1422)，不将synthetic账核销真实UNKNOWN。推荐GPT6.1sol/high、Sonnet5.5/high因设备区间/准入因果；实际模型未知。仅工程done，真实NOT_READY，不签训练令。
