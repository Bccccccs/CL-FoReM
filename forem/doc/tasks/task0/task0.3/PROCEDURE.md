# task0.3 独立构建 — 流程

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

前置：[上一节点结果](../task0.2/RESULTS.md)满足其TASK完成条件。

启动独立容器，在/root/mm_husky_ws内初始化catkin工作区，仅构建本轮必需包，输出到forem/build和forem/devel。构建时明确source /opt/ros/noetic/setup.bash；必要时显式设置系统Python，不能source旧工作区devel。

## 6. 命令示例（计划，全部尚未执行）

从总工作区调用；下面只说明接口。必须先完成入口修正和源码准备，不能盲目原样执行当前up。

```bash
sg docker -c 'docker ps --format "{{.Names}} {{.Status}}"'
sg docker -c 'docker image inspect mm_husky:node01 --format "{{.Id}}"'
# 修正run.sh的workdir/entrypoint后再执行：
sg docker -c 'bash forem/docker/run.sh up'
sg docker -c 'bash forem/docker/run.sh shell'
```

容器内拟议构建方式（Python路径和catkin可用性先核验）：

```bash
cd /root/mm_husky_ws
source /opt/ros/noetic/setup.bash
catkin init
catkin config --extend /opt/ros/noetic --cmake-args -DPYTHON_EXECUTABLE=/usr/bin/python3
catkin build forem_sim -j2 -p1
source devel/setup.bash
```

-j2/-p1是首次构建的保守起点，不是性能参数。launch名、trajectory消息和反馈检查命令由Claude实现并在ENV/RESULTS中给出实测可用版本，不在本文编造尚不存在的执行入口。


## 输出与异常处理

将配置标识、实际命令、退出结果和证据追加到本节点RESULTS；出现失败先记录并定位，不以父节点已有计划替代验收，不进入依赖该结果的后续步骤。仅处理自己的进程。

## Agent模型与推理强度

- Codex：GPT6.1sol，低（low）/平台默认。
- Claude：Sonnet5.5，低/平台默认；本轮环境执行由Claude负责。
- 无特殊推理要求；跨模块排错按具体问题提高到中等，复杂控制稳定性问题才考虑高强度，并记录理由。实际模型和档位在结果中注明，无法核实写未知。
