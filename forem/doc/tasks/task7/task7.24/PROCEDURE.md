# task7.24 — 短程任务小试流程草案

**2026-10-26执行冻结：paused。** 用户已冻结task7全部后续执行，见[父冻结入口](../TASK.md#2026-10-26-当前冻结入口)。已完成成果与下文历史状态保留；不得依旧授权自动续训、恢复或派发。当前转入task8地图迁移规划。

> 执行者先读[TASK](TASK.md)与根AGENTS。用户已于2026-10-23确认并要求子Agent执行，使用subagent-driven-development；若用户要求并行委派，先建立相应子任务三文档再派发。当前实施开始登记，只有实际命令/结果才可标执行。

**目标**：仅通过缩短完整末端路线任务，检查下层局部控制的初步学习表现和成本。  
**结构**：现有EpisodeSampler增加可关闭的路线长度筛选；独立试验入口/协议驱动A/B；共享Core/SAC/候选与v5规则沿用。  
**技术**：现有forem-dev、Python/PyTorch和task7_sim/task7_lower，无新依赖。  
**规格**：[TASK](TASK.md)，全部预算/长度现按SRC-0971确认执行。

## 递归规则与执行关系

每层恰有TASK/PROCEDURE/RESULTS；新子任务需先建三文档、登记负责人/模型/输入/验收。由父Codex协调：task7.24.1实现/预检准备→task7.24.2监督审查→task7.24.3有界预检与A/B/判读；全部计算共用4h预算。各阶段验收依赖前一阶段，父RESULTS汇总实际结果。

## 全局约束

只在隔离工作区的forem内实施，不改当前运行中v5的源码/配置/目录；训练代码从明确快照构建，不让旧进程与新源码清单混用。不覆盖旧checkpoint，不动D10半轮与claim，不提交/推送Git。旧训练继续由原任务管理。每阶段登记累计预算及退出码，所有Python长任务用python3 -u、独立run-id/PID/日志。

## P0 — 冻结方案、版本与预算

- [ ] 核对用户已确认的短任务定义、1–2m、每组50k及4h上限；本次已由SRC-0971确认，不再重复询问；不擅自挑新范围。
- [ ] 读取最新PROGRESS、进程/GPU、forem-dev及挂载。选定单独GPU3前确认无他人计算；不可用则报告依赖，不移动/停止他人任务。
- [ ] 将A/B协议、代码/几何哈希、map index、seed与随机流、原5M学习率日程写入新run元数据；实际A/B唯一预期差异为短路线筛选，单独列其造成的任务分布变化。
- [ ] 用现有验证地图固定局部案例清单：每张固定验证图一份原分布案例、一份短路线案例；固定起始状态/扫描历史/路线/候选与proposal seed，两个模型都评同一清单。零时长、原地/非原地都登记，不筛掉困难样本；若短任务采样无法完成既定图覆盖，停止报告，不换图凑数。

## P1 — 最小采样扩展与测试

计划文件（**均尚未创建/修改**）：
- `forem/src/task7_sim/episode.py`：`EpisodeSampler(..., route_length_bounds=None, sampling_deadline=None)`；在原合法性与规划链中按最终`route.length`过滤，默认None沿旧逻辑；统计长度拒收/接受。deadline只作计算保护，耗尽抛错，不当实验成功或回退到简单地图。
- `forem/src/task7_sim/env.py`：透传可选采样参数；默认行为不变，Core状态推进/奖励/终止不改。
- `forem/src/task7_lower/training.py`：读取独立试验配置的可选采样字段；原配置缺省仍走旧路径。实施在隔离源码，禁止覆盖当前v5工作树。
- `forem/scripts/task7_short_task_trial.py`：明确A/B、预算账本、固定案例评估与元数据；复用LowerSAC/Replay及已有保存恢复，单worker，不调用D10并行驱动。
- `forem/config/task7/short_task_trial.json`：两组共同配置与route_length_bounds=[1,2]差异、50k/组、总4h、原学习率日程。
- `forem/src/task7_sim/tests/test_short_task_sampling.py`与`forem/src/task7_lower/tests/test_short_task_trial.py`：有意义的行为与统计边界测试。

- [ ] 先加失败测试：关闭筛选时，同RNG/输入得到原提案与状态；筛选开启时最终路线长在闭区间且保留合法性/碰撞见证；障碍绕路后长度超界不能按端点距离误收。
- [ ] 覆盖固定图采样耗尽：报告哪图/提案/原因，不自动换图；采样计时包含拒收开销。
- [ ] 覆盖route_end先于candidate：两类分别计数，不能靠reason=arrival直接认定底盘到达；原地/零时长单列、无伪造交互。
- [ ] 覆盖固定案例与评估隔离：不同训练结果不能改变评估状态/候选列表，不读验证集进replay；地图/候选/初态随机流可恢复。
- [ ] 覆盖50k预算边界/恢复：不丢尾批、不重复计环境动作、检查点含新增采样身份；短任务reset增加后经验池next_observation仍为原段末状态，不被reset覆盖。
- [ ] 测试失败后才写最小实现，再运行相应测试和受影响回归；保存命令/退出码，不用旧332/375测试计数冒充本轮通过。

## P2 — 有界端到端检查

- [ ] 单worker先进行有界采样与真实训练开头计时，计算预算计入总4h；分别记录reset/采样拒收、环境/IK、推理/update、replay/搬运、检查点与验证。
- [ ] 核实际tensor/optimizer及GPU；记录显存峰值，不能把初始化显存当整轮峰值。已有D10多worker OOM不照搬。
- [ ] 用实际吞吐和reset成本核剩余预算是否覆盖两组各50k及共同评估；无证据则停，不承诺工期或开启正式长训。

## P3 — 对照短跑

- [ ] A/B均从同初始化开始，seed4718，E256，网络/奖励/IK/候选/节拍/失败/价值mask一致。A沿原分布，B仅路线长1–2m；由于拒收/reset不同，后续轨迹不同是预期，不声称逐轨迹等价。
- [ ] 两组串行，每组上限50k有效转移，统一保持4,999,743更新的学习率衰减日程；采样与更新按原规则记账。所有训练、评估、失败重跑计总4h。
- [ ] 在固定局部案例上评价初始化和各组50k终点；分别报告短路线/原分布、候选到达/路线先结束/失败/超时以及原地/非原地，保留全部分母。未完成的评估明确未完成，不能报正式D10通过。
- [ ] 原训练目录和checkpoint不参与写入；现有500k模型只作历史参考，不作为等预算A/B训练对照。

## P4 — 判读与后续

- [ ] 汇总实际交互/更新、accepted route长度与地图/难度分布、拒收成本、失败类别、奖励/Q/alpha/动作统计、局部指标和wall/worker耗时。
- [ ] 若只是短任务更容易或更频繁末端先结束，不称下层改善；若原分布局部测试变差，报告分布迁移风险。
- [ ] 若短跑稳定且局部指标有进一步研究价值，再提交下一轮长预算/多seed建议；50k不检验百万步退化，不自动扩大或放行上层。

运行命令接口草案（入口/配置尚不存在，**尚未执行**）：

```text
python3 -u scripts/task7_short_task_trial.py --protocol config/task7/short_task_trial.json --phase preflight --output results/task7/<new-run-id>
python3 -u scripts/task7_short_task_trial.py --protocol config/task7/short_task_trial.json --phase paired-trial --output results/task7/<new-run-id>
```

实际必须按ENV通过`sg docker -c`进入既有forem-dev，显式分配GPU、隔离源码路径与日志；不是直接复制这两行就在宿主运行。挂载不支持隔离源码时先解决可读路径，不能顺手重建容器。

## 异常处理

采样耗尽、OOM、NaN、预算不足、身份哈希不符均停止本新run并保留证据，使用已有安全保存机制；不自动降batch/候选间距/障碍难度或删除失败记录。停止只针对核明属于本任务的worker。恢复需核checkpoint、交互账本与采样配置，不复用失败D10的claim方式。

## 模型与自审

推荐：Codex **GPT6.1sol / medium**、Claude **Sonnet5.5 / medium**，因为需要核对采样分布、回合边界和比较口径；普通监控用low/默认。本轮文档由系统标明的gpt-6-astra编写，推理强度未知，未切换模型、未派Agent；推荐不等于实际配置。

文档自审：已区分任务目标半径/路线弧长、短任务/单候选重置、整任务成功/局部到达；已列固定评估分母与预算、短跑不能证明后期稳定性。缩短路线方案及具体长度/预算已由SRC-0971确认；步骤状态按子任务实际结果更新。[SRC-0969](../../../SOURCES.md#src-0969)


## 实施子任务（SRC-0971）

|编号|顺序/负责人|三文档|验收关系|
|---|---|---|---|
|task7.24.1 隔离实现与验证准备|Codex gpt-6.1-sol/medium，按1→2→3执行|[TASK](task7.24.1/TASK.md) · [PROCEDURE](task7.24.1/PROCEDURE.md) · [RESULTS](task7.24.1/RESULTS.md)|父核证据；2为运行前门禁并复核3最终结果|
|task7.24.2 独立监督与结果审核|Codex gpt-6.1-sol/high，按1→2→3执行|[TASK](task7.24.2/TASK.md) · [PROCEDURE](task7.24.2/PROCEDURE.md) · [RESULTS](task7.24.2/RESULTS.md)|父核证据；2为运行前门禁并复核3最终结果|
|task7.24.3 有界计时与A/B短跑|Codex gpt-6.1-sol/medium，按1→2→3执行|[TASK](task7.24.3/TASK.md) · [PROCEDURE](task7.24.3/PROCEDURE.md) · [RESULTS](task7.24.3/RESULTS.md)|父核证据；2为运行前门禁并复核3最终结果|
