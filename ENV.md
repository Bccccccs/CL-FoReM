# Docker 环境与 P0 执行入口

更新：2026-09-22；2026-09-28 补工作区改名与容器重建（D41）。**node01 环境入口已验收通过**（"可以进入 P0"标准，非 P0 已完成）；
来源机器历史见下文，二者不可互相替代。P0 算法/评测/物理链路的后续实测见
`doc/P0/logs/20260922-p0-execution.md`（来源机器）。
默认入口为 `docker/run.sh`，开发代码仍是本工作区的 `src/modulation_rl`。
后续 P0 已修动作/梯度/终止记录及 Gazebo 执行，使用 `p0-action-terminal-v2`，不与旧权重原语义数字混比。

## 工作区改名与容器重建（2026-09-28，D41）

宿主工作区已改为 `/home/ybc/projects/CL-FoReM`，容器内挂载点仍是 `/root/mm_husky_ws`。
`mmhusky-node01`、`mmhusky-node01-gz` 已按新路径用同一镜像重建：

```bash
MM_CONTAINER=mmhusky-node01 MM_IMAGE=mm_husky:node01 bash docker/run.sh up
```

重建后 CUDA、`train-smoke`、`env-smoke`（analytical 20 步）、`gazebo-check` 均 PASS。
已知现象：同一 Python 进程先 `import torch` 再导入 `pybindings_robots`（或反之）的最小探针会
`std::bad_cast`/`free(): invalid pointer` 崩溃；`p0_runner`/`sac`/`modulation.utils` 真实导入链正常，镜像未变，
非本次重建引入，未修。

## node01 环境入口验收（2026-09-22，最新结果优先）

当前工作区 `/home/ybc/projects/CL-FoReM`（2026-09-28 由 `mm_husky_ws` 改名，D41；容器内挂载点仍为 `/root/mm_husky_ws`），本机 Ubuntu 22.04.5，
4 × NVIDIA RTX PRO 6000 Blackwell（每卡 97887 MiB），驱动 590.48.01。
下文的来源机器 Ubuntu 24.04 宿主、2080 Ti、旧绝对路径及验收属于历史，不能作为本机验收依据。

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

**关键排查（避免下次重复踩坑，详见 `docker/agent_logs/20260922-env-audit.md`）**：
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

任务记录：[ENV-AUDIT-022](doc/agent_logs/20260922-env-audit.md)。

**node01 上的 P0 使用方式（2026-09-23 P0-NODE01-023 实测）**：
- 会话若未继承 docker 组，`docker` 报 socket 权限拒绝；用 `sg docker -c '<命令>'` 包裹。
- 所有 run.sh 命令需带 `MM_CONTAINER=mmhusky-node01 MM_IMAGE=mm_husky:node01`；项目根为 `/home/ybc/projects/CL-FoReM`（下文 /home/yanbochao 路径是来源机器历史）。
- **P0 正式 analytical 基线/复现必须使用 `--ik-mode fixed --ik-iterations 100`**（IK 语义 `p0-ik-budget-v1`，D24）；默认 `legacy` 为墙钟预算，结果依赖 CPU 负载，不可复现，仅保留作对照。例：
  `MM_CONTAINER=mmhusky-node01 bash docker/run.sh train --steps 2000 --save-interval 1000 --eval-interval 0 --ik-mode fixed --ik-iterations 100 --output /root/mm_husky_ws/results/<新目录>`
- 容器内写出的 results 文件属 root；宿主侧重定向日志不要指向容器创建的目录。
- Gazebo 用独立容器 `mmhusky-node01-gz`（同镜像）避免与 analytical 共用 ROS master；任务 world 需直接 `run.sh exec xvfb-run -a roslaunch modulation_rl n2m2_husky_empty_world.launch world_name:=<world> p0_laser:=true p0_start_pose:=true gui:=false`。
- Torch 2.7 下本项目 checkpoint 须经 `checkpointing.load_trusted`（weights_only=False）加载，已在主包修复。

## 来源机器环境（历史）

| 项目 | 配置 |
|---|---|
| 默认容器 | `mmhusky-p0-ready` |
| 默认镜像 | `mm_husky:p0-ready` |
| 系统 / ROS / Python | Ubuntu 20.04 / Noetic / Python 3.8.10 |
| GPU / Torch | RTX 2080 Ti / 1.8.1+cu111 |
| RL 依赖 | Gym 0.18.0、Ray 1.6.0；SB3 实际来自主包 `scripts/stable_baselines3/` |
| 工作区 | 宿主项目 → `/root/mm_husky_ws`，复用现有 Python 3.8 devel |
| GPU 接入 | NVIDIA runtime CDI：`NVIDIA_VISIBLE_DEVICES=nvidia.com/gpu=all` |
| 网络 | 独立 bridge；ROS `127.0.0.1:11311`，Gazebo `127.0.0.1:11345` |
| 运行配置 | 8 GB shm、Python 不缓冲、WandB 离线、OMP/OpenBLAS 各 2 线程 |

