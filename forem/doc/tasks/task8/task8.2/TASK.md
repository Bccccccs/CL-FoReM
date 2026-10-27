# task8.2 — PCD共享几何、射线与碰撞查询

状态：**done（2026-10-26本节点范围已由父及独立Sol high复核通过；task8整环境尚待后续）**。实际模型/强度：gpt-6.1-sol/high实施及独立复核；闭接触fix1通过。证据[SRC-0993](../../../SOURCES.md#src-0993)、[最终依赖门SRC-0994](../../../SOURCES.md#src-0994)。推荐Codex GPT6.1sol / Claude Sonnet5.5，几何high/传感器medium（复杂排错high）；推荐不代替实际配置。历史规划/过程保留。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 依赖、文件范围与交付

依赖：8.1的MapAsset与夹具验收后；与8.3独立文件可并行。

- 新建`forem/src/task8_sim/scene.py`和`tests/test_scene.py`、`tests/test_scene_collision.py`。
- 实现VoxelScene/SceneBatch，不改task7 geometry/perception或资产模块。
- 交付体素构建、射线最近命中、整机碰撞适配、planning_height、contains及来源接口。

## 接口

消费MapAsset；产生父PROCEDURE所列VoxelScene/SceneBatch。occupancy采用z/y/x索引、world米；射线origin/direction形状[E,R,3]且方向单位化，输出[E,R]斜距；缺命中inf，origin在占据内0。SceneBatch绑定每个环境map_id/hash；select/replace不能使未选行读取别图。

## 验收与范围限制

`test_scene.py`：空夹具/同点重复、轴平行/掠边/角/内部起点、最大量程外、两层遮挡、半开索引/闭接触、射线域外入域/离域无命中、batch真实动作越域不增虚拟碰撞、批量两图替换。`test_scene_collision.py`：接触/分离、底盘投影离地障碍仍阻挡、arm高度穿空与撞实体、arm高于1.6m无虚拟天花板、包络部分出域不生墙、地面保留、自碰撞由robot报告。PCD变更干预通过，且JSON box删除/改动不改变同一PCD运行几何；JSON几何只产差异报告。

遵守父任务不改科学条件、仅有界验收、task7只读、无训练的约束。实现后的子结果只由父复核后纳入父验收，不自行更新共享文档。日志路径`forem/doc/agent_logs/task8/task8.2/YYYYMMDD-agent-topic.md`。本节点交付不等于整个task8完成。
