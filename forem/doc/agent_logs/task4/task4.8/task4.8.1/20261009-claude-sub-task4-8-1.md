# task4.8.1：多仿真实例隔离与并行吞吐（Claude子Agent）

- Agent：Claude（主Agent委派的子Agent）
- 状态：review；开始2026-10-09约10:10，结束约11:05（容器时间同宿主）
- 用户要求/授权边界：按`tasks/task4/task4.8/task4.8.1/{TASK,PROCEDURE}.md`与根AGENTS性能优化要求；只新增`forem/scripts`下文件、本任务文档/日志、`logs|results/task4/t4.8.1-*`；不改`forem/src`、旧脚本、PROGRESS/SOURCES/README、父文档；不碰git；不训练。
- 已读：根AGENTS、forem/AGENTS、ENV、husky_core.launch、run_task3_core.sh、task0_proc.py、task3_env.py、docker/run.sh。

## 执行记录与证据

新增文件：`forem/scripts/scwm_instance.py`、`regress_scwm_instances.py`、`bench_scwm_parallel.py`；改写`RESULTS.md`与`TASK.md`状态行（本任务目录）。
关键命令（均经`sg docker -c 'bash forem/docker/run.sh exec ...'`，rc均0）：
- 手动冒烟：`scwm_instance.py start --inst 0/1 --run-id t4.8.1-smoke-a`，status/list，stop（残留为空）。
- 回归：`regress_scwm_instances.py --run-id t4.8.1-regress-r1`、`-r2`，26项PASS。
- 基准：`bench_scwm_parallel.py --run-id t4.8.1-bench-k{1,2,4,6,8,12,16,24,32}-r1`，K=6另有none-r2、numa-r1/r2、part-r1/r2。
- 测量期间在`logs/task4/.sim_exclusive`写了占用说明（10:17起），结束后已删除。
细节、表格、限制见任务RESULTS。观察：容器内另有主Agent的`bench_scwm_update.py`曾短时运行（非我启动，未触碰）；容器内最终仅余`sleep infinity`。

## 交接

已完成：工具、回归、K=1–32吞吐、K=6 NUMA对比、失败路径。未解决：见RESULTS§5。下一步：父Agent核验后决定实例数与核集；并行训练接入`scwm_instance.py exec`。核验方法：重跑`regress_scwm_instances.py`（需无其他仿真，约3分钟）。无运行中的任务。

## Agent模型与推理强度

- Codex推荐：GPT6.1sol，medium（并发隔离与清理因果链）。Claude推荐：Sonnet5.5，medium。
- 实际执行：Claude子Agent，Sonnet5.5，推理强度未知（平台默认，无法核实）。

## 任务归属与委派

- 任务：task4.8.1，目录`forem/doc/tasks/task4/task4.8/task4.8.1/`（TASK/PROCEDURE/RESULTS）。
- 父任务task4.8，负责人Claude主Agent；本节点由子Agent顺序执行，父Agent待核验。
