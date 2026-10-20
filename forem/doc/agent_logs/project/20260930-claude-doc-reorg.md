# DOC-REORG：按任务模块整理 forem/doc

- Agent：Claude，Sonnet5.5；推理强度平台默认（未知）；未启动子Agent。
- 状态：done；2026-09-30 15:48–15:55 +08:00
- 用户要求：“doc目录下很乱，好好整理一下，按照每个任务模块分类放好”。
- 授权：只移动/重排文档并修正引用；不改各文档语义、不改源码；不提交、不推送。
- 并发：另一 Claude 会话于 15:47 启动 task0.12（active），其日志 `agent_logs/20260930-claude-task0-fix3.md` 和 task0.12 三文档未移动/未改，避免与其写入冲突；其 PROGRESS 行保留，完成后需把该日志移入 `agent_logs/task0/task0.12/` 并改该行链接。

## 问题（整理前）

- `agent_logs/` 平铺 28 个文件（含 5 个 verification.json），项目级记录与 task0.6–0.12 各轮审核/修正日志混在一起，看不出归属。
- `PROGRESS.md` 表格被散文打断，后续行追加在散文之后，无法作为一张表阅读。
- `README.md` 索引没有列出 task0 的 12 个子任务和 agent_logs 结构。

## 实际改动

1. `agent_logs/` 下建立镜像任务编号的子目录并移动 26 个文件（文件名不变）：
   - `project/`：original-reset、forem-agents、forem-doc、forem-layout、three-documents、task-numbers、git-clean、scwm-simulation-audit 及 4 个对应 verification.json（含本日志）。
   - `task0/`：env-choice、codex-env-handoff（+json）、claude-env-setup。
   - `task0/task0.6` … `task0.11/`：各子任务日志，含 Codex 子Agent 代码审核日志。
   - 留在原位：`TEMPLATE.md`、`20260930-claude-task0-fix3.md`（active）。
2. 引用修正：脚本对被移动文件的所有 `agent_logs/<文件名>` 引用做替换（PLAN、task0 及 task0.6/0.7/0.8/0.9/0.11 的文档、根 AGENTS.md），并重算 3 份被移动日志内部的相对链接（claude-env-setup、claude-task0-remediation、claude-task0-fix2）。
3. `PROGRESS.md` 重排：当前状态摘要、项目级表、task0 表（节点列按编号排序）、task1、状态更新时间线（原散文原样保留）；新增 DOC-REORG 行。
4. `README.md` 重写：目录结构图、放置规则、task0 子任务表、Agent 记录索引。
5. 根 `AGENTS.md` 第 3 节“开工前”第4条与 `agent_logs/TEMPLATE.md` 补充子目录约定。

## 验证

- 用脚本遍历 `forem/doc`、`forem/ENV.md`、根 `AGENTS.md` 的全部 markdown 相对链接，检查目标是否存在（见下方结果，含整理前对照）。
- 未做内容层面的审校；移动后文件 sha 未变（除内部相对链接被重算的 3 份和上述引用被替换的文档）。

## 交接

无运行任务。task0.12 完成后请其负责人移动日志并更新 PROGRESS 该行与 README 索引最后一行。
