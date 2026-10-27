# task8.3 — 结果与交接

状态：**done（2026-10-26本节点范围已由父及独立Sol high复核通过；task8整环境尚待后续）**。实际模型/强度：gpt-6.1-sol/medium实施、gpt-6.1-sol/high独立复核。证据[SRC-0993](../../../SOURCES.md#src-0993)、[最终依赖门SRC-0994](../../../SOURCES.md#src-0994)。推荐Codex GPT6.1sol / Claude Sonnet5.5，几何high/传感器medium（复杂排错high）；推荐不代替实际配置。历史规划/过程保留。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

**规划阶段历史（实施前）**：当时尚未执行，只建立规划；无本节点实现、测试、仿真、地图生成或性能结果。不沿用task7旧成绩作验收。

## 执行记录模板（每run追加，保留历史）

- run-id/开始结束：尚未执行。
- 目标/授权与输入：见[TASK](TASK.md)；依赖8.1共享合同；robot策略可独立做，PcdPanorama最终依8.2。
- 负责人：传感器Agent待派发；实际模型/推理强度：未知。
- 修改文件/版本/hash：尚无；限定TASK列出的文件。
- 实际命令/容器/设备/退出码、日志/产物：尚无。
- 验收项与结果：尚未验证，见[TASK](TASK.md)及[PROCEDURE](PROCEDURE.md)。
- 共享预算消耗/余额、全局墙钟/累计worker：尚未执行，向父领取余额。
- 问题/风险/证据来源：未实施；沿父任务限制，不假定PCD迁移或SAC已通过。
- 下一步：收到执行派发后先核依赖与范围；提交父复核，不自行将父状态标done。

## t8-exec-20261026 — implementation active (2026-10-26)

负责人Codex `t83_sensor`；实际模型`gpt-6.1-sol` / medium（父派发参数）。推荐与实际分开：Codex GPT6.1sol / medium，Claude Sonnet5.5 / medium；复杂碰撞/遮挡归因升high，理由沿[TASK](TASK.md)。授权依据[SRC-0990](../../../SOURCES.md#src-0990)，工程协议依据[SRC-0987](../../../SOURCES.md#src-0987)。独立[日志](../../../agent_logs/task8/task8.3/20261026-sol-sensor.md)。

目标：固定ghost传感器和两明确传感器body豁免；仅改本节点robot/perception/tests/sensor配置，无task7/URDF/许可表改动，无训练。当前已实现，**真实SceneBatch扫描集成待8.2交付并验证，未验收**。父维护共享PROGRESS/SOURCES。

|预算命令ID|结果|累计worker墙钟(s)|证据|
|---|---|---:|---|
|0e0712faf8|预期红测2 failed，robot模块尚无，rc1|1.966862|[原日志](../../../../logs/task8/t8-exec-20261026/0e0712faf8.log)|
|1425518155|2 passed，rc0|2.066977|[原日志](../../../../logs/task8/t8-exec-20261026/1425518155.log)|
|d83078a73d|预期红测3 failed，perception模块尚无，rc1|2.017007|[原日志](../../../../logs/task8/t8-exec-20261026/d83078a73d.log)|
|368a942019|3 passed/5 deselected，rc0|2.267319|[原日志](../../../../logs/task8/t8-exec-20261026/368a942019.log)|

实际命令均为宿主`run_budget.py --owner 8.3 --limit 25 -- sg docker -c ...`，容器`forem-dev`内`timeout 23s`、CPU/float64、CUDA_VISIBLE_DEVICES空、OMP/OPENBLAS线程1、PYTHONDONTWRITEBYTECODE=1、`python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests/test_ghost_sensor.py`，各次-k及完整argv/开始结束/退出码见[共享账本](../../../../logs/task8/t8-exec-20261026/budget.json)。own计算消耗8.318164s/120s配额；未运行GPU。

已核：两个velodyne body独立接触阴性，原schema4数据/索引/allowed/zero表一致；真实top_plate/arm-arm正例保留。测试采用实际FK/碰撞引擎及局部迁移球夹具，不宣称新的网格几何精度。实际Kinematics.solve_world(...,robot=同一ghost对象)返回accepted，输出由同对象检查无自碰撞/地面接触。扫描已实现但未依赖替身宣布通过。

下一步：真实8.2 SceneBatch＋已核7份PCD夹具完成扫描/碰撞/地面/Grid/inside/姿态无关回归，再向父申请最终核验；hash在最终交接时补全。reset/动作末扫描与批量GPU由8.4/父集成验收，不用本节点单测代替。无遗留运行进程。

## t8-exec-20261026 — review handoff (2026-10-26)

**状态review：实现和本节点CPU/GPU验证已完成，等待父独立审查；不代表task8整体完成。** 实际模型仍为gpt-6.1-sol/medium；推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，复杂几何归因high。目标/授权/负责人同上。新实测主张随以下原始证据交父统一登记SOURCES，登记前标“待父统一登记”，不作父级已验收结论。

|命令ID|结果|worker墙钟(s)|证据|
|---|---|---:|---|
|6ea597a13a|真实PCD/SceneBatch，own CPU 8 passed，rc0|3.418798|[原日志](../../../../logs/task8/t8-exec-20261026/6ea597a13a.log)|
|f69aae3409|GPU0 parity 1 passed/8 deselected，rc0|3.569126|[原日志](../../../../logs/task8/t8-exec-20261026/f69aae3409.log)|
|f00db1cc7c|当前task8 CPU集合53 passed/2 skipped，rc0|8.826349|[原日志](../../../../logs/task8/t8-exec-20261026/f00db1cc7c.log)|

CPU联合通过后，父明确授权GPU0累计≤30s且计入原120s额度；运行前nvidia-smi compute apps为空。GPU实际命令同共享账本，`--limit 29`、容器`timeout 27s`、`CUDA_VISIBLE_DEVICES=0 TASK8_TEST_CUDA=1`，pytest `-q -s ... -k gpu32`。实查输出tensor为cuda:0/torch.float32，valid与CPU float64逐像素相同，深度最大绝差5.881453315481622e-7m；同步后联合查询计时0.6106485166s（含CPU参考，不是纯GPU计时），peak tensor allocated20,502,016bytes；base/arm/self_collision标志一致。测试2e-5m为明确工程精度验收门，独立于体素尺寸，不是形式误差上界；实际误差也小于旧task7 test_perception GPU门2e-6m。GPU锁已释放。

最后广测在收到父“先不广测”消息前已启动并完成，记录为当时工作树快照；8.2当时仍修改自己的实现/测试，因此不以该快照代替8.2最终验收。未再重复。**own累计验证24.132437838s/120s，无超时；全局余额以共享账本实时值为准。**

交付行为（待父来源登记）：

- GhostRobotGeometry继承已核schema4，保留body列表、names、allowed、self_body_allowed、zero-pair索引及原FK/环境胶囊；独立检测掩码只豁免velodyne1_base_link、velodyne2_base_link；未改旧URDF/许可表。body_boxes保留形状/索引用于既有接口；检测API忽略这两body。
- PcdPanorama调用真实SceneBatch.raycast，固定原360×90像素中心/6m/base相对z=.5m与解析地面；caps/body不参与扫描。Depth附sensor_policy=ghost-v1、self_occlusion=ignored；self_hit/origin_inside_self=false表示禁用自遮挡，绝不代表物理上原点没有交叠。
- 实测真实PCD近障碍遮住远障碍，inside场景仍返回零斜距，未将valid全部设真；上半空射线保持无返回。移动base XY/yaw外参、地面点、Grid落点累积/隐藏点不泄露均有断言。真实robot不同q扫描相同，旧Panorama原点在self内全无效反例保留。
- sensor-only球/真实body接触阴性；arm-arm/top_plate接触阳性保留；真实PCD机械臂/底盘碰撞及ground阳性保留。局部迁移球夹具使用真实FK/许可/碰撞引擎，**不代表新网格真值或随机姿态全覆盖**。Kinematics.solve_world用同一个ghost对象并返回可接受的无自碰撞/地面接触解。

最终SHA256（父若后续修改须重新登记）：

|文件|SHA256|
|---|---|
|forem/src/task8_sim/robot.py|4ff158e50bb3fefd9e340b419b0469e32b10d7c19ef905a6950338f937248e5e|
|forem/src/task8_sim/perception.py|f76287ba4a4d4cf993a19ceab9b59fd100184f83e6a1dd4526068fbbbe6774a9|
|forem/src/task8_sim/tests/test_ghost_sensor.py|f22263b24768423da9738e901ab23e6fab300cd6d3d169686cfd16ff24bdfa83|
|forem/config/task8/sensor.json|b29ba7ef378a00caba3cf98a00774f5d6158057688d536cefdba1b5d6a371005|
|forem/src/task8_sim/scene.py（集成时8.2输入）|bdfee03c67dc866db0bd38f22d499c9a8ba180f9485856417478b9425cc79d91|
|forem/config/task7/robot_geometry.json（只读）|6c41120ad85bdea61a24b1089e825febf4f6b62eb93da0474e51f386167b084a|
|cube-pool/manifest.json|762547eb2e7f634f37016a349220265db1cfdd6e3f4f2b5691c06873a714ef90|

剩余/限制：父审diff/原始证据、统一登记来源；8.4必须把reset和动作末scan都接同一配置，并核真实部分reset/step。本节点未训练、不证明SAC稳定/提升，不覆盖所有24图任务可行性；无遗留进程，暂无需要停止/恢复事项。
