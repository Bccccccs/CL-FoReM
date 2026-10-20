# task0.6 独立审核 — 结果

> **当前状态（2026-10-19核对）：done（审核交付）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：done（审核交付完成；task0 仍为 review，需要修正后再验收）。负责人 Codex /root；2026-09-30 +08:00。用户授权审核，无生产实现修改、无 task1 启动、无提交/push。

## 已完成与证据

- 独立静态审核见 [代码审核日志](../../../agent_logs/task0/task0.6/20260930-codex-task0-code-review.md)；父Agent核验源码及CSV，不将子Agent自报完成视作环境通过。
- 容器 forem-dev 只挂载 forem 与只读入口；镜像 sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430；包解析 /root/mm_husky_ws/src/forem_sim，ROS_PACKAGE_PATH/CMAKE_PREFIX_PATH 仅新工作区及 /opt/ros/noetic。
- `sg docker -c "bash forem/docker/run.sh exec bash -c 'catkin build forem_sim -j2 -p1'"` 退出0，1包成功，无警告；日志 `forem/logs/task0/task0.6-build.log`。本次增量构建；Claude已有的干净重建日志也已读取。
- 两次新 fresh launch：`sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.6-r1 --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'`，随后同参数 `task0.6-r2`；均退出0。六关节运动、125Hz joint/controller反馈、时钟递增、底座最大变化2.3486e-6、停止后残留0。分别保留 results/task0/task0.6-r1、r2 与对应 logs；独立原始数据核验见 `results/task0/task0.6-review/retest-audit.json`。
- 历史 t0.5-r1/r2/x1 的 manifest 全部列出的源文件hash均匹配当前。desired-actual 与记录error一致至2.23e-16rad；真实位置反馈链路有效，无命令回填。数据核验 `results/task0/task0.6-review/evidence-audit.json`。

## 审核发现与结论

1. **P1 正常保持存在持续高频状态振荡，不能当作偶发读数异常结案。** 只将joint_state/controller state发布率从125改为2000Hz，其余PID、模型、0.5ms物理步长不变，运行 `sg docker -c 'bash forem/logs/task0/task0.6-diagnostic/run.sh'` 退出0，2s保持记录3607个joint样本（实际1796Hz，有丢采样，未声称完整2000Hz）。3197对相邻0.5ms样本的肩lift速度符号100%交替；位置峰峰7.123e-6rad，速度约±0.0141rad/s，effort约±2.855N·m；位置差分与速度最大差1.703e-8rad/s。这证明仿真关节状态每步交替，即约1kHz有界振荡，125Hz采样会混叠。没有数值发散，但“静止速度偏置/偶发读数翻转”的解释不成立。具体根因（PID/物理求解等）尚未隔离，不能宣称已定位。证据 `results/task0/task0.6-diagnostic/{joint_states.csv,controller_state.csv,high-frequency-analysis.json,step-consistency.json,manifest.json}`；诊断配置与完整执行脚本 `logs/task0/task0.6-diagnostic/`。应先定位并消除或明确论证该基线动力学现象，不能只过滤反馈，再作正常基线验收。
2. **P2 自动验收有假通过路径。** `scripts/check_feedback.py:169–181` 未校验controller_state覆盖记录窗口，3个递增样本后中断仍可通过；运动仅用峰峰值下界，反向或持续有限数值偏离目标也可通过。本次CSV确实连续且向目标响应，但现有pass=true不足以独立证明要求。补充反馈覆盖/间隙、目标方向及有限范围基本稳定性检查；这不要求提前制定task1性能阈值。
3. **P2 运行入口不能严格限定本次任务清理，也允许覆盖历史。** `scripts/run_task0_smoke.sh:11,21,38,72` 无EXIT/INT/TERM清理trap、按进程模式pkill而非保存本次PID、无并发锁；复用run-id覆盖已有数据并可能读取旧startup日志；残留不参与最终退出条件。本次3轮复测已核验无残留，但异常退出/并发时不能保证“仅停止本次进程”。应拒绝已有run目录、使用锁及本次PID清理、把清理失败纳入退出码。
4. **P2 报告终值误差符号反了。** `task0.5/RESULTS.md:29–32` 标题为实际−目标，而raw t0.5-r1中shoulder_lift=+0.000610806978，elbow=−0.000756061637，wrist_1=+0.0000908358832，wrist_2=−0.0000636881871rad，与表中符号相反；r2同样。应按明确公式重算，未验证的“重力+积分限幅导致”属于假设，不能写作确定因果。

**验收结论：搭建、构建、真实位置反馈与两次启动连通性已独立核实；正常基线稳定性和自动验收可靠性尚有上述问题，task0暂不标done。** 任务保持review，交给Claude修正并追加新run证据后复核。没有更改正式源码/PID/物理配置。

## 交接与剩余事项

当前负责人：审核 Codex /root 已完成；实现修正建议由Claude继续，但本轮没有自动启动其会话。优先处理P1，之后补充验收与进程管理、纠正文档。此审核结论不自动授权task1/误差注入/训练。

三轮本次仿真均已停止，容器内无roslaunch/gzserver/rosmaster；forem-dev保持Up，两个旧mmhusky容器仍Up。重启及停止方法继续见ENV；不改动旧容器。诊断配置仅用于此次审核，正式入口仍125Hz。

## 模型与推理强度

推荐 Codex GPT6.1sol、Claude Sonnet5.5，中等（medium）：需要跨模块核对启动、反馈与验收逻辑。实际 Codex /root 与代码审核子Agent的模型/档位未从平台核实，未知；未主动切换模型。
