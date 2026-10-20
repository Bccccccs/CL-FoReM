# task0.11 task0.10最终复核 — 结果

> **当前状态（2026-10-19核对）：done（复核交付）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：done（独立复核交付完成）；task0.10和父task0仍review：上次四项已关闭，但中断采集进程遗留尚需修正。负责人Codex /root，实际模型/档位未知。本轮不修改生产代码，不进入task1，不提交/push。

## 上次四项问题的闭环证据

- 子Agent限域代码复核见[独立日志](../../../agent_logs/task0/task0.11/20260930-codex-task0-fix2-code-review.md)，父Agent独立测试及核验。
- 宿主与容器各39项测试全部OK、退出0：logs/task0/task0.11-checks/unit-host.log、unit-container.log。涵盖PID复用、孤儿/监督进程先退出、重复stop与高频坏输入。
- 用上次复核的原CSV重新运行分析CLI：empty、two、nan、few_triples分别退出2/1/2/1、pass=false，原假通过已关闭；results/task0/task0.11-checks/prior-bad-input-recheck.json。
- 新入口回归 `python3 forem/scripts/regress_task0_smoke.py --tag task0.11-reg` 报告9项ALL PASS、退出0；原始报告 results/task0/task0.11-reg-report/report.json。注意该报告残留检查存在下面指出的盲点，因此不能据此宣称所有本次进程清零。
- task0.10最终r1/r2/60s保持/高频保持与运动的47文件manifest，当前仅scripts/README.md不同，所有执行代码和配置均匹配。高频旧数据用新evaluator按请求/运动/停稳段重算，world各段PASS，quick阴性各段FAIL；results/task0/task0.11-checks/source-and-window-audit.json。物理/控制配置本轮未变，60s保持证据已核验，不重复执行同一保持实验。
- 新fresh启动task0.11-r1/r2（8s记录、3s小幅六关节轨迹）均退出0、24检查通过、125Hz；最大跟踪误差约7.6442e-4rad，底座漂移≤5.24e-15。
- 新task0.11-hf-move使用2000Hz发布诊断+bag和move模式，退出0；请求/运动/停稳三窗口全部PASS，连续三元组最少11737/4364/5918，速度高频残差最大1.21e-6/1.84e-6/2.23e-12rad/s。证据results/task0/task0.11-checks/final-run-audit.json及各run CSV/manifest/cleanup记录。

上述证据支持关闭task0.9原四项：失效PID收养、root先退孤儿/重复stop、坏输入与不足triples假通过、整bag时间窗稀释。保留Linux subreaper依赖和监督进程SIGKILL前尚未记录的极短命后代限制；本轮未发现它们在当前ROS流程构成新阻断。

## 新发现 P2：中断时反馈采集进程不在监督清理范围

位置：`forem/scripts/run_task0_smoke.sh:127–129`直接docker exec运行check_feedback；`52–59` cleanup只停止bag、launch；`task0_proc.py:103–115`的foreign名称名单不包含check_feedback。

实际复现：task0.11-reg的TERM与INT病例结束并报告PASS后，foreign=[]，但完整docker top显示两份本轮采集器仍在：容器PID71730/start596256126（task0.11-reg-term）、PID73111/start596258971（task0.11-reg-int）。它们不是launch/bag监督进程后代，宿主docker exec客户端被中断不会确保容器中的Python进程被终止；仿真时钟停止后它们在sim_wait等待，最长900s墙钟保护，后续仿真reset也可能影响其等待。原始身份/命令：results/task0/task0.11-checks/collector-residue.json。

因此“9项回归PASS/foreign=[]”不等于所有本次进程清零。此前本轮中途口头判断task0可done已撤回，以本最终记录为准。实际核心控制/高频修正有效，但异常退出清理尚未完整。

修正要求：将本次check_feedback也纳入带PID+启动身份的监督/清理（或等效可靠所有权）；中断时先停止采集，再停bag/launch；回归TERM/INT必须验证该run所有已确认成员（包含采集器）均不再存活，不能只靠ROS/Gazebo名称列表。成功/失败采集退出码仍须正确写manifest，不能用清理采集器把健康检查失败掩盖成成功。至少复测正常采集、TERM、INT、重复run/并发拒绝路径，保持旧证据。

## 清理与交接

本轮遗留两份采集器均先核验上述pid+start+完整命令，再SIGTERM，只操作本次tag进程。实际退出后remaining=[]；证据results/task0/task0.11-checks/collector-cleanup.json。最终docker top仅docker-init和sleep infinity，forem-dev保持Up。

下一步由Claude修正此P2并增加覆盖采集器的回归，再由Codex复核。task0继续review；task1、人为延迟、IK、SAC、WM均未启动。本次审查没有改变生产实现或物理参数。

## 模型与推理强度

推荐Codex GPT6.1sol、Claude Sonnet5.5 medium：进程所有权、容器客户端中断和回归判定需跨模块核对。实际模型/档位未知。
