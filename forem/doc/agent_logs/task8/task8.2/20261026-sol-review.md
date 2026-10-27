# task8.2 独立规格与代码审查

run-id：t8-exec-20261026。负责人Codex t823_review；实际模型gpt-6.1-sol / high（父派发参数）。推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high；边界/碰撞/独立参照需要几何推理。

目标与授权：只读核查8.2实现、原始PCD与测试/性能证据，分别判断spec compliance与code quality；仅本日志可写，不改实现、共享文档、子RESULTS、task7，不训练、不提交、不派Agent。来源合同继承[SRC-0987](../../../SOURCES.md#src-0987)、授权[SRC-0990](../../../SOURCES.md#src-0990)；新核查主张由父统一登记SOURCES。

开始状态active。已读dispatch-common、根/forem AGENTS、ENV、文档入口/进度、父及8.2/8.3三文档、SOURCES0984–0990、review diff；工作区main含大量既有未提交改动，无pytest/train/run_budget活动进程。父独占PROGRESS。

审查范围：scene.py、两个scene测试、assets消费接口、task7 geometry/robot只读依赖、cube-pool manifest/PCD、geometry-cpu/gpu.json及原命令日志。必要最小CPU复验总额≤35s、全部经run_budget owner8.23-review；GPU未授权不运行。

## 初审结果：spec compliance FAIL / code quality FAIL，P1阻断

**[P1] 闭体素表面胶囊接触在中心/半宽转换后漏报。** 位置`forem/src/task8_sim/scene.py:120`、`:201`–`:203`；原显式lo/hi查询与碰撞距离计算不再一致。PCD float64点`[-4.979,-3.979,.521]`构造唯一体素lo=`[-5,-4,.5]`、hi=`[-4.95,-3.95,.55]`。球胶囊`a=b=[-5.03125,-3.975,.525]`、`r=.03125`，base=`[10,10,0]`（避免无关底盘碰撞）。输入x与r均二进制精确可表示，显式x间隔正好`.03125`；y/z在盒内，因此数学距离就是r，不是构造接触点时先相减得到的模糊近接触。

原日志[13f9466c2d](../../../../logs/task8/t8-exec-20261026/13f9466c2d.log)，`run_budget owner8.23-review --limit15`→forem-dev/timeout13s/CPU float64/python3 -B，rc1（预期反例断言失败），worker2.066989s。实际精确argv在共享[budget.json](../../../../logs/task8/t8-exec-20261026/budget.json)。观察：

```text
contains([-5,-3.975,.525]) = True
raycast(origin=[-5,-3.975,.525],direction=[1,0,0]) = 0
broad candidate = True
stored centre_x = -4.975
stored half_x = 0.02499999999999991
computed segment distance = 0.031250000000000444
distance - radius = 4.440892098500626e-16
collide(...).arm = False  # 必须True
```

最小复现（在上述受预算控制的容器命令内）：

```python
import torch
from task8_sim.tests.test_scene import make_scene
s = make_scene([[-4.979,-3.979,.521]])
base = torch.tensor([[10.,10.,0.]], dtype=torch.float64)
caps = torch.tensor([[[-5.03125,-3.975,.525,
                      -5.03125,-3.975,.525,.03125]]], dtype=torch.float64)
assert s.collide(base,caps,robot=None).arm.item()
```

先行探索日志[332fe5833a](../../../../logs/task8/t8-exec-20261026/332fe5833a.log)，rc0/worker2.217352s，1080表面探测中394未报碰撞。该数量含半径`.04`输入构造roundoff，不作为394个已证明几何错误；结论仅基于随后精确二进制半径的单体素反例。累计独立复验4.284341s≤35s，未跑GPU，无遗留进程。遇反例后读并按systematic-debugging技能追到显式bounds→中心/半宽→segment distance路径，未改代码。

现有测试为何漏掉：`test_all_face_edge_corner_directions_at_negative_coordinates`只覆盖raycast；arm接触手工例位于x=0，随机SciPy capsule oracle几乎不会正好构造闭表面接触。GPU随机碰撞parity不能验证CPU和GPU共同重用的中心/半宽算法正确性。修复须保留显式闭边界语义，增加负坐标/两侧表面/非零精确半径回归；不能加任意epsilon膨胀或放宽验收。

## 已核符合项与限制

- floor float64解析、三轴半开输入校验、z/y/x占据；_pack只依相同X run→Y rectangle→Z合并，未使用sidecar/整物体AABB填孔。独立scalar raw-PCD cell slab参照与BVH实现分离；随机旋转薄片/空腔反例能暴露hull填充。公开occupancy/height/provenance均返回副本。
- raycast的closed slab、origin-inside0、域外入域、域外空及独立地面分工符合；arm地面与高于1.6m无假天花板、base旧全高度XY投影语义保留。地面与self collision不依JSON；robot q provenance在SceneBatch切片前提取，显式q优先；select/replace索引与dtype/device校验、引用替换不改其他行。
- PCD干预测试使用新manifest/hash，固定sidecar仍改变扫描/base/arm，后景变更不穿透前景；scene不读取semantics。scene是否从8.4进入policy仍需8.4/8.6整链路验收。
- 原始geometry-cpu.json的七图记录：预处理约.118–.123s、32400射线查询约.00145–.04884s；GPU JSON明确cuda:0/float32、七图32400有限mask parity、各12条独立slab参照、collision/contains parity。GPU最大实际斜距差3.020154e-7m，peak3,425,792bytes；不据此宣称GPU整体提速/端到端可行。
- 旋转解析原物体forward差`.007106781186548172m`已明确为体素几何差异，不是fp32误差。每图12独立参考射线仅抽样，且采样az集中两方向；另有300条随机薄片union参照作补充，均不能替代闭接触反例。

下一步：父退回8.2负责人定向修复，保留失败证据，修后再独立审；当前不放行8.4。8.2 RESULTS补齐由原负责人负责，本日志不代替三文档。上述新核查主张待父统一登记SOURCES。

## fix round1 定向重审：spec compliance PASS / code quality PASS

**最终判定更新：F1已关闭，无剩余阻断。** 初审失败与最小反例记录保留在上方，不将历史FAIL改写成从未发生。父可基于本审查及自身复核放行8.4；本判定不覆盖尚未实施的整环境链路。

复读[fix1精确diff](../../../../logs/task8/t8-exec-20261026/review-8.2-fix1.diff)、当前scene完整修复区域与新增测试。当前`scene.py:89`新增`_segment_bounds_distance_squared`：直接用`lo-a`/`a-hi`残差进行原分段二次最小化，保留闭slab交集距离0，`distance_squared<=r.square()`；没有中心/半宽重构、epsilon、margin或安全半径膨胀。`:118`新增`_rectangle_bounds_hits`：原0.99×0.67矩形四角投影到world XY和底盘u/v四轴，直接投影体素lo/hi，保持旧全高度XY投影语义。已删除不再使用的_boxes，provenance tensor_bytes相应变化；floor/packing/BVH/SceneBatch/q/ground逻辑未变。未修改task7源码。

已亲读原始RED/GREEN：

- [a8e442ac9c](../../../../logs/task8/t8-exec-20261026/a8e442ac9c.log)，rc1，新增3项在旧实现真实失败：精确dyadic接触、90面zero/dyadic接触、base端点闭投影。
- [b6c9916e30](../../../../logs/task8/t8-exec-20261026/b6c9916e30.log)，rc0，collision8 passed。
- [01dd7285ea](../../../../logs/task8/t8-exec-20261026/01dd7285ea.log)，rc0，CPU当前集合58 passed/3 skipped；三项CUDA另有明确GPU验证。
- [2ce007dd20](../../../../logs/task8/t8-exec-20261026/2ce007dd20.log)，rc0，GPU3 passed/16 deselected；覆盖新增五位置×六面×三半径共90接触、七图32400射线mask/collision/contains parity及独立参照。[geometry-gpu-fix1.json](../../../../results/task8/t8-exec-20261026/geometry-gpu-fix1.json)实际cuda:0/float32；最大斜距差仍3.020154e-7m，peak3,421,696bytes。不由GPU parity外推全输入精度或提速。

按verification-before-completion技能做不同目的定向复验：parent授权≤15s、owner8.23-review，原[3a01976cc0](../../../../logs/task8/t8-exec-20261026/3a01976cc0.log)，rc0/worker2.066972s，容器CPU float64，完整argv在budget.json。

1. 本审原最小反例接触arm=True；把两端x向负无穷`nextafter`移动一ULP，arm=False，确认没有通过增epsilon把分离点误报为接触。
2. seed8231生成512个yaw/XY底盘与64盒，共32768对；新world端点SAT与只读task7原四轴SAT在非特设接触的随机输入上零不一致。此项补查修复的旋转底盘实现，无新科学条件。
3. 实测哈希：scene `2f1e50c701523838c31e03b9b94f367cb49eb4bf5e67cc3b8dfd215f0ea9d38f`；collision测试`419c3be6b1e60e6ce82a551c67b3f9e5f6155823bdb7070f08242199d1e0db30`；8.3 robot/perception与初审交付hash均相同。

本次独立重审2.066972s≤15s；两轮独立核查累计6.351313s，未运行GPU、无遗留进程、不改实现/共享文档。剩余：原负责人补8.2 RESULTS最终hash/命令，父统一SOURCES登记与后续8.4/8.6验收。本节点已无需修复的审查发现。
