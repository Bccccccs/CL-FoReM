# task8.3 独立规格与代码审查

run-id：t8-exec-20261026。负责人Codex t823_review；实际模型gpt-6.1-sol / high（父派发参数）。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium；碰撞/遮挡细节归因用high。本次实际high不代表Claude已运行。

目标与授权：只读核查ghost robot/perception/config/真实PCD测试及原始CPU/GPU证据；仅本日志可写，不改实现、共享文档、子RESULTS、task7，不训练、不提交、不派Agent。合同继承[SRC-0987](../../../SOURCES.md#src-0987)、授权[SRC-0990](../../../SOURCES.md#src-0990)；新核查主张由父统一登记SOURCES。

开始状态active。已读dispatch-common与必读文档（见兄弟8.2审查日志）；核main既有dirty状态，无测试/训练遗留进程。父独占PROGRESS。

审查范围：robot.py、perception.py、sensor.json、test_ghost_sensor.py、task7 robot/kinematics/geometry/perception只读依赖、8.2 scene接口、6ea597a13a/f69aae3409原日志；CPU复验与8.2共享≤35s并入owner8.23-review，无GPU复验授权。

## 初审结果：spec compliance PASS / code quality PASS（本节点范围）

未发现8.3自身阻断；8.4仍须等待8.2闭接触P1修复，不将本判定视为task8整体通过。未重复同代码/同目的测试，亲读原始测试代码、产物、原日志与继承的RobotGeometry/FK/自碰撞路径，不能只凭子总结。

- GhostRobotGeometry不删除body条目、不改names/allowed/self_body_allowed/zero-pair索引；显式SENSOR_BODIES仅两个velodyne。schema4球–body检测掩码只将这两列设false，arm–arm仍调用原引擎；contacts/self_contacts仅清对应sensor行列。environment caps/body几何与FK均保留。继承self_collision从实际q/胶囊provenance进入重载_sphere_collision，Kinematics传同一robot对象，未看到回到旧传感器碰撞对象的路径。
- 独立sphere_fixture将球映射到真实FK局部系，保留真实body/permission引擎；分别验证两个sensor-only接触old=True/ghost=False，top_plate与arm–arm仍True，原数据/索引/allowed保留。不是只mock返回值；真实IK解分支测试使用ghost对象并核无self/ground。
- PcdPanorama沿原360×90像素中心、360°/90°、6m、base相对(0,0,.5)m；随base XY/yaw变换，真实SceneBatch最近命中与解析ground求min。caps/body完全不参与扫描，origin在self内不使扫描失效，scene内部origin仍0。Depth只含原tensor字段与两字符串模式元数据，无occupancy/sidecar/真值height注入；Grid继续原落点update。
- 测试真实PCD近物遮远物、空场上半无返回、移动外参、旧Panorama全无效的自内原点反例、不同q/真实机器人包络扫描不变；Grid隐藏远块中心未观测。并验证PCD base/arm与ground仍阳性。该Grid点级断言不是8.4候选/rollout整路径无泄露证明，后者仍待集成验收。
- 原[6ea597a13a](../../../../logs/task8/t8-exec-20261026/6ea597a13a.log)：CPU8 passed，rc0；原[f69aae3409](../../../../logs/task8/t8-exec-20261026/f69aae3409.log)：GPU1 passed，rc0，真实cuda:0/float32，valid全像素一致，最大实际深度差5.881453315481622e-7m、peak20,502,016bytes、联合CPU+GPU同步wall.6106485s。2e-5m是工程门且实际小于2e-6m，不是PCD原物体精度证明；不称纯GPU计时或端到端性能提升。

风险/下一步：8.2闭接触修复后核其对本节点接口无回归；8.4必须统一reset与step扫描配置、部分reset隔离和策略真值边界。传感器几何接触夹具不是全网格/全姿态覆盖。无训练、无遗留运行；新审查主张待父统一登记SOURCES。本节点可在8.2修复后供8.4消费。

## 8.2 fix1后依赖复核

8.2 F1闭接触缺陷经定向重审已关闭，详见[8.2审查日志](../task8.2/20261026-sol-review.md)。新CPU当前集合原日志01dd7285ea为58 passed/3 skipped；修复不改raycast/Depth/ghost接口。本审3a01976cc0在CPU验证并核hash，robot `4ff158e50bb3fefd9e340b419b0469e32b10d7c19ef905a6950338f937248e5e`、perception `f76287ba4a4d4cf993a19ceab9b59fd100184f83e6a1dd4526068fbbbe6774a9`均与初审一致。**8.3 spec compliance PASS / code quality PASS维持，无自身阻断；8.2依赖已由独立重审放行。** 后续reset/step配置与策略隔离仍归8.4/8.6，非本节点新完成事项。父统一来源登记，未重复GPU。
