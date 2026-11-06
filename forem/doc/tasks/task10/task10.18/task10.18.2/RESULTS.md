# task10.18.2 已保存行为与评分诊断

2026-11-06，done。负责人Codex子Agent；实际模型/推理强度无法核实，派发推荐Terra/high，Claude推荐Sonnet5.5/high（跨模块学习因果核查）。本分析复用[10k训练与三点评估原件](../../../../SOURCES.md#src-t10-opt-plan-20261106)，无新环境交互、训练、GPU、旧run写入或生产代码修改。父任务统一登记来源和复核。本结果只说明所检查状态，不证明整体因果或无bug。

可复算原件：[逐状态候选/评分/预测/实际与一致性](../../../../../results/task10/t10-diagnosis-20261106/behavior/analysis.json)、[统计与逐状态派生量](../../../../../results/task10/t10-diagnosis-20261106/behavior/metrics.json)、[重建脚本](../../../../../results/task10/t10-diagnosis-20261106/behavior/analyze.py)、[统计脚本](../../../../../results/task10/t10-diagnosis-20261106/behavior/summarize.py)。只加载每个9.7 MiB actor权重和单个小决策文件，CPU两线程；不加载17–23 GiB boundary。每episode重置递归状态并按记录顺序重放，共18/20/22个决策；CPU模型重建与原GPU logit最大绝对差分别0.000250/0.000261/0.000296。所有60次选中prediction与所选slot的f_k逐元素相等；所有非首状态的上一实际结果、链接和route_s对应前一步一致。候选计数从原记录timing.current.cumulative_failures按有效mask顺序对应，代码predict_candidates通过torch.where按该顺序压缩；这一核查不能证明其他所有语义正确。

12个场景的所有initial_hashes三检查点相同。2k→5k→10k严格成功数10→9→9：sparse_00004和standard_00000三次均failure_limit，standard_00001由成功变为两次completion_with_failures，其他9场景均成功；这只是在固定12图、单seed上的观测。

standard_00001在2k首先选择移动9，实际推进3.564 m、无失败，接着3完成；5k和10k先选原地12，预测/实际均推进0.25 m、无失败。第二步所有有效候选（7、8、9、12）预测均有失败：5k选9、10k选7，预测first-failure ratio 0.030/0.023，但实际分别推进3.668/4.349 m，各有1次失败，最后均抵达终点但严格失败。首个原地和失败存在时序关联，不能仅凭此归因或断言其他候选会成功。2k初次移动9预测推进1.036 m而实际3.564 m。预测只使用当时传感器网格，执行可更新观测；预测/执行差异是观察，不自动意味着实现bug。

全12初态，原地选中数0/1/1；原地平均概率0.0813/0.1159/0.1181，逐场景均匀概率的均值均0.1351。原地相对最佳移动平均minQ差−0.406/−0.133/−0.143，平均logit差−1.142/−0.371/−0.297；standard_00001的5k/10k原地minQ优势0.128/0.052，logit优势0.151/0.237。仅凭平均偏好不能解释某张图的结局。

初态actor/minQ首选不一致6/7/9次，但首选minQ regret均值0.0051/0.0092/0.0280、最大0.0281/0.0479/0.1214；全部决策均值0.0034/0.0144/0.0210，最大0.0281/0.0582/0.1214。KL(pi || softmax(minQ/0.35))初态均值0.00354/0.00293/0.00399；初态最大与次大概率差均值0.0188/0.00918/0.00912。初态Q范围/0.35均值1.231/0.516/0.452，策略熵/log(有效候选数)均值0.9636/0.9955/0.9970。后期首选分歧较多但分布整体接近对应Q softmax，不能单凭argmax不一致认定严重跟随失效，也不能因此证明critic准确。

逐决策预测选中候选有失败的次数为4/6/8，其中存在预测零失败其他有效候选4/3/4次；选中项预测有失败而实际无失败4/3/5次，预测零失败但实际有失败2/0/0次。该计数是轨迹相关观察：候选的预测失败可区分部分候选，但不是实际反事实标签，不支持直接硬筛，也不能推断未选候选实际成功。特别是5k/10k standard_00001第二步四项均预测有失败，区分其优劣缺少可靠反事实证据。

交接：父执行者可基于这些结果核查预测网格更新与风险信息对后期critic目标及选项区分的影响；需要新增反事实交互才能直接检验未选候选结果，本次未执行，也不构成新实验授权。保留单seed、小样本、轨迹分布不同、预测与实际信息不同和CPU/GPU浮点差异等限制。

复算入口：[task10_behavior_diagnosis.py](../../../../../scripts/task10_behavior_diagnosis.py)。在既有容器和当前挂载下执行：

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 -u /workspace/scripts/task10_behavior_diagnosis.py'
```

该命令会重算并覆盖本任务behavior目录的analysis.json和metrics.json（其中耗时字段自然变化），不会写入训练/评估原件。源项待父登记：三检查点行为、权重与原始字段为项目实测，适用限定为上述单seed 12图；CPU重建评分、比较统计和候选计数为对项目原件的派生分析，具体脚本/结果及计算条件见上；候选压缩顺序和预测感知约束为本项目代码审计，符号分别为`task10.environment.predict_candidates`、`PredictionCore`。不将此处结论登记成跨任务普遍规律。
