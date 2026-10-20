# AGENTS-SCOPE-GUARD

- 负责人：Codex /root；状态：done；开始：2026-10-05T19:42:29+08:00。
- 用户要求：在 Agent 约定中禁止擅自功能拓展；推荐拓展必须询问用户并获得明确同意才能加入。
- 授权与文件范围：仅修改根 AGENTS.md，并登记 PROGRESS.md 与本独立日志；不修改实现或实验文件。
- 开工核查：当前分支 main，工作树已有其他改动；根 AGENTS.md 无已有差异。Claude 与其他 Codex 进程存在，保留其文件和进程。
- 模型建议：Codex GPT6.1sol、Claude Sonnet5.5，低（low）或平台默认；明确文档修改无特殊推理要求。实际本会话模型/强度：未知。
- 已完成：根 AGENTS.md 开头新增功能范围硬性约束，并更新日期；PROGRESS 仅新增本任务登记，保留其他任务状态。
- 验证：git diff --check -- AGENTS.md forem/doc/PROGRESS.md 退出码 0；Python 核对三项关键条款与进度登记通过，退出码 0。
- 交接：规则适用于全工作区所有 Agent；无剩余事项、无新增运行任务。后续推荐拓展必须先询问用户并取得明确同意。
