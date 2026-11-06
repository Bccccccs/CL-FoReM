# task10.14.1 流程

递归规则：本节点无子任务；再委派前必须建立继承编号的TASK/PROCEDURE/RESULTS并登记独占写入、依赖、输入、验收；所有人共享父36/5400/0/90min预算。执行者可自主选平台模型/推理强度及委派，常规GPT6.1sol或Sonnet5.5，可Terra/Luna；本节点不得自行启动GPU/真实评估。

先读根AGENTS与父三文档，等父说明产物schema；独立实现复算（不能直接信summary），CPU夹具含缺失/重复/配对错/终止多触发。审查父入口，反馈缺陷；真实结束后读取原件重新复算并写本RESULTS，父最终审核。推荐GPT6.1sol/medium、Sonnet5.5/medium，理由是独立统计与因果核查。

2026-11-03父追加范围授权：独占 `forem/scripts/task10_validation_diagnostics.py` 及 `forem/src/task10/tests/test_validation_diagnostics.py`，纯CPU从同一原件复算slot12偏好、trained/initial共享状态前缀选择与logit变化、失败与路线进度及既有训练数值曲线；终态后输出run/independent-diagnostics.json，保持已冻结audit/validation文件不变，不增GPU或真实运行。

2026-11-03父批准审计schema修正：独占新增 `forem/scripts/task10_validation_audit_v2.py` 与 `forem/src/task10/tests/test_validation_audit_v2.py`，仅归一化raw map_ids的tuple/list容器类型，保持内容逐项精确核对；保留已冻结v1、首次误报结果与日志。修正后输出run/independent-audit-v2.json，无真实评估重跑。
