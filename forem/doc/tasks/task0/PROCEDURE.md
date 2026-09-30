# task0 环境配置 — 流程

状态：初次搭建与审核已执行，父任务仍review；task0.7修正与重新验收尚未执行。

## 项目规则在本流程中的执行

本任务遵循根AGENTS的项目级约定：一个任务一个目录，子任务在父目录内按taskN.i递归编号；每个节点都有TASK/PROCEDURE/RESULTS三文档。继续拆分本任务时同时建立子任务三份，并在本流程登记编号、目标、依赖、负责人和验收链接。

可以由当前Agent逐项执行，也可按独立性委派子Agent。委派前写好子TASK和PROCEDURE，附根AGENTS、三文档与独立日志路径，明确模型/推理强度及输出；子Agent填写自己的RESULTS，父Agent核验后汇总。共享改动协调后再写，有依赖步骤不能为并行而跳过前置验收。

具体实现只写forem/src、config、scripts；本目录只存任务文档。所有实测记录用本任务编号与run-id关联，不以目录存在或子Agent完成消息替代通过证据。

## 节点内部文档结构（所有层级必须遵循）

**每一个节点，包括本节点内部拆出的所有子节点，均有且使用以下三个主要文档：**

```text
<node>/
  TASK.md          # 任务：目标、范围、假设、大致路线、交付与验收
  PROCEDURE.md     # 流程：详细控制/执行步骤、输入输出、顺序、异常处理
  RESULTS.md       # 结果：实际配置、命令、证据、验收、结论与未解决问题
  <child-node>/    # 若继续拆分，该子节点也必须包含同样三个文档
```

不能只在父节点写三份，然后让子节点只剩脚本或一段口头说明。创建子节点时同时建立这三份；未执行的RESULTS明确标注尚未执行，不编造结果。每份任务/流程/结果同时给出Codex与Claude的模型和推理强度推荐。

父流程列出子节点顺序、依赖和进入/完成条件，并链接子节点三份文档；具体操作在对应子流程里维护。子节点再拆分时重复本规则。子结果记录实际证据，父结果汇总子结果，不复制原始日志。节点编号用于顺序，不能代表验收通过。

同一节点的多次运行按run-id追加到RESULTS，历史事实不被新计划覆盖；大量原始日志和轨迹在forem/logs与forem/results，Agent过程记录在doc/agent_logs。不要在节点内另建第四份README/PLAN或重复的reports目录。

## 子任务入口、依赖与负责人

|节点|任务|流程|结果|
|---|---|---|---|
|task0.1 基础环境核对|[任务](task0.1/TASK.md)|[流程](task0.1/PROCEDURE.md)|[结果](task0.1/RESULTS.md)|
|task0.2 最小包与容器入口|[任务](task0.2/TASK.md)|[流程](task0.2/PROCEDURE.md)|[结果](task0.2/RESULTS.md)|
|task0.3 独立构建|[任务](task0.3/TASK.md)|[流程](task0.3/PROCEDURE.md)|[结果](task0.3/RESULTS.md)|
|task0.4 启动与反馈|[任务](task0.4/TASK.md)|[流程](task0.4/PROCEDURE.md)|[结果](task0.4/RESULTS.md)|
|task0.5 简单运动与重复启动|[任务](task0.5/TASK.md)|[流程](task0.5/PROCEDURE.md)|[结果](task0.5/RESULTS.md)|

按task0.1至task0.5依赖执行，每个子节点完成并记录证据后才进入依赖它的下一节点。父结果只汇总，不把“计划已写”当“环境已通过”。

## 完整控制链路

参考轨迹 → ROS力矩式轨迹控制器 → gazebo_ros_control effort接口 → Gazebo物理关节响应 → joint_states/controller actual → 时间对齐与验收。控制器desired是即时参考，actual必须来自实际执行反馈。

ROS入口与解释器在task0.1/task0.2核验；构建在task0.3；暂停生成、初始姿态、控制器与物理推进顺序在task0.4；发送指令、采样和两次独立启动在task0.5。异常时更新相应子RESULTS与Agent日志，只停止自己的进程。

## 父节点验收与移交

task0.1–task0.5全部有实测完成证据，并且task0.5包含两次启动证据、ENV实际入口和停止方法，父节点才可标done；否则按问题标review/blocked。移交task1，不自动启动误差注入或世界模型。

## Agent模型与推理强度

- Codex：GPT6.1sol，低（low）/平台默认。
- Claude：Sonnet5.5，低/平台默认；本轮环境执行由Claude负责。
- 无特殊推理要求；跨模块排错按具体问题提高到中等，复杂控制稳定性问题才考虑高强度，并记录理由。实际模型和档位在结果中注明，无法核实写未知。

## 执行责任与当前选择

主任务task0初次实施由Claude完成并提交review；Codex已完成task0.6审核。当前默认由Claude按task0.7流程顺序修正；可在没有依赖与文件冲突的范围内委派独立子任务。具体委派由父Agent在PROGRESS和对应TASK登记，不默认启动多个Agent。task0.1负责环境核对，task0.2负责UR5模型/控制配置与入口，task0.3构建，task0.4启动反馈，task0.5运动与重复启动；依赖前序完成证据。

## task0.6 用户要求的独立审核

依赖 task0.1–0.5 交付，负责人 Codex /root；独立代码审核由 Codex 子Agent执行，只写专用日志；父Agent负责运行复核与最终验收。输入为现有源码和证据，完成条件是有可核验的审核结论。入口：[TASK](task0.6/TASK.md)、[PROCEDURE](task0.6/PROCEDURE.md)、[RESULTS](task0.6/RESULTS.md)。

## task0.7 审核问题修正与重新验收

依赖task0.6审核交付；拟负责人Claude，顺序自行执行，不自动委派。输入现有源码、审核与原始证据，输出有根因依据的正常配置、可靠验收与清理、纠正报告和全新复测证据。入口：[TASK](task0.7/TASK.md)、[PROCEDURE](task0.7/PROCEDURE.md)、[RESULTS](task0.7/RESULTS.md)。本节点内按安全接手→振荡定位与最小修正→验收补齐→运行管理→报告更正/最终复测推进。task0.7自测全部有证据后进入review，由Codex复核；父任务done还需关闭task0.6发现，旧task0.1–0.5通过不能替代本轮修正验收。推荐Codex GPT6.1sol/Claude Sonnet5.5 medium，跨模块因果核对；实际配置如实记载。

## task0.8 废弃容器清理

负责人Codex；用户明确确认旧任务废弃后执行，已完成；task0.7接手采用清理后的容器状态，不恢复旧任务。入口：[TASK](task0.8/TASK.md)、[PROCEDURE](task0.8/PROCEDURE.md)、[RESULTS](task0.8/RESULTS.md)。推荐GPT6.1sol/Sonnet5.5 low/默认，常规执行。
