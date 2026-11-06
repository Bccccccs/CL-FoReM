# task10.15.1 执行流程
递归规则：本节点无子任务；若委派必须先建稳定编号三文档与独占范围。执行者可自主选模型/强度与先建档委派，推荐GPT6.1sol/high、Sonnet5.5/high，因梯度与变时长目标核查。父统一GPU与总预算；本子仅CPU前向/梯度，不执行更新。
1. 读根AGENTS及父三文档，读取首更before完整learner/replay/RNG和sample，按原sample精确恢复sequence_outputs。
2. 拆解逐样本reward/势函数/折扣/mask/next Q/entropy/target/actor Q与熵，比较原首更loss（容许CPU/GPU数值差但必须报告）。查零dt与终局stall。
3. 分离actor/critic梯度，核detach预期、optimizer包含参数、参数变更及LR日程；用具体样本给支持/反证/证据不足。
4. 输出signal-*原件至父独立run；三文档/子日志记录命令退出码/耗时/局限，交父复核。不改合同和共享文档。
