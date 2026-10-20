# task5.2 Husky原版`main_ray.py` + husky_ur5：sim训练与验证 — 详细流程

状态：**active（正式训练运行；完成/评估/验收待实际结果）**。执行：Codex。流程制定/决策：Claude。冻结口径与允许偏差见[父PROCEDURE](../PROCEDURE.md#两项共同冻结的口径决策执行者不得自行更改)。

## 递归规则声明

本节点遵守根AGENTS的递归三文档规则。本节点以及今后拆出的task5.2.K，都必须各自有TASK、PROCEDURE、RESULTS三份文档。父节点为[task5](../PROCEDURE.md)。如果要把构建适配交给子Agent，先建立`task5.2.1`三文档并在父流程表登记，再派发；推荐模型见[父PROCEDURE](../PROCEDURE.md#子agent派发推荐)。

## 0. 开工

1. 确认[task5.0 RESULTS](../task5.0/RESULTS.md)已通过核验，并从中取得GPU口径与并行结论。
2. 在PROGRESS登记task5.2，并在`forem/doc/agent_logs/task5/task5.2/`下新建日志，写明实际使用的模型和推理强度。

## 1. 构建与环境（已移到task5.0）

以下工作由[task5.0](../task5.0/PROCEDURE.md) §7–§9完成，本节不再重复：容器`forem-t5-husky`；Husky工作区`forem/build/task5/ws_husky`的复制、依赖、补丁和构建；URDF等价性门槛；`RobotHusky`导入；Husky环境就绪检查。

开工前确认以下两点，否则不得开始：

- [task5.0 RESULTS](../task5.0/RESULTS.md)已通过Claude核验，其中URDF等价性和Husky就绪两项都必须通过。
- 本节点使用5.0产出的工作区和补丁清单，不另外构建。如果执行中发现还需要新的构建补丁：停下，在5.0中新开一个run-id补做并登记，再继续。

## 2. 启动ROS与冒烟（run-id `t5.2-smoke-r1`，不计入正式结果）

### 2.1 ROS

Husky的`main_ray.py`没有自动`launch_ros`，因此手动启动：

```bash
roscore &
roslaunch modulation_rl n2m2_husky_analytical.launch gui:=false
```

launch文件位于`gazebo_world/husky_ur5/`。

- 记录各节点和参数（`rosparam get /robot_description_kinematics`），确认`manipulator/kinematics_solver`为bio_ik。
- 上游的`launch_ros`对sim会启动对应的`*_analytical.launch`。这里手动启动的是同类型的Husky版本，属于[允许偏差3](../PROCEDURE.md#允许的偏差只限这些每项都要记录实际值和原因)，须记录在案。

### 2.2 训练冒烟

- 参数改动与5.1 §2.1完全相同：`--total_steps 5000`，调小`--evaluation_frequency`，`--nr_evaluations 2`。命令中使用`--env husky_ur5`。
- 产物放到`/forem_results/t5.2-smoke-r1/`。
- 如果`main_ray.py`的`ray.init(logging_level='ERROR' if debug …)`等与上游不同的行，不影响训练，就保持原样；如有影响，记录下来。

- **D6检查**：冒烟结束后确认：日志中没有`[CLUB Saved]`，`club_checkpoints/`为空，没有CUDA或AttributeError报错。任何一项不满足就停止并报告Claude。
- 在RESULTS里列出生效的`learning_starts`值，以及SimpleObstacleMap实际的spacing/offset_std（预期为3.0/0.8）。

### 2.3 吞吐

记录吞吐，估算100万步所需时长。如果和5.1同时运行，还要记录两者的CPU占用情况。

### 2.4 最终评估冒烟

- 9个任务各跑1–2个episode。
- 记录哪些任务在`husky_ur5`下能运行。跑不了的任务写明报错，不修改任务代码。
- 评估加载方式与5.1相同：用`--model_file`加载本地结构。注意Husky的`evaluation_ray.py`也注释掉了`launch_ros`，所以ROS须手动启动。

**门槛：** task5.0的URDF等价性门槛已通过，且本节§2全部走通，才能进入§3。

## 3. 正式训练（run-id `t5.2-train-s40`）

- 运行冻结命令：`--env husky_ur5 --total_steps 1000000 --seed 40`，其他参数与5.1生效命令逐字相同，`--num_gpus`取task5.0 §5确定的值。
- 后台运行，日志写到`/forem_logs/t5.2-train-s40/train.log`。记录PID和起止时间。
- 生效配置比对：除了`env`，还要列出best_defaults中`husky_ur5`段与`pr2`段的差异。这些值来自Husky快照自带配置（例如`learn_torso: False`），是快照原样的取值，逐项写入`effective_config_check.json`，不得修改。
- 监控、结束、异常处理同5.1 §3。

## 4. 训练中评估提取

同5.1 §4，输出`train_eval_series.csv`。

## 5. 最终评估（run-id `t5.2-eval-r1`）

同5.1 §5：对9个任务逐个调用`evaluation_ray.py`，使用`--env husky_ur5`、最终checkpoint，以及默认的50个episode和`eval_seed 999`。输出`final_eval.csv`。

## 6. 冻结与交接

- 写`forem/results/task5/t5.2-manifest.json`，内容包括：
  - 源码manifest和补丁
  - apt依赖
  - URDF核对结果
  - 命令、退出码
  - 偏差清单
- 填写RESULTS，把状态改为review，并更新PROGRESS和日志。
- 保留容器`forem-t5-husky`，供task5.3复核。

## 模型与推理强度

推荐Codex使用GPT6.1sol/medium。只有满足TASK中的条件时才升到gpt-6-astra/high，理由见[TASK](TASK.md#模型与推理强度)。Claude替代推荐Sonnet5.5/medium。

## R7/D10/D11有效补充（覆盖早先冲突规则）

用户2026-10-11明确授权，Claude R7核验：bookstorepnp不作为B冒烟门槛。r2训练及simpleobstacle/picknplace沿用，r3仅补dynobstacle/picknplacedyn/door/drawer/roomdoor/spline，各1–2episode，加载r2 local_model；八可运行任务链通过即启动B正式。LMS ROS_PACKAGE_PATH沿5.0已就绪路径。
最终bookstorepnp仍调用原版evaluation_ray.py一次，默认50episode/seed999，原版10次reset重试不改，外部墙钟上限1800秒；若失败，记“husky_ur5不可运行（无碰撞起止位姿采样失败）”，成功率N/A，不记0或纳入平均。并列八个可运行任务均值及九任务范围（含N/A与8/9覆盖率；完整九项均值不可计算）。保留pnp两朝向，各50episode，标准非fwdO分支用于任务均值，其他分支单列不合并。不同原因报错仍停止交Claude。
D11：主机CPU每5秒采样，连续5分钟窗口的时间加权均值>56核，只写alert并在日志/RESULTS报告；不停止训练，不更改worker，不因CPU告警取消后续已授权训练流程。依据R7/用户明确指令，新增来源登记SRC0221。
推荐GPT6.1sol/Sonnet5.5 medium（合同/记录核对），监控GPT6.1sol low，实际另记。

## 实际监督子节点

task5.2.1（Codex gpt-6.1-sol/low）：B正式启动后并行监督，依赖r2/r3门槛通过及D10/D11；只自己文档/日志，父汇总，不能以子Agent自报完成验收。[TASK](task5.2.1/TASK.md) · [PROCEDURE](task5.2.1/PROCEDURE.md) · [RESULTS](task5.2.1/RESULTS.md)。推荐Claude替代Sonnet5.5/low或默认。
