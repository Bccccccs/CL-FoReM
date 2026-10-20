# task7.6 — 流程

状态：**review（2026-10-20，四步基准已执行并交付，待Claude/用户复核；未通过/待定项明确保留，[SRC-0399](../../../SOURCES.md#src-0399)）**。目标与验收见[TASK](TASK.md)。

## 递归规则

本节点恰有TASK.md、PROCEDURE.md、RESULTS.md三份主要文档。如需拆分，子任务放在本目录内并继承编号（如task7.6.1），每个子节点同样恰有三文档；本流程须列明子节点顺序、依赖、负责人、三文档链接与验收关系，本RESULTS汇总子RESULTS，不以计划代替实测。编号稳定不复用。独立日志放`agent_logs/task7/task7.6/`，代码、配置、日志、产物分别放`forem/src`、`forem/config`、`forem/logs/task7/<run-id>`、`forem/results/task7/<run-id>`。

## 执行步骤

1. **确定实现与版本**：先查Git、已有进程、容器和nvidia-smi；不启停容器。容器内source ROS/devel，展开实际husky_ur5.xacro，记录URDF/代码/输入哈希。独立URDF FK作CPU float64参考；按B.4复合安装、DH基座Rz(π)、tool0与虚拟TCP链，使用实际软件限位。解析多分支最近q_prev为首选候选，DLS为单种子备选；现有BioIK只作参考。
2. **有界数值与计时**：先运行`--phase check`，至少10000随机q的解析FK/URDF FK对照，再混合奇异/边界/不可达/限位/多分支、失败保持与布尔成功残差拒绝。E7参数扫描而非冻结。未通过的IK/连续性项保留失败和原因，不称全域等价；FK前提不成立时停止计时。随后`--phase timing`按CPU1/2线程、GPU64/32串行运行，输入保留失败，路径内逐检查点依赖q_prev、路径间批量；记录墙钟、process CPU、CUDA event原始数组、分位数、首次/预热及吞吐。`first_wall_s`是核查后的首次measure调用，真正方法首次另由supplement测量，不能混称冷启动。各脚本仅benchmark prototype，未实现环境或完整碰撞。
3. **成本推导**：宿主`python3 forem/scripts/bench_task7_report.py`从计时JSON生成参数扫描CSV/JSON。B8的底盘点位移上界不覆盖机械臂，C按平移/旋转分别向上取整；批次时间不再乘KN。碰撞/渲染/候选/重规划成本未知则显式留参数；B1/B3交互量文档未给数值，不能自行指定训练预算。
4. **给出建议与交接**：运行verify从原始产物重算；保留数值失败、精度分支差、有限重复数与原型限制。把B8/B13/B14及解析/DLS选择写成待用户决定项；B9本次未测，仅列依赖。清理仅本次启动的ROS子进程，核查容器ps与GPU计算列表。结果、命令/退出码/预算/哈希写RESULTS，新增SOURCES项目实测条目，PROGRESS与三文档状态设review，待Claude/用户复核，不改其他任务设计。

开工前：阅读根AGENTS、`forem/doc/README.md`、`PROGRESS.md`、[父TASK](../TASK.md)与本节点三文档；在PROGRESS登记任务ID、负责人、状态与开始时间；在`agent_logs/task7/task7.6/`建立独立日志并写明实际模型与强度。

## 输入与输出

- 输入：见[TASK](TASK.md)“输入”。
- 输出：写入本节点[RESULTS](RESULTS.md)；涉及父设计的结论由父任务回写[父TASK](../TASK.md)，本节点不直接修改父TASK。

## 依赖

依赖task7.5 (A)；运行需用户授权。

## 授权边界

本次2026-10-20有界基准已授权（[SRC-0398](../../../SOURCES.md#src-0398)及本次用户消息）：仅forem-dev，每条命令≤10分钟、累计容器占用≤60分钟、至多1块确认无计算占用的GPU并固定CUDA_VISIBLE_DEVICES。显式OMP/MKL/OPENBLAS=1或2，torch intra同设置、interop=1，无多worker；不安装包、不训练/评估、不启动Gazebo、不启停/重建容器、不修改参考仓库或父/其他子任务设计。超预算先停并记录。完整复跑要先核实资源及本次剩余预算，输出新run-id，不覆盖已有证据。

BioIK若需要ROS，必须先在日志写理由；仅私有master与move_group作IK服务，本次使用11386，避免已有master。记录本次Popen PID/进程组，SIGTERM和finally均清理自己的进程。服务frame错误等无效尝试保留且不用于性能结论。不得停止未经核实的其他进程。

## 异常处理

- 与验收不符时停止并记录，不通过改变任务、奖励、传感器、执行语义或放宽判据求通过。
- 需要改动task7已定设计（[父TASK](../TASK.md)）时，回到父任务由用户确认。
- 新的数值、阈值、方法选择或“已有研究表明”类主张，在[SOURCES](../../../SOURCES.md)登记并链接；没有依据写“待补证据”。
- 发现其他Agent正在修改同一文件，先协调，不覆盖。

## 子任务

暂无。如需拆分，按上方递归规则建立`task7.6.1`等子节点并在此列表登记。

## 交接

完成后在RESULTS写明已完成事项、证据路径、未解决问题与下一步，更新PROGRESS，由父任务核验后再标状态。

## 模型与证据

推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium；原因是坐标、病态数值与计时口径需交叉核对。实际具体模型/强度本次均未知，不把推荐当实际配置。输入参数、工程扫描与实测来源统一见[SRC-0399](../../../SOURCES.md#src-0399)；精确已执行命令、run-id与产物见[RESULTS](RESULTS.md) §7；不存在“计划命令已通过”的推断。
