# task9.2 PROCEDURE — 原语后端下层SAC长训

状态：**active**。依据[TASK](TASK.md)。

## 递归规则声明

遵守根AGENTS项目级任务组织规则：每层恰有TASK/PROCEDURE/RESULTS；如需拆分则在本目录内建task9.2.1…并各自三文档，父列明顺序、依赖、负责人与验收，父结果汇总子结果。当前不拆分。

## 流程

|步|内容|负责人|
|---|---|---|
|1|`sg docker -c 'python3 scripts/task9_long_launch.py'`干跑预检→`logs/task9/t9-long-20261028/preflight.json`|Claude父|
|2|`sg docker -c 'python3 scripts/task9_long_launch.py --execute'`：重跑预检、宿主GPU监控（10s，`gpu.csv`）、4个`docker exec -d`；`launch.json`记argv/容器PID/监控PID；`launch.json`存在即拒绝重启|Claude父|
|3|启动后约10min核查：4进程存活、各GPU有compute、首条诊断（step 1000）出现、日志无异常|Claude父|
|4|首个250k评估后`sg docker -c 'python3 scripts/task9_long_monitor.py'`重算；>48h的run `touch <output>/STOP`并报告用户|Claude父（或接手者）|
|5|运行至结束；按需巡检同monitor|父/接手者|
|6|独立验收与预注册判定|另一Agent（≠父）|

## 监控与停止

- 进度：`learning.jsonl`（每1000转移）、`validation-*.json`、各run日志`logs/task9/t9-long-20261028/<run>.log`、`gpu.csv`。
- 停止某run：`touch /home/ybc/projects/CL-FoReM/forem/results/task9/t9-long-20261028/<run>/STOP`（训练保存`interrupted.pt`后退出）；不要kill -9。
- 恢复（需用户授权）：`--resume <output>/interrupted.pt`同配置同输出。
- 看门狗（训练代码内置）：非有限值或500k后|Q|max>10×500k参考→`diverged.pt`，记“发散停止”。
- 停止GPU监控：`kill <gpu_monitor_host_pid>`（见launch.json）。

## 共同约束

不改奖励/动作/观测/终止/采样与B0/B3定义；不缩步数、环境数、回放、评估；不重试失败run（失败如实记录、报告）；不停止他人进程。
