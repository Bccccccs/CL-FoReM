# FoReM环境

后续只在forem构建。node01已有镜像mm_husky:node01（ROS Noetic、Gazebo 11、Python3.10）；宿主不安装ROS。现有mmhusky-node01/mmhusky-node01-gz是旧运行环境，本次未停止、未复用为新项目验收。

本目录src尚无算法代码，build/devel为空，未适配原版、未构建、未运行仿真。docker/保留基础镜像配置，不保留旧研究流程。

新入口docker/run.sh使用独立容器forem-dev，挂载本目录为/root/mm_husky_ws。尚未启动。将来用 sg docker -c 'bash forem/docker/run.sh up' 创建，再用shell/exec检查；原版源码、第三方依赖和资源须先按新目录准备，不会自动读写husky。编译输出将落在forem/build与forem/devel。

## 首轮选定技术栈（2026-09-30核对）

Gazebo Classic11.15.1 + ROS Noetic + Python3.10.18，沿用mm_husky:node01镜像。镜像ID为sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430；版本查询在旧容器mmhusky-node01执行，仅证明已有环境依赖，不代表FoReM新环境通过。

UR5候选模型使用EffortJointInterface，eff_joint_traj_controller为effort_controllers/JointTrajectoryController；已安装effort-controllers0.22.0、gazebo-ros-control2.9.3。先测正常关节跟踪，再单独引入指令时延或响应滞后。

接下来环境配置顺序：核对并固定镜像 → 在FoReM准备最小UR5模型及必要依赖 → 使用独立容器构建 → 启动空场景和控制器 → 确认实际关节反馈及时间对齐。除已有镜像版本和源码接口核对，其余尚未执行。

## 已验证入口（2026-09-30，task0，Claude实测）

状态：环境已配置并通过两次独立启动的基本检查，待核验（见 [task0 RESULTS](doc/tasks/task0/RESULTS.md)）。以下命令均已实际执行；从 `/home/ybc/projects/CL-FoReM` 调用。

|用途|命令|
|---|---|
|创建/启动独立容器 `forem-dev`（仅挂载 forem；bridge 网络；默认无 GPU）|`sg docker -c 'bash forem/docker/run.sh up'`|
|在容器内执行（宿主 uid，产物属主为宿主用户）|`sg docker -c 'bash forem/docker/run.sh exec <命令>'`；后台执行用 `bg`，交互 shell 用 `shell`|
|构建|`sg docker -c "bash forem/docker/run.sh exec bash -c 'cd /root/mm_husky_ws && catkin build forem_sim -j2 -p1'"`（首次先 `catkin init && catkin config --extend /opt/ros/noetic --cmake-args -DPYTHON_EXECUTABLE=/usr/bin/python3`）|
|启动仿真（固定底座 UR5，空场景，力矩控制器，无 GUI）|容器内 `roslaunch forem_sim ur5_sim.launch gui:=false`|
|一键冒烟运行（fresh 启动→反馈检查→停止自己的仿真→manifest）|`sg docker -c 'bash forem/scripts/run_task0_smoke.sh RUN_ID --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'`|
|停止自己的仿真|**（旧方法已废弃，范围不安全）** 现由 `run_task0_smoke.sh` 自动清理；手动见下文“task0.7 修正后”|
|停止/恢复容器|`sg docker -c 'docker stop forem-dev'`；`… run.sh up`|

要点：容器 `.Image` 为 `mm_husky:node01`（`sha256:e674db49…dfc430`，未修改）；入口为挂载的 `docker/forem-entrypoint.sh`（不含旧 modulation_rl 路径），工作目录 `/root/mm_husky_ws`（即 forem）；`up` 会把容器内 `/root` 改为 711 以便宿主 uid 进入。
仿真：Gazebo Classic 11.15.1，ODE 步长 0.5 ms（2000 Hz），`/joint_states` 与控制器 state 125 Hz；UR5 来自 apt `ur_description` 1.5.0，关节前缀 `ur5_`，控制器 `eff_joint_traj_controller`（命令 `/eff_joint_traj_controller/command`，反馈 `/eff_joint_traj_controller/state`、`/joint_states`）。启动时 Gazebo 先暂停，设初始姿态、加载并启动控制器后再解除暂停。
数据：`forem/results/task0/<run>/`（summary、CSV、manifest），日志 `forem/logs/task0/<run>/`。

已知限制（此为初版记录，已被下文 task0.7 更新）：当时观察到的 effort/velocity 单样本翻转与 velocity 偏置，实为 ODE `quick` 求解器下的 1 kHz 逐物理步交替，task0.7 已消除；未验证 GUI。

## Codex审核后的现状与接手（2026-09-30）

上文开头“尚未构建/尚未启动”是初次计划状态，已被后续实测取代：独立容器forem-dev已创建，使用现有mm_husky:node01镜像（未新建/派生镜像）；forem_sim已构建并运行过。任务仍review。高频诊断已确认约1kHz真实关节状态交替振荡，不能继续仅描述成偶发读数翻转。详细证据见doc/tasks/task0/task0.6/RESULTS.md。

