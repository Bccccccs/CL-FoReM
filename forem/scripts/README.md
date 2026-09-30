# 入口脚本

放启动、数据采集、训练和评测入口。算法逻辑在../src，配置在../config，日志和产物分别写../logs与../results。入口应明确工作目录，不依赖从哪个目录调用。

当前只有目录说明，没有已实现的实验入口；容器基础入口仍为../docker/run.sh。

## 已有入口（task0）

- `check_feedback.py`：录制 /clock、/joint_states、控制器 state，可发一条平滑两点轨迹，输出 CSV 与 summary.json。
- `run_task0_smoke.sh RUN_ID [参数]`：fresh 启动 → 检查 → 停止自己的仿真 → manifest。用法见 [ENV.md](../ENV.md)。

## task0.7 增补

- `task0_proc.py`（容器内）：按 pid+启动时间身份启动/停止本次进程，检查外来 ROS/Gazebo 进程。
- `task0_manifest.py`：写 manifest（全部可执行源码 sha256、镜像、命令与各阶段退出码）。
- `task0_validation.py`：验收纯数据判定（`evaluate_feedback`），由 `check_feedback.py` 使用；测试在 `../tests/`。
- `bag_to_csv.py`、`analyze_task0_feedback.py`：高频 bag 转 CSV 与连续步分析（速度/位置高频残差、交替比例）。
- `regress_task0_smoke.py`：入口失败路径回归（非法/重复 run-id、并发、启动失败、INT/TERM、清理失败）。
