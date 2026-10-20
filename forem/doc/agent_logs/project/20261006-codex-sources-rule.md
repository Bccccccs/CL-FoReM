# DOC-SOURCES-RULE

- 开始：2026-10-06T21:17:40+08:00；负责人：Codex /root；状态：done。
- 用户授权：在AGENTS.md增加需要论据的数据、方法与观点统一记录出处的规则，并在doc建立统一文档；以时延选择为例。
- 范围：AGENTS.md、forem/doc/SOURCES.md、README.md、PROGRESS.md及本日志；不修改实验协议、实现或运行状态。
- 开工检查：main分支，存在大量既有未提交改动；PROGRESS记录Claude实施Task2及其他Codex文档任务，进程表存在codex与roslaunch。仅按位置增补共享文档，不覆盖任务文件。
- 推荐：Codex GPT6.1sol / Claude Sonnet5.5，low或平台默认；普通文档维护，无特殊推理要求。实际模型/强度：未知/未知。
- 已执行读取根/forem AGENTS、doc README/PROGRESS，git status --short、git branch --show-current与进程检查，退出码0。

## 交付与核验

- 已完成：根AGENTS增加强制论据来源规则；建立SOURCES全局台账、登记模板和时延选值要求；README入口与PROGRESS同步。
- 证据：AGENTS.md“论据与引用来源”、forem/doc/SOURCES.md及README入口；本轮apply_patch成功。
- 验证：git diff --check（限定三份已跟踪文档）与Python规则/台账/索引/链接目标断言，退出码均为0。
- 限制与剩余：未开展历史来源全面核查，没有给任何时延值新增文献背书；台账明确暂无已核验条目。
- 下一步：各Agent后续使用或修改需论据的主张时补登来源并核查适用性。没有启动实验、改变协议、提交或推送；没有本轮运行任务需要监控。
