# task7.14 — 结果

状态：**review（r2补完，73项测试与完整几何计时已执行，待Claude复核）**。最新为下方run-id r2-20261021-0000；保留precheck、r1部分交付与Claude复核的历史事实。依据[SRC-0428](../../../SOURCES.md#src-0428)。

## 运行记录

（以下按run-id保留历次执行，最新见r2最终汇总。）

## 交接

- 当前负责人：未登记（拟由Codex执行，用户派发）。
- 下一步：用户确认G1–G3 → 派发Codex按[PROCEDURE](PROCEDURE.md)执行 → Claude复核。


## run-id：precheck-20261020-2118 — 前置检查阻塞

- 时间：2026-10-20T21:19:06+08:00；任务：TASK7.14-ENVCORE-20261020；负责人：Codex；当前状态：**blocked（G1–G3待用户确认；实施尚未执行）**。上方“尚未执行”及历史交接保留。
- 实际模型：未知；实际推理强度：未知。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium；原因：后续几何、IK与执行分支需跨模块核对，推荐不等于实际配置。
- 依据：[SRC-0420](../../../SOURCES.md#src-0420)；完整核查与命令记录见[日志](../../../agent_logs/task7/task7.14/20261020-codex-envcore.md)。
- 核查结果：TASK仍明确标G1–G3需用户确认；按用户“仍待确认则停止并报告”的要求，没有选择建议值，未进入PROCEDURE实施步骤。
- 已执行只读命令：`cat`读取约定/入口/环境/三文档、`git status --short`、`git branch --show-current`、`git rev-parse HEAD`、`rg`/`sed`/`tail`查找状态与来源、`ps`查看宿主进程，均退出0；`ls -ld forem/src/task7_sim forem/config/task7 forem/doc/agent_logs/task7/task7.14`退出2，源码及配置目录尚不存在。命令结果与限制见日志；未产生容器原始运行日志。
- 改动：仅PROGRESS本任务行、本RESULTS追加、本任务独立日志、SOURCES新增条目；未修改TASK/PROCEDURE、代码、配置或参考仓库，未提交Git。
- 容器/GPU/torch实时核查：尚未执行；容器计算0秒，GPU使用0块，无后台任务。
- 测试、float32/float64对照、分项计时、吞吐：**均尚未执行**；无退出码、性能数值或验收通过结论；没有建立`logs/task7`或`results/task7`运行目录。
- 待决定：G1传感器高度基准；G2地面/障碍高度阈值；G3观测的末端计划下一位姿定义（现有建议完整列于TASK与日志，不作为已确认值）。
- 交接：用户确认或更正G1–G3并登记TASK后，由Codex继续资源核查与步骤1–9；实施和必要验证完成后本任务行转review交Claude核验。此次仅交付阻塞核查，环境核心尚未交付。

## 2026-10-20T21:35 G1–G3确认（Claude登记，非运行记录）

- 用户确认G1–G3均取TASK所列建议（[SRC-0421](../../../SOURCES.md#src-0421)），TASK已改写。上方`precheck-20261020-2118`的阻塞条件解除；Codex可从PROCEDURE步骤1（资源/合同核查）恢复。实施、测试与计时仍**尚未执行**。


## run-id：r1-20261020-2137 — 参数化环境内核实施与局部阻塞交接

- 记录时间：2026-10-20T22:16:22+08:00；任务TASK7.14-ENVCORE-20261020；负责人Codex；**部分实施，非整体验收通过**。依据[SRC-0423](../../../SOURCES.md#src-0423)；完整过程见[独立日志](../../../agent_logs/task7/task7.14/20261020-codex-envcore.md)。G1–G3按[SRC-0421](../../../SOURCES.md#src-0421)实施，旧precheck阻塞不再适用。
- 实际模型/推理强度：未知/未知；推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium，理由：几何、IK及L.0分支跨模块核对；推荐不是实际配置。
- 资源：forem-dev，torch2.7.1+cu128，CUDA12.8；GPU物理0，环境仅见1卡。累计本任务容器调用墙钟 **192.001秒（3.200分钟）**，最长 **26.995秒**；前次precheck为0秒。按整次调用墙钟保守计账，没有并发容器计算；无训练/网络/策略评估/容器启停/Git提交。
- 源版本：根HEAD15fae7b＋新包未提交文件；原型来源commit2380ff51c31ac30fc8506ac2dbac5c6cad24d42a。URDF SHA256 `f9e23d78f06ab1d6ad13688b48ce3177d725cc6439e930d00c785a258c7d2062`；文件哈希见[verification.json](../../../../results/task7/t7.14-r1-20261020-2137/verification.json)，已与最终源文件及计时manifest核对。

### 实现模块与文件

|文件（均在forem内）|本次实现|必要限制|
|---|---|---|
|`src/task7_sim/geometry.py`|角点JSON→中心OBB、补缺失墙/去重、padding；矩形SAT、精确线段/盒距离、线段距离、胶囊/地面/自碰撞分类|旋转合法性容差为必填；完整URDF机器人几何及臂-车体/肩部允许对组装未完成|
|`src/task7_sim/kinematics.py`|实际URDF独立FK参考、已核DH FK、tool0/TCP/安装变换、8分支解析→DLS64回退→TCP接受；m/CBL量/rad分开|最近分支不保证连续；保留跳变，不新增速度失败条件；未自选可操作度标量|
|`src/task7_sim/motion.py`|精确圆弧、动作单位换算、两变体推进封顶、位置弧长/slerp及整路线同号处理|同位置异姿态段的弧长度量未定，明确拒绝该类输入|
|`src/task7_sim/perception.py`|360×90斜距射线、OBB/地面/胶囊自遮挡、G1原点相交报告、只落点更新、最高高度、128旋转裁剪、量化解码、LocalCollision|真实机器人几何尚未组装，尚不能对实际G1位置给无相交结论；局部模块无真值输入|
|`src/task7_sim/core.py`|参数化L.0动作/子步尝试-提交-回退、渲染时机、B/G、回合边界与mask、队列；尝试子步诊断；f_k v1编码；E×K推演|M_r通过必填future_offsets输入；同步原地s_in暂由调用方显式提供；三个物理风险量的聚合器未实现，feature_metrics必填；无默认值冒充物理测量|
|`src/task7_sim/benchmark.py`|显式脚本夹具的18分项有界计时及精度实测|空机械臂或6条人工胶囊夹具，不是完整机器人端到端计时|
|`src/task7_sim/tests/test_*.py`|45项几何/运动学/感知/流程/信息边界及批量回归|通过仅覆盖列明夹具，未覆盖下述被阻塞的整体验收|
|`config/task7/model.urdf`|复制task7.6 r1实际展开模型，用于固定安装/TCP与独立FK核查|不依赖宿主ROS，不改阶段一模型|

没有实施候选生成器、网络、训练、ManiSkill、mapgen生成、随机reset/地图/路线采样或阶段一改动。`Core`为接受显式初始状态/地图/路线/几何的内核，并非已经交付完整VectorEnv/reset封装。

### 测试命令、退出码与日志

逐次真实调用为宿主`python3 forem/logs/task7/t7.14-r1-20261020-2137/container.py <label> < forem/logs/task7/t7.14-r1-20261020-2137/<label>.input.py`（首次为heredoc，同名input保留精确内容）；wrapper仅用`sg docker -c`执行`docker exec -i -e CUDA_VISIBLE_DEVICES=0 -e PYTHONPATH=/root/mm_husky_ws/src -w /root/mm_husky_ws forem-dev timeout 580s python3 -u -`，并加宿主超时。原始argv/耗时见[commands.jsonl](../../../../logs/task7/t7.14-r1-20261020-2137/commands.jsonl)。写入代码与pytest均在该容器Python内完成；宿主wrapper只编排与留日志。

|调用label|退出码|调用墙钟s|原始日志|结果/说明|
|---|---|---|---|---|
|`preflight`|0|2.252|[preflight.log](../../../../logs/task7/t7.14-r1-20261020-2137/preflight.log)|核查/写入退出0；完整输入见同名.input.py|
|`inspect_model`|0|0.133|[inspect_model.log](../../../../logs/task7/t7.14-r1-20261020-2137/inspect_model.log)|核查/写入退出0；完整输入见同名.input.py|
|`geometry_red`|2|1.934|[geometry_red.log](../../../../logs/task7/t7.14-r1-20261020-2137/geometry_red.log)|预期：新geometry模块不存在，收集退出2|
|`geometry_green`|0|2.753|[geometry_green.log](../../../../logs/task7/t7.14-r1-20261020-2137/geometry_green.log)|9通过|
|`ik_red`|2|2.014|[ik_red.log](../../../../logs/task7/t7.14-r1-20261020-2137/ik_red.log)|预期：新kinematics模块不存在，收集退出2|
|`ik_green`|1|3.647|[ik_green.log](../../../../logs/task7/t7.14-r1-20261020-2137/ik_green.log)|2失败：自拟1e−12与混合单位2e−6测试不合合同|
|`ik_diagnose`|1|3.715|[ik_diagnose.log](../../../../logs/task7/t7.14-r1-20261020-2137/ik_diagnose.log)|1失败：原自拟2e−6位置门未满足；保留实测|
|`ik_contract`|0|3.708|[ik_contract.log](../../../../logs/task7/t7.14-r1-20261020-2137/ik_contract.log)|13累计通过|
|`motion_red`|2|1.944|[motion_red.log](../../../../logs/task7/t7.14-r1-20261020-2137/motion_red.log)|预期：新motion模块不存在，收集退出2|
|`motion_green`|1|2.657|[motion_green.log](../../../../logs/task7/t7.14-r1-20261020-2137/motion_green.log)|1失败：整条路线四元数符号对齐缺失，已修复|
|`motion_sign_fix`|0|2.643|[motion_sign_fix.log](../../../../logs/task7/t7.14-r1-20261020-2137/motion_sign_fix.log)|4通过|
|`perception_red`|2|1.959|[perception_red.log](../../../../logs/task7/t7.14-r1-20261020-2137/perception_red.log)|预期：新perception模块不存在，收集退出2|
|`perception_green`|0|2.632|[perception_green.log](../../../../logs/task7/t7.14-r1-20261020-2137/perception_green.log)|5通过|
|`core_red`|2|1.980|[core_red.log](../../../../logs/task7/t7.14-r1-20261020-2137/core_red.log)|预期：新core模块不存在，收集退出2|
|`core_green`|1|16.036|[core_green.log](../../../../logs/task7/t7.14-r1-20261020-2137/core_green.log)|2失败：浮点路线长夹具与精确零残差期望有误|
|`core_fixtures`|1|16.591|[core_fixtures.log](../../../../logs/task7/t7.14-r1-20261020-2137/core_fixtures.log)|1失败：夹具错把不同步T_seg=6 s预期为2 s|
|`contracts_red`|0|10.593|[contracts_red.log](../../../../logs/task7/t7.14-r1-20261020-2137/contracts_red.log)|7个新增合同回归直接通过（标签不是失败声明）|
|`edge_tests`|0|26.329|[edge_tests.log](../../../../logs/task7/t7.14-r1-20261020-2137/edge_tests.log)|39通过|
|`benchmark_write`|0|0.127|[benchmark_write.log](../../../../logs/task7/t7.14-r1-20261020-2137/benchmark_write.log)|核查/写入退出0；完整输入见同名.input.py|
|`timing`|0|13.367|[timing.log](../../../../logs/task7/t7.14-r1-20261020-2137/timing.log)|18分项；首轮H2D误含往返，见勘误|
|`continuity_inspect`|0|0.209|[continuity_inspect.log](../../../../logs/task7/t7.14-r1-20261020-2137/continuity_inspect.log)|核查/写入退出0；完整输入见同名.input.py|
|`jump_probe`|0|1.887|[jump_probe.log](../../../../logs/task7/t7.14-r1-20261020-2137/jump_probe.log)|已知大跳变诊断已保留|
|`diagnostics_red`|1|2.161|[diagnostics_red.log](../../../../logs/task7/t7.14-r1-20261020-2137/diagnostics_red.log)|预期失败：尚无尝试子步诊断attempts|
|`diagnostics_green`|0|25.521|[diagnostics_green.log](../../../../logs/task7/t7.14-r1-20261020-2137/diagnostics_green.log)|41通过|
|`timing_v2`|0|13.632|[timing_v2.log](../../../../logs/task7/t7.14-r1-20261020-2137/timing_v2.log)|18分项；H2D边界已修正，当前计时版本|
|`precision_extended`|0|4.463|[precision_extended.log](../../../../logs/task7/t7.14-r1-20261020-2137/precision_extended.log)|4个新增CPU64/GPU32专项通过|
|`final_tests`|0|26.995|[final_tests.log](../../../../logs/task7/t7.14-r1-20261020-2137/final_tests.log)|45通过，24.86 s；JUnit/verification哈希已核|
|`final_files`|0|0.120|[final_files.log](../../../../logs/task7/t7.14-r1-20261020-2137/final_files.log)|源/URDF/计时哈希一致；新文件归属workspace UID1004|

最终每个用例的实际测试命令共用：`final_tests.input.py`内`pytest.main(['-q','src/task7_sim/tests','--junitxml=results/task7/t7.14-r1-20261020-2137/pytest.xml'])`；退出0、**45 passed in 24.86s**，日志[final_tests.log](../../../../logs/task7/t7.14-r1-20261020-2137/final_tests.log)。全部45个用例的名称/运行时间逐项保留于[pytest.xml](../../../../results/task7/t7.14-r1-20261020-2137/pytest.xml)，没有用未执行项凑通过数。最终六模块结果如下：

|模块|用例数|结果与命令|
|---|---|---|
|`src.task7_sim.tests.test_contracts`|7|全部通过，退出0；共用下述final_tests命令和日志|
|`src.task7_sim.tests.test_core`|9|全部通过，退出0；共用下述final_tests命令和日志|
|`src.task7_sim.tests.test_geometry`|10|全部通过，退出0；共用下述final_tests命令和日志|
|`src.task7_sim.tests.test_kinematics`|7|全部通过，退出0；共用下述final_tests命令和日志|
|`src.task7_sim.tests.test_motion`|5|全部通过，退出0；共用下述final_tests命令和日志|
|`src.task7_sim.tests.test_perception`|7|全部通过，退出0；共用下述final_tests命令和日志|

失败历史没有删除：初次缺模块的收集失败属实现前记录；motion的整路线四元数同号错误已修复；IK初版测试自拟1e−12与2e−6门不能冒充TASK合同，纠正为独立FK数值核查和B.R的1e−4 m/rad精确接受门，保留所有原失败日志与实测，不声称达到旧自拟门；core的浮点长度、零量与不同步T_seg预期夹具已纠正，未修改任何接受/奖励/超时语义。

### float32 GPU与float64 CPU对照

- 一般128目标：CPU/GPU均接受128；该组分支一致128/128；GPU结果由CPU64回检，最大位置差 **5.232274054609185e−6 m**、SO(3)角 **2.281432697769957e−5 rad**、CBL无量纲量 **5.108851952595472e−8**。见timing-v2 precision；不以GPU自检替代CPU回代，不据此推广到边界/奇异全体。
- task7.6 r1索引84、249分别在CPU64/GPU32测试接受，检查其回检与单位；DLS、圆弧、路线、射线、落点累积、局部裁剪、Truth/Local/self碰撞、Core奖励/提交及E×K特征均有CPU64/GPU32专项对照。
- task7.6 r7已知最大跳变位置(time0,path15)，历史2.4699274725371536 rad；当前同前态、DH生成目标、现合同1e−4接受时为 **1.5049447706773267 rad**，仍接受并记录，未加速度拒绝/平滑。完整证据[continuity_probe.json](../../../../results/task7/t7.14-r1-20261020-2137/continuity_probe.json)。普通连续路径测试通过不构成奇异处平滑保证。
- 不保证精确擦边/分支边界上float32与float64分类逐位一致；未给所有边界添加新epsilon。栅格/观察语义与时间参数没有为提速改变。

### 分项计时（当前v2，非通过门）

完整版本、输入、逐项样本数和p50/p95/p99/max、吞吐见[timing-v2/timings.json](../../../../results/task7/t7.14-r1-20261020-2137/timing-v2/timings.json)。GPU计时前后同步，包含Python与发射开销；每项先2次预热，再8–12次样本，分位数仅描述该小样本。吞吐单位按items：IK解/秒、ray/秒、cell/秒、transition/秒或candidate/秒，不能跨项混比。

|分项|重复×items/调用|p50 ms|p95 ms|p99 ms|max ms|items/s|
|---|---|---|---|---|---|---|
|`fixture_reset_state_route_grid`|12×1|2.901|2.950|2.974|2.980|344.22|
|`host_to_gpu_map_tensor`|12×5|0.022|0.022|0.023|0.023|231038.09|
|`arc_batch_13`|12×13|0.346|0.370|0.378|0.380|37230.80|
|`ik_analytic_batch_1`|12×1|10.393|11.774|12.375|12.525|94.10|
|`ik_dls64_batch_1`|8×1|278.283|278.565|278.571|278.573|3.59|
|`ik_analytic_batch_13`|12×13|10.443|10.495|10.501|10.503|1244.40|
|`ik_dls64_batch_13`|8×13|278.776|280.019|280.186|280.228|46.59|
|`panorama_360x90_no_robot_capsules`|12×32400|1.005|1.050|1.051|1.051|32048670.49|
|`grid_crop_128x128`|12×16384|0.465|0.486|0.494|0.496|35075672.58|
|`truth_collision_six_fixture_capsules`|12×1|2.223|2.432|2.553|2.583|443.42|
|`local_collision_six_fixture_capsules`|12×1|3.219|3.248|3.250|3.251|310.16|
|`scripted_action_transition_with_render_no_arm_geometry`|10×1|47.201|47.373|47.379|47.381|21.18|
|`rollout_E1_K1_4substeps_unknown_fixture`|8×1|110.867|113.522|114.607|114.878|8.98|
|`rollout_E1_K13_4substeps_unknown_fixture`|8×13|121.467|123.978|124.968|125.216|106.68|
|`rollout_E2_K3_4substeps_unknown_fixture`|8×6|115.798|116.618|116.935|117.014|51.75|
|`cpu64_ik128_threads_1`|12×128|6.763|7.038|7.089|7.101|18828.98|
|`cpu64_ik128_threads_2`|12×128|6.456|6.572|6.572|6.572|19805.70|
|`cpu64_ik128_threads_4`|12×128|6.468|6.549|6.559|6.561|19742.56|

- 环境动作夹具含两次IK/碰撞、观测和扫描，但没有真实臂/车体几何；E×K夹具每候选4个已提交子步，风险输入取全未知/空臂夹具的已知值。它们不等于完整环境吞吐，更不是训练工期依据。
- 性能核查：已采用候选/环境维度张量批量，不用多进程或后台Python线程；CPU同一128目标1/2/4线程已测，2与4接近，保留继承的2线程，不声称全局最优。原interop64/CPU亲和0–63均记录于manifest，未启动外部线程任务。
- 首轮`timings.json`的`host_to_gpu_map_tensor`误含GPU→CPU→GPU往返；已完整保留首轮和benchmark_v1.py，v2先在计时外准备CPU张量，才计H2D。此勘误不能用旧项作H2D收益结论。

### 未通过整体验收、待决定与剩余实施

以下均未假装已执行/已通过；按用户“只停该部分”要求，独立模块完成后在此交接，不再开展文档复核轮次。

|项|位置与缺口/冲突|可选理解或必要下一步（尚未采纳）|影响|
|---|---|---|---|
|P1|task7.5 B.2的cos²+sin²“超容差”无数值|由用户/Claude写定校验容差；目前为调用必填，测试1e−8仅夹具输入|默认地图入口待组装，读取与几何内核可独立使用|
|P2|task7.13 L.2、task7.8 V3的M_r/采样窗，task7.4 §9仍未定|固定点数/间隔或显式弧长列表；当前future_offsets必填，不把测试(.01,.1)当协议|默认观测配置未完成|
|P3|task7.14胶囊“URDF外接”与task7.5 B.5允许“恒接触”未列完整几何/对表；夹爪开合姿态未定|确认夹爪固定开度或全行程包络、连杆外接构造、车体/肩部表示及允许对清单；不得从SRDF119条整体放行|完整实际UR5连杆/臂-车体/夹爪、自遮挡、G1实际几何相交检查未执行；A.5对应实体几何验收未通过|
|P4|B.7为位置弧长的单值P(s)，A.6又要求零平移转姿段|补显式s节点/姿态度量，或禁止这类路线；当前明确拒绝同位置异姿态，保留相同重复位姿不除零|零平移转姿段尚未实现；其余普通路线测试通过|
|P5|D15要求段开始内部计算s_in，引用父§2.8“最远”；候选生成器task7.9 A.3有第一连续可达样本规则|核对并复用已定R3/R4共享搜索（不实现候选生成器），明确“最远”与第一连续区间/采样相位；本次未实施共享搜索，Core要求显式固定progress|同步原地封顶/零推进流程已测，自动求s_in仍剩余实施；不把显式输入当已完成内部计算|
|P6|SRC-0393要求扫过区域格数不随检查点间隔变，D8只给端点几何；分支跳变时无子步间关节/连杆扫掠定义|明确连续扫掠模型或正式采用已定义的离散区域口径，并明确最近未知格距离的截顶/无未知取值；不得用端点覆盖偷换连续扫掠|最小清距与两项风险聚合未实现；f_k编码和传递已测，实际物理f_k与一般E×K端到端验收未完成|
|P7|B.4要求记录可操作度但无固定标量定义|确认Jacobian体积/最小奇异值/其他定义及单位；现有尝试记录包含q增量与分支，不自选标量|可操作度未实现|

尚未运行/交付：完整机器人模型上的A.5碰撞/自遮挡验收、A.6纯转姿段、物理扫掠风险、自动s_in和默认观测配置，以及依赖这些部分的完整Husky+UR5端到端计时。随机回合任务/路线准备、完整VectorEnv/reset封装不在本次已实现内核内；未用脚本夹具冒充它们。纯推演的所有接口只接收状态、路线、Grid快照、运动学及明确回调；测试证明了本次数据通路的遮挡边界，不把回调调用者任意闭包当安全沙箱。

### 交接

- 当前负责人：Codex；状态：**blocked（部分交付，待上述局部决定/输入补齐）**，未标review/done；不是预算用尽。后续用户/Claude可先核验代码和证据，补定/澄清P1–P7后由Codex继续对应实现；不需要重跑已核且未变的模块。
- 剩余预算约86.800分钟容器调用墙钟（下一次仍须重读ledger计账）；没有预算扩展、训练或策略评估授权。
- 全部本任务容器进程已退出；docker top仅原docker-init/sleep；GPU无compute进程。没有待停止任务。每次PID见日志，后续wrapper实时写<label>.pid，需停止时只针对核实的该PID，不碰其他任务。
- 必要验证完成后才能转review交Claude；目前45项单测通过不代替整体验收。


### 同run收尾补充（2026-10-20T22:20:02+08:00；当前最终版本）

本节更新上文45项/v2/192秒的版本状态，保留其原始记录；依据[SRC-0424](../../../SOURCES.md#src-0424)。

- 收尾反例发现float32中小幅纯转姿段会被近似同姿态判定漏拒绝；新增回归先失败，再把Route归一化/同号后的姿态分量变化直接判为未定义纯转姿段。未实现新弧长度量，也未设可接受小角度阈值。
- **当前最终全套：46 passed in23.24s，退出0**；最终命令为`guard_and_final.input.py`内`pytest.main(['-q','src/task7_sim/tests','--junitxml=results/task7/t7.14-r1-20261020-2137/pytest-final.xml'])`。日志[guard_and_final.log](../../../../logs/task7/t7.14-r1-20261020-2137/guard_and_final.log)，逐例证据[pytest-final.xml](../../../../results/task7/t7.14-r1-20261020-2137/pytest-final.xml)，当前源/模型哈希[verification-final.json](../../../../results/task7/t7.14-r1-20261020-2137/verification-final.json)。新增1项属于motion模块，其余45项完整重跑。

|收尾调用（命令规则同上）|退出码|墙钟s|日志|
|---|---|---|---|
|`orientation_guard_red`|1|1.912|[orientation_guard_red.log](../../../../logs/task7/t7.14-r1-20261020-2137/orientation_guard_red.log)|
|`guard_and_final`|0|25.401|[guard_and_final.log](../../../../logs/task7/t7.14-r1-20261020-2137/guard_and_final.log)|
|`timing_v3`|0|13.466|[timing_v3.log](../../../../logs/task7/t7.14-r1-20261020-2137/timing_v3.log)|
|`final_cleanup`|0|0.126|[final_cleanup.log](../../../../logs/task7/t7.14-r1-20261020-2137/final_cleanup.log)|

- 当前计时为[v3完整18项](../../../../results/task7/t7.14-r1-20261020-2137/timing-v3/timings.json)，与最终源文件/URDF哈希逐项匹配。口径/限制与v2相同，保留旧版本；关键分项如下，均为夹具数据，无通过门或工期承诺：

|分项|p50 ms|p95 ms|p99 ms|max ms|重复×items/调用|items/s|
|---|---|---|---|---|---|---|
|`ik_analytic_batch_1`|10.242|11.620|12.356|12.540|12×1|95.36|
|`ik_dls64_batch_1`|275.188|277.242|278.016|278.209|8×1|3.63|
|`panorama_360x90_no_robot_capsules`|0.998|1.050|1.064|1.068|12×32400|32226435.84|
|`scripted_action_transition_with_render_no_arm_geometry`|46.737|47.418|47.755|47.839|10×1|21.35|
|`rollout_E1_K13_4substeps_unknown_fixture`|120.514|121.511|121.902|122.000|8×13|107.72|

- 当前累计容器墙钟 **232.906秒（3.882分钟）**；最长26.995秒；剩余预算约86.118分钟。账本[commands.jsonl](../../../../logs/task7/t7.14-r1-20261020-2137/commands.jsonl)，收尾无本任务运行进程/GPU任务。
- 状态保持 **blocked（部分交付）**。P1–P7及剩余物理模型/风险/默认组装未解除，不标完成或review。

## Claude复核 r1-20261020-2137（2026-10-20T22:30–22:50，claude-opus-5-5，推理强度未知；只读核查＋重跑测试）

- 重跑：forem-dev内（确认无本任务进程、GPU无compute进程后）`CUDA_VISIBLE_DEVICES=0 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m pytest -q -p no:cacheprovider src/task7_sim/tests`，**46 passed in 25.68s**，退出0；与Codex最终结果一致。墙钟约30 s，计入本任务容器预算。
- 语义对照（逐行读`src/task7_sim/core.py`，对照task7.13 L.0、L.3、L.5、D13–D20与task7.4 N2、N4–N6）：B（−10·c只计底盘碰撞、残差取最后提交子步、动作变化只比ω/v且对队列）、G（Δρ＋到达−2·失败，不同步＋Δs）、同步/不同步组合、T_seg＝3·T_ideal＋2及进度候选取max、截断上限（不同步s_k、同步原地s_in、其余L）、提交后“路线终点→到达候选→段超时”判定次序、失败不提交、动作步末渲染、mask真值表、o_(t+1)在队列put之前构造、换段沿用可见上一动作、回合级F＝5/卡住5次/D_max＝150/T_max＝200 s/成功0.025 m与0.05、推演不判回合条件——**均与规格一致，未发现语义偏差**。
- 结论：r1作为部分交付属实，Codex的blocked状态与P1–P7列项如实；P1–P7已由用户确定（[SRC-0425](../../../SOURCES.md#src-0425)），见TASK。
- **性能风险（非验收门，但根AGENTS性能要求在阶段L长训前必须处理）**：
  1. 推演循环每个动作步构造3次观测（`rollout`内先`observe`，`step`内再算`before`与`after`），执行路径每步2次；观测里的路线通道对每个路线节点在16384格上Python循环求线段—方格距离，`_body_transform`每次走CPU的URDF变换。
  2. 夹具计时：执行一个动作转移p50约47 ms（无机械臂几何），E1×K13推演2个动作步约121 ms，DLS64单次约275 ms。若不改进，阶段L 5M动作转移仅环境部分在单环境下约65小时量级（47 ms×5M，推算，未计训练更新、推演与真实几何），每次决策的K候选推演也会远超可接受范围。
  3. 建议Codex在补完P1–P7时一并做：去掉重复观测（复用上一步的after）、路线通道向量化、固定变换预计算，并以同输入逐元素比对证明输出不变；再测E批量扩展（E＝1/16/64/256）的吞吐。这是性能核查，不改任何语义。


## run-id：r2-20261021-0000 — P1–P7补完、完整几何验收与有界优化

状态：active（2026-10-21T00:10:21+08:00中间登记，尚未完成）。负责人Codex，实际模型/推理强度未知；推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（几何/流程与性能同输入核对）。授权沿SRC-0419，P1–P7沿[SRC-0425](../../../SOURCES.md#src-0425)。承接r1 232.905596秒＋Claude复核约30秒；后者为用户/Claude提供的近似值，按30秒预留，非精确实测。预算依据见`forem/logs/task7/t7.14-r2-20261021-0000/budget_carry.json`，所有本轮调用见同目录commands.jsonl。

已进入实现：URDF网格外接胶囊/固定默认夹爪、10000均匀关节样本Always表、碰撞与渲染接入、默认路线点、共用s_in搜索、离散格并集风险和|det J|。完整结果、命令/退出码、计时与限制在本run下继续追加；尚未执行的E扩展/优化不视为完成。


### r2最终汇总（2026-10-21T00:51:39+08:00）

**review：P1–P7已补完，73项测试通过；完整几何与CPU64/GPU32核对、三项指定优化及E=1/16/64/256计时均已执行，交Claude复核。** 实际Codex模型/强度未知；推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（跨模块语义、几何与证据核对）。方法与所有数值依据：[SRC-0428](../../../SOURCES.md#src-0428)及[SRC-0426](../../../SOURCES.md#src-0426)、[SRC-0427](../../../SOURCES.md#src-0427)。本轮无新增待决定参数；G1相交按授权要求报告，不移动传感器。

#### 版本、改动与产物

- 开工：forem-dev已经运行，只使用CUDA_VISIBLE_DEVICES=0，torch2.7.1+cu128；容器核查[inspect.log](../../../../logs/task7/t7.14-r2-20261021-0000/inspect.log)。实际Python3.10.18/CUDA12.8、GPU型号和线程数见verification.json。根HEAD15fae7b＋未提交改动；保留既有工作，没有提交git、训练/策略评估/网络、容器启停或参考/阶段一代码修改。
- [verification.json](../../../../results/task7/t7.14-r2-20261021-0000/verification.json)列包、测试、配置SHA256并核对最终profile；URDF来源和IK原型沿r1/SRC-0423，原型commit2380ff51c31ac30fc8506ac2dbac5c6cad24d42a；URDF SHA256 f9e23d78f06ab1d6ad13688b48ce3177d725cc6439e930d00c785a258c7d2062。未改参考网格，来源路径/哈希逐个记录。

|文件（forem内）|本轮实施与验证|
|---|---|
|[geometry.py](../../../../src/task7_sim/geometry.py)|P1默认旋转范数容差1e-6；TruthCollision接入完整RobotGeometry自碰撞|
|[robot.py](../../../../src/task7_sim/robot.py)、[robot_geometry.json](../../../../config/task7/robot_geometry.json)|URDF碰撞网格外接胶囊＋0.02m；默认零关节夹爪并集、固定车体包络；相邻/10000组Always允许表；不读地图|
|[search.py](../../../../src/task7_sim/search.py)|P5共用s_in搜索，0.05m样本、第一连续IK可接受前缀；Core同步原地段开始内部调用，rollout同步progress可为None|
|[risk.py](../../../../src/task7_sim/risk.py)|P6段初＋已提交状态的投影格并集、最小间隙/未知比例/最近未知；只读冻结Grid与机器人运动学|
|[kinematics.py](../../../../src/task7_sim/kinematics.py)|预计算并按device/dtype缓存固定变换及同精度逆；IK合同、地图隔离、接受判据未改变|
|[perception.py](../../../../src/task7_sim/perception.py)|完整车体/臂/夹爪自遮挡和G1报告；LocalCollision从Grid批量打包柱体，不接真值|
|[core.py](../../../../src/task7_sim/core.py)|P2默认15×0.1m未来点并重复末端；内部s_in、自动P6/f_k；P7逐尝试abs(det J)仅诊断；L.0观测缓存、独立张量、路线批量光栅化|
|[bench_full.py](../../../../src/task7_sim/bench_full.py)、[profile_full.py](../../../../src/task7_sim/profile_full.py)|固定完整几何夹具与有界计时；脚本策略，不实现候选生成器或网络|
|[tests/](../../../../src/task7_sim/tests/)|新增robot/capsule_fit/completion/full_geometry/optimization；调整旧同步原地cap测试服从内部s_in；P4继续验证拒绝|

#### 完整机器人几何与G1

- 8条UR5 base/shoulder/upper/forearm/wrist1–3/固定夹爪胶囊，8个固定车体URDF支撑盒包络；底盘与环境仍为0.99×0.67矩形。拟合固定最长局部AABB轴，对全顶点作外接包含检查、再加已定0.02m，推导见SRC-0426；车体无额外膨胀。
- seed20261021、限位内独立均匀10000组q，原始输入[allowed_pair_samples.npz](../../../../results/task7/t7.14-r2-20261021-0000/allowed_pair_samples.npz)；配置副本[robot_geometry.json](../../../../results/task7/t7.14-r2-20261021-0000/robot_geometry.json)。120个非对角无序对：相邻15，Always22，其中非相邻Always8，允许并集23。仅“每组都接触”才归Always，不采用Never对。
- 初版重复延长端帽导致10000/10000拒绝，保留robot_geometry_overlong_v1.json；修正外接构造后同样本628合法、9371自碰撞、3106碰地（类别可重叠）。计时前选首合法索引5固定到fixture.json，未按吞吐筛样本；全部失败计数保留。
- **G1报告**：[g1_final.json](../../../../results/task7/t7.14-r2-20261021-0000/g1_final.json)显示原点(0,0,0.5m)在3219/10000组中落入胶囊包络，其中234组通过自碰撞/地面检查；固定车体相交0组。零位/名义位/计时初态不相交，最终有效像素分别7161/7162/7843。相交合法样本实际渲染origin_inside_self=True、valid全False，测试证明没有移动原点或回填伪造点。此为保守包络结果，不是精细网格真实接触概率。
- A.5：完整肘/前臂高障碍而底盘/工具点空闲、端点安全但中点碰撞、地面/折臂/车体/允许邻接、自遮挡、LocalCollision已观测柱体、失败半步回退与单次计数均有用例。独立肘部测试夹具为同样本索引31（elbow_fixture.json），没有替换计时初态。
- B.14第1条：只移动墙后被遮挡真值盒子时，实际机器人自遮挡后的Grid及自动f_k推演逐元素相同；TruthCollision仍能区分隐藏盒子。局部模块没有读取真值补全。

#### 测试命令、退出码与结果

最终实际执行为容器stdin脚本`cache_ownership_fix.input.py`中的`pytest.main(['-q','src/task7_sim/tests','--junitxml=results/task7/t7.14-r2-20261021-0000/pytest-final.xml'])`，随后逐个py_compile；**退出0，73 passed in31.99s**。每个用例的名称/耗时在[pytest-final.xml](../../../../results/task7/t7.14-r2-20261021-0000/pytest-final.xml)。便于Claude复核的等价命令（尚未由Claude执行本轮复核）：

```bash
sg docker -c 'docker exec -e CUDA_VISIBLE_DEVICES=0 -e PYTHONPATH=/root/mm_husky_ws/src -w /root/mm_husky_ws forem-dev timeout 580s python3 -B -m pytest -q -p no:cacheprovider src/task7_sim/tests'
```

所有历史调用实际外层命令为`sg docker -c 'docker exec -i -e CUDA_VISIBLE_DEVICES=0 -e PYTHONPATH=/root/mm_husky_ws/src -w /root/mm_husky_ws forem-dev timeout 580s python3 -u -'`，stdin是下表同名input.py（wrapper附PID记录前缀）。input.py保留当时改代码和测试的精确顺序；**历史编辑脚本仅作证据，不应重放覆盖最终源**。本表列测试调用的真实入口；其他核查/计时调用逐条见[commands.jsonl](../../../../logs/task7/t7.14-r2-20261021-0000/commands.jsonl)。

|label|stdin中的测试入口|退出|实际结果|脚本 / 日志|
|---|---|---|---|---|
|robot_red|`pytest.main(['-q', 'src/task7_sim/tests/test_robot.py'])`|2|1 error in 1.38s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/robot_red.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/robot_red.log)|
|robot_build|`pytest.main(['-q', 'src/task7_sim/tests/test_robot.py'])`|0|2 passed in 1.93s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/robot_build.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/robot_build.log)|
|completion_red|`pytest.main(['-q', 'src/task7_sim/tests/test_completion.py'])`|2|1 error in 1.45s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/completion_red.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/completion_red.log)|
|completion_green|`pytest.main(['-q', 'src/task7_sim/tests/test_completion.py'])`|0|4 passed in 3.18s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/completion_green.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/completion_green.log)|
|integration_probe|`pytest.main(['-q', 'src/task7_sim/tests/test_core.py', 'src/task7_sim/tests/test_contracts.py', 'src/task7_sim/tests/test_completion.py'])`|1|1 failed, 19 passed in 24.61s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/integration_probe.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/integration_probe.log)|
|capsule_fit_red|`pytest.main(['-q', 'src/task7_sim/tests/test_capsule_fit.py'])`|2|1 error in 1.45s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/capsule_fit_red.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/capsule_fit_red.log)|
|capsule_fit_fix|`pytest.main(['-q', 'src/task7_sim/tests/test_capsule_fit.py', 'src/task7_sim/tests/test_robot.py'])`|0|3 passed in 2.16s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/capsule_fit_fix.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/capsule_fit_fix.log)|
|full_geometry_tests|`pytest.main(['-q', 'src/task7_sim/tests/test_completion.py', 'src/task7_sim/tests/test_full_geometry.py', 'src/task7_sim/tests/test_contracts.py::test_synchronous_inplace_raw_action_penalty_and_cap'])`|0|9 passed in 27.94s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/full_geometry_tests.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/full_geometry_tests.log)|
|cache_red|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py::test_observation_reuse_count'])`|1|1 failed in 1.42s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/cache_red.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/cache_red.log)|
|cache_fix|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py'])`|0|3 passed in 20.57s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/cache_fix.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/cache_fix.log)|
|raster_tests|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py', '-k', 'raster'])`|0|1 passed, 3 deselected in 4.34s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/raster_tests.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/raster_tests.log)|
|raster_implementation|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py'])`|0|4 passed in 24.72s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/raster_implementation.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/raster_implementation.log)|
|raster_sparse|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py'])`|0|4 passed in 16.49s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/raster_sparse.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/raster_sparse.log)|
|fixed_mount|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py'])`|0|5 passed in 16.47s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/fixed_mount.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/fixed_mount.log)|
|batch_geometry_tests|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py', '-k', 'batched_local'])`|0|1 passed, 5 deselected in 3.27s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/batch_geometry_tests.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/batch_geometry_tests.log)|
|batch_geometry|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py', 'src/task7_sim/tests/test_completion.py', 'src/task7_sim/tests/test_full_geometry.py'])`|0|14 passed in 19.84s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/batch_geometry.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/batch_geometry.log)|
|final_contracts|`pytest.main(['-q', 'src/task7_sim/tests/test_completion.py', 'src/task7_sim/tests/test_full_geometry.py'])`|0|13 passed in 7.11s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/final_contracts.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/final_contracts.log)|
|sync_rollout_none_red|`pytest.main(['-q', 'src/task7_sim/tests/test_completion.py', '-k', 'sync_rollout_accepts'])`|1|1 failed, 7 deselected in 1.46s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/sync_rollout_none_red.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/sync_rollout_none_red.log)|
|final_integration|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py', 'src/task7_sim/tests/test_completion.py', 'src/task7_sim/tests/test_kinematics.py'])`|0|21 passed in 16.95s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/final_integration.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/final_integration.log)|
|fixed_ik_complete|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py', 'src/task7_sim/tests/test_kinematics.py'])`|1|1 failed, 13 passed in 16.37s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/fixed_ik_complete.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/fixed_ik_complete.log)|
|fixed_ik_reference_path|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py', '-k', 'fixed_kinematics'])`|0|1 passed, 6 deselected in 3.61s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/fixed_ik_reference_path.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/fixed_ik_reference_path.log)|
|final_suite|`pytest.main(['-q', 'src/task7_sim/tests', '--junitxml=results/task7/t7.14-r2-20261021-0000/pytest-final.xml'])`|1|1 failed, 71 passed in 30.24s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/final_suite.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/final_suite.log)|
|verified_suite|`pytest.main(['-q', 'src/task7_sim/tests', '--junitxml=results/task7/t7.14-r2-20261021-0000/pytest-final.xml'])`|0|72 passed in 29.11s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/verified_suite.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/verified_suite.log)|
|precision_manifest|`见脚本`|0|见原始日志|[input](../../../../logs/task7/t7.14-r2-20261021-0000/precision_manifest.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/precision_manifest.log)|
|final_cleanup|`见脚本`|0|见原始日志|[input](../../../../logs/task7/t7.14-r2-20261021-0000/final_cleanup.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/final_cleanup.log)|
|cache_ownership_red|`pytest.main(['-q', 'src/task7_sim/tests/test_optimization.py', '-k', 'tensor_ownership'])`|1|1 failed, 8 deselected in 3.09s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/cache_ownership_red.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/cache_ownership_red.log)|
|cache_ownership_fix|`pytest.main(['-q', 'src/task7_sim/tests', '--junitxml=results/task7/t7.14-r2-20261021-0000/pytest-final.xml'])`|0|73 passed in 31.99s|[input](../../../../logs/task7/t7.14-r2-20261021-0000/cache_ownership_fix.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/cache_ownership_fix.log)|
|final_cleanup_v3|`见脚本`|0|见原始日志|[input](../../../../logs/task7/t7.14-r2-20261021-0000/final_cleanup_v3.input.py) / [log](../../../../logs/task7/t7.14-r2-20261021-0000/final_cleanup_v3.log)|

