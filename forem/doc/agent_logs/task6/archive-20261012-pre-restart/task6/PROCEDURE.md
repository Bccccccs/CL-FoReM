# task6 训练配方对照组 — 详细流程

状态：**§1完成、§2进行中；R3（2026-10-12）把§4起改为对照组流程，§4–§10尚未执行**。执行者：Codex。流程制定与决策：Claude。口径以[TASK](TASK.md)为准，执行者不得自行更改。

## 递归规则声明

本任务遵守根AGENTS的递归三文档规则。本节点以及今后拆出的每个task6.K，都必须各有TASK、PROCEDURE、RESULTS三份文档。当前作为单节点执行，各阶段以本文件的§编号区分。如需委派子Agent（例如sim模式实现、长训监控），先建对应子节点的三文档并在本节登记，再派发；子Agent推荐模型见[TASK](TASK.md#模型与推理强度推荐)。父节点汇总并核验子结果，不能把子Agent自报的完成直接当作通过。

| 阶段 | 内容 | 依赖 | run-id |
|---|---|---|---|
| §1 | 开工与基线冻结 | 无 | — |
| §2 | sim模式实现与回归 | §1 | — |
| §3 | 场景等价性门槛 | §2 | `t6-equiv-r1` |
| §4 | D14对照开关实现与单元测试（R3新增） | §2 | — |
| §5 | 冒烟、profile与并行方案（R3扩展） | §3、§4通过 | `t6-smoke-r1`、`t6-perf-r1` |
| §6 | 启动：F0三种子×100万步优先，随后F1–F6筛选各30万步 | §5通过 | `t6-sim-plain-s{0,1,2}`、`t6-scr-F{1..6}-s0` |
| §7 | F0早期读数与筛选门槛（Claude） | F0到15万/30万步；筛选全部完成 | — |
| §8 | 确认训练：Claude选定的组三种子×100万步 | §7放行 | `t6-conf-F<k>-s{0,1,2}` |
| §9 | 最终评估（sim侧和Gazebo侧） | F0与§8训练完成；Gazebo侧可提前，前提是资源不冲突 | `t6-eval-sim-*`、`t6-eval-gz-s*` |
| §10 | 对照汇总、冻结、交付 | §9 | — |

R3说明：§1–§3原文不变。原§4（冒烟）、§5（正式训练）、§6（最终评估）、§7（汇总）尚无运行证据，按R3并入新的§5、§6、§9、§10；原run-id `t6-smoke-r1`、`t6-sim-plain-s{0,1,2}`、`t6-eval-*`保留原含义。

目录约定：
- 代码放在`forem/scripts/`和`forem/src/`（只新增sim相关内容和D14开关）；筛选协议文件放`forem/config/task6/`。
- 原始日志放在`forem/logs/task6/<run-id>/`。
- 产物放在`forem/results/task6/<run-id>/`。

## §1 开工与基线冻结

1. 先阅读以下资料：根AGENTS（尤其是性能优化共同要求）、本任务三文档、[task4.8 RESULTS](../task4/task4.8/RESULTS.md)、`config/task4_scwm/plain.yaml`、`config/task3/{task_contract,sac}.yaml`、`scripts/scwm_{train,env,sac,eval,instance,supervise}.py`、`scripts/task3_env.py`，以及SRC-0222。
2. 在PROGRESS登记task6；新建日志`forem/doc/agent_logs/task6/YYYYMMDD-codex-task6.md`，写明实际使用的模型和推理强度。
3. 核查运行环境：执行`docker ps`和`nvidia-smi`。task5的A/B运行在`forem-t5-pr2`、`forem-t5-husky`中，只用CPU，**不得触碰**。确认`forem-dev`中没有其他训练在跑。
4. **基线冻结**：读取`results/task4/t4s-plain-s{0,1,2}/run_manifest.json`中的`sources`，即各文件的sha256，与当前工作树逐一比对，生成`results/task6/baseline_source_diff.json`。
   - 若有文件在Task4.8之后被改过（例如feedback相关的修改，`run_manifest.pre_feedback_edit.json`可作参照），须逐一说明该改动是否影响plain路径。
   - 若影响plain路径：停下报告Claude，不得自行回退或修改。

## §2 sim模式实现与回归

只允许以下新增，每项都须给出diff和理由：

1. **sim启动**：新增一个launch文件，例如`forem/src/forem_husky/launch/husky_analytical.launch`。参照Husky快照中的`gazebo_world/husky_ur5/n2m2_husky_analytical.launch`：加载robot_description和SRDF/kinematics，启动`move_group`，设`allow_trajectory_execution=false`，IK求解器用bio_ik。改用forem中的包（`husky_ur5`、`bio_ik`），不启动Gazebo、控制器、costmap、pose_bridge，也不启动gui。
2. **实例管理**：扩展`scwm_instance.py`，或新增一个启动器，使每个种子在独立的ROS master端口上启动上述sim launch。端口和目录隔离方式沿用Task4.8的做法（例如11400+k），并且与Gazebo实例互不冲突。
3. **环境封装的sim分支**：
   - 在`ScwmEnv`和`Task3Env`中增加sim模式。实现方式是通过`overrides`把`world_type`设为`sim`、`init_controllers`设为`false`、`max_close_steps`设为`500`（D12）；不另写一套env。
   - D12（R2修订）：在`modulation/utils.py`中只改两处：①`wrap_in_task`增加显式关键字参数`max_close_steps=None`，为None时保持原来的`50 if analytical else 500`；②`create_env`调用`wrap_in_task`处转发`max_close_steps=config.get("max_close_steps")`。按[拟议patch](../../../results/task6/t6-d12-preflight-r1/proposed_D12.patch)实施并提供实际diff；Gazebo路径不传该键，行为不变。[SRC-0226](../../SOURCES.md#src-0226)
   - sim模式下关闭`scwm_clock`和`pacing`（它们只服务于Gazebo物理时钟）。
   - sim模式下`physical_outcome`返回`{valid: False, success: None, reason: "sim: no physics"}`，不访问任何Gazebo服务。
   - `actual_arm_joints`读取失败时记为None（现有逻辑已是如此）。
   - 不得改变`step`、`reset`的奖励、观测、终止语义。
4. **训练与评估入口**：给`scwm_train.py`、`scwm_eval.py`、`scwm_supervise.py`增加一个`--world sim|gazebo`参数，默认值为`gazebo`。默认值下，Gazebo路径的行为必须与修改前逐字节等价。
5. **回归**：
   - 在`forem-dev`中运行`tests/`下与scwm、task3、task4相关的单元测试，全部通过。
   - 新增sim分支的单元测试：physical记为N/A；不访问Gazebo服务；overrides只改这三个键；sim下`MaxCloseStepsWrapper._max_close_steps == 500`；不传该键时sim为50、gazebo为500（保持原行为）。
   - 生成`results/task6/source_diff_vs_task48.json`，内容是相对Task4.8 sources的全部改动。每处改动都要说明：在`--world gazebo`下不改变行为。

## §3 场景等价性门槛（`t6-equiv-r1`）

- 在sim中，用种子101–110各reset一次，记录`episode_spec`。
- 与`results/task3/t3.5-inst-r1/episode_instances.json`中Gazebo侧的同种子记录比对：
  - 障碍：名称、几何、尺寸、位姿，按小数点后6位取整后完全一致。
  - 目标：`goal_tip`、`goal_wrist`完全一致。
  - 起点：`base_tf`位置差≤0.02 m，yaw差≤0.02 rad。Gazebo中这个值是reset后从TF读到的实际位姿，允许有很小的物理落地偏差。
  - 规划臂初始关节完全一致。
- 先确认Task3那份实例文件与Task4.8所用代码对应的是同一个抽样器，可用`scripts/regress_scwm_instances.py`或与t4s验证记录中的`episode_hash`交叉核对。不确定时如实写明。
- 输出`results/task6/t6-equiv-r1/equivalence.json`。
- **任何一项不一致：停下报告Claude，不得开训。**

## §4 D14对照开关实现与单元测试（R3新增）

1. 按[TASK D14](TASK.md#claude决策-r32026-10-12对照组改造)在`scwm_train.py`、`scwm_sac.py`中新增开关：`update_every_env_steps`（缺省1）、`alpha_rule`（缺省`capped`，即当前规则；可选`rllib`）、`lr_schedule`（缺省`exp_updates`，即当前规则；可选`linear_env_steps`）、`random_warmup_steps`（已有）、`max_close_steps`（D12已有）。
2. 新增`forem/config/task6/screen_F{0..6}.yaml`：由`config/task4_scwm/plain.yaml`复制，F0不改任何训练项，F1–F6只改TASK表中对应项；评估项按D15设置。每个文件头部注明相对`plain.yaml`的差异。
3. 单元测试（`forem-dev`中运行，全部通过才能进入§5）：
   - 缺省开关下，与当前代码相同输入、相同种子做若干次更新，损失、参数、α、学习率逐位一致；
   - `update_every_env_steps=10`：1000环境步内恰好执行100次更新；
   - `alpha_rule=rllib`：初始α=1.0；无上限、不冻结；熵优化器学习率在第0、50万、100万环境步分别为1e-4、约5.05e-5、1e-6；
   - `lr_schedule=linear_env_steps`：actor/critic学习率同上；
   - 完整状态续训：开启各开关时，中断后续训与不中断结果一致（沿用`tests/test_scwm_train_loop.py`的做法）；
   - D15评估不改变`rng_np`、`rng_inst`和replay RNG的状态。
4. 生成`results/task6/d14_diff.json`：逐处diff，说明缺省值下行为不变，并对照B的源码位置（`ray_utils.py::get_sac_conf`、`custom_sac.py`）说明各开关与B的对应关系和已知差异。
5. 开关语义与B的实现无法对齐时（例如RLlib内部的计数方式不同）：停下报告Claude，不自行取舍。

## §5 冒烟、profile与并行方案（`t6-smoke-r1`、`t6-perf-r1`，不计入正式结果）

**冒烟（`t6-smoke-r1`）**：
- 种子0，`--world sim`，F0和F6各跑5000步，D15评估间隔临时设为2500步，cuda:0。
- 确认：训练能走到5000步；评估记录内部成功，physical为N/A；没有任何Gazebo服务调用；checkpoint能保存并用`--resume`恢复一次。

**profile（`t6-perf-r1`）**，按根AGENTS性能优化共同要求：
1. 单条run的分阶段耗时：select、env_step、update、push、reset、评估、checkpoint与replay落盘；F0（每步更新）和F1（每10步更新）各测一次，区分sim时间和墙钟时间。
2. 资源：每条run的CPU核数（含该实例的roscore、move_group等ROS进程）、内存、GPU显存和利用率。
3. 并行打包：在同一GPU上同时跑1、2、3条run（如显存和CPU允许再试4条），测每条run的步/秒和总吞吐；同时测每进程torch/OMP线程数1、2、4的影响。
4. 可选优化逐项实测，**有收益才启用**：CPU亲和、限制库线程数、检查点/replay落盘频率或异步化（不得破坏续训和写前计数）。没有收益、引入乱序或时序问题的不启用，记录原因。
5. 禁止项见TASK D17。
6. 输出`results/task6/t6-perf-r1/perf.json`和RESULTS中的方案：每GPU放几条run、线程设置、启用了哪些优化及前后实测；F0三条×100万步和F1–F6筛选的墙钟估计。
7. CPU预算：本任务与主机其他负载（task5 A/B运行到约今天下午，之后可能有task7）合计持续不超过56核（task5 D11告警线）。task6优先占用资源；方案在预算内就直接进入§6，超出则缩减并行度，不减步数、不改科学条件。

## §6 启动：F0优先，随后筛选

1. **F0三条×100万步（`t6-sim-plain-s{0,1,2}`）先启动**：种子0/1/2，`--world sim`，协议`screen_F0.yaml`（训练项与Task4.8 plain相同），其他参数与Task4.8 plain启动命令逐字相同（见t4s的`run_manifest.json`），GPU与打包按§5方案。
   - 评估：保留Task4.8的5种子验证（每10万步，101–105），另加D15的50种子评估：30万步以内每2.5万步一次，之后每5万步一次。
   - F0-s0的前30万步同时作为筛选的基线，不再另跑F0筛选run。
2. **F1–F6筛选（`t6-scr-F{1..6}-s0`）**：种子0，各30万步，协议`screen_F<k>.yaml`，D15评估每2.5万步一次。在F0启动后按§5方案剩余容量依次启动。
3. 用`scwm_supervise.py`监督。崩溃后从checkpoint续训的机制原样保留，所有重启都要记录。
4. 每30分钟记录各条run的步数、最新评估和资源占用。CPU监控只告警，不得停止训练（同task5 D11）。
5. **早期读数**：F0任一种子到15万步、30万步时，立即把三条F0的D15评估结果写入RESULTS并在PROGRESS记一条，训练不停。
6. 训练过程中如果需要停下，只能停自己启动的进程。

## §7 F0早期读数与筛选门槛（Claude）

- Codex在全部筛选run完成后，输出`results/task6/screening.json`和RESULTS中的筛选表：每组每2.5万步的成功率、到达、IK失败、碰撞、episode长度、回报，以及按D16计算的15万、30万步与F0的差值和95%区间；附B训练中评估曲线作参照（注明口径不同）。
- 然后停下等待Claude决定§8的确认组。F0三条继续运行，不受门槛影响。
- Claude的门槛决定写入RESULTS，作为§8的唯一依据。

## §8 确认训练（`t6-conf-F<k>-s{0,1,2}`）

- 只跑Claude在§7选定的组，每组种子0/1/2，各100万步。
- 种子0可从对应筛选run的30万步完整状态续训到100万步（须使用同一源码hash，续训等价性已由§4测试覆盖）；种子1、2从头训练。
- 评估与监督同§6。

## §9 最终评估

**sim侧（`t6-eval-sim-*`）**：
- 使用F0和§8各条run的`policy_step01000000.pt`。
- 执行`scwm_eval.py --method plain --world sim --seeds 2001,...,2050`，确定性动作；F5相关组须使用其训练时的`max_close_steps`。
- 输出每个种子的内部成功、到达、IK失败、碰撞、步数。

**Gazebo侧（`t6-eval-gz-s{0,1,2}`）**：
- 使用`results/task4/t4s-plain-s{0,1,2}/ckpt/policy_step01000000.pt`。
- 在Gazebo实例中，用同样的50个种子执行`scwm_eval.py --method plain --world gazebo`，确定性动作。同时输出内部成功和物理成功。
- 只评估，不训练。
- 这一侧可以在训练进行中执行，但必须使用独立的实例端口和GPU分配，不得影响sim训练。

**共同要求**：
- 分母固定为50，completed、capped、errored三类都要列出。
- 两侧都确认50个种子抽出的场景一致：比对障碍和目标字段，方法同§3。

## §10 对照汇总、冻结、交付

1. 输出`results/task6/comparison.json`，以及RESULTS中的对照表：
   - 筛选表（§7）；
   - F0与Task4.8逐点对照：每个种子的5种子验证曲线（每10万步，内部成功/5），sim与Gazebo并列；
   - F0和确认组的D15曲线（三种子）；
   - 最终50-episode内部成功率，按组、按种子列出并给出均值；Gazebo侧另列物理成功。
2. 写`results/task6/manifest.json`：源码sha256、diff（sim与D14）、协议文件、命令、GPU/打包方案、起止时间、退出码、重启记录、偏差清单。
3. 新实测论据登记SOURCES。填写RESULTS，状态改为review，更新PROGRESS和日志。不得自行标done。

## 异常处理

以下情况一律停下报告Claude，不自行变通：
- 等价性门槛不通过。
- Gazebo路径回归失败，或D14缺省等价测试失败。
- D14开关语义无法与B的实现对齐。
- 需要修改F1–F6以外的训练参数，或修改奖励、观测、任务才能继续。
- 性能优化需要改变科学条件，或CPU预算下无法完成F0三条加筛选。
- 遇到PROCEDURE没有覆盖、又超出本文件允许范围的问题。

## 模型与推理强度

见[TASK](TASK.md#模型与推理强度推荐)。执行者推荐GPT6.1sol/medium；长训监控子Agent用gpt-6.1-sol/low。只有在sim模式实现或D14开关已记录至少2种不同思路都失败、且原因不明时，才可升到gpt-6-astra/high。
