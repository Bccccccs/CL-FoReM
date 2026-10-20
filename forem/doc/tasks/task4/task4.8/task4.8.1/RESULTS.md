# task4.8.1 — 结果与交接

> **当前状态（2026-10-19核对）：closed（随task4关闭；未经独立复核）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**review**（子Agent实施完成，待父Agent核验；非done）。负责人：Claude子Agent（模型Sonnet5.5，推理强度未知/平台默认）。独立日志：[agent_logs/task4/task4.8/task4.8.1/20261009-claude-sub-task4-8-1.md](../../../../agent_logs/task4/task4.8/task4.8.1/20261009-claude-sub-task4-8-1.md)。

## 1. 交付物（均为新增文件，未改forem/src与旧脚本）

| 文件 | 作用 |
|---|---|
| `forem/scripts/scwm_instance.py` | 每实例K的`start/stop/status/env/exec/list/residue`；ROS 11400+K、Gazebo 11500+K、`IGN_PARTITION=GZ_PARTITION=forem_inst<K>`、独立HOME/ROS_HOME/ROS_LOG_DIR（均在`logs/task4/<run-id>/inst<K>/`下）、`ROS_IP/GAZEBO_IP/IGN_IP=127.0.0.1`；通过`task0_proc.py start/stop`做身份监督（pid+内核start time），`stop`只信号本实例已验证成员；`--cpus`经`taskset -c`；`exec`默认继承实例的cpus；注册表`logs/task4/.instances/inst<K>.json`，只对同一实例号用`flock`互斥；端口占用/同号运行/证据目录已存在均拒绝（rc 11/12）；`residue`扫描`/proc/*/environ`中的分区标记，判定无残留 |
| `forem/scripts/regress_scwm_instances.py` | 隔离回归（同时含`--child pose-pub`、`--child env-driver`两个子模式；`env-driver`首个重量级import为`ray`） |
| `forem/scripts/bench_scwm_parallel.py` | K实例并发吞吐基准（每实例一个`Task3Env`随机动作驱动，无学习更新；同步起跑；采样`/proc/stat`与实例进程CPU） |

就绪判据与`run_task3_core.sh`相同（`launch.log`含`controllers running`与`You can start planning now`），超时默认240 s。单次启动实测约5.2–9 s就绪（K=1…32同时启动：5.6→9.1 s）。

隔离要素与已知共享资源（逐项）：ROS master端口、Gazebo master端口、ignition-transport分区（UDP组播发现不受master URI约束，所以必须分区）、HOME（~/.gazebo、~/.ros、~/.cache、~/.ignition）、ROS_LOG_DIR均每实例独立；未使用`.smoke.lock`。`forem/src`下检索未发现硬编码11311/11345或固定/tmp路径（simulator_api/combined_env/occupancy_grid_manager只匹配到注释/变量名）。`/tmp`中其他条目（freeze-path-*等）是旧任务产物，本任务未核查实例是否在/tmp写文件（未验证，未发现冲突迹象）。

## 2. 隔离回归（实测）

- 命令：`sg docker -c 'bash forem/docker/run.sh exec python3 scripts/regress_scwm_instances.py --run-id t4.8.1-regress-r1'`（及r2，r2在脚本小改后复跑）。退出码均为0，**26项检查全部PASS**；证据：`forem/results/task4/t4.8.1-regress-r1/regress.json`、`.../t4.8.1-regress-r2/regress.json`，日志`forem/logs/task4/t4.8.1-regress-r{1,2}*/inst{0,1}/`。
- 覆盖：(1)两实例同时start均rc0；(2)同号重复start被拒（rc 11）且不产生证据目录；(3)两master的节点URI集合不相交，各自含`/gazebo /move_group /pose_bridge /robot_state_publisher /twist_mux`；在A上`rosparam set`的参数在B不可见；(4)各自`/gazebo/model_states`恰有一个`husky_ur5`；仅向A发`/husky_velocity_controller/cmd_vel`(0.5 m/s, 3 s)：A位移1.395 m，B位移2.8e-14 m；(5)两实例各用`Task3Env`做`reset(seed=7)`，`episode_spec['hash']`相同（0d7755ba…0623d），且停止A、重启A后单独复位的hash仍相同；(6)停止A后B（驱动进程仍存活）继续step 20步无错；A的residue为空、端口释放；(7)故障：kill -9 B的gzserver后A仍可读取状态且不受影响，对B执行`stop`rc 0、residue为空、端口已释放；(8)收尾时两实例residue为空、端口空闲。
- 限制：回归只覆盖2个实例；K>2的隔离由吞吐基准间接支持（每个K个驱动均rc0且各自读到自己的master；`stop`均rc0，`residue_after`全空）。