P0 开工快照中旧容器均已退出；未启动、删除或重启旧容器。只使用默认容器与独立 `mmhusky-p0-gz`，后者隔离物理世界。实际会话/PID 与日志见执行记录。
主机 ROS2 Jazzy 不参与，不在主机安装 Noetic；没有重启 Docker daemon。

## 常用命令

在宿主项目根目录执行：

```bash
cd /home/yanbochao/projects/mm_husky_ws
bash docker/run.sh up
bash docker/run.sh check
bash docker/run.sh train-smoke
bash docker/run.sh shell
```

- `up` 创建或启动默认容器，并用随机文件验证挂载内容，识别旧 inode 问题。
- `check` 必须通过 `pip check`，验证 NVML、CUDA 前后向、C++ RobotHusky、ROS 包、
  项目及兼容依赖导入；打印模块路径并断言使用仓库内 SB3。
- `train-smoke` 用合成 replay 执行普通 SAC 的 3 次 CUDA 更新，并检查 actor 参数变化。
  它不依赖 ROS，不保存 checkpoint，不验证 prior-SAC 正确性或学习效果。
- 运行其他命令：`bash docker/run.sh exec python3 -u your_script.py`。
  普通 `docker exec` 不会自动执行 ENTRYPOINT，项目命令建议通过上述入口。

解析仿真，在终端 1 保持运行：

```bash
bash docker/run.sh analytical
```

看到 MoveGroup 初始化完成后，在终端 2：

```bash
bash docker/run.sh env-smoke
```

`env-smoke` 验证 reset 和 20 步有限观测/奖励，不要求本阶段解决确定性。
`train` / `eval` 使用新的显式入口：默认 husky_ur5、simpleobstacle、sim、seed 11。
必须指定一个尚不存在的输出目录；评测必须指定 checkpoint 与种子文件。以下在本机以同参数执行，结果在 `results/p0-20260922/`（重复执行请换输出目录）：

```bash
bash docker/run.sh train --steps 2000 --save-interval 1000 \
  --output /root/mm_husky_ws/results/my-sac-smoke
bash docker/run.sh eval \
  --checkpoint /root/mm_husky_ws/results/p0-20260922/sac-fixed-ik/latest.pt \
  --seeds /root/mm_husky_ws/results/p0-20260922/seeds-validation20.json \
  --episodes 20 --output /root/mm_husky_ws/results/my-sac-eval
```

普通 SAC 默认；先验版本显式 `--algorithm prior_sac --beta .2 --prior-checkpoint PATH`。
`prior_sac_legacy_alpha` 单独命名旧alpha耦合目标。训练保存policy/critic/target、优化器、
调度器、alpha、replay、RNG与计数；`--resume PATH`严格检查协议一致，属于
`partial_environment_reset`，不恢复模拟器。训练时初始 `--steps` 就是完整预算，恢复时保持一致。
`--eval-interval 0` 关闭周期评测；Gazebo训练必须关闭周期评测，另用隔离世界评估。
评测默认每回合独立进程，重建BioIK；逐回合日志/异常/轨迹均保留，耗时包括策略与环境step。
工程2000步只验证训练正确性，不证明收敛或研究收益。

切换 ROS 模式，在另一终端执行并等待原 launch 终端退出：

```bash
bash docker/run.sh stop-ros
```

同一容器不同时运行 analytical 和 gazebo。需要另一独立环境时使用
`MM_CONTAINER=mmhusky-other bash docker/run.sh up`。

Gazebo 空场景，在终端 1：

```bash
bash docker/run.sh gazebo
```

终端 2 的 **P0 环境入口验收**：

```bash
bash docker/run.sh gazebo-check
```

这只检查空世界、Husky spawn、BioIK、运行控制器和局部代价图，不发送速度。
`gazebo-smoke` 是 P0 物理移动检查，阈值保持 >0.03m；修复重力后已实测0.3013m通过。

Gazebo 默认使用 Xvfb 和 `/usr/share/gazebo-11/worlds/empty.world`，无需桌面。
入口显式启用 `p0_laser:=true p0_start_pose:=true`；直接launch时两开关默认关闭。
任务资产先执行 `bash docker/fetch_assets.sh`，它核对固定提交与干净状态；模型路径由run入口显式传入。
launch 已包含 MoveIt，勿重复启动。`gazebo-gui` 可用于后续视觉检查，但本轮未做 GUI
视觉验收。创建容器时会透传 DISPLAY、X11 socket，以及存在时的 XAUTHORITY；
未修改全局 X11 访问策略。ROS/RViz 工具需在该容器里运行。

## 构建与依赖

