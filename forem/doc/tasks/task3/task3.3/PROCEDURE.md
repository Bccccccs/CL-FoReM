# task3.3 机器人、IK、观测与任务核心迁移 — 实施计划与详细流程

**当前：done，父Task3.6 R2独立验收通过（2026-10-07），旧review是历史。** 最终当前freeze4、GPU默认及来源/时间/路径/包装身份修正闭环见[3.6结果](../task3.6/RESULTS.md)及[SRC-0066](../../../SOURCES.md#src-0066)。推荐GPT6.1sol/Sonnet5.5，跨模块medium，常规整理low/default；实际原Claude强度未知，最终验证子gpt-6.1-sol/medium。

> 执行Agent：后续明确授权后按superpowers:executing-plans逐项执行；不默认委派，不自动启动实现。研究参数/来源和实际配置分别登记。

**Goal：** 迁移原环境reset/step链与任务/地图，验证底盘动作、末端计划和关节执行角色一致。

**Architecture：** 接收父任务契约与依赖节点结果，按下面文件职责和步骤交付；产物/版本单一事实来源为本节点RESULTS，父结果链接汇总。

**Tech Stack：** FoReM容器内ROS Noetic/Gazebo、原Husky控制/环境/SAC；Task4按冻结选择接入视觉惯性定位。

**Spec：** [本节点TASK](TASK.md)及[父流程](../PROCEDURE.md)。

**授权更新（2026-10-07）：** 用户明确授权实施task3.1–3.5（必要源码迁移、容器依赖适配、构建、启动与验证），不含Task4定位/人工误差/补偿/世界模型/新任务/大规模训练；原“仅计划、尚未执行”是历史状态。实施结果与证据见同目录RESULTS，3.6由Codex独立复核。

**递归规则：** 每层恰有TASK.md、PROCEDURE.md、RESULTS.md；子任务放父目录内并继承编号，更深拆分同样先建三文档；父流程列顺序、依赖、负责人、三文档及验收关系，父结果仅汇总实际子结果。编号稳定不复用，不另建同职责README/PLAN/reports。当前无委派；如后续委派先登记输入、范围、模型/强度、日志与验收，父Agent独立核验。


## 输入与输出接口

输入：task3.2已核验；父契约、源代码/实际依赖收据、固定任务实例、运行权限与资源上限。输出：本节点交付、配置/代码diff/hash、运行命令和退出码、原日志/数据及验收结论；失败与未执行项同样写RESULTS。

## 计划文件（已实现；实际文件与差异见下方“实际实施偏差”）

- `forem/src/modulation_rl/src/robot_env.cpp`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/modulation_rl/src/robot_husky.cpp`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/modulation_rl/src/worlds.cpp`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/modulation_rl/scripts/modulation/envs/robotenv.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/modulation_rl/scripts/modulation/envs/combined_env.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/modulation_rl/scripts/modulation/envs/eeplanner.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/modulation_rl/scripts/modulation/envs/tasks.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/src/modulation_rl/scripts/modulation/envs/map.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/scripts/check_task3_env.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/tests/test_task3_env_contract.py`：由本节点按以下职责实现/接收；本轮仅文档。

## 执行步骤

- [x] 1. 接收3.1清单与3.2实际模型，编译C++/pybind并建立Python导入来源证据；剥离其他机器人硬依赖仅在单Husky可达闭包证明无用后记录，不改算法语义。
- [x] 2. 保留当前底盘动作→下一预期base→末端计划/IK→同控制步异步发送arm/base的关系；记录每步SAC/脚本动作、转换后的cmd、IK状态和实际反馈，不能称SAC默认直接输出六关节。
- [x] 3. 按冻结task_contract接回目标采样、地图/局部地图、原观测字段顺序/归一化、奖励项、碰撞、IK失败、成功/终止与截断。SimpleObstacleTask静态环境是首任务，不新增门/抓放/动态障碍。
- [x] 4. 移除/home/cbl和旧workspace硬编码路径，配置/资源只由FoReM入口解析；离线本地日志不需要外部账号，网络上传不作为运行依赖。
- [x] 5. reset真实复位并清理本episode状态/前动作，检查时钟回退、连续两次reset、非法/越界动作和失效TF；get_robot_obs中规划态与实际测量标签分开。
- [x] 6. 用同公开初态/目标与动作序列做原函数级语义回归和新物理运行；不把迁移修复默默变成新的reward/观测定义。

## 验证与异常处理

- 接口reset(seed, episode_spec)与step(action)在包装层返回契约规定obs、reward、done、info；旧Gym四元组与截断语义明确，不因库升级暗改。
- test_action_shape_rejected、test_observation_field_order、test_reset_clears_previous_action、test_reward_components_preserved、test_expected_joint_not_labeled_actual。
- 至少一条完整任务尝试可终止并保留失败理由；随机动作失败不等于迁移失败，但物理/接口/错误输入问题须关闭。

（历史计划表述）CLI/测试已实现并运行，实际命令、退出码与偏差见RESULTS。命令前核对容器/锁/foreign，真实构建/检查退出0及预期证据齐全才通过，不用空测试或动画代替。来源、契约/有限性、错误frame、时间/reset、进程身份或预算失败立即停止本run，保留证据，不回退隐藏真值、不覆盖旧run。修复保持授权范围，换run-id/版本，必要时重跑受影响先导。下一节点仅在本节点必要验收通过后运行。

依据：[SRC-0042](../../../SOURCES.md#src-0042) · [SRC-0043](../../../SOURCES.md#src-0043) · [SRC-0044](../../../SOURCES.md#src-0044) · [SRC-0046](../../../SOURCES.md#src-0046)。

## Agent与推理强度

推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**。常规文档/明确步骤运行low或平台默认；来源迁移、坐标/时间/观测与验收的跨模块核对medium，理由是需要追踪完整因果链。当前文档作者Codex /root，实际模型/强度未知；拟Claude实施、Codex独立复核，均未接手，不自动启动Agent。实施时记录实际配置，推荐不冒充执行配置。


## 实际实施偏差（2026-10-07，Claude）

C++/Python环境文件逐字导入于3.1清单（未重复列出）；新增`scripts/{task3_env.py,check_task3_env.py}`、`tests/test_task3_env_contract.py`。
全部步骤已勾选为已执行；具体命令/run-id/退出码/失败与修正历史见[RESULTS](RESULTS.md)。
