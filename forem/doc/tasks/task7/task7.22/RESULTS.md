# task7.22 — 结果

**2026-10-26执行冻结：paused。** 用户已冻结task7全部后续执行，见[父冻结入口](../TASK.md#2026-10-26-当前冻结入口)。已完成成果与下文历史状态保留；不得依旧授权自动续训、恢复或派发。当前转入task8地图迁移规划。

状态：**review（部分交付，待Claude复核；完整试训与端到端验收尚未完成）**。2026-10-21实施已授权，[SRC-0439](../../../SOURCES.md#src-0439)；最新事实见末节run-id（r1为历史），正式训练未授权、未启动。

## 运行记录

按run-id追加：执行Agent与实际模型/强度、改动文件、命令、代码/配置版本、退出码、证据路径、结论与限制。

## 交接

- 当前负责人：Codex；本轮交Claude复核，部分交付与待决定事项见文末交接。

## t7.22-r1-20261021 — 独立训练组件交付与接入门禁（2026-10-21）

当前负责人Codex；**部分交付，非流水线完成**。实际模型gpt-6.1-sol / medium（本次exec PID2931701参数核实）；复核推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium：需核对半马尔可夫目标、循环预热、跨阶段冻结与恢复。本任务实施依据[SRC-0439](../../../SOURCES.md#src-0439)，组件合同与工程选择见[SRC-0510](../../../SOURCES.md#src-0510)。正式训练未授权，未启动。

### 开工与下层限制

- task7.20和7.21以各自RESULTS末节Claude复核done为准（不是文首遗留模板）。main，保留其他会话全部改动；未提交、未启停容器、未停止他人进程。
- GPU1 compute门禁开工仅表头；每条容器命令前查询，原始快照见本run各`*.gpu.txt`。只用物理GPU1，`CUDA_VISIBLE_DEVICES=1`，进程内cuda:0；Xorg不计占用。
- 下层：`forem/results/task7/t7.18-20261021/pilot-{sync,async}/compatible.actor.pt`，step50000，加载版本`task7-lower-actor-v1`。**流水线验证用pilot下层；下层未经冻结验收**。task7.19正式D10未执行、阶段L已按用户决定停止，自碰撞几何诊断并行；本次不评价学习效果或任务成功率。

### 实际改动与已实现边界

|归属文件|实现/限制|
|---|---|
|`src/task7_upper/replay.py`|CPU精确回放；按run/env/episode分序列；不跨回合；uint8栅格、保存下一候选和掩码；不存e/h；容量10万、32条完整长度8片段；采样RNG可恢复。中段片段从零隐状态＋4步预热，不宣称等于全历史隐状态|
|`sac_discrete.py`|有效mask离散SAC、仅terminated切自举、γ^(Δt/0.1)、双Q目标；共享ψ的RL损失一次backward；Actor的Q detach；软更新0.001；Adam/指数衰减/裁剪10；温度0.35·exp(logα)、0.05固定。f_p参数不进RL优化器|
|`fp_trainer.py`|只对执行且到达标签计算1−cos；固定f_enc目标；回合级留出（10%数量向上取整）；耐心5轮的状态机；选择候选与其他候选cos差/离散度；G3逐维仿射一次拟合后拒绝重拟合，零随机方差显式拒绝；**未实现缺协议的完整epoch调度及新信息三档**|
|`stages.py`|片段前4无梯度/后4损失，下一状态临时递推后恢复当前历史；在线/目标网络各自重建；阶段接入复制头B，logits/Q/分布atol=rtol=1e-6硬断言；完整32×8 RL与f_p单批入口；前1000决策有效候选均匀采样；learner级原子保存与恢复。**实际环境adapter、完整阶段1→2→3在线编排与交互状态恢复未完成**|
|`evaluate.py`|G1及已提供adapter的学习组确定性评估函数，每图新环境1回合；严格成功率与无可行候选/选择变化计数；验证选择器要求显式间隔与并列规则，保存选择状态|
|`scripts/task7_upper_train.py`|有界预算与接入门禁；当前明确退出，不导入环境、不训练；**不是可用训练入口**|
|`scripts/task7_upper_eval.py`|G1完整50/100图池入口（本轮未执行正式池评估）；学习组因adapter缺口明确退出；GPU1与compute门禁|
|`config/task7/upper_train.json`、`tests/test_training.py`|已定超参与有界上限；未定协议字段null；组件测试。未修改task7_sim、task7.21生产模块、下层/参考仓库|

没有把入口占位门禁称为完整训练流水线；代码不能作为启动正式训练的依据。

### 测试与失败记录

依据[SRC-0511](../../../SOURCES.md#src-0511)。日志根`forem/logs/task7/t7.22-r1-20261021/`；产物根`forem/results/task7/t7.22-r1-20261021/`。完整argv/退出码/wrapper墙钟见[commands.jsonl](../../../../logs/task7/t7.22-r1-20261021/commands.jsonl)。运行在已存在forem-dev，单命令timeout580s，OMP/MKL线程2。

- 初轮新增组件：`python3 -u -m pytest -q src/task7_upper/tests/test_training.py`，14 passed/6.07s，退出0（直接docker命令，输出`training-tests.log`、JUnit `training-tests.xml`）。
- 第一轮全上层：`python3 -u .../run.py all-upper-tests -m pytest -q /root/mm_husky_ws/src/task7_upper/tests --junitxml=.../all-upper-tests.xml`，60 passed/8.97s，退出0；wrapper9.901s。
- 最终全上层：`python3 -u .../run.py upper-tests-final -m pytest -q /root/mm_husky_ws/src/task7_upper/tests --junitxml=.../upper-tests-final.xml`，**61 passed/9.94s，退出0**，wrapper10.923s。包含task7.21既有44项，本任务新增17项；不把61全记为新增。
- 新增覆盖：片段不跨回合/容量/下一候选mask/uint8往返；手算Q目标（含0.05s、终止和可截断自举、padding NaN隔离）；capped温度；两变体零步接入；G3尺度拟合/固定/零方差拒绝；f_p到达标签/冻结/早停状态；4步burn-in无梯度及32×8更新；四RL阶段CPU learner恢复与GPU阶段3恢复；固定验证选择；每图一次严格成功计数；无效损失拒绝。
- **恢复结果只限learner测试**：同种子继续一步后的损失、模型逐元素相同；优化器/调度器/温度/经验池与采样RNG及全RNG均保存。GPU用例核验参数与Adam exp_avg实际cuda。未接入环境时`online_resumable=false`，要求在线恢复会明确拒绝；没有“完整在线恢复通过”的结论。
- profile-sync首轮退出1/wrapper91.637s：临时脚本`profile.py`与标准库重名，被cProfile二次导入，torch._dynamo循环导入失败。更名为`bounded_probe.py`；失败脚本`profile-failed.input.py`、失败日志与`probe-progress-sync-failed.json`保留，不采用其性能结论。保守算最多6次随机决策，没有训练更新。
- `cli-gates`第一次被compute门禁拦住：占用者为本任务尚在运行的profile-sync；未启动第二条容器命令，未停止该profile。后续命令串行。

### 待决定与暂停的部分

按本PROCEDURE“规格有歧义只停该部分”执行；已完成独立组件与测试，其余不能通过调参或补常数绕过。

1. **实际上一结果→VCM 19维合同**：task7.21要求上一候选4/5维＋19维f_k v1；DecisionEnv返回r_t缺该表中的若干字段，实际碰撞类型又区分底盘/臂/自碰撞。禁止用`selected_prediction`冒充实际量。只读核对发现`core.feature_vector(core)`可在实际Core自动reset前算出公共19维（所有实际碰撞共用reason=3）；DecisionEnv未导出该快照。可选实现为7.22包装边界采集该函数的真实输出，但是否采用该公共编码及f_enc保留r_t的字段合同尚待明确；未擅改只读模块。**真实上层试训、完整阶段编排、学习组评估依赖此项，尚未执行**。
2. **阶段2epoch/预算口径**：W.3规定留出损失连续5“轮”不降，但未定义一轮批次数/片段复用；本任务阶段2≤2000“次决策”又是离线训练，如何计数未明确。只交付单批与早停状态机，没有自定epoch长度。
3. **W.4新信息量三档**：没有三档边界，也没有共同世界栅格下新增观测计数；两个移动局部栅格同像素之差不等于新信息。该诊断暂停，不自定阈值。
4. **正式验证选优**：N12明确间隔与并列规则待补，配置保持null；选择器可用，但正式运行配置未定，不能声称选优/测试通过。
5. **G3零随机方差**：未定处理规则；当前明确拒绝该拟合而非加epsilon。正常非零方差用例通过，不意味着该边缘情形已决定。

这些是协议/接入待办，不是训练效果差导致的暂停。无NaN/Inf、阶段3一致性或恢复失败被绕过；测试里故意注入无效值只验证拒绝行为。

### 最后补充验证（同run，保留前述61项历史）

- `begin_rl_branch`补齐U.4的**温度数值/固定状态继承、温度优化器重建、RL优化器/目标重新初始化与空D3**；G3未拟合固定系数时拒绝进入。此后执行`run.py final-regression -m pytest -q .../src/task7_upper/tests --junitxml=.../final-regression.xml`，**62 passed/9.75s，退出0，wrapper10.739s**（既有44＋新增18）。源码增加该边界函数后重新回归，未以旧61项充当新函数验收。
- `run.py final-contracts .../final_contracts.py`退出0/wrapper3.453s：[final-contracts.json](../../../../results/task7/t7.22-r1-20261021/final-contracts.json)。两变体GPU1零步接入的logits/Q最大差均0，**断言仍采用atol=rtol=1e-6**，不由本例零差改成严格相等。5001次决策拒绝、5000次因未定实际结果合同拒绝、G4独立评估入口拒绝，三个子进程均预期退出2；入口语法编译通过。没有因此启动交互/训练。

### 有界独立性能核查（完整上层端到端验收尚未通过）

依据[SRC-0512](../../../SOURCES.md#src-0512)。仅调用只读环境、下层与已有DLS开关；物理GPU1、float32、E=1、seed722、task7.16默认训练池、OMP/MKL线程2。每个成功探针3次均匀随机决策；模型未控制真实环境，不称上层试训。原始分布、逐决策分项、源码哈希与GPU设备在`profile-*.json`，汇总[performance-summary.json](../../../../results/task7/t7.22-r1-20261021/performance-summary.json)。`environment_decision`包括真实执行及下一边界准备/必要自动reset，不重复计入缓存的current边界；initial_reset另列。

|路径|初始reset s|决策wall s：mean / median / min–max|真实执行mean s|下一候选生成mean s|下一推演mean s|整探针wrapper s / 退出码|
|---|---:|---|---:|---:|---:|---|
|sync eager|30.050|5.010 / 2.937 / 0.889–11.204|1.008|0.304|3.679|49.507 / 0|
|sync graph|9.199|4.388 / 2.401 / 0.359–10.404|0.918|0.039|3.411|27.155 / 0|
|async eager（未完成）|141.018|前两次140.092、245.853；第三次超时，不能给完整三样本分布|未汇总|未汇总|未汇总|580.361 / 124|
|async graph|30.510|40.567 / 45.560 / 29.049–47.092|13.396|0.045|27.085|156.748 / 0|

- DLS graph为task7.18已有优化（[SRC-0471](../../../SOURCES.md#src-0471)/[SRC-0475](../../../SOURCES.md#src-0475)）；只设`env.episodes.kin.dls_cuda_graph=True`。两路径同地图/种子/动作；[graph-equivalence.json](../../../../results/task7/t7.22-r1-20261021/graph-equivalence.json)核对sync完整保存回放（观测uint8、候选/掩码、r_t、奖惩、结束字段、链接与RNG），逐元素相同，仅排除`search_wall_seconds`墙钟诊断。async eager未存完整checkpoint，只能核对已保留两步reward/dt/lower_steps/arrived/end flags，全部相同；**不把它称完整异步回放等价验证**。
- 成功graph探针提交仿真时间sync4.150s/async35.700s、下层动作步44/358；峰值allocated约1.398/1.909GiB。与wall分开；推演不是环境交互预算。冷启动/首次图捕获包含在原始样本内。n=3不报告可靠p95/p99，也不以整条命令比值当正式长期提速。
- CPU回放插入每次约0.004s；小型learner＋3条回放checkpoint约0.07s。容量10万时的写盘、压缩、退出排空、在线恢复与周期评估未测，不外推该小checkpoint成本。profile checkpoint保存`online_resumable=false`。
- 独立候选/头的合成128状态、13候选SAC更新约0.016–0.206s（各三次，含冷启动）；没有VCM和真实片段重建，不能拿来补成完整训练吞吐。
- [component-profile.json](../../../../results/task7/t7.22-r1-20261021/component-profile.json)：明确合成12维向量/3候选/32×8，前4无梯度。CPU片段采样0.000160–0.000281s；32×8份uint8单栅格构造＋搬运0.002620–0.010465s（不含下一栅格/全部向量）；f_p循环预热/重算/Adam更新首批1.055s，后两批0.108/0.112s；固定G3仿射拟合50×128样本0.000620s。参数与Adam动量cuda:0，三批损失有限；只是组件计时，不是实际阶段2曲线。
- GPU event为stream elapsed（含主机调度空隙），不是纯kernel总耗时；CPU项以同步wall为准。所有测量期各自`source_unchanged=true`。测量后stages.py仅新增`begin_rl_branch`及测试，该函数不在所测路径；最终manifest与测量哈希分别保留，不把旧测量版当完整最终流水线性能。
- 并行/线程：本轮仅一worker、环境E=1；未启动未经隔离核查的多进程。线程2是固定核查配置，沿已有task7.18线程1/2/4对照“无稳定收益保留2”的证据，不宣称本上层最优。CPU回放也暂定；实际adapter和完整更新路径缺失时，无法验收异步采样/并行环境的端到端收益，未擅自启用。

### 试训状态、诊断与条件墙钟推算

依据[SRC-0513](../../../SOURCES.md#src-0513)。**两变体上层阶段1/2/3有界试训均尚未执行**，没有真实学习曲线、成功率、f_p留出有效性或G4优于G2/G3结论。真实环境只跑上述随机性能探针；合成网络损失序列留在JSON，不称学习曲线。所有试训预算上限不变，没有以性能慢为由缩正式预算或改奖励/步长。

仅作条件场景计算：假定正式全程仍为E=1、随机探针的平均决策成本，取graph路径`c_sync=4.387811 s/决策`、`c_async=40.567280 s/决策`。用`B*c/3600`得到**环境部分**，未计真实循环SAC、阶段2、完整评估或IO。短探针的策略与任务分布会改变，不能当真实正式工期，也不是向量化worker的下界。

|组/阶段（每变体每种子）|sync条件环境小时|async条件环境小时|未计项|
|---|---:|---:|---|
|阶段1 B1=200000|243.767|2253.738|真实VCM/片段采样/SAC更新、验证、IO|
|阶段3或G2续训 B3=100000|121.884|1126.869|G3/G4偏置与f_p、验证、IO|
|G1|训练0|训练0|每测试档100图×1回合的评估成本，不能写成总成本0|
|G2 B1+B3|365.651|3380.607|同上，含实际输出头训练|
|G3 B1+B3|365.651|3380.607|还需阶段2训练后f_p作尺度参照、留出拟合；随机f_p冻结|
|G4 B1+B3|365.651|3380.607|还需阶段2与阶段3 f_p更新|
|G7仅阶段1，2变体×3种子共120万决策|未能量化|未能量化|规则路径执行器不同，不能套用下层SAC探针成本；也不能把旧短路线微基准当完整工期|

在此**未验证E=1条件场景**，单组已超过48h，必须停在正式训练授权前报告。没有改B1/B3、减种子、放宽门限或开正式训练。

- 若按种子共享同一阶段1检查点给G2/G3/G4：两变体×3种子的条件累计环境成本为`Σ_v 3*(B1+3*B3)*c_v/3600 = 18731.288 worker小时`。
- 若每组独立重训阶段1：条件累计环境成本为`Σ_v 3*3*(B1+B3)*c_v/3600 = 33716.319 worker小时`。这只是显式列出是否共享的成本影响，不视为已批准的正式调度方案。
- 只授权GPU1；若严格串行，上述场景全局墙钟与累计worker小时相同，未以4卡理论算力除耗时。G1评估、G7阶段1均另外登记为未测成本，不能从总量删除。
- 完整学习组成本应为`T_g=B1*c1+I_g*B3*cg+T_fp,g+T_eval,g+T_periodic_IO,g+T_resource,g`（秒，g为G2/G3/G4）；`c1/cg`必须包括真实VCM、采样/搬运与更新。共享阶段1时全局依赖公式见summary JSON。**完整全局墙钟与累计worker目前不可确定**：实际adapter/阶段2轮次/验证间隔/向量化批量/全容量IO与恢复尚缺。
- 下一步先明确结果输入与阶段2/评估协议，在本任务已授权预算内续做真实端到端profile与两变体有界试训；之后才可提交正式可行性估计。已有DLS优化可作为候选执行路径，实际学习策略及并行批量仍须同输入核查，不能用本表承诺正式工期。

### 预算、最终范围与交接

- [budget.json](../../../../results/task7/t7.22-r1-20261021/budget.json)：已记账wrapper累计947.558s；初轮直接测试另保守计15s，共962.558s（约16.04分钟）＜6小时。每条容器命令timeout580s。随机环境探针保守计sync12次、async6次尝试（包含失败脚本二次导入和超时中的第三次）；正式训练0，真实上层训练阶段1/2/3均0。合成单测与组件更新不冒充环境训练预算。
- [delivery-manifest.json](../../../../results/task7/t7.22-r1-20261021/delivery-manifest.json)固定9个归属代码/测试/入口/配置文件SHA256及根HEAD `cac6c15599efcbe47a1a7ed30f59a475e4997fd4`（未提交工作树，HEAD不是交付版本本身）。[scope-verification.json](../../../../results/task7/t7.22-r1-20261021/scope-verification.json)核对所有task7_sim、task7_lower与task7.21生产模块与首个成功profile哈希一致；仅本任务stages.py在计时后增加边界函数。未修改参考仓库/阶段一代码，未提交Git。
- 收尾`gpu-final.txt` compute仅表头；本任务run/probe/pytest已全部退出，无需停止或恢复后台任务。收尾进程rg退出1表示无匹配，不是测试失败。
- **交接目标与授权**：本任务只实现限定文件、做有界核查/试训与正式成本推算；当前为review（部分交付），不能标done或启动正式训练。当前负责人Codex，交Claude复核；推荐GPT6.1sol / medium、Sonnet5.5 / medium，跨阶段梯度/恢复/计时适用性核对。
- **已完成**：精确序列池、离散SAC、单批f_p与G3固定拟合、阶段边界、learner恢复、确定性评估函数/入口门禁；62项测试通过，另两变体GPU接入断言通过；两变体真实随机探针及分项/合成组件计时、已有DLS优化对照、条件成本外推与限制落账。
- **剩余与风险**：前述实际结果输入合同、stage2 epoch/离线预算、新信息档位、验证选优参数；真实adapter/完整阶段编排/在线恢复、真实两变体试训和完整工期不可确定。pilot未D10冻结，自碰撞模型正在诊断，不可据本轮宣称学习有效或几何正确。E=1条件外推已超48小时；不能以此直接推定向量化正式worker工期，也不能忽略该警讯。
- **下一步**：Claude先核对本RESULTS/SRC-0510–0513及manifest、关键代码和原始日志，再明确待决定合同并安排本任务授权预算内的剩余接入/真实端到端核查。有界试训仍须按原上限执行；正式训练需单独授权。无运行任务或恢复中的容器。

## Claude复核 t7.22-r1（2026-10-21T21:05，claude-opus-5-5，推理强度未知）

- 读RESULTS：独立组件62项测试通过（Codex记录）；五项待决定确属规格缺口，已由用户定（SRC-0907）。E=1决策成本同步4.39 s、异步40.57 s，阶段1条件环境时长244/2254小时，须E扩展与推演批量化（用户同意一并做）。
- 结论：返工r2。


## t7.22-r2-20261021 — 端到端续接（active；21:53中间记录）

负责人Codex，实际gpt-6.1-sol/high（宿主exec PID2984488参数核实）；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为跨阶段接入与同输入等价核查。用户已定协议及范围见[SRC-0907](../../../SOURCES.md#src-0907)。本轮仅GPU1，不改robot.py/robot_geometry.json、不启停容器、不停止非本任务进程、不提交Git、正式训练未授权。

- 已实现真实19维reset前快照与全局新观测计数、在线/序列精确adapter、stage1/2/3与G2/G3分支入口、完整环境＋精确回合前缀恢复、交互账本防预算回退、阶段2batch256整轮/早停/三分位诊断、G3零方差均值回退和验证三级选优。实现与覆盖限制见[SRC-0514](../../../SOURCES.md#src-0514)，尚不能以源码代实际试训通过。
- 所有候选SIM压缩已弃用：E16两变体完整转移虽各200字段相同，但E64出现f_k最大差14.6；两轮较早压缩也有7.9/4.2差。失败原始证据/源码保留，详见[SRC-0515](../../../SOURCES.md#src-0515)。未放宽容差、未在试训启用。
- 最终性能候选保持完整E×13 SIM与NN，仅独立几何分块32→256/128及不保留无用预测Transition。88项回归通过；真实完整对照正在执行，见[SRC-0516](../../../SOURCES.md#src-0516)。各版性能分开登记，不把旧压缩版本的计时当最终路径。
- 当前task7.18.2为review部分交付，修复验收失败且生产仍v1。收尾按当时生产版本跑sim/lower/upper三目录独立进程回归，不把候选几何失败当生产已修好。
- 真实上层试训阶段1/2/3此时仍0；r2真实随机核查sync80次、async32次（暂计，最终以各JSON attempted为准），后续均保守纳入原5000/2000上限。原r1累计962.558s从6h扣除，wrapper会在不足下一条580s上界时拒绝启动。无正式训练。

### r2性能与版本更新（23:44，actual trial active）

完整SIM/NN保持E×13，采用P6 chunk256、观测chunk128；E16/64/256同输入核查及真实单批成本、缓存schema4配对结果（详见哈希/元数据审计更正）见[SRC-0516](../../../SOURCES.md#src-0516)。没有采用SIM行压缩。schema4已由task7.18.2于23:30完成，实际trial合同/summary已读出schema4，冻结源码逐项hash一致；不改其robot.py或JSON。本轮E64只是保证完整8步序列的有界工程选择，跨版本扫描不能证明最优E。

实际阶段1同步已开始；各阶段最终计数、更新数、恢复及新几何三目录回归仍待，不用此中间记录作为完成验收。

## t7.22-r2b-cpu-history-20261022 — 恢复接线修复后续跑（active，中间证据）

实际Codex gpt-6.1-sol/high；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，原因是跨设备恢复、版本保全与同输入核查。延续r2原6h及每阶段上限，不重置计数；正式训练仍未授权。

- 异步201在已保存960次决策后，下一前缀重建因CPU/GPU历史混合退出1。错误在下一动作意图之前，账本/检查点对齐，未回退交互。修复只令`load_online`返回首次CPU载入的历史，环境仍GPU；新增GPU回归1 passed。原检查点/合同保全、active版本元数据迁移、全张量/数组/标量与集合等值证据见[SRC-0518](../../../SOURCES.md#src-0518)及同run `migration-devicefix/`。
- 修复后异步已真实保存1088次决策、89次SAC更新；Actor/Critic/温度损失、梯度范数有限，参数与Adam exp_avg均实际cuda:0（物理GPU1）。当前D1完整片段203，eligible训练/留出到达15/3。实际采样/学习证据见[SRC-0517](../../../SOURCES.md#src-0517)，只能证明该有界流水线执行，不作学习效果结论。
- 同步仍1152次/5片段/0更新，数据前提未满足；不得把它称已训练。异步将继续至1152，再做独立续行对照、完整epoch f_p/5轮早停、schema4三目录回归、阶段3先1024；这些步骤此时尚未完成。
- 本节为执行中快照，最后验收以本RESULTS后续收尾节、最终manifest与实际产物为准。原r1与r2a中间记录作为历史保留。


<a id="r2-final"></a>
## t7.22-r2-20261021 / r2b 收尾（2026-10-22 03:22，review部分交付）

**异步G4完成真实三阶段有界流水线；同步只完成阶段1采样，未满足训练数据前提，阶段2/3未执行。** 不能将本任务标done。负责人Codex，实际gpt-6.1-sol/high（宿主exec参数已核实）；推荐Codex **GPT6.1sol/high**、Claude **Sonnet5.5/high**，原因是端到端接线、跨设备恢复和同输入等价需联合核对。沿用户已定协议[SRC-0907](../../../SOURCES.md#src-0907)，本轮只GPU1，下层仍task7.18旧pilot50k，**仅证明流水线执行，不作学习效果结论，上层正式训练未启动**。前面r1/r2/r2b执行中快照保留，当前结果以下表及原始证据为准。

### 实现与文件边界

实现事实及工程选择登记[SRC-0514](../../../SOURCES.md#src-0514)，交付12个文件SHA及四份active合同见[delivery-manifest.json](../../../../results/task7/t7.22-r2-20261021/delivery-manifest.json)。修改五个upper模块、train/eval入口、upper_train.json、对应测试，以及用户授权的DecisionEnv/Core性能路径。未写robot.py、geometry.py、perception.py或robot_geometry.json，保留task7.18.2的Core.step两处实际IK q接线；未改只读参考仓库、未提交Git。

- DecisionEnv在实际执行段结束、自动reset前计算`core.feature_vector(actual_core)`的19维快照（碰撞统一reason3），导出上一候选、路线进度/位置等重建字段；实际结果不由选中预测代替。f_enc保留完整r_t13维，最终sync78/async79维；VCM使用上一候选4/5＋实际19维，在线与回放均由原始uint8栅格/精确CPU回合前缀重建，未保存过期latent充当训练输入。
- 阶段2每轮对已收集eligible样本完整遍历、batch256、末批保留，固定回合留出、连续5轮未优于best早停；新增全局新观测格数及一次固定留出三分位诊断。G3随机维零方差时scale0、shift为训练f_p均值，其余维正常仿射。新信息分档不参与奖励或选优。
- 配置已写每10000决策验证、严格成功率优先→到达率→更早检查点；本轮未到10000，所以**配置与组件已验，实际完整验证/最优checkpoint选择尚未执行**。
- 阶段3真实首边界做logits/Q1/Q2一致性断言`atol=rtol=1e−6`；新D3、重建RL优化器/目标、继承温度数值与固定状态；f_p只接自身监督梯度，target next-Q前同步当前f_p。G2/G3代码分支有组件验证，本轮真实试训为G4。阶段3FP权重继承、FP Adam重建是已记录工程选择，未冒称继承原Adam状态。

### 两变体实际计数与诊断

依据[SRC-0517](../../../SOURCES.md#src-0517)，原始[summary.json](../../../../results/task7/t7.22-r2-20261021/summary.json)、各`trial-*/summary.json`、`learner-updates.jsonl`与阶段2`events.jsonl`。

|变体/阶段|真实决策或独特离线样本|SAC更新|f_p更新/epoch|结果|
|---|---:|---:|---:|---|
|sync阶段1|1152决策/18批|0|不适用|仅5个完整8步窗口，未达32；eligible到达0/0，78早期到达排除|
|sync阶段2|尚未执行|不适用|0|缺可用train/holdout独立到达样本|
|sync阶段3|尚未执行|0|0|依赖阶段2，剩余墙钟不足下一段采样|
|async阶段1|1152决策/18批|153|不适用|218完整窗口；eligible train27/hold4，89早期到达排除|
|async阶段2|31独特样本＝训练27＋留出4|不适用|1125更新/1125epoch|完整遍历训练27，末批27；5轮无新best后早停|
|async阶段3|1024决策/16批|25|25|187完整窗口；eligible train17/hold2，64早期到达排除|

当前序列规则是完整长度8窗口末位置的唯一到达标签，前4步burn-in；回合索引0–6的实际到达没有末位置完整窗口，单独计omitted，**不表示没有发生到达**。sync896时只读审计发现若改用任意后缀标签另有3个覆盖点，但那是另一数据覆盖口径，本轮未实施、未填充或跨回合凑样本。此覆盖限制与同步数据不足是明确的剩余事项，不用改预热/奖励/终止绕过。[SRC-0514](../../../SOURCES.md#src-0514)、[SRC-0517](../../../SOURCES.md#src-0517)

阶段2来自19训练回合、3留出回合，独特样本31≤2000；复用1125轮不是新增交互。最优留出0.013987302780151367，最后train/hold为0.0008036626968532801/0.014407917857170105。固定新信息阈值[0,0]、三箱3/0/1（空箱loss=null），chosen-minus-other=0.3291021585、dispersion=0.00095124694；阈值重复、留出很小，诊断不能证明泛化或有效性。实际G3零方差维0，均值回退只由组件用例触发。[SRC-0517](../../../SOURCES.md#src-0517)

真实学习loss、梯度范数和温度、保存模型/优化器Tensor均有限；参数与SAC/FP Adam exp_avg实际cuda:0，对应物理GPU1，阶段2FP Adam保存设备也经CPU审计读原storage标签核实。下层GPU路径未回退CPU。CPU回放/精确前缀是明确存储布局；async阶段1/3末次峰值allocated约19.79/19.89GB（bytes见summary），不能将GPU占用率当速度证据。[SRC-0517](../../../SOURCES.md#src-0517)、[SRC-0518](../../../SOURCES.md#src-0518)

[真实曲线](../../../../results/task7/t7.22-r2-20261021/curves-async.png)仅绘实际153/25次SAC更新、1125个epoch与25次阶段3FP更新，无填补或合成曲线。同步0更新不画训练曲线；下降或有限损失不等于任务效果提升。

### 性能选择、等价与版本适用性

完整证据见[SRC-0515](../../../SOURCES.md#src-0515)、[SRC-0516](../../../SOURCES.md#src-0516)。候选SIM行压缩在E64出现f_k最大差14.6，已全撤回，归档失败与源码；没有因E16通过就采用，也没有放宽容差。最终SIM及下层NN均保持完整E×13，仅采用独立几何计算分块256/观测128、段内路线几何缓存，以及不保存无用推演Transition；公开观测返回clone所有权保持。

|真实冻结下层NN单批扫描|E16 秒/决策|E64 秒/决策|E256 秒/决策|几何/限制|
|---|---:|---:|---:|---|
|sync|6.171705|3.355589|3.088391|v1，文件hash与保存v1配置核实；各n=1、不含learner|
|async|4.596435|2.471753|2.168877|schema3；各n=1、不含learner|

reset及完整批墙钟保留SRC-0516表和`performance-final-*.json`，未摊入上表；不能把混几何扫描证明统一最优E。分块同E逐元素证明：sync E16真实NN训练池、async E16真实NN短路线fixture、E64/E256脚本短路线fixture，全部公开转移/观测/f_k/奖励/mask与回放字段相同；后两E不称真实NN训练池成对证明。跨E的原轨迹/浮点差异不作bitwise相同承诺。

schema4同输入完整缓存对照：sync E64为280.742805→190.858979s（31.96%），async E64为158.189339→132.051733s（16.52%），所有公开/回放字段逐元素相同，各n=1。缓存只在base/route_s未变时复用路线几何，扫描仍重算，reset/begin清理。同步期间仅三项审计元数据变化，物理几何相同，`cache-geometry-audit.json`已核对；早期误记schema3已纠正。首个同步580s组合命令退出124保留，后独立后台长命令完成对照，不以超时记录称通过。[SRC-0516](../../../SOURCES.md#src-0516)

本轮E64是完整8步序列与有界预算的工程选择。stage3≤2000，E256至少8批需2048已越界；E64在1024内16批。不能据此称正式E64最优。task7.18.2已done后在最终schema4上完成下述三目录回归，不再沿旧几何验收。[SRC-0516](../../../SOURCES.md#src-0516)、[SRC-0518](../../../SOURCES.md#src-0518)

### 真实恢复、故障与完整回归

依据[SRC-0518](../../../SOURCES.md#src-0518)。异步stage1第201段在已完整保存960时，下一动作前发生CPU/GPU历史混设备堆叠；修复`load_online`只取首次CPU bundle.histories，GPU环境恢复不变。新增GPU回归覆盖恢复→追加CPU行→重建。旧完整checkpoint/meta/合同/源码均保存在`migration-devicefix/`，active合同仅显式更新版本hash/环境config_hash并带provenance；迁移前后全部Tensor/NumPy/scalar及集合核验相同，计数/RNG/模型/标签不变。未关版本门禁、未回退交互预算，后续实际恢复采样/更新成功。

|隔离恢复对照|主源决策/更新|两副本真实续行|浮点字段|最大绝对差|结果|
|---|---|---|---|---:|---|
|async阶段1|1152/153|各64决策＋1 SAC更新|576，568 exact|7.450580596923828e−9|通过，atol=rtol=1e−6|
|async阶段3|1024/25 SAC/25 FP|各64决策＋1 SAC＋1 FP|411全部exact|0|通过，仍atol=rtol=1e−6|

A载入源后保存、保存后活对象继续；B新建载入该保存再继续。环境/动作/回放逐元素相同；主源checkpoint SHA未变。隔离副本更新154或26/26不计入主run更新，续行决策仍保守计预算。原始[阶段1恢复](../../../../results/task7/t7.22-r2-20261021/recovery-async-stage1.json)与[阶段3恢复](../../../../results/task7/t7.22-r2-20261021/recovery-async-stage3.json)含字段比较、源码/源checkpoint SHA、设备、wall/stream分项；仅单批＋单次更新，不扩成长期恢复保证。stream elapsed含host间隙，不是kernel总时间。

schema4完整GPU回归：**sim243＋lower18＋upper71＝332 passed，fail/error/skip均0**，wrapper363.501472s/退出0；下层3个既有torch.tensor复制警告保留。生产源码回归后无变化，四份active合同当前源码差异均空；最终stages SHA `cc91f441eadd2e132666b91d3c701575b7e776f4a3377a93a3d3c7e07b0f99d9`。原始XML与[final-integrity.json](../../../../results/task7/t7.22-r2-20261021/final-integrity.json)核对计数、账本complete/meta/checkpoint、loss行数=更新数、模型/优化器有限、早停/G3、恢复源SHA全部通过；显式列缺`sync-stage2/3`，不据此升级整个任务完成。

收尾helper首次误匹配恢复`.input.meta.json`触发KeyError source、退出1/29.891739s；归档首轮报告及helper，仅收窄报告glob，未改生产/产物/容差；复查退出0/31.123485s。错误和复查均计原预算。[SRC-0518](../../../SOURCES.md#src-0518)

### 正式条件墙钟与实际计时

输入/公式及限制见[SRC-0519](../../../SOURCES.md#src-0519)、[conditional-costs.json](../../../../results/task7/t7.22-r2-20261021/conditional-costs.json)。E64实际schema4全路径wall包含该stage启动、失败重启、环境、CPU回放/搬运、真实更新与小buffer保存；隔离恢复/测试另计核查预算。它不能代表正式10万容量IO和后期状态分布。

|实测路径|wrapper wall s|原始秒/决策|有效更新均值s / 样本数|校正预热后的正式阶段条件h|
|---|---:|---:|---|---:|
|sync阶段1|3370.304338|2.925611|未知/0|未知；仅同采样路径162.533967h|
|async阶段1|4131.515510|3.586385|0.285406543 /153|212.913893h（B1=200000）|
|async阶段3 G4|3568.345303|3.484712|0.273743750 /25|104.139638h（B3=100000）|
|async阶段2|350.166957|离线无此口径|1125epoch实际训练|正式样本量/轮数未知，不能按决策线性外推|

不能把本轮1000次预热比例外推正式阶段。定义`c0=(stage wrapper−全部sequence_update wall)/N`，按当前ready(count≥1000)得到正式更新数`max(B−999,0)`，条件小时`[B*c0+max(B−999,0)*mean(u)]/3600`。async c0_1=3.548469130、c0_3=3.478017910s/决策。直接总wall/N不校正的199.243611/96.797561h只作对照，不作为主估计。[SRC-0519](../../../SOURCES.md#src-0519)

async G2/G3只显式借G4阶段3成本作代理（本轮未实际profile两组），每组每种子已测路径部分317.053530h，另缺正式FP准备/训练、完整验证/测试、全容量IO/故障和后期策略分布。三种子共享stage1场景1575.998418 worker h；各组独立stage1场景2853.481774 worker h，只含async已测部分。只用GPU1串行，同场景global wall等于累计worker，不再除E或4卡。sync真实更新/stage3未知，**完整两变体global wall和worker总量保持未知/null**；G1训练0但评估未知，G7独立执行器成本未知，不能套冻结NN成本。

该条件场景显著超过48h，**未建立上层正式训练可行性**；不改B1/B3/种子/物理步长，不启动上层正式训练。E64跨10000验证边界与100000尾批调度尚缺正式验收，当前CLI明确拒绝相应不对齐调用；完整固定池评估/最佳checkpoint选择也未实跑，不能从上述条件算术推定已支持正式规模。[SRC-0519](../../../SOURCES.md#src-0519)

### 预算与交接

[budget.json](../../../../results/task7/t7.22-r2-20261021/budget.json)：r1 962.558s＋本轮全部容器命令累计**21380.062660s＝5h56m20.063s＜6h**，余219.937340s，无active job。48条命令包括失败/重跑、迁移、恢复、全目录测试与最终产物检查；超过10分钟的实际GPU任务均docker exec后台、Python -u、独立PID/log/timeout，前台命令均≤10分钟，未以后台规避累计预算。同步准备续至1408时在容器启动前被预算门禁拒绝，未启动新交互，宿主调度器退出1为预算拒绝，不是数值失败。全局elapsed（另含实施/文档/等待）见summary，不能与容器wall相混。[SRC-0517](../../../SOURCES.md#src-0517)

[action-accounting.json](../../../../results/task7/t7.22-r2-20261021/action-accounting.json)保守合计所有带attempted的探针/fixture和r1：阶段1 sync2540/async2486各＜5000；async阶段3含独立两副本恢复共1152＜2000；阶段2独特样本31＜2000。测试fixture/探针未混入训练池或伪装训练效果。

[resource-final.json](../../../../results/task7/t7.22-r2-20261021/resource-final.json)与gpu-final.txt：GPU1无compute，无本任务训练/恢复/helper/调度程序；GPU2/3外部下层训练保留，未停止非本任务进程、未启停容器。最终protected hash：robot.py `9fa144f7858130e09945dd09b8094ae8d2046f8698ed48315ecae2affbda3017`；robot_geometry.json `6c41120ad85bdea61a24b1089e825febf4f6b62eb93da0474e51f386167b084a`。[SRC-0517](../../../SOURCES.md#src-0517)、[SRC-0518](../../../SOURCES.md#src-0518)

- **目标/授权与负责人**：本轮接线、等价、E扩展、两变体有界试训及工期报告；Codex部分交付review，不发起新的文档复核轮次，不标done；正式训练仍未授权。
- **已完成**：用户五项协议接线与性能路径，异步真实三阶段/有限性/入口断言/两阶段独立恢复，schema4三目录332项、产物完整性与哈希、E扩展和条件成本/失败限制落账。证据均在同run根目录及commands日志，模型/推理推荐如本节开头。
- **剩余**：同步实际SAC、阶段2/3及其恢复；完整验证/测试与选优；G2/G3真实分支、G7 standalone环境factory接入与成本；正式向量验证/尾批调度和满容量IO/长轨迹性能。不能按未执行项验收全任务。
- **风险/待决定**：同步当前完整末位置到达标签口径导致覆盖不足，另一后缀口径仅审计、未获本轮实际采用；不以新标签语义绕过。若拟改标签覆盖，先明确规格及影响；若坚持原合同，则需继续采样的时间预算。6h剩余约220s不足有界新采样＋保存/验收，不能擅自延时。pilot50k旧下层与留出4样本不支持学习效果或物理泛化结论。
- **下一步**：接收方先读本收尾与SRC-0514–0519、manifest、关键源码和原始产物，再核对依赖/剩余预算；现无需监控或恢复后台任务。同步未完部分保持明确依赖，不自动进入正式训练或改变数据合同。
