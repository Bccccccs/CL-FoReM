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

### 决策者复核 · 2026-11-02

A/B 接口与四场景配对管线验收，C 有效训练与恢复未通过，D 暂不派发。报告复算与八项哈希核对一致。更正上文“下一采样通过”的口径：本次 replay 仅 16 条，restore_evidence 的 32 条抽样分支未执行；真实抽样恢复仍待验。下一轮优先细分复位/候选推演成本、补齐全量计数并验证同输入等价，再核定覆盖预热与有效 GPU 更新的墙钟。恢复验收需同时覆盖非空样本身份、更新后的优化器和可重建采集边界。[复核依据](../../SOURCES.md#src-t10-010)


## 2026-11-02 · 63e1f6e审核后的成本与恢复补证（review）

本轮只补成本/恢复与预算建议，未启动新的1000预热试训。原失败试训16/0及全部旧证据保留。推荐GPT6.1sol/high、Sonnet5.5/high：跨层计时、GPU状态、恢复锁和预算需要因果核对；实际父模型/强度未知，10.5 terra/high、10.6 sol/high、10.7独立terra/high，委派记录见各节点。[授权/界限SRC-T10-011](../../SOURCES.md#src-t10-011)。

新run namespace `t10-cost-recovery-20261102`，产物绝对根`/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-cost-recovery-20261102`，log根同工作树`forem/logs/task10/`。代码以63e1f6e为起点，准备提交d22169f，最终实现/只读报告随本分支提交；实际脚本/恢复模块SHA在measurement-contract、diagnosis、online config及汇总中，未把dirty运行假称固定旧commit。

### 计数与同输入对照

- 真sampler从seed101/8env重建旧两批selected，16行的观测、候选/mask/19维f_k、实际结果及失败计数逐项与旧journal一致；比较双方先用旧exact_cpu表示，只排除`candidates.diagnostics.search_wall_seconds`。
- 完整baseline包括初始、两次prepare与两次结束行reset，共5边界。名义312槽、有效196槽，推演1037 B3批/40948行调用，41893尝试/41166提交；真实执行2359尝试/2299提交、369 B3批/2952行调用。末次reset33槽/7251尝试/7086提交是本轮重建补计，旧日志仍保持其历史下界。[SRC-T10-012](../../SOURCES.md#src-t10-012)。
- 首探针8行因decoded-grid键集合比较失败；修复后余24行继续原900s绝对截止，完整baseline完成，但instrumented被外层截止rc124，未通过全轨迹对照。首失败8已确认、新baseline16已确认、仪表批8预留未确认；原性能相位保守按32消费，不重开窗口。
- 父从预留240s做一次0真实选择/0更新、初始8场景、最多104槽/256提案的独立instrumented复核；50.110s/rc0，初边界观测/候选逐位等于旧首journal及baseline同SHA，实际68槽。仅此初边界对照通过，不扩大为全instrumented轨迹通过；baseline和缓存factory reset总耗时不能拿来宣称仪表/优化收益。**未采用性能优化。**

### 采集瓶颈分解

完整baseline业务wall共250.984s/16：reset（含内部候选）118.616s、真实执行59.414s、prepare72.955s。实际场景采样只有7.875s，44提案/16接受，故reset主成本不是生成新场景，主要在其内部推演。候选生成合计1.370s，所有边界推演合计182.057s（这两个时间已经嵌于reset/prepare，不再次相加）。

初始68有效槽预测inclusive39.686144s的exclusive分解如下；这是单初边界profile，非所有地图稳态分布。

|推演分项|exclusive wall秒|占39.686s|
|---|---:|---:|
|IK调用（含内部机器人分支检验）|24.4241|61.54%|
|B3预处理/推理|0.4695|1.18%|
|局部碰撞|2.2812|5.75%|
|栅格crop|0.7108|1.79%|
|observe（含路线栅格投影等）|3.1665|7.98%|
|扫掠风险（含几何）|4.0716|10.26%|
|其余Core调度/未包裹计算|4.5624|11.50%|

同初态候选生成1.2895s（内含IK1.2708s），实际采样5.2114s、episode reset setup5.2766s。GPU event为含CPU提交间隙的嵌套stream interval，不是kernel compute；父子inclusive与exclusive不可重复相加。瓶颈证据支持先检查推演IK及观测/风险路径，不能称B3网络为主要瓶颈。[完整来源/限制SRC-T10-012](../../SOURCES.md#src-t10-012)。

### 恢复修复及验收范围

`runner.restore_evidence`现转入`recovery.verify_learner_checkpoint`，有数据时sample(min(32,len))并核对非空身份，空池not_verified。旧真实16在`collector-boundary/real-replay-evidence.json`独立验证sample16身份、RNG/模型/计数，通过；不代表正式训练32序列或预热达标。[SRC-T10-013](../../SOURCES.md#src-t10-013)。

GPU派生夹具复制原16到32，provenance明确非新真实、非在线预热；共5次跨分支update。更新1次的checkpoint有85个Adam状态条目，model与moments原存储CUDA0、step CPU；仅vcm/candidate_encoder/head_a变动。加载后的完整model/optimizer/target/scheduler、下一32样本身份、RNG精确；下一GPU更新损失全字段相同，但CNN weight及Adam moments共11叶逐位不同（weight最大3.72529e-9）。严格下一更新验收未通过，原因尚未证实，不因数值小而放宽容差；原300s截止后没有再做deterministic诊断。诊断rc0只表示记录完成，JSON为exact_mismatch。CPU组合34passed/8.60s、profiling CPU7passed，二者为夹具，不替代在线结果。

安全采集边界限定：全batch自然episode结束，最后transition已入回放且journal原子持久化，prepare_next完成，无pending/inflight，下一回合尚未采样。存sampler三purpose RNG、policy generator、episode IDs/totals、learner/replay、账本/hash/原monotonic deadline及Linux boot_id。持flock后重验账本/journal/owner/时限，拒同PID（显式test_only例外）、旧owner活着、stale账本、自定义可变factory或重启host；修复了锁前校验TOCTOU。

在线实际验证只用batch1：PID223自然终局第1行保存后退出，PID231新进程从同checkpoint重建下一场景/观测/候选/采样RNG/generator/选点均exact，提交恢复后1行；账本reserved=completed2/inflight0，journal为episode1/2各decision0，无重复，继续使用原360s deadline，旧snapshot因ledgerchanged拒绝。外层143.857s/rc0，0在线更新。**未验证batch8全终局边界可用性、任意中途恢复或跨主机重启。**

### 下一试训预算建议（交决策者核定，尚未执行）

保持seed101、冻结B3 seed4718、batch8、1000随机预热、既定奖励/折扣/严格成功与每新增真实决策一次update。建议下一端到端试训仍用**1200条真实决策、200次更新，训练墙钟7h**；原四场景配对另30min，候选总7.5h。现有runner的1800s硬限未擅改，新预算核定前不能照此启动。

复算：采集系数=(新baseline业务250.984s + 旧上层.120s + journal.142s + replay搬运.094s)/16=15.708732s/决策；1000预热约4.364h。短GPU诊断两next-update连恢复/比较共3.9285s，只得这两次平均更新耗时≤1.96425s；估价向上取4s/update，固定预留60s，整体乘1.25作为工程余量：`(1200×15.708732 + 200×4 + 60)×1.25 = 24638.10s ≈ 6.844h`，取整7h。[SRC-T10-014](../../SOURCES.md#src-t10-014)。

这些系数/余量不是置信上界：只有16个独特旧决策；派生fixture只有40个loss位置，正式最多256且更长prefix未测。7h在当前采集系数/60s固定费下隐含update平均余量31.448s，但尚未证实长prefix/重尾reset在此内。建议适用batch8原路径，**不适用直接改batch1**；batch8恢复未验、GPU严格下一更新未过，交由决策者核定风险和后续验收口径，不称正式长训条件通过。

### 总账、复算和交接

四相位caps900/300/360/240合计1800s；worker666.288s，首测至最后在线产物global1762.212s（含修复/等待）。新真实测量已确认26行，另8预留未确认保守按34收费（上限36）；GPU fixture5次单列。原试训16/0、旧三actor/地图/全部失败记录未改。总账`measurement-ledger.json`保留首错误、续测原epoch/attempt及124；不能把被杀后陈旧active快照当运行中。

```bash
cd /home/ybc/projects/CL-FoReM-task10
# 只读复算（已执行rc0，不启动训练/模型）
python3 forem/scripts/task10_cost_recovery_report.py --root forem/results/task10/t10-cost-recovery-20261102 --old forem/results/task10/t10-smoke-20261102-s101 --output forem/results/task10/t10-cost-recovery-20261102/summary-final.json
```

原始有界命令、参数和PID完整记在measurement-ledger及phase log；同phase只允许显式修复后续原deadline，不能新建预算重跑。只读storage审计为`task10_recovery_storage_audit.py`，数据为storage-audit.json；独立审查见[10.7 RESULTS](task10.7/RESULTS.md)，恢复原始CPU日志task10.6-cpu-recovery-crossprocess2.log。所有新增代码/配置/脚本位于forem，未改冻结参考69文件或科学参数。

交接给决策者：成本与限定恢复已有实测；完整instrumented轨迹、默认GPU严格下一更新与batch8恢复仍未通过/未验证。建议核定上述7h+配对预算及这些验收口径，之后另派新试训；本执行者不自启千次预热、正式训练或task11。负责人Codex、状态review；推荐GPT6.1sol/high、Sonnet5.5/high继续核验，理由为上述跨层状态/时钟/预算约束。

### 第二次决策复核 · 2026-11-02

复算 summary-final 与原件一致。接受旧16条非空采样、初始边界成本和 batch1 限定恢复。7h 可列排期估值，当前不放行启动。正常 train 入口尚无 batch8 采集保存/恢复调用；Python 预算、外层监督均仍为30分钟。下次先用同一数据做连续对连续、连续对存取后下一更新的 CUDA 对照，再经正常入口验证 batch8 可达安全边界的跨进程恢复与原截止/账本，不能主动截短 episode 来制造边界。按同设置列实测耗时；若实际批次无法到达边界或确定性配置改变成本，回报限制与预算。完成后再复核 1200/200 的试训放行。[复核记录](../../SOURCES.md#src-t10-015)

## 2026-11-02 · GPU归因与正常batch8入口恢复（review；不放行试训）

本轮严格按[授权SRC-T10-016](../../SOURCES.md#src-t10-016)处理两个问题。工作树`/home/ybc/projects/CL-FoReM-task10`，分支`codex/task10-upper-wm`，接手HEAD=ca57b4b、祖先检查rc0，初始工作区干净。接线/真实运行提交 **afc56f6**；独立审核后的严格字节与完整恢复原件修复 **ede1299**。原始测量诊断SHA及后来非有限JSON小修分别保留，不把dirty运行假称已提交旧版。未推送、合并或改参考仓库。

父Codex实际平台模型/强度未公开，记未知；task10.8与10.9实际sol/high，task10.10独立terra/high。推荐后续Codex GPT6.1sol/high、Claude Sonnet5.5/high，因CUDA归因与跨进程采集时钟/账本需跨模块核对。执行者有范围内选模/委派权限，子任务已先建三文档、独占写入登记，共享父预算/截止；父复跑并核对原件后汇总。[分工与全记录](../../agent_logs/task10/20261102-codex-gpu-batch8.md)。

### 1. GPU差异能否归因于保存/恢复？

**不能依据现有差异归因于存取；差异在完全不存取的重复GPU更新中也能复现。** 复用旧已更新Adam的derived-fixture.pt，同一内存前态分别做内存/内存与连续/实际存取两组对照；默认、确定性、默认复现各4次，共12次fixture更新，0新增真实。每组更新前model/target/Adam/scheduler/温度/模式/设置/RNG和下一32anchors（40loss位置）逐位一致；loss和更新后RNG一致。

默认及复现的两组都在CNN裁剪前梯度观察到差异。首次默认纯内存组按稳定字段遍历的首差为`model.vcm.f_enc.cnn.0.bias[0]`，最大绝对差`5.4569682106375694e-12`；更新后权重`cnn.2.weight`最大`3.725290298461914e-9`，Adam亦不同。存取组同bias梯度首差`2.9103830456733704e-11`。这不是CUDA执行先后定位。设置`CUBLAS_WORKSPACE_CONFIG=:4096:8`（Python启动前）、`torch.use_deterministic_algorithms(True)`、`cudnn.deterministic=True`，并保持threads2、TF32=False、benchmark=False后，两组所有loss/梯度/权重/Adam比较逐位一致。

证据支持默认GPU更新的非确定性表现；**具体CUDA算子/kernel原因未定位**。未放宽逐位验收；默认设置的严格下一更新仍不通过。三次Python过程9.970928/10.734226/9.943892s；默认首更新1.064186s、热0.090655–0.093046s，确定性首更1.260951s、热0.136430–0.138486s。不能用40loss夹具的热值估正式256loss且长prefix更新。六份原始pt已CPU重算全部比较树，与原JSON相同。[SRC-T10-017](../../SOURCES.md#src-t10-017) · [10.8结果](task10.8/RESULTS.md)。

### 2. 正常batch8入口从什么边界续跑，哪些已实测？

代码只在**同一批8行全部自然终止、prepare_next已清pending、末条转移已入回放、journal持久化、账本无inflight且计数一致、下一回合尚未采样**时显式保存并退出；新PID恢复原ledger与monotonic deadline，不重置截止。mixed结束行照常reset；没有等待凑全结束、提前终局或改变地图采样。`--resume`核对源码/actor/配置/当前GPU合同、owner、boot_id、journal/ledger摘要与独占锁；同主机同boot的干净边界才支持，任意中途/主机重启不支持。

确定性CPU夹具通过正常`runner.train`验证mixed→reset→全终局保存、独立进程下一批8环境观测/候选/掩码/选点/ID/RNG、journal/回放/账本及原截止一致、无漏重。独立审核发现旧数值比较未区分正负零、恢复端完整原件未落盘、GPU合同及deadline验收缺口，真实运行结束后以RED反例修复至ede1299，再做**163passed/3条件skipped、40.09s、rc0**组合；3跳过为CUDA下层1项与显式GPU训练2项。最终CPU双端start/end原件字节复算均exact。不能把CPU合成数据称真实恢复。

**真实batch8恢复尚未验证。** 正常入口afc56f6，冻结B3 seed4718、上层101、batch8、既定1000预热/环境语义不变；新验证cap主56、参照额外最多8、恢复在主账本内收费，总64、0更新、阶段1320s。7批实际56决策，逐批自然结束行数如下。

|批|真实决策累计|自然结束行数|安全边界|
|---|---:|---:|---|
|1|8|4|无|
|2|16|4|无|
|3|24|2|无|
|4|32|5|无|
|5|40|7|无|
|6|48|6|无|
|7|56|5|无|

达到预登记主采集决策上限后退出rc0，Python wall614.676152s、外层监督616.170092s、阶段616.172633s；未用剩余总额度改变主56cap继续采集。reserved=completed=56、inflight0、回放56、在线更新0；7份journal/56身份/560实际字段与回放逐位核对，无漏计/重复，选点均有效、B3前后不变。最后3活动行记未完成，未伪造终局；离线checkpoint不能续环境。**没有全8自然边界，因此没有真实collector checkpoint、连续参照批或新PID恢复，也未实测真实恢复后的场景/观测/候选/选择/episode与decision ID/journal/ledger/原截止。** 最终ede1299严格修复只有CPU复验，不虚构为本次真实afc56f6的通过条件。[SRC-T10-018](../../SOURCES.md#src-t10-018) · [10.9](task10.9/RESULTS.md) · [独立审核](task10.10/RESULTS.md)。

### 3. 是否建议放行1200真实决策、最多200更新？

**当前不建议放行，交回决策者核定。** 7h继续只作排期估值。新真实采集`616.172633/56=11.003083s/决策`，含实际结束位置/复位分布，与旧16条不是同输入优化比较，不能称性能提升。保守取旧15.708732s/决策，维持原工程假设4s/update、固定60s、1.25余量：`(1200×15.708732 + 200×4 +60)×1.25 =24638.098s≈6.844h`，整小时候选7h；估计不是置信界或承诺。真实batch8安全边界/跨进程恢复未验，默认GPU严格下一更新未过，确定性设置尚未核定纳入正常训练合同，完整32×8和长prefix成本仍未测。[SRC-T10-019](../../SOURCES.md#src-t10-019)。

本轮测量与必要复验global1318.725992s（总cap1800），GPU/采集受监督worker wall累计655.057321s，56真实/12fixture更新；所有失败与等待计入原global窗，CPU测试/原件复算0真实/0GPU更新。没有参照/恢复的隐含免费运行；未启动1000预热、7h试训、四场景配对或task11。原1800s硬限未增加。

### 原始产物、实际命令与复算

统一根：`/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-gpu-batch8-20261102/`。GPU原件在`gpu-{default,deterministic,default-repeat}/`，紧凑GPU复算`gpu-analysis.json`；正常入口`batch8/`，总账`measurement-ledger.json`保存全部实际参数、命令、返回码、时限/计数，父汇总`summary-final.json`，账本审计`storage-audit.json`，最终CPU原件`cpu-final/`。原日志在本工作树`forem/logs/task10/`，前缀`t10-gpu-batch8`；RED和独立记录也保留。

实际启动正常入口的父命令（已执行rc0；**不可重跑同账本**）：

```bash
python3 -u forem/scripts/task10_batch8_probe.py --root forem/results/task10/t10-gpu-batch8-20261102 --commit afc56f647108c79456dc35d0da2ec8edf779614b
```

以下为只读复算，不采集、不更新；GPU报告读取6份原始pt，并非重跑GPU。容器挂载工作树`/workspace`、主仓只读`/reference`，核对其状态再用。

```bash
cd /home/ybc/projects/CL-FoReM-task10
python3 forem/scripts/task10_gpu_batch8_report.py --root forem/results/task10/t10-gpu-batch8-20261102 --output /tmp/task10-gpu-batch8-recomputed.json
cmp /tmp/task10-gpu-batch8-recomputed.json forem/results/task10/t10-gpu-batch8-20261102/summary-final.json
# torch原件审计：CUDA隐藏，输出/tmp，不改原账本
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 /workspace/scripts/task10_batch8_storage_audit.py --run /workspace/results/task10/t10-gpu-batch8-20261102/batch8 --output /tmp/task10-batch8-storage-audit.json'
# GPU六份pt复算的实际参数见task10.8 RESULTS；同样只读CPU
```

运行已结束；负责人Codex，状态review。下一步由决策者核定确定性配置和真实batch8边界验证办法/预算，不能将本轮接线/CPU通过直接放行为1200/200。原始证据、剩余项、风险和监控/停止记录均在父独立日志；不要求接收者依赖聊天恢复任务。

### 第三次决策复核 · 2026-11-02
本轮诊断按预登记停止，可结项。接受夹具确定性对照；56 条真实执行完整，batch8 全自然终局 0 次，在线恢复未验。采用夹具已验的确定性设置作为下一版上层学习器配置，接入后须核对正常入口实际设置、同输入输出与成本。当前不放行 7h。若以尽早取得在线更新为优先，可提请用户单独批准一次允许中断后以不完整结果结项的连续有界试训，保持原科学协议；恢复能力仍须独立验收。否则维持既定恢复门。此处未授权运行或扩展恢复机制。[来源](../../SOURCES.md#src-t10-020)

## 2026-11-02 · 用户批准唯一连续在线试训（active）

本轮授权取代此前“当前不放行”的启动限制，只批一次连续1200真实/200更新/7h且允许故障不完整结项；不恢复/重启，不配对/正式长训/task11。[SRC-T10-021](../../SOURCES.md#src-t10-021)。推荐GPT6.1sol/high、Sonnet5.5/high，因deadline/有效GPU梯度跨模块；父实际模型/强度未知，10.11/12实际sol/high，独立10.13 terra/high。所有人共享预算，父唯一启动并持续监控。

入口代码b5b60ee：显式online-trial25200与默认smoke1800、同原epoch两层timeout及ledger/合同硬截止，20s清理在hard内；确定性CUBLAS pre-Python/cuDNN/算法True、TF32/benchmarkFalse、threads2；CPU203passed/3条件skipped/47.09s，正常入口GPU旧fixture5更新/0真实、两组严格同输入与取证verified_cuda、rc0/14.641s。独立审核缺口已修复，原始RED和完整原件保留。[SRC-T10-022](../../SOURCES.md#src-t10-022)。

唯一试训run-id `t10-online-20261102-s101`，从空回放初始化，B3-5M4718、上层101/batch8/train和1000真实均匀预热/既定科学合同不变，连续采集不等全8终局。开始北京时间19:29:28，硬截止2026-11-03 02:29:28；GPU1，container workerPID554、父3815493。actual contract runtime flags与25200/1200/200及outer deadline已核对，源码/配置冻结；运行中，当前不预宣称预热完成或真实GPU更新。原件根、实际命令、监控与停止方法见[父日志](../../agent_logs/task10/20261102-codex-online-trial.md)与[SRC-T10-023](../../SOURCES.md#src-t10-023)。结束后统一只读复算/报告，不拿旧16/56条及预检5更新混计。
