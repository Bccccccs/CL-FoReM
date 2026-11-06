# task7.19 — 结果

**2026-10-26执行冻结：paused。** 用户已冻结task7全部后续执行，见[父冻结入口](../TASK.md#2026-10-26-当前冻结入口)。已完成成果与下文历史状态保留；不得依旧授权自动续训、恢复或派发。当前转入task8地图迁移规划。

状态：**正式D10因CUDA OOM中断，0完整轮，待定位/安全恢复；尚无冻结结论**（2026-10-23 14:23复查）。八worker日志均显存不足且现场已无原进程；原始部分数据与claim保留。本次仍为SRC-0916允许的v5同步500k评估，未自动重启，见[SRC-0965](../../../SOURCES.md#src-0965)。下文10:08运行中为历史快照，原实现已复核不等于正式验收通过。

## 运行记录

（尚无。每次执行按run-id追加：执行Agent与实际模型/强度、改动文件、命令、版本、退出码、证据路径、结论与限制。）

### 2026-10-21 G7-1–G7-4设计（Claude起草；**2026-10-21用户四项均按推荐确定，[SRC-0434](../../../SOURCES.md#src-0434)**；下文“建议”均已成为已定）

- 执行：Claude（claude-opus-5-5，推理强度未知），只写文档，未实现、未运行。记录见[日志](../../../agent_logs/task7/task7.19/20261021-claude-g7-design.md)。推导与工程理由登记[SRC-0436](../../../SOURCES.md#src-0436)。
- 不改的已定前提：B.9（路径表示、f_k、纯函数、“被评分即执行”）、B.10/B11（失败只按IK与真值碰撞）、⑦⑧⑨（[SRC-0392](../../../SOURCES.md#src-0392)）、D8 0.05 s子步与B.R的IK合同（N1）、评估只用LocalCollision与局部栅格、执行用TruthCollision、|v|≤0.3 m/s、|ω|≤1.0 rad/s（B.3）、D10门槛本身（[SRC-0431](../../../SOURCES.md#src-0431)）。

#### G7-1 路径族与N（建议）

- 原语：分段常值(v, ω)；直行用|v|＝0.3 m/s、原地转用|ω|＝1.0 rad/s（B.3上限，与下层SAC可用的最快速度相同）。每段时长向上取整为0.05 s的整数倍、按“距离÷取整后时长”降速，使段界落在子步上且终点精确。目标为决策开始时锚定的世界系c*（B.8）。
- 底盘路径7条：
  - P1 先转后直再转（前进）：原地转向朝向目标→直行→原地转到候选朝向。父TASK §2.9要求必含，与SC²-WM“先转向再前进”同思路。
  - P2 同P1但倒车：转到背向目标→倒车直行→转到候选朝向。理由：12扇区中后方扇区若只能前进，须先原地转约180°。
  - P3 单圆弧＋末端转：与当前朝向相切、过目标点的唯一圆弧，再原地转到候选朝向；目标正后方等退化情形不生成（掩码）。
  - P4–P7 侧向绕行：在起点→目标连线中点沿法向偏移o∈{−0.5, −0.25, +0.25, +0.5} m取途经点，按P1方式先到途经点（不做末端转）再到目标。
- 末端推进：
  - 不同步（B7已定两种都含）：S-a联动——s在底盘运动全程匀速推进，速率＝(s_k−s)/T_base，超过0.3 m/s时封顶，底盘到位后以0.3 m/s补完；S-b先到位——底盘运动中s不变，到位后以0.1 m/s推进到s_k。故N＝7×2＝14。
  - 同步：末端从决策开始按恒速0.1 m/s推进（CBL规划器默认上限[SRC-0388](../../../SOURCES.md#src-0388)，与G3预览速度相同），各路径只差底盘运动，N＝7。
  - 原地候选：只有“底盘不动、s推进”一条（不同步0.1 m/s推进到s_k；同步按⑦），其余槽位掩码。
- 退化或不生成的路径用掩码，N固定以便批量；被掩码路径永不被选。
- 成本参照：task7.6 §6在K＝13、C＝58时GPU64已测部分N＝8为0.365 s、N＝32为0.367 s（[SRC-0399](../../../SOURCES.md#src-0399)），N＝14不显著增加GPU已测部分；完整成本待实现后测。
- 备选：(a) 最小族，只P1（每候选1条，不同步2条）；(b) 更大族（按曲率/偏移网格采样数十条）。

#### G7-2 路径评分（建议：分层排序，不设权重）

1. 整条计划可行（局部栅格碰撞与IK预测均无失败）；
2. 最小间隙≥0.10 m（2格）；
3. 计划时长T_plan更短；
4. 最大TCP位置残差更小；
5. 固定序号（P1<…<P7，S-a<S-b）。
- 全部不可行时按⑨：首个失败检查点越靠后越好，再按2–5。
- 未知格风险不进评分（B6：未知按空闲；风险只作f_k特征交上层）。
- 理由：U25原写“权重为工程选择”，分层排序不需要无依据的权重，且与⑨的分层规则同一形式、可复现。备选：加权和（时长、间隙、残差各一权重，需另定3个数）。

#### G7-3 重规划段长与超时（建议）

- 每执行0.5 s（5个动作步、10个子步）重规划一次：从当前状态对同一世界系c*重新生成G7-1的路径族，用最新累积栅格（上一动作步末渲染）评估，按G7-2选优，执行其前0.5 s；剩余计划不足0.5 s时执行到底。“被评分即执行”：每段实际执行的10个子步与刚评分路径的前10个子步逐点相同（B.14 #2）。同步变体末端时间照常连续推进，重规划只换底盘路径。
- 理由：0.5 s内底盘最多走0.15 m（3格）；每次重规划只评估1个候选×N条，远小于决策时K×N；1 m候选计划时长约3.3 s（纯直行）到约10 s（含两次大角度原地转），即约7–20次重规划。备选：0.1 s（每次渲染都重规划，最灵敏、成本约5倍）；1.0 s。
- **超时（实现所需，原B10系数κ未定）**：建议G7直接用主方案D7的T_seg＝3·T_ideal＋2 s（推演与执行同一上限），取代“计划时长×κ”，使D10配对比较时两种执行器时限相同。这改变⑦中G7超时的计算方式，须用户确认。
- 到达仍按⑦（计划走完；理想执行下等于精确到达，落在D5容差内）。

#### G7-4 D10验收的抽样、分母与配对（建议；C类项）

- 被验收的检查点：task7.18每个变体训练结束时的最终（5M）检查点，不在验证地图上挑选检查点（避免在同一集合上既选又验）。
- 地图：验证池稀疏、标准两档各50张（[SRC-0364](../../../SOURCES.md#src-0364)），与训练池不重叠。
- 抽样：每张图按固定种子列表跑回合；每次决策由task7.15生成候选，在掩码＝1的候选中均匀抽一个（与下层训练的子目标分布U33相同）。
- **配对**：抽中候选后保存环境快照（底盘、q、s、累积栅格、上一动作队列、计数、各随机数流）；A＝冻结下层SAC确定性执行该候选到段结束；恢复快照；B＝G7执行器执行同一候选；记录两者结果后，回合沿A的结束状态继续（状态分布由下层SAC自身诱导）。
- **分母**：决策时G7路径评估判为可行（≥1条路径整条可行）的抽中候选数n。到达＝“到达候选”或“到达路线终点”；失败＝IK失败或真值碰撞；其余为超时。
- **门槛（D10原文不改）**：到达率_SAC≥90%，且失败率_SAC≤失败率_G7＋5个百分点（同一n个候选），两变体分别判定，按点估计判。另报告（不作门槛）：到达率Wilson 95%区间、配对失败率差的按回合bootstrap区间、分档/分扇区/原地候选分项、G7判不可行候选上的结果。
- **样本量**：每变体至少1000个G7可行配对样本（到达率90%附近Wilson半宽约±1.9个百分点，推导见SRC-0436）；先跑100张图×2回合，不足时按预先固定的后续种子补回合，规则在运行前写定。
- 不通过：报告排查，不降门槛、不进入阶段1（L.9）。
- 备选：分母改为全部抽中候选；不配对（两执行器各自独立跑回合）；用验证集上最优检查点。

#### 不阻塞D10、以后需定的事项

- G7组上层训练所需的f_k字段（B.9字段与f_k v1的对应）与G7组预算/比较点（C类）：2026-10-21已定，见下节G7-5、G7-6（[SRC-0435](../../../SOURCES.md#src-0435)）。

### 2026-10-21 G7组上层训练：G7-5、G7-6（Claude起草；**2026-10-21用户均按推荐确定，[SRC-0435](../../../SOURCES.md#src-0435)**；下文“建议”均已成为已定）

- 执行：Claude（claude-opus-5-5，推理强度未知），只写文档。依据：父[TASK](../TASK.md) §4第7组、[task7.4 RESULTS](../task7.4/RESULTS.md)文首修订节第6条与N12、[task7.13 RESULTS](../task7.13/RESULTS.md) D20（f_k v1）、[task7.5 RESULTS](../task7.5/RESULTS.md) B.9字段。不新增实验组，不接f_p（父TASK已定）。

#### G7-5 G7的候选特征（建议：映射到f_k v1同一19维布局）

G7中每个候选的f_k由“决策时选出的最优路径p_k*”的评估结果填入主方案f_k v1（D20）的同一位置，候选编码器结构与维数与主方案相同：

|f_k v1字段|主方案（冻结下层推演）|G7（最优路径p_k*评估）|
|---|---|---|
|①是否到达|推演到达候选|p_k*整条可行|
|②结束类型5类|到达候选/路线终点/IK失败/局部图碰撞/段超时|同5类：计划走完/路线终点/首个预测IK失败/首个局部图碰撞/计划时长超过T_seg|
|③首个失败时刻/T_seg|同左|p_k*首个预测失败子步的时刻/T_seg，无失败为1.0|
|④用时t_c|推演用时|p_k*计划时长（不可行时按⑨取前段）|
|⑤T_seg|同|同（G7-3已定超时用T_seg）|
|⑥终点相对候选(Δx,Δy,Δθ)|推演终点|可行时为0；不可行时为前段终点|
|⑦Δs、⑧–⑩残差、⑪最小间隙|推演轨迹|p_k*（前段规则同⑨）|
|⑫⑬未知格比例与最近距离|推演扫过区域|p_k*扫过区域（B.9定义）|

- B.9原字段“N条中可行条数”不进f_k（G7的N＝14或7、主方案无此量，加入会使两组编码器输入维数不同）；只记入info作诊断。
- 理由：G7本来就同时改变执行器与特征来源（父TASK §4），保持编码器结构相同，至少不再额外引入网络差异。备选：20维（多一维“可行条数/N”），更贴近B.9原合同，但两组网络输入不同。

#### G7-6 G7组预算与比较点（建议）

- 训练：G7只做阶段1（不接f_p，父TASK已定），B1＝20万次决策、每变体3个种子，超参与主方案阶段1相同（N12、P7）；检查点按同一验证规则取最优（P4）。
- **主要比较点**：G7（阶段1，B1）对**主方案阶段1基线**（G2/G3/G4共同的阶段1检查点，同为B1、同一上层结构与超参，只差执行器与f_k来源）。两者预算相同，可直接比较。
- 次要（描述性，不作预先写定的主要比较）：G7对G4最终结果；须注明G4多B3预算与f_p，差异不能归因于执行器。
- 优先级：G7排在G1–G4之后；预算不足时按N12先做同步变体，G7若仍放不下则报告用户，不自行删减或缩步数。
- 备选：G7也训练B1＋B3（续训输出头），与G2等预算比较。
- task7.19实施的运行预算与GPU，在设计确认后写入派发提示。

## 交接

- 当前负责人：未登记（拟由Codex执行，用户派发）。


## run-id t7.19-r1-20261021 — Codex实施、配对工具与有界计时（review，部分停止）

执行模型 **gpt-6.1-sol / medium**（本次exec进程参数核实）；推荐Codex **GPT6.1sol / medium**、Claude **Sonnet5.5 / medium**，理由为跨路径/IK/执行/配对合同核对。授权、实际范围及实施依据：[SRC-0480](../../../SOURCES.md#src-0480)；[独立日志](../../../agent_logs/task7/task7.19/20261021-codex-g7-impl.md)。下文仅本run记录，不把上文设计或历史测试当本次结果。

### 改动与接口

只新增 `forem/src/task7_sim/g7.py`、`d10_eval.py`、`tests/test_g7.py`、`tests/test_d10_eval.py`；未改core.py/env.py、阶段一、参考库与容器生命周期，无训练、正式D10或Git提交。根HEAD `cac6c15599efcbe47a1a7ed30f59a475e4997fd4`，未提交源码以最终manifest哈希为准。

- `generate_paths`：固定P1-a/P1-b…P7-a/P7-b（异步14）/P1…P7（同步7），原地只有slot0；圆弧无有限解或侧向法向不存在时掩码。底盘段时长ceil至.05s后降低速度；s为B.9显式绝对曲线，末端精确封顶，避免逐次加法残余。近退化大弧只展开T_seg内控制；完整duration另存float64参与排序，超int64的计数仅存储饱和，不变更路径或新设退化阈值。
- `evaluate(state,route,grid,candidate,kin,robot,synchronous=...)`：签名不接真值/环境/renderer；N维批量逐子步调用共同`trial`，LocalCollision、同N1、失败优先IK→自碰撞→机械臂→底盘，残差/进度/用时/风险只按已提交前段。返回最优路径、19维f_k、路径掩码/可行计数及逐子步trace；可行计数只在info。K候选可先展开E×K并复制对应传感器输入。
- `execute(Core或EpisodeEnv,candidate,mask=...)`：同trial；真实执行只看IK/真值碰撞，不以局部预测停车。每10个子步重新评分，同一世界c*，初始cap/T_seg不重置；同步s曲线锚定决策初始s和累计提交时间。复用Core.begin的D7/D15和Core._finish回合计数；.1s动作末/提前结束渲染；记录失败、提交/尝试数、残差、关节跳变、触发条件和重规划wall。
- `snapshot/restore`：拥有动态Core/路线/栅格/动作队列/缓存/历史/计数与回合元数据，保存三类numpy流与CPU/本任务GPU RNG；固定运动学/几何/renderer接口保留身份。`paired`按同一快照分别执行外部确定性无状态策略与G7，再恢复策略结束快照；异常恢复初始快照并传播。
- `run_episode_batch`：消费已reset的外部地图/回合计划及显式候选RNG，均匀抽生成mask槽位；配对后沿策略状态继续。`summarize`两变体须分别调用，报告G7可行分母、不可行分项、到达/失败/超时、失败类型/平均时间、Wilson95、按回合bootstrap95和分档/扇区/原地分项；bootstrap次数与seed无默认值。正式地图覆盖、最终5M检查点及补充种子协议由后续正式运行派发核验，本次未运行。

### 待决定、部分停止与验收边界

1. **全不可行且含纯超时路径**：⑨只定义首失败检查点排序，G7-5包含纯超时结果却未定义此键。该分支抛`SpecificationPending`，不把超时硬当失败、不跳样本、不换候选；D10捕获异常时回滚起始快照后向外传播。可选解释仅列日志，尚未实施；需要用户决定此具体分支。直接调用execute若在后续重规划遇到此异常，会保留已执行前段供交接；只有paired承诺完整回滚。
2. 正式100张验证地图×2回合的种子列表、后续补充回合种子规则和bootstrap重复数未给出，本次不自行补正式协议。
3. 同一评分/执行输入在不同批大小下IK q可能有约1e−31的CPU64舍入差；测试q用1e−12，base/s仍逐元素；完整CPU64/GPU32另按1e−4核对f_k，不称所有q逐位相同。
4. 正式D10完全尚未执行，不对5M策略、≥1000可行对/变体、90%或＋5个百分点门槛作通过结论。

### 验证与计时

正在完成最终固定模块回归与真实验证池有界计时；前期记录保留于日志，最终命令/退出码/逐例结果与计时表随后追加。不得据本段“进行中”将任务标done。


### 最终代码测试与历史失败说明（15:25版本；依据SRC-0481及下文补充证据）

**原有17模块153项通过；最终自有25项通过（g7 19、d10 6，110.77s）。** 这是分次验证的153＋25，不伪称单次178全绿。原153在`final.xml`中无失败；同次运行总174 passed/2 failed，两项为本任务早期曲线/夹具问题，已修复并由后续全部自有测试覆盖。早期`regression.log`另纳入并行task7.20尚在改动的测试，157 passed/2 failed，失败均在`test_decision_env`；未修改/隐藏其他任务文件，后续明确固定原17模块。

共用容器执行前缀：`sg docker -c 'docker exec -e CUDA_VISIBLE_DEVICES=3 -e PYTHONPATH=/root/mm_husky_ws/src -e OMP_NUM_THREADS=2 -e MKL_NUM_THREADS=2 -e PYTHONDONTWRITEBYTECODE=1 forem-dev bash -c "cd /root/mm_husky_ws && timeout 580 <命令>"'`；早期不同线程/超时/是否-u的原始参数列[commands.json](../../../../logs/task7/task7.19/commands.json)，不将这个便于复核的前缀冒充每次历史命令。

|运行|容器内实际命令主体|退出码、结果|证据|
|---|---|---|---|
|固定范围回归|`python3 -u -m pytest src/task7_sim/tests --ignore=src/task7_sim/tests/test_decision_env.py --ignore=src/task7_sim/tests/test_g1.py -q --junitxml=logs/task7/task7.19/final.xml`|1；原153通过，新增2失败已修复；174 passed/2 failed，174.59s|[日志](../../../../logs/task7/task7.19/final.log) · [XML](../../../../logs/task7/task7.19/final.xml)|
|曲线修复后自有模块|`python3 -u -m pytest src/task7_sim/tests/test_g7.py src/task7_sim/tests/test_d10_eval.py -q --junitxml=logs/task7/task7.19/owned_final.xml`|0；23 passed，91.62s|[日志](../../../../logs/task7/task7.19/owned_final.log)|
|加强前10子步与隐藏几何|`python3 -u -m pytest src/task7_sim/tests/test_g7.py::test_replanning_anchor_batch_and_timeout src/task7_sim/tests/test_g7.py::test_truth_failure_rolls_back_first_substep -q --junitxml=logs/task7/task7.19/boundary_final.xml`|0；2 passed，31.80s|[日志](../../../../logs/task7/task7.19/boundary_final.log)|
|最终掩码修复后自有模块|`python3 -u -m pytest src/task7_sim/tests/test_g7.py src/task7_sim/tests/test_d10_eval.py -q --junitxml=logs/task7/task7.19/owned_masked_final.xml`|0；25 passed，110.77s|[日志](../../../../logs/task7/task7.19/owned_masked_final.log) · [XML](../../../../logs/task7/task7.19/owned_masked_final.xml)|
|活动路径优化对照|`python3 -u logs/task7/task7.19/equivalence.input.py`|0；CPU64/GPU32×两变体离散结果相同、f_k/base/s误差0；GPU异步q最大6.676e−6rad，其余q误差0；48.357s|[JSON](../../../../results/task7/t7.19-r1-20261021/active_equivalence.json) · [日志](../../../../logs/task7/task7.19/active_equivalence.log)|
|实际设备核查|`python3 -u logs/task7/task7.19/device_audit.input.py`|0；base/q/IK q/controls/features/capsules均cuda:0 float32，实际只可见物理GPU3；无网络/optimizer|[JSON](../../../../results/task7/t7.19-r1-20261021/device_audit.json)|

早期RED/失败均保留：模块缺失red退出2；green1朝向相差2π，按等价朝向比较；green2不同批大小CPU q舍入差约1e−31，q用1e−12、base/s仍精确；green4暴露重复累加使s未精确封顶，采用既定显式s曲线；arc_overflow_red超int64，修完整时长存储；active_pruning_red全部14条持续调用IK；masked_replan_red已结束行错误阻塞其他行。近退化存储、活动行优化、掩码修复均未增加物理/安全/评分阈值。

|验收项|最终用例（同上最终自有命令执行）|结果与限制|
|---|---|---|
|路径族、速度、.05s段界、端点、掩码、稳定排序|`test_paths_endpoints_and_limits`、`test_inplace_degenerate_and_ranking`、`test_near_degenerate_arc_has_bounded_expansion_but_full_duration`|通过；朝向按模2π比较；CPU浮点端点检查不冒充无限精度|
|纯评估、顺序/批量独立|`test_pure_evaluation_and_scored_execution`、`test_candidate_order_and_batch_independence`|通过；state/Grid/随机流不变，Kinematics固定变换缓存不属于物理状态|
|前10子步被评分即执行、同世界锚点、T_seg|`test_replanning_anchor_batch_and_timeout`|通过；首段10个子步base/s精确、q 1e−12；重规划候选世界坐标不变，采用初始D7超时|
|信息边界、真值失败停点、局部预测不停车、⑨前段|`test_truth_failure_rolls_back_first_substep`、`test_first_failure_prefix_and_information_boundary`、`test_trial_failure_priority_and_no_input_commit`|通过；实际改变隐藏盒子但Grid不变，G7 f_k相同，真值近墙第一子步失败；失败0提交/0渲染且只计一次，首失败前段有限|
|同步/异步、原地零推进、路线终点|`test_zero_and_route_end_inplace`及路径族两变体参数化测试|通过；同步原地内部同一s_in搜索，零推进不产生执行步|
|GPU32/CPU64|`test_cpu64_gpu32`、`test_full_robot_frozen_grid_cpu64_gpu32`|通过；完整机器人冻结相同Grid，离散可行/最优编号一致，19维f_k绝对1e−4检查通过，不放宽|
|活动行与批量独立|`test_masked_and_finished_paths_do_not_keep_calling_ik`、`test_finished_row_cannot_block_other_rows_replanning_or_advance_queue`、D10 `test_pair_does_not_score_inactive_ended_rows`|通过；终止行残留目标不进入新评估、不阻塞其他行，未参与行队列不推进|
|快照逐元素、配对同起点、沿策略结果继续|D10 `test_snapshot_restores_all_elements_and_rng`、`test_pair_starts_equal_and_continues_policy_end`、`test_gpu_snapshot_and_masked_pairs`、`test_exception_restores_start_and_snapshot_is_reusable`|通过；主动消耗maps/initial/other、CPU torch及GPU RNG后恢复；包含掩码、异常与复用|
|分母、结果分类、Wilson/回合bootstrap、分项|D10 `test_summary_denominator_clusters_and_ineligible`|通过；统计夹具100次bootstrap只为测试，不是正式协议|
|未定超时排序|`test_undefined_all_infeasible_timeout_order_stops_only_that_case`|通过的是明确抛SpecificationPending；该协议分支仍未实施/未验收，不能据此标done|

最终掩码修复：重规划与配对资格评估只处理活动行，`replans.indices`给出其原E行映射；`visible_previous`只随实际尝试动作的行更新，未行动行保持。掩码修复前源码/manifest保留为before_masked与*_pre_mask；原153依赖未改变，无需把无关原测试重复运行冒充新证据。


### 最终v3 E扩展计时与D10墙钟推算（最终掩码修复后，SRC-0483）

依据：[SRC-0482](../../../SOURCES.md#src-0482)说明方法/旧版本；最终版本与数值由[SRC-0483](../../../SOURCES.md#src-0483)补充。六个子命令均0，外层`timeout 580 python3 -u logs/task7/task7.19/profile_batch.input.py v3`实际wall **319.365s**；逐项argv、退出码与wall见[profile_v3_commands.json](../../../../results/task7/t7.19-r1-20261021/profile_v3_commands.json)。六项g7/d10及相关共享依赖哈希逐一与[最终manifest](../../../../results/task7/t7.19-r1-20261021/source_manifest.json)匹配，源码快照位于同目录source_snapshot。

输入为完整机器人固定夹具、普通候选移动0.19m（正式规则候选为1m，不能混淆），异步推进0.019m；一项一个样本，E行相同场景，无延迟分位数推断。每候选N条一次评估；整次决策含2次重规划；配对列含资格评估、脚本策略执行、恢复、G7执行和恢复策略状态，不能再把列逐项相加当单对成本。前后CUDA同步，单位为wall秒；末列为G7提交sim秒，二者分开。

|变体|E|N|每候选评估(s)|两次重规划各wall(s)|完整G7决策(s)|完整配对(s)|G7 sim(s)|
|---|---|---|---|---|---|---|---|
|异步|1|14|11.876|11.704/5.656|17.685|31.909|0.65|
|异步|4|14|12.547|12.295/6.337|18.964|33.824|0.65|
|异步|16|14|15.548|15.297/9.292|24.944|42.973|0.65|
|同步|1|7|6.639|6.485/0.446|7.260|14.280|0.65|
|同步|4|7|6.833|6.444/0.440|7.212|14.178|0.65|
|同步|16|7|7.755|7.539/0.859|8.755|16.850|0.65|

每项完整原始JSON均在`forem/results/task7/t7.19-r1-20261021/profile_E*_sync*_v3.json`，含内存、实际设备/dtype、路径长度、可行条数、结果、配对记录、源哈希。v1/v2及旧曲线/旧掩码计时保留，不与v3混作同版本统计。活动行优化同输入对照收益小，见SRC-0481；不把曲线bug修复或输入分布改变当性能提升。

D10条件模型（不是预算承诺）：`T_pair-only(E)=ceil(1000/E)×[t_async(E)+t_sync(E)]`。假设实际可行比例p＝1、每批满载、每对与这个短候选/脚本策略夹具成本相同：

|E|每变体批次数|两变体各≥1000对的配对部分(s)|小时|
|---|---|---|---|
|1|1000|46188.879|12.830|
|4|250|12000.307|3.333|
|16|63|3768.811|1.047|

完整形式为`sum_v ceil(1000/(E*p_v))*(t_pair_v+t_generation_v)+T_reset_schedule+T_bootstrap+T_IO`，各项wall秒；批不满、策略动作/推理、补回合还会改变成本。只有一个向量worker，上表累计worker wall等于串行总wall，不能将E当独立worker或推算多卡工期。推导输入和条件逐项保存在[conditional_projection_v3.json](../../../../results/task7/t7.19-r1-20261021/conditional_projection_v3.json)。

**不能据此批准正式D10有限工期。** 两个旧版真实验证池探针（固定seed71901、sparse_validation_00030、slot0、路线3.8089783m）分别wall318.155s/238.044s后触发全不可行纯超时排序缺口，配对未完成，非到达/失败/超时样本，不能计入分母；当时尚未启用活动行优化，亦不能冒充最终成本。未换种子找快样本；该具体分支暂停。真实p_v、长段分布、最终5M确定性策略和正式种子/补回合/bootstrap预算均未知，下一次派发必须先核定这些依赖，不能把约1小时的夹具条件结果直接作为正式预算。

### 预算与最终交接

预算账本见[commands.json](../../../../results/task7/t7.19-r1-20261021/commands.json)：已测容器外层wall求和，早期未包装调用以pytest/阶段实耗＋60s/调用保守余量计，合计 **3327.7s（55.46min）**，低于90min；这个余量不是实测启动延迟或科学阈值。嵌套profile子进程不重复计费，所有实际单条命令均≤10min。

**状态：review（部分停止，交Claude复核；不是done）**。已交付4个归属源码/测试文件，最终自有25项通过、原153项无回退、GPU3设备核查与两变体E扩展计时/条件推算。没有训练、正式D10、容器生命周期操作、Git提交或参考库改动；core.py/env.py与task7.17哈希相同。

剩余依赖/风险：①全不可行含纯超时路径的排序键待用户决定，本分支抛SpecificationPending且D10回滚；②正式100张验证地图、回合及补充种子列表、bootstrap重复数待派发写定；③task7.18最终5M检查点与真实分布成本未验收；④相同精度不同批大小的q可能存在小舍入差，不能宣称全部关节逐位相同。直接G7 execute在后续重规划遇到规格异常会保留已执行前段；paired承诺异常恢复起始快照。

接手Claude：先读本节/独立日志，核对最终manifest及四个源码；复核上列停止分支，提交用户决定；之后在独立正式派发中核验检查点、地图覆盖、种子及预算，再决定D10运行。不得把本次脚本夹具的统计当冻结验收。当前本任务计算进程已结束后才更新PROGRESS为review；无训练或长任务需要接管。

## Claude复核 t7.19-r1-20261021（2026-10-21T17:00–17:15，claude-opus-5-5，推理强度未知）

- 读RESULTS、接口与停止分支：g7.py/d10_eval.py只新增、未改core/env；评估签名不接真值；执行只按IK/真值碰撞；快照/配对异常回滚；自有25项＋原153项通过（Codex记录；GPU被其他任务门禁占用，本次未重跑，留r2复核时跑）。
- 停止分支合理：纯超时排序确为规格缺口，已由用户定（SRC-0904）；D10协议参数同。
- 性能风险：异步每候选评估约12 s、完整决策约18 s（固定夹具），D10在E16约1小时可接受；G7组阶段1训练前须优化。
- 结论：返工r2（实现SRC-0904两项，补测试）；正式D10待task7.18检查点。


## run-id t7.19-r2-20261021 — SRC-0904两项落地（2026-10-21，review）

本节取代r1“纯超时排序未定/正式协议待定”的当前状态，保留上文为历史。执行人Codex，实际`gpt-6.1-sol` / `medium`（派发进程argv核对）；本类任务推荐仍为Codex **GPT6.1sol / medium**、Claude **Sonnet5.5 / medium**，理由为排序语义、配对调度和统计合同需跨接口核对；推荐不等于Claude实际配置。授权依据[SRC-0904](../../../SOURCES.md#src-0904)，实现/选值依据[SRC-0484](../../../SOURCES.md#src-0484)，测试证据[SRC-0485](../../../SOURCES.md#src-0485)。

### 实际改动

- `forem/src/task7_sim/g7.py`：移除`SpecificationPending`类及对应抛错分支；`rank_paths(..., pure_timeout=...)`显式分为可行＞纯超时＞失败。失败先比较归一化首失败位置（越晚越好），同类依U25间隙阈值/完整时长/残差，完全并列保留固定路径序号；mask始终优先排除。`Evaluation.first_bad`现在记录归一化位置，无物理失败（含纯超时）为1.0，与既有19维特征第6维一致；未改特征布局。
- `forem/config/task7/d10_protocol.json`：正式协议唯一配置，地图index路径/哈希、100张具体map_id和难度、首批200个固定回合种子、补回合规则、最小可行配对数与bootstrap全部在此。
- `forem/src/task7_sim/d10_eval.py`：新增`load_protocol(path)`、`protocol_round(protocol, round_index)`、`run_protocol_variant(callback, protocol_path=..., synchronous=...)`、`summarize_protocol(records, protocol_path=...)`。协议路径必须显式给出；低层`summarize`现在也必须显式传`minimum_eligible_pairs`，删除原1000硬编码。正式配置中的种子、补回合起点、最小配对数与bootstrap预算均从文件读取，没有代码默认值。
- 对应两份测试增加混合分类/并列与协议调度覆盖。只改归属4份源码/测试及新增协议；`core.py`、`env.py`与r1哈希相同；没有改其他任务文件，没有Git提交、训练或正式D10。

### 协议内容摘要与种子选择

1. 钉住既有地图池`results/task7/maps/a/20261021T021400Z/index.json`及SHA256，validation中map_id排序，sparse/standard各50图。两变体共享相同固定表，用于同图同回合比较。
2. 首批种子列表为`2**80+j (j=0..199)`，图i的第r轮(r=0,1)用列表`2*i+r`。后续整轮r≥2按`2**80+200+(r-2)*100+i`顺延；每变体必须先完成两轮，之后若G7可行配对<1000，继续同100图整轮，直到≥1000（允许最终整轮超额）。耗尽预留区间报错，不复用种子或静默扩大协议。
3. 预留闭区间`[1208925819614629174706176,1208925819614633469673471]`（`2**80`起，宽`2**32`）。这是工程命名空间选择，不是方法有效性证据：高于地图种子区间和`EpisodeSampler`生成的int64提案种子；已审计22215份现存task7文本文件，区间冲突0。支持任意非负Python整数的`SeedSequence`直接消费，不转uint64。具体审计范围/限制见[seed_audit.json](../../../../results/task7/t7.19-r2-20261021/seed_audit.json)及[SRC-0484](../../../SOURCES.md#src-0484)；正式启动前再核对新增运行与未记录外部运行，不能宣称已审计不存在的未来记录。
4. bootstrap按完整回合重采样10000次，固定seed=`71920261021`；保留既有Wilson及D10点门槛，不把bootstrap置信区间变成新验收条件。
5. 本轮实现的是调度/统计入口；回调接收指定map_id/difficulty/round/episode/seed并返回全部配对记录，身份变更报错。后续正式运行方须将确切Python-int回合种子接入地图固定的reset和独立候选RNG，加载task7.18最终5M确定性策略并核验预算；本轮未执行此依赖接入，也未把夹具回调冒充真实环境结果。

### 命令、退出码与证据

实际完整命令登记在[commands.json](../../../../results/task7/t7.19-r2-20261021/commands.json)。两次测试均在既有forem-dev，`CUDA_VISIBLE_DEVICES=`、`PYTHONPATH=/root/mm_husky_ws/src`、OMP/MKL双线程、`PYTHONDONTWRITEBYTECODE=1`，容器工作目录`/root/mm_husky_ws`，`timeout 580`；不启停容器。

|执行|实际容器命令主体|结果|日志|
|---|---|---|---|
|首次CPU回归|`python3 -u -m pytest src/task7_sim/tests/test_g7.py src/task7_sim/tests/test_d10_eval.py -k "not cpu64_gpu32 and not gpu_snapshot" -q --junitxml=logs/task7/task7.19/r2/owned_cpu.xml`|退出1；33 passed/1 failed/5 deselected，66.83s；新增断言把第6维写成第3维，已修正测试|[日志](../../../../logs/task7/task7.19/r2/owned_cpu.log)|
|最终CPU回归|同上，XML文件改为`owned_cpu_final.xml`|退出0；**34 passed、5 deselected，66.33s**|[日志](../../../../logs/task7/task7.19/r2/owned_cpu_final.log) · [XML](../../../../logs/task7/task7.19/r2/owned_cpu_final.xml)|
|种子审计|`timeout 60 python3 -u logs/task7/task7.19/r2/seed_audit.py`|退出0；22215文本，0冲突；宿主首次尝试因历史ROS日志链接权限失败，已改容器内只读审计，未改权限|[日志](../../../../logs/task7/task7.19/r2/seed_audit.log) · [结果](../../../../results/task7/t7.19-r2-20261021/seed_audit.json)|

新增测试覆盖可行/纯超时/失败全部混合组合、各类并列与固定序号、失败先后/U25/mask、真实纯超时位置1.0、固定100图/200种子及后续种子唯一、SeedSequence大整数有效、无默认值/坏配置/区间耗尽、两变体相同计划、200对不足时补到10整轮1000对，以及首轮已够仍完成两初始轮。配对数量为**夹具**，不是D10实测分母。原有自有CPU用例同次通过；未重跑原153全目录，不引用旧GPU结果充当本轮回归。

### 交接与限制

**review，待Claude复核。GPU回归延期由Claude复核时执行**：门禁[nvidia-smi记录](../../../../logs/task7/task7.19/r2/gpu_gate.txt)显示GPU3已有compute（PID2704977）；本轮5个GPU参数化用例未运行，未占用任何GPU。源码/配置哈希与副本见[source_manifest.json](../../../../results/task7/t7.19-r2-20261021/source_manifest.json)和同目录source_snapshot。无本任务后台计算进程遗留，无停止/恢复动作需要交接。

剩余事项：Claude核查代码/配置与CPU证据并执行可用GPU回归；正式D10仍等task7.18最终检查点及正式派发/预算检查，不能判冻结通过。r1提出G7组阶段1训练前的性能优化要求继续保留，本轮未获得该训练或优化扩展授权，也未实施。

## Claude复核 t7.19 r2（2026-10-21T20:15–20:25，claude-opus-5-5，推理强度未知）

- 重跑（GPU3，训练已停空闲）：`test_g7.py`、`test_d10_eval.py` **39 passed**（含Codex延期的5个GPU用例），退出0。
- SRC-0904落实：纯超时按无失败排序并有组合测试；`config/task7/d10_protocol.json`含100张验证图、200个初始回合种子、补回合规则（同图顺延、各变体独立停止、不替换地图不跳回合）、保留种子区间与耗尽报错、bootstrap按回合10000次固定种子，d10_eval.py从配置读取。
- 结论：**实现部分复核通过**；本任务的正式D10须等task7.18修复自碰撞后重新训练得到的检查点再执行，状态保持review（实现完成、待执行D10）。注意：自碰撞几何修复（task7.18.1后续）会同样作用于G7评估，届时须用修复后的几何重跑G7相关测试。


## run-id t7.19-d10-v5-20261023 — Codex接手只读快照

- 原执行者Claude子Agent（实际claude-sonnet-5-5，推理强度未知），按SRC-0916只评估v5同步500k；GPU0/1各4 worker。启动/驱动与估时见[原执行日志](../../../agent_logs/task7/task7.19/20261023-claude-sonnet-d10-v5.md)；本审核没有重启或新增评估。
- 2026-10-23T10:08:48+08:00：8个worker存活，轮0–7的元数据均100图、800项map/seed/episode独立复算一致；正式jsonl尚0条配对/0完成轮。尚无正式率、CI、通过/冻结结论，不能把8轮在飞算800回合完成。[SRC-0964](../../../SOURCES.md#src-0964)
- 完整运行与停止前缀/分母/bootstrap/最终汇总待原运行完成后核验。发现driver无残留claim回收和轮内断点，直接删claim重跑会向旧jsonl追加重复；**当前进程均活着，不自动清理/重跑**。接手者须先核PID/输出并归档失败轮，明确恢复范围。5–8h工期未验证。
- 本节仅状态核对，不取代原执行方后续完整RESULTS与SRC-0955–0959登记。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium；本次实际审核子Agentgpt-6.1-sol/medium，父配置未知。当前归属审核负责人Codex，原计算进程独立运行。

- 2026-10-23T10:13:59.129821+08:00 审核增补：分析脚本未显式守住前两整轮完整，driver默认31轮耗尽也可正常退出；最终需独立核完整前缀0/1、eligible≥1000与原门槛，勿只读pass/退出0。静态风险详[SRC-0963](../../../SOURCES.md#src-0963)，本审核未修改或重启驱动。


## 2026-10-23 14:23运行故障复查

来源[SRC-0965](../../../SOURCES.md#src-0965)：八worker均CUDA OOM，原进程不再存在；GPU0/1 0%/14MiB。轮0–7各只落第一决策100条，共800条、112 eligible、0 final；尚不足正式连续完整轮协议，不能给通过/失败指标。原claim不自动回收，直接删除后向同jsonl重跑有重复风险；本审核未清理/重启。需先定位显存峰值与安全恢复，再按原协议完整验收。未取得原worker shell退出码/精确退出时刻，不伪造。