## 3. 吞吐实测（`bench_scwm_parallel.py`，每实例600步随机动作+1次强制复位，无学习）

测量环境：forem-dev，64 CPU（NUMA0=0–31，NUMA1=32–63），ODE步长等未改；Gazebo无GUI、不暂停实时。**机器非独占**：测量开始时另有主Agent的GPU基准`bench_scwm_update.py`短暂在容器内运行（未见其后继续占用）；宿主其他用户负载未知，表内`机器忙比例`含这些外部负载。速率不含`env.reset()`耗时（复位耗时单列）；CPU统计窗口内含复位。窗口为各驱动phase-1的重叠区间。每个K一次运行（K=6有重复）；run-id`t4.8.1-bench-k<K>-r1`，原始`forem/results/task4/<run-id>/bench.json`（含`series.json`采样），日志`forem/logs/task4/<run-id>/inst*/`。全部驱动与停止rc为0、停止后无残留。

| K | 每实例 step/s（均值，[min,max]） | sim/wall | 单步wall(ms) | 总step/s | 相对K=1每实例速率 | 机器忙比例 | 实例树占核（gzserver/driver/其他ROS） | 复位耗时均值/最大(s) |
|---|---|---|---|---|---|---|---|---|
| 1 | 60.65 | 0.942 | 16.5 | 60.7 | 100% | 0.063 | 2.19（1.04/0.61/0.53） | 19.1 / 20.5 |
| 2 | 60.36 [59.9,60.8] | 0.939 | 16.6 | 120.7 | 99.5% | 0.073 | 4.26 | 18.9 / 24.3 |
| 4 | 61.48 [61.0,62.0] | 0.959 | 16.3 | 245.9 | 101% | 0.138 | 8.62 | 18.4 / 21.3 |
| 6 | 62.04 [61.6,62.3]（r2: 62.06） | 0.971 | 16.1 | 372.2 | 102% | 0.20 / 0.17 | 11.33（5.8/3.3/2.3） | 18.0 / 20.9 |
| 8 | 61.32 [60.9,61.8] | 0.968 | 16.3 | 490.5 | 101% | 0.252 | 16.1 | 18.0 / 21.4 |
| 12 | 58.55 [57.9,59.5] | 0.926 | 17.1 | 702.6 | 96.5% | 0.402 | 25.5 | 17.9 / 20.8 |
| 16 | 57.05 [55.8,58.4] | 0.856 | 17.5 | 912.9 | 94.1% | 0.507 | 31.9 | 18.4 / 21.3 |
| 24 | 50.89 [48.7,54.0] | 0.652 | 19.7 | 1221.3 | 83.9% | 0.682 | 42.8 | 19.2 / 22.3 |
| 32 | 47.49 [44.0,50.7] | 0.596 | 21.1 | 1519.7 | 78.3% | 0.771 | 48.3 | 21.1 / 27.4 |

要点：每实例平均约2 CPU核（gzserver≈1，Task3Env驱动≈0.6–1，其余ROS节点≈0.4）；总吞吐到K=8近线性，K≤12损失<4%，K=16损失约6%，K≥24显著衰减（sim/wall降至0.65→0.60，即实时因子下降，单步更慢）。启动并发：K=32同时启动9.1 s就绪，驱动加载（含首次reset）20–31 s。**复位耗时约18–21 s，一个600步（约10 s）窗口内通常含3–4次复位，是训练墙钟的主要部分之一**——这是原环境reset（Gazebo set_model_state、障碍物生成、IK/规划）成本，本任务未改动，K增大对它几乎无影响（K≤16）。

### NUMA/亲和对比（K=6）

| 布局 | 命令参数 | 每实例step/s（r1 / r2） | 总step/s | 单步ms |
|---|---|---|---|---|
| 无亲和 | `--layout none` | 62.04 / 62.06 | 372.2 / 372.4 | 16.12 / 16.11 |
| NUMA节点绑定（实例i→节点i%2全部32核；节点0放3个、节点1放3个） | `--layout numa` | 62.35 / 62.58 | 374.1 / 375.5 | 16.04 / 15.98 |
| 节点内不相交切片（每实例10核） | `--layout part` | 62.38 / 62.33 | 374.3 / 374.0 | 16.03 / 16.04 |

