# task0.13 采集器修正独立复核 — 结果

> **当前状态（2026-10-19核对）：done（task0最终独立复核）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：done；Codex于2026-09-30独立复核通过，task0.12采集器P2关闭，父task0环境验收done。实际模型/推理档位未知；代码复核子Agent同样未知。没有修改生产实现、提交/push或进入task1。

## 验收依据

1. 宿主、容器各45项单元测试全部OK、退出0；日志 `forem/logs/task0/task0.13-checks/unit-host.log`、`unit-container.log`。先前PID/孤儿/退出码及高频坏输入回归仍通过。
2. `python3 forem/scripts/regress_task0_collector.py --tag task0.13-col`：4项全部PASS，退出0。正常采集check0/wrapper0，失败采集check3/wrapper1，TERM/INT前各2条本次采集命令行、后0条，check1/wrapper143或130、cleanup0。完整docker top核验，没有采集器/监督器遗留。报告 `results/task0/task0.13-col-report/report.json`，日志 `logs/task0/task0.13-checks/collector-regression.log`。
3. `python3 forem/scripts/regress_task0_smoke.py --tag task0.13-reg`：9项全部PASS、退出0；非法/重复run、并发、启动失败、不可达容器、中断、清理失败、HF证据不足均给出正确结果；报告 `results/task0/task0.13-reg-report/report.json`。结束后完整docker top也仅保活进程，日志 `processes-after-entry.log`。
4. 新fresh启动 `task0.13-r1`、`task0.13-r2`：相同 `--duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3`，两次24项检查通过，采集/总退出/清理均0；125Hz，最大跟踪误差≤7.6442e-4rad、底座漂移≤8e-15，check和launch residue=[]。
5. 新 `task0.13-hf-move`：`--bag --hf-mode move --launch-arg controller_config:=/root/mm_husky_ws/config/diagnostics/task0.7/ur5_controllers_hf2000.yaml`，相同8s/3s轨迹。请求/运动/停稳三个窗口都通过；采集/总退出/清理均0，无残留。各run原始CSV/manifest/cleanup保留，父Agent汇总 `results/task0/task0.13-checks/final-run-audit.json`。
6. task0.12旧最终6run的48文件hash核验：仅scripts/README.md文档变动，所有执行实现及配置匹配。旧60s保持CSV实际跨度60s、全部有限、采集与清理0；高频保持/运动通过，quick阴性三个窗口失败。完整核验表 `results/task0/task0.13-checks/source-and-evidence-audit.json`。本轮未改物理/ROS包，复核既有干净构建与60s证据，不重复构建/保持。
7. 子Agent只读代码复核及安全mock支持关闭P2，父Agent实际4项回归核验；[独立日志](../../../agent_logs/task0/task0.13/20260930-codex-collector-code-review.md)。监督器记录root退出码，wrapper成功/失败/中断分别保留，清理不掩盖失败。原task0.12修正前同一K3/K4失败证据已核对，历史保留。

## 结论与完成边界

上次采集器漏清P2已关闭，先前PID/孤儿、高频假通过/时间窗口、误差符号及求解器振荡问题已有历次独立闭环证据。task0满足当前约定：FoReM独立容器/构建路径，固定底座UR5空场景、effort轨迹控制、真实反馈与参考分开、小幅轨迹响应、正常保持与高频检查、两次独立启动、正常/失败/TERM/INT清理和可靠证据保护。可以标done。

验收限于这个固定底座场景与小幅慢速轨迹，GUI/复杂接触/移动底盘/大幅高速动作/最大仿真速度未测。ODE内部机理未完全解释；world求解器在本场景效果已验证，不外推其他场景。运动后重力负载下约6e-4rad跟踪偏差是后续测量的基线特征。

Linux subreaper与/proc依赖保留；wrapper SIGKILL不可捕获，不承诺自动清理，该场景按本次meta/tree人工停止；监督器强杀前未持久记录的极短命后代边界仍在。它们与已通过的TERM/INT路径分别说明，不将未测写成通过。

## 进程与下一步

最终 `docker top forem-dev -eo pid,ppid,args` 仅docker-init/sleep infinity，证据 `logs/task0/task0.13-checks/processes-final.log`。forem-dev保留Up，无采集器/监督器/ROS/Gazebo。本轮原始数据和日志不入Git，生产代码未修改，其他Agent文档整理改动保留。

下一步建议task1正常跟踪测量；本轮未执行task1，没有添加人为延迟/扰动、IK、SAC或世界模型。使用ENV中的启动与停止方法，run-id不可复用。父RESULTS/PROGRESS保存最新done结论，历史review记录继续保留。

## 模型与推理强度

推荐Codex GPT6.1sol、Claude Sonnet5.5 medium，因涉及容器中断、进程身份和退出码跨模块核查。实际模型/档位未知，没有主动切换模型。
