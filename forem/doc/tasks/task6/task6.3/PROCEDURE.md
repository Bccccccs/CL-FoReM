# task6.3 sim训练策略的Gazebo零样本迁移 — 详细流程

状态：**尚未执行（2026-10-13）**。目标、范围、验收见[TASK](TASK.md)；结果填写在[RESULTS](RESULTS.md)。

## 递归规则声明

本节点遵守根AGENTS的递归三文档规则：task6.3及今后拆出的task6.3.M都必须各有TASK、PROCEDURE、RESULTS三份文档。父节点[task6](../PROCEDURE.md)负责顺序、依赖与汇总；本节点结果以本RESULTS为准。执行者只更新本节点文档和自己的日志`agent_logs/task6/task6.3/`；父RESULTS、PROGRESS、SOURCES的汇总条目由Claude维护（执行者可追加自己产生证据的SRC条目）。执行者自报完成不能当作通过，须经Claude复核。当前无子节点。

## 输入与依赖

- 策略：`results/task6/t6.1-sim-plain-s{0,1,2}/ckpt/policy_step01000000.pt`（task6.1 done，R4复核）。
- 评估脚本：`scripts/eval_task6_final.py`；task6.1的启动方式见`logs/task6/t6.1-eval-launch/eval_one.sh`。
- 对照数据：task6.1 §9的`results/task6/t6.1-eval-{sim,gz}-*/eval.json`与`results/task6/t6.1-summary/comparison.json`。
- 上游参考（只读）：`mobile-rl/scripts/evaluation_ray.py`、`mobile-rl/scripts/modulation/{utils.py,evaluation.py,envs/robotenv.py,envs/eeplanner.py,envs/combined_env.py}`、`mobile-rl/src/robot_env.cpp`；Husky原版同名文件`husky/src/modulation_rl/...`。
- 容器：`forem-dev`。task6.2的`forem-t6-husky-gz`正在训练G-B，**不得触碰**。

## §1 开工与上游配置核对

1. 登记PROGRESS与独立日志；检查`forem-dev`进程、GPU、Gazebo实例占用，记录主机CPU（G-B训练约14核）。
2. 重算task6.1 F0三个策略文件和`eval_task6_final.py`、`scwm_env.py`、`task3_env.py`、`modulation/utils.py`的sha256，与`results/task6/t6.1-summary/manifest.json`比对，不一致则停止报告。
3. 逐项核对上游Gazebo评估配置，写成核对表（上游位置、上游取值、本项目取值、一致/偏差）。至少包括：
   - `evaluation_ray.py` L29–37对`time_step`、`world_type`、`init_controllers`、`ik_fail_thresh`（取`ik_fail_thresh_eval`）的覆盖，L81–85从命令行覆盖的键；
   - `utils.py` L106–149缺省值：`time_step 0.02`、`ik_fail_thresh_eval 50`、`execute_style track`、`perception_style base`、`exec_action_*`为None、`nr_evaluations 50`；
   - `robotenv.py` step中`rate.sleep`被注释、`dt_exec=rate.sleep_dur`；`eeplanner.py`规划步长取实际流逝时间、上限0.5 s；
   - `wrap_in_task`中`max_close_steps`在非解析环境取500；
   - 上游评估动作是否确定性（核对`evaluate_on_task`调用策略的方式）；
   - 上游单episode步数上限（若有）与本项目`max_steps_per_episode`（task6.1为2000）的对比；
   - 物理步长：本项目Task3为0.0005 s／2000 Hz，上游启动器取值，列为已知偏差（不改）。
   核对中若发现上表以外、会影响Z-A的上游评估设置，记录后交Claude决定，不自行加入。
4. 核对本项目C++ `track`分支对Husky差速底盘可用：`src/modulation_rl/src/robot_env.cpp`的`track`分支调用`RobotHusky::calcDesiredBaseCommand`（`robot_husky.cpp` L78，差速实现）。

## §2 评估脚本最小改动与回归

