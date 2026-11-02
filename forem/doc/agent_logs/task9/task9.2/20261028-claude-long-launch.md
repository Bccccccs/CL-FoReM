# 2026-10-28 Claude — task9.2 长训启动

- Agent：Claude父（claude-opus-5-5，推理强度未知）；本步无子Agent。
- 用户要求：“启动训练”（SRC-1316），对象为task9.1 P3所列task9.2。
- 授权边界：B0/B3×种子4718/4719×3M，4卡各1 run；协议不变；首个250k重算，>48h者STOP报告；不自动续训、不跑task9.3。

## 已做

1. SOURCES登记SRC-1316；建task9.2三文档；PROGRESS/README/task9父三文档更新。
2. 生成`config/task9/lower_train_{B0,B3}_prim_seed{4718,4719}.json`（仅seed差异）；新写`scripts/task9_long_launch.py`（预检/冻结快照/启动）与`scripts/task9_long_monitor.py`（只读巡检与外推）。
3. 干跑预检通过（`logs/task9/t9-long-20261028/preflight.json`）。首次`--execute`在宿主建结果目录时因`results/task9`归root而PermissionError，发生在启动任何进程之前（无GPU监控、无docker exec）；删去宿主mkdir（训练代码在容器内自建输出目录），重跑`--execute`成功，`launch.json` status=LAUNCHED。

## 运行中

见`logs/task9/t9-long-20261028/launch.json`（容器PID、GPU监控宿主PID、argv）。巡检：`sg docker -c 'python3 scripts/task9_long_monitor.py'`。停止某run：其输出目录`touch STOP`。

## 下一步

启动后核查首条诊断；首个250k评估后重算外推（L2）；独立验收待定。

## 2026-10-28 11:55 L2 250k重算

4 run完成250k评估；外推B0 23.1/23.3h、B3 9.3/9.6h，均<48h，全部继续。评估wall≈1300–1360s（smoke为557s），检查点19.6–25.9GB且增长，磁盘仍够。详见task9.2 RESULTS“L2”。下一步：后台等首个run结束（预计B3约19:30），再核原件。

## 2026-10-28 19:27 B3完成

B3两种子都到3M，正常结束（9.49/9.51h）；验证3M为0.63/0.64，按预注册判据初步不退化。B0在1.25M，Q均值−42/−30，仍在运行，预计10-29 09:00前后结束。后台等待B0结束。

## 2026-10-28 22:31 B0-seed4718 看门狗发散停止

1.645M处|Q|max超过500k参考的10倍，自动保存diverged.pt并退出（预注册“发散停止”）；没有重启。B0-seed4719继续（4.5×）。后台等它结束。

## 2026-10-29 12:05 全部结束，派独立验收

B0-seed4719于10-29 04:35在2.463M处被看门狗发散停止。父的后台等待循环在进程数为0时比较出错、未通知（只影响通知）；父12:05手动核查发现，已停止该循环与宿主GPU监控（PID 2575788）。派Claude子Agent（sonnet-5-5 / high，≠父）只读独立验收L1–L5，原件写`logs/task9/t9-long-20261028/acceptance/`，日志`agent_logs/task9/task9.2/20261029-sonnet-acceptance.md`。
