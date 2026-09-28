# 运行环境（node01）与 Docker 入口

更新：2026-09-28（DOCREV-028 全量审查）。本文只描述本机 node01 的现行环境；来源机器（2080 Ti / Python 3.8 / `mmhusky-p0-ready`）的历史内容已移至 [审查前快照](doc/archive/20260928-docrev/ENV-pre-docrev.md)，不适用于本机。

## 1. 概览

| 项 | 当前值 |
|---|---|
| 宿主 | node01，Ubuntu 22.04.5，内核 6.8，64 逻辑 CPU，RAM 约 251 GiB |
| GPU | 4 × NVIDIA RTX PRO 6000 Blackwell（每卡 97887 MiB），驱动 590.48.01 |
| 工作区 | 宿主 `/home/ybc/projects/CL-FoReM` → 容器内 `/root/mm_husky_ws`（D41） |
| 镜像 | `mm_husky:node01`（`sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430`） |
| 容器内软件 | Noetic（Focal 公开基础镜像）、Python 3.10.18（`/opt/python310`；系统 Python 3.8 仅供 apt/ROS 工具）、PyTorch 2.7.1+cu128、Gazebo 11 |
| 常驻容器 | `mmhusky-node01`（analytical）、`mmhusky-node01-gz`（Gazebo），均为 bridge 网络、NVIDIA runtime、shm 8g，2026-09-28 按新路径重建 |
| 入口 | [docker/run.sh](docker/run.sh)，默认容器 `mmhusky-node01`、镜像 `mm_husky:node01` |

## 2. 常用命令

在宿主项目根目录执行。当前会话若未继承 docker 组，用 `sg docker -c '<命令>'` 包裹。

```bash
cd /home/ybc/projects/CL-FoReM
bash docker/run.sh up            # 创建/启动默认容器，并用随机文件校验挂载
bash docker/run.sh check         # pip check、CUDA、绑定、ROS 包、导入路径（见“已知限制”）
bash docker/run.sh train-smoke   # 普通 SAC 合成 batch 的 3 次 CUDA 更新
bash docker/run.sh shell         # 进入容器（自动加载 ROS/devel/PYTHONPATH）
bash docker/run.sh exec python3 -u your_script.py
```

普通 `docker exec` 不会执行 ENTRYPOINT，项目命令请通过 `run.sh exec`，或显式调用 `/usr/local/bin/mm-entrypoint`。操作 Gazebo 容器时加 `MM_CONTAINER=mmhusky-node01-gz`。

**analytical**：终端 1 保持 `bash docker/run.sh analytical`；看到 MoveGroup 初始化完成后，终端 2 执行 `bash docker/run.sh env-smoke`（reset + 20 步）。

**训练 / 评测**（默认 husky_ur5、simpleobstacle、sim、seed 11）。正式 analytical 实验**必须**带 `--ik-mode fixed --ik-iterations 100`（`p0-ik-budget-v1`，D24）；默认 `legacy` 为墙钟预算，结果随 CPU 负载变化、不可复现。输出目录必须尚不存在：

```bash
bash docker/run.sh train --steps 2000 --save-interval 1000 --eval-interval 0 \
  --ik-mode fixed --ik-iterations 100 --output /root/mm_husky_ws/results/<新目录>
bash docker/run.sh eval --checkpoint /root/mm_husky_ws/results/<run>/latest.pt \
  --seeds /root/mm_husky_ws/results/<seeds>.json --episodes 20 \
  --ik-mode fixed --ik-iterations 100 --output /root/mm_husky_ws/results/<新目录>
```

