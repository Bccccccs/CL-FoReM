# task7.23.2 — 审核流程

递归规则：每层任务恰有TASK、PROCEDURE、RESULTS三文档；如需进一步拆分须先由父Agent建立子任务三文档并登记，当前不新增子任务。

1. 阅读授权、AGENTS及指定输入，记录实际模型与强度。
2. 核查task7.18.4–7.18.8与task7.19的现有日志和产物，重点v5退化、不同步候选不可达、D10完整性；复算小型JSON/CSV统计，不加载大检查点，不运行仿真或训练。
3. 记录每条命令与结果、精确证据、局限，区分事实/推断/建议；遇读不到的证据标未核验。
4. 只更新本TASK状态、本RESULTS与独立日志，将拟登记来源发送父Agent；不得写共享PROGRESS/SOURCES。

独立日志：forem/doc/agent_logs/task7/task7.23/task7.23.2/20261023-codex-audit.md。

Codex推荐 GPT6.1sol / medium；Claude推荐 Sonnet5.5 / medium。跨文件因果与事实核验需要中等强度；实际派发 gpt-6.1-sol / medium，执行方收到后记录实际配置。依据[SRC-0960](../../../../SOURCES.md#src-0960)，推荐不等于运行事实。
