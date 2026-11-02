# task7.16 — 结果

状态：**review**（2026-10-21，r1实现与地图池交付，CPU验证和产物审计已执行，待Claude复核；见末节）。

## 运行记录

（尚无。每次执行按run-id追加：执行Agent与实际模型/强度、改动文件、命令、版本、退出码、证据路径、结论与限制。）

## run-id r1-20261021-1002 — 试生成与全量前估算

- 负责人Codex；实际模型/推理强度：未知/未知。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（几何与复现合同交叉核对），推荐不是实际配置。
- 授权：[SRC-0431](../../../SOURCES.md#src-0431)、用户补定M1–M5 [SRC-0433](../../../SOURCES.md#src-0433)。方法与参数来源[SRC-0450](../../../SOURCES.md#src-0450)；最终结果将另追加，历史文首“尚未执行”为建立时状态。
- 改动：`forem/src/task7_sim/mapgen_a.py`、`tests/test_mapgen_a.py`、`forem/config/task7/mapgen_a.json`、本RESULTS、独立日志、PROGRESS本行、SOURCES预留条目；未改其他源码/配置/参考仓库。根HEAD `cac6c15599efcbe47a1a7ed30f59a475e4997fd4`，生成器SHA见各图metadata和index。
- 23项新测试通过（pytest1.54s、调用1.949s），RED/GREEN与种子范围负例退出码见[日志](../../../agent_logs/task7/task7.16/20261021-codex-mapgen.md)。CPU float64、CUDA_VISIBLE_DEVICES空；完整GPU73项按用户答复交Claude复核，不在本任务执行。
- 实际命令：宿主`python3 -u forem/logs/task7/t7.16-r1-20261021-1002/run.py pilot python3 -u -B -m task7_sim.mapgen_a --config config/task7/mapgen_a.json --output results/task7/maps/a/20261021T021036Z-pilot --root-head cac6c15599efcbe47a1a7ed30f59a475e4997fd4 --mode pilot --workers 8`；wrapper用`sg docker -c`进入forem-dev，CUDA禁用、库线程1、timeout1700s。完整argv/退出码/墙钟在`forem/logs/task7/t7.16-r1-20261021-1002/commands.jsonl`。
- 试生成退出0：稀疏100/100合格、标准100/100合格，无整图拒绝；各多评估4个批尾候选未入池。跳过网格点25/24（每图原始重抽和跳过记录可查）。稀疏单图评估p50/p95=0.085907/0.093553s，标准0.094405/0.100654s；评估不含父进程PNG/JSON写入。
- **全端到端**（含进程池/JSON/check/PNG输出）：调用6.430116s；两档集合墙钟2.701298/3.487286s。全量10300张按同配置线性外推 `6.430116/200×10300=331.151s`（约5.52分钟），仅推算，不是已执行或工期承诺；包含每图输出、不含后续全量审计。
- 产物：[试生成index](../../../../results/task7/maps/a/20261021T021036Z-pilot/index.json)，`maps/`每张JSON/check/PNG；`reports/`完整尝试记录、拒绝分布、抽样10张清单。原始日志`pilot.log`；宿主wrapper PID2300929/sg2300931已退出，无遗留后台任务。
- 全量当时尚未执行。先完成同输入串行/8worker性能比对，再使用相同门槛全量生成，每档验证50、测试100、训练5000；与pilot及其他集合种子区间不交叠。

## 交接

- 当前负责人：Codex；下一接收方Claude。完整GPU回归及随机10图人工核对尚未执行；本任务不自标done。

## run-id r1-20261021-1002 — 最终汇总与交接

执行Agent、模型推荐和授权见上节；实际模型/推理强度仍为未知。全部最终结论登记[SRC-0451](../../../SOURCES.md#src-0451)，方法、工程选择和适用性见[SRC-0450](../../../SOURCES.md#src-0450)。只新增授权的生成器、测试、配置及本任务记录；未训练、用GPU、启停容器、修改其他task7_sim模块/阶段一/参考仓库或提交Git。

### 地图交付

正式池：[index.json](../../../../results/task7/maps/a/20261021T021400Z/index.json)。目录`forem/results/task7/maps/a/20261021T021400Z/`；每张有JSON、check JSON、PNG，共10300张地图/30900份地图文件。所有日志和产物均被Git忽略。两档每档训练5000、验证50、测试100；与独立pilot及其他集合的预留种子区间不交叠。源SHA256 `bdb59e11b2d71487317a539110d3a41d81bba5caf03456ce06503963f4e66a1d`，根HEAD与试生成相同；源/配置/测试快照在日志目录。

|档/集合|合格/尝试|拒绝原因|跳过网格点（全部尝试）|
|---|---|---|---|
|稀疏验证|50/50|无|7|
|稀疏测试|100/100|无|17|
|稀疏训练|5000/5000|无|1027|
|标准验证|50/50|无|15|
|标准测试|100/100|无|26|
|标准训练|5000/5005|连通性5张|1378|

标准训练合格率99.9001%，其余100%；未触发低合格率/尝试上限停止，未放宽条件。10305次正式尝试之外另有23次并行批尾评估未入池，计入worker耗时。地图级拒绝与单障碍重抽的拒绝是两种计数，后者见每图metadata及集合报告。

### 命令、退出码与计时

日志根目录`forem/logs/task7/t7.16-r1-20261021-1002/`。下列pytest均在已运行的forem-dev内，`CUDA_VISIBLE_DEVICES=`、`PYTHONPATH=/root/mm_husky_ws/src`、禁用pyc/cache；后期库线程1。完整实际argv/计时为[commands.jsonl](../../../../logs/task7/t7.16-r1-20261021-1002/commands.jsonl)，测试逐例[CPU回归XML](../../../../logs/task7/t7.16-r1-20261021-1002/cpu-regression.xml)。

|步骤|命令（公共pytest前缀`python3 -B -m pytest -q -p no:cacheprovider`）|退出码|原始日志与结果|
|---|---|---|---|
|初始RED|`... src/task7_sim/tests/test_mapgen_a.py`|2|`red.log`；缺模块，预期失败，不计通过|
|几何GREEN|同上加`-k "not connectivity and not grid_report"`|0|`geometry-green.log`；19 passed/2 deselected，1.48s|
|种子区间RED|同上加`-k overlapping_seed`|1|`seed-red.log`；未提前拒绝重叠种子，随后修复|
|新测试GREEN|`... src/task7_sim/tests/test_mapgen_a.py`|0|`all-green.log`；23 passed，1.54s|
|原73例CPU部分＋新测试|`run.py cpu-regression python3 -B logs/task7/t7.16-r1-20261021-1002/cpu-regression.input.py`|0|`cpu-regression.log`；76 passed/20 skipped，21.29s，调用23.168221s|
|同输入并行核对|`run.py profile python3 -B logs/task7/t7.16-r1-20261021-1002/profile.input.py`|0|`profile.log`；16候选哈希全部一致，串行1.329251s/8worker0.198437s|
|试生成|上节完整命令（`run.py pilot ... --mode pilot --workers 8`）|0|`pilot.log`；两档各100/100，调用6.430116s|
|全量|相同入口改`run.py full`、`--mode full --output results/task7/maps/a/20261021T021400Z`|0|`full.log`；10300张，调用239.835201s|
|全量审计|`run.py audit python3 -u -B logs/task7/t7.16-r1-20261021-1002/audit.input.py`|0|`audit.log`；10300图及30900份文件通过，调用21.548313s|

原73项中的53项CPU用例均通过；20项包含显式CUDA调用，依用户确认全部延期，精确名单[deferred-gpu.json](../../../../logs/task7/t7.16-r1-20261021-1002/deferred-gpu.json)，没有修改原测试或假称GPU回归通过。新模块仅numpy float64，无GPU float32执行路径。

全量index墙钟239.544401s，worker累计候选评估929.306330s；父进程逐图JSON/check/PNG输出累计113.734479s。计时包含几何/栅格检验与周期性输出；阶段并行不能相加当墙钟。主调用账本累计292.743080s，初始4次测试额外约4.73s；包括只读核查的容器累计调用仍远小于120分钟，最长239.84s小于30分钟。不是训练成本测量。全部Python/worker已结束，最终进程证据`final-processes.log`；无后台任务。产物/日志所有权已归UID/GID1004。

### 检验统计与一致性

完整六集合分布/高度占地见[审计报告](../../../../results/task7/maps/a/20261021T021400Z/reports/audit.json)；每集合`reports/<difficulty>_<split>.json`含所有接受与拒绝的seed、check、单障碍拒绝/跳过及耗时。以下统计仅合格图。

|指标|稀疏|标准|
|---|---|---|
|全部合格图最小连通比|0.966390|0.907322|
|全部合格图最小掉头比例|0.517719|0.366989|
|训练图每图障碍数min/median/max（不含墙）|5/8/8|12/14/14|
|训练图骨架宽度中位数的跨图中位数(m)|2.209072|1.646962|
|训练图低/工作带/全高障碍数量|9715/15526/13732|17146/27180/24297|
|训练图低/工作带/全高占地面积累计(m²)|3899.200/6235.758/5516.124|6673.741/10646.510/9532.725|

通道骨架最小宽度可为0.10m，按M2只报告，不把细枝、窄死端称可通行路线，不新增0.80m拒绝门。占据与距离都是0.05m栅格口径；比例≥90%不等于全部自由区连通，不证明真实Husky/UR5任务可完成。

全量审计对每图执行现有`geometry.load_map` CPU64读取并核对角点→中心结果、没有重复加墙；每个PNG核对CRC及按同JSON几何渲染的逐像素结果；全部种子去重并与pilot隔离；随机10张重新调用生成＋全部check，结果精确相等。[SHA256清单](../../../../results/task7/maps/a/20261021T021400Z/reports/artifact_sha256.json)覆盖30900份文件。单元测试另有手算角点/颜色位置夹具，避免只用同函数自证几何。

随机10张清单：[sample_10.json](../../../../results/task7/maps/a/20261021T021400Z/reports/sample_10.json)；[拼图](../../../../results/task7/maps/a/20261021T021400Z/reports/sample_10_montage.png)依清单从左至右、从上至下，蓝/橙/紫对应低/工作带/全高，黑为墙，上方为+Y。Codex已查看拼图，未见明显越界/裁剪；**Claude逐张人工JSON核对尚未执行**。PCD是可选输出，本轮未导出，不声称已通过PCD一致性。

### 限制、待决定与下一步

- 当前未通过测试：无遗留本任务失败；上述2次RED保留为历史。当前待决定：无（M1–M5及CPU回归已由用户补定）。未执行项：完整GPU73例、Claude随机10图人工核对、真实机器人/ManiSkill通行与训练表现。
- 纯函数复现以同源版本、种子、参数和本次numpy1.23.5环境为界，不宣称跨NumPy版本逐位一致。高度占地和合格率是本批数据，不是普遍分布/成功保证；重抽后高度比例允许与初始抽样比例不同。样本质量只按既定几何/栅格门验收。
- 共享PROGRESS并发损坏曾导致UTF-8补丁失败；本任务只定点插入自己的行，保留他人字节，之后文件由并发方恢复。完整过程见[独立日志](../../../agent_logs/task7/task7.16/20261021-codex-mapgen.md)。
- 接收方Claude先读本节/日志，再核对source SHA、index、审计清单与CPU回归；按既定授权运行完整GPU73例、人工核对sample_10后决定是否done。未授权任何训练或参考模块改动；本任务状态为review，不标完成。

## Claude复核 r1-20261021-1002（2026-10-21T10:35–10:55，claude-opus-5-5，推理强度未知）

- 版本：`mapgen_a.py` SHA256复算`bdb59e11…6a1d`，与RESULTS和index一致。PROGRESS对cac6c15只有新增、无删除行，并发损坏已恢复。
- **独立几何检查（全部10300张，不复用生成器代码）**：容器内`python3 -I`临时脚本（`forem/logs/task7/.claude_mapcheck.py`，用后删除）按“角点＋theta绕角点旋转”重建每个盒子，检查：旋转矩阵合法、角点不越出[−5, 5]、非墙盒子三边≥0.10 m、高度落在三个采样层、原点到每个盒子距离≥0.7 m、所有盒子两两（含墙）SAT严格穿透深度≤1e−9、每图恰4面墙、六个集合种子互不重叠。结果：**违规0**；最小原点净空0.7001 m；高度层低/工作带/全高27658/43976/39197（25.0%/39.7%/35.4%，规格约25/40/35）；集合张数5000/50/100（每档）。
- 人工核对：查看Codex抽样拼图（10张，无越界/裁剪；第2张底部蓝紫相邻经上项检查为不重叠）；另抽不在其样本中的`map_standard_test_00042`，逐个把14个障碍的角点、尺寸、朝向与高度层颜色对照PNG（20 px/m、原点居中、+Y向上），全部一致。
- **完整GPU回归**（GPU3，全目录）：146 passed、1 failed；唯一失败`test_env.py::test_wrapper_cpu64_gpu32`属并行进行中的task7.17。task7.16新测试及原73项（含其延期的20个CUDA用例）全部通过。
- 结论：**task7.16 done**。限制沿Codex记录：只证明几何/栅格层面条件，不证明机器人通行与任务可完成；跨NumPy版本不保证逐位复现；未导出PCD。
