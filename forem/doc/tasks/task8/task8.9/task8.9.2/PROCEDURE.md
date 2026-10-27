# task8.9.2 — 执行流程

状态：**blocked（r2完成40个批次后安全停机，依赖A的P2/P5硬门决定；当前禁止新运行）**。旧流程/失败保留，现行补充见文末。目标/验收见[TASK](TASK.md)。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；当前不再拆分。阶段A/B为同一节点内串行阶段；若阶段B规模需要另立子任务，子目录继承`task8.9.2.N`并先建三文档、登记顺序/依赖/负责人/模型强度/验收关系；编号稳定不复用。

## 输入与文件归属

- run-id `t8-pool-<YYYYMMDD>`；产物`forem/results/task8/<run-id>/`，账本`forem/logs/task8/<run-id>/budget.json`，日志`forem/doc/agent_logs/task8/task8.9/task8.9.2/`。
- 新写：`forem/scripts/task8_pool_stats.py`（阶段A）、`forem/scripts/task8_build_pool.py`（阶段B）、配置`forem/config/task8/pool_<scheme>.json`（阶段B）。
- 只读：v3语义池、`forem/src/task8_sim/`生产代码、task7 mapgen_a池与配置、task8.8 r4表。

## 步骤

1. 开工：读根AGENTS、PROGRESS、父与本节点三文档；登记；建账本。
2. 阶段A：Sol写统计脚本与固定种子表→Luna执行→Sol复核原产物→写方案对比与推荐→独立Sol验收M1/M2→父汇总，**停在用户决定处**。
3. 阶段B（用户选定后另行派发）：构建manifest；S3时导出立方体PCD并抽样复核；独立验收M3/M4。

## 异常处理

某图采样接受率为0或统计异常：单列，不删图、不改采样规则；需改语义/重新生成地图时停下报告用户。

## 派发

尚未派发。用户同意后由Claude追加派发prompt并codex exec派发、后台监督。

## 阶段B实际执行与停止点（2026-10-27）

本次由父派Sol high直接实施（不再派子Agent）；推荐GPT6.1sol/Sonnet5.5 high核几何合同、low执行固定导出。文件独占task8_build_pool.py、pool_s3.json、本节点三文档/日志；生产scene、task7/mapgen只读。父维护全局文档。完整实际命令、返回码、预算见[RESULTS](RESULTS.md)。

