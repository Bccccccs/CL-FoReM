# task3.5 核心集成验收与Task4交接契约 — 实施计划与详细流程

**当前：done，父Task3.6 R2独立验收通过（2026-10-07），旧review是历史。** 最终当前freeze4、GPU默认及来源/时间/路径/包装身份修正闭环见[3.6结果](../task3.6/RESULTS.md)及[SRC-0066](../../../SOURCES.md#src-0066)。推荐GPT6.1sol/Sonnet5.5，跨模块medium，常规整理low/default；实际原Claude强度未知，最终验证子gpt-6.1-sol/medium。

> 执行Agent：后续明确授权后按superpowers:executing-plans逐项执行；不默认委派，不自动启动实现。研究参数/来源和实际配置分别登记。

**Goal：** 冻结可复现的核心运行入口和向Task4交付的定位替换边界。

**Architecture：** 接收父任务契约与依赖节点结果，按下面文件职责和步骤交付；产物/版本单一事实来源为本节点RESULTS，父结果链接汇总。

**Tech Stack：** FoReM容器内ROS Noetic/Gazebo、原Husky控制/环境/SAC；Task4按冻结选择接入视觉惯性定位。

**Spec：** [本节点TASK](TASK.md)及[父流程](../PROCEDURE.md)。

**授权更新（2026-10-07）：** 用户明确授权实施task3.1–3.5（必要源码迁移、容器依赖适配、构建、启动与验证），不含Task4定位/人工误差/补偿/世界模型/新任务/大规模训练；原“仅计划、尚未执行”是历史状态。实施结果与证据见同目录RESULTS，3.6由Codex独立复核。

**递归规则：** 每层恰有TASK.md、PROCEDURE.md、RESULTS.md；子任务放父目录内并继承编号，更深拆分同样先建三文档；父流程列顺序、依赖、负责人、三文档及验收关系，父结果仅汇总实际子结果。编号稳定不复用，不另建同职责README/PLAN/reports。当前无委派；如后续委派先登记输入、范围、模型/强度、日志与验收，父Agent独立核验。


## 输入与输出接口

输入：task3.4已核验；父契约、源代码/实际依赖收据、固定任务实例、运行权限与资源上限。输出：本节点交付、配置/代码diff/hash、运行命令和退出码、原日志/数据及验收结论；失败与未执行项同样写RESULTS。

## 计划文件（已实现；实际文件与差异见下方“实际实施偏差”）

- `forem/scripts/validate_task3_core.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/scripts/collect_task3_core.py`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/config/task3/execution_freeze.json`：由本节点按以下职责实现/接收；本轮仅文档。
- `forem/tests/test_task3_core_lifecycle.py`：由本节点按以下职责实现/接收；本轮仅文档。

## 执行步骤

- [x] 1. 运行固定契约下的启动/静止/直行/转向/协调、任务reset/step、SAC smoke与checkpoint回放，记录全部尝试，不以成功尝试选择性汇总。
- [x] 2. 复测一次进程启动、一次中断和一次重新reset，检查底盘命令停止、所属arm目标退出、仿真/采集无本run残留；不得停止他人运行。
- [x] 3. 对有效原bag/日志独立检查命令/实际响应、控制周期和帧，冻结模型/代码/依赖/配置/任务实例/pose来源/CLI及接口hash。
- [x] 4. Task4接收：机器人/控制/任务/动作/观测/奖励/截断、地图来源、可替换pose topic及frame、旧true-position通路列表；摄像头/IMU未加入的事实单列。
- [x] 5. 提交3.6交审清单与明确风险，未解决控制/来源/契约问题保持review，不因文档完整标父done。

## 验证与异常处理

- core_receipt.json可验证来源、构建、运行、资源、动作与SAC接口，所有失败有run-id/退出码/日志。
- test_foreign_process_not_stopped、test_clock_reset_requires_new_episode、test_checkpoint_reload_uses_frozen_obs，真实入口中断后无本run残留。
- 给Task4的baseline合同完整；不借Task1/2旧固定臂结果验收移动核心。

（历史计划表述）CLI/测试已实现并运行，实际命令、退出码与偏差见RESULTS。命令前核对容器/锁/foreign，真实构建/检查退出0及预期证据齐全才通过，不用空测试或动画代替。来源、契约/有限性、错误frame、时间/reset、进程身份或预算失败立即停止本run，保留证据，不回退隐藏真值、不覆盖旧run。修复保持授权范围，换run-id/版本，必要时重跑受影响先导。下一节点仅在本节点必要验收通过后运行。

依据：[SRC-0042](../../../SOURCES.md#src-0042) · [SRC-0043](../../../SOURCES.md#src-0043) · [SRC-0044](../../../SOURCES.md#src-0044) · [SRC-0046](../../../SOURCES.md#src-0046)。

## 迁移后的用户讲解交付

用户要求迁移完成后详细说明原Husky“有几条线、各自什么用途”。3.1审计原运行入口/调用图，3.5在本层RESULTS交付完整说明，3.6按源码和运行证据核对。按“算法训练/评估分支”“在线任务到物理执行链”“世界模式/位置来源”分别给核实计数；不把重复源码树或入口文件数冒充有效运行线。每条说明目的、入口、输入输出、上下游、活跃/历史状态和迁移保留/改造/未迁移范围，并标未运行项。迁移完成后向用户逐条讲解，不只交文件清单；本轮尚未迁移，也未核实最终数量。审核说明其他分支不扩大本次移植范围。[SRC-0049](../../../SOURCES.md#src-0049)

## Agent与推理强度

推荐Codex **GPT6.1sol**、Claude **Sonnet5.5**。常规文档/明确步骤运行low或平台默认；来源迁移、坐标/时间/观测与验收的跨模块核对medium，理由是需要追踪完整因果链。当前文档作者Codex /root，实际模型/强度未知；拟Claude实施、Codex独立复核，均未接手，不自动启动Agent。实施时记录实际配置，推荐不冒充执行配置。


## 实际实施偏差（2026-10-07，Claude）

实际：`scripts/{validate_task3_core.py,check_task3_clock.py,collect_task3_instances.py,freeze_task3.py,regress_task3_lifecycle.py,task3_lifecycle_driver.py,build_task3_receipt.py}`、`config/task3/{execution_freeze.json,core_receipt.json}`、`tests/test_task3_core_lifecycle.py`；计划名`collect_task3_core.py`由`collect_task3_instances.py`+各check脚本分担。
全部步骤已勾选为已执行；具体命令/run-id/退出码/失败与修正历史见[RESULTS](RESULTS.md)。
