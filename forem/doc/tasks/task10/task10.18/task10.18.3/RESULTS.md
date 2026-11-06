# task10.18.3 冻结表征的终局价值诊断

2026-11-06，done。Codex子Agent执行，实际模型/推理强度无法核实，派发Terra/high；Codex推荐GPT6.1sol/high、Claude推荐Sonnet5.5/high，理由是辨别价值头拟合与表征能力。依据父任务既有诊断范围及[项目授权](../../../../SOURCES.md#src-t10-opt-plan-20261106)，只使用旧训练原件、CPU与独立诊断参数，未运行仿真或生产训练，也未修改原模型、生产代码或原run。由父登记新来源和统一复核。

**结果。** 原10k价值头在此样本中已有较明显的已选动作成功/失败排序信号；冻结表征下独立头继续拟合可以降低拟合集误差，但留出AUC略低于原头。不能从此推论整条策略已能可靠区分候选、学习率变更可改善任务表现，或否定对其他状态/方法的研究。

预登记见[pre-registration.json](../../../../../results/task10/t10-diagnosis-20261106/value-probe/pre-registration.json)：按1250批编号等距、含首尾取64批，保留所有初态、终局真实已选转移，不按标签选择或补采。实际228条（预期的300余条只是估计）：map_id分组seed1813打乱、按地图数75/25拆分，拟合171条/169张图，留出57条/57张图；拟合集成功105、失败66，留出成功42、失败15。均为旧训练池、曾参与旧训练的图；诊断留出地图不在本次头拟合中，但不是独立新图泛化测试。所有选中候选有效，均满足初态route_s=0、bootstrap_mask=0、终局且原奖励等于严格成功的0/1。

固定10k小actor.pt中VCM、候选编码器和实际输入，空记忆逐批计算已选动作的`concat(state,e)`。第一个小批显式重建Q与完整模型相同，最大误差0；特征和输入及地图列表见[frozen-inputs.pt](../../../../../results/task10/t10-diagnosis-20261106/value-probe/frozen-inputs.pt)、[sample-split.json](../../../../../results/task10/t10-diagnosis-20261106/value-probe/sample-split.json)。目标为真实原reward，损失为原终局SAC双Q损失`0.5*(MSE(Q1,r)+MSE(Q2,r))`；AUC和成功/失败Q均值基于双Q平均。原头为0更新，两臂各自从相同原始头复制、重置Adam，200更新、batch32、完全相同的预生成批次，lr分别1e-6及1e-4；优化仅发生于独立Q副本。

| 诊断头 | 拟合双Q平均MSE | 留出双Q平均MSE | 拟合AUC | 留出AUC | 留出成功/失败平均Q |
|---|---:|---:|---:|---:|---:|
| 原头 | 0.05035 | 0.09027 | 0.9674 | 0.9397 | 0.8234 / 0.2395 |
| 1e-6，200步 | 0.04712 | 0.08964 | 0.9704 | 0.9349 | 0.8526 / 0.2157 |
| 1e-4，200步 | 0.02193 | 0.08399 | 0.9981 | 0.9333 | 0.9039 / 0.2026 |

两臂梯度L2均值分别0.3924/0.3409，最大均0.8070，200步均有限。完整逐步拟合/留出曲线和最终Q1/Q2各自MSE见[summary.json](../../../../../results/task10/t10-diagnosis-20261106/value-probe/summary.json)、[1e-6曲线](../../../../../results/task10/t10-diagnosis-20261106/value-probe/lr-1e-06-curve.json)、[1e-4曲线](../../../../../results/task10/t10-diagnosis-20261106/value-probe/lr-1e-04-curve.json)。独立诊断头和同批索引位于同一value-probe目录，非部署权重。原权重SHA256 `64a2faf77a105991dd7ea055534c23859ed6a79c2c7f8716b5203841564c77e3`；64批各自哈希记录于split文件。完整过程CPU两线程4.42秒，退出码0，未用GPU、未新增环境步或生产更新。

限制：这是被原策略实际选中、第一步即终局的样本；无法判定未选候选或多步状态的价值是否正确，也没有新地图或新种子策略结果。诊断头的重置Adam、固定输入、小批采样和纯终局数据不等同在线训练；两学习率仅是既定的有限敏感性对照，不能由此归因整个10→9→9变化或选择生产超参。若需探讨学习率与在线任务成绩，应另行设计受控研究；本诊断不自动授权其他探针或训练。

复算入口：[task10_value_probe.py](../../../../../scripts/task10_value_probe.py)。下述命令会覆盖本次value-probe诊断产物，不写旧训练原件：

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 -u /workspace/scripts/task10_value_probe.py'
```

待父统一登记来源：选样、原奖励及权重为项目run原始证据，脚本与summary为受预登记约束的项目派生分析；原损失形式为`task7_upper.sac_discrete`的实现审计，适用范围均如上，不得作为普遍化结果。
