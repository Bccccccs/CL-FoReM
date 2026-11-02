# task10.9 流程

递归规则：本节点恰有TASK/PROCEDURE/RESULTS三文档；继续拆分须先建子节点三文档，登记依赖、负责人和父验收。当前无子节点。

独占写入：forem/src/task10/recovery.py、forem/src/task10/tests/test_recovery.py、forem/src/task10/tests/test_runner_boundary.py，本节点三文档及[独立日志](../../../agent_logs/task10/task10.9/20261102-codex-runner-boundary.md)；共享文档、runner及入口由父独占。输入为根AGENTS、ENV、task10三文档、SRC-T10-015及父日志。推荐GPT6.1sol/high、Sonnet5.5/high，因跨模块状态核验；实际配置在RESULTS记录。执行者可按难度选可用模型/强度并决定独立完成或先建档再委派，所有子Agent共享父授权/总预算/截止；父核验原始证据并统一验收。

1. 审阅原save/load及真实train顺序，先与父固定args.resume、stop_at_boundary、boundary_reference、max_decisions/max_updates/seconds和collector-boundary.pt/boundary-reference.pt。
2. 先写边界一致性失败夹具；确认相同journal身份但真实transition六字段不同、replay终局类型与live core不同均被旧实现错误接受，再最小修复。显式fsync journal，核对最后transition真实字段及终局类型，拒重复journal身份。保留原采样器/锁/原截止恢复机制。
3. CPU synthetic batch8环境首批仅4结束，正常reset这4行；第2批8行自然terminated/truncated，真实train才保存并退出。monkeypatch环境/B3/model设备/初始化/timers和模型输入；真实Budget、EpisodeReplay、journals及save/load均保留。不运行真实物理采集/在线更新/GPU。
4. 对ca57b4b原runner的临时模块执行同夹具RED，限定真实Budget容量24以防进入1000预热；临时文件不替换共享runner。旧入口预算退出后缺collector-boundary.pt应失败。
5. 新PID子进程保存，父测试进程恢复，验证24条回放/账本、24个唯一environment/episode/decision身份、原journal SHA不变、原monotonic started/deadline相同。另通过父boundary_reference分支执行synthetic连续8条，与新PID恢复8条逐位比较scene/观测/候选/选择/RNG/journal/replay/ledger，主账本与shadow分别保留。
6. 容器内CPU pytest，单次120s限制，原始log/JUnit及临时产物持久化到forem/logs/results。失败时保留日志与阶段，不改科学语义、不开GPU、不扩父预算。源代码冻结后只写文档，真实GPU阶段由父统一排期。[证据](../../../SOURCES.md#src-t10-018)。

父验收：复跑确定性夹具并核查原件，再验证正常batch8真实可达安全边界。真实不可达必须明确未验证，不主动截短episode；CPU成功不等于真实恢复通过。