失败记录解释：robot_red/completion_red/capsule_fit_red/cache_red/sync_rollout_none_red是实现前缺失接口的预期失败；integration_probe中旧外部cap断言被P5内部搜索合同取代；valid_fixture暴露初版过长包络，按原余量和允许对规则修正，未放宽接受；fixed_ik_complete为加载旧快照的URDF相对路径错误，修正测试显式路径；final_suite为测试误以为失败尝试会进入trace，修正为仅段初/提交状态；cache_ownership_red暴露缓存张量别名，修复返回/缓存所有权后通过。当前无遗留失败测试，原日志和中间XML均保留。

|最终测试模块|用例数|
|---|---|
|test_capsule_fit.py|1|
|test_completion.py|8|
|test_contracts.py|7|
|test_core.py|9|
|test_full_geometry.py|7|
|test_geometry.py|10|
|test_kinematics.py|7|
|test_motion.py|6|
|test_optimization.py|9|
|test_perception.py|7|
|test_robot.py|2|

#### GPU float32与CPU float64

[precision.json](../../../../results/task7/t7.14-r2-20261021-0000/precision.json)是precision_v3实际退出0产生的逐字段误差。CPU64从相同物理夹具独立渲染扫描/累积Grid，E1 K13参考分别与GPU实际E1/16/64/256输出比对；单/双动作执行也逐状态/奖励/mask比较。沿现有绝对1e-4、相对0的对照要求，离散字段精确一致；不以float32通过替代float64核对。单位按各字段分别列出。

