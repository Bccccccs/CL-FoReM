# task8.3 — 固定虚拟传感器与PCD扫描

状态：**done（2026-10-26本节点范围已由父及独立Sol high复核通过；task8整环境尚待后续）**。实际模型/强度：gpt-6.1-sol/medium实施、gpt-6.1-sol/high独立复核。证据[SRC-0993](../../../SOURCES.md#src-0993)、[最终依赖门SRC-0994](../../../SOURCES.md#src-0994)。推荐Codex GPT6.1sol / Claude Sonnet5.5，几何high/传感器medium（复杂排错high）；推荐不代替实际配置。历史规划/过程保留。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 依赖、文件范围与交付

依赖：8.1共享合同；robot策略可独立做，PcdPanorama最终依8.2。

- 新建`forem/src/task8_sim/robot.py`、`perception.py`、`tests/test_ghost_sensor.py`、`forem/config/task8/sensor.json`。
- 不修改旧URDF/robot_geometry.json、原球拟合或许可表，不删除全部机械臂碰撞。
- 交付显式ghost配置、局部派生的传感器检测掩码与PcdPanorama。

## 接口

`GhostRobotGeometry`兼容旧RobotGeometry API；从已核schema4派生副本，传感器body名单仅`velodyne1_base_link`与`velodyne2_base_link`（新增未知传感器须审计不能关键词全禁）。`PcdPanorama(SceneBatch,sensor_config)`返回旧Depth结构，复用原Grid落点更新；sensor_config记录ghost-v1、固定外参、原FOV/range/resolution。

## 验收与范围限制

至少包含原`test_panorama_shapes_occlusion_and_sensor_inside_self_report`对应的task8新语义反例：旧路径全无效的内部原点，新路径应看到场景；原task7测试及默认实现不改。sensor-only碰撞消失，arm–arm/arm–top_plate/环境障碍/ground仍能触发；移动base的射线原点变换精确符合固定外参。

遵守父任务不改科学条件、仅有界验收、task7只读、无训练的约束。实现后的子结果只由父复核后纳入父验收，不自行更新共享文档。日志路径`forem/doc/agent_logs/task8/task8.3/YYYYMMDD-agent-topic.md`。本节点交付不等于整个task8完成。
