# FoReM 运行环境

2026-10-19重写为当前状态（旧版188行按时间堆叠的Task0–Task4记录已备份到`/home/ybc/projects/CL-FoReM-reset-backups/20261019-doc-fix/`，其中task1/task2/视觉惯性相关内容已随文档清理删除，[SRC-0321](doc/SOURCES.md#src-0321)）。以下为2026-10-19只读核查（`docker ps`、`docker images`、`docker inspect`、`nvidia-smi`）。

## 硬件

4×NVIDIA RTX PRO 6000 Blackwell Server Edition（每张约96 GB，驱动590.48.01，CUDA 13.1）；2×Xeon Gold 6530共64核；内存251 GB；/home空闲约19 TB。宿主不安装ROS；Docker命令用`sg docker -c '<命令>'`。

## 容器

|容器|镜像|挂载要点|用途|
|---|---|---|---|
|`forem-dev`|`mm_husky:node01`（ROS Noetic、Gazebo 11、torch 2.7.1+cu128、ray 1.13）|`forem/`→`/root/mm_husky_ws`|阶段一主容器：task0环境、task3迁移链路、task4.8、task6.1、task5.5（cbl自写SAC）|
|`forem-t5-pr2`、`forem-t5-husky`|`dhonerkamp/mobile_rl:11.1-latest`（上游N²M²镜像，melodic、torch 1.7.1、ray 1.6）|`husky/src`、`mobile-rl/`只读参考；`forem/logs|results|build/task5`|task5 A（PR2）/B（Husky原版RLlib）|
|`forem-t6-husky-gz`、`forem-t6.4-husky`、`forem-t6.4-pr2`|同上|同上，另挂task6结果目录|task6.2 / task6.4 Gazebo训练与评估|

以上容器均为阶段一使用，长期保活；使用或停止前先核实其中是否有其他Agent的进程，不停止未经核实的任务。task7尚未建立自己的容器（ManiSkill可行性待冒烟，见[task7](doc/tasks/task7/TASK.md) U13）。

## 入口

- 创建/启动`forem-dev`：`forem/docker/run.sh`（镜像可由`FOREM_IMAGE`覆盖，`FOREM_GPU=1`挂GPU）。
- 各任务的运行命令、冻结配置、监控与停止方法以对应任务的PROCEDURE/RESULTS为准，本文不重复维护：[task0](doc/tasks/task0/RESULTS.md)、[task3](doc/tasks/task3/RESULTS.md)、[task4](doc/tasks/task4/RESULTS.md)、[task5](doc/tasks/task5/RESULTS.md)、[task6](doc/tasks/task6/RESULTS.md)。
- 已删除任务（task1、task2、视觉惯性定位）对应的脚本与配置仍在`forem/scripts`、`forem/config`中，未清理，不再作为可用入口，见[config/README](config/README.md)。