|E|执行q最大差(rad，单/双动作较大值)|f_k最大位置残差字段差(m)|f_k SO(3)诊断字段差(rad)|mask与前6个离散字段|
|---|---|---|---|---|
|1|3.81225e-06|1.123433e-06|5.549855e-06|精确一致|
|16|3.81225e-06|8.945663e-07|3.893664e-06|精确一致|
|64|3.81225e-06|9.429033e-07|3.90531e-06|精确一致|
|256|3.81225e-06|9.429033e-07|3.90531e-06|精确一致|

所有E的最小间隙字段差4.768372e−9 m，未知比例/最近未知距离差0；执行底盘差0，奖励最大差8.940697e−10。另完整机器人同步K3、progress=None、内部s_in对照通过，结束one-hot精确一致，各字段差在同一JSON的synchronous_full_robot_no_external_progress。机器人胶囊/自碰撞、渲染、栅格、LocalCollision、DLS与已知奇异输入84/249仍有CPU64/GPU32专项测试。分支跳变只诊断，没有增加速度失败条件或平滑。

#### 优化前后（相同输入）

采用逐元素torch.equal核对原始快照与最终版本的完整转移、状态、奖励、mask、上一动作、完整CPU64/GPU32 f_k、路线边界、碰撞和风险。固定变换另逐字段比对原版解析→DLS结果（包含拒绝）；观测张量所有权反例也与原始重新构造行为一致。物理0.05s子步、0.1s动作、观测内容/奖励/终止均未修改。

