# task6.3 sim训练策略的Gazebo零样本迁移 — 任务

> **当前状态（2026-10-19核对）：done（Claude复核R3）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**尚未执行（2026-10-13，文档阶段）**。流程、门槛与复核：Claude。执行：Codex（用户派发；Codex额度不足时可由Claude子Agent临时代行，须在RESULTS注明）。

授权依据（[SRC-0248](../../../SOURCES.md#src-0248)）：用户2026-10-13：“世界模型用task7，然后6里面验证一下sim的训练结果是否可以迁移到gazebo中，配置应该参考原论文项目对gazebo的测试，然后现在6只是验证gazebo为什么失败吧”。

## 研究问题

task6.1已证明：Task4.8的训练器在sim中训练并在sim中评估，内部成功率约0.43；在Gazebo中训练并在Gazebo中评估，约0.05（[SRC-0246](../../../SOURCES.md#src-0246)）。但还没有测过**sim训练的策略放进Gazebo**的表现。

N²M²原文就采用这种方式：在解析环境（sim）中训练，Gazebo只做零样本测试，平均成功率只比sim低0.3–9个百分点（[SRC-0249](../../../SOURCES.md#src-0249)）。SC²-WM也是在Habitat中训练后零样本部署到实机（[SRC-0250](../../../SOURCES.md#src-0250)）。

**本任务问：task6.1的F0策略（sim训练，100万步）零样本放进Gazebo，在原论文项目的Gazebo测试配置下能否保持sim中的成功率？由此判断Task4.8失败是因为“在Gazebo里训练”，还是Gazebo执行本身让同一策略失效。**

## 评估条件

所有条件都只做评估，不训练。策略为`results/task6/t6.1-sim-plain-s{0,1,2}/ckpt/policy_step01000000.pt`；评估种子2001–2050，分母固定50；动作确定性；场景、障碍（Gazebo全矩形）、任务与task6.1 §9 Gazebo侧相同。

|条件|执行设置|作用|
|---|---|---|
|**Z-A（主口径：原论文项目Gazebo测试配置）**|按上游`evaluation_ray.py`的Gazebo评估：`execute_style=track`（**T63-D2：上游对差速底盘实际走direct，见RESULTS“Claude复核R2”，Z-A按direct执行**）、评估IK失败阈值`ik_fail_thresh_eval=50`、`time_step=0.02`、Gazebo自由运行（不固定窗口，`rate.sleep`照上游注释掉）、`max_close_steps=500`（上游Gazebo分支取值）、episode上限100000步（超限计失败，T63-D1）|回答“按原论文方式测试能否迁移”|
|**Z-B（与R-48同口径）**|与task6.1 §9 Gazebo侧完全相同：`execute_style=direct`、`ik_fail_thresh=20`、episode上限2000步，其余同Z-A|与R-48（Task4.8策略，Gazebo训练，0.053）只差训练环境，单因素对照|

上游配置来源见[SRC-0249](../../../SOURCES.md#src-0249)。原论文的Gazebo控制频率约30–70 Hz、异步执行；我们的栈每步约0.015–0.04 s仿真时间，与之同量级。固定0.1 s窗口**不是**原论文协议，本任务不包含。

## 对照与解读

|对照|差异|
|---|---|
|Z-B 对 R-48（task6.1 §9 Gazebo侧）|只差训练环境（sim/Gazebo），评估配置完全相同|
|Z-B 对 F0 sim侧（task6.1 §9，0.433）|同一策略，只差评估执行环境 → 迁移损失|
|Z-A 对 Z-B|同一策略，只差评估配置（track+IK50 对 direct+IK20）|

结果解读（只是解释方法，不预设结论）：

|Z-B|Z-A|解读|
|---|---|---|
|接近sim（损失与N²M²同量级）|—|sim策略能迁移；Task4.8失败主要因为在Gazebo里训练（训练数据/时间语义），不是Gazebo执行让任务不可完成|
|明显低于sim|接近sim|Task3迁移版的Gazebo执行配置（direct、IK20）是主要障碍；原论文配置可用|
|明显低于sim|明显低于sim|Gazebo执行本身让同一策略失效；须进一步拆分执行因素（另行请示）|

“接近”“明显低于”的判定：以三种子均值与sim侧差值及Wilson 95%区间描述；参考N²M²原文损失0.3–9个百分点（外部参考，不作硬门槛）。

## 范围

- **包含**：评估脚本最小改动（新增`--execute_style`、`--ik_fail_thresh`两个可选参数，缺省值不变）及其回归；上游Gazebo评估配置逐项核对；冒烟；Z-A、Z-B各3条评估；内部成功、物理成功、IK失败、碰撞、步数统计；47种子敏感性；汇总与交接。
- **不包括**（需要时另行请示用户）：
  - 任何训练或续训；
  - Task4.8策略在Z-A配置下的评估；
  - 固定0.1 s窗口、观测滞后、底盘加速斜坡等单项执行因素拆分；
  - 修改物理步长（Task3的0.0005 s保持不变；task6.3 §1核实与上游`modulation_tasks.world`的0.0005 s相同，上游0.002 s覆写只用于PR2，见SRC-0251）、奖励、观测、任务；
  - 追查3个场景不一致种子的根因；
  - 世界模型（属于task7）；
  - 修改`husky/`、`mobile-rl/`，干预task6.2的G-B训练。

## 交付与验收

- 上游Gazebo评估配置核对表（每项给上游代码位置、取值、本项目实际取值、一致/偏差）。
- 评估脚本改动的diff、sha256，以及缺省路径与task6.1 §9等价的回归证据。
- Z-A、Z-B各3条`eval.json`（每个episode含`episode_spec`、内部/物理成功、IK失败次数、碰撞、步数、是否capped/errored）；errored留在分母。
- 汇总表：Z-A、Z-B、F0 sim侧、R-48四组并列，50种子主口径加47种子敏感性。
- 按上表给出解读及限制。
- Claude复核通过后才能标done。

## 模型与推理强度推荐

|工作|Codex|Claude|强度与理由|
|---|---|---|---|
|上游配置核对、脚本参数、回归|GPT6.1sol|Sonnet5.5|medium：跨Python/C++核对评估路径的执行语义|
|冒烟、评估执行、汇总|GPT6.1sol|Sonnet5.5|low/默认：步骤明确|
|Claude复核|—|Sonnet5.5|medium|

本文档作者Claude（claude-opus-5-5，推理强度未知）。
