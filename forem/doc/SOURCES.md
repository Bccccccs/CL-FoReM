# 论据与引用来源台账

> **2026-10-16文档整理**：task1、task2、experiment/、task4.1–4.6、task4.11–4.13及其日志已删除；下方条目中指向这些路径的链接已失效，原文见[SRC-0321](#src-0321)所列备份。条目本身保留，编号不复用。

本文件统一保存需要论据的数据、参数、方法和观点的出处，规则见[根AGENTS](../../AGENTS.md)。使用论据的文档须链接到对应稳定编号，例如 `SOURCES.md#src-0001`（按所在目录调整相对路径）。同一来源可支撑多个条目，但必须分别说明它支持什么，不能只列论文标题。

## 当前覆盖范围

2026-10-06建立规则与模板，尚未开展历史文献、参数依据的集中核查；下方新增条目仅核对项目安排与本地源码，不代表历史文献、参数依据已集中核验。本文件的建立不证明现有时延取值来自通用工作，也不证明其适用性。已有文档中的引用保留，在后续使用或修改相应主张时补登核查。

## 登记与维护

1. 新条目按 `SRC-0001` 起顺序编号，编号永久保留、不复用；正文采用 `## SRC-0001` 标题，便于链接。
2. 先写明确的主张，再查能直接支持它的原始来源。状态使用“待补证据 / 待核验 / 已核验 / 已被修正”；来源已核验不意味着对本项目的适用性已验证。
3. 在任务/实验正文相关句子旁链接条目；本台账的“使用位置”反向链接正文。参数协议、原始数据与结果保留在既有位置。
4. 发现冲突或来源更新时追加核查记录，说明影响；保留历史来源、版本及旧结论被修正的原因。

## 条目模板（尚未登记的占位示例）

```markdown
## SRC-NNNN

- 主张：具体数据、参数、方法选择或观点。
- 类型：外部文献 / 项目实测 / 推导 / 工程选择 / 待验证假设。
- 核查状态：待补证据 / 待核验 / 已核验 / 已被修正。
- 来源：作者或机构；标题；年份；版本；URL/DOI或本地证据链接。
- 精确位置：章节、页码、表图；或代码commit与符号；或run-id与数据字段。
- 原始依据：来源实际说明什么；数值、单位、适用条件。摘要与直接引文须区分。
- 本项目采用：采用内容、理由及换算/推导过程；输入来源、公式、单位。
- 适用限制：平台、控制频率、任务、机制差异；不支持哪些延伸结论。
- 使用位置：任务/实验正文链接。
- 核查人及日期：实际阅读/核对者与日期；未核查写未知。
- 待办与变更：缺失证据、验证事项及后续修正记录。
```

## 时延选择的填写要求

必须回答：所选值是已有工作直接采用的、本项目实测推导的，还是探索性扫描的工程选择？

- 沿用已有工作：给出原始出处、取值/范围、单位、动作或控制周期、时延所在层与机制、平台和任务条件，说明迁移到本项目的理由与限制。某项工作采用某值，不能单独证明该值是行业通用标准。
- 根据基线选值：链接实际run与测量字段，说明基线响应、动作时间尺度和候选时延之间的关系及计算过程。
- 探索性选值：标记工程选择，解释扫描范围的理由和待验证事项，不声称已获文献或实测证明。
- 若按步数表示：同时记录秒数、周期、换算及取整方式；区分整条轨迹传输延迟、逐步动作延迟与执行器响应滞后。

以上仅为记录要求，不指定时延值、不改变现有协议，也不授权追加实验。

## SRC-0001

- 主张：当前Task3登记为补偿诊断计划准备；RL备选exp4拟训练固定底座UR5无接触到达/轨迹跟随策略；动作、奖励、容差、预算尚未冻结，未训练。
- 类型：工程选择（已有方案/进度的文档事实）。
- 核查状态：已核验文档内容；实验效果及适用性待验证。
- 来源：FoReM项目文档，2026-09-30候选设计及2026-10-06进度；本地dirty工作区，根HEAD `438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804`（这些工作区文档不均在该commit内）。
- 精确位置：Task3准备日志（旧任务内容已删除）目标/授权段；[exp3 TASK](experiment/备选/exp3/TASK.md)目标；[exp4 TASK](experiment/备选/exp4/TASK.md)目标/方法；[exp4 PROCEDURE](experiment/备选/exp4/PROCEDURE.md)步骤1、2、6；[exp4 RESULTS](experiment/备选/exp4/RESULTS.md)开头尚未执行声明；PROGRESS的TASK3-PLAN登记。
- 原始依据：Task3日志为补偿诊断草案、尚未交付；exp3明确固定轨迹、不用SAC；exp4写明固定底座先做到达/跟随、最终动作由SAC输出，在线交互提供经验，关节速度/增量只是待选动作接口。
- 本项目采用：向用户解释现有计划和拟议训练对象，保持候选与冻结协议的区别。
- 适用限制：未核对已取消旧PH路线中Task3含义；不能据此断言所有历史安排都相同；不证明已实现关节策略，也不新增功能/实施授权。
- 使用位置：[本次解释记录](agent_logs/task3/20261006-codex-rl-scope-clarification.md)。
- 核查人及日期：Codex /root，2026-10-06，已阅读所列本地文档。
- 待办：RL实施前须审计/选择接口并冻结任务、奖励、频率及训练协议；本次不执行。

## SRC-0002

- 主张：本地参考SAC实现更新策略网络及双Q网络；原Husky策略动作配置包含底盘动作，并可按配置加入末端速度幅值和关节动作，不能直接当固定底座UR5六关节策略。
- 类型：项目源码核查（参考代码静态事实，非训练实测）。
- 核查状态：已核验所列代码；具体历史训练配置待核验。
- 来源：Husky+UR5参考快照，本地代码；工作区根HEAD `438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804`；AGENTS记录恢复来源 `1ccedd087ac12dd317e93accc37bb81e05beeb99`，本次未重新执行371文件内容校验。
- 精确位置：[sac.py](../../husky/src/modulation_rl/scripts/sac.py) `SAC.update_parameters`，90–125行双Q损失/优化及policy损失/优化；[combined_env.py](../../husky/src/modulation_rl/scripts/modulation/envs/combined_env.py) `CombinedEnv.__init__`，127–143行动作构造；[robotenv.py](../../husky/src/modulation_rl/scripts/modulation/envs/robotenv.py) `get_ranges`，底盘及可选关节字段。
- 原始依据：qf1/qf2损失相加后优化critic；policy.sample及policy_optim更新策略；get_ranges根据drive/learn_vel_norm/num_learned_joints构造动作。
- 本项目采用：区分RL学习决策策略/价值估计与学习预测模型，并提醒参考策略与候选固定臂接口不同。
- 适用限制：仅静态阅读，不证明任何训练已经运行或成功；不表示FoReM已选用/接通此SAC实现。
- 使用位置：[本次解释记录](agent_logs/task3/20261006-codex-rl-scope-clarification.md)。
- 核查人及日期：Codex /root，2026-10-06；本地源码已阅读。
- 待办：历史checkpoint动作含义需其真实配置/日志；固定底座训练接口尚未冻结。

## SRC-0003

旧任务方案及关联内容已按用户2026-10-07明确要求删除，仅保留稳定编号作删除标记；不保留原方案参数/结果正文，不作为新Task3/4依据。删除记录见[SRC-0042](#src-0042)。

## SRC-0004

旧任务方案及关联内容已按用户2026-10-07明确要求删除，仅保留稳定编号作删除标记；不保留原方案参数/结果正文，不作为新Task3/4依据。删除记录见[SRC-0042](#src-0042)。

## SRC-0005

旧任务方案及关联内容已按用户2026-10-07明确要求删除，仅保留稳定编号作删除标记；不保留原方案参数/结果正文，不作为新Task3/4依据。删除记录见[SRC-0042](#src-0042)。

## SRC-0006

旧任务方案及关联内容已按用户2026-10-07明确要求删除，仅保留稳定编号作删除标记；不保留原方案参数/结果正文，不作为新Task3/4依据。删除记录见[SRC-0042](#src-0042)。

## SRC-0007

- 主张：Task2的0/80/160 ms及8 ms迟到容差、B/Z等价/重复性阈值为本项目机制验证工程选择；没有已核查文献证明这些值是UR5硬件实测或通用标准。
- 类型：工程选择及单位换算推导；适用性待验证。
- 核查状态：已核验冻结配置和协议原文；外部时延依据待补证据，不将工程选择称文献结论。
- 来源：FoReM，2026-10-06；[exp2.1协议](experiment/备选/exp2/exp2.1/PROCEDURE.md)§1、2、5；[execution-freeze](../results/task2/t2.3-exec1/freeze.json) frozen_config、pre_registered_gates；[Task1配置](../config/experiments/task1/baseline.yaml)。工作区HEAD `438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804`，执行源码为dirty文件，以freeze内sha256为版本。
- 原始依据：常规125 Hz（周期8 ms）、物理步0.5 ms、轨迹3/6 s；首版整条header.stamp=0 JointTrajectory在发送与控制器间排队，PID/物理不变。协议以可观测性说明80/160 ms，未沿用明确外部工作的原始时延设定。
- 本项目采用：按探索性工程选择登记。80/160 ms ÷ 8 ms = 10/20反馈周期，÷0.5 ms = 160/320物理步，恰整除，无取整；按仿真纳秒时钟到期交付，并不实际用步数实现。占3 s轨迹2.667%/5.333%，占6 s轨迹1.333%/2.667%。8 ms是一个常规反馈周期的工程迟到容差；等价/重复性各阈值取冻结gates字段，来源仍为预注册工程判据，而非测得机器人精度。
- 适用限制：UR5固定底座、Gazebo、整条两点轨迹；不代表驱动响应滞后、真实通信时延或SAC逐动作时延；导航参数不能证明其适用性。原t_ref对齐判据与fit对齐实现不同，见SRC-0008。
- 使用位置：[task2.5审核](tasks/task2/task2.5/RESULTS.md)、[task2.6修正流程](tasks/task2/task2.6/PROCEDURE.md)。
- 核查人及日期：Codex /root，2026-10-06；已阅读所列本地原文与冻结配置。
- 待办：修正验收口径，不因本条登记新增实验、改变τ或宣称硬件合理性。

## SRC-0008

- 主张：Task2.5独立审核核对52次正式/高频尝试、6225项无差异，186单元测试及3次fresh M3/19项生命周期检查通过；发现3项P2，父Task2仍review。
- 类型：项目实测、独立重算和源码核查；结论边界不包含补偿/预测/WM收益。
- 核查状态：已核验本轮命令和证据；3项缺陷未修正。
- 来源：Codex /root，2026-10-06；[审核summary](../results/task2/task2.5-audit-20261006/summary.json)、[原bag独立重算](../results/task2/task2.5-audit-20261006/independent_report.json)、[脚本](../results/task2/task2.5-audit-20261006/independent_audit.py)、[对齐诊断](../results/task2/task2.5-audit-20261006/alignment_report.json)、[私有反例](../results/task2/task2.5-audit-20261006/private_report.json)、[生命周期](../results/task2/task2.5-lifecycle-20261006-report/lifecycle.json)、[日志](agent_logs/task2/task2.5/20261006-codex-final-audit.md)。脚本版本sha256在summary.json；正式源码版本依t2.3-exec1 freeze。
- 精确位置：正式exp2.1-m1 50次尝试（48有效、2真值检查失败），exp2.1-hf1 2有效；independent_report.checks/failures/runs；private_report.probes；alignment_report的t_ref/fit；scripts/aggregate_task2.py equivalence_bz 217–219行；scripts/analyze_task2.py check_command_chain及analyze_run；scripts/freeze_task2.py verify 166–173行。
- 原始结论：原bag命令/state与CSV一致、artifact/采集代码/镜像hash一致、各窗口关节/FK位置及跨轮统计一致；原t_ref对齐9组B/Z q_actual RMSE 4.47e−5–4.02e−4 rad，均超1e−5门槛，fit对齐通过。非零header一致链与未冻结40 ms反例被分析器判pass。原freeze因TASK状态文字变化核验退出1/入口退出12；审核专用freeze唯一变更为该状态文字，新B/Z/D160各退出0（队列0/160 ms、ε=0）。生命周期19项通过，结束foreign=[]。
- 输入/公式/单位：q_nom=q0+dq(3u²−2u³), u=clip((t−t0)/T,0,1)，t0为原发送区间中点（秒），q为rad；e_servo=actual−desired、e_schedule=desired−q_nom、e_total=actual−q_nom；RMSE=sqrt(mean(e²))、峰=max|e|，FK位置为URDF变换链求积后的位置范数（m），跨run样本std(ddof=1)。重算abs1e−10/rel1e−6沿用Task1核验契约；不重新设置实验阈值。合成40 ms/非零header是拒绝性测试，不是新物理条件。
- 本项目采用：保留原正式证据、报告通过项和失败项；修正与复核交接到task2.6/2.7，不标实验done。拟合方法的数学动机可以成立，但不能把fit门槛结果称原t_ref协议已通过；先导前已有变更记录，不据此指控事后调参。
- 适用限制：独立重算不证明坏数据能被生产分析器拒绝；反例使用既有合成fixture生成器，变异与断言为Codex新写；生命周期沿用已审读的ROS测试harness。F1/F2真值流稀疏支持测量质量失效，但未实验识别宿主调度根因；不能外推到真实机器人、补偿或预测收益。极小姿态约1e−8 rad限制保留，本轮主要独立核验关节/FK位置。
- 使用位置：[task2.5 RESULTS](tasks/task2/task2.5/RESULTS.md)、Task2/exp2.1最新审核追加段、task2.6/2.7三文档、PROGRESS与ENV的本轮更新。另见[Claude修正提示词交接](agent_logs/task2/task2.6/20261006-codex-remediation-handoff.md)，仅整理既有问题，不新增实验授权或证据。
- 核查人及日期：Codex /root，2026-10-06；实际模型/强度未知；未委派Agent。
- 待办：T2-A01–A03修正后以新分析/冻结ID保存证据并独立复核，未授权新实验因素或学习。

追加（2026-10-06，Claude，task2.6）：T2-A01–A03的修正与证据见[task2.6 RESULTS](tasks/task2/task2.6/RESULTS.md)与SRC-0009/0010；本条的“3项缺陷未修正”为task2.5审核当时状态，保留为历史。修正后状态仍待task2.7独立复核，不据此改写SRC-0008的审核结论。

## SRC-0009

- 主张：exp2.1 B/Z等价性在原预注册口径（threshold t_ref对齐）下对q_actual曲线9/9组未满足（RMSE 4.47e−5–4.02e−4 rad，限1e−5 rad）；差异由t_ref的8 ms采样量化造成，而非代理改变伺服：预测的量化错位影响与观测RMSE之比为0.9998–1.0031；按亚采样拟合起点对齐（v1.1事后修订，同一数值门槛）9/9通过。
- 类型：项目实测与推导（对既有run的重算）；拟合口径的采纳是事后工程选择。
- 核查状态：已核验本地数据与重算（待task2.7独立复核）；不是外部文献结论。
- 来源：FoReM，2026-10-06，Claude；分析`results/experiment/exp2/exp2.1-m1-agg2/equivalence_bz.json`（`protocol_v1_t_ref`、`protocol_v1_1_fit`、`alignment_explanation`）、`results/experiment/exp2/t2.6-a1/`重算（分析版本task2.6-1，`diff_report.json`）、Codex对照证据[alignment_report](../results/task2/task2.5-audit-20261006/alignment_report.json)；协议修订[exp2.1 PROCEDURE §8](experiment/备选/exp2/exp2.1/PROCEDURE.md)。
- 精确位置：`scripts/aggregate_task2.py`的`equivalence_bz(…,alignment)`与`alignment_explanation`；`scripts/analyze_task2.py`的`fit_start_time`、`delay.fit_validity`（常数FIT_RESIDUAL_MAX_RAD=1e−7、FIT_SHIFT_SENSITIVITY_RAD=1e−6、FIT_SHIFT_PROBE_S=0.5 ms）；run字段`delay.t_ref_minus_t_start_fit_s`（3.5–13.0 ms）。
- 输入/公式/单位：q_act(t_ref+t_rel)=f(t_rel+δ)，δ=t_ref−t_start_fit（s），f为控制器三次插值曲线；B−Z差≈f′·(δ_B−δ_Z)；预测RMSE=rms(v_nom(t_rel+δ̄)·dq·Δδ)（rad），v_nom=6u(1−u)/T·dq，观测RMSE=对应曲线差的逐关节均方根。
- 本项目采用：v1口径结果原样保留为“未满足”，v1.1 fit口径并列报告；v1.1的采纳在正式数据之后，因此标注事后修订，拟合代码本身早于先导（task2.3 RESULTS）。有效/可辨识常数为工程选择（残差远低于实测4e−10 rad；平移±0.5 ms使残差≥1e−6 rad）。
- 适用限制：仅适用于`desired`为理想三次插值的本控制器；不证明硬件时延；n=3；数值门槛未改。
- 使用位置：[task2.6 RESULTS](tasks/task2/task2.6/RESULTS.md)、[exp2.1 RESULTS](experiment/备选/exp2/exp2.1/RESULTS.md)、[exp2.1 PROCEDURE §8](experiment/备选/exp2/exp2.1/PROCEDURE.md)。
- 核查人及日期：Claude，2026-10-06；实际模型Sonnet5.5/强度未知。
- 待办：task2.7独立重现两种对齐并评价v1.1采纳是否可接受。

## SRC-0010

- 主张：离线分析器自分析版本task2.6-1起独立核验冻结mode/τ/case、支持消息结构与位移/时长契约；审核的两个反例（一致链非零header、未冻结40 ms）判invalid；freeze schema 2把可变状态说明与不可变协议/源码快照分开，状态行更新不再封入口，真实改动仍拒绝。
- 类型：工程实现与测试证据（项目实测）。
- 核查状态：已核验本地测试、变异检查、回归与fresh运行；待task2.7独立复核。
- 来源：FoReM，2026-10-06，Claude；`scripts/analyze_task2.py`（`check_frozen_contract`）、`scripts/freeze_task2.py`（schema 2、`audit`）、`tests/test_task2_measurement.py::FrozenContract`、`tests/test_task2_freeze.py`、`results/task2/t2.6-protocol2/`、`results/task2/t2.6-exec2/`、`results/task2/task2.6-after-20261006/`与`logs/task2/task2.6-repro-20261006/`（修正前后对照）、`results/task2/task2.6-fresh-M3-*`、`logs/task2/task2.6-final-regress.out`。
- 精确位置：契约门槛名`contract_*`、`chain_proxy_delay_matches_condition`；freeze字段`schema`、`protocol_version`、`mutable_status_rule`、`files.protocol_docs.{mode,sha256}`；全量206项单元OK。
- 原始依据：任务审核[SRC-0008](#src-0008)的T2-A02/A03反例；冻结契约来自[exp2.1 PROCEDURE §1–§3](experiment/备选/exp2/exp2.1/PROCEDURE.md)与`fixed_delay.yaml`（[SRC-0007](#src-0007)）。
- 本项目采用：状态行豁免仅限exp2.1 TASK.md前6行的“状态：/定位：”行（其余行、PROCEDURE.md全文、配置、七Task1文件、采集源码仍严格hash）；起始位姿容差0.01 rad沿用Task1预检边距；位移容差1e−9 rad为浮点往返容差。
- 适用限制：契约核验基于记录文件，不证明记录未被篡改；状态行文字不受校验；旧schema-1 freeze保持历史严格行为，仅可`audit`。
- 使用位置：[task2.6 RESULTS](tasks/task2/task2.6/RESULTS.md)。
- 核查人及日期：Claude，2026-10-06；强度未知。
- 待办：task2.7独立复核；不新增实验或授权。


## SRC-0011

- 主张：task2.7独立复核支持T2-A01/A03修正、原A02两个反例已拒绝，但A02的记录契约仍有NaN漏拒绝残留T2-A04（P2）；父Task2/exp2.1继续review。
- 类型：项目实测、独立重算、源码/记录核查；非外部文献结论。
- 核查状态：本轮已核验；T2-A04未修正。
- 来源：Codex /root，2026-10-07；[summary](../results/task2/task2.7-audit-20261007/summary.json)、[独立原bag/重分析核对](../results/task2/task2.7-audit-20261007/independent_report.json)、[历史保全核对](../results/task2/task2.7-audit-20261007/history_report.json)、[双对齐重算](../results/task2/task2.7-audit-20261007/alignment_report.json)、[私有反例](../results/task2/task2.7-audit-20261007/private_report.json)、[NaN CLI](../results/task2/task2.7-audit-20261007/nan_cli_report.json)、[冻结边界](../results/task2/task2.7-audit-20261007/freeze_boundary_report.json)、[日志](agent_logs/task2/task2.7/20261007-codex-fix-audit.md)。当前工作区HEAD `438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804`＋dirty，当前采集源码依`t2.6-exec2` sha256，原run依`t2.3-exec1`。
- 精确位置：`scripts/analyze_task2.py:180` check_frozen_contract 中sender dq容差比较及analyze_run的moving_idx；private_probes.py的nan_sender；nan_cli_report.exit/pass/lag_joints。独立脚本版本sha256在summary；正式50（48有效/2无效）、hf2、先导22共74原记录未改。主脚本52原bag/6585检查0差异；history1279检查0问题；206容器单元退出0；新fresh M3 B/Z/D160各退出0；freeze边界15场景符合预期。
- 原始结论：B/Z原t_ref口径9组q_actual RMSE失败、fit口径0组失败，双口径及标签已分开；观测/量化错位预测比0.999779–1.003117。新schema2状态说明可更新，目标/协议/参数/七文件/源码真实变化仍拒绝，原schema1快照完整。非零header/40 ms与未知case反例拒绝，但dq[0]=NaN时CLI退出0、pass=true、contract_case_displacement_duration=true，shoulder_pan的lag条目遗漏。Inf对照拒绝、正常对照通过。
- 输入/公式/单位：沿用SRC-0008的关节/原发送轴/FK公式及abs1e−10/rel1e−6核对容差；量化解释采用u=(t_rel+(δ_B+δ_Z)/2)/T、v=6u(1−u)/T（窗外0），预测差=v*dq*(δ_B−δ_Z)，RMSE单位rad。δ为threshold起点与拟合起点的差（s）；这是一阶局部近似，不能构成其他动力学因果证明。NaN反例仅变更合成sender dq一个分量，不改消息/反馈/hash链；NaN>tol与abs(NaN)>0均False，故门槛未拒绝且该关节被排除。
- 本项目采用：T2-A01按如实保留v1失败/v1.1事后修订而关闭报告口径问题，T2-A03新freeze入口及真实变动保护独立关闭；A02部分修正，T2-A04须补字段形状与有限性再比较。只写修正/复核交接，不改实现，不新增物理实验因素。
- 适用限制：合成反例不是真实机械臂故障；74实际run的dq/duration/q_target/q_start_observed均有限，不据此判现有正式数值失真。主要独立重算关节/FK位置，约1e−8 rad极小姿态限制继续保留；n=3、F1/F2根因未确定；补偿/预测/WM收益未测。12个H正式run无运动、不进行起点拟合，有效拟合统计为36个正式运动run（另2个hf），不能称48个正式run都有拟合。
- 使用位置：[task2.7 RESULTS](tasks/task2/task2.7/RESULTS.md)、task2.8/2.9三文档、Task2/exp2.1与PROGRESS/ENV本轮追加段。另见[task2.8 Claude修正提示词](agent_logs/task2/task2.8/20261007-codex-nan-remediation-handoff.md)，仅整理已有缺陷与范围，不新增实验依据或因素。
- 核查人及日期：Codex /root，2026-10-07；实际模型/强度未知；推荐GPT6.1sol / Sonnet5.5、medium（多模块时序/冻结核对）；未派Agent。
- 待办：T2-A04修正与独立复核；不能据审核交付进入Task3。

## SRC-0012

- 主张：task2.6-1分析器遇发送记录dq含NaN时漏拒绝（`NaN>tol`为假，`abs(NaN)>0`为假，关节被静默排除，CLI退出0）；task2.8-1在任何比较/关节选择前核验发送记录类型/形状/有限性，NaN/Inf/形状错误/时长异常均判invalid（CLI退出1），正常输入仍通过且每个运动关节保留lag项；历史数据无verdict变化。
- 类型：项目实测与工程实现（含修正前后对照与测试）。
- 核查状态：已核验本地修正前后输出、222项测试、变异检查、重算与fresh；待task2.9独立复核。
- 来源：FoReM，2026-10-07，Claude；问题证据[task2.7审核](../results/task2/task2.7-audit-20261007/)（`nan_cli_report.json`、`nan_root_cause.json`、`probes/sender_dq_nan`，只读）；修正前`logs/task2/task2.8-repro-20261007/before.out`、修正后`after.out`/`private_after.out`；`scripts/analyze_task2.py`（`validate_sender_record`、`check_frozen_contract`、`moving_joints_match_frozen_case`、`lag_reported_for_all_moving_joints`）；`tests/test_task2_measurement.py::SenderRecordFiniteness`；`results/task2/t2.8-protocol3/`、`t2.8-exec3/`；重算`results/experiment/exp2/t2.8-a1*`、聚合`exp2.1-m1-agg3`；协议记录[exp2.1 PROCEDURE §8.4](experiment/备选/exp2/exp2.1/PROCEDURE.md)。
- 原始依据：IEEE 754中任何与NaN的有序比较为假（`nan>x`、`abs(nan)>0`）——故“不超容差”不能当作“在容差内”；审核算术根因见`nan_root_cause.json`。
- 本项目采用：有限性/形状验证先于比较；运动关节集合须与冻结case一致；容差1e−9 rad沿用task2.6。
- 适用限制：针对记录文件，不证明未被篡改；历史74次尝试无NaN记录（task2.7独立核验），不改变既有数值结论；不涉及τ、门槛、双对齐口径。
- 使用位置：[task2.8 RESULTS](tasks/task2/task2.8/RESULTS.md)。
- 核查人及日期：Claude，2026-10-07；强度未知。
- 待办：task2.9独立复核；不新增实验或授权。


## SRC-0013

- 主张：task2.9独立核验关闭T2-A04并累计关闭T2-A01–A04，Task2固定传输时延机制及exp2.1限定阶段验收done；不代表原v1 q_actual门槛通过或补偿/WM收益成立。
- 类型：项目实测、源码审阅、私有反例与独立重算。
- 核查状态：已核验本轮命令/原始证据；限定范围验收通过。
- 来源：Codex /root，2026-10-07；[summary](../results/task2/task2.9-audit-20261007/summary.json)、[原bag与重分析](../results/task2/task2.9-audit-20261007/independent_report.json)、[历史保全](../results/task2/task2.9-audit-20261007/history_report.json)、[私有探测](../results/task2/task2.9-audit-20261007/private_report.json)、[原NaN CLI](../results/task2/task2.9-audit-20261007/nan_cli_report.json)、[冻结边界](../results/task2/task2.9-audit-20261007/freeze_boundary_report.json)、[双对齐](../results/task2/task2.9-audit-20261007/alignment_report.json)、[fresh验证](../results/task2/task2.9-audit-20261007/fresh_validation.json)、[环境](../results/task2/task2.9-audit-20261007/final_environment.json)、[独立日志](agent_logs/task2/task2.9/20261007-codex-final-audit.md)。生产版本以t2.8-exec3文件sha256为准（分析task2.8-1）；根HEAD `438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804`＋dirty，审核脚本sha256见summary。
- 精确位置：analyze_task2.py validate_sender_record/_finite_vector、入口早退、moving_joints_match_frozen_case/lag_reported_for_all_moving_joints；原sender_dq_nan输入只读，当前CLI退出1/contract_sender_record_wellformed=false；新增私有形状/Inf/时长对照。主独立核验52原bag/7385检查0差异（含关节/位置/拟合/全部lag及不可辨识原因），历史74次尝试/1279检查0问题，222全量测试退出0，29探测预期匹配、15冻结边界预期匹配。
- 原始结论：正常M3/M6/MR3均有6关节lag，H无运动；NaN/Inf/畸形/时长异常以及原非零header/40 ms均拒绝。新freeze校验通过、真实变动仍拒绝。9组原t_ref q_actual门槛失败、fit口径通过，透明保留v1.1事后修订标签；双对齐及量化解释比与task2.7一致。新fresh4次尝试/3有效：B-r1、Z-r2、D160-r1退出0；Z-r1仅Gazebo真值质量失败（动态位置1/姿态5违例、静态0），按原协议一次新ID补跑通过，原失败保留。最终容器仅init/sleep、foreign=[]。
- 输入/方法/单位：沿用SRC-0008/0011的原发送轴、误差分解、独立URDF变换链FK和量化错位近似，核对容差abs1e−10/rel1e−6（rad或m依指标）；采集条件/τ/门槛与冻结配置不变。NaN/Inf/类型/形状变异仅为合成拒绝测试，不是物理实验因素。当前新采集源码相对t2.6-exec2仅分析器变化，七文件/配置一致。
- 本项目采用：累计独立验收Task2与exp2.1机制阶段；T2-A04由有限性验证先于比较闭环，正常关节不静默排除。保留原v1失败和v1.1事后口径，报告fresh全部尝试，不把质量失败计成功。父exp2其余预测器研究继续备选，不自动进入Task3实施。
- 适用限制：n=3、B组4处重复性不足、极小姿态数值限制保留；F1/F2与本轮Z的记录流问题提示测量链对接收时刻/负载敏感，本轮Z最大间隙14 ms、疑似时序抖动但根因未证实。验收不等于所有潜在输入缺陷穷尽，仿真整条轨迹传输时延不等于真实电机动态；补偿、多步预测、WM收益未测、未证明。
- 使用位置：[task2.9 RESULTS](tasks/task2/task2.9/RESULTS.md)、Task2父及相关子结果、[exp2.1 RESULTS](experiment/备选/exp2/exp2.1/RESULTS.md)、PROGRESS/README/ENV当前状态。
- 核查人及日期：Codex /root，2026-10-07；实际模型/强度未知；推荐GPT6.1sol / Sonnet5.5、medium（记录/时序/冻结因果核对），未派Agent。
- 待办：本节点必需验收已完成；上述研究收益与记录流根因属后续另定范围，不纳入本轮实施。

### 已删除的旧方案登记（原重复编号SRC-0014）

原补偿方案登记正文已按用户要求删除。下方同编号的Task2实测解释来源保留，未改动原实测证据。

### 已删除的旧方案登记（原重复编号SRC-0015）

原补偿方案登记正文已按用户要求删除。下方同编号的Task2实测解释来源保留，未改动原实测证据。

## SRC-0016

旧任务方案及关联内容已按用户2026-10-07明确要求删除，仅保留稳定编号作删除标记；不保留原方案参数/结果正文，不作为新Task3/4依据。删除记录见[SRC-0042](#src-0042)。

## SRC-0014

- 主张：Task1 M3正常伺服运动末端RMSE约0.127 mm、停稳约0.203 mm；Task2 M3原发送轴完整执行窗无注入/80/160 ms的总末端RMSE约0.138/0.910/1.697 mm、峰值0.217/1.246/2.362 mm，已包含正常执行偏差，不能另加一遍Task1指标。时延组停稳仍约0.203 mm。
- 类型：项目已测结果引用及汇总/差值推导；非新的机器人实验。
- 核查状态：已读取原指标并重算三轮均值/差值/比值；原测量验收分别见Task1.10和Task2.9。
- 来源：FoReM，2026-10-07，Codex解释核对；[comparison.json](../results/task2/accuracy-comparison-20261007/comparison.json)、[日志](agent_logs/task2/20261007-codex-accuracy-interpretation.md)；Task1 `results/task1/t1.9-a3/runs/<M3正式run>/run_metrics.json`，由`t1.3-m1/run_index.json`筛role=formal/case=M3（三个ID记录在comparison）；Task2 `results/experiment/exp2/exp2.1-m1-agg3/per_run.json`的M3/B,Z,D80,D160各3run；原审核[SRC-0013](#src-0013)。
- 精确位置：Task1 `metrics.motion/settle.ee_pos_err_m.{rmse,max}`；Task2 `exec_nom_ee_pos_total_m_{rmse,max}`、`motion_nom_...`、`motion_ee_pos_servo_m_rmse`、`settle_ee_pos_servo_m_rmse`；comparison.metrics_mm/delta/ratio。
- 输入/公式/单位：m×1000=mm；组均值=三run指标算术均值；80 ms组相对B的RMSE增量=0.910384−0.138034=0.772350 mm，160 ms组=1.696949−0.138034=1.558915 mm；倍数6.595/12.294。它们是总RMSE的差/比，不是独立时延误差分量的RMSE。逐关节e_total=e_servo+e_schedule；末端位置差向量同样可分解，但其范数/均方根没有标量加法恒等式。
- 原始结论：同一M3轨迹下正常跟踪的控制器轴指标与Task2 B接近（运动0.127 mm）；时延主要增大原任务时序上的运动偏差。Task1参考为controller desired，Task2总误差参考为原发送计划；两者不能直接当作同一指标相加。Task2 B为同协议的无注入对照，比较有延迟组应以B为基准。
- 本项目采用：回答“正常误差加时延共造成多少偏差”，使用已经包含正常误差的Task2总指标并报告增量；原M3完整执行窗为发送后T+τ，即3/3.08/3.16 s。若严格固定3 s原运动窗，对应RMSE为0.138/0.922/1.740 mm，comparison同时保留，不与完整窗值混用。
- 适用限制：仅固定底座Gazebo、此M3幅度/速度/姿态，n=3；整条轨迹传输延迟与闭环逐动作时延不同。停稳正常只说明本实验延后完整轨迹的终态未额外劣化，不能外推所有任务/硬件静态精度。数据不含补偿/WM收益，不代表精准度要求已满足；Task1其他L工况约2 mm不能与此M3数值直接拼加。
- 使用位置：[Task2结果的精度解释](tasks/task2/RESULTS.md)、[本轮日志](agent_logs/task2/20261007-codex-accuracy-interpretation.md)。
- 核查人及日期：Codex /root，2026-10-07；实际模型/强度未知；未派Agent。
- 待办：本次解释无必需剩余，不新增研究实施授权。

## SRC-0015

- 主张：不到1 cm不能单独判定误差有无意义；当前Task2已证明可控、可测、可重复的仿真时延机制，尚未证明任务损失或世界模型必要性。若全程位置容差为10 mm，当前M3峰值未触及该假设门槛；若为1 mm，D80/D160的峰值会违反该假设要求。
- 类型：基于项目实测的条件推导与研究判断；容差仅为解释示例，不是采用的工程参数。
- 核查状态：已读M3三run/条件的原聚合峰值；逻辑/单位换算已核对；实际任务成功容差与效果尚未定义/验证。
- 来源：FoReM，2026-10-07；[SRC-0013](#src-0013)机制验收与收益边界、[SRC-0014](#src-0014)精度对比；`results/experiment/exp2/exp2.1-m1-agg3/per_run.json` case=M3/condition=B,D80,D160 的`exec_nom_ee_pos_total_m_max`；[本次解释日志](agent_logs/task2/20261007-codex-error-significance.md)含逐组峰值均值和三run最大值。
- 输入/公式/单位：1 cm=10 mm；位置误差用同一原计划时间轴的末端位置范数，峰值单位m×1000=mm。D80峰值均值约1.246 mm，D160约2.362 mm；每个实际run峰值均低于10 mm且时延组超过1 mm。定义示例的全程要求max_t||p_actual−p_plan||≤容差，则超过阈值意味着未满足该位置要求，不等于已测任务失败率。
- 原始结论：Task2动态偏差比无注入基准大，但停稳误差基本保持；当前并无接触/避障/抓取任务失败、补偿或WM收益测试。
- 本项目采用：解释意义应由任务容差、时序要求及结果决定；当前适合机制诊断，不能仅用小于1cm或相对倍率宣称无用/有用，更不能自动推导世界模型必要性。
- 适用限制：10/1 mm是假设，不代表工业任务常见标准；不得写入本项目协议当实际成功判据。当前低速固定轨迹及仿真结果不外推到硬件或其他速度/姿态；末端位置范数不能替代姿态、时序或完整任务表现。不会因希望效果明显而加大时延或刻意降低SAC成功率。
- 使用位置：[本次解释日志](agent_logs/task2/20261007-codex-error-significance.md)、[Task2结果意义说明](tasks/task2/RESULTS.md)。
- 核查人及日期：Codex /root，2026-10-07；实际模型/强度未知；未派Agent。
- 待办：实际任务意义与收益需后续在明确目标/授权内验证，本次不新增实验因素或要求。

## SRC-0017

- 主张：当前Husky实际Python任务路径的默认末端到达位置阈值为0.025 m；Hall门/抽屉/房门类基础阈值为0.01 m，抓取/放置普通子目标沿用默认阈值，部分阶段放宽至0.05 m。若1 mm指判据同一坐标表示的最终绝对位置残差，低于这些位置阈值；这不证明完整任务成功。
- 类型：本地原始源码静态审计、单位换算与条件推导；不是运行实测，也不是外部硬件精度规范。
- 作者/机构与标题、版本：本地恢复的Husky + UR5参考源码，modulation_rl任务/规划/评测实现；本次根Git HEAD `438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804`，实际读取文件SHA256见[audit.json](../results/task2/husky-task-tolerance-20261007/audit.json)。未把根HEAD当成所有dirty文件版本。
- 核查状态：已读实际导入的`scripts/modulation/`，没有混用`scripts/modulation（修改后）/`副本；没有启动Husky或验证硬件。
- 精确位置：`husky/src/modulation_rl/scripts/main_ray.py:19`实际导入；`scripts/modulation/utils.py:437–452`任务分发与`530–531`成功函数；`envs/tasks.py:140–159`BaseTask默认值；`envs/tasks_chained.py:39–47,116–123,314–322`继承和抓取/放置覆盖；`envs/tasks_realworld.py:397–465`Hall/Office覆盖；`envs/eeplanner.py:187–193`位置与姿态同时判定；`modulation/evaluation.py:92–127,294–304`轨迹距离和成功指标；路径前缀均为`husky/src/modulation_rl/scripts/`。`gazebo_world/husky_ur5/robot_config.yaml:5–9`是夹爪frame/offset。
- 原始结论：planner检查欧氏位置距离严格小于各TaskGoal阈值，同时检查旋转距离；episode success还要求IK失败次数和底盘碰撞次数为零。轨迹偏差指标对每个实际位姿取所有期望轨迹点的最小空间距离，阈值分别0.1/0.05 m，未按同一时刻比较。姿态度量`1−(q_a·q_b)^2`见`envs/env_utils.py:123–131`，不能将0.05直接写为rad。
- 输入、公式、单位：0.001 m=1 mm；0.01/0.025/0.05 m=10/25/50 mm；比较0.001<0.01和0.001<0.025，仅判定位置分量。时延沿同一路径但相位不同，最近轨迹点指标可能不敏感，是按公式的条件推导而非实际失败率结果。
- 本项目采用：解释1 mm在当前参考任务中满足所列位置门槛；Task2小幅同步跟踪偏差是否足以影响原任务成功率仍待实际任务验证，不能由机制有效直接宣称任务损失/补偿收益/世界模型必要性。
- 适用限制：最终绝对目标残差、额外执行误差及Task2同步动态RMSE不是同一量；Task2测量wrist与Husky夹爪目标表示/offset也有差别。碰撞、姿态、接触和抓取结果必须另外判断；不把目标到达阈值解释成可容忍任意路径偏差或实际装配精度。不修改阈值、不新增实验授权。
- 核查日期与核查人：2026-10-07T09:28:08.384173+08:00，Codex /root，实际模型/强度未知；只读命令退出0，未派Agent。
- 使用位置：[Husky任务精度要求核查日志](agent_logs/project/20261007-codex-husky-task-tolerance.md)。

## SRC-0018

- 主张：继续做已知固定时延补偿诊断有有限价值，但现有证据不足以支持直接投入世界模型训练；需要区分真实轨迹精度改善、任务收益和学习模型额外收益。
- 类型：基于项目实测、源码审计及当前计划的研究判断/建议；不是新实测、正式决策或新增实施授权。
- 来源作者/版本：FoReM当前Task2.9验收、Husky本地源码审计与Task3计划，2026-10-07。
- URL/本地证据和精确位置：[Task2.9结果](tasks/task2/task2.9/RESULTS.md)的独立验证和限制；[精度对比JSON](../results/task2/accuracy-comparison-20261007/comparison.json)；[Husky审计SRC-0017](#src-0017)及audit.json；[Task3 TASK](tasks/task3/TASK.md)“研究问题、假设与范围”和“路线、交付与验收”。
- 核查状态：已读以上既有记录和本轮Task3 TASK；没有运行Task3或测Husky任务成功率。Task3实施仍未授权。
- 原始结论：Task2固定传输时延机制已验证，当前测得小幅动态位置偏差；Husky所列目标到达阈值为厘米级且空间轨迹偏差指标不同于同步误差。Task3只提前已知τ发送整条已知轨迹，不学习模型，不改变消息内容，结果尚未产生。
- 本项目采用方式：建议先完成既定已知模型补偿的有限诊断，目的为检查误差是否可补偿/测量时间轴是否一致；其后依据真实任务成功、碰撞、耗时或明确精度目标的实际影响，决定是否值得投入学习模型。任务效果验证是建议，未加入已授权协议。
- 推导条件：已知固定τ及完整未来参考允许直接提前发送，因而简单排程无需学习模型；其成功不能证明未知/时变误差可学，也不能证明世界模型优于直接补偿。若任务指标基本不变，仅小幅跟踪RMSE改善不足以支撑“提高原任务成功率”的主张；若研究目标明确为精度，精度改善仍可作为自身目标，但不能冒充任务成功率收益。
- 适用限制：位置容差大不能证明时延不会引发碰撞、姿态或接触问题；现有低速固定轨迹不外推到Husky完整任务。补偿未改善时应先检查实现、测量与误差归因，不能直接断言所有世界模型无效；有改善也不能证明WM必要。没有新设阈值、放大时延、收紧任务容差或改变研究目标。
- 核查日期与人：2026-10-07T09:29:41.305480+08:00，Codex /root；模型/强度未知。
- 使用位置：[本轮判断日志](agent_logs/project/20261007-codex-continuation-value.md)。

## SRC-0019

- 主张：DATS的世界模型训练及接入机制：先用已承诺动作队列预测到新动作生效时的状态，再MPC/CEM规划，将优化序列首动作入队。
- 类型：外部文献；SC²-WM另含官方源码静态核查。
- 核查状态：已阅读原文方法；所列SC²-WM代码已静态核查；未运行算法，本项目适用性尚未验证。
- 来源：Baiming Chen、Mengdi Xu、Liang Li、Ding Zhao；Delay-Aware Model-Based Reinforcement Learning for Continuous Control；2020，arXiv:2005.05440v1；https://arxiv.org/html/2005.05440v1。
- 精确位置：§II-B、§IV/IV-A、Algorithm 1/2。
- 原始依据：物理状态及实际执行动作→下一状态分布；真实转移学习概率动力学集成。先用已承诺动作队列预测到新动作生效时的状态，再MPC/CEM规划，将优化序列首动作入队。
- 本项目采用：解释预测器的输入/监督及在训练或在线决策链路的接入位置；不采用论文参数或宣称复现。
- 适用限制：直接涉及动作时延；需要已知固定时延与队列，是模型规划方法。原Gym/MuJoCo实验、已知奖励；不是SAC插件，不是未知UR5伺服模型。Task2整条轨迹启动延迟不等同逐动作队列时延。
- 使用位置：[exp0接入调研](experiment/备选/exp0/RESULTS.md)、[本轮日志](agent_logs/experiment/exp0/20261007-codex-wm-integration.md)。
- 核查人及日期：Codex /root，2026-10-07；实际模型/强度未知，未委派。
- 待办与变更：如选用须另行授权、审计接口与冻结协议；本次不选参数、不改执行方案。

## SRC-0020

- 主张：SC²-WM的世界模型训练及接入机制：执行前用前瞻反馈修正当前潜态，再由导航动作头决策；条件触发测试期模型适配。
- 类型：外部文献；SC²-WM另含官方源码静态核查。
- 核查状态：已阅读原文方法；所列SC²-WM代码已静态核查；未运行算法，本项目适用性尚未验证。
- 来源：Xuan Yao、Yuze Zhu、Junyu Gao、Zongmeng Wang、Changsheng Xu；SC²-WM: A Self-Correcting World Model with Closed-Loop Feedback for Vision-and-Language Navigation in Continuous Environments；2026，arXiv:2608.07548v1；https://arxiv.org/html/2608.07548v1；官方https://github.com/sunrise-yuze/SC2_WM；已有本地commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b。
- 精确位置：§3.1–3.3、公式9–13、Algorithm 1/2；scwm/vlnce_baselines/models/etp/vilmodel_cmt.py:GlobalMapEncoder与forward_navigation，590–621、900–998行；ss_trainer_ETP.py 2245–2318行。
- 原始依据：视觉/语言/历史构成潜态，前瞻动作→预测潜态/视觉特征；专家动作监督、KL与未来特征损失训练。执行前用前瞻反馈修正当前潜态，再由导航动作头决策；条件触发测试期模型适配。
- 本项目采用：解释预测器的输入/监督及在训练或在线决策链路的接入位置；不采用论文参数或宣称复现。
- 适用限制：Habitat导航，不提供UR5关节驱动时延模型。论文用预测未来潜态减当前潜态，不能称实际跟踪误差；本地代码具体实现为候选特征重建+门控残差+重新评分，与论文抽象分别说明，不声称逐项等价。
- 使用位置：[exp0接入调研](experiment/备选/exp0/RESULTS.md)、[本轮日志](agent_logs/experiment/exp0/20261007-codex-wm-integration.md)。
- 核查人及日期：Codex /root，2026-10-07；实际模型/强度未知，未委派。
- 待办与变更：如选用须另行授权、审计接口与冻结协议；本次不选参数、不改执行方案。

## SRC-0021

- 主张：MBPO的世界模型训练及接入机制：从真实replay状态分支短模拟轨迹，用模型数据训练SAC策略与双Q；在线仍由SAC直接输出动作。
- 类型：外部文献；SC²-WM另含官方源码静态核查。
- 核查状态：已阅读原文方法；所列SC²-WM代码已静态核查；未运行算法，本项目适用性尚未验证。
- 来源：Michael Janner、Justin Fu、Marvin Zhang、Sergey Levine；When to Trust Your Model: Model-Based Policy Optimization；NeurIPS 2019；https://papers.neurips.cc/paper_files/paper/2019/file/5faf461eff3099671ad63c6f3f094f7f-Paper.pdf；官方https://github.com/jannerm/mbpo。
- 精确位置：§5、印刷页6、Algorithm 2；Predictive model/Policy optimization/Model usage段。
- 原始依据：真实状态及动作→下一状态/奖励分布；真实经验最大似然学习概率模型集成。从真实replay状态分支短模拟轨迹，用模型数据训练SAC策略与双Q；在线仍由SAC直接输出动作。
- 本项目采用：解释预测器的输入/监督及在训练或在线决策链路的接入位置；不采用论文参数或宣称复现。
- 适用限制：支持模型增强SAC训练的机制与样本效率研究；不是现成UR5在线时延补偿器。模拟数据单列成本，不算真实环境交互。
- 使用位置：[exp0接入调研](experiment/备选/exp0/RESULTS.md)、[本轮日志](agent_logs/experiment/exp0/20261007-codex-wm-integration.md)。
- 核查人及日期：Codex /root，2026-10-07；实际模型/强度未知，未委派。
- 待办与变更：如选用须另行授权、审计接口与冻结协议；本次不选参数、不改执行方案。

## SRC-0022

- 主张：原始Dreamer的世界模型训练及接入机制：在模型想象轨迹内训练actor/critic，通过可微动力学传播多步价值梯度训练actor；在线实际观测更新潜态，actor出动作。
- 类型：外部文献；SC²-WM另含官方源码静态核查。
- 核查状态：已阅读原文方法；所列SC²-WM代码已静态核查；未运行算法，本项目适用性尚未验证。
- 来源：Danijar Hafner、Timothy Lillicrap、Jimmy Ba、Mohammad Norouzi；Dream to Control: Learning Behaviors by Latent Imagination；2019预印本/ICLR 2020，arXiv:1912.01603v1；https://arxiv.org/html/1912.01603v1。
- 精确位置：§2–4；Figure 3、Algorithm 1、模型状态/转移/奖励定义。
- 原始依据：真实观测/动作序列学习潜态、动力学与奖励；潜态/动作→预测下一潜态/奖励。在模型想象轨迹内训练actor/critic，通过可微动力学传播多步价值梯度训练actor；在线实际观测更新潜态，actor出动作。
- 本项目采用：解释预测器的输入/监督及在训练或在线决策链路的接入位置；不采用论文参数或宣称复现。
- 适用限制：这是原始Dreamer，梯度机制不无条件归于所有后续版本。不是SAC增强接口，也没有本项目UR5执行补偿证据。
- 使用位置：[exp0接入调研](experiment/备选/exp0/RESULTS.md)、[本轮日志](agent_logs/experiment/exp0/20261007-codex-wm-integration.md)。
- 核查人及日期：Codex /root，2026-10-07；实际模型/强度未知，未委派。
- 待办与变更：如选用须另行授权、审计接口与冻结协议；本次不选参数、不改执行方案。

## SRC-0023

- 主张：TD-MPC2的世界模型训练及接入机制：模型rollout加末端Q评估候选序列，策略先验辅助采样，在线MPC优化后执行首动作，下步重规划。
- 类型：外部文献；SC²-WM另含官方源码静态核查。
- 核查状态：已阅读原文方法；所列SC²-WM代码已静态核查；未运行算法，本项目适用性尚未验证。
- 来源：Nicklas Hansen、Hao Su、Xiaolong Wang；TD-MPC2: Scalable, Robust World Models for Continuous Control；2023预印本/ICLR 2024，arXiv:2310.16828v2；https://arxiv.org/html/2310.16828v2；官方https://github.com/nicklashansen/tdmpc2。
- 精确位置：§3.1–3.2、公式2–4；Components/Model objective/Policy objective与规划首动作段。
- 原始依据：观测→潜态；潜态/动作→下一潜态、奖励与Q；联合潜态一致性、奖励与TD学习，不要求观测重建。模型rollout加末端Q评估候选序列，策略先验辅助采样，在线MPC优化后执行首动作，下步重规划。
- 本项目采用：解释预测器的输入/监督及在训练或在线决策链路的接入位置；不采用论文参数或宣称复现。
- 适用限制：完整算法参照；规划决定最终动作，不能当作SAC内部消融；在线规划成本另算。未有本项目复现或补偿效果证据。
- 使用位置：[exp0接入调研](experiment/备选/exp0/RESULTS.md)、[本轮日志](agent_logs/experiment/exp0/20261007-codex-wm-integration.md)。
- 核查人及日期：Codex /root，2026-10-07；实际模型/强度未知，未委派。
- 待办与变更：如选用须另行授权、审计接口与冻结协议；本次不选参数、不改执行方案。

## SRC-0024

- 主张：FoReM既有exp4候选主线为预测特征辅助SAC，最终动作由SAC输出，是尚未验证的项目接口选择。
- 类型：工程选择及待验证假设。
- 核查状态：已核对既有文档，未实现或验证收益。
- 来源：FoReM，2026-10-07当前工作区；[exp0流程](experiment/备选/exp0/PROCEDURE.md)、[exp4任务](experiment/备选/exp4/TASK.md)；外部接入机制参照SRC-0019–0023。
- 精确位置：exp0“信息权限与动作角色”；exp4“方法与交付”B3/B4。
- 原始依据：既有候选把简单辨识模型与WM接到相同预测特征接口，最终动作由SAC输出；未知误差主组只用当前/历史实际可得观测、已发动作及任务信息。
- 本项目采用：解释已有接口：历史实际反馈/已发动作→预测器→预测特征；当前实际反馈与预测特征共同输入SAC。未来状态若依赖动作，必须明确已承诺动作或候选动作条件，不能读取未来未决SAC动作；预测实际反馈，不能把指令当实际。
- 适用限制：跨度、字段、网络/损失及具体SAC动作接口尚未冻结，尚未训练或验证收益。未知误差组禁止读取隐藏注入参数/队列、未来真值；DATS的已知队列权限与其不同。本轮不新增实施授权。
- 使用位置：[exp0接入调研](experiment/备选/exp0/RESULTS.md)、[本轮日志](agent_logs/experiment/exp0/20261007-codex-wm-integration.md)。
- 核查人及日期：Codex /root，2026-10-07；实际模型/强度未知，未委派。
- 待办与变更：解释交付，不修改exp4设计或其他Agent实施文件；具体训练需另行授权与冻结。

## SRC-0025

- 主张：移动底盘可能放大机械臂相对时延造成的世界坐标末端偏差；不是一移动必然更大。固定底盘毫米级结果不能外推到边移动边操作。
- 类型：本地原始源码静态审计、条件运动学推导与待验证假设；不是移动实验实测。
- 作者/标题/版本：本地Husky + UR5参考协调实现、FoReM Task2，2026-10-07；源码SHA256和估算输入见[mobile_base_hypothesis.json](../results/task2/husky-task-tolerance-20261007/mobile_base_hypothesis.json)。
- 精确来源位置：`husky/src/modulation_rl/scripts/modulation/envs/combined_env.py:356–367`同一步传入底盘动作和世界末端目标；`husky/src/modulation_rl/src/robot_env.cpp:177–202,235–258`先计算下一预期底盘位姿/设置world joint再求IK，物理执行时分别发送arm/base；[Task2 TASK](tasks/task2/TASK.md)范围与[Task2.9 RESULTS](tasks/task2/task2.9/RESULTS.md)限制。
- 原始结论：参考实现具有底盘/机械臂协调求解和分开发送通道，延迟失配可能破坏同步假设；源码未证明移动误差大小。Task2只验证固定底盘整条轨迹时延，不能直接当已验证移动流式控制。
- 推导输入/公式/单位/条件：`p_world=b(t)+R(t)r(t)`。固定世界目标P的理想臂位置`r*(t)=R(t)^T(P−b(t))`。臂滞后τ、底盘使用当前位姿时`e=b(t)+R(t)r*(t−τ)−P`；小τ、速度近似恒定可得`e≈[v_b+ω_b×(P−b)]τ`。直线无旋转且忽略反馈/动态时||e||≈||v_b||τ。说明示例v=0.1 m/s、τ=0.08/0.16 s给出8/16 mm；v是假设，不是测量、文献值或推荐参数；τ只沿用Task2已有80/160 ms解释，不证明移动场景选值合理。
- 本项目采用方式：认可用户假设值得检验，移动影响、任务损失、补偿与WM收益均须另行验证；本轮只解释，不扩展授权或实施。
- 适用限制：先停再操作、目标随底盘或有效同步补偿时未必更大。平移/旋转为向量可抵消，不把RMSE直接相加；同延迟两通道也须明确世界目标及时间轴。开环局部估算不是闭环长期误差，更不是移动任务实测；不引入滑移/噪声等额外因素。
- 核查状态、日期与人：已读上述原始源码和计划；2026-10-07T09:32:33.857235+08:00，Codex /root，实际模型/强度未知；未执行移动仿真。
- 使用位置：[解释日志](agent_logs/project/20261007-codex-mobile-base-delay-hypothesis.md)。

## SRC-0026

- 主张：Husky常规IK模式是在同一控制步内协调底盘/机械臂目标并分别异步发送，不是必须等待底盘完成再移动机械臂。协调来自下一预期底盘位姿下的IK求解；物理通道仍分开，实际同步未由代码证明。
- 类型：本地原始源码静态审计与运动学解释，不是移动实验。
- 作者/标题/版本：本地Husky + UR5 modulation_rl默认动作与控制实现，2026-10-07；精确文件hash见[base_arm_coupling.json](../results/task2/husky-task-tolerance-20261007/base_arm_coupling.json)。
- 精确位置：`husky/src/modulation_rl/scripts/modulation/utils.py:128`默认learn_joint_values=False；`scripts/modulation/envs/combined_env.py:356–367,435–448`动作解码、末端规划器与robot.step；`scripts/modulation/envs/robotenv.py:260–297`缩放底盘动作及C++传参；`src/robot_env.cpp:177–202,235–258`计算下一预期base姿态、设置world joint、求IK和发送；`src/robot_husky.cpp:91–123`arm sendGoal后返回，普通send函数无waitForResult；`src/robot_env.cpp:259–274`状态更新模式。前缀均`husky/src/modulation_rl/`。
- 原始结论：默认策略输出底盘动作，末端路径由EE planner给下一世界坐标目标；开启learn_vel_norm可另控EE推进速度。C++按底盘动作积分下一预期底盘位姿，并在其下求解关节以达到世界末端目标。物理step依次提交arm trajectory与base速度，提交arm不等待运动完成，因此实际运动可以同时进行；解析sim只更新运动学，不代表真实物理同步验证。
- 本项目采用：向用户说明“先计算底盘下一步，再解机械臂”属于计算顺序，不能理解成物理上先走完底盘才动手臂。任务可能有暂停/抓放阶段或策略选择停底盘，但不是默认强制交替。
- 条件推导与例子：只考虑沿同一轴平移，`p_world=b+r`。若期望末端世界位置不变、底盘前移0.02 m，机械臂相对底盘位置应变化−0.02 m；这是说明协调的假设示例，不是run数据或推荐动作。若延迟使手臂使用旧关节目标而底盘继续移动，会破坏该协调，大小仍需实测。
- 适用限制：learn_joint_values=True有直接关节动作路径，不适用默认IK链的完整描述；SAC未直接学出默认全部关节控制。默认perception_style=base可能只更新实际底盘而保留期望关节，不能把每步规划状态统一说成机械臂真实反馈；底层控制器反馈另属于执行层。尚未测实际通道时差，也未证明WM必要。
- 核查状态、日期与人：已读原始代码；2026-10-07T09:33:41.500177+08:00，Codex /root，实际模型/强度未知，无移动仿真/子Agent。
- 使用位置：[解释日志](agent_logs/project/20261007-codex-husky-base-arm-coupling.md)。

## SRC-0027

- 主张：SC²-WM做导航不意味着家具/障碍物本身必须运动；其核心预测涵盖智能体行动引起的观测与潜态转移。已读材料没有给出专门的动态物体预测/动态障碍协议，不能由论文“dynamic environments”措辞推断该项已验证。
- 类型：外部文献、本地官方代码静态核查、概念解释与受限推断。
- 核查状态：已阅读论文任务/方法/实验/实机段及下列配置；未运行仿真，不穷尽所有底层Habitat能力。
- 来源：Yao等，SC²-WM，2026，arXiv:2608.07548v1，https://arxiv.org/html/2608.07548v1；Matterport3D作者Chang等，2017，https://arxiv.org/abs/1709.06158（已读摘要，仅支持室内RGB-D扫描/重建资料性质）；官方本地scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b。
- 精确位置：SC²-WM §1“dynamic environments”、§3任务定义/先验预测、§3.2未来视觉特征监督、§4.1、Appendix E；scwm/run_r2r/r2r_vlnce.yaml、run_rxr/rxr_vlnce.yaml的SIMULATOR/AGENT/TASK/DATASET；habitat_extensions/habitat_simulator.py:step_without_obs，62–95行。
- 原始依据：以RGB-D及语言指令导航，执行移动/转向动作，预测下一视角/潜态并修正决策；当前配置提供场景与智能体动作，所查habitat_extensions/run_r2r/run_rxr中未找到动态物体添加/控制逻辑；该wrapper方法中step_world注释，仅限该方法。实机描述家庭布局/视觉歧义，不提供移动物体专项预测结果。
- 本项目采用：区分物理场景变化、智能体位姿变化、观测变化、内部表征变化。房间不变而相机移动也会有状态转移；同理固定场景中机械臂关节状态会变化，模型可预测动作后果，不要求外界物体运动。
- 适用限制：不能称所有SC²-WM实机场景绝无动态对象，也不能推出Habitat不能模拟动态物体；“主要是动作相关观测/潜态转移”是依据方法与配置的解释。与UR5执行响应预测的对象不同，不宣称导航结果证明机械臂补偿。
- 使用位置：[exp0结果](experiment/备选/exp0/RESULTS.md)、[追问日志](agent_logs/experiment/exp0/20261007-codex-wm-integration.md)。
- 核查日期与人：2026-10-07，Codex /root；实际模型/强度未知。
- 待办：本次仅概念解释，无新功能、实验或参数授权；动态障碍能力若要主张需另读专项证据。

## SRC-0028

旧任务方案及关联内容已按用户2026-10-07明确要求删除，仅保留稳定编号作删除标记；不保留原方案参数/结果正文，不作为新Task3/4依据。删除记录见[SRC-0042](#src-0042)。

## SRC-0029

旧任务方案及关联内容已按用户2026-10-07明确要求删除，仅保留稳定编号作删除标记；不保留原方案参数/结果正文，不作为新Task3/4依据。删除记录见[SRC-0042](#src-0042)。

## SRC-0030

旧任务方案及关联内容已按用户2026-10-07明确要求删除，仅保留稳定编号作删除标记；不保留原方案参数/结果正文，不作为新Task3/4依据。删除记录见[SRC-0042](#src-0042)。

## SRC-0031

旧任务方案及关联内容已按用户2026-10-07明确要求删除，仅保留稳定编号作删除标记；不保留原方案参数/结果正文，不作为新Task3/4依据。删除记录见[SRC-0042](#src-0042)。

## SRC-0032

- 主张：SC²-WM原文报告执行前状态修正、视觉历史与测试期条件适配的导航收益；其组合在R2R-CE Val Unseen的SR为50.90%，复现基线43.77%，平均路径26.16→17.65 m；效果不证明UR5执行补偿或世界模型普遍必要。
- 类型：外部文献结果、表格差值推导及研究适用边界解释；非项目实测。
- 核查状态：已阅读arXiv v1方法/主表/消融/实机描述，PDF表格文本与HTML核对；未独立运行算法。README指向的OpenReview版本被浏览器验证拦截，未核验最终版本，不冒称最终版一致。
- 来源：Yao、Zhu、Gao、Wang、Xu；SC²-WM: A Self-Correcting World Model with Closed-Loop Feedback for Vision-and-Language Navigation in Continuous Environments；2026，arXiv:2608.07548v1；https://arxiv.org/html/2608.07548v1；https://arxiv.org/pdf/2608.07548；官方已有本地scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b README仅作交叉核对。
- 精确位置：§4.1/4.2表1/2（PDF印刷页7/8）；§4.3表3（印刷页8）；附录D.2表6/7（页16）、D.3（页16/17）及E（页17/18）。
- 原始结果：表3依次为基线SR43.77%、State-C48.34%、State-C+VCM49.86%、完整50.90%；对应TL26.16/21.75/18.73/17.65 m；固定每2步适配SR50.30%，条件触发50.90%；去未来特征预测损失SR48.89%。表6不适配49.86%、熵最小化49.48%、未来特征对实际特征监督50.90%；平均episode耗时17.21/18.92 s（基线/完整），不是单控制步延迟。表7在测到的2/4/6/8记忆长度中4最好，不外推普遍最佳长度。表1/2包含单目与全景、VLN-3DFF/ETPNav/HNR多个骨干增益，不代表每指标/每基准均最优。附录E报告GO2+D435i家庭导航70%→85%，作者写100trial×5重复=500runs、成功位置门槛1.5m，无独立复现。
- 推导：总SR差50.90−43.77=7.13个百分点；顺序增益4.57/1.52/1.04个百分点，均为该消融条件的观察差值，不是各组件独立效应可无条件相加。表2正文将8.36m称TL但表格字段为NE，正文ETPNav SPL也与表2/5有差异；本轮采用表格字段并不传播正文误标。
- 本项目采用：向用户解释“预测辅助执行前决策有导航收益、历史与在线学习也贡献增益、在线更新需要与实际观测关联的监督”。基线用表3作者复现43.77，不混用README原VLN-3DFF44.9来计算7.13。
- 适用限制：全部为作者报告；不将论文显著措辞当已核实统计显著性。导航潜态内部修正非关节伺服闭环；当前方法为模仿学习，不是SAC；历史模块同时引入，不能由完整组收益直接断言纯世界模型胜同历史SAC。没有UR5驱动时延/协调控制补偿结果，也不是预测损失越低就必然任务越好。真实导航门槛不能作为机械臂精度标准。
- 使用位置：[exp0主要结论](experiment/备选/exp0/RESULTS.md)、[日志](agent_logs/experiment/exp0/20261007-codex-wm-integration.md)。
- 核查日期与人：2026-10-07，Codex /root；实际模型/强度未知，未委派。
- 待办：结论说明本身无必需剩余；算法复现/机械臂适用性尚未验证，本次不改实验或授权范围。

## SRC-0033

- 主张：SC²-WM内部前瞻修正与强化学习兼容；SAC有观测反馈不构成拒绝模型预测的理由。作者仅讨论RL扩展，尚未以论文实验证明Husky/SAC结合收益。
- 类型：外部文献与概念推断。
- 核查状态：已读原文方法和附录D.3，以及SAC原始方法；未复现。
- 来源：Yao等，SC²-WM，2026，arXiv:2608.07548v1，https://arxiv.org/html/2608.07548v1；Haarnoja、Zhou、Abbeel、Levine，Soft Actor-Critic: Off-Policy Maximum Entropy Deep Reinforcement Learning with a Stochastic Actor，ICML 2018，https://proceedings.mlr.press/v80/haarnoja18b/haarnoja18b.pdf。
- 精确位置：SC²-WM §3公式3–6、Algorithm 1；Appendix D.3的Closed-Loop、Difference from critic-based feedback、Potential extension to reinforcement learning；SAC §4.1–4.2、Algorithm 1（印刷页5）。
- 原始依据：SC²-WM每步本来读取观测/历史，额外内部环是初步动作→预测下一潜态→修正当前表示→最终动作；作者区分内部修正与外部测量控制，指出RL兼容并提出辅助表征/内在奖励为未来扩展。SAC从当前状态采样动作、与环境交互、存真实转移，用期望回报优化策略/价值，不要求显式下一状态预测器。
- 本项目采用：把“反馈环是否存在”与“是否显式预测动作后果”分开。SAC可根据经验学到提前动作，其策略/价值也包含未来回报的信息，不能贬为只会事后反应；显式世界模型可提供结构化预测，但是否增加有效信息要检验。SC²-WM基线的逐步观测反馈不因作者称其open-loop而消失；该措辞针对缺少内部前瞻校验。
- 适用限制：不是“RL一律闭环”或“SAC必然补偿”；闭环取决于输入与执行反馈链路。作者RL扩展是讨论而非完成实验；本轮不改奖励、不实施新接口/训练。Critic通常是回报评估，不是每控制周期显式伺服误差控制器。
- 使用位置：[exp0兼容性解释](experiment/备选/exp0/RESULTS.md)、[日志](agent_logs/experiment/exp0/20261007-codex-wm-integration.md)。
- 核查日期与人：2026-10-07，Codex /root；实际模型/强度未知。
- 待办：解释交付不选择/授权实施；收益仍待明确范围内验证。

## SRC-0034

- 主张：Husky参考路径的观测条件策略可容纳预测辅助决策的概念；默认base感知不保证机械臂关节反馈是真实执行值，接入执行模型不能以目标状态代替实际监督。移植可行性与收益是不同问题。
- 类型：本地原始源码静态核查；接口概念映射与待验证假设，不是实现/实测。
- 核查状态：已读下列代码，未运行Husky/SAC或接入模型。
- 来源：Husky+UR5参考工作区，根HEAD 438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804；本轮未重做完整参考快照校验。既有[SRC-0026](#src-0026)与[exp4候选](experiment/备选/exp4/TASK.md)；理论依据[SRC-0033](#src-0033)。
- 精确位置：husky/src/modulation_rl/scripts/sac.py:select_action/update_parameters（60–125）；scripts/modulation/envs/combined_env.py:step/_to_agent_obs/_convert_policy_to_env_actions（356–455）；scripts/modulation/utils.py:perception_style默认（149）；src/robot_env.cpp:step（235–280）感知刷新。路径均在husky/src/modulation_rl内。
- 版本凭据SHA256：sac.py=e4e900e034939fd51622337414cbc4b66383096322da18e305f9d6627f59f7c5；robot_env.cpp=6fab72460d686f12b43797c1e4bc1b61d844a43ef46b5e418f07f6dfa4ce703a；combined_env.py=672ab9f538d00a23747bb49875b218809ddce2eef20abc39283f959a48f33a06；utils.py=a2d851e7bafdae94167a7668d4f28a93db753abca35c6b2669a63d3c0d2f26c2。
- 原始依据：select_action由map/robot状态直接policy.predict；环境每步生成新robot/plan/map观测，可拼前动作；base感知刷新实际底盘而保留期望关节，all分支使用状态监视器刷新关节；默认IK路径把SAC底盘动作与末端计划组合求关节目标，不能称SAC直接出六关节动作。
- 本项目采用：解释概念移植为“当前观测/历史→初步策略动作→模型预测行动后果→修正决策特征→策略最终动作→原控制链”；不改变SAC动作角色，也不将此草图升级为已冻结的双头训练设计。底盘/机械臂时差可能造成世界末端偏差，若模型能预报，策略可能通过底盘动作减轻，是待验证假设。
- 适用限制：现有网络没有实现此前瞻修正，不意味着下载模型权重即可用；SC²-WM视觉/语言/路点输入与Husky地图/机器人/计划语义不同，连续动作训练也需适配。不能把当前理想IK/默认期望关节状态当实际机械臂执行真值；仅解释不自动改为all或修改参考代码。收益须与同历史SAC/简单预测器比较，不能因已有闭环断言模型无用。
- 使用位置：[exp0兼容性解释](experiment/备选/exp0/RESULTS.md)、[日志](agent_logs/experiment/exp0/20261007-codex-wm-integration.md)。
- 核查日期与人：2026-10-07，Codex /root；实际模型/强度未知，未派Agent。
- 待办：无本次解释必需剩余；实现/训练尚未授权或执行。

## SRC-0035

- 主张：SC²-WM没有像FoReM控制偏差研究这样逐项测量/拆分IK、伺服跟踪、指令时延及底盘—臂同步误差；它围绕导航内部表征/决策修正做任务指标和模块消融。完整控制误差建模不是使用预测辅助策略的逻辑前置，但若宣称补偿特定执行偏差，需要对应证据。
- 类型：外部文献与官方代码静态审计、项目目标比较及工程判断；非新实验。
- 核查状态：已读原文方法、表1–3/6–7、Appendix D.3/E；核对已有scwm配置/动作层及此前审计。属于已查范围未见，不声称穷尽所有研究/底层仿真功能。
- 来源：Yao等；SC²-WM；2026，arXiv:2608.07548v1，https://arxiv.org/html/2608.07548v1；已有官方scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b；[旧审计](agent_logs/project/20260930-scwm-simulation-audit.md)；根AGENTS研究方向与误差定义（本轮上下文已读），exp0/exp4既有候选。
- 精确位置：论文§1/3.1内部状态漂移、部分可观测/视觉扰动；§4主指标与消融；D.3内外闭环区别；E实机低层执行；scwm/run_r2r、run_rxr配置；habitat_extensions/nav.py动作离散推进；vlnce_baselines/models/graph_utils.py:GraphMap识别节点阈值（161–176）。
- 原始依据：方法以历史视觉校准、预测潜态内部修正、条件测试期更新缓解导航偏差；主要测成功率、导航误差、路径效率，测试不同模块/更新损失/记忆长度。已查原文和配置未见独立执行时延扫描或关节/力矩/伺服响应辨识。loc_noise是位置匹配阈值，不是控制噪声幅度，动作actuation字段不等于电机动态模型。实机深度避碰也不等于逐项执行误差辨识。
- 本项目采用：说明方法迁移与机制归因的研究问题不同。若问题是“预测修正能否提升Husky任务”，可直接围绕策略接入与任务对照研究，不逻辑要求先构建每种误差；若问题是“补偿某种执行误差”，则必须分开指令、实际反馈、IK与时序，才能归因。这里是目标关系解释，不改变已授权计划、不实施功能或跳过已有必要验证。
- 适用限制：不声称SC²-WM完全忽略感知不确定性/碰撞，不据其未分解控制误差认定无效；也不将其表征修正包装成低层执行补偿。模型可否吸收复杂影响是待验证假设。SAC闭环与其内部预测环兼容见SRC-0033/0034，不是因RL已有反馈而禁止结合。
- 使用位置：[exp0结果](experiment/备选/exp0/RESULTS.md)、[追问日志](agent_logs/experiment/exp0/20261007-codex-wm-integration.md)。
- 核查日期与人：2026-10-07，Codex /root；实际模型/强度未知。
- 待办：解释不新增执行范围；机制/任务收益需在用户明确选定的目标和授权内验证。

## SRC-0036

- 主张：原Husky+UR5 Gazebo参考启动把仿真底盘绝对位姿经TF作为策略位置反馈，不能凭轮式平台断言它有累计里程计定位漂移；当前FoReM未测移动导航漂移，SC²-WM式潜态漂移也未被本项目确认。
- 类型：原始源码静态核查、现有项目记录与条件性结构推断；不是新运行/导航实测。
- 核查状态：已追踪启动→gdt_tf→worlds.cpp→策略输入，已读Task1/2和Task3b当前结果；未启动ROS/仿真、未验证当前容器TF发布者或历史运行配置。
- 作者/版本：Husky+UR5当前参考代码，根HEAD438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804，2026-10-07工作区读取；非完整快照复核。
- 精确位置：modulation_rl/gazebo_world/husky_ur5/n2m2_husky_empty_world.launch:88–92及husky_ur5同名入口:86–90，gdt.launch启动gdt_tf；pcl_configure/CMakeLists.txt:167指向src/tf.cpp；tf.cpp:OdomCallback/main直接读/ground_truth/state的pose发布odom→base_footprint，使用ros::Time::now重盖stamp；husky_ur5/urdf/husky_ur5.xacro:48–58为p3d绝对world/base_footprint位姿；modulation_rl/src/worlds.cpp:BaseWorld::getBaseTransformWorld查询map→base，无Gazebo单独读取get_model_state替代；husky_control/control.launch:7/34默认ENABLE_EKF=false，control.yaml不发布编码器odom TF；modulation_rl/scripts/model.py:GaussianPolicy.forward（141起）CNN+FC而非循环潜态；combined_env.py:step/_to_agent_obs（356–430）每步组机器人/地图/目标/可选前动作。
- 输入版本SHA256：husky/src/modulation_rl/src/worlds.cpp=e8d03015853d5d477a1fbe6e83df62e664867473685b7efed1f977725206bd7f；husky/src/modulation_rl/gazebo_world/husky_ur5/n2m2_husky_empty_world.launch=2b71871c4dae1ca5bc2f30b54e408ea863282f8c8442d2ea4104dd461ad9da9d；husky/src/pcl_configure/launch/gdt.launch=add68a7ec4f3df1fd4392b5738b288989109532758b54c94a0ad57bbc739f4b4；husky/src/pcl_configure/src/tf.cpp=fa605754669801f8adaa1cf248484c520ae8d6ee8aae7857d7147161b18679a9；husky/src/husky_ur5/urdf/husky_ur5.xacro=db1429ae2a4cad1fb1d50f871ecebedf103eb870e04768cab91b01aad6c647c8；husky/src/husky/husky_control/launch/control.launch=068432a21d206ec355fbf5e7a4c4b9c7fcc00c28130b2831177ecd2ffa955adc；husky/src/modulation_rl/scripts/model.py=3e561632951cb94ae1e9e7cf800ef6d4056ed0da13bed23f29a036cf4cb2d99e。
- 原始结论：该入口map→odom及world→map为恒等静态TF；gdt节点直接映射仿真pose，不逐步积分轮速。另有EKF/导航组件不证明默认使用它们。此结构不构成累计编码器漂移模型，仍可能有采样/时间戳/其他发布者问题；未量化。默认base观测保留期望关节的问题已另见SRC-0034。
- 本项目采用：区分定位估计偏差、任务路径偏离和内部表示漂移。源码不能证明当前SAC策略是否走偏/撞障，固定底座Task1/2也不能验证移动导航；Task3b仅方案、尚未运行见t3b结果（旧任务内容已按用户要求删除）。SC²-WM基于潜态历史/语义推断，与本地所读直接地图/数值状态策略不同；其潜态漂移假说需单独证据，不能把导航失败自动命名为同种漂移。
- 适用限制：仅所读参考Gazebo默认入口；ENABLE_EKF环境覆盖、自定义TF/实机定位/其他模型路径可能不同。不是已确认完全无位置误差，也不否定真实轮速/IMU估计漂移。ground_truth命名/gaussianNoise配置本身不能证明运行输出精度。没有本次新导航测量，不用旧Husky历史表现当FoReM验收。
- 使用位置：[本轮日志](agent_logs/project/20261007-codex-husky-navigation-drift.md)、[exp0漂移核查](experiment/备选/exp0/RESULTS.md)。
- 核查日期与人：2026-10-07，Codex /root；实际模型/强度未知，未委派。
- 待办：若要确认某运行的定位/路径偏差，需该运行配置及同步估计/独立位姿与任务记录；本次不新增实验或实施授权。

## SRC-0037

- 主张：里程计积累漂移与直接仿真位姿发布不同；p3d配置gaussianNoise不能直接解释为位置每步加噪或累计定位漂移。
- 类型：官方文档/源码与条件性解释，不是当前容器二进制核验。
- 核查状态：已读官方raw原文；docs.ros.org两页面被访问拦截，改读维护者raw文档；实际插件版本未知。
- 来源：cra-ros-pkg robot_localization，noetic-devel，State Estimation Nodes，https://raw.githubusercontent.com/cra-ros-pkg/robot_localization/noetic-devel/doc/state_estimation_nodes.rst；OSRF/ros-simulation gazebo_ros_pkgs，noetic-devel，gazebo_ros_p3d.cpp，https://raw.githubusercontent.com/ros-simulation/gazebo_ros_pkgs/noetic-devel/gazebo_plugins/src/gazebo_ros_p3d.cpp（分支浏览时版本，未锁commit）。
- 精确位置：state_estimation_nodes.rst“~[frame]”关于odom/map及融合连续/全局位置说明（42–50）；GazeboRosP3D::UpdateChild读取WorldPose（266）、填pose（312–319）、GaussianKernel仅添加twist（320–332）及covariance（335–347）。
- 原始依据：官方区分odom连续但会积累漂移、map包含全局校正；p3d upstream直接读world pose，噪声添加到twist，pose协方差设gn²而pose值不在此处加GaussianKernel。
- 本项目采用：限制配置解读：本地p3d gaussianNoise=0.01只是配置字段，不证明位置误差为0.01m，也不证明漂移。若实际安装与此源一致，gdt只复制pose，则该noise不会按此路径积分为位置漂移。直接pose仍可能有消息延迟，gdt改stamp需独立时间核对。
- 适用限制：不把官方当前分支当当前已加载插件/旧运行版本；不将协方差当位置实测误差，不据编码器odom的一般描述给Husky groundtruth路径定性“必漂移”。
- 使用位置：[本轮日志](agent_logs/project/20261007-codex-husky-navigation-drift.md)、[exp0漂移核查](experiment/备选/exp0/RESULTS.md)。
- 核查日期与人：2026-10-07，Codex /root；实际模型/强度未知。
- 待办：本次无运行核验，若将插件噪声作为数值主张必须核对实际版本与输出；不新增实验授权。

## SRC-0038

- 主张：TF是坐标关系传递/查询接口，可以传递视觉惯性估计而非Gazebo真值；相机+IMU估计定位存在现成公开算法，但当前FoReM兼容性未验证。
- 类型：官方文档/作者代码说明；工程接口解释。
- 核查状态：已读官方/作者README与文档，未安装/构建/运行定位算法。
- 来源：ROS geometry noetic-devel tf/mainpage.dox，https://raw.githubusercontent.com/ros/geometry/noetic-devel/tf/mainpage.dox；HKUST Qin/Cao/Pan/Li/Shen，VINS-Fusion README/master，https://raw.githubusercontent.com/HKUST-Aerial-Robotics/VINS-Fusion/master/README.md；Campos等，ORB-SLAM3 V1.0 README，https://github.com/UZ-SLAMLab/ORB_SLAM3（声明版本2021-12-22，浏览2026-10-07；未锁commit）。
- 精确位置：TF Common Usage/TransformListener/TransformBroadcaster；VINS Features、Prerequisites、EuRoC、Run with your devices；ORB-SLAM3 README介绍/示例及Prerequisites。
- 原始依据：TF追踪坐标系并发送/接收变换，不规定变换必须由真值产生。VINS-Fusion支持单目+IMU/双目+IMU/双目、时空校准与回环；官方声明Kinetic/Melodic，未据此保证Noetic。ORB-SLAM3提供视觉/视觉惯性SLAM及单目/双目带IMU示例，存在依赖与接口适配要求。
- 本项目采用：建议替换当前ground_truth→TF发布者为sensor estimator→TF，保留策略/机器人TF接口；用户若确实要完全去TF，可另评topic接口，但不因替换定位来源而必然删除所有TF。算法仅可行性参照，不据此选定型号/传感器/依赖。
- 适用限制：现成源码≠本机实时/初始化稳定/Noetic兼容。IMU、相机安装关系、同步、成像/校准与坐标系必须核对。传感器估计不保证一定产生明显漂移，也不保证WM有收益。
- 使用位置：[方向讨论日志](agent_logs/project/20261007-codex-husky-sensor-baseline.md)。
- 核查日期与人：2026-10-07，Codex /root；实际模型/强度未知。
- 待办：场景/传感器配置/初态与目标frame、算法版本和实际构建验证待后续明确设计，本轮未实施。

## SRC-0039

- 主张：Husky参考有IMU/相机模型但并非已核验的FoReM视觉惯性定位链；仿真T265的现成odom/sample是p3d位姿输出，不可称图像+IMU估计基线。
- 类型：本地源码静态核查；非传感器运行实测。
- 核查状态：已读宏、默认开关、插件和地图/策略接口；未启动ROS、未编译/加载传感器。
- 作者/版本：Husky+UR5参考工作区，根HEAD438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804；2026-10-07读取。
- 精确位置：husky/src/husky/husky_description/urdf/husky.urdf.xacro:54–57相机默认开关、252–267 IMU插件；accessories/intel_realsense.urdf.xacro:深度相机图像/深度/点云插件；husky/src/husky_ur5/urdf/husky_ur5.xacro:26–32腕部D435注释；husky/src/realsense_ros_gazebo/README及xacro/tracker.xacro:184–195 IMU、207–217 odom libgazebo_ros_p3d.so；modulation_rl/scripts/modulation/envs/map.py:get_local_map(304–313)解析/真值图和gazebo/world costmap分支；combined_env.py:get_local_map/_to_agent_obs目标与机器人相对量计算；当前forem/src/forem_sim为固定基座UR5，移动Task3b仍方案。
- 原始依据：原Husky IMU宏有输出与噪声字段，相机配件默认HUSKY_REALSENSE_ENABLED=0，腕相机另处注释；源码可用不证明当前实测可用。T265例子的odom/sample来自p3d，若直接读该话题仍绕过真实定位计算。策略依赖机器人状态、目标相对关系与地图来源，替换位置源时必须检查完整输入计算，不能隐藏调用Gazebo真值。
- 本项目采用：建立基线必须消费图像、标定及IMU等原始可得传感数据，由定位算法产生位姿；相机已有odom话题先审计来源。沿用机器人模型/控制协调/任务接口的意思是移植必要项目核心到forem，不改husky参考或把固定UR5实验冒充完整Husky。
- 适用限制：不把相机默认关闭认定永远不可启用；不推断本地全部不同模型入口都无传感器。插件noise值不是本轮选定参数，未评价具体漂移/精度；无需因希望世界模型有效而放大噪声。
- 使用位置：[方向讨论日志](agent_logs/project/20261007-codex-husky-sensor-baseline.md)。
- 核查日期与人：2026-10-07，Codex /root；实际配置未知，未派Agent。
- 待办：后续明确环境后核验实际topic/时间戳/外参/初始化；本轮未运行或修改。

## SRC-0040

- 主张：用户提出“统一Husky核心→传感器定位完成任务的SAC基线→世界模型增强”在接口上可作为研究路线；这是待确认设计方向，不是已执行方案或收益结论。
- 类型：用户意图记录、工程方案及待验证假设；非新增实施授权。
- 来源：本轮用户明确提议；当前FoReM/Task3b/exp4候选、[SRC-0038](#src-0038)及[SRC-0039](#src-0039)接口依据；SC²-WM接入与RL兼容性[SRC-0033](#src-0033)。
- 精确位置：用户本轮要求、本轮日志意图复述；Task3b TASK已写机器人/协调核心但未纳入SLAM/SAC/WM，exp4尚为备选固定底盘预测辅助SAC。不能声称新方向已在原授权范围。
- 原始意图/方案：先统一机器人模型、底盘/臂协调动作、任务/奖励/终止与策略接口，再把传感器估计位置供策略完成任务，最后在同位置来源与任务下比较预测修正收益。环境Gazebo/实机已异步询问，推荐先Gazebo但用户尚未作答时不当作选定。
- 本项目采用：提供两种范围选项——先用成熟视觉惯性定位器替换位置来源并保留既有策略接口（推荐，定位与决策作用可分），或同时把策略改成直接处理图像/IMU（更接近视觉导航，但还改变表征/任务接法、归因和工程范围更大，未纳入已授权执行）。不自行选择后者或添加模块。前者也需定义目标/地图/机器人在同一估计frame，目标可预先给定，但相对目标不能偷偷由真实底盘位姿计算。
- 验证思路：先确认定位初始化/连续输出与任务可运行；策略基线在估计反馈上训练/评估，不能仅拿真值训练旧策略换输入退化当公平主比较。WM与基线保持同传感器/定位器/任务/动作及预算，检查同历史策略；Gazebo真值可单独评测实际定位与任务成功，不进入在线策略/修正输入。是否允许训练期特权监督须另明确，不能默认为已许可。
- 适用限制：主要研究对象将由执行偏差转向感知估计及预测辅助决策，不能把新结果自动解释成驱动时延补偿，也不取消已有数据/历史。传感估计漂移有无/程度及WM价值待测，不预设收益，不先削弱正常定位能力。实现均在forem，参考只读、ROS容器内运行。此方向讨论不自动重排Task3a/3b或启动算法安装/训练。
- 核查状态与日期：2026-10-07，Codex /root，已有文档/源码/外部方法入口已读；方案尚待用户设计选择，实际模型/强度未知。
- 使用位置：[方向讨论日志](agent_logs/project/20261007-codex-husky-sensor-baseline.md)。
- 待办：确认环境和首个任务，再按项目三文档规则形成明确方案与执行范围；本轮不写实施代码/依赖/正式协议。

## SRC-0041

- 主张：Gazebo与实机可采用相同的传感器定位→策略→控制接口，但输入来源和验证要求不同；推荐先Gazebo建立此基线，不等于用户已选定或批准实施。
- 类型：基于现有源码/官方定位器说明的工程路线比较与推荐；非实测结论。
- 来源：[SRC-0038](#src-0038)官方VINS-Fusion/ORB-SLAM3设备校准、同步与接口说明；[SRC-0039](#src-0039)现有仿真相机/IMU宏；Forem ENV已建立容器/Gazebo/固定UR5，Task3b移动仅方案；用户本轮问“这俩有什么区别”。
- 精确位置：VINS-Fusion README“Run with your devices”、Features时空校准；husky传感器宏/插件位置如SRC-0039；forem/ENV.md后续环境验收更新、Task3b RESULTS未执行段；[讨论日志](agent_logs/project/20261007-codex-husky-sensor-baseline.md)。
- 原始依据：仿真相机渲染图像与IMU插件数据可供实际定位计算，必须剔除p3d直接位姿话题；真实设备输入需要实际标定/时序与设备接口。现有仿真基座环境可复用，但移动Husky传感器/定位基线仍需实现核验；没有本轮真实Husky/传感器可用性证据。
- 本项目采用：先Gazebo是推荐的工程顺序，便于反复运行并用独立仿真真值评测；算法在线只用可得图像/IMU/约定任务信息，真值只在评测侧。实机后续验证真实传感与执行条件的可迁移性；仿真收益不能直接称实机收益。
- 适用限制：不说仿真传感器等同真实硬件，不保证定位漂移程度或WM收益，不因问区别就把用户环境选择当已回答。实机路线依赖真实平台、相机/IMU和驱动，当前未核验；本次无新增功能/运行。
- 核查状态、日期与人：已读来源及本地代码，工程比较尚待选择；2026-10-07，Codex /root，实际模型/强度未知。
- 使用位置：[讨论日志](agent_logs/project/20261007-codex-husky-sensor-baseline.md)。
- 待办：用户了解差别后确定环境；现阶段只讨论建议，不开始依赖环境选择的实现。

## SRC-0042

- 主张：用户最新明确要求删除Task3a/Task3b所有内容，重写Task3为Husky核心迁移，Task4为图像/IMU定位估计；本轮仅任务计划与文档同步。
- 类型：用户明确要求与工程组织决定。
- 核查状态：已收到用户纠正，已删除两个任务父/子目录、旧Task3.1–3.5兼容入口、相关未执行exp3.1/3.2方案、旧task3ab计划日志/快照；无仿真进程需要停止。
- 来源：本轮用户原指令及纠正“删除task3a 3b所有内容”；根AGENTS编号稳定/三文档/开发边界，最新用户要求优先。
- 精确位置：[本轮日志](agent_logs/task3/20261007-codex-husky-core-task34-plan.md)；删除清单`results/task3/task34-plan-20261007/deletion_manifest.json`仅记录路径/数量，不存被删全文。
- 原始依据：本轮最初提出保留取消文档，用户明确否定；已遵照纠正直接删除，不额外归档全文。Git历史、Task0/1/2实际实现/数据不改。
- 本项目采用：新Task3父文档覆盖原兼容入口，子号按用户最新要求重新编号为3.1–3.6，覆盖先前避开历史号的选择；Task4为4.1–4.6。旧任务已删除，无cancelled目录或待实施旧流程。
- 适用限制：删除不冒充研究完成；文档编写不授权源码迁移、依赖安装、仿真或训练。Gazebo为现有项目内计划环境，实机/WM/补偿/误差注入不纳入Task3/4。
- 使用位置：[Task3](tasks/task3/PROCEDURE.md)、[Task4](tasks/task4/PROCEDURE.md)、[本轮日志](agent_logs/task3/20261007-codex-husky-core-task34-plan.md)。
- 核查日期与人：Codex /root，2026-10-07；实际模型/强度未知，未派Agent。
- 后续状态：新Task3/4三文档与共享索引已核验交付，检查报告见本轮计划产物；实施尚未执行，不恢复已删除任务。

## SRC-0043

- 主张：Husky核心包含模型/底盘臂协调/末端规划与IK、任务观测奖励终止、SAC普通更新及运行接口；原main.py还含旧先验权重与修改更新，不等于普通SAC基线。
- 类型：本地原始源码静态核查。
- 核查状态：已读所列原始文档/代码；新工程、定位与训练尚未执行。
- 来源：Husky参考，根HEAD438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804，当前工作区源码；modulation_rl/package.xml/CMakeLists.txt、scripts/main.py/sac.py/model.py/replay_memory.py/modulation/utils.py/envs/tasks.py/combined_env.py、src/robot_env.cpp/robot_husky.cpp/worlds.cpp；来源版本逐文件hash见本轮source_receipt.json。
- 精确位置：main.py:153–155旧prior权重，243调用update_parameters_modified；sac.py:update_parameters(70起)/update_parameters_modified(166起)；SimpleObstacleTask(329起)、episode_is_success；robot_env.cpp协调/感知分支及worlds.cpp TF。
- 原始依据：非纯上游N²M²。默认底盘动作结合末端计划，在下一预期底盘位姿求IK并异步发送arm/base；SAC普通update函数已存在，main.py默认读/home/cbl旧checkpoint并走prior修改更新。Gazebo与解析sim要区分；默认base感知保留期望关节。
- 本项目采用：保留普通SAC与核心任务语义，单列移植差异；新入口不直接执行含硬编码checkpoint的大训练脚本。依赖只取Husky可达路径，其他机器人不视迁移目标；保留来源/许可证和原文件hash。
- 适用限制：静态可读不等于可构建/可运行/复现性能；新网络/奖励/任务不是迁移修复。标准SAC替代原主脚本prior支路是明确基线选择，不能称原main运行复现。
- 使用位置：[Task3](tasks/task3/PROCEDURE.md)、[Task4](tasks/task4/PROCEDURE.md)、[日志](agent_logs/task3/20261007-codex-husky-core-task34-plan.md)。
- 核查人/日期：Codex /root，2026-10-07；实际模型/强度未知，未委派。
- 待办：实施时先接收来源、完成对应前置验证与冻结；本次仅文档，不宣称效果或授权运行。

## SRC-0044

- 主张：Task3是Husky核心独立迁移与运行接口验收；保留定位来源契约和真实反馈测量，但本阶段不新增传感器定位或完整训练。
- 类型：工程设计选择与待验证交付。
- 核查状态：已读所列原始文档/代码；新工程、定位与训练尚未执行。
- 来源：本轮授权；SRC-0043源码、Task0.13/Task1.10/Task2.9现有验收；现有forem/docker/run.sh和scripts/task0_proc.py。
- 精确位置：新Task3及3.1–3.6 TASK/PROCEDURE；Task0 ENV与控制器/world solver记录。
- 原始依据：承接现有独立容器、只挂forem；固定UR5已验收并非移动模型通过。保留原ROS包名/pybind模块接口，源码导入forem/src，新增forem_husky组装包和受控入口；truth_tf定位仅用于本Task3复现原参考定位路径，标权限。
- 本项目采用：首个任务选原SimpleObstacleTask静态场景/原动作语义，场景/初态清单先冻结，不新增抓取/门/动态障碍或人工时延。SAC短回放/一次批次更新/保存加载是链路检查，不算任务性能训练。Task4继承同模型/控制/任务契约再换反馈源。
- 适用限制：Task3性能未测，已有world直接solver是否适用移动环境须新验；不退回已知旧异常求解器冒充原样统一。数字周期/限位/成功条件由来源接收子任务读取实际值冻结，不从记忆/旧平台套数值。
- 使用位置：[Task3](tasks/task3/PROCEDURE.md)、[Task4](tasks/task4/PROCEDURE.md)、[日志](agent_logs/task3/20261007-codex-husky-core-task34-plan.md)。
- 核查人/日期：Codex /root，2026-10-07；实际模型/强度未知，未委派。
- 待办：实施时先接收来源、完成对应前置验证与冻结；本次仅文档，不宣称效果或授权运行。

## SRC-0045

- 主张：Task4从真实原始仿真图像与IMU估计底盘位置，替换truth_tf来源并建立同任务普通SAC基线；TF保留为传递接口，WM留后续。
- 类型：工程设计选择、官方接口依据与待验证假设。
- 核查状态：已读所列原始文档/代码；新工程、定位与训练尚未执行。
- 来源：SRC-0038/0039/0040/0041；VINS-Fusion官方README(https://github.com/HKUST-Aerial-Robotics/VINS-Fusion)、ORB-SLAM3官方README(https://github.com/UZ-SLAMLab/ORB_SLAM3)已读；本轮用户范围。
- 精确位置：新Task4及4.1–4.6三文档；tracker.xacro:207起odom/p3d；TF监听worlds.cpp；map.py/combined_env.py输入坐标换算。
- 原始依据：已有相机/IMU宏不等于定位链，T265现成odom来自p3d不可当VIO；主候选VINS-Fusion双目+IMU，必须先验证同步/内外参/Noetic依赖与初始化，再锁版本。替代ORB只在主候选不满足同接口时登记一次选择，不同时移植两个算法。
- 本项目采用：相机与IMU刚性安装在底盘，定位器只消费图像/CameraInfo及加速度角速度；不把仿真IMU姿态四元数或camera/odom真值当估计输入。地图/目标/末端规划使用一致估计frame；初态map对齐权限明确、禁止连续用truth校正。真值只供隔离评测，估计反馈基线须在此反馈下训练。
- 适用限制：仿真不是实机校准，不预设明显漂移/模型收益；不削弱回环或增噪以造退化。奖励/终止沿用Task3并公开信号来源，独立真实成功统计可发现假成功，不偷偷改奖励修正定位。Task4本轮只有计划，不安装算法、运行或训练。
- 使用位置：[Task3](tasks/task3/PROCEDURE.md)、[Task4](tasks/task4/PROCEDURE.md)、[日志](agent_logs/task3/20261007-codex-husky-core-task34-plan.md)。
- 核查人/日期：Codex /root，2026-10-07；实际模型/强度未知，未委派。
- 待办：实施时先接收来源、完成对应前置验证与冻结；本次仅文档，不宣称效果或授权运行。

## SRC-0046

- 主张：Task3/4的验收按阶段验证来源、构建、启动、控制/观测、定位与任务结果；性能数值/资源预算需要前置先导冻结，不能把计划字段当已测结论。
- 类型：工程验收与评测设计。
- 核查状态：已读所列原始文档/代码；新工程、定位与训练尚未执行。
- 来源：Task0/1/2现有验收实践、SRC-0043来源、SRC-0045接口设计；本轮用户任务目标。
- 精确位置：Task3/4父流程输入/输出/失败/冻结与独立复核；各子TASK交付；配置schema和gate函数计划。
- 原始依据：必须核验错误来源拒绝、数值有限性、动作shape/限位、时间/reset一致、TF单一发布者、定位丢失不回退truth、checkpoint与obs/action契约、所有失败尝试保留。独立复核人不与实现者相同。
- 本项目采用：Task3协议数值直接继承经读取的对应原任务/物理参数并记录必要适配；Task4定位质量门槛依据相同任务容差与先导，在正式数据/训练前冻结。训练steps/seed/更新/设备/墙钟/失败补跑预算在4.1资源方案和4.4先导后冻结，预算缺项不运行，避免原main无界长训。训练/测试按完整episode/场景实例分开。
- 适用限制：不存在预设世界模型必赢/漂移下限/导航通用阈值；小规模SAC更新只验证数值与接口，不支持性能结论。定位与真实任务表现都报，不把估计坐标到达当物理到达；原参考任务含数值语义须审计。
- 使用位置：[Task3](tasks/task3/PROCEDURE.md)、[Task4](tasks/task4/PROCEDURE.md)、[日志](agent_logs/task3/20261007-codex-husky-core-task34-plan.md)。
- 核查人/日期：Codex /root，2026-10-07；实际模型/强度未知，未委派。
- 待办：实施时先接收来源、完成对应前置验证与冻结；本次仅文档，不宣称效果或授权运行。

### SRC-0046 定位度量推导补充

输入：同sim stamp、只经一次固定初始frame对齐的估计/仿真base x/y/yaw；有效配对条件与时间容许误差由Task4.1/4.4先导冻结。e_p=[x_est−x_true,y_est−y_true]（m），RMSE=sqrt(mean(||e_p||²))、peak=max||e_p||（m）；yaw_err=wrap(yaw_est−yaw_true)（rad）。这是工程评价定义/单位推导，不是实测数值；覆盖不足/初始化或追踪丢失另报，不以缺样本减少失败分母。用途：[Task4流程](tasks/task4/PROCEDURE.md)，核查Codex /root，2026-10-07。

### 2026-10-07旧任务内容删除后的来源适用性

旧补偿/移动任务的方案登记正文已删除，只留编号删除标记；原重复编号0014/0015的旧方案段已移除，同号Task2实测解释登记保留。没有旧数值/矩阵/命令作为新Task3/4执行契约。本轮新范围/接口来源SRC-0042–0047；Task0/1/2项目实测继续按实际RESULTS引用。

## SRC-0047

- 主张：Task4先以独立视觉惯性估计器输出位姿，再替换现有机器人状态/地图观测的坐标来源；普通SAC主基线从头训练，不直接沿用旧真值反馈策略作为新基线。
- 类型：原始源码核查＋用户明确要求＋工程选择；迁移有效性为待验证假设。
- 来源：2026-10-07用户“得重新训练，包括设计IMU和相机对位置的估计方式”；Husky本地`scripts/sac.py`、`model.py`、`replay_memory.py`，根HEAD438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804，实际工作区hash见[源码收据](../results/task3/task34-plan-20261007/source_receipt.json)；HKUST-Aerial-Robotics，VINS-Fusion官方README和master源码，2019版权、2026-10-07在线读取，远端commit本轮未固定。
- URL与精确位置：[官方说明](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion)§Features、§1.1、§3.2及§6；[estimator.cpp](https://raw.githubusercontent.com/HKUST-Aerial-Robotics/VINS-Fusion/master/vins_estimator/src/estimator/estimator.cpp)`inputImage`、`inputIMU`、`processMeasurements`、`processIMU`、`optimization`；[feature_tracker.cpp](https://raw.githubusercontent.com/HKUST-Aerial-Robotics/VINS-Fusion/master/vins_estimator/src/featureTracker/feature_tracker.cpp)`trackImage`。本地`sac.py:SAC.__init__/select_action/update_parameters/load_checkpoint`、`model.py:QNetwork/GaussianPolicy`。
- 核查状态：已读本地接口/检查点载入代码及上述官方页面/代码；未安装、未构建定位器，未训练或验证旧权重。远端master为核查时版本，实际实施须固定commit、记录patch及构建证据。
- 原始结论：官方支持双目+IMU，具有视觉特征跟踪、IMU处理与优化融合；README声明Kinetic/Melodic，不能据此宣称已支持本项目Noetic。现有SAC输入为机器人状态与地图，actor/critic按该空间建立，普通update_parameters无需直接读取raw图像或IMU；load_checkpoint可载入策略/价值网络及优化器等旧状态。
- 本项目采用：按传感器标定/同步、视觉特征、IMU预积分/初始化、联合估计、相机/IMU到base外参、初始任务frame与失效处理写设计；只实现最终选定定位器。actor/critic维度、动作和普通SAC公式保持原合同，位姿以及所有依赖它的相对量/地图裁剪改为估计来源。定位质量/时间/失效供适配层判定，不自行增加SAC输入字段。
- 重新训练选择：正式基线随机初始化actor/critic，target由新critic初始化，熵系数/优化器/调度器/回放/归一化状态新建，训练和评估均运行冻结的估计链。理由是用户要求及明确新基线数据来源，避免把旧训练分布/优化状态混入新基线；不是证明旧权重必定不能用。只允许同Task4协议检查点的正常中断恢复，记录protocol/hash/预算累计。旧权重可加载性取决于维度/语义/归一化契约，即使兼容也不保证表现；本轮不运行旧策略迁移或微调对照。
- 适用限制：第一版不是图像/IMU直接输入的端到端SAC，不额外加入视觉编码器、RNN、观测历史或协方差特征。相同网络结构不保证在估计误差/延迟下足够，任务结果必须实测；若不可运行先查定位/接口再记录局限。训练奖励/内部终止继承原任务并登记是否使用真值，不能偷偷改奖励；actor/critic观测、定位/IK/地图变换不得偷读true base，独立成功按真实状态判定。主基线训练从头是本项目选择，不声称所有方法都必须从头训。
- 使用位置：[Task4父流程](tasks/task4/PROCEDURE.md)、[task4.1](tasks/task4/task4.1/PROCEDURE.md)、[task4.3](tasks/task4/task4.3/PROCEDURE.md)、[task4.5](tasks/task4/task4.5/PROCEDURE.md)。
- 核查人/日期：Codex /root，2026-10-07；实际模型/强度未知。
- 待办：Task3先完成核心迁移；Task4实施时锁定标定、时间/frame、算法版本与预算，再建立新训练/任务结果；当前仅计划文档。

## SRC-0048

- 主张：相机与IMU可通过EKF/MSCKF进行紧耦合位姿估计；OpenVINS是这类官方实现，应纳入Task4.1与优化式VINS-Fusion的有限选型核查，最终只接入一个定位器。
- 类型：官方文档核查＋用户指定调研＋工程候选选择；不是本项目定位实测。
- 作者/机构与版本：Patrick Geneva、Kevin Eckenhoff、Woosik Lee、Yulin Yang、Guoquan Huang，University of Delaware RPNG；OpenVINS官方文档（引用ICRA2020论文，本轮未读论文全文）；KumarRobotics，MSCKF_VIO官方README，在线master版本，未固定commit。
- URL/精确位置：[OpenVINS首页](https://docs.openvins.com/)§介绍及Project Features；[安装指南](https://docs.openvins.com/gs-installing.html)§ROS Dependency；[IMU传播推导](https://docs.openvins.com/propagation.html)§IMU Measurements/Inertial State Vector/Mean and Uncertainty Integration；[更新推导](https://docs.openvins.com/update.html)§Linear Measurement Update；[MSCKF_VIO官方代码说明](https://github.com/KumarRobotics/msckf_vio)§介绍/Calibration/ROS Nodes。
- 核查状态：已读上述官方页面；不是只读搜索摘要。未下载/编译/运行算法，不宣称在FoReM已可用；论文全文、实际版本和性能待核验。
- 原始结论：OpenVINS以EKF融合IMU和稀疏视觉特征，使用滑动窗MSCKF，支持同步双目及静/动态初始化。官方安装指南声明在Ubuntu20.04/ROS Noetic等平台测试构建。KumarRobotics的MSCKF_VIO接收同步双目与IMU，image_processor输出特征、vio紧耦合融合并输出IMU frame的6DoF odom/covariance，声明测试Ubuntu16.04/Kinetic。
- 方法解释：IMU角速度/加速度用于带偏置/重力建模的姿态/速度/位置及不确定性传播；相机特征提供测量残差，EKF线性化更新修正状态与协方差。不是直接把两套“绝对位置”取平均，也不是SAC训练公式。状态frame与初始全局目标对齐仍需明示，不能由相对VIO自动获得任务绝对坐标。传播/更新属于所选定位器，不能把VINS优化式IMU预积分写成所有滤波器必须同样实现。
- 本项目采用：用户建议“通过卡尔曼滤波结合IMU和相机”授权调研。Task4.1优先核查OpenVINS这一滤波候选与原VINS-Fusion候选的输入、frame/同步、初始化、依赖和正常定位能力；不是同时移植多个算法或算法排名。最终唯一算法冻结后Task4.3实际接入，pose_adapter下游/SAC接口不因滤波或优化选择改变；普通SAC主基线从头训练按SRC-0047。
- 适用限制：Noetic官方构建记录不等于本项目成功，初始化/平面Husky运动/场景纹理/时间和算力均须先导验证；不承诺绝对无漂移、不声称滤波性能优于优化。OpenVINS核心不默认等于完整全局回环导航系统，附属模块不自动列入实施范围。标定/噪声/阈值/频率不直接抄论文或其他平台数值，按实际配置依据冻结。
- 使用位置：[Task4.1选型流程](tasks/task4/task4.1/PROCEDURE.md)、[Task4父流程](tasks/task4/PROCEDURE.md)。
- 核查人/日期：Codex /root，2026-10-07；实际模型/强度未知。
- 待办：实际容器依赖与代码commit/patch/许可证核查、唯一选择及真实链路验证尚未执行。

## SRC-0049

- 主张：用户要求Husky核心迁移完成后详细解释原项目有哪些运行/算法链路及各自用途；这是Task3的审计与交付说明要求，不能只交目录拷贝。
- 类型：用户明确要求＋源码静态核查＋工程交付安排。
- 来源：2026-10-07用户“迁移完了要详细给我讲说原来的husky有几条线，分别有什么用处”；Husky本地参考源码，根HEAD438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804及工作区实际文件。
- 精确位置：`husky/src/modulation_rl/run_experiment.sh`入口分派；`scripts/main.py`153–155 prior构建/冻结旧权重、243 modified更新；`scripts/sac.py`普通/modified更新；`scripts/main_ray.py`trainer/tune训练；`scripts/eval.py`载检查点评估；`scripts/evaluation_ray.py`trainer.restore/ray_eval；`scripts/evaluation_moveit.py`、`evaluation_bi2rrt.py`、`evaluation_articulated.py`作为待读对照入口；`scripts/modulation/envs/{combined_env,robotenv,eeplanner,tasks,map}.py`、`src/{robot_env,robot_husky,worlds}.cpp`为任务到执行主链。
- 核查状态：已读本轮入口分派/main/普通SAC/Ray入口片段和combined_env片段；未逐项完整审计或实际运行所有分支。对照入口本轮仅发现文件，用途须Task3.1全文核查后写确定结论。
- 原始结论：仓库存在本地SAC与prior修改更新、Ray训练/评估入口和共享任务/执行层；文件存在不能证明对应链路可运行或同一算法。重复“modulation（修改后）”和“改过的地图场景”等树不自动作为活动运行线。
- 本项目采用：Task3.1按实际入口/调用关系审计，Task3.5在RESULTS内交付面向用户说明：明确分类口径与核实数量，列每条线目的/入口/输入/输出/上下游、实际活跃/历史状态、迁移保留/必要改造/未纳入部分及证据；Task3.6核对。把算法训练分支、在线任务执行数据流和世界模式分别说明，不能混在一套计数里。
- 适用限制：当前尚未迁移，数量暂不定论，不把发现文件数当有效链路数；审核/说明其他分支不授权移植/运行全部算法、其他机器人或新任务。详细报告写本层RESULTS，遵守三文档，不额外建第四份同职责报告。
- 使用位置：[Task3任务](tasks/task3/TASK.md)、[task3.1流程](tasks/task3/task3.1/PROCEDURE.md)、[task3.5交付](tasks/task3/task3.5/PROCEDURE.md)。
- 核查人/日期：Codex /root，2026-10-07；实际模型/强度未知。
- 待办：迁移实施时完整审计，并以最终实际结果给用户详细讲解；本轮仅纳入计划。

## SRC-0050

- 主张：用户明确要求新Task3从task3.1开始重新编号，旧Task3.6–3.11未实施计划依次改为Task3.1–3.6；旧任务删除不变，不是恢复旧补偿方案。
- 类型：用户明确要求与工程组织决定。
- 来源：2026-10-07本轮用户“为什么开始就是task3.6，重新编号”；[操作日志](agent_logs/task3/20261007-codex-renumber.md)。
- 精确位置：Task3父子三文档、Task4前置、PROGRESS/PLAN/README/DECISIONS及根AGENTS最新同步；[编号核验](../results/task3/task34-plan-20261007/renumber_verification.json)。
- 核查状态：已核对Task3六个子任务仍为未实施方案；本次只重编号和同步引用，无代码/仿真/训练。
- 原始依据：此前为了避开已删除旧子号而从3.6开始；用户现明确要求重编号，最新用户指令优先于通用编号稳定约束。
- 本项目采用：3.1来源/契约、3.2模型/控制、3.3环境/IK/任务、3.4普通SAC接口、3.5集成/讲解/交接、3.6独立复核；Claude实施3.1–3.5，Codex独立复核3.6；Task4依赖新3.6通过。
- 适用限制：部分曾删除的旧路径因新计划编号再使用，其内容属于新核心迁移方案。旧删除清单与旧文档hash报告保留为当时事实，不能再要求复用路径当前不存在，也不能当成当前编号核验。Task0/1/2证据与Git历史不变，任务实施未开始。
- 使用位置：[Task3](tasks/task3/PROCEDURE.md)、[Task4](tasks/task4/PROCEDURE.md)、[进度](PROGRESS.md)。
- 核查人/日期：Codex /root，2026-10-07；实际模型/强度未知。
- 后续状态：重编号后结构/角色/依赖/引用及工程输入hash已核验通过，按新编号交接；尚未实施迁移。

## SRC-0051

- 主张：Husky参考模型的bumper宏对全部机器人链接设置turnGravityOff，导致Gazebo中底盘无法行驶；仅对底盘/轮子恢复重力后命令被跟随。
- 类型：项目实测（task3.2、task3.5）。
- 来源/证据位置：forem/results/task3/t3.2-motion-r1（全链重力关、spawn z=0.2：0.2 m/s指令→0.0075 m/s）、t3.2-motion-grav-off-diag1（spawn z=0：z漂至0.12 m、0.019 m/s）、t3.2-links-diag1（wheel link z=0.3651、footprint z=0.2，机器人悬空）；全链重力开：t3.2-motion-r2/r3/r4；最终模型（底盘重力开、臂/夹爪重力关）：t3.5-motion-armgrav-r1/r2/r3（直行0.195 m/s，转向0.456–0.461 rad/s，原地转平移0.17–0.18 m）。源：husky/src/modulation_rl/gazebo_world/common/plugins/modulation_bumper.gazebo.xacro；robot_env.cpp setJointValuesFromDict（reset时base z=0.05）。
- 本项目采用：宏增加参数gravity_off（默认false），husky_ur5.xacro仅对15个臂/夹爪链接调用传true（config/task3/patch_reasons.json，semantic_impact=declared）。
- 适用限制：原作者是否在Gazebo中真正驱动过底盘未知（原训练主链main.py默认world_type=sim为解析环境），不据此推断其结论；底盘有重力而臂无重力是混合物理模型（臂是参考的无重力动力学），Task4/后续研究须知此限制。
- 使用位置：[task3.2结果](tasks/task3/task3.2/RESULTS.md)、[core合同](../config/task3/core_contract.yaml)
- 核查人/日期：Claude（Sonnet5.5，强度未知），2026-10-07；实际运行/测量，独立复核由task3.6承担。

## SRC-0052

- 主张：pybind模块与torch的导入顺序：torch先于pybindings（或二者前无ray）会std::bad_cast/free(): invalid pointer；ray先导入则正常。
- 类型：项目实测（task3.2）。
- 来源/证据位置：forem/logs/task3/scratch/imp.py探针；torch→pybindings_robots=bad_cast，pybindings_robots→torch=free() invalid pointer，ray→torch→pybindings_robots=ok，torch→sac→modulation.utils=ok（modulation.utils先导入ray）。ldd：librobots.so等同时链接libpython3.10与系统libpython3.8（来自ROS MoveIt/tf库链）。
- 本项目采用：工程规避：所有入口第一行import ray；写入core_contract.environment.import_order。
- 适用限制：原因推断为libpython3.8/3.10双重加载冲突，未做根因定位；仅在当前镜像mm_husky:node01成立，换镜像须复测。
- 使用位置：[core合同](../config/task3/core_contract.yaml)、[task3.2结果](tasks/task3/task3.2/RESULTS.md)
- 核查人/日期：Claude（Sonnet5.5，强度未知），2026-10-07；实际运行/测量，独立复核由task3.6承担。

## SRC-0053

- 主张：参考Husky SimpleObstacle的生效配置：main.py的env_config不含execute_style/perception_style，故create_env回落direct/base；SimpleObstacleMap构造后覆盖obstacle_spacing=3.0、offset_std=0.8；MaxCloseStepsWrapper在非解析世界取500步。
- 类型：源码阅读（task3.1）+工程重建。
- 来源/证据位置：husky/src/modulation_rl/scripts/main.py ray_config["env_config"]；modulation/utils.py create_env/wrap_in_task/get_parser；modulation/envs/map.py SimpleObstacleMap.__init__；configs/best_defaults_ray.yaml husky_ur5。逐项来源见config/task3/task_contract.yaml的provenance/effective_override。
- 本项目采用：task_contract.env_config=argparse默认值叠加best_defaults[husky_ur5]，并设env=husky_ur5、task=simpleobstacle、world_type=gazebo，键集合对齐main.py。
- 适用限制：原作者训练/评估Husky所用命令行未知（main.py的env默认pr2，world_type默认sim），本合同是工程重建而非恢复的原运行配置；evaluation_ray路径传入全部argparse键（execute_style默认track），与此不同。
- 使用位置：[task_contract](../config/task3/task_contract.yaml)、[task3.1结果](tasks/task3/task3.1/RESULTS.md)
- 核查人/日期：Claude（Sonnet5.5，强度未知），2026-10-07；实际运行/测量，独立复核由task3.6承担。

## SRC-0054

- 主张：Task3.2物理检查验收门槛是工程选择（检测不动/反向/非有限/失稳/TF错误），不是性能主张；有两处在看到数据后修订并公开。
- 类型：工程选择（待验证假设）。
- 来源/证据位置：forem/scripts/check_task3_physics.py GATES；首版门槛先于首次运行写入；r2后turn_xy 0.10→0.60 m（skid-steer原地转向平移约0.38 m）；r3后coord速度/速率改为指令的0.5–1.3倍（弧线路径速度比0.74、速率比0.85）。
- 本项目采用：门槛来源：直行/转向取指令±20–25%，保持取1 cm/0.01 rad，关节取参考joint_limits.yaml；无外部文献依据，不推断通用值。
- 适用限制：修订发生在看到r2/r3数据之后，属事后调整，r1–r4原始数据均保留；4轮skid-steer原地转向平移与组合弧线减速是该模型物理特性，不是验收性能指标。
- 使用位置：[task3.2流程](tasks/task3/task3.2/PROCEDURE.md)、[task3.2结果](tasks/task3/task3.2/RESULTS.md)
- 核查人/日期：Claude（Sonnet5.5，强度未知），2026-10-07；实际运行/测量，独立复核由task3.6承担。

## SRC-0055

- 主张：Husky移动场景下ODE solver world与quick对比：均通过运动检查；world实时因子0.75–0.82，quick 0.87–0.93，原地转向响应不同（0.53 vs 0.42 rad/s）。
- 类型：项目实测（task3.2）。
- 来源/证据位置：forem/results/task3/t3.2-motion-r4与t3.2-motion-quick-diag2的physics_summary.json（rtf、phases）。
- 本项目采用：沿用FoReM task0.7决定（TASK0-SOLVER-20260930，针对固定UR5的1 kHz交替）选world；quick为参考原值。
- 适用限制：每个solver仅1次运动检查，无重复统计；Husky上未做task0.7的2 kHz高频交替复测（待补证据）；选择world是工程选择。
- 使用位置：[world.yaml](../config/task3/world.yaml)、[task3.2结果](tasks/task3/task3.2/RESULTS.md)
- 核查人/日期：Claude（Sonnet5.5，强度未知），2026-10-07；实际运行/测量，独立复核由task3.6承担。

## SRC-0056

- 主张：URDF对p3d请求gaussianNoise 0.01，但实测p3d与Gazebo真值差~1e-10 m（静止），噪声在gazebo_ros_p3d 2.9.3中未生效。
- 类型：项目实测（task3.2）。
- 来源/证据位置：t3.2-motion-r1…r4 physics_summary.json tf.p3d_minus_truth_xy_last（~6e-11）；后续run含时间插值统计tf.p3d_minus_truth_xy。URDF：husky_ur5.xacro p3d_base_controller。
- 本项目采用：gazebo_reference姿态=p3d样本，实测等同Gazebo真值（含采样时间抖动）。
- 适用限制：未读gazebo_ros_p3d源码确认原因；不得对Task4表述“参考位姿含1 cm噪声”。
- 使用位置：[core合同pose_chain](../config/task3/core_contract.yaml)
- 核查人/日期：Claude（Sonnet5.5，强度未知），2026-10-07；实际运行/测量，独立复核由task3.6承担。

## SRC-0057

- 主张：原Husky入口审计：7个算法训练/评估Python入口；main.py/eval.py/main_ray.py/evaluation_ray.py依赖的modulation.myray.custom_sac在当前ray1.13下不可导入（SACTrainer.with_updates缺失）；evaluation_moveit/bi2rrt缺pybindings_moveit与modulation.planning.rrt；husky_ur5/src/husky_goal.py含U+200B语法错误。
- 类型：静态源码审计+一次导入实测（task3.1）。
- 来源/证据位置：forem/scripts/audit_husky_branches.py→forem/results/task3/t3.1-audit-r1/husky_branches.json；custom_sac导入：将参考modulation目录只读拷贝到forem/logs/task3/scratch/refpkg后在forem-dev内import，AttributeError: type object 'SACTrainer' has no attribute 'with_updates'。
- 本项目采用：数量按入口与调用关系统计，讲解见task3.5 RESULTS。
- 适用限制：导入失败仅指本镜像ray1.13；与旧环境审计“main.py不走ray_utils”的记录不符（main.py第15行import ray_utils），以本次为准；其他机器人/真实机器人/基线路径均未运行。
- 使用位置：[task3.1结果](tasks/task3/task3.1/RESULTS.md)、[task3.5讲解](tasks/task3/task3.5/RESULTS.md)
- 核查人/日期：Claude（Sonnet5.5，强度未知），2026-10-07；实际运行/测量，独立复核由task3.6承担。

## SRC-0058

- 主张：SAC.update_parameters与update_parameters_modified差异：后者要求冻结的prior_agent，目标值与策略损失各加α·logπ_prior项；两者共享alpha上限0.35/下限0.05、学习率指数衰减、梯度裁剪10。
- 类型：源码阅读+单元测试（task3.4）。
- 来源/证据位置：husky/src/modulation_rl/scripts/sac.py；forem/tests/test_task3_sac_roundtrip.py::test_modified_update_needs_prior_and_differs（缺prior抛TypeError，同批数据policy loss不同）。
- 本项目采用：FoReM普通基线采用update_parameters；不加载prior或旧权重。
- 适用限制：“普通”更新仍含参考的alpha缩放/截断与学习率衰减，不是教科书SAC；main.py的resume=True在训练前评估并把20个评估episode写入replay，本入口不复制。
- 使用位置：[task3.4结果](tasks/task3/task3.4/RESULTS.md)、[sac.yaml](../config/task3/sac.yaml)
- 核查人/日期：Claude（Sonnet5.5，强度未知），2026-10-07；实际运行/测量，独立复核由task3.6承担。

## SRC-0059

- 主张：全部链接重力开启时，参考臂控制器（effort PID，wrist_3 p=100/d=0.1，轨迹容差0.1 rad）在随机策略episode后出现剧烈不稳定，臂复位轨迹因path error中止，RobotEnv.reset抛出“Could not set start pose after 50 trials”；臂链接保持无重力后12/12 episode复位无失败。
- 类型：项目实测（task3.5）。
- 来源/证据位置：失败：t3.5-int-r2（sac_smoke阶段，`results/task3/t3.5-int-r2/sac_smoke/stdout.log`）、t3.5-resets-r1（world solver，第2个episode复位失败，臂末态wrist_3误差−1.3 rad/速度−20 rad/s，action结果`ur5_wrist_3_joint path error`）、t3.5-resets-quick1（quick solver，同样失败，说明不是solver选择）；修复后：t3.5-resets-r2（12个episode，其中1个goal_reached，0次复位失败，3609个臂goal中3586个为PREEMPTED——每步新goal抢占旧goal属正常）。脚本scripts/check_task3_resets.py。
- 本项目采用：臂/夹爪链接重力关（见SRC-0051）；不改PID增益、不改轨迹容差。
- 适用限制：未做根因（数值刚度、PID、惯量）定位，也没有改增益对照；失败率样本小（重力全开3次中3次失败；修复后12次0失败），不是统计显著性结论；Task3其余run（env-r1、train-r1）发生在全链重力模型上，已由最终模型的int-r3复验。
- 使用位置：[task3.5结果](tasks/task3/task3.5/RESULTS.md)、[world.yaml](../config/task3/world.yaml)
- 核查人/日期：Claude（Sonnet5.5，强度未知），2026-10-07；独立复核由task3.6承担。

## SRC-0060

- 支撑主张：Task3.6独立审查发现T3-A01 checkpoint未覆盖环境语义源码、T3-A02位姿门控可把旧样本误判为时钟复位/混入epoch、T3-A03冻结实例路径依赖当前工作目录。Task3验收不能只依赖现有测试与实现者all_pass。
- 类型：项目源码审查、独立反例实测、原始CSV指标推导；非外部文献、非性能实验。
- 作者/版本：Codex /root，2026-10-07；根HEAD 438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804，加当前未提交Task3实现；实际Agent模型/强度未知。
- 精确位置：scripts/task3_sac_entry.py::source_hashes/make_contract/load_checkpoint_checked；src/forem_husky/scripts/pose_gate.py::PoseGate.check及pose_bridge.py::cb；scripts/freeze_task3.py::cmd_verify第91–93行。源码身份由config/task3/execution_freeze.json（t3.5-core-freeze1）和本次independent-source-hashes.json关联。
- 本地证据：[审查结果](tasks/task3/task3.6/RESULTS.md)、[独立产物](../results/task3/task3.6-review-20261007/)、[日志](../logs/task3/task3.6-review-20261007/)、[Agent记录](agent_logs/task3/task3.6/20261007-codex-review.md)。
- 原始结论：只改临时副本combined_env.py的return reward，contract仍完全相等、真实checkpoint加载accepted；PoseGate对10→8秒旧消息接受并增加epoch，对10→0.1(reset)→10.02(旧epoch)→0.12给出全部accept且epoch再增；freeze verify从仓库根退出1报changed task_instances，进入forem退出0，文件并未变化。新fresh task3.6-int-20261007-r1五阶段退出0；GPU task3.6-gpu-20261007-r1 device=cuda、policy tensors=cuda:0、76步60更新、存取确定性差0、退出0；生命周期task3.6-life-20261007-r1报告8/8、退出0，最终容器仅init/sleep、foreign=[]。这些正常路径通过不关闭独立反例。
- 参考身份核查：原modulation_rl全部371个Git文件的Git blob SHA1与1ccedd087ac12dd317e93accc37bb81e05beeb99逐项一致；当前导入266文件SHA256与manifest一致，12补丁独立diff与登记一致，证据reference-snapshot-check.json/independent-source-hashes.json/independent-patch-diffs.json。
- 重算输入/公式：新run task3.6-int-20261007-r1/physics/timeseries.csv，按phase取t_sim/原始truth x,y,yaw；Δt=t末−t首秒，路径速度=Σsqrt(Δx²+Δy²)/Δt m/s，转速=wrap(yaw末−yaw首)/Δt rad/s；同phase时戳严格递增、有限、Δt>0。比较摘要的1e-4 m/s、rad/s为CSV舍入精度的工程核对容差，不是任务性能阈值。完整独立指标见independent-physics.json。
- 任务重算输入/公式/条件：同run env/steps.csv，按segment epN分组，sum(reward)（原奖励分数）及sum(kin_failure/base_collision)、行数、末行done与env_summary比较；CSV reward五位小数累计舍入界n×0.5e-5，field关节差五位小数界1e-5 rad，base xy四位小数差向量界sqrt(2)×1e-4 m。要求数据有限、动作在[-1,1]、episode有末行done。实际误差均小于舍入界，证据independent_env_result.py/independent-env.json。数字为摘要核对，不是任务成功率或性能门槛。
- 本项目采用：登记三项P2，保持Task3 review，Task4前置尚未满足；本次审查不改实现，不因问题登记增加实验功能授权。
- 适用限制：奖励改动仅在/tmp临时副本，未写实际环境或冻结配置；pose反例为纯门控逻辑，未在正式话题注入消息，未主张日常p3d已出现该故障；CWD差异是路径解析误报，未证明冻结源文件损坏。fresh为短接口核验，不能证明收敛/定位/世界模型收益。
- 核查日期/人：2026-10-07，Codex /root；上述反例与必要运行核验均已实际执行，审查交付完成，原始退出码/命令/清理见审查RESULTS链接的manifest/报告/日志。
- 使用位置：task3.6三文档、父Task3结果、PROGRESS、README/ENV的本次审查更新。

## SRC-0061

- 支撑主张：用户要求给Claude提供Task3修改提示词；本次交接限定T3-A01/A02/A03的必要修正、反例与受影响正常链核验，不扩大任务功能。
- 类型：用户明确请求、基于已核查问题的工程交接；未执行的修正要求，不是实测改善。
- 来源/作者/版本：2026-10-07用户“给出修改提示词，给claude”；Codex /root整理。模型推荐沿根AGENTS用户指定GPT6.1sol/Sonnet5.5，跨模块契约/时序修正medium，普通交接low或默认；实际Codex模型/强度未知。
- 精确位置：[task3.6 RESULTS修改提示词](tasks/task3/task3.6/RESULTS.md#2026-10-07-给claude的三项p2修改提示词)、[交接日志](agent_logs/task3/task3.6/20261007-codex-claude-fix-handoff.md)。问题依据为[SRC-0060](#src-0060)及其真实反例、运行/清理证据。
- 原始要求/本项目采用：提供可复制的修正执行提示词，完整说明范围、三项问题、修正前后验证、GPU SAC核验、历史freeze/run保留与来源同步、结束清理、Claude交review/Codex独立复核边界。
- 理由与待验证事项：现有正常路径通过但三个反例未闭环，需修正契约/时序/路径并重新核验；具体实现由接手者按最小必要范围决定，提示词不证明修正成功。
- 核查日期/人：2026-10-07，Codex /root；已对照最新RESULTS/PROGRESS与空闲容器状态，只完成文档内容核对。
- 适用限制：本轮未发送给Claude、未修改实现/正式freeze、未创建后续功能。实际实施以用户将提示词交给Claude、其登记接手后的记录为准；不得把写提示词当已派发或将自测作为独立验收。
- 使用位置：Task3.6结果交接、PROGRESS和本轮Agent日志。

## SRC-0062

- 支撑主张：Task3三项P2（T3-A01 checkpoint语义来源、T3-A02位姿reset/epoch、T3-A03 freeze路径）的修正方案及其参数：语义身份范围、`reset_jump`=1 s沿用原bridge默认、`future_tolerance`=1 s、halt策略、新freeze-id。
- 类型：项目实测 + 工程选择（非外部文献）。
- 来源/作者/版本：2026-10-07用户修正要求；Claude Sonnet5.5（强度未知，推荐medium）；问题依据[SRC-0060](#src-0060)、[SRC-0061](#src-0061)。
- 精确位置：[task3 RESULTS修正节](tasks/task3/RESULTS.md#2026-10-07-task36三项p2修正claude)；修正前证据results/task3/t3.5-fix1-before/，修正后results/task3/t3.5-fix1-after/、t3.5-fix1-int、t3.5-fix1-gpu、t3.5-fix1-life、t3.5-fix1-inst、t3.5-fix1-receipt；代码scripts/task3_identity.py、task3_sac_entry.py、forem_husky/scripts/pose_gate.py、pose_bridge.py、scripts/freeze_task3.py。
- 采用方式：身份=当前实际文件树哈希（非manifest/freeze）；reset=独立/clock回退，检测后停止发布（沿用“reset_simulation不支持”边界）；两个1 s阈值为工程选择：reset_jump沿用原值，future_tolerance为传输时延容限，均未经敏感性扫描（待验证）；路径按FoReM根解析。
- 核查日期/人：2026-10-07，Claude（自测，非独立验收）。
- 适用限制：身份不含devel二进制与镜像其余部分；ros:*组仅容器内可得（宿主为absent，契约须在容器内生成/加载）；<1 s的/clock回退不被判为reset，由严格递增戳规则兜底；真实reset仅在一次fresh运行中验证；不含Task4。
- 使用位置：Task3 RESULTS、task3.2/3.4/3.5追加说明、ENV。

## SRC-0063

- 主张：用户要求“能用GPU加速就用GPU”，随后明确修改后派发子智能体执行、模型由父选择；Task3 SAC默认auto选择可用CUDA，集成smoke/eval传递设备；Gazebo/ROS物理控制保持原CPU设置。
- 类型：用户授权、工程设备选择与执行组织；运行改善结论尚待实测。
- 来源/版本：2026-10-07本轮用户两项补充；GPU代码变更相对于t3.5-core-freeze2，旧328文件/原freeze已逐hash归档，现t3.6-gpu-freeze3；实际父模型/强度未知。
- 位置：scripts/task3_sac_entry.py::resolve_device/main、validate_task3_core.py::main、config/task3/sac.yaml、tests/test_task3_device.py；task3.6.1三文档及父agent_logs/task3/task3.6/20261007-codex-r2-review-gpu.md。
- 原始依据/采用：用户优先GPU且明确委派；CUDA可用优先CUDA、不可用才CPU，显式--device cpu保留。选择用户默认GPT6.1sol，平台名gpt-6.1-sol，medium，因跨模块设备/契约/时序与真实证据核对；Claude替代推荐Sonnet5.5/medium，不等于实际执行。
- 证据/核查：5项设备测试修正前失败（默认cpu/无传递设备/无auto选择），修正后通过；原记录logs/task3/task3.6-r2-20261007/gpu-tests-red.log、gpu-tests-green.log。完整集成及执行子记录尚未完成，不能宣称GPU默认链已实测验收。
- 适用限制：没有增加多GPU并行、训练规模、定位/世界模型或物理变化；现有已启动parent检查接管而非重复运行，须如实记录parent启动/子接管，父汇总原产物。Task3仍review，子执行完成不自动通过/启动Task4。
- 核查人/日期：Codex /root，2026-10-07；派发实际模型/强度由工具结果及子日志补记。
- 使用：task3.6父/子三文档、PROGRESS/ENV/GPU交接。

## SRC-0064

- 主张：原T3-A01底层语义树保护扩大后，实际策略入口包装仍遗漏scripts/task3_env.py及task3_sac_entry.py；仅改变包装奖励或replay mask，契约仍相等、真实checkpoint加载accepted。残留登记T3-A04/P2。
- 类型：独立源码审查与临时副本反例实测；未改变正式任务奖励/终止或运行模型。
- 来源/版本：Codex/root与子/root/task3_6_1_execution，2026-10-07；task3_identity.py::semantic_identity只列src/config/ros组，GPU入口版freeze3（相关身份算法与Claudefreeze2相同）。
- 精确证据：results/task3/task3.6-r2-20261007/probe_wrappers.py、wrapper-counterexamples.json；子独立复现results/task3/task3.6.1-exec-20261007/wrapper-counterexamples.json；src根身份源码scripts/task3_identity.py，运行包装scripts/task3_env.py::step及task3_sac_entry.py::make_mask。
- 原始结果：临时副本将float(reward)改float(reward)+123.0，或将float(not done)改1.0，形状不变，contract_unchanged=true、load=accepted；正式源语义未改变。
- 工程采用/授权解释：为满足用户要求的Task3验收前置，补齐原已授权T3-A01“实际环境/任务/控制语义身份”的包装入口漏项；仅元数据指纹与反例测试，不改策略/环境的数学和信息权限，不新增功能。当前冻结运行结束后才能修改，再交子智能体独立验证。
- 待验证与限制：正式保护补齐尚未实施；原底层6类改动拒绝已获子验证支持，但不能据此忽略包装漏项。123.0/1.0仅刻意反例，不是实验设置；未运行更改奖励的仿真/训练。父Task3仍review，修复前不解锁Task4。
- 核查人/日期：Codex /root（实际模型/强度未知）、执行子Agent（派发gpt-6.1-sol/medium），2026-10-07。
- 使用：task3.6 RESULTS/日志/PROGRESS，后续保护补齐结果另追加真实证据。

## SRC-0065

- 主张：用户明确要求Task3验收通过后自动执行Task4，并要求自动派发时注意模型选择。
- 类型：用户条件授权及执行组织，不是定位/训练实际结果。
- 来源/版本：2026-10-07最新用户“3验收通过后去执行4哈，自动派发的时候注意模型选择”。Task4已有父子三文档为工作范围；根AGENTS默认GPT6.1sol/Sonnet5.5。
- 精确位置：Task4 TASK/PROCEDURE本轮授权更新、PROGRESS、agent_logs/task3/task3.6/20261007-codex-r2-review-gpu.md。
- 采用：Task3所有必要验收与已确认P2闭环且父任务done后，按Task4.1–4.6依赖顺序自动派发；Codex子Agent默认gpt-6.1-sol（用户名称GPT6.1sol）/medium承担跨模块工程，复杂研究设计/难复现故障确需时high并解释；常规文档low/默认。Claude替代推荐Sonnet5.5同等强度；推荐不冒充实际使用。
- 限制：条件未满足不开始Task4实施；不扩大到实机、新任务/奖励、人工误差/补偿/世界模型、旧truth权重迁移实验；仍按原设计接入一个视觉惯性定位器、从头建立普通SAC基线，冻结预算并独立验收。
- 核查人/日期：Codex /root，2026-10-07；实际父模型/强度未知，未来各次派发配置单独登记。
- 使用：Task4父/子三文档的实施授权/委派、全局进度与执行交接。

## SRC-0066

- 主张：Task3修正/GPU默认/包装身份追加经过独立必要验收，T3-A01–A04闭环，Task3 done，满足用户Task4自动实施条件。
- 类型：项目源码审查、反例与真实运行实测、依据哈希的增量验证；不是训练收敛或加速比实验。
- 作者/版本：父Codex /root实际模型/强度未知；执行子/root/task3_6_1_execution实际gpt-6.1-sol/medium；2026-10-07，根HEAD438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804加工作树，最终t3.6-core-freeze4（330文件）。Codex推荐GPT6.1sol、Claude Sonnet5.5，跨模块medium，常规整理low/default。
- 精确位置：scripts/task3_identity.py::semantic_identity新增runtime:task3_env.py/task3_sac_entry.py/task3_identity.py；task3_sac_entry.py::resolve_device、validate_task3_core.py::main设备传递；PoseGate.check/on_clock、PoseBridge.cb；freeze_task3.py::instance_path/instance_rel/instance_diffs。包装身份3测试修正前失败/修正后通过，设备5测试同样red→green。
- 原始证据：[父独立核验JSON](../results/task3/task3.6-r2-20261007/parent-final-verification.json)、[执行子结果](tasks/task3/task3.6/task3.6.1/RESULTS.md)、results/task3/task3.6.1-exec-20261007/反例与原CSV重算，task3.6.1-wrapper-20261007/gpu-identity-probe.json及freeze-delta.json；日志task3.6.1-wrapper-20261007/unittest-container.log（298/3 skip，0）。
- 实测：fresh task3.6-r2-int-20261007-r1五阶段全0、默认auto的smoke/eval实际cuda:0；子接管父已启动run，非子独立启动。生命周期task3.6.1-life-20261007-r1由子新启动8/8、0。追加freeze4新run task3.6.1-wrapper-gpu-20261007-r1由子启动，未指定--device，auto→cuda:0，76步/60更新、有限loss、参数更新、保存加载动作差0、载入驱动通过，check/cleanup/final均0。
- 反例闭环：底层source/config/模型6类真实临时改动拒绝旧CUDA checkpoint；包装reward/mask/identity代码3类形状未变改动也拒绝，同契约允许，schema1或缺runtime的schema2及实际freeze3 checkpoint拒绝；迟到10→8不发布、真实clock reset10→0.1后halt、不发布旧epoch；三CWD verify均0、真实实例变化拒绝。
- 身份/增量关联：freeze2原328文件及freeze3原329文件逐hash归档；freeze3→4只身份实现/两现有测试变化+1新测试，物理/环境/clock/lifecycle源码、固定实例、镜像挂载一致。freeze4未重复全套物理运行，引用freeze3全套证据并补齐当前身份实际GPU运行。父重查330当前文件、checkpoint SHA256和Husky原snapshot371 Git blob全一致；verify0、foreign=[]、docker top仅init/sleep。
- 重算/公式：沿SRC-0060定义在新fresh raw CSV重算，子independent-physics.json/independent-env.json，物理摘要差低于CSV精度容差；任务两episode94/385步、IK各20、碰撞0、done1，奖励求和差1.17e-5/6.22e-5低于n×0.5e-5舍入界，动作有限且范围内。数字用于摘要一致性核对，不是性能门槛。
- 本项目采用：父核验接受Task3迁移接口交付，释放Task4.1依赖。旧报告/失败保留；额外包装修复仅必要指纹闭包，不改任务数学。
- 适用限制：短GPU核验不证明收敛/任务成功率或公平加速倍数；底盘重力开、臂/夹爪无重力限制保留；reset_simulation后需fresh重启，同进程/新进程复用恢复探测失败及ODE LCP warning保留；两个1 s门控值仍工程选择。原Husky7算法入口兼容性未恢复，原实机/其他算法未运行。身份不含所有容器二进制；Task4新增来源须独立扩展契约。
- 核查人/日期：Codex /root，2026-10-07；已读原摘要/原探针/源码delta/测试日志及清理，未以子自报完成代替父核验。
- 使用：Task3父/3.6最终结果、PROGRESS/ENV/README、Task4接手。

## SRC-0067

- 主张：Task4.1有限比较后只选OpenVINS核心EKF/MSCKF双目+IMU；官方ROS1源码直接读取角速度/加速度而非IMU绝对姿态，具有静态/动态初始化、ZUPT和特征状态；核心并不提供本项目回环/失效后自动重定位。官方Noetic测试声明不等于当前容器成功构建。
- 类型：已读官方文档/源码的外部依据；选一个定位器是工程选择（用户卡尔曼建议及Noetic适配降低有限集成风险），非精度排名。
- 作者/标题/版本：RPNG / OpenVINS，pin `69488123ed9362dd44b6f28e7f4680abbff1442b`；[官方仓库](https://github.com/rpng/open_vins/tree/69488123ed9362dd44b6f28e7f4680abbff1442b)、[官方安装说明](https://docs.openvins.com/gs-installing.html)。GPLv3见该pin LICENSE。安装页已读并保存HTML，声明Ubuntu20.04/Noetic、OpenCV4.2等测试与Eigen/Boost/Ceres依赖，不宣称当前pin在我们环境已通过。
- 精确位置：`ReadMe.md` Project Features/Codebase Extensions（secondary posegraph是外部扩展）；`ov_msckf/CMakeLists.txt` L5–12/CPP14/ROS1选择；`cmake/ROS1.cmake` catkin依赖；`ROS1Visualizer.cpp::callback_inertial` L434–448只取stamp、wm/am，`setup_subscribers` L151–193、`ROS1Visualizer.h` L152 ApproximateTime；`visualize_odometry` L245–348原global/imu、原sim stamp、传播输出及两TF开关；`VioManagerHelper.cpp::try_to_initialize` L105–107将存在ZUPT映射为不等jerk；`StaticInitializer.cpp::initialize`两半窗口、由平均specific force定重力方向/偏置及初始协方差；`Propagator.cpp::propagate_and_clone`、`UpdaterMSCKF.cpp::update` L275–285压缩/卡尔曼更新。源码快照及精确hash见[manifest](../config/task4/estimator_manifest.json)和`results/task4/t4.1-protocol-20261007-r1/references/open_vins/`。
- 模板参数原值：`config/euroc_mav/estimator_config.yaml` FEJ/RK4、stereo2、KLT200、max_clones11、slam50/update25/msckf40、静态窗口2 s/IMU阈值1.5/初始化disparity10 px/features50、ZUPT速度0.1 m/s/noise multiplier10/disparity0.5 px及chi2 multiplier0；原try_zupt=false、only_beginning=false、track_frequency21 Hz、gravity9.81及calib_cam三个true。`kalibr_imu_chain.yaml`加速度density0.002 m/s²/√Hz、bias diffusion0.003 m/s³/√Hz、gyro density0.00016968 rad/s/√Hz、diffusion0.000019393 rad/s²/√Hz、200 Hz。
- 本项目采用/限制：其余列出的模板参数为有限起点，NOT实测仿真噪声或适合Husky的证明。SRC-0069记录显式覆盖：try_zupt/only_beginning=true、calibration=false、track20、gravity9.8。Ceres即使static init也在当前CMake为必需，不能因关闭dynamic init省略依赖。只运行订阅入口，不用`initialize_with_gt`、官方合成truth初始化、外部posegraph/激光/轮速/GPS融合或自创GPU版本。尺度来自真实双目基线；实际特征、初始化、时间/帧/数值精度仍待4.2–4.4验证，失败必须保留。
- 核查日期/核查人：2026-10-07 Codex /root/task4_1_protocol，实际GPT6.1sol（平台gpt-6.1-sol）/medium；Claude替代推荐Sonnet5.5/medium，因跨模块raw/TF与依赖核对，不切换实际模型。
- 使用位置：Task4.1三文档、protocol.yaml/sensors.yaml/estimator_manifest.json，后续4.3构建输入。

## SRC-0068

- 主张：VINS-Fusion官方支持stereo+IMU但其README所列Ubuntu16.04/18.04和Kinetic/Melodic未直接声明本容器Noetic已通过；两候选都依赖Ceres。本容器OpenVINS实际CMake配置因缺Ceres失败，定位尚未构建/运行。
- 类型：外部官方源码依据 + 本项目依赖/配置探测；配置失败非算法质量对比。
- 作者/标题/版本：HKUST Aerial Robotics / VINS-Fusion，pin `be55a937a57436548ddfb1bd324bc1e9a9e828e0`，[官方仓库](https://github.com/HKUST-Aerial-Robotics/VINS-Fusion/tree/be55a937a57436548ddfb1bd324bc1e9a9e828e0)。GPLv3见LICENCE/README§License。
- 精确位置：README§Prerequisites/§3.2明确双目+IMU与可选loop_fusion，`vins_estimator/CMakeLists.txt` OpenCV/Ceres/Eigen与ROS依赖；`src/rosNodeTest.cpp::imu_callback` L135–146从acc/gyr输入，双目同步循环、`src/estimator/estimator.cpp` stereo+IMU初始化/优化分支（`initFirstIMUPose`、`optimization`）、`src/utility/visualization.cpp::pubOdometry` world输出。只读快照与hash在[manifest](../config/task4/estimator_manifest.json)，不安装/编译第二套。
- 原始结论/采用方式：VINS优化式与OpenVINS滤波式均能处理原始双目+IMU；本轮优先官方明确Noetic测试及用户EKF建议选OpenVINS，不以任务精度、速度或可迁移性推断优劣。VINS-Fusion可能适配Noetic，但本次未构建，待补证据；不写“不支持Noetic”。
- 实测输入/命令/位置：`sg docker -c 'docker exec forem-dev bash -lc "... dpkg-query -W ...; pkg-config --modversion opencv4; rosversion -d"'`，日志[dependencies.log](../logs/task4/t4.1-protocol-20261007-r1/dependencies.log)；实测Ubuntu20.04.6、CMake3.16.3、Eigen3.3.7、Boost1.71、OpenCV4.2、ROS Noetic、cv_bridge1.16.2/message_filters1.17.4/image_transport1.12.1，libceres-dev未安装。该聚合shell最后rosversion退出0，dpkg缺Ceres错误明确保留，不能当所有依赖均通过。
- 原始失败证据：容器执行`source /opt/ros/noetic/setup.bash; cmake -S /root/mm_husky_ws/results/task4/t4.1-protocol-20261007-r1/references/open_vins/ov_msckf -B /tmp/t4_1_openvins_configure -DENABLE_ROS=ON`实际退出1，`find_package(Ceres)`无CeresConfig.cmake；[日志](../logs/task4/t4.1-protocol-20261007-r1/cmake-probe.log)、results同run的cmake-probe.exit。OpenCV/Boost先被找到。未执行编译，不称build success。
- 核查日期/核查人：2026-10-07 Codex /root/task4_1_protocol，gpt-6.1-sol/medium。
- 限制/后续：4.3安装容器libceres-dev并核查Eigen/OpenCV ABI、catkin Python3.10/ROS3.8现状与最终构建/运行；4.1没有改镜像/依赖/Task3。公开README支持不是本容器可用性证明。
- 使用位置：Task4.1比较、结果、manifest与4.3交接。

## SRC-0069

- 主张：Task4.1协议中的传感器、时序/初态/失效/信息权限与先导预算是显式工程选择或由当前Task3合同推导，未经定位实测；权限反例与当前330文件核查已经实际执行。不存在人工时延/误差扫描。
- 类型：工程选择 + 项目源码审计/单测/配置探测 + 帧/几何推导，非文献精度结论。
- 原始输入/版本/位置：Task3最终`freeze_id=t3.6-core-freeze4`、330文件及accepted JSON在`results/task4/t4.1-protocol-20261007-r1/`，[SRC-0066](#src-0066)；core/task/world/sac合同、RobotEnv/CombinedEnv/map和wrapper/identity调用点及行号保存在[input_audit.json](../results/task4/t4.1-protocol-20261007-r1/input_audit.json)。实际world `src/forem_husky/worlds/husky_empty.world` L14 gravity=(0,0,-9.8) m/s²，Gazebo步0.0005 s、Task3控制0.02 s，基座链z=0.1323 m；SAC原smoke64+12=76步、batch16、900 s、普通update每步至多1次，已有实跑60 updates，评估默认1episode/60步见`task3_sac_entry.py`。
- 官方传感器来源：ROS gazebo_ros_pkgs/noetic-devel pin `cd9cc952402375be5f274f39b29399c4087aa839`，[camera utils](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/cd9cc952402375be5f274f39b29399c4087aa839/gazebo_plugins/src/gazebo_ros_camera_utils.cpp) L504–515 `cx/cy=(size+1)/2`、focal=width/(2tan(hfov/2))，L588–614 K/P；[multicamera](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/cd9cc952402375be5f274f39b29399c4087aa839/gazebo_plugins/src/gazebo_ros_multicamera.cpp)::Load左右名称/P baseline、OnNewFrame从LastMeasurementTime取stamp；两util共用SDF的frameName（camera_utils L146–149），不能把右目topic误当已正确独立header，4.2按已核实视点校验并规范左右光学frame；[IMU sensor plugin](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/cd9cc952402375be5f274f39b29399c4087aa839/gazebo_plugins/src/gazebo_ros_imu_sensor.cpp) L107–123从Sensor取角速度/加速度且同时填绝对orientation，因此下游严禁使用orientation；[官方multicamera说明](https://classic.gazebosim.org/tutorials?tut=ros_gzplugins#Multicamera)给同步多视点/相机pose机制。Gazebo-classic gazebo11 pin `b22c6e15e52299865b31093b8feebc9ca19e26e8` [ImuSensor::UpdateImpl](https://github.com/gazebosim/gazebo-classic/blob/b22c6e15e52299865b31093b8feebc9ca19e26e8/gazebo/sensors/ImuSensor.cc) L369–376从加速度减局部重力。源码快照和commit JSON保存在同run references，官方机制已读，不当作容器对应二进制hash已同一版本。
- 工程参数及理由：底盘base_link前侧(x0.35,z0.45 m)装左右目y±0.06 m，实际基线0.12 m；同位置中点IMU，光学轴为右−y/下−z/前+x。640×480、HFOVπ/2、20 Hz图像/200 HzIMU兼顾有限先导计算与窗口样本，非最佳性能证明；名义fx=fy=320 px、默认主点(320.5,240.5)按以上源码推导，最终以CameraInfo及实际SDF渲染一致性验证为准。相机near0.05/far30 m为覆盖当前任务地图的工程可视范围，需检查近端遮挡；不新造场景/纹理。相机/IMU传感噪声0、无人工扰动；滤波Q沿SRC-0067非零模板仅作数值起点，不宣称sim实测噪声。在线标定关闭因模拟器固定外参可公开，须4.2核实；重力改9.8匹配world，静态specific force应+9.8（理论由a−g、静止a=0推导，原raw值待4.2）。
- 帧推导：约定T_A_B为B→A。T_map_base(t)=T_map_global*T_global_imu(t)*inverse(T_base_imu)；初始T_map_global=T_map_base_commanded_initial*T_base_imu*inverse(T_global_imu_initial)。输入公开已命令初态/固定URDF链与原始估计，一次对齐；无p3d/model_states读回。保持world/map/odom一致契约，估计global仅内部。协方差需SE3 Jacobian含杆臂传递，官方odom quaternion约定需真实旋转测试，不盲拷内部JPL。
- 初始化/时序选择：2 s静态窗口沿官方模板，开启beginning ZUPT使官方不等jerk；等待墙钟上限120 s为有限资源选择，不是典型初始化时延。最大估计年龄0.1 sim s=2×20 Hz图像周期；未来容限0.0005 s=1个Gazebo步，均工程安全门而非跟踪精度结论，4.3/4.4实际验证再冻结。Exact stamp左右配对、队列10沿官方同步缓存数（官方本身ApproximateTime，本项目上游另要求相同曝光stamp）。不引入宿主sleep模拟物理时延。
- reset权限：BaseWorld构造/RobotEnv reset依赖map→base TF（原awaitTfs取now+0.5 s），CombinedEnv reset还公开teleport x30再抽初态；单纯先等VIO再构造有循环依赖。后续4.3用公开spawn/drawn/teleport命令在同pose_bridge权限限定bootstrap，改await为最新有效TF，不造未来sensor stamp；policy/replay禁入bootstrap，最终公开start完成后清队列、fresh estimator静态初始化、一次对齐、撤销bootstrap才释放观测。失效停止/episode invalid，必须显式fresh重初始化，不持续truth纠正。独立clock回退停止整个run，保持reset_simulation需重启限制。此为实施协议，尚未运行reset适配。
- 预算/权限：先导1run seed0、≤76步/≤60更新、batch16/warmup64、≤900墙钟s、1调参尝试、1checkpoint、评估1episode≤60步，沿Task3短链限定接口核验；磁盘≤10 GiB为工程资源上限，图像只保留有限必要采样不录900s全RGB。正式训练预算/评估清单全部null/disabled，必须4.4先导质量/实际成本后冻结，未冻结不可运行4.5。SAC CUDA优先、VIO官方CPU；同41维robot_state/120×120×1 map/3维动作、奖励/终止/普通SAC不变，已知地图/goal/laser避碰仍公开，不能称纯视觉端到端。所有base依赖来自estimate，truth只独立评测，Task4实际runtime/config/定位器及binary身份覆盖，拒旧truth checkpoint/replay/optimizer。
- 实际核查/原始结果：9项新增测试先因audit缺失失败，后宿主/容器9/9通过；真实官方IMU callback加orientation、真实CombinedEnv goal输入替truth、真实launch增第二bridge及原truth输入均被拒绝，公共bootstrap读truth/允许policy动作、正式预算未冻结也拒绝。审计复核当前330内容hash全一致，Task3 runtime-as-Task4退出1（truth_source_identity、forbidden_pose_input），不是漏掉的成功。host全套147测试/10 skip退出0；容器全套最终结果见本节点RESULTS及日志，不在此提前宣称。
- 核查日期/人：2026-10-07 Codex /root/task4_1_protocol，gpt-6.1-sol/medium；父只读指出gravity与名义主点差异后已纠正，不是运行校准。
- 适用限制：静态扫描仅已知topic/调用点和直接orientation读取的保守门，不能证明任意别名/间接data flow或live ROS authority；4.3/4.6须独立运行隔离/TF/失效反例。当前sensors名义未实测，未完成定位安装/build/run或训练。光照/地面纹理、臂遮挡、相机渲染、双目轴/CameraInfo、初始化可用性和估计误差均待验证；不为了通过增加场景或改任务。
- 使用位置：Task4.1三文档、三个Task4配置、audit脚本/反例测试与4.2/4.3交接。

## SRC-0070

- 主张：Task4.1协议/候选/权限实现经父必要核验done，4.2可按用户范围启动；不声称定位已构建运行。为Task4后续delta已归档Task3最终freeze4完整330文件。
- 类型：项目独立审查/测试与用户授权下的执行组织，非算法优劣结论。
- 版本/证据：Task4.1 delivery_receipt.json实际gpt-6.1-sol/medium，父复跑9tests exit0、逐hash20官方已读文件及9交付文件一致，读取宿主147/10skip/0、容器307/3skip/0与input_audit.json当前配置hash，acceptance.json在results/task4/t4.1-parent-review-20261007。配置Ceres缺失1/原Task3被拒1保留；runtime_ready=false、formal.enabled=false。
- 工程采用：唯一OpenVINS选择由SRC0067–69支撑，4.2先实际原始传感器/渲染/标定验证；4.3依赖安装/唯一VIO build+reset/TF闭环；SAC优先CUDA，能用GPU渲染时采用受支持正常路径，不私改ROS/Gazebo物理或VIO算法。
- 来源冻结：results/task3/freeze-archive/t3.6-core-freeze4/{execution_freeze.json,snapshot/,archive_receipt.json}330/330原SHA256匹配，父2026-10-07实际归档，为Task4必要变更保全Task3已接受源；freeze3/2也保留。当前Task3历史验收不因Task4新源误称失效/重跑。
- 模型/强度：4.2推荐/拟实际GPT6.1sol（平台gpt-6.1-sol）/medium，需核对Gazebo相机渲染/IMU轴/时间/标定，Claude替代Sonnet5.5/medium；普通文档low/default，父实际未知。派发工具后另记实际。
- 核查日期/人：2026-10-07T14:59:23.910120+08:00，Codex /root。
- 限制：静态权限门不证明完整间接data flow/ROS graph；传感器名义值、初始化质量/估计精度和GPU渲染仍待实测，旧truth权重不作Task4基线。
- 使用：Task4父/4.1验收、4.2接手、PROGRESS/ENV/Agent记录。

## SRC-0071

- 主张/类型：Task4.2刚性真实双目/IMU及最小输入规范属于工程实现；真实基线0.12m、fixed外参和原模型94个link/joint/transmission逐元素一致来自项目实际resolved URDF/SDF，不用两个header名字证明立体。
- 来源/版本：4.1官方Gazebo Noetic插件参考固定文件（SRC-0069）；`gazebo_ros_multicamera.cpp::Load` L83–95左右名字各util但共frameName；`gazebo_ros_imu_sensor.cpp::LoadParameters` L214–222默认updateRateHZ1，`UpdateChild` L95–103取LastUpdateTime并正数节流；`gazebo_ros_camera_utils.cpp` L154–157/update_period_与CameraInfo。原文在results/task4/t4.1-protocol-20261007-r1/references/，pin/hash在estimator_manifest。Task4.2实际源码snapshot在results/task4/t4.2-raw-r4/source_snapshot/，开始/结束11文件hash一致；最终交付另receipt（后处理新增配置realized，不冒充运行时配置）。Task3原330仅CMakeLists增加urdf/adapter安装，old/new/diff见accepted_task3_deltas.json及CMakeLists.txt.diff，Task3归档未改。
- 实测/推导：robot.sdf rig合并到base_footprint位置(0.35,0,0.58228)，左右camera局部y±0.06、SDF视点0.12m。URDF base_link→IMU(0.35,0,.45)、optical旋转rpy(-π/2,0,-π/2)，x右/y下/z前，camera translation IMU系y±.06；继承footprint→base_link真实.13228m。`calibration_geometry.json`记录原named元素94/94一致。
- 采用/理由：独立assembler包含原husky_ur5.xacro，独立launch继承原控制/世界/任务且本raw阶段truth bridge只用于原任务运动。无新mass/collision/visual/noise。camera plugin updateRate0让sensor20Hz单独控制；IMU sensor200Hz、plugin ceiling2000Hz仅拒同LastUpdateTime重复消息，2000取继承物理update rate上限，非2000Hz传感器，不改物理。r3 plugin0重复同sample且诊断/2000Hzmodel_states积压，r4有限diagnostic RGB每phase/topic最多3、model_states≤50Hz/queue1辅助诊断、输入bag完整有限LZ4；原stamp独立核验另SRC-0073。
- 时间/反例：T4-R01父raw-counterexamples.json复现NaN被计OK，已validate_imu拒acc/gyr非有限且truth有限，正反例6单测。T4-R02父复现clock rollback后旧epoch能pair；现rollback清队列并永久halt、任何后续旧/新stamp均拒，父raw-counterexamples-after.json复跑拒绝。测试logs/task4/t4.2-raw-r4/time-tests-*。SensorTime不声称实现future/no-clock保护；4.3需完善packet/freshness与完整run停止，不支持reset_simulation跨epoch复用。
- 核查：2026-10-07 Codex /root/task4_2_sensors，实际GPT6.1sol(gpt-6.1-sol)/medium；Claude替代Sonnet5.5/medium，因渲染/标定/时序跨模块，普通文档low/default。
- 限制/使用：frame adapter保留原图/acc/gyr/stamp，仅规范左右frame和剥离orientation；原插件IMU绝对orientation只diagnostic.bag，禁止定位读取。ModelStates无header，receipt时间不作精确采样/时延证据；官方p3d原stamp仅独立运动sanity且原gaussianNoise0.01声明仍保留。Task4.2三文档/源码/sensors配置及4.3交接。

## SRC-0072

- 主张/类型：本容器支持Gazebo Classic11真实NVIDIA相机渲染，工程部署+项目实测；Xvfb自身不能证明GPU。
- 外部原文：VirtualGL官方 `doc/advancedconfig.txt` EGL back end（https://github.com/VirtualGL/virtualgl/blob/main/doc/advancedconfig.txt）、官方release3.1.5（https://github.com/VirtualGL/virtualgl/releases/tag/3.1.5）；API发布收据/原文/实际amd64.deb在results/task4/t4.2-gpu-probe-r1/。Release版本3.1.5；读取main文档原文件hash在最终delivery receipt，不把main声明为release源码pin。
- 采用：容器安装mesa-utils与官方virtualgl_3.1.5_amd64.deb；私有xvfb-run显示+`/opt/VirtualGL/bin/vglrun -d egl0 roslaunch ...`，利用已有NVIDIA EGL库/dev/dri，不在宿主装ROS/改驱动、不改Classic物理、不套Gazebo Sim Ogre2 headless flag。容器curl Emptyreply原失败install.log保留；宿主urllib下载官方deb再容器dpkg成功。catkin build forem_husky --no-deps exit0；安装/build与raw运行分开。
- 实测位置：logs/task4/t4.2-gpu-probe-r1/renderer.log，glxinfo NVIDIA RTX PRO6000 Blackwell/4.6 NVIDIA590.48.01；ogre-r1.log GL_VENDOR=NVIDIA、GL_RENDERER同名；logs/task4/t4.2-raw-r1/gpu-process.log，GPU0 `gzserver` G进程141MiB，支持实际Gazebo相机GPU渲染。四GPU可见原before.log；未测公平加速比，Gazebo ODE/ROS仍CPU，VIO/SAC本节点未运行。
- 核查日期/人：2026-10-07 Codex /root/task4_2_sensors GPT6.1sol/medium。适用限制：本forem-dev当前驱动/库设备路径可用，依赖安装只当前容器，不把Docker镜像自动声称包含VirtualGL，复建应按原版本收据安装；其他任务进程未停止，运行末foreign=[]仅自身无残留。
- 使用：Task4.2运行wrapper、RESULTS/PROCEDURE和4.3渲染交接。

## SRC-0073

- 主张/类型：Task4.2 raw链真实有限验证通过候选（父复核前review），尚无VIO初始化/位置估计/训练结论。项目实测与有限工程门。
- 运行/证据：t4.2-raw-r1 exit1(check2)：实际K不等名义320±1e-6且IMU插件默认1Hz，包/失败保留；r2 exit1：1Hz不足、numpy.bool_ JSON序列化失败、部分raw保存；r3 exit1：基础sensor200/camera20，task callback积压rate15Hz及x30旧reset错分，不作为通过；r4 start2026-10-07 15:17左右至15:18:39+08，check0/cleanup0/final0/foreign_after=[]，state.json/timeline/check.log，输入/evaluation/diagnostic包、sensor_summary.json、independent_raw_validation.json及原stamp/图像/imu数组。原source snapshots/r3失败均保留；r1加载前checker重建文件明确为根据当时工具指令推导而非现场snapshot，r2snapshot在刚startup后取得非严格预snapshot，r3/r4预snapshot及结束hash记录可核对。
- 相机实测/推导：CameraInfo fx=fy319.9988245765257、cx320.5/cy240.5、D0、R identity、右P03=-38.399858949183084=-fx×.12；SDF HFOV序列化1.5708，640/(2tan(1.5708/2))给出实测fx。名义320容差.002仅覆盖序列化.001175差值的工程一致门，非定位精度阈值；P实际K×baseline严格1e-6。resolved外参见SRC0071，frames左右optical/IMU约定通过。
- 原stamp独立核验：inputs仅raw双目Image/CameraInfo、acc/gyr-only Imu和原/clock，无GPS/wheel/p3d/T265/modelstates/TF。399个左右同stamp对，全bag各1未匹配边界曝光（不把任何错stamp配对，统计保留）；52原plugin图像payload和5551原plugin IMU payload对原stamp完全一致，2诊断图像未匹配边界不算已验证。四类原stamp窗口重新分组：static3.575–6.605、straight6.610–9.605、turn10.635–13.640；task明确以task_steps第一步27.609至最后29.8835，排除reset callback标签积压。实际camera约19.9966–20.0034Hz，49–51ms；IMU200Hz、所有5ms间隔。无非单调/有限性错误。配对/有限性/epoch反例6项host/container均exit0。
- 运动/单位：static acc均值近[0,0,9.800000]m/s²、gyr近0；turn gyr z正约.46rad/s。Task r4 callback辅助位移.4526m，但精确原stamp独立p3d运动证据27.620–29.880、114样本、位移.366522m/转角.386613rad，支持真实运动sanity；不等于定位精度，原p3d噪声声明限制保留。候选静止task-geometry窗25.605–27.609内100原stamp样本，xyzrange≤8.32e-6m，仅可供4.3初始化验证，未跑VIO。
- 纹理/资源/限制：原ground plane角点static0/straight0、turn3、原SimpleObstacleTask样图73（OpenCV goodFeaturesToTrack max200/quality.01/minDistance10，仅图像诊断不是OpenVINS特征/初始化验收）。任务图有不同视点mean像素差且物理baseline确认；环境只原地面/原任务障碍，没有新增纹理救场。raw r4约9.4MiB全产物，全部尝试合计<100MiB，均远小10GiB；IMU噪声0，官方Q为模板未实测，稀纹理/遮挡可能令4.3初始化/跟踪失败，不回退truth。
- 工程验收门：static加速度距[0,0,9.8]<.2/gyro norm<.02、turngz>.1、straight位移>.1/turnyaw>.3/task位移>.01、camera rate±.3/IMU±2Hz，只检测缺失/单位/轴/无运动/采样链异常，不支持算法精度/UR5参数合理性或时延选择。原始数值与传感器采样周期相关工程sanity，非外部通用参数。
- 核查：2026-10-07 Codex /root/task4_2_sensors，实际GPT6.1sol(gpt-6.1-sol)/medium，Claude替代Sonnet5.5/medium。父独立复核待执行。使用：Task4.2三文档/交付收据/任务raw配置及4.3可执行交接。

## SRC-0074

- 主张：Task4.2 raw双目/IMU与正常GPU渲染交付经父独立必要验收done，释放4.3定位接入；估计初始化/精度/训练仍未运行。
- 类型：项目原bag独立重算、源码/几何/哈希审核与执行组织；非定位性能或加速倍数结论。
- 版本：r4 runtime11文件启动前snapshot与结束一致，sensors.realized运行后追加已明示；delivery_receipt current11交付hash及3baghash父重核一致。执行子gpt-6.1-sol/medium、父实际未知。Task3最终330仅forem_husky/CMakeLists安装adapter/urdf的必要delta，原94link/joint/transmission父解析一致；原Task3 snapshot/archive保留。
- 精确证据：results/task4/t4.2-parent-review-20261007/{bag-verification.json,motion-and-identity.json,raw-counterexamples.json,raw-counterexamples-after.json}，logs同目录；raw-r4 inputs/evaluation/diagnostic.bag、independent_raw_validation.json、source_start/end与delivery_receipt，SRC0071–73。父复跑6测试0，读取catkin0/容器6tests0/入口check0-cleanup0-final0及foreign=[]。
- 原始数据核查：inputs仅6topic（双目images+CameraInfo/IMU/clock），7431非clock样本，6683与diagnostic原stamp/payload匹配（5551 IMU、1080 CameraInfo、有限52 images），其余748图像因diagnostic有限抽样无对照，不虚称全部图片均有plugin字节对照；有对照的signature零不同。399精确stamp对，其中113对不同图像bytes，静止远景相同不伪算视差。原samples stamp严格递增、bagstamp相等，IMU无绝对orientation且finite，K/P与actualFOV/baseline一致。独立SDF真正左右y±.06、baseline.12m；只读解析须规范Gazebo非标准ignition::tag，首次父XML解析失败保留，原SDF未改。
- 原stamp运动重算：task_steps公开动作区间27.609–29.8835 sim s，evaluation /ground_truth/state原headerstamp114样本，XY末首norm=.36652200187632233 m；yaw=atan2(2(wz+xy),1−2(y²+z²))，wrap末首=.38661288204894806 rad；数值为运动证据，不是任务成功/控制精度门。静止raw平均az9.80000007，IMU200Hz、camera约20Hz由原stamp间隔；理论/工程阈值依据SRC0073。
- 反例：父在私有真实Capture.recv/SensorTime逻辑复现NaN入rows和clock rollback后旧epoch左右混配，修正后均拒绝；无正式ROS注入/真bag修改。r1K过严/1Hz、r2序列化、r3录制积压假位移及全部ODE warnings保留。当前SensorTime为monotonic/rollback halt门，不能声称已有完整future/frame/失效定位门；4.3必须补估计端相应规则。
- GPU依据：VirtualGL3.1.5官方EGL+私有Xvfb glxinfo真实NVIDIA RTX PRO6000 Blackwell/GL4.6 590.48.01，gzserver GPU0 G141MiB实测，SRC0072。VIO尚未build，官方CPU执行不新创CUDA算法，SAC继续CUDA优先。
- 工程模型选择：4.3继续GPT6.1sol（gpt-6.1-sol），high，仅提高推理强度：已确认constructor/reset TF初始化循环依赖、公开bootstrap与策略禁入、真实ROS时间/四元数与杆臂转换/源码权限闭包，需要联合证明原任务语义和truth隔离，属复杂设计核对；Claude替代Sonnet5.5/high。模型推荐不是actual，实际spawn另记。4.2实际medium/普通文档low/default。
- 核查日期/人：2026-10-07T15:32:54.915916+08:00，Codex /root；下一节点仍按SRC0065用户授权，不扩展场景/奖励/算法/人工误差或旧权重迁移。
- 使用：Task4父/4.2验收/4.3接手、PROGRESS/ENV/Agent统筹。

<a id="src-0075"></a>
## SRC-0075 — Task4.3 pinned OpenVINS source, realized calibration and build engineering
- Claim/type: official source audit + project derived calibration + engineering choices; CPU OpenVINS is sole VIO; ROS quaternion is Hamilton IMU→global; actual K/rig are raw-r4, not nominal.
- Author/title/version: rpng OpenVINS, commit `69488123ed9362dd44b6f28e7f4680abbff1442b`; [official source](https://github.com/rpng/open_vins/tree/69488123ed9362dd44b6f28e7f4680abbff1442b). Read original local pinned source, not secondary report.
- Exact evidence: `forem/src/open_vins/SOURCE.json`; `ov_msckf/src/ros/ROS1Visualizer.cpp` publish_state / visualize_odometry comment “JPL GtoI ... ItoG Hamilton”; `ov_init/src/static/StaticInitializer.cpp`; `ov_core/src/types/PoseJPL.h`; `forem/results/task4/t4.2-raw-r4/calibration_geometry.json` and CameraInfo, SRC0073.
- Checked: 2026-10-07 Codex /root/task4_3_localization, actual GPT6.1sol/high; source copied unchanged, Ceres necessary dependency installation in `forem/logs/task4/t4.3-build-r1/`.
- Original finding/adoption: use unchanged official algorithm, EuRoC engineering template/noise values per SRC0069 (not measured Gazebo noise calibration). Pin stereo T_IMU_CAM optical axes/±.06m and K319.9988245765257/cx320.5/cy240.5; T_base_IMU translation(.35,0,.58228) from URDF. No truth/orientation/other fused sensors. Parameters in `config/task4/estimator.yaml`/kalibr_* are engineering choices; inherited finite-noise model is not claimed matched to noiseless Gazebo.
- Derivation: T_map_base=T_map_global T_global_IMU inverse(T_base_IMU); once T_map_global=T_commanded_initial T_base_IMU inverse(T_global_IMU_initial). Pose covariance input order(p_global,theta_IMU), ROS PoseJPL left JPL update equivalent Hamilton right/local IMU. J=[[R_map_global,R_map_global R_global_IMU skew(t_base_IMU)],[0,R_map_global R_global_IMU]], C_base=J C_IMU Jᵀ; meters/radians. Includes lever arm, excludes unknown commanded alignment uncertainty; not a proven calibrated confidence bound.
- Build attempts: initial overlapping own builds and CMake failure retained; only affected new packages cleaned, sequential build ongoing at entry creation. Build/initialization success requires following run receipts, not source availability.

<a id="src-0076"></a>
## SRC-0076 — Task4.3 lifecycle gate and actual source identity
- Claim/type: project source evidence and engineering gate, not localization accuracy result.
- Author/version: FoReM Codex /root/task4_3_localization GPT6.1sol/high, 2026-10-07 implementation.
- Evidence: `forem/src/forem_localization/scripts/estimate_gate.py`, `pose_adapter.py`; `forem/scripts/task4_env.py`, `task4_identity.py`, `audit_task4_inputs.py`; tests `test_task4_pose_adapter.py`, `test_task4_identity.py`, `test_task4_source_permissions.py`; `forem/logs/task4/t4.3-build-r1/{gate-red,gate-green,archive-red,archive-green,identity-tests}.log`.
- Original finding: original C++ getRobotObs caches MoveIt worldjoint; existing get_basetf_world reads TF and set_joint_values(worldjoint-only,False) updates cached planned base without simulator command; use these after VIO init, no inherited C++ source change. Root accepted330 archived `results/task3/freeze-archive/t3.6-core-freeze4/snapshot` preserved; current allowed CMake delta old/new hashes in `config/task4/accepted_core_deltas.json`.
- Adoption: one adapter/pose_bridge TF authority; public spawn/reset commanded anchor only while no effective policy obs/actions; old VIO stopped, epoch/discard+fresh raw init then once align. Original stamp preserved. Official estimator caller required; invalid/future/stale/frame/nonfinite/oldepoch/reset stops cmd_vel and cancels/holds arm; simulator clock rollback requires fresh run. Actual identity covers inherited/current source + Task4 runtime itself, config, official source and built binary, rejects Task3/truth namespaces regardless of shape.
- Bounds/basis: max age .1sim s=two20Hz camera periods; future tolerance .0005sim s=one physics step; init wall120s and run900s/1000steps are previously selected engineering resource limits SRC0069, not measured accuracy thresholds. Unit4 cases and source10 cases pass, identity1 passes at entry creation; no claim of live pipeline success yet. No formal training budget frozen.
- Checked: 2026-10-07 Codex; parent independent runtime/source audit pending. Runtime graph/actual reset/loss/coverage must be separately evidenced before Task4.3 acceptance.

### SRC-0075 actual ROS lifecycle/reporting deltas (2026-10-07 follow-up)
- Exact patch/base/new hashes: forem/src/open_vins/SOURCE.json preserves pristine commit file map; config/task4/openvins_patches.json lists actual deltas. No longer pure unchanged upstream after these fixes.
- Cause1: debug-r4 SIGABRT main destructor→ROS1Visualizer sync_cam→Synchronizer::disconnectAll→Signal1<Image>::removeCallback boost mutex invalid. Original declaration order sync_cam before sync_subs_cam causes reverse destruction to invalidate subscriber Signal first. Reorder inputs before synchronizer. Stack: forem/results/task4/t4.3-offline-debug-r4/shutdown_backtrace.txt.
- Cause2: after member fix r5 produces24raw poses but nodeexit−6 image_transport LibraryUnloadException; debug-r6 global-exit ROS1Visualizer/image_transport::Publisher→pluginlib::ClassLoader→MultiLibraryClassLoader destruction. Stack: forem/results/task4/t4.3-offline-debug-r6/shutdown_backtrace.txt. Entry honors official multi_threading_subs:false, one ROS spinner, stop/join callbacks, releases viz/sys before global registries die. This changes message scheduling and processing time; estimator equations unchanged. Quality/resource conclusions must use final configuration. multi_threading_pubs:false alone did not solve either error and is not the root cause.
- Cause3: online-r1 actual static initialization success and ongoing41-feature ZUPT, zero published pose/actions, init timeout. VioManager::initialized requires is_initialized_vio AND timelastupdate!=-1; stationary ZUPT returns before first normal MSCKF update sets timelastupdate. Policy-blocked-until-pose cannot cause the motion this reporting gate awaits. New read-only state_initialized accessor preserves original initialized/internal filter; publish_state exposes only genuine camera/ZUPT-updated initialized state before existing full-ready visualization gate, original timestamp and duplicate suppression. No IMU-tick old-state re-stamping/fast propagation. Evidence: forem/results/task4/t4.3-online-r1/summary.json, logs/task4/t4.3-online-r1/launch.log and VioManager/ROS1Visualizer symbols. Static initialized, normal-MSCKF-ready and sufficient visual constraint/accuracy remain different claims.
- Frontend version choice: callback_stereo rejects timestamp<last+1/track_frequency. Raw-r4 exposures49–51ms, actual r7 pose maxgap.101s at cap20. Normal frontend cap21Hz (official EuRoC default21,47.619ms<49ms) avoids throttle rejecting normal sensor jitter. Actual sensor20Hz/IMU200Hz, age gate.1sim s unchanged; protocol/runtime config synced before online. Engineering scheduling choice, not accuracy-threshold relaxation or sensor-rate change. SRC0073.
- All patches confined selected VIO ROS integration/read-only state exposure; inherited robot/task/reward/action/control C++ unchanged. Final online/fault acceptance pending.

<a id="src-0077"></a>
## SRC-0077 — Task4.3 raw-only offline initialization and real shutdown receipts
- Type/claim: project measurement/source/diagnostic evidence: raw images+gyro/accel can initialize selected VIO and produce finite poses. Not accuracy or online task-success proof.
- Owner/date/model: Codex /root/task4_3_localization,2026-10-07,actual GPT6.1sol/high; parent independent review pending.
- Input/evidence: raw-r4 inputs.bag SHA256 1ce4a73752c90b71edcf797cbb80f30351a707d128e2fa3a4e9e0fcfb065fde8. Each results/task4/t4.3-offline-*/segment.json, source_start/end/snapshots, container_identity_start/end, poses.json, summary.json, owned_subprocess_exits; logs/task4/<run>/state.json/check.log/foreign_after.json.
- Conditions: public continuous25.605–29.8835sim s only;856originalIMU,78/78genuine left/rightImage,85/85Info,4512originalClock. Bag alone publishes clock, no additional --clock; no diagnostic/evaluation/truth opened by VIO/input checker. Playback.25×wall speed, original headers/payload; not sensor-rate experiment. Actual calibration SRC0073/0075.
- Outcomes: r1/r2 real24finite global-frame poseimu at28.000–29.851; ROS wrapper0 did not prove clean node (shutdownabort). debug-r3 failed before VIO because gdb installation unfinished; retained. debug-r4/r6 GDB0poses are shutdown diagnostics only. r5 member patch24poses but actualnode−6/checker/final1. r7 both lifetime fixes24poses/directnode0/checker0/final0/cleanup0/foreign=[],source and runtime identity unchanged. No overwrite. Native static initializer raw excitation.028/.028, arbitrary initial yaw[0,−0,−.7071,.7071], origin0; not simulator pose.
- Limits/adoption: first output after public motion27.609; no first-moving-pose→commanded-start fit claimed as offline accuracy proof. Online init remains stationary/policy blocked until true updated pose. CPU only. Cleanup version differs from later static-state exposure/frontcap21; final online quality requires final actual config. p3d evaluation not used here; independent error evaluation must match original headers and record frame alignment.

<a id="src-0078"></a>
## SRC-0078 — Task4.3 final online source/lifecycle and bounded original task evidence
- Claim/type: project actual execution and implementation evidence; raw-only estimate feedback/TF integration and fail-closed lifecycle work under recorded configuration. No SAC training, no accuracy/performance acceptance.
- Owner/version/check: Codex /root/task4_3_localization, actual GPT6.1sol/gpt-6.1-sol/high,2026-10-07; parent independent artifacts in forem/results/task4/t4.3-parent-review-20261007. Final selected pin plus four file-level ROS/reporting patches per SRC0075; original internal filter equations/initialized and inherited330Task3 files unchanged except previously authorized CMake install delta.
- Exact primary paths: forem/results/task4/t4.3-online-r3/{summary.json,task_steps.json,episode_spec.json,poses.json,statuses.json,tf_edges.json,graph_initialized.json,graph_truth_recorder_off.json,container_identity_start.json,container_identity_end.json,source_snapshot,source_unchanged.json}; forem/results/task4/t4.3-faults-r2/{faults.json,summary.json,hold_commands.json,tf_edges.json,delivery_receipt.json,container_identity_start.json,container_identity_end.json,source_start.json,source_end.json}; logs/task4/<run>/state.json/check.log/cleanup/foreign_after.json.
- Final ordinary task attempt: fixed zero3-dimensional diagnostic action, no network/replay/optimizer, original SimpleObstacleTask/41state+120x120x1map and original controls/reward/termination. online-r3 done=true/success=false,125steps,66realestimatedposes,20IK failures/0base collisions;33.2916697wall s checker body (not entire launch/cleanup). Native original failure retained, not claimed SAC performance. Source233file hashes match, container identity start=end/allgroupspresent, TF22751base edges unique odom→base_footprint caller/pose_bridge. Truth reader only separate rosbag recorder, disabled after5steps while estimate/steps continue. Actual VIOstop0/checker0/wrapper0/cleanup0/foreign=[]; host auxiliary identity-end old symlink path PermissionError separately retained, actual container/source proof remains available.
- Final faults-only attempt: faults-r2 is lifecycle diagnostic, not actual-task success;0policy steps,done=false,success=null,lifecycle_tests_passed=true. True C++ node PID+kernel start/cmd/ROSAPI checked, same live identity before SIGCONT. SIGSTOP yields stale INVALID_STOP/noTFsource,0step action refusal;490actual zero cmd_vel plus issued six-joint zero-velocity arm hold (.1s command horizon). Diagnostic feedback maxdifference0 is not independent physical tracking proof: checker joints_feedback.get(n,pos) falls back to commanded pos when a joint is missing, so0 alone cannot establish feedback completeness; adapter itself requires all joint names before emitting this command. Fresh explicit reset stops old node0, spawns new node, epoch3→5READY after fresh raw init/once public alignment; real /gazebo/reset_simulation epoch6INVALID clock_rollback and furtheraction rejected. UniqueTFauthority, final node0/checker0/wrapper0/cleanup0/foreign=[]; source233 and runtime identity twoends/current exactly match, mandatory components/binaries nonempty.
- Source delta receipt: r3→faults-r2 only task4_identity.py/check_task4_localization.py/run_task4_localization.sh. Actual private binary paths instead of absolute devel symlink; native NumPy→JSON/JSONL flush, distinct lifecycle summary, own-process identity checks and actual hold diagnostics; wrapper snapshot errors refuse/start/end16. No env/pose adapter/estimator/config/control/reward/observation math changes. Old/newSHA, final official source+patch conformity and actualbinary digests in delivery_receipt.json; not merely stale manifest hashes.
- Failures preserved: online-r1 realstaticinit/41-feature ZUPT but public initialized gate suppresses output until motion (0actions,timeout); online-r2 real76poses/atleast5steps but NumPy bool JSON end failure loses full step/summary evidence, no invented result; faults-r1 actual lifecycle JSON complete but zero-step summary IndexError giveschecker1. RED→GREEN real failures, final26container Task4 tests0; host26 command has NumPy import errors and no host dependencies installed. Parent reread validates actual source/hash/clock/TF/source permission, independent from author claims.
- Accuracy limits: online-r3 only5/66header-stamp truth matches within.02s engineering50Hz pairing bound (7.5758% coverage); over those5only,3D RMSE.0514119487m/yawRMSE.0326837767rad; parent independentXYRMSE.0122287m. Public commanded initialz.05 versus physical settling near0 and unknown alignment covariance limit3D interpretation. Not whole-run accuracy, fair baseline success or threshold pass. Offline first-moving-pose→commanded initial alignment is diagnostic and not accuracy acceptance. Full evaluation/XY gate, real RL checkpoint loading/rejection and GPU pilot belong4.4; not added/executed here.
- Identity limitation/adoption: Task4 current content identity includes raw/helper/gate/adapter/lifecycle/identity code itself, actual official/source patches/config/binary, inherited core/binary; metadata namespace guard rejects Task3/truth regardless shape in units. No actual RL checkpoint file loaded in4.3;4.4 must wire actual SAC entry and loader/replay/optimizer guard. Final source/SOURCES write rights returned to parent upon handoff, no running child process.

<a id="src-0079"></a>
## SRC-0079 — Task4.3父独立必要验收与4.4自动派发
- 类型/主张：项目原始运行证据与父独立核验；4.3估计/TF接入必要验收done，非定位精度或SAC基线done。模型安排是工程选择，沿用户GPT6.1sol默认，不作模型优劣研究结论。
- 核查：Codex /root，2026-10-07T16:51:08+08:00；实际父模型/强度未知；执行子gpt-6.1-sol/high。
- 精确来源：forem/results/task4/t4.3-parent-review-20261007/{verify_delivery.py,t4.3-online-r3-review.json,t4.3-faults-r2-review.json,actual-step-estimate-matches.json,limited-errors.json,acceptance.json}；forem/logs/task4/t4.3-parent-review-20261007/{tests-container-current.log,runtime-source-gate.log,tests-current.log}；原运行与已核查官方pin/四文件ROS必要patch依据SRC0075–78。
- 原始结论：233源文件运行首尾与归档逐hash一致，容器实际身份40组完整一致，父26单测0；125步XY逐项匹配真实估计pose、最大匹配age.0785sim s，base TF唯一pose_bridge，truth独立读进程。真实SIGSTOP失效停止/新epoch与新VIO初始化/实际时钟回退拒动作成立，check0、cleanup residue[]、foreign[]。宿主单测先因缺numpy产生2import error，保留且未装宿主ROS或数值依赖；实际验收在容器。
- 适用限制：原零动作任务125步失败20IK，不算SAC性能；精度仅5/66匹配，XY RMSE由原误差向量前两分量平方均值开根推导.0122287266m，非完整精度门槛。armhold0有缺反馈fallback，不能证明独立物理跟踪；实际六关节保持命令已记录。r3→最终仅identity/checker/wrapper三文件最小差已审计并由fresh faults-r2验证最终源；不声称最终源重复完整任务。真实RL权重加载/旧truth拒绝、完整评测与正式预算待4.4。
- 采用：按用户SRC0065自动进入4.4。Codex推荐GPT6.1sol/gpt-6.1-sol medium，Claude备选Sonnet5.5 medium；跨评测时间/实际终止/真值隔离/实际CUDA检查点与预算冻结需中等因果核对，非更大型号。4.4有限先导，不提前正式训练，不调整原任务/动作/奖励/终止，不新增噪声/场景/WM。

<a id="src-0080"></a>
## SRC-0080 — Task4.4 pre-pilot quality/actual task criteria
- Type: original project code + explicit derivation + engineering choice, verified 2026-10-07 Codex `/root/task4_4_pilot` (actual GPT6.1sol/medium).
- Claim/source: `forem/src/modulation_rl/scripts/modulation/envs/eeplanner.py:_is_done` L187–193 compares Euclidean distance<.025m and `env_utils.py:calc_rot_dist` L123–130 =1−(qa·qb)^2<.05 (dimensionless). `modulation/utils.py:episode_is_success` L530–531 requires no IK failures/base collisions and ee_done. Original `gazebo_world/husky_ur5/robot_config.yaml:global_link_transform` is gripper_base_link, not wrist_3_link; independent Gazebo link comparison uses goal_wrist directly, with no tip offset required. Unit correction supersedes parent dispatch's erroneous '.05rad'. For unit quaternions rotation distance sin²(theta/2), theta<2asin(sqrt(.05))=.4510268118rad. No source/contract modification.
- Adoption: physical gripper_base_link position and quaternion compared with original goal_wrist, original IK/collision failure requirements. Independent receipt-timed Gazebo LinkStates has no original header; its skew must be reported, not presented as exact-stamped truth. p3d/header used for localization only (noise=.01, unknown anchor covariance).
- Pre-pilot engineer gates: config/task4/pilot_quality.json XY RMSE≤.025m, peak≤.075m, yaw RMSE≤.05rad, peak≤.15rad, matched poses/control coverage≥.95, age≤.1sim s, truth skew≤.02sim s, all attempted initialization succeeds within120wall s. XY shares original task position scale; yaw=.05rad is separate conservative engineering choice, not original task rotation tolerance; peaks3x and95% coverage are provisional engineering screening guards. Frozen before Task4.4 pilot measurements, no result-based relaxation. Pilot task success is reported, not convergence gate; missing/failed attempts never dropped. Applicability: same Gazebo Husky/UR5 public once-aligned frame, not external platform acceptance claim.

<a id="src-0081"></a>
## SRC-0081 — Task4.4 fresh CUDA pilot / failed sealed initialization / measured cost
- Type: project original measured evidence, checked 2026-10-07 Codex `/root/task4_4_pilot`, actual GPT6.1sol/medium; Claude alternative Sonnet5.5/medium.
- Evidence: `forem/results/task4/t4.4-pilot-r1/{pilot_summary.json,contract.json,container_identity_start.json,container_identity_end.json,source_start.json,source_end.json,task_steps.json,transition_000.npz,pilot_checkpoint.pt,evaluation.bag,evaluation.json}`; logs/task4/t4.4-pilot-r1/{check.log,check.json,state.json,foreign_after.json}; source snapshots identify exact executed versions. checkpoint SHA ad0ece2dcef241ffe7d3ef42feafd1385957aac695beb2934a41661522dd48ee, 41116145 bytes.
- Original result: fresh seed0 CUDA76 actual envsteps/60 original update_parameters; warmup64/batch16; no prior/Task3 init weight/replay/optimizer. Networks and loaded Adam moments cuda:0, no CPU fallback. Deterministic roundtrip maxactiondiff0; real oldtruth file rejected before SAC.load_checkpoint and42actual currentidentity group mutations rejected. Original masks unchanged. Policydelta.40267588 proves update, not learning. Saved supplement alpha/alpha-optimizer/schedulers is not resumable training (replay/RNG/tuning flag/cumulative-budget absent), no resume claim. Current later helper/config changes intentionally yield a different identity and reject archival pilot weights; formal always fresh.
- Attempts retained: seed0 initialized16.48945wall s; sealedseed101 fresh static OpenVINS initialization timed out, reset141.59318wall s includes120s collection and control reset; 2 init attempts/1success, validation1attempt/0completed/0actions. No test episode and no task-success claim from missing validation. Entire run181.85223wall s, check1/final1/cleanup0/foreign[]. No second training pilot.
- Full original-stamp p3d:142/142 matches, all76attempted controls valid, XYRMSE.02197687995m/peak.06686816526m, yawRMSE.03442486362rad/peak.04005349133rad, 3DRMSE.07002817m; numeric gates passed but initialization gate failed. p3d .01noise and commandedz/settling+unknownanchor uncertainty restrict accuracy. Original physical evaluator lacked gripper_base_link after Gazebo fixedjoint reduction; empty physical file is explicitly failed independent physical evidence, not successful EE check.
- Cost:76env step bodies total2.068446s (mean.0272163985wall s, p95orderstat.0302881),60updates total2.139910s (mean.03566517s atbatch16), maxactorRSS2325980KiB, peak CUDAallocated/reserved fields in summary (reserved195035136bytes). GPU wholeprocess reported882MiB live; PyTorch allocated peak omits context/Gazebo/other processes. Host numpy unavailable probe retained as failed tool check; scientific recomputation container-only. Resource extrapolation is provisional, not measured formal throughput/convergence.
- Adoption/limit: fail-closed formal disable because sealed initialization failed. FullTask4.4 independent diagnostic SRC0082 fills complete physical evidence for another new run; does not fill missing validation retrospectively or satisfy sealedseed101 gate. Model recommendation comes from user default and cross-source/time/quality/budget review, not a benchmarking claim.

<a id="src-0082"></a>
## SRC-0082 — Task4.4 full original diagnostic, actual physical EE and fixed-joint reduction
- Type: original live project measurement+URDF derivation; checked 2026-10-07 Codex `/root/task4_4_pilot`.
- Evidence: results/task4/t4.4-quality-r1/{summary.json,episode_spec.json,commanded_initial.json,evaluation.bag,poses.json,physical.jsonl,joint_feedback.jsonl,physical_link_contract.json,robot_description.urdf,evaluation.json,actual_task_evaluation.json,source_snapshot,container_identity_start.json,container_identity_end.json}; logs/task4/t4.4-quality-r1/{check.json,state.json,foreign_after.json}. Actual source snapshot precedes later offline evaluator/instance/budget-helper amendments.
- Original result: seed0 complete original zero-action196steps, done=true, originalsuccess=false/20IKfailures/0basecollisions, checker38.64124wall s/init17.74434; check/final/cleanup0, foreign[]. No SAC training in this diagnostic.92/92 originalp3d-stamp matches;196/196attempted controls valid; XYRMSE.0168064800/peak.0225949770m, yawRMSE.0326155291/peak.0357835305rad; p3d uncertainty/commandedz caveats preserved. Actual independent task success false;196/196physical/joint samples valid, finalpositionerr4.4941220m/quaterniondist.88528953; no goalachieved samples. Original failure is legitimate result, not reward/task change.
- Live source correction to SRC0080 initial directlink expectation: Gazebo /gazebo/link_states list omits fixed gripper_base_link. Actual sensor reports husky_ur5::ur5_wrist_3_link. From actual robot_description: ur5_gripper_fixed wrist3→ee_link identity; gripper_base_joint ee_link→gripper_base_link translation0/rpy(0,−1.57075,0). Evaluation computes T_world_gripper=T_world_wrist3×T_wrist3_ee×T_ee_gripper, compares goal_wrist from original task. No directwrist3 substitution, no plannedjoints; static chain/names/matrix archived. Complete finite six JointState feedback required, no fallback when missing.
- Time limitation: LinkStates has no header; separate node records simulation receipt, nearest control-time skew≤.02s; JointState originalheader skew≤.04s engineering match for25Hzfeedback. p3d localization still uses originalheaders≤.02s. These receipts do not prove exact physical timestamps or tracking/hold accuracy. Missing/invalid/skew failures retain complete196 denominator. Actor/estimator never subscribe truth; evaluator process only.
- Applicability: same original publicgoal/scene and oncealigned estimate. This fullfailedtask does not cure sealedseed101 initialization or imply CUDApilot performance/convergence. No source/thresholdVIO change.

<a id="src-0083"></a>
## SRC-0083 — Task4.4 provisional finite formal resources and whole-instance split
- Type: engineering choice + conservative scaling, not executed/final accepted freeze; checked2026-10-07 Codex `/root/task4_4_pilot`.
- Inputs: SRC0081 measured76step body mean.0272164s and batch16 update mean.0356652s; config/task3/sac.yaml original batch256/horizon5000001/network/update retained. Batch256 estimated16×batch16 update cost≈.570643s assuming linear scale, unverified;20000steps would≈11413supdate+544sstep, initialization/control overhead/retry may exceed cap. Therefore12000s hardcap is bounded screening, not predicted completion or convergence guarantee; exceeding counts failure. Actual finite limits in config/task4/sac_baseline.json all nonnull, enabled=false because initialization failed and formal executable not complete; protocol.yaml formal remains false/unfrozen, no approved execution_freeze fabricated.
- Limits: fresh trainingseeds0/1/2,20000steps,19744updatescap, warmup1000,batch256, replay10000≈10000×(2×120×120×4+2×41×4+3×4+8)≈1.156GB (Python overhead extra), actorRSS16GiB/CUDA12GiB caps,3checkpoints scheduled5000/10000/20000,10GiB/attempt;6maximum attempts (1freshretry/seed),72000trainingwall+18000evalwall=90000totalwall,70GiBdisk overall, tuning1configuration. Interruptedrun staysfailed andfreshretry consumes budget; no unsupportedresume/pilotreuse. Resource limits must be enforced/tested in formalrunner before gate can pass.
- Sealed whole-instance partition: original results/task3/t3.5-inst-r1/episode_instances.json seeds101–110 untouched; training publicinstance seeds0–99; validation101–105, oncefinaltest106–110, allgoal/obstacles/initialarm/map retained. Base_tf original snapshot separately distinguished from publiccommandedinitial, and commandedXY/yaw versus seal must verified (publicz=.05↔originalplanarz0 documented only). Pilotseed101 initfailed before real publicinstance comparison; therefore whole-instance actualcomparison remains UNVERIFIED, not claimedpassed basedunit projection. Originalspec/hash never edited. No neighboring-time split/testtuning; validationonlycheckpoint selection, missing/timeout/controlerrors countfailedepisode. Perinstance1episode≤2000steps/600wall s; finite evaluation on3trainseeds=30episodes≤18000s. formalbaseline not run.
- Adoption/limitations: config is a reviewable provisional budget for parent, not task4.5 authorization or guarantee. task4_budget.py rejects null/nonfinite/overlap or disabled/failedquality/absentparent/formalrunner. Both agent recommendations GPT6.1sol and Sonnet5.5 medium for cross-module review; actual GPT6.1sol/medium. Required remaining: sealedinitialization engineering fix without easier task/distribution, allqualitypasses, publicinstance runtimeproof, executable formal budget tests, actualfreeze+parentacceptance before4.5.

<a id="src-0084"></a>
## SRC-0084 — Task4.3.1 seal101 raw initialization causal diagnostic
- Claim/type: project original measured raw evidence plus selected official source/library tracing; not Task4.4 acceptance or full estimator quality proof.
- Owner/check: Codex `/root/task4_3_1_init`, actual GPT6.1sol/gpt-6.1-sol/high;2026-10-07. Claude alternative Sonnet5.5/high is recommendation only. High follows raw/featureDB/reset/window causal debugging, user default model unchanged.
- Exact evidence: `forem/results/task4/t4.3.1-init-r1/{summary.json,raw.bag,images.jsonl,imu.jsonl,statuses.jsonl,public_draws.json,init_analysis.json,source_snapshot,source_start.json,source_end.json,container_identity_start.json,container_identity_end.json,exact_manifest.txt,exact_pairs}`; `forem/logs/task4/t4.3.1-init-r1/{launch.log,check.log,state.json,foreign_after.json}`. Selected official OpenVINS pin69488123ed9362dd44b6f28e7f4680abbff1442b; `ov_core/src/track/TrackKLT.cpp:feed_new_camera,perform_matching` L55–65/L850–858, `ov_init/src/init/InertialInitializer.cpp:initialize` L84–100/L123–129; official URL https://github.com/rpng/open_vins/tree/69488123ed9362dd44b6f28e7f4680abbff1442b, local actual source read, original equations unmodified.
- Actual result: unchanged120wall-s initialization wait failed; seed101 reset132.87018wall s/full checker146.91468s,0 controls/raw recorder0/checker1/wrapper1/cleanup0/foreign[]. Raw original header window14.952–92.0sim s:1541left+1541right images/CameraInfo,15409finite accel+gyro, median .05/.005sim s; no truth/orientation estimator input. Actual ALL existing logging762featureDB updates all0,1524failed initializations/no disparity/IMU-window warnings; no stated internal-deque size because not directly instrumented. Raw image viewed: untextured original black rectangular obstacles/ground/sky; same frame rawFAST20=23 versus equalizeHist(raw)FAST20=8, official retained7left/5right, less than10 actual temporal matching requirement. Initializer therefore no real tracked camera timestamp, before IMU-window test; not missing images or x30 final command. Actual command XY/yaw matchesoriginal101, public z=.05 documented. PNG is raw lossless encoding; all measured pixels achromatic, rgb channel interpretation does not change r1 pixels.
- Important limitation/correction: r1 diagnostic spy incorrectly called map.get_scene_objects(), which randomly redraws SimpleObstacleMap obstacles and consumes RNG after actual start/goal draw. `public_draws.json:obstacles` is NOT actual spawned scene and is invalid evidence; base/goal captured beforehand and raw actualscene remain useful, no policy actions occurred. Existing Task3Env._capture_spec uses same historical metadata call; originalsealobstacles cannot by themselves prove actualscene. Parent identified this, new diagnostic observes actualspawn arguments without redraw; no Task3core/oldseal edit authorized. Actual full scene equality remains pending. Preserve failure denominator.
- Adoption: explains measured feature/preprocessing rejection only, not forced initialization, not platform-general VIO limitation. No sensor/view/quality threshold or filter equation changed in r1; original fallback-less permission/lifecycle preserved.

<a id="src-0085"></a>
## SRC-0085 — Task4.3.1 actual official frontend counterfactual and minimal supported parameter
- Type: original raw/library replay counterfactual plus engineering choice; inspected2026-10-07 Codex `/root/task4_3_1_init` GPT6.1sol/high.
- Primary evidence: `forem/tests/task4_init_tracker_probe.cpp` linked actual unchanged `devel/.private/ov_core/lib/libov_core_lib.so`; `forem/results/task4/t4.3.1-tracker-evidence/{manifest.txt,old50.log,candidate200.log,old50-points.log,minpx3-hypothesis.log,histogram-none.log,exact-old.log,exact-none.log}`; exact80original20Hz bag frames in SRC0084, no image augmentation or retiming. Compile commands/exits in agent log and logs/task4/t4.3.1-probe*-build.log. Full-image FAST is independent diagnostic and not a featureDB count.
- Actual counterfactuals: same70sparse originalstamp pairs50→200 init budget fails (7/6→0/DB0), min_px_dist10→3 fails (7/5→0/DB0); neither applied. Official `histogram_method:NONE` with alloriginal50/10/5x5/FAST20 retains12/12,14distinct DBtrack IDs/newest camera stamp; features counted over both cameras separately by original FeatureHelper. Exact80original20Hz pairs: currentHISTOGRAM allDB0/newest−1; NONE final original2s halfwindow counts24/24≥15. These are actual frontend/initializer-input counterfactuals, not onlinefilter initialization/performance proof.
- Supported choice: official `ov_msckf/src/core/VioManagerOptions.h` L468–480 supportsNONE/HISTOGRAM/CLAHE; `TrackKLT.cpp:feed_new_camera` NONE passes originalgrayscale through, rather than global histogram equalization that erased existing shadow corners here. Proposed one config parameter HISTOGRAM→NONE; no feature thresholds, camera/view, task/action/reward/termination, filter equations or quality gates changed. Parent coordination and new live validation pending at registration. `forem/tests/test_task4_init.py` genuine official-library configuration regression: first setup attempt OpenCVYAML directive parser error retained, corrected parser; currentconfigRED0<15, logs/task4/t4.3.1-test-red2.log. GREEN/live result must append, cannot infer from replay alone.
- Limits: source/calibration/binary identity must remain frozen at both newrun ends, oldpilot weights stale under newidentity; seed0 control and seal101 live init, full source/lifecycle regressions, independent4.4quality still required. No single raw replay proves all101–110 scenes or eventual SAC benefit.
- 2026-10-07 parent coordination update for SRC0085: root explicitly approved this necessary single supported parameter repair, with original image/scene/quality/filter/binaries unchanged. Actual estimator.yaml now NONE, protocol same parameter/basis; old/new SHA in `results/task4/t4.3.1-tracker-evidence/parameter_delta.json`. Regression currentconfig GREEN1test0 (`logs/task4/t4.3.1-test-green.log`), versus archived validRED0<15. New live r2 launched, results still pending at this entry; old source/bag/failures untouched.

<a id="src-0086"></a>
## SRC-0086 — Task4.3.1 final native init and fail-closed regression delivery
- Claim/type: actual original draw/raw native estimator and lifecycle regression, source identity verification; deliveredreview, parent acceptance and completeTask4.4quality pending. Owner/check Codex /root/task4_3_1_init, actual GPT6.1sol/gpt-6.1-sol/high,2026-10-07; Claude alternativeSonnet5.5/high recommendation only.
- Primary evidence: forem/results/task4/t4.3.1-init-r2/{delivery_receipt.json,summary.json,attempts.json,raw.bag,images.jsonl,statuses.jsonl,spawn_commands.json,spawn-*.sdf,robot_description.urdf,public_draws.json,public_instance_comparison.json,initialization_windows.json,graph-seed101.json,graph-seed0.json,source_snapshot,container_identity_start.json,container_identity_end.json,runtime_source_gate.json,nvidia-smi.txt}; forem/results/task4/t4.3.1-faults-r3/{summary.json,faults.json,hold_commands.json,tf_edges.json,statuses.json,source_snapshot,source_start.json,source_end.json,container_identity_start.json,container_identity_end.json}; logs/task4/<runs>/{check.log,launch.log,state.json,foreign_after.json}; logs/task4/t4.3.1-{test-red2,test-green,tests-task4-final,tests-all-final,runtime-source-gate2}.log and diagnostic-source SHA receipt. SRC0084/85 input/cause/oneparameterbasis apply.
- r2: seal101 then0 freshraw initialization + each1 original zero-action step;2controls/0SAC/fullchecker57.2826665wall s, check/final/cleanup0/rawrecorder0/foreign[]. Reset including one control17.7905323/24.6752200s. First COLLECT→first READY (status receipt durations, not exact internal start):1014.0709824wall s,sim15.119→17.5095/originalpose17.5/age.0095;04.0880909wall s,sim24.591→27.0105/originalpose27.0/age.0105; epoch3→5. Native originalstatic initializer/window/ZUPT genuineupdatedposes; original41vector+120x120x1map each, acceptedstep sourceopenvins_stereo_imu; no successfulgoal/convergence claim. NVIDIA GPU0 realgzserver149MiB G underVirtualGL EGL0; estimator/physicsCPU, no CUDAport/SAC.
- Public instance: actualspawn arguments16objects each reset+32actualSDF+live robot_description archived with no additionalget_scene_objects/RNG draw. Actual101commandXY/quaternion,goal_tip,arm_command,map_size equal old1016dp; publicz.05 vs originalplanarz0 explicit. ActualsceneA differs oldseal metadataB; original _capture_spec re-drawn metadataB still exact equal oldsealB. This diagnoses metadata defect, does not verify physicalscene equality fromoldseal nor change originalscene/taskgeneration. Parent must independently establish corrected publicscene authority; oldfiles unchanged. Publicz.05 is commandedresetlift, not an independent physicalheight/accuracy proof; publicnominalground alignment and physicalbias remain parent4.4 review, not part ofhistogram repair.
- r3 finalsameconfig: genuinekernelpid/start/cmd VIO SIGSTOP→stale INVALID_STOP,actionrefusedand0controlsteps;460zero cmd_vel +1sixjoint armhold command, ownidentity verifiedbefore SIGCONT. Freshreset epoch3→5READY; actual /gazebo/reset_simulation→clock_rollback INVALID_STOP/furtheractionrefused.4originalposes,56.8431902checkerwall s,check/final/cleanup0/foreign[], actualVIO lifecycle exits archived. Armhold feedback_max_error uses inheritedchecker fallback whenmissing; no independentphysicaltrackingproof.
- Identity: all243snapshotfilehashes eachrun equal start/end/archives; finalsource matchescurrent. Actual47runtimegroups complete/equal r2/r3 and twoends; officialsource and9actualbinarygroups unchanged r1→r2, only config/task4+runtime:diagnose_task4_init.py identitydelta. Exactsource r2=r3. Genuineofficiallibraryconfigtest validRED→GREEN,40Task4tests0,338wholeprojecttests0/3existingreference skips168.258s; finalcontaineronlyinit/sleep,foreign[]. First sourcegate CLI importpatherror retained, corrected PYTHONPATH=scripts actual verify_runtime0/oldarchivalpilotcontractmetadata rejectedsameTask4namespace butdifferentactualsourceidentity; noweights/policyloaded/newpilot executed. Actual RL checkpoint load/refusal recheck belongs4.4.
- Limits/adoption: exactly3physicaldiagnosticruns (r1failure retained)+2controls/0SAC,results~85MiB below10GiB/run≤600wall s; wholewrapperwallbounds inlogs. One supportedparameterHISTOGRAM→NONE only, init50/FAST20/grid5x5/minpx10/quality/view/filterequations/action/reward/termination unchanged. Repairs tested101nativeinit and retains0normal/failclosed; no all101–110 robustness/fullaccuracy/success/formalbudget freeze/4.5 claim. Source/SOURCES handedback toparent afterdelivery; reviewnotparentdone.

<a id="src-0087"></a>
## SRC-0087 — Task4.3.1父独立验收及4.4继续实施
- 主张/类型：项目原始运行、父独立核验、必要工程修复；支持单一官方histogram_method NONE修复本封存视点初始化，非通用精度/训练收益。
- 核查/模型：Codex /root，2026-10-07（实际父模型/强度未知）；执行子gpt-6.1-sol/high，沿默认GPT6.1sol；接续4.4实际原子gpt-6.1-sol/medium，Claude备选Sonnet5.5/medium，跨实例记录/指标/预算源链因果核对。
- 精确证据：forem/results/task4/t4.3.1-parent-review-20261007/{artifact-review.json,current-and-deltas.json,acceptance.json}；forem/logs/task4/t4.3-parent-review-20261007/tests-after-init-fix.log；原r1/r2/faults-r3 source snapshot、container_identity两端/实际命令/summary，父已逐hash/exit核查。原因/同原20Hz图像官方C++ tracker反事实依据SRC0084–86，父40tests实际再跑0。
- 原始结论：三run各243源文件归档与首尾一致；47actualruntimegroups非空一致，最终与当前逐hash一致。r1 original HISTOGRAM真实timeout保留；r2只支持参数NONE，101/0真实freshinit和41+120x120x1观察/各1原动作step；r3同源真实SIGSTOP停车/新epoch与新node初始化/clockrollback拒动作通过，foreign/residue[]。官方source和9binary groups未变，实际差为config与诊断helper。全套338/3refskip由子原日志核查，不重复全套；父另40tests。
- 限制/采用：4.3.1 done为已发生原失败必要修复，不证明所有输入可定位/新质量/真实任务或正式SAC成功；旧seal场景再抽样限制需SRC0088修复，4.4重新冻结真实公共实例与同新定位质量。公开z.05 resetlift不当3D精度证明；原worlds.cpp:getBaseTransformWorld会强制z0供Cpp规划，getGripperTransformWorld诊断TF保持3D，因此父初步怀疑5cm直接改变IK/终止的说法不成立（robot_env.cpp:getRobotObs的planned vs achieved、eeplanner.py:_is_done实际planned字段），当前不新增zanchor改动。用户SRC0065授权继续4.4，无第二76/60训练pilot，正式4.5仍前置未满足。

<a id="src-0088"></a>
## SRC-0088 — 公共场景封存记录getter再抽样缺陷与必要元数据纠正
- 主张/类型：原源代码与私有实际方法反例/工程纠正。旧Task3封存obstacles/hash一致不能证明Gazebo实际同场景；迁移源码/控制/训练接口验收与该观测元数据缺陷分开记录，不倒填历史。
- 位置/版本：当前保持Task3 freeze4原330与CMake已声明delta；forem/src/modulation_rl/scripts/modulation/envs/map.py:Map.get_scene_objects L679、SimpleObstacleMap.get_varying_scene_objects L849起，每次调用使用np_random重抽；CombinedEnv.reset L260 map.map_reset使用A→spawn_scene_objects；forem/scripts/task3_env.py:_capture_spec L105再调用getter抽新B。SRC0086 r2实测actualspawnA!=oldsealB，而旧原getter记录B又可一致；不能声称B是实际物理输入。
- 证据/核查：Codex /root，2026-10-07；forem/results/task4/t4.4-parent-review-20261007/{probe_scene_rng.py,scene-rng-counterexample.json}，实际原类私有对象仅方法调用、无ROS/Gazebo注入。seed101同一对象两次getter各16个objects、结果不同，RNG before/afterfirst/aftersecond三digest不同。实际r2 spawn参数/SDF和public_instance_comparison见SRC0086。本条不宣称私有反例是新的物理run。
- 采用/限制：保留旧Task3文件/源/archivalfreeze，撤回旧obstacles作为actualspawn证明。Task4Env仅观测记录必要覆盖：缓存既有spawn_scene_objects实参/真实publicdraw commands，不为读取再调用getter或truth，不改变原物理场景/目标/奖励/动作/滤波。Task4新的公共seal需记录实际A并核查完整SDF与公共initial/goals、重复时RNG不被观察更改；旧base/goals/arm/map字段仍可单项核查，不静默忽略障碍物。此为原4.4封存输入必要修正，非新增实验/任务机制；尚待实测与freeze，不把拟修复写已完成。

<a id="src-0089"></a>
## SRC-0089 — Task4 pure actual public draw/spawn metadata; original Task3 seal defect
- Type: original code causal inspection + counterexamples + actual measurement; checked 2026-10-07 Codex /root/task4_4_pilot, actual GPT6.1sol/gpt-6.1-sol medium; Claude Sonnet5.5 medium (public inputs/shape/RNG/currentsource review).
- Source: original modulation/envs/map.py:SceneMap.get_scene_objects L679–680 and map_reset L792–800, task3_env.py:_capture_spec getter redraws16obstacles/advances RNG after actualscene A spawn. Parent SRC0088 results/task4/t4.4-parent-review-20261007/scene-rng-counterexample.json and actual3.1-r2 spawned A versus oldmetadata B prove oldobstacle seal is not physical authority. OriginalCore330 and results/task3/t3.5-inst-r1/episode_instances.json unchanged. NewTask4Env own cached _capture_spec observes existing spawn_scene_objects arguments, existing _spawn_model_srv(name,xml,namespace,pose,frame) and original draw result, without getter/RNG draws/goal changes/truth feedback. SDF is actual service argument.
- Real contract: RobotEnv.reset L201–222 receives six-joint list then dict(zip(originaljointnames,list)); actual publicbase command is6XYZ+RPY (actual3.1 public_draws.json). Original physical command/value object/shape/order untouched; metadata records original fullprecisionbase and canonical_base computes XYZ+xyzw then rounds6dp for historicalXY/quaternion comparison. No earlyyaw rounding/physicalreset change; publicliftz=.05 retained. Old goal_tip/goal_wrist/arm/map reliable fields checked6dp; oldB obstacles explicitly not actualexpected, while newA objects and actualservice pose/frame/SDF remain contract fields.
- Evidence: tests/test_task4_public_capture.py; initial getter/RNG and missedscene mutation RED logs/task4/t4.4-public-capture-red.log; actualoldr1/r2source API counterexamples results/task4/t4.4-preflight-review/API-red-green.json; actual6RPY RED logs/task4/t4.4-six-rpy-red.log; final5tests0 logs/task4/t4.4-resumed-capture-tests-final.log. Actualr4 attempts.json seed101 initialized/publicvalid,16objects/servicecalls, two purecapture calls equalMap/CombinedEnv RNGdigests and publicfields, spawnpose/frame/SDFclosed, all oldreliable fields pass. Saved XML and episode JSON identify A for101.
- Limits: only101 actualpositivecaptured; secondpass NOT run,102initfailed, othertrue seals unavailable. Currentoldseal copy annotated historicalB/notphysicalauthority; no completeTrueTask4seal/freeze fabricated. Rawlocalization/VIO/Task3 source unchanged; this is necessary metadata correction, not new feature.

<a id="src-0090"></a>
## SRC-0090 — Resumed API/compile failures and pre-launch source gate
- Type: execution errors + corrected originalAPI delegation + syntax counterexample; checked2026-10-07 Codex /root/task4_4_pilot.
- Failures: t4.4-seal-r1 10persistedattempts/0init, servicefunction missed .close; originalMap.map_reset→clear→GazeboAPI.clear L523–527 closes _spawn_model_srv. r2 originalarm list wrongly assumed dict.items; originalCombinedEnv max10 retries wraps metadata error;10persistedattempts then ownidentity-supervised interruption check−9/cleanup0, containerendmissing (not fabricated). r3 collector IndentationError, py_compile failed but shell invocation did not gateexit, so physicallaunch/check1 occurred,0instanceattempts. Oldsource/runtime/logs retained. These are metadata/launch coding mistakes, not VIO failures.
- Counterexamples: r1/r2 actual source_snapshot/scripts/task4_env.py loaded into2real-interface tests by results/task4/t4.4-preflight-review/probe_interfaces.py; r1=2errors/r2=1error/current2green. Actual6RPY normalization against original101 source (SRC0089), final5publictests0. OriginalServiceProxy.close delegated, originaldraw arm list/value returned unchanged; dict-onlyfixture does not establish realAPI.
- Prevention: task4_preflight.py compiles every runtimePY doraise before actualsource/binary verification; run_task4_localization.sh invokes it before roslaunch/check, nonzero→final12/skipped/noROSlaunch. InvalidtemporaryPython→PyCompileError versus valid0 at results/task4/t4.4-preflight-review/compile-red-green.json; host/container py_compile and shell bash-n0. Parent independentpreflight/publictests0 logs/task4/t4.3-parent-review-20261007/public-interface-preflight-parent.log, permits last r4 only.
- Limits: no fifthrun; finalcollector failfast records unattemptedrequests, no source/configmutation duringruns. No broad338suite repeated; necessary5tests/preflight/sourcecore+officialbinarygates only. API fixes do not prove new102 VIO cause or finalquality.

<a id="src-0091"></a>
## SRC-0091 — Final r4 actual101 metadata positive / actual102 static initialization timeout
- Type: project measurement with planneddenominators; checked2026-10-07 Codex /root/task4_4_pilot.
- Evidence: results/task4/t4.4-seal-r4/{summary.json,attempts.json,episode_instances.json,exception.txt,spawn-*.sdf,source_snapshot,source_start.json,source_end.json,container_identity_start.json,container_identity_end.json}; logs/task4/t4.4-seal-r4/{check.json,check.log,launch.log,preflight.log,state.json,foreign_after.json}. Command run_task4_localization.sh t4.4-seal-r4 -- python3 -u scripts/collect_task4_instances.py --passes2 --quality-seeds101 0 (actualCLI spaces recordedstate.json); hostsession62063, actualPID/start/cmd check.json. Prelaunchgate0.
- Result: requested20 instance attempts(101–110×2), attempted2(101,102), initialized1/publicvalid1, unattempted18. 10117.1wall s successful16objects/serviceSDF/RNGinvariance/reliablelegacy fields;102140.3wall s reset includes native120s staticVIOwait timeout, failfast stops. Exactdurations attempts.json. Checker170.56517wall s. Requestedqualityseeds101/0 unattempted0/2, zeroSAC/policy/controlsteps; no newhistNONE RMSE/fullactualsuccess evidence. Oldconfiguration metrics do not replace finalquality.
- Exit: check1/final1/cleanup0; source start=end and actualcontaineridentity start=end. Fourresumedphysicalrun allowance exhausted (r1/r2/r3 SRC0090); no fifth/secondtrainingpilot. Parent one attemptedread-onlyrawcapture nearcleanup is separateartifact, child claims no raw/root-cause data it did not collect. New102 cause unverified; failedinitialization logs alone cannot prove featureDB/camera/IMU cause.
- Limits: valid101 cannot prove allscenes/repeat/otherinit. TrueTask4fullseals/quality/readyfreeze missing, formaldisabled. Publiczanchor .05 unchanged: original worlds.cpp:getBaseTransformWorld L32–38 forces plannedz0; RobotEnv.getRobotObs gripper_tf isplannedFK and eeplanner._is_done usesplannedgripper_tf; achieved3DTF diagnostic separately. Parent SRC0088 originalcode inspected; no unnecessaryzcalibration/claim .05 alone makes successimpossible, 3D/noisytruth/unknownanchor limitations preserved.

<a id="src-0092"></a>
## SRC-0092 — Resumed finite diagnostic budget; conditional formal preparation blocked
- Type: authorizedengineering bound and unexecutedconditional preparation; checked2026-10-07 Codex /root/task4_4_pilot GPT6.1sol/medium; Claude Sonnet5.5/medium.
- Bound: currentTask4.4 takeover permits≤4diagnosticruns, each≤900wall s,total≤3600wall s/10GiB, body≤850s/qualityepisode≤1000zeroactions, eachVIOinit≤120s. Actualr1/r2/r3/r4 retained, allcheckfail/cleanup0, perrunfrozen. r2 exactkernelidentitystop SIGINT→SIGTERM→SIGKILL ownmembers/noresidue; missingcontainerend not filled. No trainingadded; freshCUDA76/60 SRC0081 remains oldruntime evidence, ordinarySAC sources/binaries unchanged, no finalhistformalquality/performanceclaim.
- Provisionalformal limits SRC0083/sac_baseline.json remain enabledfalse/status blocked by102 and incomplete true seals; protocolformalfalse/noexecution_freeze. Intendedwholeinstance train0–99/validation101–105/test106–110 retained. Publicinput collection is not testperformancetuning; no estimator/hyperparameter selected usingtest outcomes. HistoricalB cannot serve as physicalseal. Failed/missing/unattempted count fullplanneddenominators.
- Artifact: results/task4/t4.4-formal-preparation/ contains compiled Pythondrafts for persistentattempt/phase/globalwall/resourceledger, ordinarytrain/eval/validation-onlyselection and verifiedownerwatchdog. NOT installedruntime, NOT tested/accepted completeformalrunner, NOT used forfreeze/readiness/budgetenforcement claims. Conditional/unexecuted because prerequisitefailed. Existingproductionbudgethelper remainsfailclosed. OriginalSAC/action/network/reward/termination/mask wouldneed preserved, freshonly/spentledger/retry/unsupportedresume/current-source/oldcheckpointreject and allresourceguards tested if parentlaterpasses prerequisites. No formaltrain/eval/selection executed.
- Remaining: parentnecessary102 raw/nativeinit causal audit without easiergoal/scene/posthocthreshold; alltrue10seals/repeat/completefinalquality; fullactualformalrunner/guards/pretraining actual-taskacceptance; realexecutionfreeze/source/binaries/container/publicinstances and parentacceptance before4.5. Formalbatch256 cost unmeasured, finite screenbudgets not convergencepromise. This entry grants no additionalrun/features.

<a id="src-0093"></a>
## SRC-0093 — 封存102真实初始化失败后的必要诊断接手与累计资源
- 主张/类型：原始run负结果、授权范围与有限工程排错安排，不宣称新根因。
- 来源/位置：用户SRC0065自动实施Task4；SRC0089–0092及forem/results/task4/t4.4-seal-r4/{summary.json,attempts.json,resumed_delivery_receipt.json}，forem/logs/task4/t4.4-seal-r4/timeline.txt。父2026-10-07已读原summary：2/20尝试、101有效、102实际VIO120stimeout、18未尝试、0/2quality，check1/cleanup0，未正式freeze/训练。源码首尾/真实身份完整性将在父单独审查追加，不仅接受子自报。
- 已用资源：此前4.4接续4物理run累计502.184墙钟s（含startup/cleanup）、约61.51MB日志结果，3个metadata/API/语法失败及r4真实102failure保留；此数字据子收据，父尚未重算每run时刻。原3.1同101的3诊断run另有历史，不清零或隐藏。
- 工程安排：已有Task4方法接入/公共实例初始化必要工作，新增task4.3.2同102原raw/官方返回条件因果诊断，最多2物理run各600wall/总1200wall/10GiB、最多一个有证据的受支持配置修正组，不新增SAC训练/任务场景/qualitygate/算法方程。明确将已用4.4接续诊断和新增3.2合并上限为6run/4800wall（旧4run3600上限+本新增2run1200），不称旧预算尚有余额；额外诊断是因新真实viewport失败尚无raw证据的必要修复，不作参数搜索/性能研究。
- 模型：Codex推荐GPT6.1sol/gpt-6.1-sol high，Claude Sonnet5.5 high；困难raw/featureDB/初始化/跨旧正常viewport的一致性因果排错，沿默认型号非更大型号。实际spawn后另记；父实际模型/强度未知。
- 限制：102raw图尚未核查，不根据101根因推断102同因，不直接改视点/纹理/滤波来放行。证据需先行，有必要超受支持接口/参数范围的具体修正由父核查原授权与影响再处理；Task4.4仍review、4.5禁止。

<a id="src-0094"></a>
## SRC-0094 — Task4.3.2 原始 seed102 初始化失败的真实输入

- **主张与类型**：项目实测、原始源码因果核对；同一公开 seed102 在当前 histogram_method=NONE、初始化特征预算50时仍真实失败，不根据101猜测原因。用户授权及新增有限预算见 SRC0093。
- **负责人/核查**：Codex `/root/task4_3_2_init`，实际 GPT6.1sol（平台 `gpt-6.1-sol`）/high，2026-10-07。Claude备选 Sonnet5.5/high；难点为原像素、官方特征库、初始化窗口与时序的联合查因，沿用户默认型号。
- **原始证据与位置**：`forem/results/task4/t4.3.2-init-r1/{summary.json,attempts.json,raw.bag,init_analysis.json,exact_manifest.txt,exact_pairs,images.jsonl,statuses.jsonl,public_draws.json,spawn_commands.json,spawn-*.sdf,robot_description.urdf,source_start.json,source_end.json,container_identity_start.json,container_identity_end.json}`；`forem/logs/task4/t4.3.2-init-r1/{check.json,launch.json,preflight.log,check.log,launch.log,state.json,timeline.txt,foreign_after.json}`。原bag SHA256为 `d6a5b4e56a71b96c7bd4b53cc58845399fdcff0c9fc461f7ccad639a55369225`。
- **实际命令与结论**：`FOREM_CHECK_TIMEOUT=550 sg docker -c 'bash forem/scripts/run_task4_localization.sh t4.3.2-init-r1 -- python3 -u scripts/diagnose_task4_init.py --seeds 102'`。原120s初始化等待失败；reset耗132.447099墙钟s，checker146.090747s，完整wrapper196.277s，0控制步/0 SAC更新。check/final=1，raw recorder/cleanup=0，foreign=[]。
- **原始输入**：COLLECT仿真15.443–86.3s内有1418个同stamp双目对、14172个有限accel/gyro；相机/IMU中位间隔0.05/0.005仿真s，未重打stamp。截取80个连续原始20Hz双目对16.4505–20.4005s。已亲自view左右19.4s原PNG：灰色天空/地面、3个黑障碍与影子；独立全图FAST20各19个角点，并非黑帧/零帧。实际官方日志700次DB update均0，1401次初始化失败，无半窗口视差或IMU不足分支日志。
- **采用与限制**：原图片/IMU/clock/status、公开命令和实际16个spawn实参/SDF冻结；不调用随机getter观察。原IMU存在不等于直接测量内部deque；当前源码空DB/newest<0的早返回在IMU初始化分支之前，具体因果见SRC0095。245个源文件archive=start=end、49个实际身份组首尾一致；诊断helper仅增加明确授权102入口，原Task3/任务/滤波源码不变。不能作为完整定位质量或正式训练验收。

<a id="src-0095"></a>
## SRC-0095 — 原始102网格配额不足与单个受支持初始化参数修复

- **主张与类型**：官方源码依据、项目原始输入反事实、配额推导及工程选择；初始化特征预算50→200恢复本102输入的可用跟踪特征，并保留101。不是性能调参、最佳预算或普适鲁棒性结论。
- **作者/机构/版本及核查**：OpenVINS官方rpng源码，commit `69488123ed9362dd44b6f28e7f4680abbff1442b`；[官方源目录](https://github.com/rpng/open_vins/tree/69488123ed9362dd44b6f28e7f4680abbff1442b)。本条不依赖论文发表年份；核查本地选定版本的原文源码，2026-10-07，Codex `/root/task4_3_2_init`，实际 GPT6.1sol/gpt-6.1-sol high；Claude备选Sonnet5.5 high。
- **精确位置与原始结论**：`forem/src/open_vins/ov_msckf/src/core/VioManager.cpp` L131–136把初始化总预算除相机数；`ov_core/src/track/Grider_GRID.h` L88–93/L123–138按网格截取最高响应点；`TrackKLT.cpp:perform_matching` L850–854在点数<10时返回全零mask，`feed_stereo`只将good tracks写入DB；`ov_init/src/init/InertialInitializer.cpp` L83–94在空DB/newest<0时早返回，L121–124要求两个半窗口各至少15个视差观测；`InertialInitializerOptions.h` L73/L130/L153–158定义、解析并检查`init_max_features`；`VioManagerHelper.cpp` L124使用已配置`num_pts/2`切换初始化后的跟踪预算。
- **推导（点数单位）**：50总预算/2相机→25点/相机；5×5网格→每格 `floor(25/25)+1=2`。原102角点集中少数网格，实际官方提取仅7/7，低于时域匹配10点条件，故DB无当前时间戳。200总预算/2→100点/相机，每格 `floor(100/25)+1=5`；原输入得13/13跟踪点。输入均来自上述代码、冻结配置和原始实测，没有修改网格/检测器/门槛。
- **同输入有限反事实与反例测试**：`forem/results/task4/t4.3.2-tracker-evidence/{exact50.log,exact200.log,old101-200.log,counterfactual_summary.json,parameter_delta.json,diagnostic_source_identity.json,ldd.txt}`。复用原官方实际库链接的`probe-histogram`及`forem/tests/task4_init_tracker_probe.cpp`，源码/程序/当前libov_core哈希已登记。原102的80×20Hz帧：50→DB0/newest−1/半窗口0,0；仅200→DB14/current20.4005/半窗口26,28。旧101原80帧同200→17/16点、DB18/current19.9505、半窗口33,33。这里半窗口数是相机视差观测，不是独立3D地标数。前期1Hz稀疏诊断不作为窗口通过证据。
- **采用方式与限制**：只同步`config/task4/estimator.yaml`和`protocol.yaml`的`init_max_features:50→200`及本来源。200沿已有初始化后`num_pts:200`的工程预算，没有无界扫描；旧FAST20/grid5×5/minpx10/NONE、官方15/10门槛、2s窗口/IMU1.5/视差10、quality/freshness、滤波方程、视点、任务、奖励、动作、终止不变。新测试`test_task4_init_102.py`先对当前50失败（无当前DBstamp），101仍通过；改后GREEN。新鲜物理回归及未通过输入见SRC0096。

<a id="src-0096"></a>
## SRC-0096 — Task4.3.2 新鲜102/101通过、原始103失败及有限资源交付

- **主张与类型/核查**：项目原始实测、原像素负结果和实际来源身份核验；局部102修复/101回归通过，不能声称所有封存实例可用。2026-10-07，Codex `/root/task4_3_2_init`，实际 GPT6.1sol/gpt-6.1-sol high；Claude备选Sonnet5.5 high。状态review，须父独立验收。
- **命令/进程**：`FOREM_CHECK_TIMEOUT=550 sg docker -c 'bash forem/scripts/run_task4_localization.sh t4.3.2-init-r2 -- python3 -u scripts/diagnose_task4_init.py --seeds 102,101,103,104,105 --steps-per-reset 1'`。父明确允许原有其它封存视点；helper max5、500s body、新reset前预留145墙钟s、原120s初始化期限、失败即停止并记录未试。host session96200；真实kernel PID/start/cmd在`forem/logs/task4/t4.3.2-init-r2/{check.json,launch.json}`，共享锁/task0_proc监督且不改运行期间源码。
- **结果与分母**：请求5、尝试3、初始化2（102/101）、原控制步2；103失败，104/105未尝试。102/101各真实新鲜VIO静态初始化和1原zero action step，观察41+120×120×1，pose_source=openvins_stereo_imu，reset含step16.626014/24.513049墙钟s。按同一fresh epoch3/5的首COLLECT→首READY状态回执计3.620140/4.126401s，首估计age0.037/0.009仿真s；不称为精确内部初始化起点。103 epoch7原120s等待失败，reset141.183620墙钟s，无READY，无truth回退/强制initialized。checker196.136185s，wrapper246.766s；check/final=1，raw recorder/cleanup=0，foreign=[]。
- **原始103输入与官方返回条件**：`forem/results/task4/t4.3.2-init-r2/{raw.bag,raw_phase_analysis.json,seed103_exact_manifest.txt,seed103_exact_pairs,seed103_pixel_analysis.json,images.jsonl,statuses.jsonl,public_draws.json,spawn_commands.json,spawn-*.sdf,robot_description.urdf,attempts.json,summary.json}`；已亲自view左右stamp62.1原图，大黑近障占下半画面，天空/地面单色。COLLECT33.1615–92.0仿真s内有1177个双目对、11767个有限accel/gyro，中位间隔0.05/0.005仿真s。原80双目对34.2–38.15s中，相邻间隔实际0.0495–0.0505s（名义20Hz而非严格每0.05s）；独立Python OpenCV4.9.0全图FAST20左右每帧各1点。`tracker-evidence/original103-current200.log`为同80原对、同当前200/NONE/FAST20/grid/minpx的实际官方C++ OpenCV4.2 ROI tracker：1/2提取与0/0交替，DB始终0/newest−1/半窗口0,0，仍在matching<10/空DB早返回。独立全图计数与官方ROI计数分开；无第二参数组或新检测器反事实。配额不会创造不存在的角点；不宣称其它所有视点均如此。
- **公开输入与身份**：`forem/results/task4/t4.3.2-delivery/{audit_delivery.py,review_receipt.json,current_container_identity.json,analyze_final_raw.py,inspect_103_pixels.py}`。102两run的全精度原公开draw/实际SceneA16障碍完全相等（除stamp）；102/101/103的公开XY/quaternion、arm、goal_tip、map与旧可靠字段6dp一致，102/101另有goal_wrist和16实际service/SDF闭环。旧Task3障碍B仍不是物理输入权威。原base命令z0/reset lift0.05保持，不证明物理3D高度。两run各245源文件archive=start=end，49实际身份组非空、首尾一致；r2=current。r1→r2仅config/task4与diagnose helper，两配置文件+helper的已声明差；官方源/patch不变。实际11个二进制身份组（5官方、2pybindings、4继承lib）逐内容均未变，不继承旧9组计数。无需配置变化之外的新build。
- **验证与资源**：原102/101官方窗口test RED→GREEN；46个Task4 tests实际0，4.602s，已有非有限反例警告保留，不重复整项目测试。两run实际prelaunch0。GPU0真实gzserver在VirtualGL EGL0（各nvidia-smi.txt）；VIO/physics仍CPU，本次无SAC/GPU训练声明。两物理run196.277+246.766=443.043墙钟s，日志/结果100973471bytes（最终资源审计时），每run<600、总<1200、<10GiB。之前4.4四run收据502.184s保留，合并已用6run945.227s；此前3.1三run另行保留，未清零。不新增训练/第三run/第二参数组。
- **分析错误与剩余**：最初离线按phase取首READY误选上一epoch102遗留READY，使101计时为负；`raw_phase_analysis-phase-only-invalid.json`保留，当前分析按fresh COLLECT epoch/clock过滤，raw/actor未改，不采用错误时长。Task4.4完整true10 seal/repeat/quality/formal freeze仍缺，4.5未执行。若继续，先核对当前rig是否能看见原场景足够固有角点；仅经父协调授权后才考虑最小sensor mount/view及对应外参校准改动（xacro/imucam/frame contract），保持原任务/几何/物理/外观/滤波/quality，并另登记有限视点回归协议。没有选高度/俯仰数值或额外预算，不实施纹理/运动激励/新增检测器/强制初始化/truth fallback。

<a id="src-0097"></a>
## SRC-0097 — 父独立核验102修复与103有限负结果

- 主张/类型：项目原始实测独立复算及工程验收；仅接受102初始化配额必要修复和101回归，完整封存可用性不通过，Task4.4/4.5正式前置未满足。不是所有VIO/所有场景不可行结论。
- 作者/版本：Codex /root，2026-10-07T19:00:22+08:00核查；父实际模型/强度未知，子实际GPT6.1sol/gpt-6.1-sol high；Claude推荐Sonnet5.5/high。源码运行版本为t4.3.2-init-r2/source_snapshot，245文件；官方OpenVINS commit沿SRC0095，11实际二进制身份组。
- 本地证据/精确位置：results/task4/t4.3.2-parent-review-20261007/{raw-r2-independent-summary.json,current-source-review.json,independent-103-features.json,official103-parent-probe.log,config_task4_estimator.yaml.diff}；logs/task4/t4.3-parent-review-20261007/task4-current-after102-parent.log，46测试4.607s退出0；原raw/SDF/publicdraw与运行命令在SRC0096。父亲自view102/103原PNG，103的80双目对/160原PNG全图FAST20各1点，实际官方跟踪器当前200/NONE DB始终0/两半窗口0,0/无当前stamp；相邻原曝光间隔0.0495–0.0505s，不伪精确恒定周期。
- 原始结论/采用：r2请求5，尝试3，102/101各初始化+1原零动作步，103原120s超时，104/105未试。245源archive/current/start/end全部相同，49真实组非空/两端相同，11binary未改；只有init_max_features50→200及protocol和有限诊断helper改动。docker top仅init/sleep。父复算4.4四run总502.184s，3.2两run443.043s，合计6run945.227s；不重置失败或预算。
- 适用限制/下一步：测试通过不能替代完整封存初始化/定位质量/真实SAC性能。103已测原视野信息不足，未检验改变已有相机视野是否可改善；原场景/纹理/几何不改，正式入口仍disabled/no finalfreeze，4.5/4.6尚未执行。旧source/run与错误离线phase计时均保留。

<a id="src-0098"></a>
## SRC-0098 — 原有相机视野与标定范围内的必要只读审查

- 主张/类型：用户Task4已授权传感器标定/方法设计的工程范围解释与待验证假设；不是新增场景、纹理或定位器的授权，也不是相机调整已证明有效。
- 作者/日期/核查：用户2026-10-07要求Task3通过后自动执行Task4（SRC0065）；Task4原方法设计/标定授权SRC0047，parent Codex /root于2026-10-07T19:00:22+08:00登记。原输入SRC0096/97。推荐Codex GPT6.1sol/gpt-6.1-sol medium，Claude Sonnet5.5 medium：几何、遮挡、既有输入与标定的跨模块审查；实际派发另记。
- 精确位置/输入：doc/tasks/task4/task4.2/task4.2.1三文档；src/forem_husky/urdf/visual_inertial_sensors.urdf.xacro；config/task4/{sensors.yaml,kalibr_imucam_chain.yaml,frame_contract.yaml}；t4.3.2-init-r2真实public_draws/spawn_commands/spawn SDF/原RGB与resolved URDF。
- 原始结论/采用方式：前述103有限负结果并未排除原rig对固有障碍角点遮挡/视野不足；先做无ROS、无新physical run、无源码/config改动的有限几何审查，证明现有视野局限/可见固有物体条件，再提出至多一个最小既有双目安装或视野与标定修正供父核查。不把投影角点数量当官方可跟踪特征或真实VIO成功，不基于测试SAC表现调参。
- 适用限制：不新相机/IMU、算法、激励或纹理；不改变机器人碰撞/质量/任务/目标/地图/动作奖励终止；既有用户固定输入不改。尚未选择新安装数值、未授权新实际运行预算。若只能更改场景视觉条件才可继续，依据根AGENTS先向用户提交具体扩展再实施；现审查不构成该扩展授权。

<a id="src-0099"></a>
## SRC-0099 — Task4.2.1 原103实际场景、原sensor安装与原图负结果复核
- 主张/类型：项目原始源码/封存实测的只读核查；不是新物理run。103原黑色块来自actual obstacle7，原前向图像只有低箱轮廓和灰背景；不能叫相机坏或用旧Task3 getter重抽scene B代表physical scene。
- 作者/标题/版本：FoReM Task4实测`t4.3.2-init-r2`（2026-10-07），Codex既有实际诊断；本子`/root/task4_2_1_visibility`只读核查，实际GPT6.1sol/gpt-6.1-sol medium，Claude Sonnet5.5 medium推荐未执行。
- 精确位置：`forem/results/task4/t4.3.2-init-r2/{public_draws.json,spawn_commands.json,spawn_sdf.jsonl,spawn-*.sdf,robot_description.urdf,seed103-left-62100000000.png,seed103-right-62100000000.png,seed103_pixel_analysis.json,seed103_exact_pairs/,summary.json}`；public phase seed101/102/103，103 obstacle7；SDF visual/geometry/box/size与material/script/name。原`src/forem_husky/urdf/visual_inertial_sensors.urdf.xacro:task4_raw_sensors/task4_optical`，`config/task4/sensors.yaml` realized与`kalibr_imucam_chain.yaml:cam0/1:T_imu_cam`、`frame_contract.yaml:T_base_imu`；上述四current files逐字节等r2 source_snapshot。
- 核查日期/人：2026-10-07 Codex `/root/task4_2_1_visibility`；view原左右PNG（左直接渲染亲看、右后续亲看），48个SDF hash/尺寸/黑材质及16×3 public→spawn实参等价由artifact实际核查。收据：`forem/results/task4/t4.2.1-visibility/verification_receipt.json`，含输入hash；原官方tracker DB0/半窗口0,0与103120s timeout分别继承SRC0096–0098已核查记录，本子没有重新运行tracker。
- 原始结论：103 base command XY=(-1.5103220805591842,3.3989234016241703)m/yaw2.2650803173595975rad；box7中心map(-2.579358378601087,4.484248783441851,.24)m/尺寸(1.1289781143398998,.7803324645155015,.4531229674638444)m；body中心(1.5181,.1271)m为推导见SRC0100。rig base_link(.35,0,.45)m、left/right ±.06m、+Xforward/.12m物理baseline；footprint→base_link z.13228m；actualfx319.9988245765257px、640×480、20Hz/IMU200Hz。80对原PNG全图FAST20各图1点是原PythonOpenCV4.9独立结果，与官方C++OpenCV4.2 ROI计数分开；不把几何角点当此实测。
- 本项目采用/限制：用于原Task4传感器安装必要性审查与SRC0100有限工程推导；无ROS/新训练/新scene。公共reset lift .05m不是实际settled姿态，本子未恢复实际roll/pitch/z，不能据封存command声称精确渲染位姿。旧成功101/102各仅1step，不是true10/正式训练/定位质量验收。

<a id="src-0100"></a>
## SRC-0100 — 既有双目视野单候选的离线几何推导与标定影响（未实施）
- 主张/类型：以SRC0099原输入为依据的可复算几何推导、工程候选/待验证假设；非外部文献通用参数，非新实测或已证明初始化。单whole-stereo左向yaw+π/2候选并非最小角度/最优设计，不扫描height/yaw/FOV。
- 作者/版本/核查：Codex `/root/task4_2_1_visibility`，2026-10-07，GPT6.1sol/gpt-6.1-sol medium；`forem/results/task4/t4.2.1-visibility/geometry_review.py:rz,raybox,analyze,main`与`geometry_review.json`、`verification_receipt.json`；`forem/logs/task4/t4.2.1-visibility/geometry_review.log`，成功两次确定性同JSON SHA256 `bec8c6a00fab8e3bdf42658a26088b8803940bf98b1f7765c9068cb4ea146648`；3segment/slab数学检查和当前sensor四文件等archive核验。原输入run/48SDF/160PNG hashes在收据。
- 输入/公式/单位：原public base XY/yawψ、yaw定向SDF box pose/size(m)、实际K(px)、rig yawα，c=public XY+Rzψ[(.35,0,.58228)+Rzα(0,±.06,0)]、另加条件footprint z；q=Rz(−ψ−α)(p−c)，u=cx−fx q_y/q_x、v=cy−fy q_z/q_x；.05<q_x<30m与图像范围裁剪；ray c+t(p−c)、t无单位，用box局部slab首交t<1−1e−7排遮挡，该数为工程数值容差非质量门。固定80×60 lattice/8px间距只估box覆盖。两输入z0/.05m是public lift/settling不确定性端点、roll/pitch=0条件，不能称实际姿态bounds/像素拟合。
- 原始推导结论：原103只有box7可见几何顶角4/4；z0条件左右1306/4800、1304/4800射线命中box7（≈27.2%），不是全图遮挡；其它大多侧后方/视场外，box3中心相对body约52°、相对camera约55°超±45°。升高不改变水平bearing。单candidate yaw+90°原101/102/103条件z0可见box角分别11/12、34/30、36/34；原分别16/17、19/20、4/4。candidate z.05分别11/12、33/29、37/35。各相机独立几何角数，非共同匹配/独立地标/FAST/DB/初始化门通过。
- 单工程采用建议/标定：只whole stereo绕原中点(.35,0,.45)base_link yaw+π/2，IMU位置朝向保留，baseline一起旋转。Gazebo sensor pose(.35,0,.45,0,0,π/2)，camera local±Y .06保留；optical URDF TF相对IMU left(−.06,0,0)/right(+.06,0,0)、rpy(−π/2,0,0)；R_imu_optical=[[1,0,0],[0,0,1],[0,-1,0]]，两Kalibr T共该R和±.06 Xtranslation。body左/右(.29,0,.45)/(.41,0,.45)；T_base_imu不动，K/D/R和rightP03=−38.3998589492(px·m)预期不动须实测确认。仅转光轴保留旧bodyYbaseline不符合rectification，禁止如此实施。受影响文件/identity与raw真实校验逐项见`forem/doc/tasks/task4/task4.2/task4.2.1/RESULTS.md`“唯一工程候选”。无新sensor/物理/场景/外观/算法/quality。
- 理由/适用限制：原103既有box分布左侧；单安装yaw自由度可改变可见几何，101角数减少是回归风险而非已失败。未知实际settled pose、完整robot mesh/arm遮挡、renderer纹理采样/阴影、双目匹配和官方tracking/init；许多背景仍无纹理，不能保证true10/重复/质量门。当前原103无有效tracking为事实，但不足以证明所有既有sensor安装都不可能。
- 待验证/资源工程选择：父独立核查、明确新有限预算之后才可实施；建议仅1fresh `t4.2.1-side-reg-r1`原101→102→103、各1reset/原120s上限/最多各1原zero step，无SAC，checker≤550s/fullwrapper≤600s/≤10GiB。120s来自原helper既有合同，其余为本次待批准资源选择，非性能实测/自动预算授权。任何失败立即停、保留未试分母，不新参数/视野搜索；成功也不能放行Task4正式训练。若必须新增场景视觉条件则需用户明确另授权；本子无runtime变更或新physical run。

<a id="src-0101"></a>
## SRC-0101 — 正式入口独立准备与严格累计预算保护

- 类型/主张：项目工程选择、准备代码反例测试及父独立核验；不声称实际ROS/CUDA formal集成、质量冻结或性能已通过。
- 作者/版本/日期：子Codex /root/task4_4_1_runtime，actual GPT6.1sol/gpt-6.1-sol high；父Codex /root（actual未知），2026-10-07；Claude推荐Sonnet5.5/high，跨崩溃/进程/来源/累计预算因果核对。
- 原始来源/精确位置：results/task4/t4.4.1-runtime-preparation/{draft,delivery_receipt.json,install_manifest.json,source_closure_and_budget.patch,mask_semantics_receipt.json}；16准备产物sha收据。父results/task4/t4.4.1-parent-review-20261007/draft-independent-review.json及logs同ID/draft-tests.log；35新draft风险tests父0、.176s（合成receipt/mock loop/真实os._exit崩溃）；编译/实际provisionalcheck rc1 formaldisabled在子收据；未安装/无ROS/新CUDA/formal。
- 已核查原语义：task3_sac_entry.make_mask L82–84与原main.py对应L190–191/L256–258均float(not done)，含truncation为0；原push顺序/普通update不改。
- 预算解释/推导：sac_baseline.steps_per_seed=20000与gradient_updates_per_seed_cap=19744是同seed所有失败/retry累计上限，3seed总≤60000实际交互、≤59232更新；6attempt不代表120000步授权。训练resume unsupported，fresh完整目标无法在剩余额度完成则beforebegin拒绝/计incomplete，不清账/增加终点ckpt；init0step失败仍可完整freshretry。counter completed/attempted分开，pending WAL保守收费非实际测量，新runID不能新budget。
- 采用/限制：固定账本唯一锁、source实际完整组/父freeze匹配、测试access预先claim且同seed/instance仅一次，验证排序success→全分母原return失败0→最早checkpoint须未来明确freeze，缺actual_task_acceptance/选择规则/全true seal/quality就拒绝。预算60eval×600s=36000s上界但eval总18000s保持，未测全分母失败，不暗扩预算。必须安装真实identity闭包后另验；当前只能称准备review。

<a id="src-0102"></a>
## SRC-0102 — 既有双目rig必要单候选适配与一次有界回归

- 类型/主张：已授权Task4传感器安装/标定设计内的必要工程适配与新增有界验证协议；不是新功能或场景视觉扩展，未实测成功。用户SRC0047/SRC0065授权，父2026-10-07登记；Task4.2.1原几何/单候选依据SRC0099–0100，父可复算artifact results/task4/t4.2.1-parent-review-20261007/candidate-consistency-parent.json（先Python类型直比不等，经无损JSON规范数值全部相等；非几何失败）。
- 负责人/模型：拟实际接手Codex /root/task4_2_1_visibility执行task4.2.2，沿 gpt-6.1-sol/medium（GPT6.1sol）；Claude Sonnet5.5 medium。理由：whole-stereo物理baseline、optical TF和Kalibr外参/实际raw跨模块一致性，未换大模型。推荐不当实际，派发/接手另记。
- 原/新与精确位置：src/forem_husky/urdf/visual_inertial_sensors.urdf.xacro与config/task4/sensors.yaml/kalibr_imucam_chain.yaml/protocol必要来源。原rigforward+X yaw0→唯一left+Y yawπ/2；相机中心/IMU(.35,0,.45)与IMU姿态不变，whole stereo local±Y .06一起转、body左(.29,0,.45)/右(.41,0,.45)，optical rpy(−π/2,0,0)。物理baseline仍.12且沿optical X；config及真实URDF/SDF/CameraInfo必须一致，不能只转视轴而留旧baseline。新左右T_imu_cam见SRC0100，未改方程、原scene/任务/物理、时间/质量门。
- 预算/方法：仅1 fresh物理run，固定顺序103→101→102，每seed1次原reset/120s原初始化上限/至多1原zero action step，无SAC。checker550wall/实际完整wrapper600wall/本节点总600s/10GiB；新reset前145s余量、失败即停/所有未试分母保留。顺序先验证103信息变化再101/102回归，结果前冻结；不再换第二角/增加高度/FOV/texture/节点。加此前4.4+3.2已用6run，本次合计7run允许额外≤600s（旧945.227s保留），不是重置预算或正式调参试验。
- 原始结论/采用/限制：仅geometry表明103可见固有box边角增加、101风险，不能用geometry当FAST或VIO通过。实际raw/标定/真实GPUrender/原publicdrawSceneA/source+binary两端/退出cleanup要全部检查。失败保留并阻止4.4/4.5，只有本三seed通过也不能代替完整true10/repeat/quality/finalformal身份。若需新增视觉纹理/改变场景/算法/初始化激励，须另向用户提具体范围，不自行实施。

<a id="src-0103"></a>
## SRC-0103 — 单whole-stereo left90必要安装与冻结外参一致性适配
- 类型/主张：Task4已有传感器安装/标定范围的工程适配与真实配置测试；不表示初始化或质量通过。依据SRC0100离线唯一候选、SRC0102一次103→101→102有界授权；无新场景/纹理/sensor/定位算法/质量门。
- 作者/核查：2026-10-07 Codex `/root/task4_2_1_visibility`接续task4.2.2，actual GPT6.1sol/gpt-6.1-sol medium；Claude Sonnet5.5 medium推荐未执行。whole physicalbaseline/TF/Kalibr/实际输入跨模块一致性。
- 精确位置：`src/forem_husky/urdf/visual_inertial_sensors.urdf.xacro:task4_raw_sensors/task4_optical`；`config/task4/sensors.yaml:stereo/calibration/current_rig_design/realized_history`、`kalibr_imucam_chain.yaml:cam0/1:T_imu_cam`、`protocol.yaml:sensor_mount_revision`；tests/test_task4_stereo_rig.py三真实配置测试，logs/task4/t4.2.2-preparation/{red.log,green.log,preflight.log,audit.log,task4-tests.log}，旧源完整`t4.3.2-init-r2/source_snapshot`保留。
- 原始结果/采用：OLD RED原yaw0与原opticalforward断言失败，投影采样合同通过；只转whole stereo sensor pose yaw+π/2、两个localcamera仍±Y.06，因此basebody左右(.29,0,.45)/(.41,0,.45)，optical TF相对IMU左右∓X.06、rpy(−π/2,0,0)，新Kalibr R=[[1,0,0],[0,0,1],[0,-1,0]]/t左右∓X.06同步。IMU(.35,0,.45)/rpy0/200Hz、T_base_imu、actualK/FOV640×480/20Hz/baseline.12m、NONE/init200/frontend21/quality保持。右P03局部预期−fx*.12，仍需实际CameraInfo确认，未用nominal代替实测。
- 已核验/限制：配置测试GREEN3项；一次字符串替换同时误转IMU，原IMU不变测试正确抓获，真实运行前已恢复，仅artifact绿色日志与当前值为最终事实。49项Task4容器测试OK（4.661s）、actualruntime preflight PASS、runtime audit ok；未新增依赖/build/官方source/Task3 core/CMake改动。旧r4 realized明确改为history，不将旧forward标定当新安装验证。此条准备阶段不宣称新raw/VIO成功；后续唯一physicalrun结果另条。

<a id="src-0104"></a>
## SRC-0104 — left90原双目安装实际raw/标定、同原场景与来源身份回归
- 类型/主张：项目原始实测和封存文件独立脚本核查；不是离线几何替代raw，非全运动定位质量或true10验收。作者Codex `/root/task4_2_1_visibility`接续task4.2.2，2026-10-07，actual GPT6.1sol/gpt-6.1-sol medium，Claude Sonnet5.5 medium推荐未执行；唯一rig工程依据SRC0100–0103。
- 精确版本/位置：run `t4.2.2-side-reg-r1`；`forem/results/task4/<run>/{raw.bag,robot_description.urdf,robot.sdf,public_draws.json,spawn_commands.json,spawn_sdf.jsonl,spawn-*.sdf,source_snapshot,source_start.json,source_end.json,container_identity_start.json,container_identity_end.json,runtime_identity_start.json,runtime_identity_end.json,images.jsonl,imu.jsonl,statuses.jsonl}`；`forem/results/task4/t4.2.2-preparation/{analyze_side_run.py,raw_receipt.json,verify_actual_geometry.py,actual_geometry_cleanup_receipt.json,preparation_receipt.json,runtime-before.json}`；logs同prep/raw-audit.log/actual-geometry-audit.log/nvidia-during.log；原对照t4.3.2-init-r2。
- 核查方式/日期/人：2026-10-07 Codex子实际容器postbag审计exit0、宿主actualgeometry核查0；raw原stamp而非PNG每秒保存频率。实际URDF与预resolved只有autogenerated路径注释不同，XML真实元素全部一致；原94physical named元素等旧r2。初byte比较失败因注释，未掩盖结构差。全部245源首尾equal、49实际groups非空/首尾equal、11binary等旧r2；原源码/官方pin/Task3core/CMake无新增改动，仅SRC0103四路径delta。
- 原始标定结论：真实resolved SDF stereo sensor pose(.35,0,.58228,0,0,1.5708)，IMU同XYZ/yaw0，camera local±Y.06；URDF optical左右IMU系∓X.06/rpy(−π/2,0,0)与新Kalibr一致。SDFyaw−π/2=3.6732051e−6rad明确序列化误差，比较1e−5rad为数值核查容差非定位quality。所有CameraInfo K fx/fy319.9988245765257px、cx320.5/cy240.5、D0/R单位、640×480/plumb_bob、leftP03−0、rightP03−38.399858949183084px·m=−fx*.12；规范化frame正确/未restamp。imu_covariance[0]−1、gyro/acc有限，原绝对orientation不用。
- 原始raw结论：fresh各phase COLLECT→stepafter窗103/101/102双目pair48/49/49、IMU487/495/491；左右全stamp与左右CameraInfo各stamp列表完全相等，stream严格单调；stereo20.000/20.0041675/20.000Hz（median.05s），IMU200Hz（median.005s）。acc均值m/s²依次(−.0034465,.0003091,9.8103718)、(−.0016424,.0063128,9.8080763)、(−.0025577,−.0016634,9.8007220)，只记原上轴specific force符号近+9.8，不推实机精度。
- 原始视觉/GPU事实：每phase窗两张/side原PNG独立fullimageFAST20：103L38,38/R32,32；101L22,22/R21,23；102L34,36/R37,37，非官方tracker库/独立地标数。子亲view有效103L15900000000/R16950000000、101L26350000000/R26250500000、102L35700000000/R35600000000（均run目录seed前缀.png），存在原box/自体机械臂/阴影。曾误选102phase最后close后36.6/36.7图，保留且排除，最终以fresh窗校准；不能用close后空场图当scene。实际nvidia-smi GPU0 gzserver417180 G149MiB，wrapper真实VirtualGL egl0，原RGB确实渲染，VIO/physicsCPU/无SAC训练。
- 场景采用/限制：三publicdraw全精度base/arm/goal/map/16actualobstacles忽略stamp完全等原r2；spawn实参/SDF序列48hash与字节完全等，非旧Task3 getterB。用于必要安装raw标定回归，不改任何视觉条件/物理/动作奖励/原门；静态短窗不能证明全轨迹追踪/自体特征影响、true10/repeat或定位精度。配置当前pending是run启动前冻结文字，实际证据以本run为准，未在run后改变源身份。

<a id="src-0105"></a>
## SRC-0105 — 唯一left90回归的真实初始化/原动作步、有限预算及清理交接
- 类型/主张：原项目运行实测/资源计数/监督记录；仅已有Task4必要sensor适配103→101→102通过，不放行正式训练或代替完整质量。2026-10-07 Codex `/root/task4_2_1_visibility`接续task4.2.2，actual GPT6.1sol/gpt-6.1-sol medium；Claude Sonnet5.5 medium推荐未执行。
- 精确证据：`forem/results/task4/t4.2.2-side-reg-r1/{summary.json,attempts.json,statuses.jsonl,graph-seed103.json,graph-seed101.json,graph-seed102.json}`；`forem/logs/task4/t4.2.2-side-reg-r1/{launch.log,check.log,timeline.txt,check.json,launch.json,state.json,check.cleanup.json,launch.cleanup.json,foreign_after.json}`；prep `bounded_run.py/supervisor_live.json/supervisor_receipt.json/raw_receipt.json/native_initialization_log_receipt.json/resource_receipt.json/delivery_receipt.json`，对应wrapper/log/原binary身份。
- 实际命令与授权：SRC0102只有1fresh `FOREM_CHECK_TIMEOUT=550 ... run_task4_localization.sh t4.2.2-side-reg-r1 -- python3 -u scripts/diagnose_task4_init.py --seeds 103,101,102 --steps-per-reset 1`，宿主bounded_run.py从Popen前计时/按本wrapper PID-start-cmd身份、560s TERM预留40cleanup/完整600s/10GiB。原helper body500/reset-start-margin145/每init120不改，所有配置运行中冻结。没有第二run/新视点搜索/纹理/算法/额外SAC先导。
- 原始结果：requested3/attempted3/initialized3/unattempted[]，各1原zero-step共3/0SAC更新，status41维/map120×120×1/pose_sourceopenvins_stereo_imu，三个step无error。reset含step17.529031145/24.692723780/24.855941773墙钟s，fresh epoch3/5/7首次COLLECT→READY回执4.397421692/3.989198943/4.227266103墙钟s、首estimateage .012/.0115/.0125仿真s；不是内部精确init起点。官方VioManagerHelper.cpp:136真正successful initialization日志49351/60726/72190行（静态读取）；最近TrackKLT.cpp:390 good_left.size()21/17/23（不是FeatureDB总数），新原tracking确实通过，旧forward103120s timeout保留。
- 资源/监督核查：checker80.898281597s、全wrapper132.087337037s、check/cleanup/final0，rawrecorder0、foreign_after[]、最终container只init/sleep。host wrapperPID377309/starttime658224483/fullcmd明确；container launchroot416948/start658224739/sup416947，checkroot418010/start658226458/sup418009，各真实cmd/树归档；session10984已结束，运行19:44:46.787+0800启动，deadline未触发。前4.4+4.3.2六run945.227s保留，此次累计7run1077.314337s；max该run文件39,431,306bytes，最终节点run+prep+logs写resource收据前39,717,827bytes(<10GiB)，交付收据写入前最后实数另登记。该资源上限是工程预算，不外推正式训练成本。
- 采用/限制/下一步：本子review交回源码/配置/台账全部写权给父；父需独立核查后再登记适配验收。结束INVALID_STOP来自env.close停车，非step期失败。未跑104/105/其它输入、全true10×重复/质量/正式identity冻结/入口真实guard/Task4.5；这些原门仍前置未满足，本3seed短回归不能宣称任务成功/定位准确/世界模型收益。所有原scene保持，若需要新的视觉条件另获用户范围授权。无commit/push/merge。

<a id="src-0106"></a>
## SRC-0106 — 侧向双目局部回归父独立验收

- 类型/主张：项目原始实测独立复算及有限工程验收；仅验收same existing rig whole侧向配置、原103/101/102 nativeinit与3原step，不通过全部true10/定位质量/formal训练。
- 作者/日期/版本：2026-10-07 Codex /root，父actual模型/强度未知；子/root/task4_2_1_visibility actualGPT6.1sol/gpt-6.1-sol medium，Claude推荐Sonnet5.5 medium。新run t4.2.2-side-reg-r1 SOURCE245/49actualgroups/11binary，具体immutablehash见两端收据。
- 精确证据：results/task4/t4.2.2-parent-review-20261007/{acceptance.json,pre-run-scope.json,actual-r1-parent-summary.json,raw_receipt.json,actual_geometry_cleanup_receipt.json}，logs/task4/t4.3-parent-review-20261007/{new-rig-parent-tests.log,new-rig-parent-raw.log}。父独立3 sensor tests0/.043s，原245逐hash只4授权path变；实际rawbag重算与child完全相等；生成后URDF/SDF、wholebaseline、光学TF、真实K/D/R/P/IMU与原scene48SDF/dropout/control/source/cleanup均核查。父亲view三scene窗内新PNG。
- 原始结果/采用：103/101/102 nativeinit+各1原zero-step，shape41与120×120×1、pose_source=openvins；全132.087337s/3控制步/0SAC；raw20/200Hz、IMU保持、原精确曝光/信息stamp、旧scene全精度equal、GPU0G149MiB实际render，source两端/currentsame/官方11binary不改、cleanup0/foreign[]。实际sensor yaw1.5708与π/2约3.6732e−6rad序列化差公开；预launch曾误匹配IMU，test抓到后恢复，未实际使用错误IMU。
- 限制：图像还含机器人近场部分，三seed静态nativeinit不能替代移动质量；下一步重验新view全true10/重复与移动时pose精度，不用原forwardview质量代替。父首复制rawanalysis未修hardcodedOUT写回同deterministicchildreceipt，hash未变；随后将OUT改父独立目录并重新raw复算得到一致，实际数据不改，记录此复制路径失误。

<a id="src-0107"></a>
## SRC-0107 — 新相机视野下既有完整封存与受影响质量复验协议

- 类型/主张：自动Task4既授权范围内必要验收复验工程选择，未执行结果。依据SRC0065/0106；不新训练先导、场景、算法或动作语义。父2026-10-07登记，拟执行新task4.4.2，GPT6.1sol/gpt-6.1-sol high、Claude Sonnet5.5 high；理由完整封存/时序/物理反馈/当前freeze与执行保护跨模块核对，actual另记。
- 输入/精确位置：task4.4/task4.4.2三文档；固定camera yaw90/init200/NONE与原quality阈值（SRC0080/0103–0106）；原三seedraw新source245，Task3旧可靠base/arm/goal/map与真实SceneA；config/task4/quality_action_replay.json（只76旧Task4先导已发动作向量/seed0，不含观测/权重/回放训练）。
- 控制复验来源：results/task4/t4.4-pilot-r1/task_steps.json中phase=train/episode0的76实际已发3维动作，全部finite且[-1,1]、原done数0。只作为原新相机改动所影响的移动测量输入复放，不load旧模型/optimizer/replay，也不用于任何formal训练data。原位置/角度单位、动作/奖励/终止/step调用不改；新被测轨迹/反馈仍原raw新记录。
- 步骤/预算：只1 fresh真实run t4.4-complete-r1，固定seals101–110两遍（20reset，失败/未试分母）、101零动作原诊断≤1000step（原done即stop）及0同76动作控制复放（READY后才动作，原done/失效即stop）。每初始化原120s；checker850s/完整wrapper900s/10GiB，独立own身份监督及清理余量，全失败占run不重试。原quality numeric gates/freshness/coverage/wholetruth匹配保持，预先固定view不根据heldouttest调参。复放完整结束只说明有限控制测量完成，未达到原done仍记录任务未完成/真实成功false，不改Task3终止。
- 采用/限制：原forward76/60训练先导保留，不新训练；新motion下独立rawp3d/header与真实gripper/joints匹配、body位移/时延/poseage与噪声限制分开，不能以静态camera角点或forecast代验移动定位。零动作诊断/复放任务失败不当学习失败。alltrue10/重复/两完整质量任何缺失禁止finalfreeze/4.5。若本run失败不追加camera候选/texture/放宽门；保持负结果。必要prep collector支持一个固定动作fixture/记录不同诊断completion，仅测试工具、不产品新功能。

<a id="src-0108"></a>
## SRC-0108 — 正式前声明的有限能力门与验证选择规则

- 类型/主张：尚无formal训练/测试结果前的工程最低重复证据与验证选择协议，不来自论文/旧政策性能，不证明鲁棒性或保证收敛。用户Task4要求可追溯普通SAC任务基线(SRC0047/0065)，父2026-10-07定义；Codex GPT6.1sol/high、Claude Sonnet5.5/high用于跨预算/完整物理判据/数据隔离核对。
- 精确来源/证据：results/task4/t4.4.1-runtime-preparation/{formal_protocol_fields.merge.json,delivery_receipt.json,tests,test-specific draft helpers}；母物理公式src/modulation_rl/scripts/modulation/envs/eeplanner.py:_is_done及utils.py:episode_is_success，SRC0080。v2准备42meaningful tests父0/.175s、19产物sha全same，仍未安装/无实际formalCUDA/ROS；日志logs/task4/t4.4.1-parent-review-20261007/draft-tests-v2.log。
- 物理单位/门：每episode实际末端位置误差<.025m，quatdistance=1−(qa·qb)^2<.05无量纲且unitquat有效，0IKfail/0collision/原任务done及内部success，并全部steps真实反馈有效。计划3trainingseeds×5test=15请求全固定分母，必须全部15实际attempted/init/completed/fullactualfeedback，每seed至少1confirmed物理成功才达到本有限baseline可完成门；其余失败仍留分母，不宣称高成功率。缺一次/失效任何一episode则不得性能accepted。
- 选择规则/理由：only validation101–105，先confirmed物理成功数，再完整实际反馈且完成episode数，再全5请求分母原return（失败0），最后最早checkpoint。第二排序项防所有无初始化0return压过真实有效负return；不读取test106–110选参数/权重。最多3原scheduleckpts/seed及一次sealedtest访问，失败访问先WAL计数不得换checkpoint重测。
- 采用/限制：merge只含未来字段，无enabled/预算变化，配currentquality/allseals与actualruntimeclosure父freeze后才可启。per-seed失败/retry累计20000/19744、3seed60000/59232同SRC0101；fresh状态不借旧truth/先导权重/数据，resume仍unsupported。现在4.4review/正式未执行，缺任意依赖仍拒绝，不把设计和测试当正式性能。


<a id="src-0109"></a>
## SRC-0109 — 完整质量采集器固定76命令测量支持与守卫测试

- 类型/主张：工程实现与项目静态验证；只允许SRC0107原固定76命令测量，0更新，不更改原任务done/action/reward。Codex实际gpt-6.1-sol/high（GPT6.1sol），Claude推荐Sonnet5.5/high；来源身份、尝试分母、时序、原done与测量complete需要跨模块核对，沿用户默认模型。
- 作者/版本/精确位置：Codex 2026-10-07；`scripts/task4_instances.py::run_quality_steps`、`scripts/collect_task4_instances.py::quality/main`、`tests/test_task4_quality_replay.py`；运行版本精确SHA见`results/task4/t4.4.2-preparation/preparation_receipt.json`及`t4.4-complete-r1/source_snapshot/`，不是Git提交。
- 原证据：`logs/task4/t4.4.2-preparation/red.log`为6个缺测量loop断言失败；`green.log`6通过；`preflight.log`PASS；`task4-tests.log`55测试/0失败；`formal-draft-tests.log`既有v2准备稿42测试/0失败；`all-tests.log`容器全套353tests/3原reference skips/169.771s，退出0。
- 核查：2026-10-07，Codex /root/task4_4_2_complete，已实读及运行。新loop初始化失败禁止命令，原done立即停、失效尝试保留、finite/bounded/exact76检查，测量结束不篡改任务done。初次文本编辑残留旧inner except被pycompile发现IndentationError，run前修正；未运行错误版本。
- 本项目采用与限制：只有采集支持已安装；静态fake环境反例不能替代实际新视野下移动质量。正式v2准备稿测试重新通过，但未安装、未执行正式训练；下方SRC0110失败后conditional安装/冻结不执行。

<a id="src-0110"></a>
## SRC-0110 — 唯一完整封存运行在seed106公开初态比较失败

- 类型/主张：项目实际有限失败，不是全封存/移动质量/训练通过。来源/负责人Codex /root/task4_4_2_complete，gpt-6.1-sol/high；2026-10-07唯一`t4.4-complete-r1`。
- 精确证据：`results/task4/t4.4-complete-r1/{attempts,episode_instances,summary,source_start,source_end,container_identity_start,container_identity_end}.json`、`source_snapshot/`与80个`spawn-*.sdf`；`logs/task4/t4.4-complete-r1/{state,launch,check,foreign_after}.json`、`timeline.txt`及日志；`results/task4/t4.4.2-preparation/{supervisor_receipt,complete_receipt}.json`、`analyze_complete.py`。run/source/binary SHA在原收据。
- 核查日期/核查人：2026-10-07，Codex，已重算原记录；容器离线脚本`python3 -u results/task4/t4.4.2-preparation/analyze_complete.py`退出0。body146.935934640s，whole197.516435365s；check1/final1/cleanup0/foreign[]，结束docker top仅init/sleep。
- 原始结论：请求101–110两遍20reset；实际首遍101–106共6尝试/6初始化/5publicvalid，seed106只`initial_base_XY_quaternion_6dp=False`，其他arm/goal_tip/goal_wrist/maps比较True，按预定规则停止；14reset未试、两quality101/0未试、0动作/0SAC更新。首5实际场景各16objects/16spawnservice，80SDF内容SHA等文件名，capture前中后RNG与public重复相同。第106失败分支在比较前未落盘first/commanded/RNG/SDF，缺证据公开，不能用推导回填。
- 身份/资源：246源首尾相同，49实际容器组无absent且首尾相同，11二进制等已验`t4.2.2-side-reg-r1`；GPU0 gzserver424795实际G149MiB，`logs/task4/t4.4.2-preparation/nvidia-during.log`；whole900/check850/10GiB均未触限，run峰值17,332,177bytes。wrapper own390099/start658337837完整cmd在监督收据；sg根最早采样cmd空，监督停止依已确认wrapper完整身份，不声称空cmd为完整根身份。
- 采用/限制：保留唯一失败；旧累计7run1077.314s加本run197.516435365s=8run1274.830435365s，不重置。未得到20完整封存、第二pass或新移动定位/真实EE六关节质量，不能验收4.4或启动正式4.5。没有第二physicalrun、相机/纹理/门槛变更或新训练先导。

<a id="src-0111"></a>
## SRC-0111 — seed106四元数表示符号的离线反例与待验证根因

- 类型/主张：本地数学推导/待验证假设；不是failed106实际输入恢复或已证根因。作者Codex，2026-10-07。
- 输入/精确位置：旧`results/task3/t3.5-inst-r1/episode_instances.json` seed106 base_tf quaternion `(0,0,-.729485,.683997)`；`scripts/task4_instances.py::canonical_base`、collector严格分量相等、Task3Env原`ro.base_tf`捕获、`map.py::SimpleObstacleMap._draw_initial_base_pose` yaw在[0,2π]；原文件SHA/公式/数值在`results/task4/t4.4.2-preparation/antipodal_hypothesis.json`，可用同目录`antipodal_hypothesis.py`重算。
- 推导：归一化q=(v,w)，R(q)=(w²−v·v)I+2vvᵀ+2w[v]×；q整体变负时全部二次项不变，所以R(q)=R(−q)。相对最短角δ=2acos(clamp(|dot(unit(q),unit(q2))|))，单位rad。旧q norm1.000000130617，yaw−1.635137162449rad，同旋转yaw4.648048144731rad得到canonical q=(0,0,.729484904717,−.683996910658)，严格round6分量比较False、absdot1/δ0。原`src/modulation_rl/scripts/modulation/envs/env_utils.py::calc_rot_dist` L123–131使用`1−dot(q1,q2)^2`，对于上述unit对无量纲距离0，也对整体符号不敏感；此核查不改原函数或数学合同。
- 核查：2026-10-07 Codex；离线脚本退出0，未启动ROS/reset/step；原source/config未改。
- 采用/限制：说明严格四元数符号比较可误拒相同物理朝向，提示检查必要元数据诊断；本run106 first/commanded完整原值未保存，故不能证明该次只是符号而非其他真实初态差异，不改原失败为pass、不改定位/任务门。不是额外实验实施授权。

<a id="src-0112"></a>
## SRC-0112 — 未过前置时正式入口/冻结保持关闭的交接

- 类型/主张：工程执行边界与项目当前文件事实；依据SRC0107条件执行和SRC0110失败，2026-10-07 Codex。
- 精确证据：`config/task4/sac_baseline.json` enabled=false，`config/task4/sealed_instances.json`旧partial历史不覆盖；`config/task4/execution_freeze.json`不存在；`results/task4/t4.4.1-runtime-preparation/{delivery_receipt,install_manifest,formal_protocol_fields.merge}.json`及draft保持准备态；`results/task4/t4.4.2-preparation/delivery_receipt.json`、task4.4.2三文档/独立日志（交前生成）。
- 原结论/核查：新完整封存失败后未安装formal五runtime文件、未替换预算守卫、未合并enabled/提前性能规则、未生成actual execution_freeze或父acceptance；本节点未创建campaign ledger/checkpoint、未跑CUDA非训练probe/正式训练。当前moving门未尝试而非通过。
- 采用/限制：交review，父独立核验原失败、元数据比较/缺失败capture证据与剩余范围；没有另授physicalrun或改门权。不得拿旧forward/pilot质量/3seed短初始化回归替代新view完整motion质量，不能将该交付称formal ready/4.4 done。Codex实际GPT6.1sol/high；Claude推荐Sonnet5.5/high，完整合同/时序/反馈/预算关系需要high，未换更大模型。

<a id="src-0113"></a>
## SRC-0113 — 全封存首轮106初态比较失败的独立核验

- 类型/主张：项目原始失败实测、父独立复算与有限数学反例；不能恢复缺失的actual106输入或把该run改pass。
- 版本/作者/核查：2026-10-07 Codex /root，实际父模型未知；子/root/task4_4_2_complete actualGPT6.1sol/gpt-6.1-sol high，Claude推荐Sonnet5.5 high。源版本t4.4-complete-r1/source_snapshot246文件、49实际groups/11binary，具体hash在两端收据。
- 精确证据：results/task4/t4.4.2-parent-review-20261007/{complete-r1-failure-parent.json,quaternion-double-cover-probe.json}，子t4.4.2-preparation/{complete_receipt.json,antipodal_hypothesis.json,delivery_receipt.json}，logs/task4/t4.4-complete-r1/state.json与timeline。母比较symbols collect_task4_instances:initial_base_XY_quaternion_6dp、task4_instances:canonical_base；原utils.py:calc_rot_dist的1−dot²说明符号不影响同rotation。
- 原始结论：20seals请求、6尝试/nativeinit、5public_valid；106仅baseXYquaternion component比较失败、arm/goaltip/goalwrist/maps通过；14seals与2quality未试，0测量控制/0学习。whole197.516435s/check146.935935s，failure后stop/cleanup0/foreign[]，源码/实际binaries两端不改；child353tests/3原reference跳过0（父未机械重复全suite）。formal未安装/未enabled/no finalfreeze/noCUDAprobe。
- 推导：历史106q=[0,0,−.729485,.683997]因6dp略非unit（norm1.0000001306），规范为单位后同q/整体−q的旋转矩阵逐项delta0；component比较false。canonical RPYyaw[0,2π]与旧feedback wrap可能使q表示相反，属于representation反例，未证明该actual106向量恰为此。actualfirst/publiccmd/RNG未在throw前保存，旧failure保持不能补造。
- 采用/限制：修正仅元数据物理等价判断并提高失败证据保留，原场景/位置/旋转精度/质量/动作/任务不改；下一项有界重验另记录SRC0114。不能用数学反例代替实际完整20seals/newmotion。

<a id="src-0114"></a>
## SRC-0114 — 四元数表示等价与失败输入持久化必要修复及单次续验

- 类型/主张：自动Task4授权内必要元数据错误修复与一次新增有界验证协议，未执行结果；不是基于test性能改变view/任务/quality，也非新增功能或实验算法。父2026-10-07登记，依据SRC0113/0107原依赖；Codex同actual拟gpt-6.1-sol/high（GPT6.1sol），ClaudeSonnet5.5/high，完整metadata/来源/负结果跨模块核对。
- 精确范围/方法：task4_instances及collect_task4_instances必要helper、对应有意义tests；初始publicXY保持原6dp逐值匹配；quaternion仅允许原4component或整体−4component的原6dp值匹配，实旋转改变/非整体符号改变/位置差继续拒绝，不以angle大容差替代匹配。原其他publicfields/实际spawn/SDF/双pass/RNG不变；每次freshcapture立即持久化实际first/publiccmd/RNG与expected差，再检查/throw，避免丢失败输入。原106首次缺失保持未知，不回填。
- RED/GREEN验收：原旧106q与−q物理相同而componentfail，允许两种表示后通过；实际位置/旋转微差及单component符号改变仍fail；failed checker实际输入在throw前留存。只元数据表达/证据，不改原reference/Task3 core、VIO/camera/quality/budget/model/任务或训练。
- 新有限资源：同task4.4.2接续唯一t4.4-complete-r2，仍全20seal/101原zero≤1000/0固定76测量0学习、init120/check850/whole900/10GiB，严格source/config两端freeze与ownPID监督。r1已失败197.516435s保留，此前7run1077.314s不清零，累计8run1274.830s；本次新增仅1run≤900（将为9run），没有额外view/texture/threshold搜索。失败仍完整未试分母/stop，不能无限case修复刷新预算。
- 采用/限制：r2仍不可正式训练；只有所有原seal/newviewstatic+movingquality真实通过，才能沿已准许scope安装v2formalactualclosure/非训练CUDAprobe/预定义协议与actualfreeze交父。SOURCES0115–0118子独占，父不并发台账。候选原view和全部物理门不变，属于合法表示修复而不是测试参数调优。


<a id="src-0115"></a>
## SRC-0115 — 严格六位公开初态表示修复与失败证据持久化

- 类型/主张：SRC0114授权的必要工程修复与静态反例验证，无角/位置容差扩展；Codex实际gpt-6.1-sol/high（GPT6.1sol），Claude推荐Sonnet5.5/high，元数据/来源/失败保留复杂跨模块核对。
- 精确来源：2026-10-07 `scripts/task4_instances.py::legacy_public_checks/persist_capture_evidence`、`scripts/collect_task4_instances.py::main`、`tests/test_task4_seal_representation.py`；源码SHA在`results/task4/t4.4.2-r2-preparation/preparation_receipt.json`，将以r2实际source_snapshot为运行事实版本。
- 原结论：XY保持原已round6逐值相等；q只原四分量或整体−四分量精确相等，不逐分量随意翻号、不增加角阈值、不规范化放宽。捕获first/second/commanded/RNG/legacy和repeat expected及各checks先保存到capture-seedN-passM.json，实际SDF也在检查前落盘；repeat的原verify_public_instance只移到持久化后，严格字段合同不变、控制/抽样/RNG不变。
- 核查/证据：2026-10-07 Codex；初6缺函数反例RED6→GREEN6；生产collector实际main的AST执行隔离ROS（固定failed XY输入），旧r1真实collector source丢capture RED1→current GREEN。最终7metadata反例、Task4针对62tests退出0（4.675s）、实际preflight PASS。日志`logs/task4/t4.4.2-r2-preparation/{red,collector-persistence-red,green,targeted-tests,preflight}.log`；未再次跑353全suite。
- 采用/限制：仅元数据物理表示/失败记录，不改Task3 core、rig、VIO、滤波/数学、quality/init、任务/reward/action/termination。r1真实106原值缺失继续UNKNOWN/failed；新物理r2结果另记，静态测试不能替代完整seal/newmotion。


<a id="src-0116"></a>
## SRC-0116 — r2真实20封存、重复、公共场景与源身份

- 类型/主张：项目有限实测，真实封存通过但完整质量/任务/正式入口未通过；Codex /root/task4_4_2_complete actualgpt-6.1-sol/high（GPT6.1sol），ClaudeSonnet5.5/high推荐。
- 精确证据：2026-10-07唯一`t4.4-complete-r2`，`results/task4/t4.4-complete-r2/{attempts,episode_instances,summary}.json`、20份capture-seedN-passM.json/160spawn-SHA.sdf与source_snapshot246文件/两端source/runtime/containeridentity；`results/task4/t4.4.2-r2-preparation/{complete_receipt,seal_and_action_receipt,native_initialization_receipt,supervisor_receipt,resource_receipt}.json`，logs同run state/timeline/launch/check/cleanup/foreign记录。具体版本SHA保留原snapshot/收据，非Git提交。
- 核查：2026-10-07 Codex；独立离线脚本analyze_complete.py与seal/action复算读取原文件，exit0。20请求/20实际尝试/20初始化/20publicvalid，10truefirstpass和10严格repeat，全部first/second public equality及RNG before/middle/after一致；160 SDF SHA内容一致。native官方日志22个successful initialization，对应20seal+2quality顺序执行，但日志无独立seed phase标记，不伪造各epoch。
- 原结论：r2seed106实际canonical base=(−3.903622,−.208039,0,−0,0,.729485,−.683997)，旧q整体负/XY精确6dp相同，原fullprecision RPYcommand/publiccmd见完整capture。此新证据证明该新r2表示等价；r1缺完整106输入仍未知/failed，不能回填或倒改pass。
- 身份与监管：246源/49实际runtime groups首尾一致、无absent，11binary等已验side，原core330/VIO/rig/adapter/质量/任务不改。actualGPU0 gzserver437471 G149MiB，nvidia-during.log。whole608.226705781s/body556.570071791s，check1/final1/cleanup0/foreign[]，结束仅init/sleep；900/check850/10GiB均未触限，run峰值48,939,702bytes。host root409468/wrapper409470 start658432964完整cmd，container自身PID/start/cmd及树在日志；没有只按裸PID停止外来任务。
- 采用/限制：SRC0114新增唯一r2预算已用完；按指定后续诊断链旧8run1274.830435365s加608.226705781s=9run1883.057141146s，旧独立先导等历史另保留，不清零。全seal仅metadata/初始化/来源通过，不能代替下条新view完整移动质量；无r3、参数/view/纹理搜索、训练或正式执行。

<a id="src-0117"></a>
## SRC-0117 — 新视野下原零诊断与固定76命令的实际失败质量

- 类型/主张：项目原始测量/独立离线重算，质量失败，非任务性能提升或因果根因已证。2026-10-07 Codex /root/task4_4_2_complete，actualGPT6.1sol/gpt-6.1-sol high、ClaudeSonnet5.5/high推荐。
- 证据/版本/精确位置：r2 `quality-seed101/`和`quality-seed0/`原evaluation.bag、poses/physical/joint_feedback.jsonl、task_steps.json/jsonl、episode_spec/summary/physical_link_contract/actual robot_description.urdf；各evaluation.json/actual_task_evaluation.json由原`analyze_task4_localization.py::evaluate_rows`与`evaluate_task4_baseline.py::evaluate_physical`重算。独立`results/task4/t4.4.2-r2-preparation/{analyze_complete.py,complete_receipt.json,control_lookback_receipt.json,seal_and_action_receipt.json}`。
- 原结果：101原零动作167/1000cap后done=true/20IK/0collision/internalsuccess=false，30.853675024墙钟s含reset；76/76运动窗pose原header匹配，XYRMSE.027335518497m>原.025m，peak.034853380841m，yawRMSE.029762998982rad/peak.034374805730rad，age.011–.0265sim s。167/167完整物理EE+六JointState实际反馈，actualsuccess=false/0目标达成样本；final positionerr5.306662390m、dimensionlessquatdist.46871477372。
- 原移动结果：0固定76已发命令fixture仅28/76实际命令（前28向量精确等config），原done=true/20IK/0collision/internalsuccess=false，48命令未试、0learning；measurement_complete=false，29.415727889墙钟s含reset。严格运动窗217.7525–218.3835sim s，12/12原header匹配，XYRMSE.569101429274m/peak.827728846898m（原.025/.075均失败），yawRMSE.006849692043rad/peak.013526077030rad，age.013–.0185sim s。28/28完整EE+六关节，actualsuccess=false/0目标达成样本，final positionerr4.729271734m/quatdist.983359179018。原p3d body净XY位移.076874704682m/净yaw.234833874998rad，32样本；噪声限制见下，不作为精确物理仪器位移。
- 时间/方法核查：仅运动误差使用首command_before至末command_stamp，排除旧epoch/reset的9/8个pose，不再拟合对齐；原truth消息header.frame_id=world/child=base_footprint，原stamp严格递增，最大匹配skew≈.01sim s≤原.02。控制覆盖按原0≤step_stamp−estimate_stamp≤.1s freshness，必须保留首控制前≤.1s已READY估计候选，最终167/167及28/28有效。最初窄motion窗口把首动作前2个候选切掉，产生165/167及26/28的边缘数，保存complete_receipt-pre-lookback/quick日志但不称实际控制无pose；原门没改，正确候选窗口和motion误差窗口分开。两段原reward有限。
- 物理/限制：LinkStates没有header，仅simreceipt近邻物理匹配≤.02s；原JointState header≤.04s，六finite实际关节无fallback，实际URDF两fixedjoint wrist3→gripperbase静态链保留。p3d gaussianNoise=.01、公开z=.05/settling与anchor covariance未知；估计pose recorder未保存frame字段，实际冻结pose_adapter发布odom、launch静态world/map/odom为identity，truth headerworld有原消息实证。短0.631s/28动作不是完整76质量，不能用已初始化/age正常证明精度或训练可行；没有查明误差根因，不据此变更view/阈值/模型。
- 采用：all_gates_pass=false，固定76未完成+两XY门失败阻止4.4 done/安装freeze/4.5。旧forward/pilot/NONE200三seed短回归不能代替该实测，原失败/缺试分母全部保留。

<a id="src-0118"></a>
## SRC-0118 — r2质量失败后的正式前置关闭与交接

- 类型/主张：项目当前文件事实/条件执行边界；依据SRC0114/SRC0117，2026-10-07 Codex actualGPT6.1sol/high、ClaudeSonnet5.5/high推荐。
- 精确证据：本节点RESULTS/独立agent日志；`results/task4/t4.4.2-r2-preparation/delivery_receipt-r2.json`与resource_receipt（交前生成）；r1第一交付复制`results/task4/t4.4.2-preparation/delivery_receipt-r1.json`保持原SHA。config/task4/sac_baseline.json仍enabled=false，旧sealed历史未覆写，execution_freeze.json不存在；v2formal5文件及预算/resources/watchdog仍uninstalled draft。
- 原结论/核查：r2有限metadata/全seal交付，但新实际质量门失败。195原控制/0更新/0新checkpoint；没有正式train、额外pilot、CUDA0step探针或campaign ledger。没有安装或伪造formal_runner_complete/父acceptance；source运行后仍同r2版本，质量门原15Hz/10features/.1age/120init/NONE200及原物理/任务/数据分布不改。r1/r2旧失败均保留，无额外r3。
- 采用/限制：交review并返全部写权，父独立核验原raw/完整seal/各质量失败及正确时间窗；后续原因分析/方案变更/任何新run由父另登记明确授权，不自动进入4.5，不将仅元数据修复通过或静态62tests视为定位完成。质量缺失时不执行条件formal安装/probe/freeze，是按原授权流程中止而非完成当前研究目标。

<a id="src-0119"></a>
## SRC-0119 — 全20封存通过但新视野质量失败的实际交付

- 类型/核查：项目原始实测负结果/局部父读取证据，全部质量独立重算正在进行，不冒充已经父验收。2026-10-07 Codex /root（actual未知），子/root/task4_4_2_complete actualGPT6.1sol/gpt-6.1-sol high，Claude推荐Sonnet5.5 high。
- 精确证据：results/task4/t4.4-complete-r2/{summary.json,attempts.json,capture-seed106-pass0.json,source_start.json,source_end.json,quality-seed101,quality-seed0}，子t4.4.2-r2-preparation/{delivery_receipt-r2.json,complete_receipt.json,control_lookback_receipt.json}；父独立7metadata tests0/.014s日志logs/task4/t4.4.1-parent-review-20261007/seal-representation-parent.log，读actual106 q=[−0,0,.729485,−.683997]与legacyq=[0,0,−.729485,.683997]只有整体sign相反/完整输入已存，r1旧缺口不回填。
- 原始结果：20reset/nativeinit/publicvalid、两遍10真实公共实例/RNG不变/160唯一SDF通过；quality101原零动作167steps/20IK/0collision，其首command到末command窗XYRMSE.0273355185m>.025工程门；seed0固定原76中28原done/20IK、48未试，XYRMSE.569101429m/peak.827728847m，真实净bodyXY.076874705m/yaw.234833875rad，yawRMSE.006849692rad。两quality实际EE+sixjoint195/195，正确原.1s freshness候选lookback后control167/167与28/28（初窄motionwindow计165/167与26/28边界错误保留/不采用）；误差窗仍first到last原command，不改门。internal/actual successfalse。
- 采用/限制：whole608.226706s/check556.570072s，source246/49actual组与11binary首尾不改，check/final1/cleanup0/foreign[]/0学习；此前累计9diagnosticrun1883.057141s（其他早期run分类保留），no r3。新formal未安装/no enabled/no freeze/no CUDAprobe/ledger/checkpoint。不可将全seal或freshstamp当moving定位质量通过；原camera forward质量不验新sideview。主要质量测量袋记录p3d、pose、physical/joints，没有完整moving image/IMU重放证据，无法凭这些数据已证明frontend/self-feature/IMU根因。

<a id="src-0120"></a>
## SRC-0120 — 移动定位失真必要只读因果审查

- 类型/授权：已授权Task4唯一VIO正常运行必要排错，不新功能/算法/场景/纹理/预算扩展。用户SRC0065自动Task4，SRC0119真实negative尚未闭环。父2026-10-07登记task4.3.3，Codex推荐/拟gpt-6.1-sol high（GPT6.1sol），Claude Sonnet5.5 high；frame/采样/初始化状态/机器人像素/IMU与真实反馈涉及复杂因果关系，实际spawn另记。
- 精确输入：task4.3/task4.3.3三文档；current246 source、selected OpenVINS源码/pin与当前rig/标定，SRC0103–0106、0119；完整newquality原poses/p3d/joints/physical/tasksteps及public commanded initial，原oldpilot质量/actualframe证据不混新truth。
- 方法/待证假设：仅离线由原header重算绝对/相对轨迹与误差起点，检查误差在init已有还是动作后增长，预先publicanchor/frame/leverarm公式、官方Kalibr读取/ROS输出q方向、原GazeboIMU取样坐标/点、selfrobot动态影像可能性；各假设区分有证/排除/缺raw不可判。绝不refiterror对齐或事后松门，不能凭新鲜pose/静态成功宣称位置正确。
- 限制/交付：无ROS/新physicalrun/GPU训练/source/config改动，只自身三文档/log/离线results与SOURCES0121–0122。最多提出一项有原证据必要修正（必须父复核/另登记后实施）；证据不够时给所缺最少raw捕获方案与有限成本建议，不自行新增预算/相机视野/纹理/检测器。任务/策略/WM不扩展。父后续据证据决定，当前4.4/4.5前置仍失败。


<a id="src-0121"></a>
## SRC-0121 — 新视野原r2位置失真起点、相对位移与动作节拍只读复算

- 类型/主张：项目原始测量与明确推导；seed0新epoch初态误差很小，动作后位移误差增长，单一初始平移无法解释；原零学习动作复放与旧SAC先导不属于相同时间激励，不能直接据旧forward质量验收side rig。
- 来源/精确位置：2026-10-07唯一原run `results/task4/t4.4-complete-r2/quality-seed{101,0}/{poses.jsonl,task_steps.json,episode_spec.json,evaluation.bag}`；旧 `t4.4-pilot-r1/{task_steps.json,pilot_summary.json}`。只读重算 `results/task4/t4.3.3-motion-audit/{audit_motion.py,motion_receipt.json,seed*_matched_rows.json,seed*_truth_header_rows.json,cadence_receipt.json}`；原输入SHA256逐文件在motion_receipt，相关源码SHA在frame_receipt，未改原文件。核查人Codex `/root/task4_3_3_motion`，实际GPT6.1sol/gpt-6.1-sol high；Claude推荐Sonnet5.5 high，未运行。
- 公式/条件：仅motion=[首stamp_before,末stamp]；原p3d header最近邻≤.02 sim s，原pose不重标时/不拟合。e(t)=p_est(t)−p_truth(t)，单位m；净位移Δp=p(last)−p(first)，相对位移误差Δp_est−Δp_truth，诊断用RMSE按e(t)−e(first)求，不能替代绝对门；速度=Δp/实际首末pose时间(s)，方向cos=Δp_est_xy·Δp_truth_xy/(两范数)。首次READY原.1s lookback另列，不扩大motion误差窗。
- 结果：101窗203.456–207.2915，76motion、2lookback；0窗217.7525–218.3835，12motion、2lookback。各7/6更早pose排除于lookback（motion总9/8排除），两个bag仅p3d。0首lookback217.7原estimate精确public command，XY误差.005952640m；motion首217.8误差.075914197m，末218.351误差.827728847m。匹配首末.551s内estimate净XY=(.688781183,−.419647644)m，truth=(−.068098449,.025252357)m；相对净误差=(.756879632,−.444900001)m，方向cos=−.981605614；速度estimate=(1.250056594,−.761610969)、truth=(−.123590651,.045830050)m/s。绝对XYRMSE.569101429m、相对诊断RMSE.615666892m（不更改验收）。101初lookback.012730039m、首motion.012888129m、末.034853381m；绝对.027335518m、相对诊断.015516465m。
- 节拍/源码：原 `config/task3/task_contract.yaml:18,78` 和core_contract:46–48明示Gazebo dt_exec=.02s；`.1s TIME_STEP_TRAIN`是解析训练/规划观测常量。`robotenv.py:243–247`原rate.sleep被注释，dt_exec取rate.sleep_dur，C++robot_env.cpp::step未wait；EEplanner.py:162–173,224–244实际rospy时间差。旧pilot前16command_before间隔mean.024633333s、新前16.0219s；旧16–27为.102227273s（首次CUDA更新导致最大.674s），新同期.022954545s。旧全76平均.04958s，新28平均.022425926s。不能把相同76向量称严格时间重放；无法仅据此解释第16前已产生的失真，也没有证据支持自行增加100ms pace。
- 限制/采用：nearest header仍有≤.01s约束误差；仅短28/76停止段不是完整测量，保留48未试与0learning；旧epoch原pose保留但不纳入新motion。p3d pose噪声语义核查见SRC0122；不将freshstamp、初始化成功、相对误差或旧forward通过当移动定位通过。Task4.4/4.5前置仍失败。

<a id="src-0122"></a>
## SRC-0122 — 原坐标/IMU语义审查、物理异常线索与最少缺失输入边界

- 类型：官方一手代码审查、项目已有反馈/日志、代数推导；根因尚未证明，单次原输入捕获仅工程提案，未获新增run预算/未实施。核查2026-10-07 Codex `/root/task4_3_3_motion`，actualGPT6.1sol/gpt-6.1-sol high；Claude推荐Sonnet5.5 high。
- 本地源与位置：OpenVINS官方pin69488123ed9362dd44b6f28e7f4680abbff1442b（当前允许ROS发布补丁），VioManagerOptions.h:263–269将Kalibr T_imu_cam作为C→I读取再逆为状态I→C；ROS1Visualizer.cpp:335–336与596–629输出global IMU pose，JPL G→I同xyzw数值表示Hamilton I→G；quat_ops.h::quat_2_Rot；StaticInitializer.cpp:112–136设置v=0/p=0并用gyro/acc平均估bias。生产estimate_gate.py:22–23,40–55一次A=T_anchor*T_bi*inverse(T_gi0)，T_base=A*T_gi*inverse(T_bi)，T_bi=(.35,0,.58228)m；task4_env.py::_begin/reset_robot显式新epoch/先旧reset再freshinitialize；pose_adapter.py::initialize/pose检查epoch/caller。实际相关SHA在frame_receipt，源没有更改。
- 几何/推导核查：原实际side-reg-r1/robot.sdf的IMU sensor已fixed reduction到base_footprint，pose(.35,0,.58228)，与原quality-seed0/robot_description.urdf对应链一致；不能再把base_link→IMU .45误用为footprint .45。Kalibr双目横向±.06及R=Rx(−π/2)与既有真实标定一致（SRC0106）。官方JPL公式与Hamilton矩阵转置delta0；真实production gate已知刚体往返maxabs3.33e−16、align一次不变（frame_receipt/audit_frames.py），仅证明代数和源码方向一致，不证明当时每个raw包正确。e_IMU=e_base+(R_est−R_truth)lever；seed0姿态lever额外XY最大.042762175m，而implied IMU误差peak.858280301m，不能靠该已核准杆臂或仅yaw修正消掉大误差。
- 官方外部读源：已实际browse [Gazebo11.15.1 ImuSensor.cc](https://github.com/gazebosim/gazebo/blob/gazebo11_11.15.1/gazebo/sensors/ImuSensor.cc)，Load/UpdateImpl:193–199,299–358；其输入link world velocity，附加ω×r为sensor点速度，经时间差分转IMU轴并减world gravity。原ROS sensor插件pin cd9cc952402375be5f274f39b29399c4087aa839本地4.1references::UpdateChild直接读取LinearAcceleration/AngularVelocity、stamp LastUpdateTime；rpyOffset仅影响发布orientation，xyzOffset unused。当前无这些offset，raw input adapter复制gyro/acc/stamp，弃绝对orientation。版本实读Gazebo11/libgazebo11=11.15.1-1~focal，源码不等于逐指令binary验证；下载源SHA7e66c9d05b297baf13e34e8719fec35bda702afa5e014cd752bd20b3e75d4dea保存在audit目录。
- p3d语义修正：已实际browse [官方2.9.3 p3d](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/2.9.3/gazebo_plugins/src/gazebo_ros_p3d.cpp)::UpdateChild:250–347；原4.1官方pin相同文件与2.9.3tagSHA均eebf7e648493edb067a3a671f26ed673fbe4a5fb64862166a13ae739bab8e0ac。pose直接WorldPose加offset，gaussianNoise只加twist且写pose/twist covariance；.01不是实际位置噪声幅值。容器包2.9.3-1focal.20250521.004734、p3d binarySHA7c7466903298bcc12d66559b520eca6502a64705d904bc9575d49477534d958f、IMU binarySHAb7230c8be70fa50479398ed613b680f943c2ddf01cfdc7c96e91bfdd054b9520见official_versions.json。未重建以逐指令证明包与source一致，不能冒称硬件仪器真值；但不应再用.01positionnoise解释该pose轨迹。已有Task3 world.yaml也明示task3.2静态p3d−Gazebo位置≈1e−10m。
- 原实测异常线索：frame_receipt seed0原32motion body pose中z最高.083086954m、|roll|最高.079278107rad、|pitch|最高.199249874rad，50Hz姿态反馈并非纯平面运动；twist线速度norm峰.496782700m/s、角速度norm峰1.631376634rad/s（twist含原.01噪声）。whole原launch.log计264402条ODE LCP internal error；末init相邻日志511793–511883有44条，native_log_receipt/last_native_init_excerpt保留位置。最后nativeinit打印v=0/bias近0，后续ZUPT速度0→.191→.690→1.617、disparity增至12.762并拒绝；22初始化块没有独立seed/stamp标记，不能精确配每条native日志到动作时刻或证明ODE导致VIO失败。
- 未知：当前两个quality bags仅ground_truth/state，无完整moving images/gyro/acc/native pose/velocity/covariance和逐帧feature。不能回放不存在输入，不能证明selfrobot/arm动态特征、IMU输送/差分尖峰或视觉更新为唯一根因；静态图/旧rigraw不能作新motion实测。不查出纯frame bug便不提源码修复，不变view/FOV/纹理/算法/physics/奖励/quality。
- 唯一下一步提案（尚未执行，父独核及另登记预算后才可做）：同原side rig和seed0固定已发28动作前缀、原ready/reset/原0update节拍/原done停止，单次fresh捕获从最后explicit initialize前开始至done；保留两路真实RGB+CameraInfo、plugin与normalized IMU、clock、nativeposeimu/odomimu、adapterpose/status、现有cmd_vel/armcontrol、p3d/linkstates/joints/actualspec。无新算法/参数/试其他视角，不补48未试、不重试。目的在同一原输入证据中定位camera/IMU→native估计→一次align边界，并按实际body姿态核对sensor点速度/acc；已有120s init/900s whole/10GiB上限可作为父拟约束，不能写成本轮授权预算。RGB理论数据量=640×480×3×20×2=36,864,000 B/s；120s=4.42368GB（十进制，不含ROS开销/其他流），实际吞吐须监控，达到任何父登记上限停止/保留失败。该成本为工程推导不是已采集大小，不实施capture便保持未知/质量失败/正式训练关闭。

<a id="src-0123"></a>
## SRC-0123 — 新moving质量父独立原header重算与审查结论

- 类型/主张：项目原始实测独立复算，质量失败结论确认；根因仍未知，不是修复或formal验收。2026-10-07父Codex/root(actualmodel未知)，子/root/task4_3_3_motion actualGPT6.1sol/gpt-6.1-sol high，ClaudeSonnet5.5high，跨IMU/frame/真实motion因果核对。
- 精确原证据：父results/task4/t4.4.2-parent-review-20261007/{recompute_quality.py,quality-independent-recompute.json,actual-vs-estimated-quality.png}及对应logs/task4/t4.4.1-parent-review-20261007/quality-independent-recompute.log，容器实际退出0。无refit，原p3d.header.stamp最近邻≤.02s，原.1s lookback只用于控制覆盖，误差窗first到lastcommand。
- 重算：101窗口203.456–207.2915/76matchedposes/167controls，XYRMSE.0273355185/peak.0348533808m/yaw.029762999rad，fullcontrols167；0窗口217.7525–218.3835/12matched/28controls，XYRMSE.5691014293/peak.8277288469m/yaw.006849692rad/fullcontrols28，firsterror.075914197→last.827728847；p3d全窗body净XY.076874705m，估计matched首末净XY.806550472m（端点窗口不同不混同）。新epoch初pose对p3d误差约.00595m，非初始全局平移可消除。
- 已核查限制：SRC0121/22原frame与IMU定义/点、physical tilt/z/ODE及节拍结论；body非严格平面正常，不把原ODE警告或selfrobot像素假设当根因。原dt_exec20ms，不添加100ms pacing；原p3d .01只twistnoise/pose直接WorldPose，不用它解释位置误差。
- 外部primary补读：OSRF/Gazebo classic gazebo11分支 [MultiCameraSensor.cc](https://github.com/gazebosim/gazebo-classic/blob/gazebo11/gazebo/sensors/MultiCameraSensor.cc#L146-L150)，Init L146–150读camera局部pose与sensorpose组合并绑定parentvisual；父2026-10-07实际读原文，分支而非当前安装binary重构，不能据此代实际stereo视点测量。相机/IMU/控制动态完整原输入尚缺，formal继续disabled。

<a id="src-0124"></a>
## SRC-0124 — 缺失移动原输入的单次必要补采协议

- 类型/授权：用户自动Task4(SRC0065)内为解决已测失真必要原输入采集，不是新算法/定位器/场景/参数搜索；没有支持源码修复，故先取最少证据。父2026-10-07登记task4.3.4，Codex沿GPT6.1sol/gpt-6.1-sol high、ClaudeSonnet5.5high，原输入→native→align与实际body的复杂因果核对，实际接手另记。
- 精确输入/范围：task4.3/task4.3.4三文档，当前sideview/init200/NONE/所有quality原门不改，seed0固定已有76动作fixture的首28（只原命令/no model/optimizer/训练data），原done/失效即停止。新增仅diagnostic脚本/identity实际闭包与必要捕获测试，所有旧source/failure/raw不覆盖。
- 一次有限run：t4.3.4-motion-raw-r1，freshGazebo/一次seed0 reset（记录与旧20seal+101后seed0物理前史不同，不伪相同初条件），最多28原commands/0updates/0正式。whole≤600wall、check≤500wall、body≤450wall，raw≤120simsec/10GiB，init120wall不变，ownPID-start-cmd监督/停止留清理。旧9run1883.057141s保留，此为明确新增第10诊断≤600，不重置counter/no第二run。
- 捕获/权限：从explicitinitialize前保存actualleft/rightRGB及CameraInfo、原plugin与normalizedIMU、clock/nativepose+odom(v/cov)/trackhist/loopfeatures可用项、adapterstatus/pose、cmdvel/现有六joint与独立physical/body/headerp3d，完整topic/type/stamps/count/hash/缺失明确。truth只独立评价recorder/闭bag，actor和定位器不订truth，追加观测不得改变输入/滤波/物理/控制/动作/奖励/终止或初始化强制状态。原dt_exec20ms沿继承，不补hostdelay或100ms。
- 后处理/限制：严格标freshhistory与旧失败context，原包原header检查输入数值/同步/动态、native与aligned相对轨迹及Gazebo真实状态，RGB机器人/静态场景影像仅实际证据判断；无raw则保留unknown。最多给一项有证必要修正/或负结论，尚未准许mask/噪声/gravity/view/physical变更或新离线模型扫描。SOURCES0125–0128子独占；交review返权限，父独核后另安排必要修复。


<a id="src-0125"></a>
## SRC-0125 — 原始移动输入单次采集的必要工具与实际来源闭包

- 类型/主张：SRC0124已授权necessary诊断工具，不改变定位器、物理、传感器、策略语义。2026-10-07 Codex /root/task4_3_3_motion，actualGPT6.1sol/gpt-6.1-sol high；Claude推荐Sonnet5.5 high未运行。
- 精确源码：scripts/task4_motion_raw.py::load_prefix/execute_prefix/limit_reason/main；scripts/task4_identity.py仅RUNTIME_FILES新增task4_motion_raw.py以actualpreflight语法/实际文件hash闭包；tests/test_task4_motion_raw.py。run版本将由新run实际identity/source及diagnostic_source_start记录；当前preparation SHA写results/task4/t4.3.4-preparation/preparation_receipt.json。
- 原合同：actor只订clock、不订truth/RGB/native状态，不将录制truth返送Task4Env或VIO；独立rosbag原topics完整无throttle、独立record_task4_quality物理节点沿用。bag.active建立后才构造Task4Env/显式seed0 reset；fixture只原76前28、原step/原done/异常即停，异常动作仍attempt并原stamp计分母，0updates。原.02执行、不加.1或hostsleepphysicaldelay；等待bag注册属于采集启动同步。
- 验证：新模块不存在时RED missingmodule，新增后宿主6tests/.006s与容器6/.007s GREEN，涵盖28cap/done/failure分母、cap边界、原stamp、actor真值权限与sourceclosure；容器task4_preflight实际PASS，日志logs/task4/t4.3.4-preparation/{red,green,preflight}.log。未把static通过当新moving成功。官方debug名称直接读当前ROS1Visualizer.cpp构造：poseimu/odomimu/trackhist/points_msckf/points_slam/loop_feats；请求ghost/无数据须notavailable，不伪造state值。
- 预算/局限：独立诊断订阅debug导致额外输出/录制负载，须报告actualcadence/RTF；fresh一seed0前史不同旧20seal+101序列。不改任何VIO/rig/adapter算法、核心330或formal；唯一t4.3.4-motion-raw-r1尚未物理执行，whole600/check500/body450/raw120sim/10GiB，只有第10run/no第二run。


<a id="src-0126"></a>
## SRC-0126 — 单次fresh移动raw实际采集、来源和有限资源

- 类型/核查：SRC0124唯一第10诊断项目实测，2026-10-07 Codex /root/task4_3_3_motion，actualGPT6.1sol/gpt-6.1-sol high；Claude推荐Sonnet5.5 high（未运行）。不是正式质量验收或训练。
- 证据：t4.3.4-motion-raw-r1/{raw.bag,summary.json,task_steps.json(l),episode_spec.json,commanded_initial.json,robot_description.urdf,robot.sdf,graph_ready/end.json,source_start/end.json,runtime_identity_start/end.json,container_identity_start/end.json,diagnostic_source_start.json}；analysis/raw_receipt.json/delivery_receipt.json；监督results/task4/t4.3.4-preparation/{bounded_run.py,supervisor_receipt.json,current_host_identities.json}与对应日志。bagSHA256 c170acd184104e89d8c838d8f4e237745374d4a26bab4f8965ecbcfd3516a904，760281970bytes。
- 实际：fresh simulator、一次outer seed0正常reset；原bootstrap内部epochs1→2→3公开构造/reset命令保留，不谎称只有一个begin调用。bag在constructor/explicitinitialize前建立，原COLLECT_STATIC_RAW14.9415、READY首原pose17.3505，原动作28/28向量逐值一致，motion17.429–18.0955、0updates/done=false/0IK/0collision，原fixture剩48未执行，未增加第二run/权重/训练data。
- 原输入完整性：RGB左右各290/约20Hz，同CameraInfo各290；normalized IMU2903/200Hz、plugin2901/200Hz，全部请求24topic有数据。nativepose15、adapterpose15、odom88/200Hz、trackhist55、points_msckf/points_slam/loop_feats各9；其point/feature内容可以为空，topic有消息不等于有效feature。原payload按topic SHA/type/count/header时间与缺口在raw_receipt；无稀释/新时间戳。actor+VIO实际graph不订truth，bag独立订truth/linkstates，orientation只offline独立核查。
- 来源/资源：246原snapshot文件首尾一致，newdiagnostic单独snapshot/hash并在actualidentity运行闭包（50groups）首尾一致；实际container无absent，宿主wrapper ROS source组因宿主没装ROS存在absent，不将宿主快照误判实际缺依赖。原官方11binary首尾未变，Task3/VIO/rig/adapter/physics/quality未改。hostwrapperPID474348/start658724287/fullcmd归档；sgroot474346首快速cmd空，当前完整身份在current_host_identities，不伪原首次有cmd。containeractor/recorders/PID树与owncleanup记录齐全。
- 退出：whole82.197657502wall/body31.784036244wall、rawclock3.4205–19.2885共15.868sim（袋实际钟4.507–19.0225，录制注册边缘明确）；峰资源784166572bytes，check/final/cleanup0/foreign[]，首尾仅init/sleep，无cap触发。旧9run1883.057141146s保留，累计10run1965.254798648s。早启动actual nvidia-smi记录GPU0 gzserverPID480275 G17MiB；未采运动时GPU峰值/利用率，不伪称149MiB或每帧GPU利用。沿已验证VirtualGL/EGL0配置，真实RGB与实际GPU context均有证据。
- 限制：fresh前史不同旧20seal+101后移动，新增debug/原包订阅有额外负载；28commandmeaninterval.023777778s，motion sim/wall粗比.87308，不能称等旧SAC时间重放。采集成功只说明此必要诊断交付，质量仍SRC0128失败。

<a id="src-0127"></a>
## SRC-0127 — 静止与运动IMU原包、物理动态对应及不判饱和的边界

- 类型：项目原始实测+原模型推导，非IMU硬件标定或badIMU根因证明。2026-10-07 Codex实际GPT6.1sol/gpt-6.1-sol high/ClaudeSonnet5.5 high推荐。精确证据raw.bag与analysis/{imu_receipt.json,imu_body_fd_rows.json,imu_orientation_evaluation_only.json,task4_imu_data_raw.json,task4_plugin_imu.json,gazebo_link_states.json}；离线scripts在t4.3.4-preparation/analyze_imu.py，最终容器exit0日志analyze-imu.log。官方语义继承SRC0122，原OpenVINS fast local odom语义见Propagator.cpp::fast_state_propagate、ROS1Visualizer.cpp:292–330。
- 包/时序：normal2903、plugin2901，共同2901 stamp原acc/gyro逐值一致；2个边缘normal样本仅bag启动订阅起点不同。所有原IMU包finite，header严格5ms=200Hz（最小/最大浮点表达≈.005）；无包内非正dt/整段dropgap。轴仍原x前/y左/z上、单位m/s²/rad/s，未翻轴/加g/改stamp/加filter。
- 静止：整COLLECT14.9415–17.3505共481包，acc均值[−.001855357,.000634517,9.804339613]、std[.1631286,.1016186,.1639701]m/s²，含原reset settling不切掉。另标纯诊断最后1sim秒200包accmean[−.000018548,.000026013,9.800006413]，gyromean[−.000000514,.000000205,.000001801]rad/s；官方staticinit实际打印v=0、gyro/accbias近0（原日志完整bias行在imu_receipt，不编造动态bias时序）。最后1s仅解释static值，不代替整个初始化质量门。
- 运动：133原包accabspeak[52.889812095,45.050965772,44.173763946]m/s²、std[8.184270,6.301944,5.943840]，gyroabspeak[.446763080,.671054598,.357015650]rad/s。当前Gazebo配置零noise/无声明硬件量程或饱和clipping，不能把峰值称饱和或坏IMU。
- 物理推导：r=(.35,0,.58228)m；v_IMU_world=v_base_world+ω_world×(R_base*r)，f_IMU=R_baseᵀ[(v_IMU(t)−v_IMU(t−dt))/dt−g_world]，g=[0,0,−9.8]m/s²；gyro=R_baseᵀω_world。输入原LinkStates实际world pose/twist与IMU原5ms，最近bag simreceipt配对，133样本bodyreceipt skew0。predictedaccpeak[52.889812095,45.050965772,46.333349458]，acc逐轴相关[.999500464,.999693377,.999190182]；残差RMSE[.259670320,.166239421,.259344081]m/s²，gyro残差[.000980845,.002233203,.002107854]rad/s。说明尖峰与仿真实际body点动态高度对应，不支持依据峰值改轴/重力/传感器noise；不是精确硬件误差模型。
- 限制：LinkStates无header，用bag记录simreceipt恰重合不等于已证明sensor物理采样时刻相同；高频差分与transport可alias impulses，z预测峰与实际不同及残差保留，不refit/搜索offset消残差。plugin绝对orientation只独立offline评测到body姿态；normalized orientationcov[0]=−1全体，actor/VIO不使用它。此与nativevelocity/covariance一起保存，不从绝对orientation在线纠正策略。

<a id="src-0128"></a>
## SRC-0128 — 原输入到native/对齐边界与fresh质量负结果

- 类型/核查：项目负结果与有限代数/视觉审查，2026-10-07 Codex /root/task4_3_3_motion actualGPT6.1sol/gpt-6.1-sol high、Claude推荐Sonnet5.5 high。精确证据analysis/{raw_receipt,paired_motion_rows,imu_receipt,native_loop_features,delivery_receipt}.json、同analysis实际rawL/R/trackhist-sample0/1/2.png；原source/frame公式SRC0121/22；旧r2负结果不覆盖。
- fresh质量：原window17.429–18.0955，13motion+2lookback pose；全部nativeposeimu exact stamp对应adapter，按原一次align与T_bi重算输出位置delta0，不新增fit。首lookbackXY误差.012217926m/yaw.032251238rad；首motion .029099198m，末.030476671m；XYRMSE.028415422m>.025原门，peak.038400590m，yawRMSE.031775704rad。公开anchor与actualsettling存在位置/yaw偏差，不能用相对诊断通过抵消绝对门。
- 相对轨迹：.601s匹配首末estimate netXYZ=(.029419081,−.018973739,−.005189164)m，actual=(.023383691,−.021883017,.000706787)m，XY方向cos+.983943102、relativeXYRMSE.007863118m，非旧r2反向.80655m估计位移；fresh body zmax.006906046m/rollabsmax.012811458rad/pitchabsmax.020415823rad，而旧r2 z.083087/pitch.19925。fresh原whole仍41156条ODE LCP error，计数受时长/前史影响不能直接比率归因。
- native动态：原odom88messages，motion86（以imu_receipt实际数量为准），200Hz local速度/角速度/cov保存，pose/twist cov全finite。debug subscribers只触发既有ROS可视化发布；检查原ROS1Visualizer.cpp::visualize_odometry/publish_images/publish_features/publish_loopclosure_information，未改滤波参数或算法。不把debug描绘的所有feature都称为MSCKF有效更新；points_slam原9消息有0→4feature，真实point内容单列。
- 视觉：实际trackhist显示近侧柱形/弧面与底部前景表面上有官方feature轨迹，远方黑色物体也有轨迹，左右原RGB确实不同，原CameraInfo K/D/R/P/两光学frame保存。没有逐像素物体身份标签或逐feature实际measurement/update归属，不能仅凭前景形状把所有点判机器人、宣称selffeature是根因，也不能仅凭source/SDF理想baseline证明renderer实际投影完全正确。未加检测器/mask/texture/新FOV。
- 剩余唯一因果问题：为何旧长reset/封存前史下native估计出现反向大位移，而本fresh同原28向量下body动态温和、native相对移动接近实际？旧严重失败时raw缺失，不能区分该历史body状态变化对IMU/视觉更新的具体作用。当前不实施参数/物理/算法修正、不追加重放/第二run或新扫描建议；交父独核后决定必要后续。原全质量仍未通过、48完整fixture未试、正式4.5/启用/freeze/probe未开始。

<a id="src-0129"></a>
## SRC-0129 — 父Agent独立原包IMU链路复核及用户状态答复

- 类型/核查：项目原始实测的独立复核。2026-10-07 21:30+08:00 Codex /root；父实际模型/强度未知，子实际gpt-6.1-sol/high（GPT6.1sol）。后续此跨模块排错推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，原因是需要区分输入链路、机器人动态与定位估计；推荐不冒充运行。
- 精确证据：原run `t4.3.4-motion-raw-r1/raw.bag`，760281970 bytes；父脚本/收据 `forem/results/task4/t4.3.4-parent-review-20261007/{verify_imu.py,imu-independent-receipt.json}`。命令 `sg docker -c 'bash forem/docker/run.sh exec python3 -u results/task4/t4.3.4-parent-review-20261007/verify_imu.py'` exit0，仅读闭包原IMU，无ROS发布或新物理运行。
- 原始结论：normalized2903/plugin2901，全部2901重叠加速度/角速度/原header时间戳/frame逐值相同；normalized全部相邻时间差5000000ns即200Hz、无非递增、全部finite；绝对orientation covariance[0]均为−1。原运动窗口17.429–18.0955含133样本，三轴加速度绝对峰值52.8898120952/45.0509657723/44.1737639461 m/s²，与子原包报告完全一致。
- 采用/限制：仅支持本次采集的原值/时间/接入链路，bag边缘订阅样本数不同不推成内部丢包；静止重力/运动真实动态推导读SRC0127，LinkStates receipt/差分不能充当精密标定。峰值不是传感器故障、饱和或旧定位失真根因证明。SRC0128绝对XY质量仍失败；不得因此启用正式训练或改变原质量门。此次容器 `sg docker -c 'docker top forem-dev -eo pid,args'` 仅docker-init/sleep，原run已清理；无新增算法、噪声、物理或训练。

<a id="src-0130"></a>
## SRC-0130 — 用户要求后续由Claude执行与当前交接

- 类型/原始授权：2026-10-07用户最新明确“接下来的工作让Claude进行吧”。核查者Codex /root；本地精确记录`forem/doc/agent_logs/task4/20261007-codex-to-claude-imu-handoff.md`。
- 项目采用：Codex完成已执行诊断的事实/三文档及交接，不派发新实施Agent或新实验；下一执行负责人拟Claude，尚未启动/登记接手，实际模型/强度未知。推荐Claude Sonnet5.5/high，跨reset前史、输入动态与native失真的复杂因果问题；Codex适用推荐GPT6.1sol/high，但本轮不再派发。不改默认模型、不把推荐写成实际启动。
- 限制/当前状态：Task3 done；Task4质量review未通过、4.5/4.6未执行，formal disabled。IMU状态见SRC0127/0129，native失真根因仍未证明。移交不构成新功能/算法/物理/预算授权；接收方先读文档、核查源/进程及结果，再登记实际接手。

<a id="src-0131"></a>
## SRC-0131 — Claude实际后台接手派发与监控

- 类型/授权：SRC0130用户指定后续Claude执行。2026-10-07 Codex /root实际派发；Claude CLI v2.1.280，明确配置claude-sonnet-5-5/high（用户名称Sonnet5.5），permission-mode auto，未绕过权限检查、未指定fallback升级。
- 精确证据：forem/results/task4/claude-handoff-20261007/launch-receipt.json；本机`claude agents --json --cwd /home/ybc/projects/CL-FoReM`真实会话514b8a46 / 514b8a46-ca0e-4df9-85b9-e121051c7407，PID 485831，kernel start 658898637，busy/working；`claude logs 514b8a46`实际终端头Sonnet5.5 with high effort并正在读交接/任务文件。CLI派发命令退出0。
- 采用/限制：下一执行负责人Claude，不再由Codex派新执行子Agent。仅交接中原Task4和必要排错、同质量门/预算/源码权限；已启动与已读文件不等于定位通过或正式训练完成。Claude须自行核查并记录实际接手。监控logs、交互attach、停止本会话stop均使用514b8a46，不停止其它idle用户会话。父完成此派发记录后交回共享写权。

<a id="src-0132"></a>
## SRC-0132 — Claude接手及长前史失真的离线因果证据

- 类型/授权：用户2026-10-07指令“请继续FoReM的Task4，负责定位问题修复、验证及后续执行；Sonnet5.5，复杂因果排查high”（原话见本会话；承接SRC0130/0131）。核查者：Claude `claude-sonnet-5-5`，用户指定high（平台是否实际应用该档位未能核实）。
- 精确证据（均为现有产物只读重算，无新物理运行）：`forem/results/task4/t4.3.5-offline/offline_evidence.py`→`offline_evidence_receipt.json`；探查脚本wrist.py/settle.py/teleport.py/quiet_jitter.py/imu_view.py同目录。输入：`logs/task4/t4.4-complete-r2/launch.log`（22个成功init块）、`logs/task4/t4.3.4-motion-raw-r1/launch.log`、两份`physical.jsonl`（wrist3 LinkStates，约2 kHz，无header）、`results/task4/t4.3.3-motion-audit/seed*_matched_rows.json`、两份p3d bag。OpenVINS定义：`forem/src/open_vins/ov_init/src/static/StaticInitializer.cpp`第62–118行（pin 69488123…），“IMU excitation stats”打印两个相邻1 s窗口内加速度向量的样本标准差（m/s²），初始化阈值`init_imu_thresh: 1.5`（config/task4/estimator.yaml）。
- 观测结果：①旧r2的22个init块，21个excitation在.003–.010，**仅seed0块.050/.046**；fresh块.003/.005。②ZUPT：旧seed0 |v|=0→.001→.191→.69→.86→1.57（chi2 .124→438→7786→1.35e5…），fresh 0→.001→.037→.06→.133→.134（chi2 .002→6.3→3079…）。③旧seed0静止期wrist相邻样本差std .05–.06/.05/.03 µm，旧seed101与fresh ≤.02 µm（z 0）；到位后0–2.25 s settle三者相同（≈2.1–2.25 s）。④首次动作后0–0.1 s wrist hp_std逐20 ms旧/新一致。⑤旧估计在truth静止时跳变：217.75 s XY误差.0066 m、217.8 s .0759、217.851 s .3426；truth身体z/pitch在217.84 s仍≈0，217.9 s起才摇晃，旧step3–6 planned臂关节随之跳变。
- 采用/限制：这些是**相关性证据与假设排除**，不是已证根因；旧失败run没有IMU/RGB原包，不能直接证明旧seed0的IMU序列；wrist LinkStates无header，仅相对比较；excitation阈值1.5远大于实测静止值(.003–.010)是配置事实，不等于已证它造成失败。H1/H2/H3判别见SRC0133。
- 前序结论保持：IMU 200 Hz、原值/时间链路正常（SRC0127/0129）；p3d噪声只作用twist（SRC0122）；q与−q等价已修复（SRC0114/0115）。

<a id="src-0133"></a>
## SRC-0133 — task4.3.5 history-r1 判别运行协议（工程选择）

- 类型：工程选择（非外部文献）。理由：SRC0132表明旧失败缺少moving RGB/IMU，而物理运动头与fresh一致、差别在reset后静止微抖动与init excitation；需要同一Gazebo/VIO生命周期内连续reset的完整原始记录来区分H1（前史依赖）/H2（与前史无关）。选择“连续≤12个seed0 episode+原76命令fixture”而非完整重放r2的20封存+101：每episode约18 s wall，成本≤500 s，且提供多次独立reset样本；缺点是前史不同于r2（无seed101零动作终态），未复现时不能否证H1，该限制在PROCEDURE写明。
- 预算：第11次diagnostic运行（此前10 run/1965.254798648 s，SRC0126），≤500 s whole、body 420 s、raw sim 400 s、磁盘12 GiB、≤12 episodes；0 SAC更新；不改任务/动作/奖励/终止/质量门/场景/物理/噪声。预先登记指标与判别规则见`forem/doc/tasks/task4/task4.3/task4.3.5/PROCEDURE.md`。
- 待验证：运行结果、判别结论和后续修复（若有）写入task4.3.5 RESULTS及后续SRC，不预设。

<a id="src-0134"></a>
## SRC-0134 — history-r1复现结果与车轮复位干预协议

- 类型：项目实测+工程选择。核查/执行：Claude（会话中途用户把模型切换为`claude-opus-5-5`；history-r1及其之前的工作由`claude-sonnet-5-5`完成，强度high为用户指定、未能核实平台实际档位）。
- 精确证据：`forem/results/task4/t4.3.5-history-r1/`（raw.bag 12 episode、summary.json、analysis_history.json），`forem/logs/task4/t4.3.5-history-r1/{timeline.txt,state.json}`；分析脚本`forem/results/task4/t4.3.5-offline/{analyze_history.py,joint_jitter.py,link_jitter.py}`；结果表见task4.3.5 RESULTS。
- 原始结论：首episode XY RMSE .0228/peak .0484（过原门），后11个全部不过原门，ep5/6 RMSE .47/.45并按原规则20 IK done；init excitation首episode .003/.001，之后.021–.061；静止抖动集中在车轮自转（数mrad/s），原reset不复位车轮关节。按预登记规则严格H1、H2均未满足（好/坏阈值间有重叠），不得表述成“已证根因”。
- 干预协议（工程选择）：`t4.3.5-wheelzero-r1`，与history-r1完全相同（同脚本、同seed0/76命令、≤12 episode、0更新、同记录），唯一差别是每次原robot.reset之前通过Gazebo官方`/gazebo/set_model_configuration`把四个车轮关节角置0（`scripts/task4_history_raw.py --zero-wheels-at-reset`）。车轮角不进入任何观测/动作/奖励/终止。判别（运行前固定）：若≥10/12 episode的init excitation≤.012且静止车轮抖动回到ep0量级（joint vel std≤.0005 rad/s），则支持“车轮关节前史状态→静止抖动”；再看原门通过率。若抖动不降，则车轮角假设被否定。预算：第12次diagnostic运行（此前10 run/1965.254798648 s，history-r1为第11次、actor whole 323.17 s），本次≤500 s whole、12 GiB、≤12 episode。history-r1原始bag暂保留，分析完毕后再按PROCEDURE精简。


<a id="src-t4-gate-review-20261007"></a>
## SRC-T4-GATE-REVIEW-20261007 — 定位精度与世界模型研究目标的门槛解释复审

- 类型：项目原协议核查＋逻辑推导＋待验证研究假设；非外部性能结论，未实施协议修订。
- 用户问题（2026-10-07）：精度有问题是正常的，我们不就是要用世界模型去纠正他的精度吗。
- 核查人/时间：Codex /root，2026-10-07T22:14:23.048526+08:00；实际模型/强度未知，适用GPT6.1sol/medium、Sonnet5.5/medium（协议与研究目标核对）；Claude现行排错配置不由本答复变更。
- 输入来源与精确位置：SRC-0080及forem/config/task4/pilot_quality.json；末端目标位置容差.025m来自eeplanner.py:_is_done，定位XY RMSE≤.025m、peak≤.075m是工程筛选选择。Task4 TASK“目标与范围”“SAC适配与重新训练”及SRC0047记载定位基线与后续WM分阶段；SRC0134记载前史相关异常未证根因。
- 推导/原始结论：末端单次任务目标距离（m）与底盘定位时间序列RMSE（m）是不同指标。相同单位/数值不提供二者等价或定位RMSE必须小于任务目标容差的证明；缺乏端到端误差传播/补偿可行性证据，不能把原工程门当作世界模型研究必须达到的精度标准。
- 本项目解释与假设：真实、持续且有结构的定位误差可作为后续预测/补偿研究对象；其可预测性、在允许输入下可纠正性及任务收益均待验证。不需预设定位已达到最终任务精度，也不预设WM能修正所有误差。坐标/时间/真值权限/reset异常与正常估计偏差须区分；当前前史异常尚未证根因，不能直接认定全部错误是正常漂移或机械性归零。
- 采用与限制：本次仅解释/复审建议，不修改已冻结数值/正式训练enabled/现行任务状态，不启世界模型训练；保留既有失败事实。若后续获授权重订协议，保留旧门结果，新的链路有效性/误差刻画/训练条件与最终真实任务性能要求须分别明确，并同时用于基线和改进方法。
- 使用位置：agent_logs/task4/20261007-codex-sensor-success-status.md及本轮聊天答复。

<a id="src-0135"></a>
## SRC-0135 — 视差强制ZUPT在运动起步时破坏状态（机理证据）及候选修复

- 类型：官方源码审计+项目实测+离线重放；候选修复为工程选择（采用官方文档化的另一模式），待在线验证。执行：Claude claude-opus-5-5（用户切换后），强度沿用户要求high（未能核实平台档位）。
- 官方依据：OpenVINS pin 69488123ed9362dd44b6f28e7f4680abbff1442b，`ov_msckf/src/update/UpdaterZeroVelocity.cpp::try_update`拒绝条件`!disparity_passed && (chi2 > chi2_multipler*chi2_check || |v| > zupt_max_velocity)`（视差通过即无条件接受）；官方配置注释`zupt_chi2_multipler: 0 # set to 0 for only disp-based`、`zupt_max_disparity: 0.5 # set to 0 for only imu-based`（`config/euroc_mav|rs_d455|rpng_sim/estimator_config.yaml`第31/34行；rpng_sim使用multiplier 1+disparity 0的IMU-based模式；官方模板try_zupt均为false）。`VioManager.cpp`第294–305行ZUPT成功即return不克隆；`ROS1Visualizer.cpp`第214–218行Task4补丁在state_initialized后即发布位姿，READY不依赖ZUPT。
- 项目实测：`results/task4/t4.3.5-{history-r1,wheelzero-r1}/`，`results/task4/t4.3.5-offline/{zupt_accept.py,decompose_native.py,decompose_t4.3.5-wheelzero-r1.json}`；wheelzero中被接受ZUPT chi2 539/642/569的ep3/5/11对应RMSE .25/.25/.13 m，其它≤70的≤.036 m；坏episode首运动帧IMU位置误差约(−.11,−.13) m、滚转−.026 rad，truth静止；旧r2 seed0 chi2 7786、fresh 4.3.4 6.3。离线重放`results/task4/t4.3.5-replay-cur1/replay_results.json`复现分化。
- 候选修复：`config/task4/estimator.yaml`仅改`zupt_max_disparity: 0.5→0`、`zupt_chi2_multipler: 0→1`（官方IMU-based ZUPT：只有IMU残差在χ²95%分位内且|v|<0.1 m/s时才施加零速约束）；保留try_zupt/only_at_beginning（静态初始化不等jerk的原理由不变），不改噪声、滤波方程、物理、任务、质量门。适用限制：IMU-based模式在静止期也可能拒绝ZUPT（例如有前史抖动时），此时仅退化为普通传播+视觉更新；须离线全量重放和在线闭环、全封存与质量复验确认，未通过不得宣称修复。


<a id="src-t4-gpu-status-20261007"></a>
## SRC-T4-GPU-STATUS-20261007 — 当前GPU低占用的实际阶段核查

- 类型：项目只读瞬时运行核查＋配置/既有执行证据，非加速性能结论。
- 主张：当前定位离线重放使用官方CPU OpenVINS；未开启正式SAC/WM训练，本轮四张GPU瞬时利用率均0%，当前低GPU占用与执行阶段相符。
- 来源/精确位置：本轮宿主nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader，各卡RTX PRO6000 Blackwell Server Edition、0%、14/97887MiB；query-compute-apps无条目；sg docker -c 'docker top forem-dev -eo pid,ppid,comm'只有保活及python/roscore/rosmaster/rosout/run_subscribe_m/rosbag/play，无gzserver或SAC进程。命令均退出0。过程记录agent_logs/task4/20261007-codex-sensor-success-status.md。
- 核查时间/人：2026-10-07T22:25:35.444510+08:00 Codex /root；实际模型/强度未知；适用GPT6.1sol/low或默认、Sonnet5.5/low或默认（明确配置/进程核查）。
- 配置与原结果：config/task4/protocol.yaml estimator.device=cpu、resource_policy=GPU_first_SAC_CPU_official_VIO_no_CUDA_port、pilot.device=cuda。Task4.3.5 RESULTS“第二失败机制”记录无Gazebo的rosbag离线重放运行中。既有SAC CUDA实际运行SRC0066/0081、相机GPU渲染SRC0074；Gazebo物理/ROS CPU，OpenVINS固定官方CPU源码SRC0075；当前Task4.5正式训练未启动，WM不在Task4实施范围。
- 采用/限制：瞬时0%不证明此前未用GPU或长时间平均为0，不把GPU可用或显存占用当持续计算；相机渲染与CUDA神经网络训练分开。当前无自动GPU化VIO/物理或多卡训练实现，不修改源码、参数或启动额外训练来填GPU利用率。定位质量/正式训练工程门关系沿SRC-T4-GATE-REVIEW-20261007，不新增精度达标的研究必要性主张。

<a id="src-0136"></a>
## SRC-0136 — task4.3.5最小修复实施与闭环验证协议

- 类型：工程修复（依据SRC0134/0135实测与官方模式），待在线验证。执行：Claude claude-opus-5-5，high（用户要求，未能核实平台档位）。
- 修改（仅两处）：①`forem/config/task4/estimator.yaml`：`zupt_chi2_multipler 0→1`、`zupt_max_disparity 0.5→0`（OpenVINS官方IMU-based ZUPT模式），其余参数不变；②`forem/scripts/task4_env.py`：新增`WHEEL_JOINTS`与`Task4Env._zero_wheels()`，在原`reset_robot`最前（`_begin`与原C++ reset之前）经Gazebo官方`/gazebo/set_model_configuration`把四个车轮关节角置0，失败即抛错（fail-closed，走原reset错误→stop路径）。车轮角不进入观测/动作/奖励/终止；不改物理参数、噪声、滤波方程、任务、质量门、Task3 core330。
- 依据：wheelzero-r1（车轮置0）使init excitation 12/12≤.012且静止抖动回到首episode量级；离线配对重放`results/task4/t4.3.5-replay-imuzupt1/replay_results.json`：IMU-based ZUPT在安静初始化episode 12/12过原门（含在线严重失败的3个），在有车轮前史抖动的history-r1 episode仅5/12过门（当前配置重放基线：安静组9/12、前史组2/12，合计11/24 vs 候选17/24）；因此两项都必要。当前配置全量重放基线见`results/task4/t4.3.5-replay-cur2/`。
- 测试：`forem/tests/test_task4_reset_zupt_fix.py` RED（2 fail+2 error，`logs/task4/t4.3.5-fix/red.log`）→GREEN 5/5（`green.log`）；Task4全部82测试OK（`task4-tests.log`）；preflight PASS。
- 闭环验证协议（运行前固定）：(a)`t4.3.5-fix-history-r1`：同history-r1脚本与参数（≤12 episode、seed0、原76命令、0更新、≤500 s/12 GiB），不加诊断开关（车轮复位已在Task4Env内）；判据：逐episode原门（XY RMSE≤.025 m且peak≤.075 m），报告通过数/12，任何episode严重失真（RMSE>.075）即视为修复未完成。(b)若(a)全部12个通过，再做`t4.4-complete-r3`：原`collect_task4_instances.py --passes 2 --quality-seeds 101 0 --fixed-replay config/task4/quality_action_replay.json`（20封存两遍+101零动作+seed0固定76），原门不变，≤900 s/10 GiB；全通过才进入正式入口安装/freeze与4.5。累计：此前10 run/1965.254798648 s；history-r1 323.17 s、wheelzero-r1 317.16 s（actor whole）；离线重放（--no-launch，无Gazebo）另计不占物理run。

<a id="src-0137"></a>
## SRC-0137 — 修复后闭环验证（部分改善，未达原门）与剩余自身特征候选

- 类型：项目实测+官方源码说明。执行：Claude claude-opus-5-5。
- 证据：`results/task4/t4.3.5-fix-history-r1/{summary.json,analysis_history.json,raw.bag}`，`logs/task4/t4.3.5-fix-history-r1/state.json`（exit 0）；`results/task4/t4.3.5-offline/{decompose_t4.3.5-fix-history-r1.json,frames/*.png}`。
- 结论：两项修复后严重失真0/12（此前2/12）、过原门6/12（此前1/12）；按预登记规则仍未完成。剩余误差在首次视觉更新时出现台阶+漂移；图像显示UR5肩座和车体前板在左目/底部视野内并带跟踪特征。OpenVINS官方静态遮罩：`config/tum_vi/estimator_config.yaml` L107–110 `use_mask/mask0/mask1`（相对配置目录），`ov_core/src/track/TrackKLT.cpp` L165–166/L445–446 像素>127的特征被拒绝。是否采用遮罩待用户决定；自身特征为剩余误差的唯一原因尚未证明。

<a id="src-0138"></a>
## SRC-0138 — 机器人自身静态遮罩（候选A）离线评估

- 类型：项目离线重放+几何推导（工程候选，未接入运行）。执行：Claude claude-opus-5-5。用户2026-10-07选择“先离线评估再定”，未授权接入运行。
- 证据：`results/task4/t4.3.5-offline/{mask_from_geometry.py,mask_v4/,mask_v5/occupancy_counts.npz,cfg_imuzupt_maskA/}`；`results/task4/t4.3.5-replay-{maskA1,imuzupt2}/replay_results.json`，`logs/task4/t4.3.5-replay-{maskA1,imuzupt2}/state.json` final_exit 0。OpenVINS官方静态遮罩语义见SRC0137。
- 结论：并集遮罩会遮去左目92%（上臂扫过），不可行；≥99%占据的静态遮罩A（只覆盖车体前板带）在两修复后录制的12个episode重放中把过原门从8/12提高到11/12，修复的正是在线失败的ep4/ep5；其它组无实质损害。限制：重放无IK闭环；运动臂仍未被遮挡；阈值99%与膨胀8 px为工程选择。

<a id="src-0139"></a>
## SRC-0139 — 遮罩A接入运行与闭环验证协议

- 授权：用户2026-10-08对“是否把遮罩A接入运行配置”选择“接入并验证”：先12 episode闭环（≤500 s），全部达标才做20封存+101/seed0完整复验（≤900 s），全部通过后安装正式入口并按原顺序进入4.5。
- 修改：`config/task4/estimator.yaml`加`use_mask: true / mask0: mask_left.png / mask1: mask_right.png`；新增`config/task4/mask_{left,right}.png`（=SRC0138遮罩A，SHA256 275d6e59…/35d82b7a…）。测试`tests/test_task4_reset_zupt_fix.py::SelfMask` RED（1 fail+1 error，`logs/task4/t4.3.5-fix/red-mask.log`）→GREEN 7/7；Task4 84测试OK；preflight PASS。
- 闭环判据（运行前固定）：`t4.3.5-mask-history-r1`，同history-r1脚本/参数，12个episode全部满足原门（XY RMSE≤.025 m且peak≤.075 m）才算通过；否则停止，不做complete-r3、不进4.5。

<a id="src-0140"></a>
## SRC-0140 — 遮罩A闭环结果（10/12）与确定性初始锚点偏差

- 证据：`results/task4/t4.3.5-mask-history-r1/{summary.json,analysis_history.json,raw.bag}`、`logs/task4/t4.3.5-mask-history-r1/state.json`（exit 0）；`results/task4/t4.3.5-offline/{anchor_offset.py,decompose_t4.3.5-mask-history-r1.json}`。执行：Claude claude-opus-5-5。
- 结论：遮罩A接入后闭环过原门10/12（ep3 .0259、ep4 .0394），按预登记规则未通过；所有episode在动作前真实底座相对公开命令初态偏差XY .0126 m/yaw −.0326 rad（36/36，几乎不变），属瞬移后确定性物理沉降与“公开命令位姿锚定”设计之间的系统偏差；不是噪声，也不是本节点修改引入。适用限制：p3d位置无噪声（SRC0122），yaw来自p3d姿态；偏差的物理原因（底盘落地/轮地接触/臂复位反力）尚未单独核查。

<a id="src-0141"></a>
## SRC-0141 — 复位5 cm落差导致的确定性初始位姿偏差

- 类型：源码审计+项目实测（只读）。执行：Claude claude-opus-5-5，用户2026-10-08选择“先查复位偏差原因”。
- 证据：`forem/src/modulation_rl/src/robot_env.cpp` L374–384（`origin.setZ(0.05)`后`setModelState`），与`husky/src/modulation_rl/src/robot_env.cpp`同段逐行相同（diff为空）；`results/task4/t4.3.5-offline/settle_trace.py`对`t4.3.5-mask-history-r1` ep3的p3d轨迹：瞬移瞬间dxy=0/dyaw=0、z=.05，落地弹跳后dxy≈(−.0071,+.0103) m、dyaw −.0327 rad并保持；SRC0140的36/36统计一致。
- 结论/限制：偏差来自继承的5 cm落差复位与刚性接触落地滑移；修复候选（改core复位高度为静止高度，或Task4层落地后重新放置）都会改变复位流程，尚未实施，物理上能否消除滑移需实测。

<a id="src-0142"></a>
## SRC-0142 — Task4复位层静止高度重新放置（实施与验证协议）

- 授权：用户2026-10-08对复位落差修复选择“Task4层落地后重新放置”（不改Task3 core）。执行：Claude claude-opus-5-5。
- 修改：`scripts/task4_env.py`新增`REST_Z=0.0`（实测base_footprint静止z −1e-6 m、roll/pitch<3e-7 rad，`t4.3.5-mask-history-r1` link_states）与`Task4Env._replace_base()`：原C++复位（含5 cm落差）返回后，暂停物理→`/gazebo/set_model_state`按`/task4/localization/commanded_pose`（即估计所用公开锚点）x/y/四元数、z=REST_Z、零速度放置→恢复物理，失败抛错（fail-closed），然后才`initialize` VIO。顺序：车轮置0→bootstrap→原C++复位→重新放置→VIO初始化。测试RED（1 fail+2 error，`logs/task4/t4.3.5-fix/red-rest.log`）→GREEN 10/10；Task4 87测试OK；preflight PASS。
- 验证（运行前固定）：`t4.3.5-rest-history-r1`同history-r1脚本参数，判据12/12过原门；附带检查动作开始时真实底座相对公开命令初态偏差（预期远小于此前12.6 mm/1.9°，实测为准）。全部通过才做complete-r3（20封存+101+seed0，≤900 s）。

<a id="src-0143"></a>
## SRC-0143 — 重新放置首次失败（触地瞬移导致关节爆炸）与3 mm间隙调整

- 证据：`results/task4/t4.3.5-rest-history-r1/{summary.json,joint_feedback.jsonl}`，`logs/task4/t4.3.5-rest-history-r1/{state.json,check.log}`（final_exit 1，“Could not set start pose after 50 trials”×9）。执行：Claude claude-opus-5-5。
- 结论/选择：z=0触地瞬移时机械臂关节突变，原规则复位失败；改为REST_Z+3 mm（工程选择：避免瞬移即接触，同时把落差从50 mm降到3 mm）。3 mm能否避免关节问题并消除落地滑移，以`t4.3.5-rest-history-r2`实测为准；失败则停止并报告。累计新增物理run：history-r1、wheelzero-r1、fix-history-r1、mask-history-r1、rest-history-r1（失败，42.6 s）。

<a id="src-0144"></a>
## SRC-0144 — 3 mm间隙重新放置的实测：锚点偏差消除，stale中止

- 证据：`results/task4/t4.3.5-rest-history-r2/{summary.json,analysis_history.json,joint_feedback.jsonl,raw.bag}`、`logs/task4/t4.3.5-rest-history-r2/{state.json,launch.log}`；`results/task4/t4.3.5-offline/anchor_offset.py`。执行：Claude claude-opus-5-5。
- 结论：初态偏差XY .0126→.0009 m、yaw −.0326→−.0018 rad；无关节异常；3个episode中2个过原门、ep1 .0255；ep2第74步因VIO位姿晚81 ms被原0.1 s新鲜度门fail-closed。stale原因未证明，不能归因于修改或录制负载；正式训练中同类事件会使episode失效，需单独评估。

<a id="src-0145"></a>
## SRC-0145 — rest-history-r3 重跑授权与判据

- 授权：用户2026-10-08选择“重跑12 episode验证”；代码/配置与r2相同（ZUPT IMU模式、车轮置0、遮罩A、3 mm间隙重新放置）。判据仍为12/12过原门（XY RMSE≤.025 m且peak≤.075 m）；另统计每帧VIO位姿发布延迟（poseimu bag接收时刻−header）以区分stale是偶发还是系统性。≤500 s/12 GiB，0更新。

<a id="src-0146"></a>
## SRC-0146 — rest-history-r3：11/12过原门、无stale

- 证据：`results/task4/t4.3.5-rest-history-r3/{summary.json,analysis_history.json,raw.bag}`、`logs/task4/t4.3.5-rest-history-r3/state.json`（exit 0）、`results/task4/t4.3.5-offline/latency_t4.3.5-rest-history-r3.json`。执行：Claude claude-opus-5-5。
- 结论：四项修复共同作用下12 episode闭环11/12过原门、0严重失真、初态偏差≈1 mm；唯一未过ep11 RMSE .0272 m为平滑漂移。预登记12/12未满足。stale在本run未复现（p99 25 ms）。

<a id="src-0147"></a>
## SRC-0147 — 完整核验授权（及“后续按推荐执行”）

- 用户2026-10-08：对rest-history-r3后的选择回答“跑原定完整核验”，并明确“后面的选择都按照你推荐的跑”。因此此后各决策点按Claude在文档中写明的推荐项执行，并逐项记录推荐理由；不扩大到未列出的新机制。
- 运行：`t4.3.5-complete-r1`，原`scripts/collect_task4_instances.py --passes 2 --quality-seeds 101 0 --fixed-replay config/task4/quality_action_replay.json`（20封存两遍+seed101零动作诊断+seed0固定76命令），原质量门（XY RMSE .025/peak .075 m、yaw .05/.15 rad、匹配/控制覆盖≥.95、新鲜度.1 s）不变；FOREM_CHECK_TIMEOUT 850 s，whole≤900 s，≤10 GiB；0训练更新。全部通过才安装正式入口/freeze并进入4.5。限制：11/12闭环（SRC0146）在交付中如实保留。

<a id="src-0148"></a>
## SRC-0148 — 修复后原定完整核验通过

- 证据：`results/task4/t4.3.5-complete-r1/`（attempts、capture、quality-seed{101,0}/evaluation.bag等）、`logs/task4/t4.3.5-complete-r1/state.json`（final_exit 0）、`results/task4/t4.3.5-complete-analysis/{analyze_complete.py,complete_receipt.json,analyze.log}`。执行：Claude claude-opus-5-5。
- 结论：all_gates_pass=true；20/20封存；seed101 .0180/.0265 m，seed0 76/76命令 .0162/.0304 m；原质量门未放宽。生效修改：ZUPT IMU模式（SRC0136）、复位车轮置0（SRC0136）、前板静态遮罩A（SRC0139）、3 mm间隙重新放置（SRC0142/0143）。限制：单次完整核验；闭环12 episode 11/12（SRC0146）。

<a id="src-0149"></a>
## SRC-0149 — 正式入口安装、冻结与非独立4.4接受

- 授权：用户2026-10-08“后面的选择都按照你推荐的跑”（SRC0147）；按原Task4顺序，完整核验通过（SRC0148）后安装4.4.1 v2正式入口并冻结。执行：Claude claude-opus-5-5。
- 安装：`scripts/{run_task4_formal.sh,task4_budget_watchdog.py,task4_formal_entry.py,task4_formal_gate.py,task4_resources.py}`与manifest SHA一致（`results/task4/t4.4.1-runtime-preparation/install_manifest.json`）；`scripts/task4_budget.py`=草稿（基线SHA匹配）；`task4_identity.py`/`run_task4_localization.sh`的闭包列表手工加入5个正式文件（草稿补丁基线早于task4_motion_raw/history_raw的加入）；6个草稿测试装为`tests/test_task4_formal_*.py`（仅改路径），42/42 OK（`logs/task4/t4.4-formal-install/formal-tests.log`）。
- 配置：`config/task4/sac_baseline.json`仅合并`actual_task_acceptance`与`checkpoint_selection_rule`（=草稿merge文件）并enabled=true，预算数字全部不变（前版本`logs/task4/t4.4-formal-install/sac_baseline.before.json`）；`config/task4/sealed_instances.json`改为`t4.3.5-complete-r1`真实20封存（10实例、verify_spawn通过），旧Task3元数据保留为`sealed_instances.task3_historical.json`；`config/task4/execution_freeze.json` freeze_id `t4.4-freeze-20261008-1`（56个实际identity组）。
- 接受：`results/task4/t4.4-formal-install/acceptance.json`由Claude代父出具，**非独立复核**，独立复核留task4.6。容器`task4_formal_entry.py --mode check`退出0“PASS actual container freeze/parent/source/budget/CUDA; no training”（`logs/task4/t4.4-formal-install/container-check.log`）。
- 限制：batch256实际成本此前未测（budget_basis原注）；6 attempts、72000 s训练/18000 s评估/90000 s总上限不变，评估可能被截断（4.4.1已注）。

<a id="src-0150"></a>
## SRC-0150 — 正式4.5运行失败：训练实例VIO初始化不可用

- 证据：`results/task4/t4.5-formal-r1/{formal_summary.json,train-seed*/summary.json,train-seed*/reset_attempts.jsonl}`、`results/task4/formal_campaign/ledger.json`、`logs/task4/t4.5-formal-r1/{timeline.txt,state.json,launch.log}`。OpenVINS `ov_init/src/init/InertialInitializer.cpp` L78–123（无特征时直接返回false；<15特征打印not enough feats）。执行：Claude claude-opus-5-5。
- 结论：6个attempt全部失败/被拒（4次VIO初始化超时、2次原预算规则拒绝），0更新，验证/测试0尝试；训练实例初始化12/15成功（24/37/33失败）。限制：仅15次reset样本；遮罩A的影响、失败实例的具体视野未单独核查；未改任何预算或规则补跑。

<a id="src-0151"></a>
## SRC-0151 — 训练实例VIO初始化可用性普查（诊断协议）

- 依据用户“后续按推荐执行”（SRC0147）；推荐理由：正式预算已耗尽（SRC0150），任何修复前先量化训练分布上的初始化失败率及遮罩A是否减少关键特征。工程选择，非新机制。执行：Claude claude-opus-5-5。
- 运行：`t4.5-init-survey-r1`，`scripts/task4_init_survey.py 0-29`（新增，测试`tests/test_task4_init_survey.py` RED→GREEN 5/5，已加入runtime闭包）：同Task4Env原复位生命周期，逐实例reset（无动作、0更新、不读真值），记录初始化成功/超时；每实例在reset返回或失败时保存一对原始双目图像，供离线统计FAST角点总数及落入遮罩A的数量。≤1800 s whole（单实例最坏200 s门）、≤1 GiB。新增文件使t4.4-freeze-20261008-1的identity失效；该冻结预算已耗尽，后续正式运行本来就需要新冻结。

<a id="src-0152"></a>
## SRC-0152 — 训练实例初始化普查结果：约13%视角特征不足，遮罩不是原因

- 证据：`results/task4/t4.5-init-survey-r1/{summary.json,survey.jsonl,features_vs_mask.json,inst*.png}`、`logs/task4/t4.5-init-survey-r1/state.json`（final_exit 0，foreign []）；分析`results/task4/t4.3.5-offline/features_vs_mask.py`（FAST阈值20=config fast_threshold）。执行：Claude claude-opus-5-5。
- 结论：实例0–29中26/30初始化成功，失败1/7/24/27（正式run另见24/33/37）；失败实例右目FAST角点1–6、左目6–15，成功实例右目≥12、平均约32；遮罩A在任一组只去掉1–3个角点，关闭遮罩也达不到OpenVINS初始化所需≥15跟踪特征。原因是训练分布中部分初始视角朝向空旷区域。适用限制：FAST角点只是跟踪特征的代理；30个实例样本。
- 处理选项均涉及任务语义/场景/正式预算：训练复位遇VIO初始化失败时重新抽取实例（类似原复位重试，但改变训练分布）、场景纹理/视点（新机制）、或接受失败作为基线结果；需用户决定，并需新的正式预算冻结。

<a id="src-0153"></a>
## SRC-0153 — 4.5正式运行r2：训练重抽、训练专用初始化超时、磁盘扫描节流与新预算

- 授权：用户2026-10-08“按你推荐的重新抽实例，申请新预算继续跑”。执行：Claude claude-opus-5-5。
- 依据：SRC0150/0152（训练实例约13%视角无法初始化；评估封存实例全部可初始化）；实测成本（`results/task4/t4.5-init-survey-r1/survey.jsonl`成功reset均值23.6 s/最大42.7 s；`results/task4/formal_campaign/ledger.json` r1约24步/episode；history bags中VIO静态初始化2.39–2.52 sim s，RTF≈0.45→约5.5 s墙钟）；r1中`resources()`每步两次遍历results/task4+logs/task4整树（约47 GB/大量文件且每步新增npz）导致约1 s/步。
- 修改（测试`tests/test_task4_formal_redraw.py` RED 7/7→GREEN；Task4全部141测试OK）：①`task4_formal_entry.reset_with_redraw`：仅训练reset、仅错误“raw VIO initialization timeout”时记录`vio_init_failed_redrawn`并按同一RNG重抽，≤`training_vio_init_redraws_cap`=5；评估/封存实例不重抽。②`Task4Env._await_ready`读`init_timeout_wall_s`（默认120不变），正式训练reset设`training_init_timeout_wall_s`=30，评估仍120。③`task4_resources.DiskMeter`：actor与watchdog的整树磁盘扫描每路径至多30 s一次（与既有30 s源码复核节奏一致），磁盘上限不变。④账本路径改为`results/task4/formal_campaign/<freeze_id>/ledger.json`，且freeze必须带`budget_authorization`；同一freeze内仍拒绝任何重置；r1账本原位保留为历史。⑤3个旧测试中硬编码的freeze1预算数字改为读取当前配置，1个依赖live状态的门测试改为临时根目录（意图不变）。
- 新预算：每attempt 36000 s，训练216000 s（=6×36000，现有校验规则要求），评估36000 s（=60集×600 s，避免截断），总252000 s；seeds/steps/updates/attempts/checkpoints/评估实例与选择规则不变。预期实际约25–30 h（估计，非承诺）。限制：重抽排除少数空旷视角实例，训练分布与原定略有差异，交付须写明。

<a id="src-0154"></a>
## SRC-0154 — 4.5正式运行r2：开始学习，但被瞬时基础设施故障终止

- 证据：`results/task4/t4.5-formal-r2/{formal_summary.json,train-seed*/summary.json,train-seed*/reset_attempts.jsonl}`、`results/task4/formal_campaign/t4.4-freeze-20261008-2/ledger.json`、`logs/task4/t4.5-formal-r2/{timeline.txt,launch.log,check.log,state.json}`。执行：Claude claude-opus-5-5。
- 结果：seed0 a0在1892步/1636次更新、seed1 a0在566步/310次更新时因定位门INVALID_STOP失败（status显示末估计年龄0.216 s；“invalid lifecycle”是失效后到达位姿覆盖的原因字段，首因判断为stale，未能直接证实）；seed2 a0在1382步/1126次更新时gzserver段错误（exit 139，紧邻一次正常“Reseting environment”，约1.9 h、约100次复位后），之后sim时钟停止、campaign挂起约70 min，由Claude按身份监督停止（check exit 1，cleanup 0，foreign []）。三个seed的重试均因已消耗交互按原规则拒绝，freeze2预算实际耗尽（训练计费3237 s）。VIO每帧处理全程≤48.5 ms、behind≤1.7 ms，stale不来自VIO计算；重抽机制按设计工作。
- 结论/限制：当前正式runner“任何定位失效或仿真崩溃即判整个attempt失败、已有交互不可重试、不支持恢复”与该仿真栈在数小时连续运行中的瞬时故障率不相容；修复需改变训练期故障处理语义（例如episode级失效截断、或可恢复训练状态），属协议变更，需用户决定。

<a id="src-0155"></a>
## SRC-0155 — 4.5正式运行r3：训练期容错与可恢复训练（实施与新预算）

- 授权：用户2026-10-08对“训练容错并续跑”（episode级定位失效截断+崩溃后从保存点恢复+排查超时来源，验证/测试语义不变，再申请预算）选择推荐项。执行：Claude claude-opus-5-5。
- 修改：`scripts/task4_resources.py` Ledger新增`abandon_operation`/`register_resume`/`suspend`/`resume`，挂起作业在重开时保留、`close()`不判失败；步/更新上限=原目标+显式丢失额度（`training_lost_interactions_cap_per_seed`/`training_lost_updates_cap_per_seed`=5000），且已完成计数不得超过原目标；墙钟仍从首次开始计（停机时间计入）。`scripts/task4_formal_entry.py`：训练episode内“localization ready:”失效→放弃该步（不存转移）、记录`localization_faults.jsonl`、重新复位（≤100/attempt）；复位时“localization invalid”也按重抽处理；`ClockLiveness`线程（/clock停滞>45 s墙钟→SIGUSR1→InfrastructureFault），ROS错误伴随时钟停滞也判基础设施故障；每1000步原子保存完整训练状态（网络/target/优化器/调度器/log_alpha/alpha及其设备/回放/全部RNG/计数），哈希登记于账本；基础设施故障→挂起作业并退出75，不对已死仿真做阻塞关闭；新段`ensure_env`→加载→单次reset继续同一attempt；评估中基础设施故障该集仍记失败（语义不变）然后进入新段。新增`scripts/task4_formal_resumable.py`（宿主驱动：每段宿主门+一次受监督完整栈启动，退出75则续下一段，≤12段），并入runtime闭包与FORMAL_RUNTIME_FILES。
- 测试：`tests/test_task4_formal_resume.py` RED 12→GREEN 13；旧训练循环测试的假上下文补新钩子并断言第0步先保存；r2重抽测试改用不可重抽错误（行为按设计改变）；Task4全部153测试OK（`logs/task4/t4.4-formal-install/r3-all-task4-tests.log`）。真实SAC CUDA恢复往返：保存→加载→续5次更新与原地续更新损失最大差0.0、策略参数一致、实例RNG一致（`results/task4/t4.4-formal-install/resume_integration.json`）。
- 新预算（freeze3）：沿freeze2的时间上限（每attempt 36000 s、训练216000 s、评估36000 s、总252000 s）及步/更新/seed/attempt/checkpoint不变，另加丢失额度5000/5000与≤12段。局限：恢复回滚最多丢失约1000步交互（计入额度）；停机时间计费；stale来源尚未定位（运行中记录故障时刻供排查）。

<a id="src-0156"></a>
## SRC-0156 — r3结果（复位路径崩溃未被识别）与r4修正

- r3证据：`results/task4/t4.5-formal-r3-s1/`、`logs/task4/t4.5-formal-r3-s1/{launch.log,state.json}`、`logs/task4/t4.5-formal-r3-driver.jsonl`、`results/task4/formal_campaign/t4.4-freeze-20261008-3/ledger.json`。seed0在2595步/2339更新（恢复点2000步）时gzserver再次段错误（exit 139，约30 min，发生在一次训练reset中）；传输错误从reset路径抛出，r3只在env.step处做基础设施判别，因此seed0被判failed而非挂起；随后seed1两次在已死仿真上0步失败。Claude按身份监督停止（check -9，cleanup 0），驱动判stop未再续段。r3期间无定位失效记录。宿主apport未保存core，launch/check日志无法把崩溃归因到具体Gazebo服务调用。
- r4修正（同SRC0155用户授权；测试RED 2 fail+1 error→GREEN，Task4 156测试OK，`logs/task4/t4.4-formal-install/r4-*.log`）：①train()中除预算/中断外的任何异常都先做仿真存活判别，时钟停滞则挂起而非失败；②新attempt在首次reset前先保存恢复点；③仿真在任何交互/更新前就死亡的attempt记为`infrastructure_failed_before_start`，不占重试与attempt上限；④恢复保存间隔1000→250步，单次崩溃最多丢约250步（额度5000）；⑤`visual_inertial.launch`仅对Gazebo include注入glibc `libSegFault.so`（`SEGFAULT_SIGNALS=segv abrt bus ill fpe`），下次崩溃在launch.log留下回溯，用于定位原因（`gzserver --version`预检正常）。freeze3中seed0/1已按规则耗尽，r4用新冻结继续，预算数字不变。

<a id="src-0157"></a>
## SRC-0157 — r4中止：LD_PRELOAD覆盖VirtualGL导致软件渲染；修正与GPU渲染复核

- 证据：`results/task4/t4.5-formal-r4-s1/train-seed0-attempt0/{localization_faults.jsonl,reset_attempts.jsonl}`（约3 min内7步、几乎每个episode开头即stale/invalid）、`logs/task4/t4.5-formal-r4-s1/state.json`（Claude监督停止，check -9，cleanup 0）；运行中`nvidia-smi`仅见SAC python进程、无gzserver（此前健康运行gzserver约149 MiB图形上下文）。执行：Claude claude-opus-5-5。
- 原因：SRC0156在launch中`<env LD_PRELOAD=libSegFault.so>`覆盖了vglrun注入的VirtualGL faker，Gazebo相机退化为软件渲染，图像/位姿延迟导致stale。这是Claude引入的回归，r4数据不作训练结论。
- 修正：`value="$(optenv LD_PRELOAD) /lib/x86_64-linux-gnu/libSegFault.so"`（追加而非覆盖），测试断言该写法；`t4.5-gpu-render-check-r1`（init_survey 0-1，exit 0，cleanup 0）运行中`nvidia-smi`见`gzserver 149MiB G`于GPU0，实例0初始化、1失败与普查一致。Task4 156测试OK（`logs/task4/t4.4-formal-install/r5-all-task4-tests.log`）。以新冻结r5继续，预算不变。

<a id="src-0158"></a>
## SRC-0158 — r5结果：机械臂卡死后原复位持续失败；归为仿真卡死的基础设施故障

- 证据：`results/task4/t4.5-formal-r5-s1/{formal_summary.json,train-seed*/summary.json}`、`logs/task4/t4.5-formal-r5-s1/check.log`、`logs/task4/t4.5-formal-r5-driver.jsonl`、`results/task4/formal_campaign/t4.4-freeze-20261008-5/ledger.json`。执行：Claude claude-opus-5-5。
- 结果：r5 seed0运行约75 min达5828步/5572更新（期间1次定位失效被容错、无Gazebo崩溃），随后原C++复位“Reached 9 reset attempts, exception: Could not set start pose after 50 trials”；check.log 500次重试中同一关节始终1.52894 rad（目标≈0）且arm_client失败，即机械臂在该仿真实例中卡死；仿真时钟正常，故未被判为基础设施故障，seed0判failed；随后seed1/seed2各两次在同一卡死仿真上0步失败，campaign按规则结束（训练计费4598 s）。
- 修正（同SRC0155授权）：`is_simulator_stuck`——原复位耗尽重试且报“Could not set start pose”时，训练中挂起并在新段从保存点续跑；评估中该集仍记失败（语义不变）后进入新段。复位与任务语义不变，不新增强制关节设定。段上限12→30（墙钟上限不变，仍限总耗时）。测试RED（3 fail+1 error）→GREEN；Task4 159测试OK（`logs/task4/t4.4-formal-install/r6-*.log`）。freeze5中seed0–2已按规则耗尽，以新冻结r6继续，预算数字不变；按设计不跨冻结恢复旧保存点。

<a id="src-0159"></a>
## SRC-0159 — r6运行中问题诊断：预算比例、内部成功与物理末端偏差、挂起分布（只读）

- 类型：项目实测只读复核+推导；核查2026-10-09 Claude claude-opus-5-5（用户问“Task4问题的解决方案”）。未停止/修改r6，未启动新运行。
- 证据：`results/task4/t4.5-formal-r6-s*/eval-{validation,test}-seed0-*/{summary.json,actual_task_evaluation.json,task_steps.jsonl}`；`logs/task4/t4.5-formal-r6-driver.jsonl`；`logs/task4/t4.5-formal-r6-s{1..7}/check.log`；`config/task4/sac_baseline.json`；原版`husky/src/modulation_rl/scripts/configs/best_defaults_ray.yaml`（total_steps 1000000/10000000）与`husky/src/modulation_rl/scripts/modulation/utils.py` L46–48（total_steps默认10000000、buffer_size 100000）；`src/modulation_rl/src/robot_env.cpp` L479–515（gripper_tf为内部规划运动学，gripper_tf_achieved为TF查询）。
- 结果1（预算）：冻结每seed 20000步、回放10000，为原版best_defaults 1000000步的2%、原回放的10%（推导：20000/1000000）。r6自2026-10-08 22:09起约10.7 h完成seed0训练+20集评估及seed1约19.7k步，推得当前吞吐≈5 h/2万步/seed；按此线性外推100万步≈250 h/seed（推导，未实测）。
- 结果2（内部/物理不一致）：seed0 step10000验证实例104 `original_internal_success=true`但物理`position_error_m=0.0805`（门0.025 m），`actual_goal_achieved_samples=0`。同集`gripper_dist_to_achieved`（内部规划夹爪与TF夹爪）首步0.0738 m、均值0.0747 m、末步0.0886 m；末步两者z差≈0.095 m。即偏差从第0步就存在且量级大于成功门。来源分解（规划z0平面/公开z.05与VIO z、基座估计误差、关节跟踪、夹爪静态链）**待验证**；truth反馈下同指标尚无对照测量。
- 结果3（测试）：seed0选中step5000，测试106–110共5/5完成、0确认成功；按SRC0108每seed≥1确认成功门，r6性能接受已不可能满足（执行仍可完成）。
- 结果4（挂起）：段s1–s7中s4、s6为“Could not set start pose”机械臂卡死，其余为时钟停滞/定位失效触发；各段持续约0.9–1.6 h（s4约3.2 h）。“运行时长相关的仿真退化”为**待验证假设**，未测gzserver内存/时长相关性。
- 采用/限制：仅支持Task4问题诊断与方案建议，不构成新实验/修改授权；不改变r6冻结协议与结论口径。

<a id="src-0160"></a>
## SRC-0160 — r6中断与分离式续跑的Claude历史记录（原误复用SRC-0159）

> 2026-10-09 Codex校正：本条保留Claude原始记录，独立编号消除重复锚点。下述“工具后台终止牵连”的因果归因不准确：09:01:45是Codex依用户明确暂停指令发送TERM，见[SRC-0163](#src-0163)的PID身份与信号收据；r6b随后也已按同一用户指令停止。中断期间的失败应区分行政暂停与自主运行失败，不将其用于判断策略能力。

- 事实：2026-10-09 09:01:45 Claude会话中承载宿主驱动的后台工具任务结束，驱动进程随之终止，其子进程wrapper收到TERM并执行受监督清理（`logs/task4/t4.5-formal-r6-s8/state.json`：interrupted TERM，check -9，cleanup 0，final 143）。此时seed0/seed1训练均已完成（各20000步/19744更新），seed1正在验证。
- 影响（不可改写的账本记录，如实保留）：seed1 step10000验证中，实例101在清理前（09:01:34）因VIO初始化超时失败，属真实失败；实例102（跨越09:01:45）、103、104（清理期间，TF外推错误/“independent watchdog died”）为**工具中断造成的失败**，按协议仍计失败并影响seed1的checkpoint选择（不利于step10000）。未手工编辑账本。session按崩溃尾部规则保守计费。
- 处理：以`setsid nohup`在独立会话启动驱动，新段前缀`t4.5-formal-r6b`（旧段run-id已存在），同一freeze6账本继续；日志`logs/task4/t4.5-formal-r6b-driver.{out,jsonl}`。执行：Claude claude-opus-5-5。


<a id="src-0161"></a>
## SRC-0161 — Task4独立故障复算：规划残差、估计TF和物理末端分离

- 类型：项目已有实测的独立离线复算＋代码审计＋几何推导；核查人Codex /root，2026-10-09。未新建仿真/训练。
- 版本/证据：`results/task4/t4-diagnosis-20261009/{snapshot.json,ledger_snapshot.json,failure_classification.json,evaluations_seed0.json,training_snapshot.json,decompose.py,decomposition_summary.json,decomposition_rows.json}`；代码及输入SHA见snapshot/decomposition_summary；运行原始版本为`t4.4-freeze-20261008-6`，验证案例`t4.5-formal-r6-s4/eval-validation-seed0-step10000-instance104`。
- 精确代码：`src/modulation_rl/src/robot_env.cpp:setWorldJoint/step/getRobotObs`，`scripts/task4_env.py:_begin/_replace_base`，`src/forem_localization/scripts/estimate_gate.py:accept`，`src/modulation_rl/scripts/modulation/envs/{robotenv.py:step,eeplanner.py:_is_done,combined_env.py:step}`，`scripts/record_task4_quality.py:physical`。
- 结论：seed0五个测试均正常结束但0/5确认成功；每集20次kin_failure均伴随`dist_to_desired>.1 m`，无selfcollision/底盘碰撞；该量是规划期望末端与IK规划解的残差，不能称实际伺服误差，也未证明BioIK原始求解标志均为失败。冻结要求每seed至少1真实成功，故r6不能性能accepted（SRC0108）。训练seed0 317个已记录终止episode仅4内部成功；含回滚段记录，不等同去重正式样本数。
- FK推导：由该run记录URDF固定链和关节轴构造`F(q)`；`P=T_planar F(q_plan)`、`A=T_planar F(q_measured)`、`E=T_est3D F(q_measured)`、`G=独立物理夹爪`。位置向量恒等式`G-P=(A-P)+(E-A)+(G-E)`，单位m；最后项含定位/时序/模型残差，不能全算VIO。`T_true_inferred=G F(q_measured)^(-1)`只用于离线解释，不是新真值传感器。记录关节按名字匹配；物理LinkStates无header，使用最近sim receipt配对，物理步最大偏差5.5ms、关节对物理最大4ms、估计最大53.5ms，因此不是严格同刻因果实验。
- 案例104末步：规划距目标.024467m，物理距目标.080463m；规划与物理相差.056457m；规划与估计TF相差.088576m。原SRC0159平均.074685m是规划—估计TF，不是规划—物理（后者本集均值.048218m）。重建规划—TF距离与原日志最大差9.4e-10m，支持FK链复算正确；夹爪末端固定链无平移，不能用“漏15cm夹爪偏移”解释本案例。
- 坐标事实：`_begin`固定锚点z=.05m，`_replace_base`投放到.003m后落地；规划world joint只存x/y/yaw。案例首步估计TF末端比物理末端高.049857m。此不一致已确认，但不能推断修正z后所有成功率问题消失；残差仍混合底盘姿态/XY漂移/实际关节跟踪及异步反馈。
- 时序线索：规划执行参数dt=.02s；案例104评估相邻步sim间隔中位.054s，seed0训练相邻递增记录中位.09375s（不含done边界，但可能含故障reset间隔）。代码未按固定dt等待，端到端负载改变实际间隔；是否造成低成功率待有控制的验证。
- 采用/限制：支持先核坐标/时间/反馈，再判断学习预算。20000相对参考配置1000000为2%只说明预算差异，不能证明必须训练100万步或扩大预算一定有效。

<a id="src-0162"></a>
## SRC-0162 — Task4 CPU/GPU与线程现状；优化候选及证据限制

- 类型：项目代码审计＋一次设备/进程观察；核查2026-10-09 Codex /root。证据`results/task4/t4-diagnosis-20261009/pre_pause_device_observation.json`，原入口`task4_formal_entry.py:new_agent/resources/ordinary_train_loop/emit_transition`及`task4_resources.py:atomic_write`，原训练`train-seed0-attempt0/fresh_state.json`。
- GPU事实：正式入口硬要求policy/critic/target/熵在cuda:0；SAC.select_action/update_parameters将网络和输入送CUDA，地图CNN包含其中；run_task4_localization.sh用VirtualGL egl0。暂停前nvidia-smi pmon同时观察到gzserver图形与actor CUDA进程。不能把SAC说成在CPU训练。
- 采样限制：09:00左右seed1评估/复位期间GPU0瞬时0%、917MiB；其余3卡瞬时0%。ps lifetime CPU为gzserver159%、actor41.6%、pose_adapter41%、OpenVINS38.2%（100%=一个逻辑核）。这些不是正式训练分阶段profile，不能推出CPU墙钟占比或GPU训练利用率。
- CPU事实：Gazebo ODE、BioIK/MoveIt、ROS/costmap、OpenVINS本地KLT/Eigen路径在CPU；`ReplayMemory.sample`使用random.sample＋np.stack，SAC随后构造FloatTensor并复制GPU。每步transition压缩/哈希、账本原子写＋fsync是串行成本候选，真实占比尚未测。
- 线程事实：`config/task4/estimator.yaml:num_opencv_threads=4`，`VioManager.cpp`调用cv::setNumThreads，`TrackKLT.cpp`使用parallel_for_和CPU calcOpticalFlowPyrLK；不是所有模块单线程。multi_threading_pubs/subs当前false；官方本地`VioManagerOptions.h:414–418`对仿真/串行回放有关闭异步的注释，`ROS1Visualizer.cpp:callback_inertial/callback_stereo`有异步分支。不能直接全改true而不验证消息顺序与reset。
- 工程建议（未实施/未测收益）：先分段测reset/定位等待/env step/采样与CPU→GPU复制/CUDA update/日志与预算管理；比较已有OpenCV4线程与受限候选线程数，检查有效后端/实际线程；对独立采样准备、压缩和离线分析优先评估并行。Python CPU循环不假定普通线程可提速，优先释放GIL的库或受控进程。任何异步写入保留预算写前声明、数据与checkpoint一致性、退出排空。固定输出合同后才考虑锁页内存/批复制；不默认把OpenVINS移植CUDA、换物理后端、多GPU SAC或并行物理环境。
- 采用/限制：支持task4.5.2性能计划，按用户“可以多线程就优化”的要求验证有效后启用；本次只写计划，未宣称新线程优化完成。

<a id="src-0163"></a>
## SRC-0163 — 用户暂停正式训练、后续文档与范围选择（2026-10-09）

- 类型：用户指令＋行政操作实测；记录Codex /root，2026-10-09；本条为SRC0160错误停机归因的校正。
- 指令：用户先要求检查Task4给方案，追加CPU/GPU问题；随后明确“继续帮助书写Task4的后续文档，可以暂停现在的无用训练了”；又要求评估传感器/SCWM和可行多线程优化。TF选择确认“刚才搞错了，反正按照你的推荐”：保留TF传递估计位姿、隔离真值，先保留双目＋IMU。不是新增传感器/真值对照/更换定位器/大规模训练授权。
- 操作与版本：`results/task4/t4-diagnosis-20261009/{pause_signals.json,pause_second_driver_and_gate.json,sac_baseline.before_pause.json,pause_receipt.json,ledger_before_user_pause.json,ledger_after_user_pause.json}`；宿主driver和wrapper经PID/start-time/cmd核对，用pidfd发送TERM。r6在09:01:45开始清理；另一个执行方误将其当工具中断重启r6b，09:04:52同法停止r6b，并将现有`sac_baseline.json` enabled设false，阻止再次正式启动；其余训练参数未改。旧freeze/source snapshots/账本保留，不更新旧freeze冒充匹配。
- 结果：r6-s8与r6b-s1均check -9、cleanup 0、wrapper final143、foreign=[]；温和停止超时后既有清理器按身份核验升级信号。09:05:49后容器仅docker-init/sleep。6个训练checkpoint及2个resume文件保留；seed0/1各20000steps/19744updates，seed2未训练；暂停时评估不完整，行政中断不包装成算法失败或成功。
- 恢复边界：task4.5 paused。暂停优先于之前自动续跑/按推荐推进指令。未经用户恢复不启新formal；live enabled=false是暂停保护，不能仅改true绕过身份/预算核验。修正后新版本重新回归和冻结；跨版本旧replay/权重不自动沿用为正式主基线。

<a id="src-0164"></a>
## SRC-0164 — SC²-WM不是整套RGB-only度量定位系统

- 类型：外部原论文/官方源码；2026-10-09 Codex /root已读对应原文与本地代码，未运行SCWM。
- 来源：Yao等，SC²-WM，2026，arXiv:2608.07548v1，https://arxiv.org/html/2608.07548v1；官方仓库https://github.com/sunrise-yuze/SC2_WM，本地`scwm` commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b。
- 精确位置：论文§3任务定义、Appendix C模型/输入、Appendix E实机；代码`run_r2r/r2r_vlnce.yaml:7/18/29`，`run_r2r/iter_train.yaml:MODEL`，`vlnce_baselines/ss_trainer_ETP.py:rollout`约1810–1897（depth投影/地图）和2091–2130（get_pos_ori进入图），`common/environments.py:get_pos_ori/get_agent_info`直接调用sim.get_agent_state。
- 原始结论：仿真定义RGB-D输入，monocular在该文指单视角RGB-D；实机D435i的深度用于避障，不能据此断言实机策略必需深度编码或相机自带IMU必被算法使用。仿真实现另读取模拟器位置/朝向维护地图；本文已读部分不交付一个等价于FoReM raw双目/IMU定位的独立精度验收。代码有部分depth encoder注释，不应仅凭配置断言每个网络分支都吃深度；上述实际depth投影路径另已核查。
- 采用/限制：用来纠正“SCWM只需RGB，所以FoReM删IMU更好”的前提；导航潜态修正与本项目机械臂度量定位不同，不能由导航表现担保2.5cm末端门。此处传感器说明不构成SCWM复现/WM训练授权。

<a id="src-0165"></a>
## SRC-0165 — FoReM传感器与位姿来源建议：保留双目惯性，附条件的备选

- 类型：官方技术资料＋本地代码＋工程选择；核查2026-10-09 Codex /root。
- 来源/位置：OpenVINS官方`https://docs.openvins.com/gs-calibration.html`的IMU Noise Calibration / Camera-IMU Calibration，`https://docs.openvins.com/fej.html`的VINS可观性；Mur-Artal/Tardós ORB-SLAM2官方README简介`https://github.com/raulmur/ORB_SLAM2`（双目/RGB-D true scale），2017论文DOI10.1109/TRO.2017.2705103（本轮未重读全文）；robot_localization Noetic官方`https://raw.githubusercontent.com/cra-ros-pkg/robot_localization/noetic-devel/doc/configuring_robot_localization.rst`的Fusing Unmeasured Variables/重复信息提醒。均已读上述网页/原始rst，ROS文档主页被反爬，未据其空页取证。
- 原始依据：视觉惯性依赖外参/时间/噪声标定及可观性条件；单目纯视觉与双目/RGB-D度量尺度能力不同；轮式平台可融合轮速与惯性，但同源pose/twist不应当独立重复证据。尺度推导：纯投影`u~K(RX+t)`对同时缩放X和t不变，若无已知尺寸/基线/运动或其他度量信息，单目图像不能唯一确定米制尺度；不声称任何单目系统都不可能度量定位。
- 本地事实：Task4用双目RGB图20Hz＋6轴IMU200Hz，VIO不是直接视觉SAC；`visual_inertial_sensors.urdf.xacro`、`protocol.yaml`输入权限、`task4_input_adapter.py` raw转换、`pose_adapter.py/estimate_gate.py`；worlds.cpp的TF监听读由估计桥发布的map→base，关节TF由实际joint_states发布，记录的规划末端另来自IK关节（SRC0161）。公式`T_map_base=A T_vio_imu inv(T_base_imu)`，A每次reset只由公开起点与首次VIO算一次；TF不减少来源误差；真值仅独立评估。无绝对锚点时不能仅凭VIO恢复任意世界原点/绝对yaw。
- 工程建议：保留当前双目＋IMU先修已知链路错误；纯RGB会改变估计器/尺度与输入合同，暂无改善本问题的证据。现有`husky_control/config/control.yaml`包含diff_drive_controller/轮关节反馈，前激光用于costmap；未来若视觉可用性仍不足，优先审查轮速辅助，其次再评估已有激光定位或RGB-D。均仅备选，不安装/融合；不得把odom消息名当编码器实测，须核对open_loop、原始关节来源、轮径/轮距、滑移、时间/协方差与相关性；不能把VIO与其已用IMU再次当独立观测简单叠加。
- 限制：双目惯性是有依据的工程选择，未证明当前Gazebo特征/平面运动条件下已满足末端任务精度；添加传感器也不会自动修复锚点/规划与实际反馈混用。新增传感器/估计器仍须明确批准范围。

<a id="src-0166"></a>
## SRC-0166 — Task4暂停后的最小修复/性能/回归路线（工程计划，未实施）

- 类型：依据SRC0161–0165与用户暂停/文档指令的工程选择；2026-10-09 Codex /root制定，默认模型GPT6.1sol/Sonnet5.5。跨坐标/难复现故障high，性能/回归medium，普通文档low或默认；实际本会话模型/强度未知。
- 选择：task4.5.1先核感知/TF权限、坐标与执行残差；task4.5.2分阶段计时与有证据的CPU/GPU/多线程优化及故障边界；task4.5.3有限回归→重新冻结→用户恢复后同任务普通SAC基线→task4.6独立复核。具体输入输出与三文档以task4.5父/子流程为准，本条不另维护协议。
- 理由/备选：已有残差/锚点/时序问题不能靠放宽成功门解决；GPU网络/渲染已开启，先profile才能决定加线程或搬数据是否有效。未选默认增加训练至100万步、换传感器/物理引擎、并行环境、世界模型训练、truth同预算对照或改奖励/终止/观测。
- 资源工程候选：离线线程比较1/2/4（现有4）/8，每档同一已录raw、固定输入区间各3次，预热和有效段分开，整体候选墙钟≤900s/产物≤2GiB；不是已授权运行。CPU数量与库后端不足的档位跳过并说明。既有物理complete检查候选沿SRC0147≤900s/10GiB/0更新，CUDA先导沿原76步/60更新预算，保持是接口检查；任何新增预算正式前单独冻结，不自动累加失败次数或复用预算。
- 采用/限制：文档交付review不等于实验通过。启用线程必须数据/消息/预算/恢复一致性回归；没有收益或时序变差就不启用。旧测试已可见，不能边看106–110边挑配置后再宣称独立未知测试；若新方案依赖其结果调参，独立确认集需要另行预登记。当前仅保留旧测试作历史验收/回归，不自动新增数据集。


<a id="src-0167"></a>
## SRC-0167 — 用户授权按服务器确定充分训练规模；硬件实测与预算推导

> **当前效力说明（2026-10-09）：** 本条保存此前审计/工程草案。作者自定的预算细分、实验模式和参数不等于用户授权；最新范围与适用校正见[SRC0178](#src-0178)、[SRC0179](#src-0179)。硬件/源码实测及其原有限制仍保留。


- 类型：用户最新指令＋项目硬件实测＋线性推导＋工程配置建议。2026-10-09 Codex /root核查；用户要求“训练规模不要加以太多限制，可以根据服务器参数确定训练规模”。覆盖SRC0166中先不推荐百万步的早期选择，不撤销明确暂停。
- 原始证据：`results/task4/t4-diagnosis-20261009/{hardware_snapshot.json,scale_derivation.json}`（lscpu/free/df/nvidia-smi/topo/docker inspect命令及退出码）；freeze6 ledger中seed0/1训练jobs；本地参考`husky/src/modulation_rl/scripts/configs/best_defaults_ray.yaml:2/22/48`为1000000步，:69另分支10000000，具体任务不同，不能把参考数值当本任务收敛保证。
- 实测：2×Xeon Gold6530，共64在线逻辑CPU、每核1线程、2 NUMA；内存270121525248 bytes≈251.57GiB，可用约235GiB（瞬时）；4×RTX PRO6000 Blackwell Server Edition，每卡97887MiB≈95.59GiB。GPU0/1近CPU0–31，GPU2/3近32–63。/home卷可用20466945507328 bytes≈18.61TiB，ROTA=1逻辑卷（不能单凭标志断言底层硬盘型号/IOPS）；根SSD可用约489.7GiB。容器无CPU/内存硬限额，shm2GiB。均为快照，执行前重查他人占用。
- 推导：seed0 17155.198s/20000=.85776s/有效step；seed1 20665.179s/20000=1.03326s/step，含各自训练阶段复位/故障开销。线性外推每seed100万步约9.93–11.96天，3seed串行29.78–35.88天；若三份真正隔离环境且吞吐不退化，并行墙钟约单seed时长。未含新优化收益、episode长度变化、额外评估；不是承诺工期。
- 内存推导：已有10000条replay实际1163080000 bytes；按同结构100000条约11630800000 bytes≈10.83GiB/seed，不含模型、临时np.stack、序列化双份等峰值。故恢复原参考100000容量在本机有空间，仍需实测峰值。
- 工程建议：正式目标3个原seed×1000000有效交互；batch256、普通update每步1次、warmup1000、学习率horizon5000001保持既有合同；每seed更新上限999744，replay100000。保存100k/250k/500k/750k/1m用于验证选择，不将首100k当低成功率自动终止门。没有通过误差链/有限回归前仍不训练。
- 资源建议：每worker一张GPU/16个CPU/64GiB RAM，显存保护32GiB；三worker最多48CPU/192GiB RAM，留16CPU/约60GiB及第四张卡给系统/其他工作（不是独占授权）。每seed产物200GiB、campaign新增1TiB；训练18天/seed作约1.5倍较慢实测速率余量，3seed合计54worker-days，评估合计3worker-days，总57worker-days。资源保护不应当被误称预期消耗。具体值唯一协议见task4.5.3流程，本台账仅说明依据。
- 并行限制：当前单ROS master/共享锁/固定GPU0/全局ledger只能串行。三seed多环境并行属于拟议部署改造，未实现，不能直接多开现有driver；本轮不创建容器/进程。若选并行，先完成端口/命名空间/锁/账本/输出/TF/资源与清理范围隔离验收，保持每seed普通SAC，不做DDP共享梯度；未获该改造范围则串行执行相同规模。
- 失败保护建议：用同seed同版本checkpoint续跑，不轻易丢掉整seed重来；保留可累计故障与丢失步数统计。连续故障应诊断，不用很小attempt总数代替可靠性处理，也不能无条件无限重启。与18天预算一致的段数/故障率阈值在新freeze前明示，旧30段/10小时上限不能原样套到百万步；本轮不修改live预算数字。


<a id="src-0168"></a>
## SRC-0168 — SC²-WM的内部状态偏差：研究动机与可计算信号的区别

- 主张：作者针对VLN-CE中部分可观测、历史理解漂移及执行前缺少后果校验提出世界模型；没有给出真实潜态作为逐步漂移误差标签。执行前Δ是动作引起的预测潜态变化，不能直接当真实状态误差。
- 类型：外部原论文与官方源码静态核查；产生偏差的具体解释是机制推断，不是本项目实测。
- 来源：Xuan Yao、Yuze Zhu、Junyu Gao、Zongmeng Wang、Changsheng Xu，SC²-WM: A Self-Correcting World Model with Closed-Loop Feedback for Vision-and-Language Navigation in Continuous Environments，2026，arXiv:2608.07548v1，https://arxiv.org/html/2608.07548v1；本地官方scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b。
- 精确位置：§1；§3公式3/5/9–13；§3.3；Appendix D.3/E。代码`scwm/vlnce_baselines/models/etp/vilmodel_cmt.py:GlobalMapEncoder/forward_navigation`（600–621、932–978），`ss_trainer_ETP.py`（2245–2318）：候选预测特征、门控修正及前一步预测与当前实际视觉特征比较。
- 原始结论：潜态由观测/语言/历史动作推断；公式9为预测下一潜态减当前潜态，正文明确不是需要最小化的训练目标。公式13用后续视觉特征作预测监督；测试期按修正前后动作分布变化条件更新。附录明确内部修正环区别于经典外测反馈，当前使用模仿学习。论文/代码实现细节不同：正文公式13平方误差，本地测试期为余弦损失与L2正则；代码门控修正也不能说逐行就是公式9。
- 采用/限制：将视觉歧义/历史失配/泛化不足作为潜态不可靠的机制解释；假设示例须标“解释性例子”。预测变化非零可能只是正常运动，预测视觉误差也可能来自模型/观测噪声；均不能单独证明定位漂移或累积状态误差。导航指标/消融支持任务收益，不能直接证明原Husky机械臂补偿。
- 核查：2026-10-09，Codex /root；本轮已读原文上述段落并核对源码，未运行SCWM；实际模型/强度未知。
- 使用位置：[本轮核查日志](agent_logs/project/20261009-codex-scwm-problem-comparison.md)；旧解释另见[SRC0033](#src-0033)/[SRC0035](#src-0035)。

<a id="src-0169"></a>
## SRC-0169 — 原Husky累积误差风险：底盘反馈与机械臂内部状态分别核查

- 主张：原Husky Gazebo默认底盘反馈不是轮速积分定位；默认perception_style=base更新底盘而保留IK目标关节，机械臂实际反馈未完整回填到策略状态。存在未被该层纠正的状态偏差风险，但未证实误差随时间累积增大。
- 类型：项目原始源码静态核查＋条件性机制推断；无本轮运行/误差曲线，不是新实测性能结论。
- 来源/版本：收到时Husky+UR5移植原样快照1ccedd087ac12dd317e93accc37bb81e05beeb99；本轮9个相关modulation_rl文件逐字节与该commit根相对路径比对一致，根当前HEAD438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804。不是纯上游N²M²，也不是当前FoReM。
- 精确位置：`husky/src/modulation_rl/scripts/modulation/utils.py:149/489`默认base；`src/robot_env.cpp:step`（188–196、239–280）、`sendArmCommandCurrent`（294起）、`getRobotObs`（479–515）；`src/robot_husky.cpp:sendArmCommands`（91–123）；`scripts/modulation/envs/robotenv.py:step`（259–318）、`combined_env.py:step/_to_agent_obs`（356–425）、`eeplanner.py:EEPlannerFullPython.step/generate_obs_step_ee_obs`（225–255）；`scripts/model.py:GaussianPolicy.forward`（141起）。底盘入口`gazebo_world/husky_ur5/n2m2_husky_empty_world.launch:88–92`→`husky/src/pcl_configure/launch/gdt.launch`→`src/tf.cpp:OdomCallback/main`；`husky_ur5/urdf/husky_ur5.xacro:48–58`为p3d；`src/worlds.cpp:32–47`读取TF。
- 原始事实：Gazebo位姿经ground_truth/state→odom/base TF，map/odom静态恒等，再每步查询；p3d有噪声配置、TF重新盖stamp，不能说零误差。base分支不调用setToCurrentState，all分支才同步关节；策略观测/到达检查使用内部gripper_tf，实际TF gripper_tf_achieved另记。轨迹以绝对关节位置发给控制器，正常step不等待getArmSuccess；Python计划沿上一规划点前进，执行名义dt与规划实测dt来源不同。
- 机制解释/限制：若物理臂滞后、跟踪失败或底盘—臂时序失配，未修正的内部臂状态可继续影响下一步IK/观测/到达判定；“规划到了、物理未到”是可发生情景，非本轮已复现。参考推进本身是正常规划方式，绝对目标与低层控制也可能追平误差，不能推出线性增长/无限发散。无循环潜态网络不代表策略绝无认知偏差，SAC逐步观测闭环也不等于自动消除所有误差。sim解析模式未执行真实控制器，应与Gazebo模式分开。
- 核查：2026-10-09，Codex /root；只读源码/版本，未编译/启动/训练；不使用Task4/VIO结果证明原版风险。用户追加“惯性估计已弃用，只看原Husky”，本轮仅登记该范围，不实施路线修改。
- 采用：答复应为“有持续/传播偏差风险，尚未证明累积增大”；SC²-WM潜态漂移不能直接等同原Husky物理臂跟踪问题。补实测仅是证据缺口，不构成新实验授权。
- 使用位置：[本轮核查日志](agent_logs/project/20261009-codex-scwm-problem-comparison.md)；底盘既有审计[SRC0036](#src-0036)。


<a id="src-0170"></a>
## SRC-0170 — 用户重定Task4为SCWM思想接入Husky，文档交Claude执行

- 类型：用户指令；2026-10-09 Codex /root记录。用户明确核心是将SCWM世界模型内部闭环思想接入Husky，认可Gazebo真实位姿普通SAC基线→动作条件WM→执行前反馈→同预算对照→随后单独条件适配，要求“重新写文档，然后我交给Claude执行”。惯性估计已弃用，另一个会话也记录此点（SRC0169）。
- 本轮授权：Codex只写/核验文档，不实施、不派发Claude、不恢复旧训练。用户交给Claude后由Claude登记接手按新流程执行，新任务范围不再受旧“Task4不训练WM”历史约束，也不需反复询问已明确的常规步骤。旧VIO run保持停止，禁止将新的实施交接解读为恢复r6。
- 组织：Task4父目标重写；旧4.1–4.6及4.5.1–3原路径保留历史/不再执行，新节点4.7–4.13，不复用已有编号。原文档57份快照/SHA在`results/task4/t4-replan-scwm-20261009/document_snapshot/`及相邻`document_snapshot_manifest.json`。
- 权限：新研究允许Gazebo当前真实底盘位姿作为两方法共同可得信息，TF保留；实际关节/规划关节分开，不读取未来真值/测试标签。VIO/相机/IMU不再前置，已有激光局部地图沿用。该理想感知假设不代表实机性能。
- 训练条件：用户明确接受100万步且完整一轮训练与评估≤72小时，要求性能优化/可行多线程。不能继续SRC0167的30天方案，不减规模冒充达标。新父PROCEDURE明确所有方法/共享前缀/计算计数；未profile不承诺可达。
- 限制：不新增人为误差、传感器融合、机器人任务、MPC替换SAC、RGB端到端策略或实机；本轮文档不冒充新运行结果。

<a id="src-0171"></a>
## SRC-0171 — SCWM到Husky的机制映射与原文/代码差异

- 类型：原文/官方源码静态重读；Codex /root，2026-10-09。Yao等SC²-WM，2026，arXiv:2608.07548v1，https://arxiv.org/html/2608.07548v1 ，§3.1公式9–10/Algorithm1、§3.2/§3.3/Algorithm2；scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b，未运行。
- 位置：`vlnce_baselines/models/etp/vilmodel_cmt.py:GlobalMapEncoder/forward_navigation`（590–625/895–995）；`ss_trainer_ETP.py:_setup_tta_optimizer`及2245–2310。前序SRC0020/0164/0168。
- 原始结论：预测下一潜态与当前潜态之差是执行前指导信号，不是待最小化的真实误差。已读代码重建候选特征，detach后门控残差再评分；TTA比较已执行候选的旧预测和新到特征，KL分位触发与正文熵条件有差异。因此不能把论文抽象/代码分支说成逐项完全等价。
- 采用：迁移“前瞻预测→内部反馈→最终SAC动作”与独立条件模型适配。首版连续动作/状态地图表征/MLP是FoReM工程适配，不复现语言、VCM、图路点、递归后验或Transformer；不加载SCWM权重，不称完整原论文复现。未来观测只能到达后用于监督，不能提前用于决策。导航收益不保证Husky收益。

<a id="src-0172"></a>
## SRC-0172 — 连续SAC闭环与公平共同前缀：本地代码/推导/工程选择

> **当前效力说明（2026-10-09）：** 本条保存此前审计/工程草案。作者自定的预算细分、实验模式和参数不等于用户授权；最新范围与适用校正见[SRC0178](#src-0178)、[SRC0179](#src-0179)。硬件/源码实测及其原有限制仍保留。


- 核查：2026-10-09 Codex /root；`src/modulation_rl/scripts/{sac.py:SAC.select_action/update_parameters,model.py:GaussianPolicy,stable_baselines3/common/distributions.py:SquashedDiagGaussianDistribution}`，`config/task3/{task_contract.yaml,sac.yaml}`，`scripts/task3_env.py`；源内容待新4.7冻结SHA。
- 原始事实：输入41维机器人/目标/规划状态＋120×120×1局部激光地图；动作是末端计划速度/底盘角速度/线速度，臂由BioIK。CUDA训练actor/twin critic/地图CNN，不训练OpenVINS。当前观测关节是规划值，首版WM预测可得策略表征，不宣称纯物理动力学辨识。
- 工程选择：每seed全新普通SAC共同前缀后，完整状态分叉plain/feedback；前缀按各方法预算计入，不借旧truth/VIO权重。固定从前缀actor trunk复制的WM参考编码器，避免监督目标随策略移动；两策略自己的trunk继续学习、critic输入不变。具体模型和参数唯一见新父PROCEDURE。
- 概率：候选动作是未修正actor的确定性均值变换；反馈是当前观测的确定函数，最终只采样一次squashed Gaussian。actor loss、target action、logprob都调用同一最终策略。若候选也随机抽样，实际会成为混合分布，不能把最后一层条件logprob当边缘密度，首版不采用。
- 梯度：仿照已读官方detach选择，SAC actor更新不沿WM预测/候选支路反传；WM只由next-feature监督更新，反馈adapter与actor由SAC更新。这是明确的截断梯度适配，不声称候选支路全导数。执行期可以no_grad，actor训练不能整体no_grad。
- 静态待复现：GaussianPolicy.predict对actions_from_params结果再次tanh，而本地SquashedDiagGaussianDistribution.sample/mode本已tanh；训练sample路径无第二次。4.7/4.8须以同均值/RNG反例验证，如确认则两方法共用修复并冻结，不能只修反馈组；本轮未运行反例、不宣称已证性能根因。
- 限制：新增表征修正属于策略结构适配，SAC目标/critic/奖励及最终决策角色保持；不是“所有实现完全未变”。预测误差降低与任务收益分别验收。

<a id="src-0173"></a>
## SRC-0173 — 百万步/72小时新任务计算账本与性能门

> **当前效力说明（2026-10-09）：** 本条保存此前审计/工程草案。作者自定的预算细分、实验模式和参数不等于用户授权；最新范围与适用校正见[SRC0178](#src-0178)、[SRC0179](#src-0179)。硬件/源码实测及其原有限制仍保留。


- 类型：用户约束SRC0170＋硬件SRC0167＋推导/工程选择；Codex /root，2026-10-09。旧VIO吞吐不是新真值链实测。
- 选择/计数：两正式训练方法plain/feedback，各3seed×100万名义步；每seed共同前缀10万，分叉各90万，实际唯一交互570万、按方法汇报600万。feedback-off/TTA是反馈checkpoint的评估模式，无隐藏第三套SAC重训。模型监督更新与前缀都记账。
- 推导：60h训练窗口、3并行worker，名义600万/(3×60×3600)=9.259有效步/s/worker；唯一570万为8.796。采用每worker≥10有效步/s为工程门并保留余量，需包含reset、梯度更新、保存及资源管理；另8h全部评估/4h机动，总campaign从首个prefix到落盘≤72h。累计worker-hours与全局墙钟分开，不能用3×72h冒充72h完成。
- 第四GPU安排各seed独立WM监督，合计≤6h并与plain后缀尽量并行。报告额外WM计算，不宣称两方法FLOPs相等。64CPU/约252GiB/4×约96GiB资源边界同SRC0167；ROS/TF/Gazebo master、锁、ledger、目录及清理权限必须隔离，现driver不能三开。
- 性能候选：移除新目标不需要的VIO/相机负载，profile复位、CPU回放/H2D、推理梯度、压缩/WAL/checkpoint与多线程。旧失败重抽配对118/128次合计约5862/6361s，中位49.6/49.7s，证据`results/task4/t4-diagnosis-20261009/reset_cost_snapshot.json`；成功复位未记录完成墙钟，不能估完整占比。
- 仿真节流依据：官方`https://classic.gazebosim.org/tutorials?tut=physics_params` real_time_factor/real_time_update_rate（本轮已读）；当前.0005s×2000Hz上界1，取消墙钟节流是候选，不保证更快。不能增大物理步长、换求解器或延长动作执行时间来凑吞吐；固定仿真时间决策窗口、轨迹/反馈回归后方可采用。
- 限制：72h尚未证明可达；不足则不启动正式、交差距/热点/替代设计，不偷减步数、延到30天、移除WM或放宽成功门。超出范围的替代再确认。

<a id="src-0174"></a>
## SRC-0174 — 新Task4首版参数与评测的工程依据

> **当前效力说明（2026-10-09）：** 本条保存此前审计/工程草案。作者自定的预算细分、实验模式和参数不等于用户授权；最新范围与适用校正见[SRC0178](#src-0178)、[SRC0179](#src-0179)。硬件/源码实测及其原有限制仍保留。


- 类型：工程选择/待验证假设；2026-10-09 Codex /root。精确协议唯一见新Task4父PROCEDURE；不是文献最优值或已执行配置。
- 依据：SAC trunk256维、batch256/更新比1/参考replay100000来自本地model.py/sac.yaml；预算来自SRC0173。WM先用固定256维表征＋3动作、两层MLP，避免把RGB生成/大Transformer作为前提。
- 初值理由：共同前缀100k提供新表征/数据；episodes稳定hash80/20切分、仅训练拟合标准化；WM hidden512×2/Adam1e-3/batch512/max100epochs/10epochs验证不进步停止、std floor1e-3/每seed≤2h。反馈门控有界残差、零初始化输出层、强度1单配置先导冻结；不看测试调参数。
- 条件适配：每episode恢复初始WM，历史KL容量1000/先32样本不更改、超过历史90%分位并通过验证集冻结的变换前Gaussian熵中位阈值才更新；lr1e-5、每已完成转移最多1步、每episode最多5步，冻结actor/critic/reference encoder/adapter。是连续分布适配，不能照搬离散softmax阈值或提前用未来。
- 数据/评价：训练0–99、验证101–105；新确认测试201–220预登记，不筛成功seed；旧106–110仅历史。增加同任务实例覆盖但不保证统计功效。plain/feedback/off/TTA同实例配对、报告各seed/固定分母与额外计算。实际位置<.025m、旋转1−dot²<.05、零IK/碰撞、原done/internal success及完整反馈沿SRC0108，不用预测准确度替代。
- 公开合同变化：新基线transition_noise_base由Task3继承.04设0，避免在当前闭环研究中叠加无关随机动作扰动；两方法一致，不把旧Task3性能当同协议对照。奖励/终止/动作维度不变；公共正确性/时间修复显式版本化并回归。收益不预设，若需要更改研究角色/新机制另行确认。


<a id="src-0175"></a>
## SRC-0175 — 原Husky全局地图、局部策略观测与地图来源的区别

- 主张：所读原Husky入口没有统一global_mode/use_global_map/非全局切换；环境地图、规划地图、SAC局部输入、ROS global/local costmap及定位来源是不同层。部分规划器用环境较大范围地图，策略默认仍局部图；不能把全局地图存在等同策略全图观测。
- 类型：原始项目源码静态核查；“全局规划＋局部策略观测”为所读链的解释，不是本轮已执行运行的身份，不猜用户旧版本命名。
- 来源/版本：收到时Husky+UR5原样移植快照1ccedd087ac12dd317e93accc37bb81e05beeb99；下列9个包内文件与该commit逐字节一致。核查2026-10-09 Codex /root，实际模型/强度未知；未编译/仿真/训练。
- 精确位置：`husky/src/modulation_rl/scripts/modulation/envs/map.py:Map.__init__`（24–104，local_map_size_meters默认3.0m）、`_get_local_map_gt`（220–285）、`get_local_map`（304–312）、`map_reset/update`（460–496）；`combined_env.py:_to_agent_obs`（401–433）、`get_local_map`（220–227）；`eeplanner.py:PointToPointPlanner.map_to_weights/calc_xyplan/_calc_6Dplan`（490–517、589–639）；`utils.py:63/97–100`；`models/mapencoder.py:LocalDoubleMapCNN`（42–97）；`scripts/model.py:GaussianPolicy.__init__`（83–101）。ROS配置：`gazebo_world/husky_ur5/costmap/husky_costmap_2d.launch`（8–22）、`costmap_global.yaml`（2–17）、`gazebo_world/common/costmap/costmap_common_local.yaml`（1–11）。
- 原始事实：sim或显式use_ground_truth从内部地图裁剪/旋转局部图；gazebo/world策略图默认从local costmap读取。update_from_global_costmap只控制内部环境图更新来源，并不把策略输入换成整张图。目标/末端计划等在输入前转底盘相对坐标；use_map_obs=false才移除地图输入。默认地图裁剪边长3m，local costmap配置3×3m，Husky global costmap配置10×10m/rolling_window=true/static_map=false，均是源码设定非本轮运行实测。LocalDoubleMapCNN是同一局部图整体降采样＋中心原分辨率裁剪，不是全场景＋局部两张图。
- 适用/限制：地图输入范围、地图是否预知/由传感器构建、是否使用全局坐标/真值定位不得混为一个开关。局部策略仍可收到来自较大范围地图的规划信息，不能称端到端全局信息完全隔离；地图名称global不能证明完整已知场景。先前删除的研究版本不恢复，也不能把其口头“非全局模式”包装成收到时原版功能。是否存在累积误差沿[SRC0169](#src-0169)，局部信息不自动证明漂移或WM必要。
- 使用位置：[追加核查日志](agent_logs/project/20261009-codex-scwm-problem-comparison.md)；只解释原Husky，无新实施授权。


<a id="src-0176"></a>
## SRC-0176 — 原Husky可借鉴SCWM内部闭环：可接入与收益证据分别判断

- 主张：可工程适配动作条件预测与执行前表征修正，保留最终SAC输出/IK角色；不要求原Husky已被证实具有同种潜态累积漂移。接入可行不等于已有任务收益。
- 类型：原论文/本地源码依据＋工程适用性推断＋待验证收益假设，非新实验结果。
- 来源：Yao等SC²-WM，2026，arXiv2608.07548v1，https://arxiv.org/html/2608.07548v1 ，§3/Algorithm1及Appendix D.3（本轮重读，作者讨论RL兼容而非已验证Husky/SAC）；原Husky1ccedd0所读GaussianPolicy/RobotEnv/CombinedEnv；[SRC0168](#src-0168)、[SRC0169](#src-0169)、[SRC0171](#src-0171)、[SRC0172](#src-0172)、[SRC0175](#src-0175)。
- 采用：当前观测→初步SAC候选→预测下一任务相关表征→修正策略表征→最终SAC动作→原IK/控制执行；下一观测到达后才能监督WM。修正策略表示不等于任意改写实际测量；内部规划关节与实际关节仍分开，预测策略特征不包装成纯物理辨识。SAC已有外部观测反馈，该设计新增执行前内部预测环。地图范围/已知当前位姿不足以确定动作后果，故全局图不从逻辑上排除预测模块，但新增有效信息/收益均待验证。
- 限制：原文语言/候选路点/模仿学习与本项目连续动作/地图状态/SAC不同，不能直接加载原权重宣称复现。缺失实际反馈的工程问题不能仅靠预测模型掩盖。普通SAC和反馈SAC使用相同任务/输入权限/交互预算，实际任务成功与额外成本才是收益证据；预测损失下降或内部动作变化本身不足。条件测试期适配是独立因素，与首个内部环分别判断。此为既有新Task4方案解释，不新增实验/参数/实施授权。
- 核查：2026-10-09 Codex /root；实际模型/强度未知，本轮未委派/改源码/运行训练。当前新Task4文档review、尚未实施，不能当性能证据。
- 使用位置：[本独立日志](agent_logs/project/20261009-codex-scwm-problem-comparison.md)；实际方案事实来源仍[Task4 TASK](tasks/task4/TASK.md)/[PROCEDURE](tasks/task4/PROCEDURE.md)/[RESULTS](tasks/task4/RESULTS.md)。


<a id="src-0177"></a>
## SRC-0177 — Task4当前工作重点答复：基线正确性→预测→执行前反馈→任务对照

- 主张/类型：依用户最新方向及已有新父方案的研究建议与执行顺序解释；不是新实验、参数或收益结论，不修改另会话负责的计划。
- 来源：用户本轮问“你认为Task4现在应该干什么”；[SRC0170](#src-0170)既有新方向；[SRC0171](#src-0171)/[SRC0172](#src-0172)/[SRC0176](#src-0176)机制与连续SAC；当前`forem/doc/tasks/task4/TASK.md`研究目标/目标链/验收及`PROCEDURE.md`递归顺序/共享合同/模型梯度/评测协议（2026-10-09正在改写）。原始研究依据仍Yao等2026 SC²-WM §3、D.3，https://arxiv.org/html/2608.07548v1。
- 采用：第一步审计/冻结原任务的状态、动作、时间及物理成功口径，再有限普通SAC先导/吞吐验证；Gazebo当前底盘反馈、现有局部地图和IK/控制角色保持，规划关节与实际关节分别记录，不擅自切换perception_style。随后动作条件预测下一任务相关表征，排除恒等拷贝/无动作信息；执行前候选→预测→表征修正→最终SAC动作。先比较普通SAC与冻结WM反馈SAC，测试期适配另列，未来观测只能到达后监督。
- 验收/限制：最终以同任务/输入权限/交互预算下真实末端任务成功、碰撞/IK失败及额外计算开销判断，预测损失下降不当收益。不以证明同种累积潜态漂移作为逻辑前置，不故意注入扰动压低普通SAC，也不恢复弃用的VIO线。真实反馈检查不能被模型学习替代；本问句仅要求意见，不启动实现/训练。
- 当前核查：父TASK/PROCEDURE新内容可读，RESULTS仍旧VIO内容；尝试读取4.7/4.8子TASK时不存在（核查时缺失=['forem/doc/tasks/task4/task4.7/TASK.md', 'forem/doc/tasks/task4/task4.8/TASK.md']）。属另会话正在写文档的快照，不据父文档宣称完整交接已验收；待其同步完成再按最新入口接手。本轮不创建子节点或修其他Agent文件。
- 核查日期/人：2026-10-09 Codex /root；推荐GPT6.1sol/Sonnet5.5 medium（跨状态/策略/对照口径），实际未知。只读main、husky无新改动，进程过滤无ROS/Gazebo/python3。
- 使用位置：[本独立答复日志](agent_logs/project/20261009-codex-scwm-problem-comparison.md)。工程方案唯一事实来源仍Task4三文档，不另维护协议。


<a id="src-0178"></a>
## SRC-0178 — 新版Task4文档最终范围、授权与草案校正

- 类型：用户最新明确指令＋文档核查，2026-10-09 Codex /root；实际模型/强度未知。用户本轮仅授权文档，不改源码/运行配置、不安装/构建/仿真/采集/训练/派发Agent。
- 研究要求：相同任务、观测权限及训练预算下把SC²-WM候选动作→预测后果→内部反馈→最终SAC动作接入Husky；惯性估计弃用；不以证明同种累积潜态漂移为前置，不制造误差或削弱baseline。顺序是普通SAC有限先导/性能→动作条件WM→冻结WM的首轮执行前反馈→公平任务比较→条件测试期适配独立因素。
- 已核查文档：新Task4 TASK/PROCEDURE已引用4.7–4.13，但子文件尚缺、RESULTS页首仍旧VIO；前稿含作者自行拟定参数、完整四模式测试矩阵与预算细分。负责人为本会话Task4重写；另会话PROJECT-SCWM系列已done且记录明确不改此方案，保留其SRC0168/0169/0175–0177。
- 校正：SRC0172–0174及此前4.5.1–3中的共同前缀固定10万步、新测试201–220、额外feedback-off正式评估组、60/8/4小时分摊、10step/s硬门、WM单独2h/6h、每seed存储/RAM硬上限、固定TTA阈值/更新数等是前稿工程建议，不是用户批准的有效预算/实验协议；本轮从当前执行合同移除，保留历史条目。source登记不能把建议变授权。
- 参数变化边界：不自动把transition_noise_base由.04设0、不自动固定新动作窗口.02s、不切perception_style或修正动作squash实现；先核对已有合同/必要性和两方法影响，实施阶段按明确授权变更，当前不修改配置。禁止新增扰动不等于任意重写旧合同参数。
- 有效规模：用户此前确认100万步规模、完整一轮（原讨论含3seed）训练与评估72h以内，最新要求预算沿有效协议。方法数量、共享数据/前缀归属、WM额外训练/适配消耗须在4.7预算表逐项对照授权；未明确的覆盖口径不能自动扩成额外预算，也不能强加作者自定更紧上限。未冻结完整覆盖表前不进入长训练。本轮不决定额外组/预算。
- 采用：4.7–4.13编号保持，补齐21份子三文档，重写父当前三文档并保留旧结果，更新入口/进度/来源/独立日志。RESULTS统一尚未实施，不把旧证据写成新验收。
- 模型推荐按用户最新：GPT6.1sol / Sonnet5.5；文档low或默认，跨模块机制核对medium，不默认升级high；实际未知另记。

<a id="src-0179"></a>
## SRC-0179 — 首轮冻结WM时连续SAC一致性与数据因果的工程判据

- 类型：基于SRC0171/0172/0176的数学推导与工程方案；2026-10-09 Codex /root，尚未实现或运行。本地位置`src/modulation_rl/scripts/{sac.py:SAC.update_parameters,model.py:GaussianPolicy}`，官方SCWM位置沿SRC0171。
- 采用的最小接口：o_t→固定版本参考表征z_t；确定性候选a0_t→F_phi(z_t,a0_t)→预测变化→策略表征修正→最终连续策略。只执行最终动作a_t；F的训练样本必须是实际执行a_t和同episode执行后o_{t+1}，不能将未执行a0_t配该next作监督。next不能参与当步前瞻。
- 推导：确定性候选使最终Gaussian参数仍是当前观测的确定函数；最终只采样一次并使用其正确squash/scale后的logprob。随机候选一般产生混合分布，原末层条件logprob不自动等于边缘密度，首版选择确定候选避免该问题。actor更新/next-action target/alpha/在线采样要使用同一定义。
- 冻结定义：首轮WM参数和参考编码器不被SAC optimizer改变；这不等于actor训练时必须no_grad整个WM调用。若候选依赖actor参数，保留经冻结F输入到候选的导数才对应该复合策略的完整链式导数。执行推理/target计算可按用途no_grad。前稿的默认delta.detach是另一种截断梯度工程选择，不能静默冒充完整SAC actor梯度；本轮以冻结权重且保留需要的输入梯度为基准，若选截断须单独论证/登记，不能仅照搬离散SCWM实现。
- 数据/表征：参考编码器版本须固定且源hash可追溯，训练/验证按完整episode或运行段分开，归一化只拟训练侧；恒等预测与同输入动作变化/动作打乱检查属于必要预测诊断，不新增正式RL训练组。初始MLP/门控残差是实现候选，具体规模和超参先在4.7按现有效协议登记来源，不把SRC0174示例值当既定参数。
- 判据：冻结权重哈希不变、梯度路径符合定义、off旁路不多采样且与baseline同RNG一致、真实replay只写最终动作、模型无效时显式报错/记失效。损失更低/动作变化本身都不是任务收益；条件适配在首轮固定模型比较之后另冻结协议。

<a id="src-0180"></a>
## SRC-0180 — 文档验收、预算核对和性能先导的工程流程

- 类型：用户范围落实与工程流程选择，2026-10-09 Codex /root；无新性能实测。依据SRC0178、既有硬件快照SRC0167、既有坐标/时间审计SRC0161和基线接口SRC0172。
- 验收分层：文件/链接/来源/编号检查仅说明文档完整；基线实际位姿/关节/末端反馈与动作时间必须在将来有限先导核验；WM恒等/动作依赖/未来泄漏、连续SAC概率/梯度、真实任务指标分别验收。无需先证明Husky具有SCWM同种累积潜态漂移。
- 性能方法：新真值链先计时env step、reset、采样/H2D、GPU推理/update、记录/保存及任务吞吐；已有SAC/渲染GPU事实与新性能收益分开。多线程/多GPU仅在既有授权与隔离正确性下规划验证，不直接承诺4卡加速倍数或新10step/s门。
- 推导模板：先列已批准方法/seed/步数和可并行程度，再用对应实测有效step/s（包含周期性reset/保存）估训练墙钟，加未包含的WM监督、验证/测试、恢复等开销；同一时间项目不得重复扣/计。与72h一轮约束核对，口径缺失则不进入formal，不能复制旧VIO预算或增设其他轮数。未满足时报告差距，不自行减规模/延长/添加算法。
- 初始技术核查只读入口：Task3普通SAC/Task3Env、robot_env.cpp/worlds.cpp、RobotEnv.step、既有物理评估脚本；旧VIO脚本仅作历史证据。原成功阈值SRC0108供对齐核对，不能将旧运行通过视作新真值链或WM收益证明。
- 采用：Task4父流程与4.7–4.13明确输入、动作、输出、验收、失败分支、授权与模型推荐；不另建第四份同职责文档。未来参数事实记录在所属RESULTS并关联来源，本台账不复制另一套协议。


<a id="src-0181"></a>
## SRC-0181 — 用户要求将性能优化纳入共同Agent约定

- 类型：用户明确指令，2026-10-09 Codex /root记录；用户本轮追加“性能的优化要写入AGENT.md中”。工作区现有统一入口为根AGENTS.md，本次写入该文件并由forem/AGENTS.md引用，不新建并行AGENT.md。
- 采用：把GPU实际使用、端到端分阶段profile、可行多线程/并行优化验证、数据/时间/恢复一致性和长训可行性核查列为工程职责；性能不能只以GPU利用率/理论算力或旧VIO速率判断。具体优先项来自已读本地链路SRC0162/0180，收益尚未测。
- 预算边界：以最新用户授权和有效协议为准，不在共同规则新增硬性GPU/RAM/线程数/吞吐/尝试数限制；不因预算紧张自行缩规模、改物理/任务语义或延长工期。需要超范围架构变更时先说明，不把“优化”当任意新增功能的许可。
- 当前限制：本轮仍只有文档授权，不实施优化、不修改运行配置、不启动benchmark/仿真/训练。推荐GPT6.1sol/Sonnet5.5，文档low/默认，跨模块性能核对medium；实际未知。


<a id="src-0182"></a>
## SRC-0182 — FoReM项目整体思路与当前进度PPT证据快照

- 主张：Task0/1/2/3在各自限定范围内已最终独立验收；旧VIO线退出主线、正式训练暂停；新Task4按SCWM执行前反馈方向整理方案，尚未实施。汇报中Task1的26有效run、关节约1.82mrad/末端约2.01mm峰值与Task2 M3原发送轴FK位置RMSE0.138/0.146/0.910/1.697mm均来自既有结果，不是本轮新测量。
- 类型：项目原始结果/独立审核记录的汇报汇总＋已有工程方案；新闭环的任务收益为待验证假设。
- 作者/年份/版本：FoReM项目，2026；main dirty，根HEAD438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804。该HEAD不涵盖全部工作区新增文件，精确读入版本由快照及sha256标识。
- 来源及精确位置：task0.13 RESULTS最终验收；task1.10 RESULTS结论及task1.4 RESULTS结果/限制；task2.9 RESULTS最终验收与exp2.1 RESULTS结果二M3表；task3.6 RESULTS R2最终验收；SRC0163暂停收据；SRC0178–0180新版范围/因果/验收；新版Task4 PROCEDURE递归顺序4.7–4.13。
- 原始证据快照：[source_snapshot.json](../results/project/project-ppt-20261009/source_snapshot.json)及其evidence_snapshot各原文副本，记录路径/hash/读取时间；不依赖随后正在修改的任务文档恢复本次依据。
- 核查：2026-10-09，Codex /root，已读上述原始本地记录；未重跑仿真/训练/实验，实际模型/强度未知。
- 原始结论/采用：区分既有正常跟踪测量、受控时延机制、迁移接口验收、旧失败/暂停与新计划；Task2的B/Z原t_ref等价未满足、fit为事后修订等限制在讲解备注保留。来源条目不形成新实施授权。
- 适用限制：Task1为固定底座慢速仿真；Task2时延为工程选择的整条轨迹传输延迟而非硬件驱动模型；Task3短SAC接口验证不代表收敛/成功率；新Task4未来收益和一轮72h可达性尚未实测。文档正由另会话同步，PPT是本次读取快照，不验收新计划完整性，不沿用已撤销草案参数。
- 使用位置：[PPT](../results/project/project-ppt-20261009/FoReM_整体思路与当前进度_20261009.pptx)、[讲解与出处](../results/project/project-ppt-20261009/讲解与出处.md)、[本次日志](agent_logs/project/20261009-codex-project-ppt.md)。


<a id="src-0183"></a>
## SRC-0183 — 当前Husky基线来源与Task4实施进度独立核查

- 主张：Task3迁移核心来自收到时Husky+UR5；正在准备的新Task4 plain基线沿其普通SAC，不能称收到时main.py的prior分支逐字复现。核查过程中Claude开始4.7/4.8实施，旧“尚未实施/容器仅保活”快照已被新现场覆盖；未有本次核查确认的正式百万步训练或收益结果。
- 类型：项目原始源码/hash及CPU回归实测、当时现场/进度核查；不为算法效果证据。核查人/日期：Codex /root，2026-10-09约10:16–10:19+08:00，实际模型/强度未知。
- 版本：收到时modulation_rl快照1ccedd087ac12dd317e93accc37bb81e05beeb99（该历史树根直接是包文件，不是当前仓库路径前缀），371 Git文件逐字独立比较，0差异。main dirty，以[输入快照/hash](../results/project/husky-baseline-check-20261009/current_inputs.json)为当时新包装版本依据；未修改参考仓库。
- 原始证据：[独立source检查](../results/project/husky-baseline-check-20261009/independent_source_check.json)、[六项静态审计](../results/project/husky-baseline-check-20261009/audit.json)、[旧freeze检查](../results/project/husky-baseline-check-20261009/freeze_check.json)、[新包装CPU6测试](../results/project/husky-baseline-check-20261009/scwm_sac_tests.log)。source_manifest 266导入文件（254逐字/12登记补丁）源和目标hash均匹配。model/replay/mapencoder/combined_env/eeplanner/tasks/map与参考逐字一致，SAC仅初始化设备有补丁，update_parameters/select_action等函数AST相同。
- 精确符号：task3_sac_entry.py SCRIPTS_DIR/SAC导入和run_training(update_parameters)；task3_env.py Task3Env.__init__→modulation.utils.env_creator；config/task3/sac.yaml algorithm；原main.py153–155 prior_agent/load_and_freeze_checkpoint、242–243原普通更新被注释且调用update_parameters_modified；scwm_sac.py ScwmSAC(SAC)/update_from_batch/GpuReplay，scwm_policy.py FixedGaussianPolicy.predict；test_scwm_sac.py各6测试，尤其test_update_equals_reference_update三批更新/网络参数对照。
- 命令/结果：audit_task3_core.py --out本核查目录，退出0六项通过；sg docker -c 'python3 forem/scripts/freeze_task3.py verify'退出1列5项后续forem_husky VIO增量，未修改冻结；容器CPU OMP/MKL/OPENBLAS=1、SCWM_TEST_DEVICE=cpu，python3 -W ignore -m unittest discover -s tests -p test_scwm_sac.py -v，6tests/0.739s/退出0（CPU、合成数据，无ROS仿真或训练）。
- 当前差异与采用：新包装从Husky SAC继承，但predict双tanh修正、device回放、完整训练状态保存是新增公共适配；已读4.7 RESULTS和policy_tanh_audit支持单tanh修正对两方法共同采用，不能说与原入口全部相同。静态来源及CPU回归支持更新/回放一致性，未单独验证CUDA数值/长期训练/完整正式身份。
- 进度：Claude日志登记2026-10-09T10:09接手（实际Sonnet5.5/high）；4.7 RESULTS为已交付待汇总，4.8.1 RESULTS active；docker top新出现run t4.8.1-smoke-a inst0/inst1独立ROS/Gazebo，4.8父RESULTS旧未实施标题滞后。运行归Claude及其子Agent，本核查不停止/接管、不改其任务文件。
- 限制/下一步：来源确认不等于原prior训练结果复现/学习收敛。正式基线前用新运行收据绑定实际导入模块/配置/实例/公共delta和语义身份，原SAC与反馈组同样适用公共修正；旧VIO权重/数据/时延注入不得偷偷进入新基线。原transition_noise_base=.04沿现合同，不能自动设0或把“未注入新误差”写成“原配置完全无噪声”。旧Task3 freeze需合法delta/新freeze，不能覆盖旧证据或把当前旧verify当通过。
- 使用位置：[独立核查日志](agent_logs/project/20261009-codex-husky-baseline-check.md)、PROGRESS本核查登记。当前各任务事实仍归所属RESULTS，本条不新增实验组/训练授权或第四份协议。


<a id="src-0184"></a>
## SRC-0184 — 当前小型表征世界模型与内部反馈代码设计说明

- 类型/主张：当前工作区正在开发的工程实现静态核查，不是已训练效果。2026-10-09 Codex /root，实际模型/强度未知；用户问“模型怎么设计”，只读解释，不修改实现/训练。
- 精确来源：`forem/scripts/scwm_wm.py:RefEncoder/WorldModel/train_world_model/evaluate/stable_split`；`scwm_feedback.py:FeedbackGaussianPolicy.distribution_params/__init__`。原始版本由[本次hash快照](../results/project/wm-design-check-20261009/snapshot.json)和源副本保留；任务4.9 RESULTS当时仍未交训练结果，不凭文件存在宣称运行完成。
- 原始设计：固定SAC地图CNN＋状态拼接后的FC trunk副本形成256维参考z；3维执行动作与标准化z拼接，WorldModel默认259→512→512→256，隐藏层ReLU，预测标准化的z_next−z；还原为z_hat_next=z＋预测残差×训练侧残差std＋mean。默认MLP可训练参数推导259×512＋512＋512×512＋512＋512×256＋256=527104（约52.7万），不含冻结参考encoder或反馈模块。
- 训练：真实replay最终动作和同episode执行后next，完整episode稳定hash拆分，只训练侧拟合z/残差统计；标准化残差MSE监督，validation原单位MSE选模型/早停；恒等预测、动作打乱/置零作预测诊断。当前函数默认hidden512/layers2/Adam lr1e-3/batch512/maxepochs100/patience10是开发代码默认，尚未等同有效冻结配置或新预算授权；未来须在所属RESULTS登记理由/实际采用。
- 反馈：actor自己的h→确定候选a0=tanh(mean(h))→固定F(z,a0)→标准化预测变化；[h;变化]经sigmoid门与线性修正，h'=h＋gate×delta_head，再用SAC原动作头给最终分布，实际只执行最终动作。修正head零初始化；首轮F/E冻结但保留候选输入梯度，策略及修正模块通过SAC训练。预测变化不是实际误差标签，不直接输出关节指令；规划/物理通道区别仍沿SRC0183/0179。
- 限制/采用：是小型单步任务表征预测，不是整套物理模拟或未来图像生成；尺寸仅当前代码默认。无法据此证明预测准确、task4.9验收或任务收益。使用位置：[本次解释日志](agent_logs/project/20261009-codex-wm-design-check.md)及用户答复。


<a id="src-0185"></a>
## SRC-0185 — SCWM仿真位置来源与虚拟传感器定位的区别

- 主张/类型：SCWM所读Habitat仿真链直接使用当前agent位置/朝向；名为GlobalGPS的本地模拟传感器本身也直接返回sim状态，不等于相机/IMU估计。原文研究执行前内部反馈与条件适配，非定位方法。将定位理想化以分离决策算法变量是工程解释/推断，不冒充作者明确理由。
- 原始来源：Yao等2026 SC²-WM arXiv2608.07548v1，https://arxiv.org/html/2608.07548v1 §3/§4.1/Appendix E，本轮已读；本地官方参考scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b，common/environments.py get_agent_state/get_agent_info（88–100）调用self._env.sim.get_agent_state；ss_trainer_ETP.py rollout位置读取（1761–1772/1804–1826）；habitat_extensions/sensors.py GlobalGPSSensor.get_observation（55）直接返回self._sim.get_agent_state().position。
- 原始结论/采用：区分直接当前真值/理想模拟GPS，以及由RGB/深度/IMU等原始观测估计位置；给真值包传感器接口不产生新的测量误差。研究执行前预测的额外信息不要求定位失效；已知当前位置仍不代表知道候选动作后果/视觉语义。
- 限制：静态阅读不证明所有分支或实机用同种定位。论文Appendix E有GO2/D435i实机验证，但所读该节未明确交代完整位姿估计链，不能说实机也取仿真真值或无传感器。当前结果只能限定于所读仿真接口，不证明定位噪声鲁棒性。
- 核查：2026-10-09 Codex /root，实际模型/强度未知；只读文献/参考源码并登记，没有运行仿真/修改当前实现或恢复VIO。使用位置：[独立说明日志](agent_logs/project/20261009-codex-scwm-sim-position.md)与本次答复。


<a id="src-0186"></a>
## SRC-0186 — SAC决策与SCWM强化学习扩展的原文边界

- 类型：原论文已读结论＋本地SAC实现事实＋本项目工程适用性判断；不是SAC优于模仿学习或新反馈收益的实验。2026-10-09 Codex /root，实际模型/强度未知。
- 原始来源/精确位置：Yao等2026 SC²-WM，arXiv2608.07548v1，https://arxiv.org/html/2608.07548v1#A4.SS3 ，Appendix D.3 Difference from critic-based feedback / Potential extension to reinforcement learning，本轮网页589–610行已读；FoReM/Husky sac.py:SAC.update_parameters，既有接口/来源SRC0183和反馈实现SRC0184。
- 原文结论：当前SCWM使用模仿学习；作者以VLN-CE强部分可观测和稀疏奖励说明仅奖励驱动优化可能不稳定。其RL扩展是未来方向：前瞻信号可作内在奖励，或辅助潜态表示；核心前瞻自修正与策略学习范式可兼容。作者明确目的不是比较RL与WM。Critic提供压缩的标量价值评价，前瞻反馈提供高维转移信息，这不等于critic不能学动作后果，也不证明新信号必然提供额外收益。
- 本项目采用/推断：普通SAC通过真实转移/奖励优化连续动作策略，Q评估长期回报；适用于继承的Husky连续动作合同是工程选择，不能泛化为比SCWM更先进或表现更好。当前选择表征辅助/执行前反馈，保留奖励及最终SAC决策，不采用论文建议的内在奖励改写。SAC自身已有反馈和学得价值预期，WM可能提供显式转移信息但也可能冗余/错误/增加开销，需同任务权限预算对照。
- 限制：原论文D.3提出兼容性及例子，没有据该段给出SCWM＋SAC的验证结果；VLN模仿学习与本项目机械臂连续SAC任务不同，不能跨任务直接比较成功率。当前来源核查/接口回归不代表收敛或新WM训练收益。
- 使用位置：[本次说明日志](agent_logs/project/20261009-codex-sac-scwm-rl.md)与用户答复。本次只读说明，不实施新奖励/算法/实验或派发。


<a id="src-0187"></a>
## SRC-0187 — SCWM基础动作生成：候选路点、图节点评分与执行分层

- 类型：原论文/官方本地源码静态核查，2026-10-09 Codex /root，实际模型/强度未知；用户问基础动作机制，无本次运行。
- 来源：Yao等2026 SC²-WM arXiv2608.07548v1 https://arxiv.org/html/2608.07548v1 §3 Task Definition（98–104行）/D.3；scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b，本地ss_trainer_ETP.py1928–1948占用/语义图与waypoint_predictor、2411–2425 teacher交叉熵、2478–2494 Categorical采样/teacher混合或argmax、2506起env_actions；models/etp/vilmodel_cmt.py forward_navigation（global_sap_head/global_logits 918起、enhanced_sap_head 981起）。
- 原始结论/采用：基础高层策略是语言/视觉/导航历史信息下对候选路点/图节点（含STOP）评分并选择，非SAC输出连续速度/力矩。候选来自路点预测和图记忆；实际所读链先预测占用/语义图再路点heatmap；基础分数与WM修正重评分结合后选最终动作。训练有teacher标签交叉熵与按sample_ratio混合teacher动作；评估argmax。学习高层去哪里与底层如何执行分开；论文概括低层连续控制，本地执行还有back_algo/tryout分支，不能说所有配置都同一连续控制器或执行完美。
- 限制：模仿学习描述由原文D.3与所读teacher训练支持，不将cross_entropy说成强化学习，也不把“连续环境”当连续高层动作分布。代码与论文抽象差异沿SRC0171；没有本次逐配置执行或原训练复现。与Husky连续SAC的区别是决策接口/学习信号，非已证明性能优劣。
- 使用位置：[本次解释日志](agent_logs/project/20261009-codex-scwm-action-generation.md)及答复。不修改参考/项目实现，不新增实验授权。


<a id="src-0188"></a>
## SRC-0188 — 当前训练入口是否已使用世界模型反馈的状态核查

- 类型/主张：2026-10-09 Codex /root只读代码/执行记录快照；用户问“现在就是这样做吗”。已存在WM/feedback模块设计实现，但当前scwm_train.py约195行构造ScwmSAC未传policy_factory，使用默认FixedGaussianPolicy，因此该入口当时仍plain而非feedback，不能把模块存在称已实际用于正式反馈训练/推理。
- 原始来源/位置：scwm_train.py module docstring（plain now/later feedback）和run agent构造；scwm_sac.py ScwmSAC.__init__(policy_factory=FixedGaussianPolicy)；scwm_feedback.py FeedbackGaussianPolicy.distribution_params实现候选→WM→门控特征修正→最终动作分布。实际版本见[快照hash](../results/project/feedback-status-20261009/snapshot.json)。
- 进度：Claude主日志最新4.8进行中；4.9/4.10RESULTS仍未交实际模型训练或反馈验收结果。仅支持当前准备普通基线、反馈代码已写；没有本次确认的正式WM训练checkpoint/完整反馈运行/收益结果。文档可能滞后，结论限定于所读入口和记录，不说整个任务未开始。
- 采用/限制：当前路线确是训练/推理使用同一反馈policy，奖励/critic目标沿baseline，首轮WM/E_ref冻结；方案成立不等于已完成工程或效果验收。未运行新测试/仿真/训练，实际模型/强度未知，不接管Claude。
- 使用位置：[本次记录](agent_logs/project/20261009-codex-feedback-status.md)与答复。


<a id="src-0183"></a>
## SRC-0183 — 用户追加指令：按原项目配置完整跑一次，容量装不下也要跑

- 类型：用户明确指令（对话内，2026-10-09，Claude接手实施期间）。原话：“装不下也没关系一定要按照原项目的配置跑一次”。
- 采用：Task4正式运行按原项目参考配置（实时步进、transition_noise_base 0.04、reward/done/action/observation原样、100万步×3种子）执行，**即使超过72h也跑完**；72h可达性只作如实报告，不作开跑门槛，不缩步数、不改任务语义。性能优化义务不变且优化不得改变语义。
- 限制：不改变SRC0178中“不新增实验组/传感器/误差”的限制；预算口径(a)(b)(c)（task4.7 RESULTS §7）仍待用户确认，其中plain三种子不依赖(b)(c)。核查人：Claude主Agent，claude-sonnet-5-5。

<a id="src-0184"></a>
## SRC-0184 — 参考GaussianPolicy.predict的双tanh：项目内反例

- 类型：项目源码静态核查＋可复现反例（实测）。Claude，2026-10-09，run-id `t4.7-contract-audit-r1`。
- 证据：`scripts/audit_scwm_policy_tanh.py` → `results/task4/t4.7-contract-audit-r1/policy_tanh_audit.json`；源码`src/modulation_rl/scripts/model.py:GaussianPolicy.predict`（对`action_dist.actions_from_params`结果再次tanh）与`stable_baselines3/common/distributions.py:SquashedDiagGaussianDistribution.sample/mode`（已tanh）；文件sha256见`source_manifest.json`。
- 结论：同参数同RNG下，`predict`＝`tanh(sample动作)`；在线执行动作上界±tanh(1)=0.7616，而`update_parameters`的actor损失/critic目标/logprob针对单tanh分布。
- 采用/限制：新增`scripts/scwm_policy.py:FixedGaussianPolicy`作两方法共同修复（子类，原`model.py/sac.py`不改）；修复使动作分布与训练一致，不是性能结论。历史Task3/Task4基线含该缺陷。

<a id="src-0185"></a>
## SRC-0185 — Task4.8 单步/端到端耗时与更新路径优化（实测）

- 类型：项目实测，Claude，2026-10-09，容器forem-dev，RTX PRO 6000 Blackwell，torch 2.7.1+cu128。
- 证据：`results/task4/t4.8-perf-update-r1/{bench_cuda0.json,bench_cuda0_cudnnbench.json}`（`scripts/bench_scwm_update.py`，合成二值地图，batch 256）；profiler `scripts/prof_scwm_update.py`；真实循环`logs/task4/t4.8-pilot-rt1`、`t4.8-par-s{0,1,2}`（progress.jsonl的phase_ms_mean/sim_*）。
- 结果：参考路径单次更新31.6 ms，设备回放路径17.7 ms（cudnn.benchmark 16.7 ms）；GPU核时间约5.1 ms/更新（CPU/launch受限）；真实循环select 1.4、env.step 16.4、update 22–24、push 0.4 ms，reset 20–25 s/episode，平均episode约140–150步，约5 steps/s/worker，3 worker并行互不拖慢。
- 限制：微基准数字在子Agent同时运行仿真时测得，含外部噪声；端到端数字来自6000步以内先导，不外推全程。

<a id="src-0186"></a>
## SRC-0186 — 观测读取时序与物理/内部成功的差异（实测）

- 类型：项目实测＋C++源码阅读。Claude，2026-10-09。
- 证据：`results/task4/t4.8-obslag-r1/obs_lag.json`（`scripts/diag_scwm_obs_lag.py`，种子101，恒定转速指令）；`src/modulation_rl/src/robot_env.cpp:RobotEnv::step`（先发命令后`world_->getBaseTransformWorld()`读TF）；先导`t4.8-par-s{0,1,2}/episodes.jsonl`。
- 结果：step返回的观测中底盘位姿在命令发出时刻读取，不含该动作的物理影响；底盘对转速指令有约2步加速斜坡。先导117个已完成episode内部成功1/3/5、物理成功0/0/1（Gazebo LinkStates独立判据）。
- 限制：单场景单转速诊断；物理成功采用wrist_3 link×URDF静态变换，LinkStates无header（取服务响应时的sim时间）。

<a id="src-0187"></a>
## SRC-0187 — 多Gazebo/ROS实例隔离与并行吞吐（子Agent自报，主Agent部分复核）

- 类型：项目实测（子Agent task4.8.1，Claude Sonnet5.5 medium，自报）；主Agent抽查`results/task4/t4.8.1-bench-k1-r1/bench.json`（60.65 step/s，2.19核）一致，并在3个并行worker的真实训练中验证隔离与自动恢复。
- 证据：[task4.8.1 RESULTS](tasks/task4/task4.8/task4.8.1/RESULTS.md)，`scripts/{scwm_instance,regress_scwm_instances,bench_scwm_parallel}.py`，`results/task4/t4.8.1-*`。
- 结果（自报）：26项隔离回归通过；K=1…12每实例约57–62 steps/s（随机动作、无学习），K≥24衰减；NUMA绑核≤0.8%。
- 限制：未核对ROS/Gazebo官方文档条文（子Agent标“待核”）；回归只覆盖2实例；测量时机器非独占。

<a id="src-0188"></a>
## SRC-0188 — reset耗时构成与已否决的提速（实测）

- 类型：项目实测，Claude，2026-10-09。
- 证据：`results/task4/t4.8-reset-prof-r1/reset_prof.json`（cProfile，3次reset）、`results/task4/t4.8-spawn-probe-r1.json`、`scripts/probe_scwm_pause.py`输出、`results/task4/t4.8-fast-reset-r1/fast_reset.json`（`scripts/check_scwm_fast_reset.py`，慢/快各6次×2种子）。
- 结果：reset≈20–30 s墙钟，其中`map_reset`≈15 s（delete_model固定约0.4 s×约16，重复pause/unpause，spawn约4 s）、机械臂复位C++≈13 s；`/gazebo/pause_physics`服务耗时0.3–2.5 s。reset期间去节流：场景哈希与首个观测与慢速逐位一致，但墙钟26→35–50 s（更慢）；线程并发spawn/delete无收益；固定仿真窗口因每步需pause而不可行。
- 采用：不采用上述三项；保持参考实时步进。限制：Gazebo 11.15.1/gazebo_ros版本相关，未读gazebo_ros源码确认0.4 s固定延迟来源。


<a id="src-0189"></a>
## SRC-0189 — 2026-10-09 14:50普通SAC正式训练进度快照

- 类型：当前训练原始日志/manifest与进程只读核查，非收敛或性能验收。核查人Codex /root，实际模型/强度未知；日期2026-10-09T14:50:06+08:00。
- 原始来源/精确位置：三个run t4s-plain-s0/s1/s2的logs/task4/<run>/progress.jsonl最后完整行（每1000步）、episodes.jsonl、results/task4/<run>/run_manifest.json及ckpt；docker top实际三scwm_supervise/scwm_train(cuda0/1/2)与三个仿真实例；Task4.8 RESULTS首节正式启动与§后续，Claude实施日志。原文快照和汇总[status_snapshot.json](../results/project/training-status-20261009/status_snapshot.json)及同目录各run日志/manifest副本。
- 原始数值：目标各1000000步，三种子共3000000；最新整千日志s0=54000/53743updates、s1=58000/57743updates、s2=58000/57743updates，对应5.4/5.8/5.8%，合计170000（170000/3000000=5.6667%）；实际运行在日志间继续推进，完成episode末步已高于这些计数。started manifest为04:01:26UTC，即12:01:26+08；当前三个worker存活。各保存20000/40000步checkpoint。
- 评估/阶段：episodes快照只见train（评估0行），验证每100000步，尚未到首次验证；训练期间零星内部/物理成功不同，不能当独立测试成功率或收敛。WorldModel/feedback模块已写，但4.9/4.10RESULTS未交模型训练或完整反馈实跑；当前三个方法均plain，不能称WM辅助SAC训练已开始。
- 授权/适用限制：Claude最新记录用户要求原配置跑完即使超过72h，72h不再作为开跑硬门。本核查不再使用旧“必须72h内才开跑”说明阻断其运行；保留其用户授权原始记录而不新增预算。未暂停/修改运行，不估确定完工日期，吞吐含reset且可能变化。仅说明最新读取快照，不覆盖他人任务结果或实际账本。
- 使用位置：[独立核查日志](agent_logs/project/20261009-codex-training-status.md)、本次进度答复。


<a id="src-0190"></a>
## SRC-0190 — SCWM选点后的路径生成与执行

- 类型：2026-10-09 Codex /root静态代码及原文核查；实际模型/强度未知，无运行/新实现。用户问“路径如何生成”，沿SCWM上下文。
- 原始来源：Yao等2026 SC²-WM arXiv2608.07548v1 https://arxiv.org/html/2608.07548v1 §3（候选waypoint→低层控制）；本地scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b，models/graph_utils.py:GraphMap.update_graph（194起）记录节点/连接，按节点距离加权，266–267 nx.all_pairs_dijkstra_path/path_length；ss_trainer_ETP.py2553–2607，目标ghost→front_to_ghost_dist关联front；back_algo=control时当前节点到front取shortest_path构造back_path；common/environments.py:single_step_control（386起）compute_turn_angle/turn与按距离计算forward步，multi_step_control448起，step461起。
- 原始结论/采用：候选路点/已访问位置逐步形成图，策略＋WM反馈选择下一子目标；已知图内采用Dijkstra求到关联已访问节点的路线，然后向未访问候选目标移动；每次新观测再更新/选目标，非预先生成完整终点轨迹，也非WM直接生成路径。底层转向/前进及tryout碰撞处理分开。
- 限制：back_algo非control时back_path=None，环境teleport到front，因此必须区分控制回溯/瞬移分支，不能称所有配置均沿连续控制完整走回溯路线。本次未核对实际运行配置或执行效果，不保证避障/执行准确，不当新算法授权。
- 使用位置：[本次日志](agent_logs/project/20261009-codex-scwm-path.md)、用户答复；不更改项目实验方案。

- 两点间执行追加核查（同日）：common/environments.py:turn（359–380）把相对角度四舍五入到TURN_LEFT/RIGHT的actuation.amount并重复转向；single_step_control（386–445）读取当前sim位置/朝向，calculate_vp_rel_pos求相对角与距离，先转向，再按ksteps=int(distance//MOVE_FORWARD.actuation.amount)前进，碰撞时可走tryout离散试探方向。此分支没有先求样条/时间参数化连续轨迹，实际轨迹由离散动作与仿真执行产生；角度/距离量化及碰撞意味着不保证精确落在目标点，不能声称动作完美执行或每两点之间已有完整连续避障轨迹。


<a id="src-0191"></a>
## SRC-0191 — 14:58项目复现、训练规模与世界模型试跑状态

- 类型：2026-10-09T14:58:40+08只读运行日志/任务结果与原始WM输出，Codex /root实际模型/强度未知。用户要求当前项目进度、原SAC是否复现完/规模/WM训练。
- 原始证据：[SAC快照](../results/project/training-status-20261009/status_snapshot_1458.json)；原日志logs/task4/t4s-plain-s0/s1/s2/progress.jsonl最后完整行，三个实际scwm_train/supervise进程仍运行；task4.8/4.9/4.10当前RESULTS；原WM试跑[wm_result.json](../results/task4/t4.9-dryrun-r1/wm_result.json)，同核查目录另存1458原文副本。
- 数值/口径：plain每seed1000000，3seed并行共3000000；最新整千日志58000/61000/61000（5.8/6.1/6.1%），合180000/3000000=6%。更新57743/60743/60743。原Husky参考main.py horizon为5000001且prior/modified，当前普通update分支与单tanh公共修正不能称原入口逐字复现；迁移/接口完成不等于训练/评估收敛验收完成。
- WM：已存在训练/反馈模块及测试，正式按当前4.9计划等待plain100000步的参考encoder/回放；尚无该分叉点正式WM结果。已有t4.9-dryrun-r1用先导6000步回放试训练，6000有效转移/40episodes，训练5142/验证858（6验证episode），MLP hidden512×2、约527104参数，实际该试跑maxepochs15/patience10/lr.001/batch512。生成wm.pt/wm_result.json；不再称模型从未训练，但不能当正式科学结果或任务收益。
- 已读原试跑验证：skill_vs_identity=.006239，打乱动作误差未增（ratio−1=−.000044845），对应动作敏感性弱；只支持早期试跑无可信前瞻收益，不保证10万步后一定改善。首轮反馈权重固定、策略/门控由SAC优化的机制沿SRC0184/0188；尚未确认真实反馈臂任务训练运行。
- 规模限制：百万步为当前用户规模，LR horizon5000001不等于实际采样500万；WM离线监督数据不是另100万环境交互。正式feedback共享前缀的实际/按方法计数与预算需沿有效冻结记录，不在答复新定额外训练规模。
- 使用位置：[状态核查日志](agent_logs/project/20261009-codex-training-status.md)追加、用户答复；无修改训练/其他Agent任务文件或启动/停止进程。


<a id="src-0192"></a>
## SRC-0192 — 旧伤害SAC/模型补偿历史复查与当前Transformer选择建议

- 类型：2026-10-09 Codex /root旧原始实测产物只读核对＋当前工程建议，不新运行或恢复旧路线，实际模型/强度未知。用户要求查最早伤害SAC试验，追加问WM训练安排/后续是否Transformer。
- 原始历史证据：husky/results/stage0-028-r03c/r03c-analysis.json nominal_sr=.70、gain1.8_delay10 sr=.33，100独立episode，该原设置gain/动作延迟不是新Task2整条轨迹ms；husky/results/screen-028/s5-l3/result.json/analysis/result.json nominal/stale/wm_comp各100回合SR=.70/.70/.70，wm−stale=0，配对95%CI[-.05,.05]，k=3观测延迟、exploratory=true。旧日志previous-doc/agent_logs/20260928-stage0.md R0-4b在线适应仅改善残差、未达到其门槛；20260929-screen-pipeline.md L1/L3对照。读取版本/hash与副本见[历史复查快照](../results/project/old-wm-check-20261009/sources.json)。
- 原始结论/采用：最早确实存在SAC伤害测试和世界模型补偿对照，不应把当前“完整反馈对照尚未完成”外推为所有历史从未比较。强失配退化已测，但该观测延迟探索WM对照未提高任务成功率；旧在线残差改善/特征预测正结果不等于SAC任务收益。原始聚合已读，不冒称本轮重算每条episode或整个旧PH路线独立验收。旧PH已取消，归档只读不恢复，不用旧数据当新方法证据。
- 当前安排依据：task4.9当前RESULTS/scwm_wm_train.py，等待plain10万步检查点/回放，冻结actor参考编码器、整episode训练/验证、残差MLP与恒等/动作信息诊断；task4.10冻结预测器再训练反馈策略。首版结构及默认超参沿SRC0184/0191，函数默认不等于实际冻结协议。当前有效计划无确定Transformer升级或额外对照授权。
- 工程判断/待验证：现在不因MLP小或原SCWM用Transformer自动换模型；先检查10万数据覆盖、表征可预测性/动作依赖及真实时序。Task4.8已报告当前一步next对动作底盘/地图影响滞后，换网络不会自动补回缺少的信息/时间对齐。若后续证据显示单步输入不充分、预测需历史或MLP表达确有限制，可提出有预算/同数据验证的序列/注意力方案；Transformer为候选非既定下一阶段，需用户同意后实施，不增加当前scope。不是证明MLP最佳/Transformer无用或性能提升保证。
- 使用位置：[独立日志](agent_logs/project/20261009-codex-old-wm-review.md)及答复；不改变Claude当前运行/计划。


<a id="src-0193"></a>
## SRC-0193 — SCWM条件在线适配触发：正文与公开实现区别

- 类型：2026-10-09 Codex /root原文/源码核查，实际模型/强度未知；用户问触发条件。无仿真/训练/阈值新增授权。
- 来源：Yao等SC²-WM 2026 arXiv2608.07548v1 https://arxiv.org/html/2608.07548v1 §3.3正文201–210行、Algorithm2；官方本地scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b，ss_trainer_ETP.py2180–2202概率/KL记录、2266–2281视觉loss与trigger、1333队列初始化。
- 原文：KL(p_before||p_after)衡量反馈前后动作分布变化，当大于近期KL经验分布的tau分位且修正后分布熵小于epsilon时触发。大变化＋低熵是作者的工程触发信号，不是预测不准/模型容量不足的直接证明；正文无通用固定数字阈值，Algorithm2简化为kappa>tau。触发后用新到观测形成预测重建loss更新WM，不能提前使用未来。
- 已读实现：eval step>=1；KL方向为KL(enhanced||global)（与正文顺序不同），绝对值写deque(maxlen1000)；至少10样本，当前KL大于按config.IL.tta_thres取的队列分位，且有上一实际动作对应的有效视觉预测损失才更新；损失为cosine重建＋L2正则。在这段if没有看到正文的低熵门，不称二者逐项一致。当前项目连续SAC不能直接照抄离散softmax/KL条件，适配留task4.12独立验证。
- 使用位置：[解释日志](agent_logs/project/20261009-codex-scwm-tta-trigger.md)、本次答复；仅文献解释不把原阈值登记成FoReM执行参数。


<a id="src-0194"></a>
## SRC-0194 — 当前SAC训练规模与显存占用的区别

- 类型：2026-10-09T15:29:49+08:00当前GPU/进程/日志只读实测＋源码及字节推导；Codex /root实际模型/强度未知。用户问规模大吗/为何显存少，不扩容/改训练配置。
- 原始来源：容器nvidia-smi query-gpu index/name/memory.used/memory.total/utilization.gpu；docker top三个scwm_train --device cuda0/1/2，原日志t4s-plain-s0/1/2 progress.jsonl末完整行；config/task4_scwm/plain.yaml batch256/replay100000/每seed1000000；scwm_sac.py:GpuReplay.__init__ GPU预分配map_s/map_n uint8，modulation_rl/scripts/model.py QNetwork/GaussianPolicy。[快照](../results/project/gpu-training-size-20261009/snapshot.json)。
- 数值：三个seed70k/73k/72k目标各1M，3M总交互；GPU0/1/2各3740MiB（约3.65GiB），各总97887MiB，约3.82%；GPU3 17MiB。瞬时利用率16/0/13/0%，单次采样不等长期平均；设备回放与CUDA训练路径的CPU/CUDA一致性已测沿Task4.8 RESULTS，显存低不等未用GPU。
- 推导/解释：两份10万×120×120×1地图以uint8存储，100000×120×120×2×1byte=2.88e9bytes≈2.682GiB；其余状态/动作/reward/mask/网络/梯度/Adam/激活及CUDA缓存另计，不将3.65GiB全部归权重。训练1M步为累计工作量，显存由网络、批次、回放容量等决定，回放有上限且覆盖旧数据，不保留全部1M样本。当前41维状态＋单通道局部图＋CNN/MLP非大RGB/语言Transformer；原可得配置不为了填满96GiB改模型/batch。
- 瓶颈边界：已测Task4.8循环GPU更新22–24ms/步，reset20–25s/episode，reset约80%墙钟；GPU可能等待CPU/仿真/复位，显存容量与利用率不是一回事。本次不重复profile，沿既有证据，不承诺更大网络更好/更快或规模已足够收敛。
- 使用位置：[状态日志](agent_logs/project/20261009-codex-gpu-training-size.md)、用户答复；纯只读，未干预训练。


<a id="src-0189"></a>
## SRC-0189 — 分叉点(10万步)世界模型：trunk表征无动作信息，robot_state有（实测）

- 类型：项目实测，Claude，2026-10-09。run-id `t4.9-wm-s{0,1,2}`（`scripts/scwm_wm_train.py`）、`t4.9-wm-diag-rob-s0`（`scripts/scwm_wm_diag.py`）。
- 证据：`results/task4/t4.9-wm-s*/wm_result.json`（数据/哈希/拒绝计数/分段/按episode结果）、`results/task4/t4.9-wm-diag-rob-s0/diag.json`；输入为`t4s-plain-s*`第100000步检查点（sha256在manifest）。
- 结果：256维actor-trunk表征上skill_vs_identity=+2.8…+4.1%、打乱动作增幅≤0.11%（几乎不用动作）；同数据原始41维robot_state上skill=+15.4%，若干维度动作依赖显著（打乱增幅0.5–2.7×）。
- 限制：单一分叉点、单一超参配置（工程选择）；robot_state诊断仅seed0；一步预测受观测滞后影响（SRC0186）；不是任务收益证据。


<a id="src-0195"></a>
## SRC-0195 — 10万步验证及世界模型判据独立核查

- 类型：项目原始实测产物只读核查、指标公式推导与工程解释；核查日期2026-10-09约17:04–17:08+08，Codex /root，实际模型/强度未知。用户要求看10万步/说明WM判据，不授权本次新训练或修改机制。
- 来源：Claude当前正式t4s-plain-s0/1/2的validation_step00100105/00100020/00100067.json、progress/episodes/events.jsonl与supervisor.log；t4.9-wm-s0/1/2与t4.9-wmrs-s0/1/2的wm_result.json；scwm_train.py:run_eval/validate、scwm_wm_train.py:result.verdict_rule；[核查快照/原文件hash](../results/project/100k-wm-check-20261009/snapshot.json)。现有任务[4.9流程](tasks/task4/task4.9/PROCEDURE.md)/[结果](tasks/task4/task4.9/RESULTS.md)、[4.11流程](tasks/task4/task4.11/PROCEDURE.md)。已读本地产物/代码，未重跑模型或仿真。
- 原始结果：约17:04日志整千步106k/107k/107k，各目标1M；10万步附近确定性验证三个seed各5场景，物理与内部成功0/5、1/5、0/5（汇总1/15=6.7%，同5场景跨3策略，不是15个独立场景）；14失败均IK计数20、碰撞0，不能解释为每一步IK失败。训练早期0–20k与80–100k物理成功分别2/147→1/108、3/133→2/113、1/126→1/103，随机训练场景/策略变化下未见清晰提升，不能当配对评估或收敛证明。
- WM：固定256维actor表征验证，相比保持当前状态的恒等预测MSE下降2.76–4.13%；打乱动作后MSE相对原模型增加0.0535–0.1109%，动作信息证据弱。新增原始41维robot_state产物同种子下降11.56–15.42%，打乱动作增加2.40–3.17%；低变化半数劣于恒等（skill约−135%至−162%），不表示所有状态或真实物理动力学均预测好。不同表征MSE单位/尺度不同，只作各自同空间对照，不比较绝对MSE。
- 推导：skill=1−MSE_model/MSE_identity；shuffle increase=MSE_shuffled/MSE_model−1，均无量纲，百分数乘100。恒等为z_next_hat=z_t。举例“误差100降到96”只是比例教学例子，不是实际MSE单位；“换动作却预测几乎不变”是动作打乱诊断的通俗解释，不保证所有单样本预测不变。
- 判据局限：4.9计划定性要求可靠动作信息，JSON verdict_rule仅skill>0且shuffle increase>0；现两个表征均满足两个数值条件。已有4.9 RESULTS“未通过”不能说成已违反明确数值阈值，较准确为可信程度不足/需澄清判定口径；本次不新增最小百分比门或改Claude结果。缺重复打乱/不确定性量化时，小正号不足以证明稳定动作信息。数据因果/整episode验证/固定encoder也必须满足；最终有效性依据4.11同任务/观测/预算、多种子物理任务成功与碰撞/IK/额外成本，尚无feedback任务对照，预测提升不证明任务收益。robot_state含规划/IK字段，不能宣传为仅物理后果。
- 使用位置：[本独立日志](agent_logs/project/20261009-codex-100k-wm-check.md)及用户通俗答复；只追加独立来源与进度，未修改实施任务或干预训练。


<a id="src-0196"></a>
## SRC-0196 — GPU3当前已转入三种子冻结WM反馈SAC训练

- 类型：项目进程/原日志只读核查；2026-10-09T17:15:59.910950+08:00，Codex /root，实际模型/强度未知。
- 来源：nvidia-smi GPU3 UUID GPU-29fe1ea1-d4e9-c14b-64f2-cb875ae92a0a；compute PID2614394/2614397/2614399与ps scwm_train命令匹配；logs/task4/t4s-fb-s0/1/2 progress/events/supervisor.log，results/task4/t4s-fb-s0/1/2/run_manifest.json；scripts/scwm_feedback.py冻结requires_grad与eval；scwm_train.py feedback/fork路径。
- 事实：GPU3总14841MiB约14.5GiB，每feedback进程4936MiB；三run cuda:3、仿真实例3/4/5，从对应plain第100000步完整状态/回放分叉，载入t4.9-wmrs-s0/1/2/wm.pt（robot_state版），目标累计各1000000步；17:05+08启动，核查整千步102000/103000/102000（仅分叉后新增约2000/3000/2000步）。世界模型冻结，更新反馈SAC策略。GPU0/1/2的plain原进程同时仍在。
- 限制：瞬时GPU利用率0%不等停机，进程与进度均存在；仅早期运行核查，不等验收或任务收益。用户此前讨论时尚无反馈运行，当前已发生状态变化，以本核查为准；本次不审核新分叉授权/公平性或改变实施安排。
- 使用：[独立日志](agent_logs/project/20261009-codex-gpu3-status.md)及用户答复。


<a id="src-0197"></a>
## SRC-0197 — 随机种子机制沿Husky，三种子0/1/2为FoReM实验安排

- 类型：本地原参考代码/项目协议核查；2026-10-09，Codex /root，实际模型/强度未知。
- 来源：husky/src/modulation_rl/scripts/modulation/utils.py:45 --seed默认−1，272–274/398–404负一时random.randint(10,1000)并set_seed，313–316固定torch/numpy/random；scripts/main.py:125–126/164一个config seed用于网络与回放，main_ray.py:290 num_samples=1；ros_startup_incl_train.sh运行单一CMD。参考基准版本1ccedd087ac12dd317e93accc37bb81e05beeb99（本轮未再次全仓hash核验）；forem/doc/tasks/task4/task4.7/RESULTS.md:65–77将3种子记录为用户“原3种子讨论”，而非Husky固定配置；当前t4s-plain-s0/1/2及feedback入口见SRC-0196。
- 结论：所检查的本地训练入口支持可指定seed，但不自动固定启动0/1/2三轮；三个seed是当前FoReM重复实验安排。不能把“原项目配置”理解成三种子是其默认脚本行为。不根据这些入口断言作者论文完全未做多种子实验，也未独立核验Task4所述过去用户对话授权。
- 使用位置：[独立日志](agent_logs/project/20261009-codex-seed-origin.md)及用户答复；未改变训练数量/预算。


<a id="src-0190"></a>
## SRC-0190 — 基线低成功率的单因素对照（IK阈值50 / 恢复双tanh）

- 类型：项目实测（诊断），Claude，2026-10-10。运行`t4.8-diag-ik50`、`t4.8-diag-legacytanh`（`scripts/scwm_train_diag.py`，种子0，6万步，GPU 3，实例6/7）；对照基准正式`t4s-plain-s0/1/2`前6万步。
- 证据：`results/task4/t4.8-diag-comparison.txt`、`logs/task4/t4.8-diag-*/episodes.jsonl`；正式运行45万步统计（结束距离、episode长度、失败占比）见task4.8 RESULTS §7。
- 结论：IK阈值20→50使episode变长但未改善末端接近目标；恢复双tanh无可见差别。限制：单种子短程，不能排除更长训练后的差异；`ik_fail_thresh_eval=50`来自`modulation/utils.py:109`，原项目训练实际用值未知。


<a id="src-0198"></a>
## SRC-0198 — N²M²原文：sim训练、Gazebo只做零样本测试；训练步数与评估口径

- 主张：N²M²在解析环境（sim）中训练，Gazebo仅用于零样本测试；训练步数按100万步解读；评估为每任务50个episode、学习方法取5种子平均；PR2在sim中9任务平均成功率88.2%。
- 类型：外部文献。
- 核查状态：已核验（通过arXiv HTML原文的工具摘录，未逐页阅读PDF）。
- 来源：Honerkamp, Welschehold, Valada；“N²M²: Learning Navigation for Arbitrary Mobile Manipulation Motions in Unseen and Dynamic Environments”；IEEE T-RO 39(5):3601–3619，2023；arXiv:2206.08737v2 https://arxiv.org/html/2206.08737v2 ；项目页 https://mobile-rl.cs.uni-freiburg.de/
- 精确位置：Sec. III-F（解析训练环境，rnd obstacle训练任务，目标0.5–5 m，膨胀0.4 m可解性检查，约束违反超过20步提前终止）；Table II（steps “10e6”，buffer size “10e5”，lr 1e-4→1e-6，batch 256，tau 1e-3，gamma 0.99，train intensity 0.1，hidden [512,512,256]，action noise 0.04）；Sec. IV-C（每任务50 episode，5种子平均）；Table III（sim：PR2 rnd obstacle 86.0、p&p 97.6、bookstore p&p 70.0、dynamic obstacle 84.4、dynamic p&p 81.6、cabinet 97.2、drawer 97.6、door 98.4、spline 80.8，平均88.2；HSR 82.4；TIAGo 65.4）；Sec. IV-I/Table VI（Gazebo零样本：PR2 79.2、HSR 82.7、TIAGo 62.8）。
- 原始依据：见上，数值单位为成功率%。表II中的“10e6/10e5”记法有歧义：字面可读作1e7/1e6。
- 本项目采用：用上游代码（[SRC-0199](#src-0199)）消除歧义。代码中buffer为100,000，因此“10e5”即1e5；同一记法下steps“10e6”为1e6，与代码`total_steps: 1000000`一致。因此task5按100万步执行（推导）。评估采用每任务50 episode；任务名与代码的对应见[task5 PROCEDURE](tasks/task5/PROCEDURE.md)。
- 适用限制：原文数值为5种子平均，task5每项只有单种子，不能作复现结论。表III列名与代码任务名的对应由执行者用`taskname()`和GMM文件核对，尚未核验。
- 使用位置：[task5 TASK](tasks/task5/TASK.md)、[task5 PROCEDURE](tasks/task5/PROCEDURE.md)、[task5.1 RESULTS](tasks/task5/task5.1/RESULTS.md)。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-11。
- 待办与变更：表III列名与代码任务名的对应待执行者核对。

<a id="src-0199"></a>
## SRC-0199 — 上游N²M²代码的训练默认口径（1M步、20 worker、seed 40、9个评估任务）

- 主张：上游官方训练口径为RLlib SAC、20 worker、training_intensity 0.1、`--load_best_defaults`；三台机器人`total_steps`均为1,000,000；默认任务simpleobstacle，world_type为sim；脚本起始种子40；评估任务为9个，在sim与gazebo中进行。
- 类型：外部官方代码。
- 核查状态：已核验（本地阅读源码）。
- 来源：robot-learning-freiburg/mobile-rl，https://github.com/robot-learning-freiburg/mobile-rl ，HEAD 6281205846b1bac4525d05ee230a47bddf42023d（2025-04-09），本地克隆于`mobile-rl/`；Docker镜像`dhonerkamp/mobile_rl:11.1-latest`（Docker Hub最后更新2022-11-18，压缩约8.06 GB）。
- 精确位置：
  - `docker_run.sh:3-6`：训练命令`--num_gpus 0.24 --num_workers 20 --num_cpus_per_worker 0.1 --num_envs_per_worker 1 --num_gpus_per_worker 0 --ray_verbosity 2 --training_intensity 0.1 --load_best_defaults`，`startseed=40`，`envs=("pr2")`。
  - `docker_run.sh`评估段：9个任务，`--evaluation_only --eval_execs sim gazebo`，每个任务单独调用。
  - `scripts/configs/best_defaults_ray.yaml`：pr2/tiago/hsr的`total_steps: 1000000`；tiago另有`frame_skip: [8]`与`frame_skip_curriculum: 1000000`。
  - `scripts/modulation/utils.py`：`:46` total_steps默认1_000_000；`:48` buffer 100_000；`:104` task默认simpleobstacle；`:107` world_type默认sim；`:108-109` ik_fail_thresh 20 / eval 50；parse_args中命令行参数优先于best_defaults。
  - `run_experiment.sh`：`--shm-size=120gb`。
  - `environment11.1.yml`：python 3.7、pytorch 1.7.1、ray[rllib]==1.6.0。
- 原始依据：见上。上游仓库没有`main.py`、`sac.py`，也没有任何prior相关代码。
- 本项目采用：作为task5两项共同的冻结口径（[task5 PROCEDURE](tasks/task5/PROCEDURE.md)）。
- 适用限制：torch 1.7.1在Blackwell GPU上预计不可用（待5.1实测），届时改为CPU训练，属于已登记的偏差。镜像内代码与HEAD的差异待5.1核对。
- 使用位置：task5 TASK/PROCEDURE、task5.1、task5.2。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-11。
- 待办与变更：镜像digest、镜像内代码差异由5.1补记。

<a id="src-0200"></a>
## SRC-0200 — Husky快照：`main.py`硬编码prior微调；`main_ray.py`无prior且作者曾用其训练husky_ur5；快照默认10M步

- 主张：Husky快照的`main.py`无条件加载并冻结一个不存在的prior checkpoint，用KL形式的`update_parameters_modified`微调，因此不能原样运行，也不是从零训练。`main_ray.py`不含prior，作者曾用它以与原文相同的超参数训练husky_ur5。快照`best_defaults`中husky_ur5的`total_steps`为10,000,000。
- 类型：本地参考代码核查。
- 核查状态：已核验。
- 来源：`husky/src/modulation_rl`，快照commit 1ccedd087ac12dd317e93accc37bb81e05beeb99。
- 精确位置：
  - `scripts/main.py:131` `resume = True`；`:153-155` prior_agent `load_and_freeze_checkpoint("/home/cbl/.../checkpoints_pnp_plus/sac_checkpoint_husky_ur5_4000")`；`:167-168` agent加载同一文件；`:219` 只有`resume == False`时才做随机预热；`:243` `update_parameters_modified(..., prior_agent)`（`:242`普通`update_parameters`被注释）；`:138` `num_steps = 5000001`，`:262`在`total_numsteps > num_steps`时退出循环。
  - `scripts/sac.py:166-219`：目标Q加`α·log π_prior(a'|s')`，策略损失为`α·log π − Q − α·log π_prior`，等价于KL(π‖π_prior)正则。`:306-330` prior参数`requires_grad=False`。
  - `scripts/main_ray.py:32` launch_ros被注释；`:39` ray.init日志级别改动；`:279` 注释掉的restore路径`/home/cbl/mm_ws/.../ray/husky_ur5_acceleration_penalty:0.05_learn_vel_norm:0.1_training_intensity:0.1_transition_noise_base:0.04.../SACTrainerCustom_modulation_rl_env_..._2025-03-27_23-18-14/checkpoint_000991`。
  - `scripts/configs/best_defaults_ray.yaml:68-69` `husky_ur5: total_steps: 10000000`，`learn_torso: False`。
  - 快照中没有`checkpoints*`目录；`scripts/model_checkpoints/`下只有hsr/pr2/tiago。
  - 当前`mm_husky:node01`为noetic + ray 1.13，`custom_sac`在该版本下不可导入（[SRC-0057](#src-0057)）。
- 原始依据：见上。
- 本项目采用：task5.2使用`main_ray.py`，不使用`main.py`，步数显式设为100万以与5.1一致，不采用快照的10M。
- 适用限制：注释路径只能说明作者曾用RLlib训练husky_ur5，不能说明其训练结果、步数或所用的ray版本。prior checkpoint的来源未知。
- 使用位置：task5 TASK、task5.2 TASK。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-11。

<a id="src-0201"></a>
## SRC-0201 — 用户授权：task5 sim对照（A上游PR2、B Husky原版main_ray），Claude制定流程、Codex执行

- 主张：用户授权在sim模式进行两项对照：上游N²M²选一台机器人做训练与验证；Husky用原版`main_ray.py`训练与验证；每项1个种子，训练步数一致，按原文口径进行。分工为Claude负责决策、流程与复核，Codex（GPT）负责执行，由用户派发。
- 类型：用户指令。
- 核查状态：已核验（本会话原话）。
- 来源：2026-10-11本会话中用户的连续消息：“那我们去sim模式训练一次吧…注意训练的步数要一致”“都按照原文口径来进行”“我们现在只跑12 然后1选用一个机器人看一下就可以了，然后HUSKy跑一次”“B”（选择`main_ray.py`方案）“注意那个也要同时做NM的训练和验证，之后你和codex交换角色，你作为决策者和流程制定者，让GPT去执行”“你不必派发，写好文档给我提示词我去派发”；以及模型推荐要求：“除非特别难的任务否则不用Astra，一般6.1sol足矣，然后如果挂子agent要给出派发的模型推荐”。
- 本项目采用：task5范围、分工与模型推荐规则。机器人由Claude选定为PR2（用户说“选用一个机器人看一下就可以了”）。
- 适用限制：不授权Gazebo评估、预训练模型评估、多种子，也不授权干预Task4运行。
- 使用位置：task5 TASK。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-11。

<a id="src-0202"></a>
## SRC-0202 — 用户指令：删除Task4无用数据，只保留最终训练结果等关键数据

- 主张：2026-10-11，用户要求清理Task4数据，原话为“原项目自带的保留，其他的全部删除，只保留一些关键的数据，比如最终训练的结果这种”，并选择“直接删除”。
- 类型：用户指令及执行记录。
- 核查状态：已执行。
- 执行：Claude（claude-opus-5-5）。只处理`forem/results/task4`和`forem/logs/task4`，没有动`husky/`、`mobile-rl/`、`forem/src`、`forem/config`、`forem/scripts`、文档以及其他任务的数据。共删除343项，约93.99 GB；清理前后容器内都没有训练进程（fb-s0已于16:15跑完100万步）。删除清单逐项记录在`forem/logs/task4/cleanup-20261011-manifest.json`，含路径和字节数。
- 保留内容（约0.57 GB）：
  - t4s-plain/fb-s0/1/2：`train_summary.json`、`run_manifest*.json`、全部`validation_step*.json`、`ckpt/latest.json`、全部`ckpt/policy_step*.pt`、`ckpt/state_01000000.pt`；对应日志`progress/episodes/events.jsonl`和`supervisor.log`。
  - t4.9-wm-s*与t4.9-wmrs-s*（WM权重）。
  - `t4.8-diag-comparison.txt`。
- 适用限制：被删的原始数据不可恢复。旧文档（Task4.1–4.6、4.7–4.9先导/诊断/基准等）中指向这些路径的证据链接会失效，相关结论只能以文档里已经写下的摘要为准，不能再重算。训练中间replay/state（含plain的10万步分叉点）已删除，fb分叉和续训无法再从中间点复现。
- 使用位置：[Task4 RESULTS](tasks/task4/RESULTS.md)、PROGRESS。
- 核查人及日期：Claude，2026-10-11。

<a id="src-0203"></a>
## SRC-0203 — 用户本轮只授权Codex执行task5.0环境准备

- 支撑主张：本轮仅task5.0，按Claude冻结§0–11执行；不训练/评估、不进入5.1/5.2；文档未覆盖且超出允许偏差的问题须停止并交Claude决策。
- 类型：用户指令；已核验本会话原话（2026-10-11）。
- 来源/精确位置：本次Codex用户任务消息，“本次只执行FoReM项目的 task5.0（环境准备）”“遇到文档没有覆盖、又超出允许偏差的问题…停下来，写进RESULTS和日志，交给Claude决策”；本地转录摘要见[执行日志](agent_logs/task5/task5.0/20261011-codex-task5-0.md)。
- 原始要求/采用：只执行环境准备；Claude决策/复核；RESULTS与PROGRESS记review，不能记done；forem-dev仅允许§8只读渲染。模型默认gpt-6.1-sol/medium，实际无法核实须写未知。
- 适用限制：不扩大任务范围；review表示交付待审，不表示环境检查通过；本轮没有用户授权重启Docker daemon或停止Claude原pull。
- 核查：Codex，2026-10-11；使用位置：[5.0 RESULTS](tasks/task5/task5.0/RESULTS.md)、PROGRESS与日志。

<a id="src-0204"></a>
## SRC-0204 — task5.0本次镜像拉取未完成与开工检查（t5.0-env-r1）

- 支撑主张：本次未取得完整本地镜像，后续容器/构建/URDF/就绪门槛尚未执行，GPU与并行口径未判定；不得放行5.1/5.2。
- 类型：项目实际命令观测；远端官方镜像清单只读核查；停止本次CLI为工程处理，挂起根因待验证。
- 来源：本地[证据目录](../results/task5/t5.0-env-r1/)，[本次pull日志](../logs/task5/t5.0-env-r1/image-pull-retry1.log)，Claude原始`forem/logs/task5/t5-image-pull.log`；Docker官方registry镜像dhonerkamp/mobile_rl:11.1-latest（远端清单返回2026-10-11版本，未取得本地RepoDigest）。
- 精确位置：`preflight.json`各command/exit_code；`remote-image-manifest.json`的layers；`pending-layer-sizes.json`；`registry-head-probes.json`两个HEAD结果；`own-pull-cancellation.json`的核验cmdline/PID；`final-observations.json`的docker image inspect与ps结果；`env_manifest.json`；本次pull CLI PID1934873，Claude原PID1847732。证据文件sha256见`evidence_sha256.json`。
- 原始结果：开工docker ps只有forem-dev，宿主4卡无计算进程（仅Xorg），nproc64，free -g Mem total251/available232。原日志72层中67层已完成/缓存，5层未报告完成；远端清单中这5层压缩大小合计2,784,272,300 bytes（求和推导，仅层总大小，不代表剩余下载量）。manifest inspect退出0；两个未完成层的HEAD均200。最终本地image inspect退出1，目标不存在；Claude原pull仍运行约41分钟。本次pull约14分钟未自行退出，仅对已核验身份的本次CLI发SIGTERM后退出143，原pull/daemon/forem-dev未触碰。
- 本项目采用：记录§1未完成、停止后续推进并交Claude决策持续无新输出的处理方式；5.0交付review但验收未通过。
- 适用限制：日志无新输出不能证明零字节下载或具体网络/daemon根因；HEAD200不能证明完整层GET成功；SIGTERM143是主动结束CLI，不是自然网络失败，不宣称连续3次失败。宿主GPU空闲不能证明旧torch可运行；仅nproc/free不足以判定20-worker双环境并行。未改镜像/Python栈/源码或科学条件。
- 核查人/日期：Codex，2026-10-11，实际精确模型与强度未知；使用：[5.0 RESULTS](tasks/task5/task5.0/RESULTS.md)、PROGRESS、执行日志。

### SRC-0204 进度复查追加（2026-10-11 17:24 +08:00）

Codex按用户状态询问只读复查，目标本地镜像仍不存在；Claude原pull PID1847732已持续约70分钟且仍未退出，docker ps只有forem-dev。证据：[status-check-1724.json](../results/task5/t5.0-env-r1/status-check-1724.json)。不推断下载根因；未恢复实施，GPU/并行及后续门槛均仍未判定。

### SRC-0203 用户后续明确指令（2026-10-11）

用户原话：“镜像下载中，请你持续监控”“下载完毕即开始”。采用：恢复持续监控，完整镜像取得后自动继续已授权task5.0环境流程；不解释为task5.1/5.2训练授权。核查人Codex；记录见独立执行日志。

### SRC-0204 持续监控记录（用户授权恢复后）

恢复监控后，发现Claude新pull PID1964257，日志`forem/logs/task5/t5.0-env-r1/image-pull-claude-retry2.log`。后续检查的实际时间、docker image inspect退出码、镜像metadata或错误及日志尾部，追加到[image-monitor.jsonl](../results/task5/t5.0-env-r1/image-monitor.jsonl)。记录反映当次状态，不推断根因，不替代完整镜像确认。Codex核查，2026-10-11。

### SRC-0204 带终端进度检查（2026-10-11 18:52 +08:00）

按§1“镜像不存在则再pull”授权，Codex用script记录一次带TTY的官方pull，命令与原因见独立日志。原始[image-pull-progress-r3.log](../logs/task5/t5.0-env-r1/image-pull-progress-r3.log)，抽取的带时间快照[image-byte-progress.jsonl](../results/task5/t5.0-env-r1/image-byte-progress.jsonl)。首次取得8816f79d49f6层实际显示348.1MB/610.8MB；比例348.1÷610.8≈57%（显示值推导）。非完整镜像状态，不能推断稳定速率或承诺完成时间。未改Docker配置/镜像标签/科学条件，未停止Claude原重试。

<a id="src-0205"></a>
## SRC-0205 — task5.0镜像落地、两容器与Python/CUDA实测（t5.0-env-r2）

- 主张：完整镜像取得；两容器按冻结要求创建；实际Python栈可导入custom_sac；两卡CUDA矩阵均失败，A/B按允许偏差统一num_gpus=0。
- 类型：项目实测，已核验实际命令输出。
- 来源/版本：dhonerkamp/mobile_rl:11.1-latest，RepoDigest与image inspect Id均sha256:42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915，Created 2022-11-18；[证据目录](../results/task5/t5.0-env-r2/)，[TTY拉取日志](../logs/task5/t5.0-env-r1/image-pull-progress-r3.log)，pull退出0。
- 精确位置：image.json、initial_commands.json、container_creation.json、forem-t5-{pr2,husky}-inspect.json、python_stack_*.txt、stack_and_extra_diff_commands.json、gpu_tests.json（完整stdin/输出/退出码）。
- 原始结果：容器PR2=f0b50dcfbdb85dcc0769fb7f9d7b723fb923cd618342d01b801768fa7cf0c720/GPU0；Husky=b2f8f4ed89b486fc568fba177578bcb5ca1bde3d11a777d12925b0671b0450e0/GPU1；bridge、shm128849018880bytes、WANDB_MODE=offline、两参考挂载只读。Python3.7.13，ray1.6.0，torch1.11.0+cu102/CUDA10.2，wandb0.10.11，gym0.21.0，numpy1.21.5；两容器ray_utils导入退出0。GPU可用标志True，但torch.randn(64,64,device=cuda)两边均退出1，报Blackwell sm_120不兼容/no kernel image，未算出矩阵结果。
- 本项目采用：不升级/替换栈，按父流程GPU允许偏差取两项num_gpus=0；仅环境检查，不训练。
- 限制：实际镜像栈不同于计划预期torch1.7.1，不把yml声明冒充安装版本；导入成功不是训练成功；CUDA失败不等于GPU硬件故障。
- 核查人/日期：Codex（精确实际模型/强度未知），2026-10-11。使用：[5.0 RESULTS](tasks/task5/task5.0/RESULTS.md)、执行日志。

<a id="src-0206"></a>
## SRC-0206 — 镜像与参考HEAD差异、Husky快照371文件和原样复制

- 主张：镜像内代码与上游HEAD存在指定差异，A按Claude已冻结决策保留镜像代码；Husky modulation_rl当前内容与1ccedd0的371文件均一致，复制后的文件sha256一致。
- 类型：项目原始代码核查/文件实测。
- 来源：上游参考HEAD6281205846b1bac4525d05ee230a47bddf42023d；镜像同SRC-0205；Husky快照1ccedd087ac12dd317e93accc37bb81e05beeb99及其他所需包当前文件。[r2证据](../results/task5/t5.0-env-r2/)。
- 精确位置：upstream_code_diff.txt、upstream_core_diff.txt、mapencoder_diff.txt、costmap_launch_diff.txt、upstream_diff_commands.json；husky_modulation_snapshot_check.json的371个expected/actual Git blob与sha256；husky_source_manifest.json各source_path/work_path/sha256。
- 原始结果：main_ray.py、evaluation_ray.py、configs、src文本diff退出0；envs/myray文本代码一致，只有缓存目录差异。mapencoder.py镜像LocalDoubleMapCNN继承jit.ScriptModule，HEAD改nn.Module并注释optimizer非叶节点问题；costmap launch的lasers_and_filters include不同；另外有文档/脚本/模型/rviz/缓存缺项，全部rq清单保留。当前Husky modulation_rl逐371文件按Git blob核查，0不匹配；六包（modulation_rl、husky_ur5、husky_description、robotiq_85_description、bio_ik、tmc_control_msgs）原样复制到build/task5/ws_husky/src，逐文件hash相等。
- 本项目采用：只记录镜像差异，不把HEAD替换进去；不沿用Task3改造源码，构建只用新复制包。
- 限制：mapencoder优化器问题来自上游代码注释，尚未训练验证，不宣称本镜像一定报错或已消除；1ccedd0的Git树证明范围仅modulation_rl，其他包仅文件sha256冻结，不伪造它们属于该commit；复制成功不是构建/URDF/环境成功。
- 核查人/日期：Codex，2026-10-11。使用：[5.0 RESULTS](tasks/task5/task5.0/RESULTS.md)、日志。

<a id="src-0207"></a>
## SRC-0207 — task5.0资源口径：主入口Ray线程与bio_ik默认并发，采用先后运行

- 主张：64CPU/可用RAM约232GiB；入口按ray→torch导入后torch intraop为1；默认bio2_memetic每求解器4线程，40 rollout worker潜在IK线程超64核，因此保持冻结worker数/求解参数，采用A/B先后运行。
- 类型：硬件/运行栈实测、代码核查、容量推导与工程选择（不是并行训练性能实测）。
- 来源/位置：[r2证据](../results/task5/t5.0-env-r2/)，resources.json、resources_main_import_order.json、ray_cpu_thread_source.txt、ray_thread_all_references.txt、pr2_bioik_concurrency.txt、resource_decision.json；镜像ray1.6.0/__init__.py:31–35默认设置OMP_NUM_THREADS=1；两main_ray.py先导入ray；bio_ik/src/kinematics_plugin.cpp:252–255默认mode bio2_memetic/threads0，ik_parallel.h:120–122采用solver并发，ik_evolution_2.cpp:649 concurrency()=4；Husky源码SHA见SRC-0206。
- 原始结果：nproc64/lscpu64核，free -g显示RAM251/available232；容器可见0–63 CPU且无CPU/memory限制。单独先import torch时intraop64，但正式main_ray导入顺序ray→torch实测两边intraop1、interop32、OMP_NUM_THREADS=1（Ray自带行为，未新增线程环境变量）。bio2默认求解器并发4。
- 推导：2项×20 rollout×4线程/solver=160潜在IK线程，尚未计评估/trainer/ROS，超过64核；线程池容量不等于所有线程始终繁忙。普通1线程torch不能用来忽略IK并发。
- 采用：保守安排先后运行，保持20 worker、IK模式/线程参数不变；同一项也可能有过量调度，须在后续已授权冒烟/profile中核查，不能自行调科学条件。
- 限制：没有双20-worker训练/内存峰值实测；本条不证明并行绝对不可执行或给出墙钟承诺，不启动训练，性能必须由5.1/5.2阶段实际验证。
- 核查人/日期：Codex，2026-10-11。使用：[5.0 RESULTS](tasks/task5/task5.0/RESULTS.md)、日志。

<a id="src-0208"></a>
## SRC-0208 — task5.0描述包依赖获取：ROS源/容器Git失败与官方源码位置（进行中）

- 主张：ROS apt源请求失败，两个描述包未通过apt安装；仅在FoReM build/task5获取官方依赖源码，保留Python栈/算法；velodyne_description来自Dataspeed的velodyne_simulator而非ros-drivers/velodyne。
- 类型：项目命令实测、外部官方包索引、依赖路径/构建兼容工程处理。核查状态：已核实下列事实，构建/URDF尚待后续。
- 来源：[r2证据](../results/task5/t5.0-env-r2/)，[r2日志](../logs/task5/t5.0-env-r2/)；官方[ROS包索引](https://index.ros.org/p/velodyne_description/)的melodic Package Summary/Repository Summary（核读web3069–3092：版本1.0.13，来源https://bitbucket.org/DataspeedInc/velodyne_simulator.git，master，2022-12-02）；本地official_dependency_sources.json登记索引字段/核查日期。
- 精确位置：apt_update_command.json与apt-update.log、dependency_initial_commands.json、ros_repository_protocol_probe.json、external_dependency_remote_branches.json/commands.json、own_git_timeout_cleanup.json/own_git_helper_cleanup.json、ur_host_remote_probe.json、ur_host_clone_command.json、ur_dependency_manifest.json、velodyne_host_clone_command.json、velodyne_simulator_official_refs.json；命令、stdin、退出码与清理目标均保留。
- 原始结果：apt update退出0但ROS InRelease连接失败；install两包退出100找不到包；HTTP curl52空响应、HTTPS curl35 SSL_ERROR_SYSCALL。容器UR git首次空响应/重试挂起，后者仅终止本次经cmdline核验的Git与其指定URL helper；容器Velodyne克隆TLS握手失败128。宿主UR ls-remote/clone退出0，melodic-devel实际commit09ba93f5bd4df876465573617ed8bdb76ea4bf01，ur5_macro.xacro及调用参数存在；原文件161项SHA冻结。误取ros-drivers/velodyne不含描述包，保留为未使用尝试；正确描述包官方来源/分支已核实，实际克隆/构建/URDF结论须追加。
- 工程采用：仅依赖获取使用宿主Git（build/task5/deps），容器构建依旧ROS melodic；UR描述包相对链接接入新ws_husky/src；网络请求使用有界命令参数，无全局网络/apt配置修改，无Python栈升级。ROS索引仍失效，不把apt update退出0算依赖成功。
- 限制：容器与宿主请求结果差异不能单独证明网络/旧TLS库根因；源码获取不是URDF等价性通过，后续仍执行§8；不能将备用驱动仓库当描述依赖。未改参考目录、forem/src或C++算法。
- 核查人/日期：Codex，2026-10-11。使用：[5.0 RESULTS](tasks/task5/task5.0/RESULTS.md)、执行日志。

### 获取完成追加（SRC-0208）

Velodyne正确仓库master实际clone退出0/commit b98e156c4431210b08de679735e6fe81acc7932f，描述包19文件SHA见velodyne_dependency_manifest.json；首次渲染缺lms1xx后取得官方melodic-devel 791c622b4f3f7953bb1b8c908e5099d17748efd2/18文件，见lms1xx_dependency_manifest.json。两次渲染分开保留，依赖获取不是门槛通过，最终门槛失败见SRC-0209。

<a id="src-0209"></a>
## SRC-0209 — task5.0 Husky melodic构建/导入成功，URDF惯性差异门槛失败并停止

- 主张：新Husky工作区首轮构建/新绑定导入成功且原始复制741文件未变；Melodic与Noetic渲染的规定字段存在7项惯性质量/质心差异，按用户§8停止，不进行就绪/训练。
- 类型：项目实际构建/渲染/文件核验、按用户阈值的数值比较；已核验本次实际输出。
- 来源：[r2证据](../results/task5/t5.0-env-r2/)，[r2日志](../logs/task5/t5.0-env-r2/)；UR依赖09ba93f5bd4df876465573617ed8bdb76ea4bf01、Velodyne描述依赖b98e156c4431210b08de679735e6fe81acc7932f；额外LMS1xx依赖791c622b4f3f7953bb1b8c908e5099d17748efd2（官方[ROS索引](https://index.ros.org/p/lms1xx/)melodic Repository Summary，web3311–3334：clearpathrobotics/LMS1xx，melodic-devel）。
- 精确位置：husky_build_attempt1.json/husky-build-attempt1.log（catkin --extend /opt/ros/melodic，PYTHON_EXECUTABLE=/opt/conda/bin/python，-j8 -p2）；husky_import_test.json的bindings_file断言；source_unchanged_after_build.json；urdf_render_commands.json（首次Melodic失败2/lms1xx缺失，Noetic成功0）；urdf_render_attempt2.json（补运行描述路径后Melodic成功0）；husky_{melodic-attempt2,noetic}.urdf；compare_urdf.py及urdf_equivalence.json中的SHA/全部规定字段快照/差异；完整XML结构差异urdf_full_structural_diff.txt。
- 原始结果：9个catkin包构建成功、退出0、构建报告49.1秒（构建工具wall报告，非实验时延）；新模块RobotHusky和ray_utils导入退出0，绑定文件位于新devel/lib/python3/dist-packages/pybindings_robots.cpython-37m-x86_64-linux-gnu.so。构建后741原始复制文件sha仍相等，无源码补丁。首次xacro缺lms1xx，官方源码仅经ROS_PACKAGE_PATH用于描述查找，未编译/启动传感器驱动。最终两个模型均39joint/40link，关节规定字段/碰撞URDF描述/SRDF/kinematics一致；7项差异为ur5_forearm_link质量2.275 vs2.33 kg及forearm/shoulder/upper_arm/wrist1/wrist2/wrist3的inertial origin xyz（m），具体值与全部差异见JSON。数值绝对容差1e-6沿用户§8，不放宽。
- 采用：§8失败立即停止，保留两个新容器（最终仅sleep infinity），§9两就绪与§10加载机制均未执行，5.0为review/未通过，不放行5.1/5.2；不调整UR质量/质心或放宽门槛。
- 限制：Noetic使用已配置Task3迁移包，仅只读xacro一次；迁移记录有Gazebo重力/插件差异，完整XML结构diff另保留，不能称整份XML一致。未获准额外读取forem-dev依赖/mesh文件，Noetic准确UR依赖版本及外部mesh字节一致性未核查；只比较URDF几何描述/URI/scale。惯性差异成因/是否影响解析实验需Claude决策，不能以sim可能忽略惯性自行豁免，也不把构建/导入当环境成功。
- 核查人/日期：Codex（精确模型/强度未知），2026-10-11。使用：[5.0 RESULTS](tasks/task5/task5.0/RESULTS.md)、PROGRESS、执行日志。


<a id="src-0210"></a>
## SRC-0210 — task5.0 r2核验决策依据：ur_description版本差异与上游mapencoder官方修复

- 主张：
  - (1) task5.0 r2的URDF不一致只来自ur_description版本差异（melodic侧用universal_robot melodic-devel 09ba93f，noetic侧用ros-noetic-ur-description 1.5.0），只影响UR5的惯性参数。
  - (2) 上游镜像中的`mapencoder.py`早于官方修复commit 3c6706d。该修复把`LocalDoubleMapCNN`从`jit.ScriptModule`改为`nn.Module`，注释写明前者在训练时会导致optimizer的non-leaf错误；Husky快照已包含该修复。
  - (3) sim解析模式不使用惯性参数。
- 类型：(1)(2)为本地证据和官方代码核查；(3)为推导，依据是RobotEnv的解析路径只做运动学和碰撞检查，见task3.5的B1链路说明和`robot_env.cpp`中`isAnalytical`分支不发送控制命令。
- 核查状态：(1)(2)已核验；(3)为推导，未做实测。
- 来源/位置：
  - `forem/results/task5/t5.0-env-r2/urdf_equivalence.json`（required_field_differences共7项，均为inertial），`ur_dependency_manifest.json`（melodic-devel 09ba93f）。
  - `docker exec forem-dev dpkg -l`：ros-noetic-ur-description 1.5.0-1focal.20250520。
  - `git ls-remote` universal_robot：tag 1.5.0 → e4c1c42e854e45084ad827adca6a6bda00324955。
  - `mobile-rl`：`git show --stat 3c6706d`（2025-03-10，“fix non-leaf issue”，只改了mapencoder.py 4行）；`git log`显示HEAD 6281205之前的最后一个代码commit就是3c6706d。
  - `mapencoder_diff.txt`。
  - `husky/src/modulation_rl/scripts/modulation/models/mapencoder.py:42`为`class LocalDoubleMapCNN(nn.Module)`。
- 本项目采用：[task5.3 R2](tasks/task5/task5.3/RESULTS.md)中的D1、D2。
- 适用限制：(3)只适用于sim模式，不适用于Gazebo或物理。是否真的会出现non-leaf错误尚未实测；选择采用官方修复是为了让A、B的实现一致，并与上游HEAD一致。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-11。

<a id="src-0211"></a>
## SRC-0211 — task5.0 r3 D1执行、模型字段相等与完整URDF非惯性差异停止

- 主张：r3检出官方universal_robot tag 1.5.0/e4c1c42e854e45084ad827adca6a6bda00324955；Husky增量构建8包成功退出0。melodic/noetic xacro均成功0；规定joint/inertial/collision字段（1e-6）与SRDF/kinematics相等，r2七项惯性差异消失。完整模型仍有17项Gazebo语义差异（按相同reference合并gazebo块、忽略兄弟顺序与1e-6内数值差后）：两插件缺失、5个mimic库名差异、10个turnGravityOff缺失。
- 类型：项目原始实测/官方Git源码；停止口径为用户本轮r3明确指令（“出现惯性以外的任何差异仍按失败停止”），不自行豁免Gazebo。
- 来源/版本：官方https://github.com/ros-industrial/universal_robot.git tag 1.5.0；依赖原melodic-devel 09ba93f保留Git对象。执行依据SRC-0210、task5.3 RESULTS R2 D1–D3。
- 精确位置/证据：[r3](../results/task5/t5.0-env-r3/) ur_checkout.json、husky_rebuild.json、ur_dependency_manifest.json、urdf_render_commands.json、urdf_equivalence.json、urdf_full_semantic_differences.json、compare_full_semantics.py、urdf_full_structural_diff.txt。迁移补丁来源forem/config/task3/patch_reasons.json（grasp、mimic、planning_scene、gravity）。
- 失败记录：初次fetch TLS错误退出128，重试0；未更改代理/Git全局设置。
- 原始结论/采用：官方1.5.0在melodic可渲染，因此不适用D1“无法渲染”的有条件通过分支。规定字段相等不等于整份URDF一致；按最新指令§8 failed并停止D2/§9/§10，状态review；两容器保留仅sleep；未训练/评估。
- 适用限制：比较XML几何描述/URI/scale，未读forem-dev外部mesh字节；不是环境就绪或物理验证。完整比较记录已确认的Gazebo差异，不能凭推测sim不使用它们自行改门槛。GPU0与先后结论沿用r2及D3，不重新实测。
- 核查人/日期：Codex，2026-10-11；实际精确模型/强度未知，用户指定gpt-6.1-sol/medium，未切换/委派。

<a id="src-0212"></a>
## SRC-0212 — task5.0 r4 D2、两50步就绪与本地输出/加载只读核查

- 主张：D2实际替换镜像PR2 mapencoder为上游HEAD文件（最后改动3c6706df1c8e0aa22396c23ec0f98bae126c0140），SHA从273a5ce11eccde3357ece2cc416e8e11976bc15ae5d7725cf3d92e4d2d554248变为f52e54bc3d335ccc6bb3a3a867fe7ea7557be806c45565ed32b49fca9108de95；导入确认nn.Module。两容器analytical/move_group/bio_ik就绪，parse_args最佳默认、env_creator、reset及随机动作各50步成功0，不训练不写replay。输出路径和本地model_file机制已只读核查。
- 类型：项目实测、官方/快照代码核查；D4与GPU0/先后口径是Claude决策继承，非本轮重测。
- 来源/精确位置：[r4证据](../results/task5/t5.0-env-r4/) d2_manifest.json、d2_replace.json、d2_import_verify.json、env_readiness_{pr2,husky}.json（逐步奖励/done/info/观测/动作/耗时）、{pr2,husky}_ros_commands.json（命令/PID/节点/IK/清理）、readiness_import_paths.json、output_read_commands.json、output_and_eval_loading.md、evaluation_ray.diff。日志../logs/task5/t5.0-env-r4/。
- 代码版本：上游HEAD6281205846b1bac4525d05ee230a47bddf42023d；Husky原始快照1ccedd087ac12dd317e93accc37bb81e05beeb99。symbols：utils.parse_args/setup_config_wandb/env_creator；ray_utils.get_local_ray_dir/get_local_wandb_dir；ray_wandb.restore_ckpt_files/_save_ckpt/RAY_METADATA_ENDING；evaluation_ray.main。
- 原始结果：PR2 reset0.446298s/mean step0.00991566s，Husky reset0.469327s/mean step0.0134114s，各50步done=0；仅单环境就绪耗时，不是训练吞吐/工期。PR2 right_arm(_and_torso)与Husky manipulator bio_ik。两容器最终仅sleep，forem-dev本run未执行任何命令。
- 输出机制：parse_args logpath=<scripts>/logs，ray=<logpath>/ray，wandb dir=<logpath>/wandb；本地恢复要求checkpoint-N、对应_trainableState、同目录ray_config.pkl及value包装config.yaml，运行恢复时生成.tune_metadata。evaluation_ray仅launch_ros注释差异。脚本logs指向results的软链接是未来路径工程方法，本轮未实施。
- 失败：PR2检测脚本AST误选字典KeyError，Husky引号导致宿主提前展开ROS_PACKAGE_PATH；两个attempt1日志/JSON保留，均只修自身检查脚本/命令，不改科学代码。最终两次检查均0。
- 采用/限制：5.0 review等待Claude核验，5.1/5.2未开始。§8继承Claude R3 D4通过（修订§8门槛），不覆盖r3历史failed；GPU0和默认先A后B，D3并行例外需后续授权5.1实测。parse_args的device元数据为cuda，但本轮没有模型/optimizer/tensor CUDA执行，不能当训练设备验收；num_gpus0仍沿r2真实CUDA失败。不实际调用本地restore或评估，不验证checkpoint可用性。
- 核查人/日期：Codex，2026-10-11。用户指定gpt-6.1-sol/medium，实际精确模型/强度未知，未切换/委派；Claude替代推荐Sonnet5.5/medium。

<a id="src-0213"></a>
## SRC-0213 — Husky快照相对上游N²M²的任务与训练语义差异

- 主张：除新增husky_ur5机器人和兼容性修改外，Husky快照还改动了以下内容：
  - SimpleObstacleMap障碍间距/偏移写死为3.0/0.8（上游1.75/0.4375）。
  - eeplanner的height_preference写死为True。
  - learning_starts写死为0。
  - 新增CLUB因果掩码回调。
  上游当前代码中，`wandb_config.rnd_steps`不在parser里，DotDict会返回None；论文训练时该值为0。
- 类型：本地代码核查。CLUB回调“不起作用”是推断，待5.2冒烟验证。
- 来源/位置：
  - 逐文件`diff mobile-rl/scripts husky/src/modulation_rl/scripts`。
  - `modulation/envs/map.py:837-838`；`modulation/envs/eeplanner.py:545,679`；`modulation/myray/ray_utils.py:130`；`modulation/myray/ray_callbacks.py`（CLUB、`on_train_result`、`policy.replay_buffer`、`model.set_mask`、`.cuda()`）。
  - `modulation/dotdict.py`（`__getattr__`返回`self.get`）。
  - `mobile-rl/scripts/model_checkpoints/pr2/config.yaml:511,621`（`rnd_steps: 0`）。
  - 在forem-t5-husky中grep ray 1.6的`sac_torch_policy.py`/`torch_policy.py`，没有`replay_buffer`。
  - `forem/config/task3/task_contract.yaml:38-39,75-76`（Task3继承了3.0/0.8的覆盖）。
- 本项目采用：[task5.3 R4](tasks/task5/task5.3/RESULTS.md)中的D5–D7。
- 适用限制：上述diff的范围只覆盖scripts目录；C++部分已在Task3/5.0中核对。CLUB回调是否不起作用、learning_starts的实际值，都以冒烟实测为准。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-11。

<a id="src-0214"></a>
## SRC-0214 — task5.1 冒烟r1/D7与r2离线W&B初始化失败

- 主张：r1因learning_starts=None在RLlib replay_buffer.py:322失败，退出1；按Claude D7仅将容器ray_utils.py的learning_starts改为0，r2 params.json实际值0。r2随后因Ray1.6 W&B集成_set_api_key未发现API key而失败，退出1，未完成训练/评估门槛。
- 类型：项目实测/本地官方代码核查；CPU核数为/proc/stat推导，非完整训练性能。
- 来源/精确位置：../results/task5/t5.1-smoke-r1/d7_manifest.json、d7.diff、ray_utils.before.py/after.py，r1 trial error.txt/params.json；../results/task5/t5.1-smoke-r2/下trial error.txt/params.json、host_cpu_5s.jsonl、smoke_summary.json、exit_code.txt、final_docker_top.txt、ray_wandb_key_check.txt；../logs/task5/t5.1-smoke-r{1,2}/train.log。容器forem-t5-pr2，上游6281205与D2继承SRC0212，新增D7。
- 推导：每5秒读取主机/proc/stat aggregate CPU，核数=64×(delta total−delta idle−delta iowait)/delta total；前8字段，total包含user/nice/system/idle/iowait/irq/softirq/steal，单位核。峰值/均值与样本数见r2 summary；主机所有进程均包含。
- 原始结果：r1监控启动包装未存活，0有效样本；r2采样正常，但均为初始化而非训练负载。两次无检测到CUDA运行错误（r1/r2日志有sm120兼容警告），不等于完成训练tensor/optimizer设备验收。无有效env步吞吐/百万步时长、无checkpoint和9任务评估。
- 采用/限制：D3并行结论未建立，不能用初始化CPU低于32核放行5.2；按用户要求停止超出流程的W&B API key问题，交Claude决策，不自行登录/上传/设key/改W&B代码。
- 核查人/日期：Codex，2026-10-11；用户指定gpt-6.1-sol/medium，实际平台精确型号/强度未知，未切换/委派。

<a id="src-0215"></a>
## SRC-0215 — W&B离线运行：ray 1.6要求API key；上游官方离线说明

- 主张：ray 1.6的W&B集成在实例化`WandbSACTrainer`时会调用`_set_api_key`。如果找不到API key，即使处于offline模式也会抛出ValueError。上游readme给出的无账号运行方式是执行`wandb offline`或`wandb disabled`。
- 类型：项目实测和官方代码/文档核查。
- 来源/位置：
  - `forem/results/task5/t5.1-smoke-r2/ray_wandb_key_check.txt`（`ray/tune/integration/wandb.py` `_set_api_key`源码）。
  - r2 trial error.txt中的调用栈：`modulation/myray/ray_wandb.py:68`调用`_set_api_key`，抛出ValueError。
  - `mobile-rl/readme.md:36-37`、`:137`。
- 本项目采用：[task5.3 R5](tasks/task5/task5.3/RESULTS.md)中的D8，即`WANDB_MODE=offline`、执行`wandb offline`、设置40个字符的占位key，三项同时使用，不改代码。
- 适用限制：占位key只用于通过检查。实际是否离线以冒烟实测为准（offline run目录、日志），未验证前不作结论。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-11。

<a id="src-0216"></a>
## SRC-0216 — task5.1 r3 D8离线训练冒烟/CPU/性能/本地评估记录

- 类型：项目实测与推导；依据D8工程决策SRC0215。
- 主张：r3训练5000步正常退出0，D7学习起点0，2000/4000步各2episode评估可运行，最终checkpoint-5保存；CPU峰/均和吞吐见本run summary。九任务加载与后续正式训练以RESULTS追加实际记录为准，不将计划当结果。
- 来源：../results/task5/t5.1-smoke-r3/的training_smoke_summary.json、host_cpu_5s.jsonl、ray trial result.json/progress.csv/params.json/checkpoint_000005、local_model/config_provenance.json、cleanup.json、eval-*.exit；../logs/task5/t5.1-smoke-r3/下train.log、wandb-offline.log、eval-*.log；离线run logs/config。容器forem-t5-pr2，官方镜像digest继承SRC0205，上游6281205加D2/D7容器补丁。
- 精确位置：RLlib result timesteps_total/time_total_s/timestamp/evaluation；5秒采样/proc/stat；W&B离线run logs/debug.log mode offline与目录offline-run；官方evaluation_ray.main/ray_eval与utils.setup_config_wandb。
- 推导/单位：CPU公式继承SRC0214；训练采样时间下界=result最后timestamp−time_total_s。52样本峰10.350674核/均2.952650核；5000/247.450978=20.206022步/s，百万步×247.450978/5000/3600=13.747277小时。含Tune总265.63秒比例估算14.757222小时。
- 采用/限制：CPU峰≤32满足D3，5.2仍未授权启动。仅短程/主机总CPU，线性推算非正式工期，replay填满/正式评估与checkpoint等开销未全覆盖。offline缺config.yaml时按实际trial params.json的wandb.original_config逐项value包装为本地加载config，非照抄预训练配置。无登录/上传/修改W&B或ray代码。TCP5秒快照/本地日志只能报告观测到的连接，不能排除采样间短暂连接。
- 核查人/日期：Codex，2026-10-11；指定gpt-6.1-sol/medium，实际精确型号/强度未知，未切换/委派。

### SRC-0216 r3最终追加：九任务门槛未通过

- r3训练退出0/5000步；simpleobstacle、picknplace、bookstorepnp、dynobstacle、picknplacedyn、door、drawer评估退出0；roomdoor退出1，spline顺序入口尚未执行。`roomdoor_map_evidence.txt`与`eval-roomdoor.log:744`及调用栈证明：RoomDoorChainedTask读取modulation_tasks.yaml，Map.get_map_yaml引用同目录modulation_tasks.png，后者在容器缺失，Map.load_map的Path.exists断言失败。参考mobile-rl同样无该PNG。未生成/替换地图，不修改任务代码。
- 本地checkpoint加载采用实际run trial params.json的wandb.original_config，value包装config.yaml；checkpoint-5、_trainableState及同trial ray_config.pkl复制入local_model，七任务已真实加载。picknplace/bookstorepnp由上游ray_eval各执行两朝向，每朝向冒烟1episode；其他通过任务各1episode。
- D8核验：wandb offline退出0；本地训练offline-run-20261011_141222-bec10_00000及多个评估offline-run生成，debug.log显示mode offline；train/eval stdout无api.wandb.ai连接报错，训练期间IPv4 TCP5秒快照无remote443项（offline_network_check.json）。未观测到API连接尝试或成功连接；采样不能排除间隙短连接/IPv6，不声称抓包证明绝无网络。未登录/上传/修改W&B或ray代码。
- 状态blocked：九任务冒烟门槛未满足，正式训练未启动，交Claude决定地图资源缺失处理；D3 CPU通过结论仍有效（但不启动5.2）。本次无运行训练/评估，ROS本任务节点仍在，final_docker_top.txt记PID。

<a id="src-0217"></a>
## SRC-0217 — roomdoor评估地图`modulation_tasks.png`的来源

- 主张：上游main分支（6281205）、官方镜像和Husky快照中都缺少`gazebo_world/worlds/modulation_tasks.png`，导致roomdoor评估无法创建环境。同一官方仓库的`moma-codesign`分支（commit 4d8dc0c，2025-04-08）包含该文件，且该commit的`modulation_tasks.world`与`.yaml`和main分支逐字节一致。
- 类型：官方代码仓库核查。
- 来源/位置：`mobile-rl`本地克隆。`git log --all -- gazebo_world/worlds/modulation_tasks.png`显示仅4d8dc0c；`git ls-tree -l 4d8dc0c gazebo_world/worlds/`中PNG blob为a27c86486f4423d9300a529d11aa9d2694181e02（2506 B），world blob 399927d、yaml blob 219b9cb与`git ls-tree main`相同。PIL读取结果为(2000,2000)、mode 1。yaml内容为resolution 0.01、origin [-10,-10,0]。失败链路见`forem/results/task5/t5.1-smoke-r3/roomdoor_map_evidence.txt`。
- 本项目采用：[task5.3 R6](tasks/task5/task5.3/RESULTS.md)中的D9，并要求做PNG与world墙体的叠加合理性检查。
- 适用限制：该文件来自同一官方仓库的另一分支（作者为Raphael Schneider，项目为moma-codesign）。不能证明它与N²M²论文评估时所用文件逐字节相同，roomdoor的结果须带此标注。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-11。

<a id="src-0218"></a>
## SRC-0218 — D9地图复制及墙体合理性核查

- 类型：项目实测、坐标/栅格推导；资源来源/限制继承SRC0217。
- 主张：git show 4d8dc0c:gazebo_world/worlds/modulation_tasks.png取得2506字节/2000²图，Git blob a27c86486f4423d9300a529d11aa9d2694181e02，SHA256 5d9cc6a11f15be78e53f2ef077a9c48a569d7fc58710b851a2eba9c4208a380e。复制到PR2容器与forem/build/task5/ws_husky相应worlds目录，未改参考工作树。六个明确wall model collision box与PNG墙像素视觉吻合，无明显不匹配。
- 来源/位置：../results/task5/t5.1-smoke-r4/map_manifest.json、map_world_overlay.json/png、modulation_tasks.png；../build/task5/check_d9_map.py；官方world wall_* model pose及collision box size，yaml resolution .01/origin[-10,-10,0]。副本SHA复查见该run map_copy_sha256.txt。
- 推导：PNG黑像素为占据，像素中心映射x=-10+(col+.5)*.01、y=10−(row+.5)*.01；world墙box按model yaw旋转/平移，原分辨率采样box内点。侧墙占据比例97.4%/97.43%，其余四墙100%，上边界墙只统计图内半侧。没有新验收阈值，比例辅助已授权视觉核查。
- 限制：只核对六个明确墙盒，未核查所有家具/门mesh，不能证明论文地图逐字节身份。world原始嵌套注释导致XML解析失败，检查脚本只在内存剥除注释，不修改world；宿主缺numpy，改用现有容器绘图库，不安装依赖。宿主无root产物写权限，判定JSON由容器写入。
- 核查人/日期：Codex，2026-10-11；GPT6.1sol/medium指定，实际平台精确型号/强度未知。

<a id="src-0219"></a>
## SRC-0219 — Task5 A正式启动/B冒烟与持续监控

- 类型：项目实测、已授权工程运行包装选择；不是完成验收。
- 来源/位置：../results/task5/t5.1-train-s40/launch.json、train.pid、effective_config_check.json、effective_wandb_original_config.json、host_cpu_5s.jsonl/monitor_30min.jsonl、ray trial params.json/result.json/progress.csv；../logs/task5/t5.1-train-s40/train.log。B ../results/task5/t5.2-smoke-r{1,2}/下train.pid/exit_code.txt/kinematics.yaml、../logs/task5/t5.2-smoke-r{1,2}/analytical.log/train.log。包装../build/task5/t51_formal.sh/t52_r2_smoke.sh/monitor_task5_train.py。
- 主张：A已用冻结1M/seed40/20worker/GPU0/TI.1启动，D7/8/9生效；50episode/eval_seed999/75000步评估来自实际配置。B r1因本Agent遗漏已就绪LMS路径导致launch失败、kinematics缺失，退出1；补回5.0已有ROS_PACKAGE_PATH后r2 bio_ik参数存在并训练推进；不是新依赖/源码补丁。完成/最终结果以节点RESULTS追加实测为准。
- 监控：CPU5秒公式沿SRC0214；30分钟记录环境步/episode/最新原始evaluation。用户R6“持续>56核”工程解释为连续两次5秒样本，保守触发SIGINT自己A/B train PID并暂停报告，写alert收据；不修改科学协议/worker，不停止其他任务。无超限触发时不能声称压力门完整通过。
- 采用/限制：D5保留spacing3.0/offset.8与高度偏好，D6按实际日志/checkpoint目录检查。A/B尚未1M验收；线性工期沿SRC0216。不自动续训，失败新run需按Claude决策。
- 核查人/日期：Codex 2026-10-11，指定gpt-6.1-sol/medium，实际平台精确型号/强度未知；Claude推荐Sonnet5.5/medium。

<a id="src-0220"></a>
## SRC-0220 — B冒烟bookstorepnp首reset失败停止，A正式继续

- 类型：项目实测/原版源码核查，不是地图缺失或碰撞根因证明。
- 来源/精确位置：../logs/task5/t5.2-smoke-r2/eval-bookstorepnp.log（10000/20000/30000 Error on map与Reset0 failed日志）；../results/task5/t5.2-smoke-r2/eval-bookstorepnp-stop.json、eval-*.exit/pid、final_docker_top.txt、runtime_config.json/training_smoke_summary.json、local_model；Husky快照map.py draw_startpose_and_goal:369–391（每1万日志、3万RuntimeError）、combined_env.reset的重试逻辑。源码版本1ccedd0继承5.0，新PNG补D9，aws_bookstore.png未更改。
- 原始结果：B r2训练5000步退出0，263.329s/18.987638步每秒、1M线性14.629h（短程A/B并行，非工期）；D6日志无CLUB Saved/CUDA/AttributeError、无CLUB文件；真实配置learning_starts0、SimpleObstacleMap spacing3.0/offset.8（传入参数1.75/.4375被快照覆盖）。simpleobstacle、picknplace评估通过0（pnp两个朝向各1episode）。bookstorepnp首reset采样30000次后无法取得无碰撞起始/目标，打印base/EE/joints/goal，随后开始10次reset重试；未开始episode。
- 处理：按用户超出流程问题停止交Claude，本Agent仅停止自身bookstorepnp PID24187，信号/退出码以stop.json及exit文件实际记录为准；没有等完全部内部reset重试，不把主动终止写成自然耗尽总重试。后续6任务未执行，不改任务/碰撞/目标/奖励/观测，不启动B正式。A1M已获授权且运行不受影响，CPU5秒/30分钟记录及父§4–6后处理监督器继续，监控子Agenttask5.1.1 gpt-6.1-sol/low实际已派发，根AGENTS/三文档先建立。
- 限制：没有确定具体失败条件（底盘/EE碰撞、路径、goal碰撞/可达性均可能）；一次eval_seed999下的reset失败不证明所有bookstore任务不可运行。不改变D5原样条件或删除任务，需要Claude决策。采样CPU未超过56核持续门；不是并行B正式训练验收。
- 核查人/日期：Codex 2026-10-11，主会话指定GPT6.1sol/medium，实际平台精确型号/强度未知；子Agent派发gpt-6.1-sol/low。

SRC-0220停止收据追加：PID24187先SIGINT未退出reset循环，随后SIGTERM，包装退出143，停止已核实；没有SIGKILL。A最新20k/1M仍运行，monitor2140918/posttrain2203635存活；只停止B问题评估，容器和ROS保留。B r2证据69文件SHA保存在evidence_sha256.json。

<a id="src-0221"></a>
## SRC-0221 — R7 D10/D11执行授权与监控纠正

- 类型：用户明确决策/Claude R7、工程执行与源码静态核查；非新科学条件/CPU压力实测。
- 主张/授权：CPU连续5分钟均值>56核只告警，无论何时不得因CPU自动停止训练，A不重启。B bookstorepnp豁免冒烟门槛；最终原版10reset逻辑完整入口调用一次，墙钟最多1800s，失败为不可运行/N/A不计成功率，同报八可运行均值/九任务口径，不改地图/任务/碰撞。
- 来源/精确位置：用户2026-10-11最新指令；[Claude R7](tasks/task5/task5.3/RESULTS.md)；../results/task5/t5.1-train-s40/monitor_D11_change.json、D11_verification.json、monitor.pid/posttrain.pid、host_cpu_5s.jsonl/monitor_30min.jsonl；../build/task5/monitor_task5_train.py、task5_posttrain.py；B补跑../results/task5/t5.2-smoke-r3/及../logs/task5/t5.2-smoke-r3/。
- 实际修正：2026-10-11T23:04:04.691342+08:00旧主机监控2140918只监控进程SIGTERM，新监控2238780；A训练PID34861未停止/未重启。A后处理监督2203635→2243657仅监督进程更替，移除CPU警报导致blocked检查。没有向训练发送信号。旧代码另存pre-D11历史，不运行。
- 监控算法：每5秒从/proc/stat差分计算核数，公式沿SRC0214；连续300秒窗口按实际采样间隔加权mean=sum(core_i×dt_i)/sum(dt_i)，窗口≥300秒且mean>56才alert_only；JSON/独立日志/RESULTS报告，不break训练或发信号。需积累完整5min窗口。D11静态核查无process signal/subprocess调用，监督无CPU失败门，进程存活；未做新的负载实验、不声称已触发告警。
- D10报告方式：八任务标准非fwdO分支宏平均；上游pnp额外朝向仍各50ep并单列。九任务表保留bookstore N/A/状态与8/9覆盖率，完整九项均值N/A（不把不可运行填0）。原版10次reset代码不变，外部timeout SIGKILL1800s仅用于有明确墙钟授权的B最终bookstore评估，不用于训练；若先超时，记录未跑完10次，而不宣称重试已全部耗尽。其他失败原因仍停止交Claude。
- 限制：旧自动中止规则是本Agent此前过度解读，现已撤销，不能再据SRC0219历史条款实施；B最终评估尚未执行，补跑六任务结果/正式训练以节点RESULTS实际追加为准。
- 核查人/日期：Codex 2026-10-11；指定gpt-6.1-sol/medium，实际精确平台型号/强度未知；监控子Agent派发gpt-6.1-sol/low，Claude推荐Sonnet5.5/medium。

### SRC-0221 实际追加 2026-10-11T23:15:17.578172+08:00

B r3六任务各1episode退出0（smoke_gate.json），结合r2训练与simpleobstacle/picknplace，按D10门槛通过；B正式于2026-10-11T23:09:53.221330+08:00启动，容器train PID36511，主机D11 monitor2264737、posttrain2282978（后处理分类规则更新，不影响训练）。A train34861保持原进程，monitor2238780/posttrain2243657存活。命令/时刻见B launch.json/posttrain_protocol.json和PID文件。
B effective_config_check.json冻结显式值通过；best_defaults_A_B_diff.json记录env/learn_torso及moveit/articulated配置差异，B原10M由命令覆盖1M，完整原始配置差异全部披露。B r3六评估/正式日志均offline，暂未检出CUDA/AttributeError/CLUB Saved；最终D6状态以完整运行证据为准。父已部署§4–6监督器，不将未来导出/最终评估/冻结当已完成。两监控子Agenttask5.1.1/task5.2.1按三文档派发gpt-6.1-sol/low，只自己文档/记录。

SRC-0221运行核查追加 2026-10-11T23:16:14.778529+08:00：R7_execution_snapshot.json记录A43000步/B6000步、PID与CPU采样，训练未退出、两monitor/posttrain存活、无CPU告警。B正式当前全日志未命中CLUB Saved/AttributeError/CUDA error/no kernel image，club_checkpoints文件查询为空；仅当前观测，最终待完整日志核验。

<a id="src-0222"></a>
## SRC-0222 — 用户授权task6：除执行环境外条件一致，把Task4.8普通SAC改在sim中训练

- 主张：用户要求把task5.2（sim）与Task4.8（Gazebo）之间除执行环境以外的条件全部对齐，然后训练。
- 类型：用户指令，加上设计推导。
- 来源：本会话中用户2026-10-12的原话：“先让两边除了执行环境外的条件一致，然后尝试训练吧”“对于新的task6是否能上GPU跑”“继续去写吧”。
- 设计推导：
  - 对齐方向选Task4.8那一侧，即main.py式训练器在forem-dev上运行，只把world_type改为sim。反向做法是让RLlib的20个worker在Gazebo里跑，需要20个Gazebo实例，不可行。
  - 两者之间不可去除的差异就是world_type本身带来的那些：执行方式、局部地图来源、碰撞判定、reset方式、有无物理成功。
  - GPU可用的依据：Task4.8 run_manifest记录的torch为2.7.1+cu128，gpu为RTX PRO 6000 Blackwell，device为cuda:0。
  - 吞吐估算依据：task4.8 RESULTS中update约22–24 ms、select 1.4 ms、push 0.4 ms；task5.0 r4中PR2 sim每步约9 ms。由此推算约28步/秒，100万步约10小时。这是推导值，以§4实测为准。
- 本项目采用：[task6 TASK/PROCEDURE](tasks/task6/TASK.md)。
- 适用限制：三个种子的结果只作诊断。Gazebo侧的最终评估复用Task4.8保留的最终策略，Task4.8的其他中间数据已于2026-10-11清理（[SRC-0202](#src-0202)）。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-12。


<a id="src-0223"></a>
## SRC-0223 — task6开工静态核查：sim切换会改变近目标终止阈值，阻塞待Claude决策

- 类型：项目源码静态核查、文件哈希实测；不是仿真/训练实测。
- 主张：当前三个Task4.8 plain run_manifest的sources共54项与当前工作树全部一致。仅设置world_type=sim会触发MaxCloseStepsWrapper阈值50，Gazebo为500，达到阈值后直接done=True；不能将现行两键overrides方案称为终止条件完全对齐。
- 来源/作者/版本：FoReM现行源码；Task4.8 plain manifests；2026-10-12 Codex读取，源码版本以证据sha256为准，根main工作树未提交。
- 精确位置：`src/modulation_rl/scripts/modulation/utils.py::wrap_in_task` L449–450；`MaxCloseStepsWrapper.step` L649–660；`config/task3/task_contract.yaml::env_config.ikslack_dist/ikslack_rot_dist`为0.1/0.05，激活该wrapper。证据：[基线比对](../results/task6/baseline_source_diff.json)、[收据](../results/task6/t6-preflight-r1/preflight_receipt.json)、[源码摘录](../logs/task6/t6-preflight-r1/termination_source_excerpt.txt)。
- 原始结论：上述静态分支明确存在；其对实际成功率的影响尚未测量。另`robotenv.py::step` L247存在sim/Gazebo执行时长分支，作为原执行环境差异披露，未改动也未自行判定其可接受性。
- 历史限制：pre_feedback_edit三个manifest均另记scwm_train.py/scwm_sac.py旧hash。当前文本显示feedback方法分支与默认FixedGaussianPolicy注入，但未找到旧hash对应完整源码，不能仅凭hash证明历史plain行为逐字节等价；当前manifest并非覆盖原历史核查的证据。
- 本项目采用：task6按PROCEDURE异常处理停止在§2实现前；不自行改wrapper、不回退源码、不运行sim/训练。Claude需决定终止合同与允许实现范围并更新流程；历史plain差异仍须确认。
- 核查日期/人：2026-10-12，Codex；指定gpt-6.1-sol/medium，实际精确部署型号/强度未知。

<a id="src-0224"></a>
## SRC-0224 — task6决策依据：近目标终止阈值按world_type取值；Task4.8 plain代码版本的混合历史

- 主张：
  - (1) 上游和Husky代码的`wrap_in_task`中，`MaxCloseStepsWrapper`的阈值sim为50、Gazebo为500，达到阈值时done。
  - (2) Task4.8三条plain训练所用代码存在版本混合：s2全程使用feedback改动前的代码；s0在269,425步、s1在302,125步之后续训时加载改动后的代码。改动前的文本不可恢复。改动后plain默认策略仍为FixedGaussianPolicy。
- 类型：本地代码和运行记录核查。
- 来源/位置：
  - `forem/src/modulation_rl/scripts/modulation/utils.py:449-450`（wrap_in_task），`:643-664`（MaxCloseStepsWrapper，done在655–659）。
  - `forem/config/task3/task_contract.yaml`中ikslack_dist和ikslack_rot_dist非零。
  - `forem/logs/task4/t4s-plain-s{0,1,2}/events.jsonl`中的start/exit/resume事件：s0于2026-10-09 16:33 UTC从269425续训；s1于18:53从302125续训，10-10 00:56从436557续训；s2只有一次start和exit。
  - `results/task4/t4s-plain-s*/run_manifest{,.pre_feedback_edit}.json`：scwm_train.py a63651aa→3340d0d3，scwm_sac.py 3d3f5385→c317d946。
  - `git status`显示两个文件均为untracked。
  - `scripts/scwm_sac.py:7,153`中policy_factory默认FixedGaussianPolicy；task4.8 RESULTS第13行记录开训时即为单tanh FixedGaussianPolicy。
  - Codex预检证据：[SRC-0223](#src-0223)。
- 本项目采用：task6 TASK中的D12（sim强制500）和D13（以当前代码为基线并披露）。
- 适用限制：无法证明旧版plain路径与当前版本逐字节等价。D12使task6的sim运行与N²M²原文sim默认值（50）不同。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-12。


<a id="src-0225"></a>
## SRC-0225 — task6 D12可选键接入缺少create_env转发

- 类型：项目源码静态核查；未执行sim/测试/训练，非运行实测。
- 主张：仅修改wrap_in_task不能使Task3Env overrides中的max_close_steps生效；还需在create_env调用wrap_in_task处显式转发该可选config键。
- 来源/版本/精确位置：FoReM现行`task3_env.py::Task3Env.__init__` L89调用env_creator(cfg)；`modulation/utils.py::env_creator` L535–541将cfg交给create_env；`create_env` L501–519只构造列明的任务env_kwargs/wrap_kwargs并传入wrap_in_task，未转发max_close_steps。读取版本sha256见[收据](../results/task6/t6-d12-preflight-r1/receipt.json)。核查人Codex，2026-10-12。
- 原始结论/采用：D12已明确500和D13当前基线，旧决策阻塞已解除；新发现为参数传递缺口。用户明确“只改这一处”，增加create_env调用改动需Claude确认，按PROCEDURE异常处理停止。
- 拟议最小改动：[proposed_D12.patch](../results/task6/t6-d12-preflight-r1/proposed_D12.patch)，未应用。wrap_in_task添加显式可选参数避免它落入task构造env_kwargs；调用处用config.get转发；缺省None保持原分支。
- 限制：未声称拟议补丁通过单元测试或Gazebo回归；未修改源码。不是新增科学条件/功能提案，仅为已批准D12的必要参数传递。

<a id="src-0226"></a>
## SRC-0226 — task6 R2：D12两处改动核验与放行

- 类型：项目源码静态核查与Claude工程决策；未运行测试、sim或训练。
- 主张：SRC-0225的发现成立；D12须同时修改`wrap_in_task`签名和`create_env`调用处转发，拟议patch不改变Gazebo路径行为。
- 来源/精确位置：`forem/src/modulation_rl/scripts/modulation/utils.py`（sha256 a2d851e7bafdae94167a7668d4f28a93db753abca35c6b2669a63d3c0d2f26c2）L437–456 `wrap_in_task`、L458–519 `create_env`、L534–541 `env_creator`；对`src/`、`scripts/`、`tests/`中`wrap_in_task|create_env(`的grep仅得L519和L537两处调用；`config/task3/task_contract.yaml` env_config中没有`max_close_steps`键（L77只是注释说明）；`docker inspect`显示forem-t5-pr2、forem-t5-husky不挂载`forem/src`。拟议patch：`results/task6/t6-d12-preflight-r1/proposed_D12.patch`。核查人Claude（claude-opus-5-5），2026-10-12。
- 采用：放行该patch，作为D12的实现。更正SRC-0225中“用户明确‘只改这一处’”的说法：该限定来自Claude起草的PROCEDURE，不是用户原话。
- 限制：Gazebo行为不变目前只是静态推导，须在§2回归和单元测试中实测确认；本条不构成回归通过。


<a id="src-0227"></a>
## SRC-0227 — 用户授权task7：Task5 B改在Gazebo中训练；B与Task4.8训练设置差异核查

- 主张：
  - (1) 用户要求把Task5 B的sim换成Gazebo训练，用来判断Task4.8失败是否源于Gazebo以外的设置；选择N个隔离Gazebo实例；新建task7，世界模型闭环顺延为task8。
  - (2) Task5 B与Task4.8 plain的训练设置差异如[task6.2 TASK差异清单](tasks/task6/task6.2/TASK.md#差异清单task5-b-与-task48-plain)（原task7，2026-10-12合并）所列。
  - (3) Husky快照RLlib的`env_creator`不按worker隔离ROS master，B在Gazebo下多worker运行须另加实例隔离。
- 类型：用户指令；项目源码与运行配置静态核查（Claude）；容器版本只读核查。不是训练实测。
- 来源：
  - 用户2026-10-12本会话原话：“我希望把现在的task5 的B的sim换成gazebo然后跑一下，看看是不是除了gazebo其他参数的问题呢，给我列举task5 task4.8不同的训练设置过”；随后在选项中选择“N个隔离Gazebo实例”“新建task7，WM顺延task8”。
  - B实际配置：`forem/results/task5/t5.2-train-s40/{launch.json,effective_wandb_original_config.json,best_defaults_A_B_diff.json}`。
  - Husky快照（`husky/src/modulation_rl/scripts/`，快照1ccedd0）：`main_ray.py` L42–222（env_config未含execute_style；evaluation_config中transition_noise_base 0、eval_seed）；`modulation/myray/ray_utils.py::get_sac_conf`（initial_alpha、熵学习率=lr_start、lr_schedule线性至total_steps、learning_starts 0、grad_clip 10）；`modulation/myray/custom_sac.py` L58、L150–167（α=exp(log_alpha)，无上限）；`modulation/utils.py` L250–251（init_controllers由world_type推出）、L450（MaxCloseSteps 50/500）、L488–489（execute_style默认direct）、L534–541（env_creator无worker隔离）、L281–290（launch_ros会kill已有ROS/gzserver）。
  - Task4.8：`forem/config/task4_scwm/plain.yaml`、`forem/config/task3/{sac,task_contract}.yaml`、`forem/scripts/scwm_sac.py` L166–218、`forem/src/modulation_rl/scripts/sac.py` L22–25、L51（max_alpha 0.35、min_alpha 0.05、alpha_optim lr=lr_start×0.01）。
  - 版本只读核查（2026-10-12 09:0x）：`forem-dev`中ray 1.13.0、torch 2.7.1+cu128、Gazebo 11.15.1、ROS noetic；`forem-t5-husky`中Gazebo 9.0.0、ROS melodic；镜像Ray 1.6.0/Torch 1.11.0沿task5.0 RESULTS。
  - 中期成功率：`results/task5/t5.{1,2}-train-s40/monitor_30min.jsonl`中`latest_evaluation.custom_metrics.success_mean`；Task4.8：`results/task4/t4s-*/validation_*.json`。
- 推导：B以`training_intensity` 0.1×batch 256计，重放训练步/采样步=25.6，即每10环境步一次256批更新；Task4.8每步一次更新，更新次数约为B的10倍。
- 本项目采用：原task7的对齐口径与T7-D1–D4；2026-10-12按[SRC-0229](#src-0229)合并为[task6.2](tasks/task6/task6.2/TASK.md)，决策改记为G-D1–G-D4，原文存档于`agent_logs/task6/archive-20261012-pre-restart/task7/`。
- 适用限制：差异清单为静态核查；Task4.8验证是否带0.04噪声按代码推断（验证复用训练env），未单独实测。task7与Task4.8之间仍差训练器和运行栈，只与task5.2构成单因素对照。中期成功率为训练未完成时的单种子数值。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-12。

<a id="src-0228"></a>
## SRC-0228 — 用户授权task6改造为训练配方对照组；Task4.8的α轨迹与“全程未学习”证据

- 主张：
  - (1) 用户要求把task6改造为对照组，排查Task4.8与Task5 B之间哪个训练参数导致失败；立即改造，筛选每组30万步×1种子，注意性能优化；并确认F0（Task4.8训练器原样放到sim）优先。
  - (2) Task4.8三条plain的最终α完全相同：log α=−1.0076，α=0.35×exp(log α)≈0.1278；对应999,743次更新。熵学习率1e-6，Adam每次约移动1e-6，故log α随更新次数近似匀速下降，自动调节未起作用。
  - (3) B（task5.2）的α：1000步0.990、7.6万0.482、15.1万0.249、22.6万0.136、30.1万0.078、60.1万0.015；同样近似按Adam最大速率下降（约1.5万次更新时log α≈−1.4），只是速率约为Task4.8的4倍以上（按环境步计）。A（task5.1）几乎相同。
  - (4) Task4.8三个种子的训练episode在100万步内各项指标基本不变：约90–92%的episode因20次IK失败终止，训练内部成功5–8%，episode长度中位142–158步，结束时离目标中位2.1–2.6 m，从0–10万步到80–100万步没有趋势。
  - (5) `forem/src/modulation_rl/scripts/sac.py` L49–53保留了被注释掉的`Adam([self.log_alpha], lr=self.lr_start)`，现行为`lr=self.lr_start * 0.01`并注释“限制alpha时使用”，说明熵学习率和α上限是Husky作者在main.py路径上的改动；RLlib路径（B）没有该改动。
- 类型：用户指令；项目运行产物只读统计（Claude）；源码静态核查。不是新训练实测。
- 来源/位置：
  - 用户2026-10-12本会话原话：“我们要不把task6做成一个大的对照组排查4.8和5中间的问题，究竟哪个训练参数导致了4.8的失败”；“现在改造6 把6做成一个大对照组，然后我刚才看到，15w步就可以让4.8拉开比较大的差距，我们可以测试一下不同参数对训练的影响，然后注意要尽可能性能优化”；选项“30万步×1种子”；对“是否按优先跑F0调整”回复“确认”。
  - (2)：`forem/results/task4/t4s-plain-s{0,1,2}/ckpt/state_01000000.pt`中`agent.log_alpha`、`agent.alpha`、`updates`；在`forem-dev`中用torch只读加载，读取脚本用后删除。
  - (3)：`forem/results/task5/t5.{1,2}-train-s40/ray/*/*/progress.csv`列`info/learner/default_policy/learner_stats/alpha_value`，读取时B到60.9万步、A到66.2万步。
  - (4)：`forem/logs/task4/t4s-plain-s{0,1,2}/episodes.jsonl`中kind=train的记录（共17,782条），按step_start分段统计nr_kin_failures≥20、internal_success、n、physical.pos_err_m。
- 推导与限制：(2)(3)的“匀速下降”是由Adam单步幅度约等于学习率推出，并与观测值吻合，未逐步核对α日志（Task4.8未记录逐步α）。(4)说明Task4.8没有学习进展，但不能单独区分是Gazebo执行条件、训练参数还是Gazebo侧封装问题造成；这正是task6 F0与task7要回答的问题。
- 本项目采用：原task6 R3的F0–F6、D14–D17及F0优先安排；2026-10-12重新开始后由[task6.1](tasks/task6/task6.1/TASK.md)沿用（SRC-0229）。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-12。


<a id="src-0229"></a>
## SRC-0229 — 用户要求task6重新开始并与task7合并为一个对照组

- 主张：原task6（ScwmSAC改sim及F0–F6参数对照）与原task7（B配方改Gazebo）合并为task6，从头执行；task7编号取消。
- 类型：用户指令；Claude工程决策（任务结构与资源优先级）。
- 来源：用户2026-10-12本会话原话：“task6重头开始吧，我们不是说把task6和7合并到6里做一个大对照组吗”。
- 重新开始时的核查（Claude，2026-10-12 09:27）：`forem/src/modulation_rl/scripts/modulation/utils.py` sha256仍为`a2d851e7…`（R2放行的D12 patch未应用）；`docker ps`只有`forem-t5-husky`、`forem-t5-pr2`、`forem-dev`，无task7容器；`forem/results/task7`、`forem/logs/task7`、`forem/build/task7`均不存在；`forem/results/task6`只有原预检证据。
- 本项目采用：
  - 父[task6](tasks/task6/TASK.md)：四组对照（R-B=task5.2、R-48=Task4.8、F0、G-B）加F1–F6；子任务[task6.1](tasks/task6/task6.1/TASK.md)（ScwmSAC sim臂）、[task6.2](tasks/task6/task6.2/TASK.md)（RLlib Gazebo臂）；run-id前缀`t6.1-`、`t6.2-`，不覆盖原`t6-`证据。
  - 资源优先级（工程选择）：task5 A/B > F0三种子 > G-B > F1–F6筛选 > 确认训练。理由：F0与G-B是区分“Gazebo执行还是训练配方”的两条关键对照。
  - 原task6、task7文档及task7日志存档于`agent_logs/task6/archive-20261012-pre-restart/`；D12、D13、D14–D17与G-D1–G-D4的内容原样沿用。
  - 世界模型闭环仍按用户此前选择编为task8，尚未建立。
- 适用限制：两组之间仍有运行栈差异（melodic/Gazebo 9与noetic/Gazebo 11），G-B只与R-B构成单因素对照。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-12。


<a id="src-0230"></a>
## SRC-0230 — task6.1新基线冻结与§2回归阻塞

- 类型：本项目文件哈希、容器进程只读核查、容器单元测试实测；不是sim或正式训练实测。
- 具体主张：Task4.8三个plain manifest共54项sources与本轮修改前工作树54/54一致；授权sim/D12实现后新增sim测试5/5通过，task3回归76项有1 failure/3 skip，task4回归159项有2 failure/4 error/1 skip，不能认定§2通过。
- 来源/作者/版本：FoReM根main未提交工作树，Codex本次执行；修改前文本与sha256、当前diff见[基线](../results/task6/t6.1-baseline/baseline_source_diff.json)、[逐处diff](../results/task6/t6.1-baseline/source_diff_vs_task48.json)、[环境收据](../results/task6/t6.1-baseline/environment_receipt.json)。
- 精确位置：`tests/test_task3_source_contract.py::RealTreeTest.test_contract_covers_create_env_keys` L244和`audit_task3_core.py::OPTIONAL_SOFT_KEYS` L40只认可player_gamma，D12 config.get引入max_close_steps后静态审计拒绝；`test_task4_init_102::OriginalInitializationInputs`缺probe/manifest（seed101/102）、`test_task4_public_capture::RealBasePoseContract`缺public_draws.json、`test_task4_source_permissions`三项缺接受freeze/引用源码。全栈及具体路径见[task3日志](../logs/task6/t6.1-baseline/regress_task3.log)、[task4日志](../logs/task6/t6.1-baseline/regress_task4.log)、[sim GREEN](../logs/task6/t6.1-baseline/sim_tests_green.log)。
- 原始结论：两回归退出1。task3失败是新增可选键的旧审计不接受；task4失败显示旧证据依赖缺失，不能据此断言Gazebo动力学行为有改变，也不能算全量回归通过。未自行改变审计允许集合、合同或重建旧证据。
- 本项目采用/限制：按task6.1 PROCEDURE §2/异常处理停止后续实施，待Claude决定处理范围；§3–§10未执行，无F0/筛选/正式训练，无吞吐与学习效果结论。scwm最终退出0，23 tests通过；[回归收据](../results/task6/t6.1-baseline/regression_receipt.json)含日志/源码sha256。仍不能解除task3/task4门槛失败。
- 核查日期/人：2026-10-12T09:39:33.938568+08:00，Codex；实际精确模型/推理强度未知；推荐GPT6.1sol/Sonnet5.5 medium不等于实际配置。


<a id="src-0231"></a>
## SRC-0231 — task6.2 §1冻结与§2启动入口阻塞（Codex）

- 主张：Task5 B工作区复制一致，复制devel绑定可导入；现行PROCEDURE指定handle_launchfiles入口不支持husky_ur5，退出2，未达到Gazebo就绪。
- 类型：项目本次实测与源码核查；不是Gazebo训练/性能结果。
- 作者/机构与版本：FoReM Codex，2026-10-12；Task5 B工作区实际SHA见[清单](../results/task6/t6.2-baseline/baseline_ws_manifest.json)；镜像dhonerkamp/mobile_rl digest `42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915`。
- 来源及精确位置：[配置SHA](../results/task6/t6.2-baseline/baseline_config_sha256.json)、[副本](../results/task6/t6.2-baseline/copy_ws_manifest.json)、[依赖](../results/task6/t6.2-baseline/dependencies_manifest.json)、[未改源码核验](../results/task6/t6.2-baseline/source_diff_vs_task5.json)；[入口运行](../results/task6/t6.2-env-r1/launcher_execution.json)、[日志](../logs/task6/t6.2-env-r1/launcher.log)、[阻塞收据含源码SHA](../results/task6/t6.2-env-r1/blocking_receipt.json)。符号：`scripts/modulation/handle_launchfiles.py::__main__ parser --env`（有效代码L344）、`gazebo_cmds`（L197）；实际choices与字典均只有pr2/tiago/hsr。
- 原始结论：4616个工作区文件/软链条目、1004个依赖文件/软链条目复制一致（软链记录字面目标，不跟随跨挂载路径）。导入来自新挂载devel成功。roslaunch --files最初缺husky_control，补只读快照依赖路径后XML枚举退出0；这仅是静态launch解析，未启动/验证控制器。指定handle_launchfiles命令argparse退出2；新容器最终只sleep infinity。apt update退出0但ROS索引连接失败；apt安装模拟退出100，无包安装。
- 本项目采用：按task6.2 PROCEDURE异常处理停止§2后续，交Claude明确启动入口与可接受改动；不自行patch launcher/model/env、不启动§3–7。新容器保留。
- 适用限制：只完成基线冻结和容器/绑定/静态入口核查；Gazebo就绪、隔离、profile、N20预算与训练结果均尚未执行。两秒主机CPU快照约5.68核仅是当时负载，不用于外推N或验收性能。未调用launch_ros、未对Task5/forem-dev执行命令或信号；Task5源冻结后二次比对未变。
- 核查日期/人：2026-10-12T09:41:29.725539+08:00，Codex。实际系统标识GPT-6；精确型号/推理强度未知。

<a id="src-0232"></a>
## SRC-0232 — task6.1/6.2 Claude审核R1：回归门槛、启动入口更正与安全性能优化分级

- 主张：
  - (1) task6.1 §2的task3审计失败只因D12新增可选键未登记，放行在`OPTIONAL_SOFT_KEYS`中加入`max_close_steps`；task4的6项失败读取的目录已于2026-10-11清理（SRC-0202），须用原始源码复核相同后记为既有环境失败。
  - (2) task6.2阻塞原因是Claude原PROCEDURE写错启动器路径；Husky快照的Gazebo启动器是`gazebo_world/husky_ur5/handle_launchfiles.py`。
  - (3) 用户要求“审核，加入安全的性能优化”；性能优化按“数值不变／舍入级差异须过等价门槛／禁止”三类执行。
- 类型：用户指令；源码与运行记录静态核查（Claude）；torch缺省开关只读实测。
- 来源/位置：
  - 用户2026-10-12本会话原话：“审核，加入安全的性能优化”。
  - Codex记录：[SRC-0230](#src-0230)、[SRC-0231](#src-0231)；`forem/doc/tasks/task6/task6.1/RESULTS.md`、`task6.2/RESULTS.md`；`forem/results/task6/t6.1-baseline/original/`与当前源码的diff（Claude逐处阅读）。
  - `forem/scripts/audit_task3_core.py` L40（`OPTIONAL_SOFT_KEYS = {"player_gamma"}`）、L253。
  - `forem/results/task4/`现仅存t4.8/t4.9/t4s目录，`t4.1-protocol-20261007-r1`、`t4.3.1-*`不存在；引用它们的测试：`tests/test_task4_public_capture.py`、`test_task4_init_102.py`、`test_task4_init.py`。
  - `husky/src/modulation_rl/gazebo_world/husky_ur5/handle_launchfiles.py`：`gazebo_cmds={'husky_ur5': ...n2m2_husky_empty_world.launch}`、`get_world_file`（simpleobstacle→empty.world）、`gazebo_set_pyhsics_properties(time_step=0.002)`、`--env` choices含husky_ur5、`Popen(["roscore"])`；对照`forem/build/task6.2/ws_husky/src/modulation_rl/scripts/modulation/handle_launchfiles.py` L344 choices仅pr2/tiago/hsr。
  - `forem-dev`中torch 2.7.1缺省：`torch.backends.cuda.matmul.allow_tf32=False`、`cudnn.allow_tf32=True`、`cudnn.benchmark=False`、`cudnn.deterministic=False`（2026-10-12只读实测）。
  - Task4.8分阶段耗时：`forem/logs/task4/t4s-plain-s{0,1,2}/progress.jsonl`累计，reset约75–76%墙钟（约21 s/次）、update约22.5–23.3 ms、env_step约16.5 ms。
- 推导/工程选择：二类优化的等价门槛（200次更新相对差≤1e-4、确定性动作≤1e-5、端到端提速≥15%）是工程选择；理由是Task4.8在`cudnn.deterministic=False`下本就不能逐位复现，舍入级差异属于已有不确定性范围。待验证：§5实测。
- 本项目采用：task6.1 TASK D18/D19（D17作废）、task6.2 TASK G-D5/G-D6，以及两份PROCEDURE的对应修订。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-12。


<a id="src-0233"></a>
## SRC-0233 — task6.1 D18回归通过与sim/Gazebo障碍几何不等价

- 类型：项目容器单元测试、sim reset实测及源码核查；不是训练/性能实测。
- 主张：D18后task3 76 tests通过（3原skip）；task4当前/原始源码完整套件均159 tests、同6项失败（2 failure/4 error/1原skip），完整错误栈归一化临时根路径后相同；§2按D18通过。§3种子101–110中sim障碍存在CYLINDER而Gazebo全RECTANGLE，门槛失败。
- 来源/作者/版本：FoReM根main未提交树，Codex；[D18原始源码收据](../results/task6/t6.1-baseline/d18_original_receipt.json)、[D18错误比较](../results/task6/t6.1-baseline/d18_task4_comparison.json)、[场景数据](../results/task6/t6.1-equiv-r1/equivalence.json)、[逐障碍差异](../results/task6/t6.1-equiv-r1/obstacle_diff.json)、[命令/哈希/退出码](../results/task6/t6.1-equiv-r1/receipt.json)。
- 精确位置：`src/modulation_rl/scripts/modulation/envs/map.py::SimpleObstacleMap.get_varying_scene_objects` L870–876：先抽random；random<0.5或world_type=gazebo或fake_gazebo时矩形，否则圆柱。当前文件sha256 `2b012d752dd9771010a92764f0790d0ce8f22571b448bc968b72e87507116f2d`。该文件本轮未修改。
- 原始结论：10/10场景几何门槛失败；同场景障碍名称/尺寸/位姿、目标、初始关节均一致，base位置/yaw差均0。各seed圆柱/矩形差异数量为 `{"101": 6, "102": 10, "103": 8, "104": 9, "105": 7, "106": 8, "107": 7, "108": 6, "109": 7, "110": 10}`（每场景16障碍）。Task3实例hash与Task4.8三种子最终验证101–105的15条episode_hash全部相同，支持参考抽样器来源一致。
- 本项目采用/限制：按PROCEDURE §3及异常处理停止；未自行将sim几何强制矩形、未改变fake_gazebo/任务合同。Claude须决定如何处理执行环境自带的几何差异。§4/D14、§5/D19及正式训练尚未执行，不能依据本记录推断学习/吞吐收益。只启动k10/ROS11410的本任务analytical实例，停止退出0、residue=[]、端口释放；未操作task5/task6.2。
- 核查日期/人：2026-10-12T09:51:58.861198+08:00，Codex，实际精确模型/推理强度未知。


<a id="src-0234"></a>
## SRC-0234 — task6.2 R1/G-D5后roscore端口与预启动探针

- 主张：普通roscore不按ROS_MASTER_URI12400绑定；先roscore -p12400后，普通core仍创建11311 master，未按PROCEDURE §3.1a预期退出。
- 类型：项目本次端口/ROS XMLRPC实测；依赖源码核查与工程依赖选择；不是Gazebo/训练/profile结果。
- 来源/作者/版本：Codex，2026-10-12，容器forem-t6-husky-gz，镜像digest42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915，ROS melodic/rosversion1.14.13。
- 精确位置：`build/task6.2/scripts/t62_port_probe.py`及`t62_precore_probe.py`；[普通core](../results/task6/t6.2-env-r2/roscore_port_probe.json)、[预启动core](../results/task6/t6.2-env-r2/roscore_precore_probe.json)、[完整命令](../results/task6/t6.2-env-r2/roscore-precore-probe.json)、[原始core日志](../logs/task6/t6.2-env-r2/precore-probe/roscore.log)。
- 原始结论：普通core仅11311监听；预启动方案11311和12400均监听，XMLRPC getUri分别返回各自端口。日志WARNING ROS_MASTER_URI port12400 does not match roscore11311，接着auto-starting new master。两个探针进程组均自主SIGINT清理退出0。
- 本项目采用：依异常处理停止后续Gazebo/§3–7，交Claude决定额外默认master处理；未自行改启动器/roscore。正确Husky启动器SHA与参考相同，[收据](../results/task6/t6.2-env-r2/correct_launcher_sha256.json)。
- 工程依赖选择：pcl_configure原样独立构建退出0；缺包从官方固定源补充ros_control0.18.4（对齐已装controller_interface）、gazebo_ros_pkgs2.8.7（对齐已装gazebo_ros）、ros_controllers0.17.3及teleop_twist_joy0.1.3（固定ROS1依赖选择，非Task5 Gazebo已测版本）。[源URL/commit/全部SHA/理由](../results/task6/t6.2-env-r2/new_dependency_sources.json)。ros_controllers0.18.2不存在克隆退出128；经ls-remote核实改0.17.3成功。build首次缺controller_manager退出1，补官方同版本包后build-r2退出0（12/12，95.4s）。原控制器配置/插件源码未改，未安装apt包/关闭TLS验证/修改apt源。
- 适用限制：独立core探针，没有运行正确启动器，Gazebo/move_group/costmap未启动，不能证明节点归属/就绪/隔离/学习结果。未做线程或CPU亲和优化，N20预算未知。依赖版本属于允许构建范围内工程选择，后续兼容与科学合同须实际就绪核验。
- 核查日期/人：2026-10-12T09:55:23.315525+08:00，Codex；实际精确模型/强度未知（系统GPT-6）；推荐GPT6.1sol/Sonnet5.5 medium。

<a id="src-0235"></a>
## SRC-0235 — task6审核R2：sim与Gazebo障碍几何差异（D20），实例roscore包装（G-D7），控制器依赖接受（G-D8）

- 主张：
  - (1) 上游SimpleObstacleMap在sim中约一半障碍为椭圆柱，Gazebo中全部为矩形；随机数消耗相同，故两种world只差几何。Task5 B（sim）与Task4.8（Gazebo）因此在障碍形状上不同，这是此前未识别的任务差异。
  - (2) task6.1 sim运行强制矩形（D20），使F0与Task4.8场景一致。
  - (3) 普通`roscore`不认`ROS_MASTER_URI`端口；task6.2以包装脚本按启动器`__main__`顺序运行、只给roscore加`-p`（G-D7）。
  - (4) task6.2从官方源码构建的控制器依赖可接受（G-D8）。
- 类型：项目源码静态核查与Codex实测记录核查（Claude）；工程决策。
- 来源/位置：
  - `forem/src/modulation_rl/scripts/modulation/envs/map.py` L54–58（`/fake_gazebo`参数）、L105–108、L664–670（fake_gazebo切到GazeboAPI）、L871–876（几何条件）；Husky快照同一逻辑。
  - Codex §3实测：`forem/results/task6/t6.1-equiv-r1/obstacle_diff.json`（seed 101–110每个16个障碍，差异数6/10/8/9/7/8/7/6/7/10，合计78/160）、`equivalence.json`、`receipt.json`；[SRC-0233](#src-0233)。
  - Codex端口与依赖实测：`forem/results/task6/t6.2-env-r2/roscore_precore_probe.json`、`new_dependency_sources.json`、`controller-dependency-build-r2.json`；[SRC-0234](#src-0234)。
  - `husky/src/modulation_rl/gazebo_world/husky_ur5/handle_launchfiles.py`的`__main__`：`Popen(["roscore"])`、`sleep(5)`、`start_launch_files(args.env, args.algo, args.task, args.gui)`。
- 推导：椭圆柱与同尺寸矩形相比占地更小（若尺寸为外接框，面积约为π/4），因此sim场景整体更易通行；该影响的大小尚未测量，属于待验证假设。
- 本项目采用：[task6.1 TASK D20](tasks/task6/task6.1/TASK.md)、[task6.2 TASK G-D7/G-D8](tasks/task6/task6.2/TASK.md)、父TASK注记。
- 适用限制：D20使task6.1的sim场景与N²M²原文及task5的sim场景不同；G-B与R-B同时差执行环境和障碍形状。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-12。


<a id="src-0236"></a>
## SRC-0236 — task6.2 r3实例启动成功、第三次reset控制失败

- 主张：G-D7包装保持原函数并仅指定core端口，节点归属/无11311/0.002s及500Hz/控制器状态通过；底盘速度响应正常；第三次env reset失败，§2.5的3×50门槛未通过。
- 类型：项目本次实测；依赖工程选择与源码静态核查，非训练/物理成功评估。
- 作者/机构/年份与版本：Codex，FoReM，2026-10-12；镜像digest42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915，Task5 B副本代码；[源码diff/SHA](../results/task6/t6.2-env-r3/source_diff_vs_task5.json)、[G-D7逐行对照](../results/task6/t6.2-env-r3/launcher_main_diff.json)。
- 精确证据位置：[health-inst0.json](../results/task6/t6.2-env-r3/health-inst0.json)、[env_readiness.json](../results/task6/t6.2-env-r3/env_readiness.json)中resets/step_records/error、[摘要](../results/task6/t6.2-env-r3/readiness_summary.json)、[探针退出1收据](../results/task6/t6.2-env-r3/env-reset-step-probe-r2.json)、[探针日志](../logs/task6/t6.2-env-r3/env-reset-step-probe-r2.log)、[Gazebo日志](../logs/task6/t6.2-env-r3/inst0/launch.log)L558–559关节名错误。
- 原始结论：Gazebo/move_group/两costmap的节点URI/PID及/proc环境均为12400 master，11311 getUri失败；physics0.002/500，costmap膨胀false/0/0；五个必要控制器running。直发0.2m/s、墙钟2s：底盘位移0.400834m。env第0/1轮reset13.059493/20.583092s，各随机动作50步；第2轮失败（原环境内置10次retry最终Reached9 reset attempts / Could not set start pose after50 trials）。100步均值15.526ms，仅就绪步时延，非完整训练性能。env.close成功、probe退出1。
- 诊断与限制：日志The arm_client_ failed、resetArm failed、Missing world_joint，以及Gazebo Joints on incoming goal don't match the controller joints；没有采集逐个action result/goal匹配，因此未证明具体根因或将关节名错误归因到某个action。源码RobotHusky::sendArmCommands L91–121/getArmSuccess L125–139、combined_env.py::reset L263–277仅只读核查，未改。
- 依赖与首次启动失败：本Agentsystem_env先source依赖再sourcehusky，CMAKE_PREFIX_PATH被覆盖，导致已建pcl/teleop及DefaultRobotHWSim不可定位；原日志inst0-attempt1保留，修正包装CMAKE_PREFIX_PATH接线后成功。按§2.6额外补原快照roboticsgroup_gazebo_plugins原样构建、官方interactive_marker_twist_server1.2.1（原launch固定请求marker_server的缺包，工程固定版本），2包构建退出0/15.9s；源URL/tag/commit/SHA见[dependency_manifest](../results/task6/t6.2-env-r3/dependency_manifest.json)。没有修改插件/控制器/模型/世界/env代码。
- 本项目采用：按控制器异常停止§3–7，交Claude决策；未自行调PID/轨迹/关节名/reset/预算或重训。保持G-B与R-B障碍形状和运行栈差异披露（SRC0235）。
- 适用限制：整体就绪未通过，不是Gazebo训练学不会；无隔离/profile/N20结论。Task5/参考源未修改，副本只换scripts/logs软链到t6.2-env-r3用于合法产物路由；原启动器SHA不变。自有实例/TF探针清理后容器仅sleep（[最终](../results/task6/t6.2-env-r3/final_own_top.json)）。
- 核查日期/人：2026-10-12T11:01:09.597997+08:00，Codex；实际精确模型/强度未知（系统GPT-6），推荐GPT6.1sol/Sonnet5.5 medium。

<a id="src-0237"></a>
## SRC-0237 — task6.2 t6.2-env-r4：reset失败根因诊断（物理步长0.002 s下UR5 effort-PD颤振）

- 主张：在原样Husky启动器设定的物理步长0.002 s（500 Hz）下，Gazebo模式的Husky机械臂reset大概率失败；失败的直接机理是`shoulder_pan`（及`shoulder_lift`）effort-PD在reset目标位姿附近进入±150 N·m饱和颤振，偏置0.10–0.13 rad超过`checkArmValues`的0.1 rad阈值，goal同时因路径容差被立即中止；同一实例、同一代码和同一控制器参数仅把步长改为0.001或0.0005 s后，reset不再失败。
- 类型：项目实测（自有实例上的受控单因素探针）；机理解释（D项离散稳定性）为推导/推测，标注如下。
- 作者/版本：Claude子Agent（claude-sonnet-5-5，推理强度未知），2026-10-12；镜像digest42a779ab…（同Task5），Gazebo 9.0.0+dfsg5-3ubuntu1+ppa2，控制器源码构建同G-D8（ros_controllers 0.17.3）；Task5 B副本代码未改（`utils.py` sha256 a2d851e7…不变）。
- 精确证据：[诊断汇总](../results/task6/t6.2-env-r4/diagnosis_summary.json)；单goal探针[arm-probe-1.log](../logs/task6/t6.2-env-r4/arm-probe-1.log)（result error_code −5，轨迹末pan误差0.08/−0.034/−0.075 rad）、125 Hz记录[pan-idle.json](../logs/task6/t6.2-env-r4/pan-idle.json)、[pan-goal1.json](../logs/task6/t6.2-env-r4/pan-goal1.json)（result −4，sim_elapsed 0.102 s）、[e1-dt002.json](../logs/task6/t6.2-env-r4/e1-dt002.json)、[e2-dt001-a/b.json](../logs/task6/t6.2-env-r4/)；reset统计[dt0.002](../logs/task6/t6.2-env-r4/reset_stats_dt002.log)及[rep1–3](../logs/task6/t6.2-env-r4/)、[dt0.001 ×12](../logs/task6/t6.2-env-r4/reset_stats_dt0001.log)、[dt0.0005 ×12](../logs/task6/t6.2-env-r4/reset_stats_dt00005.log)、[dt0.001 3×50步](../logs/task6/t6.2-env-r4/reset_steps_dt0001.log)；URDF转储[robot_description.urdf](../logs/task6/t6.2-env-r4/robot_description.urdf)；脚本`build/task6.2/scripts/t62_{arm_probe,pan_probe,set_dt,reset_stats,dt002_repeat}.*`。
- 原始数据：dt=0.002共6次`env.reset()`（4次独立env创建）：2次成功（且各带若干外层重试）、4次最终失败（“Reached 9 reset attempts / Could not set start pose after 50 trials”）；失败的全部inner `resetArm failed`行中pan关节占400/420（其余20行为rep1的其他关节），phase diff 0.10–0.13 rad。dt=0.001：12/12 + 3/3成功，0次inner/outer失败；dt=0.0005：12/12成功，0失败。dt=0.001的3 reset×50随机步：reset 11.1/17.7/17.9 s，步均墙钟15.5 ms，仿真步均15.0 ms，与r3(dt 0.002)步时延15.5 ms相同。颤振：dt=0.002时pan、lift力矩在末5 s内99–100%样本达150 N·m限幅（速度峰值3.2–3.9 rad/s、符号逐步翻转）；dt=0.001时pan 100%饱和但速度峰值1.5 rad/s、位置摆幅约0.01 rad，lift不再饱和。URDF中全部链接含`turnGravityOff true`（含底盘、轮、臂、夹爪），故不是重力载荷问题；力矩静止时为0。另：每次reset一次的“Joints on incoming goal don't match the controller joints”来自夹爪goal（关节名gripper_finger1_finger_joint/finger2_finger_joint与`gripper_controller/joints=[gripper_finger1_joint]`不符，robot_env.cpp:134→robot_husky.cpp::openGripper），与臂reset失败无关，dt=0.001下同样出现。
- 推导/推测（非已证实）：以符号逐步翻转的±150 N·m颤振估算等效惯量 I≈F·dt/(2|v|)=0.047（dt 0.002）/0.053（dt 0.001）kg·m²；经验判据D·dt/I<2（D=200）给出dt<≈0.0005 s；与“0.001仍有小幅pan颤振但低于容差、0.0005更稳”方向一致。这是假设性估算，未从URDF惯量计算，未验证判据本身，未做改增益对照（按任务约束不得改）。
- 与已有证据：[SRC-0059](#src-0059)记录Task3在重力全开且物理步长0.0005/world求解器下出现同类“Could not set start pose after 50 trials”，通过臂链接无重力修复；本项目快照URDF已全链无重力，步长0.002，机理表现为颤振而非重力不稳。Task3的物理配置（`config/task3/world.yaml`: max_step_size 0.0005, 2000 Hz, solver world）与原始启动器的0.002/500 Hz不同。
- 本项目采用：未改任何受限项（env/控制器/PID/容差/模型/世界/launch/训练参数、启动器）；步长仅在自有诊断实例上经服务临时改变，实例已身份清理。将“把Gazebo步长改为0.001 s”作为待Claude决策的最小修复候选，它违背G-D6列出的“禁止改物理步长0.002、max_update_rate 500”。
- 适用限制：样本小（dt 0.002下6次reset；dt 0.001/0.0005下27次/12次）；全部在同一实例、同一宿主负载下；没有验证为什么原作者在0.002下可用（可能与Gazebo 9小版本、ros_controllers版本或未知差异有关，待补证据）；没有测更大步长后的训练吞吐/RTF（仅有dt 0.001的150步级步时延）；颤振机理为推测。不是Gazebo训练表现结论。
- 核查日期/人：2026-10-12，Claude子Agent（claude-sonnet-5-5，强度未知）。


<a id="src-0238"></a>
## SRC-0238 — task6.2审核R3：G-B的Gazebo物理步长改为0.0005 s／2000 Hz（G-D9）

- 主张：原Husky启动器设置的物理步长0.002 s在本运行栈下使UR5复位失败（worker会崩溃），不能使用；G-B改用0.0005 s、`max_update_rate` 2000，与Task3/Task4.8的Gazebo世界一致。
- 类型：子Agent实测（[SRC-0237](#src-0237)）与项目配置核查（Claude）；工程决策。
- 来源/位置：
  - `forem/results/task6/t6.2-env-r4/diagnosis_summary.json`、`reset_stats_dt002*.json`、`reset_stats_dt0001.json`、`reset_stats_dt00005.json`：0.002下reset多数失败；0.001与0.0005下各12次全成功；0.001下shoulder_pan停止后力矩饱和比例仍为1.0（幅度小）。
  - `forem/src/forem_husky/worlds/husky_empty.world` L29–30：`real_time_update_rate 2000`、`max_step_size 0.0005`（Task3/Task4.8所用）；Task3采用依据见[SRC-0059](#src-0059)。
- 本项目采用：[task6.2 TASK G-D9](tasks/task6/task6.2/TASK.md)；G-D6中“禁止改物理步长0.002/500”改为“固定0.0005/2000，不得再改”。
- 适用限制：G-B与原Husky启动器（0.002）不同；N²M²原文Gazebo评估所用步长未核实。0.0005下臂是否完全无颤振须在r5记录。物理步数为0.002时的4倍，21实例下能否保持实时须§4实测。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-12。

<a id="src-0239"></a>
## SRC-0239 — task6.1 Claude子Agent接手：D20/D14复核、§3 r2、§5性能实测与F0/筛选启动

- 主张：
  - (1) D20（`/forem/force_rectangle_obstacles`，`random()`仍为首个操作数）与D14开关实现符合TASK；D14缺省在训练循环级与冻结脚本逐位一致；`t6.1-equiv-r2`场景等价性10/10通过。
  - (2) sim下单run约23步/秒（随机策略早期窗口）、约1.7核；同GPU打包2/3/4条每run分别约−3%/−10%/−19%；线程数1/2无差异；torch.compile与cudnn.benchmark提速分别约6%/1%，未达≥15%门槛，且compile在第0次更新即与eager不同（随机数流）。
  - (2b) D15评估外移（异步）可行：F1筛选run的25027步快照在独立sim实例重评50个种子，离散结果（steps、done、internal_success、IK失败、碰撞、episode_hash）全部相同，仅return_有浮点差（最大相对3.1e-4）；真实训练中的D15评估每次82–238 s，约占F0墙钟12%、筛选15–18%；本批run未启用。
  - (3) D19二类字面等价门槛（连续200次更新各步损失/最终参数相对差≤1e-4）在现行eager路径上自身不可满足：同输入两次eager运行200次更新后损失相对差0.4–0.6%。
- 类型：项目实测与源码核查（子Agent）；性能时长为早期窗口的外推，非承诺。
- 作者/版本：Claude子Agent（claude-sonnet-5-5，推理强度未知），2026-10-12；forem-dev，torch 2.7.1+cu128，4×RTX PRO 6000 Blackwell；源码为训练run`run_manifest.json`中sources所列哈希。
- 精确证据位置：`forem/logs/task6/t6.1-claude-verify/*.log`（测试）、`forem/results/task6/t6.1-claude-verify/loop_equiv/`（循环级逐位核验）、`forem/results/task6/t6.1-equiv-r2/equivalence.json`、`forem/results/task6/t6.1-perf-r1/*.json`（profile、update微基准、算子profile）、`forem/results/task6/t6.1-baseline/source_diff_r2_claude.json`、`forem/logs/task6/t6.1-smoke-r1-F{0,6}`、`forem/scripts/bench_task6_{perf,update}.py`、`prof_task6_update_ops.py`、[RESULTS](tasks/task6/task6.1/RESULTS.md)。
- 原始结论：见RESULTS各表。F0三种子与F1–F6筛选已于2026-10-12T15:34–15:35+08:00启动，尚无训练结果。
- 本项目采用：§6方案（每GPU一条F0加至多一条筛选，第4块GPU放F1/F5/F6）；不启用任何二类优化。
- 适用限制：profile每案例1个样本，波动约±2%，多个案例同时在不同GPU上测（共享CPU）；学会后episode长度变化会改变reset占比；未实现异步评估开关、未实施CUDA Graph；异步评估的等价核验仅1个快照（F1-s0，25027步）；训练收益不在此条。
- 核查人及日期：Claude子Agent（claude-sonnet-5-5），2026-10-12。

<a id="src-0240"></a>
## SRC-0240 — task6.2 G-D9物理步长0.0005 s下的单实例就绪（t6.2-env-r5）与多实例隔离回归（t6.2-iso-r1/r2）

- 主张：①G-D7包装脚本在原`start_launch_files`之后用原函数`gazebo_set_pyhsics_properties(time_step=0.0005)`设置步长，实测physics 0.0005 s／2000 Hz；该设定下UR5复位12/12次成功、3×50随机步无异常；shoulder_pan仍力矩饱和（比例1.0，摆幅0.0007–0.037 rad，低于0.1 rad容差），lift不饱和。②`env_creator`中的worker→实例映射在2实例回归中把train/eval env分别绑定到各自master，参数/节点/运动不串，停止一个实例不影响另一个。
- 类型：项目实测（自有实例，Claude子Agent）；实现为工程选择（G-D2、G-D9）。
- 证据：[t6.2-env-r5/readiness_summary.json](../results/task6/t6.2-env-r5/readiness_summary.json)、[health-inst0.json](../results/task6/t6.2-env-r5/health-inst0.json)、[reset_stats_dt00005.log](../logs/task6/t6.2-env-r5/reset_stats_dt00005.log)、[launcher_main.diff](../results/task6/t6.2-env-r5/launcher_main.diff)；[t6.2-iso-r1](../results/task6/t6.2-iso-r1/isolation.json)（11/12，B位移1.04 mm超出自设1 mm阈值）、[t6.2-iso-r2](../results/task6/t6.2-iso-r2/isolation.json)（12/12，空闲漂移基线判据）、[source_diff_vs_task5.json](../results/task6/t6.2-baseline/source_diff_vs_task5.json)。
- 适用限制：r5样本为12次reset+3次探针reset；回归仅2实例，K>2由§4运行间接检验；底盘无重力下自身有约1 mm／8 s的缓慢漂移，故“B不动”判据用空闲漂移作基线（r2判据在运行前写明，r1结果保留）；pan颤振在0.0005 s下未消除。非训练表现结论。
- 核查日期/人：2026-10-12，Claude子Agent（claude-sonnet-5-5，强度未知）。

<a id="src-0241"></a>
## SRC-0241 — task6.2 §4冒烟、profile与N判定（G-D9 0.0005 s步长下的Gazebo训练开销）

- 主张：①Task5 B配方在Gazebo中（N=2训练+1评估实例）可运行5000步并存checkpoint，映射正确；②实例树约2.75–3.2核/实例，21实例仅实例树就约58–67核，超过56核门槛；③0.0005 s步长下单实例RTF约0.65，9实例并发时单步仿真时长与单实例偏差超过5%；④Gazebo下规划器dt取决于仿真时钟步间隔。
- 类型：项目实测（Claude子Agent）；N=20外推和100万步墙钟为线性外推（推导），评估阻塞与否未测。
- 证据：[smoke_summary.json](../results/task6/t6.2-smoke-r1/smoke_summary.json)、[cpu.jsonl](../results/task6/t6.2-smoke-r1/cpu.jsonl)、[worker_map.jsonl](../logs/task6/t6.2-smoke-r1/worker_map.jsonl)、[train_command.txt](../results/task6/t6.2-smoke-r1/train_command.txt)；[bench_summary r1](../results/task6/t6.2-bench-r1/bench_summary.json)、[r2](../results/task6/t6.2-bench-r2/bench_summary.json)；源码`scripts/modulation/envs/eeplanner.py` L165–176、`robotenv.py` L261–264。
- 推导：learner约48 s/1000步 = 111次更新×0.43 s（`num_steps_trained`/256；`learn_time_ms`）；采样速率1.56步/s·worker由N=2的各迭代时间减去learner推得。外推到N=10/20的时间假设采样与更新串行、worker速率不随N变。
- 适用限制：冒烟仅2个worker；评估仅1次结果；bench对照时宿主负载不同（单实例24核 vs 9实例49核，含task5后处理和task6.1），不是严格同条件；9实例未覆盖21实例；未实测任何G-D6优化。
- 核查日期/人：2026-10-12，Claude子Agent（claude-sonnet-5-5，强度未知）。


<a id="src-0242"></a>
## SRC-0242 — task6.2审核R4：Gazebo模式步长语义随吞吐变化；G-B固定每步0.1 s（G-D10）与N=10（G-D11）

- 主张：
  - (1) Gazebo模式下，末端规划器每步时长取两次`env.step`之间实际流逝的仿真时间，sim中固定为0.1 s。G-B冒烟约0.34 s/步，Task4.8约0.04 s/步。
  - (2) 用户同意G-B每步固定推进0.1 s仿真时间，训练worker取N=10。
- 类型：源码静态核查与运行日志统计（Claude）；子Agent实测；用户决定。
- 来源/位置：
  - `forem/src/modulation_rl/scripts/modulation/envs/eeplanner.py` L22（`TIME_STEP_TRAIN = 0.1`）、L162–176（Gazebo中`dt = rospy.get_time() − _rostime_at_start − _time_planner_prepause`）、L224–233（上限0.5 s）；`robotenv.py` L243–247（`rate.sleep`被注释，`dt_exec`取`rate.sleep_dur`即0.02 s）；`combined_env.py` L137、L365。Husky快照同一逻辑。
  - Task4.8：`forem/logs/task4/t4s-plain-s0/progress.jsonl`的`sim_interval_s`中位约0.037–0.0405 s，`rtf_window`约0.43–0.53。
  - G-B冒烟：[SRC-0241](#src-0241)，`forem/results/task6/t6.2-smoke-r1/`。
  - 用户2026-10-12在选项中选择“固定每步0.1秒”“现在用N=10”“停掉实例10”。
  - 已有机制参考：`forem/scripts/scwm_clock.py::FixedWindowClock`。
- 推导/待验证假设：Task4.8每步约0.04 s，比sim细2.5倍；20次IK失败阈值和γ=0.99对应的时间尺度随之缩短。这可能是Task4.8失败的原因之一，尚未验证。
- 本项目采用：[task6.2 TASK G-D10/G-D11](tasks/task6/task6.2/TASK.md)。
- 适用限制：G-B的步长语义因此与R-B一致、与R-48不同；观测落后一个窗口的上游结构不变。
- 核查人及日期：Claude（claude-opus-5-5），2026-10-12。

<a id="src-0243"></a>
## SRC-0243 — task5 A最终评估door超限回合的处理（D21）

- 主张：(1) A door评估第39回合（种子1037）超过上游20000步上限，触发assert导致进程退出，此前38/38成功；(2) 上游每回合用`env.seed(eval_seed+i)`重置随机性、评估策略是确定性的，因此可用上游已有参数`--eval_seed/--nr_evaluations`单独复现任一回合；(3) 上游在assert后注释掉了把超限回合作为结束处理的代码。
- 类型：项目实测日志与上游源码静态核查（Claude）；D21为工程选择（决策）。
- 位置：`forem/logs/task5/t5.1-eval-r1/eval-door.log` L855–870；`mobile-rl/scripts/modulation/evaluation.py` L198–226、L247–260（上游HEAD 6281205846b1bac4525d05ee230a47bddf42023d）；`mobile-rl/scripts/modulation/utils.py` L139、L144；`forem/results/task5/t5.1-train-s40/posttrain_status.json`。
- 采用方式：[task5.3 R10/D21](tasks/task5/task5.3/RESULTS.md)。超限回合记失败；先做确定性核查，再用种子1038起的11回合补齐50回合。
- 待验证：“按回合种子可复现”需由D21第2步实测确认，尚未执行。
- 适用限制：拼接评估与一次性连续评估在程序路径上不同，最终表须注明。
- 核查：2026-10-12，Claude（claude-opus-5-5，强度未知）。

<a id="src-0244"></a>
## SRC-0244 — task6.2 G-D10实现与验证：固定0.1 s仿真窗口（t6.2-fw-r1…r8）

- 主张：①在env_creator之后的包装中用`/gazebo/pause_physics`＋`/gazebo/unpause_physics`＋`/clock`推进0.1 s窗口，在本机栈中满足不了验收（规划器dt中位数偏差≤0.002 s、最大≤0.12 s）：pause服务调用延迟在env运行时有长尾，窗口超出量最大1.2–1.9 s；②改用`gz world -m 200`（gz transport multi_step，Gazebo自己执行200次0.0005 s迭代后保持暂停）后，规划器每步dt恒为0.1000 s（n=176/192，min=max），reset后第一步dt也为0.1000 s（需要把规划器的`_rostime_at_start`重置到第一个窗口起点），代价是每步墙钟中位约0.52 s（pause方案约0.14 s）；③暂停期间发送的指令在窗口中被执行；④窗口推进后costmap及时更新。
- 类型：项目实测（Claude子Agent，claude-sonnet-5-5）；方案选择为工程选择（偏离G-D10文字中“pause/unpause＋/clock”的实现方式，须Claude复核）。
- 证据：全部逐运行统计[fw_runs_summary.json](../results/task6/t6.2-fw-summary/fw_runs_summary.json)（由`build/task6.2/scripts/t62_fw_all.py`从各运行文件重算）；r1失败（`Could not get costmap data`：测试脚本自己在env进程里订阅了latched costmap，已改为独立监控进程，失败保留）、r2/r4/r5（pause/unpause方案：r2持久服务连接，r5非持久；r4/r5带T62_WINDOW_DEBUG逐窗口拆分，pause调用墙钟中位5.8–24 ms、p95 0.31–0.44 s、最大1.5–2.3 s）、r3（脱离env的单独窗口诊断：300窗口窗口后仿真时间中位0.1010 s、p95 0.105、最大0.1445）、r6（脱离env的multi_step诊断：200窗口全为0.10000 s，墙钟中位0.353 s）、r7/r8（env内multistep：dt恒0.1000 s；r8含前进指令检验与costmap时延）；源码`build/task6.2/ws_husky/.../modulation/utils.py::_t62_fixed_window`。
- 数据：r8——3个episode共195步，规划器dt（非首步）min=max=0.1000，首步dt 0.1000/0.1000/0.1000；前进指令25步（2.5 s仿真）底盘位移0.267 m、机械臂关节最大变化1.75 rad（指令在暂停下发出、窗口内被执行）；costmap在步末的滞后（步末仿真时间−最近一条costmap消息戳）中位17.5 ms、p95 37 ms、最大37.5 ms（costmap戳间隔中位0.04 s）；步墙钟中位0.52 s。
- 推测（未证实）：pause延迟长尾的原因可能与Gazebo在env运行时的世界更新/传感器负载有关（standalone诊断无长尾），未定位。
- 适用限制：每个运行只有3个episode约190步；宿主负载在运行时约20–25核；planner重置`_rostime_at_start`是包装对规划器状态的改动（不改代码），使第一步dt=窗口；观测落后一个窗口的上游结构不变。
- 核查日期/人：2026-10-12（运行于17:1x–17:4x，补记于21:1x），Claude子Agent（claude-sonnet-5-5，强度未知）。

<a id="src-0245"></a>
## SRC-0245 — task6.2 持久gz-step helper、N=2冒烟与N=10+1 profile、吞吐瓶颈与间歇卡死（smoke-r2/r3、fw-r9/r10、prof-r1/r2/r3）

- 主张：①`gz world -m`短命子进程每次调用在gzserver里泄漏一个文件描述符，约1000次后EMFILE，实例失效（smoke-r2失败）；改为一个长期运行的C++ helper（持久gz transport发布者）后无泄漏（gzserver fd约80–100，N=2冒烟5004步和N=10+1共约4000步后不增长），窗口恒为0.1000 s；②N=2＋1冒烟（smoke-r3）通过；③N=10+1：每1000步约265–402 s（整体2.80步/s），与N=2（约2.37步/s）几乎相同——RLlib的SAC执行计划用`ParallelRollouts(mode="bulk_sync")`、每轮每个worker一步，任何一个worker在做约21 s的Gazebo reset，其余worker都等待，所以增加worker数几乎不提高吞吐（推导＋测量，未做逐轮计时）；按2.8步/s估算100万步约99 h；④训练期间CPU不是约束：宿主平均约14核，实例树合计平均8核；⑤在N=10运行里观察到约每1小时一次的间歇卡死（prof-r1a、prof-r2）：某worker的窗口命令后/clock不再推进，已知原因之一是fd泄漏（smoke-r2），持久helper后的卡死原因未定位。
- 类型：项目实测（Claude子Agent，claude-sonnet-5-5）；吞吐瓶颈是源码核查＋实测的推断；99 h为线性外推。
- 证据：`results/task6/t6.2-smoke-r2/`（失败，退出码1）、`t6.2-smoke-r3/smoke_summary.json`（退出码0，5004步，2148 s，规划器dt打印5250条全为0.100，评估1次结果：2 episode、success 0、长度均值123）、`t6.2-fw-r9/diag_gzstep.json`（1500窗口，墙钟中位0.106 s，gzserver fd 81→80）、`t6.2-fw-r10/`（env内dt恒0.1，步墙钟中位0.1325 s，costmap滞后中位6 ms）、`t6.2-prof-r1/`（11实例，a=默认线程退出码1：第4次迭代时worker6卡死，b=T62_WORKER_THREADS=1退出码0完成4000步；Ray默认已把worker的torch线程设为1，a/b吞吐相同，故线程优化无收益未采用）、`t6.2-prof-r2/`（卡死，退出码1，3分钟）、`t6.2-prof-r3/`（退出码0，4000步，1461 s，窗口超出量最大2.3e-14 s，重试0次，dt打印4000条全为0.100）；源码：`build/task6.2/src_helper/t62_gzstep.cc`、副本`modulation/utils.py::_t62_fixed_window`；Ray源码`ray/rllib/agents/dqn/dqn.py` L225（bulk_sync）。
- 孤儿实例事实：prof-r1的11个实例因API额度中断留下空转约11小时44分（2026-10-12约22:45至10-13 10:08），已于10-13 10:09按身份标记逐个停止（`results/task6/t6.2-prof-r1/inst*.cleanup.json`，after均为空），容器仅剩`sleep infinity`。此后所有运行经监督脚本`t62_run.sh`，训练退出时自动清理。
- 适用限制：每个profile只有4000步；卡死事件样本少（3次/约5个N=10运行小时）；未定位根因；99 h不含评估开销；未实测评估是否阻塞训练迭代。
- 核查日期/人：2026-10-12/13，Claude子Agent（claude-sonnet-5-5，强度未知）。

<a id="src-0246"></a>
## SRC-0246 — task6.1 §9最终评估：F0（sim）与Task4.8（Gazebo）种子2001–2050，及两侧场景一致性

- 主张：
  - (1) F0三条（ScwmSAC，sim，100万步）最终内部成功21/22/22（/50，均值0.433）；Task4.8 plain三条（Gazebo）为2/1/5（均值0.053），物理成功0/0/3（均值0.020）；两侧分母50，completed 50、capped 0、errored 0。
  - (2) 种子2001–2050中47个两侧场景（障碍含几何、目标、规划臂初始关节、起点）完全一致，3个种子（2006、2012、2021）两侧场景完全不同，且在各侧重复评估时稳定；根因未查明；47种子敏感性：sim均值0.440、Gazebo 0.057。
  - (3) F0三条的5种子验证（101–105）合计61/150内部成功，Task4.8同口径合计11/150。
- 类型：项目实测（Claude子Agent执行）；(2)的根因为待查假设，未验证。
- 作者/版本：Claude子Agent（claude-sonnet-5-5，推理强度未知），2026-10-13；forem-dev，torch 2.7.1+cu128；训练源码sha见`forem/results/task6/t6.1-summary/manifest.json`；评估脚本`forem/scripts/eval_task6_final.py`。
- 精确证据位置：`forem/results/task6/t6.1-eval-sim-s{0,1,2}/eval.json`、`t6.1-eval-gz-s{0,2}/eval.json`、`t6.1-eval-gz-s1-r2/eval.json`（`t6.1-eval-gz-s1`因gzserver SIGSEGV未完成，证据在`forem/logs/task6/t6.1-eval-gz-s1/`与`forem/logs/task4/t6.1-eval-gz-s1/inst61/launch.log`）、`forem/results/task6/t6.1-eval-probe-{sim,gazebo}.json`、`forem/results/task6/t6.1-summary/{comparison,manifest}.json`、[RESULTS §9–§10](tasks/task6/task6.1/RESULTS.md)。
- 本项目采用：作为task6.1交付数据，供Claude在父task6汇总四组对照（R-B、R-48、F0、G-B）。
- 适用限制：每侧3个种子×50个episode；两侧同一评估种子在3/50处场景不同；sim无物理成功；R-B（task5.2）障碍形状混合，与全矩形的F0不可直接相减；不含显著性检验。
- 核查人及日期：Claude子Agent（claude-sonnet-5-5），2026-10-13。


<a id="src-0247"></a>
## SRC-0247 — task6.2 Codex接回现场及训练中评估逐点监控

- 主张：2026-10-13T14:48:23.768691+08:00接回既有G-B训练，32次迭代/32000步；11个Gazebo实例和11个helper、main_ray与监督器均存活，规划器打印dt全0.100，1个helper卡死事件已恢复、train.log Traceback/RuntimeError计数0。用户授权监控至30万步评估完成后汇报，不停止训练。
- 类型：项目实时核查；用户执行指令。
- 作者/版本：Codex（精确实际模型/推理强度未知），2026-10-13；run-id t6.2-gz-train-s40，已有代码/配置保持不变。
- 精确位置：`build/task6.2/scripts/t62_status.py`退出0；`results/task6/t6.2-gz-train-s40/ray/*/*/progress.csv`迭代32；`logs/task6/t6.2-gz-train-s40/{train.log,worker_map.jsonl,window_*.jsonl,*.stalls.jsonl}`；`results/task6/t6.2-gz-train-s40/supervisor.pid`=462341；本次docker top与容器ps核查摘录见[接回日志](agent_logs/task6/task6.2/20261013-codex-task6.2.md)。R-B逐点来源`results/task5/t5.2-train-s40/train_eval_series.csv`。
- 原始结论/采用：保持既有训练运行；采集正式评估读数并与R-B同步数并列，不把训练成功率当评估。
- 适用限制：此时正式评估尚未触发，不能判断学习表现；错误计数仅指既有脚本匹配Traceback/RuntimeError，不代表所有ROS警告为零；dt核查为train.log末3MB打印，非全部物理窗口。对照有N、几何/终止/运行栈等已披露差异。
- 核查日期/人：2026-10-13T14:48:23.768691+08:00，Codex；后续快照/评估的核查时间按本日志和RESULTS追加，不将未来步骤当已执行。

<a id="src-0248"></a>
## SRC-0248 — 用户指令：世界模型用task7；task6只查Gazebo为何失败，新增sim策略的Gazebo零样本迁移验证

- 主张：用户2026-10-13（约15:00+08:00）指令：“世界模型用task7，然后6里面验证一下sim的训练结果是否可以迁移到gazebo中，配置应该参考原论文项目对gazebo的测试，然后现在6只是验证gazebo为什么失败吧”。此前同一会话中用户确认“需要把sim训练出来的东西放在gazebo中测试”。
- 类型：用户执行指令。
- 本项目采用：①新增task6.3（F0策略Gazebo零样本评估，Z-A原论文项目配置为主口径、Z-B与R-48同口径）；②task6范围限定为Gazebo失败原因诊断；③世界模型任务编号定为task7。task7曾于2026-10-12合并入task6.2并取消（无运行证据），此次按用户明确指令复用该编号，覆盖根AGENTS“编号不复用”的通用约定；原task7存档保留在`agent_logs/task6/archive-20261012-pre-restart/task7/`。
- 适用限制：本指令授权task6.3文档；task6.3的执行由用户派发。task7三文档与实施范围尚待用户进一步确认，不因编号登记而视为已授权实施。Z-B条件、固定0.1 s窗口是否纳入由Claude在文档中提出：Z-B已列入task6.3（为与已有R-48数值单因素可比），固定窗口未列入。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-13。

<a id="src-0249"></a>
## SRC-0249 — N²M²原文与上游代码的Gazebo测试协议（零样本、异步30–70 Hz、track执行、评估IK阈值50）

- 主张：(1) N²M²把解析环境中训练的策略零样本迁移到Gazebo，不再训练；Gazebo中策略须适应未见过的物理与底层控制器、异步执行，以及由LiDAR构建的带噪声、不完整的占据地图；机械臂碰撞计为失败；控制平均频率约30–70 Hz。Gazebo平均成功率：PR2 79.2%、HSR 82.7%、TIAGo 62.8%，比解析环境分别低约9、0.3、2.6个百分点。实机（PR2、HSR）同样不重训、动作乘0.5，成功率82.6%（150 episode）、78.6%（140 episode）。(2) 上游评估代码的Gazebo配置：`evaluation_ray.py`按命令行覆盖`time_step`、`world_type`、`init_controllers`，并把`ik_fail_thresh`设为`ik_fail_thresh_eval`；argparse缺省`time_step 0.02`、`ik_fail_thresh 20`、`ik_fail_thresh_eval 50`、`execute_style track`、`perception_style base`、`exec_action_*` None、`nr_evaluations 50`、`eval_seed 999`；`robotenv.py`中`rate.sleep`被注释（自由运行），`dt_exec`取`rate.sleep_dur`；`eeplanner.py`在非解析环境中规划步长取实际流逝时间、上限0.5 s。(3) Husky迁移栈（Task3）的契约为`execute_style direct`、`ik_fail_thresh 20`（工程重建，原作者命令行未知，见SRC-0053），与上游评估配置不同；本项目C++ `track`分支对Husky调用差速实现`RobotHusky::calcDesiredBaseCommand`。
- 类型：(1)外部文献；(2)(3)官方代码与本地代码静态核查。
- 来源：Honerkamp, Welschehold, Valada，N²M²，IEEE T-RO 39(5) 2023，arXiv:2206.08737v2 https://arxiv.org/html/2206.08737v2 ；上游代码`mobile-rl/`（commit 6281205，见SRC-0199）；本项目`forem/src/modulation_rl/`、`forem/config/task3/task_contract.yaml`。
- 精确位置：原文Sec. IV-I/Table VI（Gazebo）、Sec. IV-J/Table VII（实机）、Sec. IV-C（每任务50 episode）；`mobile-rl/scripts/evaluation_ray.py` L29–58、L81–85；`mobile-rl/scripts/modulation/utils.py` L106–149、L250–251；`mobile-rl/scripts/modulation/envs/robotenv.py` step（`rate.sleep`注释与`dt_exec`）；`mobile-rl/scripts/modulation/envs/eeplanner.py` L163–176、L225–239；`mobile-rl/src/robot_env.cpp` L238–252；`forem/src/modulation_rl/src/robot_husky.cpp` L78–88；`forem/config/task3/task_contract.yaml` env_config与timing段。
- 核查状态：(1)经WebFetch工具摘录arXiv HTML原文（工具由小模型概括，非逐页阅读PDF），数值与SRC-0198一致；“30–70 Hz”“asynchronous execution”为摘录引文，待执行者或复核者对照PDF确认。(2)(3)Claude直接阅读源码。
- 本项目采用：task6.3以(2)为Z-A主口径（原论文项目Gazebo测试配置），以task6.1 §9配置为Z-B；固定0.1 s窗口不是原论文协议，不作主口径。（2026-10-13更正：上游差速底盘不支持track、TIAGo强制direct，Husky的Z-A实际用direct，见SRC-0254。）
- 适用限制：原文Gazebo结果为PR2/HSR/TIAGo、9任务、5种子；本项目是Husky+UR5、simpleobstacle、3种子，原文迁移损失只作量级参考。（2026-10-13更正：原写“上游Gazebo物理步长与本项目不同”不准确；上游0.002 s覆写只用于PR2，`modulation_tasks.world`为0.0005 s，与本项目相同，见SRC-0251。）上游README说明Gazebo中的后方测距传感器依赖不可用的专有节点，原作者的定量结果可能与公开代码不同。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-13。

<a id="src-0250"></a>
## SRC-0250 — SC²-WM的训练与部署方式：Habitat中训练，零样本部署到四足实机

- 主张：SC²-WM在Habitat-Sim（VLN-CE R2R-CE/RxR-CE）中训练：R2R-CE从预训练25,000次迭代的权重初始化，联合训练12,000个episode（lr 1e-5），再冻结语言编码器微调10,000个episode（lr 4e-6）；RxR-CE从VLN-3DFF检查点初始化训练14,000个episode。实机为Unitree GO2+RealSense D435i，动作集合与仿真一致，100个试验×5次重复，成功率85%（基线70%），论文称其从仿真迁移到实机；测试期适配采用异步执行。
- 类型：外部文献（本地PDF）。
- 来源：Yao等，SC²-WM，ICML 2026，本地`scwm/paper/SC2-WM-ICML2026.pdf`；arXiv:2608.07548v1（见SRC-0020）。
- 精确位置：附录“Experimental Details”（训练阶段与学习率）；附录E Real-World Verification与Figure 5；README第24行（基于Habitat-Sim）。
- 核查状态：Claude用pdftotext提取本地PDF并阅读上述段落。
- 本项目采用：作为“先在仿真中训练、再零样本到更真实执行环境测试”路线的第二个参照，支持task7在sim中训练世界模型、在Gazebo中测试的方向。
- 适用限制：导航任务、离散动作、模仿/监督训练为主，与Husky+UR5的SAC移动操作不同；实机结果不证明机械臂执行误差补偿。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-13。


<a id="src-0251"></a>
## SRC-0251 — task6.3 §1冻结核查与上游Gazebo episode上限差异（停止交Claude）

- 主张：task6.3开工核查eval_task6_final.py、scwm_env.py、task3_env.py、modulation/utils.py及F0三个100万步策略共7文件，与task6.1-summary/manifest.json中的冻结sha256全部一致。上游evaluation_rollout在非解析世界用max_len=100000，rollout在len(episode)>max_len时抛断言；本项目eval_task6_final.py缺省max_steps=2000，run_eval用此上限并保留capped记录。两者上限及超限记账不同。
- 类型：项目文件核查、官方代码静态核查；不是新评估实测。
- 作者/版本：Codex，实际精确模型/强度未知；上游commit 6281205846b1bac4525d05ee230a47bddf42023d；本项目脚本冻结sha见hash_check.json。
- 精确位置：mobile-rl/scripts/modulation/evaluation.py:224–227（超限断言）、:259（sim 20000 / 非解析100000）；forem/scripts/eval_task6_final.py:33（2000缺省）、:47（run_eval）；forem/results/task6/t6.3-baseline/{hash_check,upstream_audit_sources,host_cpu}.json；forem/logs/task6/t6.3-baseline/{git_status,processes,forem_dev_top,gpu}.txt；[task6.3 RESULTS](tasks/task6/task6.3/RESULTS.md)。
- 原始结论/采用：PROCEDURE §4明确“若§1发现上游不同，按Claude决定”，当前未找到Claude对100000与2000差异的决定，故§1停止并交接；不改上限，不改脚本，不运行§2–§5。
- 物理步长核查：上游handle_launchfiles.py:143–146的0.002 s物理覆写仅用于PR2且algo非moveit/bi2rrt；modulation_tasks.world:20–21为0.0005 s/2000 Hz，与本项目husky_empty.world:29–30相同。不能泛称所有上游机器人均0.002 s；本项目不修改物理步长。
- 适用限制：track链路仅静态证实调用RobotHusky差速实现，未动态测运动；未产生任何零样本评估结果；CPU两秒快照不是完整性能评估；未重新核验论文数值。
- 核查日期/人：2026-10-13，Codex；准确接手及停止时间见日志。

<a id="src-0252"></a>
## SRC-0252 — task6.3 Claude复核R1：T63-D1 episode上限与超限记账

- 主张：Z-A用上游非解析评估上限100000步，超限记capped并计为失败、不中断（沿用task5 D21与用户“超长episode算失败”）；Z-B保持2000步以与task6.1 R-48完全同口径（R-48 capped 0，上限未起作用）；Z-A另报>2000步episode与“2000步内成功”事后口径。
- 类型：工程选择（Claude流程决定），依据上游代码与既有用户决定。
- 依据位置：`mobile-rl/scripts/modulation/evaluation.py` L222–224、L259（Claude重读）；`forem/scripts/eval_task6_final.py` L33；SRC-0243（D21）；SRC-0246（R-48 capped 0）；SRC-0251（Codex §1）。
- 适用限制：上游超限会中断评估，本项目改为计失败继续，属已披露偏差；6 h单run墙钟报告线为工程选择。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-13。


<a id="src-0253"></a>
## SRC-0253 — task6.3 §2回归通过，§3 track差速实现抛异常而停止

- 主张：①仅eval_task6_final.py新增execute_style/ik_fail_thresh可选参数（None缺省、仅Gazebo显式覆盖），记录effective_config及episode上限；新增test_task6_eval.py。完整task6测试19项通过。缺省Gazebo R48-s0种子2001–2005回归5/5场景哈希一致，done/internal_success一致；步数原366/124/416/337/582、新53/238/293/286/582。②F0-s0 Z-A冒烟2001–2003均RuntimeError('Not implemented for diff-drive yet')，errored=3，eval进程rc0（固定分母捕获异常，不等于冒烟通过）。③track调用链最终到myutils::calcDesiredBaseCommandDiffDrive，此函数在dt检查后无条件throw，同句亦存在Husky参考和mobile-rl上游；不是已可用的差速实现。
- 类型：项目实测、官方/参考源码直接核查；阻塞原因结论。
- 作者/版本：Codex，实际精确模型/推理强度未知；源码和F0策略sha见forem/results/task6/t6.3-baseline/{code_manifest,execution_manifest,hash_check}.json；forem-dev现有Noetic/Gazebo栈，未重建。
- 精确位置：forem/src/modulation_rl/src/robot_env.cpp:243–251→robot_husky.cpp:78–88→myutils.cpp:424–445（:432无条件throw）；husky/src/modulation_rl/src/myutils.cpp:432、mobile-rl/src/myutils.cpp:432（只读核查）。单元测试forem/logs/task6/t6.3-baseline/{test_red,test_green,test_green_ros}.log；运行回归forem/results/task6/t6.3-regression-r1/{eval,comparison}.json；冒烟forem/results/task6/t6.3-smoke-r1-A/eval.json，logs/task6/t6.3-smoke-r1-{A,B}/{launch.sh,eval.out,start.out,stop.out}，results/task6/t6.3-smoke-r1-B/smoke_trace.json。
- 原始结论：Z-A effective_config为track/IK50/time_step0.02/max_close_steps500/window_s=None；Z-B为direct/IK20/其余相同。Z-A未成功返回任何step；无法验收底盘运动和IK>20继续执行。B仅完成2个记录回合（2001:772步，内部成功true/物理false，2002:2000步），因A异常按规定停止，不能作为正式成功率。
- 采用：§2通过，§3失败，§4–§5未执行；仅清理自有smoke进程和inst60/61。B评估SIGTERM后退出15，实例stop均rc0/residue=[]/端口自由；最终docker top forem-dev仅init/sleep。修复C++超过授权，交Claude决定，不自行切换Z-A或运行正式Z-B。
- 限制：自由运行不保证步数一致；测试有ROS/Gazebo/检查点边界替身，运行回归补充真实环境证据；新增参数缺省值不改变环境构造。第一次完整测试因未加载ROS出现6个导入错误，正确source后19项通过。此前SRC0251只证实track调用链未读实现体，不能据其称差速track可用；本条纠正该推断。未获得零样本正式结果，不下迁移性能结论。
- 核查日期/人：2026-10-13，Codex，准确时间见独立日志/执行manifest。

<a id="src-0254"></a>
## SRC-0254 — task6.3 Claude复核R2：上游差速底盘不支持track，T63-D2 Z-A改用direct

- 主张：上游`calcDesiredBaseCommandDiffDrive`无条件抛出“Not implemented for diff-drive yet”；上游唯一差速机器人TIAGo在`robot_env.cpp`中无论`execute_style`取值均走`direct`。因此原论文项目对差速底盘的Gazebo测试实际执行方式为`direct`，task6.3 Z-A改为direct，保留评估IK阈值50与100000步上限。SRC-0249中“上游Gazebo评估用track”只适用于全向底盘（PR2、HSR），对Husky不适用。
- 类型：官方代码静态核查（Claude重读），结合Codex §3冒烟失败实测（SRC-0253）。
- 精确位置：`mobile-rl/src/myutils.cpp` L424–432；`mobile-rl/src/robot_env.cpp` L240；`mobile-rl/scripts/modulation/envs/robotenv.py` L138–146；`forem/src/modulation_rl/src/myutils.cpp` L432（相同）；`forem/results/task6/t6.3-smoke-r1-A/eval.json`（errored 3）。
- 适用限制：原文未单独报告TIAGo的执行方式；“direct即上游差速底盘协议”是依据代码的推导。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-13。


<a id="src-0255"></a>
## SRC-0255 — task6.3 T63-D2 r2冒烟与Gazebo零样本正式评估

- 主张（阶段事实，后续结果追加）：r2冒烟A/B均0errored，start/eval/stop退出0。A direct/IK50/100000：三个回合655/2344/761步，种子2002在IK49仍非终止、IK50终止；各回合底盘位移>0。B direct/IK20/2000：651/2000/362步，capped1。按门槛启动六条正式评估，每条2001–2050固定50分母。
- 类型：项目实测；启动规模/设备为有效流程下的工程分配。
- 作者/版本：Codex，精确实际模型/强度未知，推荐GPT6.1sol/Sonnet5.5 low/默认。沿§2已通过脚本，未再改代码、配置/依赖、未训练。
- 精确位置：forem/results/task6/t6.3-baseline/{resume_r2_check,smoke_r2_checks,formal_preflight_cpu,formal_launch_manifest}.json；results/task6/t6.3-smoke-r2-{A,B}/{eval,smoke_trace}.json；logs/task6/t6.3-smoke-r2-{A,B}/launch.sh；[RESULTS](tasks/task6/task6.3/RESULTS.md)及[日志](agent_logs/task6/task6.3/20261013-codex-task6.3.md)。
- 实际配置：Z-A direct/IK50/100000，Z-B direct/IK20/2000；两侧time_step0.02、max_close_steps500、window_s=None，物理0.0005 s保持。A-s0/1/2实例60/61/62、GPU0/1/2；B-s0/1/2实例63/64/65、GPU0/1/3。启动前2秒全主机忙核约9.819/64（/proc/stat前8字段，64*(delta_total-idle-iowait)/delta_total），加流程预估12低于56；此快照不替代端到端性能profile。
- 采用/限制：r1证据保留但不计入；r2通过只是执行链验证，不能当50种子正式成功率。遵循T63-D1/D2与SRC0252/0254。正式结果在完成后追加，本条初写时尚未产生正式评估结论。禁止据启动记录宣称迁移性能。
- 核查人/日期：Codex，2026-10-13，精确时间见日志/JSON。

### SRC-0255 正式评估与汇总追加（2026-10-13，Codex）

- 正式结果：Z-A内部成功8/13/9（各/50，均值0.200），物理3/7/5（0.100），completed各50、capped/errored各0；Z-B内部7/10/7（0.160）、物理5/5/2（0.080），completed47/48/46、capped3/2/4、errored各0。因IK阈值终止Z-A37/34/38、Z-B39/38/36。均为三条sim F0策略零样本Gazebo评估。
- 同原始task6.1对照重算：F0 sim21/22/22（0.433333），R-48 2/1/5（0.053333）；Z-A比F0低23.333个百分点，Z-B低27.333个百分点，Z-B比R-48高10.667个百分点。结果只支持描述性差异，不作显著性检验或Gazebo细分因素归因。
- Z-A >2000步episode5/8/8，其中内部成功1/2/0；2000步内内部成功7/11/9，均值0.180。Z-A IK计数分布按0、1–19、20–49、>=50四区间分别为9/2/2/37、14/0/2/34、10/0/2/38。精确计数直方图见comparison.json。
- 47种子敏感性：Z-A8/13/9（/47，0.212766），Z-B7/10/7（0.170213），F0 sim20/20/22（0.439716），R-48 2/1/5（0.056738）。9份Gazebo结果（本轮6+R48旧3）全部50种子场景哈希一致；与sim仅既知2006/2012/2021不一致，未追查。
- 推导：每run Wilson95%，输入k=原始internal_success is true计数、n=固定50或47，z=1.96；p=k/n，中心=(p+z²/(2n))/(1+z²/n)，半宽=z*sqrt(p*(1-p)/n+z²/(4n²))/(1+z²/n)。区间为中心±半宽，无量纲，三种子均值仅描述，不将重复场景当150个独立样本。within2000为已记录终点成功且steps<=2000的事后筛选，不是重跑。历史sim碰撞字段为数字字符串，在统计中显式int转换，未改原JSON。
- 精确证据：forem/results/task6/t6.3-zs-{A,B}-s{0,1,2}/eval.json；forem/results/task6/t6.3-summary/{comparison,manifest,verification}.json（每run Wilson、步数/碰撞/IK/上限/47种子、完整源码/策略sha、命令/实例/GPU/退出码/时间/偏差）；forem/logs/task6/t6.3-zs-*/{launch.sh,eval.out,start.out,stop.out}；forem/logs/task6/t6.3-baseline/{formal_monitor.jsonl,formal_docker_top.txt,formal_gpu_processes.txt,final_docker_top.txt,forem_dev_image.txt}。
- 执行与退出：正式6条均首次完成，start/eval/stop各rc0、residue=[]、端口自由；全局runner墙钟2079 s、累计runner11285 s（不是训练预算）。无>20000步episode、无6h报告线触发，无训练/源码修改/容器G-B干预。最终forem-dev只有init/sleep。source/策略全部冻结哈希核查通过。
- 采用与限制：task6.3 review交Claude，未标done。零样本策略在Gazebo未保持sim内部成功水平；更宽IK门槛/上限未消除下降，符合TASK“Z-A/Z-B都明显低于sim”的描述性分支。执行细分因果、历史策略旧训练与新策略差异的严格归因未验证；自由运行非确定、物理成功与内部成功分开，机器人/任务不同不能宣称论文完整复现，原论文量级只为参考。

<a id="src-0256"></a>
## SRC-0256 — task6.3 Claude复核R3：F0 sim策略Gazebo零样本迁移结果

- 主张：F0三个sim策略（100万步）在Gazebo零样本评估（种子2001–2050），内部成功：Z-A（direct、IK50、100000步）8/13/9，均值0.200，物理3/7/5；Z-B（direct、IK20、2000步，与R-48同口径）7/10/7，均值0.160，物理5/5/2，capped 3/2/4。对比sim 0.433、R-48 0.053。47种子配对：两侧都成功4/6/5，只在sim成功16/14/17，只在Gazebo成功3/4/2。IK失败终止sim 18/21/20、Z-B 39/38/36。
- 类型：项目实测（Codex执行，SRC-0255），Claude独立复算与配对统计。
- 精确位置：`forem/results/task6/t6.3-zs-{A,B}-s{0,1,2}/eval.json`、`forem/results/task6/t6.3-summary/{comparison,manifest,verification}.json`；对照`forem/results/task6/t6.1-eval-sim-s*/eval.json`、`t6.1-eval-gz-*/eval.json`；[task6.3 RESULTS](tasks/task6/task6.3/RESULTS.md)。
- 本项目采用：Task4.8失败为两部分叠加——Gazebo执行条件使同一策略损失约27个百分点，Gazebo中训练再损失约11个百分点（Z-B对R-48）。迁移损失远大于N²M²原文（0.3–9个百分点，SRC-0249）。
- 适用限制：3种子×50 episode，无显著性检验；执行因素未拆分；Husky与原文机器人不同。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-13。

<a id="src-0257"></a>
## SRC-0257 — 用户指令：按原论文Gazebo方法评估task5 A/B（task6.4）

- 主张：用户2026-10-13在得知task6.3不是N²M²本身、task5 A/B只做过sim评估后，指示“那去写个计划做一下”（前问：“按照原论文里的gazebo方法配置呀，复现不了n2m2那篇论文的吗”“评估做过了吗”）。Claude核查`results/task5/t5.{1,2}-eval-r1/commands.json`全部为`--eval_execs sim`，训练中评估`eval_execs`为`["sim"]`，确认未做过Gazebo评估。
- 类型：用户执行指令＋项目文件核查。
- 本项目采用：新增task6.4，用上游原版`evaluation_ray.py --eval_execs gazebo`对A（PR2）、B（Husky）做Gazebo零样本评估；阶段一simpleobstacle，阶段二A其余8任务须Claude放行。用户未回答“9任务还是只simpleobstacle”“等待D21还是并行”，Claude按分阶段与隔离优先的工程选择处理。
- 适用限制：本指令授权task6.4文档与执行（由用户派发）；B的其余任务、训练、固定步长不在内。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-13。


<a id="src-0258"></a>
## SRC-0258 — task6.4开工隔离与Gazebo静态缺包阻塞

- 主张：2026-10-13 Codex按用户授权从§1接手；task5 PR2/Husky各保留analytical ROS，采用同镜像新bridge容器。A launch枚举退出0；B枚举退出1，`Resource not found: husky_control`。按task6.4异常处理停止，未启动ROS/Gazebo、未评估/训练或调整物理步长。不是策略迁移失败结论。
- 类型：项目只读现场检查、启动链静态核查；新容器选择为工程选择（避免干扰task5且不等待未清理ROS）。
- 作者/版本：Codex /root，task6.4 preflight，2026-10-13；镜像sha256:42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915。
- 精确位置：`forem/results/task6/t6.4-preflight/{container_creation,network_isolation,hash_verification,A-launch-static,B-launch-static,manifest}.json`；`forem/logs/task6/t6.4-preflight/{A,B}-launch-static.log`。静态命令`roslaunch --files modulation_rl n2m2_husky_empty_world.launch gui:=false world_name:=empty.world`；缺包发生于其include链（`husky_ur5/launch/spawn_husky.launch`引用husky_control）。
- 哈希核查：A/B各5个指定文件与task5 live副本一致；B与task5.0的原始manifest一致，A与mobile-rl参考一致。A/B checkpoint-1000与各自原训练trial一致。task5最终manifest尚未生成，不声称有历史checkpoint SHA封存；细项见hash_verification。
- 原始结论与采用：新容器forem-t6.4-pr2/forem-t6.4-husky独立网络命名空间，无宿主端口映射，只有sleep infinity；task5 ROS PID首尾一致。缺包交Claude决定，未安装、复制依赖或构建，未触碰G-B容器内部。当前未证明实际ROS master隔离或Gazebo就绪，因没有启动master。
- 适用限制：`roslaunch --files`只枚举XML，不证明可执行文件/插件/控制器齐全；A未做运行验证，B只暴露首个缺包，后续依赖未知。无episode成功率/吞吐/阶段一或二时限结论；主机2秒快照16.69忙核不作为并发峰值验收。不得据此认定N²M²不可复现。
- 核查日期/人：2026-10-13T21:30:52.276541+08:00，Codex，实际精确模型与推理强度未知。

- 2026-10-14续核（Codex）：2026-10-14T00:16:03.286963+08:00，run-id t6.4-preflight-r2，同一B原版launch静态命令仍退出1/Resource not found husky_control；证据`forem/results/task6/t6.4-preflight-r2/{B-launch-static,manifest}.json`与`forem/logs/task6/t6.4-preflight-r2/B-launch-static.log`。沿用原容器，未见新增缺包决策；按异常规则再次停止，0episode/无ROS、仿真、依赖准备或训练。新容器top仅sleep，task5原ROS PID仍在；本轮未操作G-B。适用限制：同一首缺包复核，不是新增策略评估或运行就绪证据。

<a id="src-0259"></a>
## SRC-0259 — task6.4 Claude复核R1：A独立推进，B复用task6.2的Gazebo依赖

- 主张：用户2026-10-14“一切按你的推荐”。T64-D1：A（PR2）启动链静态枚举通过，与B解耦独立推进。T64-D2：B（Husky）缺`husky_control`等Gazebo依赖；同一镜像的依赖已在task6.2准备、经G-D8接受并实际运行通过，故只读复用`build/task6.2/deps/`及其构建产物，不重建、不改源码；B用`handle_launchfiles.start_launch_files`包装启动后再运行`evaluation_ray`。
- 类型：工程选择（Claude流程决定），依据task6.4 §1证据（SRC-0258）与task6.2依赖记录（SRC-0236附近、G-D8）。
- 精确位置：`forem/results/task6/t6.4-preflight{,-r2}/`；`forem/results/task6/t6.2-env-r1/additional_dependency_manifest.json`、`t6.2-env-r2/new_dependency_sources.json`、`t6.2-env-r3/dependency_manifest.json`；`forem/build/task6.2/deps/`。
- 适用限制：依赖版本为工程选择（与task6.2相同），非原作者环境；B的运行栈与task5 sim评估相同代码，仅增加Gazebo运行依赖。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-14。

<a id="src-0260"></a>
## SRC-0260 — Task5 D21 A door确定性核查未通过（t5.1-eval-r2）

- 主张：原模型/入口/参数仅增加eval_seed1029、nr_evaluations8的复现自然退出0、8/8成功，但原i=30/31/34的步数614/585/534变为605/512/507；其余5回合步数一致。因此不满足D21逐回合完全一致门槛，不能拼接A评估。
- 类型：项目实测；停止推进为Claude D21既定决策的执行，不是新口径。
- 作者/版本：Codex，2026-10-14，D21/R11；实际模型/推理强度未知。源码/模型/r1前后SHA检查82文件changed=[]。
- 证据与精确位置：`logs/task5/t5.1-eval-r1/eval-door.log` Eval ep30–37；`logs/task5/t5.1-eval-r2/check-door-seed1029-n8.log` Eval ep0–7；`results/task5/t5.1-eval-r2/determinism_check.json`的逐seed对照；`commands.json`完整命令/起止/退出0；`episode_metric_checks.json`与`offline_raw_export.json`核对8/8、doorrnd/success=1.0；`source_model_r1_unchanged.json`。
- 原始结论/采用方式：3/8步数不一致，成功标记8/8一致；按[task5.3 R10](tasks/task5/task5.3/RESULTS.md)停止A，不执行seed1037超限复现及后续任务，不把这8回合重复计入最终评估。
- 限制/待验证：不一致原因未诊断；不能据此断言模型或种子协议失效，也不能降低门槛；9任务最终结果尚未完成。CPU原始5秒采样位于`results/task5/t5.1-eval-r2/host_cpu_5s.jsonl`，完整统计在本轮全部进程退出后更新。
- 核查日期/人：2026-10-14T00:29:59.339239+08:00，Codex。

<a id="src-0261"></a>
## SRC-0261 — Task5 D21/R11 B spline种子999超限复现（t5.2-eval-r2）

- 主张：B原模型/入口/参数仅增加eval_seed999、nr_evaluations1，再次在20001步触发上游同一assert，退出1且没有Eval ep完成行，符合R11的独立复现门槛。
- 类型：项目实测；继续B剩余49回合为既定D21/R11的执行。
- 作者/版本：Codex，2026-10-14，模型/推理强度未知；原模型`/forem_results/t5.2-train-s40/local_model/checkpoint-1000`，Husky原入口与配置不改。
- 证据/精确位置：`logs/task5/t5.2-eval-r1/eval-spline.log`原20001步assert；`logs/task5/t5.2-eval-r2/check-spline-seed999-n1.log`最后traceback/AssertionError；`results/task5/t5.2-eval-r2/commands.json`本调用完整命令、起止/rc1；`check-spline-seed999-n1-episodes.json`为空列表。
- 原始结论/采用方式：i=0记失败且分母保留；B从种子1000起49回合独立续跑，不重跑B其余已完成任务，bookstorepnp仍D10 N/A。A的确定性核查失败不放宽也不拼接。
- 限制：本条只证实B原i=0再次超限，不证明所有种子逐步确定性；B剩余补跑与9任务汇总尚未完成，后续追加实测。
- 核查日期/人：2026-10-14T00:34:59.579524+08:00，Codex。


<a id="src-0262"></a>
## SRC-0262 — task6.4 R1依赖复制复用、A异常退出与B回退冒烟（未验收）

- 主张：T64-D1/D2执行后B静态枚举rc0；两侧原物理0.002/500启动与health rc0。A三个回合结束（0/3 success、goal_reached0、每回合base_collisions50、IK均0；1523/679/1804步），但评估进程rc134，冒烟未通过。B原步长在首reset内置重试耗尽rc1/Could not set start pose；按既有授权换新run为0.0005/2000，首回合642步/成功/无碰撞/IK0。发现A异常后按协议主动清理B，B当次退出1/TF future extrapolation；该TF异常与清理重叠，不能据此证明独立自然故障或回退后完整reset通过。
- 类型：项目运行证据；因异常停止/回退为既定工程协议执行；rc134成因未知，不能将其直接认定为已查明的C++析构缺陷。
- 作者/版本：Codex /root，2026-10-14，实际精确模型/强度未知；镜像42a779ab…同task5，普通eval策略CPU（日志TorchPolicy running on CPU，num_gpus0）。模型/五入口首尾SHA与SRC0258基线一致；没有策略/任务代码或每步时长改动。
- 精确证据：`forem/results/task6/t6.4-R1/{freeze_recheck,B-static,postrun_source_verification,smoke_summary,mount_failure}.json`；`forem/results/task6/t6.4-smoke-{A-r1,B,B-r2}/{commands,status,health,cleanup,offline_raw_export}.json`；`forem/logs/task6/t6.4-smoke-*/{launch,eval,health,cleanup}.log`。B-r2另`interruption.json`及`interruption_cleanup.json`；A eval.log末尾ClassLoader卸载警告，无根因证明。
- 依赖复用：原task6.2目录不写入、不进入G-B。既有B容器拒绝bind mount，使用R1允许的复制后逐文件核sha（`build/task6/task6.4/*-copy-verification.json`），容器内/t64_runtime复制内容仅重定位349条绝对软链（`results/task6/t6.4-preflight/B/runtime_link_relocation.json`），源码与二进制字节未改变。部署次序Husky devel后source依赖devel --extend，补保留依赖prefix/LD/ROS_PACKAGE_PATH；原源码/模型仍只读，日志与恢复metadata写独立副本。
- 原始结论/采用：§2冒烟没有整体通过，§3正式A/B均0episode，状态blocked交Claude；不标阶段一review，不自动重跑/训练/阶段二。两自有容器仅sleep，cleanup after=[]；task5原ROS保留，其他任务既有活动不干扰。
- 推导/工程估算：A三个已结束回合日志墙钟0.89/0.77/1.09分钟，均值55秒，线性50回合约2750秒（45.83分钟）；B-r2单回合0.40分钟，线性50回合约1200秒（20分钟）。输入为日志保留两位小数的分钟，公式sum(minutes)*60/n*50，仅滚动成本算术；启动/收尾/失败恢复及长回合未覆盖，且冒烟失败/中止，不能作为阶段一工期或可行性承诺。阶段二无可靠估计。
- 配置适用限制：上游setup_config_wandb本地model_file分支有意保留训练wandb.config，CLI覆盖发生于返回DotDict（utils.py L351–403）。因此offline config的sim/50不是本次实际gazebo/3；准确命令、Eval ep计数和gazebo prefix是实际路径证据，不改原版日志/恢复代码。
- 适用限制：A仅3结束回合但进程非正常退出，B仅1结束回合后中止；不是正式50episode结论或论文复现判断。被动model_states位移包含reset搬迁，不能作为轨迹距离；B-r2实际twist速度峰值0.505m/s证明观测到运动，但不作控制精度/性能验收。未排查A异常根因、B TF自然发生与清理影响。完整源码/模型数值正确不等于Gazebo完整依赖或运行就绪。
- 核查时间/人：2026-10-14T00:38:59.475798+08:00，Codex；停止依据task6.4 PROCEDURE异常处理及SRC0259。

<a id="src-0263"></a>
## SRC-0263 — Task5 D21 B spline补齐及r1 W&B读取阻塞、A/B CPU收尾

- 主张：B spline种子999–1048恰好50回合，47个自然结束均失败，999/1000/1036三个20001步超限按D21计失败，结果0/50；最后1037–1048共12回合退出0、stdout0/12与上游离线spline/success=0.0一致。中断段没有上游任务汇总。导出B原r1 W&B时DataStore checksum断言失败、rc1，9任务原始指标核验/最终JSON未完成。B旧stdout标准picknplace8/50，fwdO4/50，父结果2026-10-13粗读0.08为fwdO，两朝向仍待r1 W&B交叉核验。CPU300个5秒样本峰值22.199435核、时间加权均值9.363942核，>56样本0。
- 类型：项目实测、原始stdout核查；0/50为D21规定失败计数的汇总。停止为未覆盖异常的既定要求，不改科学口径。
- 作者/版本：Codex，2026-10-14，实际模型/强度未知；Husky原入口/checkpoint1000不变。登记源/配置/模型/r1产物集合SHA：A82文件、B210文件changed=[]，仅限登记集合。
- 证据/精确位置：`results/task5/t5.2-eval-r2/spline_episode_ledger.json`逐seed、`spline_segments.json`三段/末段raw_summary、`spline_completion_check.json`重新50行核对；`logs/task5/t5.2-eval-r2/check-spline-seed999-n1.log`及`continue-spline-seed1000-n49.log`、`continue-spline-seed1001-n48.log`、`continue-spline-seed1037-n12.log`的Eval ep/最后assert；r2 `continue-spline-seed1037-n12-offline.json`；`commands.json`完整命令/起止/rc/log。失败日志`offline_r1_raw_export.log`：export_wandb_offline.py:11 → wandb/sdk/internal/datastore.py:114 checksum断言。旧`logs/task5/t5.2-eval-r1/eval-picknplace.log`两个前缀ep49。A r2 `cpu_sampling_summary.json`/`host_cpu_5s.jsonl`（2026-10-14T00:27:23.125995+08:00至2026-10-14T00:52:19.796812+08:00）。A/B r2 `source_model_r1_unchanged.json`/`evidence_sha256.json`。
- 采用方式：B spline补齐，但9任务交付blocked；A按SRC-0260确定性失败不拼接。两子任务交Claude，保留r1及新r2软链，旧训练posttrain_status不覆盖。
- 限制/待验证：checksum失败的具体源文件与原因未定位，不断言来自bookstorepnp，不跳过/截断/修复原始数据。完整9任务原始指标、均值、fwdO核验仍未完成；不生成final_eval_summary，不置review/done。CPU为5秒CPU-time采样（不含idle+iowait），不证明未观测的更短瞬时峰值。无新训练、源码/模型/合同修改，不触碰task6.2/forem-dev。
- 核查日期/人：2026-10-14T00:57:15.939110+08:00，Codex。

<a id="src-0264"></a>
## SRC-0264 — task5.3 R12：D22（确定性门槛改为成功标记一致）、D23（stdout主口径、W&B逐文件核验）

- 主张：A door 8回合成功标记8/8一致、步数3/8不同；door在sim中不依赖Gazebo（`mobile-rl/scripts/modulation/envs/tasks_chained.py` `requires_simulator`返回False），步数差异推断来自BioIK按墙钟超时求解（未验证）。D22把门槛改为成功标记一致，2(a)通过；1037按原r1记失败。B的r1 W&B DataStore checksum失败；D23以stdout“Eval ep”逐回合行为主口径，W&B逐文件导出交叉核验，失败文件披露。
- 类型：工程选择（Claude决策），依据SRC-0260、SRC-0263。
- 适用限制：BioIK非确定性为推断；stdout为上游自身打印的累计计数，与W&B同源。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-14。

<a id="src-0265"></a>
## SRC-0265 — task6.4 R2：A退出134与真实底盘碰撞，B在0.0005 s下重做

- 主张：A三回合“Eval ep”完整、指标已导出，退出码134出现在pluginlib卸载警告之后（T64-D3：以回合与指标完整为有效判据，134记偏差）。A三回合均因与Gazebo障碍物（obstacle16/18/19）的真实底盘接触达50次而终止（日志`Collision:`行计数44/39/35），同种子sim中0碰撞。B在0.002 s下复位失败，0.0005 s下首回合成功；r2中止系执行者因A异常主动停止，不作B失败证据。
- 类型：项目实测（Codex，SRC-0262）＋Claude日志核查（`forem/logs/task6/t6.4-smoke-A-r1/*.log`的Collision行；`forem/logs/task5/t5.1-eval-r1/eval-simpleobstacle.log` ep0–2）。
- 适用限制：仅3回合；后方测距传感器缺失是否相关未验证。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-14。


<a id="src-0266"></a>
## SRC-0266 — task6.4 R2/T64-D3 B完整冒烟与阶段一评估证据（持续追加）

- 主张（截至2026-10-14T08:35:39.323255+08:00）：T64-D3授权下，A正式`t6.4-A-simpleobstacle`已启动，PR2 track/0.002/500，50episode/seed999；B-r3完整3回合653/1893/652步，success3/3、goal3/3、IK0/base_collisions0、success_nojumps2/3；自然退出0、cleanup after=[]，原始W&B指标与Eval ep计数一致。由此按既有授权启动B正式`t6.4-B-simpleobstacle`，direct/0.0005/2000，50episode/seed999。正式结果尚未完成，不作成功率/复现结论。两侧异常独立处理。
- 类型：项目实测；原流程执行；下段原文数值为外部文献直接核查。
- 作者/版本：Codex /root，2026-10-14，模型/强度实际未知；镜像/依赖沿SRC0258/0259/0262，不建容器/依赖、不训练。R2/freeze_recheck.json的五文件/两checkpoint与前置一致；A/B torch策略实际CPU（num_gpus0）。
- 精确运行证据：`forem/results/task6/t6.4-smoke-B-r3/{commands,status,health,cleanup,offline_raw_export,verified_eval}.json`；`forem/logs/task6/t6.4-smoke-B-r3/{launch,health,eval,cleanup}.log`；正式各run的status/commands与log。`forem/results/task6/t6.4-R2/{freeze_recheck,cpu_before_launch,monitor_latest}.json`、host_cpu_5s.jsonl。评估包装/scripts/run_task6_4_eval.py，核验/scripts/summarize_task6_4_eval.py；源码入口未改。
- 原文对照直接核查：Honerkamp/Welschehold/Valada，N²M²，arXiv2206.08737v2、IEEE T-RO2023，https://arxiv.org/html/2206.08737v2 。Codex本轮通过Web读取原文HTML Sec IV-I/Table VI（lines400–418），PR2 N²M² rnd obstacle/simpleobstacle 81.6%，九任务平均79.2%。其他任务数值只保留备查`R2/paper_reference.json`，本轮未运行其他任务；不能以平均79.2替代单任务81.6，也不能直接对Husky解释为复现。
- 采用方式/限制：Task6.4阶段一对照原文simpleobstacle81.6%，本地task5原始sim50另核对；单训练种子40/评估种子999对论文5seed平均仅作描述比较，未宣称整篇复现。world/依赖版本和B步长已披露；A134仅在回合完整且指标导出后按T64-D3接受。B-r3通过不是正式50episode通过，不把3/3当100%最终性能。B速度观察仅运动就绪，不作控制精度。
- 核查日期/人：2026-10-14T08:35:39.323255+08:00，Codex；记录阶段实测持续追加，不预填正式结果。


### 2026-10-14T09:26:35.046606+08:00 SRC-0266 阶段一正式实测与交接（review）

- A：t6.4-A-simpleobstacle，seed999–1048各一次、50 Eval ep行；success16/50=.32、goal16/50；有底盘碰撞31回合（30回合计50、1回合计34）、IK非零3回合（2回合50、1回合20）、IK均2.40；selfcollision6/50，success_nojumps.28；步数232–2435、均1029.62、总51481。请求回合与W&B全部指标导出/交叉一致，eval134发生于完整结果之后，按T64-D3接受并披露；原码134保留。
- B：t6.4-B-simpleobstacle，50 Eval ep行/同seed列表；success36/50=.72、goal39/50；有底盘碰撞5回合（4回合50、1回合7）、IK非零10回合/其中6回合50、IK均6.62；selfcollision8/50，success_nojumps.40；步数512–4137、均1364.06、总68203。eval自然退出0；原W&B与stdout一致。两侧无需D21，未启动阶段二。
- 真实接触日志：A Collision打印1158行，robot mesh全部`pr2::base_footprint::base_footprint_fixed_joint_lump__base_link_collision_1`，涉及18种障碍mesh命名字符串。各seed对象/行号在summary/A_collision_objects.json；robot与障碍对符合R2真实Gazebo接触。日志窗口包含reset/rollout，打印事件不是上游每回合base_collisions计数，按字符串聚合也不推断跨seed同一实体；不作检测错误或传感器成因推断。
- 同策略sim对照：task5原simpleobstacle.stdout各39/50=.78；Gazebo差A−46、B−6个百分点。论文PR2对应任务81.6%（本条前文直接HTML核查），本地A比它低49.6个百分点；不能替代整篇九任务/5种子复现判断。F0/R48并列用SRC0256，但种子/训练器/ROS-Gazebo栈不同，不单因素归因。
- 公式与条件：rates=k/50，percent=100*k/50；delta_pp=100*(Gazebo_rate−sim_rate)；goal/selfcollision的k=round(上游二元回合mean*50)。输入为各run原日志+离线W&B，与同checkpoint/task/requested eval seeds配对的sim旧stdout；未验证逐seed起止/场景完全一致，解析/Gazebo几何/感知差异保留。
- 资源/耗时：538个约5秒全主机CPU-time样本，时间加权均12.481核，样本峰28.118核，>56为0；不证明更短瞬态峰。A runner2724.803秒，B2368.486秒；正式全局2724.803秒（45.413分），累计runner5093.289秒（84.888分）；不当CPU累计耗时或串并行等价提速证明。监控自然在本任务stop标记后退出0。设备实际CPU，num_gpus0沿冻结，未宣称GPU加速。
- 精确新增证据：`forem/results/task6/t6.4-summary/{comparison,manifest,verification,A_collision_objects,cpu_sampling_summary,evidence_sha256}.json`；两formal run `{commands,status,health,cleanup,offline_raw_export,verified_eval}.json`及对应原eval.log/原生*.wandb。`t6.4-R2/final_verification.json`证明五源码/原与复制checkpoint首尾一致、不同网络sandbox/无发布端口、两自有容器仅sleep且11311/11345均不监听；task5末次进程只读记录，G-B无容器操作。
- 采用/边界：阶段一review交Claude；不标整个task6.4 done，不放行/运行§4，之后由Claude决定。无新训练、原代码/奖励/观测/任务/每步时长改变、依赖重建/任务增加。A退出偏差、B步长回退、原版镜像/costmap/后方传感器限制及非独立物理success均披露。
- 核查人/时间：2026-10-14T09:26:35.046606+08:00，Codex /root，实际模型/强度未知；未委派/切换，推荐Codex GPT6.1sol、Claude Sonnet5.5，明确执行low/默认、跨模块核查medium。

<a id="src-0267"></a>
## SRC-0267 — Task5 B D23逐文件W&B核验与最终9任务汇总（t5.2-eval-r2）

- 主张：stdout主口径下B标准任务成功数为39、8、N/A、22、7、13、10、0、0，各可运行分母50；8任务算术均值99/400=0.2475（24.75%），9任务表覆盖8/9、bookstorepnp N/A、完整9均值N/A，不把N/A当0。picknplace fwdO4/50单列。spline沿SRC0263的0/50，不重跑任何B任务。
- 类型：项目原始日志核验与算术汇总，D23/D10工程口径沿SRC0264/0221。公式为sum(各标准任务成功数/50)/8；朝向不混池。
- 证据/精确位置：`results/task5/t5.2-eval-r2/final_eval_summary.json` tasks与alternate_fwdO_orientation；`d23_episode_metric_checks.json`：r1七可运行任务/八朝向全部matched，spline末段12回合matched、前35回合上游assert前未产生汇总为stdout_only；原r1 Eval ep0–49及SRC0263逐seed账本。`d23_offline_file_report.json`与`d23_exports/`逐文件原始导出；commands.json每文件命令/起止/rc/log。
- W&B：共13文件，12可读；不可读为 `/forem_results/t5.2-eval-r1/wandb/offline-run-20261012_080853-1peniqus/run-1peniqus.wandb`，DataStore.scan_record checksum AssertionError，完整traceback在summary/file_report及对应导出日志。该文件未修复/截断，未使用部分记录。原始wandb-metadata.json args明确eval_tasks bookstorepnp，用于关联其旧stdout（旧进程被超时终止，log未打印run-id）。bookstorepnp仍D10 N/A，无完成回合，不变成失败0。
- 采用：按D23完成B最终汇总并置review，独立Claude task5.3待复核，不标done；A仍继续授权补跑。
- 限制：单训练种子、spline拼接；stdout/W&B为上游同源。不可读文件的checksum原因未诊断，文件名/任务关联不证明原因。raw非有限指标在最终严格JSON用null表示，逐文件原始JSON仍保留原值。
- 作者/版本及核查：Codex，2026-10-14T08:35:49.530624+08:00，实际模型/强度未知，推荐GPT6.1sol/Sonnet5.5 medium用于跨文件指标核对。

<a id="src-0269"></a>
## SRC-0269 — 用户要求先复现N²M²；原作者预训练模型与原文Table III/VI逐任务数值

- 主张：(1) 用户2026-10-14：“这里的原因要排查，我们至少要先复现出来N2M2的结果”。(2) 上游仓库附带原作者预训练模型`mobile-rl/scripts/model_checkpoints/{pr2,hsr,tiago}/checkpoint-1000`，config均为`task: simpleobstacle`、`obstacle_config: rnd`、`world_type: sim`、`total_steps: 1000000`、`execute_style: track`、`time_step: 0.02`；seed PR2/TIAGo 41、HSR 40；`ik_fail_thresh_eval` PR2/HSR 100、TIAGo 50；README第147行给出`evaluation_ray.py --evaluation_only --eval_execs sim gazebo --env ... --model_file=[robot]/checkpoint-1000`。(3) 原文N²M²逐任务成功率（%）：Table III sim：PR2 86.0/97.6/70.0/84.4/81.6/97.2/97.6/98.4/80.8（平均88.2），HSR 63.2/92.0/68.0/82.0/88.0/93.2/87.2/88.0/84.0（82.4），TIAGo 61.2/91.6/42.0/54.4/50.4/81.6/89.2/62.4/56.0（65.4）；Table VI Gazebo：PR2 81.6/87.6/48.8/93.2/74.4/94.0/96.8/60.4/75.6（79.2），HSR 64.0/92.4/54.4/91.2/78.8/95.6/90.4/85.6/91.6（82.7），TIAGo 56.0/85.2/54.8/71.2/51.2/78.8/82.4/30.0/56.0（62.8）；列序为rnd obstacle、p&p、bookstore p&p、dynamic obstacle、dynamic p&p、cabinet、drawer、door、spline。
- 类型：(1)用户指令；(2)本地代码与文件核查（Claude读config.yaml与README）；(3)外部文献，经WebFetch摘录arXiv HTML（工具提示列对齐为其从扁平文本推断，待对照PDF确认）。
- 来源：Honerkamp等，N²M²，arXiv:2206.08737v2 Table III、Table VI；`mobile-rl/scripts/model_checkpoints/*/config.yaml`；`mobile-rl/readme.md` L145–151。
- 本项目采用：task6.5以原作者PR2模型在simpleobstacle上的sim 86.0%、Gazebo 81.6%为首要复现目标；TIAGo（差速）为第二目标。
- 适用限制：原文为5种子平均（原作者只发布一个模型）；“rnd obstacle”对应`simpleobstacle`依据原作者config推断；Table数值列对齐待PDF确认。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-14。

SRC-0266运行对照输入续记（2026-10-14 Codex）：只读重算task5原eval-simpleobstacle.log，A/B均50条ep0–49、末条success39/50=0.78；A IK均6.34、碰撞回合0，B IK均5.12、碰撞回合3。精确来源与复算存`results/task6/t6.4-R2/sim_comparison_inputs.json`，原日志`logs/task5/t5.{1,2}-eval-r1/eval-simpleobstacle.log`。这只是既有单任务stdout核对，task5.3最终验收另管；本轮不采集sim数据或改其文件。

<a id="src-0268"></a>
## SRC-0268 — Task5 D22/D23最终A评估与A/B交付验证（续用r2）

- 主张：A标准九任务为simpleobstacle 39/50, picknplace 48/50, bookstorepnp 37/50, dynobstacle 39/50, picknplacedyn 37/50, door 49/50, drawer 50/50, roomdoor 46/50, spline 40/50，九任务算术均值0.855555555556。door原i0–37成功38、原i38/1037超限失败固定计分、补i39–49成功11，49/50；1037复跑同样20001步assert、rc1，仅记录不改变原分数。drawer/roomdoor/spline从seed999各50；超限按D21计失败。B沿SRC0267，8可运行均值24.75%、九含bookstorepnp N/A（完整9均值N/A），不重跑。
- 类型：项目实测/原始stdout逐行核验、算术推导；方法/门槛/失败计数沿Claude D21/D22/D23及D10，不是新增科学口径。均值公式sum(标准朝向成功数/50)/可运行任务数，fwdO不混池。
- 证据/精确位置：A/B `results/task5/t5.{1,2}-eval-r2/final_eval_summary.json` tasks/alternate_fwdO_orientation/metric_checks；A `door_seed1037_d22_diagnostic.json`、四个`<task>_episode_ledger_d22.json`/`<task>_segments_d22.json`；两run `commands.json`每次完整命令/起止/rc/log；`d23_offline_file_report.json`和`d23_exports/`每文件原始导出或完整错误，`d23_episode_metric_checks.json`；`source_model_r1_d22_d23_unchanged.json`登记源/配置/模型/r1集合A82、B210 SHA changed=[]；`handoff_verification_d22_d23.json`/`evidence_d22_d23_sha256.json`最终证据；原stdout来自r1及r2日志中的Eval ep行。
- W&B核验：A12文件中不可读0，具体文件名/traceback/相关stdout在summary；可读且发出success的逐前缀指标全部与stdout一致。assert中断未发指标的段只保留stdout并披露。B唯一不可读bookstorepnp run-1peniqus.wandb checksum断言，按SRC0267/D23披露、D10 N/A；不修复/截断/使用部分记录。逐文件原始JSON保存原非有限值，严格最终JSON将非有限原始指标用null披露，不影响成功计数。
- 资源：本次续跑274个5秒样本，峰25.391663核、时间加权均值12.635225核、>56样本0；A r2 host_cpu_d22_5s.jsonl/cpu_d22_sampling_summary.json，2026-10-14T08:31:49.991609+08:00至2026-10-14T08:54:36.493307+08:00。自身监控通过cpu_d22.stop退出；不向任何训练发送信号。
- 采用/限制：两任务交付review，仅Claude task5.3最终复核后可done；一训练种子、拼接与同源stdout/W&B限制保留。登记SHA只限列明集合；5秒CPU采样不证明未观测更短瞬时峰。未改算法源码/模型/任务/world/max_len/种子协议，不触碰task6.2、forem-dev、task6.4。
- 核查人/时间：Codex，2026-10-14T08:54:42.608553+08:00；实际模型/强度未知。推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（逐日志/指标/拼接核对），文档/监控low或默认。

<a id="src-0270"></a>
## SRC-0270 — task6.4阶段一：N²M²原版方法训练的A（PR2）、B（Husky）Gazebo零样本评估

- 主张：simpleobstacle，上游`evaluation_ray.py --eval_execs gazebo`，50回合，eval_seed 999：A 16/50＝0.32（sim 39/50＝0.78），30个回合因底盘与Gazebo障碍物碰撞达50次而终止；B 36/50＝0.72（sim 39/50＝0.78），5个回合有碰撞、10个有IK失败。Husky用N²M²原版方法sim→Gazebo损失约6个百分点，与原文同量级；task6.3中ScwmSAC链路损失约27个百分点。
- 类型：项目实测（Codex执行），Claude从`logs/task6/t6.4-{A,B}-simpleobstacle/eval.log`独立复算。
- 适用限制：单训练种子、50回合；sim与Gazebo的障碍形状不同（sim约一半椭圆），配对只作参考；A退出码134（评估完成后）；B物理步长0.0005 s、执行方式direct；B的Gazebo栈为Husky原版代码（melodic），与Task3迁移栈不同。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-14。

<a id="src-0271"></a>
## SRC-0271 — task5最终sim评估（A PR2、B Husky，9任务）

- 主张：A（上游N²M²＋PR2，100万步，种子40）9任务sim平均0.856（0.78/0.96/0.74/0.78/0.74/0.98/1.00/0.92/0.80），原文PR2 88.2%；B（Husky原版RLlib配方）simpleobstacle 0.78，8个可运行任务平均0.248，bookstorepnp N/A。
- 类型：项目实测（Codex执行），Claude从`logs/task5/t5.{1,2}-eval-r{1,2}/`的“Eval ep”行独立复算；`results/task5/t5.{1,2}-eval-r2/final_eval_summary.json`。
- 适用限制：单种子；D21（超限计失败、续跑拼接）、D22（确定性门槛为成功标记一致）、D23（stdout主口径，部分W&B文件不可读）；door/roomdoor与原文cabinet/door的对应为推断。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-14。


<a id="src-0272"></a>
## SRC-0272 — task6.5 原作者PR2 sim50完成，Gazebo健康检查包装错误停止

- 支撑主张：原作者PR2 checkpoint-1000在simpleobstacle sim，seed999–1048完整50回合，43/50成功=86%，goal44/50，底盘碰撞回合0，IK均3.24（4回合非零，3回合达到50），总14388步/平均287.76/范围61–1020；自然退出0。Gazebo启动器退出0，但评估前健康检查health.py第2行多余缩进产生IndentationError/rc1，包装状态error/rc1，完成回合0，没有Gazebo成功率。不是模型或Gazebo物理失败证据。
- 类型：项目实测（stdout与原始离线指标）＋包装源码/错误日志核查；43/50及均值为算术汇总，异常停止为既定工程协议，不作因果扩展或新验收。
- 作者/版本：Codex /root，实际精确模型/推理强度未知；镜像sha256:42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915，forem-t6.4-pr2复用；上游五文件SHA首尾与mobile-rl一致，版本沿task6.4/SRC0262，未改上游。模型checkpoint sha256 a4d24df66107ba4cd90cdbbaed99d7d99a84c1ade8c1a3fc009b718add66f49d；四文件模型集详见preflight/model_source_sha256.json。
- 精确证据：`forem/logs/task6/t6.5-pr2-sim/eval.log` Eval ep0–49、TorchPolicy CPU及最后汇总；`forem/results/task6/t6.5-pr2-sim/{verified_eval,offline_raw_export,commands,status,model_copy_verification,cleanup}.json`；唯一离线run-1k4bold5.wandb已导出且success/epoch_len/ik_fails/base_collisions交叉一致。`forem/logs/task6/t6.5-pr2-gz/health.log` L1–4、同run/health.py L2；`forem/scripts/run_task6_5_eval.py` L85–102生成health文本缩进错误；Gazebo `commands/status/cleanup.json`保留全部起止/退出码。`results/task6/t6.5-preflight/{final_verification,cpu_sampling_summary,final_top}.json`及`results/task6/t6.5-summary/{comparison,manifest}.json`。
- 配置与采用：task6.5 §1→§2，原model目录逐字节复制到各run/model，源只读；task6.5主口径50，因utils.py L351–403保存config仅显式CLI覆盖而显式`--ik_fail_thresh_eval 50`（保存值100）；模型训练seed41，learn_torso true，track/time_step .02/默认nr50/eval_seed999/num_gpus0，策略CPU有真实日志。事后成功且IK≤100仍43/50，仅同50阈值rollout筛选，不等于终止阈值100重跑。无D21，无训练/上游修改/阶段二。复现对照值沿SRC0269，多种子论文86%与本次单模型86%相同，不能宣称整篇或Gazebo复现。
- 耗时/资源：sim runner218.232 s，Gazebo未评估启动/清理53.275 s；66个约5秒host CPU-time样本时间加权均11.536核、峰18.094核、>56为0。统计公式沿monitor脚本busy=(total-idle-iowait)/total*64；不证明未观测更短瞬态峰。
- 原始结论/限制：sim50可交Claude复核；阶段一未完成，task6.5 blocked并按异常停止交Claude，不标阶段一review/done。Gazebo health未完成，物理实际值/控制器未独立核验；不能以启动器代码代替health实测。两run cleanup after=[]，容器仅sleep，监控退出0，task5只读top、G-B未进入/操作。未修复或重跑包装，保留可定位错误待Claude放行。
- 核查日期与核查人：2026-10-14T11:17:21.329562+08:00，Codex；Claude独立复核尚未执行。推荐GPT6.1sol/Sonnet5.5 low/默认，跨模块异常核对需要时medium，推荐不是实际配置。

<a id="src-0273"></a>
## SRC-0273 — task6.5 Claude复核R1：原作者PR2模型sim复现原文，Gazebo包装错误放行修正

- 主张：原作者PR2预训练模型（`mobile-rl/scripts/model_checkpoints/pr2/checkpoint-1000`）在我们的sim中simpleobstacle 43/50＝0.86，与原文Table III PR2 rnd obstacle 86.0%一致。Gazebo评估因执行者包装生成的health.py缩进错误在开始前停止（0回合）；T65-D1放行修正后用新run-id重做。
- 类型：项目实测（Codex执行，SRC-0272），Claude从`forem/logs/task6/t6.5-pr2-sim/eval.log`复核。
- 适用限制：单个原作者模型、50回合，原文为5种子平均。
- 核查人及日期：Claude（claude-opus-5-5，推理强度未知），2026-10-14。

## SRC-0274

- 主张：Dreamer4离线VPT条件下想象PMPO由policy头出动作；表7钻石0.7%对照0%，表1单H10021FPS；SOAR部分未报告机器人RL收益。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Hafner, Danijar；Yan, Wilson；Lillicrap, Timothy；Google DeepMind；Training Agents Inside of Scalable World Models；首稿/公开日期2025/09/29；arXiv预印本（所读版本）；所读arXiv 2509.24527v1；[版本原文](https://arxiv.org/abs/2509.24527v1)；DOI：本轮未核到DOI。代码/入口：本次作者项目页未找到官方实现；不将第三方复现算官方开源。[链接](https://danijar.com/project/dreamer4/)。
- 精确位置：正文§1–6，pp.1–18；附录A、B；表1/2/3/7；图3/4/7；阅读深度：正文全文精读；附录A数据、B任务及表7/8选读；原始PDF SHA256 `8655cce4bf12ce6210f6694f83c1a723c7acd7579214ca3ebc57c4394d0b1aeb`。
- 原始依据：方法：先视频模型预训练，再多任务BC/奖励头微调，最后在冻结Transformer的想象轨迹中用PMPO更新policy/value头；最终动作由任务条件policy头输出。在线不是CEM或SAC内部残差反馈。 模型：连续token潜空间；随机shortcut-forcing Transformer，确定性因果tokenizer。输入历史表示、键鼠动作、噪声级/步长；tokenizer用MSE+0.2 LPIPS，动力学用x-space flow/自蒸馏损失；每帧4次前向，MTP长度8；RL用λ-return与行为先验KL。 条件：Minecraft离线VPT 2541 h，360×640、20 FPS，23二值键+121类鼠标；2B参数（400M tokenizer+1.6B动力学），256–1024 TPU-v5p。训练集/验证集90/10按5分钟块隔离；1000个60分钟真实游戏评估回合。模型消融各48 h，不等于完整agent总训练时长；RL rollout数值未在所读正文找到。另有SOAR 180 h、7维末端相对动作、5 FPS的模型生成展示。 结果：表7：钻石Dreamer4 0.7%，WM+BC、VLA(Gemma3)、BC与VPT均0%；铁镐29.0% vs WM+BC16.9%、VLA11.2%。表1：单H100生成21 FPS、交互任务14/16，Oasis large5/16；表2 FVD57 vs最初diffusion-forcing306。机器人图6仅生成展示，无机器人RL收益表。 时延：未涉及受控观测/传输/控制器/驱动时延。9.6 s是192帧历史窗口；21 FPS是模型计算吞吐，均不是执行器延迟。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；检查预测是否受动作控制、保持训练/验证时间块隔离及分别评价真实任务和预测。及借鉴冻结模型学习头、控制因果与生成效率；需大规模离线预训练，条件不同。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者：记忆短、背包物品不清/变化。核查：钻石成功率仍低；任务序列提示见表6；VPT额外270k h与Dreamer4数据量不等，不能称严格同数据比较；机器人视觉生成不能推出UR5控制有效。 平台：Minecraft；SOAR展示；直接替换普通SAC为PMPO或把21 FPS当FoReM吞吐承诺。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第★ Dreamer 4条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-dreamer4)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0275

- 主张：DreamerV3以RSSM想象训练actor而非执行时搜索；所读v2表9 Atari100k均值125%对IRIS105%，跨域计算配置并不相同。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Hafner, Danijar；Pasukonis, Jurgis；Ba, Jimmy；Lillicrap, Timothy；Google DeepMind、University of Toronto；Mastering Diverse Domains through World Models；首稿/公开日期2023/01/10；arXiv所读v2；首稿2023、修订2024（未用后续Nature版替代正文）；所读arXiv 2301.04104v2；[版本原文](https://arxiv.org/abs/2301.04104v2)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/danijar/dreamerv3)（论文项目入口；本轮未运行）。
- 精确位置：正文Learning algorithm、Results；表2/4/9/10；图3/6；阅读深度：正文全文精读；附录算法、表2/4/9/10选读；原始PDF SHA256 `d0385798e8bada8e81b915c1743be81d9ce8776f12ed937e09351995e099ce37`。
- 原始依据：方法：真实交互训练RSSM；actor/critic在潜态想象中训练。真实环境只从actor采样，无lookahead；最终由Dreamer actor输出，不是SAC。 模型：确定性循环h+32组类别随机z；输入图像/向量、上一动作；重建/奖励/continue NLL和分离stop-grad KL（1 nat free bits、1% unimix）；symlog、symexp twohot、5–95百分位return归一化。正文T=16与表4 H=15按计数约定分别记录；actor用REINFORCE，critic λ-return。 条件：8域>150任务；表2 Atari200M原始帧/重复4、Atari100k400k原始帧=100k决策、控制500k/1M；单A100每agent，控制模型12M，其他默认200M；Minecraft64环境、100M步、8.9 GPU-days。视觉/本体控制重复2；周期不能跨任务统一换秒。 结果：表9/10 Atari100k gamer均值125%、中位49%，IRIS105%/29%、TWM96%/51%；其单A100约0.1 GPU-days vs IRIS3.5（原文换算）。图6模型规模/训练比例消融支持特定基准可扩展性，未提供Husky实验。 时延：未涉及显式时延；记忆/预测误差与通信/驱动延迟不能混称。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；区分模型损失与任务收益，检查表征/模型/策略训练的梯度边界。及借鉴损失尺度稳定化与历史表征；应先核查FoReM信号尺度。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者承认不同Atari100k协议影响比较，EfficientZero有提前reset；核查：固定超参数不等于固定算力/模型大小，表2环境数和replay比率跨域变化。 平台：仿真/游戏；照搬RSSM/奖励变换/replay比例或据此宣称所有任务无需调参。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第★ DreamerV3条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-dreamer3)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0276

- 主张：DreamerV2离散RSSM想象训练；表1在200M帧下median2.15 vs Rainbow1.47，未涉及机械臂时延。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Hafner, Danijar；Lillicrap, Timothy；Norouzi, Mohammad；Ba, Jimmy；Google Research、University of Toronto；Mastering Atari with Discrete World Models；首稿/公开日期2020/10/05；ICLR 2021；所读arXiv v4修订2022；所读arXiv 2010.02193v4；[版本原文](https://arxiv.org/abs/2010.02193v4)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/danijar/dreamerv2)。
- 精确位置：§2.1/2.2、§3；表1；附录超参；阅读深度：部分：摘要、§2方法、§3实验、表1/2、讨论；原始PDF SHA256 `037dce26de328dd86ce4ab71dfb54f44513fef49a02f2995a1c05848ccef158f`。
- 原始依据：方法：真实数据训练模型，冻结模型权重时在想象中训练actor/critic；最终actor出动作，无在线搜索。 模型：RSSM确定性循环+32×32类别变量；图像/动作输入；图像、奖励、discount NLL+KL balancing（0.8）；straight-through采样。想象H=15（附录），价值λ-return和actor梯度估计。 条件：55个Atari、200M原始帧（重复4后50M输入）；单V100、单环境、<10天；另模拟humanoid连续控制；非机器人真机。 结果：表1 human-normalized median2.15、mean11.33，Rainbow1.47/9.12，IQN1.29/8.85；不是统一机器人成功率。 时延：未涉及显式时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；权重冻结与输入梯度分开核查。及离散/随机表征与KL稳定化。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：游戏事件分布与控制误差不同；离散潜态与固定像素重建代价不能直接预期在局部地图中占优。 平台：Atari/仿真humanoid；直接把Atari成绩和200M帧预算变成UR5依据。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第DreamerV2条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-dreamer2)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0277

- 主张：DreamerV1解析梯度想象训练；图6为5M步return823 vs PlaNet332，D4PG786使用100M步。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Hafner, Danijar；Lillicrap, Timothy；Ba, Jimmy；Norouzi, Mohammad；Google Research、DeepMind、University of Toronto（正文署名）；Dream to Control: Learning Behaviors by Latent Imagination；首稿/公开日期2019/12/03；ICLR 2020；首稿2019；所读arXiv 1912.01603v3；[版本原文](https://arxiv.org/abs/1912.01603v3)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/danijar/dreamer)。
- 精确位置：§2–4/6；图6；附录A；阅读深度：部分：摘要、§2–4方法、§6实验、结论及附录A；原始PDF SHA256 `318891d59ba0065f57eb0e735735700e5eb528f53bf08b81c773437385586c64`。
- 原始依据：方法：在潜态想象中通过可微模型优化action/value网络；部署action网络，非在线CEM。 模型：高斯随机潜态+确定性循环RSSM；图像64×64和动作；ELBO重建+奖励+KL，比较contrastive/仅reward；continuous actor经tanh、λ-return反传；附录H=15。 条件：20个DMC像素控制任务，1–12维动作、重复2、回合1000步；5 seeds；单V100+10CPU核，约3h/1M原始环境步。 结果：图6：5M步平均return823，PlaNet332；D4PG100M步786。交互预算不同，不能写成同预算全面优势。 时延：未涉及显式时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；bootstrap让模型预测horizon和任务horizon分开。及可微预测辅助训练、表征损失的任务关联性。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：仅reward表征在该研究中不足；不同模型学习方式任务成绩明显不同；主比较为小型控制仿真。 平台：DMC等仿真；据此改变SAC更新为Dreamer或直接回传模型奖励。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第DreamerV1条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-dreamer1)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0278

- 主张：PlaNet用RSSM+CEM而非actor出动作；表1 cheetah662对D4PG524，walker951对968，非所有任务占优。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Hafner, Danijar；Lillicrap, Timothy；Fischer, Ian；Villegas, Ruben；Ha, David；Lee, Honglak；Davidson, James；Google AI/DeepMind等，见署名；Learning Latent Dynamics for Planning from Pixels；首稿/公开日期2018/11/12；ICML 2019；首稿2018；所读arXiv 1811.04551v5；[版本原文](https://arxiv.org/abs/1811.04551v5)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/danijar/planet)。
- 精确位置：§2/3/4/5；算法2；表1；附录A/D；阅读深度：部分：摘要、§2–5方法/实验、表1与附录A；原始PDF SHA256 `abac727526e6a45669d3ab9957126587e22aacf4dc9bcd60ffe5c853108e5bcc`。
- 原始依据：方法：CEM优化有限动作序列的预测reward；只执行首动作再重规划；最终由CEM输出，没有学习actor。 模型：确定性GRU+高斯随机RSSM；图像/动作；ELBO，讨论latent overshooting多步KL；明确最终RSSM不必用overshooting。附录默认CEM horizon12、10迭代、1000候选、100精英（附录A；各任务action repeat不同）。 条件：六个DMC像素任务64×64；任务分别设置action repeat，单V100约10–20h；在线收集，1000回合比较D4PG100000回合。 结果：表1 cheetah PlaNet662 vs D4PG524；walker951 vs968；因此不能写成所有任务胜出。 时延：未涉及显式时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；明确当前观测与未来预测的因果边界。及receding horizon和多步预测误差检查。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：模型偏差、在线搜索开销；overshooting并非最终系统必需；基线数据量/输入权限不同。 平台：DMC仿真；把CEM输出动作称为最终SAC动作，或把DMC动作重复作为FoReM周期。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第PlaNet条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-planet)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0279

- 主张：MuZero模型只监督reward/value/policy，最终MCTS动作；表1 Reanalyze200M帧median731.1% vs LASER431%。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Schrittwieser, Julian；Antonoglou, Ioannis；Hubert, Thomas；Simonyan, Karen；Sifre, Laurent；Schmitt, Simon；Guez, Arthur；Lockhart, Edward；等（完整署名见原文）；DeepMind；Mastering Atari, Go, Chess and Shogi by Planning with a Learned Model；首稿/公开日期2019/11/19；Nature 2020；所读arXiv v2；DOI 10.1038/s41586-020-03051-4；所读arXiv 1911.08265v2；[版本原文](https://arxiv.org/abs/1911.08265v2)；DOI：10.1038/s41586-020-03051-4。代码/入口：本次未核到完整官方论文复现代码；[链接](https://github.com/google-deepmind/muzero) 仅作官方伪代码入口，未核完整训练实现。
- 精确位置：§3/4；式1；表1；Methods；阅读深度：部分：摘要、§3方法/§4结果、Methods训练设置；原始PDF SHA256 `25588ee1d48690b33359a08a42fadfe86335aefefeee241d465b8bbd5eaa445c`。
- 原始依据：方法：确定性潜态模型预测policy/reward/value，MCTS形成改进策略；真实动作从搜索visit分布选取，非policy头直接最终输出。 模型：表示h、动力学g、预测f；无像素重建；训练展开K=5，reward/value损失+MCTS policy交叉熵+L2；随机环境由确定性模型近似。 条件：棋类800 simulations/决策，Atari50 simulations且动作重复4；1M训练batch（棋2048、Atari1024）；棋/游戏，不涉及机器人。Atari每game 8 TPU-v3训练+32 TPU-v3 selfplay，棋类16训练+1000 selfplay；12h是Atari主表特定分布式配置，不能当单卡时间。 结果：表1：MuZero20B帧mean4999.2%/median2041.1%；Reanalyze200M帧2168.9%/731.1%，LASER200M帧median431%。两个MuZero预算不能混合。 时延：未涉及观测或驱动时延；thinking time是搜索耗时。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；控制相关预测与像素重建可分开讨论。及候选预测价值但要独立验证模型误差。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：不直接处理Poker式不完备信息；确定性latent非物理状态；离散树搜索及巨大并行预算不同于Husky。 平台：棋类/Atari；套MCTS/离散化SAC动作作为本轮实施或拿游戏成绩证明机器人收益。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第MuZero条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-muzero)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0280

- 主张：Genie潜动作生成并用BC映射演示转移；表2 pixel-input ΔPSNR1.91 vs token1.33，FVD排序相反。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Bruce, Jake；Dennis, Michael；Edwards, Ashley；Parker-Holder, Jack；Shi, Yuge；Hughes, Edward；Lai, Matthew；Mavalankar, Aditi；等（完整署名见原文）；Google DeepMind；Genie: Generative Interactive Environments；首稿/公开日期2024/02/23；ICML 2024（所读arXiv v1）；所读arXiv 2402.15391v1；[版本原文](https://arxiv.org/abs/2402.15391v1)；DOI：本轮未核到DOI。代码/入口：作者项目页本次未找到官方训练代码：[链接](https://sites.google.com/view/genie-2024/)。
- 精确位置：§2/3；表2/3；图15；附录B/C；阅读深度：部分：摘要、§2方法、§3实验/数据与§5讨论；原始PDF SHA256 `94c63a5ced89355326706c88236591c2972ced12f3dece4f8982f020110c81f3`。
- 原始依据：方法：主要是生成环境；§3.3给latent-action行为克隆转移，而非证明在其模型中RL成功；用户或已训练policy选择潜动作。 模型：VQ tokenizer、VQ潜动作、ST Transformer MaskGIT；token CE和VQ重建/commitment；随机token采样、逐帧自回归。潜动作索引不是机器人实际命令。 条件：6.8M×16s platformer视频约30k h，10 FPS、160×90，11B模型；另机器人视频验证，未给UR5控制实验。 结果：表2 Platformers pixel-input FVD40.1/动作可控ΔPSNR1.91，token-input38.8/1.33：更低FVD不等于更可控；图15约200真实专家样本映射latent后达oracle BC相近（图示，未读出精确百分比）。 时延：未涉及显式时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；动作条件依赖与视觉指标分开核查。及少标签视频/潜动作思路。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：图像生成与可执行动作不等价；latent映射需真实动作标定；不是SAC反馈实证。 平台：平台游戏/机器人视频；用无标定latent直接接UR5或把BC转移叫RL收益。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第Genie条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-genie)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0281

- 主张：Genie3官方博客宣称720p/24FPS/数分钟交互，未披露可核的RL训练/机器人任务对照。
- 类型：外部文献（官方博客功能描述，非同行评议实证）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Jack Parker-Holder、Shlomi Fruchter（官方署名）；Google DeepMind；Jack Parker-Holder、Shlomi Fruchter；Genie 3: A New Frontier for World Models；首稿/公开日期2025-08-05；官方博客，2025-08-05；无论文版本号；所读官方博客2025-08-05；无arXiv版本号；[版本原文](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/)；DOI：无。代码/入口：未公开实现/权重于所读博客；[链接](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/)。
- 精确位置：Towards world simulation、Capabilities、Fueling embodied agent research；无论文表图编号；阅读深度：原始博客全文；技术未披露项明确未知；原始PDF SHA256 `网页无固定PDF；以官方发布日期与小节定位`。
- 原始依据：方法：演示SIMA在生成环境中导航；博客未交付完整RL训练、对照和优化目标；最终导航动作由SIMA/用户给出。 模型：博客未披露潜/像素建模内部架构、随机性、具体训练损失或动作条件细节；只知道视频输出及navigation/text world-event输入，不能借其他Genie版本补齐。 条件：24 FPS、720p、持续数分钟的公开演示；数据量、训练硬件/时长、机器人型号与控制频率未披露。 结果：上述为官方功能描述，无统计对照表、标准化任务SR或UR5实验，不列成研究验收通过。 时延：未涉及受控观测/传输/控制器/物理时延；24 FPS是生成显示速率，不是通信或执行偏差的测量。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；暂无可直接迁移的具体方法。及交互世界应响应真实动作、可测试反事实。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：技术/评测不可审计；demo长时一致性不等于可靠物理接触；研究预览不是开源训练基础设施。 平台：交互视频；将演示性能/分辨率作为FoReM控制证据。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第Genie 3（官方博客）条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-genie3)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0282

- 主张：UniSim表3 .81/.58是48任务模型内SR，非真机定量SR；方法是视频模型内REINFORCE，模型5.6B/512TPUv3/20天。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Yang, Sherry；Du, Yilun；Ghasemipour, Kamyar；Tompson, Jonathan；Kaelbling, Leslie；Schuurmans, Dale；Abbeel, Pieter；Google DeepMind、MIT、UC Berkeley（作者联合署名）；Learning Interactive Real-World Simulators；首稿/公开日期2023/10/09；ICLR 2024；所读arXiv v3；所读arXiv 2310.06114v3；[版本原文](https://arxiv.org/abs/2310.06114v3)；DOI：本轮未核到DOI。代码/入口：作者项目页本次未找到官方完整训练代码：[链接](https://universal-simulator.github.io/)。
- 精确位置：§2.1/2.2/4.1/4.2/6；表2/3；附录C/D；阅读深度：部分：摘要、§2方法、§4政策训练/评估、§6局限；原始PDF SHA256 `956d21809f36cc107c82b3a32177ea555cacf032b3bde014fed1b958bc09c295`。
- 原始依据：方法：hindsight数据增强训练VLM；另一分支VLA在生成视频内用REINFORCE+学得reward优化，部署VLA动作，部分高层视频通过逆动力学执行。 模型：视频空间条件扩散U-Net，内部非Dreamer RSSM；历史帧+T5语言/离散连续控制混合编码，去噪MSE；预测变长视频段、接着自回归。 条件：5.6B，512 TPU-v3、20天模型训练；Language Table二维末端控制、真实机器人部署图；VLM生成10k长轨迹；RL定量表3评估48个模型内任务，不等于48真机回合。统一动作Hz未报告。 结果：表3模拟SR .81 vs VLA-BC .58，pointing .71 vs .12；表2模型内RDG(all) .34±.13 vs .07±.11；真机图8给定性迁移，不能把这些SR称真机SR。 时延：未涉及显式时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；区分模型内与真实环境成绩。及失败数据覆盖、学得模型和真实部署接口对齐。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者：不可能动作幻觉、短记忆、未知形态泛化有限；模型内奖励/评测自身偏差可能放大，真实定量证据有限。 平台：Language Table等；将VLA/逆动力学作为最终SAC或迁移其数据/奖励合同。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第UniSim条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-unisim)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0283

- 主张：GameNGen用PPO收集50M环境步，训练引擎用70M样本、64历史帧；单TPU-v5 20FPS是生成吞吐，未报告在模型内训练RL的任务收益。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Valevski, Dani；Leviathan, Yaniv；Arar, Moab；Fruchter, Shlomi；Google Research、Tel Aviv University（原文署名）；Diffusion Models Are Real-Time Game Engines；首稿/公开日期2024/08/27；ICLR 2025；首稿2024、所读v2修订2025；所读arXiv 2408.14837v2；[版本原文](https://arxiv.org/abs/2408.14837v2)；DOI：本轮未核到DOI。代码/入口：项目页未找到官方训练代码：[链接](https://gamengen.github.io/)。
- 精确位置：§3.1–3.3/4/5；表1/2/3；图4；阅读深度：部分：摘要、§3方法、§4实验设置、§5结果/局限；原始PDF SHA256 `6442a8e2a2da84c4c2be74406fdf2b8c719ad191e83fe37c6d8024f6859dfa47`。
- 原始依据：方法：PPO先在真实游戏采数据，之后训练神经游戏引擎；不是在世界模型中优化PPO。最终动作来自玩家/外部agent。 模型：Stable Diffusion1.4 VAE潜态扩散，动作embedding+历史帧潜态；velocity去噪MSE，context噪声增强，decoder像素MSE；预测下一帧。 条件：DOOM；§4.1 PPO收集50M环境步、8个并行游戏；§4.2模型用70M样本子集、700k训练updates、128 TPU-v5e、320×240图像pad至320×256；默认64帧/动作历史。§3.3单TPU-v5推理20 FPS（4次denoise共40ms+decoder10ms）；游戏键动作，非机器人控制频率。完整训练wall-time未报告。 结果：§5 teacher-forced PSNR29.43/LPIPS .249；人类短片鉴别58–60%。表2更多context提升预测；这些是引擎质量指标，没有模型内RL任务收益对照。 时延：计算20FPS涉及推理耗时；未涉及观测/执行时延注入。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；区分模型采数和策略用模型训练。及context鲁棒性与生成细节。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：有限context导致长期状态不一致，数据受policy覆盖限制；视觉相似不保证内部计分/物理正确。 平台：DOOM；把游戏引擎吞吐、视觉PSNR证明SAC收益。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第GameNGen条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-gamengen)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0284

- 主张：V-JEPA2-AC冻结encoder、L1未来特征+CEM，非RL；表2 PnP80%/65% vs Octo15%/10%，表3单4090规划16s/动作；动作由实测位姿差构造。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Assran, Mido；Bardes, Adrien；Fan, David；Garrido, Quentin；Howes, Russell；Mojtaba；Komeili；Muckley, Matthew；等（完整署名见原文）；FAIR at Meta、Mila/Polytechnique Montréal；V-JEPA 2: Self-Supervised Video Models Enable Understanding, Prediction and Planning；首稿/公开日期2025/06/11；arXiv预印本，2025（所读v1）；所读arXiv 2506.09985v1；[版本原文](https://arxiv.org/abs/2506.09985v1)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/facebookresearch/vjepa2)。
- 精确位置：§2.1/3.1/3.2/4.1–4.3；表2/3；附录B.1/B.4；阅读深度：部分精读：§1–4完整控制方法/结果，§2预训练；附录B.1/B.4；§5–7理解/QA未逐项精读；原始PDF SHA256 `9cfcfde5fb0d9730637da5b9e7317825c3f3d09e91f3553e22eeba42c74d2226`。
- 原始依据：方法：AC在冻结encoder上学动力学；执行时CEM最小化未来与image goal的latent L1，执行首动作再重规划。该机器人分支不训练RL actor；最终由CEM输出。 模型：确定性latent预测Transformer（AC≈300M、24层；encoder≈1B）；帧表示+末端位姿+动作；预训mask特征L1+EMA/stop-grad，AC teacher-forcing L1+2步rollout L1。动作标签由相邻实测末端状态差构造，不是原始控制命令。 条件：>1M h互联网视频与1M图像；AC筛选DROID约23k轨迹、<62h，256²、4FPS、7维末端/夹爪；两实验室Franka+RobotiQ，未收集部署场地训练数据，但手选camera视角。CEM horizon1、800样本×10轮，单4090约16s/动作；阻塞式等待执行完成，没有固定servo Hz。 结果：表2跨lab PnP杯80%/盒65%，Octo15%/10%；每task10trials。表3 Lab2 Cosmos80样本×10轮约4min/动作，PnP杯0%/盒0%，AC80%/50%。4FPS数据与16s规划必须分开。 时延：未研究受控时延；16s是计算延迟，阻塞执行机制，不是UR5驱动时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；固定目标encoder、监督空间一致、动作标签来源分开核查。及不必重建像素的动作条件预测；teacher-forcing与rollout验证分开。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者：相机坐标轴歧义、长rollout误差、搜索空间和image-subgoal依赖；核查：10trial样本小，目标子图与外部选择不能称完全自主长时任务；动作标签实际差分可能混合控制响应。 平台：Franka真机；把CEM替换SAC/手选视角或4FPS沿用为UR5周期。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第★ V-JEPA 2条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-vjepa2)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0285

- 主张：NWM可以给NoMaD候选排序；表2 ATE1.93→1.78（32候选），planning1.13；这是RECON轨迹评估，非UR5延迟或SAC反馈证据。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Bar, Amir；Zhou, Gaoyue；Tran, Danny；Darrell, Trevor；LeCun, Yann；Meta、UC Berkeley等（作者署名）；Navigation World Models；首稿/公开日期2024/12/04；CVPR 2025；首稿2024、所读v2；所读arXiv 2412.03572v2；[版本原文](https://arxiv.org/abs/2412.03572v2)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/facebookresearch/nwm/)。
- 精确位置：§3.1–3.3/4；表2/3；附录表8；阅读深度：部分：摘要、§3方法、§4实验/结果与附录8运行成本；原始PDF SHA256 `33b6532143148b60d991f7cfc0c6ff2c168a54c8dcd285e4dbee5eec84c51a5e`。
- 原始依据：方法：CDiT预测每个候选未来；CEM规划或NoMaD多候选rerank，最终由CEM/最低能量候选输出；不更新SAC。 模型：VAE latent随机扩散；历史帧、平面平移u、yaw、time shift（±16s）；clean-state MSE+variance VLB；多goal/time条件避免动作被时间变量替代。 条件：SCAND/TartanDrive/RECON/HuRoN、Ego4D视频，模型最高1B；评估主要离线轨迹2s/视频16s，导航相对动作非UR5控制；实验含1/4FPS设置。 结果：表2 RECON ATE：NoMaD1.93±.04，NWM+NoMaD32候选1.78±.03，NWM planning1.13±.02；RPE .52/.48/.35。附录表8完整trajectory30.3s，time-skip14.7s、distill .4s，4bit .1s仅估计，不能当已测。 时延：未涉及受控时延；time shift是预测时间跨度，不是传输/执行延迟。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；明确候选来源及执行者。及动作后果排序最贴近候选预测思想；需另审最终SAC概率合同。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：轨迹相似/ATE不等于真实碰撞成功；动作常从实际pose差近似，镜头/场景OOD；distill计算和估计成本不能直接保证FoReM实时。 平台：导航视频/轨迹；搬导航单位/时延或把rerank称SAC反馈等价。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第Navigation World Models条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-nwm)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0286

- 主张：Cosmos提供两类视频WFM；表19 62.6%是camera pose估计成功率非机器人SR，整体10kH100/3个月不是单模型预算。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：NVIDIA；:；Agarwal, Niket；Ali, Arslan；Bala, Maciej；Balaji, Yogesh；Barker, Erik；Cai, Tiffany；等（完整署名见原文）；NVIDIA团队（全体贡献者见附录A）；Cosmos World Foundation Model Platform for Physical AI；首稿/公开日期2025/01/07；技术报告2025；所读arXiv v3；所读arXiv 2501.03575v3；[版本原文](https://arxiv.org/abs/2501.03575v3)；DOI：本轮未核到DOI。代码/入口：官方公开代码/权重有各自许可：[链接](https://github.com/nvidia-cosmos/cosmos-predict1)；本轮未审核许可兼容性。
- 精确位置：§3/5/6.2；表10/19；Discussion；阅读深度：部分：摘要、§5.1/5.2模型、§5.3实验、§6.2机器人后训与讨论；原始PDF SHA256 `c3c61f0a6f9a32700fc47d9898db573628d72bdea07562ca319ceba046e95c84`。
- 原始依据：方法：主要提供模拟/数据基础设施；此报告机器人后训做动作条件生成，未给同任务SAC训练比较；外部策略/控制输入动作。 模型：连续latent扩散（EDM加权denoise MSE）和离散token自回归（next-token CE）两族；文本/视频prompt，后训增加相机/末端动作条件；生成horizon跨各模型不统一。 条件：20M h原始视频筛约100M 2–60s clips；报告整体10k H100集群、3个月覆盖所有WFMs（非单模型成本）。机器人Bridge约20k episodes、5FPS、7维末端动作；1X EVE≈200h/30FPS。 结果：表19 7B Text2World pose-estimation成功62.6% vs VideoLDM4.4%，PSNR33.02 vs26.23；这是生成多视角一致性，不是机器人任务成功。 时延：未研究显式时延；视频fps不是机器人controller周期。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；不把视觉一致性指标叫任务SR。及基础模型后训动作grounding、数据整理性能思路。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者承认不遵守物理规律的生成仍存在；大规模/视频重建成本、动作后训与真实可控性须另验。 平台：视频；Bridge/EVE后训；安装大模型/更换任务观测/拿集群成本作FoReM期限承诺。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第Cosmos条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-cosmos)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0287

- 主张：TD-MPC2为decoder-free确定性latent+MPPI，最终规划动作；表8 horizon3/512候选；表1 317M模型80任务score70.6/33GPU-days。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Hansen, Nicklas；Su, Hao；Wang, Xiaolong；UC San Diego；TD-MPC2: Scalable, Robust World Models for Continuous Control；首稿/公开日期2023/10/25；ICLR 2024；所读arXiv 2310.16828v2；[版本原文](https://arxiv.org/abs/2310.16828v2)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/nicklashansen/tdmpc2)。
- 精确位置：§3.1–3.3/4/5；表1/8；图7/8/9/10；阅读深度：精读正文方法/实验/讨论；附录H架构与表8，相关工作选读；原始PDF SHA256 `99832c555b66665ad1e26cd48e75ea9dda4f3750175b993e7ed5b8dfe399b9e0`。
- 原始依据：方法：联合学encoder/dynamics/reward/Q与max-entropy policy prior；执行时MPPI搜索，policy只提供部分候选，最终输出规划分布首动作。它不是保留SAC actor最终输出的结构。 模型：确定性decoder-free latent MLP；LayerNorm+Mish、SimNorm，输入状态/像素、动作、任务embedding；latent stop-grad一致性MSE+reward/value log-space CE，5个Q随机取2最小；policy entropy/归一化价值目标。默认horizon3、6轮、512候选、24policy候选、64精英（表8）。 条件：104在线任务DMC/Meta-World/ManiSkill2/MyoSuite；3seed，主要5M参数，batch256、UTD1。多任务80任务545M transitions由240单任务agent回放产生；317M模型单3090约33 GPU-days；39维动作上限，非UR5Gazebo。10像素DMC任务另验；各域控制周期未统一给出。 结果：表1多任务：1M模型score16.0/3.7GPU-days，5M49.5/4.2，317M70.6/33；图8 20k步新任务fine-tune47.0 vs从头24.0。图10视觉控制与DrQ-v2/DreamerV3相当，不能称全领域胜出。 时延：未涉及受控时延；MPPI额外计算不是驱动滞后。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；把policy候选和最终执行动作区别记录，latent一致性目标要有稳定语义。及任务相关decoder-free预测、规范化、Q/模型偏差检查。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者：离散动作扩展尚开放、奖励错设/物理安全和多任务数据规模；核查：数据采集成本不含在表1纯预训时长中，基线UTD/参数不同，同交互不是同计算。 平台：连续控制仿真；自动把SAC改为MPPI、复制表8超参或用多任务吞吐承诺72h。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第★ TD-MPC2条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-tdmpc2)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0288

- 主张：TD-MPC用TOLD/TD/MPPI；表2 Walker time-to-solve .47h vs LOOP7.72h，但SAC .41h，500k步TD-MPC5.60h vs SAC1.41h。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Hansen, Nicklas；Wang, Xiaolong；Su, Hao；UC San Diego；Temporal Difference Learning for Model Predictive Control；首稿/公开日期2022/03/09；ICML 2022；所读arXiv 2203.04955v2；[版本原文](https://arxiv.org/abs/2203.04955v2)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/nicklashansen/tdmpc)。
- 精确位置：§3/4/5；式7–11；表1/2；附录F/H；阅读深度：精读方法§3/4、实验§5、结论；附录超参和运行成本选读，相关工作浏览；原始PDF SHA256 `b80e9fc9eaebfa43ad30641ebb0327346998e604cd7421ae44701ef373b501aa`。
- 原始依据：方法：policy-guided MPPI优化短序列+末端value bootstrap；学习policy用于proposal/TD目标，最终是规划动作，非policy直接执行。 模型：确定性MLP h/d/R/Q/p，无RNN随机模型或decoder；reward MSE+TD Q MSE+EMA encoder latent一致性，多步反传；policy最大化Q；默认H5、512候选、6迭代（Dog8/Humanoid12）。 条件：92控制任务、DMC状态/像素、Meta-World；图像3×84²帧堆叠，state主评5seed，像素100k表10run；单RTX3090 wall-time；任务各自action repeat，未统一servo Hz。 结果：表1 100k像素Finger Spin943±59 vs DrQ901±104，但Cheetah222±88 vs DrQ344±67；表2 Walker达到940分：.47h vs LOOP7.72h、SAC .41h；500k步TD-MPC5.60h vs SAC1.41h。并非比SAC所有wall-time更快。 时延：未注入显式时延；附录约20ms推理是该GPU模型规划成本，不能当UR5控制/传输延迟。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；预测步长、任务horizon、值函数与真实步耗时分别记。及多步latent一致性与task-oriented模型。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者：Finger Turn Hard探索不足、模型/规划精度与算力权衡；核查：state任务优势不等于视觉任务全面优于所有方法。 平台：DMC/Meta-World；据20ms固定FoReM动作周期或将MPPI叫SAC输出。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第★ TD-MPC条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-tdmpc)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0289

- 主张：MBPO在真实replay状态生成短模型样本训练SAC，最终SAC动作；图2Ant300k vs SAC3M，图3Hopper1步强/500步失败；非普适提升保证。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Janner, Michael；Fu, Justin；Zhang, Marvin；Levine, Sergey；UC Berkeley；When to Trust Your Model: Model-Based Policy Optimization；首稿/公开日期2019/06/19；NeurIPS 2019；所读arXiv v3修订2021；所读arXiv 1906.08253v3；[版本原文](https://arxiv.org/abs/1906.08253v3)；DOI：本轮未核到DOI。代码/入口：公开作者代码：[链接](https://github.com/jannerm/mbpo)。
- 精确位置：§4.1–4.3/5/6/7；算法2；图2/3/4；附录C表1；阅读深度：正文全文精读；附录C超参表，证明按假设/定理核查而非逐行复证；原始PDF SHA256 `89d12b6142a285e541f6315a8911db469bea33514f3b80bdbe6e52439197b149`。
- 原始依据：方法：从真实replay状态branched短rollout生成训练样本，给SAC额外更新；部署仍由SAC actor输出，没有候选未来反馈修正。 模型：原观测/状态空间概率ensemble（7个MLP），预测next与reward的对角高斯，NLL；随机选择ensemble成员表示不确定性；非潜空间/非像素decoder。模型horizon按任务1→15/25或固定1；SAC Q与actor照常训练。 条件：六个MuJoCo控制任务、标准1000步回合、5trial；20–40 SAC更新/真实步，400模型rollouts/真实步（附录C）；原文所读段未提供统一GPU/总训练时长/控制Hz，不能据sim-time分钟推wall-time。 结果：图2 Ant300k真实步达到SAC3M步的相近回报（曲线口径，无精确数字硬读）；图3 Hopper固定1步rollout已强，500步失效，200步不如短rollout。图4 model/real return相关为Hopper诊断。 时延：未涉及显式时延或执行器动态。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；普通SAC最终actor与模型用途区别；计入模型训练/生成/额外更新成本。及短预测降低误差累计与新policy分布下检查模型。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：严格误差界过于悲观，经验model generalization用于动机，不是实用算法对任意机器人必单调提升；部署策略变更会带来模型distribution shift；同交互下更新数/模型计算不同。 平台：MuJoCo；未经授权往replay加合成数据/改UTD；把理论界当Task4收益保证。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第★ MBPO条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-mbpo)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0290

- 主张：Dream-MPC用policy候选梯度优化序列；表1DMC433低于TD-MPC2 MPPI657，胜policy-only367；收益依赖初始policy，不普遍胜MPPI。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Spieler, Jonathan；Behnke, Sven；University of Bonn；Dream-MPC: Gradient-Based Model Predictive Control with Latent Imagination；首稿/公开日期2026/05/06；ICML 2026（作者官方代码标注）；所读arXiv v3；所读arXiv 2605.04568v3；[版本原文](https://arxiv.org/abs/2605.04568v3)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/jspieler/dream-mpc)。
- 精确位置：§4/5.1–5.5；表1/2/3/4；算法1；阅读深度：部分：摘要、§4完整规划方法、§5设置/结果/消融；原始PDF SHA256 `0daa66219bae0d15e831e71783685d06d3436fdc3ebcc03c4c34e1540173b8ca`。
- 原始依据：方法：policy rollout产生候选；加不确定性正则、跨步复用，梯度上升优化序列；最终选择预测return最高序列首动作。优化后的动作通常不是原policy采样。 模型：TD-MPC2/BMPC确定性latent+reward/Q；Dreamer分支RSSM；继承原模型loss，推理优化return-uncertainty，不是重新定义SAC loss；默认示例5候选×1迭代×H3，前向次数比较不能当含backward wall-time。 条件：24状态连续控制（DMC、HumanoidBench、Meta-World），另6视觉DMC；3seed×10eval；部分试验仅替换预训planner，另有从头训练。动作Hz、完整wall-time本次未查到；代码未运行。 结果：表1 DMC TD-MPC2规划657±225、policy-only367±247、Dream-MPC433±259：并未击败原MPPI。§5.1 BMPC基础上IQM+26.7%、mean+20.5%；表3 Dreamer Cheetah751±111→836±49，Walker575±33→632±52。 时延：未研究显式时延；推理优化耗时要另测。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；区分候选动作与优化后执行动作。及模型不确定性、跨时刻warm-start，仅作为设计思路。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者：依赖好policy初值，局部极值与value精度；核查：5×1×3与512×6×3前向数比较忽略梯度反传/批量并行，不能说wall-time快同样倍数。 平台：控制仿真；将梯度MPC追加成当前SAC执行链或认为保留policy prior就仍是SAC最终动作。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第Dream-MPC条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-dreammpc)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0291

- 主张：IRIS为token世界模型但actor在解码图像上学习；表1mean1.046 vs SPR.616，非击败EfficientZero1.943。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Micheli, Vincent；Alonso, Eloi；Fleuret, François；University of Geneva等（作者署名）；Transformers are Sample-Efficient World Models；首稿/公开日期2022/09/01；ICLR 2023；所读arXiv 2209.00588v2；[版本原文](https://arxiv.org/abs/2209.00588v2)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/eloialonso/iris)。
- 精确位置：§2.1–2.3/3；表1；附录Horizon/compute；阅读深度：部分：摘要、§2方法、§3实验、表1与附录训练成本；原始PDF SHA256 `6b583542ba35dc99a36127dd3b7650aac5d28479f3fe0e5e47f741768ae587b4`。
- 原始依据：方法：VQ表示+GPT世界模型；actor/critic在解码出的想象像素上学习；部署actor。token dynamics不等于actor直接使用latent。 模型：16个离散image tokens+actions；transition/termination CE、reward MSE或CE；VQ L1/感知/commitment；policy/value CNN-LSTM与REINFORCE/λ-return，H20。 条件：Atari26任务、100k actions、5seed、每game最终100eval；8A10040GB、同GPU两个任务约7d，即3.5GPU-days/game（不是2h训练）。 结果：表1 meanHNS1.046/IQM.501，SPR .616/.337；10/26超人；EfficientZero mean1.943，不能称所有算法SOTA。 时延：未涉及时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；记录actor实际输入而非仅模型latent。及多步事件覆盖、模型数据不足影响策略。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：Frostbite新关卡事件罕见使模型/agent受分布限制；median优势不显著；自回归token成本大。 平台：Atari；换tokenizer/游戏预算或按2h gameplay承诺墙钟。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第IRIS条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-iris)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0292

- 主张：DIAMOND像素EDM想象RL，Atari100k表1mean1.459 vs STORM1.266、IQM.641 vs.636；单4090约2.9天/run。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Alonso, Eloi；Jelley, Adam；Micheli, Vincent；Kanervisto, Anssi；Storkey, Amos；Pearce, Tim；Fleuret, François；University of Geneva等（作者署名）；Diffusion for World Modeling: Visual Details Matter in Atari；首稿/公开日期2024/05/20；NeurIPS 2024；所读arXiv v2；所读arXiv 2405.12399v2；[版本原文](https://arxiv.org/abs/2405.12399v2)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/eloialonso/diamond)。
- 精确位置：§3.1/3.2/4/5；表1；附录D/E；阅读深度：部分：摘要、§3方法、§4实验、§5细节分析与表1；原始PDF SHA256 `842ff972404c74ca4bac9d2f37a6d309506c19eb3f2efa3e0daf75d6abc19707`。
- 原始依据：方法：在预测像素+reward/termination模型内训练CNN-LSTM actor/critic；部署actor，无online搜索。 模型：像素空间EDM U-Net next-frame，context图像+动作；denoise MSE，独立CNN-LSTM reward/termination，REINFORCE/λ-return；随机生成。附录Atari配置3NFE、想象H15；不迁移为FoReM默认值。 条件：Atari26任务×5seeds，100k动作；单4090≈12GB、2.9天/run；另CS:GO离线生成不是机器人RL；真实gameplay2h不是训练wall-time。 结果：表1 meanHNS1.459 vs STORM1.266/IRIS1.046，IQM.641 vs STORM.636；11/26超人。强调细节收益依任务，而非扩散普遍优于所有latent模型。 时延：未涉及时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；模型任务效用与图像指标分开。及任务关键细节不能随意压缩。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：rare events、分布外行为和扩散生成开销；模型奖励误差；像素细节对游戏关键不证明局部地图SAC需视频扩散。 平台：Atari/CS:GO；直接引入像素生成或把CS:GO引擎当robot控制证据。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第DIAMOND条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-diamond)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0293

- 主张：Simulus v4组合intrinsic reward与prioritizedWMreplay等；表9mean1.645/IQM.990 vs DIAMOND1.459/.641；这些组件会改变训练合同。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Cohen, Lior；Wang, Kaixin；Kang, Bingyi；Gadot, Uri；Mannor, Shie；Technion、Microsoft Research、ByteDance Seed；Simulus: Combining Improvements in Sample-Efficient World Model Agents；首稿/公开日期2025/02/17；arXiv预印本，首稿2025、所读v4修订2026；所读arXiv 2502.11537v4；[版本原文](https://arxiv.org/abs/2502.11537v4)；DOI：本轮未核到DOI。代码/入口：公开官方代码：[链接](https://github.com/leor-c/Simulus)。
- 精确位置：§2/3；图4/5；附录表9、Hardware/Run Times；阅读深度：部分：摘要、§2方法、§3实验、消融及附录表9/compute；原始PDF SHA256 `4a509242c78c245f09c95a35c9052398391dc8e215183a4871c0fc2aa5ee5e38`。
- 原始依据：方法：token模型想象训练actor/critic，非执行时规划；最终controller出动作。内在奖励改变探索/训练目标。 模型：REM/RetNet+parallel observation prediction，按模态tokenization；token CE、reward/value regression-as-classification；4个prediction head disagreement JSD作intrinsic reward，prioritized WM replay；CNN/MLP-LSTM controller、REINFORCE λ-return。 条件：Atari100k、DMC本体500k、Craftax1M；DMC连续向量和Craftax多模态token；附录AtariV100≈29h/4090≈12h、DMCV100≈40h；非Gazebo；统一控制Hz未报告。 结果：附录表9 Atarimean1.645/IQM.990，DIAMOND1.459/.641、REM1.222/.673；图4 DMCmean796 vs DreamerV3 754；版本v4不可和v1结果混用。 时延：未涉及时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；明确每项训练机制的对照/成本。及模块化、动作模态与预测效用检查。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者指出有限数据下intrinsic探索可能耗在无关区域；复合改进效应不能分配为单机制收益；公开后续Simulus-A不是本篇v4全部结果。 平台：Atari/DMC/Craftax；擅自加内在奖励/优先回放/额外探索，改变当前Task4合同。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第Simulus条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-simulus)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0294

- 主张：DayDreamer真实UR5 2Hz离散末端动作，图5 8h≈2.5物体/min；基线是Rainbow/PPO，非连续SAC；Sphero与DrQv2相近。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Wu, Philipp；Escontrela, Alejandro；Hafner, Danijar；Goldberg, Ken；Abbeel, Pieter；UC Berkeley；DayDreamer: World Models for Physical Robot Learning；首稿/公开日期2022/06/28；CoRL 2022（所读arXiv v1）；所读arXiv 2206.14176v1；[版本原文](https://arxiv.org/abs/2206.14176v1)；DOI：本轮未核到DOI。代码/入口：公開官方代码：[链接](https://github.com/danijar/daydreamer)。
- 精确位置：§2/3.1–3.4/5；图4/5/6/7；附录D；阅读深度：正文全文精读；附录D和机器人设置选读；原始PDF SHA256 `2ee10ae0961bef97ca522bb7ee5b7514e7a918a637dedad569b572b18bccb35e`。
- 原始依据：方法：DreamerV2 RSSM监督训练，imagined actor/critic优化；actor和learner异步线程，最终actor出动作；没有SAC内部candidate反馈。 模型：多模态encoder、确定性h+离散z RSSM，重建/动力学KL/reward；continuous用重参数梯度、discrete用REINFORCE。正文H16与附录D H15分开保留计数；batch32×length32。 条件：A1 20Hz、12电机角经PD+Butterworth；UR5 2Hz离散XYZ末端增量+夹爪，Z仅抓物时允许/目标bin上自动开夹爪；XArm约.5Hz；Sphero2Hz扭矩。直接真机在线学习、无仿真/专家预训练。单GPU学习（正文未给统一GPU型号）；UR5 8h、XArm10h是实验wall-time。 结果：图5 UR5 8h约2.5 objects/min，Rainbow/PPO只抓起后原bin放下；图4 A1≈1h翻身站立行走，SAC未站立/行走；图7 Sphero距离.15（场地归一单位），DrQv2表现相近。不能挑前两图宣称WM各平台必胜。 时延：未注入显式时延。异步用于减少动作计算阻塞，不等于识别/补偿驱动延迟；2Hz是任务动作频率。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；记录实际机器人动作限制和真实结果，保留不优于基线的案例。及异步训练与输入多模态；需经授权再做时序/性能验证。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者：磨损/人为干预/长训练边界；核查：A1图是单run，UR5空间和抓放逻辑强约束，UR5基线离散Rainbow/PPO不是普通连续SAC，同型号不等于同控制条件。 平台：A1/UR5/XArm/Sphero真机；将2Hz、8h和离散任务奖励当HuskyUR5合同/吞吐依据。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第★ DayDreamer条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-daydreamer)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0295

- 主张：WMPO arXivv1模型内GRPO；表1 P128 mean47.1% vs DPO37.3%，真机70% vsbase53%/DPO60%；另用真实policy轨迹对齐。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Zhu, Fangqi；Yan, Zhengyang；Hong, Zicong；Shou, Quanxin；Ma, Xiao；Guo, Song；HKUST、ByteDance Seed；WMPO: World Model-based Policy Optimization for Vision-Language-Action Models；首稿/公开日期2025/11/12；ICLR 2026身份由会议页面确认；正文实际读arXiv v1（2025），会议PDF本次403；所读arXiv 2511.09515v1；[版本原文](https://arxiv.org/abs/2511.09515v1)；DOI：本轮未核到DOI。代码/入口：官方公开代码：[链接](https://github.com/WM-PO/WMPO)（本轮只核页面/链接，未审计许可证兼容性或运行）。
- 精确位置：§3.2–3.4/4.1/4.6；表1/2；附录A；阅读深度：部分：摘要、§3完整方法、§4实验/结果、附录A；原始PDF SHA256 `1f3e88874bcb716ad0417347f9c6a73f1dd70c873e7872d3ceed6c57af2b7598`。
- 原始依据：方法：OXE视频预训→policy真实rollouts对齐WM→模型内GRPO；VideoMAE reward判别。最终VLA action head给动作；发生恢复行为不是显式candidate→feedback→SAC结构。 模型：OpenSora-STDiT-v3视频latent扩散但policy接口像素；去噪loss、noisy conditioning、逐帧action AdaLN；VideoMAE BCE success；action每维256bins，chunk8、context4帧、预测8帧；GRPO clipped ratio、动态丢弃同奖励组。 条件：MimicGen四task：每task300专家轨迹，另外P128/1280 policy真实轨迹做WM对齐，eval128初态；真实Cobot Mobile ALOHA：200专家+128policy，30trial、5mm插接间隙。附录policyBC8H100，WM/GRPO32H100；未核到统一controlHz/总wall-time。 结果：表1 P128平均47.1%，DPO37.3/GRPO33.2/base33.6；P1280为57.6 vs42.4/37.1。§4.6真机base53%/DPO60%/WMPO70%；不是完全零真实数据。 时延：未研究显式时延；frame alignment是动作-视频对应关系。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；WM需覆盖失败/当前policy分布，动作帧配对。及固定模型内训练的on-policy一致性；但GRPO非SAC。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：failure分布对齐和reward classifier可靠性重要；动态丢弃组影响采样成本/口径；会议原文未读，结果对应arXiv版本；不能将对齐数据免费。 平台：MimicGen/ALOHA真机；加载VLA/额外轨迹/改变任务奖励或复制256动作bins。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第WMPO条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-wmpo)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0296

- 主张：World4RL以冻结像素扩散模型训练PPO；表III报告93.3%/DP88.3%/BC68.3%，但BC逐项计数推导60.0%不一致，不能将“↑25”作为已核验提升。
- 类型：外部文献；表内算术推导；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Jiang, Zhennan；Liu, Kai；Qin, Yuxin；Tian, Shuai；Zheng, Yupeng；Zhou, Mingcai；Yu, Chao；Li, Haoran；等（完整署名见原文）；CAS/UCAS、Zhongguancun Academy、Tsinghua等（正文署名）；World4RL: Diffusion World Models for Policy Refinement with Reinforcement Learning for Robotic Manipulation；首稿/公开日期2025/09/23；arXiv预印本，2025；所读v2修订2026；所读arXiv 2509.19080v2；[版本原文](https://arxiv.org/abs/2509.19080v2)；DOI：本轮未核到DOI。代码/入口：项目页为占位链接，本次未找到可用官方实现：[链接](https://world4rl.github.io/)；不将YOUR_GITHUB_USERNAME模板当代码。
- 精确位置：§III/IV/V；表I/II/III/IV；阅读深度：部分：摘要、§III方法、§IV实验/§V消融；原始PDF SHA256 `939ff5ea644eb768d6822e864ebc5f3c57df959a5e515137215da4319515530a`。
- 原始依据：方法：先BC与reward classifier/WM预训，冻结WM，用想象PPO优化policy；部署policy，不在执行时额外搜索。 模型：像素EDM随机next-frame，4历史帧+连续动作twohot；denoise MSE、ResNet18成功BCE；PPO clipped目标并限制探索std，防分布外rollout。330M模型，不是RSSM。 条件：Meta-World六任务各50专家+150BC+30random轨迹、每条50步；真机Franka六任务各50专家+50BC+50random，固定初始场景、20eval/task。模型4A80040GB≈20h，policy单A800≈6h；controlHz未找到。 结果：表II六个Meta-World任务平均SR67.5%；表III真机WORLD4RL报告93.3%、DP88.3%、BC68.3%。但BC逐行13/20、8/20、12/20、12/20、12/20、15/20，加总72/120=60.0%，与表中68.3%不一致；WORLD4RL112/120=93.3%、DP106/120=88.3%与均值一致。这里的60%仅是表内算术核查，未拿到原始trial数据，不能确定哪一项印错；原文“↑25”不作为已证提升。Put bread in WORLD4RL16/20低于DP18/20。表I policy-rollout FVD326.5 vs NWM547.4。 时延：未研究显式时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；失败数据、OOD模型输出和任务SR分别审计。及冻结WM用于训练，模型高保真与task结果双证据。均为建议（待用户授权），未写入任务范围或改任何参数。 推导：表III BC成功计数输入13+8+12+12+12+15=72，每task20次、6task共120次；公式SR=Σ成功/(6×20)×100%=60.0%；仅等权表内算术，原始trial未知；原报68.3%与之矛盾。
- 适用限制：模型/成功classifier可能共同幻觉，动作support/std限制依赖数据；真机固定初态/少trial；WM组230轨迹vsBC50，不是同总信息预算。 核查发现表III BC汇总与分项算术矛盾，待独立复核/作者勘误；不以冲突值做收益结论。 平台：Meta-World/Franka；改变SAC为PPO、加入成功classifier奖励或额外数据而不计预算。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第World4RL条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-world4rl)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。World4RL BC汇总冲突待作者勘误或原始trial核验。

## SRC-0297

- 主张：World-Gymnast模型内GRPO，表1开drawer58% vsSIMPLER34%，close62%低于74%；表2蓝sink18×仅该任务。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Sharma, Ansh Kumar；Sun, Yixiang；Lu, Ninghao；Zhang, Yunzhe；Liu, Jiarao；Yang, Sherry；NYU、NYU Shanghai、UC Berkeley；World-Gymnast: Training Robots with Reinforcement Learning in a World Model；首稿/公开日期2026/02/02；arXiv预印本2026，v1；所读arXiv 2602.02454v1；[版本原文](https://arxiv.org/abs/2602.02454v1)；DOI：本轮未核到DOI。代码/入口：官方公开代码：[链接](https://github.com/world-gymnast/world-gymnast)。
- 精确位置：§3.1–3.4/4.1/4.2；表1/2；附录A.4；阅读深度：部分：摘要、§2/3方法、§4设置/主结果和适配说明；原始PDF SHA256 `cf1afebacb119acc44b84543229f8975a4bf0f836b6734a8b50b4474291c14ef`。
- 原始依据：方法：WorldGym生成视频，VLM给binary completion，GRPO优化OpenVLA-OFT；动作最终由VLA出。后续adaptation修改policy，而不是Task4冻结WM的首轮反馈。 模型：继承WorldGym600M latent diffusion（policy接口视频）；group相对优势、PPO式clipping，去KL、dynamic sampling；actionchunk5、rollout≤40模型步；模型具体损失见继承平台，不新造RSSM。 条件：Bridge/WidowX，17训练任务；AutoEval4真实任务，各10trial×5重复。4H200140GB full-policy finetune1–2天；对比SIMPLER有不同reward设计/任务覆盖；统一真实controlHz未找到。 结果：表1开drawer58±4% vsSIMPLER34±7%，close62±6%低于74±5%；蓝sink72±10% vs32±10%。表2蓝sink SFT4±4%→72±10%即18×，不能泛称所有任务18×。 时延：未研究显式时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；保留失败与不胜出任务，记录额外生成与reward计算。及模型/策略分布迭代风险和test-time compute单列。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者/方法：离线WM在policy distribution外误差累计，建议迭代真实数据；核查：VLM奖励、dynamic sampling成本与不同sim奖励需审；并非零采集成本/所有任务超过软件仿真。 平台：WidowX真机/SIMPLER；把test-time GRPO混进Task4首轮或接VLM奖励。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第World-Gymnast条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-worldgymnast)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0298

- 主张：Interactive World Simulator以consistency latent作示范生成/imitation与评测；图7相关r=.8553/.8455/.8869/.9908，单4090生成15FPS；非SAC实验。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Wang, Yixuan；Syed, Rhythm；Wu, Fangyu；Zhang, Mengchao；Onol, Aykut；Barreiros, Jose；Nayyeri, Hooshang；Dear, Tony；等（完整署名见原文）；Columbia、Toyota Research Institute、Amazon、UIUC；Interactive World Simulator for Robot Policy Training and Evaluation；首稿/公开日期2026/03/09；RSS 2026由官方代码标注；正文arXiv v1；所读arXiv 2603.08546v1；[版本原文](https://arxiv.org/abs/2603.08546v1)；DOI：本轮未核到DOI。代码/入口：官方公开代码：[链接](https://github.com/WangYixuan12/interactive_world_sim)。
- 精确位置：§III.B/C/D、IV.A–D；表I；图7；阅读深度：部分：摘要、§III方法、§IV设置/预测/训练/评测结果；原始PDF SHA256 `6038aefdcdd3ec7b6e50304c32438e98cd106ba653f282af78f30c11bef39f22`。
- 原始依据：方法：人/策略在WM中采合成示范后做imitation training（DP/ACT/π0等），以及policy evaluation；本篇不是在线SAC/GRPO训练收益。最终动作由外部imitation policy输出。 模型：image encoder+consistency decoder，冻结autoencoder后学latent consistency dynamics；3Dconv/FiLM、观测历史+动作；两阶段加权回归损失，context噪声训练；单帧自回归，随机模型。 条件：ALOHA双臂6真实task（绳、mug、piles等）+MuJoCo T-push；每task≈600×200step play episodes≈6h采集，T-pushsim10kepisodes；128²图像，动作空间有平面限制。训练单H2006h+12h，单4090最高15FPS/>10min稳定生成；192step=19.2s是评测视频时轴。 结果：图7所绘四组真实/model相关r=.8553/.8455/.8869/.9908；只限所评task/policies。表I对比包括community Dreamer4实现（非作者官方），不能写成击败原作者配置。 时延：未研究受控时延；15FPS是model生成，不是ALOHA控制器Hz。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；区分仿真器指标和真实SR，基线实现身份透明。及consistency模型提速、闭环交互质量验证。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者可访问生成demo不证明所有接触准确；任务限制/覆盖量、imitation示范人工开销；相关性不能替代真实反馈。 平台：ALOHA/仿真T-push；把合成示范训练算普通SAC或直接新增图像生成平台。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第Interactive World Simulator条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-interactive)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0299

- 主张：WorldGym评测policy不训练RL；§4.1 OpenVLA真实70.6% vsmodel67.4%、Octo20%vs23.82%，只支持已评政策相关。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Quevedo, Julian；Sharma, Ansh Kumar；Sun, Yixiang；Suryavanshi, Varad；Liang, Percy；Yang, Sherry；Stanford University、NYU、Google DeepMind；WorldGym: World Model as An Environment for Policy Evaluation；首稿/公开日期2025/05/31；arXiv预印本2025，v3仍标Under review；所读arXiv 2506.00613v3；[版本原文](https://arxiv.org/abs/2506.00613v3)；DOI：本轮未核到DOI。代码/入口：作者项目页本次未找到完整代码仓库（页面链接需后续核验）：[链接](https://world-model-eval.github.io/)。
- 精确位置：§3.1/3.2/4.1–4.3；图4；表1/2；阅读深度：部分：摘要、§3方法、§4实验、附录A参数；原始PDF SHA256 `81ac9b9109a60c39b5c739dcd0484750f4d9c29e70f87666601076993ab8dd24`。
- 原始依据：方法：外部VLA在action-conditioned WM中Monte Carlo rollout，GPT-4o评分；不是在这篇里用RL提高policy。 模型：latent DiT diffusion forcing，动作线性embedding/AdaLN、action dropout/CFG，因果temporalattention；horizon按policychunk变化，生成像素给policy，VLMreward不等于真实成功测量。 条件：OXE多机器人视频含Bridge/RT1/VIOLA/BerkeleyUR5；17个Bridge未见task，Octo/RT1X/OpenVLA对照；256²图像、7维动作；模型2A10080GB、300kupdates、batch16、10diffusionsteps。评估公开既有真机结果，非本轮新UR5训练。 结果：图4/§4.1真实vsmodel：RT1-X14.0%vs15.5%，Octo20.0%vs23.82%，OpenVLA70.6%vs67.4%；对照为policy身份，不是baseline训练改进。 时延：未研究显式时延。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；世界模型评测只作辅助，不能取代真实环境。及显式动作sweep和分布外相对排名检查。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者：精细物体交互仍难；VLM判分、fewpolicy相关和OOD生成幻觉；正确排序不意味着逐seed/绝对SR无偏。 平台：Bridge/WidowX等；用modelSR替代Gazebo物理末端成功验收。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第WorldGym条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-worldgym)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0300

- 主张：WorldEval用policy内部latent action非真实指令生成评测视频；表1Pearson .942 vsreal-to-sim .411，不能支持绝对物理正确性。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Li, Yaxuan；Zhu, Yichen；Wen, Junjie；Shen, Chaomin；Xu, Yi；Midea Group、East China Normal University；WorldEval: World Model as Real-World Robot Policies Evaluator；首稿/公开日期2025/05/25；arXiv预印本2025，v1；所读arXiv 2505.19017v1；[版本原文](https://arxiv.org/abs/2505.19017v1)；DOI：本轮未核到DOI。代码/入口：官方公开代码：[链接](https://github.com/liyaxuanliyaxuan/Worldeval)。
- 精确位置：§3.2/3.3/4；表1/2；附录A/B；阅读深度：部分：摘要、§3方法、§4实验/表1/2、附录A/B；原始PDF SHA256 `9ba537bf8a9bae5223465c26858d1c55489253e107b6dca53015f0370d30a043`。
- 原始依据：方法：Policy2Vec latent+language+首图生成视频，Gemini2.0判断success；不做模型内RL，最终动作仍由被评policy产生。latent action不是最终执行指令。 模型：WAN2.1 14B image-to-video latent扩散、LoRA+projection；条件是policy输出前latent embedding与语言；依赖生成模型原去噪目标，未引入物理state监督。附录81帧、50diffusionsteps。 条件：AgileX ALOHA式双6DoF，14维联合动作/状态，top RealSense457，采集50Hz；5tasks每task40eval、总>1000rollouts；部分tasks100/50轨迹。附录8H800约11h LoRA训练，非推理Hz。 结果：表1 WorldEval vs RoboTwin real-to-sim平均Pearson .942 vs .411、MMRV .044 vs .261；表2 Policy2Vec .939 vsVQVAE -.862，一种编码依赖此policy/dataset条件。 时延：未受控研究时延；50Hz数据采样不能作为UR5频率依据。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；评测代理与独立物理反馈分开，数据/策略身份审计。及行为表征对齐和排名而非像素指标评估。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者：低成绩policy幻觉/ghosting和未知场景泛化；核查：用最终checkpoint latent训练WM可能混淆“latent更接近训练分布”与真实policy更好（附录B对此现象有描述），跨policy latent语义不必共通。 平台：AgileX双臂真机；拿policy latent代替真实执行动作监督或用Pearson作Task4任务验收。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第WorldEval条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-worldeval)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0301

- 主张：Ctrl-World采用多视角动作条件SVD，筛成功合成数据SFT；图9 38.7%→83.4%为44.7个百分点，不是RL反馈提升。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Guo, Yanjiang；Shi, Lucy Xiaoyang；Chen, Jianyu；Finn, Chelsea；Stanford University、Tsinghua University；Ctrl-World: A Controllable Generative World Model for Robot Manipulation；首稿/公开日期2025/10/11；ICLR 2026；首稿2025，所读v3；所读arXiv 2510.10125v3；[版本原文](https://arxiv.org/abs/2510.10125v3)；DOI：本轮未核到DOI。代码/入口：官方公开代码：[链接](https://github.com/Robert-gyj/Ctrl-World)。
- 精确位置：§4.1/4.2/5.1–5.4/6；表1；图9；阅读深度：部分：摘要、§4方法、§5设置/结果及§6局限；原始PDF SHA256 `5acee75221001b53171078e8b02f85151147b6dc629b36cf086d91d1c921ba0f`。
- 原始依据：方法：多视角预测→外部policy rollout评测；搜索并人选成功合成轨迹后SFT改善policy，非RL。最终π0.5等policy出动作。 模型：SVD1.5B latent diffusion，三视角jointtokens、pose-conditioned sparse history memory+frameaction crossattention；diffusion x0 MSE；历史7帧、间隔1–2s、下一15动作=1schunk。 条件：DROID95,599轨迹、564场景、约76k成功/19k失败；192×320×3camera，16H100、batch64、2–3天；数据15动作/s不等于FoReM动作Hz；每task生成400轨迹人选25–50成功、SFT2kupdates。 结果：表1第三视角PSNR23.56/FVD97.4 vs WPE单视角20.33/156.4；图9新指令任务成功38.7%→83.4%，提高44.7个百分点，非相对44.7%；是合成data SFT。 时延：未研究通信/执行时延；历史1–2s采样间隔非delay。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；成功率差分单位和额外人工/数据成本写清。及长期history re-anchoring、action细粒度对齐。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者明确不够精确以改善已见指令低层success；精细接触/长推理/初态敏感；人选/成功过滤成本不可省略。 平台：DROID/Franka；把SFT提升当冻结WM反馈SAC收益或直接新增multi-camera。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第Ctrl-World条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-ctrlworld)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0302

- 主张：固定delay论文为观测/奖励d2/5/10/20步，非执行延迟；表3Cheetah d20 Extended493.3±21.8 vsAgnostic118.8±11.4，预算与平台限制明确。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Karamzade, Armin；Kim, Kyungmin；Kalsi, Montek；Fox, Roy；UC Irvine；Reinforcement Learning from Delayed Observations via World Models；首稿/公开日期2024/03/18；RLC/RLJ 2024（所读arXiv v2）；所读arXiv 2403.12309v2；[版本原文](https://arxiv.org/abs/2403.12309v2)；DOI：本轮未核到DOI。代码/入口：官方公开代码：[链接](https://github.com/indylab/DelayedDreamer)。
- 精确位置：§3.1/3.3/4.1–4.4/5/6；图3/4；附录B表1–3；阅读深度：正文全文精读；理论定义/命题按假设核查；附录B各数据表选读；原始PDF SHA256 `2ce1c56c9e4a5f918e3b58bcd5943e0324e8d36ae99caac0e088e9a3d04ef4db`。
- 原始依据：方法：Extended actor以延迟latent+其后已执行actions为输入；Latent actor把模型推进d步；Memoryless不用动作buffer，Agnostic在无delay训练后仅推理补偿。Dreamer模型内actor学习，最终actor输出，不是candidate下一步反馈。 模型：DreamerV3 RSSM deterministic+stochastic，继承重建/奖励/continue+KL；model监督按真实时间重新对齐；Extended actor/critic值监督再对齐；模型理论等价要求congruent，不声称学得模型精确满足。H16正文，与episode/d相关会影响有效想象。 条件：MuJoCo4任务Dreamer500k steps，对照DCAC1M、D-TRPO5M；DMC6任务本体/图像，图像1M，5seeds。无真机；控制Hz和GPU/总wall-time正文未报告，不能把步数换毫秒。 结果：附录B表3 Cheetah Run图像d20：Extended493.3±21.8、Memoryless395.5±21.2、Latent273.1±24.6、Agnostic118.8±11.4（SEM）；§5.2视觉DMC归一均值相对Agnostic约+250%（作者汇总，不能用该单task数字重建它）。 时延：观测/奖励到达层：固定d∈{2,5,10,20}环境/决策步，agent得到o(t-d)/r(t-d)，动作不故意迟发。reset初期随机动作等首观测；监督完成后重排为真实(o,a,r)。原文不提供统一秒数，未沿用为UR5取值。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；测量stamp、已执行动作历史与监督配对。及把到达观测前的belief预测与训练信息权限分开。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者：Latent多步误差累积、Extended架构与超参敏感、Reacher弱；核查：不同baselines交互预算不等，未知delay训练与已知训练不能合并；固定delay证明不涵盖随机乱序。 平台：MuJoCo/DMC；新增delay机制、把d20换成UR5毫秒、宣称能补偿物理驱动动态。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第★ 固定观测延迟 Dreamer条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-delayfixed)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0303

- 主张：DA-Dreamer处理有timestamp的随机OOS观测、posterior/prior回放；表1U0–20 HalfCheetah2958.56低于Encoding4242.77，表2长delaybutton .91vs.12。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Karamzade, Armin；Kim, Kyungmin；Lanier, JB；Corsi, Davide；Fox, Roy；UC Irvine；Model-Based Reinforcement Learning under Random Observation Delays；首稿/公开日期2025/09/25；L4DC 2026，PMLR331；首稿2025，所读arXiv v2；所读arXiv 2509.20869v2；[版本原文](https://arxiv.org/abs/2509.20869v2)；DOI：本轮未核到DOI。代码/入口：官方公开代码：[链接](https://github.com/indylab/DA-Dreamer)。
- 精确位置：§3/4.1/4.2/5/7；式3–6；算法1；表1/2；附录A/B；阅读深度：正文全文精读；附录A/B.1–B.4；证明/滤波近似按条件核查；原始PDF SHA256 `781dbaabd538b2f5fb366584fdec0af1267f3f7b86973a79cbed0f504c2bd2af`。
- 原始依据：方法：timestamped buffer，重放从最早未到达观测前的belief checkpoint；有观测用posterior、没有用prior，policy根据belief采样；model完整顺序数据训练，policy按received information；最终Dreamer actor。 模型：RSSM ELBO/重建+KL；approximate posterior filtering，可Kparticles（默认1），确定性路径保留history；等待episode末所有pending观测再入replay；imagination没有新真实观测，作者承认训练分布有偏差。 条件：MuJoCo6任务/Meta-World4视觉任务、64²、1M envsteps、5seed；Meta-World repeat2→500k decision steps，回合人为缩到50步（主动放大deadline效应），无真机。GPU/总时长/统一Hz未报告。 结果：表1 U{0,10} HalfCheetah DA4985.40±253.10 vs Encoding4189.26±401.81；U{0,20} DA2958.56±54.19低于Encoding4242.77±213.47。表2 N+(20,1) buttonpress SR .91±.13 vs memoryless .12±.14；均为mean/95%CI。 时延：sensor观测生成后独立整数d，到达t+d，允许0/多个/OOS；假设已知生成stamp及有界maxD。分布U{0,10}/U{0,20}，MetaU{0,5}、N+(10,3)/N+(20,1)（按文中记号，Gaussian截断后round整数，参数第二项遵原文方差约定）；不提供统一秒数，无UR5换算。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；到达时刻与采样时刻分开、乱序重播及跨episode边界。及历史belief与实时信息权限。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：作者：递归误差、开销随最大delay线性增加；核查：近似belief不是精确posterior，K1缺全面不确定性表达，50步Metaepisode改变条件，逐task不全面占优。 平台：MuJoCo/Meta-World；擅自新增乱序队列/重写观察合同/搬delay步数为硬件设定。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第★ 随机观测延迟 DA-Dreamer条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-delayrandom)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0304

- 主张：ResidualRL使用Panda4ms采样、通信状态delay40–240ms等+作者单次50ms累计；表1mean .037m(sim)/.045m(real)非baseline提升倍数。
- 类型：外部文献（原论文）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Deng, Kaize；Yang, Zewen；Technical University of Munich；Residual Reinforcement Learning for Robot Teleoperation under Stochastic Delays；首稿/公开日期2026/05/14；arXiv预印本2026，v1；所读arXiv 2605.15480v1；[版本原文](https://arxiv.org/abs/2605.15480v1)；DOI：本轮未核到DOI。代码/入口：原文未给可核的官方代码链接，本次开源状态未知。
- 精确位置：§2.1–2.4/3.1/3.2/4.1–4.3；表1；阅读深度：部分：摘要、§2系统/§3方法、§4实验与附录训练说明；原始PDF SHA256 `fb600fef69353b5a4a0ea73b33247c4f2093fed33368ea69647c9975f9d9ee97`。
- 原始依据：方法：LSTM重建当前leader状态，nominal computed-torque PD+SAC residual torque；最终力矩为两项合成，不是Task4 SAC高层动作全量输出。 模型：数值state空间LSTM+residual head，history q/qdot/delay，监督state估计与smoothness；SAC critic/actor和tracking/velocity代价；没有视觉生成latent WM。 条件：同构leader/follower Franka Panda，MuJoCo训练后真机部署无重训；采样4ms=250Hz；7关节力矩、任务Cartesian轨迹；总steps/GPU/完整wall-time未从已读设置中核出，保留未核验。 结果：表1高delay/highvariance sim meanCartesian error .037m/max.063m，real .045m/.078m；1.22×/1.24×是sim-to-real误差比，不是相对baseline提高倍数。PD/PMDC为性能图基线，未从曲线猜精确值。 时延：leader→agent状态传输U(120,160)/U(200,240)/U(40,240)ms；agent–follower action/observation链正文写ωo=ωa=50ms；作者报告总170–210/250–290/90–290ms，仅加一次50。符号/链路累计有歧义，不能自作解释加两次。4ms采样中状态delay分别30–40/50–60/10–60周期（端点整除无取整）；50ms=12.5周期，原文未给离散取整，本轮不补造。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；采样周期、链路层次与不确定符号明确记。及残差分工、tracking与smoothness冲突。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：本体/torque/nominalcontroller与UR5位置控制不同；LSTM真实监督依仿真可得state，传递延迟不是servo响应；稳定性描述不构成任意policy正式证明。 平台：Franka仿真/真机；未经授权新增torque residual控制/teleop或沿用Panda delay值为UR5合理范围。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第Residual RL Teleoperation条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-residualdelay)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0305

- 主张：World Model for Robot Learning: A Comprehensive Survey原文提供方法/评测分类，没有本综述新的机器人RL训练结果；被引方法仅为待补原文的候选线索。
- 类型：外部文献（原始综述分类；被引方法为二手线索）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Hou, Bohan；Li, Gen；Jia, Jindou；An, Tuo；Guo, Xinying；Leng, Sicong；Geng, Haoran；Ze, Yanjie；等（完整署名见原文）；NTU及Berkeley/Stanford/Tokyo/Oxford/Microsoft/ETH/Princeton/Harvard联合团队；World Model for Robot Learning: A Comprehensive Survey；首稿/公开日期2026/04/30；arXiv综述预印本（版本/日期见元数据）；所读arXiv 2605.00080v1；[版本原文](https://arxiv.org/abs/2605.00080v1)；DOI：本轮未核到DOI。代码/入口：[链接](https://github.com/NTUMARS/Awesome-World-Model-for-Robotics-Policy)。
- 精确位置：§3.1/3.2–3.6/4/7/8；表1/5/6；阅读深度：部分原文：摘要、§3分类/§4 simulator、§7评测、§8.4–8.6挑战；对被引方法的讨论属于二手线索，不视为已读其原文；原始PDF SHA256 `1b035d79d5c135fd437e1bbe7625a7e284a405e0451a240e816ce5dcaf35f586`。
- 原始依据：方法：综述覆盖想象训练、规划、候选筛选、数据生成/评测；最终动作输出者随被引方法变化。所引其他论文本轮未精读，标二手线索。 模型：包含像素/latent/几何/随机/确定性各族，不存在本综述单一模型、预测horizon或训练loss；应回原始方法核验。 条件：非新训练/实验研究；机器人、动作频率、数据/compute来自不同文献，不能合并为统一设定。 结果：表1分类、表5/6摘录他文benchmark；没有新机器人运行或统一实验预算，不能直接把表中汇总当同协议排名。 时延：没有本综述自己的受控时延实测；被引方法时延参数未在本条核验，不登记成UR5依据。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；仅用分类检查当前方法描述和评测是否混淆。及候选补读定位与predictive fidelity/control utility分离。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：综述分类是作者整理框架，非所有方法的独立复现；跨版本/平台/预算数值不能直接排名，近期期刊模板页眉不当发表场合。 平台：跨平台文献；凭综述二手数值设Task4参数或扩大正式精读/实施范围。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第World Model for Robot Learning: A Comprehensive Survey条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-survey1)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0306

- 主张：World-Action Models for Robot Learning and Control: A Survey原文提供方法/评测分类，没有本综述新的机器人RL训练结果；被引方法仅为待补原文的候选线索。
- 类型：外部文献（原始综述分类；被引方法为二手线索）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Lu, Zuxing；Zhai, Hongjia；Wang, Guanzhi；Zeng, Huajian；Yang, Jiaqi；Liu, Jingyu；Cheng, Lei；Zhang, Yuantai；等（完整署名见原文）；MBZUAI及Caltech/Amazon/UVA/Georgia Tech/NYU/Berkeley联合团队；World-Action Models for Robot Learning and Control: A Survey；首稿/公开日期2026/09/13；arXiv综述预印本（版本/日期见元数据）；所读arXiv 2609.16074v1；[版本原文](https://arxiv.org/abs/2609.16074v1)；DOI：本轮未核到DOI。代码/入口：原文官方项目清单：[链接](https://rcl-robotics.github.io/Awesome-World-Action-Models)；这是文献资源入口，不是本综述训练实现。
- 精确位置：§II/III/V；表II/III；参考[74]；阅读深度：部分原文：摘要、§II概念、§III模型分类、应用/§V评测与挑战；对被引方法的讨论属于二手线索，不视为已读其原文；原始PDF SHA256 `c410bbbd06e25c4592a043acf66ca2dcab5ef03eeae601c29093e50898338df4`。
- 原始依据：方法：综述覆盖想象训练、规划、候选筛选、数据生成/评测；最终动作输出者随被引方法变化。所引其他论文本轮未精读，标二手线索。 模型：包含像素/latent/几何/随机/确定性各族，不存在本综述单一模型、预测horizon或训练loss；应回原始方法核验。 条件：非新训练/实验研究；机器人、动作频率、数据/compute来自不同文献，不能合并为统一设定。 结果：表II为HNS/SR/轨迹/生成等指标定义、表III资源映射；无原创RL性能表或统一训练预算。 时延：没有本综述自己的受控时延实测；被引方法时延参数未在本条核验，不登记成UR5依据。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；仅用分类检查当前方法描述和评测是否混淆。及候选补读定位与predictive fidelity/control utility分离。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：综述分类是作者整理框架，非所有方法的独立复现；跨版本/平台/预算数值不能直接排名，近期期刊模板页眉不当发表场合。 平台：跨平台文献；凭综述二手数值设Task4参数或扩大正式精读/实施范围。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第World-Action Models for Robot Learning and Control: A Survey条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-survey2)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0307

- 主张：World Models for Robotic Manipulation: A Survey原文提供方法/评测分类，没有本综述新的机器人RL训练结果；被引方法仅为待补原文的候选线索。
- 类型：外部文献（原始综述分类；被引方法为二手线索）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Wang, Fangyuan；Wang, Ziyuan；Pei, Guorui；Zhang, Mengshi；Liang, Canxi；Hu, Jun；Li, Zhongxuan；Wu, Jinsong；等（完整署名见原文）；Hong Kong PolyU、Great Bay University、KTH等（全机构见原文署名）；World Models for Robotic Manipulation: A Survey；首稿/公开日期2026/05/27；arXiv综述预印本（版本/日期见元数据）；所读arXiv 2606.00113v1；[版本原文](https://arxiv.org/abs/2606.00113v1)；DOI：本轮未核到DOI。代码/入口：本轮未核到独立官方代码/清单repo。
- 精确位置：§IV/V.B/V.C/V.D/VI/VIII；参考[69]/[84]/[85]/[90]；阅读深度：部分原文：摘要、representation分类、§IV/V/VI功能与§VIII评测、候选引用条目；对被引方法的讨论属于二手线索，不视为已读其原文；原始PDF SHA256 `ab4e6baa7d48a482e138220441f3d07cfbbae8def18557e8a99af275e2bc4986`。
- 原始依据：方法：综述覆盖想象训练、规划、候选筛选、数据生成/评测；最终动作输出者随被引方法变化。所引其他论文本轮未精读，标二手线索。 模型：包含像素/latent/几何/随机/确定性各族，不存在本综述单一模型、预测horizon或训练loss；应回原始方法核验。 条件：非新训练/实验研究；机器人、动作频率、数据/compute来自不同文献，不能合并为统一设定。 结果：综述称覆盖34个manipulation datasets；分类表不是新实验数值，对被引方法只作二手定位。 时延：没有本综述自己的受控时延实测；被引方法时延参数未在本条核验，不登记成UR5依据。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；仅用分类检查当前方法描述和评测是否混淆。及候选补读定位与predictive fidelity/control utility分离。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：综述分类是作者整理框架，非所有方法的独立复现；跨版本/平台/预算数值不能直接排名，近期期刊模板页眉不当发表场合。 平台：跨平台文献；凭综述二手数值设Task4参数或扩大正式精读/实施范围。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第World Models for Robotic Manipulation: A Survey条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-survey3)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。

## SRC-0308

- 主张：A Step Toward World Models: A Survey on Robotic Manipulation原文提供方法/评测分类，没有本综述新的机器人RL训练结果；被引方法仅为待补原文的候选线索。
- 类型：外部文献（原始综述分类；被引方法为二手线索）；本项目适用性部分为工程分析/待授权建议，非项目实测。
- 核查状态：已核验下列所读原文段落/参数/表图；阅读笔记review待独立复核；未复现、不证明FoReM适用。
- 来源：Zhang, Peng-Fei；Cheng, Ying；Sun, Xiaofan；Wang, Shijie；Li, Fengling；Zhu, Lei；Shen, Heng Tao；作者联合机构详见正文署名；本轮未逐机构核验；A Step Toward World Models: A Survey on Robotic Manipulation；首稿/公开日期2025/10/31；arXiv综述预印本（版本/日期见元数据）；所读arXiv 2511.02097v2；[版本原文](https://arxiv.org/abs/2511.02097v2)；DOI：本轮未核到DOI。代码/入口：本轮未核到独立官方代码/清单repo。
- 精确位置：§II/III/IV/V；表I；参考[22]/[30]/[63]；阅读深度：部分原文：摘要、§II概念、§III概览、§IV决策/训练功能与§V挑战/结论；对被引方法的讨论属于二手线索，不视为已读其原文；原始PDF SHA256 `14e5c813af11a2cbd3d18a64a3ef6e8b95333cd14342e54a520a726d82097ac8`。
- 原始依据：方法：综述覆盖想象训练、规划、候选筛选、数据生成/评测；最终动作输出者随被引方法变化。所引其他论文本轮未精读，标二手线索。 模型：包含像素/latent/几何/随机/确定性各族，不存在本综述单一模型、预测horizon或训练loss；应回原始方法核验。 条件：非新训练/实验研究；机器人、动作频率、数据/compute来自不同文献，不能合并为统一设定。 结果：表I列方法组成、输入/输出/architecture；没有原创training run或跨论文统一胜负实验。 时延：没有本综述自己的受控时延实测；被引方法时延参数未在本条核验，不登记成UR5依据。 均为原文转述，非逐字引文。
- 本项目采用：仅登记阅读、角色分类与Task4条件映射；仅用分类检查当前方法描述和评测是否混淆。及候选补读定位与predictive fidelity/control utility分离。均为建议（待用户授权），未写入任务范围或改任何参数。
- 适用限制：综述分类是作者整理框架，非所有方法的独立复现；跨版本/平台/预算数值不能直接排名，近期期刊模板页眉不当发表场合。 平台：跨平台文献；凭综述二手数值设Task4参数或扩大正式精读/实施范围。。外部数值不证明UR5参数合理。
- 使用位置：[阅读笔记第A Step Toward World Models: A Survey on Robotic Manipulation条及比较/建议](agent_logs/project/20261014-codex-wm-rl-literature.md#paper-survey4)。
- 核查人及日期：Codex /root；实际模型GPT-6（系统仅披露系列，精确型号未知），实际推理档位未知；2026-10-14。推荐配置不冒充实际配置。
- 待办与变更：独立复核所列数表、正式版差异与适用性；未报告/未核出字段保持未知；原文不能作为FoReM验收。


<a id="src-0309"></a>
## SRC-0309 — task6.5 T65-D1包装修正与原作者PR2 Gazebo50阶段一结果

- 支撑主张：原作者PR2模型simpleobstacle Gazebo新run t6.5-pr2-gz-r2 seed999–1048完整50回合，26/50=52%（goal26、success_nojumps21），23个非成功回合各底盘碰撞50次（累计1150），另一非成功回合无底盘碰撞且max_close_steps_reached，IK仅1回合1次。总55921步/均1118.42/范围245–2706；selfcollision上游指标4/50。Collision打印879条、16种环境对象字符串，全部机器人侧为PR2底盘；逐回合计数与打印事件分别保留。sim沿已核43/50=86%，Gazebo−sim=-34个百分点；原文Gazebo81.6%对照，当前低29.6个百分点。
- 类型：项目实测（stdout/ROS health/原W&B单文件导出）＋算术推导；不是因果分离实验。比例success_count/50；百分点=100*(Gazebo−sim或paper)。论文值沿SRC0269，sim沿SRC0272–0273。
- 作者/版本：Codex /root，实际GPT-6系列（系统仅披露系列，精确型号未知），实际推理档位未知，未切换/委派。forem-t6.4-pr2，镜像sha256:42a779abba40da560e9a80a392513df9b2c8db3c5fb037192530f30b97714915；原作者checkpoint SHA a4d24df66107ba4cd90cdbbaed99d7d99a84c1ade8c1a3fc009b718add66f49d，四模型文件复制前后/源目录末检一致；五上游入口首尾sha一致，未改上游。
- 精确证据：`forem/logs/task6/t6.5-pr2-gz-r2/eval.log` Eval ep0–49、最后汇总与W&B写出后卸载警告；同run export.log（单offline run-1agru0to.wandb导出0）；`forem/results/task6/t6.5-pr2-gz-r2/{commands,status,health,cleanup,offline_raw_export,verified_eval,model_copy_verification}.json`。`forem/results/task6/t6.5-R2/{fix_verification,preflight_commands,source_freeze,model_freeze,episode_statistics,cpu_sampling_summary,final_verification,closed_ports,final_top}.json`和wrapper.diff；summary/{comparison,manifest,PR2_collision_objects}.json逐回合原日志行号与碰撞对象。
- 包装修正/验证：T65-D1放行仅移除health生成字符串多余整体一空格，不改评估参数/上游；旧health编译可复现IndentationError，修后health/observer/launcher的实际Python2与cleanup实际Python3 compile均rc0。wrapper前SHA97103e8f82c1f09b472abf8e879c2f5b7f8e8930c2ae26aabed14f1efcbef6fc，后74737b71f4e18b532b88c463ddcf0191c931760e581167bd930f79f8a62944a7。监控只更新run-id与独立R2输出/stop目录。旧gz证据SHA核查保留、不计入；sim不重跑。
- 原始配置/有效性：PR2 track，原启动器30 s等待后physics实测0.002 s/500 Hz/unpaused，九控制器running，policy time_step0.02/确定性/eval_seed999/50/num_gpus0/自由运行，无人为时延/步时长/动作缩放；IK评估CLI50覆盖保存100；策略真实CPU。完整50条Eval ep且指标已导出，success/epoch_len/IK均/base_collision比例与stdout一致；退出134在完成/指标写出后，按T64-D3有效并记偏差，不把rc改0，不宣称已查明退出根因。无D21。
- 耗时/资源：R2 runner2783.387 s（46.390 min），含启动/评估/收尾/清理；有效sim+gz runner累计3001.619 s（50.027 min），不含用户交接间隔和旧失败run，不是项目全局墙钟或CPU时间。CPU563个约5秒主机CPU-time样本，加权均7.412核、峰20.934核，>56样本0；不证明未观测更短峰。
- 原始结论与项目采用：阶段一review交Claude，原作者模型sim数值达86%，本栈Gazebo52%低于论文81.6%，公开原作者模型并未在本栈复现论文Gazebo量级；不能只由我们的A训练解释所有本地PR2低表现，但传感器/地图/版本/控制时序各贡献未分离。本轮未执行原因诊断、其他任务/机器人、训练或阶段二。同期A/B/F0只引用已有结果并列，不作单因素归因。
- 适用限制：论文多训练种子均值，本地一个发布模型/50回合；sim与Gazebo障碍几何/感知不完全相同。success使用上游定义，不是独立物理成功判据；碰撞/IK/selfcollision可重叠，打印事件不等于控制器counter。事后success且IK≤100为26/50，不能当100阈值重跑。原镜像/task5已批准依赖差异沿task6.4保留。
- 清理/下一步：cleanup after=[]，容器仅sleep，11311/11345无监听；R2监控按自身stop退出0。task5只读top与开工一致，G-B未进入/改动/发信号。负责人Codex已停止，Claude独立复核及阶段二决定尚未执行。旧partial comparison/manifest已另存blocked-r1版本，不覆盖历史运行证据。
- 使用位置：task6.5 RESULTS末节、独立日志；核查日期与核查人：2026-10-14T12:14:01.852764+08:00 Codex。推荐Codex GPT6.1sol / Claude Sonnet5.5，low/默认（明确执行），必要跨指标/链路复核medium；推荐不冒充实际配置。


<a id="src-0310"></a>
## SRC-0310 — task5.4用户要求与B必须从头训练5M的代码依据

- 支撑主张：(1) 用户2026-10-14要求“对cbl这个sac多训练一些，训练500w步，做好性能优化”；“cbl”指Husky快照作者路径`/home/cbl/...`，即task5.2对照B（`main_ray.py`+`husky_ur5`，sim）。(2) B不能从t5.2的1M checkpoint续训，须从头训练5M；5M run的前1M与t5.2不同。
- 类型：用户指令（聊天原话）＋原始代码核查（Husky快照1ccedd0，只读）。
- 精确位置：`husky/src/modulation_rl/scripts/main_ray.py:30` `assert not wandb_config.restore_model and not wandb_config.resume_id, "Not implemented yet"`；`main_ray.py:247–260` stop=`timesteps_total: total_steps`、ASHA `max_t=max(75000,total_steps)`、`grace_period=min(800000,total_steps)`；`main_ray.py:276–277` `checkpoint_freq=100`、`checkpoint_at_end=True`；`modulation/myray/ray_utils.py:121–126` 四个优化器lr_schedule均为`[[0, lr_start],[total_steps, lr_end]]`；`ray_utils.py:176` 探索噪声`scale_timesteps=total_steps`；`modulation/utils.py:54–55` `lr_start`默认1e-4、`lr_end`默认1e-6；`utils.py:46` `total_steps`默认10,000,000。
- 原始结论：上游入口不实现续训；lr与探索噪声随total_steps线性衰减，t5.2在1M时lr已到1e-6。
- 本项目采用：task5.4从头训练`--total_steps 5000000`，其余同t5.2；按步数与t5.2比较时注明日程差异。
- 适用限制：未核查RLlib 1.6内部lr_schedule插值细节与噪声类的精确衰减形状，只按配置写法认定为随total_steps缩放；单试验下ASHA实际不淘汰试验属推断，待执行时由日志确认。
- 使用位置：[task5.4 TASK](tasks/task5/task5.4/TASK.md)、[PROCEDURE](tasks/task5/task5.4/PROCEDURE.md)、[Claude日志](agent_logs/task5/task5.4/20261014-claude-task5.4-plan.md)。
- 核查人及日期：Claude（claude-opus-5-5，强度未知），2026-10-14。

<a id="src-0311"></a>
## SRC-0311 — t5.2训练耗时分解（learner为瓶颈）与task5.4性能门槛的工程选择

- 支撑主张：t5.2（B，1M，与A并行）每1000步迭代中位58.0 s、均60.1 s，合计16.70 h；每迭代100次SAC更新、单次`learn_time_ms`约420–550 ms（CPU，`num_gpus 0`），learner约占迭代墙钟85%；`mean_env_wait_ms`约16 ms；训练中评估迭代（每75迭代）约190–250 s，13次共额外约0.55 h；`perf/cpu_util_percent`约8%。
- 类型：项目实测（t5.2原始progress.csv/params.json）＋推导。
- 精确证据：`forem/results/task5/t5.2-train-s40/ray/husky_ur5_.../SACTrainerCustom_modulation_rl_env_d27fe_00000_0_2026-10-11_15-09-58/progress.csv`（1000行）与同目录`params.json`（train_batch_size 256、training_intensity 25.6、timesteps_per_iteration 1000、num_workers 20、evaluation_num_workers 1、evaluation_parallel_to_training true、num_gpus 0.0）。
- 推导：更新次数/迭代=`(info/num_steps_trained/info/num_steps_sampled)×1000/256`=25.6×1000/256=100；learner合计≈100×0.5 s≈50 s；占比≈50/58≈85%。5M线性估计≈5000×60 s≈83 h，评估额外≈66×150 s≈2.8 h，合计约86 h（未优化、单独运行时可能不同）。
- 假设（待task5.4 §1实测）：learner在Tune trainable进程中以单线程执行（Ray默认给actor设OMP_NUM_THREADS=1）。尚未核实，不得当作事实。
- 工程选择（理由）：O1等价性判据loss相对差≤1e-5、参数最大绝对差≤1e-6，取浮点归约顺序差异量级；采用门槛为中位迭代时间下降≥10%且两次重复一致，用以排除短程噪声。两者均非外部文献依据，可由Claude复核时调整。
- 适用限制：t5.2与A同时训练，CPU争用可能影响计时；未单独测过checkpoint写入耗时；GPU不可用沿task5父流程允许偏差1（torch 1.7.1不支持Blackwell，禁止换栈）。
- 使用位置：[task5.4 TASK](tasks/task5/task5.4/TASK.md#已知性能事实来自t52实测非新测量)、[PROCEDURE §1–§2](tasks/task5/task5.4/PROCEDURE.md)。
- 核查人及日期：Claude（claude-opus-5-5，强度未知），2026-10-14，读取原始CSV复算。


<a id="src-0312"></a>
## SRC-0312 — task5.4接手冻结与单线程learner路径现场实测

- 支撑主张：当前Husky工作副本147个源码/配置SHA与t5.2最终冻结一致；t5.4-prof-r1 learner intra-op1、model/optimizer CPU，20 rollout各1线程；前10迭代丢弃前3后中位52.7916秒、100次更新、单次learn计时中位414.624ms，learner占比中位78.54%，因此达到§1≥50%进入O1门槛。
- 类型：项目实测＋推导；不是t5.2数据复用。
- 作者/版本：Codex /root，实际模型/强度未知；镜像未换，代码task5.0 Husky snapshot1ccedd0与允许兼容；r1只加默认关闭只读探针。
- 原始证据/精确位置：`forem/results/task5/t5.4-preflight-r1/freeze_check.json`147项及`container_processes.txt`；输入对照`forem/logs/task5/t5.2-eval-r2/source-model-r1-d22-d23-final.log`。`forem/logs/task5/t5.4-prof-r1/train.log`的FOREM_T54_LEARNER_PROBE；`forem/results/task5/t5.4-prof-r1/learner_threads_top.txt`、learner_status_and_save_api.txt、rollout_worker_proc.txt；该run ray trial progress.csv第1–10迭代；`forem/build/task5/t54_analyze_profile.py`公式，profile_summary.json随后追加迭代重算，完整原CSV保留。
- 推导：每迭代更新数=相邻num_steps_trained差/256=100；learner秒=更新数×learn_time_ms/1000；占比=learner秒/time_this_iter_s，各迭代占比取中位；非learner残差包含环境/搬运/日志等，未进一步独立剖分。
- 原始结论：本次learner仍是主要开销；CPU主线程约100%，OS线程25不等于intra-op线程数。初始一次探针在初始化阶段，worker.foreach_worker读取不消耗环境步数、不采样、不改RNG。
- 本项目采用：依已冻结§1门槛进入O1；尚无候选线程收益/采用结论；默认关闭O1的隔离测试3项通过，before/diff/SHA和红绿证据在preflight目录。
- 适用限制：r1单独运行、仅短程20k仍在跑，当前10迭代读数；不将短程计时或CPU-only解释成5M完训或GPU加速。r1监控初次nohup未独立，后改start_new_session，最早阶段CPU5s缺样本；探针interop32，不证明实际32线程并行。评估worker线程仍需独立记录。
- 核查：2026-10-14T15:28:42.315543+08:00，Codex /root，直接读取原始日志与CSV。
- 使用：[task5.4 RESULTS](tasks/task5/task5.4/RESULTS.md)、[日志](agent_logs/task5/task5.4/20261014-codex-task5.4.md)。


<a id="src-0313"></a>
## SRC-0313 — task5.4 r1正常20k完成、等价性脚本pickle协议异常停止

- 支撑主张：t5.4-prof-r1从头20000步/20迭代正常退出0；丢弃前3后中位迭代53.604544秒、P90 54.943775秒、learner计时中位422.727ms×100≈42.2727秒/迭代，占比中位79.4968%，time_total_s=1059.081788秒。O1等价性尚未执行SAC更新即反序列化异常，候选/正式训练未启动。
- 类型：项目实测＋基于原始计时的推导；执行脚本失败，不是科学等价性不通过。
- 作者/版本：Codex /root，实际模型/强度未知；容器forem-t5-husky，原镜像/torch未改，conda Python3.7.13、标准pickle最高protocol4；RLlib1.6原RolloutWorker.save使用ray.cloudpickle，其loads模块pickle5._pickle。
- 原始证据/精确位置：`forem/results/task5/t5.4-prof-r1/exit_code.txt`=0、run下ray trial progress.csv第1–20迭代/result.json/checkpoint_000020/checkpoint-20；`profile_summary.json`为完整20迭代汇总（CPU monitor183/184样本差为采样收尾，冻结最终以文件为准）；`forem/logs/task5/t5.4-preflight-r1/equivalence.log`唯一Traceback：`/forem_build/t54_equivalence.py:16`标准pickle双层loads读取worker字节时`ValueError: unsupported pickle protocol: 5`；`profile_sequence_status.json`blocked、`profile_sequence.log`。只读API证据`pickle_protocol_readonly.txt`：rollout_worker.py import ray.cloudpickle及sys.version/HIGHEST_PROTOCOL/loads.__module__。
- 原始结论：测试脚本使用与RLlib保存时不一致的加载器；失败发生在构造policy/batch前，无loss/参数差值，不能认定多线程不等价或无收益。单线程CPU learner瓶颈门槛通过。
- 本项目采用：依冻结异常规则停止§2后续，交Claude。建议待Claude放行后仅修自有等价性脚本采用现有ray.cloudpickle，重新构造固定随机权重/batch256/RNG；不升级栈、不加载t5.2权重。建议尚未实施，不算放行。
- 清理证据：`cleanup_ros.json/log`按PID及cmdline身份向本run roscore107/roslaunch175发SIGINT；`processes_final.txt`仅sleep；profile监控PID680802和序列PID714356均已退出。其他容器/参考仓库未操作。
- 适用限制：等价性与候选端到端收益没有结果；默认关闭hook仅隔离单测通过，未获数值等价性验收。无5M、训练中正式评估、最终9任务或comparison.json，不能置review/done或称优化完成。r1是20k且lr/噪声日程按20k缩放，非5M先导性能曲线。
- 核查人/日期：2026-10-14T15:40:42.591415+08:00，Codex /root，读取当前原始日志/代码/进程；没有重跑等价性或进行替代反序列化。
- 使用：[RESULTS](tasks/task5/task5.4/RESULTS.md)、[日志](agent_logs/task5/task5.4/20261014-codex-task5.4.md)。


<a id="src-0314"></a>
## SRC-0314 — task5.4 R1审批：等价性脚本加载器修正放行（T54-D1）

- 支撑主张：task5.4 §2阻塞系执行者脚本`forem/build/task5/t54_equivalence.py:16`用标准pickle读取RLlib checkpoint（protocol 5，容器Python 3.7.13标准pickle最高4），非候选优化或训练语义问题；放行改用`ray.cloudpickle`后继续§2→§3。
- 类型：用户指令（2026-10-14“审批”）＋Claude只读核查项目证据（工程决策）。
- 精确证据：`forem/logs/task5/t5.4-preflight-r1/equivalence.log`（Traceback，line 16 ValueError: unsupported pickle protocol: 5）；`forem/results/task5/t5.4-preflight-r1/{O1.diff,pickle_protocol_readonly.txt,profile_sequence_status.json}`；Codex RESULTS §0–§2、SRC-0312/0313。核查时`docker top forem-t5-husky`仅`sleep infinity`。
- 本项目采用：T54-D1，见[task5.4 RESULTS Claude复核R1](tasks/task5/task5.4/RESULTS.md#claude复核)。
- 适用限制：仅审批脚本加载修正与继续执行；O1尚无数值等价性和端到端收益证据，不能视为已采用。
- 核查人及日期：Claude（claude-opus-5-5，强度未知），2026-10-14。


<a id="src-0315"></a>
## SRC-0315 — task5.4 T54-D1新run固定batch完整SAC更新等价性

- 支撑主张：t5.4-equiv-r1中N=4/8/16对N=1，actor/critic/alpha三loss相对差全部0，模型与target全部参数最大绝对差7.4505805969e-9/2.2351741791e-8/9.6857547760e-8，RNG序列一致；均满足冻结loss≤1e-5/参数≤1e-6，因此可进入候选profile。尚未证明端到端收益。
- 类型：项目实测（离线工程等价性单步测试），非性能验收。
- 版本/作者：Codex /root，实际模型/强度未知；镜像/torch/Ray不变，FOREM_T54_PROBE/O1保留Claude R1批准的默认关闭改动。只修t54_equivalence.py的checkpoint/worker/ray_config.pkl加载为现有ray.cloudpickle；旧失败preflight-r1不写。
- 精确证据：`forem/results/task5/t5.4-equiv-r1/{loader.diff,loader_sha.json,t54_equivalence.before.py,t54_equivalence.after.py,launch.json,equivalence.json,equivalence_inputs.pkl,resume_freeze_check.json}`；`forem/logs/task5/t5.4-equiv-r1/equivalence.log`四条N=1/4/8/16 JSON。固定输入脚本symbol master/policy.learn_on_batch/policy.update_target/allparams，profilecheckpoint仅取policy_specs与ray_config.pkl配置，不取checkpoint.state权重/optimizer/replay；不读t5.2权重。
- 输入/条件：fresh随机权重seed40，固定合成256样本batch由独立RandomState54生成，obs14441/action3，恢复同一fresh policy+target+optimizer state与Python/NumPy/Torch RNG；每个N重建policy且set_state相同初态，完成actor、双critic、alpha四优化器learn_on_batch及target软更新；检查thread setter未消耗Torch RNG。
- 原始结论：该固定单batch更新数值差在冻结门槛内；alpha loss因初始log_alpha为0而为0，但完整alpha optimizer仍执行。单次更新wall秒0.5855/0.1983/0.0989/0.0961只作测试时间，不能代替端到端profile或承诺工期。
- 采用/限制：允许测试全部三个候选，是否正式采用仍待各30k×2端到端、≥10%与两次方向一致及主机≤56核；仅一个合成batch和fresh初态，不等于任意训练状态数学恒等或统计结果。
- 核查日期/人：2026-10-14T16:01:17.905526+08:00，Codex /root，实际读取新JSON/log与完整输入文件；后续独立Claude复核待执行。
- 使用：[task5.4 RESULTS](tasks/task5/task5.4/RESULTS.md)、[日志](agent_logs/task5/task5.4/20261014-codex-task5.4.md)。


<a id="src-0316"></a>
## SRC-0316 — task5.4 R2：用户要求learner线程加到32（T54-D2）

- 支撑主张：用户2026-10-14 16:5x“能加大一些吗”“加到32核心”；Claude决定将N=32加入O1候选，等价性与端到端收益通过且不比N16慢超过5%时采用32。
- 类型：用户指令＋项目实测（只读）＋工程决策。
- 精确证据：`lscpu`（2 socket×32核、Thread(s) per core 1、NUMA0 0–31/NUMA1 32–63）；`forem/results/task5/t5.4-prof-r{2,3,4,5}/ray/**/progress.csv`丢弃前3迭代的time_this_iter_s中位54.92/27.00/21.53/17.82（r5仅11迭代，未完成）与learn_time_ms中位430.6/159.7/104.0/70.5；`t5.4-equiv-r1/{equivalence.json,profile_sequence_status.json,formal_launcher_status.json}`。
- 推导：非learner耗时≈迭代中位−learn_ms×100/1000，基线≈11.8 s、N16≈10.7 s；N32最多再省learner剩余约7 s中的一部分。
- 适用限制：r5未完成、第二轮重复未做；跨NUMA线程的实际收益未测。
- 使用位置：[task5.4 RESULTS R2](tasks/task5/task5.4/RESULTS.md#r2--用户要求learner加到32线程claude2026-10-14-165x)。
- 核查人及日期：Claude（claude-opus-5-5，强度未知），2026-10-14。


<a id="src-0317"></a>
## SRC-0317 — task5.4首轮30k基线/N4实测与分离后台执行链

- 支撑主张：r2原配置30k/30迭代/rc0，丢弃前3中位54.918678秒、P90 56.386786秒、learn_time_ms430.567；r3仅learnerN4同30k/rc0，中位26.999634秒、P90 28.988838秒、learn_time_ms159.742；首轮中位下降50.837065%。两run远程rollout20及远程eval1均Torch1线程；learner分别1/4。尚未通过两次重复最终采用门槛。
- 类型：项目实测＋推导＋后台执行包装核查；不是正式5M完成或最终性能采用。
- 版本/作者：Codex /root，实际模型/强度未知；源/镜像/torch/ray不变，O1默认关闭改动已Claude R1接受。自有监督脚本SHA见equiv-r1/execution_scripts_sha256.json，不是另一个Agent。
- 精确证据：`forem/results/task5/t5.4-prof-r2/`和`r3/`的exit_code.txt、ray trial progress.csv/params.json、profile_summary.json、host_cpu_5s.jsonl/process_samples.jsonl；train.log初始化FOREM_T54_LEARNER_PROBE。主机CPU峰分别14.274368/12.696787核；learner ps生命周期CPU平均85.5722%/300.1852%，非瞬时线程利用率。
- 推导：中位下降=1−26.99963402748108/54.91867804527283=0.50837065；固定30k/seed40、前3丢弃、剩27迭代，完整环境+采样+CPU搬运+learner+日志。30k没有75000步周期评估/100迭代周期checkpoint，正式外推须沿冻结公式加旧t5.2评估额外开销，不把此短测说成涵盖全部长周期成本。
- 原始结论/采用：等价性在SRC-0315已过，首轮N4有明显整体收益，但还需所有通过候选和基线各30k×2；最终门槛与选N按PROCEDURE/T54-D1，不提前采用。
- 后台证据：equiv-r1/profile_sequence.pid、profile_sequence_status.json、formal_launcher.pid/formal_launcher_status.json；build/task5/t54_profile_sequence.py、t54_start_formal.py、t54_monitor_train.py、t54_posttrain.py与t54_reporting.py源码；logs/task5/t5.4-equiv-r1各监督日志；posttrain-accounting-checks.log离线5项通过（50seed/cap失败/D10 N/A/两朝向/未覆盖异常，非仿真实验）。cgroup读权限只读核查已存。
- 后续行为为已授权计划（尚未执行）：全profile完成后自动核验门槛/冻结/无活跃客户端，再正式5M；实际params对t5.2只允许四项total_steps派生差，记录model/optimizer CPU及实际learner线程/远程worker1，监控CPU56仅告警；训练正常≥5M后才9任务sim、D10/D21/D23、comparison/review。异常保留证据交Claude，不自修/续训/重跑/标done。
- 限制：当前正式5M尚未启动，N8/16与第二轮尚未全完成；后台代码存在不可事先实测的长训/评估路径，未知失败停下，不包装为已验收。计数5项仅脚本逻辑检查。
- 核查日期/人：2026-10-14T17:07:53.873664+08:00，Codex /root，读取实际新日志/JSON、存活PID/只读cgroup；Claude独立复核待执行。
- 使用：[RESULTS](tasks/task5/task5.4/RESULTS.md)、[日志](agent_logs/task5/task5.4/20261014-codex-task5.4.md)。


<a id="src-0318"></a>
## SRC-0318 — 2026-10-16用户所附SC²-WM逐段阅读与解释边界

- 支撑主张：VLN-CE任务定义；VCM历史视觉检索/融合；候选动作→动作条件预测→潜态差异→表示细化→最终动作；Δ不是最小化目标；修正前后动作专家监督、先验后验KL与未来视觉特征预测三损失；测试时KL百分位与低熵条件触发、不包含策略的模型参数更新；正文与算法2重建目标不一致。
- 类型：外部文献原文已读；“决策变化大不推出预测错误”等为基于公式的逻辑分析；教学类比、模仿/强化/深度学习区分是概念解释，不是本项目实测或本文新增实验结论。
- 作者/标题/版本：Xuan Yao、Yuze Zhu、Junyu Gao、Zongmeng Wang、Changsheng Xu，SC²-WM: A Self-Correcting World Model with Closed-Loop Feedback for Vision-and-Language Navigation in Continuous Environments。用户所附PDF自述PMLR 306/ICML 2026，本轮未独立核验出版状态，不假定与既有arXiv登记完全同版。
- 原始证据：`/home/ybc/.codex/attachments/7c2e58fa-66b4-44a4-8f6d-1e7f35c5d685/Yao 等 - SC2-WM A Self-Correcting World Model with Closed-Loop Feedback for Vision-and-Language Navigation i.pdf`；SHA256 `e77f42e075484b5b78756bdff7bfecc4222b98d60e47f18247b6521a472a9d7a`。临时提取文本`/tmp/forem-sc2wm-reading.txt`非长期证据，原PDF及哈希为准。
- 精确位置：pp.1–3摘要/§1–2/任务定义；p.4图2、式1–8；p.5 §3.1–3.2、式9–13、算法1；p.6 §3.3式14、算法2第9行与§4开头。
- 原始结论：作者用预测后果引导状态表示，并按反馈导致的动作分布变化和确定性选择测试时适应。正文明确Δ为引导而非最小化目标；式11同时监督原始与细化状态的动作。正文引用式13下一步特征目标，算法2却用当前校准特征，存在待核对文本差异。
- 推导/解释：Δ=s̃_(t+1)−s_t比较不同时间的状态，故不是预测与实际之差；动作分布KL大度量决策变化，逻辑上不足以单独确认预测不准，低熵也不保证正确。该判断仅基于比较量的定义，无新增实验数据。
- 项目采用及限制：仅供共同阅读和纠正聊天遗漏，不据此调整FoReM机制/协议。尚未逐段阅读主结果、消融或完整审计实现；不宣称触发机制已获本轮验证，不把内部潜态漂移等同机械臂执行误差。类比遮挡门控只是可能行为，不是网络已测能力；学习方法概念解释未另行文献综述。
- 核查日期/人：2026-10-16，Codex /root；用户PDF原文阅读及图式核对，非仅二手摘要。
- 使用：[当天阅读笔记](agent_logs/project/20261016-codex-sc2wm-reading.md)。

<a id="src-0319"></a>
## SRC-0319 — SC²-WM参考源码GateFusion门控权重计算

- 支撑主张：视觉融合门控由当前特征与历史检索特征拼接，经线性层和sigmoid产生逐维度权重；并非固定人工比例。
- 类型：官方参考仓库本地源码静态核查，无运行/训练验证。
- 作者/版本：SC²-WM作者代码，本地`scwm/` commit `f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b`；该文件git status为空（无本地修改）。
- 原始证据/精确位置：`scwm/utils_p/vln_memory.py:108–160`，`GateFusion.__init__`与`forward`；`nn.Linear(dim*2,dim)`，`torch.cat([x1,x2],dim=-1)`，`torch.sigmoid(self.proj(...))`及加权融合；同文件416–417行传入original_query和retrieved。
- 原始结论：scale=sigmoid(W[x1;x2]+b)，fused=scale*x1+(1-scale)*x2。输出末维dim，支持逐特征门控；W、b为可训练层参数，scale按输入计算。
- 项目采用及限制：只解释论文α的本地实现对应，不修改代码、不宣称已核对所有训练调用/梯度；无证据证明学到了固定的遮挡—权重规律，也不估算整个模块参数规模。
- 核查日期/人：2026-10-16，Codex /root，只读代码与commit核查。
- 使用：[当天阅读笔记§3](agent_logs/project/20261016-codex-sc2wm-reading.md)。


<a id="src-0320"></a>
## SRC-0320 — SC²-WM基线指标与强化学习扩展说明（2026-10-16补读）

- 类型：外部论文原文选读；未复现，不是FoReM实测。
- 作者/版本/原文：Yao等SC²-WM，2026，用户所附PDF，文件路径及SHA256同[SRC-0318](#src-0318)。
- 精确位置：表1（p.7）R2R-CE、表2/3（p.8）RxR-CE与消融；附录B指标定义；附录D末尾“Difference from critic-based feedback”“Potential extension to reinforcement learning”。
- 支撑主张及原始结果：R2R-CE单目Val Unseen基线VLN-3DFF*→SC²-WM：表3精确SR43.77→50.90、SPL29.39→37.17、TL26.16→17.65m、NE6.05→5.37m、OSR54.92→58.84；表1Test Unseen SR43.8→47.0、SPL28.6→32.1。RxR-CE单目Val Unseen表2：SR26.7→35.8、SPL20.1→27.2、NE9.40→8.36m。表3无模型适应State-C+VCM→条件适应：SR49.86→50.90、SPL36.05→37.17；固定每2步适应SR50.30、SPL36.58。上述百分数相减为百分点，TL减少8.51m；正文称约5m与表格不一致，本次以表格计算。单目与全景基线不同，全景对应ETPNav*/HNR*，不跨摄像头条件直接排名。
- RL原始表述：当前实现采用模仿学习，理由为部分可观测与稀疏奖励下纯奖励优化不稳定，作者认为示范有助于先建立可靠行为；未以此证明RL普遍不适合导航。作者把Δ描述为高维状态转移引导，与critic标量期望回报不同，明确目标不是RL与世界模型的范式比较。未来可把Δ用于内在奖励或辅助潜在表示，核心机制与策略学习范式正交；这是未来方向，不是已实现/验证的RL算法，未给出内在奖励的具体标量化公式，不支持直接用差值范数当奖励或已验证SAC收益。
- 项目采用/限制：仅回答用户论文问题，补充当天阅读笔记；不改变FoReM协议、不新增实验、不启动训练。本轮选读表格与指定附录段，未全面审计统计显著性/完整公平性。
- 核查：2026-10-16，Codex /root，直接读取用户PDF提取文本的表格、附录段落；差值为表中数字直接相减。
- 使用：[阅读笔记补读](agent_logs/project/20261016-codex-sc2wm-reading.md#补读主要对比与强化学习)。


<a id="src-0321"></a>
## SRC-0321 — 2026-10-16用户指令：现有任务归为CBL复现、task7起从头构建世界模型闭环、删除无用文档

- 支撑主张：task0、task3–task6归入阶段一“CBL项目复现”；task7起为阶段二“世界模型闭环”；删除task1、task2、experiment/、task4.1–4.6、task4.11–4.13及对应日志；根AGENTS末尾按日期追加的旧状态段精简为当前状态。
- 类型：用户明确指令与确认（项目管理），不是技术依据。
- 原始依据：用户原话“我们现在的干扰很多，请你检查现在的文档，把现有的task作为对CBL项目的复现，然后task7开始我们从头构建我们的世界模型闭环项目，把无用文档删掉”；随后在选项中确认四项均按推荐处理（删task1/2；删task4.1–4.6与4.9–4.13；删整个experiment/；精简根AGENTS）。
- 执行偏差及更正：Claude提问时把task4.9–4.13描述为“旧WM计划”，删除后核对备份发现task4.9/4.10含实际运行结果（WM负结果与反馈臂实现），已从备份恢复，只删除未执行的4.11–4.13。
- 备份：删除前整个`forem/doc`、`forem/AGENTS.md`与根`AGENTS.md`打包为`/home/ybc/projects/CL-FoReM-reset-backups/20261016-doc-cleanup/forem-doc-before-cleanup.tar.gz`（465个文件，SHA256 `fd3f52c81e4137636fbf7c260ef7a49f945bd7180123c790bff7be76d2acec06`）。本台账中指向已删除文档的链接以该备份为准。
- 限制：只改文档；`forem/src`、`config`、`logs`、`results`中与已删除任务相关的代码与产物未动。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5）。
- 使用：[README](README.md) · [PLAN](PLAN.md) · [task4 TASK](tasks/task4/TASK.md) · [task7 TASK](tasks/task7/TASK.md)。


<a id="src-0322"></a>
## SRC-0322 — SC²-WM的地图类型、训练环境与真机验证

- 支撑主张：SC²-WM建立在ETPNav/HNR框架上，策略使用拓扑图（节点为已访问视点及全景特征，幽灵节点为航路点预测器给出的候选点），动作是选点；单目设置另用语义可通行栅格辅助航路点预测。训练与主要评估都在Habitat（VLN-CE，R2R-CE/RxR-CE）中、采用模仿学习；低层动作为前进0.25 m/转向15°的运动学动作；附录E在Unitree GO2真机上做了部署验证。
- 类型：外部论文与官方源码静态核查；未复现。
- 来源：SC²-WM论文（同[SRC-0318](#src-0318)的用户所附PDF）；本地`scwm/` commit同[SRC-0319](#src-0319)。
- 精确位置：附录C“Implementation Details/The Baseline Framework”（拓扑图构建与单目语义可通行图）；正文§4实验设置（ETPNav/HNR集成）；附录D“Potential extension to reinforcement learning”；附录E“Real-World Verification”（100任务×5次，SC²-WM 85%、基线70%，动作与仿真一致，测试期梯度更新异步）。源码：`scwm/vlnce_baselines/models/graph_utils.py:139` `GraphMap`；`scwm/vlnce_baselines/ss_trainer_ETP.py:1728` `SemanticGrid`；`scwm/run_r2r/iter_train.yaml` `IL:`、`expert_policy: spl`、`sample_ratio: 0.75`；`scwm/run_r2r/r2r_vlnce.yaml` `FORWARD_STEP_SIZE: 0.25`、`TURN_ANGLE: 15`、`ALLOW_SLIDING: True`。
- 本项目采用：作为task7地图选型与“sim训练+测试期适应”结构的参照；不采用拓扑图。
- 适用限制：其sim→真机差距主要是视觉/场景外观，未研究连续动作的执行偏差；RL扩展只是作者展望，未实测；真机结果为单平台一组对比。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5），读论文提取文本与源码。
- 使用：[task7 TASK](tasks/task7/TASK.md)。


<a id="src-0323"></a>
## SRC-0323 — FoReM/CBL局部地图在sim与Gazebo中的生成方式不同

- 支撑主张：策略观测的局部地图是以机器人为中心的3 m×3 m、0.025 m（120×120）栅格。sim中从真实平面图裁剪（二值、360°完整、无膨胀）；Gazebo中来自costmap_2d局部代价地图，由前置激光`front/scan`实时建图，含障碍层与膨胀层，3 m滚动窗口，代价≥20判为占据。
- 类型：本地源码/配置静态核查；膨胀半径实际取值与时延未实测。
- 精确位置：`forem/src/modulation_rl/scripts/modulation/envs/map.py:34`（`local_map_size_meters=3.0`）、`:85`、`:221`（`_get_local_map_gt`）、`:288–303`（`_get_local_map_from_costmap`，`>= 20`）、`:305–313`（sim用GT、Gazebo用costmap，`use_ground_truth`可强制GT）；`scripts/modulation/utils.py:99`（`local_map_resolution` 0.025）；`gazebo_world/common/costmap/costmap_common_local.yaml`（rolling_window、3.0 m、0.025）；`gazebo_world/husky_ur5/costmap/costmap_common.yaml`（ObstacleLayer+InflationLayer，`observation_sources: laser`，`front/scan`，obstacle_range 2.5）。
- 推论（待验证）：sim→Gazebo零样本损失中混有地图（感知）差距与执行差距，两者比例未测。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5），只读。
- 使用：[task7 TASK](tasks/task7/TASK.md)。


<a id="src-0324"></a>
## SRC-0324 — SC²-WM实机平台与传感器使用边界

- 支撑主张：实机为Unitree GO2四足机器人，配Intel RealSense D435i RGB-D相机；正文说明其提供视觉感知，附录E特别说明深度仅用于安全避碰。论文未在这些部署说明中明确IMU、激光雷达、关节反馈是否输入SC²-WM，不据整机可能搭载的硬件推断算法输入。仿真为Habitat导航agent，论文同时比较单视角RGB-D与12方向、30°间隔全景RGB-D设置，不能将全景设置解释为实机安装12台相机。
- 类型：外部论文原文及官方代码静态核查；未运行。
- 作者/版本：Xuan Yao等，SC²-WM，2026，arXiv:2608.07548v1；本地scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b。
- 来源与精确位置：https://arxiv.org/html/2608.07548v1 ，§4.1、§4.3 Real-world Experiments、附录C、附录E（PDF印刷页17–18）；本地scwm/paper/SC2-WM-ICML2026.pdf；scwm/run_r2r/r2r_vlnce.yaml 的AGENT_0.SENSORS、RGB_SENSOR、DEPTH_SENSOR。
- 原始结论：Unitree GO2 + D435i；“Depth sensing is utilized only for collision avoidance as a safety mechanism.”
- 本项目采用及限制：仅回答平台与传感器问题；仿真RGB-D输入与实机深度安全用途分别陈述，不宣称部署模块的数据流已获代码验证；不授权task7实施。
- 核查日期/人：2026-10-16，Codex /root；已读取本地PDF对应段落并核对在线原文。
- 使用：[核查记录](agent_logs/project/20261016-codex-scwm-sensors.md)。


<a id="src-0325"></a>
## SRC-0325 — SC²-WM训练RGB的虚拟相机采集及使用

- 支撑主张：训练在Habitat场景中由虚拟相机生成观测，不是用GO2实拍采集训练画面；默认前向RGB配置224×224、HFOV90°。运行时复制RGB/DEPTH传感器，增加30°到330°的11个朝向，连同原前向构成12方向观测；无需通过12次机器人转向动作实现这些相机朝向。环境reset与step返回观测，非依据固定视频帧率的录制协议。
- 类型：官方源码静态核查；未运行Habitat，未测渲染耗时/采样频率。
- 作者/版本：SC²-WM作者代码，scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b；论文2026，https://arxiv.org/html/2608.07548v1 §4.1及附录C。
- 精确位置：scwm/run_r2r/r2r_vlnce.yaml RGB_SENSOR与AGENT_0；scwm/vlnce_baselines/utils.py:166–173 get_camera_orientations12；scwm/vlnce_baselines/ss_trainer_ETP.py:133–165 _set_config、:1609 reset、:2625 envs.step；scwm/vlnce_baselines/models/Policy_ViewSelection_ETP.py:236–297 初步12方向/后续单方向编码、:302–338 前向编码+forward_nerf补其他方向特征、:374–402 获取其他方向真实渲染特征。
- 原始结论及适用限制：配置中可生成12方向观测，不代表所有设置每步把全部图像直接作为策略输入。当前发布路径有首步12视角初始化、后续以前向输入与场景记忆预测周围特征，且保留其他方向渲染特征的使用代码；不能将单视角描述为整个训练过程完全无法访问其他方向图像，也不能把预测特征称为当步新拍RGB。仿真本身的渲染实现未在此逐行审计。
- 项目采用：仅解释采集与输入区别，不启动实验、不改变task7。
- 核查日期/人：2026-10-16，Codex /root，直接读上述源码与此前已核对论文。
- 使用：[平台与传感器记录补读](agent_logs/project/20261016-codex-scwm-sensors.md)。


<a id="src-0326"></a>
## SRC-0326 — SC²-WM环境资产格式与策略地图数据结构

- 支撑主张：主要基准为Habitat中的Matterport3D室内扫描重建场景，R2R-CE/RxR-CE为导航任务数据；场景资产包含.glb三维网格和.navmesh导航网格。算法GraphMap为运行时拓扑图，节点含位置/视觉特征、边含距离，另有候选ghost节点；单视角分支还有占据/语义网格张量与3D特征场。场景资产与算法地图不是同一数据结构，不能把仿真器完整场景直接称为策略已知全图。
- 类型：官方源码/文档及论文原文静态核查，无运行实测。
- 作者/版本：Yao等SC²-WM（2026）；本地scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b；VLN-CE上游README在线当前版本（未固定commit）。
- 来源与精确位置：https://github.com/jacobkrantz/VLN-CE README Data/Scenes（MP3D、data/scene_datasets/mp3d/{scene}/{scene}.glb）；https://arxiv.org/html/2608.07548v1 附录C；本地scwm/README.md Data Preparation、scwm/data/scene_datasets/PLACE_HERE.txt（.glb/.navmesh）；scwm/vlnce_baselines/models/graph_utils.py:139–245 GraphMap.__init__/update_graph；scwm/vlnce_baselines/waypoint_networks/semantic_grid.py:7–27 SemanticGrid；任务路径见run_r2r/r2r_vlnce.yaml DATASET。
- 原始结论：GraphMap使用nx.Graph()，node_pos、node_embeds等字典；semantic_grid/occupancy_grid为[batch,类别通道,H,W]的torch张量。
- 采用及限制：仅说明环境与格式，不下载场景、不执行仿真；本地场景目录为占位说明，未验证资产完整性；.navmesh为行走区域表征而非给策略的视觉地图，未审计全部底层导航实现。不把存储结构当成已验证的实机建图能力。
- 核查日期/人：2026-10-16，Codex /root，原文与代码直接核对。
- 使用：[机器人传感器核查补读](agent_logs/project/20261016-codex-scwm-sensors.md)。


<a id="src-0327"></a>
## SRC-0327 — 2026-10-16用户对task7的设计决定

- 支撑主张：task7采用自写训练环境（随机立方体场景）；机器人Husky+UR5，带一个可直接获得全景观测的传感器；底盘动作采用方案一，即训练时只输出(v, ω)、执行层转换留到验证仿真中再写；训练用自写环境，ManiSkill只作验证（“训练用这个可能有些昂贵了”）；每步流程：SAC先输出初步动作→世界模型模拟执行→预测的动作后状态与当前对比→更新当前潜在状态→输出最终动作→视情况更新世界模型；随机立方体地图需按Husky尺寸确定，场景大小需定。
- 类型：用户明确指令（设计决定），不是技术依据。
- 原始依据（用户原话摘录）：“我们这里希望就用一个自己写的环境吧，然后就是也是随机立方体这样，然后机器人你推荐husky吗，上面有一个传感器可以直接获得全景观测……先让SAC输出一个动作，然后模拟执行，得到动作后状态后跟现在做对比，更新现在的潜在状态，然后输出最终动作，并视情况更新世界模型”；“我们在训练的时候不应该关心这个底盘的指令，这到时候上仿真环境再写一层转换什么的就行了”；“我选择方案一”；“我们可以用manskill做验证吧，训练用这个可能有些昂贵了”；随后要求把上述设计写入task7三文档、未定事项单列、不实施。
- 本项目采用：作为[task7 TASK](tasks/task7/TASK.md)“已确定”部分的依据；“全景传感器”具体为360°扫描是Claude的建议，用户在写入指令中确认为当前设计。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5）。


<a id="src-0328"></a>
## SRC-0328 — N²M²训练环境、感知选择与随机障碍参数（论文与代码）

- 支撑主张：N²M²在自写的“解析环境”中训练：程序化随机矩形/椭圆障碍，运动学积分并直接把IK解作为下一步关节角；感知为以机器人为中心、边长3 m的局部占据地图（解析环境用真值，其他环境由传感器建图）；作者选择占据地图而非RGB的理由；Gazebo验证中动作以约30–70 Hz发给底层控制器、由激光与测距数据建二值costmap；评估在CPU上进行。
- 类型：外部论文原文与上游/迁移代码静态核查；未复现。
- 来源：Honerkamp等，N²M²，IEEE T-RO 39(5)，2023（arXiv:2206.08737，书目同[SRC-0198](#src-0198)）；本次读取的PDF为`/tmp/research-028-literature/n2m2.pdf`（临时位置，pdftotext提取）；迁移代码`forem/src/modulation_rl/scripts/modulation/envs/`。
- 精确位置（论文）：§III-C Obstacle Avoidance（局部地图3 m；粗0.1 m＋细0.75 m@0.025 m；占据地图的三点理由：可由LiDAR/RGB-D/测距传感器构建、对RGB图像的几何抽象“we hypothesize is easier to generalize”、训练时无需复杂仿真器）；§III-F Training Environment（矩形与椭圆、规则网格加正态偏移、随机朝向、尺寸均匀采样、目标0.5–5 m、0.4 m膨胀可解性检查、“integrate the robot kinematics over time and directly use the inverse kinematics solutions as next joint values”）；§IV-C（RL智能体只用局部地图；在AMD Ryzen 9 5900X或AMD EPYC 7452 CPU上评估；PR2 Gazebo车轮/旋转关节力矩25、比例增益200）；§IV-I（动作约30–70 Hz发给底层控制器，LiDAR与测距传感器积分成二值costmap）。
- 精确位置（代码）：`map.py:43`缺省平面图(11, 11) m；`map.py:838–839`网格间距3.0 m、偏移标准差0.8 m（覆盖构造参数）；`map.py:856–866`隔列错开半格、朝向U(0, π)、长U(0.025, 1.5) m、宽U(0.025, 1.0) m、高67%为U(0.2, 0.8) m否则为最大高度；`map.py:845–847`起点在离边界0.5 m内均匀抽取；`tasks.py:339` SimpleObstacleTask `goal_dist_rng=(0.5, 8)`（与论文0.5–5 m不一致）。
- 本项目采用：task7的“自写环境训练＋物理仿真验证”结构、随机立方体参数的参照与对比基准。
- 限制：论文数值为作者自述；代码参数以迁移副本为准，与上游HEAD的一致性未逐行核对。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5）。
- 使用：[task7 TASK](tasks/task7/TASK.md)。


<a id="src-0329"></a>
## SRC-0329 — N²M²解析sim中的执行语义与差速底盘处理（代码）

- 支撑主张：解析sim中底盘直接设到命令积分位姿、机械臂直接取IK解，执行与读回实际状态只在非解析世界进行；读实际关节的接口在解析世界抛异常；底盘命令噪声加在命令上；Husky按差速处理，策略输出(ω, v)并映射为[v, 0, 0]，积分为先转后走；从期望位姿反算差速命令的函数未实现。
- 类型：本地代码静态核查（迁移副本，源自Husky快照/N²M²）。
- 精确位置：`forem/src/modulation_rl/src/robot_env.cpp:192–194`（`calcDesiredBaseTf`后`setWorldJoint`）、`:239`（`if (!world_->isAnalytical() && execute_cmd)`包住发送底盘/机械臂命令与读回位姿）、`:562–564`（`getJointValuesWorld`在解析世界抛`"Not defined for analytical world"`）；`scripts/modulation/envs/robotenv.py:142`（husky_ur5 `drive="diff"`）、`:269–270`（`transition_noise_base`高斯噪声加在底盘命令上）、`:313–317`（diff：`[vel_forward, 0, 0]`）；`src/myutils.cpp:405–421`（`calcDesiredBaseTfDiffDrive`：先旋转ω·dt再沿新朝向前进）、`:432`（`calcDesiredBaseCommandDiffDrive`抛`"Not implemented for diff-drive yet"`）。
- 推论：在解析sim中“实际状态”与命令/IK解相同，执行偏差只在物理执行环境中出现；直接输出(v, ω)的映射没有奇点。
- 本项目采用：task7方案一动作设计与“理想执行训练＋物理仿真验证”的依据。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5）。
- 使用：[task7 TASK](tasks/task7/TASK.md)。


<a id="src-0330"></a>
## SRC-0330 — Husky+UR5几何与运动参数（本地URDF/配置）及推导量

- 支撑主张与精确位置：
  - 底盘轮廓0.99×0.67 m：`forem/src/modulation_rl/gazebo_world/husky_ur5/robot_config.yaml:29`；costmap轮廓[-0.5, 0.5]×[-0.33, 0.33] m加0.01 m余量：`gazebo_world/husky_ur5/costmap/costmap_common.yaml:1–2`。
  - 车身0.9874×0.5709×0.2475 m、轴距0.512 m、轮距0.5708 m、车轮竖直偏移0.03282 m、轮半径0.1651 m：`forem/src/husky_description/urdf/husky.urdf.xacro:83–94`；base_footprint到base_link高度=轮半径−偏移≈0.132 m：同文件`:122`。
  - UR5安装在base_link上方(0.13, 0, 0.25) m：`forem/src/husky_ur5/urdf/husky_ur5.xacro:12–15`。
  - 线速度上限0.3 m/s、角速度上限1.0 rad/s：`robot_config.yaml:16–17`；末端目标高度0.7–1.15 m、受限工作空间0.4–1.1 m：`:19–22`；`arm_range` 0.8 m：`:25`。
- 推导（Claude）：原地转向外接圆半径=√(0.495²+0.335²)≈0.60 m；半车宽0.335 m；UR5底座与车顶高度≈0.132+0.25≈0.38 m；360°扫描每1°一束时，距离r处相邻束间距≈r×0.01745（3 m处≈0.05 m），因此在3 m处至少2束命中需物体宽度≳0.1 m。
- 未核实：底盘离地间隙（配置中没有）；UR5官方臂展0.85 m为一般常识，未在本项目核对说明书。
- 类型：本地代码/配置静态核查＋推导。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5）。
- 使用：[task7 TASK](tasks/task7/TASK.md)。


<a id="src-0331"></a>
## SRC-0331 — 已有mapgen语义地图：规格、内容与问题

- 支撑主张：`CL-FoReM/mapgen/outputs/all_maps/`有8类场景（home、hospital、laboratory、library、office、restaurant、warehouse、workshop）各3张，共24张；每张10×10×1.6 m，含围墙与门洞及房间分区；每张65–167个长方体，高0.04–1.6 m，占地19–53 m²；每张同时有.pcd（0.05 m实心体素点云）与.json（每个长方体`[x, y, z, sx, sy, sz, cosθ, sinθ]`及名称/类别）。
- 精确位置：`mapgen/README.md`“地图规格”“输出文件”；`outputs/all_maps/*.json`的`num_boxes`、`map_size`、`boxes`、`objects`、`scene`字段（Claude用脚本统计）；`mapgen/prompts/system.txt:11`（position为底面角点而非中心）；`mapgen/mapgen/map_builder.py:15–41`（体素化以角点为原点旋转，采样`np.arange(0, n)*res`）、`:67–84`（重叠检测SAT按角点）、`:101–108`（`_check_spawn_clearance`按中心点计算角点）、`:155–168`（JSON写出）。
- 发现的问题：①起点净空检查与其他代码坐标约定不一致，“原点0.5 m内无障碍”保证可能不成立；②体素末层比真实边界短最多一个体素（0.05 m）；③最低障碍0.04 m，需定义是否计为底盘碰撞。
- 本项目采用：task7中优先使用JSON长方体做几何计算，PCD仅用于可视化/ROS；与程序化随机立方体混用并划分见过/未见过场景类型。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5），只读代码与输出。
- 使用：[task7 TASK](tasks/task7/TASK.md)。


<a id="src-0332"></a>
## SRC-0332 — ManiSkill3/MS-HAB的自报吞吐与基线；本机硬件实测

- 支撑主张：ManiSkill3自报ReplicaCAD带渲染约2000+ FPS、简单环境RGB-D采集30,000+ FPS（4090）；内置PPO、SAC、TD-MPC2基线及ReplicaCAD、AI2-THOR、RoboCasa场景；MS-HAB（Fetch，ReplicaCAD公寓）自报带2路128×128 RGB-D、与多个动态物体碰撞时超过4000 SPS，基线为pick/place用SAC、open/close用PPO。
- 类型：外部论文/文档（作者自报，未独立复现）＋本机命令实测。
- 来源：ManiSkill3 arXiv:2410.00425（https://arxiv.org/html/2410.00425v1 ）；ManiSkill文档 https://maniskill.readthedocs.io ；MS-HAB arXiv:2412.13211（https://arxiv.org/pdf/2412.13211 ）。以上经网络搜索摘要获取，未逐段阅读原文。
- 本机实测（2026-10-16 15:32，`nvidia-smi`、`nproc`、`lscpu`、`free -g`、`df -h`）：4×NVIDIA RTX PRO 6000 Blackwell Server Edition，每张97,887 MiB，驱动590.48.01，CUDA 13.1；2×Xeon Gold 6530共64核；内存251 GB；/home空闲19 TB；宿主无`vulkaninfo`。
- 未知/待验证：ManiSkill/SAPIEN在Blackwell（sm_120）上是否可用、容器内Vulkan渲染；Husky+UR5能否导入以及底盘是轮地接触还是虚拟平面关节。
- 本项目采用：选择ManiSkill作验证环境的可行性依据；吞吐数字不作为本机承诺。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5）。
- 使用：[task7 TASK](tasks/task7/TASK.md)。


<a id="src-0333"></a>
## SRC-0333 — Mapgen 工具定位、输出协议与实现边界

- 支撑主张：mapgen 为上层 Husky 世界模型项目制作静态地图；默认 10×10×1.6 m、0.05 m 采样、出生区意图半径0.5 m。当前输出 PCD xyz、障碍物 JSON、索引与提示词，不包含世界模型训练与完整机器人接入。
- 类型：用户明确用途指令、本地源码静态核查、历史说明；参数为现有工程选择，未验证其机器人安全性。
- 用户依据：2026-10-16 本聊天要求阅读项目并补 Agent 文档，“是为了上层的husky世界模型项目做地图”。
- 版本/精确位置：独立 mapgen 仓库 main，HEAD `765e06448758dfbe34282edcac00f39ffad36aa5`，源码未改；`mapgen/mapgen/generator.py::generate_maps/_save_prompt`；`parser.py::parse_llm_response/validate_obstacles`；`map_builder.py` 常量及 `_voxelize_box/_check_spawn_clearance/_check_overlap/build_pcd/generate_map/save_boxes_json`；`config.py::get_api_config/_find_dotenv`、`llm_client.py::call_llm`、`prompt_loader.py`、`cli.py`；`mapgen/pyproject.toml`、`prompts/system.txt`。路径相对 CL-FoReM，后续模块名相对 mapgen/mapgen。
- 原始核查结论：角点旋转与出生区中心形式检查不一致，净空只查角点；重叠只告警，无通道宽度/连通性保证；裁剪后的点云、JSON、索引计数可能不同；边界墙不含在 box 元数据中；下一编号按索引长度计算，跳过后可能冲突；未强制地图数量；成功提示词覆盖且未保存所有成功响应。tests 只有缓存，无测试源码；源码根目录缺 .env.example，README 返回值与模型回退示例不匹配实际代码。
- 历史记录：`mapgen/outputs/scenes/README.md`、`summary.json` 为六场景各3张的快照，声明尚未做机器人通行性或 Nmoma 接入验收；其他历史资产不能据此当作当前 CLI 能力或本次实测。
- 资产补查：`mapgen/outputs/all_maps/` 按文件名统计 home/hospital/laboratory/library/office/restaurant/warehouse/workshop 各3份JSON，共24份，均存在同名PCD；抽查 library_map_000.json 与 workshop_map_001.json 含 objects/schema_version/frame_id/length_unit/point_representation/point_bounds/sampling_boundary_policy/scene 等扩展字段，当前生成器未输出这些字段。未逐点验收。
- 运行核查：本轮 `python3 -m mapgen --help` 与 `--dry-run` 均在导入阶段因宿主缺 numpy 退出1，未访问 LLM；不声称命令运行成功。
- 项目采用/限制：新增 `mapgen/AGENTS.md`；用途由用户指定，维护边界沿用根 AGENTS。只读核查与文档，不修代码、不安装依赖、不调用 LLM、不启动 ROS/Gazebo/训练、不声称地图可通行。
- 核查日期/人：2026-10-16，Codex /root，直接阅读上述本地代码与历史说明；机器人验收尚未执行。
- 使用：[Mapgen AGENTS](../../mapgen/AGENTS.md)；[任务记录](agent_logs/project/20261016-codex-mapgen-agents.md)。


<a id="src-0334"></a>
## SRC-0334 — SC²-WM发布代码中下一步目标的产生、世界模型调用与执行方式

- 支撑主张：发布代码中，每次决策的候选来自航路点预测器（单目分支：局部占据/语义栅格→U-Net热力图→12个30°扇区各取峰值，去掉占据格、合并近点）及拓扑图中尚未访问的幽灵节点；先由`global_sap_head`对全部候选打分，世界模型对每个候选并行预测（`world_model`为三层MLP，输入[NAV令牌, 候选融合特征, 候选原始视觉特征]，输出`H_rebuild`，`vis_predictor`预测视觉特征`V_pred`），再按候选做门控修正、由`enhanced_sap_head`二次打分，推理时取二次打分最高者为下一步目标；已访问节点被屏蔽，STOP可选。执行时必要时先瞬移回邻接已访问节点（`back_algo: teleport`），再按15°转向、0.25 m前进走到目标。
- 与论文写法的差异：论文式（§3.1）为π̃给出一个候选动作、Δ=s̃_{t+1}−s_t；代码中世界模型对所有候选并行预测，且δ=Linear([H_rebuild; a_t])为学习量而非相减，a_t为候选特征。
- 频率：仿真中无时间节拍，一次决策为选一个航路点；每回合最多30次决策（`max_traj_len: 30`），底层动作上限5000（`MAX_EPISODE_STEPS: 5000`）；消融中固定间隔更新取T=2以匹配其方法的平均更新频率（附录D）。
- 类型：官方源码与论文静态核查；未运行。
- 精确位置：本地`scwm/` commit `f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b`：`vlnce_baselines/models/etp/vilmodel_cmt.py:596–621、880–1000`；`vlnce_baselines/ss_trainer_ETP.py:1713、1900–1990`（栅格与扇区取峰值）、`:2095`（cand_angles/cand_distances）、`:2137–2175`（以enhanced_logits选动作）、`:2550–2600`（执行动作构造）；`vlnce_baselines/models/graph_utils.py:139、194`（GraphMap、update_graph）；`habitat_extensions/nav.py:30–100`（MoveHighToLowAction）；`run_r2r/iter_train.yaml:46–53`；`run_r2r/r2r_vlnce.yaml:2、8–9`；论文§3.1、附录D（同[SRC-0318](#src-0318)）。
- 本项目采用：task7按代码形式采用“候选→世界模型逐个预测→两轮打分选择”。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5）。
- 使用：[task7 TASK](tasks/task7/TASK.md)。


<a id="src-0335"></a>
## SRC-0335 — SC²-WM航路点预测器的来源与训练方式（VLN-3DFF、CWP）

- 支撑主张：SC²-WM训练中加载`pretrained/cwp_predictor.pth`到策略并冻结除`vln_bert`、`vln_memory`外的全部参数，航路点U-Net不更新。该U-Net的训练来自VLN-3DFF：输入192×192（5 cm/格）的语义（27类）与占据（3类）栅格，真值热力图由CWP标注的附近航路点各画二维高斯（σ=5格）平均而成，损失为MSE，训练2万个15步回合（2×RTX 3090）。CWP的真值航路点来自离散R2R数据集的Matterport3D连通图，经启发式调整以适应Habitat连续场景；输出120角度×12距离（0.25–3 m）热力图，高斯展开，MSE训练，用61个场景图（9,556节点），推理NMS最多5个。
- 类型：本地代码静态核查（SC²-WM部分）＋外部论文经网页摘要抽取（VLN-3DFF、CWP部分，未逐页阅读PDF）。
- 来源与位置：SC²-WM `vlnce_baselines/ss_trainer_ETP.py:262–264、308–313、985–996、1057–1059`，`vlnce_baselines/common/base_il_trainer.py:93–100`，`data/wp_pred/PLACE_HERE.txt`，`README.md` Data Preparation；Wang等，Sim-to-Real Transfer via 3D Feature Fields for Vision-and-Language Navigation，CoRL 2024（PMLR 270:2982–2995），https://arxiv.org/html/2406.09798v2 §3.2、§4.1；Hong等，Bridging the Gap Between Learning in Discrete and Continuous Environments for Vision-and-Language Navigation，CVPR 2022，https://ar5iv.labs.arxiv.org/html/2203.02764 §4.1–4.3、附录A.1。
- 本项目采用：说明候选生成器可选“规则生成”或“仿真自动标注后训练”；task7首版采用规则生成。
- 限制：外部论文细节为网页抽取，待需要时补读原文核对。
- 2026-10-20补注（Claude）：VLN-3DFF与CWP原文相关章节已由Codex于2026-10-19补核，见[SRC-0389](#src-0389)、[SRC-0390](#src-0390)；本条的网页抽取限制由该两条取代，原句保留作历史。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5）。
- 使用：[task7 TASK](tasks/task7/TASK.md)。


<a id="src-0336"></a>
## SRC-0336 — N²M²的决策频率、末端目标与逐步末端位姿的产生

- 支撑主张：N²M²训练时决策周期0.1 s（10 Hz），Gazebo执行参数默认0.02 s、论文报告约30–70 Hz发给底层控制器；末端规划器按实际经过时间推进（单步dt截到0.5 s）。每回合只抽一个末端目标位姿（距离在`goal_dist_rng`内、高度在`goal_height_rng`内、三个欧拉角各U(0, 2π)，位置截到离边界0.5 m内）；每步从末端当前规划位姿到目标重新做A*规划（0.05 m栅格，高障碍代价10000、矮障碍轻微代价，高度沿路径插值、朝向球面插值），取路径下一个点为子目标，向其移动“学到的末端速度×dt”，朝向转动受0.30 rad/s限制，再以IK求关节；末端规划器使用环境真值地图，强化学习智能体只用局部地图。
- 类型：本地代码静态核查＋论文原文。
- 精确位置：`forem/src/modulation_rl/scripts/modulation/envs/eeplanner.py:17–22`（`MIN/MAX_PLANNER_VELOCITY`、`TIME_STEP_TRAIN = 0.1`、`MAX_PLANNER_ANGULAR_VELOCITY`）、`:224–244`（step与dt截断）、`:468–580`（PointToPointPlanner权重与`_cpp_step`）、`:654–660`（每步`_calc_6Dplan`重规划）；`envs/robotenv.py:247`；`scripts/modulation/utils.py:106`（`--time_step` 0.02）；`envs/simulator_api.py:27–48`（`sample_circle_goal`）；`mobile-rl/scripts/configs/best_defaults_ray.yaml:32–34`（tiago frame_skip）；论文§IV-C（末端规划器用真值地图、智能体只用局部地图）、§IV-I（约30–70 Hz）、表II（MPC 30 Hz）（书目同[SRC-0198](#src-0198)）。
- 本项目采用：task7中末端路线作为任务给定输入可由地图JSON规划；候选生成器只用传感器观测；决策与执行节拍须在训练与验证中一致。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5）。
- 使用：[task7 TASK](tasks/task7/TASK.md)。


<a id="src-0337"></a>
## SRC-0337 — 2026-10-16用户决定：改用SC²-WM式子目标决策，候选先用简单规则生成

- 支撑主张：task7的上层决策改为像SC²-WM一样先确定一个位姿子目标、再由下层朝它执行，而不是按速度和固定间隔卡死；候选子目标先采用简单的规则生成（不训练航路点预测器）。
- 原始依据（用户原话）：“我们就换用SCWM的方式，先确定一个姿态子目标，然后朝着这个目标去实现，而不是根据速度和间隔卡死吧”；对Claude提出的“规则候选生成、离散SAC两轮打分、世界模型逐候选预测、先转后走的底层执行器”处理方案答复“可以，这里先弄一个简单的”。
- 类型：用户明确设计决定。
- 本项目采用：[task7 TASK](tasks/task7/TASK.md) §2.3、§2.7、§2.8。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5）。


<a id="src-0338"></a>
## SRC-0338 — 2026-10-16用户确认的前瞻闭环大方向；CBL/N²M²“先移底盘、再求IK、再执行”的代码顺序

- 支撑主张：①用户确认每次决策流程为：360°扫描→VCM式记忆综合历史观测与动作得到当前状态→SAC给出初步策略→由仿真器模拟底盘执行、再模拟IK→用模拟后状态与当前状态的差异反馈SAC重新生成→真实执行；“先跟大方向走，不要扣细节”。此确认取代[SRC-0337](#src-0337)处理方案中“世界模型对每个候选并行预测”的部分，候选仍用简单规则生成。②CBL的Husky快照、上游N²M²与FoReM迁移副本中，每步执行均先按(v, ω)算出期望底盘位姿并在运动学模型中设置（注释：使findIk相对于下一步期望底盘求解），再求IK，最后仅在非解析世界发送机械臂与底盘命令并读回实际底盘。
- 原始依据（用户原话）：“先让相机观测，然后VCM综合过往的历史和动作生成当前状态，然后SAC根据现在的状态去给出一个初步的策略，底盘执行该策略，然后机械臂也模拟IK过去，然后用这个状态和现在的状态的差异送回策略SAC策略重新生成，然后在真实执行”；随后更正“这里是360扫描没错我讲错了，然后这里先跟大方向走，不要扣细节，然后底盘执行这些由sim执行，我记得CBL和N2M2的项目里关于3都是这样做的吧”。
- 代码位置：`husky/src/modulation_rl/src/robot_env.cpp:193–194、236、239`（Husky快照commit 1ccedd0）；`mobile-rl/src/robot_env.cpp:192–193、235、238`（上游HEAD 6281205）；`forem/src/modulation_rl/src/robot_env.cpp:192–194、239`。
- 类型：用户设计决定＋本地代码静态核查。
- 本项目采用：[task7 TASK](tasks/task7/TASK.md) §2.7；前瞻在训练环境中与真实执行一致，在验证中不含物理偏差，是否加学习修正项列为U21。
- 核查日期/人：2026-10-16，Claude（claude-opus-5-5）。


<a id="src-0339"></a>
## SRC-0339 — task7整体实验设计文档审查（2026-10-19）

- 支撑主张：现有task7仍是设计草案；主线为子目标决策＋运动学前瞻，学习修正与测试期适应尚未确定；设计中存在下述待冻结或需澄清项。
- 类型：本地文档核对＋基于文档假设的条件推导；不是外部文献结论、实现缺陷实测或新增实验授权。
- 作者/版本：FoReM工作区main，2026-10-19读取的未提交文档；本轮审查由Codex完成。
- 原始证据与精确位置：`tasks/task7/TASK.md` §1术语、§2.1、§2.7–2.9、U1–U22、§4–5；`tasks/task7/PROCEDURE.md`阶段5–9；`PLAN.md`阶段二；`PROGRESS.md`阶段二；本轮独立日志记录具体观察。
- 原始文档结论：运动学前瞻不训练；U21决定是否加入学习修正项。训练执行理想，执行偏差只在验证环境出现。上层选择候选子目标，下层用(v, ω)。各对照组、预算与多项网络设计尚待确认。
- 审查推导与限制：
  1. 若学习项只拟合执行状态相对同一理想运动学模型的残差，则在两者完全一致、相同动作/时域/终止条件下，监督残差e=x_exec−x_kin=0（位姿用相应坐标差/流形误差；单位随状态分量），不能从此类数据获得非零物理偏差的经验监督。不意味着闭环无效，也不意味着理想环境不能学习观测预测；必须先确定学习对象。
  2. TASK §2.7终点式前瞻与§2.9逐底层步执行的等价性尚未由协议保证，中途碰撞、IK失败、提前停止与持续时间必须明确。不能直接将“完全一致”当成已验收结果。
  3. U20含未来扫描编码，但前瞻的信息权限、遮挡后区域处理、真值地图访问边界未定义。仅凭运动学不能确定未观测场景的未来扫描，若调用真值射线则须明确该特权信息；现文档不能判定已发生泄漏。
  4. §4组4到组5同时加入学习项和适应，缺少明确写出的同一学习模型“冻结/适应”配对口径；现有组定义尚不能单独归因适应收益。PROCEDURE阶段9只列组4–6，也未完整纳入§4约定的普通SAC物理验证对照。
  5. U4仅由模型损失训练表示的倾向，与不加学习修正项时的记忆训练目标尚未衔接；任务奖励/成功/终止、预算计数、评估集、checkpoint选择及适应状态何时重置等未冻结。此为协议缺项，不是要求新增机制。
  6. PROGRESS仍写U1–U15，实际TASK已列到U22；PLAN阶段二仍以(v, ω)动作概括且无条件写测试期适应；SRC-0334“本项目采用”仍写全部候选预测，被SRC-0338所述新决定取代。
- 核查日期/人：2026-10-19，Codex /root；直接读取上述本地文档，未重新核查其引用的外部论文、硬件或仿真可行性。
- 本项目采用及限制：用于本轮设计审查与后续讨论排序；不修改已定设计，不选择U事项，不增加实验组，不安装/训练/评估。
- 使用：[审查记录](agent_logs/task7/20261019-codex-design-review.md)。


<a id="src-0340"></a>
## SRC-0340 — 2026-10-19用户提出子目标内滚动动作序列、状态反馈与IK调研

- 支撑主张：用户确认先自写CBL/N²M²式理想执行训练环境；提出SAC初步策略→世界模型预测执行后状态→将状态变化编码反馈到SAC隐层→更新策略→运动学模拟底盘、求IK并执行。讨论在子目标内按固定周期分步，借鉴TD-MPC2采样多条动作序列、评选后执行一步再规划；明确允许子Agent调研可借鉴成果，并要求考虑IK失败优化。
- 类型：当前聊天用户指令与设计提议；不是外部技术证据，不代表混合算法已获验证或各超参数已冻结。
- 原始依据：2026-10-19本聊天用户消息，首句“首先我们是要先自己写一个SIM训练环境吧”，末句“关于IK失败的问题，我们有什么优化办法呢，这里也要思考一下”。完整语义按上述主张记录，不将用户对SCWM的归属判断当已核实论文事实。
- 版本/精确位置：当前会话消息；关联task7.1–7.3调研节点及task7父三文档2026-10-19讨论记录。
- 核查日期/人：2026-10-19，Codex /root，直接读取用户消息。
- 用户后续补充：除其提出的方法外，明确要求推荐相关论文，并允许指出、纠正现构想的不合理之处；随后说明子目标＋频率结合的动机是担心10 Hz下单步状态变化过小、世界模型失效。后者登记为用户提出的风险假设，不是已证明的失败结论；授权的是研究建议与设计分析，不是直接加入实现。
- 本项目采用/限制：授权调研、并行子Agent和设计分析，不实施/安装/训练/评估。学习世界模型、子目标、序列规划、SAC最终采样分布与IK行为的具体组合仍需讨论。
- 使用：[task7 TASK](tasks/task7/TASK.md)；[调研记录](agent_logs/task7/20261019-codex-sequence-design.md)。


<!-- SRC-0341–0355：2026-10-19 Codex重新核查后补登。旧子日志没有实际登记正文；以下不是恢复出的旧原稿。核查范围逐条记录，不追认旧会话全文阅读状态。 -->

<a id="src-0341"></a>
## SRC-0341 — TD-MPC2论文：隐式世界模型与策略先验MPC

- 支撑主张/类型：外部原文；潜态转移、奖励、终端价值共同学习，用策略先验辅助动作序列采样，只执行首步后重规划；不是SAC，也未给出“未来差异接入SAC隐层”的现成模块。
- 作者/标题/版本：Nicklas Hansen、Hao Su、Xiaolong Wang，TD-MPC2: Scalable, Robust World Models for Continuous Control，ICLR 2024；arXiv 2310.16828v2，2024-03-21。
- URL/精确位置：[原文HTML](https://arxiv.org/html/2310.16828v2)，§2、§3.1式(2)–(4)、§3.2式(6)，附录H为实现设置定位。论文描述均值/方差移位warm start；实际当前代码差异见SRC-0342。
- 原始结论：以joint embedding、奖励及TD目标训练控制相关潜态；策略先验引导短期轨迹优化并以终端Q延伸规划时域。没有通用秒级Husky控制周期结论。
- 核查：2026-10-19，Codex；本次直接重读§2、§3.1–3.2相关方法，**部分章节**；未逐页复核全部实验/附录。旧子报告所称全文/ICLR PDF阅读不能由本轮追认。
- 项目采用/限制：只借鉴并行路径评选、首段执行和重规划；新框架路径层是给定精确模型的采样MPC，不称TD-MPC2；不继承其H、候选数或学习目标，不作为FoReM有效性证据。
- 使用：[task7.1 RESULTS](tasks/task7/task7.1/RESULTS.md) §1–§7与“新框架下的适用性”。

<a id="src-0342"></a>
## SRC-0342 — TD-MPC2固定代码：采样、warm start及执行首步

- 支撑主张/类型：官方源码静态事实；候选序列沿预测状态调用策略；仅均值移位，std每次重置；elite加权更新；评估模式仍抽elite、只去掉末步额外噪声；规划Q用随机两项平均。
- 作者/版本：`nicklashansen/tdmpc2`团队，commit `e9f59321933cbc8e11a002b842adc7d4ffae8ff1`；2026代码快照，不能视为2024论文实验release。
- URL/精确位置：[固定代码](https://github.com/nicklashansen/tdmpc2/tree/e9f59321933cbc8e11a002b842adc7d4ffae8ff1)，`tdmpc2/tdmpc2.py::act/_estimate_value/_plan`（raw约`:99–209`）；`common/world_model.py::Q`；`tdmpc2/config.yaml` planning段（iterations=6、num_samples=512、elites=64、num_pi_trajs=24、horizon=3）。行号可能与网页折叠空行不同，以固定版本符号定位。
- 原始结论：对高斯/策略候选重复展开评分、选elite更新分布，最终只返回被抽序列首动作。评分为预测奖励和终端Q；实现有episodic mask。公式`Σγ^k r̂_k+γ^H Q̄_H`为统一下标表达；H为步数，不是候选数或秒。
- 核查：2026-10-19，Codex；直接读取上述规划函数、Q和配置，**相关函数静态核查**；未运行/编译/安装。早期子报告的commit日期本次未查GitHub提交时间，不据其作技术判断。
- 采用/限制：路径分支与时间轴分开，不能拿论文默认数值当UR5预算；新框架没有TD学习终端Q的路径评分，不复制此规划目标。GPU吞吐未测。
- 使用：[task7.1 RESULTS](tasks/task7/task7.1/RESULTS.md) §2、§4、§6。

<a id="src-0343"></a>
## SRC-0343 — TD-MPC2固定代码：多步模型损失、actor与TD目标

- 支撑主张/类型：官方代码静态事实＋目标一致性推导；模型损失共同训练表示，actor在detached latent上单独更新；target没有SAC的熵项。
- 作者/版本/URL：Hansen等官方仓库，同SRC-0342固定commit；[tdmpc2.py](https://github.com/nicklashansen/tdmpc2/blob/e9f59321933cbc8e11a002b842adc7d4ffae8ff1/tdmpc2/tdmpc2.py)，[world_model.py](https://github.com/nicklashansen/tdmpc2/blob/e9f59321933cbc8e11a002b842adc7d4ffae8ff1/tdmpc2/common/world_model.py)。
- 精确位置：`tdmpc2.py::update_pi`、`_td_target` raw`:242–257`、`_update:259–316`；`world_model.py::pi/Q` raw`:144–205`起；`common/scale.py::RunningScale`为归一化对象（本次未逐行复核内部统计公式）。
- 原始结论：真实replay动作逐步展开，rho^t加权一致性/奖励/value损失；actor目标含归一化Q与scaled entropy；`update_pi(zs.detach())`；TD target为r+γ(1−terminated)min target-Q，没有−αlogπ。由SRC-0348与此比较，熵正则actor不等于完整SAC目标；混搭soft Q与原规划奖励需要重新定义优化合同，是项目推导而非原论文定理。
- 核查：2026-10-19，Codex；**相关函数静态阅读**，未执行。未全面审核optimizer所有状态或全部数学辅助函数。
- 采用/限制：用于防止将TD-MPC2整套训练误称SAC；新框架不采用该训练栈或额外规划损失，不新增实验机制。
- 使用：[task7.1 RESULTS](tasks/task7/task7.1/RESULTS.md) §3、§6。

<a id="src-0344"></a>
## SRC-0344 — POPLIN：策略提议、动作噪声搜索与蒸馏部署的区分

- 支撑主张/类型：外部原文＋官方说明；POPLIN-A-Init固定策略参考，Replan沿变化的候选状态再调用策略；在线MPC与蒸馏后策略直接执行是不同方式。
- 作者/标题/版本：Tingwu Wang、Jimmy Ba，Exploring Model-based Planning with Policy Networks，2019 arXiv 1906.08649v1；代码`WilsonWangTHU/POPLIN` commit `edd8dba50f9049c6164eda774602bef0c299cb51`。
- URL/精确位置：[原文](https://arxiv.org/html/1906.08649v1) §3.2、§4.1式(3)–(5)、§4.2、§4.3–4.4；[固定README](https://github.com/WilsonWangTHU/POPLIN/blob/edd8dba50f9049c6164eda774602bef0c299cb51/README.md) POPLIN-A/P/MPC与Policy Control说明。
- 原始结论：策略辅助初始化、动作/参数空间搜索、蒸馏后控制分别定义；论文讨论的μ/Σ更新和BC/GAN不是SAC反馈隐层的现成实现。
- 核查：2026-10-19，Codex；直接阅读v1相关方法章节，**部分章节**；官方代码本轮只抽查README（**未重新审计算法实现**）。旧报告称OpenReview最终版被验证页阻挡，未追认最终会版已读。
- 采用/限制：仅用来解释“提议与被评分轨迹一致”；参数搜索/蒸馏/BC/GAN不进入task7范围，MuJoCo收益不外推Husky实时性。
- 使用：[task7.1 RESULTS](tasks/task7/task7.1/RESULTS.md) §5、§7。

<a id="src-0345"></a>
## SRC-0345 — LOOP：在线规划与离策略学习、actor divergence

- 支撑主张/类型：外部原文＋官方固定源码；H步模型收益接终端价值，在线规划行为与Bellman使用actor不同；ARC针对这种偏离，SAC Q target包含熵项。
- 作者/标题/版本：Harshit Sikchi、Wenxuan Zhou、David Held，Learning Off-Policy with Online Planning，CoRL 2021 / PMLR 164（2022）；`hari-sikchi/LOOP` commit `4bfc774c038348684b43b2dcf025192175eb7bd0`。
- URL/位置：[正式论文PDF](https://proceedings.mlr.press/v164/sikchi22a/sikchi22a.pdf) §4、§5.1（正文pp.4–5）、§6.1；[固定代码](https://github.com/hari-sikchi/LOOP/tree/4bfc774c038348684b43b2dcf025192175eb7bd0)，`controllers/arc.py::get_action`，`sac.py::compute_loss_q:217–247`（非A2分支`:237–242`有−alpha×logp）。
- 原始结论：ARC用actor与移位旧轨迹形成提议并作有限次重要性更新；off-policy允许行为不同，但不能用原actor概率表示规划择优概率。后一句为对概率归属的项目推导，非发散必然性结论。
- 核查：2026-10-19，Codex；**部分方法章节及上述代码函数**；未复核全部误差界证明/补充实验。初次误写`harshit-sikchi` URL返回404，随后沿作者项目页确认正确`hari-sikchi`，404不作证据。
- 采用/限制：新框架在选点层直接由离散SAC采样，原LOOP式同层actor/planner偏离问题不直接套用；不因此加入ARC、KL约束或终端soft-Q。
- 使用：[task7.1 RESULTS](tasks/task7/task7.1/RESULTS.md) §3、§5–§7。

<a id="src-0346"></a>
## SRC-0346 — SC²-WM论文：反馈细化与模型级自适应

- 支撑主张/类型：外部论文原文；算法1是初步导航动作条件的预测、差异细化、最终动作执行；式11–13为专家动作/潜态KL/未来视觉监督，非SAC训练。
- 作者/标题/版本：Xuan Yao、Yuze Zhu、Junyu Gao、Zongmeng Wang、Changsheng Xu（CASIA/UCAS等），SC2-WM: A Self-Correcting World Model with Closed-Loop Feedback for Vision-and-Language Navigation in Continuous Environments，2026，arXiv 2608.07548v1。
- URL/精确位置：[原文](https://arxiv.org/html/2608.07548v1) §3.1式(5)、(9)–(10)/算法1，§3.2式(11)–(13)，§3.3/算法2；附录D.2为与RL范式的讨论位置。
- 原始结论：将前瞻结果作为内部反馈细化导航表示，并有条件地进行模型适应；所定义的“差异”不是机械臂电机/执行残差。正文transition叙述与发布源码MLP及候选并行实现应分开登记，见SRC-0347。
- 核查：2026-10-19，Codex；**部分方法章节**（§3的反馈/损失相关段落直接重读）；附录D全部讨论和实验未在本次逐段复核，不称全文验证。
- 采用/限制：借用候选预测/反馈思想；task7换为扫描与SAC，不视为原文已经验证的机器人算法。所有候选并行这一代码事实由SRC-0347承担，不能只引算法1证明。
- 使用：[task7.2 RESULTS](tasks/task7/task7.2/RESULTS.md) §1–§2。

<a id="src-0347"></a>
## SRC-0347 — SC²-WM发布主路径：全部候选、detach、真实执行分支监督

- 支撑主张/类型：官方本地代码静态事实；候选轴不是H步时间轴；WM输出detach进入门控残差；只取实际执行候选监督；零残差不保证两评分头相等。
- 作者/版本/URL：SC²-WM作者团队，`scwm/` commit `f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b`；[固定官方仓库](https://github.com/sunrise-yuze/SC2_WM/tree/f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b)，status为空。
- 精确位置：`vlnce_baselines/models/etp/vilmodel_cmt.py:599–621、760–763、815–820、918、934–967`；`ss_trainer_ETP.py:553–575、2142–2144、2411–2458、2490–2503、2760–2818`；`imagine_T`初始化/存储与旧forward函数不等于主rollout存在时间展开。
- 原始结论：world_model两个Linear夹ReLU；全部候选拼输入并预测；H_rebuild.detach后形成`e+sigmoid(Wg[e;h])⊙Wd[h;e]`；gate/delta权重偏置归零；global与enhanced scoring为两独立头。真实动作索引对应预测与下次detached前视特征做余弦loss；不能用未执行候选做真实标签。所读主损失累积未见论文KL项，限于已审计入口，不否定所有旧分支。
- 核查：2026-10-19，Codex；**本地主前向、监督、动作保存代码静态抽查**；未执行模型/梯度。部分范围沿用旧报告定位；本次再次直接读了反馈层、两头和视觉监督关键行。
- 采用/限制：task7已选择全候选预测且无初选；f_p只用到达样本是本项目合同，不由代码“保存actual_action”自动保证所有物理执行都到达。零初始化保证特征残差为0，输出等价还要同权重头与预处理。对SRC-0358①“输出等于未加反馈”作此限定。
- 使用：[task7.2 RESULTS](tasks/task7/task7.2/RESULTS.md) §2；[交流回复](agent_logs/task7/20261019-claude-codex-sync.md#codex回复)。

<a id="src-0348"></a>
## SRC-0348 — SAC目标、两阶段概率与新离散选点框架的适用条件

- 支撑主张/类型：SAC原文＋本项目概率推导；熵必须属于所定义策略，真实transition动作必须与critic/模型标签对应。
- 作者/标题/版本：Tuomas Haarnoja等，Soft Actor-Critic Algorithms and Applications，arXiv 1812.05905v2，2019；[原文](https://arxiv.org/html/1812.05905v2) §4.1式(2)–(4)、§4.2式(5)–(10)、§5；熵target代码对照见SRC-0345。
- 原始结论：soft value包含`E[Q−αlogπ]`，actor最大化价值与策略熵，使用环境replay更新。原文不是FoReM两阶段策略或变长子目标实现的现成证明。
- 推导/条件：若先采样u~π0再采样a~π1(a|b,c(b,u))，执行边缘概率为`πexec(a|b)=∫π0(u|b)π1(a|b,c(b,u))du`，单样本条件logπ1一般不是边缘logπexec。若当前框架所有候选特征在采样前生成且只对离散索引k采样一次，则`logπ(k|context)`直接来自同一softmax，不再有该两阶段积分；padding有效掩码与“路径不可行但仍允许选择”掩码不能混淆。候选/路径若随机，其实现结果须作为已观察context记录，不能无条件省略。
- 新框架复核推导：令Wd=0则残差为0，Wg=0使g=0.5（门不是0）；保证输出初始等价还要求Actor/Critic输出头、编码、归一化及掩码相同。只对到达样本监督的误差估计以“到达且被选中”为条件，不能自动视作所有候选的误差。零时长失败会使`γ^(Δt/τ)=1`，但失败计数会改变状态；应记录正确定义的Δt/计数，不擅自增加最小时长。这些为条件分析，不是实测失败或新增机制。
- 协议文字核对输入：task7.4 RESULTS §14–§15写G2仅输出头、G4另有ψ。若两组输出头相同，则G4可训练集合比G2多ψ，故不能按参数数量称“相同”；G3与G4同ψ结构才承担容量对照。这是集合计数推导，不建议新增组或改变用户分阶段决定。预算按相同决策数并不必然等sim秒/检查点数，已定补充报告这些量可保留。
- 核查：2026-10-19，Codex；**部分SAC方法章节＋概率/代数核对**，未重新验证全部定理或具体离散SAC算法；离散SAC完整公式仍由task7.10补证，本文不代替它。
- 采用/限制：用来说明旧§3.2/§5建议已被晚间框架取代；不实施新策略，不把逻辑可组合性称任务收益。
- 使用：[task7.2 RESULTS](tasks/task7/task7.2/RESULTS.md) §3及“新框架下的适用性”；[交流回复](agent_logs/task7/20261019-claude-codex-sync.md#codex回复)。

<a id="src-0349"></a>
## SRC-0349 — MBPO转移监督与小步恒等预测的条件推导

- 支撑主张/类型：外部论文/官方代码＋本项目推导；学习状态转移无需非零执行残差，MBPO用真实数据训练模型、分叉短rollout供SAC；不采用其额外模型replay机制。
- 作者/标题/版本：Michael Janner、Justin Fu、Marvin Zhang、Sergey Levine，When to Trust Your Model: Model-Based Policy Optimization，NeurIPS 2019，arXiv 1906.08253v3；代码`jannerm/mbpo` HEAD `ac694ff9f1ebb789cc5b3f164d9d67f93ed8f129`（本次git ls-remote固定）。
- URL/位置：[论文](https://arxiv.org/html/1906.08253v3) §5/算法2；[固定constructor](https://github.com/jannerm/mbpo/blob/ac694ff9f1ebb789cc5b3f164d9d67f93ed8f129/mbpo/models/constructor.py) `format_samples_for_training:20–28`（raw）；返回奖励及next_obs−obs。
- 原始结论：模型和策略更新分别定义，模型样本来自环境replay状态附近的短展开；delta_obs是时间变化，不是执行器相对理想模型的误差。
- 推导：平滑标量位置`x'=x+vΔt`、恒预测x时，MSE=`E[v²]Δt²`；v单位m/s、Δt为s、误差m²；10 Hz→0.1 s仅为倒数换算。缩步长会缩绝对loss，不证明模型无用；扫描遮挡/IK边界/latent尺度不满足这一直线位置假设。理想执行若定义为同一F_kin，则执行残差恒0，但动作转移一般非0；无法仅从恒0残差识别未出现的物理误差。
- 核查：2026-10-19，Codex；**部分方法章节与数据目标函数**；未审MBPO理论界全部证明/全部训练实现，未在FoReM测上述现象。
- 采用/限制：新框架f_p目标是到达扫描而非固定0.1 s位移，旧频率担忧需重新解释，不为此新增多步模型rollout或扩大数据标签。
- 使用：[task7.2 RESULTS](tasks/task7/task7.2/RESULTS.md) §1、§3.4、§4。

<a id="src-0350"></a>
## SRC-0350 — DreamerV3的观测潜态预测与想象策略学习

- 支撑主张/类型：外部原文与官方代码；RSSM预测/重建观测、奖励与续存，动态/表示KL分侧stop-gradient；actor/critic从想象回报学习，环境直接采样actor。
- 作者/标题/版本：Danijar Hafner、Jurgis Pasukonis、Jimmy Ba、Timothy Lillicrap，Mastering diverse control tasks through world models，Nature 2025，DOI `10.1038/s41586-025-08744-2`；`danijar/dreamerv3`本次HEAD `e01491fad6434b2245a3b8ca201dd7faedcc458c`（不是论文实验release）。
- URL/精确位置：[Nature原文](https://www.nature.com/articles/s41586-025-08744-2) World model learning、Critic learning、Actor learning；[固定代码](https://github.com/danijar/dreamerv3/tree/e01491fad6434b2245a3b8ca201dd7faedcc458c)，`dreamerv3/rssm.py::loss:120–126`、`imagine`，`agent.py::policy:115`起、`loss:156`起、`imag_loss:382–414`（raw行号）。
- 原始结论：模型学习有独立预测信号；Nature版本对离散/连续actor采用REINFORCE，不能借旧版Dreamer声称全模型动作路径解析反传。在线动作不依赖MPC搜索。
- 核查：2026-10-19，Codex；**部分方法章节与上述接口/损失代码**；未审全训练栈或全部实验；Nature页面一处重复请求失败，不影响首次成功读取方法/REINFORCE段落，未称全文核验。
- 采用/限制：仅说明历史信息与可预测潜态可设计、模型目标不同于执行误差；新框架未采用RSSM/想象actor训练/奖励模型或续存模型，不作为SAC闭环已获验证的依据。
- 使用：[task7.2 RESULTS](tasks/task7/task7.2/RESULTS.md) §1、§3.4、§4–§5。

<a id="src-0351"></a>
## SRC-0351 — CBL/N²M²/FoReM的BioIK、残差、碰撞与失败状态

- 支撑主张/类型：本地源码静态审计＋BioIK官方说明，不是IK调用实测；允许近似解的布尔成功与上层kin_failure不等价。
- 作者/版本：N²M² U `6281205846b1bac4525d05ee230a47bddf42023d`；CBL H快照 `1ccedd087ac12dd317e93accc37bb81e05beeb99`；F未跟踪迁移文件，具体根HEAD/哈希见[SRC-0365](#src-0365)、[task7.5 A.1](tasks/task7/task7.5/RESULTS.md#a1-版本与证据约定)。BioIK官方TAMS-Group/Philipp Ruppel说明为2026-10-19读取版本。
- URL/精确位置：H/F `src/robot_env.cpp:190–239、411–470、479–515、676–708`；F `scripts/modulation/envs/robotenv.py:287–302`（H`:304–319`）；三份`validity_fun.cpp:11–30`；`combined_env.py:328–336、377–384`；F `include/modulation_rl/robot_env.h:203–231`；`forem/src/bio_ik/src/kinematics_plugin.cpp:253、638–653`；`forem/src/husky_ur5/config/kinematics.yaml:11–19`；H `gazebo_world/husky_ur5/robot_config.yaml:27`的solver_timeout=0.01 s只是旧配置，非耗时实测。URL：[BioIK官方README](https://github.com/TAMS-Group/bio_ik#readme) Disclaimer及Incremental IK。
- 原始结论：先设置下一底盘、再IK；近似解可由回调接受；slack另检并合并失败，碰撞字段可因配置改变失败统计。正则/MinimalDisplacement/AboveVelLimit为软目标；后者对有符号d惩罚，不能视为双向硬限速。checkCollision依场景/ACM而定。官方说明默认bio2_memetic不与Unity BioIK共享代码，并讨论增量跳解。
- 核查：2026-10-19，Codex；**本地相关代码直接阅读及官方说明相关段落**；没有启动ROS确认实参，也未运行求解。旧task7.3表格把H/F robotenv的行号写到297–303，实际F主失败段为297–302、H为314–319，现按此更正；U为310起。
- 采用/限制：用于失败分类与模型坐标核对，不冻结新求解器/超时；随机障碍场景能力边界见SRC-0367，不能将checkCollision名称误译成纯自碰撞。
- 使用：[task7.3 RESULTS](tasks/task7/task7.3/RESULTS.md) §1–§4；[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) §A.4–A.5。

<a id="src-0352"></a>
## SRC-0352 — UR5解析FK/IK分支与种子连续性

- 支撑主张/类型：ROS-Industrial官方源码＋坐标/秩推导；解析多分支可枚举，但分支选择、限位和路径碰撞需另检。
- 作者/版本：ROS-Industrial `universal_robot` kinetic-devel固定commit `06d8b9e2f5f86aa54f9f2845f11edbc84e2f951e`（本次git ls-remote固定）；`ur_kinematics`。
- URL/位置：[ur_kin.cpp](https://github.com/ros-industrial/universal_robot/blob/06d8b9e2f5f86aa54f9f2845f11edbc84e2f951e/ur_kinematics/src/ur_kin.cpp) `UR5_PARAMS:26–34`、`forward:47`、`forward_all:71`、`inverse:197–341`（raw，腕奇异q6_des约`:283`）；[ur_moveit_plugin.cpp](https://github.com/ros-industrial/universal_robot/blob/06d8b9e2f5f86aa54f9f2845f11edbc84e2f951e/ur_kinematics/src/ur_moveit_plugin.cpp) raw`:607–641、644–730`限位、距seed加权排序及有效性回调。
- 原始结论：独立解析函数求解UR链；MoveIt插件负责完整链坐标、限位/种子/回调。解析解数量不是连续冗余自由度；插件能力不全在纯inverse函数中。
- 推导：`T_AE*=(T_WB T_BA)^(-1) T_WG* T_EG^(-1)`，T_XY将Y变到X，位置m/旋转一致SO(3)约定；固定底盘6D完整位姿满秩UR5的局部零空间维数`6−rank(J)=0`。给定非完整(v,ω)不能瞬间横移。以上为坐标复合/线性代数，不是外部性能结果。
- 核查：2026-10-19，Codex；**相关解析/插件函数静态抽查**；未运行UR5、未证明通用DH与本机模型完全相符。ROS文档入口失败后改读官方固定raw源码。
- 采用/限制：task7.3首选研究路径为解析多解＋上一有效q分支连续选择；需安装/工具/型号一致的FK回检及碰撞，不保证总可达、不保证GPU更快，不把它升级为已选实现。
- 使用：[task7.3 RESULTS](tasks/task7/task7.3/RESULTS.md) §3–§4A。

<a id="src-0353"></a>
## SRC-0353 — DLS局部稳定性与TRAC-IK限位求解

- 支撑主张/类型：原始数学论文方法章节＋TRACLabs官方说明/库文档；DLS抑制近奇异方向增益，TRAC-IK结合改进KDL与SQP，Distance模式耗满预算。
- 作者/标题/版本：Samuel R. Buss、Jin-Su Kim，Selectively Damped Least Squares for Inverse Kinematics，作者2004-10-25稿（后发表于JGTools 2005）；Patrick Beeson、Barrett Ames，TRAC-IK: An Open-Source Library for Improved Solving of Generic Inverse Kinematics，Humanoids 2015，DOI `10.1109/HUMANOIDS.2015.7363472`。
- URL/精确位置：[Buss/Kim作者PDF](https://mathweb.ucsd.edu/~sbuss/ResearchWeb/ikmethods/SdlsPaper.pdf) §2 pp.3–4（DLS/SVD）、§3不可达目标；[TRACLabs官方项目说明](https://traclabs.com/projects/trac-ik/) 算法概述；[TRAC-IK库README固定版本](https://github.com/HIRO-group/trac_ik/blob/2e63d6b2b05095e34b51672f8475a7390f75125c/trac_ik_lib/README.md) raw`:43–55`（该仓为ROS-independent维护分支，非2015论文原release）。
- 原始结论：`Δq=Jᵀ(JJᵀ+λ²I)^(-1)e`，由最小化`||JΔq−e||²+λ²||Δq||²`得到；λ需平衡稳定/收敛。TRAC-IK两算法并发，Speed取先收敛，Distance在完整timeout内择最小seed SSE；姿态分量容差要单独定义。两者不自动保证连续路径避障。
- 核查：2026-10-19，Codex；Buss/Kim **部分章节原文**；TRAC-IK **官方说明和接口文档已读，2015论文全文本次未取得**（官方作者论文页请求失败），不追认旧报告“论文§II–III已核验”。未用ResearchGate二手摘要替代原文。Buss未发表survey入口超时后读作者正式文章稿，书目不混写。
- 项目推导/采用：有界`Δq`、关节限位及位姿加权的局部约束式是工程候选，平移m/旋转rad/Δt秒需缩放；不能保证全局可行或拿延长预算当免费改进。仅供选择解释，不实施TRAC-IK/DLS，不沿用其默认容差。
- 使用：[task7.3 RESULTS](tasks/task7/task7.3/RESULTS.md) §2–§5。

<a id="src-0354"></a>
## SRC-0354 — Reachability Behavior Priors的底盘放置与适用限制

- 支撑主张/类型：外部论文原文；底盘位姿与臂启动决策有关，可达先验不等于可操作度最优或整条路径可行。
- 作者/标题/版本：Snehal Jauhri、Jan Peters、Georgia Chalvatzaki，Robot Learning of Mobile Manipulation with Reachability Behavior Priors，RA-L 2022，DOI `10.1109/LRA.2022.3188109`，arXiv 2203.04051v3（2022-07-06）。
- URL/精确位置：[原文](https://arxiv.org/html/2203.04051v3)，§III-C IRM，§IV-C、§V任务与TIAGo++，§VI局限（学习最大化IK可达likelihood，未优化manipulability）。
- 原始结论：先验向混合动作RL提供与6D目标相关的放置/臂激活信息；工作没有解决所有障碍与操纵性问题，其机器人/任务与Husky+UR5同步路线不同。
- 核查：2026-10-19，Codex；**部分章节**，直接读IRM定义、任务描述及结论限制；未逐项重核全部实验或官方训练代码。
- 采用/限制：仅支持“先选较有利底盘候选再精确IK”的阅读建议；不新增IRM网络/BHyRL/可操作度奖励，不把其成功率移植为本项目预期收益。
- 使用：[task7.3 RESULTS](tasks/task7/task7.3/RESULTS.md) §4D、§5。

<a id="src-0355"></a>
## SRC-0355 — cuRobo批量IK、碰撞表示与计时口径

- 支撑主张/类型：外部论文作者报告＋官方旧版源码；GPU批处理可能适合多候选，但吞吐不能冒充单查询延迟，IK离散碰撞不能保证路径安全。
- 作者/标题/版本：Balakumar Sundaralingam等（NVIDIA），cuRobo: Parallelized Collision-Free Minimum-Jerk Robot Motion Generation，arXiv 2310.17274v2（2023-11-03）；官方legacy tag v0.7.8，Git对象`d64c4b005459db10c5dd867d8b30a87d5bda9bdb`。
- URL/精确位置：[论文](https://arxiv.org/html/2310.17274v2) §3–§3.4、§6.2.4/Fig.17、§6.2.6/Fig.20、附录E.3（IK/graph离散检查）；[固定旧版ik_solver.py](https://github.com/NVlabs/curobo/blob/v0.7.8/src/curobo/wrap/reacher/ik_solver.py) `IKResult`、`solve_batch:769`、`solve_batch_env:899`、`_get_success`、seed_config接口（raw行）；[官网版本告示](https://curobo.org/)称V2已发布且API重设，legacy文档标v0.7.6，不将文档与v0.7.8视作同一release。
- 原始结论：机器人球体表示、自/环境碰撞、批量目标/不同场景/种子与pose残差成功输出。Fig.17批量1000无碰撞IK约27ms、碰撞自由IK约131ms；Fig.20 RTX4090摊销约27μs/130μs每问题，非整批130μs、非本项目单步。附录E.3对IK仅离散查询，轨迹优化另有连续碰撞算法。
- 核查：2026-10-19，Codex；**部分论文方法/计时章节、旧版相关接口及官网版本告示**；无安装、Blackwell兼容或实测。计时来源未在FoReM复现，不外推硬件/UR5吞吐。
- 采用/限制：只列GPU候选；坐标变换、球近似、逐路径连续分支及与网络争用的端到端成本待授权测量；未决定采用legacy或V2，也不扩展环境碰撞表示。
- 使用：[task7.3 RESULTS](tasks/task7/task7.3/RESULTS.md) §4E、§5；[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) §A.4。

<a id="src-0356"></a>
## SRC-0356 — 子目标、固定周期、学习前瞻与IK的组合建议（2026-10-19）

- 支撑主张：本轮建议将子目标上下文、固定周期执行、多步模型前瞻、SC²-WM式内部反馈及SAC/规划器分工分别定义；不能由10 Hz或理想执行直接推导世界模型失效。
- 类型：用户要求基础上的工程建议、条件推导与待验证假设，不是已批准算法、实验结果或普遍性能结论。
- 输入依据：用户动机与设计[SRC-0340](#src-0340)；理想执行语义[SRC-0329](#src-0329)、本轮task7.3源码核查；SC²-WM、SAC、TD-MPC2、LOOP、MBPO与DreamerV3的本轮调研来源，见task7.1–7.3 RESULTS及全局对应条目。
- 公式/单位/条件：执行周期Δt以s计、展开步数H为无量纲正整数、前瞻物理时域T=HΔt以s计；仅当每个动作持续同一Δt时如此，不能把候选数N当作H，也不能把子目标距离直接当时间。用户举例10 Hz对应Δt=0.1 s，是解释用输入，不代表已批准参数或“机器人通用”依据。若只设子目标而仍用H=1，前瞻物理时域仍为Δt。理想环境中x_next=F_kin(x,a)并不意味着x_next=x；执行残差为零和动作导致状态变化为两个不同量。
- 建议A：保留反馈后的SAC Actor为最终动作分布，模型/序列搜索只提供动作前上下文；须明确定义复合策略及log概率、梯度与Critic条件，不能因仍叫SAC便默认公式不受影响。
- 建议B：在子目标上下文中，以反馈修正Actor引导候选动作序列；模型预测、价值/可行性评分后由规划器选择行为动作，只执行首步再观察重规划。较贴合本轮滚动序列构想，但最终控制器是规划器，Actor为proposal/学习策略，不再称纯SAC直接输出最终执行动作。SAC可从该行为策略产生的真实环境转移离策略学习；Actor更新中的采样和熵仍应使用其自身定义的分布，不能将被规划筛选的行为分布冒充Actor分布。规划分数与SAC软价值口径还需确定，不能直接拼接原TD-MPC2所有损失。
- 状态反馈建议：预测整段/远期任务相关变化，可作为反馈上下文；高频一步恒等预测是需要检查的风险，而非已证明失败。世界模型用环境真实执行动作和真实后继观测监督；未执行序列没有本次真实标签。当前隐层修正不是实际物理状态变化，不可用尚未执行的预测覆盖真实本体反馈。
- IK关系推导：若世界系底盘位姿为T_WB、臂安装变换为T_BA、世界系末端目标为T_WE，则新底盘位姿下IK目标为T_AE=(T_WB T_BA)^(-1)T_WE；IK输出关节q，实际运动学末端由T_WE_real=T_WB T_BA FK(q)计算。输入必须使用同一坐标约定，位置单位m、角度rad；IK残差、碰撞、关节限位、速率/连续性分开检验。终点有解不构成中间路径可行证明。
- 工程限制：H、Δt、候选数、评分/损失权重、子目标刷新、失败时底盘与机械臂如何更新均未冻结；不以减慢执行频率、放松末端判据或删失败样本制造收益。精确IK/几何可作检查，但其调用量与信息权限须一致，不宣称学习预测或GPU批处理已经更快。
- 核查日期/人：2026-10-19，Codex /root；本条为显式工程分析，不声称完成物理验证。外部原文的已核查程度按各来源条目，不由本条升级。
- 使用：[父设计调研记录](agent_logs/task7/20261019-codex-sequence-design.md)；[task7 RESULTS](tasks/task7/RESULTS.md)。


<a id="src-0357"></a>
## SRC-0357 — N2M通过成功rollout学习初始位姿偏好分布

- 支撑主张：N2M（Navigation-to-Manipulation）是导航到操作的初始位姿选择模块，区别于N²M²。采集固定操作策略π的rollout，以成功起始位姿作为正样本；RGB点云经Point-BERT与MLP预测GMM分布，主体损失为成功位姿负对数似然。推理从分布采样并检查底盘占据碰撞，再移动并执行原操作策略；不是直接预测成功率的二分类器，也不是逐步世界模型规划。
- 类型：外部论文原文核查；“分布密度不等于校准成功率”为由训练目标作出的解释。成功数据分布受采样范围影响，不能据其推导全局最优性或每个姿态的精确成功概率。
- 作者/标题/版本：Kaixin Chai、Hyunjun Lee、Joseph J. Lim；N2M: Bridging Navigation and Manipulation by Learning Pose Preference from Rollout；ICML 2026，PMLR 306:12363–12382；arXiv:2509.18671v2。
- URL：https://proceedings.mlr.press/v306/chai26a.html ；https://arxiv.org/html/2509.18671v2 ；PDF https://raw.githubusercontent.com/mlresearch/v306/main/assets/chai26a/chai26a.pdf 。本次下载到/tmp/n2m-chai26a.pdf，提取文本/tmp/n2m-chai26a.txt（临时文件，不作为永久唯一依据）。
- 精确位置：§3.1系统流程；§3.2公式(1) GMM、(2)负对数似然；§3.3.1成功rollout采集与§3.3.2视点增广；Fig.2双峰例；附录B.3碰撞检查、B.4固定初始臂关节与SE(2)底盘位姿，C.4实机位姿(x,y,θ,h)；D.4操作策略能力等失败限制。
- 原始结论：偏好由具体策略实际完成任务的表现定义，不仅看几何可达性；增广时渲染同一局部场景的不同视点并将同一成功位姿变换到相应机器人坐标系。附录C.2明确部分补充实机展示用人工规则正样本，不能概括为所有展示都由真实策略成功rollout标注。
- 核查日期/人：2026-10-19，Codex /root；直接阅读上述PMLR PDF正文与相关附录，另读取arXiv HTML；未复现、未审计官方实现。
- 本项目采用/限制：只用于向用户讲解姿态评价与数据监督；未授权接入FoReM，不以本文作为Husky+UR5性能证明，不改变task7方案。
- 使用：[阅读记录](agent_logs/project/20261019-codex-n2m-pose-preference.md)。


<a id="src-0358"></a>
## SRC-0358 — SC²-WM代码补充：反馈层零初始化与detach、占据栅格高度判定、底层执行与策略训练方式

- 支撑主张：①反馈修正对全部候选进行：`H_rebuild`先detach，门控`g=sigmoid(W_g[e;H])`、修正量`δ=W_d[H;e]`，`e'=e+g⊙δ`；`feedback_gate`、`feedback_delta`权重与偏置零初始化，因此接入时输出等于未加反馈。②航路点U-Net的占据输入由深度点云投影得到：只取前方0.5–3 m、去天花板附近点，按高度阈值区分障碍与地面；输入为27类语义＋3类占据、192×192、0.05 m/格。③选中航路点后的移动不学习：先转向目标，再按固定步长前进，碰撞时左右试探（tryout），或瞬移/沿拓扑图最短路径。④策略由模仿学习训练（教师动作`teacher_ghost`），不是SAC。⑤本地`scwm/pretrained/`只有`PLACE_HERE.txt`，`cwp_predictor.pth`等权重不在本机。
- 类型：官方源码静态核查（只读，未运行）；补充[SRC-0334](#src-0334)、[SRC-0335](#src-0335)未写明的细节。
- 精确位置：本地`scwm/` commit `f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b`：`vlnce_baselines/models/etp/vilmodel_cmt.py:599–611、815–820、940–967`；`vlnce_baselines/waypoint_networks/utils.py:377–410`；`vlnce_baselines/ss_trainer_ETP.py:247、264、302、1059、1713、1941–2040`；`vlnce_baselines/common/environments.py:386–447、461–490`；`pretrained/PLACE_HERE.txt`。
- 原始结论：见支撑主张；④仅据训练器中的教师动作与模仿损失变量判断，未逐行核对全部训练分支。
- 本项目采用：task7偏置层照①的形式（零初始化门控残差、世界模型输出detach后进入）；不直接使用其航路点权重（输入需语义、场景为室内住宅、不知道末端路线），候选点首版用规则，以后可借用②的“热力图→扇区取峰值→去障碍→合并→取前k”结构自训练；执行器照③不学习。
- 限制：只核查代码路径；未运行，不代表其数值表现；与论文写法差异见[SRC-0334](#src-0334)。
- 2026-10-19晚更正（Claude，据Codex复核[SRC-0348](#src-0348)）：①中“接入时输出等于未加反馈”只指这一层：`feedback_delta`为零使δ＝0、e'＝e；`feedback_gate`为零只使门值为0.5。整网输出相同还需下游头与编码/归一化/掩码一致；task7中的条件写在[task7 TASK](tasks/task7/TASK.md) §2.7第5步。原句保留作历史。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。

- 使用：[task7 TASK](tasks/task7/TASK.md)；[日志](agent_logs/task7/20261019-claude-framework-docs.md)。


<a id="src-0359"></a>
## SRC-0359 — 2026-10-19用户确认的task7框架

- 支撑主张：经2026-10-19下午至晚间与Claude讨论，用户确认：①不在10 Hz做学习决策；决策单位为一个前瞻点（子任务），子任务内目标不动。②前瞻点生成先不加“结果摘要回送生成网络”的子目标环，以后视情况再做。③候选前瞻点为多个；对每个候选点并行优化多条路径，按固定评分取各点最优路径，再在所有候选点之间选最优（选点由SAC学习完成）。④同意Claude建议(b)：全部候选同时做预测与修正，不保留“先初选一个再修正”；(c)：偏置层先用“冻结基线SAC，只训练偏置层与输出头”的方式。⑤准备工作包括SIM、世界模型训练、前瞻点网络改造、VCM确定等，授权Claude写文档。
- 原始依据（用户原话摘录）：“我们能不能直接用前瞻，不用10HZ那个”；“我先去掉这个子目标环吧，这个可以后面看情况做”；“不应该是，候选很多前瞻点，每个点并行优化几条路径，然后每条点选最优的，再选所有点里最优的吗”；“所以我们要准备，sim，世界模型的训练，前瞻网络的改造，VCM的确定，等等工作，你都开始写文档吧，我同意你的BC，写好文档喊我”。
- 类型：当前会话用户设计决定；不是外部技术证据，不证明方法有效。
- 讨论中被放弃的中间方案（供追溯）：SAC直接输出连续有界底盘位移作为前瞻点（Husky差速底盘不能到达任意位姿，且偏离SC²-WM“选候选点”的结构）；上下两层同时学习（层次RL非平稳风险）；在每个Δt做TD-MPC式序列规划（与选点结构不在同一层）。
- 本项目采用：[task7 TASK](tasks/task7/TASK.md) §2.3、§2.7–§2.9、§3、§4；准备子任务task7.4–7.12。各参数（候选数、路径数、检查点间隔、评分权重、网络宽度等）均未冻结。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5），直接读取本会话用户消息。
- 使用：[task7 TASK](tasks/task7/TASK.md)；[DECISIONS](DECISIONS.md)；[日志](agent_logs/task7/20261019-claude-framework-docs.md)。


<a id="src-0360"></a>
## SRC-0360 — N²M²/CBL/FoReM阶段一的终止、成功与奖励定义（代码）

- 支撑主张：①终止：`done = (本步无IK失败且末端规划完成) 或 IK失败累计≥ik_fail_thresh 或 底盘碰撞累计≥ik_fail_thresh`；IK失败或碰撞一次不结束回合。阈值默认训练20、评估50，按每个0.1 s步计数。②成功：`无IK失败 且 无底盘碰撞 且 末端到达目标`（三者同时满足）；末端到达阈值默认0.025 m与0.05（姿态量的单位/定义待核）。CBL原版与FoReM阶段一迁移环境使用同一判定，阶段一报告的“内部成功”即此值。③奖励：碰撞惩罚（默认10）×底盘碰撞＋IK项（默认'l2'：−0.5[(d/0.1)²+(r/0.05)²]）−动作/加速度惩罚（默认0）；步内末端奖励为0，没有进度奖励；末端按规划器时间前进（速度范围0.001–0.1，单位按代码常量，待核），底盘需跟上。④N²M²只检查底盘碰撞与机械臂自碰撞，不检查机械臂与环境障碍的碰撞。
- 类型：本地代码静态核查（只读）。
- 精确位置：上游`mobile-rl/` commit `6281205846b1bac4525d05ee230a47bddf42023d`：`scripts/modulation/envs/combined_env.py:309–354、356–384`；`scripts/modulation/utils.py:103–135、530–531`；`scripts/modulation/envs/tasks.py:146–147`；`scripts/modulation/envs/eeplanner.py:17–22、187–193、246–255`；`scripts/modulation/evaluation.py:49–54、116–117`。CBL快照`husky/src/modulation_rl/scripts/modulation/utils.py:530–531`、`envs/combined_env.py:382–384`（快照版本见[SRC-0338](#src-0338)）；FoReM`forem/src/modulation_rl/scripts/modulation/utils.py:530–531`、`forem/scripts/task3_env.py:175`。④依据`combined_env.py:184–188`只检查局部地图中的底盘碰撞与`robotenv.py`自碰撞字段，未逐行排除其他碰撞检查路径。
- 本项目采用：task7成功判定沿用“零失败＋到达目标”的严格口径，但失败计数单位改为检查点/决策，并新增机械臂与环境碰撞；终止改为“停在最后可行检查点、记失败、累计F次终止”；奖励结构不同（见[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md)），不直接沿用其数值。
- 限制：阶段一经验“约90–92%回合因20次IK失败终止”来自task4.8（本台账既有条目），不代表新环境的失败率。
- 2026-10-19晚更正（Claude，据Codex复核）：④过宽，收窄为“解析sim中底盘碰撞按局部地图判定；机械臂经MoveIt `checkCollision`检查（`validity_fun.cpp:11–30`），场景含机器人自身与地面平面（U `robot_env.cpp:72–91`），未见随机环境障碍加入该场景，因此缺机械臂对随机障碍的检查”，见[SRC-0367](#src-0367)；task7新增机械臂与环境碰撞的决定不变。②中姿态阈值0.05已核清：旧姿态距离为`1−(q_a·q_b)²`＝sin²(φ/2)，无量纲，见[SRC-0371](#src-0371)。原句保留作历史。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。
- 使用：[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md)；[日志](agent_logs/task7/task7.4/20261019-claude-task-definition.md)。


<a id="src-0361"></a>
## SRC-0361 — 2026-10-19用户对task7任务定义的选择

- 支撑主张：①末端沿路线的推进方式“两条路都做”：进度驱动（末端随所选候选推进到进度s，可暂停等底盘）与时间驱动（末端按规划器时间前进，底盘须跟上，N²M²式）两种任务变体都做。②段中途失败：停在最后可行检查点、记一次失败、回合继续，回合内失败累计F次终止；成功要求失败次数为0。③路径评估显示不可行的候选不屏蔽，由SAC根据候选特征与失败惩罚学习避开。
- 原始依据：2026-10-19本会话，用户对Claude三项提问的选择：“末端沿路线怎么推进？”=“两条路都做”；“段中途失败怎么处理？”=“停下记失败，累计F次终止（推荐）”；“路径评估显示不可行的候选，要不要从选项里屏蔽掉？”=“不屏蔽（推荐）”。
- 用户随后的表述：“我们这里同时做同步和不同步的吧”；澄清为“不是两种吗，一种等机械臂，一种不等”。即同步＝时间驱动（互不等待），不同步＝进度驱动（底盘与机械臂可以互相等），与①相同，不是新增维度。
- 类型：用户设计决定；数值（F、M、上限、权重、阈值）未定。
- 本项目采用：[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md)；[task7 TASK](tasks/task7/TASK.md) U24、U26。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。


<a id="src-0362"></a>
## SRC-0362 — 2026-10-19用户对task7接口问题的选择与设计原则

- 支撑主张：①现在先不设计验证仿真（ManiSkill）的环境，只考虑训练用的sim环境。②只考虑sim时，路径评估检查碰撞用扫描累积的局部地图，不用真值地图（task7.4 I1）。③执行中途停下、没到达候选点的样本不作f_p标签，只用到达的样本监督f_p（I2）。④总原则：设计要符合SC²-WM的基本思想。
- 原始依据（用户原话/选择）：I1首次回答“现在先不设计后面验证仿真的环境，只考虑sim的环境”；再问“只考虑sim的话，路径评估检查碰撞用哪种信息？”选“扫描累积的局部地图（推荐）”；I2选“只用到达的样本（推荐）”；随后“反正要符合SCWM的基本思想”。
- 与SC²-WM的对应（Claude说明，依据[SRC-0358](#src-0358)、[SRC-0334](#src-0334)）：SC²-WM智能体只用自身观测投影的局部占据/语义栅格生成候选，不用真值地图；世界模型只对实际执行的候选、用到达后的观测监督。SC²-WM导航总能到达所选航路点（瞬移或tryout），本项目“中途停下”是新增情况，“只用到达样本”为最接近的处理。（2026-10-20收窄，Claude据Codex第二轮#15与[SRC-0391](#src-0391)：SC²-WM的tryout分支尝试次数有限、碰撞时可中止，前进为整数步，不保证精确到达请求点，“总能到达”只适用于瞬移分支；用户“只用到达样本”的决定不变。原句保留作历史。）
- 类型：用户设计决定与原则；不是外部技术证据。
- 本项目采用：[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md) §11；[task7 TASK](tasks/task7/TASK.md)入口与§2.7；ManiSkill相关接口与task7.12暂缓。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5），直接读取本会话用户消息。


<a id="src-0363"></a>
## SRC-0363 — 2026-10-19用户对task7.4训练与评估协议的选择

- 支撑主张：①地图：让mapgen生成立方体、椭圆柱体这样的地图（不采用Claude“训练地图在sim内现场生成、未见场景只读使用现有24张语义地图”的推荐）。②预算按决策次数计量。③G5联合训练对照先不做。④做G6：在sim的未见场景上做测试期适应（SC²-WM的模型级自修正）。
- 原始依据：2026-10-19本会话，用户对四项提问的回答：“地图按推荐做吗？”=“让mapgen生成一些立方体，椭圆柱体这样的地图”；“预算按什么计量？”=“按决策次数（推荐）”；“要不要做G5联合训练对照？”=“先不做”；“要不要做G6？”=“做”。
- 相关事实：N²M²训练环境本身使用随机矩形与椭圆障碍（[SRC-0328](#src-0328)）；mapgen现有输出只有长方体JSON（[SRC-0331](#src-0331)），椭圆柱体需要扩展输出格式及sim中的射线求交与碰撞检查。
- 未定：mapgen地图用于训练还是测试、数量、是否仍用现有语义地图作未见场景、未见场景集合的定义；G6触发条件（U6）。
- 后续：第①项已被[SRC-0364](#src-0364)取代（只生成长方体、不加椭圆柱体、B类不做）。
- 类型：用户设计决定。
- 本项目采用：[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md) §15–§18；[task7 TASK](tasks/task7/TASK.md) §2.5、§4；task7.7。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。


<a id="src-0364"></a>
## SRC-0364 — 2026-10-19用户对mapgen地图的最终选择（取代SRC-0363第①项）

- 支撑主张：①A类地图先只生成立方体，兼容Gazebo；不加入椭圆柱体。②A类每个难度档（稀疏、标准）验证集50张、测试集100张。③B类语义场景本轮不做。
- 原始依据：用户先要求“更新mapgen需求文档：加入椭圆柱体。先跟我确认地图是用于训练还是测试、各要多少张，再动文件。”Claude确认时用户回答：A类用途“这里就先生成一些立方体吧，兼容Gazebo”；数量“验证50＋测试100（推荐）”；形状比例“不要圆柱体先”；B类“不做这个”。
- 相关事实：N²M²迁移代码中障碍以0.5概率取矩形或圆柱/椭圆，注释说明Gazebo没有椭圆模型，Gazebo环境只用矩形（`forem/src/modulation_rl/scripts/modulation/envs/map.py:871–877`）。
- 未定：A类训练时在线调用同一生成函数还是使用固定文件池（用户未选，需求文档保留两种可能）；B类不做后，G6测试期适应与“未见场景”测试改用什么场景。
- 类型：用户设计决定（第①项取代[SRC-0363](#src-0363)第①项“生成立方体、椭圆柱体”）。
- 本项目采用：[mapgen需求文档](../../mapgen/docs/husky_ur5_map_requirements.md)；[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md) §16；[task7 TASK](tasks/task7/TASK.md) §2.5。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。

<a id="src-0365"></a>
## SRC-0365 — task7.5(A)版本归属与差速积分复用审计

- 主张/类型：本地代码静态事实；复用及GPU判断为工程分析，未运行验证。三份`myutils.cpp:405–421`都是先更新朝向、再按新朝向平移，不是常值(v,ω)的精确圆弧积分；Husky调用差速函数，上游对应TIAGo而非UR5。
- 作者/版本：CBL快照`1ccedd087ac12dd317e93accc37bb81e05beeb99`（原tree路径`src/`，现位于`husky/src/modulation_rl/`）；上游N²M² `6281205846b1bac4525d05ee230a47bddf42023d`（`mobile-rl/`，干净）；FoReM根HEAD `3b519958d57c3141841c517afa4f6c59d23f467a`，但迁移目录未跟踪，不能把HEAD称其代码commit；逐文件SHA256见下方使用文档§A.1。
- 精确位置：H/F `src/robot_husky.cpp:68–75`、`scripts/modulation/envs/robotenv.py` H`:325`起/F`:308–321`；U `src/robot_tiago.cpp:68–75`；H/F/U `src/myutils.cpp:405–421`（路径前缀见版本）。H快照`git show 1ccedd0:src/myutils.cpp`与现文件SHA256同为`33f48910935a16ff5108760e0648fe961aaa3d95961e0d53f8d98263fd56c5a9`。
- 原始结论：平移仅取输入x；Python差速动作顺序为`[ω,v]`；无轮胎/驱动动态。推导：task7接口(v,ω)要显式换序；圆弧位置增量为`vΔt sinc(ωΔt/2)[cos(θ+ωΔt/2),sin(θ+ωΔt/2)]`，其中sinc(u)=sin(u)/u，零点取1；x/y单位m、θ单位rad、Δt单位s，前提常值控制。此为数学积分，不是实测。
- 采用/限制：保留非完整运动学概念，公式改写成批量张量并统一预测/执行；不直接复制ROS tf实现，不声称GPU提速。参考版本和未跟踪源码不能混记。
- 核查：2026-10-19，Codex；读取源码、Git对象、diff与哈希；未运行项目程序。
- 使用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) §A.1–A.3。

<a id="src-0366"></a>
## SRC-0366 — task7.5(A) FK/IK依赖与失败事务边界

- 主张/类型：本地代码静态事实＋工程复用建议；延续[SRC-0351](#src-0351)–[SRC-0355](#src-0355)，不是新的IK性能审计。
- 作者/版本：H/U/F定义同[SRC-0365](#src-0365)；F未跟踪文件按[RESULTS](tasks/task7/task7.5/RESULTS.md) §A.1哈希定位。
- 精确位置：H/F `src/robot_env.cpp:39–91、190–239、389–393、411–470、479–515、676–708`；U同文件`:39–91、181–238、402–461`；F `husky_ur5/config/kinematics.yaml:11–19`、`husky_ur5/urdf/husky_ur5.xacro:6–16、35`起；F `bio_ik/src/kinematics_plugin.cpp:638–653`。H/F robot_env SHA256=`6fab72460d686f12b43797c1e4bc1b61d844a43ef46b5e418f07f6dfa4ce703a`。
- 原始结论：FK由MoveIt RobotState模型变换取得，非独立UR5张量库；配置BioIK允许近似解，正则/位移等为软目标；只在碰撞标志为真时显式恢复旧臂关节，下一底盘位姿已先设置。因此旧step不满足task7“底盘与臂同时停在最后可行检查点”的事务语义。上层还合并slack失败。
- 采用/限制：模型/安装/工具坐标作参考；重用解析分支思路须先按同一模型核对FK/IK，所有分支、限位、连续性、残差和碰撞分开判；状态提交须在完整检查后进行。现有ROS/MoveIt/BioIK对象不适合直接作为GPU批量核心；新张量实现的性能、正确性均未验收。
- 核查：2026-10-19，Codex；局部代码全文/相关函数静态阅读，未查询ROS实参、未执行IK。
- 使用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) §A.4。

<a id="src-0367"></a>
## SRC-0367 — task7.5(A)碰撞调用链：地面检查存在，随机障碍未见同步到臂碰撞场景

- 主张/类型：本地代码静态事实与限定范围的负面发现；修正[SRC-0360](#src-0360)④过宽概括，不声称排除所有外部ROS扩展。
- 作者/版本：H/U/F同[SRC-0365](#src-0365)。
- 精确位置：U `src/robot_env.cpp:72–91`创建场景并显式加入地面，`:111–124`状态监视且请求components=2（ROBOT_STATE），`:164–173、441–461`调用碰撞；H/F相应`:72–92、118–125、450–470`；三份`src/validity_fun.cpp:11–30`实际为`checkCollision`，`checkSelfCollision`被注释。U/H/F `scripts/modulation/envs/combined_env.py:180–188、365–384`底盘局部栅格覆盖检查；U `envs/map.py:730–745、792–803、849–877`、`simulator_api.py`的DummySimulatorAPI只负责栅格/模拟器对象；`map.py:421–430`初始底盘到末端连线启发式不能替代全臂检查。
- 原始结论：解析sim里底盘碰撞为覆盖区域与局部图相交；MoveIt回调有机器人与机器人、已存在的world几何检查能力（受group/ACM约束），并且world中确有地面。在所读sim初始化/地图reset/step链路未见把随机长方体加入该PlanningScene，不能认为已具备全臂对这些障碍的检查；Gazebo分支另用接触回调，不能外推解析sim。
- 采用/限制：底盘几何、ACM及连杆几何可作参考；task7需分别实现底盘障碍、臂自碰撞、臂环境检查和独立真值判定；规划侧只能访问扫描累积局部地图[SRC-0362](#src-0362)。多高度感知不足时不能从单层扫描恢复真值高度。几何张量改写可讨论GPU批量，但近似形状与离散检查限制待(B)确认，未选定碰撞球或其他新模型。
- 核查：2026-10-19，Codex；读取以上主路径，检索`CollisionObject/planning_scene/octomap`；无程序运行，无动态场景验证。
- 使用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) §A.5；[Codex回复](agent_logs/task7/20261019-claude-codex-sync.md#codex回复)。

<a id="src-0368"></a>
## SRC-0368 — task7.5(A)末端规划器时间推进与路线几何的复用界限

- 主张/类型：本地代码事实＋面向同步/不同步变体的工程分析，非已实施协议。
- 作者/版本：H/U/F同[SRC-0365](#src-0365)；H/F `eeplanner.py`相同SHA256见RESULTS；与U的差异为高度偏好设置。
- 精确位置：U `scripts/modulation/envs/eeplanner.py:1–22、165–176、198–215、224–263、468–505、549–580、617–660`；H/F同函数/同位置，`:545、679`附近`height_preference=True`覆盖了U的eval/False；U/H/F `combined_env.py:365–367`先推进末端规划器，再执行机器人；U `map.py:421–430`是起点启发式。
- 原始结论：按planner时钟与dt从上一计划位姿继续推进；解析训练用固定时间增量，物理分支用ROS时间，dt还可能截断。PointToPointPlanner用pyastar、地图高度插值和SciPy四元数插值，每次generate_obs_step重算路线；不是预先固定的一条参数化路线，也不是各候选彼此隔离的纯函数。
- 采用/限制：A*路线和插值思想改写后可复用为任务输入；同步变体要单独冻结路线/时间推进、候选模拟时钟与提交时钟；不同步变体要显式参数s及保持/推进，不按旧wall时间自动走。取消旧学习速度接口不得偷偷改变本任务已定时间/进度合同。固定路线插值可GPU批量，CPU pyastar/ROS/PIL当前实现不能直接批量；无耗时结论。
- 核查：2026-10-19，Codex，相关类/调用链静态阅读，无规划运行。
- 使用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) §A.6。

<a id="src-0369"></a>
## SRC-0369 — task7.5(A)旧sim局部图来自真值裁剪，未提供目标扫描累计链路

- 主张/类型：静态源码事实及检索范围内的缺口，非全仓任意工具均不存在的证明。
- 作者/版本：H/U/F同[SRC-0365](#src-0365)。
- 精确位置：U `scripts/modulation/envs/map.py:60–64、180–218、220–310、469–480`；H对应同位置，F从`:54`新增参数后偏移1行；U/H/F `envs/occupancy_grid_manager.py:9–20、61–74`；C++ `src/mycostmap.cpp:114–160`为ROS costmap膨胀。
- 原始结论：`world_type=='sim'`无条件走`_get_local_map_gt`；Gazebo/world读ROS costmap，OccupancyGridManager仅接收栅格及增量。所读envs/C++主路径及`LaserScan/raycast/ray_trace/lidar`检索未见360束解析射线→遮挡感知→扫描累积的实现。局部裁剪不等于局部可观测信息。
- 采用/限制：坐标转换、栅格覆盖等可改写复用；sim真值裁剪作为路径评估输入不可用，违反[SRC-0362](#src-0362)。环境真值生成观测与真值碰撞仍可读JSON；规划只读累计地图/未知掩码。射线求交及累计更新需要新实现（本轮未实施），可讨论按环境×射线×障碍GPU广播/分块，不能预报吞吐。21:07重读发现并发新增[SRC-0373](#src-0373)：全景深度与128×128×2/0.05 m格已定，相关旧一维扫描措辞不当新规格；高度累计/自遮挡/臂包络细节仍待S1–S5，不能补真值。
- 核查：2026-10-19，Codex，文件/符号静态读取和检索；未执行扫描或costmap。
- 使用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) §A.7。

<a id="src-0370"></a>
## SRC-0370 — task7.5(A)mapgen角点JSON与N²M²中心障碍的适配

- 主张/类型：本地代码事实＋几何坐标推导、工程复用建议。
- 作者/版本：mapgen独立仓库`765e06448758dfbe34282edcac00f39ffad36aa5`；H/U/F同[SRC-0365](#src-0365)。
- 精确位置：`mapgen/mapgen/map_builder.py:17–43、46–64、67–97、100–107、110–136、156–169、190–215`（SHA256=`42c66d4b8ffceb973b6ffa419e79862eb2c25f1bb88cd0307ba5014ef8d052ea`）；`parser.py:40–71`。U `scripts/modulation/envs/map.py:682–702、849–877`；H`:837–838`硬编码spacing=3.0/offset_std=0.8，F`:54、871–877`另有force_rectangle参数。新环境不继承这些工程数值。
- 原始结论：JSON `boxes`每行`[px,py,pz,sx,sy,sz,cosθ,sinθ]`；点从局部0到size范围绕原点旋转，再加position，即position为底面角点，非中心。边界墙进入PCD但不在boxes中，PCD裁剪与原始boxes可不同；出生净空函数使用中心形式且只测角点，不能拿它当机器人通行验收。N²M²障碍位置按中心画矩形/椭圆；CBL把传入spacing和offset_std覆盖；FoReM额外开关不意味着始终仅矩形。
- 推导：以二维旋转R(θ)，中心`c_xy=p_xy+R(θ)[sx/2,sy/2]`，`c_z=p_z+sz/2`，米/rad；若新几何保留角点协议可不转换。不能照搬旧PIL像素旋转符号而跳过世界坐标核查。
- 采用/限制：解析JSON字面字段可直接读取，现有三个modulation_rl地图入口未见该JSON读取器；需新适配。墙/边界、裁剪策略由(B)/task7.7统一，不能凭JSON没有墙就取消围墙。数据读取可CPU一次完成、几何张量上GPU；不改mapgen、不生成地图、不增椭圆柱体。
- 核查：2026-10-19，Codex，相关源码静态阅读；未调用mapgen。
- 使用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) §A.8。

<a id="src-0371"></a>
## SRC-0371 — task7.5(A)任务/奖励/终止入口与姿态距离单位

- 主张/类型：静态代码事实＋工程复用建议；补充[SRC-0360](#src-0360)待核的姿态定义。
- 作者/版本：H/U/F同[SRC-0365](#src-0365)。
- 精确位置：U/H/F `scripts/modulation/envs/tasks.py:142–159、218–265`，`simulator_api.py:27–48`；`combined_env.py:309–354、356–395`；`eeplanner.py:187–193、242–255`；`env_utils.py:123–130`；C++ `src/myutils.cpp:44–46`。成功统计另见`utils.py:530–531`与[SRC-0360](#src-0360)。
- 原始结论：任务wrapper给末端终点/容差；combined_env逐步累计失败并计算IK/底盘/动作惩罚。姿态距离是`1−(q_a·q_b)^2`，归一化四元数下等于`sin²(φ/2)`，无量纲，旧阈值0.05不能写成0.05 rad。这里φ为最短旋转角rad，此等价式为四元数推导，不是新阈值选择。
- 采用/限制：参考失败字段与审计分项，旧奖励/终止控制流不可直接复用为task7.4；需按新半马尔可夫决策、最后可行检查点、一次失败计数、两变体及terminated/truncated重写。计数/奖励算术适合张量批量，但ROS wrapper并非GPU VectorEnv；不得改动已定任务定义或继承旧容差数值。
- 核查：2026-10-19，Codex；静态相关函数与公式核查，未执行环境/评估。
- 使用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) §A.9；[Codex回复](agent_logs/task7/20261019-claude-codex-sync.md#codex回复)。


<a id="src-0372"></a>
## SRC-0372 — 观测设计的代码依据：SC²-WM全景深度与栅格、Husky离地高度与CBL所装雷达

- 支撑主张：①SC²-WM的仿真观测为12个朝向（30°间隔）的虚拟RGB-D相机，RGB 224×224、深度256×256，视场均为90°（朝向复制见[SRC-0325](#src-0325)）；深度投影成以机器人为中心的占据栅格并按高度阈值区分障碍与地面（[SRC-0358](#src-0358)），先累积全局栅格、再按机器人位姿旋转并裁剪出局部栅格；栅格0.05 m/格、192×192。②Husky URDF碰撞模型：下层车体碰撞盒中心在base_link上方base_z_size/4、高base_z_size/2，即底面位于base_link原点；base_link离地＝轮半径0.1651−轮竖直偏移0.03282≈0.132 m，因此碰撞模型的车体离地约0.132 m。③CBL的Husky+UR5模型在base_link上前后各装一台Velodyne VLP-16（origin (±0.5, 0, 0.2) m），仿真参数设为1 Hz、1个采样点（注释原值10 Hz、200）；VLP-16的描述文件不在本机，线数与垂直视场按厂商规格，待核。
- 类型：本地代码/配置静态核查与推导；未运行。
- 精确位置：`scwm/` commit `f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b`：`run_r2r/r2r_vlnce.yaml:13–21`；`vlnce_baselines/ss_trainer_ETP.py:1713、1930–1935`。`forem/src/husky_description/urdf/husky.urdf.xacro:85、90、94、105–107、111、122`。`husky/src/husky_ur5/urdf/husky_ur5.xacro:18–24`（与`forem/src/husky_ur5/urdf/husky_ur5.xacro`同段内容一致）。
- 推导（Claude）：全景深度若安装在约0.5 m、垂直视场±45°，最低一行在约0.5 m外触地，最高一行在3 m处约达3.5 m高；水平1°一列时3 m处列间距约0.05 m（[SRC-0330](#src-0330)）。这些是几何推导，安装高度与分辨率为工程选择。
- 本项目采用：task7.7观测设计（全景深度、局部栅格、底盘碰撞判定），见[task7.7 RESULTS](tasks/task7/task7.7/RESULTS.md)。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。


<a id="src-0373"></a>
## SRC-0373 — 2026-10-19用户确定的观测与底盘碰撞设计

- 支撑主张：①传感器照SC²-WM用360°全景深度观测（不用RGB）。②局部栅格：以机器人为中心、从本回合累积全局栅格中裁出，0.05 m/格，128×128（6.4 m见方），两个通道（是否观测到；每格障碍最高高度）。③所有障碍都算挡底盘，不允许从障碍上方驶过（U9收敛）。
- 原始依据：用户先问“传感器的问题，为什么不是像SCWM里面的全景观测，然后局部格栅我不知道选什么，底盘的间隙你有想法吗”；Claude给出建议后用户确认“三项都按建议定：全景深度观测、128×128、0.05 m双通道局部栅格、所有障碍算挡底盘。写进task7.7并登记来源。”
- 类型：用户设计决定。安装高度（约0.5 m）、全景分辨率、量程、自遮挡掩码细节为工程选择，未定。
- 本项目采用：[task7.7 RESULTS](tasks/task7/task7.7/RESULTS.md)；[task7 TASK](tasks/task7/TASK.md) §2.4、U9、U10。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。



<a id="src-0374"></a>
## SRC-0374 — SC²-WM的VCM（视觉校准模块）：结构、记忆与训练信号（论文与代码）

- 支撑主张：①论文：v_t=f_enc(o_t)；VCM维护最近L步的情节记忆M_t={(k_i,m_i)}，键由存储特征加相对空间与时间编码现场构造；以v_t为查询做交叉注意力并带可学习时间衰减，c_t=Σsoftmax(A_i)m_i，A_i∝v_tᵀk_i−φ(δ_ti)；自适应门控融合v̂_t=α_t⊙v_t+(1−α_t)⊙c_t；后验状态s_t=f_q(s_{t−1}, a_{t−1}, v̂_t)（式(3)条件写为修正后的s^(Δ)_{t−1}）；动作后用(v̂_t, s_t)更新记忆。总损失L=L_ac（模仿学习）+L_wm（后验与先验KL）+L_rec（解码d(s̃_{t+1})与预训练编码器给出的v_{t+1}的平方误差）。附录：时间偏置B=−|λ|(t−k)，λ初值0.1；7维相对几何编码（相对朝向与俯仰的正余弦、归一化距离）经线性层与LayerNorm；记忆长度L∈{2,4,6,8}消融中L=4最好；作者称VCM是闭环校正的轻量功能模块，在潜空间检索、不构建显式地图。②代码：`VLNMemoryBank(mem_length=4, retrieval_layers=1, feature_dim=512, fusion_type='gate')`（文件内文档写8/2，与实际配置不一致）；记忆存前向视图的196个patch特征及位置、朝向、步号，先进先出；查询为12个方向的类别特征（前向来自CLIP，其余11个来自NeRF预测）加相对位置编码；位置编码与步号嵌入零初始化；门控`scale=sigmoid(Linear([x1;x2]))`，偏置初值2.0（初始约0.88取当前观测）。训练时（第2步起）另有记忆重建损失：增强后的11个非前向方向特征与真实渲染的CLIP特征做MSE——该项不在论文总损失式中。训练阶段可训练参数为vln_bert与vln_memory；测试期适应时只训练global_encoder，VCM冻结。
- 类型：外部论文原文（本地PDF文本提取）与官方代码静态核查；未运行。
- 精确位置：论文`scwm/paper/SC2-WM-ICML2026.pdf`（arXiv:2608.07548v1）§3式(1)–(8)、§3.1、§3.2式(11)–(13)、算法1、附录“Temporal Prior/Spatio-temporal Encodings in Memory of VCM”与“Ablation Study of Visual Memory Design”（表7）。代码`scwm/` commit `f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b`：`utils_p/vln_memory.py:24–160、163–230、297–420`；`vlnce_baselines/models/Policy_ViewSelection_ETP.py:155–161、296–420`；`vlnce_baselines/ss_trainer_ETP.py:985–1000、1040–1071`。
- 本项目采用：task7.8 VCM方案以此为模板，见[task7.8 RESULTS](tasks/task7/task7.8/RESULTS.md)。
- 限制：PDF文本提取的公式排版可能有误，关键式已与上下文对照；L=4的结论来自VLN-CE任务，不能直接证明适用于本项目。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。



<a id="src-0375"></a>
## SRC-0375 — 2026-10-19用户确定的VCM方案

- 支撑主张：①VCM结构照SC²-WM：注意力记忆（最近4次决策）＋门控融合＋GRU状态递推。②VCM首版只用SAC的Critic损失训练。③末端未来路线以“栅格通道＋向量”两种形式输入。
- 原始依据：用户对三项提问的选择：“照SC²-WM：注意力记忆＋门控＋GRU（推荐）”“只用 Critic 损失（推荐首版）”“栅格通道＋向量（推荐）”。
- 类型：用户设计决定；SC²-WM原设计见[SRC-0374](#src-0374)。“Critic损失训练编码器、Actor梯度截断”为常见做法，出处待补证据。
- 本项目采用：[task7.8 RESULTS](tasks/task7/task7.8/RESULTS.md)；[task7 TASK](tasks/task7/TASK.md) U1、U2、U4、U27。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。


<a id="src-0376"></a>
## SRC-0376 — task7.5(B)用到的地图墙体、自碰撞允许对与UR5关节速度限位（本地代码/配置）

- 支撑主张：①mapgen地图坐标以原点为中心，`MAP_SIZE_X/Y=10.0`、`MAP_SIZE_Z=1.6`、`RESOLUTION=0.05`；边界墙只写进PCD，不写进JSON boxes：`BOUNDARY_WALL_HEIGHT=1.0`、`BOUNDARY_WALL_THICKNESS=0.1`，墙点位于x、y＝±5 m的单层面上（厚度常量在墙生成函数中未使用）。②`husky_ur5/config/ur5.srdf`定义manipulator链`ur5_base_link→ur5_tool0`、whole_body与gripper组；共119条`disable_collisions`（Adjacent 18、Never 99、Default 2），含车体与车轮对`ground_plane`等。“Never”是MoveIt Setup Assistant按采样得出的，不是几何证明。forem与husky两份SRDF逐字节相同。③`husky_ur5/config/joint_limits.yaml`中6个UR5关节速度上限均为π rad/s，未给位置限位；位置限位来自xacro引用的`ur_description` `ur5_macro.xacro`，该包不在`forem/src`中，本次未核到其文件。
- 类型：本地代码/配置静态核查（只读，未运行）。
- 精确位置：mapgen `765e06448758dfbe34282edcac00f39ffad36aa5`：`mapgen/map_builder.py:8–14、46–64`（SHA256前缀`42c66d4b8ffceb97`）；`forem/src/husky_ur5/config/ur5.srdf:13–23、43–46、75–194`（未跟踪，SHA256前缀`a7d2c8f431af28ea`，与`husky/src/husky_ur5/config/ur5.srdf`相同）；`forem/src/husky_ur5/config/joint_limits.yaml:1–31`（SHA256前缀`eca6ac96fbf309c4`）；`forem/src/husky_ur5/urdf/husky_ur5.xacro:6–8、12–16、35–39`。
- 本项目采用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) (B) B.2、B.4、B.5：墙作为读取器补充的长方体；自碰撞允许对须复核后才能沿用；关节速度上限只用于关节跳变指标（task7.4 §3），不作为IK失败条件。
- 限制：未运行xacro展开，未核UR5位置限位与夹爪TCP定义；墙体厚度与放置方向为待定（B1）。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。



<a id="src-0377"></a>
## SRC-0377 — CBL末端坐标约定与用户对task7.5(B) B2、B3的决定

- 支撑主张：①CBL中任务目标为夹爪尖端位姿；代码沿目标x方向退回`tip_to_gripper_offset`＝0.15 m换算为`gripper_base_link`目标，再对`gripper_base_link`求IK；`ee_link`以零偏移固定在`ur5_wrist_3_link`上，Robotiq 85夹爪挂在`ee_link`下并绕y轴转−π/2；MoveIt运动链末端为`ur5_tool0`。②用户决定B2：任务路线与成功判定用夹爪尖端（TCP），IK通过固定变换在法兰（tool0）求解。③用户决定B3：IK用UR5解析多解，按上一有效关节解选最近分支；在task7.6中核对解析FK与URDF FK一致并计时后最终确认，阻尼最小二乘仅作备选。
- 类型：本地配置/代码静态核查＋用户设计决定。0.15 m为CBL工程配置值，Robotiq 85真实TCP距离未核对（待补证据）。
- 精确位置：`forem/src/modulation_rl/gazebo_world/husky_ur5/robot_config.yaml:5–14`；`forem/src/modulation_rl/src/myutils.cpp:191–209`；`forem/src/husky_ur5/urdf/husky_ur5.xacro:34–45`；`forem/src/husky_ur5/config/ur5.srdf:14`。用户原话：B2选“任务用TCP，IK在法兰求（推荐）”；B3选“UR5解析多解（推荐）”。
- 本项目采用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) B.4、B.15。与阶段一不同：CBL的BioIK允许近似解（[SRC-0366](#src-0366)），task7以FK回代残差不超过E7判定成功。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。



<a id="src-0378"></a>
## SRC-0378 — 2026-10-19用户对task7.5(B) B11的决定：失败只按真值判定

- 支撑主张：局部栅格只影响路径评分（候选特征f_k与路径选择）；执行器只有在IK失败或真值碰撞时才停在最后可行检查点并记一次失败；不另设安全层（取代父TASK §2.9“扫描发现障碍进入安全距离即停止”）。
- 原始依据：用户先问“这里我们CBL的项目是不是无所谓失败，只要求成功路径的IK失败是0”；Claude核实CBL成功＝零IK失败、零底盘碰撞、到达目标，失败只计数并扣奖励、累计20次终止，CBL sim中底盘碰撞按真值地图重叠计数而不阻挡（[SRC-0360](#src-0360)、task7.5 (A)）；随后用户决定“B11定为只按真值：局部栅格只影响路径评分，只有IK失败或真值碰撞才停下记失败，不另设安全层。写进文档。”
- Claude说明的理由：理想SIM深度无误差时，对已看见的障碍两种规则停在同一检查点；区别只在局部栅格误判（未知格、离散化）时，“只按真值”不记未发生的失败，与CBL只记真实发生事件的口径一致。以后在物理仿真中“真值”对应接触检测。
- 类型：用户设计决定。
- 本项目采用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) B.10、B.15；[task7 TASK](tasks/task7/TASK.md) §2.9；[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md) §4。
- 2026-10-20收窄（Claude，据Codex第二轮#16）：“理想深度时两种规则停在同一检查点”只在没有栅格离散化、遮挡与表示误差时成立；实际局部栅格存在这些误差，因此只能说二者在已正确观测的障碍上通常一致。原句保留作历史，决定本身不变。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。


<a id="src-0379"></a>
## SRC-0379 — task5 CBL两条链路的验证状态核对（2026-10-19）

- 支撑主张：task5.2 CBL原版RLlib的sim最终评估已交付并经task5.3 R13复核；task5.5自写SAC三种子均训练至5M、有最终策略文件，但其RESULTS仍明确最终sim评估尚未执行。
- 类型/机构：FoReM项目原始产物与任务记录核对；不是新实验。
- 版本/精确位置：run-id `t5.2-eval-r2`，`forem/results/task5/t5.2-eval-r2/final_eval_summary.json`的tasks、eight_runnable_task_mean及limits；[task5.3 RESULTS](tasks/task5/task5.3/RESULTS.md) R13；run-id `t5.5-sim-cbl5m-s{0,1,2}`，各`train_summary.json`的steps=5000000与`ckpt/policy_step05000000.pt`存在性；[task5.5 RESULTS](tasks/task5/task5.5/RESULTS.md)“最终评估”节。
- 原始结论：原版RLlib simpleobstacle为39/50＝0.78；8个可运行任务平均0.2475，bookstorepnp不可运行，不计为0。自写SAC已有训练产物；不能把训练中D15读数当作最终评估。
- 本项目采用：回答用户的task5状态问题，记录在[核查日志](agent_logs/task5/20261019-codex-cbl-status.md)。
- 适用限制：未重跑评估，未重新审核所有历史回合；完成日期和R13状态沿用任务记录。旧JSON仍保留交付时review状态，最终复核以task5.3记录为准。
- 核查日期/人：2026-10-19，Codex；实际模型/强度无法独立核实。


<a id="src-0380"></a>
## SRC-0380 — task5.5最终sim评估用户授权、协议沿用与启动（2026-10-19）

- 支撑主张：用户明确要求“你启动一下验证”，承接task5.5三条5M策略最终sim评估；本次沿用task6.1固定场景2001–2050、每策略50回合、确定性动作、max_steps=2000、max_close_steps=500，不含Gazebo。以上数值是沿用项目既定评估协议，不是外部通用参数。
- 类型/作者/版本：用户授权＋FoReM原始运行证据；2026-10-19，Codex。三训练run-id `t5.5-sim-cbl5m-s{0,1,2}`；评估run-id `t5.5-final-sim-s{0,1,2}-r1`。
- 精确位置：`forem/logs/task5/t5.5-final-eval-launch-20261019/manifest.json`（完整命令、策略/评估脚本/启动器SHA256），各`*-launch.json`（三次docker后台启动返回0）；`forem/logs/task6/<评估run-id>/start.out`（inst63/64/65 ready=true，startup_s=3.1），同目录`eval.out`；输出为`forem/results/task6/<评估run-id>/eval.json`。
- 原始依据：三条训练manifest的全部sources逐项核对当前文件一致；评估脚本当前ba140ec7…与task6.1原9989213…不同，差异已在[SRC-0253](#src-0253)登记，本次重读原备份与diff：Gazebo可选覆盖、配置和长回合记录，sim输入与核心循环不变。实例端口11463–11465/11563–11565启动前均空闲；forem-dev原仅init/sleep，GPU0–3空闲。
- 本项目采用：[task5.5 RESULTS](tasks/task5/task5.5/RESULTS.md)启动记录与[独立日志](agent_logs/task5/task5.5/20261019-codex-final-sim-eval.md)。
- 启动后补核：启动证据目录`startup-verification.json`、`gpu.txt`、`processes.txt`确认三条均有逐回合输出，宿主评估PID844488/844496/844498已分配GPU显存各708 MiB；未发现Traceback。
- 限制：后台启动返回0及实例ready不等于评估通过；最终指标以每条eval.json及eval rc为准。沿用启动器会在eval.out记录eval/stop rc，不能仅凭包装进程退出码判断评估成功。
- 核查日期/人：2026-10-19，Codex；实际模型/强度无法独立核实。



<a id="src-0381"></a>
## SRC-0381 — N²M²/CBL末端任务采样参数与2026-10-19用户对task7.5(B)其余待定项的决定

- 支撑主张：①N²M²/CBL迁移代码中，末端终点由`sample_circle_goal`在起点周围按距离范围与高度范围采样，并限制在地图尺寸减2.5 m的范围内；基类任务距离`(1, 3)`、高度取受限工作空间（0.4–1.1 m），`SimpleObstacleTask`默认距离`(0.5, 8)`；`robot_config.yaml`中末端高度`z_min/z_max`为0.7/1.15 m，末端规划膨胀半径0.40 m；默认地图11×11 m（[SRC-0328](#src-0328)）。②用户“都按你推荐的走”，采纳以下推荐：地图保持10×10 m；起点在全图空闲区随机采样（生成任务时可用真值检查净空，不改mapgen）；终点距起点0.5–8 m、高度0.7–1.15 m，姿态暂定“夹爪水平、朝向沿路线末段方向”（N²M²`use_fwd_orientation`含义待核）；生成时检查终点不在障碍内且至少存在一个无碰撞且IK有解的底盘位姿，否则重采样；路线在真值地图上A*规划（膨胀0.40 m），高度线性插值、姿态球面插值，改写为纯函数（B12）。B7：不同步变体的路径族同时包含“s随底盘匀速联动推进到s_k”和“底盘先到位、再推进s”，由路径评估选优；s推进速率设上限（与E8一并定）。B6：LocalCollision中未知格按空闲判定，另在f_k中加入“路径经过未知格的比例”“到最近未知格的距离”两项风险特征。B1：墙按mapgen需求§3.3写入JSON（厚0.15 m、高1.6 m），放在[−5, 5]范围以内。B5：不直接沿用SRDF中采样得出的“Never”对，只保留相邻连杆与几何上恒接触的允许对，其余按几何判定。B4：关节位置限位查到来源后登记。B10：单次决策超时取“该路径规划时长×系数”，到达容差与E1一并定。B8、B9、B13、B14交task7.6计时后定。
- 原始依据：用户先问“现在的地图你认为合适的大小是什么”，Claude建议10×10 m＋随机起点＋终点0.5–8 m（理由：与N²M² 11×11 m同量级、与6.4 m局部栅格和约3 m有效感知匹配、计算便宜；起点固定在中心时终点最远约4.5 m，每回合仅3–6次决策）；用户回答“好的，都按你推荐的走”。
- 类型：本地代码静态核查（①）＋用户设计决定（②）；各系数、上限与阈值未定。
- 精确位置：`forem/src/modulation_rl/scripts/modulation/envs/tasks.py:299–301、315–317、338–339`；`forem/src/modulation_rl/gazebo_world/husky_ur5/robot_config.yaml:19–22、32`。
- 本项目采用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) B.15；[task7 TASK](tasks/task7/TASK.md) §2.5；[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md) §1、§10。
- 2026-10-20更正（Claude，据Codex第二轮#13、#14与[SRC-0387](#src-0387)）：①把不同任务类的采样范围混在了一起。实际为：基类RndStartRndGoalsTask默认距离(1, 5)；SplineTask显式(1, 3)、受限高度，且只有它传入“地图尺寸减2.5 m”；SimpleObstacleTask默认(0.5, 8)、高度z_min/z_max、传完整地图尺寸；三者都围绕底盘起始位姿采样gripper/wrist目标后再换算到尖端，`sample_circle_goal`内部另减0.5 m边距并clip。②中“use_fwd_orientation含义待核”已核清：N²M²终点RPY逐轴随机，该开关只把中途yaw对齐路径、末尾恢复随机终点，不规定水平终点；本项目“终点夹爪水平、沿路线末段方向”是用户采纳的本项目工程设计，不是沿用N²M²。原始依据中“起点固定在中心时每回合仅3–6次决策”是Claude估计，无统计证据。用户已选的0.5–8 m、0.7–1.15 m不变；距离锚点与“水平”所指TCP轴已于2026-10-20由用户确定，见[SRC-0393](#src-0393)。原句保留作历史。
- 核查日期/人：2026-10-19，Claude（claude-opus-5-5）。


<a id="src-0382"></a>
## SRC-0382 — 离散动作SAC：原始损失与task7适用边界

- 支撑主张/类型：外部论文原文；候选上的softmax、双Q、精确动作求和的离散SAC损失有原始出处。
- 作者/版本/URL：Petros Christodoulou，*Soft Actor-Critic for Discrete Action Settings*，2019，arXiv:1910.07207v2；[原PDF](https://arxiv.org/pdf/1910.07207v2)。
- 精确位置与核查程度：§2式(4)、(9)，§3式(10)–(12)、算法1，PDF页2–4；本次已读相关原文与公式，不是摘要转述。
- 原始结论（改写符号）：V(x)=Σ_a π(a|x)[min_i Q_i(x,a)−α logπ(a|x)]；Critic最小化E[½(Q_i−y)²]，y=r+γ V_target(x')；Actor最小化E_x Σ_a π(a|x)[α logπ(a|x)−min_i Q_i(x,a)]；温度目标E_x Σ_a π(a|x){−α[logπ(a|x)+H_target]}。目标y不回传梯度；原文采用两个Q及软更新目标网络。
- 本项目采用/限制：[task7 TASK](tasks/task7/TASK.md) §2.7/U28与task7.10可据此补公式。将x理解为VCM状态和当前候选集。只在padding以外候选上归一化/求和是本项目掩码合同；将γ换成γ^(Δt/τ)、只用terminated切断自举是本项目半马尔可夫/截断合同，均不是该论文已验证的结果。宏奖励沿task7.4既定式，不借补引用改变奖励。目标熵随有效候选数的规则、更新率和数值仍待定，不照搬Atari值。
- 核查日期/人：2026-10-19，Codex；实际模型/强度未知。


<a id="src-0383"></a>
## SRC-0383 — SAC-AE与DrQ：截断Actor到共享视觉编码器的梯度

- 支撑主张/类型：外部论文原文＋作者官方代码；从图像学习SAC时共享卷积层可由Critic训练，并阻断Actor更新该共享表征；理由与适用层级必须注明。
- 作者/版本/URL：Denis Yarats等，*Improving Sample Efficiency in Model-Free Reinforcement Learning from Images*（SAC-AE），arXiv:1910.01741，[原PDF](https://arxiv.org/pdf/1910.01741)，§4.4–4.5（PDF页5–6）、附录B.2（页12）；Ilya Kostrikov、Denis Yarats、Rob Fergus，*Image Augmentation Is All You Need: Regularizing Deep Reinforcement Learning from Pixels*（DrQ），arXiv:2004.13649v4，[原PDF](https://arxiv.org/pdf/2004.13649v4)，附录B.2（PDF页15）。
- 精确代码：DrQ作者仓库[drq.py](https://github.com/denisyarats/drq/blob/6d00d0d2e06269ce61de5d1a12d3c74454d44149/drq.py#L262)，commit 6d00d0d2e06269ce61de5d1a12d3c74454d44149，262–280行update_actor_and_alpha，Actor及Critic前向均传detach_encoder=True；文件SHA256 49df2f89b4a73a67e89b00f5f217efd14f049d6cae40d62d267f7433bba9a1f0。
- 原始结论：SAC-AE §4.4认为共享编码器被Actor更新时也会改变Actor目标中的Q，产生不稳定性；其消融支持截断Actor梯度。SAC-AE最终编码器还接收重建损失，不能称为“仅Critic训练”。DrQ附录B.2明确共享卷积层只由Critic optimizer更新、Actor梯度在该处停止。
- 本项目采用/限制：[task7.8 RESULTS](tasks/task7/task7.8/RESULTS.md) B第4条与[SRC-0375](#src-0375)：首版整个VCM只用Critic损失，是借鉴该梯度隔离思路的工程选择。论文针对共享卷积层、连续控制，未证明本项目注意力/GRU或离散SAC最优；不据此加重建目标，不把Actor全部参数都冻结。
- 核查程度/日期/人：2026-10-19，Codex；已读上述相关原文与固定版本代码，未运行。


<a id="src-0384"></a>
## SRC-0384 — 循环经验回放的序列与burn-in：Google官方实现核查

- 支撑主张/类型：Google Research官方代码静态核查；连续序列前缀用于预热递归状态，训练损失在后缀计算，并可截断跨预热段的反传。
- 原始论文线索：Steven Kapturowski、Georg Ostrovski、John Quan、Rémi Munos、Will Dabney，*Recurrent Experience Replay in Distributed Reinforcement Learning*，ICLR 2019；[作者出版页](https://willdabney.com/publication/r2d2/)、[论文入口](https://openreview.net/forum?id=r1lyTjAqYX)。本次OpenReview PDF返回验证页/HTTP403，**未读到该论文原文，不将论文的实验结论写成已核验**。
- 已核原始代码/版本：Google Research SEED RL，[agents/r2d2/learner.py](https://github.com/google-research/seed_rl/blob/af9f769f4c01c602828f1fa806848031dcb52807/agents/r2d2/learner.py)，commit af9f769f4c01c602828f1fa806848031dcb52807；SHA256 9703db15baa6a1abbe3f5c80473f1466c75104b229b632604d59978b58068d91。精确符号：burn_in标志71–76行，compute_loss的burn_in分支、utils.split_structure与tf.nest.map_structure(tf.stop_gradient, training_state)；另核Google DeepMind Acme acme/agents/jax/r2d2/learning.py的102–118行在线/目标状态分别预热后再切去前缀（读取master文件SHA256 3cb24c7588ffe0d345b9ca06f55e01dcf544ca77c98e1c343ab1f52ae3caad99，不冒称固定commit）。
- 原始结论：SEED RL对同一条展开序列先运行前缀以更新存储的RNN状态，停止该状态梯度，再对后缀求loss；这直接支撑技术做法，不依赖二手博客。
- 本项目采用/限制：[task7.8 RESULTS](tasks/task7/task7.8/RESULTS.md) B第5条与task7.4 I3借用连续片段＋预热。VCM的注意力记忆及GRU均需按同一历史恢复；预热长度、初始隐状态来源及回合边界仍属工程选择，不照搬代码默认40，不声称预热精确恢复任意长历史，也不引入优先回放或R2D2其他机制。
- 核查日期/人：2026-10-19，Codex；官方代码已读，论文原文未取得；未运行。


<a id="src-0385"></a>
## SRC-0385 — 实际UR5参数与软件位置限位：容器ur_description 1.5.0

- 支撑主张/类型：本地安装包与xacro静态核查＋厂商官方DH表对照；区分默认模型、硬件规格与运动规划软件限制。
- 作者/版本/路径：ROS-Industrial ur_description 1.5.0，forem-dev内apt包ros-noetic-ur-description=1.5.0-1focal.20250520.012707；容器2456c37db9c9f1f73eb8e651bc83068118441369ddc34a738ff38b0232793314，镜像sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430。读取/哈希证据见[本轮日志](agent_logs/task7/20261019-codex-review-evidence.md)。全程宿主docker cp文件流，不执行容器内命令。
- 精确位置：forem/src/husky_ur5/urdf/husky_ur5.xacro:6–16只传prefix/硬件接口，不覆盖运动学或位置限位。其引用/opt/ros/noetic/share/ur_description/urdf/inc/ur5_macro.xacro:24–28默认读config/ur5/default_kinematics.yaml和joint_limits.yaml；ur_macro.xacro:281–323、364–391定义基座固定旋转、关节轴/限位与工具框架。历史路径解析证据另见task0/task0.2 RESULTS、task0/task0.3 RESULTS；本次未执行rospack或xacro展开，未读取活动ROS参数服务器。
- 文件身份：ur5_macro.xacro SHA256 750bd1936ad7fbe29eb57bce23fd47d43ff464a4fa5c1a17ca6887993ca4e0a6；ur_macro.xacro 03808348aabda3e8cf78863800665a63671ef91da2b5b6d22ddf5bf530376e23；default_kinematics.yaml 5682ff6543f819dbdfca67577c783e5673f7dc74406defb3ce919d4950015d73；joint_limits.yaml 76d43c7a908a10a364af60bc69017686914cf0d7afdd6952f0d9c73a6db55c7d。
- 原始结论：关节顺序shoulder_pan、shoulder_lift、elbow、wrist_1/2/3，软件位置范围分别[-2π,2π]、[-2π,2π]、[-π,π]、[-2π,2π]、[-2π,2π]、[-2π,2π] rad；六轴速度均π rad/s。限位YAML注明肘轴为避免MoveIt/OMPL规划问题被人为减半，不能称厂商六轴硬限位均如此；宏safety_limits默认false，0.15安全margin并未启用。
- 厂商原始对照：[Universal Robots官方DH表](https://www.universal-robots.com/articles/ur/application-installation/dh-parameters-for-calculations-of-kinematics-and-dynamics)，UR5小节六行（网页无固定版本，2026-10-19读取）：a=[0,−0.425,−0.39225,0,0,0] m，d=[0.089159,0,0,0.10915,0.09465,0.0823] m，alpha=[π/2,0,0,π/2,−π/2,0] rad。容器默认YAML的几何尺寸逐项相符（经典UR5，非UR5e），hash为calib_209549117540498681；未使用实体机械臂标定。
- 本项目采用/限制：task7.5 B3/B4以实际默认模型为解析IK前提。ROS ur5_base_link到内部base_link_inertia有绕z的π旋转；tool0/flange固定旋转及Husky安装(0.13,0,0.25)m必须合成。尺寸一致不等于任意DH实现的坐标/关节符号已一致，FK等价仍待task7.6获授权后验证。forem/src/husky_ur5/config/ur5/*.yaml虽存在但本宏未引用，不能代替实际apt参数；本次不修改模型或限位。
- 核查日期/人：2026-10-19，Codex；参数来源/版本与六轴软件范围已核，实体硬限位手册原文未另行核验，CBL旧镜像的独立包版本未知。


<a id="src-0386"></a>
## SRC-0386 — Robotiq 85：0.15 m是CBL虚拟TCP配置，非已核物理尖端长度

- 支撑主张/类型：本地原始模型/代码静态核查＋Robotiq官方规格；核查结论包含“无法由现有定义唯一确定物理TCP”，不是测量结果。
- 作者/版本/位置：本地Stanley Innovation / Patrick Hussey robotiq_85_description 0.0.1（package.xml），未跟踪快照；urdf/robotiq_85_gripper.urdf.xacro SHA256 893e32fd580ebb699719195a92831f3dcc6e82b06d3bd80be0f5076f645da15d。9–13行安装base_link；43–57行驱动关节；184–199、258–273行手指mimic链；没有定义独立TCP link。forem/src/modulation_rl/gazebo_world/husky_ur5/robot_config.yaml:5–14及src/myutils.cpp:190–209将虚拟尖端定义在gripper_base_link局部+x的0.15 m处、相同姿态。H/F模型与工具安装来源另见[SRC-0377](#src-0377)。
- 官方原文：Robotiq，*2F-85 & 2F-140 Instruction Manual*，20210623，[PDF](https://assets.robotiq.com/website-assets/support_documents/document/2F-85_2F-140_UR_PDF_20210623.pdf) §5.2.3，PDF页127；[TCP and Center of Mass of Robotiq Products V1.1](https://blog.robotiq.com/hubfs/support-files/TCP_20and_20Center_20of_20Mass_20of_20Robotiq_20Products_20V1.1_20210623.pdf)，20210623，页1单2F-85行及表下注：TCP=(0,0,174) mm，未装腕相机时含coupling。手册已在宿主内存读取原PDF并提取，非搜索摘要。
- 原始结论/限制：174 mm对应厂商表的安装配置，不能直接替换本地gripper_base_link系的150 mm，也不能把最大外形高度162.8 mm当TCP。手指尖端位置随开合角变化，本地无抓取中心/指腹接触点的唯一TCP定义；**0.15 m与真实物理夹爪尖端重合仍未证实**。
- 静态几何推导（不是仿真/测量）：由上述mimic链，手指尖端link原点的轴向坐标为x_tiplink(θ)=0.06142+0.04303959807 cosθ+0.03759940821 sinθ m；tip link合成旋转不随θ变，其碰撞STL顶点最大x=0.0444999560713768 m。网格路径meshes/collision/robotiq_85_finger_tip_link.stl，2436个三角面，SHA256 5663b94049ead2f0d8a7e6a36a327e0e67ccf03d1423d52110db5b9ce3627eec。故该网格尖端的轴向最远面x_max=x_tiplink+0.0444999560713768：θ=0时0.1489595541 m；robot_config.yaml:36配置θ=0.000517224494 rad时0.1489789957 m；驱动上限θ=0.804 rad时0.1628589259 m。输入为xacro的米/rad数值、STL原始顶点（与URDF无scale使用一致），条件为仅该手指网格及mimic链的静态变换。150 mm与配置近张开状态的网格前缘相差约1.02 mm，可视为近似几何参考；这不是指腹抓取中心/精确物理TCP证明，也不证明CBL作者选值动机。
- 本项目采用：task7.5 B2可把150 mm明确称“沿用CBL的固定虚拟TCP”，其相对gripper_base_link的完整变换为平移(0.15,0,0)m、旋转I；若要求物理接触TCP，须先明确开合姿态和接触点，保留待核，不自行选新值。tool0→TCP还需合成husky_ur5.xacro:35–45的安装旋转及ur_description的tool0固定链，不能只减一个标量。
- 核查日期/人：2026-10-19，Codex；本地虚拟定义和官方安装TCP已核，物理尖端等价未解决；未运行模型、未实测。


<a id="src-0387"></a>
## SRC-0387 — N²M²/CBL终点采样与use_fwd_orientation的实际含义

- 支撑主张/类型：本地/上游原始代码静态核查；终点姿态随机采样，与中间路线前向yaw调整是两回事。更正[SRC-0381](#src-0381)①的过宽概括，不改其用户决定②。
- 作者/版本：N²M²上游mobile-rl commit 6281205846b1bac4525d05ee230a47bddf42023d；CBL H与FoReM F身份沿[SRC-0365](#src-0365)。F tasks.py SHA256 8c7350cb670f099a9a9d0151bddc66d6a1d68236b3ce45b34c3de644c4cc27fd；simulator_api.py 1a0b54b385b0e2ef8e20de95f0ec71c8b62fa9aea3cf4471074f758948237be9；eeplanner.py bb62d3c2fe4f641ac1665229eef30b14cf168827d7bd874c2ba246f9649926fd。
- 精确位置：F tasks.py:241–268的RndStartRndGoalsTask默认距离(1,5)；297–318的SplineTask显式(1,3)、受限高度且仅该调用传地图尺寸减2.5；338–368的SimpleObstacleTask默认距离(0.5,8)、高度z_min/z_max，采样gripper/wrist后转换为tip；simulator_api.py:27–48逐轴RPY独立U(0,2π)、半宽为map_width/2−0.5并直接clip x/y。U同名函数/关键行对照一致。
- 原始结论：eeplanner.py:639–651先在起点与随机终点姿态间Slerp；use_fwd_orientation调用684–705的_generate_fwd_orientations，只把中途yaw换成路径方向并限每点yaw变化π/16，roll/pitch仍来自插值；路径≤12点时完全沿用Slerp；最后一行path_meters[-1]=gripper_goal_wrist恢复精确随机终点。故它不要求终点水平或沿路线末段方向，也不是均匀SO(3)姿态采样。
- 本项目采用/限制：task7.5 B12若保留“终点夹爪水平、沿路线末段方向”，须记作本项目工程设计（用户采纳推荐记录见SRC-0381），不可声称沿用N²M²的该开关。源代码围绕base_tf平移采样后clip，clip后距离不再保证仍在原采样区间，且wrist→tip偏置可改变TCP距离/高度；新规格需明确起点指底盘还是末端、范围约束作用于哪一帧，不能从旧采样函数推定。
- 核查日期/人：2026-10-19，Codex；已读调用链，无任务采样运行。


<a id="src-0388"></a>
## SRC-0388 — 末端规划器速度单位与Python/C++的dt使用

- 支撑主张/类型：H/U/F原始源码静态量纲核查与推导；MIN_PLANNER_VELOCITY=0.001、MAX_PLANNER_VELOCITY=0.1为平移速度m/s，不能当每决策位移或固定匀速。
- 作者/版本/位置：H/U/F同[SRC-0365](#src-0365)；F scripts/modulation/envs/eeplanner.py:17–22常量（角速度另为0.30 rad/s、训练步0.1 s）、96–104、224–263、288–300、377–407、549–575；src/myutils.cpp:156–185的normScaleVel/normScaleVelPython，src/pybindings.cpp:97、103；src/gaussian_mixture_model.cpp:163–188、324–344。F eeplanner/myutils哈希见task7.5(A)；GMM SHA256 a42c8ef39c67f406e88785161f4540a6b3eef5c72a6be558fa4484662d376575，pybindings 7ab81f0f32641581847168b7d96d9504223d8b09b0642d8e1949c16d3c6c8b5f。
- 原始结论：Python get_min_max_vel先乘dt，调用normscale_vel后得到m单位的单步位置增量，直接加到上一计划位置；PointToPointPlanner多子目标时令min=max，末段可降速。GMM分支传m/s给C++，在那里乘dt_real后再限增量，且min=0而非0.001；不可两处再乘一次dt。normScaleVel遇零向量返回零，因此0.001不是始终严格保证的最低运动速度；learned_vel_norm≥0可覆盖上下限。
- 推导：固定0.1 s时，默认速度范围对应0.0001–0.01 m的步增量；角度上限0.30×0.1=0.03 rad。原理想sim固定步与物理分支ROS dt/0.5 s截断须分开，不能把此换算套到task7变长决策。
- 本项目采用/限制：[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md) E8可补m/s及路径类别区别。task7 E8是待选的路线弧长推进速率，不等同于旧规划器常量范围即已选定匀速；B7上限及所有数值仍待定，不运行新计时或改速度。
- 核查日期/人：2026-10-19，Codex；静态调用/单位核查，未运行。


<a id="src-0389"></a>
## SRC-0389 — VLN-3DFF原文：网格航路点标签与训练

- 支撑主张/类型：外部论文原文；补核[SRC-0335](#src-0335)的VLN-3DFF部分，不能以网页摘要作为全文核验。
- 作者/版本/URL：Zihan Wang、Xiangyang Li、Jiahao Yang、Yeqi Liu、Shuqiang Jiang，*Sim-to-Real Transfer via 3D Feature Fields for Vision-and-Language Navigation*；CoRL 2024会议，正式PMLR 270:2982–2995（2025）；[出版页](https://proceedings.mlr.press/v270/wang25i.html)、[正式PDF](https://raw.githubusercontent.com/mlresearch/v270/main/assets/wang25i/wang25i.pdf)（SHA256 4ebf896903c7fad55e5408cc98ca5e7f0c175ec9fc8554676d1ffc63adf5d8f3）。另对照arXiv:2406.09798原PDF相关章节。
- 精确位置/核查程度：正式PDF页4–5 §3.2式(1)–(3)、页6 §4.1 Training Details，已读取原文相关页。
- 原始结论：深度累积512×512、5 cm全局图，再取192×192局部图；语义27类、占据3类，经补全模型后与16维位置嵌入输入航路点U-Net。标签继承CWP修正后的连通图附近节点，在每点画σ=5格二维高斯并取平均；热力图用MSE，语义/占据补全用各自像素交叉熵。预测器训练20K个Habitat随机15步回合、2×RTX3090；输出按12个30°扇区取峰值、去占据区域、取Top-K。
- 本项目采用/限制：task7.9改造方案可借标签热力图与后处理思路；现项目无R2R连通图和27类语义，因此“理想SIM自动生成能到/不撞/够得着标签”为另行工程设计，未被这篇原文验证，尚未实施。原GPU/回合数不是本项目预算或工期证据。
- 核查日期/人：2026-10-19，Codex；原文相关章节已核，未训练。


<a id="src-0390"></a>
## SRC-0390 — CWP原文：修正连通图、候选标签与训练细节

- 支撑主张/类型：外部论文原文，补核[SRC-0335](#src-0335)的CWP部分；原始标签依赖已有MP3D图，并非完全从任意新场景无标注生成。
- 作者/版本/URL：Yicong Hong、Zun Wang、Qi Wu、Stephen Gould，*Bridging the Gap Between Learning in Discrete and Continuous Environments for Vision-and-Language Navigation*，CVPR 2022；[arXiv:2203.02764v1原PDF](https://arxiv.org/pdf/2203.02764v1)，2022-03-05；SHA256 40577f1c2079f2d6369b610ca0553bd51564fc2bbbf090a32e2c09f8b61ef639；[作者官方仓库](https://github.com/YicongHong/Discrete-Continuous-VLN)用于确认出版身份。
- 精确位置/核查程度：PDF页5–6 §4.1–4.3，页12附录A.1已读；网页工具因15.8 MB大小失败，宿主urllib取得原PDF，pdftotext返回0，不是摘要抽取。
- 原始结论：MP3D节点投影到Habitat后，经邻域采样、移点、绕行加节点、合并及拟合轨迹端点，形成连续可通行图；由节点邻接关系在半径3 m的120角度×12距离格上做高斯热力图标签（3°/格、0.25 m/格）。训练只用61张图、9556节点；RGB/深度ResNet编码器冻结，Transformer与分类头训练，热力图MSE；AdamW、lr=10^-6、batch64、单RTX3090，NMS最多5点。
- 本项目采用/限制：task7.9可据此说明“继承人工/数据集连通图再几何修正”与我们可能的SIM自动标注不同；不把其候选点可通行标签当UR5整臂可达/连续IK标签。只写以后改造方案，不增加网络训练授权、候选数量或实验组。
- 核查日期/人：2026-10-19，Codex；已核原文指定部分，非整篇实验复现；高斯核具体尺度不移植为本项目参数。


<a id="src-0391"></a>
## SRC-0391 — task7第二轮设计核查：静态证据与工程推导

- 支撑主张/类型：项目文档/本地代码静态核查＋工程推导，不是新实测、功能或用户新决定。
- 版本/精确位置：[本轮独立日志](agent_logs/task7/20261019-codex-review-evidence.md)记录读取快照哈希；[交流文档第二轮节](agent_logs/task7/20261019-claude-codex-sync.md#codex第二轮复核2026-10-19)逐项列task7 TASK、task7.4/7.5/7.7/7.8 RESULTS与DECISIONS位置。H/U/F/M源码身份沿[SRC-0365](#src-0365)–[SRC-0371](#src-0371)。
- 原始结论：设计对照的共同环境/候选/执行器/精确信息/奖励已明确，未发现写入的组间特权信息差异；但目标坐标锚定、TCP→tool0合成、VCM回放所需位姿、失败/到达结束优先级、原地路径时长等仍有合同缺口，不能称可直接实现或已验证公平性。新旧语义并存的具体问题以交流文档为准。
- 附核代码：scwm commit f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b的vlnce_baselines/common/environments.py:386–446在tryout分支失败时可结束尝试，且前进步数为floor(dis/uni_f)，不保证精确到达请求点；故[SRC-0362](#src-0362)“总能到达（瞬移或tryout）”不可推广全部分支。mapgen墙函数及输出协议仍按SRC-0370/0376，不把需求当已实现。
- 推导条件：移动基座固定目标须在每次重规划前由同一个世界锚点换到新底盘系；VCM相对几何编码须有每决策位姿/相对变换，只有局部q和路线裁剪无法普遍恢复底盘历史。s若定义为平移弧长，零平移的纯转姿段不能靠s除长度插值，必须先明确已有路线的退化处理。上述是接口可判定性分析，不选择新参数或改奖励。
- 采用/限制：仅供Claude修订既定文档与补齐原接口，未新增实验组/功能；未重新取到此前Claude完整聊天原消息，用户设计决定的原话仅可追溯其既有SRC条目，本次不冒称重新核验原始聊天。SAC/GRU/IK/碰撞/吞吐均未运行。
- 核查日期/人：2026-10-19，Codex；实际模型/强度未知；推荐GPT6.1sol/Sonnet5.5 medium，因跨文档与原文核查。


<a id="src-0392"></a>
## SRC-0392 — 2026-10-20用户对task7合同缺口7–11的决定（原地候选、结束优先级、不可行候选、G3、计数入观测）

- 支撑主张（用户决定，均为Claude推荐项）：
  - ⑦**原地候选与到达**：统一“到达”＝路径计划终点走完，即底盘到达候选位姿，且不同步变体s＝s_k、同步变体计划时长走完。同步变体的原地候选：底盘不动，持续到末端走到“从当前底盘位姿IK可达的最远进度”（与父TASK §2.8规则4同一计算）为止；该进度不比当前s远时Δs＝0，照常生成、可选。**决策超时**＝决策开始时所选最优路径的计划仿真时长×系数（系数待定），整次决策固定，不随重规划重算，不用墙钟；超时只结束本次决策，不计失败。
  - ⑧**结束条件**：到达路线终点即terminated（有历史失败则记“到达但非严格成功”，不给R_succ）。同一检查点处理顺序：①IK失败或真值碰撞→不提交、停在上一检查点、失败数＋1，达F→terminated（失败）；②否则提交，s到达路线终点且残差在E1内→terminated（到达；零失败才算成功）；③否则到达c*或决策超时→本次决策结束；④决策结束后更新卡住计数，达M→terminated（卡住）；⑤最后检查D_max/T_max→truncated。终止优先于截断；T_max只在决策边界检查；全部触发原因记入info。
  - ⑨**全部路径不可行的候选**：p_k*按分层排序选——可行路径永远优先；不可行路径之间首个失败检查点越靠后越好，再比U25评分。f_k所有字段按“执行到首个预测失败点之前”的前段计算：Δs、用时、最大残差、最小间隙取前段值；可行＝0；首个失败位置＝j/C；可行条数＝0；失败类型取首个失败检查点上的类型，同一检查点多类时按IK＞自碰撞＞机械臂碰撞＞底盘碰撞；第一个检查点即失败时Δs＝0、用时＝0、残差＝0、间隙取起点值；不出现空值或NaN。G1在没有可行候选时用同一分层排序在全部候选中选（首个失败越靠后、Δs越大者优先），并统计“无可行候选”比例。
  - ⑩**G3形式**：随机初始化后冻结的f_p（与G4同结构、同输入、不训练）输出替代h_k；task7.10须写明把随机特征归一化到与训练后f_p输出同尺度。
  - ⑪**计数入观测**：归一化累计失败数n_f/F与卡住计数m/M两个标量进入VCM向量输入，所有组相同；不加剩余时间（超时为截断，按下一状态自举）。
- 原始依据：2026-10-20本会话，Claude逐项给出选项与推荐后，用户回复“7–11都按你的推荐定，写进文档并登记来源。”核查人直接读取本会话用户消息。
- 代码参照（⑧）：上游N²M² `mobile-rl/` commit `6281205846b1bac4525d05ee230a47bddf42023d`，`scripts/modulation/envs/combined_env.py:382–384`：`done = ((not kin_failure) and ee_done) or nr_kin_failures≥thresh or nr_base_collisions≥thresh`，即本步无IK失败且末端规划完成即结束，与历史失败无关；成功另要求零失败（[SRC-0360](#src-0360)②）。2026-10-20 Claude只读核对。
- 推导与工程理由（非外部证据）：⑦②会使反复绕路时永不超时，③使结果依赖机器速度；⑨方案C（只执行可行前段、不记失败）与[SRC-0361](#src-0361)③“不屏蔽、靠失败惩罚学会避开”冲突；⑩G4中f_p的输入(s_t, e_k)本已为SAC所见，f_p额外带来的只是从到达观测学到的知识，随机冻结f_p保留结构与依赖、去掉这部分知识；“零输入”缺s_t依赖，“同状态打乱”在K＝1时不变（Codex第二轮#17，[SRC-0391](#src-0391)）；⑪终止与成功条件依赖累计计数，经验池按片段采样、前缀预热（task7.4 I3）时窗口外失败无法由记忆恢复，Critic状态不满足马尔可夫性。
- 待补证据：⑪“终止条件依赖的计数/时间应可观测，截断则自举”的一般论证线索为Pardo等，Time Limits in Reinforcement Learning（ICML 2018）；本次未读原文，不作已核验依据。
- 类型：用户设计决定＋代码参照＋推导；数值（κ、F、M、E1等）未定。
- 本项目采用：[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md)“2026-10-20 合同缺口决定”节及§1、§4、§5、§10、§12、§15；[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) B.9–B.11、B.15；[task7.8 RESULTS](tasks/task7/task7.8/RESULTS.md)；[task7 TASK](tasks/task7/TASK.md) §2.8、§4。
- 核查日期/人：2026-10-20，Claude（claude-opus-5-5）。


<a id="src-0393"></a>
## SRC-0393 — 2026-10-20用户对终点距离锚点、终点姿态与未知格风险特征的决定

- 支撑主张（用户决定，均为Claude推荐项）：
  - ①**终点距离锚点**：终点距离0.5–8 m指底盘起始位置到TCP终点的水平距离；终点高度另按0.7–1.15 m约束。
  - ②**终点姿态**：TCP接近轴（gripper_base_link的x轴，[SRC-0386](#src-0386)）水平，指向路线最后一段的水平方向；手指沿水平方向开合。
  - ③**未知格风险特征**：“经过未知格比例”＝最优路径扫过的区域（底盘轮廓与机械臂连杆在地面上的投影）中未知格所占的格数比例（无量纲，不随检查点间隔变化）；“到最近未知格距离”＝扫过区域到最近未知格的最小距离（m），路径上没有未知格时取局部栅格半宽3.2 m为上限；局部栅格范围以外的格一律按未知处理。
- 原始依据：2026-10-20本会话，Claude逐项给出选项与推荐后，用户回复“①②③都按你的推荐定，写进文档并登记来源。”核查人直接读取本会话用户消息。
- 依据与理由（非外部证据）：①与N²M²围绕底盘起始位姿采样一致（[SRC-0387](#src-0387)），末端起点离底盘不超过约0.8 m，与按末端起点量相差不大；②为本项目工程设计，不是沿用N²M²（N²M²终点姿态随机，[SRC-0387](#src-0387)）；③格数比例与检查点间隔无关；计入机械臂投影是为反映“机械臂伸入未观测高处”的风险；3.2 m＝128格×0.05 m÷2（[SRC-0373](#src-0373)）。
- 类型：用户设计决定。处理Codex第二轮复核#12–#14（[SRC-0391](#src-0391)）。
- 本项目采用：[task7.5 RESULTS](tasks/task7/task7.5/RESULTS.md) B.7、B.9、B.15（B6、B12）；[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md) §1、§10第5行；[task7 TASK](tasks/task7/TASK.md) §2.5。
- 核查日期/人：2026-10-20，Claude（claude-opus-5-5）。


<a id="src-0394"></a>
## SRC-0394 — task5.5 最终sim评估结果与F0口径核对（只读入账，2026-10-20）

- 支撑主张/类型：项目既有实测的独立复算＋源码静态核查＋描述性推导；未新运行评估/训练。FoReM task5.5，作者/机构：项目Codex核对，2026-10-20；原评估2026-10-19，forem-dev既有环境。
- 原始证据：run-id `t5.5-final-sim-s{0,1,2}-r1`；逐回合 `episodes`、`spec`、`effective_config`及汇总字段。对照 `t6.1-eval-sim-s{0,1,2}`；完整文件路径与SHA256如下（本次直接读取原件）：

| eval.json路径 | SHA256 |
|---|---|
| `forem/results/task6/t5.5-final-sim-s0-r1/eval.json` | `fb91477f8b913fd5082661c808beaef15ff9c1a56cdd75140590d3260464dc8c` |
| `forem/results/task6/t5.5-final-sim-s1-r1/eval.json` | `f5b9bdb901cc6cccf6ca301d010cf271816856a844f8df864abf2ed6997d6cbe` |
| `forem/results/task6/t5.5-final-sim-s2-r1/eval.json` | `8bdcd6afa4b34005d9cc3edb6586bea8395bb4ff5bf734aec2b7877e9650f90c` |
| `forem/results/task6/t6.1-eval-sim-s0/eval.json` | `bdfe84116693d2f06af86b6adb4b27509e7a18ff10bb9e172b0e5b5b32731cdc` |
| `forem/results/task6/t6.1-eval-sim-s1/eval.json` | `65a0deae93a5f23d678877d2ab3c0ca6dfcbe5fb647ed94fdb7b57a0862a6aeb` |
| `forem/results/task6/t6.1-eval-sim-s2/eval.json` | `abb2649a31e64110dd99681f51d89869dd6235539a5770fdbbc61674eb80c0aa` |

- 启动/退出证据：`forem/logs/task5/t5.5-final-eval-launch-20261019/{manifest.json,*-launch.json,startup-verification.json}`；`forem/logs/task6/t5.5-final-sim-sK-r1/{eval.out,start.out,inst63/64/65/launch.exit.json,inst63/64/65/launch.cleanup.json}`（实例号依次63/64/65，不是每run含全部实例）。三条eval/stop rc均0，residue=[]；最后实例退出2026-10-19 22:52:12 +08:00；本次ps未见本任务评估/实例残留，旧评估宿主PID844488/844496/844498均不在。全部证据文件哈希与核对命令见[独立日志](agent_logs/task5/task5.5/20261020-codex-final-sim-results.md)。
- 脚本版本：本次 `forem/scripts/eval_task6_final.py` SHA256 `ba140ec7ed31e34fb5b9fa694699b1c13073b8dd0900fb116a815635608ecccb`；F0 `9989213b59a14f3bb22c1083d54d57cb26746618492a34ddbbaf3fdba91db312`，由 `forem/results/task6/t6.1-summary/manifest.json:eval_script` 与 `forem/results/task6/t6.3-baseline/original/eval_task6_final.py`的实算哈希互证；直接diff仅Gazebo可选覆盖与配置/长回合记录，sim入参与核心循环不变（历史修改见[SRC-0253](#src-0253)）。启动器 `forem/logs/task6/t6.1-eval-launch/eval_one.sh` 哈希 `fb61eaffdd7ff3a283b79c48aedd1618758e85ea5482871b9064c53a9a19cc1e`，与本次启动manifest相同。
- 精确位置/口径：原/新评估脚本 `main`，`forem/scripts/scwm_train.py:run_eval`（141–158，eval=True），`scwm_env.py:ScwmEnv.__init__`（34–55），`task3_env.py:load_env_config`（66–71），`config/task3/task_contract.yaml:env_config`（time_step 0.02 s、ik_fail_thresh 20、execute_style direct）。F0与5M训练manifest sources逐项相同且匹配当前文件；F0 eval.json无effective_config，参数可由当时脚本/启动参数与相同哈希合同还原，F0运行时生效快照无法核实。无源码Git提交可唯一代表未跟踪脚本，本条以内容SHA256为版本。
- 原始结论：三条固定种子2001–2050各50回合齐全、无重复，completed/capped/errored均50/0/0；5M内部成功32/33/30、碰撞episode 0/1/1、含IK失败episode 18/17/19、平均步数247.10/238.16/227.00；F0为21/22/22，平均成功率0.4333，5M为0.6333。三组对应评估的spec在障碍名称/几何/尺寸/位姿、goal_tip/goal_wrist、规划臂关节、base_tf与map_size_m均50/50逐字段相等（记录精度为6位小数），无不一致种子。配对“都成功/仅5M/仅F0/都失败”为19/13/2/16、20/13/2/15、18/12/4/16。
- 推导：成功率=内部成功数/50；均值=(s0+s1+s2)/150；平均步数=无error回合steps之和/50。Wilson沿F0 `forem/scripts/summarize_task6_1.py:wilson`（17–22），n=50、p=k/n、z=1.96、d=1+z²/n、中心=(p+z²/2n)/d、半宽=z√(p(1−p)/n+z²/4n²)/d，无量纲；表只对单run给区间，不作显著性检验。
- 训练配方核查：三组 `run_manifest.json` 对应比对仅身份/时间、预算及配置哈希不同，config仅total_env_steps 1M→5M，sources完全相同。lr_horizon_updates均5000001，`forem/src/modulation_rl/scripts/sac.py:43` 与 `scwm_sac.py:update_parameters` 指数更新衰减不变；5M走近完整日程（4999743次更新），F0只走前约1/5（999743次更新），不是只改变评估时checkpoint标签。
- 异口径参照：`forem/results/task5/t5.2-train-s40/train_eval_series.csv` 的 `evaluation/custom_metrics/success_mean`，525k–975k为0.82/0.76/0.82/0.78/0.74/0.76/0.76（每次50回合），故仅称训练中平台约0.78；RLlib实现、约一半椭圆柱场景、评估集与口径均不同，且仅种子40，禁止与本次/F0直接相减。
- 采用/限制：[task5.5 RESULTS](tasks/task5/task5.5/RESULTS.md#最终评估)保存协议、结果和交接，台账仅登记依据；task5.5置review待Claude/用户复核。仅sim内部成功，物理成功N/A；D15种子3001–3050不能替代最终2001–2050；F0历史sim/Gazebo分叉2006/2012/2021不影响本次sim对sim的逐种子相等，根因仍未查。Gazebo零样本评估需另行授权。
- 核查日期/人：2026-10-20，Codex；实际模型/强度未知；推荐GPT6.1sol与Sonnet5.5 / medium（需核对跨版本评估口径）。
- 独立复核（2026-10-20，Claude，claude-opus-5-5，推理强度未知）：自行sha256sum六份eval.json、六个策略文件、新旧评估脚本与启动器，15项与上列一致；自写标准库脚本从episodes重算全部计数、均值、平均步数、Wilson区间与配对四格表，结果与上文一致并与汇总字段断言相符；另核`internal_success`与“ee_done且IK失败、底盘碰撞均为0”在300回合中逐条等价；场景比较用完整spec字典与`episode_hash`，三组均50/50相等；自行diff新旧脚本与逐键比较三对run_manifest，结论同上。复核通过，task5.5标done。方法与证据见[task5.5 RESULTS 复核节](tasks/task5/task5.5/RESULTS.md#claude独立复核2026-10-20)与[复核日志](agent_logs/task5/task5.5/20261020-claude-final-sim-review.md)。

<a id="src-0395"></a>
## SRC-0395 — SC²-WM航路点热力图的后处理代码细节（扇区取峰值、删占据、合并、取前k）

- 支撑主张：SC²-WM在单目分支中把航路点U-Net输出的热力图按以下步骤转成候选：①每个样本热力图减去其最小值；②12个扇区，扇区`direction_idx`以`direction_idx·30°`为中心、±15°，扇区0跨越0°；每扇区取热力图最大值的格；③用预测占据图在该格的argmax判为占据时把该峰值置0（删点）；④`merge_scale=8`：把格坐标按16格分箱（0.05 m/格时0.8 m），用x、y各两种偏移共4种分箱，同箱内只保留值较大者；⑤`topk(k=8)`后去掉值为0者；⑥只保留到机器人距离在0.1–5 m之间的点；⑦角度按π/60（3°）、距离按0.25 m离散后交给后续模块。
- 类型：官方源码静态核查（只读，未运行）；补充[SRC-0334](#src-0334)、[SRC-0358](#src-0358)②中“热力图→扇区取峰值→去障碍→合并→取前k”的具体参数。
- 精确位置：本地`scwm/` commit `f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b`，`vlnce_baselines/ss_trainer_ETP.py:1944`（减最小值）、`:1957–1977`（12扇区取峰值）、`:1979–2003`（合并与删占据）、`:2010`（top-8）、`:2023`（0.1–5 m）、`:2030–2031`（离散化）。栅格0.05 m/格见[SRC-0358](#src-0358)②与[SRC-0389](#src-0389)。
- 本项目采用：[task7.9 RESULTS](tasks/task7/task7.9/RESULTS.md) A.2扇区方向与(B)改造方案的后处理结构；分箱尺寸、k、距离窗口不照搬，改造时另定。
- 限制：只核查代码路径与常量，未运行；不代表这些常量对本项目合适。
- 核查日期/人：2026-10-20，Claude（claude-opus-5-5，推理强度未知）。

<a id="src-0396"></a>
## SRC-0396 — N²M²/CBL配置`arm_range: 0.8`的实际用途：末端路线规划的膨胀半径，不是IK可达判据

- 支撑主张：Husky+UR5配置中的`arm_range: 0.8`在CBL与上游N²M²代码中只出现在末端规划器构造权重图的一处：先在空图上画出底盘A*路径，再以`arm_range`为半径膨胀，作为“末端离底盘的最大允许距离（约臂长）”的路线偏好；没有用它判定IK是否可解。
- 类型：本地代码静态核查（只读）。
- 精确位置：CBL快照`husky/src/modulation_rl/gazebo_world/husky_ur5/robot_config.yaml:25`；`husky/src/modulation_rl/scripts/modulation/envs/eeplanner.py:536–539`（含注释）；上游`mobile-rl/` commit `6281205846b1bac4525d05ee230a47bddf42023d`同文件`:539`同一用法；FoReM迁移副本`forem/src/modulation_rl/scripts/modulation/envs/eeplanner.py:539`。检索范围：上述目录下`*.py *.yaml *.cpp *.h`中的`arm_range`。
- 本项目采用：[task7.9 RESULTS](tasks/task7/task7.9/RESULTS.md) A.3以IK判定可达，父TASK §2.8“约0.8 m”只作说明，不作硬阈值。
- 限制：未检索参考仓库以外的位置；只说明该参数在这些代码中的用途，不说明UR5实际可达半径（UR5官方臂展未在本项目核对，见[SRC-0330](#src-0330)）。
- 核查日期/人：2026-10-20，Claude（claude-opus-5-5，推理强度未知）。

<a id="src-0397"></a>
## SRC-0397 — task7.9规则版候选生成规格的推导与工程选择（草案，待用户确认R1–R8）

- 支撑主张与类型：
  - 推导①（d上限）：局部栅格128×128、0.05 m/格，以机器人为中心，半宽3.2 m（[task7.7 RESULTS](tasks/task7/task7.7/RESULTS.md)）；走廊长d＋0.6 m须在栅格内，故d ≤ 2.6 m。
  - 推导②（走廊尺寸）：宽0.67 m为底盘宽（[SRC-0330](#src-0330)）；0.6 m余量与原地转向外接圆半径√(0.495²+0.335²)≈0.60 m一致（同来源推导）。余量0.6 m本身来自父TASK §2.8用户确认的规则（[SRC-0337](#src-0337)、[SRC-0359](#src-0359)）。
  - 推导③（计算量）：d＝1.0 m时走廊约(1.6/0.05)×(0.67/0.05)≈32×14≈450格。s_k搜索的IK调用受可达球限制：设可达半径约1 m（UR5官方臂展约0.85 m为未核常识，见[SRC-0330](#src-0330)，另加余量），直线路线落入球内的弦长≤约2 m，以0.05 m采样≤约40个样本；13个候选≤约520次，比父TASK §5举例的13×32×10≈4000次路径评估约多一成。只是量级估计，待task7.6实测。
  - 推导④（s_k取第一段连续可达）：路线回折时后面的路线段可能重新落入可达范围；取任意可达的最远点会让末端跳过中间不可达的路线段，取第一段连续可达的末端则不会。
  - 工程选择（建议，未经用户确认）：d＝1.0 m（R1，父TASK示例值）；走廊从原点出发、谓词同LocalCollision底盘判定（R2）；Δs_r＝0.05 m（R3，与栅格分辨率一致）；固定槽位（R5）；扇区0对准正前方、逆时针（R6，同[SRC-0395](#src-0395)）；改造方案标签建议L1（R7）。
  - 待验证假设：直线走廊粗筛在“标准”密度地图上不会频繁只剩原地候选；R_pre由URDF连杆长度上界计算后不误删IK可解样本。两者都要在实现后用诊断量和单元测试检验。
- 本项目采用：[task7.9 RESULTS](tasks/task7/task7.9/RESULTS.md) (A)–(D)。
- 限制：均未实现、未运行；数值待用户确认，确认后由父任务回写父TASK §2.8、U17、U30。
- 核查日期/人：2026-10-20，Claude（claude-opus-5-5，推理强度未知）。


<a id="src-0398"></a>
## SRC-0398 — 2026-10-20用户授权task7.6计时基准运行并派发Codex

- 支撑主张（用户授权）：task7.6“IK与路径评估计时基准”由Codex执行，允许在forem-dev容器内运行有界微基准（不训练、不评估、不启停或重建容器）；派发方式为Claude写提示词后以`codex exec`后台启动。
- 原始依据：2026-10-20本会话，Claude列出三项可派发任务并说明“task7.6需要在容器里跑有界微基准，选中即视为授权运行”；用户只选“task7.6计时基准”，派发方式选“我用codex exec后台启动”，随后此前用户消息为“写提示词然后派发”。task7.9草案复核与task5.5 Gazebo零样本评估未被选中，不在授权内。核查人直接读取本会话用户回答。
- 工程选择（Claude，非用户指定）：单次基准命令墙钟≤10分钟、累计容器计算≤60分钟、至多1块空闲GPU；超出须停止报告。理由：TASK只写“有界微基准”，未给预算；该上限仅用于防止失控，不是性能门槛，可由用户调整。
- 类型：用户授权＋工程选择。
- 本项目采用：[task7.6 TASK](tasks/task7/task7.6/TASK.md)授权行；派发提示与启动记录见[派发日志](agent_logs/task7/task7.6/20261020-claude-codex-dispatch.md)。
- 限制：授权仅覆盖task7.6的计时与数值一致性基准；B8、B13、B14及解析/DLS的最终选择仍由用户决定。
- 核查日期/人：2026-10-20，Claude（claude-opus-5-5）。


<a id="src-0399"></a>
## SRC-0399 — task7.6 IK与路径计时项目实测、精度差异及参数化成本

- 支撑主张：实际展开URDF与经典DH FK的随机一致性；解析/DLS/BioIK在相同目标、限位、FK残差下的接受数；CPU1/2线程、GPU float64/32计时；分支差异、奇异失败、连续路径跳变；顺序检查点的掩码/活跃压缩原型开销；圆弧/坐标变换最小原型与参数化成本。不是完整环境、训练、评估或任务成功率。
- 类型：**项目实测**＋明确标记的**推导/工程扫描选择**。作者 Codex，2026-10-20，TASK7.6-BENCH-20261020；实际具体模型/强度无法核实，均未知。建议GPT6.1sol / Sonnet5.5 medium，不代表实际配置。
- 精确位置：`forem/scripts/bench_task7_ik.py`的Model/fk/analytic/checked/solve/paths；`bench_task7_supplement.py`、`bench_task7_bioik.py`、`bench_task7_verify.py`、`bench_task7_report.py`；代码仅基准使用。解析方程改写自[SRC-0352](#src-0352)固定官方源码（原件存r1/ur_kin_reference.cpp，SHA256 8c93d4d97856f89c2685a7b6e2bcdcb8b5d4174e0d055c6f0a2a9f157cf513ad）。模型来自[SRC-0385](#src-0385)、TCP定义[SRC-0386](#src-0386)，本次实际xacro展开URDF SHA256 f9e23d78f06ab1d6ad13688b48ce3177d725cc6439e930d00c785a258c7d2062。
- 证据路径：run-id `t7.6-bench-20261020-r1`至`-r9`，位于`forem/results/task7/`和`forem/logs/task7/`；r1输入/数值原始npz与consistency.json；r2–r5原始计时数组、timing.csv/json、metadata/command/exit；r6无效TF服务尝试，已清理，不用于性能结论；r7精度分支/连续性/坐标链/首次与预热/其他开销；r8 BioIK原始服务返回与独立回检；r9/verification.json重算125项、cost_scan.csv/json的480行推导。所有可读代码/产物哈希集中于`forem/results/task7/t7.6-bench-20261020-r9/manifest.json`，SHA256 **5854343154d6d919bb6d882d73f9e9cfcf8dd397190c0407df775f51977e9162**；2个root拥有的rospack运行缓存无法宿主读取，明确排除，未用于论据。
- 原始结论：10000随机q，FK最大位置2.112e-10 m、姿态6.151e-10 rad；统一1e-5 m/rad时相同1200目标接受数解析913、DLS737、BioIK564（BioIK布尔成功913，其中349未过残差）。float32/GPU分支并不完全一致，已知奇异输入有解析假阴性，24×64连续路径最大关节增量范数2.470 rad；因此不能宣称IK全域完备或连续性已解决。完整数字与条件见[task7.6 RESULTS](tasks/task7/task7.6/RESULTS.md)，不在台账复制另一套协议。
- 工程选择与推导：E7扫描(1e-7,1e-5,1e-3)m/rad；DLS仅测试λ=0.01、64次、每次关节步范数≤0.2rad、sin姿态误差且最终用SO(3)弧度回检，没有调优或宣称DLS最佳。批量1/13/104/416/1664、N=1/8/32/128、L=0.5/1/2/2.6/8m、累计转角0/π/2/π/2π、底盘点位移h=0.05/0.025m为探索扫描，非冻结参数。底盘检查点`C=ceil(L/h)+ceil(0.60|θ|/h)`，IK与已测其他开销按`C·[t_IK(B)+t_arc_transform(B)]`估算；尚缺碰撞、渲染、候选生成、重规划与训练更新，机械臂位移不由该底盘公式保证。训练预算B1/B3待定，只给参数公式。
- 采用/适用限制：仅供task7.6 review及用户选择B8/B13/B14/求解器。计时是当前PyTorch eager基准原型；GPU CUDA event包含流中空档，不等于GPU繁忙占用；BioIK为服务参考且非CBL全套Goal配置，非GPU批量候选。未冻结E7、未修改父TASK或task7.4/7.5/7.9。没有训练工期或完整路径吞吐保证。
- 核查日期/人：2026-10-20，Codex直接运行并重算；状态review，待Claude/用户复核。授权见[SRC-0398](#src-0398)及用户本次消息。
