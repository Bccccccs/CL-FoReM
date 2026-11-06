# task10.14.1 独立复算与入口审查

状态 active。负责人 Codex 子Agent，父task10.14执行者统一核验。输入：根AGENTS、forem/AGENTS、父三文档、评估入口、冻结清单及逐回合/逐决策/账本原件。目标是实现独立CPU审计，检查36唯一身份、配对、权重/计数和三策略分母/缺失/分难度/胜负平；审查加载/独立RNG/终止/超时持久化。没有真实运行/训练授权。

独占写 `forem/scripts/task10_validation_audit.py`、`forem/src/task10/tests/test_validation_audit.py`、本节点三文档和独立日志。禁止修改共享文档、父实现和训练产物。交付脚本、必要统计夹具和缺陷说明，父以原件复核。推荐GPT6.1sol/medium、Sonnet5.5/medium；跨模块统计与加载核验。实际以子Agent记录为准。

2026-11-03父追加范围授权：独占 `forem/scripts/task10_validation_diagnostics.py` 及 `forem/src/task10/tests/test_validation_diagnostics.py`，纯CPU从同一原件复算slot12偏好、trained/initial共享状态前缀选择与logit变化、失败与路线进度及既有训练数值曲线；终态后输出run/independent-diagnostics.json，保持已冻结audit/validation文件不变，不增GPU或真实运行。

2026-11-03父批准审计schema修正：独占新增 `forem/scripts/task10_validation_audit_v2.py` 与 `forem/src/task10/tests/test_validation_audit_v2.py`，仅归一化raw map_ids的tuple/list容器类型，保持内容逐项精确核对；保留已冻结v1、首次误报结果与日志。修正后输出run/independent-audit-v2.json，无真实评估重跑。
