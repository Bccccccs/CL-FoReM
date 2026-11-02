# task9.4 G1–G4 执行记录

2026-10-29 21:04 +08:00，active；执行者Codex，用户指定 gpt-6.1-sol / high（平台内部模型/强度未独立暴露）。推荐实现/验收 GPT6.1sol、Sonnet5.5 / high：需核对默认数学逐元素等价；固定监控 medium。
授权：SRC-1322、SRC-1323及本轮用户指令。按 task9.4 PROCEDURE 顺序；仅写指定开关、stage2配置、队列脚本、stage2日志、RESULTS执行者节和本日志；不写PROGRESS/DECISIONS/SOURCES。不改科学合同，不重试失败job，首失败停报。
初检：main，有既有未提交修改（含training.py），保留全部；GPU compute空；forem-dev仅保活，磁盘可用18.1TB、MemAvailable约255GB。原sac.py/training.py复制到 logs/task9/t9-stage2-20261029/pre-g1。用户明确指定当前工作区/容器挂载，沿用该位置，不另建隔离工作树。
执行技能按用户固定协议适配：所有账本/测试产物留在授权日志目录，不创建额外skill目录、不提交。G1→G2依赖代码冻结；G2→G4依赖成本/门；G3可选。8-job结构按每组两种子各primary/preserve/resume，加pre/post共8job解释（总预算4300s）。
尚未执行：G1 GPU门、G2、G3、G4。

## 21:06 +08:00：G1首次门失败，停止

已生成12份正式配置，`config-manifest.json`逐键记录相对模板差异与SHA256（group仅为组标识元数据）；B3_5M仅total_transfers/seed不同，total_updates与checkpoint_interval保留。已新增sac.py独立α日程与Huber分支、training.py配置校验；默认MSE语句与数学未主动改动。保存/恢复继续由原config逐值比较和_contract保护。

实际命令：先GPU compute空闲检查，再 `sg docker -c 'docker exec -e CUDA_VISIBLE_DEVICES=0 -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/root/mm_husky_ws/src forem-dev python3 -B -u /root/mm_husky_ws/logs/task9/t9-stage2-20261029/g1/run_budget.py --owner G1 --limit 1800 -- bash -c "python3 -B -u /root/mm_husky_ws/logs/task9/t9-stage2-20261029/g1_test.py && python3 -B -m pytest -q /root/mm_husky_ws/src/task8_lower/tests"'`。

G1账本唯一命令010f3734f3，2026-10-29T21:05:42.806+08:00至21:05:49.281，rc1、无timeout；6.473673028871417/1800s，active={}。首组B0在首次update后，同状态同RNG的返回loss比较通过，full_state_dict逐元素比较首个报错 `root.policy.encoder.conv.4.weight`（g1_test.py:29→same:9）。未保存失败参数张量，无法报告误差幅度；没有把失败归因为某个机制。使用systematic-debugging技能只读检查日志与新旧diff；未重跑、未修补测试/实现。

后续B0动作/恢复、B3等价、T/Huber/5M校验与原测试套件因串行首失败均未执行，不得称通过。G2/G3/G4均NOT_RUN，零长训启动，无队列PID、run PID或ETA。21:06容器仅保活、GPU compute为空。本次没有需要停止的自启存活进程，也未触碰他人进程。

交接：目标/授权仍为SRC-1322/1323的12run；当前执行者Codex停止于失败门，状态blocked（任务记录状态，不涉及goal工具）。证据 logs/task9/t9-stage2-20261029/g1/{budget.json,010f3734f3.log}、g1_test.py、pre-g1原件和config-manifest.json。剩余先诊断逐元素差异/测试可重复性，获用户决定后修复与重新核验，再按G2→可选G3→G4推进；不能凭剩余预算自动重试。风险：新增代码未验收，不能用于训练；_contract随sac.py/training.py改动，旧task9.2检查点在现代码下不可恢复。本轮未保存训练检查点。父接手应先读本记录与RESULTS执行者节，核实进程/文件状态。未委派子Agent。

## 2026-10-30T07:48:31.361689+08:00：批准重跑续接（active）

