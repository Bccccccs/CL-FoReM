# task9.5.3 PROCEDURE

状态ready；尚未执行。依据[TASK](TASK.md)与父[PROCEDURE](../PROCEDURE.md)。

递归规则：每层恰有TASK/PROCEDURE/RESULTS，需进一步拆分时先在本目录建立task9.5.3.1等三文档并由父明确顺序/依赖/负责人与验收；本次禁止子Agent再委派。

1. 阅读根AGENTS、自己的TASK与父合同，确认写入边界/依赖/实际模型。
2. 按对应父步骤检查或实施，日志记录命令、rc、源码/配置hash、真实产物与未完成项。
3. 首个失败保留原件并报告，不暗改科学规则或越预算重试；对实现测试修复须记录版本/原因，实验重跑需父裁定。
4. 完整报告到RESULTS/独立日志，父验收后收尾；涉及GPU须先查旧进程/锁与release，不停止他人任务。

Codex GPT6.1sol / high、Claude Sonnet5.5 / high推荐（审查恢复与边界）；实际尚未执行。
