# task8.9.1 — 执行流程

状态：**review（r3优化O1–O4与池发布独立PASS；C首次初始化采样deadline失败、0动作，P5 blocked，3M/48h无法判定）**。当前事实见文末P5最终交接，全部历史失败/费用保留。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；当前不再拆分。若确需拆分（例如阶段B优化实施获批后另立），子目录继承`task8.9.1.N`并先建三文档、登记顺序/依赖/负责人/模型强度/验收关系；编号稳定不复用。

## 输入与文件归属

- run-id `t8-perf-<YYYYMMDD>`；产物`forem/results/task8/<run-id>/`，账本`forem/logs/task8/<run-id>/budget.json`，日志`forem/doc/agent_logs/task8/task8.9/task8.9.1/`。
- 新写：`forem/scripts/task8_profile_lower.py`（干跑训练循环与分项计时）、必要的只读profile辅助模块（放`forem/src/task8_sim/profile_*.py`，不改现有生产文件）。
- 只读：`forem/src/task8_sim/`生产代码、`forem/src/task7_lower/`（复用Timings、observation、replay、actor推理；不构造optimizer）、v5冻结actor `forem/results/task7/t7.18-v5-20261022/formal-v5-sync/checkpoint-0500000.actor.pt`（仅推理）。
- 地图：v3语义池`forem/results/task8/t8-exec-20261026/semantic-pool/`（以v3后端加载）；立方体PCD由task8.1夹具按固定种子生成≤64张作扩展性样本（不构建正式池，正式池属8.9.2）。

## 步骤

1. 开工：读根AGENTS、forem/ENV.md、PROGRESS、本节点与父三文档；核容器/GPU；登记PROGRESS与日志；建账本。
2. 设计干跑循环：复制`training.py`主循环结构（候选选择→观测→推理→环境step→replay push/sample），将`sac.update_from_batch`替换为计时空操作，**不创建optimizer**；加运行时断言确认无`torch.optim`对象。记录与原循环的差异清单。
3. 分项计时：沿用`Timings`（含cuda synchronize），另加scene构建、PcdPanorama、碰撞、DLS/IK、Grid、候选、观测细分；记录设备/显存/线程。
4. 扩展性：batch 1/16/64/256，各warmup后≥20 step；256分两种场景分配：24语义图轮转复用与64立方体图轮转。
5. scene缓存可行性：测单scene显存与构建时间；估算24与N张scene常驻GPU的显存。
6. 热点与方案：按占比排序，写优化方案（跨场景合并BVH批量查询、scene缓存、reset并行等），给等价判据与预计收益；不改生产代码。
7. 成本模型：环境每转移成本×转移数＋SAC更新（引用task7.18.3实测，按UTD折算）＋验证/检查点；给3M转移单run墙钟（UTD 1/0.1）。
8. 本次固定命令由实施者 Codex gpt-6.1-sol / high 自行执行（父明确派发，不另派 Luna）；不同 Sol high 独立验收 P1–P6，父收尾。

## 异常处理

GPU被占用则等待或只做CPU部分并记录；预算不足停止报告；发现生产代码bug只记录、不修；任何需要改语义或训练的情况停下报告。

## 派发

2026-10-27 父 Codex 按 SRC-1160 派发 /root/perf（gpt-6.1-sol / high）。本实施者不修改共享 PROGRESS/SOURCES/父文档，不再派 Agent；父另派不同 Sol high 独立验收。

## 本次可复核命令与测量口径

