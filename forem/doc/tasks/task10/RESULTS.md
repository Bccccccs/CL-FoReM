# task10 结果与交接

2026-11-02，Codex 已登记[目标](TASK.md)与[流程](PROCEDURE.md)。本次交付仅为计划，接口适配、实现、训练与评估尚未执行。

接手时在 /home/ybc/projects/CL-FoReM 读取 codex/task10-upper-wm 分支，仅细化上层 SAC 协议。原始产物在同一仓库的 forem/results、forem/logs。

[用户决定及接口依据](../../SOURCES.md#src-1360)。推荐 GPT6.1sol / medium、Sonnet5.5 / medium，用于跨模块接口核对。

## 2026-11-02 · 设计 v1 交接

Codex 已根据用户委托选定单个冻结 B3、普通上层 stage 1、按尝试时钟折扣的严格成功奖励及进度塑形，并写出 A–D 接口、训练、试训和评估合同。[协议](PROCEDURE.md) · [源码与工程选择](../../SOURCES.md#src-t10-001)。设计交付完成。实现、B3 动作一致性、场景配对、吞吐、学习曲线和成功率均尚未执行。既有下层成功率不能作为本任务结果。

执行入口为本地 codex/task10-upper-wm 分支，工作树 /home/ybc/projects/CL-FoReM-task10，原始 B3 文件在 /home/ybc/projects/CL-FoReM/forem/results。先读根 AGENTS.md 及本层三文档，按 A→B→C 交付有界证据。风险是旧环境沿用 legacy、短回合被序列采样漏掉，以及推演不慎读取执行真值。逐项核验后将 run-id、源码版本、输入哈希、命令、退出码、实际决策/更新数、最慢阶段、缺失及成本估算追加到这里。D 依赖单独预算授权。推荐 GPT6.1sol/high、Sonnet5.5/high，理由为跨层执行与回放一致性核查。

派发更新：执行负责人可自行选模型与推理强度并派发子 Agent，具体分工由接手者登记。见[父流程](PROCEDURE.md)及[授权](../../SOURCES.md#src-t10-002)。


## 2026-11-02 · A→B→C 执行（active）

负责人 Codex；工作树 `/home/ybc/projects/CL-FoReM-task10`，分支 `codex/task10-upper-wm`，起始HEAD为7b705c1且祖先检查rc0；父实际模型/强度未知。推荐GPT6.1sol/high、Sonnet5.5/high，原因是跨层时钟、终局折扣与回放边界集成。当前用户授权单次1200真实决策/200更新/1800s及4场景配对另1800s，全部Agent共用；正式长训/task11未授权。[SRC-T10-006](../../SOURCES.md#src-t10-006)。

三子模块通过父复跑：冻结B3 69源码/9推理依赖hash及同设备CPU/CUDA原版对照误差0（14测试）；学习器支持零dt、终局独立mask及短回合首步；环境局部预测与真实执行分离、attempt clock/首次失败、只selected真实标签。父组合117passed/2既有条件skipped（21.02s/rc0），最后增加pending候选禁止入回放及atomic_json目录fsync后，定向35passed/7.57s/rc0；py_compile及git diff --check rc0。证据和限制分别见[SRC-T10-003](../../SOURCES.md#src-t10-003)、[004](../../SOURCES.md#src-t10-004)、[005](../../SOURCES.md#src-t10-005)、[007](../../SOURCES.md#src-t10-007)。

独立task10.4发现并已修复两P1：真实执行完整原子journal先于账本complete；容器内timeout1798s TERM/1800s KILL，短有界监督夹具实际-9/0.203s。磁盘写失败保留in_flight、不重试；混合批reset保留survivor状态/观测/候选逐位一致。环境不支持中途恢复；offline-learner仅验证学习器RNG/下一回放/更新计数，不能作为在线collector恢复。[独立审查](task10.4/RESULTS.md)。

运行版本将在启动前本地提交；run-id `t10-smoke-20261102-s101`；新产物位于本工作树`forem/results/task10/t10-smoke-20261102-s101`与`forem/logs/task10/`。独立容器`forem-task10-runtime`，GPU1，主仓forem及results只读，工作树forem挂/workspace；2 CPU线程，8真实env，局部推演仅有效槽；配置`forem/config/task10/smoke.json`。先检查GPU空闲后启动；目前试训/配对尚未执行，所有真实计数为0。


### 唯一试训结果（failed；未重启）

run-id `t10-smoke-20261102-s101`，运行代码17f1833，首次启动15:32:00.657675+08，原1800s截止未改变。pre-ledger UID错误零交互后修为`docker exec --user1004:1004`；最终16真实决策、16回放、0更新，墙钟332.8524s，worker body251.5289s，reserved/completed均16、in_flight0；已完成8回合中5严格成功仅为随机预热诊断。[实测/故障/推导SRC-T10-008](../../SOURCES.md#src-t10-008)。

混合复位后旧ReplayAdapter堆叠非模型输入的变长diagnostics，导致[4]/[]冲突；两份完整执行journal与全部失败均保留。新适配器仅批处理模型消费字段，未删审计数据；原适配器2failed、新适配器对合成及真实回放2passed，最终120passed/2既有条件skipped/rc0，独立审查复核通过。**本轮不重启试训**。尚无有效训练梯度、update吞吐、学到选点或collector恢复证据，正式训练门未过。0更新actor仍将用于四场景配对管线检查，不能把配对差异解释为学习收益。

原始产物：`forem/results/task10/t10-smoke-20261102-s101/{contract.json,training-budget.json,training-summary.json,real-executions/,offline-learner.pt,final.actor.pt}`；原日志`forem/logs/task10/t10-smoke-20261102-s101-train.log`，RED/GREEN及最终测试日志同目录。final.actor SHA256 b87d7d9223a80ca134508b101a5220ef447ea71e8ee0dfe17e40f3cc12a01920。`pending-intent.json`是已被16条journal/账本覆盖的旧intent，非未决交互；不得仅凭文件名判定inflight。


## 2026-11-02 最终交付 · review / NOT_READY

**结论：实现及确定性合同已交付，唯一试训失败后已修复接口；尚不具备正式训练条件，不能把当前actor交task11作训练基线。** 推荐GPT6.1sol/high、Sonnet5.5/high继续跨层时钟/回放/恢复验收；父实际模型/强度未知。独立审查实际terra/high，sol容量错误时换模原因已记录。源证据：[试训与修复SRC-T10-008](../../SOURCES.md#src-t10-008)、[配对/审计/成本SRC-T10-009](../../SOURCES.md#src-t10-009)。

### 版本与产物

- 分支`codex/task10-upper-wm`包含7b705c1；实现a2af781，修复绝对墙钟入口17f1833，回放适配修复及配对代码1fb5eb6。后续只读复算/审计、包装过期检查与最终文档在本分支追加提交，无推送/合并。
- run-id：`t10-smoke-20261102-s101`；试训实际版本17f1833，配对实际版本1fb5eb6；最后checkpoint就是0更新actor，未按validation选模。
- 原始产物绝对目录：`/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-smoke-20261102-s101`；日志：`/home/ybc/projects/CL-FoReM-task10/forem/logs/task10`。`contract.json`保存实际源hash、冻结清单、config及实际输入shape，`paired-execution-contract.json`单独绑定配对版本、4地图和actor SHA；`audit-final.json`保存关键证据SHA。
- B3 seed4718 actor SHA `3db11d9f00317849e35a523d66d0935ebc2e3567d82c519ccc42f3d8de42f7ae`；上层final.actor SHA `b87d7d9223a80ca134508b101a5220ef447ea71e8ee0dfe17e40f3cc12a01920`。主仓依赖全程只读，冻结69源/9产物最终复查一致。

### 本轮计数和配对

试训16条真实决策、16回放、0更新，reserved/completed=16、inflight=0；唯一试训failed/rc1，墙钟332.852s，未重启/扩预算。16条中含1条真实零尝试停滞选择；实际尝试2359子步、提交2299子步，累计模拟尝试117.95s/提交114.95s（按全部环境求和，不是墙钟）。3条执行各20次失败全部入journal/回放；8完成训练回合5严格成功仅为随机预热诊断。原始reward/base/shaping/discount、raw结束标志与独立bootstrap mask均保留。候选批次身份由(run_id, environment_id, episode_id, decision_index)与link确定，selected映射回同批world_pose；仅所选槽有实际标签。

配对每张图同场景seed101、随机策略独立seed102，各跑一次完整回合；末因按实际Core优先级。四对初态hash、proposal seed和场景sidecar/boxes hash逐项一致。表中决策数是评估决策，未混入训练预算。

|validation map_id后缀|actor严格成功/决策/末因|uniform严格成功/决策/末因|成对结果|
|---|---|---|---|
|00000|否 / 1 / failure_limit|是 / 2 / strict_success|负|
|00001|否 / 1 / failure_limit|是 / 2 / strict_success|负|
|00002|否 / 1 / failure_limit|是 / 3 / strict_success|负|
|00003|否 / 1 / failure_limit|否 / 1 / failure_limit|平|

两策略各4/4完整、缺失0；严格成功actor0/4=0%，uniform3/4=75%，胜0/负3/平1。共12条评估决策，配对rc0、380.483s。**actor未训练，该差异只用于管线核查，不是学习效果或正式基线成绩。** 父只读审计与独立task10.4核对一致。

### 性能与成本

GPU1映射cuda:0，模型float32、torch2.7.1+cu128，8训练env、评估1env、torch线程2、无docker CPU/memory/cpuset配额；图形/ROS未启动。GPU实际compute已核实；试训峰值torch已分配5388289536bytes≈5.02GiB（不等于nvidia-smi总占用）。B3前后tensor hash相同且无grad；上层参数在CUDA，因0更新Adam无训练状态，不能把CUDA可用当有效梯度证据。因UID无home，torch JIT磁盘kernel cache警告与禁用状态保留。

|试训分项|次数|总墙钟秒|p95秒|
|---|---:|---:|---:|
|下层加载/hash|1|0.243|0.243|
|初始复位（含首候选推演）|1|45.769|45.769|
|真实执行段（含真实结果整理）|2批|57.294|30.023|
|下一候选边界|2|71.964|39.001|
|结束行复位（含候选推演）|2|72.189|36.856|
|上层记忆/推理（含失败调用）|3|0.120|0.081|
|执行journal|2|0.142|0.073|
|回放CPU搬运|2|0.094|0.047|
|checkpoint及恢复核对|1|0.943|0.943|

执行细项中Core.step自身两批23.483s/25.158s；其余为实际feature/risk/边界整理。已完整日志化的推演至少163有效槽、822批/33853行B3调用、34642尝试/34080提交子步；最后一次reset的推演诊断未单独落日志，**这是下界，不是全量计数**。实际执行B3为369批/2952行调用（含完成后仍在同批推理的行）；IK、碰撞、局部栅格和B3网络尚未单独profile，不能断言其中某个是唯一热点。

复位与候选推演占当前环境路径主要开销。试训采集分项合计247.814s/16=15.488s/决策，按本小样本折算采集1000条约4.30h。配对8回合380.483s，均摊47.560s/完整回合；复位220.675s、真实执行100.954s、后续边界48.885s。条件成本式（秒）：`T≈15.488×D + c_update×U + 47.560×N_eval + T_checkpoint`。更新系数未测；种子、冷启动、短样本和训练后选点分布变化均限制外推，不能承诺正式总工期。

首次冒烟入口至配对summary落盘全局1130.648s（18分50.648秒，含修复/核验间隔）；两阶段预算wall相加713.336s；已计时worker活动632.012s（有效训练主流程251.529+配对入口380.483，不含首错误进程及部分import，非CPU时间）。两个阶段分别低于1800s，未发生硬kill；容器内timeout短夹具可强制kill，过期绝对epoch入口直接124退出夹具通过。

### 可复算命令与停止状态

以下原始运行命令均已执行，**不要覆盖或重置既有账本**；相同目录再次运行会拒绝。新采集或长训须另行派发预算。容器已停止，复算如需torch先`sg docker -c 'docker start forem-task10-runtime'`，该重启步骤此处仅作复算说明、尚未再次执行。

```bash
# 当次试训（UID初错与修复均在原train.log，沿用第一次绝对epoch）
sg docker -c 'docker exec --user 1004:1004 -e PYTHONPATH=/workspace/src -e TASK10_STARTED_EPOCH=1793604720.657675853 -e TASK10_CODE_COMMIT=17f1833 -e TASK10_PHYSICAL_GPU=1 forem-task10-runtime bash /workspace/scripts/task10_run_bounded.sh train /workspace/results/task10/t10-smoke-20261102-s101'
# 当次配对
sg docker -c 'docker exec --user 1004:1004 -e PYTHONPATH=/workspace/src -e TASK10_CODE_COMMIT=1fb5eb66e2a4bafdd147afcf805412ba03031de5 -e TASK10_PHYSICAL_GPU=1 forem-task10-runtime bash /workspace/scripts/task10_run_bounded.sh paired /workspace/results/task10/t10-smoke-20261102-s101'
# 纯读统计复算，不启动模型或环境（宿主可执行）
cd /home/ybc/projects/CL-FoReM-task10
python3 forem/scripts/task10_report.py --run forem/results/task10/t10-smoke-20261102-s101 --output forem/results/task10/t10-smoke-20261102-s101/accounting-final.json
# 只读张量/哈希/配对一致性审计（最后一次实际rc0，结果PASS；训练门NOT_READY）
sg docker -c 'docker exec --user 1004:1004 -e PYTHONPATH=/workspace/src forem-task10-runtime python3 /workspace/scripts/task10_audit.py --run /workspace/results/task10/t10-smoke-20261102-s101'
# 最终确定性组合（实际120passed/2既有条件skipped，20.99s，rc0）
sg docker -c 'docker exec --user 1004:1004 -e PYTHONPATH=/workspace/src -e TASK10_ARTIFACT_ROOT=/reference -e TASK10_SMOKE_OUTPUT=/workspace/results/task10/t10-smoke-20261102-s101 forem-task10-runtime python3 -m pytest -q -p no:cacheprovider --basetemp=/tmp/task10-final-deterministic /workspace/src/task10/tests /workspace/src/task7_upper/tests'
```

运行均结束，现场GPU compute为空；本任务自建forem-task10-exec、forem-task10-runtime已停，未停止其他容器。保留主仓所有产物/进程与工作树历史。

### 未通过项与下一步交接

1. **C有效训练验收未通过**：0更新，未达1000预热，尚无真实GPU上层梯度、实际Adam设备/吞吐、学习曲线或选点收益证据；不能把CPU夹具梯度当本次GPU通过。
2. **在线恢复未验收**：offline learner恢复RNG/下一采样/更新计数通过；环境中途恢复明确不支持，未交可用于正式长训的可重建采集边界恢复方案。
3. **性能证据不完整**：只有粗分项，实际update/IK等细分与全量推演审计缺失；16条外推不够核定正式规模/时限。
4. 配对管线完整通过，0更新actor失败如实保留；训练baseline未交付，task11不进入实施。

接手者先读本层三文档及独立日志，按上述证据核查修复代码；下一次若获派发，应沿既定A→B→C先补有界有效更新、恢复及端到端成本证据，再由决策者/用户锁D的预算。**本轮不擅自重启、扩预算、缩预热或改科学条件。** 当前负责人Codex，状态review；无运行任务，风险与剩余项如上。
