# 2026-10-19 Claude：过时文档修正

- 用户要求：检查是否有过时文档会误导Agent；随后确认“按你第三部分的建议处理1–11项，先备份；第12项代码和配置先不动，只在config/README里注明”。
- 执行：Claude（claude-opus-5-5，推理强度未知）。只改文档，不改代码、配置、日志、产物，不触碰运行中的容器。
- 备份：`/home/ybc/projects/CL-FoReM-reset-backups/20261019-doc-fix/before-doc-fix.tar.gz`（268个文件，SHA256见同目录`SHA256SUMS`）。

## 改动

1. 重写`forem/ENV.md`（只保留2026-10-19只读核查的硬件、6个容器及镜像/挂载/用途、入口指引）、`forem/README.md`、根`README.md`（补mobile-rl/archive/mapgen）、`forem/config/README.md`（标明experiments/task1、experiments/exp2、task4/为已删除任务的停用配置）。
2. 在task0、task3–task6共76份节点TASK/RESULTS标题下加“当前状态（2026-10-19核对）”行，纠正仍写active、review或尚未执行的节点；原状态行保留为历史。依据为各节点RESULTS与PROGRESS。
3. task7 TASK：加“前瞻模型”术语说明（首版为运动学模拟、不训练；学习修正项待U21），§1研究问题、U2/U5/U6、§4对照组、§5风险改为一致表述。
4. DECISIONS顶部注明2026-10-16前条目多已被取代；doc/README注明agent_logs是历史记录不是指令。

## 未处理

- 代码与配置（第12项）未动。
- agent_logs、SOURCES历史条目内容未改。
