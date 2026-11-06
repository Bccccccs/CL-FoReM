# task9.8.4 执行流程

递归规则：本层恰有 TASK、PROCEDURE、RESULTS 三文档；若拆分，须先建立下层三文档并登记顺序、依赖、负责人及验收关系。本次不继续委派。输入为根 AGENTS、父 B 冻结协议、B-review、原 `task7_sim/core.py` 与 `task8_lower/evaluation.py`（只读）。父独写共享来源和结果。

1. 先写标准库合成测试，使用独立原行和完整事件，不加载 torch；运行 `python3 -m unittest discover -s forem/scripts/task9_8 -p test_analysis.py -v` 确认旧实现的缺失轨迹误判。
2. 实现 `coverage(events,row)`，返回 `complete: bool`、`errors: list[str]`、`counts: dict`。接受 OFF 原事件或 ON comparison 包装；所有记录（含 detail）与原行均检查有限值。核查唯一首 reset/末 final、完整身份、批次槽位、连续 segment/action/substep、必需字段与类型、提交状态链、attempted/committed 与动作数。
3. `begin` 不改变 committed state；其原始 done/terminated/truncated/strict_success/failures 为必需字段。零长度 begin 可直接 `_finish`，最后终态从最新 begin/action_end 快照与独立原行核对；零 transfers 也必须有 terminal begin。缺少终态快照判 U。原 raw_action 为三维，execution_action 亦三维；一项成功子步若没有 done，不足以覆盖原两次循环。
4. `score(events,row)` 首先 coverage；不完整立即 U 并附 missing_reasons 与 coverage。完整时按[冻结规则](../PROCEDURE.md#b-final)定位最早 pending & failed，以拒绝后的 committed state 为基准，只认同段严格大于 1e-6 m 的后续 commit 进展或明确 arrived；route_end 不替代 arrived。无拒绝、恢复、可判未恢复分别为 no_rejection/R/N。
5. 运行同一合成命令，检查输出/rc；父重新读实现并复跑后才可接正式回放。不得以合成通过宣称真实记录完整、恢复率有效或 C 通过。

源码/规则依据：[SRC-1370](../../../../SOURCES.md#src-1370)、[SRC-1372](../../../../SOURCES.md#src-1372)。证据与命令见[RESULTS](RESULTS.md)及[独立日志](../../../../agent_logs/task9/task9.8/task9.8.4/20261102-codex-coverage-fix.md)。负责人 Codex；实际模型/强度未知，请求 gpt-6.1-sol/high。推荐 Codex GPT6.1sol/high 或 Claude Sonnet5.5/high，理由为跨模块轨迹合同核对。

段边界补充：reset 隐含未开始目标段；begin 仅允许上一段 done，action_start 仅允许当前段未 done；原子步 done=True 必须在 action_end 保留。action_end 在原循环后因失败阈值/_finish 变为 done 可以合法接受，不强制反向相等或 reason 相等。对应三项合成回归已红绿验证，见 RESULTS。
