# TASK3-P2-FIX（归属task3.1–3.5）：修正T3-A01/A02/A03

- Agent：Claude（Sonnet5.5；推理强度平台默认，具体档位未知；推荐medium，理由：跨模块checkpoint来源/TF时序/冻结路径）
- 状态：review（修正自测完成，待Codex复核；开始2026-10-07T13:28+08:00）
- 用户要求（2026-10-07消息）：修正Task3.6审查的三项P2（T3-A01 checkpoint来源契约；T3-A02旧位姿消息误判reset/混epoch；T3-A03 freeze实例路径依赖CWD），完成验证后交回Codex。Task3.6独立复核仍留Codex；不启动Task4/定位/人工误差/补偿/世界模型/大规模训练；不改任务/动作/观测/奖励/物理模型/控制器语义；不推送/合并。
- 起始核查：Git分支main，工作区大量他人/Codex未提交改动（保留，不git add -A）；容器仅forem-dev（docker-init/sleep），无gazebo/ROS进程；4×GPU空闲；仿真锁无持有者。
- 依据：task3.6 RESULTS、SRC-0060、SRC-0061；反例脚本/结果 results/task3/task3.6-review-20261007/。
- run-id约定：`t3.5-fix1-*`（证据 results/task3/<id>/、logs/task3/<id>/）。

## 进展

（按阶段追加。）

### 2026-10-07 13:40 代码修正与反例前后（Claude）
- 修正前反例（新ID `t3.5-fix1-before`，用旧版哈希核对一致的代码副本，旧入口sha256 25693a98…与freeze一致、旧pose_gate与freeze一致）：契约5项形状不变的改动（奖励、终止、C++控制、机器人模型、控制配置）旧checkpoint全部accepted；迟到10→8 s被发布且epoch→1；真实reset序列旧消息被发布、epoch→2、reset后发布3条；freeze verify从仓库根/任意目录退出1、forem内退出0。证据`results/task3/t3.5-fix1-before/`。
- 修正：新增`scripts/task3_identity.py`（实际文件语义身份）、`task3_sac_entry.py`契约schema2；`pose_gate.py`/`pose_bridge.py`独立/clock判断reset+halt；`freeze_task3.py`FoReM相对路径。新增测试`test_task3_identity.py`、`test_task3_freeze_path.py`，改`test_task3_pose_bridge.py`、`test_task3_sac_roundtrip.py`，同步`check_task3_clock.py`、新增反例探针`check_task3_p2.py`。
- 修正后探针（`t3.5-fix1-after`）：契约6项改动全refused；同契约往返accepted；旧t3.4 checkpoint refused；迟到样本不发布、epoch 0；真实reset后旧消息不发布、epoch 1、reset后发布0条。
- 待做：容器全量测试（运行中）、fresh集成/GPU SAC/生命周期、归档旧freeze并创建新freeze、文档同步。

## 完成 2026-10-07 14:25
交付与证据见[task3 RESULTS](../../tasks/task3/RESULTS.md#2026-10-07-task36三项p2修正claude)。运行：t3.5-fix1-int/-gpu/-life/-inst、回执t3.5-fix1-receipt均退出0；容器无本次进程。未改历史run/实例/旧freeze；未启动Task4。下一步：Codex独立复核task3.6的三项P2。
