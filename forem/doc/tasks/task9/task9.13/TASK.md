# task9.13 完整Ray RLlib SAC在FoReM下层的对照

状态active（完整RLlib已实现、必要验证通过，正式队列部署）；负责人Codex子Agent `/root/rllib_task9_13`。用户2026-11-06已明确确认“是，测试完整Ray RLlib SAC”。本次授权框架适配、必要验证及合理训练对照；不是只把alpha_rule改成rllib，也不以旧CBL任务结果替代本环境测试。目标：判断在相同FoReM任务和训练预算下，完整RLlib SAC的严格成功、稳定性与端到端效率是否优于现有自写SAC。

主对照两臂：现役C/B1自写SAC配置与RLlib SAC（原生learner/optimizer/target/replay训练链必须实际执行），均固定原解析IK+DLS，不引入BioIK。同网络容量/编码器、任务语义与学习预算；因框架内部实现可能不同，唯一实验因素称“训练实现栈”，不可宣称只是替换一个参数或证明SAC算法优劣。差异表是验收交付，无法对齐处必须显式标注。两种子从头训练，各臂每种子3M有效消费转移，250k profile计入3M；默认不做大范围调参或联合BioIK。

交付：冻结版本与差异表、适配/更新/恢复核查、同期两臂训练和学习曲线、逐种子随机/语义严格成功及成本对照、支持/停止结论。历史9.11 C结果只作外部锚点；若不能运行同期控制，不可将历史差值作为新的因果结论。

[SRC-T9-EXPLORE-20261106](../../../SOURCES.md#src-t9-explore-20261106)。

推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high：涉及求解器/训练框架语义、因果对照与恢复一致性。实际执行者、平台模型及强度由接手者实记；实际执行者Codex `/root/rllib_task9_13`，gpt-6.1-sol/high；历史规划状态保留在过程日志。

2026-11-06T09:39:41+08:00 · active · 执行负责人Codex子Agent `/root/rllib_task9_13`；实际派发请求模型GPT6.1sol（平台gpt-6.1-sol）、high，派发工具确认后父日志补记。独占写入本任务PROCEDURE白名单（含本三文档与独立日志），共享SOURCES/PROGRESS/DECISIONS及父三文档由父管理，不并发写；task9_lr现役冻结源只读。输入/交付/验收沿本三文档与用户本轮明确执行指令；候选GPU `GPU-656ca5c1-681f-48a2-7d1f-a00824723f68`，启动前复核。独立日志：[20261106-codex-execution.md](../../../agent_logs/task9/task9.13/20261106-codex-execution.md)。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨接口语义与恢复核查需high。此前未执行描述为历史，当前授权已实际派发执行。

2026-11-06 用户执行中澄清：每个训练种子分别沿用同一现有100随机＋96语义开发回合；3M终点也为196，取消原588终点评估。正式总评估4×12×196=9408回合（工程推导），每run为12×E196；不将多策略汇总300/288误当单策略全集，不读取9.11保留测试。父将同步授权来源。
