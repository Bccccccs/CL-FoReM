# ENV-SETUP (task0)：独立环境配置

- Agent：Claude（Sonnet5.5；推理强度：平台默认，未能从会话内核实具体档位，记为“未知/默认”）
- 状态：review；2026-09-30 10:22–10:37 +08:00 完成 task0.1–0.5
- 用户要求：“开始”——执行 task0 环境配置（接续 Codex 的交接）。
- 授权边界（据根 AGENTS.md 与 task0/TASK.md）：在 forem 内准备最小源码、适配入口、必要容器依赖、构建、启动、基础反馈检查。不做误差注入/IK/SAC/WM；不改 husky 与参考仓库；不停止 `mmhusky-node01*`；不推送、不提交（Codex 的未提交文档改动仍在工作区）。
- 已读：根 AGENTS.md、forem/ENV.md、doc/README/PLAN/PROGRESS/DECISIONS、tasks/task0 及 task0.1–0.5 三文档、task1 TASK。
- 执行方式：自己按 task0.1→0.5 顺序完成，不委派子 Agent。每个节点的实测写入对应 `tasks/task0/task0.N/RESULTS.md`，父 RESULTS 汇总。

## 执行记录与证据

时间均为 2026-09-30 +08:00；详细命令、退出码、哈希、数据见各子节点 RESULTS（不在此重复）。

- 10:22–10:24 task0.1：一次性容器 `docker run --rm --entrypoint bash mm_husky:node01` 只读探测；三个旧容器 `.Image` 与 tag 一致；apt `ur_description` 1.5.0 存在，无需复制 husky。→ [task0.1/RESULTS](../../tasks/task0/task0.1/RESULTS.md)
- 10:24–10:26 task0.2：新建 `forem/src/forem_sim`、`forem/config/control/ur5_controllers.yaml`（逐字沿用 husky_ur5 控制器增益）、`docker/forem-entrypoint.sh`，修改 `docker/run.sh`；URDF/SDF 静态校验通过。→ task0.2/RESULTS
- 10:26–10:28 task0.3：创建 `forem-dev`；发现并修复 (a) `/root` 700 导致宿主 uid 无法进入、(b) 入口 `source setup.bash` 泄漏命令参数；`catkin build forem_sim` 与干净重建均退出 0。→ task0.3/RESULTS
- 10:28–10:31 task0.4：t0.4-r1 发现 `spawn_model -J` 在解除暂停之后才设初始姿态（顺序错误），改为在暂停期内由 `start_controllers.py` 设置；t0.4-r2 通过。→ task0.4/RESULTS
- 10:31–10:35 task0.5：t0.5-r1、t0.5-r2（两次独立启动，小幅 3 s 轨迹）通过；t0.5-x1（60 s 保持）通过；发现并记录 effort/velocity 单样本符号翻转（未查明原因）。→ task0.5/RESULTS
- 更新：`forem/ENV.md`（实测入口）、`doc/PROGRESS.md`、task0 父 RESULTS。
- 新增文件：`forem/src/forem_sim/**`、`forem/config/control/ur5_controllers.yaml`、`forem/docker/forem-entrypoint.sh`、`forem/scripts/{check_feedback.py,run_task0_smoke.sh}`；修改：`forem/docker/run.sh`。产物：`forem/results/task0/`、`forem/logs/task0/`、`forem/build`、`forem/devel`（均不入 Git）。
- 未做：未提交、未推送；未建派生镜像；未做 GUI 验证；未停止任何非自己的进程。
- 错误更正：早期草稿的时间戳（10:25–10:40、10:45–11:05）不是实际时间，已按日志文件时间改正；task0.5 中一处“两次结果 1e-8 内一致”的夸大表述已改为逐关节的实际差异。

## 交接

- 状态 review：环境已配置、可重复启动；待用户/Codex 核验后可标 done。运行中：容器 `forem-dev`（Up，无仿真进程）；停止 `sg docker -c 'docker stop forem-dev'`，恢复 `bash forem/docker/run.sh up`。
- 下一步建议：先弄清 effort/velocity 单样本符号翻转和静止 velocity 偏置，再开始 task1；forem 新文件与文档尚未提交，需要时由用户决定提交（只提交 forem/）。
- 接手核验：重跑 `run_task0_smoke.sh <新run-id> --duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3`，应 `pass=true`、退出 0。
