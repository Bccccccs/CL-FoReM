# task10.2 · SAC 奖励、Bellman 与短回合回放

负责人：Codex子Agent `learning_contract`，active；开始 2026-11-02T15:12:30.870185+08:00。

按父协议实现严格成功势函数奖励、独立bootstrap mask、可覆盖短回合/首段的回放和序列学习适配；确定性测试终局、零提交尝试时间、单有效槽、跨回合及padding、恢复RNG/更新。

独占写入：forem/src/task10/learning.py、forem/src/task10/tests/test_learning.py，本节点三文档及独立日志；父共享文件禁止写。输入：[父PROCEDURE](../PROCEDURE.md)、[根AGENTS](../../../../../AGENTS.md)、task7/8现有源码、只读主仓产物。
交付：实现、确定性测试、源码证据、命令/退出码/未通过项；父复跑后验收。预算：只做确定性小夹具，不启动训练、配对或新采集。

推荐 GPT6.1sol/high、Sonnet5.5/high；理由：终局折扣及回放边界需严谨因果核对。实际派发 gpt-6.1-sol/high。 依据：[SRC-T10-001](../../../SOURCES.md#src-t10-001)、[授权](../../../SOURCES.md#src-t10-002)。

2026-11-02 15:20 +08:00：实现和确定性核验完成，状态 **review**，等待父 Agent 独立复跑与集成验收。实际接口、命令、限制及来源草稿见 [RESULTS](RESULTS.md)。未启动环境采集、冒烟训练或配对评估。