```bash
bash docker/run.sh build
```

Dockerfile 基于本机 `mm_husky:deps`；构建脚本核对默认 base 的 image ID：
`sha256:7e08e15e9865c49c7ee903f6e5b9172ac4d1438574c9351c600181a41e75024d`。
新镜像 ID：`sha256:a68ab80a0fc135dd7e0bf106f214455f4fc2d98835cea8f526669838c0551f7b`。

该流程是可重复的 **本地增量构建**，不是从公开基础镜像全量安装。
迁移机器需要 `docker save/load` 转移基础或最终镜像，并备份工作区及 git 不跟踪的权重。
`MM_BASE_IMAGE` 可显式选择审计过的基础镜像；`MM_IMAGE` 控制输出镜像。
`python-freeze.txt` / `dpkg-versions.txt` 是审计快照，不是全量安装锁文件。

Dockerfile 包含：

1. 修复 OpenSSL 冲突，安装 pyOpenSSL 24.3.0 / cryptography 44.0.3。
2. 补 PettingZoo 1.23.1、Xvfb/xauth、`python` → `python3`。
3. 通过 `requirements-p0.txt` 固定兼容覆盖版本：vit-pytorch 0.20.8、
   scikit-image 0.18.3、imageio 2.9.0、Pillow 7.2.0、attrs 23.2.0、
   six 1.16.0、psutil 5.9.8；安装 pytest 7.4.4 及其依赖供 P0 回归使用。
4. 构建期间执行 `pip check`，有声明冲突则构建失败。
5. ENTRYPOINT 自动加载 ROS、devel、PYTHONPATH 与 Gazebo 资源路径。

本机构建阶段 bridge DNS 失败，因此构建使用 host 网络并透传已有代理参数；
代理没有写入镜像运行 ENV，运行仍隔离 bridge。构建上下文只含 docker/，不含权重。
运行容器若需联网安装其他依赖，须另配置网络/代理。

重建镜像不会更新已有容器。需要更新时，先结束该容器中的任务，再替换容器，
或使用新的 `MM_CONTAINER` 名称创建；不要删除仍在训练的 `mmhusky-dev`。

## 环境入口验收的历史记录（后续 P0 结果优先）

- 镜像构建与 `pip check`：通过，原 7 项依赖声明冲突已消除。
- 新容器挂载、项目/兼容依赖导入、CUDA 前后向、RobotHusky 绑定：通过。
- 普通 SAC 合成 batch=4，3 次 CUDA 更新：通过，actor 最大参数变化约 0.000299。
- analytical reset + 20 步：通过；状态 `(41,)`、地图 `(120,120,1)`、动作 `(3,)`。
- Gazebo 空世界启动、Husky、BioIK、5 个运行控制器、120×120 costmap：通过。
- pytest 已可导入。本轮未重编 catkin：当前 devel 产物已验证可加载。
  后续 C++ 开发需在容器内 `catkin build -j2`；重编前应停止使用共享 devel 的任务，
  或为编译与测试建立独立 build/devel，避免影响旧训练。

以下是环境任务结束时的历史待办；修复与当前验收见 P0 执行记录，不代表当前仍全部阻塞：

- prior-SAC 当前 actor 梯度断链，普通 SAC 烟测不能证明该路径正确。
- 同种子初始观测哈希不同，尚未建立确定性评测协议。
- 旧 Gazebo 移动检查约 1.2 cm，仍待动力学/控制排查。
- PAL / dynamic_obstacle 场景模型、Gazebo SAC reset/step 与 RViz 视觉验收待完成。
- 旧 SR=0.60 为历史语义结果，不作为修复后基线；本轮依赖变化后的正式基线也需重测。

旧容器 NVML 失败与 NVIDIA legacy hook/cgroup 已知问题相符，但具体触发事件未确认。
新环境通过 CDI 恢复 GPU；未执行会干扰旧训练的 daemon-reload 测试。
参考：https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/troubleshooting.html

本轮证据：`docker/validation/p0-ready/`；旧 `docker/validation/` 顶层输出仅作历史记录。
进度与交接：`doc/P0/logs/20260922-p0-fixes.md`。

## P0 实施后的当前结论

当前工程验收见 [P0_ACCEPTANCE](doc/P0/ACCEPTANCE.md)。普通/prior-SAC梯度、动作、checkpoint与GPU2000步通过；Gazebo真实移动、冷启动有限任务rollout、夹爪和近障碍costmap通过。严格数值复现最终仍失败，不能据环境入口通过放行P1。Gazebo配置周期30ms而实测p95约146ms，不代表实时性能通过。

评测应顺序运行：独立回合进程的父进程当前也保留模型/CUDA上下文，多组评测并发曾OOM。失败回合保留并用新目录重跑，不复用原目录。此限制已实测，不要依据torch allocated峰值估计整个多进程显存。
