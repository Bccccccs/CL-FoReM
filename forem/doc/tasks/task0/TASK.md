# task0 环境配置 — 任务

> **阶段一（CBL复现）· 基础设施**（2026-10-16归类）：建立`forem-dev`容器与ROS Noetic/Gazebo环境，后续Husky迁移在其上进行。原验收范围是固定底座UR5，done。原task1（正常跟踪）、task2（人为时延）不属于CBL复现，已按用户确认删除，备份见[SRC-0321](../../SOURCES.md#src-0321)。

状态：done（经task0.13独立复核；当前固定底座UR5环境范围验收通过）。

历史状态记录：状态：review；Claude已完成初次环境搭建，Codex审核发现问题，下一步执行task0.7修正与重新验收。

## 1. 任务、授权与完成边界

用户要求先配置实现控制误差的环境，并指定由Claude执行。Claude可以在forem内准备最小源码、修改基础入口、补齐必要容器依赖、构建、启动和验证独立仿真。Codex本轮只写交接文档，不代为执行。

交付是一个可重复启动的固定底座UR5物理仿真：空场景、力矩式轨迹控制、真实关节反馈，以及简单轨迹指令能实际驱动机械臂。下一轮才研究正常跟踪误差，然后再加入受控延迟。不要在本轮实现误差注入、IK、SAC或世界模型。

不修改husky原版及参考仓库，不沿用旧devel/build。不得停止或重建他人的容器/进程，不推送、不合并、不自动提交。正常构建适配可直接处理并记证据；需要改变研究任务或技术栈时先记录原因并告知用户。


## 大致路线

task0.1基础核对 → task0.2最小包/入口 → task0.3独立构建 → task0.4启动反馈 → task0.5运动与重复启动 → task0.6独立审核 → task0.7修正与重新验收。

技术栈：Gazebo Classic11.15.1 + ROS Noetic + UR5力矩式轨迹控制器。先固定底座、空场景、正常控制，不加入执行扰动。

## 交付与验收

交付最小包、正常控制配置、可重复入口、ENV实测命令、两次独立启动证据；各子节点完成条件和最终检查见[流程](PROCEDURE.md)。结果汇总于[RESULTS.md](RESULTS.md)。

## Agent模型与推理强度

- Codex：GPT6.1sol，低（low）/平台默认。
- Claude：Sonnet5.5，低/平台默认；本轮环境执行由Claude负责。
- 无特殊推理要求；跨模块排错按具体问题提高到中等，复杂控制稳定性问题才考虑高强度，并记录理由。实际模型和档位在结果中注明，无法核实写未知。

## 给Claude的启动提示词

```text
请接手/home/ybc/projects/CL-FoReM的task0环境配置并执行。
推荐Claude Sonnet5.5，低/平台默认强度；特殊排错提高强度时记录原因。
先读根AGENTS、forem/doc/README、PROGRESS、DECISIONS、forem/ENV，以及forem/doc/tasks/task0/TASK.md、PROCEDURE.md、RESULTS.md。
核对当前Git/容器/进程，登记task0执行任务和自己的独立日志，再按task0.1至task0.5的三文档推进。
整个项目一任务一目录；子任务在父目录内部编号，例如task0/task0.1，更深层为task0/task0.1/task0.1.1。每个节点都必须有TASK/PROCEDURE/RESULTS；继续拆分时先建立文档并更新父流程。
可以顺序自行完成，也可在独立、无共享写冲突的范围内派遣子Agent；给子Agent任务编号、范围、根AGENTS、三文档与日志路径、模型/强度和验收标准。父Agent核验并汇总子RESULTS，不凭自报完成验收。
本轮搭建Gazebo11+ROS Noetic+固定底座UR5力矩控制环境，验证实际关节反馈、简单运动及两次独立启动。只在forem开发构建，不修改参考原版，不停止他人进程，不复用旧devel，不自动提交/push。
先修正镜像WORKDIR与旧入口路径；本轮不实现误差注入、IK、SAC或WM。实际命令/版本/配置/退出结果和证据逐节点写RESULTS，未执行如实标注。
完成更新ENV、PROGRESS、自己的日志与task0结果，交接运行进程的监控和停止方式。
```

## 当前Claude接手入口

初次搭建已经执行，前面的启动提示词保留为历史。当前请执行[task0.7 TASK](task0.7/TASK.md)、[PROCEDURE](task0.7/PROCEDURE.md)、[RESULTS](task0.7/RESULTS.md)，先读[task0.6审核结果](task0.6/RESULTS.md)。高频振荡与验收/清理问题闭环后再独立复核。
