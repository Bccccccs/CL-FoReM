# FoReM环境

后续只在forem构建。node01已有镜像mm_husky:node01（ROS Noetic、Gazebo 11、Python3.10）；宿主不安装ROS。现有mmhusky-node01/mmhusky-node01-gz是旧运行环境，本次未停止、未复用为新项目验收。

本目录src尚无算法代码，build/devel为空，未适配原版、未构建、未运行仿真。docker/保留基础镜像配置，不保留旧研究流程。

新入口docker/run.sh使用独立容器forem-dev，挂载本目录为/root/mm_husky_ws。尚未启动。将来用 sg docker -c 'bash forem/docker/run.sh up' 创建，再用shell/exec检查；原版源码、第三方依赖和资源须先按新目录准备，不会自动读写husky。编译输出将落在forem/build与forem/devel。

## 首轮选定技术栈（2026-09-30核对）

Gazebo Classic11.15.1 + ROS Noetic + Python3.10.18，沿用mm_husky:node01镜像。镜像ID为sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430；版本查询在旧容器mmhusky-node01执行，仅证明已有环境依赖，不代表FoReM新环境通过。

UR5候选模型使用EffortJointInterface，eff_joint_traj_controller为effort_controllers/JointTrajectoryController；已安装effort-controllers0.22.0、gazebo-ros-control2.9.3。先测正常关节跟踪，再单独引入指令时延或响应滞后。

接下来环境配置顺序：核对并固定镜像 → 在FoReM准备最小UR5模型及必要依赖 → 使用独立容器构建 → 启动空场景和控制器 → 确认实际关节反馈及时间对齐。除已有镜像版本和源码接口核对，其余尚未执行。
