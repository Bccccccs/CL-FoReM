# task0 环境配置 — 流程

状态：review。task0.1–0.5初次搭建、0.6审核、0.7修正、0.8容器清理、0.9/0.11复核、0.10修正均已交付；task0.12（修正task0.11新P2）执行中。子任务实际状态以PROGRESS和各子RESULTS为准，父任务done需全部关闭复核发现。

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

同一节点的多次运行按run-id追加到RESULTS，历史事实不被新计划覆盖；大量原始日志和轨迹在forem/logs与forem/results，Agent过程记录在forem/doc/agent_logs。不要在节点内另建第四份README/PLAN或重复的reports目录。

## 子任务总表（顺序、依赖、负责人、验收入口）

每个子任务在本目录内都有自己的TASK/PROCEDURE/RESULTS三文档；依赖满足后才进入下一节点，“状态”取自PROGRESS，编号不代表通过。

|节点|名称|依赖|负责人|状态|流程与结果|说明|
|---|---|---|---|---|---|---|
|[task0.1](task0.1/TASK.md)|基础环境核对|—|Claude|review|[流程](task0.1/PROCEDURE.md) · [结果](task0.1/RESULTS.md)|核验ROS入口与解释器|
|[task0.2](task0.2/TASK.md)|最小包与容器入口|0.1|Claude|review|[流程](task0.2/PROCEDURE.md) · [结果](task0.2/RESULTS.md)|UR5模型/控制配置与容器入口|
|[task0.3](task0.3/TASK.md)|独立构建|0.2|Claude|review|[流程](task0.3/PROCEDURE.md) · [结果](task0.3/RESULTS.md)|forem_sim构建|
|[task0.4](task0.4/TASK.md)|启动与反馈|0.3|Claude|review|[流程](task0.4/PROCEDURE.md) · [结果](task0.4/RESULTS.md)|暂停生成、初始姿态、控制器与物理推进顺序|
|[task0.5](task0.5/TASK.md)|简单运动与重复启动|0.4|Claude|review|[流程](task0.5/PROCEDURE.md) · [结果](task0.5/RESULTS.md)|发送指令、采样、两次独立启动|
|[task0.6](task0.6/TASK.md)|独立审核|0.1–0.5|Codex（子Agent做代码审核）|done|[流程](task0.6/PROCEDURE.md) · [结果](task0.6/RESULTS.md)|发现1kHz振荡与验收漏项|
|[task0.7](task0.7/TASK.md)|审核问题修正与重新验收|0.6|Claude|review|[流程](task0.7/PROCEDURE.md) · [结果](task0.7/RESULTS.md)|振荡定位与最小修正→验收补齐→运行管理→报告更正/最终复测；推荐medium|
|[task0.8](task0.8/TASK.md)|废弃容器清理|用户确认|Codex|done|[流程](task0.8/PROCEDURE.md) · [结果](task0.8/RESULTS.md)|保留forem-dev；不恢复旧容器；常规low|
|[task0.9](task0.9/TASK.md)|修正后独立复核|0.7|Codex（子Agent做代码审核）|done|[流程](task0.9/PROCEDURE.md) · [结果](task0.9/RESULTS.md)|振荡修正通过；4项失败路径待修|
|[task0.10](task0.10/TASK.md)|task0.9复核问题修正|0.9|Claude|review|[流程](task0.10/PROCEDURE.md) · [结果](task0.10/RESULTS.md)|进程所有权、高频分析严格校验、按窗口评价|
|[task0.11](task0.11/TASK.md)|四项修正的最终复核|0.10|Codex（子Agent做代码审核）|done|[流程](task0.11/PROCEDURE.md) · [结果](task0.11/RESULTS.md)|原4项关闭；新P2：中断时采集器遗留|
|[task0.12](task0.12/TASK.md)|task0.11复核P2修正|0.11|Claude|active|[流程](task0.12/PROCEDURE.md) · [结果](task0.12/RESULTS.md)|采集器纳入监督与回归；完成后需Codex复核|

顺序：task0.1→0.5为首次搭建（逐级依赖）；0.6审核发现问题→0.7修正；0.8为用户确认后的独立清理（不阻塞修正，但0.7采用清理后的容器状态）；0.9→0.10→0.11→0.12为“复核—修正”循环，直到复核无遗留发现。父结果只汇总，不把“计划已写”当“环境已通过”。

进度追踪见[PROGRESS](../../PROGRESS.md)，Agent过程记录见[agent_logs/task0](../../agent_logs/task0/)及其各子目录。

## 完整控制链路

参考轨迹 → ROS力矩式轨迹控制器 → gazebo_ros_control effort接口 → Gazebo物理关节响应 → joint_states/controller actual → 时间对齐与验收。控制器desired是即时参考，actual必须来自实际执行反馈。

ROS入口与解释器在task0.1/task0.2核验；构建在task0.3；暂停生成、初始姿态、控制器与物理推进顺序在task0.4；发送指令、采样和两次独立启动在task0.5。异常时更新相应子RESULTS与Agent日志，只停止自己的进程。

## 父节点验收与移交

task0.1–task0.5全部有实测完成证据，并且task0.5包含两次启动证据、ENV实际入口和停止方法；同时0.6以来的所有复核发现（含0.11的P2）均有独立关闭证据，父节点才可标done；否则按问题标review/blocked。移交task1，不自动启动误差注入或世界模型。

## Agent模型与推理强度

- Codex：GPT6.1sol，低（low）/平台默认。
- Claude：Sonnet5.5，低/平台默认；本轮环境执行由Claude负责。
- 无特殊推理要求；跨模块排错按具体问题提高到中等，复杂控制稳定性问题才考虑高强度，并记录理由。实际模型和档位在结果中注明，无法核实写未知。

## 执行责任与当前选择

task0初次实施由Claude完成；Codex负责独立审核/复核（0.6、0.9、0.11）与容器清理（0.8），Claude负责修正（0.7、0.10、0.12）。修正与复核依次进行，不并行改同一批文件。可在没有依赖与文件冲突的范围内委派独立子任务，由父Agent在PROGRESS和对应TASK登记，不默认启动多个Agent。

## task0.13 采集器修正独立复核

依赖task0.12提交review，负责人Codex；代码复核子Agent只写专用日志，父Agent核验及运行测试。入口：[TASK](task0.13/TASK.md)、[PROCEDURE](task0.13/PROCEDURE.md)、[RESULTS](task0.13/RESULTS.md)。完整进程检查及证据通过后决定父任务验收状态。