- `python3 forem/src/task8_sim/profile_budget.py --ledger forem/logs/task8/t8-perf-20261027/budget.json --name <job> --limit 295 -- sg docker -c 'docker exec -e CUDA_VISIBLE_DEVICES=0 -e PYTHONPATH=/root/mm_husky_ws/src forem-dev timeout --signal=TERM --kill-after=3 292 python3 -u /root/mm_husky_ws/scripts/task8_profile_lower.py <prepare|run> --family <cube|semantic> --root /root/mm_husky_ws/results/task8/t8-perf-20261027 [--batch N]'`。内层脚本 alarm 288s，分层 timeout，超时保留 JSON partial。
- 准备：按 task8.1 `fixture_specs`/`_sample` 生成 64 个有限随机立方体夹具（seed20261027..20261090），不调用 mapgen；24 语义图来自旧 PCD 池但使用当前 v3 VoxelScene。每图真实 sample 一条带 witness 的 episode，单独保存。
- 执行：各图预采样 episode 经 factory 按环境行轮转；reset 验证、Core、候选、观测、随机冻结 actor、逐转移 replay push/sample 全走原实现。重复场景的初态也重复，因此仅是有限轮转性能负载，不等于完整随机训练分布。
- 差异：只构造 Actor(74)，不构造 LowerSAC；Optimizer.__init__/backward 运行时禁止；原 SAC update 替换为空计时；replay 容量1024而非100000（核函数不变，正式显存另外按张量字节推导）；不执行完整正式 checkpoint/验证（成本保留符号项）。
- 计时：warmup2 后目标20 step，CUDA synchronize 与 events；嵌套分项不可直接相加。总循环 wall 包括逐转移消费与审计写盘。冷 reset 单列；GPU events 含 Python/CPU 控制带来的流空闲，不冒充纯GPU运算时间。
- 推荐 GPT6.1sol / high、Claude Sonnet5.5 / high，跨CPU/GPU归因需较高推理；实际本实施者 gpt-6.1-sol / high。

## r2续接（2026-10-27）

按 [SRC-1161](../../../../SOURCES.md#src-1161)、[SRC-1162](../../../../SOURCES.md#src-1162) 恢复本节点profile，保留上文r1停止快照与费用。负责人 Codex `/root/perf_r2`，父指定 gpt-6.1-sol / high；推荐 GPT6.1sol / high、Claude Sonnet5.5 / high，跨CPU/GPU与成本归因需要较高推理。累计账本继续81.76879678107798/1800s，不重复prepare；固定批量任务交Terra low，由不同Sol high独立验收。新来源 [SRC-1163](../../../../SOURCES.md#src-1163) 由父统一登记，当前仍尚未执行r2命令。固定清单 `forem/results/task8/t8-perf-20261027/r2-fixed-jobs.json`，新日志 `forem/doc/agent_logs/task8/task8.9/task8.9.1/20261027-sol-r2-profile.md`。

## r2交付现状与后续验收

本节点固定profile执行结束，累计1597.584848462604/1800s、active=null；cube1/16/64与cube256、semantic256各累计20完整post-warmup步，256独立窗口重复同输入，原超时保留。只做profile测量修复与方案，不实施生产优化。旧低batch部分嵌套分项混cold reset，严格P2仍partial；正式随机reset/196episode评估/100k保存未测，P5整体NOT_READY。来源 [SRC-1163](../../../../SOURCES.md#src-1163)，详情 [RESULTS](RESULTS.md) 文末及其summary链接。当前不再GPU测量、不补正式池子集，不重跑旧清单；余预算留父安排不同Sol high独立必要复核。模型推荐Codex GPT6.1sol/Claude Sonnet5.5，归因/独立审查high、固定执行Terra low；实际角色登记见RESULTS与独立日志。

## 子任务（2026-10-27追加）

|子任务|三文档|依赖|负责人（推荐）|父验收关系|
|---|---|---|---|---|
|task8.9.1.1 跨场景批量射线|[TASK](task8.9.1.1/TASK.md) / [PROCEDURE](task8.9.1.1/PROCEDURE.md) / [RESULTS](task8.9.1.1/RESULTS.md)|r2 profile|Codex：Sol high实现、terra low固定执行、独立Sol high验收|逐元素等价且重测吞吐后，其结果并入本节点P3–P5|

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
|task8.9.1.2 初始采样诊断与等价缓存|[TASK](task8.9.1.2/TASK.md) / [PROCEDURE](task8.9.1.2/PROCEDURE.md) / [RESULTS](task8.9.1.2/RESULTS.md)|r3 smoke失败|Codex：Sol high诊断/实现、terra low全量缓存与校验、独立Sol high验收|初始化与reset成本并入本节点P5，smoke前置|
