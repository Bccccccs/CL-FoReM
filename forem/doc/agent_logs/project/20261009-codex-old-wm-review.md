# PROJECT-OLD-WM-REVIEW-20261009

用户问最早伤害SAC/WM对照、训练安排、后面是否换Transformer。只读backup/旧results及当前4.9，未恢复旧任务/源码或停止新训练。原始产物确认强失配.70→.33、L3模型补偿三臂均.70；无旧任务提升证据。来源[SRC-0192](../../SOURCES.md#src-0192)，副本/hash在results/project/old-wm-check-20261009。

建议先验证当前单步数据/时序/动作信息，不自动更换Transformer；若需要历史建模提出新方案再获同意。当前10万checkpoint→MLP离线→冻结反馈→公平对照保持。旧ph4-smoke报告不是正式ph4结果，最初读取后已用backup真实ph4-1报告核对，不将smoke的0分或300步当正式结果。

Codex /root实际未知，推荐GPT6.1sol/Sonnet5.5 medium（历史与新协议边界）。状态done（只读审查/建议），未运行旧实验或添加新实验。