下表为完整几何相同夹具GPU同步墙钟p50；中间阶段各5个样本，最终v3各8个样本，完整分布/吞吐/版本在各目录profile.json。单项微小波动不当作统计显著收益。

|阶段（产物目录）|E|观测(ms)|固定变换(ms)|两动作端到端(ms)|K13短段推演(ms)|
|---|---|---|---|---|---|
|baseline|1|16.811|0.200|170.458|387.429|
|baseline|16|16.867|0.205|179.991|4056.213|
|cache|1|16.755|0.194|153.872|334.711|
|cache|16|16.844|0.197|162.724|3466.144|
|raster（负收益，未采用）|1|7.893|0.190|126.266|340.090|
|raster（负收益，未采用）|16|22.106|0.197|177.907|3467.198|
|raster_sparse|1|8.131|0.188|127.257|308.597|
|raster_sparse|16|8.382|0.204|136.886|2920.386|
|fixed_mount|1|8.077|0.149|125.538|305.642|
|fixed_mount|16|8.214|0.154|135.550|2898.059|
|batched_columns_risk|1|8.172|0.159|128.846|165.157|
|batched_columns_risk|16|8.371|0.160|138.387|456.879|
|最终v3（含张量隔离/设备常量缓存）|1|8.074|0.132|127.148|164.223|
|最终v3（含张量隔离/设备常量缓存）|16|8.332|0.136|137.372|457.923|

