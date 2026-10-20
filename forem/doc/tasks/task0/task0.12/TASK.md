# task0.12 task0.11复核P2修正 — 任务

状态：done（经task0.13独立复核；当前固定底座UR5环境范围验收通过）。

历史状态记录：状态：review（Claude 已于2026-09-30执行并自测，结果见[RESULTS](RESULTS.md)；待Codex复核，父task0保持review）。来源：[task0.11 RESULTS](../task0.11/RESULTS.md) 的“新发现 P2：中断时反馈采集进程不在监督清理范围”。

## 目标与范围

`run_task0_smoke.sh` 直接 `docker exec` 运行 `check_feedback.py`：TERM/INT 中断宿主脚本后，容器里的采集进程不会被终止，且不在 launch/bag 监督树内、也不在按名称的 foreign 名单里，回归报告 PASS 却遗留进程。修正：

1. 把本次 `check_feedback` 也放进带 pid+启动身份的监督（与 launch、bag 同一机制），中断时先停采集器再停 bag/launch。
2. 采集器退出码由监督进程记录并写入 manifest；清理采集器不得把健康检查失败掩盖成成功，也不得把中断误报为成功。
3. 回归：TERM/INT 后按“本次 run-id 的完整命令行”核验采集器确实不存在，不再只靠 ROS/Gazebo 名称；正常采集、失败采集、重复 run/并发拒绝路径保持并复测。

范围只在 forem 脚本/测试/文档；不改物理/控制配置，不启动 task1、误差注入、IK、SAC、世界模型；不提交/推送；不碰他人进程。

## 完成条件

新回归先在旧脚本上失败（复现采集器遗留），再在新脚本上通过；新 run-id 的 fresh 启动、60 s 保持、高频运动复测通过；RESULTS 含问题—修正—证据表，置 review 交 Codex 复核。

## 模型与推理强度

Codex GPT6.1sol / Claude Sonnet5.5，medium。实际 Claude Sonnet5.5，档位平台默认（未知）。