下一步执行doc/tasks/task0/task0.7/PROCEDURE.md，不需要从头重建Docker或重复复制源码。接手先核查现有容器/挂载/镜像/进程。上表pkill停止方法有范围缺陷，task0.7需替换为本次PID与身份核验的清理方式，不能据此停止他人实例。新参数与入口验证后追加本文件，不覆盖历史数据。

## 废弃容器清理后的当前状态（2026-09-30）

用户明确确认旧任务已废弃后，mmhusky-r0-wm-s22、mmhusky-node01、mmhusky-node01-gz已删除。docker ps -a仅forem-dev运行，继续使用mm_husky:node01基础镜像；没有删镜像或宿主挂载数据。上文“旧容器仍运行”保留为历史。本轮修正使用现有forem-dev，不恢复旧任务。清理证据见doc/tasks/task0/task0.8/RESULTS.md。


## task0.7 修正后的入口与现状（2026-09-30，Claude；待Codex复核，task0仍review）

**物理**：正式世界 `forem/src/forem_sim/worlds/ur5_empty.world` 现使用 ODE `solver type=world`（直接求解），其余沿用参考（步长 0.5 ms、erp 0.2）；原 `quick` 求解器下六关节有持续 ~1 kHz 逐物理步交替（单因素诊断、恢复复现与阴性对照见 [task0.7 RESULTS](doc/tasks/task0/task0.7/RESULTS.md)，决策 `TASK0-SOLVER-20260930`）。重力写在 `<world>` 内，值 −9.8（参考世界把它写在被忽略的 `<physics>` 内，实际同为 −9.8）。控制器增益仍为参考值，未改。

**冒烟/验收运行**（唯一推荐入口；从仓库根调用）：
```bash
sg docker -c 'bash forem/scripts/run_task0_smoke.sh [--launch-arg K:=V]... [--bag [--hf-mode hold|move]] RUN_ID [check_feedback.py 参数]'
# 例：sg docker -c 'bash forem/scripts/run_task0_smoke.sh task0.8-x1 --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3'
```
- run-id 只允许字母数字开头的 `[A-Za-z0-9._-]`，已有 `logs|results/task0/<run-id>` 时拒绝（退出 12），历史证据不覆盖。
- 宿主 `flock` 独占：并发第二次退出 11；容器内已有 ROS/Gazebo 进程时退出 10（不触碰）；容器不可达/启动失败 13；启动超时 14；检查失败 1；清理残留 15；INT/TERM 分别 130/143，均先清理并写 manifest。
- 进程管理：容器内 `scripts/task0_proc.py` 记录本次进程的 pid+内核启动时间，仅对该身份及后代发 SIGINT→SIGTERM→SIGKILL；记录在 `logs/task0/<run-id>/{launch,bag}.json` 与 `*.cleanup.json`。手动停止：`bash forem/docker/run.sh exec python3 scripts/task0_proc.py stop --dir logs/task0/<run-id> --name launch`；查看外来进程：`… exec python3 scripts/task0_proc.py foreign`（`[]` 表示无）。
- 验收：`scripts/check_feedback.py`（判定逻辑在 `scripts/task0_validation.py`）检查反馈覆盖/间隙、限位（URDF）、跟踪、运动方向/完成度、终值、底座位姿服务；`--move` 时 `--duration` 须 ≥ `--move-time`+1 s，否则退出 3。误差约定：跟踪误差 = actual − desired，终值误差 = actual − command_target。
- 高频诊断：`--bag` 录 `/clock`、`/joint_states`、`/eff_joint_traj_controller/state`，转成 `results/task0/<run>/hf_*.csv`；配合 `--launch-arg controller_config:=/root/mm_husky_ws/config/diagnostics/task0.7/ur5_controllers_hf2000.yaml`（仅把发布率提到 2000 Hz，实际约 1.8 kHz，约 10% 相邻样本缺失）。`--hf-mode hold|move` 用已声明的判据评价（速度高频残差 ≤1e-4 rad/s、位置 ≤1e-7 rad 等，见 task0.7 RESULTS）。分析工具 `scripts/analyze_task0_feedback.py`，只用连续物理步样本。
- 回归：`python3 -m unittest discover -s forem/tests`（验收逻辑，宿主/容器均可）；`python3 forem/scripts/regress_task0_smoke.py --tag <新tag>`（入口失败路径，需要 forem-dev）。
- 构建仍为 `catkin build forem_sim -j2 -p1`（容器内）；`forem_sim` launch 新增参数 `world`、`controllers`（默认不变）。

**现状与限制**：`forem-dev` Up，容器内无仿真进程；三个旧容器已由用户确认废弃并删除。单机械臂固定底座、上举初始姿态、一条 3 s 小幅轨迹；GUI 未验证；world 求解器在更复杂场景的适用性与最大仿真速度未测；运动后 ~6e-4 rad 的偏差是重力载荷下的真实控制器行为（不是积分限幅，也与求解器无关）。task0 父节点仍为 review，等待 Codex 复核；task1 未开始。
