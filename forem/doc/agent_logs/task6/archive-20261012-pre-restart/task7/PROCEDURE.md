# task7 Task5 B改在Gazebo中训练 — 详细流程

状态：**尚未执行**。执行者：Codex。流程制定与决策：Claude。口径以[TASK](TASK.md)为准，执行者不得自行更改。

## 递归规则声明

本任务遵守根AGENTS的递归三文档规则。本节点以及今后拆出的每个task7.K，都必须各有TASK、PROCEDURE、RESULTS三份文档。当前作为单节点执行，各阶段以本文件的§编号区分。如需委派子Agent（例如多实例隔离实现、长训监控），先建对应子节点的三文档并在本节登记，再派发；子Agent推荐模型见[TASK](TASK.md#模型与推理强度推荐)。父节点汇总并核验子结果，不能把子Agent自报的完成直接当作通过。

| 阶段 | 内容 | 依赖 | run-id |
|---|---|---|---|
| §1 | 开工与基线冻结 | 无 | — |
| §2 | 容器、工作区副本、单实例Gazebo就绪 | §1 | `t7-env-r1` |
| §3 | 多实例隔离实现与回归 | §2通过 | `t7-iso-r1` |
| §4 | 冒烟、profile、确定N | §3通过 | `t7-smoke-r1` |
| §5 | 正式训练 | §4通过，且满足资源窗口 | `t7-gz-train-s40` |
| §6 | 最终Gazebo评估 | §5正常结束 | `t7-gz-eval-s40` |
| §7 | 对照汇总、冻结、交付 | §5、§6 | — |

目录约定：
- 构建与代码副本：`forem/build/task7/`（容器内挂载为`/forem_build`）。
- 原始日志：`forem/logs/task7/<run-id>/`。
- 产物：`forem/results/task7/<run-id>/`。

## §1 开工与基线冻结

1. 阅读：根AGENTS（尤其功能范围、SOURCES、性能优化共同要求）、本任务三文档、[task5 TASK/PROCEDURE](../task5/TASK.md)、[task5.2 RESULTS](../task5/task5.2/RESULTS.md)、[task5.3 RESULTS](../task5/task5.3/RESULTS.md)中已批准的偏差、[task4.8.1 RESULTS](../task4/task4.8/task4.8.1/RESULTS.md)（多实例隔离做法）、SRC-0227。
2. 在PROGRESS登记task7；新建日志`forem/doc/agent_logs/task7/YYYYMMDD-codex-task7.md`，写明实际使用的模型和推理强度。
3. 运行环境核查：`docker ps`、`nvidia-smi`、主机CPU与内存。**不得触碰**`forem-t5-pr2`、`forem-t5-husky`（task5）和`forem-dev`（task6可能在用）。
4. 基线冻结：记录`results/task5/t5.2-train-s40/{launch.json,effective_wandb_original_config.json,effective_config_check.json}`的sha256；对`forem/build/task5/ws_husky`生成文件sha256清单`results/task7/baseline_ws_manifest.json`。只读，不得修改task5的任何文件。
5. 列出B中生效的全部task5偏差（D编号、实际值、来源），写入`results/task7/inherited_deviations.json`。

## §2 容器、工作区副本、单实例Gazebo就绪（`t7-env-r1`）

1. 用与task5相同的镜像digest新建容器`forem-t7-husky`（bridge网络）。挂载：`forem/build/task7 → /forem_build`（rw）、`forem/results/task7 → /forem_results`（rw）、`forem/logs/task7 → /forem_logs`（rw）、`husky/src → /ref/husky_src`（ro）、`mobile-rl → /ref/mobile-rl`（ro）。记录完整`docker run`命令。
2. 把`forem/build/task5/ws_husky`及task5.2运行所需依赖（如`/forem_build/deps/lms1xx`）复制到`forem/build/task7/`；复制后sha256清单须与§1基线一致。task5运行中复制只读文件不影响其运行；不得在task5目录下写任何东西。
3. 在新容器中重新构建（或确认复制的devel可直接使用），记录命令和退出码。
4. 单实例Gazebo启动：按Husky快照的Gazebo入口（`modulation/handle_launchfiles.py --env husky_ur5 --pure_analytical no --bioik`，内部为`roslaunch modulation_rl n2m2_husky_empty_world.launch`和move_group），headless，不开gui。**不要调用`launch_ros`**：它在没有检测到ROS时会执行`rosnode kill -a`和`killall -9 gzserver`。
5. 就绪核查：`/gazebo`、`/move_group`、控制器均在；`world_type=gazebo`下创建一个simpleobstacle env，reset 3次、每次随机动作50步，无异常；记录每步墙钟时间、reset耗时。
6. 缺依赖时：只允许安装或构建与Husky快照Gazebo启动直接相关的包，记录来源、版本和原因。**若启动需要改动机器人模型、Gazebo插件、控制器参数、世界文件或env代码：停下报告Claude。**

## §3 多实例隔离实现与回归（`t7-iso-r1`）

1. **实例启动器**：新增`forem/build/task7/scripts/t7_instance.sh`（或Python等价物），实例K（K=0…N，K=N为评估实例）使用：
   - `ROS_MASTER_URI=http://127.0.0.1:(12400+K)`、`GAZEBO_MASTER_URI=http://127.0.0.1:(12500+K)`；
   - `IGN_PARTITION=t7_inst<K>`；
   - 独立`HOME`、`ROS_HOME`、`ROS_LOG_DIR`，放在`forem/logs/task7/<run-id>/inst<K>/`；
   - `ROS_IP=GAZEBO_IP=IGN_IP=127.0.0.1`。
   端口段与Task4.8的11400+K/11500+K错开。做法参照task4.8.1，差异须写明。
2. **worker→实例映射**（T7-D2）：只在`forem/build/task7/ws_husky`副本中修改`modulation/utils.py::env_creator`：
   - 在调用`create_env`之前，根据RLlib传入的`EnvContext.worker_index`（训练worker为1…N）和`node_handle == "eval_env"`（评估worker）确定K，设置上述环境变量。
   - 必须确认在设置环境变量之前，该worker进程中没有任何ROS节点（Python或C++）已初始化；若已初始化，停下报告Claude。
   - 核实driver（local worker）是否创建env：若创建，说明它连接哪个实例，必要时报告Claude决策，不得自行改RLlib配置。
   - 不改`create_env`、env类、奖励、观测、终止，不改`main_ray.py`中除实例映射所需之外的任何内容。
3. **diff**：生成`results/task7/source_diff_vs_task5.json`，逐处说明在`world_type=sim`且未设置实例时行为不变。
4. **隔离回归**（两个实例同时运行）：
   - 两个master的节点集合不相交，各自包含`/gazebo`、`/move_group`；
   - 在实例A上`rosparam set`的参数在B中不可见；
   - 在实例A中驱动机器人移动，实例B中机器人位姿不变（读取`/gazebo/get_model_state`）；
   - 停止实例A不影响实例B；
   - 输出`results/task7/t7-iso-r1/isolation.json`。
5. 任一项不通过：停下报告Claude。

## §4 冒烟、profile、确定N（`t7-smoke-r1`，不计入正式结果）

1. 冒烟：N=2个训练实例+1个评估实例，`--total_steps 5000`，`--evaluation_frequency 2500 --nr_evaluations 2`，其余与正式命令相同。确认：
   - 训练到5000步正常退出，checkpoint保存；
   - 两次训练中评估执行，评估episode在评估实例中运行；
   - 每个worker的机器人只在自己的实例中运动（抽查各实例`/gazebo/get_model_state`或日志）；
   - 无CUDA运行错误，W&B仍为离线。
2. profile：记录每实例CPU（核）和内存、整体环境步/秒、reset耗时占比、update耗时。区分sim时间与墙钟时间。
3. **确定N**：用实测的每实例CPU外推21个实例（20训练+1评估）的总占用，加上主机当前其他负载（task5、task6等）。
   - 若总占用持续≤56核（task5 D11告警线）：N=20，进入§5。
   - 否则：停下报告Claude，给出可行N、对应时长估计和其他方案，不自行减少worker。
4. 估计100万步墙钟时长。注意：B在sim中约17步/秒，CPU上的SAC更新可能本身就是瓶颈；须区分采样受限还是更新受限，不得把线性外推写成承诺。
5. 不做任何性能优化。发现明显瓶颈先报告。

## §5 正式训练（`t7-gz-train-s40`）

1. **资源窗口**：须在task5的A/B训练进程退出后才能启动，除非Claude根据§4的实测明确放行并行。与task6并行时，以CPU合计不超过§4的预算为准。
2. 启动21个实例（N=20时），逐一就绪检查后启动训练。命令与B的`launch.json`逐字相同，只加`--world_type gazebo`并按§4设置`--num_workers`。W&B离线等B已有设置原样沿用。
3. 记录：完整命令、`launch.json`、实际生效配置导出、`effective_config_check.json`（与B逐项对比，只允许world_type、init_controllers、num_workers（若批准）和logpath/group不同）。
4. 监控：每5秒主机CPU、每30分钟进度与最新评估（沿用task5监控脚本的做法），并检查各Gazebo实例存活。CPU只告警，不停止训练（同task5 D11）。
5. 上游代码不支持续训。若训练或任一实例崩溃：保留现场证据，停下报告Claude，不得自动重训或续训，不得自行重启实例接回训练。
6. 只能停止自己启动的进程和容器。

## §6 最终Gazebo评估（`t7-gz-eval-s40`）

1. 训练正常结束且达到100万步后执行。
2. 用最终checkpoint，在Gazebo评估实例中跑simpleobstacle 50 episode：确定性动作，`eval_seed 999`，`transition_noise_base 0`，`ik_fail_thresh`与训练中评估相同（20）。若使用`evaluation_ray.py`，须设置`--eval_execs gazebo`，并核实其`ik_fail_thresh_eval`（默认50）与训练中评估的差异；两种口径都只能如实标注，不得混用。
3. 输出每个episode的成功、到达、IK失败、碰撞、步数，以及汇总。分母固定50，completed、errored分开列出。
4. 不做9任务Gazebo评估。

## §7 对照汇总、冻结、交付

1. `results/task7/comparison.json`及RESULTS中的对照表：
   - task7与task5.2逐评估点（每7.5万步）并列：success、goal_reached、ik_fails、base_collisions、episode_len；
   - 最终评估结果；
   - Task4.8参照列（内部成功/5），注明口径不同、运行栈不同。
2. `results/task7/manifest.json`：镜像digest、容器命令、工作区sha256与diff、实例端口表、命令、起止时间、退出码、偏差清单（继承的task5偏差+本任务新增）。
3. 新实测论据登记SOURCES。填写RESULTS，状态改为review，更新PROGRESS和日志。不得自行标done。

## 异常处理

以下情况一律停下报告Claude，不自行变通：
- Gazebo启动需要改模型、插件、控制器、世界文件或env代码。
- 隔离回归任一项不通过，或worker映射前ROS已初始化。
- CPU预算不允许N=20。
- 训练或实例崩溃。
- 需要修改训练器、超参数、奖励、观测、任务或终止才能继续。
- 遇到本文件没有覆盖、又超出允许范围的问题。

## 模型与推理强度

见[TASK](TASK.md#模型与推理强度推荐)。执行者推荐GPT6.1sol/medium；长训监控子Agent用gpt-6.1-sol/low。只有多实例隔离已记录至少两种不同思路都失败、且原因不明时，才可升到gpt-6-astra/high。
