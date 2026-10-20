# task4.8.1 — 多仿真实例隔离详细流程

**递归规则：** 本节点恰有TASK.md、PROCEDURE.md、RESULTS.md；若进一步拆分，须在本目录内继承编号（task4.8.1.1…）并先建三文档，父流程列顺序/依赖/负责人/链接/验收；不另建第四份同职责文档。当前无更深子任务。

**Goal：** 可并行、可清理、可验证隔离的K个仿真实例。
**依赖：** 现有`forem_husky/launch/husky_core.launch`、`scripts/task0_proc.py`（进程身份监督）、`scripts/task3_env.py`、容器`forem-dev`（见`forem/ENV.md`）。仿真为非暂停实时Gazebo，ODE步长0.5ms，实时因子约0.8–0.9（单实例）。

## 隔离要素（须逐项处理并写明为什么）

1. `ROS_MASTER_URI=http://127.0.0.1:<11400+k>`，`roslaunch -p`；`GAZEBO_MASTER_URI=http://127.0.0.1:<11500+k>`；ignition transport分区（`IGN_PARTITION`/`GZ_PARTITION`）；`HOME`、`ROS_HOME`、`ROS_LOG_DIR`、Gazebo日志路径每实例独立目录；
2. 所有被launch启动的节点（move_group、costmap、pose_bridge、gazebo、controllers）都在该实例master下，不得连到别实例；
3. 进程身份：每实例由`task0_proc.py start`（或等价、可证明的身份监督）启动，停止只终止本实例进程树；不按名称pkill；
4. 启动/就绪判据同`run_task3_core.sh`（日志含`controllers running`与`You can start planning now`），并有超时；
5. 训练/测试进程通过`scwm_instance.py env`/`exec`取得同一环境变量；
6. 不使用共享`.smoke.lock`；改用每实例锁/PID记录，且只对“同一实例号”互斥。

## 步骤

- [ ] 读取`ENV.md`、`husky_core.launch`、`run_task3_core.sh`、`task0_proc.py`，列出需隔离项与已知共享资源（/tmp、~/.gazebo、~/.ros、端口、gazebo model database已设为空）。
- [ ] 实现`forem/scripts/scwm_instance.py`：`start/stop/status/env/exec`（含`--inst K`、`--run-id`、`--cpus`可选亲和）；证据写`forem/logs/task4/<run-id>/inst<K>/`。
- [ ] 隔离回归`forem/tests/test_scwm_instances.py`（或`scripts/regress_scwm_instances.py`）：同时起2实例，各自master下`rosnode list`不含对方节点、`/gazebo/model_states`各一个`husky_ur5`；仅向实例A发底盘速度命令，A的机器人移动而B不动；各实例用`Task3Env`（`scripts/task3_env.py`，注意先`import ray`）做`reset(seed=7)`并比较`episode_spec['hash']`与单实例一致；停止A后B仍可step；全部停止后无残留进程、端口释放。
- [ ] 吞吐实测：对K=1,2,4,6,8（机器允许时继续到12）并发，各实例跑`Task3Env`随机动作≥300步（含至少一次reset），无学习更新；记录每实例step/s、sim/wall比、reset耗时、全机CPU使用率（含`mpstat`或`/proc/stat`），并报告K增大时的衰减；再对K=6测试按NUMA节点分配`taskset`核集（节点0核0–31放3个、节点1核32–63放3个）的影响。**测量期间在`forem/logs/task4/.sim_exclusive`写入占用说明（Agent、起止时间），主Agent在文件存在时不启动其他仿真；测完删除。**
- [ ] 失败路径：杀死一个实例的gzserver/train进程后，其他实例不受影响且`stop`能干净清理；重复`start`同号实例被拒绝。
- [ ] 在本任务RESULTS记录：命令、版本、run-id、退出码、表格、限制、建议的实例/核集分配；给出需要登记SOURCES的条目文本（不自行争用编号，不改共享PROGRESS/SOURCES）。

## 验收与停止条件

验收：隔离回归全部通过；清理无残留；吞吐表完整；未改`forem/src`；未改物理/任务语义。若发现必须改`forem/src`才能隔离（如硬编码资源），停止并在RESULTS报告，不擅自改。结束后通知主Agent，不启动训练或后续任务。

## 模型与实际配置

推荐Claude Sonnet5.5 medium；实际配置按子Agent日志另记。
