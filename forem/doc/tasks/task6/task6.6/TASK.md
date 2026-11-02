# task6.6 评估CBL自己的检查点（sim与Gazebo）— 任务

状态：**done（2026-10-27，Claude子Agent Sonnet5.5执行，Claude复核通过；结果见[RESULTS](RESULTS.md)）**。流程、门槛与复核：Claude。

授权依据（[SRC-1241](../../../SOURCES.md#src-1241)）：用户2026-10-27：“建任务：用我们的sim和Gazebo评估协议（50回合）评估CBL自己的checkpoints_simpleobstacle和pnp_plus 4000，同时把no_grad的发现登记到SOURCES并更正SRC-0200”。no_grad发现与更正已由Claude在建档时完成（[SRC-1240](../../../SOURCES.md#src-1240)），不属于执行者范围。

## 研究问题

阶段一里，cbl自写SAC这条线只有我们自己的复现结果：F0（1M）sim 0.433、Gazebo 0.160（Z-B）/0.200（Z-A）（[task6.3](../task6.3/RESULTS.md)），task5.5（5M）sim 0.633（[task5.5](../../task5/task5.5/RESULTS.md)）。CBL自己的训练只留下损坏的TensorBoard和未评估过的检查点（[archive核查](../../../agent_logs/project/20261016-claude-cbl-archive-audit.md)），所以一直没有“CBL实际达到的水平”可以对照。

**本任务问：CBL自己留下的检查点，在我们的sim和Gazebo评估协议下成功率是多少？与我们复现的F0/task5.5相比如何？CBL的策略在Gazebo中是否也有类似的大幅损失？**

## 被评估的策略

全部来自cbl上传的`archive/husky_ur5/mm_husky_ws/src/modulation_rl/scripts/`（只读），哈希见`forem/results/task6/t6.6-precheck/archive_sha256.txt`：

|标签|文件|说明|
|---|---|---|
|so01–so14|`checkpoints_simpleobstacle/sac_checkpoint_husky_ur5_{1000…14000}`（14个）|编号推测为episode数；so01约19.8万次更新、so14约330万次（[SRC-1242](../../../SOURCES.md#src-1242)）|
|pp4000|`checkpoints_pnp_plus/sac_checkpoint_husky_ur5_4000`|`main.py`使用的prior；约410万次更新；训练任务未知|

`checkpoints/`下的1000/2000/4000与pp4000策略逐位相同（no_grad bug，[SRC-1240](../../../SOURCES.md#src-1240)），不另评。

## 评估条件

所有条件都只做评估，不训练。种子2001–2050，每种子1回合，分母固定50，确定性动作。场景、任务、障碍设置与task6.1 §9、task6.3完全相同，可与F0、task5.5逐种子配对。

|条件|设置|对照|
|---|---|---|
|**S（sim）**|`eval_task6_final.py --world sim`，`max_close_steps 500`，`max_steps 2000`，强制矩形障碍（D20）|F0 0.433（21/22/22）；task5.5 5M 0.633（32/33/30）|
|**Z-B（Gazebo主口径）**|`--world gazebo`，`execute_style direct`、`ik_fail_thresh 20`、`max_steps 2000`|F0 Z-B 0.160（7/10/7）；R-48 0.053|
|**Z-A（Gazebo原论文配置）**|`direct`、`ik_fail_thresh 50`、`max_steps 100000`，超限记capped并计为失败|F0 Z-A 0.200（8/13/9）|

**动作映射（T66-D1，[SRC-1242](../../../SOURCES.md#src-1242)）**：CBL训练与评估都用参考`GaussianPolicy.predict`，执行的是`tanh(tanh(g))`（双tanh）；FoReM的`FixedGaussianPolicy`是单tanh。主口径用参考类（确定性动作`tanh(tanh(mean))`），复现CBL实际执行的行为。单tanh口径会改变动作语义，**不纳入本任务**，需要时另行请示用户。

## 对照与解读（只是解释方法，不预设结论）

|观察|解读|
|---|---|
|CBL最好的so检查点在S下与task5.5 5M相近|我们的自写SAC复现在sim中达到了CBL自己的水平|
|CBL明显高于task5.5/F0|我们的迁移链路或训练与CBL存在差异，需另行排查（不在本任务）|
|CBL明显低于task5.5|CBL自己的训练并不比我们的复现好；差距来源不在本任务内追查|
|CBL在Z-B/Z-A也大幅低于S|Gazebo损失不是我们自己训练造成的，同一类策略都有|
|CBL在Gazebo接近S|CBL的策略比我们的F0更能迁移，需另行查原因|

“相近/明显”以50回合Wilson 95%区间描述，单检查点、无训练种子重复，只做描述性比较，不做显著性结论。so01–so14的曲线只说明这一条训练轨迹，不能代表CBL方法的方差。

## 范围

- **包含**：把15个检查点复制到`forem/results/task6/t6.6-ckpt/`并核对哈希、抽取`policy_state_dict`；`eval_task6_final.py`新增一个缺省不变的`--policy-class {fixed,reference}`及其回归；冒烟；15个策略×S/Z-B/Z-A共45条评估；汇总、配对比较与交接。
- **不包括**（需要时另行请示用户）：任何训练、续训或微调；单tanh口径；picknplace等其他任务；`checkpoints/`、`checkpoints_pnp/`等其他目录；修改C++、环境、奖励、观测、障碍设置或物理步长；追查差异原因；修改`archive/`、`husky/`。

## 交付与验收

- 15个检查点的复制、哈希核对与抽取记录（每个策略文件sha256、优化器step）。
- 评估脚本diff、sha256，缺省路径与改动前等价的回归证据，参考类动作|a|≤tanh(1)的检查。
- 45份`eval.json`（每回合含episode_spec、内部/物理成功、IK失败、碰撞、步数、capped/errored），errored留在分母。
- 汇总表：15个策略在S/Z-B/Z-A的内部成功/50（Wilson 95%）、物理成功、IK失败终止、碰撞、平均步数；与F0、task5.5、R-48并列；与F0/task5.5逐种子配对（场景哈希一致的种子）。
- 按上表给出解读及限制。Claude复核通过后才能标done。

## 模型与推理强度推荐

|工作|Codex|Claude|强度与理由|
|---|---|---|---|
|检查点抽取、脚本参数与回归|GPT6.1sol|Sonnet5.5|medium：要核对策略类、加载与动作映射的语义|
|冒烟、45条评估、汇总|GPT6.1sol|Sonnet5.5|low/默认：步骤明确|
|Claude复核|—|Sonnet5.5|medium|

本文档作者Claude（claude-opus-5-5，推理强度未知）。
