# task0.1 基础环境核对 — 流程

状态：计划，以下操作尚未执行。

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

## 前置与控制顺序

先读父TASK、根AGENTS并登记Claude任务。

检查Git状态、容器与占用、镜像ID、ROS/Gazebo版本、必要控制器和UR描述包。核对系统Python与默认Python的实际路径/版本及ROS模块导入；Noetic apt扩展模块可能与默认Python3.10不兼容，ROS工具/采集可使用经过核验的/usr/bin/python3，不为本轮强行统一学习与ROS解释器。

## 2. 已知事实与接手核验

工作区宿主路径：/home/ybc/projects/CL-FoReM。开发目录：该路径下forem；独立容器计划挂载forem到/root/mm_husky_ws。

2026-09-30只读核对结果：

|项目|已知状态|
|---|---|
|镜像|mm_husky:node01，ID sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430|
|版本|旧容器实测Gazebo Classic11.15.1、ROS Noetic、默认Python3.10.18|
|控制依赖|effort-controllers0.22.0、gazebo-ros-control2.9.3已在旧容器查到|
|控制接口|参考UR5模型配置EffortJointInterface；eff_joint_traj_controller类型为effort_controllers/JointTrajectoryController|
|原版|husky/src/modulation_rl为1ccedd0，371个文件内容已核验一致|
|FoReM|尚无算法代码和新构建产物，forem-dev尚未创建/验收|

上述镜像、容器和仓库状态须接手重新检查。镜像tag可变；核对镜像ID，并记录新容器实际.Image。如果旧容器.Image与tag不同，不把它们的依赖核验混为一谈。

接手先读根AGENTS、forem/ENV.md、doc总计划/决策/进度及相关日志；重读最新Git状态，保留Claude之前Git整理提交与其他Agent改动。在forem/doc/PROGRESS.md登记ENV-SETUP，负责人Claude、状态active；建立自己的agent_logs/YYYYMMDD-claude-env-setup.md，不替Codex修改历史核验结论。


## 输出与异常处理

将配置标识、实际命令、退出结果和证据追加到本节点RESULTS；出现失败先记录并定位，不以父节点已有计划替代验收，不进入依赖该结果的后续步骤。仅处理自己的进程。

## Agent模型与推理强度

- Codex：GPT6.1sol，低（low）/平台默认。
- Claude：Sonnet5.5，低/平台默认；本轮环境执行由Claude负责。
- 无特殊推理要求；跨模块排错按具体问题提高到中等，复杂控制稳定性问题才考虑高强度，并记录理由。实际模型和档位在结果中注明，无法核实写未知。
