# task10.16.1 · 目标函数独立复核结果

2026-11-03，状态 **review**，交父执行者核验；数学审查完成，不代表实现或训练通过。任务为独立审查，实际模型与推理强度平台未提供可核验标识，记未知；推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high，因为需核对变时长目标与温度的因果一致性。未修改生产代码，未使用GPU、采集或执行更新。父执行者负责来源台账登记与最终选择。

## 已有事实与推导输入

现有目标见 [task10.15结果](../../task10.15/RESULTS.md) 与[目标和梯度证据](../../../../SOURCES.md#src-t10-033)：`learning.py` 使用 g(dt)=0.99^(dt/0.1s)，且 dt=0 时 g=1；`task7_upper/sac_discrete.py` 的 next value 为 Σp(Q−α log p)，actor 为 Σp(α log p−Q)，现行自动温度目标为 0.98 log N。已记录20个零时长样本均非终局，验证集出现连续原地停滞；训练只有200次更新且未覆盖对应原地停滞终局链，不能把某个原因裁定为唯一原因。该输入的复现身份、数值及限制见 [SRC-T10-031](../../../../SOURCES.md#src-t10-031)、[SRC-T10-032](../../../../SOURCES.md#src-t10-032) 与 [SRC-T10-033](../../../../SOURCES.md#src-t10-033)。

## 一致目标及边界

以下是基于上述代码合同的数学推导与待验证工程选择，不是效果实测。记 N(s) 为有效候选数、u(a|s)=1/N(s)、p=π(a|s)，Q=min(Q1,Q2)，m为独立bootstrap mask。对固定 α>0 的均匀先验相对熵目标：

- `V(s)=Σ有效a p(a|s)[Q(s,a)−α(log p(a|s)+log N(s))] = Eπ Q − α KL(π||u)`。
- `y=r + m g(dt) V_target(s')`，p取next在线actor、Q取next target双Q最小值，N取next mask；终局m=0。
- critic 对实际选中候选拟合该 y；actor 最小化 `E_s Σ有效a p(a|s)[α(log p(a|s)+log N(s))−Q(s,a)]`，依现行梯度隔离合同处理 Q；固定α时关闭温度优化。

KL非负，因此正则项**按策略条件期望**不大于零，均匀时等于零，消除了普通SAC的正的每决策熵奖励；单条样本 `−α log(p/u)` 仍可能为正，不能说每个采样动作均非正。当前状态的 log N 相对actor参数是常数，其梯度与普通熵形式相同；但 next value 必须加上 `−α log N(s')`，尤其不同状态有效候选数可变。不能只改actor或只删除next熵。该目标改变多步价值与任务权衡，不保证行动必然离开原地：零时长零收益回路可形成平局；g(0)=1，不能从标准严格折扣收缩直接保证唯一固定点。实际环境有限停滞终止，不能据无限回路反例声称真实执行无限循环。

低温普通SAC只缩小 αH，α>0且H>0时仍有每决策正项；α=0才消除它，此时需同步去掉actor熵、target熵并关闭温度更新，探索行为会改变。另一方向是环境任务价值critic和独立探索策略，但其策略评价、off-policy训练和行为/目标策略关系需单独定义，不能直接称为当前SAC等价修复。

自动温度若沿用当前熵下限 h(s)=0.98 log N(s)，则局部温度损失 `Lβ=β E[H(s)−h(s)]`，β=log α，与 `β E[(log N−h)−KL(π||u)]` 代数相同；梯度下降在熵过低时增α。它是批量状态上的温度更新规则，不能保证原地脱困。更重要的是，若声称优化完整变时长轨迹的约束拉格朗日目标，逐决策 `−α h(s)`（等价KL界中的常量项）会随决策数量/状态变化，不可自动当作无关常数并省略；对偶目标、状态占用与终止应一起明确。为最小、可审计方案，建议固定α并先核对现有探索覆盖，不在本审查中指定新α数值或声称性能改善。

## 时长加权的不可辨识与验收

回放的dt仅对应已选动作，不能将其复制给当前其他候选或next全部候选，亦不能把当前已执行dt代作next候选时长。若目标要让每候选时长权重影响actor，则需每个候选的条件期望权重及相关估计误差，或其他经过严格推导、具有正确条件分布和覆盖的采样估计；现有样本并不自动提供这些。即使仅把选中dt放进target某项，也须首先推导它对应的完整随机变量、时间位置和损失，而不是称其为完整按时长熵SAC。除非另获授权且建立相应数据/模型与验证，不建议据此实施。

建议父执行者验证：多mask数量下直接算式、概率归一与masked padding；dt=0/正时长、m=0及N=1情形；固定策略下 `V_KL−V_entropy=−α log N`；actor梯度一致；自动温度若使用则核对符号与完整约束语义；保留初始化偏好和缺失终局链作为独立风险。上述为待执行验收，不是已通过测试。目标选择、变更授权和对照方案由父执行者确认。

## 后续实现只读复核（2026-11-03）

父任务选择固定 α=0.35 的 `relative_uniform` 方案后，复核实现者工作中的 `learning.py`、`entry.py`、`runner.py`、`recovery.py`；此处是代码审阅，不代表测试通过或效果成立。代码以当时未提交工作树为准，父任务负责冻结版本与来源台账。

`learning.py` 把 next target 两个 Q 均减 `α log N(next)`，由于相同常数可交换 min，随后原有 SAC 的 `Σp(Q−α log p)` 就是均匀先验相对熵价值；当前状态 actor 仍按原表达求梯度，因 `α log N(current) Σp=α log N(current)` 不依赖 actor 参数，所以数学梯度相同（实际浮点舍入可有微差），返回的 actor 指标加对应 batch 均值后与完整目标一致。`FixedTemperature` 固定温度且无优化器；目标版本和温度合同不匹配时加载拒绝，旧无版本检查点仅兼容 legacy。正常 train 的两个创建分支经过 `create_learner` 与 config 检查，`verify_learner_checkpoint` 默认工厂继承已有 learner 的 objective。入口仅接受指定 `relative_uniform_trial.json` 路径与严格配置；online-trial 禁止 resume 和非 train phase，恢复能力不能因此被误称为在线试验续训能力。

审阅发现旧辅助脚本 `scripts/task10_recovery_probe.py` 多个工厂与 `scripts/task10_gpu_diagnosis.py` 仍默认 legacy；把新目标检查点传入这些路径会被版本校验拒绝，不能声称所有辅助诊断/恢复工具已兼容。正常 `entry-check` 又仅允许 smoke，使用输入 fixture 自身的 objective；旧 fixture 通过不能证明新目标的真实入口已验证。是否扩大工具兼容由父按授权裁定。此项审阅未运行 GPU、环境采样或更新，必要测试交实现者与父核验。

## 试训后自动评估链只读审查（2026-11-03）

用户已授权一次试训和评估，训练在进行中；只读审查 `scripts/task10_kl_pipeline.py`、`task10_kl_validation.py`、`task10_kl_validation_launch.py` 及复用 validation/audit 路径，不修改生产源代码、不运行 GPU、不采集或更新。观察代码时间约16:55，后续实现者仍在修改时需重新核验。

训练管线没有启动或重启训练的调用；须训练 launcher rc=0，账本 1200决策、200更新、无 in-flight、summary bounded_complete，CPU audit verified 且首更GPU证据成立后才冻结评估。评估启动程序以排他创建 launch 文件及已有 budget 拒绝重复运行；最多一个 actor 策略、12个训练策略场景，按原 expected 筛选并检查6+6场景，逐场景在决策前对比旧初态树哈希，不一致则异常退出。评估外层以单个启动epoch设置5400秒deadline，supervisor/worker共用该epoch并核相等；上限1800决策、12回合、0更新。场景、权重和冻结输入的校验、0更新证据及只读逐决策审计由实现提供，尚未执行真实评估验证。

发现**完整性门不足**：复用 worker 将 `incomplete_budget` 返回进程rc0；报告在无问题但不足12个完成回合时返回 `verified_partial` 且rc0；管线目前只判断进程rc并无条件将自身设为 `complete`。此外 report 计算完整状态未显式要求 worker预算状态 complete、launcher成功及 in-flight=0，异常在最后回合落盘后也可能被误判完整。已立即通知父：最终 complete 必须要求 report `verified_complete`、12完成/无缺失、零更新、budget complete且 in-flight=0、launcher正常退出及相同启动epoch；其余标部分或待审。该发现是代码审查，需实现者修正后重新核验，不能当作实际发生的实验失败。
