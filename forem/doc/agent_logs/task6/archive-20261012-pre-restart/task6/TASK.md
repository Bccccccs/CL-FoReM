# task6 训练配方对照组：排查Task4.8与Task5 B之间的失败因素 — 任务

状态：**active（2026-10-12 R3改造为对照组；§1已完成、§2进行中；对照部分尚未执行）**。流程制定、决策和复核由Claude负责；执行由Codex负责，用户派发。

授权依据：
- 原单因素对照：用户2026-10-12“先让两边除了执行环境外的条件一致，然后尝试训练吧”“继续去写吧”（[SRC-0222](../../SOURCES.md#src-0222)）。
- **R3改造**：用户2026-10-12“我们要不把task6做成一个大的对照组排查4.8和5中间的问题，究竟哪个训练参数导致了4.8的失败”，以及“现在改造6 把6做成一个大对照组……15w步就可以让4.8拉开比较大的差距，我们可以测试一下不同参数对训练的影响，然后注意要尽可能性能优化”；筛选预算选择“30万步×1种子”（[SRC-0228](../../SOURCES.md#src-0228)）。

## 背景与研究问题

[Task5 B](../task5/task5.2/RESULTS.md)（Husky原版RLlib配方，sim）训练中评估成功率15万步0.52、22.5万步0.68、52.5万步0.82（单种子，50 episode）。[Task4.8 plain](../task4/task4.8/RESULTS.md)（ScwmSAC，Gazebo）100万步最终验证内部成功0/15。两者之间的全部差异见[task7 TASK差异清单](../task7/TASK.md#差异清单task5-b-与-task48-plain)。

已有线索（只作提示，不作结论）：
- Task4.8三个种子的最终α完全相同（log α=−1.0076，α≈0.128）。熵学习率仅1e-6，100万次更新约使log α下降1.0，说明α实际按固定速率下降，自动调节没有起作用。B的α从0.99降到0.25（15万步）、0.015（60万步）。[SRC-0228](../../SOURCES.md#src-0228)
- `sac.py`中注释掉的原行显示Husky作者把熵学习率从`lr_start`改为`lr_start*0.01`并加了α上限（“限制alpha时使用”）；RLlib路径（B）没有这项改动。
- B在α≈0.25时成功率已到0.52，Task4.8在相近α时仍接近0，所以α可能不是唯一原因；更新频率（Task4.8是B的10倍）同样可疑。

本任务分两层回答：

1. **执行环境层（基线F0，即原task6）**：Task4.8训练器原样只把`world_type`改为`sim`。
   - F0在sim中能学会：Task4.8失败的主因是Gazebo执行条件，训练参数对照只说明哪些参数影响学习速度。
   - F0在sim中也学不会：主因在训练参数或代码，由第二层定位。
2. **训练参数层（R3新增）**：从F0出发，每组只把一个参数换成B的取值，看哪个能“救活”训练；另设全部换成B取值的正对照F6。

| 组 | 相对F0的唯一改动（取B的值） |
|---|---|
| F0 | 无（Task4.8 plain原样，sim） |
| F1 | 更新频率：每1环境步1次 → 每10环境步1次 |
| F2 | α规则：初值1.0、无上限、不冻结、熵学习率1e-4且按环境步线性降至1e-6（视界100万） |
| F3 | actor/critic学习率调度：按环境步线性1e-4→1e-6（视界100万） |
| F4 | 随机预热：1000步 → 0 |
| F5 | 近目标终止阈值`max_close_steps`：500 → 50（B在sim中的值） |
| F6 | 正对照：F1–F5全部换上 |

- F6仍学不会：剩余差异是20 worker并行采样和代码版本（Task3迁移版与Husky原版），由Claude另行设计下一步，本任务不自行扩展。
- 交互作用：筛选只测单因素和全组合；若单因素都救不活而F6能救活，由Claude根据结果决定是否追加两两组合（须用户同意）。

不预设结论。

## 对齐口径（F0基线与Task4.8 plain相同；F1–F6只改各自那一项，执行者不得更改）

|项|取值（来源）|
|---|---|
|训练入口与算法|`forem/scripts/scwm_train.py --method plain`，使用`ScwmSAC`（逐行复制`sac.py`的`update_parameters`，不带prior）|
|协议|`forem/config/task4_scwm/plain.yaml`原样：100万步、随机预热1000步、每步更新1次、batch 256、replay 10万、学习率衰减视界5000001、训练场景种子范围[1000, 2³⁰)、验证种子101–105、每10万步验证一次、每2万步存checkpoint|
|SAC超参数|`forem/config/task3/sac.yaml`原样：网络[512,512,256]+LocalDoubleMapCNN、γ 0.99、τ 0.001、α上限0.35、降到0.05后冻结等|
|任务和环境|`forem/config/task3/task_contract.yaml`的env_config原样：simpleobstacle，Husky快照中写死的3.0/0.8，transition_noise 0.04，ik_fail_thresh 20，direct/base等。**只覆盖`world_type: sim`、`init_controllers: false`，另加D12要求的`max_close_steps: 500`（使近目标终止阈值与Task4.8 Gazebo相同，见下文“Claude决策”）**|
|代码版本|与Task4.8 plain三条run的`run_manifest.json`中`sources`所列文件逐一比对。只允许新增sim模式所需的文件或分支，见PROCEDURE §2|
|运行栈和设备|`forem-dev`容器（torch 2.7.1+cu128）。种子0/1/2分别用cuda:0/1/2，与Task4.8相同|
|种子|训练种子0、1、2，三条全跑，与Task4.8 plain相同|

## Claude决策（2026-10-12，§1预检后）

- **D12（近目标终止阈值）**：上游`wrap_in_task`（`modulation/utils.py:450`）按world_type设置`MaxCloseStepsWrapper`，sim为50，Gazebo为500；当IK slack非零时，达到阈值即done。为了只保留执行方式这一个差异，task6的sim运行**强制设为500**，与Task4.8相同。
  - 实现方式：新增可选env_config键`max_close_steps`，默认None，表示保持原来的按world_type取值；`wrap_in_task`在该键不为None时使用它。task6的sim运行通过overrides传入500。
  - Gazebo路径不传该键，行为逐字节不变。
  - **R2补充（2026-10-12）**：`create_env`是`wrap_in_task`唯一调用点且不转发该键，D12须改两处：`wrap_in_task`增加显式关键字参数`max_close_steps=None`，`create_env`调用处转发`config.get("max_close_steps")`。按[拟议patch](../../../results/task6/t6-d12-preflight-r1/proposed_D12.patch)实施，依据[SRC-0226](../../SOURCES.md#src-0226)。
  - 这一点与N²M²原文的sim默认值（50）不同，task5的A/B用的仍是50，比较时须注明。
- **D13（Task4.8历史代码）**：`scwm_train.py`、`scwm_sac.py`在Task4.8期间为加入feedback改过一次，旧版本文本不可恢复（两个文件都不在git中）。
  - 据`logs/task4/t4s-plain-s*/events.jsonl`：s2从头到尾是同一个进程，全程跑旧代码；s0在269k、s1在302k之后续训时才加载新代码。
  - 新代码中plain路径的默认策略仍是`FixedGaussianPolicy`（单tanh），与Task4.8开训时的记录一致（task4.8 RESULTS第13行）。
  - **决定以当前代码作为基线**，不追求恢复旧文本。上述混合历史在对照中如实标注。如果s2与s0/s1的结果没有系统差异，就作为“版本差异影响不大”的旁证，但不作为证明。
  - 依据见[SRC-0224](../../SOURCES.md#src-0224)。

## 不可避免的差异（就是“执行环境”本身，须全部披露）

- **底盘和机械臂**：sim中不发控制命令，下一状态直接取理想积分和IK解。Gazebo中由控制器加物理引擎执行，再读回实际状态，存在约1步的观测滞后和底盘加速斜坡（[SRC-0161](../../SOURCES.md#src-0161)）。
- **局部地图**：sim中从真值floorplan裁剪，Gazebo中来自前激光costmap。这是N²M²中sim和gazebo两种world_type的固有设计。
- **碰撞判定**：sim中检查地图是否重叠，Gazebo中读取接触话题。
- **reset**：sim中直接设置内部状态，Gazebo中用set_model_state并spawn障碍。
- **物理成功**：sim中没有物理，物理成功记为N/A。两边统一以**内部成功**（`episode_is_success`）作为共同指标。Task4.8的内部成功记录在`results/task4/t4s-plain-s*/validation_*.json`和`logs/task4/t4s-plain-s*/episodes.jsonl`中。

## Claude决策 R3（2026-10-12，对照组改造）

- **D14（对照开关）**：在`scwm_train.py`/`scwm_sac.py`中新增F1–F5所需的配置开关，**缺省值必须与当前Task4.8行为逐字节等价**（F0即缺省）。每组用一个协议文件`forem/config/task6/screen_F<k>.yaml`，由`plain.yaml`复制后只改对应项。各开关的精确语义：
  - F1：`update_every_env_steps: 10`，每满10个环境步执行1次`update_parameters`（batch 256不变）；学习率调度的计数方式随F3决定，F1单独开启时仍按更新次数计。
  - F2：`alpha_rule: rllib`——`log_alpha`初值0（α=1.0），α=exp(log α)，无上限、不冻结；熵优化器Adam初始学习率1e-4，按环境步线性降至1e-6，视界1,000,000环境步；目标熵仍为−3。依据`ray_utils.py::get_sac_conf`与`custom_sac.py`。
  - F3：`lr_schedule: linear_env_steps`——actor和critic学习率按环境步从1e-4线性降至1e-6，视界1,000,000环境步。
  - F4：`random_warmup_steps: 0`；回放中样本不足一个batch时不更新。
  - F5：通过D12已有的`max_close_steps`键传入50。
  - F6：上述五项同时开启。
  - 筛选只跑30万步，但F2/F3的视界仍按100万步，使前30万步与B的调度完全相同。
- **D15（筛选评估）**：Task4.8的5种子验证太稀、太少，不足以区分各组。筛选阶段改为每2.5万环境步在固定的50个种子（3001–3050，与训练种子范围、最终评估种子2001–2050都不重叠）上各跑1个确定性episode，记录内部成功、到达、IK失败、碰撞、步数、回报。评估不得消耗训练用的随机数状态（`rng_np`、`rng_inst`、replay RNG），须用单元测试证明。原Task4.8的5种子验证在F0确认训练中保留，以便与Task4.8逐点对照。
- **D16（判定方式，工程选择）**：筛选在15万步和30万步两个读数上，比较各组与F0的成功率（各50个episode），用两比例差的95%置信区间（Newcombe法）判断差异是否明显。这只是单种子筛选的工程判据，不是统计结论；进入确认阶段的组由Claude根据完整曲线决定。
- **D17（性能优化）**：按根AGENTS[性能优化共同要求](../../../../AGENTS.md#performance-optimization)执行。允许并要求评估的优化：多条run按GPU打包并行、每进程限制库线程数、CPU亲和、检查点/回放落盘频率与异步化（只要不破坏续训和写前计数）。每项须同输入实测收益后才启用，没有收益或引入时序问题的不启用并记录。**禁止**：改变物理/仿真步长、动作时长、观测/奖励/终止、更新语义，以及启用TF32/AMP/非确定性cudnn等会改变数值的设置（除非Claude另行批准）。

## 评估对齐

1. **筛选阶段（F0–F6）**：按D15，每2.5万步、50个固定种子。
2. **确认阶段训练中验证**：与Task4.8完全相同，每10万步在种子101–105上各跑1个episode；另加D15的50种子评估（每5万步一次，以控制开销）。
3. **最终评估（两边口径一致）**：用最终策略，以确定性动作，在50个固定种子（2001–2050）上各跑1个episode，统计内部成功率。
   - sim侧：评估确认阶段各条run的最终策略。
   - Gazebo侧：在Gazebo中用同样50个种子，评估Task4.8 plain保留下来的`results/task4/t4s-plain-s{0,1,2}/ckpt/policy_step01000000.pt`。只评估，不训练，物理成功也一并记录。
   - 这样最终比较的两边是同样的种子、同样的episode数、同样的指标。

## 范围

- **包含**：
  - 为forem现有代码新增sim模式（启动脚本、环境封装中的sim分支），不改变Gazebo路径的行为。
  - 场景等价性门槛和回归测试。
  - D14对照开关（缺省等价）及其单元测试。
  - 冒烟、性能profile和并行方案（D17）。
  - 筛选：F0–F6各30万步×种子0，共7条。
  - Claude门槛后的确认：F0三个种子×100万步（即原task6正式训练），以及Claude选定的组三个种子×100万步。
  - 训练中验证、两侧最终评估、对照分析。
- **不包括**：
  - F1–F6以外的训练参数改动，两两组合（须Claude提议、用户同意后另加）。
  - 修改奖励、观测、任务（F5的终止阈值除外）。
  - 模拟20 worker并行采样，或替换为Husky原版代码。
  - feedback或世界模型方法。
  - 新的Gazebo训练。
  - 修改`husky/`、`mobile-rl/`。
  - 干预task5、task7的运行。

## 交付与验收

- sim模式实现及回归：Gazebo路径回归通过；相对Task4.8 plain的源码hash差异清单中只有sim相关内容和D14开关。
- D14开关单元测试：缺省时与当前代码逐位一致；每个开关的数学行为与B的实现对照一致。
- 场景等价性门槛：同一seed下，sim和Gazebo抽出的episode在障碍、起点、目标上一致，容差见PROCEDURE。不一致就不开训。
- 冒烟结果、profile（含F0与F1两种更新负载）、并行方案及其实测依据，筛选和确认阶段的时长估计。
- 筛选7条run的原始记录和曲线；Claude门槛记录。
- 确认阶段各条训练的manifest、progress、episodes、验证记录和checkpoint。
- 两侧最终评估的原始记录和汇总。
- 对照表：筛选曲线（7组并列，B的曲线作参照、注明口径不同）；确认阶段每个种子的验证曲线和最终50-episode内部成功率，sim与Gazebo并列。
- 由Claude复核后才能标done。单种子筛选和三种子确认的结论都只用于诊断。

## 模型与推理强度推荐

|工作|Codex|Claude|强度与理由|
|---|---|---|---|
|sim模式实现、等价性和回归门槛|GPT6.1sol|Sonnet5.5|medium：要跨环境封装、ROS启动和场景抽样核对因果，不需要Astra|
|D14对照开关实现与单元测试|GPT6.1sol|Sonnet5.5|medium：需逐项对照RLlib与ScwmSAC的α/学习率/更新语义|
|profile与并行方案|GPT6.1sol|Sonnet5.5|medium：需区分CPU/GPU/IO瓶颈并实测验证|
|筛选与确认训练执行|GPT6.1sol|Sonnet5.5|medium：按流程执行，注意并行资源隔离|
|长训监控子Agent|gpt-6.1-sol|Sonnet5.5|low：只读监控，不改配置|
|复核与门槛决策|—|Sonnet5.5|medium|

只有当sim模式实现或D14开关已记录至少两种不同思路都失败、且原因不明时，才允许升级到gpt-6-astra/high，并须写明理由。本文档作者为Claude claude-opus-5-5，推理强度未知。
