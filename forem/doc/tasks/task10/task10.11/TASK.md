# task10.11 · 确定性入口及7小时截止合同

负责人Codex子Agent；状态review，待父核验。授权来自[本轮用户批准SRC-T10-021](../../../SOURCES.md#src-t10-021)：仅一次连续在线试训，1200真实决策、200更新、25200秒先到即停，允许不完整结果，不重启/恢复/配对/task11。独占入口及CPU夹具实现；唯一真实/GPU运行由父负责。[本节点证据SRC-T10-022](../../../SOURCES.md#src-t10-022)。

目标：默认smoke继续1800秒；只有显式`--run-profile online-trial`才能选择25200秒和1200/200。Python配置校验、Budget、合同与外层监督共用原始epoch换算后的硬截止；20秒清理预留由父runner单列work deadline，Budget.deadline保持实际hard。按[SRC-T10-020](../../../SOURCES.md#src-t10-020)采用已核确定性设置，并提供实际设置/版本/设备报告接口。

独占范围：`forem/src/task10/runtime.py`、新`entry.py`、`forem/scripts/task10_run_bounded.sh`、`forem/config/task10/online_trial.json`、`forem/src/task10/tests/test_entry.py`（可test_runtime.py）、本三文档及[独立日志](../../../agent_logs/task10/task10.11/20261102-codex-entry.md)。不修改runner.py/共享文档，不自行GPU/真实采集，不提交。父统一登记PROGRESS及SOURCES。

验收：CPU验证默认/显式profile和错误seconds拒绝、旧SimpleNamespace默认smoke兼容接口、Budget原hard起止持久化、过期epoch不启动worker、短剩余时限TERM与KILL均不新起钟、确定性实际flags/threads/RNG及预启动CUBLAS拒绝；父接线后独立复跑正常入口。CPU夹具不替代真实在线更新或batch8恢复。

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为epoch/monotonic/清理窗口与正常训练合同跨模块核查。父派发配置为GPT6.1sol/high；当前平台实际模型/强度不可核实，记未知。执行者可按难度选模/强度及独立完成或先建档委派，全部共享父授权、预算与截止；本节点独立完成，无再委派。
