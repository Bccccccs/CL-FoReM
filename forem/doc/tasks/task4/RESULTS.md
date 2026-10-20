# Task4 — 结果汇总（已关闭）

状态：**closed（2026-10-16）**。以下只汇总保留子节点已记录的事实，细节以子RESULTS为准；均未经独立复核。

|项|结果|出处|
|---|---|---|
|Gazebo普通SAC（t4s-plain-s0/1/2，100万步）|最终验证内部成功0/15；约91%回合因20次IK失败终止，训练全程无学习趋势|[task4.8 RESULTS](task4.8/RESULTS.md) · [SRC-0228](../../SOURCES.md#src-0228)|
|反馈臂（t4s-fb-s0/1/2）|fb-s1/s2到100万步、fb-s0到约90万步，最后验证物理成功均为0/5|[task5计划日志](../../agent_logs/task5/20261011-claude-task5-plan.md)|
|WM（10万步分叉点）|预登记256维表征：skill 2.8–4.1%，动作打乱误差增幅≤0.11%（负结果）；41维robot_state：skill +15.4%，多维显著依赖动作|[task4.9 RESULTS](task4.9/RESULTS.md)|
|内部与物理成功差异|先导117回合内部成功1/3/5、物理成功0/0/1；不能以规划到达替代物理成功|[task4.8 RESULTS §3](task4.8/RESULTS.md)|

产物数据清理（2026-10-11）：`forem/results/task4`、`forem/logs/task4`仅保留6条正式训练的摘要、验证、权重与日志及t4.9 WM权重，[SRC-0202](../../SOURCES.md#src-0202)。

结论：在Gazebo中直接训练cbl自写SAC学不会，首次WM尝试没有产生可信前瞻信息，也没有任务收益。失败原因的诊断见[task6](../task6/RESULTS.md)。

交接：无运行任务，无下一步；阶段二见[task7](../task7/TASK.md)。
