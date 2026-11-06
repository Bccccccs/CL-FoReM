# task10.17.1 正常batch8恢复

开始2026-11-03 22:52+08，完成CPU阶段2026-11-03T23:02:01.023793+08:00。负责人Codex；实际模型/强度未知，推荐GPT6.1sol/high、Sonnet5.5/high。用户授权父task10.17范围内恢复实现及CPU夹具；本子仅写recovery.py、新boundary_state.py、新test_decision_recovery.py与本节点文档，保留原未提交内容。先读根AGENTS、ENV/README/PROGRESS、父与本子三文档及父独立日志。无下级委派。

实现、命令、退出码和证据详见本子RESULTS，[来源](../../../../../SOURCES.md#src-t10-043)。CPU合并45passed/25.38s/rc0，原件forem/logs/task10/task10.17.1/cpu-tests-v2.txt；无GPU/真实决策，合成CPU fixture更新不算真实训练。父随后核对原件及A真实预算。

主要工程选择：纯状态白名单重建，完整动态Core字段保持；不序列化进程/CUDA graph/活env，不额外抽样或人为终止。旧自然终局恢复不扩权，新API独立format；来源、runtime/determinism、ledger、journal与原epoch共同拒绝不安全恢复。独立新PID CPU精确下一更新已过，GPU与正常真实混合边界尚未由本子核验。

下一步：父A统一128/64/3600s验证；A失败交回决策者，不因CPU通过直接启正式10k。源码现已交父冻结，之后未经父协调不再修改。
