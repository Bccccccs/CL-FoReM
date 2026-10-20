# task6.1 ScwmSAC sim组：F0基线与F1–F6训练参数对照 — 任务

> **当前状态（2026-10-19核对）：done（Claude复核R4）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**尚未执行（2026-10-12登记）**。父任务：[task6](../TASK.md)。执行：Codex；决策与复核：Claude。授权依据见父TASK及[SRC-0229](../../../SOURCES.md#src-0229)。

## 目标

1. **F0**：Task4.8的ScwmSAC训练器原样，只把执行环境从Gazebo改为sim，三种子×100万步。回答“同一训练器在sim中能否学会”。
2. **F1–F6**：从F0出发，每组只把一个训练参数换成Task5 B的取值（分组见[父TASK](../TASK.md#对照结构)），各30万步×种子0筛选；Claude门槛后对选定组做三种子×100万步确认。回答“哪个参数导致学不会”。
3. **最终评估**：sim侧评估F0与确认组；Gazebo侧用同样50个种子评估Task4.8保留的最终策略，使R-48与F0的最终比较口径一致。

## 对齐口径（F0与Task4.8 plain相同；F1–F6只改各自那一项，执行者不得更改）

|项|取值（来源）|
|---|---|
|训练入口与算法|`forem/scripts/scwm_train.py --method plain`，使用`ScwmSAC`（逐行复制`sac.py`的`update_parameters`，不带prior）|
|协议|`forem/config/task4_scwm/plain.yaml`原样：100万步、随机预热1000步、每步更新1次、batch 256、replay 10万、学习率衰减视界5000001、训练场景种子范围[1000, 2³⁰)、验证种子101–105、每10万步验证一次、每2万步存checkpoint。各组协议文件见D14|
|SAC超参数|`forem/config/task3/sac.yaml`原样：网络[512,512,256]+LocalDoubleMapCNN、γ 0.99、τ 0.001、α上限0.35、降到0.05后冻结等|
|任务和环境|`forem/config/task3/task_contract.yaml`的env_config原样：simpleobstacle，Husky快照中写死的3.0/0.8，transition_noise 0.04，ik_fail_thresh 20，direct/base等。**只覆盖`world_type: sim`、`init_controllers: false`，另加D12的`max_close_steps: 500`（F5为50）和D20的矩形障碍**|
|代码版本|与Task4.8 plain三条run的`run_manifest.json`中`sources`所列文件逐一比对。只允许新增sim模式所需内容和D14开关|
|运行栈和设备|`forem-dev`容器（torch 2.7.1+cu128），GPU分配按PROCEDURE §5的并行方案|
|种子|F0：训练种子0、1、2；筛选：种子0；确认：0、1、2|

## 沿用的决策D12、D13（原task6 R1/R2）

- **D12（近目标终止阈值）**：上游`wrap_in_task`（`modulation/utils.py:450`）按world_type设置`MaxCloseStepsWrapper`，sim为50，Gazebo为500；当IK slack非零时，达到阈值即done。为了只保留执行方式这一个差异，task6的sim运行**强制设为500**，与Task4.8相同。
  - 实现方式：新增可选env_config键`max_close_steps`，默认None，表示保持原来的按world_type取值；`wrap_in_task`在该键不为None时使用它。task6的sim运行通过overrides传入500。
  - Gazebo路径不传该键，行为逐字节不变。
  - **R2补充（2026-10-12）**：`create_env`是`wrap_in_task`唯一调用点且不转发该键，D12须改两处：`wrap_in_task`增加显式关键字参数`max_close_steps=None`，`create_env`调用处转发`config.get("max_close_steps")`。按[拟议patch](../../../../results/task6/t6-d12-preflight-r1/proposed_D12.patch)实施，依据[SRC-0226](../../../SOURCES.md#src-0226)。
  - 这一点与N²M²原文的sim默认值（50）不同，task5的A/B用的仍是50，比较时须注明。
- **D13（Task4.8历史代码）**：`scwm_train.py`、`scwm_sac.py`在Task4.8期间为加入feedback改过一次，旧版本文本不可恢复（两个文件都不在git中）。
  - 据`logs/task4/t4s-plain-s*/events.jsonl`：s2从头到尾是同一个进程，全程跑旧代码；s0在269k、s1在302k之后续训时才加载新代码。
  - 新代码中plain路径的默认策略仍是`FixedGaussianPolicy`（单tanh），与Task4.8开训时的记录一致（task4.8 RESULTS第13行）。
  - **决定以当前代码作为基线**，不追求恢复旧文本。上述混合历史在对照中如实标注。如果s2与s0/s1的结果没有系统差异，就作为“版本差异影响不大”的旁证，但不作为证明。
  - 依据见[SRC-0224](../../../SOURCES.md#src-0224)。

## 不可避免的差异（就是“执行环境”本身，须全部披露）

- **底盘和机械臂**：sim中不发控制命令，下一状态直接取理想积分和IK解。Gazebo中由控制器加物理引擎执行，再读回实际状态，存在约1步的观测滞后和底盘加速斜坡（[SRC-0161](../../../SOURCES.md#src-0161)）。
- **局部地图**：sim中从真值floorplan裁剪，Gazebo中来自前激光costmap。这是N²M²中sim和gazebo两种world_type的固有设计。
- **碰撞判定**：sim中检查地图是否重叠，Gazebo中读取接触话题。
- **reset**：sim中直接设置内部状态，Gazebo中用set_model_state并spawn障碍。
- **物理成功**：sim中没有物理，物理成功记为N/A。两边统一以**内部成功**（`episode_is_success`）作为共同指标。Task4.8的内部成功记录在`results/task4/t4s-plain-s*/validation_*.json`和`logs/task4/t4s-plain-s*/episodes.jsonl`中。

## 决策D14–D17（原task6 R3）

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
- **D17（性能优化；已由下文D19替代，以D19为准）**：按根AGENTS[性能优化共同要求](../../../../../AGENTS.md#performance-optimization)执行。允许并要求评估的优化：多条run按GPU打包并行、每进程限制库线程数、CPU亲和、检查点/回放落盘频率与异步化（只要不破坏续训和写前计数）。每项须同输入实测收益后才启用，没有收益或引入时序问题的不启用并记录。**禁止**：改变物理/仿真步长、动作时长、观测/奖励/终止、更新语义，以及启用TF32/AMP/非确定性cudnn等会改变数值的设置（除非Claude另行批准）。

## Claude审核R1决策（2026-10-12）：D18回归门槛、D19安全性能优化

依据：[SRC-0230](../../../SOURCES.md#src-0230)（Codex §2回归记录）、[SRC-0232](../../../SOURCES.md#src-0232)。

- **审核结论（§1–§2实现）**：§1 54/54哈希一致。§2改动只在`world=="sim"`分支生效：`fast_reset`、`window_s`、`physical_outcome`按world门控；`scwm_instance`/`scwm_supervise`/`scwm_train`的Gazebo缺省命令、日志目录和manifest键不变（`world`键只在sim时写入）；D12按R2两处实现。scwm 23项回归通过。实现可以接受。
- **D18（§2回归门槛）**：
  1. 放行：在`forem/scripts/audit_task3_core.py`的`OPTIONAL_SOFT_KEYS`中加入`"max_close_steps"`，注释写明“D12可选键，缺省None保持按world_type取值”。这是已批准D12的必要配套，不改变任何运行行为。改后task3回归须全部通过（原有skip除外）。
  2. task4的6项失败（seed101/102视差窗口、六维RPY命令、immutable baseline与330哈希、IMU方向）读取的`results/task4/t4.1-protocol-20261007-r1/`、`t4.3.1-*`目录已在2026-10-11按用户指令清理（[SRC-0202](../../../SOURCES.md#src-0202)），属于已弃用的VIO路线。处理：用§1冻结的`original/`源码在临时副本中重跑这6项，若失败原因与当前完全相同（同一缺失路径），则记为“既有环境失败，与本任务改动无关”，不计入§2门槛；task4其余测试须全部通过。不得删除、skip测试或恢复旧证据。若原始源码下这6项结果不同：停下报告。
- **D19（安全性能优化，替代D17的允许/禁止清单）**：用户要求“加入安全的性能优化”。分三类，**所有启用项都须在§5同输入实测，有收益才用，并对F0–F6及确认训练统一使用**：
  - **一类：数值完全不变，实测有收益即启用**
    - 同一GPU打包多条run（进程级并行）；每进程限制库线程数；训练进程及其ROS/move_group的CPU亲和。
    - 检查点、replay落盘异步化或降频（筛选run可降到每5万步；F0与确认训练保持能从最近检查点续训，写前计数与退出排空不变）。
    - 日志异步写；去掉训练循环中不必要的GPU→CPU同步（只改取值时机，不改数值）。
    - D15评估移出训练进程：在策略快照上用独立sim实例异步评估，训练不暂停。条件：同一checkpoint上异步评估与内联评估的50个episode结果逐项一致（一次核验）；评估不触碰训练的RNG和replay。
  - **二类：只有浮点舍入级差异，须过等价门槛后才能启用**
    - `torch.compile`（默认模式）或CUDA Graph用于`update_parameters`与动作选择；`cudnn.benchmark=True`。
    - 依据：Task4.8沿用cudnn缺省（`deterministic=False`），本身就不能逐位复现，舍入级差异在已有不确定性范围内。
    - 等价门槛（工程选择）：保持fp32，TF32开关维持当前缺省（matmul False、cudnn True，2026-10-12实测）不改；同一初始状态和同一串256批数据连续200次更新，各步损失和最终参数的最大相对差≤1e-4，确定性动作最大绝对差≤1e-5；端到端（含env、评估、落盘）提速≥15%才启用。任一项不满足就不启用，记录原因。
  - **三类：禁止**
    - AMP/bf16/fp16；改动TF32开关；改batch、更新次数、网络结构、replay内容。
    - 改sim步长、动作时长、IK求解器参数、观测、奖励、终止。
    - 减少评估种子或episode，跳过评估。

## Claude审核R2决策（2026-10-12）：D20障碍几何

依据：[SRC-0233](../../../SOURCES.md#src-0233)（Codex §3记录）、[SRC-0235](../../../SOURCES.md#src-0235)。

- **审核结论**：§3门槛按设计正确地拦下了一个真实差异。上游`modulation/envs/map.py` L871–876（SimpleObstacleMap）中，障碍几何的条件是`(np_random.random() < 0.5) or world_type == "gazebo" or fake_gazebo`：Gazebo里全部是矩形；sim里约一半是椭圆柱（101–110共160个障碍中78个不同，约49%）。因为`random()`是第一个操作数、总会被调用，两种world的随机数消耗相同，所以位置、尺寸、目标、起点都一致，只有几何不同。这是上游按world_type自带的差异，与D12的终止阈值同类。`fake_gazebo`会切换到`GazeboAPI`，需要Gazebo，不能用于纯sim。
- **意义**：Task5 B（sim）训练时约一半障碍是椭圆柱，占地小于同尺寸矩形；Task4.8（Gazebo）全是矩形。这是此前未识别的R-B与R-48之间的任务差异，已登记到父TASK。
- **D20（sim中强制矩形障碍）**：为使F0与Task4.8的场景逐项一致（与D12同一原则），task6.1的所有sim运行（F0–F6、确认、sim侧最终评估）都强制矩形。
  - 实现：仿照上游`/fake_gazebo`的做法，在`Map.__init__`中读取ROS参数`/forem/force_rectangle_obstacles`（缺省False），并把SimpleObstacleMap的条件改为`(self.np_random.random() < 0.5) or (self._world_type == "gazebo") or self.fake_gazebo or self.force_rectangle_obstacles`。**`random()`必须保持为第一个操作数**，保证随机数消耗不变。
  - ScwmEnv的sim分支在创建env之前，在本实例的master上设置该参数为True，并写入manifest。Gazebo路径不设置该参数，行为不变；Gazebo运行启动时须断言该参数不存在或为False。
  - 单元测试：同一种子下，开关开与关时障碍的位置、尺寸、目标、起点以及采样后的RNG状态逐位相同，只有几何不同；不设参数时sim仍为约一半椭圆柱（与原行为一致）。
  - 用新run-id `t6.1-equiv-r2`重做§3，几何项须10/10一致。
- **限制**：F1–F6和F6正对照因此都在全矩形场景中进行，与R-B（task5.2，约一半椭圆柱）的场景不同；与R-B的数值对照须注明这一差异。

## 评估对齐

1. **筛选阶段（F1–F6，以及F0-s0的前30万步）**：按D15，每2.5万步、50个固定种子（3001–3050）。
2. **F0与确认阶段**：保留Task4.8的5种子验证（每10万步，101–105），另加D15的50种子评估（30万步以内每2.5万步一次，之后每5万步一次）。
3. **最终评估（两边口径一致）**：用最终策略，以确定性动作，在50个固定种子（2001–2050）上各跑1个episode，统计内部成功率。
   - sim侧：F0三条和确认阶段各条run的最终策略。
   - Gazebo侧：在Gazebo中用同样50个种子，评估Task4.8 plain保留的`results/task4/t4s-plain-s{0,1,2}/ckpt/policy_step01000000.pt`。只评估，不训练，物理成功也一并记录。

## 范围

- **包含**：sim模式（启动脚本、环境封装sim分支，不改变Gazebo路径行为）；场景等价性门槛和回归测试；D14对照开关（缺省等价）及单元测试；冒烟、profile和并行方案（D17）；F0三种子×100万步；F1–F6筛选；Claude门槛后的确认训练；两侧最终评估；本节点汇总。
- **不包括**：F1–F6以外的训练参数改动及两两组合；修改奖励、观测、任务（F5的终止阈值除外）；模拟20 worker并行采样或替换为Husky原版代码；feedback或世界模型；新的Gazebo训练；修改`husky/`、`mobile-rl/`；干预task5、task6.2的运行。

## 交付与验收

- sim模式实现及回归：Gazebo路径回归通过；相对Task4.8 plain的源码hash差异清单中只有sim相关内容和D14开关。
- D14开关单元测试：缺省时与当前代码逐位一致；每个开关的数学行为与B的实现对照一致。
- 场景等价性门槛：同一seed下，sim和Gazebo抽出的episode在障碍、起点、目标上一致，容差见PROCEDURE。不一致就不开训。
- 冒烟结果、profile（含F0与F1两种更新负载）、并行方案及其实测依据、时长估计。
- F0早期读数（15万、30万步）；筛选7组曲线与表；Claude门槛记录。
- F0与确认阶段各条训练的manifest、progress、episodes、验证记录和checkpoint。
- 两侧最终评估的原始记录和汇总。
- 由Claude复核后才能标done。

## 模型与推理强度推荐

|工作|Codex|Claude|强度与理由|
|---|---|---|---|
|sim模式实现、等价性和回归门槛|GPT6.1sol|Sonnet5.5|medium：要跨环境封装、ROS启动和场景抽样核对因果|
|D14对照开关实现与单元测试|GPT6.1sol|Sonnet5.5|medium：需逐项对照RLlib与ScwmSAC的α/学习率/更新语义|
|profile与并行方案|GPT6.1sol|Sonnet5.5|medium：需区分CPU/GPU/IO瓶颈并实测验证|
|训练与评估执行|GPT6.1sol|Sonnet5.5|medium：按流程执行，注意并行资源隔离|
|长训监控子Agent|gpt-6.1-sol|Sonnet5.5|low：只读监控，不改配置|
|复核与门槛决策|—|Sonnet5.5|medium|

只有当sim模式实现或D14开关已记录至少两种不同思路都失败、且原因不明时，才允许升级到gpt-6-astra/high，并须写明理由。本文档作者为Claude claude-opus-5-5，推理强度未知。
