# task0.12 task0.11复核P2修正 — 流程

遵循根AGENTS递归规则；本节点不拆子节点，Claude 顺序执行。

1. 接手：读 task0.11 三文档与其证据（`results/task0/task0.11-checks/collector-residue.json`）；登记进度与日志；确认容器无外来/遗留进程。
2. 先写失败回归：扩展 `regress_task0_smoke.py` 的 TERM/INT 用例，按“本次 run-id 的完整命令行”查采集器；用当前（旧）脚本运行，证明会遗留（保留证据后清理，仅按 pid+启动身份）。
3. 修正：`task0_proc.py` 增加退出码记录（supervisor 收割 root 时写 `<name>.exit.json`）、`exitcode` 与 `grep` 子命令；`run_task0_smoke.sh` 用监督方式启动/等待 check，清理顺序 check→bag→launch，退出码写入 manifest；`foreign` 名单加入 check_feedback。
4. 回归与单测：进程管理单测增加退出码与快速退出；入口回归覆盖正常采集、失败采集（退出码传递）、TERM/INT（采集器清零）、重复/并发。
5. 重验：新 run-id 的 fresh 启动 ×2、60 s 保持、高频保持/运动、阴性对照。
6. 文档：RESULTS、父 RESULTS、ENV、PROGRESS、独立日志。

规则：只对自己创建/已核实身份的进程发信号；旧证据不覆盖；新 run-id 不复用。

## 模型与推理强度

Codex GPT6.1sol / Claude Sonnet5.5，medium。
