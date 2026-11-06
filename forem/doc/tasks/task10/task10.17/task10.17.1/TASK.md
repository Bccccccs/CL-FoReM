# task10.17.1 · 正常batch8边界恢复

负责人Codex子Agent，状态review（CPU实现完成、真实A待父核验）。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，涉及恢复或跨run训练/评估合同；实际配置由执行者如实记录。可自主选模与先建档委派；所有子Agent共享父授权与预算，父统一GPU、启动和原件验收。

目标：实现混合存活/新回合状态序列化、原PID退出后精确恢复；保留旧恢复拒绝规则。API约定save_decision_boundary/load_decision_boundary；CPU夹具与版本/账本/哈希拒绝；不得修改runner/entry。

输入：根AGENTS、17三文档、16最终验收与既有源码。授权仅此范围；CPU测试允许，GPU/真实交互/更新/长训均由父启动。证据链接父[SRC-T10-042](../../../../SOURCES.md#src-t10-042)。