- 缓存：执行2动作观测4→3次，推演2动作6→3次；初始观测后复用after。返回张量与缓存隔离，允许调用方原地处理观测，不污染下一步。
- 光栅化：取消逐路线节点Python循环；密集广播版E16更慢且临时显存较大，源留raster_dense_rejected.py，不采用。分块扫描数据raster_chunk_profile.json也保留；采用XY范围预筛＋原精确距离，闭接触判据不变。
- 固定变换：URDF CPU递归预计算，device/dtype常量和同精度逆缓存；不以CPU64逆转float32替换GPU32求逆。
- 实际热路径中的逐环境局部柱体与间隙计算改为批量索引/归约，风险采样集合不变；非平凡未知近邻保持原算法。E16短段推演有实测收益后采用；没有凭增加线程假定加速，最终torch CPU线程2。

#### 最终完整几何E扩展

最终以final_v3_E1_E16_E64/profile.json和final_v3_E256/profile.json为准；v2为缓存张量隔离前中间版本，不作当前验收。GPU0 float32；每项warmup1次、同步墙钟8次，原始samples_ms/版本/峰值均保留。下表延迟为整个E批的wall ms，吞吐为有效转移/s或候选/s；不是将批耗时当单环境耗时。

单转移只计Core.step，初始Core/begin在外，包含2个0.05s子步、完整碰撞、动作末扫描/栅格/观测；这是段首转移（2次观测）。两动作端到端含新Core/begin，共3次观测，数据也在原始JSON。推演计E×K组装、脚本转移、P6/f_k，不渲染、不读真值；K=13短候选，进度0.015–0.03m、底盘目标在到达容差内，所有候选本夹具结束为到达，不能代表困难/长段分布。

