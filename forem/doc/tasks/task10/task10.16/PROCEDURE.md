# task10.16 流程
递归规则：各子任务继承编号并具三文档，父汇总原件。先数学独立复核task10.16.1，再裁定并实现最小可验证变更；训练/真实评估另列预算。子1负责人Terra/high、独占子文档日志，只读检查源码/证据，无GPU/更新。
[子TASK](task10.16.1/TASK.md) · [子PROCEDURE](task10.16.1/PROCEDURE.md) · [子RESULTS](task10.16.1/RESULTS.md)。
推荐GPT6.1sol/high、Sonnet5.5/high。父子可自主选模，先建档后委派，共享父预算。

数学复审后执行task10.16.2目标实现，sol/high，独占learning/entry/runner与专属测试；父独立复核。[TASK](task10.16.2/TASK.md) · [PROCEDURE](task10.16.2/PROCEDURE.md) · [RESULTS](task10.16.2/RESULTS.md)。

## 用户批准的新目标试训与评估
2026-11-03用户批准一次1200真实/200更新/7h从头试训，随后同12验证场景新最终策略单组评估≤90min。沿原seed101/B3seed4718/batch8/1000预热，学习率总更新200，使用relative_uniform_trial.json固定alpha .35。该轮是匹配旧规模的目标修正试验，不作为充分训练结论。训练与评估各自原epoch硬截止、单run不重启，0test池。评估只运行新trained的12回合，逐初态对旧manifest配对，旧initial/uniform结果在哈希/初态一致时复用，真实评估上限12×150=1800决策。新旧权重与目标版本全部列明。终点检查原地比例、原地logit领先、严格成功、失败/停滞；即使仍失败也保留结果。采集恢复继续未验。依据SRC-T10-036，父唯一启动并监控至结束，子Agent共享资源。

16.3实现只执行新trained的12场景入口，父训练结束后顺序启动；执行者sol/high只写新scripts/专属tests，不修改运行源码。[TASK](task10.16.3/TASK.md) · [PROCEDURE](task10.16.3/PROCEDURE.md) · [RESULTS](task10.16.3/RESULTS.md)。
