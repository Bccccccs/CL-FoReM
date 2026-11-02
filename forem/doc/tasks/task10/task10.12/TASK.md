# task10.12 · 首个真实 GPU 更新证据

负责人 Codex 子 Agent；状态 review（CPU取证实现已核验，真实GPU证据由父本轮试训产生，尚未执行）。用户授权和父统一预算见[父日志](../../../agent_logs/task10/20261102-codex-online-trial.md)、[SRC-T10-021](../../../SOURCES.md#src-t10-021)。本节点工程选择和CPU原件见[SRC-T10-022](../../../SOURCES.md#src-t10-022)。

目标是在父首次 `update_sequences` 两端，独立保存 `learner.model.head_a.actor`、`.q1`、`.q2` 的原始参数、梯度、原设备和主Adam逐参数状态，以及冻结B3的完整state、梯度、模式和requires_grad。输出CPU原始张量payload及可离线复算的JSON摘要；失败或未完成不得报告有效GPU更新。首更前完整learner/replay检查点由父独立保存。

独占新增 `forem/src/task10/training_evidence.py` 与 `tests/test_training_evidence.py`，本节点三文档及[独立日志](../../../agent_logs/task10/task10.12/20261102-codex-first-update-evidence.md)。不改 runner/learning.py或共享文档，不提交，不自行GPU、采集或恢复。父唯一连续1200真实/200更新/25200s、1000真实预热、故障不重启的授权不由子节点扩展；CPU每条命令≤120s，预检和训练共享父总预算。

验收：真实tiny UpperModel + Stage1Learner和合成回放CPU验证独立分组、参数/梯度/Adam、B3、异常分支、无RNG/状态副作用、持久化原件复算；CPU只能标verified_cpu。父复跑、真实CUDA更新及完整原始检查点另验，不能把本CPU夹具称真实预热或有效GPU训练。

推荐 Codex GPT6.1sol/high 与 Claude Sonnet5.5/high；理由是独立头、梯度、参数更新与设备的跨模块因果核查。实际派发 gpt-6.1-sol/high。执行者可范围内自主选平台模型/强度、独立完成或先建档后委派，共享父授权/预算/截止；本节点独立完成，未再委派。
