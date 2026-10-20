# task0.2 最小包与容器入口 — 结果

> **当前状态（2026-10-19核对）：done（task0.13累计独立复核通过）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：review（Claude已完成静态构建与校验，未启动容器/仿真；待父节点核验；2026-09-30）。

## 实际执行记录（执行后按run-id追加）

### run-id t0.2-r1

- 日期、Agent、模型/强度：2026-09-30 10:24–10:26 +08:00（以日志文件时间为准，首稿误写，已更正），Claude，Sonnet5.5，强度平台默认（具体档位未知）。
- 输入与前置：task0.1 t0.1-r1 已满足完成条件；镜像 `sha256:e674db49…dfc430`；Git main `93e3c2f`（新文件均未提交）。
- 新增/修改文件（sha256见 `forem/logs/task0/t0.2-r1/sha256.txt`）：
  - `forem/src/forem_sim/`：`package.xml`、`CMakeLists.txt`、`urdf/ur5_fixed.urdf.xacro`、`worlds/ur5_empty.world`、`launch/ur5_sim.launch`、`scripts/start_controllers.py`。
  - `forem/config/control/ur5_controllers.yaml`。
  - `forem/docker/forem-entrypoint.sh`（新）、`forem/docker/run.sh`（修改）。
- 来源与改动（可追溯）：
  - 机械臂模型：镜像内 apt `ur_description` 1.5.0 的 `ur5_macro.xacro`，参数为宏默认值，`prefix="ur5_"`、`transmission_hw_interface=EffortJointInterface`，与 `husky/src/husky_ur5/urdf/husky_ur5.xacro` 的调用一致；未复制 husky 源码，未含 Husky 底盘、激光、夹爪、MoveIt 插件。husky_ur5 自带 `config/ur5/*.yaml` 与 apt 版哈希不同，但 `husky_ur5.xacro` 只传 prefix，实际用的是 apt 默认，本包同。
  - 控制器：`husky/src/husky_ur5/config/ur5_controllers.yaml`（sha256 `d9821dd6…54ca`）；增益、约束、125 Hz 发布频率、关节名逐字沿用，仅删去 `joint_group_eff_controller` 与夹爪控制器（与参考逐行 diff 仅有一处行尾空格差异）。未为制造误差降低增益。
  - 世界：物理参数取自 `modulation_tasks.world`（ODE quick、50 iters、erp 0.2、步长 0.0005 s、2000 Hz），仅含 sun 与 ground_plane。控制更新频率由 gazebo_ros_control 默认随物理步进，预期 2000 Hz，待 task0.4 实测。
  - 启动顺序（task0.4 使用）：Gazebo 以 paused 启动 → `spawn_model -J` 设初始关节姿态（0, -1.5708, 0, -1.5708, 0, 0）→ `start_controllers.py` 加载两个控制器，在线程中发起 switch，0.5 s 后 `unpause_physics`，等待均为 running。用挂钟时间，因为暂停时 /clock 不前进；此为自写脚本而非 `controller_manager/spawner`，因 switch 必须在 update() 中完成。
- 容器入口修正：`run.sh up` 显式 `-w /root/mm_husky_ws`，`--entrypoint /usr/local/bin/forem-entrypoint`（宿主 `docker/forem-entrypoint.sh` 只读挂载），不再用 `mm-entrypoint`；GPU 改为 `FOREM_GPU=1` 才启用；`shell/exec` 也用新入口与工作目录；`shm-size` 8g→2g；仍为 bridge 网络、仅挂载 forem、容器名 `forem-dev`。新入口只 source ROS 与 `/root/mm_husky_ws/devel`，并置 `GAZEBO_MODEL_DATABASE_URI=""`，不加 modulation_rl 路径。不覆盖 `mm_husky:node01`，未建派生镜像。`bash -n docker/run.sh` 通过；容器**尚未创建**。
- 校验命令（一次性容器 `--rm`，forem 只读挂载，退出码 0；日志 `forem/logs/task0/t0.2-r1/validate.out`，产物 `…/out/ur5_fixed.{urdf,sdf}`）：
  - `rospack find forem_sim` → `/ws/src/forem_sim`；`xacro` 退出 0；`check_urdf` 解析成功，根为 `world`→`ur5_base_link`→…→`ur5_tool0`。
  - 6 个 revolute 关节：`ur5_shoulder_pan/shoulder_lift/elbow/wrist_1/wrist_2/wrist_3_joint`；限位：前三个 effort 150 N·m，后三个 28 N·m，速度 π rad/s；位置限位 ±2π（elbow ±π）。
  - 6 个 transmission 均为 `hardware_interface/EffortJointInterface`；插件仅 `libgazebo_ros_control.so`（`robotNamespace=/`、`legacyModeNS=true`）；关节 damping/friction 均为 0（apt 默认，未改）。
  - `gz sdf -p` 转换成功（退出 0），SDF 中有 `world_to_ur5_base` 固定关节，父为 `world`。
  - `roslaunch --nodes ur5_sim.launch` 列出 gazebo、spawn_ur5、robot_state_publisher、start_controllers 四个节点。
- 完成条件核对：来源可追溯 ✔；入口不依赖旧 modulation_rl 路径 ✔（静态）；机械臂使用力矩接口 ✔（URDF 层）；底座固定 ✔（结构层：world 固定关节、关节数正确）。**底座实际不动、关节实际可动、控制器实际 running 尚未验证，属 task0.4/0.5。**
- 未验证/风险：`-J` 初始姿态在 Gazebo 中是否生效；paused 下的启动顺序是否可行；参考增益（如 wrist_1 p=500，力矩上限 28 N·m）下是否稳定；`$(find forem_sim)/../../config` 在容器 catkin 环境下是否解析正确；`catkin_install_python` 是否影响构建。均在 task0.3/0.4 检验。
- 下一步：task0.3，创建 `forem-dev` 并构建。

## 子节点结果

本节点暂未继续拆分。若新增子节点，链接并汇总各子RESULTS，不覆盖历史运行记录。

## Agent模型与推理强度

- Codex：GPT6.1sol，低（low）/平台默认。
- Claude：Sonnet5.5，低/平台默认；本轮环境执行由Claude负责。
- 无特殊推理要求；跨模块排错按具体问题提高到中等，复杂控制稳定性问题才考虑高强度，并记录理由。实际模型和档位在结果中注明，无法核实写未知。
