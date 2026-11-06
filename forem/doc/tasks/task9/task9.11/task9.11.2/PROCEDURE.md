# task9.11.2 · 审计流程

递归规则：本层三份主要文档齐全，不再拆分或委派；如未来拆分须先由父建下级三文档。读取根AGENTS及父/本三文档和独立日志入口，核源码/原事件，不以聊天替代记录。只在本层与所属日志写入，来源由父统一SOURCES登记。

初稿完成后独立核对问题与方案匹配、唯一自变量、同期对照/种子/步数/评估/墙钟/存储/停止、独立测试污染、源引用；给阻断性问题及修订建议。

推荐GPT6.1sol/high、Sonnet5.5/high，理由同TASK。全程零模型/仿真/训练。

实际只读核查顺序：检查分支/dirty/进程，读根与forem约定、入口/进度/ENV和父/.1/.2记录；从Core._finish、旧evaluate、update_due/set_transfer/consume_transition/limited_step及旧准入矩阵查合同；读原独立JSON和字段审计，标准库独立重算转移、updates、评估回合、worker预算和日程终值。未导入项目、torch、模型或环境模块。证据清单及精确hash记录在[independent-design-check.json](../../../../agent_logs/task9/task9.11/task9.11.2/independent-design-check.json)。

问题按阻断程度先发父；父独占共享文档修订，本子重读确认后更新RESULTS逐项状态。规划验收PASS/有条件通过/FAIL与未来运行释放分开。未来实现仍必须经过父PROCEDURE A–G准入，不执行本次文本中的示例命令。[唯一执行协议](../PROCEDURE.md) · [工程选择来源](../../../../SOURCES.md#src-1388)
