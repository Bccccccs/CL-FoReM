# task10.1 · 冻结 B3 观测、动作与推演输入核验

负责人：Codex子Agent `b3_contract`，review（实现与14项确定性测试完成，待父复跑）；开始 2026-11-02T15:12:30.870185+08:00。

读取冻结原始产物、格式/哈希核验，实现可复用冻结B3加载器。对比原版task8_lower SAC确定性推理；审计观测、动作、推演需继承的Core状态；不改共享Core与原版模块。

独占写入：forem/src/task10/lower.py、forem/src/task10/tests/test_lower.py，本节点三文档及独立日志；父共享文件禁止写。输入：[父PROCEDURE](../PROCEDURE.md)、[根AGENTS](../../../../../AGENTS.md)、task7/8现有源码、只读主仓产物。
交付：实现、确定性测试、源码证据、命令/退出码/未通过项；父复跑后验收。预算：只做确定性小夹具，不启动训练、配对或新采集。

推荐 GPT6.1sol/medium、Sonnet5.5/medium；理由：接口适配核对。实际派发 gpt-6.1-sol/medium。 依据：[SRC-T10-001](../../../SOURCES.md#src-t10-001)、[授权](../../../SOURCES.md#src-t10-002)。

2026-11-02父签收：本节点确定性实现/审查交付done，父复跑及实际试训/配对限制见[父RESULTS](../RESULTS.md)。不代表父C有效训练或D就绪。推荐GPT6.1sol/medium、Sonnet5.5同档，实际子Agent配置保留上述历史记录。
