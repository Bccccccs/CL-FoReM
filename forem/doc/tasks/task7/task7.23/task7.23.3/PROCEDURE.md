# task7.23.3 — 审核流程

递归规则：每层任务恰有TASK、PROCEDURE、RESULTS三文档；如需进一步拆分须先由父Agent建立子任务三文档并登记，当前不新增子任务。

1. 阅读授权、AGENTS及指定输入，记录实际模型与强度。
2. 只读核查GPU/容器/训练与看门狗进程及配置，审查C″ bootstrap、IK避碰、STOP/恢复代码与上层正式训练依赖；不启动测试/仿真，不停止任何进程，不修改代码。
3. 记录每条命令与结果、精确证据、局限，区分事实/推断/建议；遇读不到的证据标未核验。
4. 只更新本TASK状态、本RESULTS与独立日志，将拟登记来源发送父Agent；不得写共享PROGRESS/SOURCES。

独立日志：forem/doc/agent_logs/task7/task7.23/task7.23.3/20261023-codex-audit.md。

Codex推荐 GPT6.1sol / medium；Claude推荐 Sonnet5.5 / medium。跨文件因果与事实核验需要中等强度；实际派发 gpt-6.1-sol / medium，执行方收到后记录实际配置。依据[SRC-0960](../../../../SOURCES.md#src-0960)，推荐不等于运行事实。

追加范围（父Agent协调消息）：静态审查正式D10多worker driver/claim隔离、协议覆盖及中断恢复；不运行该driver或分析脚本，不改运行任务。现场取样使用date、nvidia-smi、ps、sg docker只读命令和Python标准库读取JSON/计算SHA256；没有调用训练模块或CUDA计算。