- 先验版本显式 `--algorithm prior_sac --beta .2 --prior-checkpoint PATH`；`prior_sac_legacy_alpha` 单独命名旧 alpha 耦合目标。
- 训练保存 policy/critic/target、优化器、调度器、alpha、replay、RNG 与计数；`--resume PATH` 严格检查协议一致，属于 `partial_environment_reset`，不恢复模拟器。
- `--eval-interval 0` 关闭周期评测；Gazebo 训练必须关闭周期评测，另用隔离世界评估。
- 评测默认每回合独立进程并重建 BioIK，逐回合日志/异常/轨迹均保留；多组评测并发时注意父进程也持有模型/CUDA 上下文，按实测资源安排并发。
- 2000 步只验证训练正确性，不证明收敛或研究收益。
- Torch 2.7 下本项目 checkpoint 须经 `checkpointing.load_trusted`（weights_only=False）加载。
- 容器内写出的 results 文件属 root；宿主侧重定向日志不要指向容器创建的目录。

**Gazebo**：使用独立容器 `mmhusky-node01-gz`，避免与 analytical 共用 ROS master；同一容器不同时运行 analytical 和 Gazebo（切换前 `run.sh stop-ros`）。

```bash
MM_CONTAINER=mmhusky-node01-gz bash docker/run.sh gazebo        # 空场景（Xvfb）
MM_CONTAINER=mmhusky-node01-gz bash docker/run.sh gazebo-check  # 启动检查：Husky/BioIK/控制器/costmap
MM_CONTAINER=mmhusky-node01-gz bash docker/run.sh exec xvfb-run -a roslaunch modulation_rl \
  n2m2_husky_empty_world.launch world_name:=<world> p0_laser:=true p0_start_pose:=true gui:=false
```

`gazebo-smoke` 是物理移动检查（阈值 >0.03 m）。任务资产先执行 `bash docker/fetch_assets.sh`（核对固定提交与干净状态），模型路径由 run 入口传入。launch 已含 MoveIt，勿重复启动。Gazebo 实时性尚未达标（p50 52.8 ms vs 配置 20 ms，见 P0 验收），对齐工作属于 Stage0 R0-5。

**实验任务容器**：长任务另建带任务前缀的独立容器（如 `mmhusky-r0-*`），可用 `MM_CONTAINER=<名> bash docker/run.sh up`，或参照 `doc/agent_logs/20260928-p1-retrain-launch.sh` 以 `--network none`、内存上限等参数 `docker create`。不停止或重建他人正在使用的容器。

**构建镜像**：`bash docker/run.sh build`（使用 `docker/Dockerfile.node01`，`--network host`，不传代理 build-arg）。重建镜像不会更新已有容器，需先结束容器内任务再替换，或换新的 `MM_CONTAINER`。C++ 改动需在容器内 `catkin build`，重编前确认没有其他任务在使用共享 devel。

## 3. node01 环境入口验收（2026-09-22，ENV-AUDIT-022）

**镜像与容器**：`mm_husky:node01`（`docker build -f docker/Dockerfile.node01 docker`，
`--network host`，不传代理 build-arg——本机对 PyPI/GitHub/Ubuntu 源/ROS 源均直连可达，
经代理反而有 ~10-20% 瞬时 502，详见下方"关键排查"）；容器 `mmhusky-node01`
（`MM_CONTAINER=mmhusky-node01 MM_IMAGE=mm_husky:node01 bash docker/run.sh up`）。
Python 3.10.18（独立 `/opt/python310`，系统 Python3.8 保留供 apt/系统 ROS 工具）、
PyTorch 2.7.1+cu128、Noetic（Focal 公开基础镜像，非来源机器的私有 `mm_husky:deps`）。

**验收实测（容器内实际执行，均为从零构建镜像后的复现结果，非手工临时修复）**：
- `pip check`：干净。
- CUDA 真实前向+反向（`x@x.T` 求和 backward）：PASS，4 张 GPU 全部可见。
- `catkin build -j8`：workspace 全部 34 个包成功；`pybindings`/`pybindings_robots`
  确认为 `cpython-310` ABI，`from pybindings_robots import RobotHusky` 真实 import 成功。
- `rospack find`（modulation_rl/husky_ur5/bio_ik/gazebo_ros/ur_description/
  velodyne_description/lms1xx）：全部 PASS。
