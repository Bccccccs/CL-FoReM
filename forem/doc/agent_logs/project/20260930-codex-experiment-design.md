# EXPERIMENT-DESIGN — 对照调研与实验设计

- 负责人：Codex /root；开始：2026-09-30 16:53 +08:00；状态：active。
- 用户授权：继续调研对照工作，自主设计实验，建立forem/doc/experiment；每实验任务/流程/结果三文档。当前仅调研与文档，不启动训练或仿真。
- 推荐：Codex GPT6.1sol、Claude Sonnet5.5；研究设计审查high（需识别信息泄漏、因果混杂与算法接口差异）；常规整理low。实际模型/强度：未知；不切换会话模型。
- 起始核查：main，存在大量已有暂存/未暂存与未跟踪改动，全部保留。Claude任务日志与PROGRESS新增行显示TASK1-IMPL active，task1.1已有实测；进度上方旧“尚未执行”尚未同步，不将其当成最新状态。本轮不修改tasks/task1、源码、配置和ENV，不停止任何进程。
- 写入范围：experiment新目录、本日志；共享PROGRESS/README/DECISIONS及根AGENTS只追加本轮范围说明，写前重读。
- 调研来源：论文/作者项目/官方仓库；网页可访问≠代码审计或复现成功；未运行方法均明确注明。
- 本地参考版本：nmoma ebc39271d30e32bee167c688d752adc2383337fc；topay 0ab289c0f5a665f81a63d8ccff4011c9e1cdadfc；scwm f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b。

## 用户补充与范围调整

- 用户补充：“可以先写在备选里面”。全部exp0–6节点归入forem/doc/experiment/备选/，未纳入正式执行。exp0调研事实保留，exp1–6均未执行。现有Task1继续由Claude负责，本轮不调整。
- 已创建21份三文档和一个experiment全局索引；文献表包含14项外部工作/参考和五个核心SAC受控组。方法优先级属于建议，只有目录与记录规则属于本轮确定决定。
- 使用brainstorming梳理研究问题，使用verification-before-completion核验文档交付；没有进入实现/训练，没有委派。

## 完成交接（2026-09-30T17:10:55+08:00）

- 状态：done，仅调研/设计文档；备选方案未选用、exp1–6未执行。当前文档负责人Codex，实施负责人未登记。
- 实际写入：experiment/README及备选/exp0–6三文档；本日志与verification.json；根AGENTS、doc/README、DECISIONS只追加专项说明；PROGRESS新增本任务并完成状态，保留其他Agent条目与历史。未提交/推送。
- 研究来源：通过web search/open/find读取论文摘要、DATS已知动作队列方法段、DA-Dreamer代码入口与作者仓库README。不是完整论文复现/逐文件源码审计；新官方仓库commit未冻结、依赖未安装。N²M²上游GitHub打开失败记为入口失败，未据此声称项目无代码；本地README仍可读。初次click参数失败后用返回ref_id重试成功。
- 验证：Python一次性文档结构/链接检查，7节点×3=21主要文档、61本地链接，errors=[]、退出0；git diff --check退出0。补充核验结果链接后重新检查并刷新哈希。证据20260930-experiment-design-verification.json。未运行算法测试，因为本轮没有实现修改。
- 已完成：14项外部工作/参考适用性表，5个SAC核心受控组，未知/已知/特权信息条件，动作角色与两种参考误差区分，数据泄漏/预算/seed统计/负结果/失败处理规则，以及按依赖组织的备选实验。
- 剩余：选择备选后核验Task1基线，审计候选具体实现/信息需求/许可及兼容性，冻结数值与预算，再执行并独立复核。文档依赖表不构成自动运行授权。
- 风险：现有共享文档有历史状态与正在实施的Task1变化，接手必须读最新独立记录；5训练seed是起点，不是功效保证；DATS已知延迟与未知误差不能混排，DA-Dreamer感知时延和Arli推理延迟属于独立扩展。
- 本轮没有运行任务/PID，无监控/停止交接；不得停止他人的Task1任务。
