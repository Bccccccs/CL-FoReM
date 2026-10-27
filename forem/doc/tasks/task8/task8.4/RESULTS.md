# task8.4 — 结果与交接

状态：**done（2026-10-26本节点父及独立Sol high验收通过；语义图与总验收待后续）**。实际实施/独立复核均gpt-6.1-sol/high；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨模块状态合同需推理。证据[SRC-0995](../../../SOURCES.md#src-0995)，历史过程保留。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

**规划阶段历史（实施前）**：当时尚未执行，只建立规划；无本节点实现、测试、仿真、地图生成或性能结果。不沿用task7旧成绩作验收。

## 执行记录模板（每run追加，保留历史）

- run-id/开始结束：尚未执行。
- 目标/授权与输入：见[TASK](TASK.md)；依赖8.2、8.3完整验收；不能只靠mock开始最终集成验收。
- 负责人：集成Agent待派发；实际模型/推理强度：未知。
- 修改文件/版本/hash：尚无；限定TASK列出的文件。
- 实际命令/容器/设备/退出码、日志/产物：尚无。
- 验收项与结果：尚未验证，见[TASK](TASK.md)及[PROCEDURE](PROCEDURE.md)。
- 共享预算消耗/余额、全局墙钟/累计worker：尚未执行，向父领取余额。
- 问题/风险/证据来源：未实施；沿父任务限制，不假定PCD迁移或SAC已通过。
- 下一步：收到执行派发后先核依赖与范围；提交父复核，不自行将父状态标done。

## t8-exec-20261026 实施交付（2026-10-26，待父独立验收）

**当前状态：review（实现及本节点验证已交付，不能据此代替8.6/父总验收）。** 上方“尚未执行”是保留的规划历史，本节为实际记录。负责人Codex，实际模型 **gpt-6.1-sol / high**（父显式派发）；推荐Codex **GPT6.1sol / high**、Claude **Sonnet5.5 / high**，理由仍是reset/Core/DecisionEnv/profile跨模块状态核查，不将推荐代填实际模型。

授权及科学条件沿[SRC-0984](../../../SOURCES.md#src-0984)、[SRC-0987](../../../SOURCES.md#src-0987)、[SRC-0989](../../../SOURCES.md#src-0989)、[SRC-0990](../../../SOURCES.md#src-0990)。本节新实测主张、精确原件和限制已发父协调统一登记SOURCES；本节点不跨写父所有的台账。独立执行日志见[20261026-sol-integration](../../../agent_logs/task8/task8.4/20261026-sol-integration.md)。

### 实际变更与继承边界

- 新建`forem/src/task8_sim/{episode,routes,env,decision_env}.py`、`tests/test_pcd_env.py`、`tests/test_pcd_decision.py`、`forem/config/task8/environment.json`，仅上述文件及本RESULTS/独立日志。无训练、无子Agent、无task7修改、无提交/推送。
- `PcdEpisodeSampler`使用原RandomStreams、sample_base/sample_goal、CBL_Q、initial/goal witness验证；PCD加载与scene缓存替代JSON boxes。单VoxelScene可接64 witness姿态；Core执行使用SceneBatch逐环境一一对应。不改拒绝条件，不设置重试上限，不选择易图回退。
- `PcdTruthPlanner`复用原plan/witness_cells/cells及路线原语；原A* cost/height/连通条件保持，只把height及连续XY/障碍顶检查改成同scene占据投影。浮空结构仍按旧“低于障碍顶”保守规划；真实碰撞保留3D空腔。
- `PcdEpisodeEnv`复用原Core和EpisodeEnv._ids/begin/step/info语义，重写PCD reset。显式三profile取父TASK；scan只经PcdPanorama→Grid；部分reset只换选中scene/route/状态/计数与扫描；map_id与scene provenance强制一致。仅增加out_of_map诊断，不新增越域碰撞/终止。
- `PcdDecisionEnv`构造直接注入PcdEpisodeEnv，不调用旧EpisodeEnv构造。候选、Grid snapshot rollout、选点执行、reward/replay/autoreset沿原DecisionEnv。只接两个decision profile，拒绝sync_v5；版本包含task8环境/map/ghost、原观察动作版本、profile和robot hash。恢复入口拒绝旧环境state/pickle；actor加载仍属原FrozenLowerPolicy的actor-only能力，本节点未加载actor。
- `pool`必须显式指定；接受manifest文件或恰含一个`manifest.json`/`index.json`的目录（包括cube-pool与semantic-pool），不回退旧pool。
- 采样可传单调时钟绝对`deadline`或`cancel`（callable/Event），抛`SamplingIncomplete`而不伪造truncated；每proposal、预处理、initial/plan和每64 witness块前后检查。完成的witness即使随后取消也先记targets/dls/timing。Decision reset同样传递控制，显式map_id工厂在自动reset时不捕获已过期的初始deadline。

只读复用源符号及hash详见代码头和[源hash](../../../../results/task8/t8-exec-20261026/integration/source-hashes.json)。原task7 episode/routes/env/decision_env四文件SHA256与开工读值相同，分别`db8310…b5ae`、`f49433…0475`、`ae2c44…e7e3`、`b7669f…c247`。本节点未重核父全部157文件，其全局零漂移由父另验。

### 原始验证与失败历史

全部命令通过宿主`python3 forem/logs/task8/t8-exec-20261026/run_budget.py --owner 8.4 --limit N -- <argv>`；容器`forem-dev`，工作目录`/root/mm_husky_ws`，内部`timeout`比账本小3s、`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`，`python3 -B -m pytest -q -p no:cacheprovider`。GPU额外`CUDA_VISIBLE_DEVICES=0 TASK84_DEVICE=cuda`。以下日志均在`forem/logs/task8/t8-exec-20261026/<id>.log`，完整argv/start/end/rc/耗时在[父账本](../../../../logs/task8/t8-exec-20261026/budget.json)，本节点快照见[budget-summary](../../../../results/task8/t8-exec-20261026/integration/budget-summary.json)。

|id|内容/结果|rc|累计worker秒|
|---|---|---:|---:|
|02def0a3a6|RED：6项因尚无新env/episode/routes模块失败，之后最小实现|1|2.066990|
|9f1729693f|5通过/1失败：测试误假设q=0自碰撞；未据此改生产几何|1|3.669171|
|897d506176|实测4个姿态；q=[0,0,π,0,0,0]确认非sensor自碰撞，替换错误测试夹具|0|1.866980|
|615eaf6ff7|GPU决策3失败/1通过：cuda与实际cuda:0设备比较不一致，构造规范设备名修复|1|3.619196|
|384338e2d6|GPU决策4通过；当时controlled empty场景，后续已换random_cubes重验|0|21.543874|
|4ea0b05794|CPU8通过/2GPU跳过；含异图reset和真实越域step|0|4.069872|
|d1a26f1ef9|GPU默认random_cubes batch1→2，2通过；首轮完整JSON打印保留在日志|0|6.573125|
|da3c4c7c62|CPU11通过/2GPU跳过，新增真实base/arm失败和三profile原Core受控对照|0|5.571812|
|1a9d03fde5|RED：决策reset尚不接deadline，TypeError；随后补透传|1|2.667995|
|1d61e80cf4|GPU两文件18通过（当时decision仍empty）；非最终random_cubes验收|0|28.503292|
|1911ef61ff|RED：真实64 witness完成后cancel导致targets旧统计为0；随后修复记账顺序|1|2.668009|
|1e2e3f6967|CPU12通过/2GPU跳过；完成的64目标取消后记账通过|0|6.122850|
|d3f8267465|**最终GPU两文件19通过**，两decision已用random_cubes controlled场景|0|29.804659|
|01b97181a6|宿主写容器root创建的integration目录PermissionError；未改权限，改在容器写摘要|1|0.114294|
|617bc4608b|容器写source-hashes/budget-summary成功|0|0.164354|

最终GPU命令选择`src/task8_sim/tests/test_pcd_env.py src/task8_sim/tests/test_pcd_decision.py`，外60s、内57s，pytest自身28.98s，19项全过；CPU最终pytest自身5.49s。开发验证只选择本节点两个文件，未将旧task7全套/CUDA大batch回归冒充已运行。无命令超时，无未退出子进程；GPU0结束时`nvidia-smi --query-compute-apps`空，已向父释放。

### 覆盖与实际证据

- PCD-only reset→非零step→真实提交q→实际FK→新扫描，策略原grid `[E,128,128,3]`，无renderer/collision boxes字段；动作越过x=5的数据界仍提交，新增诊断out_of_map，继承route-end reason=1，无新增失败码。
- 真实Core执行遇到PCD底盘/机械臂障碍分别给kind=2/3且无任何状态提交；SceneCollision对真实折叠q仍给self_collision=true；单scene批64姿态查询有效。
- 相同seed复现；empty/axis_aligned两种实际几何，另行reset一个已结束行时，未选活动行RNG、scene identity/map_id/seed、route、state、Grid/timestamp、episode/累计/segment计数与queue均逐字段保持。
- 原Core在同empty、同ghost、同输入三profile下，reward/B/G/dt/attempted/committed/done/reason/mask/active及next_observation逐元素一致。该对照不声称PCD离散化与旧OBB一般等价，也不把ghost观测与旧自遮挡观测等同。
- 两decision variant在**random_cubes PCD、controlled短FK route**下均跑原候选13槽→Grid-only rollout 19特征→选in-place槽12→实际下层动作→扫描→下一边界/autoreset，reward分别与原`10.0075`/`10.0025`一致（float32误差限制见测试）。policy收到的键集明确排除scene/sidecar；不扫描只替真实scene时，Grid/candidates/预测f_k逐元素不变。
- 上述controlled factory与下述**默认随机采样能力**分列；不把短受控任务称为默认决策随机任务验收。

默认random_cubes最终快照：[batch1](../../../../results/task8/t8-exec-20261026/integration/cube-default-batch1.json)、[batch2](../../../../results/task8/t8-exec-20261026/integration/cube-default-batch2.json)，对应最终d3f8267465。测试重复运行会更新这两份当前快照；首轮d1a26f1ef9逐字段打印仍保留原日志，各命令结果保留账本，不把最终计时回填首轮。

|最终默认cube|batch1|batch2|
|---|---:|---:|
|实际tensor设备/dtype|cuda:0 / float32|cuda:0 / float32|
|reset同步wall秒|0.623951521|1.042656750|
|step同步wall秒|0.654033865|0.717790907|
|本测试端到端秒|1.343349580|1.773648193|
|CUDA峰值allocated bytes|71,625,728|172,045,312|
|proposals / accepted|2 / 1|4 / 2|
|完成witness targets|64|128|
|真实提交子步/行|2|2、2|
|新扫描timestamp秒/行|0.1|0.1、0.1|

PCD SHA256 `946d9d170652083bc6db02abc38328f9aaeee504dd8d417d0beb61fee73fe087`；14,723点、13,057占据格、103 packed几何段；来源是已批准cube夹具，不读取fixture_boxes运行。batch1 proposal seed `8010734840812606961`，batch2另加`5525944440751941652`；每行实际base/q/FK、provenance、scan累计、采样计数及分项时间都在JSON。CUDA峰值为PyTorch allocator计数，不是全卡占用；没有optimizer/训练。timing是wall而非仿真推进；动作仿真推进每行0.1s。未做性能调参或GPU-only微基准。

### 预算、限制与交接

本节点全部15条计账命令累计 **119.026474504s**，低于父分配300s。budget-summary为最后摘要命令开始前快照118.862120871s，加摘要命令617bc4608b的0.164353633s；不能重复计入。摘要完成时父全局余额1518.392026936s，后续以即时账本为准。各命令最长29.805s，开发单命令均≤60s，smoke动作各一action/two substeps≤64，先batch1后batch2。六次非零退出均在上表，无超时；不把错误/测试RED计成环境自然truncated。

采样deadline/cancel在有限底层原语和块边界协作检查，不承诺硬实时中断正在运行的CUDA kernel/C++ A*；外部timeout仍是必要保护。当前取消回归实际在一次真实64目标调用完成后触发，证明不无限留在采样循环且不漏计已做工作。未修改拒绝阈值、随机分布、路线代价、奖励/终止或IK接收条件。

尚未做：语义24图运行（属8.5，等父核验本节点后启动）、8.6独立总验收、任意长默认决策任务、正式训练/成功率/WM结论。只证明这里列出的有界接口条件，不证明SAC问题已解决或地图都可通行。下一步由独立high核本代码/原始证据，再由父放行8.5/8.6；接口冲突退回本节点，不覆盖他人文件。当前无运行任务，无需停止/恢复进程。
