# task8.9.2 B 固定全量执行

负责人 Terra，实际 gpt-6.1-terra / low；推荐 Codex GPT6.1sol / low、Claude Sonnet5.5 / low，固定步骤无需特殊推理。授权见父交接及 [SRC-1129](../../../../SOURCES.md#src-1129)。范围固定清单103 build、audit、finalize；不改代码、参数、生产或其他任务。账本起始50.67397289350629/5400秒，active空，三项冻结SHA一致。执行表和逐项日志位于 `results/task8/t8-pool-20261027/fixed-full-r2.json` 与 `fixed-full-r2-logs/`。首失败停，账本保留原费用，wrapper非导出器开销按实测补计。

2026-10-27 11:51 CST：容器内 wrapper PID 2554024，脚本 `results/task8/t8-pool-20261027/fixed-full-r2-wrapper.py`，监控 `fixed-full-r2.json` 和每块日志；每块子进程 PID 记录于预算账本 active/entries。只可停止此已核实进程及其子任务，停止后先核查 active、产物与失败状态，未经父核准不恢复。首次 detached 调用容器内 `/tmp` 缺文件，未触发账本和任务；改用工作区路径后启动。11:54 已完成前6块，offset600运行中；下块开始账本207.37589669041336秒。

2026-10-27 12:08 CST 父通知 A 的 P2/P5 硬门 partial，停止后续新块并等待用户决定。对调度器 PID 2554024 发 SIGSTOP；当时 offset3900 的 exporter PID 2554333 正在运行，未中断，正常退出 rc0；账本 active 清空后向已停止调度器发 TERM+CONT 退出，未再启动 offset4000。边界复核 offset3900 报告 count100、两项 SHA、每记录生产=O和每盒非空均通过；补计停止边界检查实际开销0.025757947936654秒。前40块各100条均通过，records实际4013（含分布在这些块外的先导/profile缓存）；完整执行表 status=blocked、next_job_index=40；账本1111.4041973212734/5400秒，active=null。未运行 audit/finalize；下一步需父协调用户对 A 门的决定，恢复前重读清单、账本和产物且不得覆盖失败证据。独立最终验收尚未执行。
