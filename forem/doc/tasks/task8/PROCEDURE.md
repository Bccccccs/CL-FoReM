# task8 — 实施流程与执行者派发prompt

> For agentic workers：收到用户执行派发后，使用 subagent-driven-development（用户已指定由执行者派发子任务）；无子Agent工具时报告工具限制，不冒称已委派。此文是规划，不代表本轮已启动实施。

**Goal**：PCD真实驱动扫描及整个理想环境，再迁入现有mapgen语义场景。**Architecture**：PCD→共享体素场景→真值查询；扫描→原Grid→原策略接口。**Tech stack**：现有Python/NumPy/PyTorch、现有pyastar，运行使用已核实forem-dev；不新增仿真引擎。**Spec**：[TASK](TASK.md)。

## 递归规则

每层恰有TASK.md、PROCEDURE.md、RESULTS.md。子任务位于父目录内、继承编号；再拆分必须先建立三文档并登记负责人、输入输出、模型/强度、范围与验收。父流程列顺序/依赖/三文档，父RESULTS汇总子RESULTS。编号稳定不复用。代码/配置/原始日志/产物分别归forem/src、config、logs/task8、results/task8；prompt在本流程，不另建第四份主要文档。

## 顺序、归属、交接门

派发模型及Sol验收职责统一按[TASK模型分工表](TASK.md#model-routing)。8.1/8.5的混合阶段串行交接文件，不新增子任务层级；若执行者另拆独立子任务，先按递归规则建三文档。

|顺序/任务|三文档|文件独占与交接|负责人及验收关系|
|---|---|---|---|
|1 task8.1|[TASK](task8.1/TASK.md) / [PROCEDURE](task8.1/PROCEDURE.md) / [RESULTS](task8.1/RESULTS.md)|assets.py、fixtures.py、asset tests、asset config；父初始化包后共享__init__仅父维护|资产Agent；父核PCD反例及manifest后放行2/3|
|2a task8.2|[TASK](task8.2/TASK.md) / [PROCEDURE](task8.2/PROCEDURE.md) / [RESULTS](task8.2/RESULTS.md)|scene.py、query tests|几何Agent；独立解析参照后交4|
|2b task8.3|[TASK](task8.3/TASK.md) / [PROCEDURE](task8.3/PROCEDURE.md) / [RESULTS](task8.3/RESULTS.md)|robot.py、perception.py、sensor tests、sensor config|传感器Agent；先测机器人豁免，依2完成射线集成后交4|
|2c/4 task8.5|[TASK](task8.5/TASK.md) / [PROCEDURE](task8.5/PROCEDURE.md) / [RESULTS](task8.5/RESULTS.md)|import_mapgen.py、task8_import_maps.py、语义池配置/tests|资产迁移Agent；先离线导入，依4运行逐图诊断后交6|
|3 task8.4|[TASK](task8.4/TASK.md) / [PROCEDURE](task8.4/PROCEDURE.md) / [RESULTS](task8.4/RESULTS.md)|episode.py、env.py、routes.py、decision_env.py、环境tests与environment.json|集成Agent；只在2/3通过后接线，交5/6|
|5 task8.6|[TASK](task8.6/TASK.md) / [PROCEDURE](task8.6/PROCEDURE.md) / [RESULTS](task8.6/RESULTS.md)|task8_pcd_smoke.py、task8_pcd_verify.py、集成tests|独立验收Agent＋父复核；失败退回所属节点|
|6 task8.7（2026-10-26追加）|[TASK](task8.7/TASK.md) / [PROCEDURE](task8.7/PROCEDURE.md) / [RESULTS](task8.7/RESULTS.md)|scene.py索引修复、格点夹具tests、版本字段；新run账本≤900s|Codex父协调；S1 Sol high实现→S2 Luna low固定执行→S3 Sol medium复核→S4独立Sol high验收；依8.1–8.6已交付产物，修复v1几何缺陷SRC-0999|
|7 task8.8（2026-10-26追加）|[TASK](task8.8/TASK.md) / [PROCEDURE](task8.8/PROCEDURE.md) / [RESULTS](task8.8/RESULTS.md)|scene.py闭合面归属v3、格点夹具tests、版本字段；新run账本≤900s|Codex父协调；S1 Sol high→S2 Luna low→S3 Sol medium→S4独立Sol high；依8.7 v2代码，用户选闭合面规则SRC-1021|
|8 task8.9（2026-10-27追加）|[TASK](task8.9/TASK.md) / [PROCEDURE](task8.9/PROCEDURE.md) / [RESULTS](task8.9/RESULTS.md)|第二阶段规划；子任务8.9.1/8.9.2可并行，8.9.3依两者与用户决定；执行另行派发，8.9.3需训练授权|Codex父协调（推荐）；Claude规划与复核。2026-10-27用户作废，closed（SRC-1220）|
|9 task8.10（2026-10-27追加）|[TASK](task8.10/TASK.md) / [PROCEDURE](task8.10/PROCEDURE.md) / [RESULTS](task8.10/RESULTS.md)|新增可选后端primitive-obb-v1（默认仍v3）、独立参照R、A–H对照验收；新文件优先；8.9已关闭，接线隔离条件解除（SRC-1220）|推荐Codex父协调；S1/S2/S4 Sol high、S3 terra low；2026-10-27已由Claude子Agent执行完毕（done，见RESULTS）|
|10 task8.11（2026-10-27追加）|[TASK](task8.11/TASK.md) / [PROCEDURE](task8.11/PROCEDURE.md) / [RESULTS](task8.11/RESULTS.md)|依赖8.10 done；W接线→I初始化→R分布→T吞吐→X2独立验收|Claude父；X1/X2 Sonnet5.5 high（Codex推荐GPT6.1sol high）|
|11 task8.12（2026-10-27追加）|[TASK](task8.12/TASK.md) / [PROCEDURE](task8.12/PROCEDURE.md) / [RESULTS](task8.12/RESULTS.md)|2026-10-28 superseded，移至task9（SRC-1313）；原：依赖8.11验收，smoke→长训均需用户批准|smoke terra low/Sonnet low；验收与判定Sol/Sonnet high|
|12 task8.13（2026-10-28追加）|[TASK](task8.13/TASK.md) / [PROCEDURE](task8.13/PROCEDURE.md) / [RESULTS](task8.13/RESULTS.md)|依赖8.11 X2发现M1；只改training.py `_contract()`一行|Claude父直接完成（推荐GPT6.1sol/Sonnet5.5 low）；done|

并行仅2a/2b/2c的互不重叠实现/离线工作；GPU验证由父串行调度，不能各自领取完整1800s预算。8.3可先用最小测试替身；未接8.2真实查询不能验收完成。8.4不得改8.2/8.3文件，应发接口问题回原负责人。子Agent不得写PROGRESS/DECISIONS/SOURCES；提供待登记主张由父统一落账。每节点独立日志`forem/doc/agent_logs/task8/task8.N/YYYYMMDD-agent-topic.md`。

<a id="interfaces"></a>
## 共享接口（规划签名，执行实现须保持一致）

全部新文件位于`forem/src/task8_sim/`，不把以下签名写入task7源码。

```python
# assets.py：CPU float64原始点；保留sidecar，不向策略公开
MapAsset(map_id: str, xyz, metadata: dict, semantics: dict | None, hashes: dict)
load_asset(manifest_path, map_id: str) -> MapAsset
# manifest maps[]: id, pcd_path, sidecar_path|null, sha256, split, difficulty,
# frame_id, length_unit, resolution_m, point_representation, bounds,
# geometry_backend, semantic_policy_input=false; 路径相对manifest
# hash字典区分pcd/sidecar；未知旧difficulty标source场景类别，不伪造A池难度

# scene.py：一个scene只来自一个asset；select返回对应env批场景，禁止共享可变状态
VoxelScene.from_asset(asset: MapAsset, *, device, dtype) -> VoxelScene
scene.raycast(origins, directions, *, max_range: float) -> distances
# distances:[E,R]，最近非负交点，无命中=inf；origin在占据内=0
# 域外起点允许射线入域；离域无占据不命中；地面由Panorama单独求交
scene.collide(base, caps, *, robot, q=None, allowed=None) -> task7_sim.geometry.Collision
scene.contains(points) -> occupied_mask
scene.planning_height() -> height_yx  # truth-only，无policy路径
scene.provenance() -> dict
SceneBatch(scenes: list[VoxelScene])  # 与env行一一对应，复用上述查询接口
batch.select(indices) -> SceneBatch
batch.replace(indices, scenes) -> None  # 只改选中行，id/hash必须同步

# robot.py / perception.py
GhostRobotGeometry(data=None)  # 兼容task7 RobotGeometry，过滤已核传感器body参与检测
PcdPanorama(scene_batch: SceneBatch, *, sensor_config: dict)
PcdPanorama.__call__(base, caps, body_boxes=None) -> task7_sim.perception.Depth
# 显式忽略caps/body的遮挡，保持调用形状；近处场景遮住远处场景

# episode.py / routes.py / env.py / decision_env.py
PcdEpisodeSampler(pool, *, split, difficulty, device, dtype, kin, robot, profile)
PcdEpisode  # 原Episode字段与map_id/seed/witness，scene替代真值boxes
PcdTruthPlanner(scene: VoxelScene)  # 原路线算法/代价，真值输入改为scene
PcdEpisodeEnv(batch, *, seed, pool, profile, device, dtype)
# reset(indices=None), begin(candidate, mask=None), step(raw), info()兼容旧语义
PcdDecisionEnv(batch, policy, *, seed, pool, profile, device, dtype, run_id)
# reset/step契约沿原DecisionEnv，内部依赖必须注入新PcdEpisodeEnv
```

碰撞函数返回base/arm/self_collision三个布尔量；适配给Core的callable捕获scene/robot，签名与原`collision(base,caps,allowed=None,q=None)`一致。Core的pure IK/动作/状态提交可复用；不得依赖`renderer.boxes`或`collision.boxes`去reset新场景。批量接口以CPU float64和CUDA float32都可测为约束，内部实现/缓存布局由执行者决定，记录版本。scene内容不可变，replace仅替换引用；部分reset不改其他行Grid/RNG/route/timestamp/counters。真值scene不进入observe/replay/rollout。

## 关注的五类失败

- PCDFIELDS/行数/NaN/单位/点云坐标边界或manifest声明hash不符：8.1/8.5拒绝并记录；JSON几何与PCD不一致仅作差异诊断，PCD仍权威。干预测试生成新的manifest/hash，不能让旧hash失配与几何差异混为一谈；绝不静默截点/替用boxes。
- 薄墙/旋转采样/体素边界与擦边射线：8.2以独立遍历参照、手工解析夹具测误差，不用宽容差掩盖漏碰。
- 传感器豁免扩大成机械臂/顶板豁免：8.3以只触sensor和只触top_plate的正负例回归。
- 初始reset正确而部分reset/决策构造回到旧地图：8.4用两张明显不同图、冻结未选行、PCD-only输入做整链路检查。
- 原地全无效扫描/真值直接灌Grid/旧pickle环境混入：8.3/8.4/8.6检查可见性、隐藏障碍不泄露、协议版本与恢复拒绝。

## 有界执行与验证入口（规划命令；实际结果见RESULTS）

先核AGENTS、ENV、PROGRESS与进程，登记run-id和修改范围；确认源manifest哈希，若漂移先记录归属，不覆盖他人改动。父在`forem/logs/task8/<run-id>/`建带实际argv、开始结束、退出码、累计墙钟/worker耗时的账本。可用已有运行容器，不创建/停止容器。本轮计划上限/数值依据[SRC-0987](../../SOURCES.md#src-0987)：累计1800s，包括各子任务验证；单smoke120s/64动作步，先batch1后2；24图诊断每图30s。超限退出写incomplete，不把超时当环境自然truncated。

开发与常规单元验证也登记耗时；不以反复开新run重置预算。运行前读取当前余额，timeout取余额和本命令上限较小值；共享GPU只用核实空闲设备，记录真实tensor设备/显存。CPU预处理的耗时单列。下列为规划入口合同；脚本现已由所属子任务交付，实际调用/结果/退出码见RESULTS和共享账本，不能把示例命令当成已运行证据：

```bash
# 已运行forem-dev内，根路径/root/mm_husky_ws；宿主经sg docker -c调用
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -u scripts/task8_import_maps.py --source /root/mm_husky_ws/results/task8/<run-id>/source --output /root/mm_husky_ws/results/task8/<run-id>/semantic-pool
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -u scripts/task8_pcd_smoke.py --config config/task8/environment.json --pool results/task8/<run-id>/cube-pool --profile sync_v5 --batch 1 --max-steps 64 --max-wall-s 120 --output results/task8/<run-id>/smoke-cubes
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -u scripts/task8_pcd_verify.py --run-dir results/task8/<run-id>
```

父将源24对PCD/JSON复制到forem新run的source目录，复制前后核hash；容器只见forem挂载，不假定能读宿主mapgen。源拷贝/派生缓存不入Git。测试命令若触及旧回归，显式使用旧配置/旧默认路径；不修改旧测试预期配合新协议。失败先定位最小复现，属于地图/传感器接口可修；涉及奖励、分布、候选网络或预算增量则记blocked等待相应决定。

## 可直接复制的执行者角色prompt

```text
你是FoReM task8第一阶段的执行协调者。工作区/home/ybc/projects/CL-FoReM。用户现在派发你按已写规划完成PCD地图迁移，并由你派发各子任务实施和核验。请先读AGENTS.md、forem/AGENTS.md、forem/ENV.md、forem/doc/README.md、PROGRESS.md，以及forem/doc/tasks/task8/{TASK,PROCEDURE,RESULTS}.md及各子任务三文档。遵守最新用户指令和SOURCES SRC-0984–0987。

task7已按用户要求冻结（paused）；其历史成果和未完成项保留。不得恢复v5、D10、7.24、旧诊断、上层训练或ManiSkill。任务范围是task8.1–8.6：随机立方体PCD先跑通，继而接mapgen现有24对语义地图；地图必须驱动扫描、碰撞、reset/路线和真实step，不能只展示PCD而仍运行JSON盒体。传感器相对底盘固定，实体无碰撞，忽略整机自遮挡；场景遮挡、机器人非传感器自碰撞/环境碰撞仍有效。语义元数据保留但不扩充策略输入。

先核分支、未提交修改、各Agent活动、容器和GPU占用；保留他人改动。登记task8执行run-id、负责人、实际模型/强度和日志路径。核t8-plan-20261026/source-manifest.json的旧实现哈希；本次实现全部放forem/src/task8_sim、config/task8及task8脚本，不修改task7源码/配置/产物。任务目录每层恰有三文档，计划/接口见task8 PROCEDURE，执行结果逐项填RESULTS，代码不放文档目录。

按依赖派发：8.1先通过；之后8.2几何和8.3传感器的独立部分可并行，8.5可先离线导入；8.2与8.3完成才派8.4整环境集成；8.5运行部分依8.4；8.6由独立Agent核验全链路，最后你亲自复查。不是一次性并发所有任务。每次派发附根AGENTS、子任务三文档、独立日志、文件归属、输入输出签名、验收条件、预算余额和源hash。子Agent只能改自己文件和自己的RESULTS/日志；共享PROGRESS/SOURCES/DECISIONS和__init__由你统一维护。接口冲突退回责任人，不能互相覆盖。

模型分工按用户SRC-0989和父TASK“模型、强度与验收分工”：简单明确的清单、文件复制/hash、固定格式夹具输出、固定导入命令与记录可派GPT6 Luna / low；需推理的协议、异常/根因、几何、接口接线均用GPT6.1sol。8.1/8.5按Sol medium先定合同→Luna low执行明确步骤→Sol medium验收；8.2几何、8.4整环境、8.6独立总验收用Sol high；8.3传感器用Sol medium，复杂排错升high。父协调Sol medium，复杂冲突high。Luna的每项交付必须由Sol检查diff、原始产物和必要测试后验收，不能仅采信自报，也不让Luna提高强度代替Sol做推理。同一文件按阶段移交，不并发写。

显式选择平台模型标识gpt-6-luna / gpt-6.1-sol并记录实际模型/强度；在支持显式覆盖且要求fork_turns=none的spawn_agent上必须使用该设置，并给子Agent完整任务上下文，不能因继承父会话而实际仍跑Sol却记为Luna。Claude Sonnet5.5仍是双Agent文档的相应强度备选，本次推理与验收明确派Sol，除非用户另行指定。模型不可用时如实报告，不擅自换更大型号。没有子Agent工具则如实报告，不能假称委派。新方案/参数依据同步登记SOURCES，各文档链接；未验证写待核验。

采用PCD→固定world体素→共享查询的规划，JSON只是语义和审计侧车。先写能暴露故障的测试，再最小实现与回归：尤其PCD改变/JSON不变会改变扫描与碰撞、PCD-only输入、场景遮挡、ghost自身无遮挡、sensor-only碰撞豁免、非传感器碰撞保持、Grid无真值泄露、部分reset隔离、两变体显式profile及旧checkpoint环境拒绝。规划中的所有接口和参数取TASK/PROCEDURE，不自行增奖励、网络、实验组或重建数据集。

本批只做有界单元/集成验证与端到端profile，不训练任何网络。验证累计墙钟上限1800s由父统一账本管理，不给每个Agent另起完整预算；smoke每次≤120s和64动作步、batch从1到2，24图逐图≤30s。单命令外部timeout取余额/子上限较小值，完整记录失败、超时、拒绝原因及worker累计耗时。按AGENTS检查tensor实际设备、加载/预处理/采样/IK/碰撞/渲染/搬运/推理/日志耗时。GPU验证串行；不停止或重建未经核实的现有进程/容器。超限或科学条件冲突时停相关步骤、写清依赖，不放宽验收，不偷偷续预算。

不用LLM生成新图，不改mapgen参考资产；从宿主只读复制到forem结果目录供容器读取并核hash。旧下层actor最多用于冻结推理的接口冒烟，不把旧full checkpoint中的env/replay/optimizer恢复到新地图；不以此宣布SAC问题解决。

完成时交付：源/派生地图和版本manifest、随机立方体及语义图的扫描/轨迹/碰撞证据、逐图状态、必要测试与性能报告、未通过项及根因范围、task8各层RESULTS和共享来源/进度。独立复核后才能标第一阶段done；环境跑通不等于SAC稳定或WM有效。最后为下一阶段下层SAC修复列出输入证据和待决定事项，等用户明确安排，不自动训练。不提交推送、合并或删除历史。
```

模型、强度与理由按[TASK分工表](TASK.md#model-routing)及[SRC-0989](../../SOURCES.md#src-0989)：Luna low执行简单明确步骤，Sol medium/high负责推理和验收；Claude Sonnet5.5保留同档备选。实际执行配置与推荐分开登记。
