# task10.6 · 非空抽样、更新后优化器与采集恢复边界

负责人Codex `recovery_check`，active，开始2026-11-02T16:11:50.649490+08:00。
修<32空列表误报；真实16可sample(min(32,len))非空身份核对，但正式训练仍32且1000预热不改。用真实回放派生明确标注GPU fixture更新后核对optimizer/下一更新；实现可重建可续跑边界及账本无重复的限定API，明确夹具与在线区分。不得改旧run。
独占：forem/src/task10/recovery.py、forem/src/task10/tests/test_recovery.py、forem/scripts/task10_recovery_probe.py；runner.py仅restore_evidence函数，本节点三文档及独立日志；不改其他共享文件、不提交。输入：根AGENTS和本轮用户规则、父三文档、63e1f6e审核、旧run t10-smoke-20261102-s101。交付代码/确定性tests/测量入口及声明预算，父启动GPU测量并复跑验收。所有子Agent共享父总范围、1800s测量账本/截止条件。
执行者获准按难度选择可用模型和强度、独立完成或委派，无需另问；再委派前建三文档、独占文件与依赖验收，不能另设预算。

推荐GPT6.1sol/high、Sonnet5.5/high；跨模块计时/恢复一致性需高强度。实际派发gpt-6.1-sol/high。沿用默认模型。 方法沿父[SRC-T10-001](../../../SOURCES.md#src-t10-001)、审核[SRC-T10-010](../../../SOURCES.md#src-t10-010)；新授权/依据由父统一登记。

本轮实现边界细化：仅支持全batch自然episode终局、prepare_next完成、最后transition与原始journal均落盘、ledger无in_flight，下一episode尚未采样的边界。不支持活动Core中途恢复；batch8同时终局未验。恢复限同Linux host boot、原monotonic deadline；重启系统、旧进程仍存活、ledger/journal变动、custom mutable sampling factory均拒绝；单一恢复持有flock。范围内实现与测试由当前执行者独立完成，未再委派。新增数值/方法证据由父统一登记SOURCES（下述RESULTS提供草稿；未登记前不作全局已验收结论）。

父后续要求在线证据跨真实进程；同预算内save/exit→newPID resume入口已交父，CPU真跨进程通过。samePID例外仅显式test_only合成fixture。恢复来源预留[SRC-T10-013](../../../SOURCES.md#src-t10-013)，父实测后登记。

父收尾：状态review，无运行工作。父核验与具体已通过/未通过范围见[父RESULTS](../RESULTS.md)，不把CPU夹具或诊断rc0当线上总通过。
