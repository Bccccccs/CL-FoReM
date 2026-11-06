# task10.17.2 · 唯一10k训练入口与持久监督

负责人Codex子Agent，状态active。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，涉及恢复或跨run训练/评估合同；实际配置由执行者如实记录。可自主选模与先建档委派；所有子Agent共享父授权与预算，父统一GPU、启动和原件验收。

目标：新增显式10k profile；独立训练模块/launcher，复用原语，接17.1 API；正常batch8每256及2000/5000/10000一致检查点，UTD/9000 scheduler、48h原epoch账本；不修改原runner/learning/recovery。

输入：根AGENTS、17三文档、16最终验收与既有源码。授权仅此范围；CPU测试允许，GPU/真实交互/更新/长训均由父启动。证据链接父[SRC-T10-042](../../../../SOURCES.md#src-t10-042)。
