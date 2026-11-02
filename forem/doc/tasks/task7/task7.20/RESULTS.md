# task7.20 — 结果

状态：**review，交Claude复核**（2026-10-21；最新r5全目录218 passed，G1两处待定已按SRC-0905补齐；历史运行与限制见下文）。

## 运行记录

各run按下文追加；历史失败与门禁记录保留。

## 交接

- 当前负责人：Codex；交Claude复核，当前结论与剩余项见文末续接交接。


## t7.20-preflight-20261021 — 开工门禁阻塞

状态：**blocked，未实施**（2026-10-21T14:23:53.666337+08:00）。依据[SRC-0490](../../../SOURCES.md#src-0490)，GPU1存在Xorg PID2212（G、4MiB），按派发“无其他进程”要求停止。未把常驻图形进程自行豁免；未停止该进程。

- 实际Agent：Codex gpt-6.1-sol/medium（核实本次codex exec PID2530516命令行）。复核推荐：Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，跨模块与回合合同核对。
- 只读核查：main，HEAD cac6c15599efcbe47a1a7ed30f59a475e4997fd4；7.15和7.17末节Claude复核done；既有153 passed为历史复核数，本次未运行测试。
- 命令：`nvidia-smi`、`nvidia-smi -i 1`、git状态/HEAD、进程及文档/产物检索；GPU命令退出0，原始证据在[日志](../../../agent_logs/task7/task7.20/20261021-codex-decision-env.md)。无容器命令，容器计算0秒。
- task7.18 RESULTS尚未执行；产物清单未发现7.18检查点；**加载集成测试未执行**。
- 改动仅本RESULTS、独立日志、PROGRESS本行、SOURCES SRC-0490；无生产代码、测试或配置改动，无提交。
- 测试/计时/未通过项：全部尚未执行，无本任务功能通过结论；全部实现与E16/64/256计时仍待执行。
- 交接：当前Codex；下一步由用户/派发方明确Xorg是否允许或使GPU1满足门禁，再完成全部规格阅读与PROCEDURE。无本任务后台程序。此为明确资源规则依赖，未标done/review。

## t7.20-r2-20261021 / t7.20-r3-20261021 — 实施、续接与验证

当前负责人Codex；状态active，最终统计与交接随后追加。实际模型gpt-6.1-sol/medium（r2 PID2535683、r3 PID2695456命令行核实）；复核推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，因涉及跨模块合同、冻结版本与自动重置。授权与实现依据：[SRC-0491](../../../SOURCES.md#src-0491)、本任务TASK；GPU门禁已由用户更正为只看GPU1 compute，原blocked历史不再是当前状态。

### 已写入的交付

- 三个生产文件：`src/task7_sim/lower_policy.py`、`decision_env.py`、`g1.py`；两测试：`tests/test_decision_env.py`、`tests/test_g1.py`。未修改Core/EpisodeEnv/候选生成器/参考库，未训练、未提交、未启停容器。
- 冻结Actor加载、显式版本校验、参数/梯度冻结与确定性动作；推演及执行共用同一policy。DecisionStep导出观测/候选、奖励分量、已提交子步Δt及折扣、终止/截断、全部触发原因、r_t、G1遮挡与推演/执行不一致诊断、逐决策回放字段。结束行先clone最终观测和下一候选后独立reset，存活行保持原返回值。经验池及上层网络不属本任务。
- G1可行候选按推进量选；全不可行的实际预测失败分支仅支持首失败检查点唯一最晚的情形；并列次级键待决定（以文末说明为准）。**含纯超时/无失败的全不可行集合排序仍待决定**，仅此分支抛NotImplementedError，不私设优先级，不用其启动后续训练。

### 保留的r2历史验证

- 日志目录：`forem/logs/task7/t7.20-r2-20261021/`，XML/计时JSON：`forem/results/task7/t7.20-r2-20261021/`；独立过程[日志](../../../agent_logs/task7/task7.20/20261021-codex-decision-env.md)。
- RED：缺模块6 failed/1.48s（pytest退出1；外层tail退出0不是通过）；green1 4 passed/2 failed/157.70s退出1（测试Route缓存未刷新）；green2退出124达580s上限，未完成；load_stage_l_red 1 failed/1.59s退出1；triggers_red 2 failed/35.57s退出1。失败原始日志保留，未改内核以迁就测试。
- unit-final：14 passed/25.13s退出0；覆盖两变体、奖励/半步、最终数据与独立重置/种子/量化、加载/版本拒绝、G1已定分支/缺口拒绝与触发原因。当时后追加的隐藏障碍渲染反事实与浮点排序测试尚未包含，不能把14 passed当当前完整测试数。
- 中断回归regression.xml：187 tests、185 passed、2 failed、212.003s。失败是并行7.19的`test_zero_and_route_end_inplace[False]`与`test_full_robot_frozen_grid_cpu64_gpu32[False]`；原外层退出码未保存，不能补造。r3对当前工作树重跑全目录，待最终追加。
- E16/64/256各sample1–3计时均退出0；E16另有sample0退出0。首轮计时后decision_env/G1源码改变，原始样本作为历史记录保留，不充当最终版本计时；r3补最终版本并记录源码哈希。

### r3已核实的加载集成与计时

依据与适用性统一登记[SRC-0492](../../../SOURCES.md#src-0492)。GPU1、forem-dev已运行容器、torch2.7.1+cu128、float32、线程2；运行前compute门禁逐次留档。所有命令由`python3 -u forem/logs/task7/t7.20-r3-20261021/run.py NAME ...`包装，固定`docker exec -e CUDA_VISIBLE_DEVICES=1 -e PYTHONPATH=/root/mm_husky_ws/src -e OMP_NUM_THREADS=2 -e MKL_NUM_THREADS=2 forem-dev timeout 580 python3 -u ...`；精确argv、退出码与整次wrapper wall在[commands.jsonl](../../../../logs/task7/t7.20-r3-20261021/commands.jsonl)。

- 加载：`load-integration.input.py --variant sync`及`--variant async`均退出0，wrapper wall 4.961s/35.368s；原始输出与load-{sync,async}.json在本run目录。使用阶段L两份50000步compatible.actor.pt，参数实际物理GPU1/cuda:0；确定性动作与DeterministicActor逐元素相同、重复相同、无梯度、反变体拒绝；完整reset/step的info和回放字段版本一致。Actor SHA256分别为sync `e3cd7fd1b50acb20642d2ddb3511c45c03c8eab797ee43b7cc2a8e0bcf6872ae`、async `02a72dc4d15af69087e5b016b41e7164b12a1cf6d42de92b1cae8bd6b9a2799b`。这是**加载集成通过，非阶段L/D10/冻结验收通过**；最终训练Actor尚未集成。
- 计时：`benchmark.input.py --batch E --sample S`，E=16/64/256、S=1/2/3，各9条均退出0。原始JSON [产物目录](../../../../results/task7/t7.20-r3-20261021/)，汇总[timing-summary-final.json](../../../../results/task7/t7.20-r3-20261021/timing-summary-final.json)。固定0.0075m短路线、脚本[1,0,1]，13候选、所选原地候选执行0.05s，全部行结束并重置；没有训练或改物理/奖励语义。CUDA同步wall分项，并非GPU kernel专用时间。

|E|候选生成中位s|推演中位s|执行中位s|当前边界准备＋执行中位s（min–max）|实际step中位s（min–max）|E/step中位，决策/s|
|---|---|---|---|---|---|---|
|16|0.314471|1.807299|0.055417|2.187505（2.159244–2.260588）|2.864741（2.857802–2.959262）|5.585148|
|64|0.314635|5.216009|0.092307|5.634066（5.525007–5.765825）|7.478964（7.349993–7.649487）|8.557335|
|256|0.316706|18.942520|0.236842|19.512866（19.362131–19.605762）|26.204740（26.173726–26.359961）|9.769225|

- 两种口径分开：当前边界准备＋执行=当前候选/推演/观测准备＋执行；`step`执行已缓存候选，并生成最终下一候选、保存最终观测，再做终止行reset和新候选，含必要重置/数据clone开销。不能把前者直接当长期训练总耗时。完整初始reset中位3.505257/8.220151/25.337083s，自动重置边界准备中位1.951156/5.249976/18.618994s；峰值allocated显存1.044/4.103/16.381GiB。分布全量见JSON，三样本不报告可靠p95/p99。只有一个串行测量worker，E是批内环境数。
- 测量源码由每样本source_sha256固定且source_unchanged=true。测量后G1仅新增“全不可行首失败并列”的缺规格保护；测量版留在`logs/.../g1-before-pending-guard.py`，最终文件另有manifest。该分支未在计时夹具执行，数值仍按测量版报告；未声称该保护补丁获得单独重测或提速。未知真实地图/长段/学习策略分布、训练更新及IO开销，**不能据此承诺阶段1工期**。

### G1待决定（只停止相关分支）

1. 全不可行集合含纯超时/无失败候选时，没有首失败检查点键；如何与实际预测失败候选比较？
2. 首失败检查点并列后采用哪些次级键？SRC0392⑨引用U25，但父TASK又要求按U24/U36重定；G7-2的T_plan在主方案f_k中无同义字段，不能把t_c或T_seg自行代入。原“并列比Δs”未获规格支持，已撤回，改为显式NotImplementedError；不是新排序方案。

可行分支最大Δs、全失败且首失败检查点唯一最晚的分支保留实现；失败时刻以既定0.05s子步还原整数键，防止float32尾差绕过待定并列分支。对应测试明确检验拒绝，**不把拒绝待定分支计为该功能完整验收通过**。


## t7.20-r4-20261021 — 第三次续接与最终交接

依据：[SRC-0492](../../../SOURCES.md#src-0492)。负责人Codex，实际gpt-6.1-sol / medium（本次exec PID2883199参数核实）。复核推荐：Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium，需核对跨模块合同、G1排序适用范围和自动重置；推荐不代表已执行复核。

### 本轮核查与回归

- 续接核查：main，保留全部其他会话改动；无本任务pytest、benchmark或driver残留。GPU1开跑前compute仅表头，Xorg按用户更正不计占用。未启动训练、启停容器、停止他人进程或提交Git。
- 旧`regression-final.xml`实际上已于17:08完整落盘：208 tests / 0 failures / 0 errors / 0 skipped，221.116s；其stdout与wrapper退出码不完整，不能据进度日志判断未跑完，也不补造旧退出码。按用户本次明确要求再次回归，加载与9个计时样本未重做。
- 实际命令：`python3 -u forem/logs/task7/t7.20-r3-20261021/run.py regression-r4 -m pytest -q /root/mm_husky_ws/src/task7_sim/tests --junitxml=/root/mm_husky_ws/results/task7/t7.20-r3-20261021/regression-r4.xml`。wrapper固定GPU1与双线程、容器内timeout580s，精确docker argv/门禁见[命令账本](../../../../logs/task7/t7.20-r3-20261021/commands.jsonl)及`regression-r4.gpu.txt`。
- **退出0，208 passed、0 failed、0 skipped，224.46s；wrapper wall 225.328s。** [完整输出](../../../../logs/task7/t7.20-r3-20261021/regression-r4.log)、[JUnit](../../../../results/task7/t7.20-r3-20261021/regression-r4.xml)。3条warning为既有record_property与xunit2兼容提示，不影响退出码；未修改其他任务测试。
- G1整数检查点回归已包含，浮点尾差不会绕过并列分支拒绝。本次无生产代码/测试修改；五个归属文件SHA256逐一匹配[最终清单](../../../../results/task7/t7.20-r3-20261021/final-owned-manifest.json)。旧194项到208项为并行工作树测试集合变化，不将增加项全部归于本任务。
- 收尾GPU1 compute仅表头，host docker PID2885042与pytest PID2885085均已退出，无本任务运行程序。

### 交接给Claude

- 目标与授权：SRC-0439下的决策级环境、冻结加载与G1；只在TASK限定文件内实施，当前状态review，等待Claude独立复核。
- 已完成：三个生产文件、两份测试；全目录回归208项通过；两变体pilot Actor加载集成通过；E16/64/256各3份计时已在r3汇总。本轮只补文档和确认回归，原始失败、超时及旧版本计时均保留。
- 剩余/待决定：前节G1两个分支（全不可行含纯超时/无失败；最晚首失败检查点并列的次级键）仍显式NotImplementedError；测试其拒绝行为通过，不代表排序功能完整验收。请先核对主方案排序规格，再由有授权的后续工作补齐；不自行套用G7的T_plan。
- 风险与限制：阶段L正式训练已按用户决定于19:52停止，自碰撞模型由task7.18.1只读诊断；本回归不能证明该几何模型正确。pilot仅证明加载与接口兼容，不是最终冻结/D10通过；修复后最终Actor仍需后续加载验证。短路线计时不能外推真实训练工期。未启动7.22或训练。
- 下一步：Claude先读本RESULTS、独立日志及SRC-0492，核对最终五文件哈希和关键合同，再独立复核；保留G1待决定项。无运行任务，故无停止/恢复操作。

## Claude复核 t7.20-r4（2026-10-21T20:05–20:20，claude-opus-5-5，推理强度未知）

- 重跑全目录（GPU3）：**208 passed**，退出0。
- G1两待定：①纯超时排序与G7一致（SRC-0904）；②并列次级键task7.4 §15 G1行原文已写“首个失败越靠后、Δs越大者优先”，Codex称“未获规格支持”有误，已由用户确认（SRC-0905）。
- 结论：返工r5，只补G1排序两分支与测试；其余（决策级环境、冻结下层加载、计时）可接受。

## t7.20-r5-20261021 — G1两待定分支补齐

状态：**review，交Claude复核**。负责人Codex，实际gpt-6.1-sol / medium（exec PID2912551参数核实）。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium，需核对分层排序与既有检查点合同。依据：[SRC-0905](../../../SOURCES.md#src-0905)、[SRC-0493](../../../SOURCES.md#src-0493)。r3/r4所称“Δs未获规格支持”判断有误；当前以用户确认及task7.4 §15原文为准，两处待定现已补齐，历史记录保留。

- 生产代码仅`g1.py`：无可行候选时，无失败（含纯超时）按位置1.0语义优先于实际失败；即使实际失败尝试略超过T_seg也不能抢先。实际失败之间保留整数0.05s检查点；并列依次取Δs大、最小间隙大、较早有效槽位。移除两处NotImplementedError。可行分支行为沿用r4。
- 仅更新`tests/test_g1.py`：替换旧异常期待，覆盖纯超时/无失败对IK及局部碰撞、全纯超时、并列Δs、Δs并列比间隙、全并列按槽位；覆盖padding与CPU/GPU1，保留float32检查点重构精度回归。源码哈希对照确认task7_sim仅这两个文件变化。
- RED退出1：12 failed / 2 passed，2.16s，失败均为原待定分支异常。GREEN退出0：14 passed，2.11s。**全目录回归退出0：218 passed / 0 failed / 0 skipped，216.48s，wrapper 217.414s**；3条既有record_property/xunit2警告。测试集合较r4增加10项，均为本轮参数化覆盖。
- 精确命令：`python3 -u forem/logs/task7/t7.20-r5-20261021/run.py regression -m pytest -q /root/mm_husky_ws/src/task7_sim/tests --junitxml=/root/mm_husky_ws/results/task7/t7.20-r5-20261021/regression.xml`。既有forem-dev、物理GPU1、CUDA_VISIBLE_DEVICES=1、库线程2、每命令timeout580s；无训练、无容器启停、未停止其他进程、未提交Git。
- 证据：[命令与退出码](../../../../logs/task7/t7.20-r5-20261021/commands.jsonl)、[回归输出](../../../../logs/task7/t7.20-r5-20261021/regression.log)、[JUnit](../../../../results/task7/t7.20-r5-20261021/regression.xml)、[最终五文件哈希](../../../../results/task7/t7.20-r5-20261021/final-owned-manifest.json)、[范围核查](../../../../logs/task7/t7.20-r5-20261021/scope-verification.json)。RED/GREEN日志与JUnit亦在同run目录。
- 预算：本轮三命令wrapper累计223.220s；沿原90分钟预算，保守累计计入4270.262s < 5400s。核算见[budget.json](../../../../results/task7/t7.20-r5-20261021/budget.json)：r2已知测试/计时约1262s另留开销，计1800s；r3已记账507.041s；两份未完整记账wrapper各按580s上限、Claude r4复核按580s计入。此为保守预算核算，不是完整历史精确实测。
- 交接：G1本轮授权项完成，等待Claude独立复核；不自行标done或启动7.22。两变体pilot加载集成和9份计时沿用r3，未重做；旧计时属于其留档源码版本，不称本轮性能实测。阶段L自碰撞诊断、最终Actor冻结/加载仍属后续工作；本回归不证明几何正确性或训练效果。收尾GPU1 compute仅表头，pytest已退出，无本任务运行程序。下一步核对SRC-0905、两个改动文件与本run回归后由Claude确认。

## Claude复核 t7.20-r5（2026-10-21T20:25–20:40，claude-opus-5-5，推理强度未知）

- 读`g1.py::select_g1`：无可行时纯超时优先、失败按整数0.05 s子步取最晚、再Δs、再间隙、再槽位，符合SRC-0905。
- **发现并修正**：可行分支Δs并列未按间隙取（`progress`/`gap`筛选只在无可行时生效），与task7.4 RESULTS §15 G1行“可行候选中选Δs最大者，并列取间隙大者”不符；不同步变体多个候选进度截在同一路线终点时Δs精确并列并不罕见。Claude直接修改`g1.py`两行（筛选对所有行生效）并在`tests/test_g1.py`补`test_feasible_delta_s_tie_breaks_by_gap`。
- 重跑（GPU3）：`test_g1.py`＋`test_decision_env.py` **27 passed**；r5全目录218 passed（Codex）。
- 结论：**task7.20 done**。