1. `eval_task6_final.py`新增两个可选参数：`--execute_style {direct,track}`、`--ik_fail_thresh INT`，缺省为None（不传override，行为与现状逐位相同）。仅在`--world gazebo`时把给定值作为`overrides`传入`ScwmEnv`（→`Task3Env`→`create_env`）。`eval.json`和manifest记录实际生效的`execute_style`、`ik_fail_thresh`、`time_step`、`max_close_steps`、`window_s`（应为None）。
2. 不改`scwm_env.py`、`task3_env.py`、`modulation/`其他文件；若必须改，停止报告Claude。
3. 原文件冻结到`results/task6/t6.3-baseline/original/`，记录diff与sha256。
4. 回归：
   - 单元测试：缺省参数下生成的env配置与改动前逐键相同；传参时只改变两个键。
   - 运行回归：用缺省参数在Gazebo上对task6.1 R-48的s0策略（`results/task4/t4s-plain-s0/ckpt/policy_step01000000.pt`）跑种子2001–2005，与`t6.1-eval-gz-s0/eval.json`对应5个episode比较`episode_hash`、`done`、`internal_success`、步数。Gazebo自由运行不保证逐位确定：`episode_hash`（场景）必须相同，其余字段不同须记录，不作失败判据。
   - 现有task6测试套件（`tests/test_task6_*.py`）仍通过。

## §3 冒烟

（T63-D2，2026-10-13：Z-A改为`execute_style=direct`、`ik_fail_thresh=50`、`--max-steps 100000`；下文“`track`下底盘确实运动”改为“Z-A下底盘确实运动”。冒烟用新run-id `t6.3-smoke-r2-{A,B}`。）

`t6.3-smoke-r1`：F0-s0策略，Z-A与Z-B各跑种子2001–2003。核对：实际生效配置与核对表一致；`track`下底盘确实运动（底盘位移>0）；IK失败计数在Z-A中可超过20而episode不终止；无errored。失败或异常停止报告，不进入§4。

## §4 正式评估

- run-id：`t6.3-zs-A-s{0,1,2}`（Z-A）、`t6.3-zs-B-s{0,1,2}`（Z-B）；原始日志`logs/task6/<run-id>/`，产物`results/task6/<run-id>/`。
- Gazebo实例号：开工时确认未被占用（task6.1曾用60–65，task6.2训练容器独立）；记录实例号、GPU号。
- 6条可同时运行（每个Gazebo实例约2核，合计约12核；加G-B约14核，低于56核预算）。启动前读主机CPU；超出预算则分批。
- 评估设置：种子2001–2050，确定性动作，每种子1个episode；episode步数上限按T63-D1（见RESULTS“Claude复核R1”）：**Z-A用`--max-steps 100000`（上游非解析评估max_len），超限记capped并计为失败、不中断评估；Z-B保持2000（与task6.1 §9 R-48完全相同）**。保存每个episode的`episode_spec`、`nr_kin_failures`、碰撞、步数、内部成功、物理成功、capped/errored。
- 失败处理：gzserver崩溃或卡死时只停止自己的评估进程，用新run-id（加`-r2`）整条重跑，首次尝试证据保留、不计入；errored episode留在分母。

## §5 汇总

1. 由原始`eval.json`统计（T63-D1：Z-A另报步数>2000的episode数及其中成功数，以及“2000步内成功”的事后口径，使Z-A与Z-B的上限差异可见）：每条run的内部成功/50（Wilson 95%）、物理成功、completed/capped/errored、碰撞episode数、含IK失败episode数、因IK失败终止的episode数、平均步数；Z-A另报IK失败次数分布（便于看20–49次区间）。
2. 并列表：Z-A、Z-B、F0 sim侧（task6.1）、R-48（task6.1 Gazebo侧）。
3. 47种子敏感性（剔除2006、2012、2021）。
4. 按TASK解读表给出结论和限制，不预设结论。
5. 写`results/task6/t6.3-summary/{comparison,manifest}.json`（源码sha、策略sha、命令、实例/GPU、偏差清单）。新论据追加SOURCES条目。
6. RESULTS标review，交Claude复核。

## 异常处理

- 哈希不一致、上游核对发现上表以外的关键差异、`track`在Husky上不运动、需要改动§2允许范围外的源码：停止，写RESULTS，交Claude。
- 不自行增加评估条件（如固定窗口、Task4.8策略的Z-A评估），不训练。
- 不停止或干预task6.2的进程和容器。

## 交接要求

RESULTS至少写：实际命令、run-id、退出码、实例/GPU、源码与策略sha256、核对表、结果表、偏差清单、未解决问题、下一步。长时间运行时写监控与停止方法。
