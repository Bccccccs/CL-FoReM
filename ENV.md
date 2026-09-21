# 环境配置文档（mm_husky_ws）

项目：N2M2（`src/modulation_rl`）+ Husky/UR5 ROS1 相关包。记录日期：2026-09-21。

## 1. 总体方案

主机为 Ubuntu 24.04 + ROS Jazzy（ROS2），无法直接编译本项目（ROS1 / catkin），因此所有开发、编译、运行都在 Docker 容器 `mmhusky`（ROS Noetic）中进行。

| 项目 | 主机 | 容器 `mmhusky` |
|---|---|---|
| OS | Ubuntu 24.04 | Ubuntu 20.04 (focal) |
| ROS | Jazzy（不使用） | Noetic |
| Python | conda 3.14 | 系统 Python 3.8.10 |
| GPU | RTX 2080 Ti | 同（`--gpus all`） |
| PyTorch | - | 1.8.1+cu111 |

> 项目自带的 Dockerfile / readme 面向 ROS melodic + Python 3.7 + PyTorch 1.7.1，与当前环境不一致，未按其构建。

## 2. 容器

- 当前镜像：`mm_husky:backup-20260921`（由旧容器 `docker commit` 而来，含手动安装的 torch 等）。
- 原始镜像：`mm_husky:noetic`（不含 torch，不建议直接使用）。
- 创建命令：

```bash
docker run -d --name mmhusky --gpus all --network host --privileged \
  -e DISPLAY=${DISPLAY:-:0} -e NVIDIA_DRIVER_CAPABILITIES=all \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v /home/yanbochao/projects/mm_husky_ws:/root/mm_husky_ws \
  mm_husky:backup-20260921 sleep infinity
```

- 进入容器：

```bash
docker exec -it mmhusky bash
source /opt/ros/noetic/setup.bash
source /root/mm_husky_ws/devel/setup.bash
```

- 若主机上删除/重建了工作区目录，容器内的挂载会失效（看到空目录），需要重建容器。
- 容器内的改动不会自动保存到镜像；重要改动后请 `docker commit mmhusky <镜像名>`。

## 3. Python 依赖（容器内 pip 安装）

版本参考 `src/requirments.txt`，并针对 Python 3.8 调整：

```bash
pip3 install numpy==1.21.6 pybind11==2.13.6 gym==0.18.0 cloudpickle==1.5.0 \
  stable-baselines3==0.10.0 wandb==0.10.11 protobuf==3.20.3 "ray[default,rllib]==1.6.0" \
  hpbandster==0.7.4 ConfigSpace==0.7.1 supersuit==3.8.1 vit-pytorch==1.5.1 einops==0.6.1 \
  defusedxml roslibpy==1.8.1 seaborn==0.12.2 pandas==1.3.5 matplotlib==3.5.3 scipy==1.7.3 \
  tensorboard==2.11.2 pillow==9.5.0 \
  "git+https://github.com/dhonerkamp/pyastar.git@4303b3d200f91016bbccbfdfc43cdc3b67fc6264#egg=pyastar"
```

注意：`ConfigSpace` 最新版要求 Python ≥ 3.9，必须固定为 0.7.1。

## 4. catkin 工作区

`.catkin_tools` 原配置指向他人机器的 Python 3.7 路径，已改为：

```bash
catkin config --cmake-args -DCMAKE_BUILD_TYPE=Release \
  -DPYTHON_EXECUTABLE=/usr/bin/python3 \
  -DPYTHON_INCLUDE_DIR=/usr/include/python3.8 \
  -DPYTHON_LIBRARY=/usr/lib/x86_64-linux-gnu/libpython3.8.so
```

编译：

```bash
cd /root/mm_husky_ws
source /opt/ros/noetic/setup.bash
catkin build
```

结果：35 个包全部成功（5 个带警告）。`modulation_rl` 生成 `pybindings*.cpython-38-*.so`，`import modulation` 正常。

## 5. 验证

```bash
nvidia-smi -L
python3 -c "import torch,gym,stable_baselines3,wandb,ray,pyastar,rospy; print(torch.cuda.is_available())"
```

## 6. 已知问题 / 注意事项

- 未在容器内运行过 Gazebo 仿真与训练脚本，仅验证了依赖导入与编译。
- rosdep 缺少 `multimaster_launch`、`nmea_comms`（Husky 真机相关）与 `range_sensor_layer`（`modulation_rl` 依赖），未影响编译，若运行时用到需另行安装。
- 不想登录 wandb 时先执行 `wandb disabled`。
- `--privileged` 权限较宽，可按需收紧。
- 工作区根目录下的 `modulation_rl(复件)` 是 `src/modulation_rl` 的副本，未参与构建。
- 备份镜像 `mm_husky:backup-20260921` 为重建前旧容器的状态，确认无问题后可删除。
