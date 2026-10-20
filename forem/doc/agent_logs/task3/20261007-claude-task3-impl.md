# TASK3-IMPL（task3.1–3.5）：Husky+UR5核心迁移到FoReM

- Agent：Claude（模型 Sonnet5.5 / 推理强度：平台默认，具体档位未知；推荐 medium，理由：跨模块迁移、坐标/时间/观测与排错）
- 状态：review（3.1–3.5实施完成，待Codex task3.6）。开始/结束 2026-10-07。
- 用户要求（2026-10-07 消息）：启动并实施Task3：将Husky+UR5核心迁移到FoReM。明确授权执行task3.1–3.5，包括必要源码迁移、容器依赖适配、构建、启动与验证；此前文档“仅计划、实施尚未授权”属历史状态；task3.6留Codex独立复核。
- 授权边界：只在forem内开发/构建/运行，husky只读；保留Task0/1/2及他人改动；ROS仅容器内，Docker用`sg docker -c`；迁移普通SAC.update_parameters并解释main.py的prior/modified差异；保持任务/动作/观测/奖励/终止语义；区分规划状态与实际反馈；保留Gazebo参考位姿。**不做**Task4（图像/IMU定位）、人工扰动、补偿、世界模型、新任务、大规模训练；不推送/合并，不启动其他Agent。
- 已读：AGENTS.md、forem/AGENTS.md、doc/README、PROGRESS、ENV、Task3父与3.1–3.5三文档、Husky参考源码（main.py、sac.py、model.py、robotenv/combined_env/tasks/map、robot_env.cpp、robot_husky.cpp、worlds.cpp、launch、controllers）。
- 起始状态核查：Git分支main，工作区有大量他人（Codex）未提交的doc改动与已暂存task1文件（不触碰，不盲目git add）；容器`forem-dev`（镜像mm_husky:node01）Up 7天，之前核查仅保活；GPU 4×RTX PRO 6000 Blackwell空闲，但forem-dev创建时未带GPU（torch.cuda.is_available()=False）。

## 执行记录与证据

（按阶段追加，见各子任务RESULTS与下文。）

## 进展

### 2026-10-07 11:15 进展快照（Claude）
- 已完成源码导入（scripts/task3_import_sources.py：266个文件，255逐字、11个补丁，manifest在config/task3/source_manifest.json）、catkin构建（Python3.10 ABI，logs/task3/t3.2-build3，退出0）、组装包forem_husky（launch/world/pose_bridge）。
- 关键发现：参考bumper宏对全部机器人链接设置turnGravityOff，Gazebo中底盘无法行驶（t3.2-motion-r1/grav-off-diag1），移除后命令被跟随（r2–r4）；torch先于pybindings导入会std::bad_cast，需ray先导入。
- 已运行：t3.2-motion-r1…r4（物理）、t3.3-env-r1（环境，20项通过）、t3.4-smoke-r1（普通SAC，9项通过）；单元测试：pose_bridge 10、source_contract 16、sac_roundtrip 7。
- 进行中：t3.4-train-r1（450步显式预算训练，用于拿到终止转移）。
- 未完成：三文档（3.1–3.5）、core freeze/integration/生命周期（3.5）、PROGRESS/SOURCES同步、原Husky链路讲解。

## 交接

已完成：3.1–3.5全部三文档、源码迁移（forem/src）、构建、运行验证、冻结与receipt、原Husky线讲解。证据索引：[task3 RESULTS](../../tasks/task3/RESULTS.md)；全部尝试（含失败）见[task3.5 RESULTS](../../tasks/task3/task3.5/RESULTS.md)与core_receipt.json。
未解决/风险：见task3.5 RESULTS §四（混合重力模型、门槛事后修订、CPU-only、reset_simulation不支持、样本小、高频振荡未测）。
下一步：Codex执行task3.6（清单见task3.5 RESULTS §五）；通过前不启动Task4。
接手核验：`python3 forem/scripts/audit_task3_core.py`、`python3 forem/scripts/freeze_task3.py verify`、容器内`unittest discover -s tests`、新run-id复跑`validate_task3_core.py`。
运行任务：无（容器仅docker-init/sleep，foreign=[]）。注意：我早期诊断遗留的`rosrun tf tf_echo`在容器内存活了约2小时，已确认是本人启动并停止。

## Agent模型与推理强度

- 推荐：Claude Sonnet5.5，medium（跨模块迁移/排错）；Codex GPT6.1sol medium用于task3.6复核。
- 实际执行：Claude Sonnet5.5，强度未知（平台默认）。

## 任务归属与委派

- 任务：task3（父）及task3.1–3.5；三文档见[tasks/task3](../../tasks/task3/TASK.md)。task3.6由Codex独立复核，未自行实施。
- 顺序执行，不委派子Agent。
