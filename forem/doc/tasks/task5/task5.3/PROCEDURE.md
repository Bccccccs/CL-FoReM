# task5.3 汇总、独立重算与复核 — 详细流程

状态：**尚未执行**。执行：Claude。

## 递归规则声明

本节点遵守根AGENTS的递归三文档规则。本节点及以后拆出的每个task5.3.K，都必须有各自的TASK、PROCEDURE、RESULTS。父节点为[task5](../PROCEDURE.md)。

## 步骤

1. 开工登记：在PROGRESS登记task5.3，并新建日志`agent_logs/task5/task5.3/`。阅读5.1、5.2的RESULTS和manifest。
2. task5.0核验（在5.1/5.2开训前进行）：复核`t5.0-env-r1`全部证据，尤其是GPU口径、URDF等价性、两个就绪检查和补丁语义；把放行或不放行的结论写入本节点RESULTS和task5.0 RESULTS。
3. 版本核验：
   - 镜像digest与manifest记录一致。
   - Husky源码sha256与`husky/src`（1ccedd0）一致。
   - 上游代码与镜像内代码的差异清单可以复现。
4. 生效配置核验：用ray `params.json`独立比对两项与冻结口径。列出A、B之间的全部差异，并逐项判断是否属于“env或Husky快照自带配置”。
5. 补丁与偏差核验：
   - 逐个检查5.2的patch与`patch_reasons.json`，确认没有触及算法、奖励、观测或任务语义。
   - 复核URDF等价性结论。
6. 独立重算：
   - 从`progress.csv`、`result.json`以及评估原始输出，自己写脚本重算两份表：训练中评估序列、9任务最终成功率。
   - 与执行者的csv对比。
   - 重算脚本放在`forem/scripts/`，结果放在`forem/results/task5/t5.3-review-r1/`。
7. 对照汇总：
   - 填写父RESULTS汇总表。
   - 按父TASK的解读规则给出诊断，并写明限制：单种子、CPU/GPU口径、wandb离线、9任务中哪些不能运行、与原文5种子平均的差别。
8. 判定：
   - 全部通过时，task5.1、5.2和父任务标为done。
   - 有问题时，编号登记（T5-Rxx），交回执行者修正。
   - 需要用户决策的事项单独列出。

## 模型与推理强度

推荐Claude使用Sonnet5.5/medium，Codex替代GPT6.1sol/medium。