|测量|E|p50(ms)|p95(ms)|p99(ms)|max(ms)|吞吐(/s)|8次样本累计有效IK / DLS|
|---|---|---|---|---|---|---|---|
|单转移|1|67.156|67.232|67.236|67.237|14.895|16 / 0|
|K13推演|1|164.223|165.758|166.348|166.496|79.034|352 / 0|
|单转移|16|72.263|72.359|72.379|72.384|221.499|256 / 0|
|K13推演|16|457.923|460.880|461.361|461.481|453.678|5632 / 0|
|单转移|64|111.511|111.672|111.693|111.699|573.892|1024 / 0|
|K13推演|64|1403.299|1404.783|1405.234|1405.347|592.869|22528 / 0|
|单转移|256|266.859|269.079|269.850|270.043|957.749|4096 / 0|
|K13推演|256|5283.964|5289.912|5291.489|5291.883|629.801|90112 / 0|

最终这些测量加两动作端到端合计有效IK **134800次、DLS回退0次（0%）**，仅是该固定短段夹具的实际触发率；失败/提前结束未删样本。DLS另强制直接调用作分项耗时，不把强制调用混入自动回退率。原计数/结束类型/实际提交仿真时长均在JSON。8样本p99为本批插值描述，不作总体尾延迟保证，不设速度门槛，不承诺训练工期。

