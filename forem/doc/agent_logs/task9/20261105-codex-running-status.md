# 当前运行核查

2026-11-05T20:26:11+08:00 · TASK9-STATUS-20261105 · Codex · done。用户询问“现在在跑什么”；范围只读进程、容器和原始进度，不启动、停止或修改实验。实际模型/强度未知；推荐Codex GPT6.1sol、Claude Sonnet5.5，low（常规状态核查）。

现场：task9控制器PID1924513；L4718 worker PID1987295、C4719 worker PID2046341，均处于remaining训练，learning.jsonl最近记录分别1,244,000与832,000/3,000,000步；parallel-shards/state.json为RUNNING、L4719等待。GPU进程UUID映射显示L4718在物理GPU0、C4719在物理GPU2。task10 PID970022在物理GPU1，training-budget.json为active，8176/10000 decisions、7168/9000 updates。GPU3空闲。task9最新learning与task10预算文件均在当分钟更新。

证据：`ps -eo pid,ppid,etime,pcpu,pmem,args`、`sg docker -c 'docker ps'`、docker inspect挂载、nvidia-smi compute/gpu查询；原始文件：`forem/results/task9/t9.11-real-program-20261104-r3/formal-L-seed4718/learning.jsonl`、同根formal-C-seed4719/learning.jsonl、parallel-shards/state.json；task10 `/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-long-20261104-s101-r2/training-budget.json`。主进度顶部仍为11月4日旧暂停记录，不能据此认定没有训练。

来源：[SRC-TASK9-STATUS-20261105](../../SOURCES.md#src-task9-status-20261105)。本次无实现改动；数字为快照、继续变化，未验收科学效果。无剩余执行任务。
