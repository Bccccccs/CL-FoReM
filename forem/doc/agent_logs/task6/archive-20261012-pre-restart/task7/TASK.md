# task7 Task5 B改在Gazebo中训练：训练配方单因素对照 — 任务

状态：**尚未执行（文档阶段，2026-10-12登记）**。流程制定、决策和复核由Claude负责；执行由Codex负责，用户派发。原计划中“Task7引入世界模型闭环”顺延为task8，本任务不涉及世界模型。

授权依据（[SRC-0227](../../SOURCES.md#src-0227)）：用户2026-10-12原话“我希望把现在的task5 的B的sim换成gazebo然后跑一下，看看是不是除了gazebo其他参数的问题呢”；用户随后选择“N个隔离Gazebo实例”和“新建task7，WM顺延task8”。

## 背景与研究问题

[Task5 B](../task5/task5.2/RESULTS.md)（Husky原版RLlib配方，sim）训练中评估成功率最高约0.82（52.5万步，单种子，50 episode）。[Task4.8 plain](../task4/task4.8/RESULTS.md)（ScwmSAC，Gazebo）100万步时最终验证内部成功0/15。两者除执行环境外，还差训练器、更新频率、α规则、学习率调度、预热、设备、代码版本与运行栈、评估口径（逐项见下文“差异清单”）。

本任务只改一个因素：**沿用Task5 B的代码、训练器、超参数、种子和验证协议，只把`world_type`从`sim`改为`gazebo`**。

**问题**：B的训练配方在Gazebo执行下还能不能学会？
- 能学会（明显高于Task4.8）：Gazebo执行条件本身不是致命因素，Task4.8失败的主因更可能在训练器设置或代码/运行栈。
- 也学不会（接近Task4.8）：Gazebo执行条件是主因，与训练器无关。
- 介于两者之间：如实报告，不强行归类。

不预设结论。它与[task6](../task6/TASK.md)（Task4.8训练器只改到sim）互为镜像；两者合起来是2×2对照：

| | sim | Gazebo |
|---|---|---|
| RLlib配方（Task5 B） | task5.2 | **task7** |
| ScwmSAC（Task4.8） | task6 | task4.8 |

## 差异清单：Task5 B 与 Task4.8 plain

来源：B实际生效配置`results/task5/t5.2-train-s40/effective_wandb_original_config.json`、Husky快照`scripts/main_ray.py`、`modulation/myray/ray_utils.py::get_sac_conf`、`custom_sac.py`；Task4.8的`config/task4_scwm/plain.yaml`、`config/task3/{sac,task_contract}.yaml`、`scripts/scwm_sac.py`、`src/modulation_rl/scripts/sac.py`。逐项来源见SRC-0227。

**A. 随`world_type`一起改变的项（本任务改变这些，属于被测因素）**

|项|sim（B）|Gazebo（task7/Task4.8）|
|---|---|---|
|状态更新|理想积分+IK解|控制器+物理执行，回读底盘实际位姿|
|局部地图|真值floorplan裁剪|前激光costmap|
|碰撞|地图重叠|接触话题|
|reset|直接设置内部状态|`set_model_state`+spawn障碍|
|`MaxCloseStepsWrapper`|50|500（`wrap_in_task`按world_type自动取）|
|`init_controllers`|false|true（`utils.py:250-251`由world_type推出）|

**B. 训练器与算法（本任务保持B的值不变）**

|项|Task5 B / task7|Task4.8 plain|
|---|---|---|
|框架|RLlib `SACTrainerCustom`（`main_ray.py`）|`scwm_train.py`+`ScwmSAC`|
|采样|20个rollout worker并行+1个并行评估worker|单环境串行|
|更新频率|`training_intensity` 0.1：每10环境步1次更新|每环境步1次更新（10倍）|
|随机预热|0（`learning_starts=0`，task5 D7）|1000步|
|α|初值1.0，无上限；熵学习率1e-4|exp(log α)×0.35，≤0.05后冻结；熵学习率1e-6|
|学习率调度|按环境步线性1e-4→1e-6，视界1M|按更新次数指数衰减，视界5000001|
|设备|CPU（`num_gpus 0`）|cuda|
|种子|40（1个）|0/1/2|

**C. 代码与运行栈**：B为Husky快照原版+task5已披露偏差，melodic镜像`dhonerkamp/mobile_rl:11.1-latest`（Gazebo 9，Ray 1.6.0，Torch 1.11.0）；Task4.8为Task3迁移版`forem/src`+`ScwmEnv`包装，noetic `forem-dev`（Gazebo 11，Ray 1.13.0，Torch 2.7.1）。**因此task7与Task4.8之间仍差训练器和代码/运行栈两类，不是单因素；task7只与task5.2构成单因素对照。**

**D. 评估口径**：B训练中评估每7.5万步50 episode、`eval_seed 999`、评估时`transition_noise_base 0`、确定性动作；Task4.8每10万步5个种子（101–105）、确定性动作。成功判据都是`episode_is_success`。

**相同项**：任务simpleobstacle（代码内覆盖为3.0/0.8）、奖励、动作、观测、`transition_noise_base 0.04`、`ik_fail_thresh 20`、网络[512,512,256]+LocalDoubleMapCNN、γ 0.99、τ 0.001、batch 256、buffer 10万、grad_clip 10；`execute_style`两边实际都是`direct`（`main_ray.py`不把该键传入env_config，`create_env`默认`direct`）。

## 对齐口径（执行者不得更改）

- 代码：task5的`forem/build/task5/ws_husky`复制到`forem/build/task7/ws_husky`，只做PROCEDURE §3允许的多实例映射改动。不修改task5的工作区。
- 训练命令：与`results/task5/t5.2-train-s40/launch.json`逐字相同，只改两处：加`--world_type gazebo`；`--num_workers`取PROCEDURE §4确定的N（目标20）。`init_controllers`由代码自动推出。
- 种子40，100万环境步，`training_intensity 0.1`，`--load_best_defaults`，`num_gpus 0`，评估频率75000、50 episode、`eval_seed 999`，均与B相同。
- task5已批准、在B中生效的偏差（D5–D9等，以task5.2 RESULTS为准）原样沿用，逐项列入manifest。

## Claude决策（2026-10-12）

- **T7-D1（终止阈值）**：Gazebo下`MaxCloseStepsWrapper`按代码默认取500，不强制改为50。理由：这是上游代码中world_type自带的一部分，与Task4.8一致；与B（50）的差异作为被测因素的一部分披露。
- **T7-D2（多实例）**：RLlib的`env_creator`不按worker隔离ROS master（`modulation/utils.py:534-541`直接调用`create_env`），所有worker会连到同一个Gazebo、控制同一台机器人。按用户选择，每个rollout worker和评估worker各配一套隔离的ROS/Gazebo实例；只在task7工作区副本中加入“worker→实例”的环境变量映射，不改变env的step/reset/奖励/观测/终止语义。
- **T7-D3（worker数）**：目标N=20，与B相同。若§4实测CPU不允许，停下报告Claude，不自行减少worker。N≠20时作为偏差披露：`training_intensity`固定时，更新与采样之比不变，但每次策略更新之间的采样分布会变化。
- **T7-D4（评估）**：主指标为RLlib训练中评估`evaluation/custom_metrics/success_mean`，口径与B完全相同，可直接逐点对比。最终评估用最终checkpoint在Gazebo中跑simpleobstacle 50 episode（同`eval_seed 999`），见PROCEDURE §6。不做9任务Gazebo评估（Husky其他任务的Gazebo世界未验证，且未授权）。

## 范围

- **包含**：新容器与工作区副本、melodic下Husky Gazebo启动核查、多实例隔离及回归、冒烟与profile、一条100万步正式训练、训练中评估、最终Gazebo评估、与task5.2和Task4.8的对照。
- **不包括**：修改训练器/超参数/奖励/观测/任务/终止；物理成功测量（原版env不提供，需新增代码，未授权）；用B的sim策略做Gazebo零样本评估（未授权）；多种子；世界模型；修改`husky/`、`mobile-rl/`、`forem/src`、task5工作区；干预task5和task6的运行。

## 交付与验收

- 容器、镜像digest、工作区副本sha256清单，以及相对task5工作区的完整diff（只允许多实例映射）。
- 单实例Gazebo就绪证据；多实例隔离回归证据（节点集合不相交、参数不串、一个实例中移动机器人不影响另一个）。
- 冒烟、profile、N的确定依据和100万步时长估计。
- 正式训练的完整配置导出、日志、checkpoint、训练中评估序列。
- 最终Gazebo评估原始记录。
- 对照表：task7与task5.2逐评估点并列（success、goal_reached、ik_fails、base_collisions、episode_len）；Task4.8作参照，注明口径不同。
- 偏差全部披露；由Claude复核后才能标done。单种子结论只用于诊断。

## 模型与推理强度推荐

|工作|Codex|Claude|强度与理由|
|---|---|---|---|
|容器、melodic Gazebo启动与多实例隔离|GPT6.1sol|Sonnet5.5|medium：跨RLlib worker进程、ROS/Gazebo master和容器网络核对因果|
|正式训练与评估执行|GPT6.1sol|Sonnet5.5|medium：按流程执行，注意资源与实例隔离|
|长训监控子Agent|gpt-6.1-sol|Sonnet5.5|low：只读监控，不改配置|
|复核|—|Sonnet5.5|medium|

只有多实例隔离已记录至少两种不同思路都失败、且原因不明时，才允许升级到gpt-6-astra/high，并须写明理由。本文档作者为Claude claude-opus-5-5，推理强度未知。
