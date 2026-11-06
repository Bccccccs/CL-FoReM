# paper3.2 观测问题原文调研记录

2026-11-06，Codex observation_literature，状态review。授权只读论文/官方源码，独占paper3.2三文档与本日志，不改代码/运行进程/全局来源。模型/强度未知；推荐GPT6.1sol或Sonnet5.5 medium，机制/新颖性high。独立完成，无继续委派。

已读根AGENTS继承全文及paper3父/子三文档。实际联网关键词、原文版本和入口见RESULTS；原始HTML下载及文本提取在forem/results/paper3/literature。仅下载三篇HTML及一份代码文本，未执行下载源码。首次用bs4提取因环境无包退出1，随后标准库提取成功；未安装依赖。

精读ActPerMoMa 2310.00433v2、CURA-PPO 2602.01731v1、MoPA 2609.12081v2全部正文/公式/表格/局限。最初批量输出被截断，随后分篇/按章节读取补齐，不以截断输出冒充全文。ActPerMoMa官方commit fdc15f5dd6b6c2cafbdbe18e98e97170e7cf5cd0，核draw_action/reachability_utilities/ig_fn_parallel部分，未测试。

向父已报告MoPA强最近邻、ActPerMoMa普通场景IG-only优于全量的负证据、CURA方差含义与仿真边界、MoPA消融保留通信故不能单独证明通信因果。父提供当前ghost扫描/2.5D/74维状态与冻结B3推演信息；本子仅把它用于适用性，项目事实最终由paper3.1验收。

实际写入：本日志及paper3.2 TASK/PROCEDURE/RESULTS。来源草案SRC-P3-O01至O07交父追加，不并发写SOURCES。完成7初筛/3全文/1部分代码；全部新方法与验证仍建议，未运行实验。
