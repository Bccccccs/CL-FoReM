# task9.11.3 · 隔离实现与分阶段执行

状态review（执行因独立FAIL_INCOMPLETE_SUPERVISION停止；未完成主实验，不重试）；负责人Codex实施sol/high，请求gpt-6.1-sol/high，实际后端未知。用户“派发吧”正式授权父task9.11按已审协议实施，58h/2TiB及全部门，不再将已获授权阶段留作待用户确认；父执行窗口见agent_logs/task9/task9.11/execution-window.json。[SRC-1395](../../../../SOURCES.md#src-1395)

写入边界：只写forem/src/task9_lr、forem/config/task9/task9_11、forem/scripts/task9_11、本子三文档/日志与本run results/logs；旧实现/输入只读；不写共享文档。原三文档/AGENTS/来源只读；不另派Agent。禁止功能拓展、改科学合同、跳独立门、自动重试/扩预算、触碰task10 GPU1或停止其他进程。

输入：根AGENTS、README/PROGRESS/ENV、父三文档与.1/.2独立审查、窗口/旧源快照。交付：本子RESULTS/独立日志、命令/源码版本/输入与退出码/真实状态/风险/下一步。未执行步骤不能标通过。主run=t9.11-lr-20261103T171820+0800，截止2026-11-06T03:18:20+08:00，T0=2026-11-03T17:18:20+08:00。

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因跨模块科学合同/恢复/性能因果审查；用户模型仅sol/terra/luna，本轮实际只派sol，不派Claude。

父执行派发细化：.4可代理独立阶段签字，实际独立门PASS且签字/原证据/源码身份与预算均经fail-closed核验后，你在原用户执行授权内自主续进，不需父或用户再次重复确认；不能跳过真实独立门。最终test交.4独立执行，你不得逐seed看结果调参。诊断完整窗口只适用全部评估case，训练保留原训练统计/交互与pending/profile。[SRC-1396](../../../../SOURCES.md#src-1396)
