# task10.7 · 成本与恢复独立审查

负责人audit_cost_recovery，active。只读src/task10/profiling.py、recovery.py、runner.restore_evidence、scripts/task10_{cost,recovery}_probe.py和measurement manager、既有/新增证据。仅写本节点三文档和独立日志，不改源码/共享docs、不提交、不执行新采集/更新。验收是否确有分项/全量计数、同输入对照、非空抽样/更新后optimizer、在线采集边界无重复；核查样本限制与预算估计。执行者可按难度选模/强度并独立或委派，先建档，所有代理共父1800s测量预算/截止；本节点仅只读审查，小CPU读证据由父复核reserve覆盖。

推荐GPT6.1sol/high、Sonnet5.5/high，因测量口径、恢复时钟与无重复计数跨模块；实际派发gpt-6.1-terra/high（独立复核，与上轮sol容量替代一致）。

父收尾：状态done（独立审查交付），无运行工作。父核验与具体已通过/未通过范围见[父RESULTS](../RESULTS.md)，不把CPU夹具或诊断rc0当线上总通过。
