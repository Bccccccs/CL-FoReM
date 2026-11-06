# task9.11.18.2 shard修复增量独审

负责人Codex / delta_review；状态active（已发现定点修复项，未签PASS）。实际模型由父派发标注GPT6.1sol，具体平台model ID与继承强度未独立暴露；推荐GPT6.1sol/high、Sonnet5.5/high，原因是准备重入、跨进程证据及费用一致性。依据[本轮来源](../../../../../SOURCES.md#src-1462)。

授权仅审核两个外部脚本及两个新控制测试；不加载模型，不启动仿真、Docker或训练；仅写本节点证据及三文档。父维护共享PROGRESS/SOURCES。新旧科学协议、历史FAIL与成本及3M C4718证书复用不重复审。

实际12项控制测试退出0；独立copy/save故障注入发现prepare_zero_retry不可重入，save失败还会先清STOP。复现原件见[故障证据](shard-repair-v2/prepare-reentry-original-failure.json)、[定点发现](shard-repair-v2/incremental-findings-v1.json)。已报告父；父修复后仅核准备提交边界及受影响定向测试，不重跑全资产/全局预算。尚未对真实run执行准备，不声称零步模型恢复或科学验收通过。


本轮完成：状态done（控制增量审核）；15项当前测试rc0，独立copy/save失败注入后STOP保留且重入成功，成功重复准备不重复成本，新同内容STOP按身份拒删。60000s失败费超额拒绝，18.7s失败费与证据保留。两具体发现及修复原件均保留于shard-repair-v2，最终[增量结论](shard-repair-v2/delta-verdict-v2.json)、[授权v2](shard-repair-v2/authorization-v2.json)。父已收到授权SHA与两脚本冻结SHA。实际prepare/原生恢复/训练尚未执行；按父转达当前用户要求仅交付，不启动。共享来源/进度由父补新增事实。本节点原科学最终验收职责不变。
