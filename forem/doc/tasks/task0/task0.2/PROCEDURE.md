# task0.2 最小包与容器入口 — 流程

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

同一节点的多次运行按run-id追加到RESULTS，历史事实不被新计划覆盖；大量原始日志和轨迹在forem/logs与forem/results，Agent过程记录在doc/agent_logs。不要在节点内另建第四份README/PLAN或重复的reports目录。

## 前置与控制顺序

前置：[上一节点结果](../task0.1/RESULTS.md)满足其TASK完成条件。

建立包、固定底座模型、空场景launch和正常控制器配置；修正容器工作目录和入口。明确控制频率、Gazebo步长、关节限位与力矩限制。先沿用参考PID作为起点，不为制造误差故意降低增益。若稳定性要求调整，保留原值、理由与实测记录。

## 3. 源码与目录选择

首选最小固定安装UR5，保留现有UR5描述、关节限制、传动与惯性来源。先用标准ur_description和参考控制器配置，不必为本轮编译整个modulation_rl、BioIK或Husky导航系统。

建议新增ROS包forem_sim；最终包名可由Claude按实际结构选择并记录：

```text
forem/
  src/forem_sim/            # package.xml、CMakeLists、URDF/Xacro、launch
  config/control/          # UR5正常控制器配置
  config/sim/              # 基准物理/采样设置（如实际需要）
  scripts/                 # 统一启动、最小反馈检查入口
  docker/                  # 仅FoReM环境的入口适配
  results/task0/<run-id>/  # manifest、轨迹和检查结果
  logs/task0/<run-id>/     # 构建/启动/运行日志
```

只复制实际需要的参考文件，记录来源路径、Git提交或独立仓库HEAD、文件哈希及改动。优先使用镜像内已安装包；缺少的源码依赖固定来源版本并在forem内管理。不要把7GB参考src整体复制，也不要通过可写源码链接实现隔离。

参考线索：husky/src/husky_ur5/config/ur5_controllers.yaml、launch/inc/load_ur5.launch.xml及URDF中的EffortJointInterface。原版完整模型包含Husky、激光、夹爪、modulation_bumper等依赖；它不是可直接复制后启动的最小UR5场景。首轮可以不装夹爪和传感器，明确记录末端参考坐标系。

UR5实际运动关节必须使用力矩接口，不能用直接设置关节位置代替物理执行。底座通过固定安装约束到世界；不要把整台机械臂标成static导致关节也无法运动。通过展开URDF和实际运动验证固定方式，不能只凭参数名认定正确。


## 4. 先修正基础容器入口

当前forem/docker/run.sh仅经过bash语法检查，未经过启动验收。有两个已知适配点：

1. 镜像WORKDIR为/root/mm_husky_ws/src/modulation_rl/scripts；FoReM没有这个目录。创建容器和docker exec都应显式使用/root/mm_husky_ws等真实目录。不要为绕过问题建立假的旧源码目录。
2. 镜像内/usr/local/bin/mm-entrypoint会加入旧modulation_rl的PYTHONPATH和Gazebo资源路径。FoReM的入口应只source ROS和本目录devel、加载新项目资源。修改宿主复制的entrypoint.sh不会自动改变镜像内入口；需要在创建容器时显式使用挂载的新入口，或构建专用派生镜像。记录所用方法。

默认独立容器名forem-dev。保留bridge网络，不使用host网络复用旧ROS/Gazebo；不同容器可以使用各自内部11311/11345，但须检查环境与进程实际隔离。只挂载forem，不挂载旧devel或整个根工作区作为新源码。

首轮固定机械臂、无视觉传感器，不需要训练GPU。现有脚本默认暴露所有GPU，Claude可以移除该默认依赖或改为可选；不要无理由占用全部GPU。无GUI启动优先，必要时用xvfb；GUI是否可用不作为验收条件。

沿用已有镜像作为基础，不默认重建耗时的全部Torch/ROS镜像。缺依赖时仅在新容器或新派生镜像补齐并记录；派生镜像使用新tag，不覆盖mm_husky:node01。


## 输出与异常处理

将配置标识、实际命令、退出结果和证据追加到本节点RESULTS；出现失败先记录并定位，不以父节点已有计划替代验收，不进入依赖该结果的后续步骤。仅处理自己的进程。

## Agent模型与推理强度

- Codex：GPT6.1sol，低（low）/平台默认。
- Claude：Sonnet5.5，低/平台默认；本轮环境执行由Claude负责。
- 无特殊推理要求；跨模块排错按具体问题提高到中等，复杂控制稳定性问题才考虑高强度，并记录理由。实际模型和档位在结果中注明，无法核实写未知。
