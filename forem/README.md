# FoReM

我们的开发、构建和实验目录。共同约定见[根AGENTS.md](../AGENTS.md)，研究与交接入口见[doc/README.md](doc/README.md)，运行环境见[ENV.md](ENV.md)。

项目分两阶段：阶段一“CBL复现”（task0、task3–task6，已有实现、训练与评估结果）；阶段二“世界模型闭环”（task7，目前只有设计文档，尚未实施）。

|目录|放什么|现状|
|---|---|---|
|`src/`|仿真、ROS包与算法实现|含task0固定底座UR5包、task3迁移的Husky+UR5核心（`modulation_rl`等）|
|`config/`|环境、控制器与实验配置|按任务分目录，部分属于已删除任务，见[config/README](config/README.md)|
|`scripts/`|启动、采集、训练、评测入口|含阶段一各任务入口；task1/task2/旧task4视觉惯性入口仍在但已停用|
|`docker/`|容器镜像与入口|`run.sh`创建`forem-dev`|
|`doc/`|计划、进度、决策、来源、任务三文档、Agent记录|见doc/README|
|`data/`、`results/`、`logs/`|数据、产物、日志|不入Git|
|`build/`、`devel/`|编译产物|不入Git|

不要把临时脚本、配置、报告和模型散放在项目根目录。`husky/`、`mobile-rl/`、`scwm/`等参考仓库只读。
