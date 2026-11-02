# task7.15 — 结果

状态：**review（2026-10-21第二轮；边界测试口径与R_pre返工已验证，137项通过，交Claude复核；仅排除并行task7.17的test_env.py）**。最新证据[SRC-0442](../../../SOURCES.md#src-0442)、[SRC-0443](../../../SOURCES.md#src-0443)；r1历史证据SRC-0440/0441保留。

## 运行记录

建立时尚无执行记录；本次按下方run-id追加实际配置、命令、证据、失败与交接。

## 交接

- 当前负责人：Codex；r1交Claude复核，见下方run记录与待决定问题。


## run-id：t7.15-r1-20261021-1001

**交付状态：review；主体已实现，验收未全部通过。** 当前负责人Codex，下一步交Claude核对本节与原始证据；不标done，不发起新文档设计复核轮次。

### 执行与授权

- 2026-10-21约10:01开始。实际模型：**未知**；实际推理强度：**未知**（平台未提供可核实名称/档位）。推荐：Codex **GPT6.1sol / medium**，Claude **Sonnet5.5 / medium**，需跨几何、IK前缀与信息边界核对；推荐不当实际配置。
- 授权沿[TASK](TASK.md)、[SRC-0431](../../../SOURCES.md#src-0431)及本次派发。宿主HEAD `cac6c15599efcbe47a1a7ed30f59a475e4997fd4`，main工作区；保留其他会话改动。没有训练、提交git、启停/重建容器或修改参考仓库。
- 实现仅改`forem/src/task7_sim/candidates.py`、`forem/src/task7_sim/tests/test_candidates.py`；未新增配置，`search.py/core.py/geometry.py/perception.py`均只读。记录文件为本RESULTS、独立[日志](../../../agent_logs/task7/task7.15/20261021-codex-candidates.md)、PROGRESS自己的行与本任务预留来源SRC-0440/0441。
- 来源：[SRC-0440](../../../SOURCES.md#src-0440)登记实施映射与工程推导；[SRC-0441](../../../SOURCES.md#src-0441)登记本run实际测试/精度/计时。版本以[manifest.json](../../../../results/task7/t7.15-r1-20261021-1001/manifest.json)和[profile.json](../../../../results/task7/t7.15-r1-20261021-1001/profile.json)源哈希为准，不能只依赖HEAD。

### 实现与接口

`generate_candidates(local, state, route, kin, synchronous=...)`只接收局部传感器栅格、State、本任务Route、IK模块；无真值输入。返回CandidateBatch：

|字段|形状/含义|
|---|---|
|pose|E×13×3，B_t相对(dx,dy,dyaw)，空槽零补齐|
|mask|E×13，生成掩码；走廊排除的扇区为0，原地始终1；不代表推演可行性|
|progress|不同步E×13，空槽s_cur；同步为None，普通同步扇区无s字段|
|inplace|E×13，仅slot12为true|
|world_pose(base)|用决策起点base一次换算世界目标，供现有Core/rollout只读调用|
|info|n_gen、only_inplace、discard_reason（0生成/1已观测正高度格阻挡）、异步delta_s、inplace_progress/delta_s、IK目标/接受/DLS次数、批调用数、搜索同步墙钟秒|

- A.2/R1/R2/R6：固定1m、12个30°扇区（从+x逆时针）；走廊[0,1.6]×[-.335,.335]。以[0,.99]与[.61,1.6]两个同宽底盘矩形的并集调用LocalCollision所用同一个`rectangle_hits`，格仍为.05m闭方格。几何并集是推导，浮点接触限制见下文。未知格、已观测高度0均不排除。
- A.3/R3/R4：仅把生成的异步槽位或同步slot12展开成E×有效K，直接调用`search.inplace_progress`；同样.05m采样、截断终点、同N1解析→DLS接受规则、第一段连续前缀、首样本失败回s_cur。IK失败不改变生成mask。
- A.4/A.5：原地不动不转、零推进仍有效；同步s_in只在info内部诊断，不加入候选progress。执行速度/时长留现有Core D6/D15决定，不实施旧固定时长公式。
- A.6/A.7：所有诊断只进info；生成阶段不知道路径可行性，故不假报“无可行候选比例”。不增加曲线候选、历史候选、回退量、R7网络或R8自动启动机制。
- 函数不修改输入、环境状态与RNG。候选张量重复调用逐位一致；`search_wall_seconds`是实测时间，天然不逐位一致。Kinematics只填自身只读固定变换缓存，不改变物理状态。

### 实际命令、退出码与结果

所有容器调用均通过宿主`python3 forem/logs/task7/t7.15-r1-20261021-1001/run.py <label> < <label>.input.py`执行；精确stdin和stdout如下。wrapper实际调用：

```bash
sg docker -c 'docker exec -i -e CUDA_VISIBLE_DEVICES=1 -e PYTHONPATH=/root/mm_husky_ws/src -e PYTHONDONTWRITEBYTECODE=1 -w /root/mm_husky_ws forem-dev timeout 580s python3 -u -'
```

脚本前缀打印PID并设本次torch线程2；torch2.7.1+cu128，GPU1在容器内映射cuda:0。无后台Python。[commands.jsonl](../../../../logs/task7/t7.15-r1-20261021-1001/commands.jsonl)留每条argv、wall、退出码和时间；历史编辑/测试输入仅作证据，不应重放覆盖代码。

|label|退出码|容器调用wall(s)|精确命令与证据|
|---|---|---|---|
|baseline|0|32.862|[输入](../../../../logs/task7/t7.15-r1-20261021-1001/baseline.input.py) · [日志](../../../../logs/task7/t7.15-r1-20261021-1001/baseline.log)|
|candidates_red|2|2.017|[输入](../../../../logs/task7/t7.15-r1-20261021-1001/candidates_red.input.py) · [日志](../../../../logs/task7/t7.15-r1-20261021-1001/candidates_red.log)|
|candidates_behavior_red|1|3.369|[输入](../../../../logs/task7/t7.15-r1-20261021-1001/candidates_behavior_red.input.py) · [日志](../../../../logs/task7/t7.15-r1-20261021-1001/candidates_behavior_red.log)|
|candidates_first_green|0|10.679|[输入](../../../../logs/task7/t7.15-r1-20261021-1001/candidates_first_green.input.py) · [日志](../../../../logs/task7/t7.15-r1-20261021-1001/candidates_first_green.log)|
|full_suite|2|2.067|[输入](../../../../logs/task7/t7.15-r1-20261021-1001/full_suite.input.py) · [日志](../../../../logs/task7/t7.15-r1-20261021-1001/full_suite.log)|
|precision_probe|0|2.918|[输入](../../../../logs/task7/t7.15-r1-20261021-1001/precision_probe.input.py) · [日志](../../../../logs/task7/t7.15-r1-20261021-1001/precision_probe.log)|
|owned_regression|4|1.867|[输入](../../../../logs/task7/t7.15-r1-20261021-1001/owned_regression.input.py) · [日志](../../../../logs/task7/t7.15-r1-20261021-1001/owned_regression.log)|
|owned_regression_v2|1|38.368|[输入](../../../../logs/task7/t7.15-r1-20261021-1001/owned_regression_v2.input.py) · [日志](../../../../logs/task7/t7.15-r1-20261021-1001/owned_regression_v2.log)|
|profile|0|14.485|[输入](../../../../logs/task7/t7.15-r1-20261021-1001/profile.input.py) · [日志](../../../../logs/task7/t7.15-r1-20261021-1001/profile.log)|
|final_audit|0|2.768|[输入](../../../../logs/task7/t7.15-r1-20261021-1001/final_audit.input.py) · [日志](../../../../logs/task7/t7.15-r1-20261021-1001/final_audit.log)|

- baseline：73 passed in30.41s；[逐例XML](../../../../results/task7/t7.15-r1-20261021-1001/baseline.xml)。
- candidates_red：新模块缺失的import失败；candidates_behavior_red：NotImplemented占位下19项均失败；candidates_first_green：19 passed in8.56s，完成RED→GREEN。
- full_suite：全目录`pytest -q -p no:cacheprovider src/task7_sim/tests`退出2。并行task7.16的`test_mapgen_a.py`出现时实现模块尚未就绪，collection报ModuleNotFoundError；未替别的任务修改或隐藏失败。
- owned_regression：从XML重建模块路径时误加一层src，退出4、no tests ran；owned_regression_v2已纠正，仅显式列baseline的11模块＋本任务文件，**92 passed、1 failed in36.26s**，退出1。[逐例XML](../../../../results/task7/t7.15-r1-20261021-1001/owned-regression-v2.xml)。其中原有**73/73通过**，本任务**19/20通过**；未把选择性验证称为整个并行目录全绿。
- 唯一自有失败为`test_all_sector_cell_boundaries_gpu32_cpu64`，见下文。其他候选测试包括走廊边缘/余量端点内外、未知/地面、LocalCollision格覆盖核对、真实IK直线/弯曲/回折前缀、全不可达仍生成、零推进/同步无progress、输入与RNG不变、遮挡真值盒改变后扫描栅格与候选不变、CPU64/GPU32真实IK夹具。
- precision_probe诊断退出0：32组软件限位内80%范围随机q（本地Generator seed715）作FK生成起点，原地.00001m短路线全部搜索到终点，最大误差0；**没有实施R_pre，因此此项不是R_pre粗筛验证**。输入/原始输出与[precision-probe.json](../../../../results/task7/t7.15-r1-20261021-1001/precision-probe.json)保留。
- final_audit退出0：从XML重新核对73原有测试全部通过、候选恰有1失败；编译两个归属文件、保存源哈希和边界反例。不把诊断脚本退出0解释为所有验收通过。

### CPU64/GPU32：已通过范围与未通过项

[E扩展profile](../../../../results/task7/t7.15-r1-20261021-1001/profile.json)中两变体/E=1/16/64/256的固定短路线夹具，mask/inplace精确一致；相对pose最大绝对差2.794844e-7（平移m/朝向rad按字段），进度最大绝对差4.529953e-8m，均在测试绝对1e-6、相对0的对照内。该对照容差只用于测试连续数值，不是碰撞阈值。

**未通过：全集12×16384格的闭接触覆盖，CPU64/GPU32有5个不同判定。** 原始坐标/布尔值在[manifest.json](../../../../results/task7/t7.15-r1-20261021-1001/manifest.json)，(扇区,展平格号)为(1,8127)、(2,8127)、(5,8128)、(9,4025)、(9,8262)。共享SAT的浮点投影/`gap<=r`边界舍入不同；本实现复用其规则，不自行加epsilon、不修改只读geometry。

### E×K有界计时（只记录，不设门槛）

GPU1 float32，E=1/16/64/256、K_max13，每E实际生成11槽/环境；同一0.11m直线路线与局部占据格(70,84)/(64,97)，warmup1次、每项同步wall8样本。计时含候选生成、E×有效K组装、搜索IK、诊断同步；不含扫描/栅格裁剪、路径推演或训练。CPU64参考从同一物理夹具独立构造，E扩展为相同夹具复制。完整samples/吞吐/峰值/哈希见profile.json；8样本p99仅本批插值，非总体尾延迟保证。

|变体|E|p50(ms)|p95(ms)|p99(ms)|max(ms)|实际生成候选/s|IK目标 / DLS回退（每调用）|
|---|---|---|---|---|---|---|---|
|不同步|1|286.353|287.027|287.161|287.194|38.4|44 / 36|
|同步|1|13.762|13.856|13.861|13.862|798.8|4 / 0|
|不同步|16|289.364|290.082|290.294|290.346|608.4|704 / 576|
|同步|16|13.852|13.941|13.952|13.955|12694.1|64 / 0|
|不同步|64|288.479|291.889|292.326|292.436|2434.7|2816 / 2304|
|同步|64|13.935|14.016|14.035|14.040|50488.4|256 / 0|
|不同步|256|290.432|294.138|294.317|294.361|9657.9|11264 / 9216|
|同步|256|13.960|14.023|14.030|14.032|201576.1|1024 / 0|

异步夹具每环境44个IK目标、36个DLS回退（81.82%），同步只有原地4目标且0回退；差异来自本夹具候选位置，不能当作任务分布频率。共享search批量计算包括前缀失败以后的样本，未来若优化须由其负责人保持同一规则核验。GPU实际pose/progress为CUDA float32，无网络/optimizer。批量覆盖矩阵归约与有效K搜索已实现，无多进程/多环境生命周期操作，也未改变物理步长、子步、观测、奖励或终止条件。

### 待决定与交接

1. **精度边界（实质未通过项）**：现有共享SAT下R2同一覆盖函数、闭接触和CPU64/GPU32离散判定精确一致不能在这5个边界同时保证。候选接口可复核，不能据此宣布完全验收。可选方向是由几何模块负责人统一决定数值接触合同，或授权统一精度预计算离散模板并核实与LocalCollision一致性；本任务未选容差或改共享模块。
2. **R_pre**：共享search没有粗筛接口。按本次“复用search同一规则”直接调用，未新增半径/误删机制；若A.3必须含粗筛，需要明确接口修改归属，本轮只停此部分。
3. **旧A.4固定时长测试**：现行D6/D15下推进速度由SAC控制，同步也非固定v_ee，故未输出/测试旧固定时长公式。已核对现有Core的内部s_in与零推进测试通过；交Claude按现行合同确认此版本对应，不自行补v_ee。

限制：有界性能来自同一短路线/状态复制，不代表训练地图、长路线或运行时分布；“无可行候选比例”需后续推演才能统计。本生成器没有R_pre，长路线会继承共享search全长采样/批量DLS成本；没有启动长训或扩大预算。

PROGRESS初次定点插入误用文本字符偏移，误覆盖该行之前的一段中文；收尾已按开工读到且与HEAD一致的原片段做**局部字节恢复**，逐字节确认其他会话新增行和后续内容均保留。误写前快照位于logs的`progress-offset-before.bin`，后续状态更新用UTF-8字节定位，仅自身行。没有把此问题藏作他人改动。

本run容器累计调用wall **111.399785s（1.857分钟）**、最长单条**38.367539s**，均在60分钟/单条10分钟预算内；所有调用已退出，无本任务后台进程。最后资源核查见final_audit.log后宿主docker top/nvidia输出：仅容器原入口/sleep，GPU无compute进程。当前PROGRESS本行已review，等待Claude核对待决定项，未标done。

## Claude复核 t7.15-r1-20261021-1001（2026-10-21T10:14–10:30，claude-opus-5-5，推理强度未知）

- 重跑（GPU1，排除并行中的`test_mapgen_a.py`）：task7.15相关仅`test_all_sector_cell_boundaries_gpu32_cpu64`失败，与Codex报告一致；另一失败`test_env.py::test_wrapper_cpu64_gpu32`属并行进行中的task7.17，不计入本任务。原73项通过。
- PROGRESS误覆盖核查：`git diff cac6c15 -- forem/doc/PROGRESS.md`只有新增行、无删除行，Codex的局部恢复正确。
- 读码`candidates.py`对照task7.9 A.2–A.6：扇区0…11从+x逆时针每30°、d＝1.0 m、朝向＝θ_j；走廊长1.6 m（d＋0.6）、宽0.67 m，以[0, 0.99]∪[0.61, 1.6]两个车身矩形复用LocalCollision同一`rectangle_hits`；只“已观测且高度>0”阻挡、未知按空闲；槽12原地且掩码恒1；不读真值。**语义与规格一致。**
- 待决定项处理（Claude复核意见）：
  1. 5个格边界float32/float64差异：与task7.14已接受的合同一致（“不保证精确擦边处float32与float64分类逐位一致；未给边界加新epsilon”，见task7.14 r1“float32 GPU与float64 CPU对照”）。属测试要求过严：改为在|SAT分离量|>1e−5 m的格上要求精确一致，边界带内的不一致计数并报告；不改geometry判定、不加碰撞epsilon。
  2. R_pre：属task7.9 A.3规格第2步（“只能放宽、不能误删”，[SRC-0397](../../../SOURCES.md#src-0397)），不改变结果、只省IK；本夹具不同步生成286 ms、82% DLS回退，主要来自不可达远样本，按根AGENTS性能要求应实施。授权本任务第二轮修改`search.py`加入R_pre：半径取展开URDF连杆长度上界＋N1的DLS近似接受容差0.1 m（保证不误删可被近似接受的样本），用随机FK采样验证不误删，并以同输入逐元素比对证明有无R_pre时`inplace_progress`输出完全相同；Core的s_in同用此函数，task7.14/7.17相关测试不得回退。
  3. 旧A.4固定时长公式：已被D6/D15取代（推进速度由下层SAC决定），不实现、不测试是正确的。
- 结论：**返工（r2：上述1、2两项）**，完成后再复核；其余部分可接受。


## run-id：t7.15-r2-20261021-1037 — 第二轮返工

**状态：review；本轮两项返工已完成并验证，交Claude复核，不自标done。** r1失败与旧待决定记录保留为历史，不覆盖原实测。

### 授权、范围与实际配置

- 按本次用户派发及上节Claude复核：授权search.py加入R_pre和tests/test_search.py，保持`inplace_progress(state,route,kin,*,return_info=False)`接口；边界测试改为带外精确一致/带内计数；旧A.4时长已由D6/D15取代，不再列待决定。
- Codex实际模型、实际推理强度均**未知**（无法核实）。推荐Codex **GPT6.1sol / medium**、Claude **Sonnet5.5 / medium**，理由是URDF几何界、TCP近似接受与跨模块搜索等价需逐项核对。
- 改动仅`forem/src/task7_sim/search.py`、`candidates.py`（新增粗筛诊断透传）、`tests/test_candidates.py`、新增`tests/test_search.py`。未改core/geometry/perception、配置、阶段一或参考仓库。`geometry.py/perception.py`与r1源哈希逐字节一致；其他会话对其归属文件的改动保留。
- 来源：[SRC-0442](../../../SOURCES.md#src-0442)登记授权/推导/方法适用性；[SRC-0443](../../../SOURCES.md#src-0443)登记本轮实测。日志续写[原独立日志](../../../agent_logs/task7/task7.15/20261021-codex-candidates.md)。[manifest](../../../../results/task7/t7.15-r2-20261021-1037/manifest.json)列当前源哈希/测试核对结果，不能只用Git HEAD标记未跟踪源版本。

### R_pre半径、安全推导与实现

取已载入展开URDF（`config/task7/model.urdf`；sha256见[safety.json](../../../../results/task7/t7.15-r2-20261021-1037/safety.json)）中`ur5_base_link`→`ur5_tool0`路径的全部joint origin平移范数之和；旋转保持范数，固定关节也纳入。非零范数分别为0.089159、0.425、sqrt(0.39225²+0.10915²)、0.09465、0.0823 m，极小z分量按原值math.hypot计算，九个关节逐项xyz/范数保留在safety.json。

`R_U = Σ||origin.xyz|| = 1.0982622696663507 m`

`R_pre = R_U + 0.1 = 1.1982622696663507 m`

N1的实际位置接受式是TCP残差`≤0.1+1e-6 m`。为保证DLS近似接受不会误删，粗筛必须保留既有1e-6保护，且考虑固定tool0→TCP偏移：名义长度l=0.15m（GPU32表示为0.15000000596m）。**没有新增接受阈值或碰撞epsilon。**

由于N1在TCP上评估，直接用目标tool0的位置并加0.1m不能自动保证安全：目标姿态与实际姿态不同时，工具偏移也不同。实现使用tool0径向距离的保守下界：

`d_lower = max(0, ||target_TCP − UR5_base|| − l)`

任一原合同可接受q都满足`||target_TCP−UR5_base|| ≤ ||actual_TCP−UR5_base||+0.100001 ≤ R_U+l+0.100001`，故`d_lower ≤ R_pre+1e-6`。只拒绝违反此必要条件的样本；不是用姿态相关目标tool0距离误删样本。代码因半径为正，省略max(0)不改变布尔比较。这是为满足“只能放宽、不能误删”的安全放宽，不把l另设为新的可调半径。[SRC-0442](../../../SOURCES.md#src-0442)

粗筛失败直接accepted=false，不调用IK。保留原0.05m采样、截断终点、cumprod第一段连续前缀、首样本失败返回s_cur；未按候选优化改路线/步长/接受式。无URDF证据的solve_world-only自定义IK全放行（原PrefixIK等接口不破坏）。info保留原键：targets现在为实际交给IK数，新增sampled_targets/coarse_rejected/ik_batch_calls；candidates只透传这些诊断，不进观测/奖励/f_k。

### 测试与命令证据

本轮wrapper仍执行以下命令，每次stdin先打印容器PID、设torch CPU线程2；精确命令内容见各input.py，stdout/退出码/wall逐项保留：

```bash
sg docker -c 'docker exec -i -e CUDA_VISIBLE_DEVICES=1 -e PYTHONPATH=/root/mm_husky_ws/src -e PYTHONDONTWRITEBYTECODE=1 -w /root/mm_husky_ws forem-dev timeout 580s python3 -u -'
```

实际宿主入口`python3 forem/logs/task7/t7.15-r2-20261021-1037/run.py <label> < <input.py>`；账本[commands.jsonl](../../../../logs/task7/t7.15-r2-20261021-1037/commands.jsonl)。全部运行于forem-dev、GPU1（逻辑cuda:0），torch2.7.1+cu128；无后台Python。

|label|退出码|wall(s)|命令/日志|
|---|---|---|---|
|search_red|1|2.968|[输入](../../../../logs/task7/t7.15-r2-20261021-1037/search_red.input.py) · [日志](../../../../logs/task7/t7.15-r2-20261021-1037/search_red.log)|
|search_green|0|20.693|[输入](../../../../logs/task7/t7.15-r2-20261021-1037/search_green.input.py) · [日志](../../../../logs/task7/t7.15-r2-20261021-1037/search_green.log)|
|regression|0|51.486|[输入](../../../../logs/task7/t7.15-r2-20261021-1037/regression.input.py) · [日志](../../../../logs/task7/t7.15-r2-20261021-1037/regression.log)|
|compare_profile|0|25.499|[输入](../../../../logs/task7/t7.15-r2-20261021-1037/compare_profile.input.py) · [日志](../../../../logs/task7/t7.15-r2-20261021-1037/compare_profile.log)|
|safety_evidence|0|3.119|[输入](../../../../logs/task7/t7.15-r2-20261021-1037/safety_evidence.input.py) · [日志](../../../../logs/task7/t7.15-r2-20261021-1037/safety_evidence.log)|
|final_suite|0|49.234|[输入](../../../../logs/task7/t7.15-r2-20261021-1037/final_suite.input.py) · [日志](../../../../logs/task7/t7.15-r2-20261021-1037/final_suite.log)|
|audit|1|1.817|[输入](../../../../logs/task7/t7.15-r2-20261021-1037/audit.input.py) · [日志](../../../../logs/task7/t7.15-r2-20261021-1037/audit.log)|
|audit_v2|0|1.817|[输入](../../../../logs/task7/t7.15-r2-20261021-1037/audit_v2.input.py) · [日志](../../../../logs/task7/t7.15-r2-20261021-1037/audit_v2.log)|

- **search_red**：新增远样本“不调用IK”与两精度10000 FK测试先执行，3项按预期失败（旧版仍调用IK、无粗筛helper）。实现后search_green：**31 passed in18.62s**（候选20＋搜索11），[XML](../../../../results/task7/t7.15-r2-20261021-1037/search-candidates.xml)。
- **regression**：全目录排除并行test_mapgen_a.py/test_env.py，**114 passed in49.41s**。随后发现task7.16已review、实现就绪，最终扩大覆盖加入mapgen测试。
- **final_suite**：`pytest -q -p no:cacheprovider src/task7_sim/tests --ignore=src/task7_sim/tests/test_env.py`，**137 passed in47.18s，退出0，无skip**；[逐例XML](../../../../results/task7/t7.15-r2-20261021-1037/final-suite.xml)。仅排除task7.17并行active中的test_env.py，其已报告的观测格边界问题不属于本任务，没有修改或放宽它。task7.17的episode/routes测试亦在137项内。
- **audit/audit_v2**：首版audit已核对XML/编译/哈希，但最后尝试在容器内读取未挂载的Git目录失败，退出1、未保存manifest；修正为读取宿主host.json记录的HEAD后，audit_v2退出0并保存manifest。原73个(classname,name)均存在且通过，本任务31/31通过，四源编译及只读几何/感知哈希核对通过。137不是整个仍在开发目录的全套通过结论，明确保留上述test_env排除。

### 10000组FK、近似接受与等价性

- `test_uniform_10000_fk_and_approximate_tcp_targets_are_not_filtered`：CPU64与GPU32分别10000组，seed20261021，本地Generator在完整LOW/HIGH软件限位内均匀q；改变世界base到(1.3,-.7,.9)验证坐标系。每组真实FK目标均保留；再将目标TCP径向移动0.100001m，所有样本也保留，未加随机姿态排除。
- safety_evidence另以独立URDF origin/axis递归FK核对10000组：最大tool0半径**1.0319115823555614m**，均≤R_U；不是只用同一DH FK自证。再构造TCP位置偏移0.09m、姿态偏移0.3rad目标，按原`Kinematics._result`在原q上判定，CPU64/GPU32各**10000/10000被N1接受、0被粗筛误删**。这证明测试夹具包含近似接受情形，不声称执行了10000次DLS迭代或穷举证明安全。原始构造、数值、URDF哈希见safety_evidence.input.py/.log及safety.json。
- 四类路线（直线、弯曲、回折、全不可达），CPU64/GPU32各覆盖：非零s_cur下共享`inplace_progress`与冻结r1逻辑逐元素相同；两变体候选s_in/s_k亦逐元素相同，回折不跳过中间不可达段。冻结r1逻辑仅在测试/日志内，不给生产函数添加开关或改变签名。
- compare_profile还将本run保存的原r1-search.py/r1-candidates.py在同一进程实际重放（不是只引用历史数字）；E=1/16/64/256两变体的pose/mask/inplace/s_in/s_k全部torch.equal，CPU64独立夹具与GPU32连续字段按原1e-6测试对照通过。产物[profile-compare.json](../../../../results/task7/t7.15-r2-20261021-1037/profile-compare.json)保留exact_r1_r2_outputs与全部样本。

### 边界带口径与计数

测试以CPU64对完整1.6×0.67m走廊独立计算四个SAT轴的有符号分离量（max gap−projected radii，单位m）；仅用来划分精度对照域，不进生产判定。全集12×16384=196608个扇区格：

|对照域|格数|GPU32/CPU64不一致|
|---|---|---|
|SAT分离量绝对值>1e-5m|196488|0|
|边界带（其余）|120|5|

5格与r1相同：(1,8127)、(2,8127)、(5,8128)、(9,4025)、(9,8262)；最大绝对分离量**1.249000902703301e-16m**。这是已接受擦边精度合同内计数，不再判测试失败；没有改geometry、不在生产SAT比较中加1e-5或epsilon。[SRC-0442](../../../SOURCES.md#src-0442)、[SRC-0443](../../../SOURCES.md#src-0443)

### E扩展与r1同输入计时对照

同r1夹具：0.11m直线、局部占据格(70,84)/(64,97)，每环境实际生成11/13槽；GPU1 float32，每版本每变体每E warmup1、同步墙钟8样本，含生成/粗筛/IK/诊断，排除扫描/crop/Core推演/训练。表中“r1重测”与r2在本轮同一进程；“r1历史”为上轮数值。完整p95/p99/max、吞吐、显存、原始samples与哈希见profile-compare.json。8样本尾分位只描述本批。

|变体|E|r1历史p50(ms)|r1重测p50|r2 p50|r2 p95|r2 p99|r2 max|r2实际生成候选/s|DLS每调用r1→r2|
|---|---|---|---|---|---|---|---|---|---|
|不同步|1|286.353|284.240|281.685|283.977|284.626|284.788|39.0|36→4|
|同步|1|13.762|13.635|14.060|14.172|14.209|14.218|781.2|0→0|
|不同步|16|289.364|288.077|285.511|286.958|287.515|287.654|616.2|576→64|
|同步|16|13.852|13.772|14.237|14.307|14.314|14.316|12363.5|0→0|
|不同步|64|288.479|286.477|286.074|286.518|286.572|286.586|2461.4|2304→256|
|同步|64|13.935|13.829|14.278|14.444|14.499|14.512|49204.4|0→0|
|不同步|256|290.432|288.339|286.788|287.707|287.751|287.762|9815.9|9216→1024|
|同步|256|13.960|13.891|14.319|14.367|14.370|14.371|196597.0|0→0|

异步每环境采样44目标，R_pre拒绝32，实际IK44→12，DLS36→4；接受目标总数不变，输出逐元素相同。对应E=1/16/64/256粗筛数32/512/2048/8192，DLS36/576/2304/9216→4/64/256/1024。同步只有原地4目标，均保留，DLS0→0。计数是本夹具，不能推广到任务分布。

实测异步墙钟收益较小、同步略增检查开销，**不报告普遍提速**；GPU批量DLS仍有回退样本时保留同样64次迭代/调用开销。本轮不为降低时延改变步长/子步/观测/奖励/终止、不削掉失败样本、不扩大实现范围。

### 限制、预算与交接

- 本轮无遗留自有失败、无新增待决定；旧R_pre与边界测试返工项已解决，旧A.4无固定时长实现是现行D6/D15要求。仅保留已接受边界带分类差异作为限制。
- FK/近似接受采样与四类路线是有界验证，安全性依赖上文三角不等式、同URDF模型和N1合同；不声称穷举证明。性能只来自同一短路线/初态，未测长路线/真实地图/训练更新，不能据此承诺训练工期。无URDF的自定义IK不启用粗筛。
- 已读r1账本111.399785s；本轮账本156.632309s，累计**268.032094s（4.467分钟）**，最长单调用51.485683s；均低于累计60分钟/单条10分钟。wrapper包围整个docker exec的wall保守计入，不是GPU-only时间。
- 所有本轮调用均退出，无本任务后台PID需恢复。停止说明仍为只中断本run工具session/日志记录PID，不停止其他会话或容器。未训练、未启停/重建容器、未提交Git、未启动其他Agent。
- PROGRESS只按UTF-8字节定点更新本行为review，交Claude复核SRC-0442/0443、半径/TCP安全放宽、精度域、最终XML和同输入计时。不发起新的文档设计复核轮次，不自行启动task7.18。

## Claude复核 t7.15-r2-20261021-1037（2026-10-21T10:40–11:00，claude-opus-5-5，推理强度未知）

- 重跑（GPU3）：`test_candidates.py`、`test_search.py`、`test_completion.py`、`test_core.py` **48 passed**；此前全目录GPU回归中候选与搜索测试亦全部通过。
- 读码`search.py`：R_pre＝ur5_base_link→tool0各关节origin平移范数之和（三角不等式上界1.0983 m）＋0.1 m；比较量为“到目标TCP距离−‖tool0→TCP‖”的保守下界，覆盖N1在TCP上的近似接受，推导成立；无URDF模型的测试替身全放行，接口不变。等价性（四类路线×两精度×E扩展逐元素相同）、10000组FK与近似接受不误删、边界带计数（带外196488格0差异、带内120格5差异）证据齐全。
- **性能发现（转task7.18）**：异步夹具DLS回退36→4次，但生成耗时286→282 ms几乎不变——DLS固定64次迭代，一次批量调用约275 ms与目标数无关，只要批内任一样本需DLS即付此成本。阶段L大E并行时每个子步都可能触发，须在task7.18端到端性能核查中优先处理（如减少逐迭代Python开销/图捕获/提前收敛退出，须保持N1接受语义）。
- 结论：**task7.15 done**。
