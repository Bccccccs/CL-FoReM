# task9.8.4 轨迹完整性修复

状态 review（本子实现及合成验证完成，待父从原件核验）。目标为修复 B 轨迹覆盖和独立判分；授权仅 `forem/scripts/task9_8/analysis.py`、`test_analysis.py`、本层三文档与独立日志，不运行模型、环境、GPU 或 evaluate，不写父共享文档。冻结判分依据[父 PROCEDURE](../PROCEDURE.md#b-final)及[SRC-1370](../../../../SOURCES.md#src-1370)，缺失轨迹误判问题见[SRC-1372](../../../../SOURCES.md#src-1372)。

交付 `coverage(events,row)` 和 `score(events,row)`；`row` 必须来自独立的本轮原 evaluate 输出，不能由 trace.final 回填。原行 transfers 限定全局动作数，原 Transition.attempted/committed 限定子步覆盖。缺项、重复、乱序、非有限或身份/终态不一致均保留错误并判 U。OFF/ON 相同不构成完整性证据，父须先分别覆盖验证，再 exact compare。

验收包括正 transfers 仅 reset/final、双方同缺子步、重复子步、完整无拒绝、首次拒绝后同段平移/原地恢复、仅新段进展、阈值/route_end、身份/动作计数/非有限、真实零动作及 trailing begin 终止边界的合成回归。正式回放与 C 独立核验属于父范围，本子结果不代替其通过。

负责人 Codex 子 Agent；实际模型/强度未知（未独立核验），派发请求 gpt-6.1-sol/high。推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high；理由为需要核对原评估、事件时序和回滚/终态因果关系。推荐不代表实际执行配置。
