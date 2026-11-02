# task7.17 — 结果

状态：**review（r2，2026-10-21；完整默认入口/批量reset/E4已交付，原73通过；新增真实池近奇异关节对照1项失败待决定，不标done）**。

## 运行记录

运行记录按run-id追加，见下文；建立时的“尚未执行”状态已由本次实际记录替代。

## 交接

- 当前负责人：Codex；部分交付review，交Claude核验，未完成项与下一步见本run末节。

## run-id：t7.17-r1-20261021（部分交付review）

- 负责人Codex；实际模型/强度：未知。推荐GPT6.1sol/medium；Claude Sonnet5.5/medium（跨代码与合同核对）。授权SRC-0431，范围以TASK为准，不训练/不提交/不启停容器。
- 开工：2026-10-21T10:05+08:00；main，保留并行修改；forem-dev已运行，GPU2空闲。原73项测试退出0，73 passed in 31.74s；原始日志`forem/logs/task7/t7.17-r1-20261021/baseline.log`。

### 原代码核对表（先核对，后实现；依据[SRC-0460](../../../SOURCES.md#src-0460)）

|项|原做法与代码路径:行号（均为只读）|本项目采用/偏离|
|---|---|---|
|栅格/代价|迁入`eeplanner.py:469–518`：0.05m，障碍10000后＋1、低障碍偏好0.25；`map.py:550–591`通过ROS inflation|先提供显式权重A*，不猜测JSON几何到ROS inflation的等价变换；B12膨胀0.40m合同保留待组装|
|A*|迁入`eeplanner.py:590–615`：允许对角、linf，精确端点替换|实现8邻接/linf权重搜索原语；不声称等成本路径tie-break与pyastar一致；严格无碰撞与有限代价的关系待决定|
|高度|迁入`eeplanner.py:52–89,624–637`：障碍高度＋0.25m、interpolate_z_cpp后分段线性|B12:327写起终点高度线性，与照原代码的授权存在冲突；暂停生产高度策略，显式节点线性插值可独立实现|
|姿态|迁入`eeplanner.py:639–653`：按水平累计距离SLERP，use_fwd_orientation可改中途yaw；终点保持原目标|本项目终点TCP接近轴沿最后水平段、手指水平；位置弧长＋禁止同位置异姿态为必须偏离；只实现显式端点SLERP原语|
|末端起点|迁入`eeplanner.py:198–203`、`map.py:351–363`：FK得到实际末端，不独立随机采样|本项目使用现有kin.world_tcp(base,q)，不把目标回填成实际关节|
|末端终点|迁入`simulator_api.py:27–46`：距离/z均匀、随机RPY、XY裁至边界内0.5m；`tasks.py:260–263`wrist转tip|本项目距离0.5–8m、高0.7–1.15m、TCP、明确水平姿态，越界拒绝而不裁剪以保留距离约束；原RPY被合同替代|
|初始关节|迁入`robot_env.cpp:518–548`：固定六关节；上游`mobile-rl/src/robot_env.cpp:509–536`：MoveIt随机采样＋自碰撞拒绝|授权未指定冲突时选哪套，暂停默认关节分布；显式给定q时仍校验关节限位/完整碰撞/FK|
|随机数|原map/goal共享np_random|本项目合同要求地图/初始化/其他流分开，且各环境独立；采用显式按env-id/流编号派生，不用全局RNG|

路径前缀：迁入python文件均在`forem/src/modulation_rl/scripts/modulation/envs/`；迁入C++在`forem/src/modulation_rl/src/`。上游HEAD与精确符号记录于SRC-0460。

### 待决定（仅暂停关联部分，不发起文档复核轮次）

1. task7.5 RESULTS B12:327规定高度线性，task7.17 TASK要求照原代码（障碍抬升）：选B12线性/原障碍抬升？
2. 初始关节：选CBL迁入固定六关节/上游N²M²随机拒绝？不擅自设默认。
3. 原有限障碍代价允许穿越障碍；本项目要求无碰撞路线：保留原代价后拒绝碰撞路径/将膨胀障碍设不可通行？几何到ROS inflation不具现成等价实现。

其余独立部分继续，完整地图→默认任务→环境入口不作为已交付能力。

### 实现进展与偏离更新（10:20）

