# task7.24.3 — 有界计时与A/B短跑

**2026-10-26执行冻结：paused。** 用户已冻结task7全部后续执行，见[父冻结入口](../../TASK.md#2026-10-26-当前冻结入口)。已完成成果与下文历史状态保留；不得依旧授权自动续训、恢复或派发。当前转入task8地图迁移规划。

状态：active（已登记待派发）；负责人Codex子Agent，2026-10-23T14:51:00.757134+08:00。

授权：[SRC-0971](../../../../SOURCES.md#src-0971)，规格[父TASK](../TASK.md)。

范围：依赖实现与监督通过，执行P2/P3/P4；共用累计4h预算，先固定评估案例/端到端成本检查，再GPU3单worker串行A/B各50k，汇总未完成项和限制。

唯一源码写入根（监督只读）：/home/ybc/.codex/worktrees/task7-24-short-task/CL-FoReM/forem。共享原工作树forem/src/config/scripts禁止写入。运行副本/home/ybc/projects/CL-FoReM/forem/build/task7.24/source只允许本任务同步，启动自己的计算后不再覆盖其源码。数据/日志仅/home/ybc/projects/CL-FoReM/forem/results/task7/t7.24-short-20261023和/home/ybc/projects/CL-FoReM/forem/logs/task7/task7.24。共享文档只由父Agent写，子Agent仅写本三文档及独立日志/home/ybc/projects/CL-FoReM/forem/doc/agent_logs/task7/task7.24/task7.24.3/20261023-codex-work.md。禁止委派子Agent、Git提交/推送、停止或恢复非本任务进程。

输入：根AGENTS、forem/AGENTS、父TASK/PROCEDURE、workspace.json、已批准配置与前序交付。交付：具体命令/退出码/版本、证据与问题，供父复核；SOURCES拟条目交父登记，不直接写全局账本。

推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium；实现/运行需跨模块medium，监督需独立科学合同审查high。实际子Agent将显式请求gpt-6.1-sol/medium，尚未派发时不写已运行。


当前状态更新（2026-10-23T15:52:24.303095+08:00）：active（Sol medium已派发P2预检，P3待成本门禁）；依据[SRC-0973](../../../../SOURCES.md#src-0973)。
