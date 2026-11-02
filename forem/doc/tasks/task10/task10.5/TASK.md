# task10.5 · 采集成本分解与同输入核验

负责人Codex `cost_profile`，active，开始2026-11-02T16:11:50.649490+08:00。
复用旧16回放及scene seeds，分项测reset/candidate/B3/IK/collision/grid，补全所有边界slot/attempt/commit计数。只增加可关闭的上下文wrapper，不修改冻结69文件。先不优化；比较uninstrumented与instrumented相同轨迹候选/mask/features/actual/failure。父统一启动测量。
独占：forem/src/task10/profiling.py、forem/scripts/task10_cost_probe.py、forem/src/task10/tests/test_profiling.py，本节点三文档及独立日志；不改其他共享文件、不提交。输入：根AGENTS和本轮用户规则、父三文档、63e1f6e审核、旧run t10-smoke-20261102-s101。交付代码/确定性tests/测量入口及声明预算，父启动GPU测量并复跑验收。所有子Agent共享父总范围、1800s测量账本/截止条件。
执行者获准按难度选择可用模型和强度、独立完成或委派，无需另问；再委派前建三文档、独占文件与依赖验收，不能另设预算。

推荐GPT6.1sol/high、Sonnet5.5/high；跨模块计时/恢复一致性需高强度。实际派发gpt-6.1-terra/high。选择Terra因上轮sol容量中断，适合本次跨层计时核对。 方法沿父[SRC-T10-001](../../../SOURCES.md#src-t10-001)、审核[SRC-T10-010](../../../SOURCES.md#src-t10-010)；新授权/依据由父统一登记。
