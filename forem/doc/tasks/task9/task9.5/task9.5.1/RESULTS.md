# task9.5.1 RESULTS — 独立参数与设计预审

状态：**done（独立预审交付已由父核验并采纳；新增实验尚未执行）**。依据[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)。

负责人Codex；开始2026-10-31T21:42:00+08:00，交付2026-10-31T21:47:11.020584+08:00。派发记录指定实际GPT6.1sol/high；内部配置独立核验未知。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因批次恢复、参数更新及截止排程需跨模块因果核查。

交付原件：[preflight-review.md](../../../../../logs/task9/t9-opt-design-20261031/preflight-review.md)；[独立日志](../../../../agent_logs/task9/task9.5/task9.5.1/20261031-sol-preflight.md)。事实来源：[SRC-1337](../../../../SOURCES.md#src-1337)、[SRC-1342](../../../../SOURCES.md#src-1342)，由父补登本报告审查证据，审核者未写共享台账。

结论：三轴研究范围有条件通过，实施合同当前需修正。最重要的是旧--transfers250000会改变末个向量动作批，不能据此声称profile/resume等价连续3M；应保持3M动作预算，在消费250k、完成原评估后保存pending再暂停。其余必须落实逐卡含G1/smoke/保存的截止排程、分阶段release、完整冻结导入/路径/恢复合同。

19配置、17run、69文件hash数量已独立核对；19配置与69文件相对快照无漂移。B3/E15/R200的3M更新299975，U20为149988；历史B3配对终点均值63.5%、末三均值57.333%。六路12h代理=72 worker h，但四卡旧任务预估释放后，至少两条卡道首波须在11-01 07:00前启动才装得下两run，G1/smoke使全六路能否完成尚未证实。精确输入、公式、限制及建议见原件。

仅运行cat/sed/rg/git只读状态、ps、date、Python标准库JSON/hash/时间与布局计算，工具命令退出0。没有torch导入、GPU/optimizer/训练、实验实现或旧进程启停，未commit。实际写入仅本RESULTS、独立日志、logs原件报告。父处理F1–F4并核对证据后交实施者；本次不等于CPU/GPU等价或新训练通过。

父Codex2026-10-31核验采纳：本预审交付已核原件，F1–F4已同步父流程/实施brief并形成CPU候选，依据[SRC-1343](../../../../SOURCES.md#src-1343)、[SRC-1346](../../../../SOURCES.md#src-1346)。本预审子节点状态done（仅预审交付）；新增实验与最终验收仍属父任务active。
