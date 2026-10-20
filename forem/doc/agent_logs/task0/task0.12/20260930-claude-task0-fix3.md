# TASK0-FIX3 (task0.12)：修正 task0.11 的中断采集器遗留 P2

- Agent：Claude，Sonnet5.5；推理强度平台默认（未知）；未启动子Agent。
- 状态：review；2026-09-30 15:47–16:05 +08:00
- 用户要求：“继续修改，文档已经写好”——处理 Codex task0.11 复核指出的 P2。
- 授权：只改 forem；不动他人进程；不启动 task1/误差注入/IK/SAC/世界模型；不提交/推送。
- 已读：task0.11 三文档；原 4 项已由 Codex 关闭。

## 执行记录与证据

时间均为 2026-09-30 +08:00；详见 [task0.12 RESULTS](../tasks/task0/task0.12/RESULTS.md)。

- 15:47 登记 task0.12 三文档、PROGRESS、本日志。
- 15:49 先写 `regress_task0_collector.py` 并对旧 wrapper 运行：K1/K2 通过，K3/K4 失败（采集器遗留），证据保留；两个遗留采集器按完整命令行精确匹配由我清掉。
- 15:50–15:55 修正：监督进程记录 root 退出状态、`exitcode`/`grep` 子命令、foreign 加入 check_feedback；wrapper 用监督方式运行采集器、清理顺序 check→bag→launch、中断时记录采集器退出状态；新增 6 项进程测试。过程中一个测试用例遗留 `sleep 300` 孤儿（测试自身没杀进程组），我确认是自己的后清掉并改测试。
- 15:56–16:03 45 项单测（宿主/容器）、采集器回归 K1–K4 ALL PASS、入口回归 C1–C8 ALL PASS、最终运行 r1/r2/hold/hf-hold/hf-move（退出 0）与阴性对照（退出 1）。
- 16:04 文档：task0.12 RESULTS、task0.10 更正说明、父 RESULTS、ENV、scripts/README、PROGRESS。
- 未做：未提交/推送；未启动 task1 等；未改物理/控制配置。

## 交接

- 状态 review，交 Codex 复核；容器仅 `sleep infinity`，foreign=[]。已知限制：采集期间 wrapper 被 SIGKILL 不会自动清理（下次运行 foreign 检查拒绝，需手动 stop）。
