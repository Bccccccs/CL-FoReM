# task8.9.1 — 批量性能核查（task8 v3环境×下层训练路径）

**2026-10-27 已作废（closed）**：用户指令“现在的8.9作废吧，要优化好了整体的地图再开始训练”（[SRC-1220](../../../../SOURCES.md#src-1220)）。本节点不再执行；以下为作废前的历史状态与记录，原样保留。

状态：**review（r3优化O1–O4与池发布独立PASS；C首次初始化采样deadline失败、0动作，P5 blocked，3M/48h无法判定）**。当前事实见文末P5最终交接，全部历史失败/费用保留。

## 目标

在**不训练**的前提下，实测下层训练路径在task8（pcd-voxel-v3＋ghost-v1）上、256个并行环境且场景各不相同时的端到端成本，找出热点，给出有依据的优化方案和训练成本模型，供task8.9.3定规模与工期。

## 已知事实（输入）

- task7下层训练：256环境，每转移1次SAC更新（`forem/src/task7_lower/training.py` L183–296）；v5正式长训约48.7转移/s（3.16M转移约62.4ks）。task7.18.3分项中`sac_update`累计约24.5–28.0s、`environment_step`约6.9–7.6s、`reset`约45–49s（同一E2E窗口，[task7.18.3 RESULTS](../../../task7/task7.18/task7.18.3/RESULTS.md) L60–75）。
- task8：v1时Core单步（含IK/碰撞/扫描）batch1/2约0.694/0.716s，仅n1；语义图每次采样p50约2.16s，其中重建scene约1.04s、初态0.76s、witness0.30s（`forem/results/task8/t8-exec-20261026/acceptance-r2/performance.json`）。
- `SceneBatch.raycast/collide`对每个环境行单独循环（`forem/src/task8_sim/scene.py` SceneBatch），BVH遍历为Python while循环；256环境下可能线性放大。
- 训练入口尚未接入task8环境；本节点用“无更新的干跑训练循环”测量。

## 范围

**包括**：①scene构建/上传成本与显存（24语义图、抽样立方体PCD图）及scene缓存可行性；②episode采样/reset分项（scene、初态、路线、witness）；③Core step分项（DLS/IK、碰撞、PcdPanorama射线、Grid更新、观测、候选生成）；④冻结actor推理、replay push/sample；⑤batch=1/16/64/256的扩展性；⑥实际tensor/进程设备、GPU利用率与显存、CPU线程；⑦热点排序与优化方案（跨场景批量射线/碰撞、scene缓存等），每项给预计收益与精确等价要求；⑧训练成本模型（每百万转移墙钟，按UTD=1与0.1，含验证/检查点开销）。

**不包括**：任何optimizer step或SAC更新（含单测），`task7_lower`测试；SAC更新耗时只引用task7实测；修改生产代码实现优化（阶段B，需用户批准后另派）；改动环境语义、物理步长、动作持续时间。

## 交付与验收

|门|内容|
|---|---|
|P1 设备|记录每项实际device/dtype、GPU编号与显存峰值；无CPU静默回退|
|P2 分项|每个batch规模、每个分项给n、p50/p95/max与总占比，warmup后≥20个step样本；区分sim时间与wall时间|
|P3 扩展性|batch 1/16/64/256的每转移墙钟曲线；指出线性放大的环节及证据|
|P4 热点与方案|热点排序；每个优化方案给依据（profile数字）、预计收益、实现位置、精确等价判据（固定输入下距离/碰撞/Transition逐元素相同，CPU64与GPU32）与风险；不实施|
|P5 成本模型|公式、输入来源、单位：每百万转移墙钟（UTD 1/0.1），含reset/验证/检查点；与task7的48.7转移/s对照|
|P6 合规|无optimizer/SAC更新（运行时断言或不构造optimizer）；账本内；独立Sol high验收|

## 预算与资源（工程选择，SRC-1102）

验证累计墙钟≤1800s，单命令≤300s；只用一块核实无compute进程的GPU串行；已运行`forem-dev`。

## 模型与强度（推荐）

|阶段|Codex|Claude备选|理由|
|---|---|---|---|
|父协调|gpt-6.1-sol / medium|Sonnet5.5 / medium|调度与账本|
|profile脚本与归因|gpt-6.1-sol / high|Sonnet5.5 / high|GPU/CPU路径归因、扩展性分析|
|固定命令执行|gpt-6-luna / low|Sonnet5.5 / low|判据固定|
|独立验收|gpt-6.1-sol / high（≠实施者）|Sonnet5.5 / high|终审|

## r2续接（2026-10-27）

按 [SRC-1161](../../../../SOURCES.md#src-1161)、[SRC-1162](../../../../SOURCES.md#src-1162) 恢复本节点profile，保留上文r1停止快照与费用。负责人 Codex `/root/perf_r2`，父指定 gpt-6.1-sol / high；推荐 GPT6.1sol / high、Claude Sonnet5.5 / high，跨CPU/GPU与成本归因需要较高推理。累计账本继续81.76879678107798/1800s，不重复prepare；固定批量任务交Terra low，由不同Sol high独立验收。新来源 [SRC-1163](../../../../SOURCES.md#src-1163) 由父统一登记，当前仍尚未执行r2命令。固定清单 `forem/results/task8/t8-perf-20261027/r2-fixed-jobs.json`，新日志 `forem/doc/agent_logs/task8/task8.9/task8.9.1/20261027-sol-r2-profile.md`。

## r2交付现状与后续验收

本节点固定profile执行结束，累计1597.584848462604/1800s、active=null；cube1/16/64与cube256、semantic256各累计20完整post-warmup步，256独立窗口重复同输入，原超时保留。只做profile测量修复与方案，不实施生产优化。旧低batch部分嵌套分项混cold reset，严格P2仍partial；正式随机reset/196episode评估/100k保存未测，P5整体NOT_READY。来源 [SRC-1163](../../../../SOURCES.md#src-1163)，详情 [RESULTS](RESULTS.md) 文末及其summary链接。当前不再GPU测量、不补正式池子集，不重跑旧清单；余预算留父安排不同Sol high独立必要复核。模型推荐Codex GPT6.1sol/Claude Sonnet5.5，归因/独立审查high、固定执行Terra low；实际角色登记见RESULTS与独立日志。

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

## P5 r3最终交接：真实CLI冷启动失败（2026-10-27）

C首失败停止：preflight PASS，B0-primary原账本ba918a165a rc1，CLI wall243.166660481s、C账本243.370039869s。初始env.reset→逐环境sampler.sample→episode.py:100（asset/scene/planner块后）check_sampling检出deadline，SamplingIncomplete；不是外timeout，原235/255/275s界限未改。interrupted.meta steps/action_calls/env_actions全0，无有效训练吞吐；0/失败wall不作为吞吐。B0恢复/B3/196评估未执行，成功summary与分项不存在，3M/48h无法判定。[SRC-1201](../../../../SOURCES.md#src-1201)

GPU1的243个1Hz样本memory.used峰值11306MiB，p50/p95=11192/11284MiB；仅全命令设备采样，非PyTorch allocated/reserved精确峰值或训练显存认证。interrupted.pt约513.6MB/actor约18.6MB是失败取证，未加载/恢复/单独计时，不算成功或满100k回放CP成本。无reset分项/接受数flush，不能从deadline检出位置断言某个阶段独占全部耗时，也不把0转移说成0已接受episode。[SRC-1201](../../../../SOURCES.md#src-1201)

[cost-r3.json](../../../../../results/task8/t8-perf-opt-20261027/cost-r3.json) / [cost-r3.md](../../../../../results/task8/t8-perf-opt-20261027/cost-r3.md)及完整1201草稿已交父。公式完整保留：743/75短窗与正式2999743/299975更新密度修正、12次合计196评估、13完整CP/3000诊断及随机reset/缓存/争用；本次无有效CLI分项，不代入旧SAC或缓存profile冒称smoke实测。满有效100k CP/restore与增量update成本仍未知、不填0；启动/退出残差不是精确恢复。

最小待决定事项仅为建议：是否授权保持原256环境与采样/几何/接受规则的一次有界初始化分项诊断及预算，然后依据实测决定初始化/训练/评估限额如何分段。本节点不实施、不新优化、不重试、不延限或缩规模、不启动3M。实际汇总负责人Sol/high，推荐GPT6.1sol/Sonnet5.5 high，因需跨初始采样/恢复/长期成本核查。[SRC-1201](../../../../SOURCES.md#src-1201)

C最终395.012048684061/3600s、active={}；opt最终473.152745853178/1500s、余1026.847254146822s、active=null。A本轮仅三次标准库快照合计0.119631129317s，无新增实际验证/加载/采样/训练；源失败和费用全部保留。P5 blocked等明确诊断/执行界限决定，父task8.9就绪报告汇总，本负责人结束交接。
