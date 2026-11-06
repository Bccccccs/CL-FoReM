# 2026-10-31 Codex — B0/B1/B2/B3/T已有对照归因

- 任务ID TASK9.4-CAUSAL-ASSESS-20261031；开始2026-10-31T08:42:57+08:00；状态active；负责人Codex。
- 用户要求：“所以能否确定到底是什么有问题”。范围仅解释与核查已有实验/代码证据，不改生产代码、配置、奖励/终止等科学语义，不新增训练、探针或实验；不启停既有运行。
- 已读task9.3 S3及parent-errata、9.2 RESULTS、前轮9.4 snapshot/RESULTS、实际SAC更新和LR/target代码、相关配置；沿用根/forem AGENTS、README/ENV和既有交接，本轮复读PROGRESS/SOURCES末尾及git状态。
- 模型推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high，理由为区分受控配置效应与更新/温度/target/LR耦合机制；实际本会话模型/强度未知，未切换或委派Agent。
- 关键静态核查：B0模板→B1-4718只差group与update_every_transfers 1→10；B2-4718→B3模板同样只差这两项。命令标准库JSON全字段差异比较rc0，另读取sac.py与training.py更新调用链。
- 尚未执行：任何机制解耦新实验/诊断探针。结论整理后登记全局来源与9.4 RESULTS。

## 分析完成

- 用户续问“分别讲明每个任务的配置姗姗嘛”，按各训练组配置解释，与归因问题一起完成。
- 实际读取/核查：S3、parent-errata、9.2 RESULTS、task7/8 SAC及training更新链、B0/B1/B2/B3/T/H/5M配置；JSON逐字段差异比较与两组断言通过，命令rc0；没有新增训练/梯度探针。
- 证据：`forem/logs/task9/t9-stage2-20261029/causal-assessment-20261031/config-comparison.json`；全局[SRC-1330](../../../SOURCES.md#src-1330)；[9.4 RESULTS](../../../tasks/task9/task9.4/RESULTS.md)新增配置表与归因边界。
- 结果：2×2支持高更新比及关联训练节奏为主要配置问题，不能单独归因到critic/alpha/target/LR某一机制。B2/T失败削弱“只改温度就足够”的解释；H仍在运行，不能提前得结论。
- 本轮写入本日志/PROGRESS/SOURCES/9.4 RESULTS及配置证据JSON；未改生产配置/代码、未启停运行、未派Agent。
- 状态done（仅本轮分析）；剩余长期训练与最终独立验收沿既有交接。任何机制解耦新实验均尚未执行、需另获用户授权，本轮不加入执行范围。

## 2026-10-31T20:45:38+08:00 3M/5M训练效果比较（TASK9.4-3M5M-COMPARE-20261031，done）

- 用户补充“训练效果”，承接“5M和3”；只读已有同种子结果，未新增实验/启停训练/改配置。已复读进度与来源、读取原始评估/summary，标准库逐回合重算4个已完成B3 run末三原件，差值计算断言通过，命令rc0。
- [SRC-1333](../../../SOURCES.md#src-1333)与[9.4 RESULTS](../../../tasks/task9/task9.4/RESULTS.md)登记；原件`forem/logs/task9/t9-stage2-20261029/compare-3m-5m-20261031/comparison.json`。写本日志/PROGRESS/SOURCES/9.4 RESULTS及比较JSON，保留原记录。
- 同种子4718最终验证63%→67%，末三56.33%→62%，迁移45/96→49/96，wall9.49h→15.84h；仅一个5M完成，不能认定稳定提升。原预算日程不同，不能当原3M续训；H/其它5M进度沿SRC-1332，未重复做全现场审计。
- 推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（比较数据和预算日程口径）；实际模型/强度未知。剩余为既有5M run结束及独立验收，不新增任务。