执行者Codex，用户指定gpt-6.1-sol / high；实际平台内部配置未知。授权SRC-1325及本轮用户指令；仍遵守原prompt全部边界，仅写测试、授权日志/RESULTS/后续队列脚本；不写PROGRESS/DECISIONS/SOURCES（原prompt明确排除，开工登记在本日志）。已读父审核及对照探针，main既有修改保留；GPU compute空，forem-dev仅保活，磁盘17TB、MemAvailable237GiB。仅在g1_test.py导入torch之后、CUDA运算前加三项确定性设置，原件g1_test.pre-rerun.py；运行环境设CUBLAS_WORKSPACE_CONFIG=:4096:8，不传给生产训练。账本初值used_s=16.86753193475306，剩余1783.132468065247；本次仅一次重跑，若失败停止。G2/G3/G4尚未执行。推荐GPT6.1sol / high与Sonnet5.5 / high：逐位等价与CUDA测试因果核查；常规监控medium。

### G1重跑通过；G2准备
G1 b1c797ac3b rc0、无timeout，27.204723s；累计44.072255/1800s。B0/B3更新/动作/保存恢复逐位一致、T/Huber/12配置/5M/update_due通过；原task8_lower/tests 30 passed in17.32s。原件g1-report.json、g1/budget.json；生产代码未改。冻结g1-frozen.json。prepare_smoke.py按9.1原计划生成4组，每组两种子S4718/S4719、八job、4300s，preserve沿r2 JSON语义相等修正，GPU0/1/2/3分别B1/B2/T/H；smoke配置只改checkpoint_interval1000，保留正式步数/环境/回放/196评估。独立验收角色按task9.4父流程留待父/另Agent，执行者不自称独立。下一步启动G2。

### G2首轮评估中；G3/G4准备（尚未启动长训）
四组S4718已完成primary512、preserve安全检查、恢复至1000及首条诊断，进入完整196评估。生产tensor/optimizer设备由summary与GPU compute交叉核，CPU Adam step计数器依load_checkpoint现有逻辑保留，不能视为CPU回退。G3可选探针决定不执行；无同卡2run收益证据，采用每卡1run串行。已准备新宿主队列/只读监控，尚未生成最终队列计划或启动长训。queue_checks.py以临时目录/mocks完成12项通过，拒绝陌生进程/冻结漂移/已有输出/磁盘不足/提前summary/错误退出等，未用GPU或optimizer。成本分析准备以新smoke组件相对task9.1比例校准task9.2成熟端到端每转移成本，并含既有最大评估/满回放保存开销；属于工程推导，须250k重算，不作长程实测。

## 2026-10-30T08:15:34.947732+08:00：G2独立固定判据复核委派登记

依据用户继续有效的原prompt明确“可派gpt-6.1-terra / low子Agent做固定判据巡检，结果须由你复核”，为落实S6独立验收（不是新增实验），委派Terra/low。任务仍属task9.4既有节点及三文档，依本节点PROCEDURE“G1–G4作为本节点阶段…不拆子节点”，不新增子任务目录。输入：根/forem AGENTS、task9.4三文档、task9.1 TASK及r2wrapper、本目录G1冻结/四组smoke计划/账本/原件、analyze_g2.py；交付仅本目录review/g2-independent.{md,json}（独立日志即该md），不写全局或其他共享文档，不用GPU/训练/optimizer、不重试job。判据S1–S6（两种子8job、更新/恢复/196评估/后端/设备/冻结/无重试/预算），成本算式只读复核，不另改阈值；结果由Sol复核，未全部完成不得pass。父仍负责长训完成后的最终独立验收。实际子模型由spawn元数据登记gpt-6.1-terra / low。

## 2026-10-30T08:19:59.677054+08:00：G2执行与成本门通过，待独立固定门

四组八job全部complete/rc0，无timeout/重试，G2宿主编排会话rc0。B1/B2/T/H账本1597.640930/1720.057716/1602.781671/1716.807814s。analyze_g2.py一次执行rc0：primary/恢复/100+96/更新/后端/设备/冻结检查通过，3M条件成本11.206891/26.284996/25.336301/26.592237h；B3-5M低UTD代理18.604599h。保存成本额外采用本轮/旧smoke保存均值比例（至少1）校准既有成熟满回放保存成本：B1/B2/T/H倍率1.431/3.169/2.145/3.185；这只是工程推导，非长训实测。逐项wall/显存/检查点/采样/局限在g2-report.json，Sol已复算成本算式。GPU compute空、容器仅保活，尚未启动G4。已通知独立Terra核全部原件及成本，待pass后准备/预检并启动队列。

