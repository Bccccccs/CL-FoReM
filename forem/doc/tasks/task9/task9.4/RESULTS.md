# task9.4 RESULTS — 阶段2长训

状态：**review（2026-11-02：13run全部退出，6正常完成、5保护停止、2用户提前停止H；三5M已完成，整批最终独立验收仍待）**。[SRC-1351](../../../SOURCES.md#src-1351)，H类别沿[SRC-1344](../../../SOURCES.md#src-1344)。依据[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)；授权[SRC-1322](../../../SOURCES.md#src-1322)、[SRC-1323](../../../SOURCES.md#src-1323)、[SRC-1326](../../../SOURCES.md#src-1326)。

## 派发（父，2026-10-29）

- 执行者：Codex `codex exec`，gpt-6.1-sol / high，需要docker与GPU，派发目录`forem/logs/task9/codex-dispatch-20261029-t94/`（`prompt.txt`）。2026-10-29父准备含danger-full-access的派发脚本时，被Claude Code自动模式分类器以[Create Unsafe Agents]拒绝；本任务需要docker/GPU，workspace-write沙箱不适用，因此交用户在终端启动。
- B3-5M：用户以“ok”回答“B3要按5M日程新开两个种子吗？”，父理解为批准，加入本任务（SRC-1323），共12个run。

## 执行者节

### 2026-10-29 Codex：G1首次等价门失败，已停止（blocked）

执行者：用户指定 gpt-6.1-sol / high，平台内部配置未独立暴露。推荐后续实现/验收 **GPT6.1sol / high、Sonnet5.5 / high**（需判断逐元素差异及训练合同）；固定监控 medium。授权沿[SRC-1322](../../../SOURCES.md#src-1322)、[SRC-1323](../../../SOURCES.md#src-1323)。本段覆盖本轮执行事实；顶部派发状态保留为历史。

|阶段|实际结果|
|---|---|
|G1实现|已写独立alpha_lr_schedule、critic_loss/huber_delta及配置校验；12份配置已生成，尚未验收|
|G1测试|**FAIL**，B0首个下一更新的policy.encoder.conv.4.weight逐元素不一致，rc1，无timeout；6.473673/1800s|
|G2|B1/B2/T/H全部未运行，S1–S6未验收，无成本/显存/48h外推结论|
|G3|未运行，未选定排队并发方式|
|G4|未运行；12个run均未启动，无队列/训练PID、GPU分配或预计结束时间|

证据：[失败原件](../../../../logs/task9/t9-stage2-20261029/g1/010f3734f3.log)、[唯一命令账本](../../../../logs/task9/t9-stage2-20261029/g1/budget.json)、[测试脚本](../../../../logs/task9/t9-stage2-20261029/g1_test.py)、[配置差异及hash](../../../../logs/task9/t9-stage2-20261029/config-manifest.json)、[停止快照](../../../../logs/task9/t9-stage2-20261029/stopped-manifest.json)。来源待父登记：[草稿T94-G1](../../../../logs/task9/t9-stage2-20261029/sources-draft.md#t94-g1)；本轮不写全局SOURCES。

原sac.py/training.py保存于 `forem/logs/task9/t9-stage2-20261029/pre-g1/`，保留了已有training.py修改；只追加授权开关。配置T/Huber依TASK定义，B3_5M保留total_updates=4999743、checkpoint_interval=250000、全部评估，只改total_transfers与对应seed。group为组名元数据。**以上为实现内容，不能代替正确性验证。**

测试命令和版本详见[执行日志](../../../agent_logs/task9/task9.4/20261029-codex-stage2.md)。测试容器forem-dev，物理GPU0，运行前compute空；B0返回loss比较通过，接着full_state_dict比较失败。未保存不一致张量，差异幅度与原因未知；没有证据将其归因到CUDA非确定性或实现问题。后续动作/恢复、B3、T日程/Huber值与梯度、5M validate_config/日程和原测试套件均未执行。遵守首失败停止，没有修补后重试。

**兼容性：** `_contract()`随sac.py/training.py变动，旧task9.2检查点无法在当前代码下恢复；新字段由配置逐值一致检查覆盖。本轮代码未验收，不可放行长训。

**交接父/用户：** 21:06 +08:00检查GPU compute空、容器仅保活；自启命令已退出，账本active={}，无存活队列/训练可监控或停止。需决定是否授权针对首次逐元素差异开展诊断、修复并重新核验；然后才可进入G2/G3/G4。当前没有ETA，不能沿用约16h/run代理值作为本轮实测成本。无长训首诊断或250k结果需要接手。


### 2026-10-30 Codex：批准重跑续接（active，G1通过，G2执行中）

授权[SRC-1325](../../../SOURCES.md#src-1325)及本轮用户指令；执行者用户指定 gpt-6.1-sol / high，平台内部配置未知。推荐 **GPT6.1sol / high、Sonnet5.5 / high**（逐位等价与合同核查），固定监控 medium。

仅修改 `g1_test.py`：导入torch后、任何CUDA运算之前设置benchmark=False、deterministic=True与use_deterministic_algorithms(True)；通过docker exec环境设置CUBLAS_WORKSPACE_CONFIG=:4096:8。**生产代码与生产训练默认设置未变**。原测试脚本保留为`g1_test.pre-rerun.py`。

G1唯一获批重跑 b1c797ac3b：rc0、无timeout，27.204723s；原账本累计44.072255/1800s，余1755.927745s。B0/B3更新、动作、保存恢复后更新逐位一致；T/Huber/12配置validate_config/5M日程/update_due通过；原src/task8_lower/tests **30 passed in17.32s**。证据[g1-report.json](../../../../logs/task9/t9-stage2-20261029/g1-report.json)、[账本](../../../../logs/task9/t9-stage2-20261029/g1/budget.json)、[重跑日志](../../../../logs/task9/t9-stage2-20261029/g1/b1c797ac3b.log)。来源草稿[T94-G1-RERUN](../../../../logs/task9/t9-stage2-20261029/sources-draft.md#t94-g1-rerun)，待父登记。

G2于2026-10-30 07:49:59–07:50:02 +08:00启动：GPU0/1/2/3分别B1/B2/T/H，宿主wrapper PID198696/198697/198698/198699，各组两种子各primary→preserve→resume，加pre/post共8job，独立4300s账本。沿9.1原件及r2 preserve配置JSON语义相等修正，只改checkpoint_interval1000；每组完整两次196评估。G2尚未完成，不能据此放行G4；G3/G4尚未执行。执行者核查不替代父流程要求的独立验收。


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

## 父审核（Claude，2026-10-29 21:4x）

原件`forem/logs/task9/t9-stage2-20261029/review/parent-review.md`，[SRC-1324](../../../SOURCES.md#src-1324)。

- 用户在终端启动了Codex（gpt-6.1-sol / high）。Codex在G1等价测试首项失败后停止，没有重试，G2–G4未运行，无训练进程。
- 父审核：代码diff只新增开关，默认路径未变；12份配置差异与TASK一致。对照探针（GPU0，计入G1账本，共10.4s）：旧代码对旧代码在默认cuDNN下也不等（最大9.31e-9）；确定性算法下旧对旧、旧对新（B0/B3，两次更新）全部逐位相等。**失败来自测试未关闭CUDA非确定性，不是实现不等价。**
- 建议：只给`g1_test.py`加确定性开关，用剩余G1账本完整重跑G1，通过后继续G2–G4。因PROCEDURE规定首失败不重试，需用户批准。
- 2026-10-29用户“批准重跑”（[SRC-1325](../../../SOURCES.md#src-1325)）；续接prompt `forem/logs/task9/codex-dispatch-20261029-t94/prompt-r2.txt`，由用户在终端启动。

## 父记录（Claude，2026-10-30）

- 07:45 用户第一次在终端启动r2，约40s后连接失败退出（workspace routing discovery failed），没有执行任何操作，不算G1重跑。07:47 带代理变量重启成功（codex exec PID 192246）。
- **G1重跑通过**（父核对原件）：账本`g1/budget.json`中`b1c797ac3b`（owner G1-approved-rerun）rc0，无超时，27.2s，G1累计44.1/1800s；`CUBLAS_WORKSPACE_CONFIG=:4096:8`只用于测试；`g1_test.py`相对`g1_test.pre-rerun.py`只加3行确定性开关；`g1-report.json`的B0/B3等价、T、Huber、12份validate_config与5M日程、update_due全部通过；原测试套件`30 passed`。
- 07:49 G2 smoke启动，B1/B2/T/H四组各用一张GPU。
- 用户追加第13个run：B3-5M种子4720（[SRC-1326](../../../SOURCES.md#src-1326)）。配置在`config/task9/stage2-extra/`，validate_config通过。Codex本轮不负责；父在G4交接后加入队列。
- 07:59 用户将离开几天，要求5M训练能自动启动（SRC-1326补充）。父写了`forem/scripts/task9_extra_b3_5m_waiter.py`并以分离方式启动（宿主PID 219930，setsid，PPID 1）。
  - 规则：Codex队列（`scripts/task9_stage2_queue.py`）每次派发前都会拒绝非本队列的GPU/训练进程，所以等待脚本只在`queue-state.json`没有queued run、某卡道全部ended、该GPU无compute进程时才启动；队列stopped_on_error、无队列或等待超过7天就不启动。
  - 启动方式与队列相同（`docker exec`，`CUDA_VISIBLE_DEVICES`为空出的卡，`--max-wall-s 172800`）；输出`results/task9/t9-stage2-20261029/B3_5M-seed4720`。250k外推只记录不STOP。
  - 自测：判定逻辑离线8种情况全部正确；对真实GPU只读预检，正确识别四卡被smoke占用。实际启动路径尚未在GPU上跑过（需等条件满足）。
  - 查看状态：`logs/task9/t9-stage2-20261029/extra/waiter-state.json`、`waiter.log`；停止等待：`kill 219930`（只停等待脚本；若已启动训练，用`docker exec forem-dev touch <输出目录>/STOP`优雅停止）。
- 08:24 Codex交接后退出（`last_message-r2.md`）。父核对：G1重跑、G2四组门与成本、queue-plan、首批4 run的进程/GPU一致，登记[SRC-1327](../../../SOURCES.md#src-1327)。
- 08:25 父启动250k守护`scripts/task9_stage2_250k_guard.py`（PID 262591，setsid）：每10分钟运行Codex的`task9_stage2_monitor.py`，在每个run首个250k评估后记录外推；连续两次>48h才写该run的STOP。离线测试4种情况都正确（正常/持续超时/一次超时/早期不判）。状态`logs/task9/t9-stage2-20261029/parent-250k/guard-state.json`。08:25首查时4个run都还没到250k（B1约6.6h、B2约18.7h，都是早期推导）。
- 停止方法：守护`kill 262591`；等待脚本`kill 219930`；队列/单个run见上方Codex交接。

## 2026-10-30 21:29 Codex接手与状态复核

用户“接受claude的所有工作，然后检查现在的训练进度”。Codex接手保留全部现有改动和既有运行安排；历史review/paused/限制保留，未提交/推送/合并、未改代码或配置、未启停训练。事实来源与适用限制统一登记[SRC-1328](../../../SOURCES.md#src-1328)，证据快照[inspection.json](../../../../logs/task9/t9-stage2-20261029/status-20261030-codex/inspection.json)。本轮仅核查和记录完成，task9.4继续active，最终独立验收尚未完成。

|run|状态/转移数|最新完整验证|最新完整迁移|
|---|---|---|---|
|B1-4718|正常结束，3M|3M：62/100|44/96|
|B1-4719|正常结束，3M|3M：72/100|48/96|
|B2-4718|运行，1.75M|1.5M：48/100|27/96|
|B2-4719|运行，1.75M|1.5M：41/100|28/96|
|T-4718|运行，431k|250k：42/100|32/96|
|T-4719|运行，412k|250k：43/100|27/96|
|H×2、B0/B3-4720、B3-5M-4718/4719|主队列queued，尚未启动|尚未执行|尚未执行|
|B3-5M-4720|追加等待脚本waiting，尚未启动|尚未执行|尚未执行|

B1两路rc0、12次196评估与final.pt齐全，逐回合重算一致。末三次验证60/69/62%和67/68/72%，均值63.67%/69%，峰值70%/72%，下降6.33/3个百分点，按既定15个百分点门均不退化；不代替任务最终独立验收。B2/T未完成，不能判最终稳定性；B2的Q幅度比B1大，但当前没有发散终态，继续按已批准规则运行。

监控入口仍为`python3 forem/scripts/task9_stage2_monitor.py`。队列253817、GPU监控253858、250k守护262591和追加等待219930存活；守护最近21:25有检查。停止/恢复规则沿上方交接，不重启失败run。69冻结文件、12主配置和追加配置hash一致。本轮未复跑G1/G2或加载检查点做恢复验收。全工作区`git diff --check`发现原有PROGRESS行尾空格，未改动。

条件外推（沿既有monitor公式，见SRC-1328）：B2预计10-31 07:09–07:34到3M，T预计10-31 16:35–16:43到3M，四路总成本均约22–23.2h、低于48h；评估/保存与策略变化会影响估计，不承诺时间或给出新的全队列ETA。

当前负责人Codex；推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium用于跨日志/进程核查，最终独立验收二者high；实际本会话模型/强度未知。下一步：保持既有队列/守护执行，留意B2后续验证与T/H结果；全部run结束后由另一执行者独立验收，追加5M仍按原等待条件自动拉起。

## 2026-10-31 08:40状态复核（Codex）

事实与适用限制：[SRC-1329](../../../SOURCES.md#src-1329)；[原始快照](../../../../logs/task9/t9-stage2-20261029/status-20261031-codex/inspection.json)。本轮仅查询与记录，不修改训练、不重试/恢复。

|run（顺序4718/4719）|终态或最新转移数|最新完整验证|
|---|---|---|
|B1×2|正常完成3M，判据均不退化|3M：62/100、72/100|
|B2×2|发散停止1.932M/1.796M|1.75M：37/100、30/100|
|T×2|发散停止1.615M/1.542M|1.5M：35/100、29/100|
|H×2|运行约264k/302k|250k：49/100、45/100|
|B0-4720|运行约1.257M|1.25M：33/100|
|B3-5M-4718|运行3.5M/5M|3.25M：51/100|
|B3-4720、B3-5M-4719|主队列queued|尚未执行|
|B3-5M-4720|追加waiting|尚未执行|

B2/T四路均有diverged.meta.json及非空diverged.pt、exit code 1，日志明确Q最大值超过500k参考10倍保护；按SRC-1322计退化，3M末三次P字面不可判，不能报告为最终3M成功率。准确停止步数取meta，最后learning记录比它少1000步。未做恢复或加载检查点验证，终态文件存在不代表最终独立验收通过。

首个B3-5M在10-30 21:55自动启动；H分别在10-31 06:37/06:21接续T，B0-4720在10-30 23:02接续B2。队列正常running，共2正常完成/4保护停止/4运行/2 queued＋1追加等待，不把所有ended视为训练完成。队列253817、GPU监控253858、守护262591、追加等待219930存活；守护08:36有检查无last_error，69冻结文件/13配置hash一致。停止/监控沿既有入口，不变更协议。

推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium用于状态复核；实际本会话模型/强度未知。当前训练继续active；剩余H、第三种子及5M结果未闭合，最终独立验收待全部结束；本轮未开展根因诊断或提出新实验。

## 2026-10-31配置解释与归因更新（仅分析）

来源：[SRC-1330](../../../SOURCES.md#src-1330)，逐字段原件[config-comparison.json](../../../../logs/task9/t9-stage2-20261029/causal-assessment-20261031/config-comparison.json)。用户要求先判断“到底什么有问题”，随后要求逐组解释配置；本轮保留既有运行，仅分析文档。

|组|每多少转移更新一次|actor/critic LR|温度α及其LR|critic loss|总转移|
|---|---|---|---|---|---|
|B0|1|按更新数指数下降|原方式，固定1e-6|MSE|3M|
|B1|10|同B0|同B0|MSE|3M|
|B2|1|按转移线性1e-4→1e-6|RLlib式，α LR按转移线性1e-4→1e-6|MSE|3M|
|B3|10|同B2|同B2|MSE|3M|
|T|1|同B0|同B2（独立α日程）|MSE|3M|
|H|1|同B0|同B0|Huber δ1|3M|
|B3-5M|10|同B3，线性进度按5M|同B3，线性进度按5M|MSE|5M，从头新训|

原方式α=0.35·exp(logα)，降至0.05后固定，0.35不是上限；RLlib式为exp(logα)，无0.05冻结。共同环境与网络、奖励/终止/动作观测、batch256、replay100k、256环境、γ0.99、τ0.001、目标熵−3均不改；新温度不是完整RLlib算法复刻。原指数日程以4,999,743次更新为分母，不能视为3M末必到LR下限。每组4718/4719，B0/B3另补4720；5M共4718/4719/4720。

现有2×2：B0/B2（高更新比）各两种子发散，B1/B3（低更新比）各两种子完成3M且既定判据不退化。两套温度/LR包均重复这一差异，现有证据明确指向更新/数据比及其关联节奏；T说明只换温度包不足以避免本次发散。降低更新频率还同时降低alpha/target每转移更新次数，B1的指数LR按转移也衰减更慢，所以唯一内部机制尚未被解耦。不能称已证明critic过拟合、target或某行代码是唯一根因；共享代码/环境也未因此全面排除。

执行者Codex（实际模型/强度未知）；推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high用于归因边界审查。仅分析完成，不修改训练/新增实验，最终冻结与独立验收状态不变。

## 2026-10-31 09:17状态快照（Codex，只读）

来源[SRC-1331](../../../SOURCES.md#src-1331)，[原件](../../../../logs/task9/t9-stage2-20261029/status-20261031-0917-codex/snapshot.json)。无新结束或新启动，仍2正常完成/4发散停止/4运行/3等待。H约365k/403k、B0第三种子约1.359M、首个B3-5M约3.709M/5M；最新完整验证分别250k 49%/45%、1.25M 33%、3.5M **57%**（迁移36/96）。原终态结论沿08:40记录。四路训练与队列/守护/等待进程均存活，69冻结文件无漂移，守护09:16有检查。既有monitor条件估首个5M约今天13:50结束，非承诺。

本轮只查状态/写文档；未改代码/配置或启停任务。实际Agent模型/强度未知；推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium用于跨进程/日志核查；最后独立验收未执行，训练保持active。

## 2026-10-31 20:43状态复核（Codex）

来源[SRC-1332](../../../SOURCES.md#src-1332)，[逐回合复算快照](../../../../logs/task9/t9-stage2-20261029/status-20261031-2043-codex/snapshot.json)。本批13 run共4正常完成/5保护停止/4运行/0等待。

|run|当前状态|最新完整验证|
|---|---|---|
|B1×2|既有正常完成3M|62%/72%|
|B2/T各2|既有发散停止|沿前记录|
|B0-4720|新增发散停止1.389M|1.25M 33%|
|B3-4720|新增正常完成3M，299975更新，rc0|3M 64%（迁移39/96）|
|B3-5M-4718|新增正常完成5M，499975更新，rc0|5M 67%（迁移49/96）|
|H-4718/4719|约1.82M/1.86M，继续运行|1.75M 22%/15%|
|B3-5M-4719|约2.24M/5M，运行|2M 53%|
|B3-5M-4720|19:05自动启动，约500k/5M|250k 44%|

首个5M末三验证57/62/67%，均值62%，仅非预注册5M描述；其原3M末三53/45/51%，均值49.67%，截至3M峰值59%，未触发15个百分点门。B3第三种子末三55/58/64%，均值59%，峰值64%，不退化；合并9.2已有结果，3M的B3三种子均不退化，最终验证63/64/64%。B0第三种子日志为Q最大值超过500k参考10倍，仍按发散停止计退化，B0三种子均出现保护停止。H两路从已见峰值50%/54%降到22%/15%，但仍未完成3M，不能提前套用最终判据或称已停止。

所有保存完整评估逐回合成功数/分母复算一致，summary步数/预算/终态与final.pt存在一致；未加载检查点复验恢复。69冻结文件和13配置无漂移，队列/四路训练/守护/追加执行进程存活；追加5M已实际启动，本轮无手工启停。长训仍active，最终独立验收未执行；推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium用于状态核查，最终独立验收high；实际本会话模型/强度未知。

## 2026-10-31独立3M/5M效果比较（仅已有结果）

来源[SRC-1333](../../../SOURCES.md#src-1333)，[复算原件](../../../../logs/task9/t9-stage2-20261029/compare-3m-5m-20261031/comparison.json)。对齐种子4718：

|指标|独立3M|独立5M|描述差异|
|---|---|---|---|
|最终验证|63/100|67/100|+4个百分点|
|末三次验证均值|56.33%|62%|+5.67个百分点|
|最终迁移|45/96（46.88%）|49/96（51.04%）|+4.17个百分点|
|完整run墙钟|9.49h|15.84h|约1.67倍，跨日期竞争未分解|

独立3M另两个种子最终64%/64%；目前5M仅一个完成，不能认定多种子稳定提升。两个总预算各自从头训练，LR/alpha-LR按3M/5M重标，不能当既有3M检查点原样续训的纯步数效应。5M run自身3M检查点为51%，到5M为67%，此口径与独立3M预算run的63%须分开。5M末三仅非预注册描述，迁移不参与选模；本轮未新增训练、探针或修改。

推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium用于已有数据/预算日程口径核对，实际本会话模型/强度未知；独立验收仍待完成。

## 2026-10-31 21:10 CBL自写SAC改版状态汇总

来源[SRC-1334](../../../SOURCES.md#src-1334)、[本次现场快照](../../../../logs/task9/t9-stage2-20261029/status-20261031-2110-codex/snapshot.json)。B1两种子3M 62%/72%不退化；B3三种子3M 63%/64%/64%不退化，是已具备三种子证据的低更新比候选，未作最终选配。B0三种子、B2/T各两种子保护停止。H约1.89M/1.93M仍运行，最新1.75M验证22%/15%，只能说已见后段下降，不能称已完成或正式3M判据已判失败。

B3-5M首种子完成67%；其余4719约2.29M（2.25M验证58%）、4720约750k（500k验证49%）继续训练。总13 run无新结束/启动，仍4正常完成/5保护停止/4运行。现场四卡训练、队列、守护、追加执行脚本存活，守护21:06有检查；本轮未改训练/启停/新增实验。

原语后端内已有稳定改版候选，但不能称CBL自写SAC所有实现问题或唯一机制已经查明；不宣称完整RLlib复刻/物理仿真可用/世界模型提升。最终独立验收与冻结未执行。实际模型/强度未知；推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium用于状态与归因边界汇总。

## 2026-10-31稳定候选成功率瓶颈分析（仅已有日志/源码）

来源[SRC-1335](../../../SOURCES.md#src-1335)、[六候选统计原件](../../../../logs/task9/t9-stage2-20261029/success-bottleneck-20261031/analysis.json)。用户问成功率不足原因，本轮未做新实验/训练或改协议。

首个5M最终验证剩余33个失败回合全部累计20次失败退出，无truncated；失败动作步记录IK220/底盘200/臂环境20/自碰撞220，不是失败回合归因数量。稀疏40/50、标准27/50，迁移49/96。其余B1/B3稳定候选也以累计20失败为主要非成功类别；六候选共有14个验证map_id都失败，不能判为不可解。当前缺口主要是真实执行失败，不足以用“严格成功判据”解释；segment超时不等于整回合超时。

优先机制假设：完整失败动作不commit，base/q/s、扫描和上一动作可能全保持；策略在评估中是无隐状态的确定性均值动作，且观测没有失败计数/拒绝标志。在候选与输入不变条件下会重复同一无效动作，直到累计20失败。代码支持这一条件性固定点，回合日志未存连续trace，未证实33例的具体占比，首次previous切换/部分commit也可使输入改变，不能写作所有失败都被证明卡死。

任务链还包含均匀随机候选选择，候选mask仅保证生成而非完整运动可行；终点witness与末端路线不是全程底盘/机械臂联合可行证书。因此分数同时包含子目标选择与下层策略能力，不能全部归因于SAC优化器。复杂场景性能更低是事实，局部观测/网络表示/探索覆盖等解释尚待验证；延长训练单种子有改善但未达到可判平台期的证据。

结论：优先怀疑运动可行性、失败后恢复与候选选择造成的执行瓶颈；尚无唯一根因和各项贡献比例。未新增trace探针/回放、不改观测奖励终止或自动加高层/恢复兜底；世界模型是否有益待实证。推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high用于这类因果/状态合同分析，实际模型/强度未知。最终训练/独立验收状态沿既有记录。

## 2026-10-31用户提前停止H，5M保留

来源[SRC-1344](../../../SOURCES.md#src-1344)、[请求/退出原件](../../../../logs/task9/t9-opt-design-20261031/user-stop-H.json)。用户明确要求保存提前停止H两路，保留全部5M。H4718在1,990,833消费步/1,990,870已执行动作保存interrupted、21:56:46退出；H4719在2,000,000消费步保存interrupted、21:57:25退出，均resume_safe元数据true、大pt/actor/meta存在，未加载大pt复验恢复。

请求时H未触原10倍Q线，故记**用户提前停止**，不伪造预注册发散或3M结论；最新完整结果仍有后段下降。GPU0/1核空闲后可供新task9.5，旧queue/守护/容器不停止，两个5M仍运行且无STOP。现有本批13run：4正常完成、5规则保护停止、2用户提前停止、2运行，无等待。性能审计见[SRC-1345](../../../SOURCES.md#src-1345)，不是已优化结论。

## 2026-11-02进度核查：三5M均完成

[SRC-1351](../../../SOURCES.md#src-1351)父逐回合核三seed完整20×196评估、5M/499975updates与final产物：4718/4719/4720最终验证67/63/64%，迁移49/39/44（/96）；5M末三描述均值62/64.333/63%。原主queue complete、追加5M已无进程，无训练/GPU compute；H仍保留用户提前停止类别，未恢复。此核查不替代task9.4全13run最终独立验收或将H改判为发散；新task9.5结果另见所属文档。

本次状态归档推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（统计/证据整理）；实际父模型/强度未知。
