# TASK0-REMEDIATION (task0.7)：审核问题修正与重新验收

- Agent：Claude；模型 Sonnet5.5（claude-sonnet-5-5）；推理强度：任务推荐 medium，平台实际档位未能从会话内核实，记“未知/平台默认”。未启动子Agent。技能 executing-plans/systematic-debugging 在本会话技能列表中不存在，按 PROCEDURE 文本手工执行。
- 状态：review；2026-09-30 11:08–11:53 +08:00
- 用户要求：接手 task0.7，按 `forem/doc/tasks/task0/task0.7/PROCEDURE.md` 顺序修正 task0.6 审核问题并重新验收；不得用滤波/降采样掩盖振荡；只改 forem；不提交、不推送；不启动 task1、误差注入、IK、SAC、世界模型；保留原始证据；完成后置 review 交 Codex 复核。
- 已读：根 AGENTS.md、forem/ENV.md、doc/PROGRESS.md、task0 父三文档（此前已读）、task0.6/RESULTS、task0.7 三文档、task0.6-diagnostic 脚本与分析结果。
- 接手前状态（实测）：分支 main（93e3c2f），forem 有大量未提交改动（含我此前的 forem_sim、scripts 与 Codex 文档）；容器仅 `forem-dev`（Up 41 分钟，挂载 forem→/root/mm_husky_ws rw + 入口只读，镜像 sha256:e674db49…dfc430），容器内只有 `sleep infinity`，无 roslaunch/gzserver/rosmaster；三个旧容器已被删除（task0.8），不恢复。

## 执行记录与证据

时间均为 2026-09-30 +08:00；命令、退出码、哈希与数据见 [task0.7 RESULTS](../../../tasks/task0/task0.7/RESULTS.md)（不在此重复）。

- 11:08–11:12 阶段一：登记 TASK0-REMEDIATION；新增 `scripts/task0_proc.py`（pid+内核启动时间身份，SIGINT→TERM→KILL，仅对本次进程树）、`task0_manifest.py`、重写 `run_task0_smoke.sh`（run-id 白名单、拒绝已有目录、flock 互斥、trap 清理），并新增 `bag_to_csv.py`、`analyze_task0_feedback.py`。
- 11:12–11:38 阶段二（单因素诊断，约 20 次 fresh 运行）：复现 task0.6 的 1 kHz 交替；步长、迭代数、sor、erp、cfm、P/D 增益、惯量重缩放、被动关节均不消除；`solver type=world` 消除；恢复原配置复现。过程中犯的错：把 `<gravity>` 写在 `<physics>`（被 Gazebo 忽略）导致 e7/e8/e20 三次“零重力”诊断无效，后以 `/gazebo/get_physics_properties` 查出并用写在 `<world>` 的 e7b/e8b/e20b 重做；曾据无效的 e8 推断“被动臂自旋是数值伪迹”，已撤回。
- 11:26–11:33 阶段三：`task0_validation.py` + `check_feedback.py` 重写；`tests/test_task0_validation.py` 20 项，宿主与容器（py3.10/3.8）通过；旧逻辑对 4 类坏输入放行有用例证明。
- 11:33–11:38 阶段四：`regress_task0_smoke.py`；reg1 因我把 `sg` 父进程的 -15 当 wrapper 退出码判 TERM 用例失败（wrapper 自身 143），修正测试后 reg2 全 PASS；另手测外来进程拒绝并由我按 pid 清掉自建假进程。
- 11:39–11:52 阶段五：世界改用 world 求解器；声明判据后跑最终运行；发现并更正：task0.5 更正记录里“运动后偏差是求解器伪迹”的说法与新数据矛盾（终值误差换求解器后不变），用零重力单因素证明其为重力载荷，并核对 effort≈P·e（非积分限幅）；把重力从 `<physics>` 移到 `<world>`（值 −9.8，行为不变）后用 `final-v2-*` 重跑最终验收。
- 文档：task0.7 RESULTS（问题闭环表、诊断表、判据声明、最终运行、限制）、task0.5/0.4 更正记录、task0 父 RESULTS、DECISIONS `TASK0-SOLVER-20260930`、ENV、scripts/README、PROGRESS。
- 未做：未提交/推送；未启动 task1、误差注入、IK、SAC、世界模型；未改 husky/参考仓库；未恢复旧容器；未测最大仿真速度、GUI、更复杂场景。

## 交接

- 状态 review，交 Codex 复核。运行进程：无（forem-dev 内仅 `sleep infinity`；`python3 scripts/task0_proc.py foreign` → `[]`）。
- 复核建议：① 读 task0.7 RESULTS 的问题闭环表；② 重跑 `python3 -m unittest discover -s forem/tests -v`；③ 重跑 `run_task0_smoke.sh <新run-id> …` 和 `regress_task0_smoke.py --tag <新tag>`；④ 抽查 `results/task0/task0.7-diag-b0-r1|e12-solver-world|b0-r2-restore` 的 hf_joint_states.csv 与 analysis_hf.json；⑤ 关注我在 RESULTS 里标出的不确定处（内部机理、单一场景、判据阈值来源、最大速度未测）。
- 产物体量：`forem/results/task0` 约 1.9 GB（bag），不入 Git。