## 2026-10-30T08:22:13.627090+08:00：G2独立通过、G4已分离启动（active）

Terra/low独立S1–S6与成本PASS（review/g2-independent.md/json），Sol已复读并核对原件/成本一致，放行g2-release.json。G3可选未测，单卡串行。prepare_queue.py及宿主queue dry-run预检rc0，GPU空/容器仅保活/空输出/冻结/磁盘内存均通过。以setsid nohup启动queue，PID253817，GPU monitor253858；queue-state.json running无error。首批GPU0 B1-seed4718容器2676694/宿主253932；GPU1 B1-seed4719容器2676700/宿主254053；GPU2 B2-seed4718容器2676707/宿主254257；GPU3 B2-seed4719容器2676717/宿主254492。各GPU compute为自身训练进程。其余8run queued无PID。队列分配见queue-plan.json，最大全局条件外推63.776884h、worker253.541939h，按4^8分配减小全局墙钟，卡内核心→T/H→5M，不设置全局核心完成屏障。尚待首批四条1000诊断核查后结束会话，250k交父重算。

## 2026-10-30T08:23:05.371181+08:00：G4首段核查完成，交Claude父


### 2026-10-30T08:23:05.371181+08:00 Codex：G1–G4启动交接（长训active，首段review）

目标/授权：[SRC-1322](../../../SOURCES.md#src-1322)、[SRC-1323](../../../SOURCES.md#src-1323)、[SRC-1325](../../../SOURCES.md#src-1325)。本轮已完成唯一批准G1重跑、四组G2、G3选择与G4首批启动/首诊断核查；**12个run尚未完成，不能判稳定性或最终配置**。当前执行者Codex（用户指定gpt-6.1-sol/high，实际内部配置未知），交Claude父接手监控。推荐监控GPT6.1sol/medium、Sonnet5.5/medium；独立验收二者high（需跨run判据复算，验收者≠执行者）。

G1结论及证据见上方重跑段，累计44.072255/1800s，无生产代码/正式配置再修改。G2报告生成时尚待独立的状态由`g2-release.json`补全，原报告不改写。G2各组均两种子512→保存→恢复→1000→完整196，8job各恰一账本记录、rc0、无timeout、无重试；恢复/更新数/设备/后端/冻结检查通过，检查点后端以标准库流式解析pickle头部标量核对，未反序列化或调用GPU。**S6独立固定门核查由Terra/low通过、Sol复核，原件[独立报告](../../../../logs/task9/t9-stage2-20261029/review/g2-independent.md)；长训最终验收仍待另一Agent。**

|组|执行门|账本实耗 s/4300|两次196评估 wall s|外推3M h|
|---|---|---|---|---|
|B1|S1–S6 pass（独立复核见下）|1597.64|561.93/582.79|11.21|
|B2|S1–S6 pass（独立复核见下）|1720.06|566.64/569.02|26.28|
|T|S1–S6 pass（独立复核见下）|1602.78|556.77/558.20|25.34|
|H|S1–S6 pass（独立复核见下）|1716.81|567.56/562.86|26.59|

实测详见[g2-report.json](../../../../logs/task9/t9-stage2-20261029/g2-report.json)与各`smoke-<组>/`原件，包含primary/恢复/评估wall、checkpoint字节、torch与GPU CSV峰值、现有Timings及采样统计。Adam的CPU step计数器不是训练参数CPU回退。现有计时合并物理/IK及回放采样/搬运/update，未测CUDA event；不声称已分别精测。外推为工程推导：`I+N*c+floor(N/250k)*E+(floor(N/250k)+1)*C`，c用本轮组件比例校准task9.2成熟同路径实测；评估不低于既有最大评估；保存以本轮/旧smoke保存均值比例（至少1）放大既有最大均值保存成本，计入本轮已见写入变慢。尚未覆盖新组满回放/策略变化，须250k重算。来源草稿[T94-G2-G4](../../../../logs/task9/t9-stage2-20261029/sources-draft.md#t94-g2-g4)。

G3可选探针未执行、使用0s；无同卡双run收益证据，采用每卡1run串行。每卡核心组优先，T/H其后、5M最后；固定首批B1/B1/B2/B2，对余下8run枚举4^8种分卡，以G2条件成本最小化最大队列时间。全局外推63.78h、累计worker 253.54h，预计全部结束2026-11-02T00:07:54.854768+08:00；均是条件估计，非期限承诺。依据[queue-plan.json](../../../../logs/task9/t9-stage2-20261029/queue-plan.json)。

|run|GPU|当前状态/容器PID（宿主PID）|预计结束 +08:00|
|---|---|---|---|
|B1-seed4718|0|2676694（253932）|10-30 19:33|
|T-seed4718|0|queued，PID尚无|10-31 20:53|
|H-seed4718|0|queued，PID尚无|11-01 23:29|
|B1-seed4719|1|2676700（254053）|10-30 19:33|
|T-seed4719|1|queued，PID尚无|10-31 20:53|
|H-seed4719|1|queued，PID尚无|11-01 23:29|
|B2-seed4718|2|2676707（254257）|10-31 10:38|
|B0-seed4720|2|queued，PID尚无|11-01 12:55|
|B3-seed4720|2|queued，PID尚无|11-02 00:07|
|B2-seed4719|3|2676717（254492）|10-31 10:38|
|B3_5M-seed4718|3|queued，PID尚无|11-01 05:14|
|B3_5M-seed4719|3|queued，PID尚无|11-01 23:50|

输出统一：宿主`forem/results/task9/t9-stage2-20261029/<run>/`，容器`/root/mm_husky_ws/results/task9/t9-stage2-20261029/<run>/`。训练日志统一`forem/logs/task9/t9-stage2-20261029/<run>.log`；容器PID原件`<run>.container-pid`。配置在`config/task9/stage2/`，冻结hash在queue-plan；镜像/驱动/Git版本见`runtime-version.json`，保留原有dirty改动，不以HEAD代替实际源码hash。

宿主分离队列PID **253817**（setsid nohup），GPU监控PID **253858**；队列`queue-state.json`、`queue.log`，GPU记录`long-gpu.csv`。预检核GPU/容器身份、空输出、代码/配置/池/种子表hash、磁盘与宿主内存；每次后继启动再次检查，不重试。静态拒绝门见`queue-checks.json`。首批4run的1000转移诊断、有限值、更新数、runtime CUDA/后端、无STOP/异常均通过，原件[initial-inspection.json](../../../../logs/task9/t9-stage2-20261029/initial-inspection.json)。

**接手与剩余工作：** 先读本节、执行者日志，再核进程及queue-state。监控：`python3 forem/scripts/task9_stage2_monitor.py`，另用`sg docker -c 'docker top forem-dev -eo pid,ppid,args'`及nvidia-smi核活进程。每个run首个250k完整评估后重算；>48h即在该run放STOP并报告，不缩步数。停止运行中的某run用容器`touch /root/mm_husky_ws/results/task9/t9-stage2-20261029/<run>/STOP`（宿主results归root）；停止后继排队用`kill 253817`，不会向已启动训练转发信号。杀队列后GPU监控可能继续，父核实后另停PID253858。不重启/恢复失败run；合法summary/diverged/interrupted终态后方可启动本卡下一run。旧task9.2检查点与现代码contract不兼容，不从旧3M检查点续5M。

长训结束由另一Agent独立验收，逐run报告预注册3M末三次、发散停止计退化且P字面不可判；B3-5M另报4.5/4.75/5M为非预注册描述。父接手长训监控/最终独立验收、全局SOURCES/PROGRESS及顶部状态同步。本轮未写全局三文档；仅委派获准的Terra/low做G2固定门只读核查，Sol复核；未提交或推送；目前无新增用户决策请求。


最终进程核查：handoff-processes.json记录4个GPU compute PID均为本队列宿主训练PID，容器top一致；queue状态running，8run queued。交接文档链接检查通过。本会话到此结束，训练继续，父接手250k。
