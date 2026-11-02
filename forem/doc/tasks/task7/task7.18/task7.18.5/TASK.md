# task7.18.5 — v4中期D10式诊断（非正式冻结验收）

状态：**review（2026-10-22 19:10；诊断已执行，见[RESULTS](RESULTS.md)；执行方Claude子Agent Sonnet5.5）**。父任务：[task7.18](../TASK.md)。

## 目标

用task7.19的G7评估与D10配对工具，在v4训练1M步检查点上做有界诊断：随机规则候选中G7判可行的比例、在G7可行候选上下层（确定性）到达率与失败分类、同组候选G7执行器失败率；判断v4到达率低是候选多不可行还是策略能力不足。**不是正式D10，不作冻结决定。**

## 范围与约束

- 输入：`forem/results/task7/t7.18-v4-20261022/formal-v4-{sync,async}/checkpoint-1000000.actor.pt`；验证地图（d10_protocol.json中的地图与种子，可只用前一部分回合，写明子集）；G7实现`forem/src/task7_sim/g7.py`、`d10_eval.py`。
- 不训练、不改源码语义（可在logs下写驱动脚本）；不停止v4训练（GPU2/3）。GPU0（sync）、GPU1（async）；单条前台≤10分钟，长任务后台；总计≤150分钟容器计算。
- 产物`forem/results/task7/t7.18.5-diag-20261022/`；日志本目录agent_logs；SOURCES预留SRC-0930–0934。

## 模型推荐

|Agent|模型|推理强度|理由|
|---|---|---|---|
|Claude子Agent|Sonnet5.5|medium|调用既有工具做有界评估|
|Codex（备选）|GPT6.1sol|medium|同上|

文档作者：Claude（claude-opus-5-5，推理强度未知），2026-10-22。
