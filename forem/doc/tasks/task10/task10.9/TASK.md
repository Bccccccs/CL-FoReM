# task10.9 · 正常入口batch8采集恢复核验

负责人Codex子Agent；状态review（CPU交付完成，父真实采集/统一验收待定）。目标：审查安全边界并用真实`runner.train`的CPU batch8确定性夹具验证父接线、自然边界及跨进程不重计。用户本轮授权仅GPU下一更新与正常batch8恢复两问题，冻结B3 seed4718/上层seed101/正常batch8与既定科学语义；不启动预热、长训或task11。[父日志](../../../agent_logs/task10/20261102-codex-gpu-batch8.md) · [复核](../../../SOURCES.md#src-t10-015) · [本轮证据](../../../SOURCES.md#src-t10-018)。

交付：`recovery.py`安全审查及最小修复、恢复单元夹具、新`test_runner_boundary.py`。父独占`runner.py`/正常入口/真实运行及共享文档。本节点不采集、不GPU更新、不提交。验收要求全批自然terminated/truncated、prepare_next已清pending、最后transition入replay且对应journal已fsync、账本无inflight；混合结束必须照常reset结束行，不能保留等待凑边界。新PID恢复原deadline/started、episode/decision IDs、采样器/策略及全局RNG、journal/回放/账本无漏重；旧账本只读。严格逐位口径不变。

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因跨模块边界、RNG及账本一致性核验需要；实际派发GPT6.1sol/high（平台内部不可独立核验），推荐不冒充实际核验。执行者可在父范围/总资源/截止内自主选可用模型/强度，独立完成或先建档再委派；本节点独立完成。
