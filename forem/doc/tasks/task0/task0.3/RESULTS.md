# task0.3 独立构建 — 结果

> **当前状态（2026-10-19核对）：done（task0.13累计独立复核通过）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：review（Claude已执行并自测满足完成条件，待父节点核验；2026-09-30）。

## 实际执行记录（执行后按run-id追加）

### run-id t0.3-r1

- 日期、Agent、模型/强度：2026-09-30 10:25–10:28 +08:00，Claude，Sonnet5.5，强度平台默认（具体档位未知）。
- 输入与前置：task0.2 t0.2-r1 满足完成条件；镜像 `mm_husky:node01`（ID `sha256:e674db49…dfc430`）；Git main `93e3c2f`（新文件未提交）。`docker/run.sh` sha256 `b6afb886…e69e`，`docker/forem-entrypoint.sh` sha256 `55bf5e0b…3fe`（其余源文件哈希见 `forem/logs/task0/t0.2-r1/sha256.txt`；t0.3 哈希见 `t0.3-r1/sha256.txt`）。
- 容器创建：`sg docker -c 'bash forem/docker/run.sh up'`，退出 0。`docker inspect forem-dev`：镜像 ID 与上同（实际 `.Image` 已记录，与 tag 一致）；WorkingDir `/root/mm_husky_ws`；Entrypoint `/usr/local/bin/forem-entrypoint`；网络 bridge；**仅有两个挂载**：`/home/ybc/projects/CL-FoReM/forem`→`/root/mm_husky_ws`（rw）、`forem/docker/forem-entrypoint.sh`→入口（只读）。旧容器 `mmhusky-node01`、`mmhusky-node01-gz` 全程 Up，未触碰。
- 构建命令（在 forem-dev 内，以宿主 uid 1004 执行）：`catkin init`；`catkin config --extend /opt/ros/noetic --cmake-args -DPYTHON_EXECUTABLE=/usr/bin/python3`；`catkin build forem_sim -j2 -p1`。结果：`All 2 packages succeeded`（含 catkin_tools_prebuild），无 warning，退出 0，耗时 3.6 s。随后 `catkin clean -y -b -d` 后干净重建，同样成功、退出 0、3.4 s（`rebuild.log`）。日志：`forem/logs/task0/t0.3-r1/{build,rebuild,verify}.log`；catkin 原始日志在 `forem/logs/{catkin_tools_prebuild,forem_sim}/`。
- 检查结果：
  - 新入口下新 shell：`rospack find forem_sim` → `/root/mm_husky_ws/src/forem_sim`；`ur_description` 来自 `/opt/ros/noetic/share`；`ROS_PACKAGE_PATH=/root/mm_husky_ws/src/forem_sim:/opt/ros/noetic/share`；`CMAKE_PREFIX_PATH=/root/mm_husky_ws/devel:/opt/ros/noetic`；`PYTHONPATH` 仅 ROS dist-packages；环境中无 modulation/husky_ur5 相关变量；`roslaunch --nodes forem_sim ur5_sim.launch` 列出 4 个节点；`start_controllers.py` 已安装到 devel。
  - 输出位置：`forem/build`、`forem/devel`、`forem/.catkin_tools`，属主为宿主用户 uid 1004（无 root 属主文件）；CMakeCache 中无 `/husky/`、`modulation_rl` 引用；对 devel/build 的 “husky” 字符串检索只命中工作区路径名 `mm_husky_ws`（挂载点名称），不指向 Husky 包或旧 devel。
  - `PYTHON_EXECUTABLE=/usr/bin/python3`（3.8，与 ROS Noetic apt 模块一致）；`CMAKE_BUILD_TYPE` 空（纯 Python/资源包，无编译）。
- 本节点发现并修正的入口问题（均已写入 run.sh/入口脚本）：
  1. `/root` 在镜像内为 700，宿主 uid 无法进入 `/root/mm_husky_ws`（“Permission denied”）；`up` 后加 `docker exec -u 0 … chmod 711 /root`，仅改容器层，不改镜像。
  2. `source devel/setup.bash` 会把入口脚本的命令参数当作自己的参数转给 `_setup_util.py`，报 “usage:: command not found”；入口先保存参数并 `set --` 再 source，最后 `exec "${cmd[@]}"`。修正后重新验证通过（verify.log 追加段）。
  3. exec/shell 改为以宿主 uid 运行并置 `HOME=/tmp/forem-home`，避免 root 属主的构建产物。
- 完成条件核对：新容器仅挂载 FoReM ✔（另有只读入口脚本挂载）；构建退出 0 ✔；包路径与输出不指向 Husky 或旧 devel ✔。
- 限制与遗留：仅证明包可被构建、解析；未启动 Gazebo/ROS master；`start_controllers.py` 尚未运行；该容器正在运行（`forem-dev`，Up），由 `bash forem/docker/run.sh` 管理，未创建 GPU 访问；catkin 日志目录 `forem/logs` 与 task 运行日志共用同一目录树。
- 运行进程交接：容器 `forem-dev`（主进程 `sleep infinity`，ID `973b79b8…a29f`）；停止：`sg docker -c 'docker stop forem-dev'`，恢复：`sg docker -c 'bash forem/docker/run.sh up'`；只处理该容器，不动其他容器。
- 下一步：task0.4，在 forem-dev 内启动仿真并检查反馈。

## 子节点结果

本节点暂未继续拆分。若新增子节点，链接并汇总各子RESULTS，不覆盖历史运行记录。

## Agent模型与推理强度

- Codex：GPT6.1sol，低（low）/平台默认。
- Claude：Sonnet5.5，低/平台默认；本轮环境执行由Claude负责。
- 无特殊推理要求；跨模块排错按具体问题提高到中等，复杂控制稳定性问题才考虑高强度，并记录理由。实际模型和档位在结果中注明，无法核实写未知。
