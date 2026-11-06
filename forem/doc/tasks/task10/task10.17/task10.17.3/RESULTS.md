# task10.17.3 结果

**review：CPU实现与专项通过，待父复核；实际C尚未执行。** 负责人Codex子Agent，实际模型/强度未知。推荐GPT6.1sol/high、Sonnet5.5/high，涉及显式检查点合同、跨run初态及预算；可自主选模与先建档委派，本次独立完成，父统一GPU/预算与原件验收。授权依据[SRC-T10-042](../../../../SOURCES.md#src-t10-042)，新增CPU证据交父统一登记。

新增且仅新增：forem/scripts/task10_long_validation.py、forem/scripts/tests/test_task10_long_validation.py。没有修改旧脚本/src、没有GPU/真实env/更新/freeze/训练或评估。

CPU专项最终 **26 passed/1.57s/rc0**；覆盖新schema/2k5k10k真实计数、replay/ledger/index内容hash、9000 scheduler、原48h预算、KL温度、stopped_boundary/resume终态、初态dtype差异执行前拒绝、12固定分母/缺失、同epoch/全球截止shell上限/一次启动拒重、真实独立decision及3参snapshot checker集成及观测篡改检测。部分模型/子进程以fixture/mock替代，不能当实际GPU入口验收。旧参照只读CPU核验 **200 legacy文件+52 KL文件、12配对初态、模型一致/rc0**。宿主CLI help、py_compile与diff检查均rc0。

原件：forem/logs/task10/task10.17.3/cpu-tests-v6.txt、reference-input-check.txt；历史v1–v5 CPU迭代日志保留。完整命令、SHA及限制见[独立日志](../../../../agent_logs/task10/task10.17/task10.17.3/20261103-codex-long-validation.md)。

交付CLI及产物详见[PROCEDURE](PROCEDURE.md)。需父在A/B通过并且B唯一run结束后才执行C；子自报不替代父原件复核。学习曲线/原地复发/三检查点真实成绩均尚无本节点新证据，不能引用16旧结果当17结果。无本子遗留进程。

2026-11-03T23:30:28.721796+08:00 父停点：A恢复通过但成本门NOT_READY，按原流程交回。保留本子CPU实现，未启动正式训练/评估，未获GPU端到端执行验收，不写done。[父结果](../RESULTS.md)。