- `docker/train_smoke.py`（普通 SAC 合成 batch，3 次 CUDA 更新）：PASS，
  actor 参数确有更新（量级与历史记录一致）。
- analytical（`n2m2_husky_analytical.launch`）+ `docker/env_smoke.py`：PASS，
  reset+20 步，状态 `(41,)`+`(120,120,1)`、动作 `(3,)`。
- Gazebo（`n2m2_husky_empty_world.launch`）+ `docker/gazebo_smoke.py --startup-only`：
  PASS，5 个控制器运行，costmap `(120,120)`。

**已知限制（未修复，不掩盖）**：`modulation.myray.*`（ray/rllib 版 SAC，
`custom_sac.py`）在 `ray==1.13.0`（为 cp310 wheel 选用，历史 pin 是 1.6.0）下因
`Trainer.with_updates()` 被移除而无法 import；已确认 `main.py`/`eval.py`/
`docker/train_smoke.py` 均不使用该路径（用仓库自己的 `sac.py`/`model.py`），故
不阻塞本轮验收，但修复需要改 `src/modulation_rl` 算法代码，超出环境配置范围。
`docker/check.py` 整体运行仍会在到达该模块时失败，这是有意保留的真实信号。

**关键排查（避免下次重复踩坑，详见 [ENV-AUDIT-022](doc/agent_logs/20260922-env-audit.md)）**：
1. `range_sensor_layer`、`multimaster_launch`、`hsrb_moveit_config`、
   `microstrain_mips`、`hsrb_description`、`python-scipy` 六个 rosdep key
   在 Noetic apt 没有发布二进制或已废弃；逐条核实均为当前 P0 路径不触发的
   `run_depend`/`exec_depend`，已加入 `rosdep install --skip-keys`。
2. `pr2_mechanism_msgs`/`pr2_msgs`（`modulation_rl/src/robot_pr2.cpp` 直接
   `#include` 但 package.xml 未声明）、`ur5_moveit_config`（husky_ur5 launch
   需要但 package.xml 未声明）：apt 有对应包，已补进 Dockerfile。
3. `wandb==0.10.11` 在 Python3.10 下 `from collections import Mapping` 报错
   （3.10 移除该别名）；升到 `0.15.12` 修复。
4. `defusedxml`（xacro 依赖）不在任何依赖声明里，roslaunch 会直接失败；已补。
5. 本机代理（daemon 层 17893、shell 层 7892）在持续请求下有 ~10-20% 瞬时 502，
   apt 内建 `Acquire::Retries` 不足以吸收；**直连反而稳定**（同批测试 0 次 502），
   已改为构建时不传代理。curl/git 各自还需要显式超时/低速中断参数
   （`--connect-timeout`+`--speed-limit`／`GIT_HTTP_LOW_SPEED_LIMIT`），否则
   单次卡死的连接可能挂起数十分钟到两小时才被判定失败，`--retry` 根本没机会触发。
6. Docker 曾用的临时代理 drop-in `/run/systemd/system/docker.service.d/zz-temporary-proxy.conf`
   （`http://127.0.0.1:17893`）**仍是临时配置，未撤销**；本次构建未依赖它
   （镜像拉取用了它，但后续 `docker build` 均不传代理），收尾时仍需与用户/管理员
   确认是否撤销，不属本轮环境任务范围。


## 4. 2026-09-28 容器重建（D41）

`mmhusky-node01`、`mmhusky-node01-gz` 按新路径用同一镜像重建（`run.sh up`）。重建后 CUDA、`train-smoke`、`env-smoke`（analytical 20 步）、`gazebo-check` 均 PASS，证据见 [PATHSYNC-028](doc/agent_logs/20260928-path-sync.md)。

**已知现象（未修）**：同一 Python 进程里仅导入 `torch` 与 `pybindings_robots`（任一顺序）的最小探针会 `std::bad_cast` / `free(): invalid pointer` 崩溃；`p0_runner`/`sac`/`modulation.utils` 的真实导入链正常。镜像未变，属既有问题。
