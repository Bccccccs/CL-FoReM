# task8.1 — 结果与交接

当前状态：**done（2026-10-26第一阶段8.1范围父及独立Sol复核通过；27 tests，非整环境验收）**。实际实现gpt-6.1-sol/medium，固定导出gpt-6-luna/low，独立审查gpt-6.1-sol/medium；[证据SRC-0991](../../../SOURCES.md#src-0991)。推荐仍按下文GPT6.1sol/Claude Sonnet5.5对应强度；历史规划与过程保留。

## 规划历史（以下尚未执行声明仅表示实施前状态）

状态：**review（规划；尚未执行）**。规划Codex；执行负责人：资产Agent（派发时登记具体Agent及实际模型/强度）。Codex分工：**GPT6.1sol / medium先确定读取/异常协议→GPT6 Luna / low执行清单/hash、已固定读写与夹具导出→GPT6.1sol / medium验收**。解析歧义、异常设计和失败归因由Sol处理，不将这些推理交Luna。Claude备选Sonnet5.5 / low（固定步骤）、medium（协议/核验）；本次推理与验收按用户要求用Sol。 实际模型/强度未知，不以推荐代填。依据[用户SRC-0989](../../../SOURCES.md#src-0989)、[父模型分工](../TASK.md#model-routing)。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

**规划阶段历史（实施前）**：当时尚未执行，只建立规划；无本节点实现、测试、仿真、地图生成或性能结果。不沿用task7旧成绩作验收。

## 执行记录模板（每run追加，保留历史）

- run-id/开始结束：尚未执行。
- 目标/授权与输入：见[TASK](TASK.md)；依赖无；先读父共享接口。
- 负责人：资产Agent待派发；实际模型/推理强度：未知。
- 修改文件/版本/hash：尚无；限定TASK列出的文件。
- 实际命令/容器/设备/退出码、日志/产物：尚无。
- 验收项与结果：尚未验证，见[TASK](TASK.md)及[PROCEDURE](PROCEDURE.md)。
- 共享预算消耗/余额、全局墙钟/累计worker：尚未执行，向父领取余额。
- 问题/风险/证据来源：未实施；沿父任务限制，不假定PCD迁移或SAC已通过。
- 下一步：收到执行派发后先核依赖与范围；提交父复核，不自行将父状态标done。

## t8-exec-20261026 开始

状态active；负责人Codex，实际gpt-6.1-sol / medium。2026-10-26收到父派发，按既有协议实施，范围仅assets.py/fixtures.py及指定tests/config/独立日志。父核157文件hash无漂移见[baseline-check](../../../../results/task8/t8-exec-20261026/baseline-check.json)。父统一共享预算，本节点申请≤120s累计CPU验证；尚未执行。独立[日志](../../../agent_logs/task8/task8.1/20261026-sol-assets.md)。来源沿SRC-0984–0989，推荐GPT6.1sol medium / Sonnet5.5 medium用于协议与核验，Luna low用于固定导出，不替代实际配置。

## t8-exec-20261026 交父复核（2026-10-26）

状态：**review（本节点实现与本节点测试完成，待父及独立审查；不等于task8通过）**。实际负责人Sol `gpt-6.1-sol / medium`；固定导出由父显式派发Luna `gpt-6-luna / low`。推荐GPT6.1sol medium / Claude Sonnet5.5 medium用于协议、异常归因和验收；固定输出推荐Luna low / Claude Sonnet5.5 low，理由沿[SRC-0989](../../../SOURCES.md#src-0989)。参数与夹具属[SRC-0987](../../../SOURCES.md#src-0987)工程选择，不是训练分布或性能结论。

### 文件与合同

- `forem/src/task8_sim/assets.py`：`MapAsset`及`load_asset(manifest_path,map_id)`；CPU float64、immutable bytes backing，不能通过setflags恢复写入。支持PCD0.7 ASCII、三个可乱序xyz字段、SIZE4/TYPE F/COUNT1；拒绝头重复、行数/维数不符、非有限点、非world/m、hash错、三轴半开域外、binary及surface-only。带map-id与解析行号/原因，边界错误附点序号。无静默删点、缩放、补墙或JSON回退。
- `fixtures.py`：固定seed=20261026；empty、axis_aligned、rotated、occlusion、boundary、floating_slab、random_cubes七场景。随机4 cube边长0.5–1.0m，原点净空仅夹具属性；采样体内格中心，未宣称原物体连续精确重建。先落盘PCD、原子rename，再manifest；输出目录已存在即拒绝，加载只取落盘PCD。
- `tests/test_assets.py`、`tests/test_fixtures.py`共25 tests：含PCD-only、字段顺序、头/维数/行数、NaN/Inf、边界、单位/frame、空图显式允许、surface-only、hash、未知语义保留、重复seed一致和禁止覆盖。
- `forem/config/task8/assets.json`冻结合同。manifest `schema_version=task8-pcd-v1`，`geometry_backend=pcd-voxel-v1`，`sha256={pcd:64位小写hex,sidecar:hex|null}`，`bounds={min:[-5,-5,0],max:[5,5,1.6],upper_exclusive:true}`；maps[]其余字段依父接口。fixture_boxes仅审计参照，JSON不参与运行几何。PCD-only由sidecar_path=null及sidecar hash=null显式声明；已声明侧车缺失仍拒绝，不能绕过hash。

### 实际命令与结果

完整实际argv、起止时间、退出码与耗时权威为父[共享账本](../../../../logs/task8/t8-exec-20261026/budget.json)。以下均使用外层`python3 forem/logs/task8/t8-exec-20261026/run_budget.py --owner <owner> --limit 60 --`；容器使用`sg docker -c 'docker exec -w /root/mm_husky_ws forem-dev timeout 55s env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src ...'`，未写task7 pycache，全部CPU，无训练/网络调用。

单元命令：`python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests/test_assets.py src/task8_sim/tests/test_fixtures.py`。

|账本id/原日志|执行者|结果|累计worker墙钟s|
|---|---|---|---|
|[be5a6e4fd7](../../../../logs/task8/t8-exec-20261026/be5a6e4fd7.log)|Sol|rc2，预期RED：尚无assets/fixtures模块，2 collection errors|0.464836|
|[06fb50b13a](../../../../logs/task8/t8-exec-20261026/06fb50b13a.log)|Sol|rc0，16 passed，pytest 1.21s|1.516174|
|[7b0a12b404](../../../../logs/task8/t8-exec-20261026/7b0a12b404.log)|Sol|rc0，扩充头负例后25 passed，pytest 1.23s|1.566546|
|[6222ad7b17](../../../../logs/task8/t8-exec-20261026/6222ad7b17.log)|Luna|rc0，固定导出CLI|0.514907|
|[2443d828b6](../../../../logs/task8/t8-exec-20261026/2443d828b6.log)|Sol|rc0，读取实际manifest并逐7图重新load/hash/shape，核实现文件hash|0.464794|

Luna固定导出完整Python命令：`python3 -B -m task8_sim.fixtures --output /root/mm_husky_ws/results/task8/t8-exec-20261026/cube-pool --seed 20261026`。父另派源复制`python3 forem/logs/task8/t8-exec-20261026/copy_sources.py`，owner=source-copy-luna/limit30，rc0/0.314694s，非本节点几何导入，见[51c289f84a](../../../../logs/task8/t8-exec-20261026/51c289f84a.log)与[source-copy.json](../../../../results/task8/t8-exec-20261026/source-copy.json)。Sol本节点只核该源复制记录存在，48源文件完整性由父复核，不冒称本节点逐48源已再核。

本节点含Luna导出累计4.527257s；加父源复制账本合计4.841950s，读取时共享余额1795.158050s且active为空。全局本节点从10:48:00.999至10:50:03.384，约122.385s；这是包含编辑/调度的elapsed，不是CPU运行量。全部有界，无运行任务/PID待管理，无停止/恢复动作。

### 原产物与hash

新[manifest](../../../../results/task8/t8-exec-20261026/cube-pool/manifest.json) SHA256：`762547eb2e7f634f37016a349220265db1cfdd6e3f4f2b5691c06873a714ef90`。七图按上述顺序点数0/8000/8000/8000/2000/400/14723；全部PCD-only。每PCD完整SHA见manifest及Sol原始核验日志2443d828b6。旧源继承版本见父157文件[baseline-check](../../../../results/task8/t8-exec-20261026/baseline-check.json)与规划[source-manifest](../../../../results/task8/t8-plan-20261026/source-manifest.json)，本节点未修改旧源。

本节点交付文件SHA256（2443d828b6现场核验）：

|文件|SHA256|
|---|---|
|assets.py|9aa21edeed9cc63f1307d4aac1f982106e064106163f29e4306b9cffbdc94165|
|fixtures.py|7ba3df305c9bd12a6efd2595179654acf97d0cfab351d0963a1704bad3d3c00b|
|tests/test_assets.py|57ffb2128ad0dd2f9002339d6f967ac5ea9f3013e134e2ee22fc96b10009502f|
|tests/test_fixtures.py|387a18171da938b266cfc67a18787f31b2e30ed538325cb20fd0027bae68d5bc|
|config/task8/assets.json|1a292d36ceef6dc3ad47b094d65c37fb2524865e0eab965f7bc325f981eb5a09|

### 剩余、限制与交接

本节点未执行扫描/碰撞/真实step，不把资产读取测试当整环境通过；scene体素边界、旋转采样重复/乱序不变性、独立几何参照由8.2测，ghost与部分reset由后续节点测。当前未逐24语义图解析，新manifest规范不等于旧24图均可运行；8.5按现有元数据生成导入manifest，保留JSON未知字段，不把JSON boxes用于几何。

下一接收方父协调及独立审查：阅读本记录和原日志，复查代码/原manifest，决定是否放行8.2/8.3/8.5；本节点代码冻结等待反馈。新实测主张请父登记统一SOURCES并引用本结果，本节点未改共享SOURCES/PROGRESS/DECISIONS。无提交、推送或合并。

## fix round1 — 独立审查两项错误合同修复

状态仍**review**，Sol `gpt-6.1-sol / medium`，由父授权本轮≤15s累计验证。独立原证据[099782de1e](../../../../logs/task8/t8-exec-20261026/099782de1e.log)发现：显式侧车JSON `null`且hash正确时被接受；实际DATA binary/0xff负载抛UnicodeDecodeError且无map-id/行号。前述25 tests未覆盖这两个反例，不能作为错误合同完整性证明。

根因（源码直接核查）：原侧车检查按解码值`semantics is not None`判断存在性，混同“无侧车”与“显式JSON null”；原PCD先全文件ASCII decode，再解析头，导致不支持binary的声明尚未读到就被负载解码中断。按systematic-debugging定位后，TDD先增两个精确反例，再最小修复：PCD先按bytes分行，逐行decode并包装非ASCII错误；DATA binary在头部位置即报`<map-id>: PCD line N: only DATA ascii supported`。侧车检查改按`'sidecar' in paths`，任何显式侧车解码结果都必须dict。未改schema/fixtures/原产物。

完整命令仍见父[budget.json](../../../../logs/task8/t8-exec-20261026/budget.json)，owner均`8.1-fix1`，容器、PYTHONDONTWRITEBYTECODE/PYTHONPATH与前文相同；测试Python argv均为前文两指定tests命令。

|证据|命令外层/内层上限|退出码与结果|实际耗时s|
|---|---|---|---|
|[b700e63baf](../../../../logs/task8/t8-exec-20261026/b700e63baf.log)|15s/12s|rc1，预期RED，新增2 failed/原25 passed|1.616345|
|[ec9a5b7928](../../../../logs/task8/t8-exec-20261026/ec9a5b7928.log)|13s/10s|rc0，27 passed，pytest1.26s|1.566310|
|[762f51c59f](../../../../logs/task8/t8-exec-20261026/762f51c59f.log)|5s/3s|rc0，核5文件SHA256|0.164419|

本轮累计3.347074s，小于15s；末次共享余额1791.346188s（并行其他owner消耗以总账为准）。修复后assets.py SHA256=`a15162bc7c6f002abb1499517b7b0f4b39536d2f0b7f09a4896837a49ba4a052`，test_assets.py=`6d47b7bda50d6f09598f77f583b6b8641e61957410ef05f5fc6ec588f016bcfe`，其余实现文件/manifest hash保持前表；fixtures.py/assets.json/manifest已现场再核。无进程遗留、无训练。交父及独立定向重审，不自行放行后续或标done；前一交付hash保留为历史修复前事实。
