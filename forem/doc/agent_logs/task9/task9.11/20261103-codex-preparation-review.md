# task9.11 准备交付审核

开始登记：2026-11-03T21:21:32.222102+08:00。负责人Codex，实际模型/强度未知；推荐GPT6.1sol/high、Sonnet5.5/high，因进程竞争与成本合同审查。本轮未委派。用户“审核”，只读实现/日志核查，写审核记录、来源、进度及父结果，不改实现、不加载模型、不运行测试/环境/训练。

已读PROGRESS最新状态、.5三文档、.6独立结果/正式裁决、父RESULTS §9、supervise.py与admission.py关键准入/预算路径。保留所有dirty。进程匹配仅本次查询，无匹配task9.11 worker/监督/替身进程；不据此代替历史退出证明。

## 裁决：修复尚不完整，真实执行仍NOT_READY

1. **P1：worker启动之前存在watcher死亡检查空窗。** `supervise.py:167–175`在backend.resources之前检查terminal/owner，但不检查watcher存活；resources返回后直接Popen。若watcher已经写ready后在resources期间被SIGKILL，terminal可能不存在，owner仍活，资源检查也可成功，随后worker会被启动。仅在启动后的poll循环里才发现watcher死亡并停止；快速退出的客户端甚至跳过该循环。这违反“watcher有效监控后才允许启动”的门。此为静态控制流反例，不声称本次真实发生/已运行复现。修复需在资源检查后、实际launch前重核watcher身份/存活、owner、terminal与剩余时间，并设计启动握手使已观察到失效时不能launch；不能宣称普通二次检查能消除一切并发故障。新增零环境回归应让resources内杀死watcher后返回成功，断言worker启动标记从未创建，覆盖ready后死亡/超时与terminal已发布的情况。当前30+7 PASS不替代这个断言。

2. **P1，既有未完成项：完整退出/成本合同未闭合。** watch生成receipt时owner/guard仍活，wall截止发布前；owner_exit_code/owner_full_wall_s/container_worker_exit_code明确UNKNOWN。admission.activity_rows接受此阶段PASS，check_resources把wall_s作为closed成本求和。现阶段不能据此满足原“完整训练墙钟含监督发布退出尾”要求。独立审查已披露这个限制，非发现其隐瞒；应补独立最外层生命周期收据和不重不漏成本映射，或提交明确的合同修订评审，不能把阶段PASS直接升级为整机完整退出PASS。当前prepare禁用和旧STOP保持阻断。

3. **执行依赖：合法续接/预算仍未解决。** prepare显式NOT_READY，原run/protocol/旧started与新SHA不兼容；smoke4000已满，剩10788评估已分配给L ON196、正式9408、test1184，无额外C ON。旧C原件仅支持科学非干扰，不能把旧完整性FAIL改PASS。恢复方案必须明确旧科学证据复用边界、新G1/准入、累计旧账及原截止；历史未知成本不能当0。该项沿已有.6/父§9，不另要求重复已完成合成测试。

## 已核验与范围

直接核独立裁决13项引用SHA一致，读取最终30项和额外7项原stderr/rc记录，当前3个改动文件SHA与交付一致（见preparation-review-evidence.json）；未重新执行合成测试，不把本次审核称37项新测试。未改科学变量、原模型/评估数据或STOP；既有合成结果仍有效于其覆盖范围。

下一步：只修上述启动门并补独立合成反例，同时完成完整生命周期/续接合同交接，再审是否具备真实执行条件。当前不派发真实实验，不扩大预算，不将执行阻断判B1-L科学阴性。来源SRC-1402。