NUMA/切片绑定相对无亲和仅+0.5%…+0.8%（两次重复方向一致，幅度小，在本机其他负载下是否稳健未验证）。结论：K=6时无需强制亲和；亲和主要价值是给学习器/GPU进程预留核集。K>16的亲和未测。

## 4. 失败路径与清理

见上§2(6)(7)：杀死一个实例的gzserver不影响另一实例；`stop`对该实例清理干净；重复`start`被拒；中途异常时`regress`的`finally`只停自己的实例；基准`finally`对其K个实例执行stop+residue。所有基准运行末尾`residue_after`为空、容器内仅余`sleep infinity`。`logs/task4/.sim_exclusive`已在测量结束后删除（记录于10:17起）。注册表目录`logs/task4/.instances/`保留`inst<K>.stopped-*.json`历史记录。

## 5. 限制与未解决

- 吞吐为随机动作、无学习更新、无GPU推理的**环境侧上限**；真实训练的推理/update/日志会占额外核（本任务未测，属4.8后续）。驱动占核0.6–1.0/实例，对应Task3Env Python端CPU。
- 机器非独占（见§3），数字含外部负载噪声；每K仅一次运行（K=6三布局各两次）。
- 容器内`nproc`输出2，但`sched_getaffinity`为0–63（`nproc`可能受环境线程数变量影响，原因未核查）；库内线程数（OMP等）未调优，未在本任务测。
- RNG/种子：同seed的episode_spec hash跨实例一致，未比较完整轨迹逐位一致。
- 1实例驱动初始化（含首次reset）约20 s；K=32时31.5 s。
- 未做GPU分配、同机多trainer联调，未做>32实例。

## 6. 建议的实例/核集布局（供父Agent采纳，非已批准配置）

- 每实例预留≈2.2–2.5核（含驱动）；总实例数建议≤12（效率≥96%，实时因子≥0.92），要最大总吞吐可到16（94%）；24及以上每实例变慢，总吞吐仍增但sim/wall降至0.65，会改变与wall时间相关的行为，需谨慎。
- 实例号K对应固定端口：ROS 11400+K，Gazebo 11500+K；run-id含K，避免证据目录冲突。
- 亲和：默认不强制（NUMA对K=6增益<1%）；若与学习器同机，用`--cpus`把仿真实例限定在例如节点内不相交切片，学习器/GPU数据进程另留核（例：节点0放6个实例各5核+学习器独占节点1的部分核，**待实测确认**）。
- 启动/停止统一用`scwm_instance.py`；训练进程通过`scwm_instance.py exec --inst K -- python3 ...`取得同一环境；**Python中`import ray`必须先于torch**（见`task3_env.py`）。

## 7. 建议由父Agent登记SOURCES的条目（仅文本，编号由父Agent分配）

1. 项目实测：多实例隔离回归，来源`results/task4/t4.8.1-regress-r1/regress.json`与`-r2`，`scripts/regress_scwm_instances.py`，2026-10-09；支持“ROS/Gazebo/ignition分区隔离2实例可并行、互不可见、停止互不影响”；限制：仅2实例回归。
2. 项目实测：K=1–32并发吞吐，`results/task4/t4.8.1-bench-k*-r1/bench.json`（含k6 numa/part/none r1/r2），`scripts/bench_scwm_parallel.py`；支持“K≤12每实例step/s≥96%、K=16 94%、K=32 78%；NUMA绑定K=6增益<1%”；限制：随机动作、无学习、机器非独占、每点一次/两次。
3. 工程选择：端口分配ROS 11400+K/Gazebo 11500+K、分区`forem_inst<K>`、独立HOME；理由：避开默认11311/11345、ignition UDP发现须分区；待验证：K>2的跨实例泄漏仅由基准间接支持。
4. 外部文档（二手/未逐条读原文，标“待核”）：ROS `ROS_MASTER_URI/roslaunch -p`、Gazebo `GAZEBO_MASTER_URI`与ignition-transport `IGN_PARTITION`的官方说明；本任务仅通过实测验证行为，未重新核对文档条文。

## 8. 模型与实际配置

推荐Claude Sonnet5.5/medium，Codex等价GPT6.1sol/medium。实际：Claude子Agent，Sonnet5.5，推理强度未知（平台默认）。
