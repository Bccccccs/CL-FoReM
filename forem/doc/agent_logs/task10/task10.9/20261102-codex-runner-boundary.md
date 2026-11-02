# Task10.9 正常train边界恢复夹具

负责人Codex；状态active；2026-11-02接父派发，工作树codex/task10-upper-wm、初始ca57b4b。实际模型/强度按父派发GPT6.1sol/high（平台内部不可独立核验）。推荐GPT6.1sol/high、Sonnet5.5/high，需核对跨模块边界、RNG及预算一致性。

授权仅审查recovery.py、现有恢复测试，新增真实runner.train的CPU batch8确定性夹具；独占这些文件、本节点三文档与本日志，不改父runner/共享文档、不采集、不GPU更新、不提交。父统筹全1800s绝对测量窗口、真实64选择/0更新与GPU串行。来源：[SRC-T10-015](../../../SOURCES.md#src-t10-015)、[父日志](../20261102-codex-gpu-batch8.md)。执行者可在父范围/总预算内自主选模/强度、独立完成或先建档再委派；本节点自行完成。

已读AGENTS、ENV、README/PROGRESS、task10与task10.9三文档、复核和父日志。已检查分支/改动/进程，父和10.8的独占文件不覆盖。应用TDD与verification-before-completion技能：先记录失败，再最小实现、实际执行后结论。

接口协调：父选择args.resume、stop_at_boundary、boundary_reference、max_decisions/max_updates/seconds；仅全批自然结束且prepare/replay/update完成后保存，mixed ended照常reset。建议仅stop_at_boundary保存，保存退出finally不得flush已固化账本。CPU夹具保留真实Budget/EpisodeReplay/atomic保存恢复，通过monkeypatch环境/B3/model设备/timers/initialize构造batch8 synthetic自然终局，调用真实train。

2026-11-02阶段交付：7个安全测试先RED（7 failed/3.48s），再修复journal显式fsync、重复身份、六字段及live core终局一致性。25 CPU最终测试passed/17.98s/rc0，日志forem/logs/task10/task10.9-final.log、JUnit同名xml；原始synthetic保存/恢复/journal/账本位于results/task10/t10-gpu-batch8-20261102/cpu-boundary-fixture。真实runner自然mixed4→reset4→all8 save、不同PID恢复24唯一身份、连续参照与恢复start/end逐位verified，原started/deadline exact。ca57b4b临时模块旧runner RED缺collector-boundary.pt，1failed/2.60s（真实Budget容量注入24仅为避免1000预热，未替换共享runner）。

父已分配[SRC-T10-018](../../../SOURCES.md#src-t10-018)，父统一登记。审阅父task10_batch8_probe.py：主ledger56+额外shadow8总64，resume继续主账本/原时限，只有真实边界和参照产物齐全才新PID恢复；没有发现阻塞缺陷。父已处理reference finally恢复原replay/learner以免shadow混入原离线artifact。当前代码冻结，只完善本节点文档；状态review，真实采集/最终签收交父。未启动GPU、未实际采集/更新、未提交、未改旧账本。源代码变更仅recovery.py/test_recovery.py/new test_runner_boundary.py；本节点未发现需改load的已证缺陷。
