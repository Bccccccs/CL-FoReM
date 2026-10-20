# ROOT-DOC-REMOVE：移除根文档兼容入口

- 用户要求：把旧路径干掉，清理根目录。
- 负责人：Codex；开始时间：2026-09-30T16:05:55.259754+08:00；状态：done。
- 范围：仅根 doc/ 兼容入口及当前文档中的相关路径说明；保留 forem/doc 实体内容、其他 Agent 改动和历史记录。
- 已检查：根 doc 为真实目录，只有 README.md 及 PROGRESS.md、agent_logs 两个符号链接；目标均在 forem/doc。task0.12 已由 Claude 交付 review，本次不做实验复核。
- 推荐：Codex GPT6.1sol / Claude Sonnet5.5，low 或平台默认；常规目录清理，无特殊推理要求。实际模型/强度：未知。
- 待执行：登记进度，删除三个兼容入口及空 doc 目录，更新 AGENTS、文档入口与现行流程的路径说明，核验目标内容和任务三文档保留。

## 实际结果与交接

- 用 Python Path.unlink 删除根 doc 的两个符号链接及 README；Path.rmdir 删除空目录，没有递归删除目标。
- 更新根 AGENTS、forem/doc/README、DECISIONS、PROGRESS 与 task0、task0.1–0.5、task0.7、task1 的 PROCEDURE 中现行日志路径。
- 实际验证：根 doc 不存在；59 份未涉及修改的文档/证据 SHA-256 前后相同；所有任务目录仍含 TASK、PROCEDURE、RESULTS。命令退出码 0。
- 现行入口：forem/doc/README.md。其他根源码/资源兼容链接未纳入本次文档入口清理。
- 未运行构建/仿真；未提交或推送。task0 状态不变，仍待独立复核；无后台任务、无未解决事项。