- 上表A*条更新：原pyastar调用已照搬，直接使用容器安装版后端（[SRC-0461](../../../SOURCES.md#src-0461)）；不保留初版自写算法。30个固定权重图与后端路径逐元素一致。原pyastar内部C++源码未取回，不能宣称仅tie-break不同；初版与后端连总格权重也不同，失败日志保留。
- 原迁入/上游eeplanner仅两处height_preference不同：迁入均True；上游generate_base_feasible取eval、update_weights为False。其余被核对的A*、高度、姿态流程相同；本项目地图到权重生成尚未定，未选择任一分歧值。
- 可用实现：`routes.py`（原后端A*、显式节点线性高度/SLERP、合同水平TCP终姿态）；`episode.py`（raw base/goal proposal、按env/用途分流、显式joint-policy有界初态拒绝、实际FK/完整碰撞/IK核验、终点位置与给定base位姿IK见证验证）；`env.py`（每环境独立Core的batch facade，显式reset与段begin，无自动重置，inactive环境不产生转移）；对应三个测试。
- `core.py`仅增加sensor_frames/origin_inside_self_frames/fully_occluded_frames和record_render；旧render_count仍只计动作末渲染。reset通过新建所选环境Core实现，无旧Core begin/reset语义改动。初始scan由wrapper执行并计入sensor_frames。
- 默认采样→地图代价→完整任务组装未实现：关节来源/高度策略/障碍代价与严格碰撞保证的待决定项未解决；不称已可训练。给定proposal越界或碰撞不自动裁剪，不自行设搜索半径或重试次数。
- 首次原73＋本任务18项联合运行：90 passed、1 failed in 38.06s（退出1），原73均通过，唯一失败是完整CPU64/GPU32观测对照；连续状态、奖励、结束mask单独对照通过。原始XML：`forem/results/task7/t7.17-r1-20261021/own_and_original.xml`。后续新增的reset校验/原后端对照将计入最终全套，不拿此中间统计当最终结论。
- 已确认越界栅格反例：[SRC-0462](../../../SOURCES.md#src-0462)。本任务没有权限修perception.py，停止该部分验收并报告，不删测试、不放宽容差。

### 最终改动与验证（2026-10-21T10:24:36+08:00后收尾）

**结论：部分交付，待Claude复核；完整task7.17未完成。** 原73/73保留；本任务20例中19通过、1失败；包含并行模块的全套为146 passed / 1 failed / 1 warning（56.07s，退出1）。证据统一登记[SRC-0464](../../../SOURCES.md#src-0464)。

实际改动文件：

- `forem/src/task7_sim/episode.py`、`routes.py`、`env.py`；`tests/test_episode.py`、`test_routes.py`、`test_env.py`。
- `forem/src/task7_sim/core.py`只加12行G1计数相关；[原始快照](../../../../results/task7/t7.17-r1-20261021/core_before.py)、[差异](../../../../results/task7/t7.17-r1-20261021/core.diff)、[源码SHA256清单](../../../../results/task7/t7.17-r1-20261021/source_manifest.json)。
- 本RESULTS、所属独立日志、PROGRESS本任务一行、SOURCES预留SRC-0460–0464。其他工作树改动属并行方，本任务未改。没有训练、启停容器、修改参考仓库或Git提交。

### 实际命令、退出码与原始日志

工作目录为仓库根。下表命令均为`python3 forem/logs/task7/t7.17-r1-20261021/run.py <名称>`；每条的实际Python输入（包括pytest参数）和容器命令保存在对应input文件与[commands.jsonl](../../../../logs/task7/t7.17-r1-20261021/commands.jsonl)。统一在forem-dev内、CUDA_VISIBLE_DEVICES=2、PYTHONPATH=/root/mm_husky_ws/src、timeout600执行。红阶段退出非零保留，不当作当前回归。

|名称|退出码|命令wall秒|输入与日志|结果/用途|
|---|---|---|---|---|
|precision_probe|0|4.053004|[input](../../../../logs/task7/t7.17-r1-20261021/precision_probe.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/precision_probe.log)|定位既有Grid离散反例；旧/新版一致|
|additional_red|2|2.111637|[input](../../../../logs/task7/t7.17-r1-20261021/additional_red.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/additional_red.log)|预期缺sample_initial导入失败|
|action_red|1|2.587241|[input](../../../../logs/task7/t7.17-r1-20261021/action_red.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/action_red.log)|暴露非法第二行动作前第一行已提交|
|new_tests|1|8.377572|[input](../../../../logs/task7/t7.17-r1-20261021/new_tests.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/new_tests.log)|15通过、1个GPU观测失败（中间版本）|
|own_and_original|1|40.101718|[input](../../../../logs/task7/t7.17-r1-20261021/own_and_original.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/own_and_original.log)|90通过、1个GPU观测失败（中间版本）|
|astar_reference|1|1.727456|[input](../../../../logs/task7/t7.17-r1-20261021/astar_reference.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/astar_reference.log)|暴露自写A*与原后端不同，已弃用自写版|
|routes_green|0|2.828635|[input](../../../../logs/task7/t7.17-r1-20261021/routes_green.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/routes_green.log)|5通过，含30图原后端路径逐元素一致|
|reset_validation_red|1|2.328897|[input](../../../../logs/task7/t7.17-r1-20261021/reset_validation_red.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/reset_validation_red.log)|暴露reset缺初态校验|
|reset_validation_green|0|12.471978|[input](../../../../logs/task7/t7.17-r1-20261021/reset_validation_green.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/reset_validation_green.log)|14通过、1项已知GPU观测失败被单独排除（非全套）|
|profile_E16|0|8.433681|[input](../../../../logs/task7/t7.17-r1-20261021/profile_E16.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/profile_E16.log)|E16两回合计时|
|profile_E64|0|23.391934|[input](../../../../logs/task7/t7.17-r1-20261021/profile_E64.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/profile_E64.log)|E64两回合计时|
|profile_E256|0|84.751334|[input](../../../../logs/task7/t7.17-r1-20261021/profile_E256.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/profile_E256.log)|E256两回合计时|
|map_integration|0|3.304920|[input](../../../../logs/task7/t7.17-r1-20261021/map_integration.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/map_integration.log)|6张地图读入/显式q初态通过|
|profile_threads1|0|8.517129|[input](../../../../logs/task7/t7.17-r1-20261021/profile_threads1.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/profile_threads1.log)|同输入E16线程1对照|
|final_suite|1|58.168212|[input](../../../../logs/task7/t7.17-r1-20261021/final_suite.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/final_suite.log)|最终全套146通过、1失败、1 warning|
|equivalence|0|23.486183|[input](../../../../logs/task7/t7.17-r1-20261021/equivalence.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/equivalence.log)|10场景旧/新Core逐元素相同|
|provenance|0|0.223559|[input](../../../../logs/task7/t7.17-r1-20261021/provenance.input.py) / [log](../../../../logs/task7/t7.17-r1-20261021/provenance.log)|保存后端安装commit、二进制SHA及wrapper源码|

早期手工启动的命令（先于runner账本）：

|测试|实际pytest参数|退出码|pytest内部耗时|原始日志|
|---|---|---|---|---|
|开工基线|`['-q','src/task7_sim/tests']`（当时只有原73）|0|31.74s|[baseline.log](../../../../logs/task7/t7.17-r1-20261021/baseline.log)|
|首次RED|`['-q','src/task7_sim/tests/test_routes.py','src/task7_sim/tests/test_episode.py','src/task7_sim/tests/test_env.py']`|2|0.14s|[red.log](../../../../logs/task7/t7.17-r1-20261021/red.log)（三个模块尚未实现）|
|首轮实现|同首次RED参数|1|5.24s|[green1.log](../../../../logs/task7/t7.17-r1-20261021/green1.log)（10 passed、1 GPU观测失败）|

三次实际容器调用同样是`sg docker -c 'docker exec -e CUDA_VISIBLE_DEVICES=2 -e PYTHONPATH=/root/mm_husky_ws/src -w /root/mm_husky_ws forem-dev timeout 600 python3 -u -c ...'`，Python前置`torch.set_num_threads(2)`。基线工具session2316退出0；RED session64484由尾部tail令shell显示0，但pytest实际退出2，未混淆；首轮实现session93183退出1。手工调用未采集完整wall，预算分别保守预留60/5/10s，不能把pytest内部计时当命令wall。

最终原11模块73例全部通过；本任务routes5/episode5/env10（env失败1）；并行candidates20/search11/mapgen23也通过，模块统计见[test_counts.json](../../../../results/task7/t7.17-r1-20261021/test_counts.json)。全套原始[XML](../../../../results/task7/t7.17-r1-20261021/final-suite.xml)可复查唯一失败，不用“排除失败”的小套件代替。

### Core语义等价与精度限制

- [equivalence.json](../../../../results/task7/t7.17-r1-20261021/equivalence.json)：CPU64与GPU32各5场景（零提交失败、半步提交失败、路线终点半步、零推进、120动作段超时）。所有Transition字段、状态、队列、回合计数/结束、attempts、trace、f_k均逐元素torch.equal。原73仍通过。此为每个精度内旧/新版本等价，不是CPU/GPU互相相等。
- GPU/CPU连续base/q/s、奖励、mask与离散结束对照通过；完整观测对照失败，见[SRC-0462](../../../SOURCES.md#src-0462)和[precision_probe.json](../../../../results/task7/t7.17-r1-20261021/precision_probe.json)。当前未通过项恰为`test_env.py::test_wrapper_cpu64_gpu32`，不放宽1e-4容差、不边界吸附、不删测试。
- `perception.py`非本任务归属，停止相关修复与验收并报告；未擅自修改。

### 有界计时与地图集成

依据[SRC-0463](../../../SOURCES.md#src-0463)。GPU2 float32、线程2；每项E1预热一次、测两个完整夹具回合，路线0.03m、每回合2动作×2子步，terminated后100%全员reset；reset含初态碰撞/IK/FK校验与初始扫描，begin单计。结果是整个E批wall，步进吞吐按有效转移计。

|E|reset p50(ms)|step p50(ms)|step转移/s|含reset/begin转移/s|
|---|---|---|---|---|
|16|484.558|1011.266|15.822|12.721|
|64|1922.204|4011.740|15.953|12.825|
|256|7793.462|16297.878|15.708|12.620|

逐样本分布/实际尝试与提交/scan与G1/源码SHA/峰值GPU内存在[产物目录](../../../../results/task7/t7.17-r1-20261021/)。G1本夹具均0，不能代表真实任务比例。线程1同输入E16 step p50=1041.497ms，未见比线程2快，不采用新线程设置；无包级全局线程修改。当前逐环境E1 Core串行封装不具E维张量融合，**不把它称为性能已优化或阶段L就绪**，没有外推训练工期/设门槛。

地图池`results/task7/maps/a/20261021T021400Z`两档×三split各首张，共6张读入与合法初态核对通过，原始输入/地图SHA/实际FK在[map_integration.json](../../../../results/task7/t7.17-r1-20261021/map_integration.json)。所用q明确为诊断夹具，不是默认关节政策；未完成B12整回合组装。这不替代task7.16全面验收；收尾时task7.16已有最终RESULTS、状态review，仍待其Claude复核。

### 预算、资源与交接

- runner逐调用wall累计 **286.865089s**，最长 **84.751334s**；加手工3次75s和只读容器小命令/收尾30s的保守预留，累计 **391.865089s（6.531分钟）**，小于90分钟；所有命令小于10分钟。runner实测与预留分开，不声称全程每秒已精确计量。没有后台Python/未结束session；E256期间宿主PID2311730已退出；10:24:36核查forem-dev仅原入口/sleep、无GPU compute进程。日志/产物已归还UID/GID1004。
- 推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（跨源/合同与生命周期复核）；本次实际模型/强度均未知，未把推荐冒充实际。
- 当前负责人Codex，部分交付标review；接收方Claude先读本节、[独立日志](../../../agent_logs/task7/task7.17/20261021-codex-episode.md)，核对manifest/core.diff/XML/原始输入，再复核独立reset和已知反例。不发起新的文档复核轮次，不要求恢复完整聊天。
- 剩余：①高度线性还是原障碍抬升；②CBL固定q还是上游随机q；③有限障碍代价后拒绝碰撞路线还是膨胀障碍不可通行（含JSON到原代价/膨胀映射）；④只读perception栅格边界精度问题；⑤前三项明确后组装完整默认任务采样→路线→环境入口，完成真实任务分布与E维批量执行的必要核查。前三项未私定；第④项需要对应模块范围授权，不能在本任务偷偷修。
- 风险：当前只是显式策略/初态输入组件与串行batch封装，尚不能作为阶段L正式训练环境；小夹具计时/6图读入不证明任务分布或训练可行；保留所有失败证据。不标done、不进入训练。

## Claude复核 t7.17-r1-20261021（2026-10-21T11:00–11:15，claude-opus-5-5，推理强度未知）

- 全目录GPU回归（GPU3，10:50）：146 passed，唯一失败为本任务`test_env.py::test_wrapper_cpu64_gpu32`，与Codex报告一致。
- 可接受部分：原代码核对表逐项有出处；A*直接调用原pyastar后端，30图逐元素一致；core.py仅12行G1计数且新旧版本10场景逐元素等价；原73项不回退；6张地图池读入通过。
- 观测对照失败：SRC-0462反例为障碍面x＝−1.8 m正落在0.05 m栅格线上（墙内侧±4.85 m同样在栅格线上），float32/float64 floor分到两侧，属task7.14/7.15已接受的擦边精度合同；按E4改测试口径，不改perception.py。
- **阻塞问题**：`env.py`为支持独立reset改成逐环境E1 Core串行，E16/64/256步进吞吐均约16转移/s（task7.14批量Core E256约958转移/s），阶段L 5M转移仅环境即约87小时以上；按E5返工为单个批量Core＋掩码reset。
- 待决定①–③已由用户确定为E1–E3（[SRC-0437](../../../SOURCES.md#src-0437)）。
- 结论：**返工（r2）**：E1–E3组装完整默认任务采样→路线→环境入口；E4测试口径；E5批量reset与等价测试；完整任务分布下的reset/步进吞吐（E＝16/64/256）与重采样率。


## run-id t7.17-r2-20261021（Codex，2026-10-21，执行记录）

本轮依据用户确定E1–E5（[SRC-0437](../../../SOURCES.md#src-0437)），续用r1预算391.865089s；实际模型/强度未知。推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium：跨原代码、精度与批量生命周期核验。**状态review：本轮实现与规定计时已交付；最终回归152通过/1近奇异关节精度失败，原73通过。最终命令/预算/交接见本run末节，不标done。**

### 改动及合同对应

- `episode.py`：默认EpisodeSampler从task7.16固定地图池按split（可显式difficulty）抽图，B12原始底盘/目标分布，CBL固定六关节与实际FK起点；碰撞/限位/N1验证后原代价规划；无上限换proposal seed/map重采样，记录拒绝原因和IK见证数。[SRC-0465](../../../SOURCES.md#src-0465)、[SRC-0466](../../../SOURCES.md#src-0466)。
- `routes.py`：保留同安装pyastar后端；.05m闭格相交栅格，原高/低障碍代价及.40m膨胀，原障碍抬升高度、水平末段目标姿态与原XY弧长SLERP；3D弧长交Core。规划后分析每个TCP线段与全部OBB的XY交段，最低高度不得低于障碍顶。ragged route按原终点/s/quat原值padding，不重采样。
- `env.py`：整个E批只有一个Core，step是E维张量路径；只有reset/规划的host初始化逐环境。默认入口`EpisodeEnv(E,seed=...,split='train',device='cuda',dtype=torch.float32,synchronous=False); env.reset()`，默认池`forem/results/task7/maps/a/20261021T021400Z`。begin接全批Candidate和可选bool mask，step接[E,3]，reset只选实际terminated/truncated行。初次reset全批；reset只渲染选中行。
- `core.py`：按E5加masked reset/begin与每行first状态，保留未选中start/cap/timeout/queue/grid/counters/有效历史；G1计数支持选中初始扫描。不改子步、奖励、动作、观测或结束判据；其他task7_sim模块只读。
- 对应三个tests：先red再green；原Core快照逐元素比较、异步masked reset/RNG与ragged路线/地图padding、完整真实池入口与E4带内统计。当前新增真实池CPU/GPU连续字段存在近奇异q差，失败保留，[SRC-0467](../../../SOURCES.md#src-0467)。

### 原代码落实及工程限制

r1核对表继续有效；r2补充原出处见SRC-0465：eeplanner.py:52–89/624–637、myutils.cpp:452–484高度插值，robot_env.cpp:518–548固定q，costmap参数/ROS inflation computeCost252→publication98对应.98。保留原有限10000代价、不把障碍改为无穷；高障碍>.65m、低障碍>.001m、低障碍系数.25、＋1沿原实现。E3格相交占据是本项目用户合同；末端最终水平姿态、取消原目标裁剪、拒绝重采样等偏离已在r1及SRC-0466分别说明。

底盘可达采用起点所在.05m/8连通/.40m膨胀自由格区域，在原arm_range=.8m内的格心抽yaw并逐组调用同N1求解和完整机器人碰撞检查，找到有效末端见证才接受。**有限格心/每格一个yaw不是连续空间全部构型的穷尽判定，也未证明完整机械臂沿底盘路线可执行**；拒绝率可能包括采样见证未找到的可行任务。未把该限制包装为全局不可达证明。无额外安全阈值/重试上限，无训练。

### 真实分布计时及配对对照（选择器修复前的历史数据）

下表保留`async_final`版本；自然reset诊断随后暴露Route.select重算弧长的接口问题，已在归属路线包装层修复。最终版本重测以本节后续`final_v2`表为准，不用旧数冒充当前版本。

依据[SRC-0468](../../../SOURCES.md#src-0468)。GPU2 float32，torch线程2，async，真实train池seed4608（两档一并均匀抽图），各两次新环境同种子初始化；64调用窗口，规则valid候选均匀抽取、raw=0。batch latency单位ms，吞吐分子为实际active转移，所有规划/失败拒绝均保留。每次reset吞吐为E除该次wall；同种子两次输入重复，用于观测时间波动，不冒充两批独立分布。

|E|完整reset p50 ms（E/reset转移s）|step p50 / p95 / p99 ms|纯step转移/s|含两次初始reset与候选转移/s|提案/接受；拒绝率|有效执行DLS/IK|
|---|---|---|---|---|---|---|
|16|6730.400（2.377）|609.897 / 612.501 / 630.666|26.194|19.149|52/16；69.23%|127/2047（6.20%）|
|64|27431.373（2.333）|682.670 / 711.826 / 721.434|93.251|40.550|193/64；66.84%|641/8190（7.83%）|
|256|105178.746（2.434）|940.451 / 1031.569 / 1039.121|265.853|59.065|789/256；67.55%|2056/32751（6.28%）|

三个窗口自然episode reset均0，分别1024/4096/16383有效转移；reset频率记为0/该窗口，**不视为稳态reset频率**。完整初始化的reset最大耗时7.093/27.558/105.598s，逐次/全部分位数/候选耗时/路线节点与长度/地图ID/提案种子/G1及峰值内存在`profile_real_E*_async_final.json`。E256峰值GPU分配23,655,225,856 bytes。重采样比例较高，已报告；未设上限/降低碰撞或末端约束。E256拒绝533：initial348、goal171、base_connected_region5、goal_IK_collision_witness9。其余E原因见原始JSON。

r1历史短夹具E16/64/256约15.8/16.0/15.7转移s（上节）仅作历史参照，不直接算真实分布加速倍数；task7.14约958转移s同样为短夹具。以下同一批真实Episode、同目标/raw，原task7.14所有Transition字段逐元素相同；每E只两步，列原始两个时间，不给不可靠高分位结论：

|E|本轮两步ms|原task7.14批量Core两步ms|r1 E1串行两步ms|缓存任务reset本轮 / r1 ms|
|---|---|---|---|---|
|16|104.262 / 69.897|80.575 / 69.745|1057.813 / 939.906|38.037 / 442.581|
|64|182.419 / 131.856|159.005 / 131.303|4222.008 / 3714.897|87.683 / 1760.673|
|256|484.949 / 373.200|460.898 / 372.475|16859.844 / 14883.611|286.484 / 7090.596|

配对选择首个有效非原地候选（与上表均匀抽候选方法不同）；两步执行实际DLS均0，解释了它与连续窗口step耗时的差异。r1与新封装每行奖励差0；新/原批量全部字段精确相同。缓存任务reset排除共同采样/规划；不能替代完整reset。

实际全量求解计数（`paired.py`只在测量脚本临时包装solve_world；不改库）：完整reset DLS/targets：221/1074、1097/4747、4403/18155；一次全规则候选生成：2401/3553、11366/17732、48174/74358。包含inactive行计算，不能与仅有效attempt比率混用。见证单项DLS/targets：221/1028、1097/4569、4403/17458。历史stats键initial_targets实际是初始化提案数，包括提前碰撞拒绝，**不是IK调用数**。


### 最终版本复测、等价与交接（r2 final_v2）

以下以`source_manifest.json`为最终生产/测试版本；`source_snapshot/`保存七文件实测快照，`core.diff`相对task7.14原Core。只改episode/routes/env/core及对应三个测试；日志、RESULTS、自己的PROGRESS行与预留SOURCES按授权维护。归属外模块SHA/mtime在`dependencies_before_final.json`，最终核对无漂移。依据[SRC-0469](../../../SOURCES.md#src-0469)。

自然reset计时发现原Route.select重建Route时重新累计弧长，候选终点可能比父length大少量float32误差。`route_select_red`先复现s不一致；最终归属routes.py的PackedRoute.select只索引已有xyz/quat/s/length，保持原路线，不改只读motion/search/candidates，不裁剪候选或加epsilon。修复后同步/异步、CPU64/GPU32掩码reset均测试；初版计时留前节，当前版本重测如下。

|E|完整reset p50/p95/p99 ms|step p50/p95/p99 ms|纯step转移/s|含两次reset及候选转移/s|拒绝/提案|有效执行DLS/IK|
|---|---|---|---|---|---|---|
|16|6815.704/7130.559/7158.546|616.892/618.934/639.595|25.895|18.935|36/52|127/2047|
|64|26955.048/27299.949/27330.607|671.288/700.056/708.917|94.827|41.286|129/193|641/8190|
|256|101055.442/101418.088/101450.323|911.399/1002.156/1008.924|274.148|61.390|533/789|2056/32751|

方法/窗口/重采样口径同前节；每E仍是两次同种子新初始化、64调用，实际episode reset均0，不能当长期频率。所有延迟原始样本、候选分位数、路线长度/节点/地图/种子和峰值内存见`profile_real_E*_async_final_v2.json`；计时只记录无门槛，不推算训练工期。

当前版本同输入配对（`paired_E*.json`；前版另存`paired_E*_v1.json`）：新/原批量所有Transition逐元素相同，r1每行奖励差0。每E仍只有两步原始样本，分别为：

|E|本轮两步 ms|原批量两步 ms|r1串行两步 ms|缓存Episode reset本轮/r1 ms|
|---|---|---|---|---|
|16|103.075 / 68.735|79.081 / 68.418|1039.088 / 915.885|37.559/436.882|
|64|183.280 / 131.896|159.664 / 131.656|4245.902 / 3732.283|87.987/1771.539|
|256|486.221 / 373.647|462.505 / 377.042|16943.949 / 14920.163|286.375/7121.977|

完整reset的采样/IK成本未从主profile删去；配对缓存数据reset只测共同采样后的初始化。全量实际solve_world target/DLS计数见paired JSON，scope和有效attempt不同。

真实分布自然结束的partial reset诊断（固定规则slot12/零raw，至首次事件，未改终止判据）：

|E|自然结束行数|此前转移数|该事件完整reset ms|重置环境/转移|有效执行DLS/IK|
|---|---|---|---|---|---|
|16|2|112|693.437|0.01785714|77/201|
|64|1|384|520.306|0.00260417|466/700|
|256|1|1536|513.025|0.00065104|2069/2842|

各事件未选中state/grid/queue逐元素相同；每E只一个事件，不是通用reset频率或延迟分布。E16的初次诊断在select修复前执行，另用最终版本重跑并保留v1产物；以当前JSON为准。

**最终全目录：152 passed、1 failed、0 skipped；原11模块73项全部通过。** 本任务三个模块测试计数及其他并行模块见[test_counts.json](../../../../results/task7/t7.17-r2-20261021/test_counts.json)，完整[JUnit](../../../../results/task7/t7.17-r2-20261021/final-suite.xml)与[核对汇总](../../../../results/task7/t7.17-r2-20261021/verification_summary.json)。并行模块通过不替代其任务复核。

`equivalence.json`：原Core与最终Core在CPU64/GPU32各五场景（首子步失败、半步提交、路线终点、零推进、120动作超时），全部Transition/状态/队列/回合计数/attempts/trace/f_k逐元素相同。新掩码测试额外证明：其他环境reset/重新begin以及路线和地图padding增长不改变未选中行的转移、状态、队列、全局栅格/时间戳/计数、三种RNG流和f_k；同步/异步、两精度均覆盖。

E4边界统计（实际深度落点≤1e-5m影响格才排除；其他格observed与厘米uint8高度精确一致；未改perception）：

|样本|带内落点累计|影响格并集|observed差异|高度字节差异|带外observed/高度差异|
|---|---|---|---|---|---|
|test_wrapper_cpu64_gpu32|30882|792|692|709|0/0|
|test_real_pool_boundary_observations_cpu64_gpu32|14891|587|497|572|0/0|

夹具`test_wrapper_cpu64_gpu32`通过；真实池新增`test_real_pool_boundary_observations_cpu64_gpu32`的E4格与路线通道检查通过，**连续关节字段失败保留**。归一化q差0.0001118427023、原始q差0.0003513642453rad，未放宽原1e-4测试容差。`precision_real.json`证明同输入原task7.14 Core也复现，各精度内新旧完全相同；TCP差最大3.52418e-6m/3.50445e-6rad，IK分支/status/提交一致。证据[SRC-0467](../../../SOURCES.md#src-0467)。

**待决定**：task7.14 RESULTS:297连续字段1e-4与TASK:49位置/姿态按task7.6量级记录，近奇异关节向量差是否应明确接受为已有精度边界，或交运动学归属任务修复后复测。本任务仅暂停该额外精度验收；不改只读运动学、不放宽、不skip、不发起文档复核轮次，不声称完整CPU/GPU验收通过。

### r2完整命令账本

所有容器调用共用实际命令 `sg docker -c 'docker exec -i -e CUDA_VISIBLE_DEVICES=2 -e PYTHONPATH=/root/mm_husky_ws/src -w /root/mm_husky_ws forem-dev timeout 600 python3 -u -'`，stdin精确内容为下表input；宿主入口 `python3 forem/logs/task7/t7.17-r2-20261021/run.py NAME`。pytest具体参数/脚本在input中保留，未执行项不填通过。逐项wall/exit原始账本[commands.jsonl](../../../../logs/task7/t7.17-r2-20261021/commands.jsonl)。

|NAME/实际runner命令参数|退出码|wall s|stdin / 日志|结果|
|---|---|---|---|---|
|preflight|0|7.781358|[input](../../../../logs/task7/t7.17-r2-20261021/preflight.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/preflight.log)|CBL初态与原core/motion15通过|
|mask_red|1|3.126585|[input](../../../../logs/task7/t7.17-r2-20261021/mask_red.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/mask_red.log)|预期缺reset失败|
|mask_green|0|5.437787|[input](../../../../logs/task7/t7.17-r2-20261021/mask_green.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/mask_green.log)|2通过；含原Core/未reset行等价|
|planner_red|1|1.866431|[input](../../../../logs/task7/t7.17-r2-20261021/planner_red.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/planner_red.log)|预期缺原高度接口失败|
|planner_green|0|2.834934|[input](../../../../logs/task7/t7.17-r2-20261021/planner_green.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/planner_green.log)|路线6通过|
|sampler_red|1|1.966448|[input](../../../../logs/task7/t7.17-r2-20261021/sampler_red.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/sampler_red.log)|预期缺默认采样器失败|
|sampler_green|0|4.299881|[input](../../../../logs/task7/t7.17-r2-20261021/sampler_green.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/sampler_green.log)|任务采样6通过|
|batch_env_red|1|2.186197|[input](../../../../logs/task7/t7.17-r2-20261021/batch_env_red.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/batch_env_red.log)|预期旧串行API失败|
|batch_env_green|0|16.193115|[input](../../../../logs/task7/t7.17-r2-20261021/batch_env_green.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/batch_env_green.log)|新批量环境7通过|
|regression1|0|61.165664|[input](../../../../logs/task7/t7.17-r2-20261021/regression1.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/regression1.log)|中间版本146通过|
|e4_observation|0|5.484270|[input](../../../../logs/task7/t7.17-r2-20261021/e4_observation.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/e4_observation.log)|夹具E4对照1通过，带外差0|
|profile_real_E16_probe|0|14.906611|[input](../../../../logs/task7/t7.17-r2-20261021/profile_real_E16_probe.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/profile_real_E16_probe.log)|执行成功；详细结果见日志|
|profile_real_E16|0|56.108348|[input](../../../../logs/task7/t7.17-r2-20261021/profile_real_E16.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/profile_real_E16.log)|执行成功；详细结果见日志|
|profile_real_E64|0|103.661353|[input](../../../../logs/task7/t7.17-r2-20261021/profile_real_E64.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/profile_real_E64.log)|执行成功；详细结果见日志|
|profile_real_E256|0|280.095456|[input](../../../../logs/task7/t7.17-r2-20261021/profile_real_E256.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/profile_real_E256.log)|执行成功；详细结果见日志|
|extra_validation|1|15.149612|[input](../../../../logs/task7/t7.17-r2-20261021/extra_validation.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/extra_validation.log)|3通过/1近奇异关节对照失败|
|paired_E16|0|12.941435|[input](../../../../logs/task7/t7.17-r2-20261021/paired_E16.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/paired_E16.log)|执行成功；详细结果见日志|
|paired_E64|0|40.688425|[input](../../../../logs/task7/t7.17-r2-20261021/paired_E64.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/paired_E64.log)|执行成功；详细结果见日志|
|precision_real|0|9.555895|[input](../../../../logs/task7/t7.17-r2-20261021/precision_real.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/precision_real.log)|原Core重现关节差，各精度内新旧逐元素相同|
|paired_E256|0|145.654439|[input](../../../../logs/task7/t7.17-r2-20261021/paired_E256.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/paired_E256.log)|执行成功；详细结果见日志|
|masked_profile_E16|0|16.220531|[input](../../../../logs/task7/t7.17-r2-20261021/masked_profile_E16.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/masked_profile_E16.log)|执行成功；详细结果见日志|
|masked_profile_E64（第1次）|1|30.844305|[input](../../../../logs/task7/t7.17-r2-20261021/masked_profile_E64.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/masked_profile_E64_attempt1_failure.txt)|原.log被同名重试覆盖；此处为工具输出转录，原始退出/时长账本保留；独立red证据仍在|
|route_select_red|1|2.769096|[input](../../../../logs/task7/t7.17-r2-20261021/route_select_red.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/route_select_red.log)|复现选中路线s重算差异|
|route_select_green|0|24.137188|[input](../../../../logs/task7/t7.17-r2-20261021/route_select_green.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/route_select_green.log)|18通过/1已知精度项单独排除；非最终全套|
|masked_profile_E64（第2次）|0|36.546114|[input](../../../../logs/task7/t7.17-r2-20261021/masked_profile_E64.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/masked_profile_E64.log)|执行成功；详细结果见日志|
|masked_profile_E256|0|112.415846|[input](../../../../logs/task7/t7.17-r2-20261021/masked_profile_E256.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/masked_profile_E256.log)|执行成功；详细结果见日志|
|profile_real_E16_v2|0|56.692994|[input](../../../../logs/task7/t7.17-r2-20261021/profile_real_E16_v2.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/profile_real_E16_v2.log)|执行成功；详细结果见日志|
|profile_real_E64_v2|0|101.844168|[input](../../../../logs/task7/t7.17-r2-20261021/profile_real_E64_v2.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/profile_real_E64_v2.log)|执行成功；详细结果见日志|
|profile_real_E256_v2|0|269.615025|[input](../../../../logs/task7/t7.17-r2-20261021/profile_real_E256_v2.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/profile_real_E256_v2.log)|执行成功；详细结果见日志|
|final_suite|1|73.063377|[input](../../../../logs/task7/t7.17-r2-20261021/final_suite.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/final_suite.log)|最终全套，唯一近奇异关节失败|
|equivalence|0|23.226625|[input](../../../../logs/task7/t7.17-r2-20261021/equivalence.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/equivalence.log)|10场景所有字段逐元素相同|
|paired_E16_v2|0|12.641062|[input](../../../../logs/task7/t7.17-r2-20261021/paired_E16_v2.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/paired_E16_v2.log)|执行成功；详细结果见日志|
|paired_E64_v2|0|40.990024|[input](../../../../logs/task7/t7.17-r2-20261021/paired_E64_v2.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/paired_E64_v2.log)|执行成功；详细结果见日志|
|paired_E256_v2|0|146.187291|[input](../../../../logs/task7/t7.17-r2-20261021/paired_E256_v2.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/paired_E256_v2.log)|执行成功；详细结果见日志|
|masked_profile_E16_v2|0|15.982461|[input](../../../../logs/task7/t7.17-r2-20261021/masked_profile_E16_v2.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/masked_profile_E16_v2.log)|执行成功；详细结果见日志|
|provenance|0|2.160878|[input](../../../../logs/task7/t7.17-r2-20261021/provenance.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/provenance.log)|执行成功；详细结果见日志|
|cleanup|0|0.115200|[input](../../../../logs/task7/t7.17-r2-20261021/cleanup.input.py) / [log](../../../../logs/task7/t7.17-r2-20261021/cleanup.log)|执行成功；详细结果见日志|

### 预算、限制与接手

- r2 runner累计 **1756.556429s**，r1保守累计391.865089s，另给r2只读快照/收尾30s预留，保守总计 **2178.421518s（36.307分钟）**；最长容器调用280.095456s，均≤600s，总计≤5400s。实测与预留分开；所有输入/退出/原始产物保留。

- 原73的test_robot调用原build_robot_config幂等写回robot_geometry.json，mtime更新但SHA=d65450a719857c8e5c383ccfb5d00ca6ea9d19e82ee70afc4c1ddfbc913d2d47与task7.14 r2原证据相同；未编辑配置/robot.py，也未为恢复mtime重写。

- 未训练、未启停/重建容器、未提交git、未改阶段一/参考库/其他task7_sim模块；仅GPU2。最终资源与UID归还另记本日志收尾。

- 限制：有限格心/yaw的末端IK碰撞见证和.40m栅格连通不等于连续全构型/整条底盘机械臂可执行性证明；重采样率约2/3、初始化和DLS成本较高；计时为有限诊断策略，不证明学习成功率、长期reset分布或训练工期。生产入口已接真实地图池，额外近奇异关节精度项仍失败，不能报告全套通过。

- 交接：负责人Codex，PROGRESS本行→review，交Claude核对最终manifest/JUnit/E4计数/五场景等价、单Core masked reset、原成本高度迁移与真实分布计时；原73不能回退。先读本r2末节与[独立日志](../../../agent_logs/task7/task7.17/20261021-codex-episode.md)，不依赖聊天恢复。实际模型/强度未知；推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium。只需处理已列精度待决定及复核，不标done。


### 最终环境版本与原代码映射补表

[provenance.json](../../../../results/task7/t7.17-r2-20261021/provenance.json)：GPU2实际NVIDIA RTX PRO 6000 Blackwell Server Edition（逻辑cuda:0，visible_devices=1），torch2.7.1+cu128/CUDA12.8、Python3.10.18、numpy1.23.5、scipy1.10.1；CPU线程2/interop64、亲和0–63。pyastar0.0.1直接安装commit4303b3d200f91016bbccbfdfc43cdc3b67fc6264，二进制SHA与r1相同；地图index及原参考文件SHA、URDF与机器人配置SHA均保留。根仓库/上游只读HEAD见host_git_heads.json。依据SRC-0465/0469，以下落实r1核对表中已经由E1–E3确定的部分；Python/C++目录前缀沿r1核对表，未修改参考源：

|项|已核查原位置|r2最终采用与合同偏离|
|---|---|---|
|A* / 代价|eeplanner.py:469–518,590–615,676–681；mycostmap.cpp:61–75,114–129；ROS inflation_layer.h::computeCost|同安装pyastar/diagonal/linf、10000与低障碍.25偏好＋1；.40m/零衰减膨胀邻格.98。栅格改按用户E3闭格相交；有限代价保留，规划后连续TCP低于障碍顶则拒绝，不改无穷成本|
|高度|eeplanner.py:52–89,624–637；myutils.cpp:452–484；map.py:53|原障碍顶＋.25、超过z_max1.15清0、1e-3原比较与原平台段插值；E1取代B12旧线性高度。起点高度来自实际固定q的FK，不用终点高度区间拒绝它|
|起终点 / 姿态|eeplanner.py:198–203,639–653；simulator_api.py:27–46；tasks.py:260–263|保留原径向/高度提案方式，采用B12 .5–8m/.7–1.15m与用户TCP定义；越界拒绝替代裁剪；原随机RPY替换为合同水平末段姿态，姿态SLERP仍按XY弧长，Core进度用3D位置弧长|
|固定关节 / RNG|robot_env.cpp:518–548；上游mobile-rl/src/robot_env.cpp:509–536|E2明确采用CBL字面固定六关节，未用上游随机q；真值完整碰撞/IK/FK校验不回填目标；RNG按env-id与maps/initial/other独立，是本项目合同偏离原共享np_random|

收尾资源核查：forem-dev仅原docker-init/sleep，未发现本任务Python/compute；全部本任务session已退出，无后台任务需停止/恢复。日志/产物UID/GID已归还1004。原始命令全数计入上述2178.421518s保守预算，无新增容器运行待执行。

## Claude复核 t7.17-r2-20261021（2026-10-21T14:17–14:40，claude-opus-5-5，推理强度未知）

- 源哈希与`source_manifest.json`一致；`core.diff`相对task7.14原Core约100行改动（掩码reset/begin、每行first、G1计数）。
- E5批量：单个批量Core，真实池异步纯step吞吐E16/64/256为25.9/94.8/274.1转移/s（r1逐环境串行约16），同输入与task7.14批量Core全部Transition逐元素相同；掩码reset不影响未选中行（状态、栅格、队列、计数、RNG、f_k）。E256 step p50约911 ms中，真实分布约6%的IK走DLS（固定约275 ms/次批调用，每动作步2个子步）是主要成本，转task7.18性能核查。
- E1–E3：原高度抬升、CBL固定关节、原代价＋规划后碰撞拒绝已落实并登记出处（SRC-0465/0466）。提案拒绝率约67%、完整reset约0.4 s/环境（单环境局部reset约0.5 s会阻塞全批），对阶段L的reset开销转task7.18核查（可考虑后台预生成任务，不改采样分布）。
- E4：带外observed/高度差异0。近奇异关节差按E6（[SRC-0902](../../../SOURCES.md#src-0902)）改测试容差（Claude直接修改test_env.py两行）。
- 重跑全目录（GPU2）：**153 passed**，退出0。
- 结论：**task7.17 done**。限制沿Codex记录（底盘可达见证是有限采样、非穷尽；计时每E样本少）。
