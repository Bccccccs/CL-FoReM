# task8.2 — 结果与交接

当前状态：**done（2026-10-26本节点范围已由父及独立Sol high复核通过；task8整环境尚待后续）**。实际模型/强度：gpt-6.1-sol/high实施及独立复核；闭接触fix1通过。证据[SRC-0993](../../../SOURCES.md#src-0993)、[最终依赖门SRC-0994](../../../SOURCES.md#src-0994)。推荐Codex GPT6.1sol / Claude Sonnet5.5，几何high/传感器medium（复杂排错high）；推荐不代替实际配置。历史规划/过程保留。

## t8-exec-20261026 初版交付（修复前历史）

**初版闭接触验收被后续独立精确反例否定。以下旧hash/旧profile仅保留过程事实，不作为fix1最终版本的碰撞验收；修复结果见下方fix round1。**

授权与输入：父在8.1及其独立复核通过后派发8.2，MapAsset协议、七图PCD-only [manifest](../../../../results/task8/t8-exec-20261026/cube-pool/manifest.json)为输入，源hash见该manifest；root HEAD沿父`cac6c15599efcbe47a1a7ed30f59a475e4997fd4`，main原dirty状态保留。仅新增`scene.py`、`tests/test_scene.py`、`tests/test_scene_collision.py`及本记录/独立日志，运行产物放本run结果目录。

- `VoxelScene.from_asset`：CPU float64执行floor索引/重复点合并；不贴边、滤点、补洞、补墙或读取JSON boxes。固定h/origin/shape沿父协议，索引半开、几何闭合。按相同X连续占据段→相同XY矩形→相同XYZ长方体压缩，严格保留体素并集；BVH分块遍历最近射线命中，未使用整物体AABB填空腔或完整ray×point/voxel张量。`occupancy`和`planning_height`返回副本；provenance返回深拷贝。
- 查询保持实际device/dtype，显式拒绝设备/精度不匹配及非有限输入；请求CUDA不可用时报错，无CPU隐式回退。射线必须单位方向，域外可入域，无命中inf，闭体素内/接触起点0；`contains`采用同源闭体素并集，地面由传感器另算。`planning_height`为原保守全高度投影最高占据格顶，truth-only。
- `collide`：base保留0.99×0.67m全高度XY投影SAT；arm使用原task7分段二次最小化胶囊-AABB距离、解析z=0地面；无虚拟边墙/天花板。robot自碰撞由传入对象报告，原allowed与q保持；SceneBatch先提取caps的`_self_collision_q`再切片环境几何，最后对原caps整批调用robot，兼容显式q优先。没有重写IK。
- `SceneBatch`：逐环境scene引用，select产生新tuple，replace验证长度/索引/设备后原子替换；未选scene与map_id/hash保持。支持父PROCEDURE全部raycast/collide/contains/planning_height/provenance签名。

### 实际命令、失败与预算

全部验证由host `python3 forem/logs/task8/t8-exec-20261026/run_budget.py --owner 8.2 --limit N --`执行，完整实际argv、开始/结束和退出码见[父账本](../../../../logs/task8/t8-exec-20261026/budget.json)。容器均`forem-dev`、工作目录`/root/mm_husky_ws`，inner timeout均比外层小3s；Python `python3 -B`、`PYTHONDONTWRITEBYTECODE=1`、`PYTHONPATH=/root/mm_husky_ws/src`、`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1`；pytest `-q -p no:cacheprovider`。命令未写旧task7 pycache。

|账本/原日志|外/内上限s|Python命令及结果|累计worker s|
|---|---|---|---|
|[2c9549a0cb](../../../../logs/task8/t8-exec-20261026/2c9549a0cb.log)|30/27|`-m pytest ... src/task8_sim/tests/test_scene.py src/task8_sim/tests/test_scene_collision.py -k "not cuda"`；rc2，预期RED，scene尚未创建，2 collection errors|2.016840|
|[ff3fba7729](../../../../logs/task8/t8-exec-20261026/ff3fba7729.log)|60/57|同上；rc1，10 passed/1 failed；测试漏写float64，被scene按dtype合同拒绝。只修正测试输入dtype，未弱化实现校验|6.723422|
|[3ee9c9de06](../../../../logs/task8/t8-exec-20261026/3ee9c9de06.log)|40/37|同上；rc0，11 passed/1 deselected|6.774094|
|[3d1b9a0277](../../../../logs/task8/t8-exec-20261026/3d1b9a0277.log)|60/57|同上，加`TASK8_GEOMETRY_REPORT=.../geometry-cpu.json`；rc0，扩充原始PCD解析/七图profile/54负坐标闭面边角后13 passed/1 deselected|9.727510|
|[afc393dbf3](../../../../logs/task8/t8-exec-20261026/afc393dbf3.log)|45/42|`-m pytest ... src/task8_sim/tests/test_scene.py -k cuda`，`CUDA_VISIBLE_DEVICES=0 TASK8_GEOMETRY_GPU_REPORT=.../geometry-gpu.json`；rc0，2 passed/8 deselected，pytest7.06s|7.824813|
|[28a6439126](../../../../logs/task8/t8-exec-20261026/28a6439126.log)|50/47|`-m pytest ... src/task8_sim/tests`，`CUDA_VISIBLE_DEVICES=`；rc0，整个当前task8集合55 passed/3 skipped，pytest11.18s；3项CUDA专项本次显式跳过，其独立授权GPU执行另记|11.830652|
|[faaa2cea32](../../../../logs/task8/t8-exec-20261026/faaa2cea32.log)|5/无容器|`sha256sum`三份交付源码/tests及两份profile产物；rc0|0.003968|

本节点累计**44.901299s**，包括全部RED/失败/CPU/GPU/hash，小于父分配210s；单命令均≤60s。GPU父明确授权≤45s串行后先核`nvidia-smi --query-compute-apps`为空再运行，实际仅7.824813s，结束即报父释放。末次共享used=126.725965s、余额1673.274035s，无active；后续其他节点用量以实时账本为准。全局本节点首个验证2026-10-26T10:56:51.897+08:00开始，最终结束见faaa2cea32账本；编辑/等待时间不冒称worker时间。无超时或遗留进程。

### 参照与验收证据

CPU 13项测试：独立标量floor→原始体素并集slab参照（无BVH/压缩复用），轴平行、闭面/边/角、内部起点、量程外、域外入域/离域、54条负坐标各面/边/角恰好最大量程射线；300条随机旋转单层薄片/离散点射线；空图/重复点/乱序不变/不填L形空腔；两图select/replace及map/hash隔离；固定sidecar原字节、重写PCD并更新manifest/hash后深度/base和arm碰撞变化，遮挡后变动不泄露；删改sidecar boxes不改变PCD几何。碰撞另测闭接触与1e-8m分离、base投影离地障碍仍阻挡、arm下穿空腔/撞实体、1.6m上方不生天花板、包络出域不生墙、地面和robot自碰撞报告。60条胶囊独立用SciPy标量有界最小化逐体素距离，与被测原分段解析距离作分类对照。

七张实际落盘PCD用独立`np.loadtxt`读DATA区，不复用assets解析或fixtures采样，再与MapAsset逐值对照；每图完整32400射线CPU查询，并对12条固定索引射线独立逐原始体素slab核验。[CPU原产物](../../../../results/task8/t8-exec-20261026/geometry-cpu.json)包括每图hash、点数、占据数、压缩盒数、BVH节点数、加载/预处理/查询耗时及设备内存。

CUDA实际设备`cuda:0` / `torch.float32`，卡为RTX PRO 6000 Blackwell Server Edition；每图32400射线与CPU64最近距离比较，命中掩码完全相同，最大观测绝对差**3.020154e-7m**；每图另12条独立标量slab、32组base/arm碰撞、128个contains同输入parity通过。CPU完整方向使用同GPU输入值再归一化以满足float64单位方向合同，独立slab则直接使用GPU原方向值。验收算术门`32*eps(float32)*6m≈2.29e-5m`是本次尺度的工程检查，非全输入形式误差证明，也非原物体几何精度。[GPU原产物](../../../../results/task8/t8-exec-20261026/geometry-gpu.json)记录同步墙钟/真实输出device/dtype/peak；GPU tensor峰值3,425,792 bytes。

### 性能、几何差异与限制

本次七夹具单次CPU64单线程预处理0.11757–0.12307s，加载0.000286–0.13221s，32400射线查询0.00145–0.04884s；常驻tensor1,600,000–1,626,296 bytes。CUDA32 CPU预处理0.11678–0.12342s，上传同步墙钟0.00112–0.00145s，32400射线同步查询0.000491–0.049917s，32组碰撞同步0.00204–0.07820s；前几次包含首次kernel调用开销，未预热/多次统计。GPU并未显示一致提速，本节点不宣称GPU加速收益或训练吞吐。射线/几何microprofile不替代8.6整环境profile。

压缩盒数empty/axis/rotated/occlusion/boundary/slab/random为0/1/89/2/1/1/103，对应占据数0/8000/6780/8000/2000/400/13057；没有填孔。轴对齐原1m立方体前向解析距离1.5m与体素一致；旋转45°原盒前向`2-sqrt(.5)=1.2928932188134525m`，体素命中`1.3000000000000007m`，差**+0.007106781186548172m**。此为采样+floor体素表示差异，不称浮点误差，不外推全角度/薄墙上界。单采样层代表闭体素厚度0.05m，稀疏点之间的孔洞保留；不保证连续真实薄结构重建或所有原资产可通行。

尚未由本节点运行真实Core step越域/路线/partial-reset、24语义图或SAC/WM；前者交8.4/8.5/8.6，不能把单元几何测试叫全环境通过。未增加科学条件、epsilon几何膨胀或新策略输入；未执行全仓历史测试。共享来源台账由父维护，以上新增主张须父关联统一条目后纳入父结论。

### 文件哈希与下一步

|文件|SHA256（faaa2cea32）|
|---|---|
|`src/task8_sim/scene.py`|bdfee03c67dc866db0bd38f22d499c9a8ba180f9485856417478b9425cc79d91|
|`src/task8_sim/tests/test_scene.py`|b03637d1ad62c3bb43b8ced2e80ecd3b5054a869e4ee303cabbd7a999c5cd98d|
|`src/task8_sim/tests/test_scene_collision.py`|c7a810b38b4f52ab7fe1ff2f085ccb54b4a76b355ba215fcfc6ea1527ba9e098|
|`geometry-cpu.json`|0b96c4018b380d862056eb3e5ced9684d73afef2b7e1860a212346e08fcca27e|
|`geometry-gpu.json`|fd64b7334a68c4ac87323a0482c9df3101beada601d00a7f0e22480aa4c5950f|

代码冻结交父及独立Sol high审查；读本记录、原产物与账本后复核closed接触、压缩union、PCD干预、q provenance和同device执行；通过后才能接8.4。无运行任务/PID，GPU0已释放；后续若有修复由原责任人按父范围处理，不覆盖其他节点。

## fix round1 — 显式lo/hi闭接触修复

状态review，实际gpt-6.1-sol / high；推荐GPT6.1sol high / Claude Sonnet5.5 high，理由同前。父给本轮累计≤60s，GPU0另明确≤15s且计入总额，未扩科学范围。按systematic-debugging读独立原日志→追踪lo/hi到中心半尺寸重构→先失败测试→修复→CPU全集/GPU定向验证。

### 根因与最小修改

独立[13f9466c2d](../../../../logs/task8/t8-exec-20261026/13f9466c2d.log)的PCD点`[-4.979,-3.979,.521]`产生显式lo`[-5,-4,.5]`/hi`[-4.95,-3.95,.55]`。球胶囊`a=b=[-5.03125,-3.975,.525],r=.03125`是精确二进制接触，contains/表面raycast/broad均命中，而旧中心半尺寸distance`.031250000000000444>r`拒绝。原13项CPU测试和随机胶囊参照未覆盖此舍入路径，不能证明闭接触合同。独立1080例探索中含非精确构造，因此不把全部394个未报都当已证明缺陷，采用精确单例/零半径/二进制半径确认问题。

修复局限于碰撞原语，不动packing/raycast/contains、科学尺寸或task7：

- 新`_segment_bounds_distance_squared`沿原task7 `segment_box_distance`分段二次最小化方法，在world系直接使用`lo-a`与`a-hi`残差及`b-a`；不生成中心/半尺寸。slab相交直接赋距离平方0，避免重算交点`a+t*d`又产生非零残差。与原半径平方比较，无epsilon、nextafter扩展或新增裕量。
- base同类问题由RED复现：首图底盘从左恰好接触的直接世界端点区间相交，旧SAT返回False。保留0.99×0.67m矩形与四条SAT轴，改为投影实际footprint四顶点和体素原始lo/hi，避免重构体素端点。删除不再使用的`_boxes`中心半尺寸缓存及其内存计数。
- 新增CPU精确单例、5位置×6面×半径(0,.03125,.0625)=90面接触，以及5位置各4侧base显式端点区间对照；另新增同90面CUDA32接触回归。原随机/scipy、地面、出域、干预及q provenance全部保留。

[最小实现diff](../../../../results/task8/t8-exec-20261026/geometry-fix1.diff)仅包括scene.py碰撞修复。生成时反向重构旧文件并断言旧SHA确为`bdfee03c...79d91`，不是无基线的手写变更摘要。未改tests/test_scene.py；只扩test_scene_collision.py。

### 实际命令与结果

仍经父run_budget，owner=`8.2-fix1`；容器/单线程/PYTHONPATH/禁止pycache与前节相同；pytest仍`python3 -B -m pytest -q -p no:cacheprovider`。每个完整实际argv见共享budget.json。无训练、超时或遗留任务。

|原日志|外/内上限s|执行与结果|worker s|
|---|---|---|---|
|[a8e442ac9c](../../../../logs/task8/t8-exec-20261026/a8e442ac9c.log)|15/12|`src/task8_sim/tests/test_scene_collision.py -k "regression or all_faces or endpoint"`；rc1，3 failed，精确球/90面接触/base同类缺陷均先RED|2.467507|
|[b6c9916e30](../../../../logs/task8/t8-exec-20261026/b6c9916e30.log)|15/12|`src/task8_sim/tests/test_scene_collision.py`；rc0，8 passed|4.820723|
|[01dd7285ea](../../../../logs/task8/t8-exec-20261026/01dd7285ea.log)|25/22|`src/task8_sim/tests`，`CUDA_VISIBLE_DEVICES= TASK8_GEOMETRY_REPORT=.../geometry-cpu-fix1.json`；rc0，58 passed/3 skipped，pytest12.46s。此collection在下项新增CUDA接触回归前启动；该新增项只在GPU执行|13.132298|
|[2ce007dd20](../../../../logs/task8/t8-exec-20261026/2ce007dd20.log)|15/13|`src/task8_sim/tests/test_scene.py src/task8_sim/tests/test_scene_collision.py -k cuda`，`CUDA_VISIBLE_DEVICES=0 TASK8_GEOMETRY_GPU_REPORT=.../geometry-gpu-fix1.json`；rc0，3 passed/16 deselected，pytest7.70s|8.476218|
|[42ac191096](../../../../logs/task8/t8-exec-20261026/42ac191096.log)|5/无容器|host Python生成diff/附版本hash；rc1，旧SHA断言和diff成功，但root所有的CPU JSON拒绝host写入。没有修改科学结果，未隐瞒此失败|0.114318|
|[1bd0c9de50](../../../../logs/task8/t8-exec-20261026/1bd0c9de50.log)|5/3|相同proof/hash逻辑在已有容器执行；rc0，旧SHA断言、diff、两新JSON附实现hash/round、文件SHA全部输出|0.164352|

本轮累计**29.175416s/60s**，其中GPU命令8.476218s/15s，开跑前`nvidia-smi --query-compute-apps`为空，结束已告父释放GPU0。含初版本节点总计74.076716s；末次共享余额1639.814278s，实时后续用量仍由父账本管。结果JSON的`implementation_sha256`是在实测后附加的文件版本元数据，CPU测试文件hash含随后仅在GPU执行的新CUDA回归；scene.py在CPU/GPU实测与附hash之间未变。

### 新版本证据与限制

以[geometry-cpu-fix1.json](../../../../results/task8/t8-exec-20261026/geometry-cpu-fix1.json)及[geometry-gpu-fix1.json](../../../../results/task8/t8-exec-20261026/geometry-gpu-fix1.json)为本轮对应版本，不覆盖旧产物。CPU/GPU七图各32400ray命中mask及独立slab参照继续通过；GPU32与CPU64最大斜距差仍3.020154e-7m，32组base/arm碰撞和128contains parity通过；90项GPU二进制半径/零半径面接触通过。原精确球和base反例现由CPU回归直接验证。

新单次CPU预处理0.116315–0.123719s、32400ray查询0.001262–0.049779s；常驻tensor1,600,000–1,619,704 bytes。新CUDA同步射线0.000452–0.047564s、batch32碰撞0.001982–0.078298s，peak3,421,696 bytes。仍未预热/多次统计，不能用作GPU一致提速、训练吞吐或整环境验收；旧原物体离散化差异和薄结构限制未改变。

|文件|修复后SHA256（1bd0c9de50）|
|---|---|
|`scene.py`|2f1e50c701523838c31e03b9b94f367cb49eb4bf5e67cc3b8dfd215f0ea9d38f|
|`tests/test_scene.py`（未改）|b03637d1ad62c3bb43b8ced2e80ecd3b5054a869e4ee303cabbd7a999c5cd98d|
|`tests/test_scene_collision.py`|419c3be6b1e60e6ce82a551c67b3f9e5f6155823bdb7070f08242199d1e0db30|
|`geometry-cpu-fix1.json`|0a73f500c59f78f99fcd9237db8f0326e8fb449d08cfc70de5f1bce9278f4a07|
|`geometry-gpu-fix1.json`|5fd7331bd61f8a04a4bb920d85544d7bacd39adf37534aaff181d50fcddc7f6c|
|`geometry-fix1.diff`|fcc64c0eeb3a2a3134a92fd827e6da3b1e1a03a488fcac95d05e3b35cfe20e1e|

交父亲读diff及独立high定向重审，待其确认才能解除8.4依赖门。局部二次距离与SAT均为等价工程实现，以上只主张已覆盖的精确构造和有界实测，不声明任意浮点输入的形式正确性证明；无新增研究条件或许可豁免。

## 规划历史（以下尚未执行仅表示实施前状态）

状态：**review（规划；尚未执行）**。规划Codex；执行负责人：几何Agent（派发时登记具体Agent及实际模型/强度）。Codex实施与独立验收均用**GPT6.1sol / high**，理由是体素边界、射线/碰撞和独立几何参照需要推理，不能派Luna承担。Claude备选**Sonnet5.5 / high**；本次按用户要求派Sol。 实际模型/强度未知，不以推荐代填。依据[用户SRC-0989](../../../SOURCES.md#src-0989)、[父模型分工](../TASK.md#model-routing)。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

**规划阶段历史（实施前）**：当时尚未执行，只建立规划；无本节点实现、测试、仿真、地图生成或性能结果。不沿用task7旧成绩作验收。

## 执行记录模板（每run追加，保留历史）

- run-id/开始结束：尚未执行。
- 目标/授权与输入：见[TASK](TASK.md)；依赖8.1的MapAsset与夹具验收后；与8.3独立文件可并行。
- 负责人：几何Agent待派发；实际模型/推理强度：未知。
- 修改文件/版本/hash：尚无；限定TASK列出的文件。
- 实际命令/容器/设备/退出码、日志/产物：尚无。
- 验收项与结果：尚未验证，见[TASK](TASK.md)及[PROCEDURE](PROCEDURE.md)。
- 共享预算消耗/余额、全局墙钟/累计worker：尚未执行，向父领取余额。
- 问题/风险/证据来源：未实施；沿父任务限制，不假定PCD迁移或SAC已通过。
- 下一步：收到执行派发后先核依赖与范围；提交父复核，不自行将父状态标done。
