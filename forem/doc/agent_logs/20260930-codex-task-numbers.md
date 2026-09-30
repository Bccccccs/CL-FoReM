# DOC-TASK-NUMBERS

- Agent：Codex /root；开始：2026-09-30T10:11:00.499218+08:00。
- 用户要求：一个任务一个目录，按task0/task0.1等递归编号，每层三文档；允许顺序执行或派遣子Agent。
- 范围：编号、目录、流程与启动提示词更新；不运行环境，不启动子Agent。
- 推荐：Codex GPT6.1sol低/默认；Claude Sonnet5.5低/默认，无特殊推理要求。实际当前会话模型/档位未知。
- 迁移原则：保留现有环境检查顺序与内容，统一任务根为forem/doc/tasks，历史日志不重写。

## 用户明确总体要求与落实

要求提升为根AGENTS项目级规则。活动目录改为doc/tasks/task0（环境）和task1（跟踪草案）；task0下依赖顺序保留，子目录命名task0.1至task0.5。所有流程补充一任务一目录、递归编号、顺序/委派执行和父核验要求。task0/TASK中加入更新后的Claude启动提示词。未启动子Agent或环境，待链接及三文档结构核验。历史日志不改写。

## 验证与完成

Python核验退出0：7个任务节点递归编号、每节点恰好三主文档、每流程有项目规则与委派/父验收要求；活动入口相对链接无失效；旧experiments活动目录已移除。证据：20260930-task-number-verification.json。状态done仅指文档与目录。Claude启动提示词保存于forem/doc/tasks/task0/TASK.md；从TASK与PROCEDURE接手，当前未运行环境或子Agent。
