# task5.5 最终sim评估启动

- 用户授权：“你启动一下验证”；限定现有三条5M策略的既定sim最终评估，不含Gazebo或训练。
- 负责人Codex；开始 2026-10-19T22:47:46+08:00；active。实际模型/强度无法独立核实，未知。推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（需核对隔离、评估口径与产物）；推荐不等于实际。
- 计划：沿用task6.1评估脚本与既有启动器，三条策略、固定场景种子2001–2050、确定性动作、max_steps 2000、max_close_steps 500。尚未执行。
- 计划变更：本日志、task5.5三文档、PROGRESS、SOURCES；原始启动/验证证据归logs/results；不改源码、训练配置或checkpoint。
- 前置实查：forem-dev仅docker-init和sleep；GPU0–3各14 MiB、0%；现有其他容器未触碰。git main ahead42，工作区已有大量他人改动，保留。

## 已启动与交接（2026-10-19T22:49:44+08:00）

- 已执行三条既定sim最终评估；Docker后台启动返回0、隔离实例63/64/65就绪且ROS master可达。评估GPU实际进程（宿主PID）844488/844496/844498，各708 MiB，分别cuda:0/1/2；未运行训练update。策略与输入设备由现有ScwmSAC/父SAC构造、load map_location及select_action.to(self.device)路径控制，CUDA进程及逐回合输出已核实。
- 本次快照每条已记录回合数：[12, 12, 14]，无Traceback；此为启动验证，不是最终指标。
- 运行证据：`forem/logs/task5/t5.5-final-eval-launch-20261019/`的manifest、三条launch收据、gpu/processes/instances.txt及startup-verification.json。[SRC-0380](../../../SOURCES.md#src-0380)。
- 监控：读取`forem/logs/task6/t5.5-final-sim-sK-r1/eval.out`；最终`forem/results/task6/t5.5-final-sim-sK-r1/eval.json`。包装脚本自然结束后按实例身份清理，日志记录eval/stop rc。停止时先核对当前PID/命令及实例run-id，仅SIGTERM本条评估，再scwm_instance.py stop对应实例；不要使用未经核实的旧PID。
- 本轮目标“启动验证”已交付；整个评估状态active，尚未检查最终结果。未创建自动通知/监控任务。后续完成后检查三条分母50、completed/capped/errored和退出码，再与F0同口径对照。
- 实际改动：task5.5 TASK/PROCEDURE/RESULTS、本日志、PROGRESS、SOURCES；新增启动证据日志。不改源码/训练配置，不触碰其他容器。

2026-10-20结果核对与入账接续：[独立结果日志](20261020-codex-final-sim-results.md)（保留本启动记录）。
