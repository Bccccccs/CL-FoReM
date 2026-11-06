# task10.16.2 执行流程

递归规则：子任务继承编号且每层恰有TASK、PROCEDURE、RESULTS三文档，父登记顺序、依赖、负责人和验收；本节点无下级任务。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需核对目标推导和恢复隔离。执行者可按难度选择可用模型/强度并先建档委派，共享父授权与预算；本次未委派。

1. 先读根AGENTS、README、PROGRESS、ENV、16.1复核及本三文档；核对Git/已有进程，保留他人修改；由父维护共享进度与来源台账，子写独立日志。
2. 保留Stage1Learner默认legacy。新增明确objective/version，relative_uniform的alpha固定.35且不创建温度优化器。目标：`V=Σπ[minQ−alpha(logπ+logN)]`，actor日志为`Σπ[alpha(logπ+logN)−minQ]`，N只计相应状态有效mask。沿用原SAC梯度/optimizer，通过next target Q减alpha logN实现目标平移；当前logN是actor参数常数，仅加回loss日志，不改变其梯度。终局bootstrap mask、dt、g与reward不改。推导与选择见 [SRC-T10-035](../../../../SOURCES.md#src-t10-035) 和 [16.1](../task10.16.1/RESULTS.md)。
3. 新checkpoint/actor写learning_objective合同与alpha；无该字段的历史状态只属legacy。目标、版本、固定alpha或固定温度合同不匹配时，恢复在模型/优化器修改前失败。
4. normal runner.train的新建/恢复都传resolve_profile所得config到create_learner；recovery默认复验工厂继承learner目标；entry-check按输入checkpoint目标建learner，但online-trial仍只授权train，未开放新profile或GPU入口。
5. entry只允许登记路径`forem/config/task10/relative_uniform_trial.json`的精确配置，相对online_trial只多objective/version/alpha三个字段。使用现有online-trial profile及1200/200/25200s边界，不能通过复制配置或改alpha绕过校验。这只是实现入口合同，不代表本轮获准启动。
6. CPU命令统一`sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -m pytest ...'`。使用独占--basetemp避免共享临时目录所有权冲突；失败记录真实原因，不修改共享目录权限。执行专项后回归learning/entry/recovery/online_runner，保留log与退出码；不采集、不启动训练。

详细已执行命令和产物见 [RESULTS](RESULTS.md)，未执行的GPU入口与新试训留给父单独验收。
