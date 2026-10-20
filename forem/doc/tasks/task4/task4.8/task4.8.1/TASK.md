# task4.8.1 — 多仿真实例隔离与并行吞吐

> **当前状态（2026-10-19核对）：closed（随task4关闭；未经独立复核）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：**review（2026-10-09子Agent实施完成，待父Agent核验）**。父节点：[task4.8](../TASK.md)；负责人（实现）：Claude子Agent（Sonnet5.5）；父Agent核验：Claude主Agent。独立日志：`forem/doc/agent_logs/task4/task4.8/task4.8.1/`。结果见[RESULTS](RESULTS.md)。

## 目标

使同一台机器/同一forem-dev容器可**并行运行K个互相隔离的Husky+UR5 Gazebo+ROS实例**（每个实例独立ROS master、Gazebo master、HOME/日志、进程身份），供4.8–4.11的多种子/多方法训练同时使用。目前入口`run_task3_core.sh`用共享锁一次只允许一个仿真并拒绝已有ROS进程，不能多开（SRC0173/根AGENTS性能要求4）。

## 范围

- 新增可复用的实例启动/停止/环境工具和隔离回归测试；实测1/2/4/6/8（以及机器允许时更多）实例并发的每实例step吞吐、仿真RTF和CPU占用；NUMA/CPU亲和对吞吐的影响。
- **不**修改`forem/src`下任何文件、不改物理步长/求解器/任务/奖励/观测/动作语义、不训练SAC、不停止他人进程；只增加`forem/scripts`下新文件和本任务文档/日志；不改已有task0–task4旧脚本（只读复用`task0_proc.py`的进程身份机制）。
- 验收：见[PROCEDURE](PROCEDURE.md)；性能数字必须来自实际运行。

## 模型与实际配置

推荐Claude Sonnet5.5、推理medium（并发隔离、进程清理和端口/资源核对需追踪完整因果链）；Codex等价GPT6.1sol medium。本任务实际委派配置：Claude子Agent，模型Sonnet5.5，推理强度由平台默认（记录以子Agent日志为准，无法核实则“未知”）。

依据：[SRC0173](../../../../SOURCES.md#src-0173)（原并行隔离需求）、[SRC0181](../../../../SOURCES.md#src-0181)、根AGENTS性能优化要求。
