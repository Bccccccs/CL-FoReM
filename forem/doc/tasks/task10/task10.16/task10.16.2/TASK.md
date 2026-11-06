# task10.16.2 · 均匀先验KL目标实现

2026-11-03 · Codex · review（实现与CPU核查完成，待父核验）。父已选择固定alpha=0.35的relative_uniform KL正则新协议，沿旧初始温度，非调参最优值；依据 [SRC-T10-035](../../../../SOURCES.md#src-t10-035) 与 [16.1数学复核](../task10.16.1/RESULTS.md)。该选择消除正的每决策熵**条件期望**，不保证任务成功率或原地排序改善。

交付：显式配置选择的新目标、固定温度、保存/恢复目标隔离、正常runner入口接线与CPU测试。旧配置/历史无目标字段checkpoint保持legacy。独占task10/learning.py、entry.py、runner.py、新tests/test_relative_uniform.py、新config/task10/relative_uniform_trial.json，以及本子三文档与日志；父追加授权recovery.py的最小目标传递。不得修改原实验产物、task7核心或环境。

本轮只实现与CPU验证，每条CPU命令≤120秒，CUDA_VISIBLE_DEVICES为空；无GPU、无新真实交互、无实际训练运行、无提交。CPU单元测试允许合成张量上的优化器调用，仅作合同验证，不计真实训练预算。新试训是否启动由父执行者另行验收决定；新配置继续formal_training_authorized=false。

验收：均匀分布正则0、非均匀条件期望≤0、单有效及无效槽、零dt与终局、actor梯度解析/autograd、checkpoint跨目标拒绝、旧路径回归、正常train配置传至新learner。实际结果与限制见 [RESULTS](RESULTS.md)。

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，涉及目标/状态版本兼容的因果核对；实际模型/强度无法独立核实，记未知。执行者可按难度选模与先建档委派，均不扩范围、预算、截止；本次独立完成，未创建下级任务。
