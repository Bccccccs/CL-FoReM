# task8.9.1 — 结果与交接

**2026-10-27 已作废（closed）**：用户指令“现在的8.9作废吧，要优化好了整体的地图再开始训练”（[SRC-1220](../../../../SOURCES.md#src-1220)）。本节点不再执行；以下为作废前的历史状态与记录，原样保留。

状态：**review（r3优化O1–O4与池发布独立PASS；C首次初始化采样deadline失败、0动作，P5 blocked，3M/48h无法判定）**。当前事实见文末P5最终交接，全部历史失败/费用保留。

## 目标、授权和负责人

本节点按 [SRC-1160](../../../../SOURCES.md#src-1160) 仅做冻结推理性能核查，不构造 optimizer、不执行 SAC update、不跑 task7_lower 测试、不改生产语义/几何/量程、不实施优化、不调用 mapgen、不恢复 task7。实施者 Codex `/root/perf`，实际平台 `gpt-6.1-sol / high`（父明确派发）；推荐 GPT6.1sol / high、Claude Sonnet5.5 / high，因 CPU/GPU 路径与预算归因需要较高推理；固定执行由本实施者完成，独立 Sol high 尚待父安排。

父于 2026-10-27 因 task8.9.2 正式地图导出的几何合同冲突，明确要求不再启动后续性能命令。此时两条 prepare 都已正常退出，**未启动任何 run/batch profile 命令**。本节点没有生产优化、训练或运行故障，不将父线冲突当作本节点采样失败。[SRC-1103](../../../../SOURCES.md#src-1103)

## 文件和原始证据

新增独立入口 [task8_profile_lower.py](../../../../../scripts/task8_profile_lower.py)，辅助 [profile_lower.py](../../../../../src/task8_sim/profile_lower.py)、[profile_budget.py](../../../../../src/task8_sim/profile_budget.py)；未编辑生产文件或 task7 文件。脚本运行分支尚未经执行验收，不能称可用于正式训练。

原始产物根目录为 `forem/results/task8/t8-perf-20261027/`：`cube-prepare.json`、`semantic-prepare.json`、`cube-pool/manifest.json`、`cube-episodes/*.pt`、`semantic-episodes/*.pt`、`semantic-prepare-gpu.csv`。便于复核的摘要 [partial-summary.json](../../../../../results/task8/t8-perf-20261027/partial-summary.json) 含输入统计、门状态与新文件 SHA256。账本 [budget.json](../../../../../logs/task8/t8-perf-20261027/budget.json)，完整命令及 stdout 分别在账本 `commands[]` 和同目录 `prepare-cube.log` / `prepare-semantic.log`。[SRC-1104](../../../../SOURCES.md#src-1104)、[SRC-1105](../../../../SOURCES.md#src-1105)、[SRC-1115](../../../../SOURCES.md#src-1115)、[SRC-1116](../../../../SOURCES.md#src-1116)

## 实际运行与预算

|命令/范围|脚本 wall|账本外层 wall|退出码|结果|
|---|---:|---:|---:|---|
|`prepare --family cube`，64图|42.8602s|43.4455s|0|64图各真实采样1条带 witness 的 episode|
|`prepare --family semantic`，24图|36.8684s|38.3233s|0|24图各真实采样1条带 witness 的 episode|

账本累计 **81.7687967811 / 1800s**，剩余 **1718.2312032189s**，`active=null`。每条运行脚本 alarm288s、容器内 timeout292s、外层 timeout295s，最大实际43.4455s；没有超时或残留本节点 profile 进程。已停止启动后续命令，不能未经决定直接续跑。[SRC-1115](../../../../SOURCES.md#src-1115)

初次只读 host 摘要脚本因宿主没有 numpy 产生 `ModuleNotFoundError`，未运行仿真/网络；随后改为标准库统计成功。三个新增 Python 文件 AST 均可解析；此前初版 py_compile 通过。没有跑 task7_lower 或任何 SAC 测试。上述静态检查不替代 run 分支实测。[SRC-1116](../../../../SOURCES.md#src-1116)

## 设备、场景与采样成本（只适用于准备阶段）

forem-dev 已运行、未重建；GPU物理0，torch2.7.1+cu128 / CUDA12.8，实际 scene 张量 `cuda:0 / float32`。`OMP_NUM_THREADS=2`、`OPENBLAS_NUM_THREADS=2`、PyTorch intra-op2、inter-op64，进程 CPU affinity0–63；docker NanoCpus0、cpu.max=`max 100000`，因此 nproc2 不能解释为两核硬限。actor/replay/Core 未执行，不能声明这些路径本轮已通过设备验收。[SRC-1103](../../../../SOURCES.md#src-1103)

|准备阶段指标|64立方体|24语义图|
|---|---:|---:|
|提案/接受|167 / 64|248 / 24|
|sample wall p50 / p95 / max|0.5779 / 0.6829 / 1.1682s|1.3918 / 1.8580 / 1.9993s|
|asset+scene累计 / p50 / p95|14.7662 / 0.2270 / 0.2718s|23.3086 / 0.9634 / 1.1338s|
|初态校验累计 / p50 / p95|3.5128 / 0.0309 / 0.1272s|3.3923 / 0.1092 / 0.3565s|
|规划累计 / p50 / p95|0.7362 / 0.0102 / 0.0188s|0.8225 / 0.0266 / 0.0698s|
|witness累计 / p50 / p95|18.6625 / 0.2914 / 0.2942s|7.1047 / 0.2950 / 0.3005s|
|scene CPU preprocess累计|8.2892s|5.0193s|
|scene device upload累计|0.0746s|0.0294s|
|scene几何张量合计|93,082,488B|35,263,368B|
|GPU峰值allocated / reserved|143,493,120 / 161,480,704B|84,624,896 / 115,343,360B|

立方体为 task8.1 `fixture_specs/_sample` 的64个有限随机夹具（seed20261027..20261090），并非正式 mapgen 训练分布，不能证明 task8.9.2 全池合格。语义 PCD 读取已有24图池，以当前 v3 VoxelScene 构建，保留原始 PCD。每图只接受1条 episode，上述 n=64/24 是“每次接受采样”的统计，不是 warmup 后 Core step 样本。asset+scene 含 PCD读取、体素处理、上传与 planner 创建；不能将差值全部称 CPU voxel 耗时。[SRC-1104](../../../../SOURCES.md#src-1104)、[SRC-1105](../../../../SOURCES.md#src-1105)

几何张量总计 **128,345,856B** 只支持有限88场景驻留的字节核算；不包含 planner CPU 数组、模型、replay、Grid 或正式10000图。未运行跨场景raycast，不能据此声称缓存已有端到端收益。[SRC-1111](../../../../SOURCES.md#src-1111)

语义准备阶段 GPU CSV 保存1s采样；立方体命令启动时监控代码尚未加入，只有中段宿主 nvidia-smi（本节点python PID1417662、804MiB）与PyTorch峰值。没有把CUDA events当纯GPU算子时间，其跨越Python/CPU控制导致的流空闲。[SRC-1118](../../../../SOURCES.md#src-1118)

## P1–P6 门和限制

|门|本次状态|未满足内容|
|---|---|---|
|P1 设备|partial|仅scene采样张量/准备进程已记录；actor/replay/Core未实测|
|P2 分项|NOT RUN|所有batch的Core step=0；无warmup后20步，未测IK/碰撞/扫描/Grid/候选/actor/replay端到端|
|P3 扩展性|NOT RUN|batch1/16/64/256吞吐均未测，256的24/64场景轮转未运行|
|P4 热点与优化|NOT ESTABLISHED|只有采样成本分项，不能给训练热点排序、数值收益或确认瓶颈|
|P5 成本模型|NOT ESTABLISHED|无task8环境每转移成本/验证/checkpoint数据，不能给3M工期或48h启动门结论|
|P6 合规|partial / 独立复核待办|两条prepare guard均 optimizer_constructed=0、backward_calls=0，预算内；不同Sol独立验收尚未执行|

以上不足证据分别见 [SRC-1106](../../../../SOURCES.md#src-1106)–[SRC-1110](../../../../SOURCES.md#src-1110)、[SRC-1112](../../../../SOURCES.md#src-1112)–[SRC-1114](../../../../SOURCES.md#src-1114)、[SRC-1117](../../../../SOURCES.md#src-1117)、[SRC-1119](../../../../SOURCES.md#src-1119)。**本节点整体不通过，不支持启动正式长训。**

## 成本公式与方案边界（待补测，不能代入得出工期）

成本结构仅可写为 `T(N,U)=T_cold + N*c_transition + R(N)*c_reset + U*N*c_SAC + K(N)*(c_checkpoint+c_validation100+c_transfer96)`，单位秒；N为转移数，U为每转移更新次数（1或0.1），R/K为实测复位次数/协议评估检查点次数。`c_transition` 须包含真实环境、候选、观测、推理、逐转移replay/审计；reset是否含scene冷构建须分开。task8的这些量本次均待测，因此每百万转移与3M工期、UTD1与0.1总耗时均不能给数值。[SRC-1114](../../../../SOURCES.md#src-1114)

旧 task7.18.3 的更新 p50约13.5205ms、2047次累计27.9898s、checkpoint10.1212s是旧输入/旧路径资料，正式v5约48.7转移/s也是旧训练端到端口径；两者均不能替代 task8 实测，更不能把采样成本直接当训练 step 成本。[task7.18.3 RESULTS](../../../task7/task7.18/task7.18.3/RESULTS.md)、[SRC-1101](../../../../SOURCES.md#src-1101)、[SRC-1114](../../../../SOURCES.md#src-1114)

scene缓存、跨场景BVH批量射线/碰撞、reset并行仍是待profile后评估的候选方案，**本次不实施、不承诺收益**。若未来授权，等价门须对固定输入检查CPU64与GPU32各自优化前后的距离、碰撞、Transition逐元素相同，并保留动作/奖励/终止/量程/几何不变。当前没有足够step证据决定实施位置与预期收益。[SRC-1113](../../../../SOURCES.md#src-1113)

## 交接与下一步

已完成：独立profile入口与预算runner初版、64+24图有界准备、原始证据及未满足门记录。无本节点后台运行、无提交/推送/合并。所有来源草稿在 `forem/results/task8/t8-perf-20261027/sources-draft.md` 供父统一入账；共享SOURCES/PROGRESS/父文档未由本实施者改动。

剩余：父先汇报 task8.9.2 几何合同冲突，由用户决定后续；不同Sol可仅审查当前代码/原始快照。**未经恢复决定，不补跑性能、不实施优化、不启动smoke或长训。** 后续执行需先核查旧账本、保留81.7688s累计费用；run分支尚未实测，不得把此交接当完整脚本验收。

## 父汇总补记

不同Sol high已只读核查本节点保存原件/预算/入口存在性，确认部分成果与未完成项；没有新运行本节点测试/性能，**不是本节点全项独立验收通过**。地图严格内部缺格已独立成立，详[SRC-1125](../../../../SOURCES.md#src-1125)与[独立报告](../../../../../results/task8/t8-phase2-20261027/independent-review.md)。当前继续保持blocked、无smoke/长训，等待用户采样规则决定。

## r2续接（2026-10-27）

按 [SRC-1161](../../../../SOURCES.md#src-1161)、[SRC-1162](../../../../SOURCES.md#src-1162) 恢复本节点profile，保留上文r1停止快照与费用。负责人 Codex `/root/perf_r2`，父指定 gpt-6.1-sol / high；推荐 GPT6.1sol / high、Claude Sonnet5.5 / high，跨CPU/GPU与成本归因需要较高推理。累计账本继续81.76879678107798/1800s，不重复prepare；固定批量任务交Terra low，由不同Sol high独立验收。新来源 [SRC-1163](../../../../SOURCES.md#src-1163) 由父统一登记，当前仍尚未执行r2命令。固定清单 `forem/results/task8/t8-perf-20261027/r2-fixed-jobs.json`，新日志 `forem/doc/agent_logs/task8/task8.9/task8.9.1/20261027-sol-r2-profile.md`。

## r2最终原件复核与交接（2026-10-27）

本节覆盖r1“未执行run”的现行状态，原快照不删除。依据 [SRC-1163](../../../../SOURCES.md#src-1163)（父统一登记），详细原始输入/hash、每项n/p50/p95/max/占比、设备/监控及公式均在 [summary-r2.json](../../../../../results/task8/t8-perf-20261027/summary-r2.json) 和 [summary-r2.md](../../../../../results/task8/t8-perf-20261027/summary-r2.md)。实施Codex `/root/perf_r2`，父指定gpt-6.1-sol/high；固定执行Terra实际gpt-6.1-terra/low（执行日志/JSON）；不同Sol/high独立验收尚待父安排。推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high，因CPU/GPU计时及工期推导需跨模块归因；固定命令推荐Terra low，符合SRC-1162。

|负载|完整测量步|场景去重|有效转移/测量秒|转移/秒|step p50/p95/max(s)|
|---|---:|---:|---|---:|---|
|cube b1|20|1|20/3.874637|5.161773|0.1933/0.2073/0.2201|
|cube b16|20|16|320/21.987115|14.553979|0.9920/2.0351/2.1083|
|cube b64|20|64|1280/72.333709|17.695761|3.5603/3.6811/4.6817|
|cube b256|10+10|64|5120/284.660929|17.986311|14.0765/15.1834/15.2960|
|semantic b256|8+6+6|24|5119/467.506324|10.949585|23.1490/25.1530/25.2197|

每窗均独立warmup2。256窗口是同缓存与seed重启的重复轨迹，不是连续20步或20独立episode；更不是256不同地图。cube原20目标命令rc124/17步保留、不合并其受污染分项；semantic原目标10窗口rc124/8完整步，经raw/step/transfer/wall一致与rollback核验后只合并完整8步，再补6+6。所有原超时、stdout、窗口执行模型与前后hash证据保留，未把整个超时命令改为通过。新窗口修复只作用profile工具：独立窗口命名、cold_timings隔离、测量前清空、原始样本保存、不完整step回滚；没有生产优化。

设备：GPU物理0、forem-dev，torch2.7.1+cu128/CUDA12.8，冻结actor/Core state/scene/replay均CUDA float32；全部guard optimizer_constructed=0、backward_calls=0。cube256峰值allocated/reserved4,041,034,240/5,083,496,448B，semantic2565,425,108,992/6,956,253,184B。正式100k replay仅张量推导9,891,600,000B，当前profile容量1024，未包含真实SAC/optimizer/target/正式地图池，不能验收4卡显存。监控CSV1Hz为全命令范围，不把GPU利用率解释为已证明的性能成因。[SRC-1163](../../../../SOURCES.md#src-1163)

按顶层耗时environment_step分别占96.57%/98.35%，其中raycast占测量loop91.69%/94.67%；collision3.00%/2.40%、IK solve2.22%/.91%、replay消费1.69%/1.03%，嵌套不能相加。SceneBatch逐环境循环与每scene分块BVH是代码定位，有限cube的每行扫描成本随batch近线性。优化仅给跨场景raycast、scene缓存、次级collision/reset和replay方案、位置、等价判据及风险；没有实现或声称收益。Amdahl仅条件敏感性：假设raycast2×/4×，cube全局1.847×/3.202×、semantic1.899×/3.449×，非预计已达收益。详情和逐元素等价要求见summary-r2.md。[SRC-1163](../../../../SOURCES.md#src-1163)

成本秒公式：`T=T_cold+N*c_profile+U*max(0,N-257)*c_SAC_old+R*c_random_reset+Kcp*c_checkpoint+Kv*c_validation100+Kt*c_transfer96+T_logging+T_contention`。c_profile为上述完整loop/有效转移，旧c_SAC=27.9898/2047s/update，引用task7.18.3而非本轮训练实测。UTD.1用比例近似、仍沿无更新profile中的逐转移replay；不能等同新B3真实成本。每百万基础cube UTD1/.1=19.241/15.824h，3M=57.725/47.471h；semantic只作迁移负载情景，每M29.166/25.749h、3M87.500/77.246h。窗口范围详JSON，是情景区间，不是置信区间或上界。随机reset频率/完整成本、正式196episode验证、100k全状态checkpoint、周期诊断与四训练worker争用未测，保留符号项、不取0。cube B0条件基础已>48h投影门；实际新B0/B3仍待C真实smoke，不能把旧SAC代入写成新运行测量。整体NOT_READY。[SRC-1163](../../../../SOURCES.md#src-1163)

|门|r2现行结论|
|---|---|
|P1|冻结actor/Core/scene/replay设备与监控已实测；正式训练显存未认证|
|P2|每要求负载累计20完整post-warmup步，但旧b1/16/64部分嵌套IK/collision/raycast/Grid分布混cold样本、无raw可追溯删除；严格partial；b1未触发replay_sample、随机ended reset未测|
|P3|有限64/24场景轮转扩展性已测；不支持256独立地图/完整随机训练分布的外推|
|P4|热点/代码位置/只出方案与条件收益情景已交付，未实施优化或证明收益|
|P5|条件模型与未知周期符号项已给；完整工期与≤48h未成立|
|P6|guard零、所有单命令<300s、累计预算内；两超时保留；不同Sol独立验收待办|

账本最终1597.584848462604/1800s、余202.415151537396s、active=null；单命令最大289.722394312732s。仅剩预算留父独立必要审查，不再新GPUprofile，不补正式cube-export-v2子集。共享SOURCES/PROGRESS/父文档未由本实施者编辑。无本节点后台任务、无提交/推送/合并。命令原件：r2-fixed-jobs.json、r2-window-jobs.json、r2-final-window-jobs.json及budget.commands；历史清单含已停项目，不能直接全量重跑。

必要验证：CPU标准库汇总脚本`python3 forem/scripts/task8_profile_summarize.py`最终rc0，核每窗口20合并数、原transfer/wall和、raw分项、ledger/guard及hash；首次精确比较numpy与stdlib分位数末位失败已记录，改为仅重算一致检查rel/abs1e-12（不是放宽实验数值等价门）。profile入口/辅助/汇总AST可解析；未执行任何新增GPU测试或SAC操作。

交接：父先登记 [sources-r2-draft.md](../../../../../results/task8/t8-perf-20261027/sources-r2-draft.md) 为SRC-1163，再派与实施者不同Sol/high只读/必要有界复核；待C/B全门与真实smoke后更新就绪报告。不擅自以本条件成本替代真实smoke，不因48h投影门失败自行优化、缩训练或延预算。

## r3优化完成与P5后续（2026-10-27）

SRC1190授权的子节点[task8.9.1.1](task8.9.1.1/TASK.md)现O1–O4不同Sol独立PASS，详情[RESULTS](task8.9.1.1/RESULTS.md)。实施/汇总实际gpt-6.1-sol/high，固定执行gpt-6.1-terra/low，终审不同Sol/high；推荐GPT6.1sol/Sonnet5.5 high作跨设备/状态/成本归因，固定Terra low。生产只改SceneBatch森林raycast（保留loop），其他优化未实施；测试可选输出路径只为保护历史证据。[SRC-1191](../../../../SOURCES.md#src-1191)、[SRC-1192](../../../../SOURCES.md#src-1192)、[SRC-1193](../../../../SOURCES.md#src-1193)、[SRC-1194](../../../../SOURCES.md#src-1194)

|负载|r3转移/s|相对R2完整窗口比|
|---|---:|---:|
|cube64|109.542321|6.190×|
|cube256|145.353020|8.081×|
|semantic64|94.622670|无旧基准|
|semantic256|116.288947|10.620×|

各warmup2+20完整连续步、guard0。R2的256是重复10+10/8+6+6前缀，R3连续20步且语义发生4次cached ended-reset；全窗口比不能当20步严格配对。公共前缀元数据一致，旧长度加权比cube64/2566.190×/7.518×、semantic25611.867×，无新增独立测量。cube/semantic256 raycast占loop38.45%/34.36%，其他分项/显存/CSV与全部raw核对在[summary-r3.json](../../../../../results/task8/t8-perf-opt-20261027/summary-r3.json) / [summary-r3.md](../../../../../results/task8/t8-perf-opt-20261027/summary-r3.md)。峰值仅冻结actor+replay1024，不能当正式训练显存。[SRC-1194](../../../../SOURCES.md#src-1194)

P1/P3/P4对本轮固定负载有更新证据；P2新增b64/256的完整raw分布已齐，旧b1/16冷污染历史不抹除、不据此阻止SRC1190允许的smoke。P6优化子节点独立PASS。**P5仍未通过**，但依SRC1190不再是smoke前置；smoke另需父确认正式池发布及独立PASS，不由本节点自行启动。

P5必须从C真实CLI取更新数、有效转移、训练/保存/评估/恢复与外层wall，不能套旧SAC当新测量。old replay门得 `U_k(N)=max(0,floor(N/k)-floor(257/k))`，B0/B3的1000更新743/75，3M更新2,999,743/299,975；smoke更新密度较低，稳态修正含 `(rho_formal-rho_smoke)*c_update`。CLI consume_transition混合push/sample/update，不能据其单独识别增量c_update；缺项留符号。评估只有完整196合并wall，正式3M有12周期评估、12周期完整CP+1finalCP、3000诊断；恢复J及随机reset/分布/缓存/争用单列。[SRC-1194](../../../../SOURCES.md#src-1194)

smoke512/1000 CP只持久化有效[:size]，不是100k满回放；9,892,500,000B是正式100k有效行回放payload推导，满CP/restore时延未测，不能填0/伪装已验收。完整成本公式/单位/条件与未知项在summary.cost_framework。待C smoke后由父followup本负责人更新，不在本轮补测试/训练/其他优化，也不据新profile直接宣称≤48h或启动3M。

本优化账本最新473.033114723861/1500s，余1026.966885276139s，active=null；全部后续额外成本继续同账本，旧A1800s账本历史保留。来源1194完整草稿已交父统一登记，summary标准库复算仅为报告，不是新profile/测试。

## P5 r3实际smoke成本接入准备（进行中）

父已明确优化O1–O4与B10300/200发布独立PASS，C固定8job于GPU1按原3600s账本释放；P5不再作smoke前置。A负责人 `/root/opt_r3` 实际父指定gpt-6.1-sol/high，推荐GPT6.1sol/Sonnet5.5 high作成本/恢复因果核查，仅普通标准库汇总，不加载tensor/checkpoint、不启动GPU/optimizer/测试、不修改C实现或重试。[SRC-1201](../../../../SOURCES.md#src-1201)由父统一登记。

已准备 `forem/scripts/task8_cost_summarize_r3.py`，读取实际CLI wrapper wall、summary.timings、learning、196 validation、CSV与checkpoint stat/meta，输出[cost-r3.json](../../../../../results/task8/t8-perf-opt-20261027/cost-r3.json) / [cost-r3.md](../../../../../results/task8/t8-perf-opt-20261027/cost-r3.md)。初次快照仅preflight通过/B0-primary执行中、B3未运行，所有成本null；不出P5/48h通过结论。

公式保留743/75短窗到2999743/299975正式更新密度修正；100+96只合计196 wall，正式13完整CP与满100k有效回放/恢复成本未知；启动退出残差明确不是精确restore。任何新实际验证先交父决定，普通标准库快照用opt统一runner计时，避免并发写账本。候选四run仍原r3 commands，禁止本汇总启动3M。[SRC-1201](../../../../SOURCES.md#src-1201)

## P5 r3最终交接：真实CLI冷启动失败（2026-10-27）

C首失败停止：preflight PASS，B0-primary原账本ba918a165a rc1，CLI wall243.166660481s、C账本243.370039869s。初始env.reset→逐环境sampler.sample→episode.py:100（asset/scene/planner块后）check_sampling检出deadline，SamplingIncomplete；不是外timeout，原235/255/275s界限未改。interrupted.meta steps/action_calls/env_actions全0，无有效训练吞吐；0/失败wall不作为吞吐。B0恢复/B3/196评估未执行，成功summary与分项不存在，3M/48h无法判定。[SRC-1201](../../../../SOURCES.md#src-1201)

GPU1的243个1Hz样本memory.used峰值11306MiB，p50/p95=11192/11284MiB；仅全命令设备采样，非PyTorch allocated/reserved精确峰值或训练显存认证。interrupted.pt约513.6MB/actor约18.6MB是失败取证，未加载/恢复/单独计时，不算成功或满100k回放CP成本。无reset分项/接受数flush，不能从deadline检出位置断言某个阶段独占全部耗时，也不把0转移说成0已接受episode。[SRC-1201](../../../../SOURCES.md#src-1201)

[cost-r3.json](../../../../../results/task8/t8-perf-opt-20261027/cost-r3.json) / [cost-r3.md](../../../../../results/task8/t8-perf-opt-20261027/cost-r3.md)及完整1201草稿已交父。公式完整保留：743/75短窗与正式2999743/299975更新密度修正、12次合计196评估、13完整CP/3000诊断及随机reset/缓存/争用；本次无有效CLI分项，不代入旧SAC或缓存profile冒称smoke实测。满有效100k CP/restore与增量update成本仍未知、不填0；启动/退出残差不是精确恢复。

最小待决定事项仅为建议：是否授权保持原256环境与采样/几何/接受规则的一次有界初始化分项诊断及预算，然后依据实测决定初始化/训练/评估限额如何分段。本节点不实施、不新优化、不重试、不延限或缩规模、不启动3M。实际汇总负责人Sol/high，推荐GPT6.1sol/Sonnet5.5 high，因需跨初始采样/恢复/长期成本核查。[SRC-1201](../../../../SOURCES.md#src-1201)

C最终395.012048684061/3600s、active={}；opt最终473.152745853178/1500s、余1026.847254146822s、active=null。A本轮仅三次标准库快照合计0.119631129317s，无新增实际验证/加载/采样/训练；源失败和费用全部保留。P5 blocked等明确诊断/执行界限决定，父task8.9就绪报告汇总，本负责人结束交接。