1. 核实容器64 CPU affinity/cpuset、无quota；nproc受OMP_NUM_THREADS=2影响。4 worker各限制OMP/OpenBLAS/MKL为1，CPU运行，不分配GPU。
2. 读取原index 10300条，保留原ID/split/difficulty/seed/JSON字节hash和源生成器版本；每轴ceil(size/0.05)，局部中心(i+0.5)*size/count，按corner盒体旋转平移，不当作中心盒体；ASCII `%.12g`，读回PCD验证点数/有限数/半开域/精度。与task8.1 fixtures._sample公式等价。[SRC-1120](../../../../SOURCES.md#src-1120)、[SRC-1121](../../../../SOURCES.md#src-1121)。
3. 24图先导测速，父据13.1453图/s批准1800s总账（含先导和独立验收，不重置）。[SRC-1122](../../../../SOURCES.md#src-1122)。
4. 每split/difficulty各一图先导审查：原PCD严格读取→生产VoxelScene CPU float64→独立v3逐格核等→每盒5³与8角内部参照→四墙360×90方向不截量程DDA与0.05m深度门。6图全内部门失败；按父指令**停止，不运行全量、不补200样本、不改规则**。[SRC-1123](../../../../SOURCES.md#src-1123)。
5. 后续不同Sol high仅核保存证据与最小复算；若确认采样合同需要更改，由父报告用户，不能以此流程自动授权修改。M1/M2阶段A仍暂缓，M3失败，M4独立验收待执行。[SRC-1124](../../../../SOURCES.md#src-1124)。

全量发布路径仍预留`results/task8/t8-pool-20261027/cube-pool/manifest.json`，schema task8-pcd-v1；当前**不存在**。已有24个records和PCD只用于失败诊断。`evaluation-seeds.json`也未发布；源代码中的validation100×1、test200×1、semantic24×4表生成步骤尚未执行，不能供训练消费。

## r2执行覆盖（SRC-1161/1162）

正式新路径为`results/task8/t8-pool-20261027/cube-pool-v2/manifest.json`及同目录`evaluation-seeds.json`，旧cube-pool不变。配置`config/task8/pool_s3_v2.json`，导出器SHA256及固定命令清单见[r2日志](../../../../agent_logs/task8/task8.9/task8.9.2/20261027-sol-pool-r2.md)。推荐GPT6.1sol/high、Sonnet5.5/high作几何推理；固定导出Terra/low。实际实施Sol/high。

1. 每盒O=A∪B；A以world中心逆变换判断闭合OBB；B枚举包含fixture样本的闭合world格。浮点格面相等用16ε×max(1,|origin|,|sample|)米纠正计算表示，逐盒记录最大残差/使用余量；不采用生产τ。各盒独立O⊆自身闭合SAT supercover审查，SAT数值余量沿用1e-10m。
2. PCD写按zyx字典序排列的O中心、ASCII %.12g。**全图**使用严格生产_read_pcd读持久PCD，校验数量/有限/半开域/坐标；真实VoxelScene CPU float64构建后逐格=O，每盒非空；记录源字节hash/导出器hash/原split/difficulty/seed/cube-export-v2/v3。
3. 六图先导①–⑤通过才允许build；本轮已运行六图，独立审查待办。Terra先跑固定24图测速，注意6图已缓存，仅18图新导出，外推不得把24全当新图。父据新成本定总预算后，Terra再分块build（每次≤100图，逐命令超时≤300s，剩余不足先停）；原账本持续追加。
4. 全量后抽样200（train每难度70、validation每难度15、test每难度15；字典序等距含端点）做①–⑤，保留逐盒与射线原件；全量①④⑥此前已执行。finalize再核所有原hash，满足200门后发布manifest与种子表。验收失败立即停止并保留，不发布。
5. 评估表schema task8-eval-seeds-v1：validation100×1、test200×1、semantic_transfer24×4；seed为sha256(run-id+":"+map_id+":"+j)前8个hex转整数，每job stream_index=0，episode_index=j；训练/验证/测试原split严格保留，semantic只迁移不选模。不同Sol/high验收后才交训练消费。


r2二次交接：24 profile及独立六图已通过，父按新增18图实测批准累计5400s，原账本继续。固定105job清单`config/task8/pool_s3_v2_batch.json`，详RESULTS与r2日志；103×build100→audit200→finalize严格顺序，余量阈值700/660/420s，失败即停保留。推荐Terra/low固定执行，Sol或Sonnet5.5/high独立验收；5400是工程预算，未增加科学规模。当前全量尚未执行。


## r2安全停止与恢复覆盖（2026-10-27）

父因A的P2/P5硬门partial要求停止所有后续新任务，B Terra未中断offset3900当前块；该块rc0/账本active空后退出wrapper2554024及exporter2554333，未启动offset4000。执行表`fixed-full-r2.json`状态blocked、40个job、next_job_index40；原日志40份均已由Sol纯读核对。当前4013有效记录只代表部分池，audit200/finalize未跑、正式manifest/seed表不存在，不供训练消费。[SRC-1130](../../../../SOURCES.md#src-1130)。

停止后获父明确授权仅≤110s纯读：全4013文件hash/实际PCD行数header/元数据身份及边界/生产标志、固定12新图逐点实际有限边界；Sol已一次完成16.873170921579s，未调用target/scene/SAT/DDA/测试/导出，原账本累计1128.2773682428524/5400s、余4271.722631757148s、active=null。该范围不能写成4013重新逐点复验或全池几何通过。

恢复必须先读本节点三文档/r2 Sol/Terra日志、fixed-full-r2.json、预算原件与固定plan，再确认A门决定与父恢复授权、无写进程/active空、冻结hash一致；从plan job40（build offset4000 count100）顺序继续，先重核余量门，不重复前40块已有效资产。原wrapper退出且未自动跳过已完成job，接收方只能在固定plan上明确选择job40起执行，不直接运行旧wrapper而误从job0开始。遇不完整asset/hash冲突先报告，不删除或自动修复。预计仍有6287张未导出，全部门仍按原10300/200口径，不能降低规模或以部分验收代替。

模型推荐：Sol/Sonnet5.5 high用于依赖与验收判断、Terra low固定续执行；本次原件收尾实际Codex gpt-6.1-sol/high。无本节点残留执行进程，无smoke/长训。

2026-10-27 r3交接：保留原执行表后审失败，不重跑finalize或删除原件；不同Sol须对实际final-report、manifest、evaluation-seeds及全量身份和audit独立验收，消费前置以其结果为准。实际执行Terra low，建议验收Codex GPT6.1sol / high、Claude Sonnet5.5 / high（核多处来源及发布合同）。见[RESULTS](RESULTS.md)。


## r3父验收覆盖（阶段B done）

阶段B全10300图、200图①–⑤审查、manifest与evaluation-seeds已发布并经不同Sol独立验收PASS；阶段A继续暂缓，不将阶段B完成当作阶段A统计完成。[执行SRC-1195](../../../../SOURCES.md#src-1195)、[独立SRC-1198](../../../../SOURCES.md#src-1198)。原包装器finalize-report.json误读导致stopped保留；生产finalize rc0真实final-report通过，独立核验后消费门通过，未重复发布。B账本3132.918237945065/5400s、active空。

独立审查全部10300真实PCD字节hash/header/实际行数/源侧车身份及保存边界证据；额外12图实际逐点边界、200保存几何审查逐门及100验证+200测试+96迁移种子复算通过；不是全量重做逐点/几何射线。证据见[独立报告](../../../../../results/task8/t8-phase2-20261027/r3-independent-pool-final.md)。实际固定Terra/low、独立Sol/high，推荐GPT6.1sol/Sonnet5.5 high验收（几何、身份与协议核查），普通固定步骤Terra low。后续不再导出或改池。
