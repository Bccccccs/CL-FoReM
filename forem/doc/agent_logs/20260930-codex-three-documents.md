# DOC-THREE-PARTS

- Agent：Codex /root；开始：2026-09-30T10:02:54.489087+08:00。
- 用户要求：每一部分任务三文档，任务写目标和大致路线，流程写详细控制流程，结果写实际结果。
- 本轮：文档格式与现有环境/跟踪两项迁移，不实施环境。
- 选择：每个任务目录仅TASK.md、PROCEDURE.md、RESULTS.md；全局索引保留在doc/README。Agent独立过程日志仍在doc/agent_logs，原始产物在results/logs，不重复建每任务reports目录。
- 模型推荐：Codex GPT6.1sol低/默认；Claude Sonnet5.5低/默认，无特殊推理要求。当前会话实际模型/档位未知，未切换。

## 用户澄清与迁移

用户强调每个节点内部、包括子节点都要如此，并在流程中写明。已落实递归规则：环境父节点三文档，E1–E5各自三文档；跟踪父节点三文档，每份PROCEDURE写明递归规则。保留原环境操作细节，拆至相应子流程，未执行RESULTS不伪造证据。旧两目录完整备份：/home/ybc/projects/CL-FoReM-reset-backups/20260930-091202/before-recursive-three-documents.tar。活动索引/AGENTS/ENV/交接指向新文档。历史Agent记录不重写；待验证。

## 核验与结束

实际Python核验退出0：7个节点各有TASK/PROCEDURE/RESULTS且无额外主文档；每份流程明确递归规则；三份文档均有双Agent模型推荐；27个活动文档无失效相对链接；所有结果标尚未执行。证据：20260930-three-documents-verification.json。任务done仅指文档重组，无环境实施。Claude入口为00-environment/TASK.md再读PROCEDURE.md，实际执行后逐节点填写RESULTS.md。
