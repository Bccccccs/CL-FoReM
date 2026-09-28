# FLOW-MAP-028 流程编号说明

- Agent：Codex /root
- 开始：2026-09-28T15:38:34.316602+08:00
- 状态：done（流程说明）
- 范围：解释P/Stage/R/S/G，新增统一阅读入口，不改算法或实验协议。
- 已读：AGENTS、README、PROGRESS、DECISIONS（D38/D39）、P2/P4、RUNPLAN、Stage0接手记录与LOGIC-028。
- 依据：P为原阶段体系；D38调整顺序后保留技术模块编号；Stage为最新实验推进轮次。旧P4后置规则已被取代。
- 长任务：本任务无；Stage0其他Agent日志记录seed22/33已启动，本轮不核验实时进程、不干预。

## 进度

登记后整理统一说明，保留历史编号便于追踪，不引入新阶段编号。

## 完成与验证

新增doc/WORKFLOW_GUIDE.md并在README增加入口；记录P/Stage/R/S/G/D含义、Stage0-2、P2+简化P4时序及旧依赖的覆盖关系。没有改既定实验协议、代码或其他任务状态。
实际命令：读取Stage0、DECISIONS、PROGRESS、RUNPLAN，退出0；Python写文档并核验入口、链接和任务行唯一。状态来自日志，不声称实时训练完成。
下一步：按统一入口理解与推进；Stage1前补训练/回放上下文，具体见LOGIC-028。不创建新的阶段编号。
