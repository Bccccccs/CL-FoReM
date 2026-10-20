# task3.1 核心来源、任务和接口冻结 — 结果与交接

> **当前状态（2026-10-19核对）：done（随task3经task3.6 R2验收）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

**当前：done，父Task3.6 R2独立验收通过（2026-10-07），旧review是历史。** 最终当前freeze4、GPU默认及来源/时间/路径/包装身份修正闭环见[3.6结果](../task3.6/RESULTS.md)及[SRC-0066](../../../SOURCES.md#src-0066)。推荐GPT6.1sol/Sonnet5.5，跨模块medium，常规整理low/default；实际原Claude强度未知，最终验证子gpt-6.1-sol/medium。

状态：**review（实施完成，待task3.6独立复核）**。实施：Claude（Sonnet5.5，推理强度平台默认/未知；推荐medium）。授权：用户2026-10-07消息“启动并实施Task3（3.1–3.5）”。日志：[agent_logs/task3/20261007-claude-task3-impl.md](../../../agent_logs/task3/20261007-claude-task3-impl.md)。

## 实际完成与证据

|项|实际|证据|
|---|---|---|
|来源清单|8个参考包、266个文件导入`forem/src`：254逐字、12个补丁；每个文件有source/destination SHA256、license、reference git；补丁各有reason+diff+`semantic_impact`|[source_manifest.json](../../../../config/task3/source_manifest.json)、[patch_reasons.json](../../../../config/task3/patch_reasons.json)、[patches/](../../../../config/task3/patches/)；生成器`scripts/task3_import_sources.py`|
|未导入范围|husky其余9包、pcl_configure（gdt_tf被pose_bridge取代）、cloud_merger/tf_lookup/ocs2_msgs/tmc_control_msgs/realsense、PR2/Tiago/HSR源码、main.py/eval.py/main_ray.py/evaluation_*/myray/baselines、`modulation（修改后）`、`改过的地图场景`、`modulation_rl(复件)`|manifest的`excluded`段|
|静态审计|manifest、shadow、prior、assets、semantic、contract六项全过，退出0|`scripts/audit_task3_core.py`；[audit.json](../../../../results/task3/t3.1-audit-r1/audit.json)|
|契约|core/task/sac/world四份schema=1契约|[core_contract](../../../../config/task3/core_contract.yaml)、[task_contract](../../../../config/task3/task_contract.yaml)、[sac](../../../../config/task3/sac.yaml)、[world](../../../../config/task3/world.yaml)|
|入口审计|对参考的21个Python脚本（含ROS节点、launch辅助、库）做import/调用/硬编码路径分析|[husky_branches.json](../../../../results/task3/t3.1-audit-r1/husky_branches.json)；讲解见[task3.5](../task3.5/RESULTS.md)|
|单元测试|28项（source_contract 16、semantics 2、pose_bridge 10）通过|`python3 -m unittest tests.test_task3_source_contract tests.test_task3_semantics tests.test_task3_pose_bridge`，退出0|

测试名对应：`test_shadow_import_rejected`、`test_prior_required_entry_rejected`、`test_missing_asset_rejected`、`test_semantic_diff_required`均在`tests/test_task3_source_contract.py`，含反例（同名look-alike目录、第二个modulation树、重复顶层sac.py、prior标记、未解析包/缺mesh、无声语义补丁、被改动的目标/参考文件、未登记文件）。

## 冻结的任务/机器人事实（读源码得到，运行确认见3.2/3.3）

- 任务：`SimpleObstacleTask`，world_type=gazebo，动作3维`[vel_norm, base_rot, base_vel]`（不是六关节），观测`tuple(41维 robot_state, 120×120×1 本地地图)`，终止＝到达目标/IK失败≥20/碰撞≥20/MaxCloseSteps≥500，成功＝无IK失败、无碰撞且到达。
- **生效值与构造参数不同**：`SimpleObstacleMap`在构造后把障碍间距/偏移覆盖为3.0/0.8；`MaxCloseStepsWrapper`取500；reset时底盘z=0.05；`drawJointValues`总返回折叠起始姿态。
- **配置是重建的**：main.py的env_config不含`execute_style/perception_style`，生效值为direct/base；原作者实际命令行未知（[SRC-0053](../../../SOURCES.md#src-0053)）。
- 规划关节 vs 实际：`perception_style=base`只把底盘位姿换成TF实测，观测中的臂关节仍是IK规划值。
- 位姿来源：Gazebo p3d `/ground_truth/state` → TF → RobotEnv；`pose_source=gazebo_reference`。
- 原main.py**不是普通基线**：硬编码`/home/cbl/.../checkpoints_pnp_plus/...4000`作冻结prior，`resume=True`先评估20 episode并写入replay，再用`update_parameters_modified`训练。普通更新取`SAC.update_parameters`（[SRC-0058](../../../SOURCES.md#src-0058)）。

## 发现的问题（本节点）

1. 参考`modulation_rl/scripts`同时存在`modulation`与`modulation（修改后）`两个包树和`改过的地图场景`目录；后两者名称非法标识符，不会被导入但会混淆审计——不导入，audit_shadow拒绝其出现。
2. `husky_ur5/src/husky_goal.py`含U+200B，语法错误；不在闭包内。
3. 旧环境审计称main.py不走ray_utils，与源码不符（见[SRC-0057](../../../SOURCES.md#src-0057)）。
4. 引用`realsense2_description`的宏只在accessory启用时展开；在core_contract声明`unreached_package_references`（需reason+evidence，否则assets审计失败）。

## 限制

静态审计不能证明运行语义；运行证据在3.2–3.5。契约值中标`measured`的均来自run-id，其余`source-only`。没有从原作者处取得真实CLI。

## 交接

- 当前负责人：Claude（实施，已完成）；复核：Codex task3.6。
- 复核方法：`python3 forem/scripts/audit_task3_core.py`（宿主）、`python3 -m unittest tests.test_task3_source_contract tests.test_task3_semantics`；`python3 forem/scripts/task3_import_sources.py manifest`应无`patched_without_reason`。
- 后续节点依赖：3.2使用本节点manifest/契约。无后台进程。

依据：[SRC-0042](../../../SOURCES.md#src-0042) · [SRC-0043](../../../SOURCES.md#src-0043) · [SRC-0044](../../../SOURCES.md#src-0044) · [SRC-0046](../../../SOURCES.md#src-0046) · [SRC-0053](../../../SOURCES.md#src-0053) · [SRC-0057](../../../SOURCES.md#src-0057) · [SRC-0058](../../../SOURCES.md#src-0058)。

## Agent模型与推理强度

推荐Codex GPT6.1sol、Claude Sonnet5.5；跨模块来源核对medium。实际：Claude Sonnet5.5，强度未知（平台默认）。