#### 完整几何分项计时

[full_parts.json](../../../../results/task7/t7.14-r2-20261021-0000/full_parts.json)：最终v3源，GPU32，8次同步墙钟样本＋1次warmup，原始p50/p95/p99/max与吞吐全部保留；这里列p50。DLS64是直接调用，不是本场景自动回退频率。

|分项|E1 p50(ms)|E16 p50(ms)|
|---|---|---|
|robot_capsules|2.831|2.875|
|FK_world_tcp|1.717|1.727|
|IK_analytic_dispatch|10.430|10.448|
|DLS64_direct|277.489|273.554|
|truth_collision|3.347|3.390|
|panorama_360x90|3.905|5.239|
|grid_update|0.392|3.455|
|local_crop|0.477|0.470|
|local_collision|4.543|4.570|
|risk_committed_trace|26.521|27.011|

分项不能相加替代端到端；初次几何/渲染初始化在这里的稳态计时外。重复grid_update使用同一已填充Grid与相同落点，最高值更新幂等；风险分项使用段初＋两个提交子步。实际命令入口为full_parts_v3.input.py，退出0；最终E扩展为final_v3_small_medium.input.py、final_v3_E256.input.py，均退出0；精度/清单为precision_v3.input.py、final_cleanup_v3.input.py，均退出0，完整命令与日志见账本。

