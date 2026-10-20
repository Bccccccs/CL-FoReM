# Husky任务精度要求核查

- 用户要求：看看husky任务要求，1mm误差是否可以。
- 2026-10-07T09:25:19.344941+08:00，Codex /root；实际模型/强度未知；推荐GPT6.1sol / Sonnet5.5，medium（需追踪配置、子任务覆盖、Python与C++成功语义）。
- 只读husky参考，所有记录仅forem；不运行ROS/训练，不改源码/协议/后续Task3。
- 当前main/既有dirty；Task3另有文档活动登记，避免修改Task3文件；共享PROGRESS/SOURCES修改前重读并仅追加本项。
- 发现脚本内有modulation（修改后）副本，核查以实际导入modulation路径为准，不混用。

## 核查结果与交接（2026-10-07T09:28:08.384173+08:00）

- 本轮done；证据：`forem/results/task2/husky-task-tolerance-20261007/audit.json`，全部主张见[来源SRC-0017](../../SOURCES.md#src-0017)。
- 普通任务默认25 mm，普通抓取/放置沿用25 mm，抓取前接近50 mm；Hall门/抽屉基础10 mm，部分开启/释放阶段放宽50 mm；Office门20 mm、Office抽屉11.5 mm。实际阈值由TaskGoal传到planner，位置和旋转同时检查。
- 最终绝对位置残差1 mm满足所列位置判据；整体成功还依赖无IK失败/无底盘碰撞、姿态等，不能等同物理抓取已成功。轨迹最近点距离指标不是Task2同步轨迹误差，时延机制未必能显著改变该指标，属于公式推断。
- Husky使用夹爪frame/offset，不能将Task2 wrist动态RMSE直接与Husky目标距离相比；没有执行Husky任务、统计成功率或调参。
- 命令：rg阈值/成功调用；sed读取任务继承、TaskGoal、planner、evaluation、env_utils与robot_config；Python仅存读取文件hash及来源记录。所有读取/记录命令退出0。
- 保留所有其他Agent改动；只改本日志、全局来源台账和本项PROGRESS状态，新增静态审计JSON。没有修改husky源码/Task3文件。
- 共享台账原有SRC-0014、SRC-0015重复编号（并发文档活动），本轮不重编号既有稳定链接；新项使用当前最高编号之后的SRC-0017。此历史冲突未作为本轮结论证据。
- 推荐GPT6.1sol / Sonnet5.5、medium，实际模型/强度未知；剩余必需工作无，后续任务效果测试需独立授权。
