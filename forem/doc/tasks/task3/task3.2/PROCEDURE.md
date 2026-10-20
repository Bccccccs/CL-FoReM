# task3.2 移动模型、控制器与参考位姿链 — 实施计划与详细流程

**当前：done，父Task3.6 R2独立验收通过（2026-10-07），旧review是历史。** 最终当前freeze4、GPU默认及来源/时间/路径/包装身份修正闭环见[3.6结果](../task3.6/RESULTS.md)及[SRC-0066](../../../SOURCES.md#src-0066)。推荐GPT6.1sol/Sonnet5.5，跨模块medium，常规整理low/default；实际原Claude强度未知，最终验证子gpt-6.1-sol/medium。

> 执行Agent：后续明确授权后按superpowers:executing-plans逐项执行；不默认委派，不自动启动实现。研究参数/来源和实际配置分别登记。

**Goal：** 在FoReM独立构建并启动Husky+UR5物理模型，验证底盘/机械臂控制与参考位姿来源。

**Architecture：** 接收父任务契约与依赖节点结果，按下面文件职责和步骤交付；产物/版本单一事实来源为本节点RESULTS，父结果链接汇总。

**Tech Stack：** FoReM容器内ROS Noetic/Gazebo、原Husky控制/环境/SAC；Task4按冻结选择接入视觉惯性定位。

**Spec：** [本节点TASK](TASK.md)及[父流程](../PROCEDURE.md)。

**授权更新（2026-10-07）：** 用户明确授权实施task3.1–3.5（必要源码迁移、容器依赖适配、构建、启动与验证），不含Task4定位/人工误差/补偿/世界模型/新任务/大规模训练；原“仅计划、尚未执行”是历史状态。实施结果与证据见同目录RESULTS，3.6由Codex独立复核。

**递归规则：** 每层恰有TASK.md、PROCEDURE.md、RESULTS.md；子任务放父目录内并继承编号，更深拆分同样先建三文档；父流程列顺序、依赖、负责人、三文档及验收关系，父结果仅汇总实际子结果。编号稳定不复用，不另建同职责README/PLAN/reports。当前无委派；如后续委派先登记输入、范围、模型/强度、日志与验收，父Agent独立核验。


## 输入与输出接口

输入：task3.1已核验；父契约、源代码/实际依赖收据、固定任务实例、运行权限与资源上限。输出：本节点交付、配置/代码diff/hash、运行命令和退出码、原日志/数据及验收结论；失败与未执行项同样写RESULTS。

## 计划文件（已实现；实际文件与差异见下方“实际实施偏差”）

- `forem/src/forem_husky/package.xml`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/forem_husky/CMakeLists.txt`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/forem_husky/launch/husky_core.launch`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/forem_husky/urdf/husky_core.urdf.xacro`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/forem_husky/scripts/pose_bridge.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/config/task3/controllers.yaml`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/config/task3/world.yaml`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/scripts/run_task3_core.sh`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/tests/test_task3_pose_bridge.py`：由本节点按以下职责实现/接收；本轮仅文档。

## 执行步骤

- [x] 1. 按3.1清单复制必要包到forem/src，保留ROS包名/资源URI/pybind模块名并记patch；组合包forem_husky只负责组装与入口，参考husky只读。
- [x] 2. 保留现有forem_sim固定UR5入口，与新移动入口互斥使用同容器/仿真锁，不同时spawn同名机器人/控制器。复用已验收容器，不安装宿主ROS、不盲目重建容器。
- [x] 3. 构建独立forem/build/devel；移植Husky四轮模型、UR5/夹爪安装、底盘Twist、effort轨迹controller和MoveIt/BioIK需要的配置。物理求解器沿用FoReM已验收选择起步，移动条件重新检查，必要适配写差异。
- [x] 4. pose_bridge输入nav_msgs/Odometry及原采样stamp，在pose_source=gazebo_reference时发布原策略需要的TF；移除原重盖时间gdt_tf重复发布者。控制器joint反馈、底盘/末端独立仿真测量分别记录。
- [x] 5. 依次检查静止、直行、转向和底盘/臂共同动作的基本响应，验证命令实际走物理控制，不以world_type=sim解析状态或瞬移结果验收。
- [x] 6. 对启动失败/中断使用现有身份监督和foreign核查，只停止本run进程；收集日志、有效运行参数、TF发布者、资源与控制器状态。

## 验证与异常处理

- catkin实际构建退出0、ros package/module路径落在forem/devel/src。
- 唯一有效map/odom/base发布链，TF原采样stamp与参考消息一致；test_duplicate_pose_authority_rejected、test_wrong_frame_rejected、test_backdated_and_duplicate_rejected、test_late_sample_without_reset_is_rejected_not_an_epoch、test_real_reset_halts_and_old_epoch_samples_are_never_published（T3-A02修正后更名/新增）覆盖关键边界。
- 四种动作检查有原命令和实际位姿/关节证据；机器人限位/非有限/未解释振荡拒绝交审，截图不能代替数据。

（历史计划表述）CLI/测试已实现并运行，实际命令、退出码与偏差见RESULTS。命令前核对容器/锁/foreign，真实构建/检查退出0及预期证据齐全才通过，不用空测试或动画代替。来源、契约/有限性、错误frame、时间/reset、进程身份或预算失败立即停止本run，保留证据，不回退隐藏真值、不覆盖旧run。修复保持授权范围，换run-id/版本，必要时重跑受影响先导。下一节点仅在本节点必要验收通过后运行。

依据：[SRC-0042](../../../SOURCES.md#src-0042) · [SRC-0043](../../../SOURCES.md#src-0043) · [SRC-0044](../../../SOURCES.md#src-0044) · [SRC-0046](../../../SOURCES.md#src-0046)。

## Agent与推理强度

推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**。常规文档/明确步骤运行low或平台默认；来源迁移、坐标/时间/观测与验收的跨模块核对medium，理由是需要追踪完整因果链。当前文档作者Codex /root，实际模型/强度未知；拟Claude实施、Codex独立复核，均未接手，不自动启动Agent。实施时记录实际配置，推荐不冒充执行配置。


## 实际实施偏差（2026-10-07，Claude）

实际文件：`src/forem_husky/{package.xml,CMakeLists.txt,launch/husky_core.launch,worlds/husky_empty.world,scripts/pose_bridge.py,scripts/pose_gate.py}`、`scripts/{run_task3_core.sh,check_task3_physics.py,task3_lib.py,task3_manifest.py}`、`tests/test_task3_pose_bridge.py`；未建`urdf/husky_core.urdf.xacro`（沿用husky_ur5.xacro并带xacro参数）、`config/task3/controllers.yaml`（控制器配置逐字取自husky_control/husky_ur5，见world.yaml）。补丁：去重力关闭标签、去不可用插件、Python3.10重建。
全部步骤已勾选为已执行；具体命令/run-id/退出码/失败与修正历史见[RESULTS](RESULTS.md)。