#### 未通过项、限制、预算与交接

- **当前未通过测试：无。** 预期red、暴露问题的旧夹具/旧包络、负收益优化与中间计时全部保留并在上文解释，没有用旧通过替代最终验证。
- G1：部分无碰撞关节姿态仍让原点落入保守胶囊，报告全自遮挡；没有移动相机、过滤姿态或改变复位分布。后续若需改变安装或姿态范围，属于另行用户决定，本轮未做。
- 胶囊/固定车体盒是保守包络，夹爪固定URDF零关节；10000组Always表不是恒接触证明；离散提交状态扫过不覆盖子步之间连续扫掠或分支跳变。最近未知用格中心欧氏距离，间隙与局部柱体几何计算，沿SRC-0426；未知不读真值补全。
- 性能来自重复同一地图/初态和短段脚本，不覆盖多地图、长段、困难DLS分布或训练更新。库没有自动复位/候选生成器/网络/G7/训练；这是TASK明确范围，不当成已实现能力。测试/计时复核需要本run保存的几何采样/原版快照与task7.6历史奇异样本产物；不把运行产物纳入git。
- 新数值/方法与等价核对统一登记SRC-0426/0427/SRC-0428。**本轮无新增阻塞参数或遗留待决定实现**；已定G1相交现象交用户/Claude知悉，不自拟新设计。
- 预算：承接r1 232.905596s＋Claude约30s保守预留；本轮调用合计744.526217s，任务累计**1007.431813s（16.791分钟）**，最长单调用59.045452s，未超10分钟/90分钟。账本commands.jsonl逐调用记录。只用GPU0；收尾四卡均14MiB/0%，forem-dev仅原入口与sleep（final-resources-*.log）。所有本任务Python/PID/工具session均已退出，无后台任务需恢复；任务文件归还workspace UID/GID1004。
- 当前负责人Codex，PROGRESS本行→review。下一步Claude按本节最终命令复核代码/输出、几何允许表、G1报告、CPU64对照和计时版本；本轮没有发起新的文档设计复核或扩大授权。通过后由复核方依共同约定更新状态，不在此自标done。

## Claude复核 r2-20261021-0000（2026-10-21T09:00–09:20，claude-opus-5-5，推理强度未知；只读核查＋重跑测试）

- 重跑：确认forem-dev只有入口与sleep、GPU无compute进程后，执行上文“便于Claude复核的等价命令”，**73 passed in 33.11s**，退出0；与Codex最终结果一致。墙钟约40 s，计入本任务容器预算（累计约1047 s）。
- 读码：`search.py`（P5：0.05 m采样、对每个样本独立判IK可接受、cumprod取第一段连续前缀、首样本不可达返回s_cur，与R4一致；可接受用N1同一IK合同）；`risk.py`（P6：段初＋已提交状态的底盘矩形与胶囊水平投影格并集、间隙对“高度高于胶囊最低点”的已观测格、未知比例与最近未知距离均无则3.2，与SRC-0425一致；只读冻结Grid）；`robot.py`（P3：碰撞网格外接胶囊＋0.02 m、固定车体盒、10000组均匀q的Always表）。信息隔离：risk/search不引用真值接口；LocalCollision只接Grid；B.14第1条有逐元素测试。
- 允许对核对（`config/task7/robot_geometry.json`）：Always的8个非相邻对为UR5底座–上臂、UR5底座–顶板、肩–base_link、肩–顶板、**上臂–顶板**、前臂–wrist2、wrist1–wrist3、wrist2–夹爪。其中“上臂–顶板”因上臂胶囊肩端球帽（半径约0.129 m含余量）恒与顶板重叠而被整对放行，**上臂压到顶板的碰撞不会被检出**；顶板下方约2 cm的base_link与上臂仍检查，故实际漏检限于约2 cm高度带。记为已知限制，属P3规则（整对放行）的直接后果，不是实现错误。
- **G1报告需用户知悉**（g1_final.json）：传感器原点(0,0,0.5 m)落入机械臂包络（主要是上臂，3034/3219）的比例为随机q的32%、无碰撞随机q的37%（234/628）；此时整帧全景无有效像素、栅格本帧不更新。零位、名义位与计时初态不相交。随机q不代表任务中的实际姿态分布，真实发生率尚无数据。
- 性能（完整几何，夹具，非门槛）：执行单转移E1 67 ms、E256 267 ms（约958转移/s）；按此推算阶段L 5M转移的环境部分约1.5小时（推算，未含训练更新与真实地图/长段）。K13短段推演E256约5.3 s（约630候选/s，夹具候选1–2个动作步即到达）；推演每候选步比执行更贵，主要在段开始搜索与P6风险聚合（risk_committed_trace约26.5 ms/调用，最近未知距离仍有逐环境Python循环）。阶段1（20万次决策×13候选）推演会是主要墙钟来源，需在阶段L/阶段1前的端到端核查中再测长段分布。DLS回退率0%只代表短段夹具。
- 结论：TASK“交付与验收”各项均有对应测试与证据，r2无遗留失败测试；**task7.14标done**（含上述已知限制）。G1遮挡与“上臂–顶板”放行作为后续决定/限制记录，不阻塞本任务。
