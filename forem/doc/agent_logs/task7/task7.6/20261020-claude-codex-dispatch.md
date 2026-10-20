# task7.6派发记录：IK与路径评估计时基准（Claude→Codex）

- 编写：2026-10-20 14:00 +0800，Claude（claude-opus-5-5，推理强度未知）。
- 用户要求：“写提示词然后派发”；在Claude列出的三项中只选task7.6，派发方式选“Claude用codex exec后台启动”。授权见[SRC-0398](../../../SOURCES.md#src-0398)；task7.9复核与task5.5 Gazebo评估未授权。
- 推荐模型：Codex GPT6.1sol（`gpt-6.1-sol`），推理强度medium（计时口径与端到端成本推导，见[task7.6 TASK](../../../tasks/task7/task7.6/TASK.md)）。启动时显式传入，覆盖`~/.codex/config.toml`默认的high。
- 本文件只记录派发；执行记录由Codex写在`20261020-codex-ik-bench.md`。

## 派发前核查（只读）

- 容器`forem-dev`在运行；容器内Python 3.10.18、numpy 1.23.5、torch 2.7.1+cu128，CUDA可见4卡；`os.cpu_count()`＝64，`OMP_NUM_THREADS=2`（容器内`nproc`因此显示2）；ROS noetic，`ur_description`在`/opt/ros/noetic/share/ur_description`。
- 宿主4块GPU均空闲（各14 MiB）。
- URDF入口：`forem/src/husky_ur5/urdf/husky_ur5.xacro`。
- 无task7代码；task7.6此前未派发、未执行。

## 派发提示（正文）

```text
你在 /home/ybc/projects/CL-FoReM 工作，执行 task7.6「IK与路径评估计时基准」。用户2026-10-20授权本任务在 forem-dev 容器内运行有界微基准（SRC-0398，边界见下）。推荐模型 GPT6.1sol、推理强度 medium；在日志里写明实际模型和强度，无法核实写“未知”。

== 授权边界 ==
- 允许：通过 sg docker -c 'docker exec forem-dev ...' 在 forem-dev 内运行计时与数值一致性脚本；新写仅供本基准使用的代码；至多使用1块空闲GPU（先 nvidia-smi 确认无占用，用 CUDA_VISIBLE_DEVICES 固定）。容器内 OMP_NUM_THREADS=2、os.cpu_count()=64，CPU多线程计时须写明线程数与相关环境变量，避免进程数×库线程过量调度。
- 预算：单次基准命令墙钟≤10分钟；本任务累计容器计算≤60分钟。需要更多时先停下，在日志写明原因和所需预算后结束，不自行扩大。
- 不允许：训练、评估；启动 Gazebo；启动、停止、重启或重建任何容器；停止不是你启动的进程；安装新包（确需安装时停下写明，由用户决定）；修改参考仓库（husky/、mobile-rl/、nmoma/、scwm/、topay/、archive/）；修改 task7 父TASK及 task7.4/7.5/7.9 等其他子任务的设计文档；为提速改变执行语义、放宽IK判据或删除失败样本。可以用 xacro/rospack 等只读展开URDF；若要调用 BioIK/MoveIt 作参考需要 roscore/move_group，先在日志写明理由，只在 forem-dev 内启动，结束时清理你自己启动的进程。
- 不实现环境：本任务的代码是计时与一致性基准，不是 task7 环境实现。底盘圆弧积分、局部栅格碰撞等如需原型计时，只能按 task7.5 RESULTS B.3/B.5 已定语义写最小原型，文件名与注释标明 benchmark prototype，不作为环境实现交付。

== 并发 ==
Claude 会话可能同时写 forem/doc 下的共享文件。每次写共享文件前重读；向 SOURCES.md 追加前先看末尾当前最大编号（目前到 SRC-0398），从下一个编号开始，写入前确认文件在你读取后未被改动。不要 git add -A，不要提交。

== 开工前必读 ==
根 AGENTS.md（特别是“论据与引用来源”和“性能优化共同要求”）、forem/AGENTS.md、forem/ENV.md、forem/doc/README.md、forem/doc/PROGRESS.md；task7 父 TASK（forem/doc/tasks/task7/TASK.md）§2.2、§2.5、§2.9、§5；task7.6 三文档；task7.5 RESULTS 的 A.4 与 (B) B.3、B.4、B.5、B.9、B.12 及待定表 B8/B9/B13/B14；task7.3 RESULTS §1–§4；task7.4 RESULTS §3、§4、§7（E1、E7）、§14；task7.9 RESULTS (A) R1–R4（K≤13、d、Δs_r 均为待用户确认的草案值，只作扫描范围）；SOURCES 中 SRC-0352、0377、0381、0385、0386、0398。
在 PROGRESS.md 登记本任务（任务ID TASK7.6-BENCH-20261020，负责人 Codex，状态 active，开始时间，日志路径）；建立独立日志 forem/doc/agent_logs/task7/task7.6/20261020-codex-ik-bench.md，并在 task7.6 RESULTS 交接节登记当前负责人。

== 步骤（对应 task7.6 PROCEDURE 四步）==
1. 确定被测实现与版本
   - 运动学以 forem-dev 内展开 forem/src/husky_ur5/urdf/husky_ur5.xacro 得到的 URDF 为准（ur_description 1.5.0）；记录展开命令与文件哈希。
   - 坐标链按 task7.5 B.4：T_A,tool0=(T_W,B·T_B,A)^(-1)·T_W,TCP·(T_tool0,TCP)^(-1)；ur5_base_link 安装 (0.13,0,0.25) m；解析DH基座与 ur5_base_link 之间绕z的π固定旋转；tool0→TCP 固定链按 SRC-0386。限位按 B.4（SRC-0385）。
   - 候选：(a) UR5 解析多解＋按 q_prev 取最近可行分支（用户B3首选，SRC-0377）；(b) 阻尼最小二乘 DLS（备选）；(c) 现有 BioIK/MoveIt 仅作参考，能在授权内调用就测，不能则写明原因。三者用同一输入、容差与失败规则。
2. 数值一致性（先于计时；未通过不得写“已等价”）
   - 解析FK 对 URDF FK：限位内随机 q 不少于1e4组，报告位置/姿态残差的最大值与分位数。
   - FK→IK→FK 回环；多分支；腕/肩/肘奇异附近；不可达目标；限位边界；q_prev 连续性与分支选择；“布尔成功但残差超阈”被拒绝。E7 尚未定，残差阈值作为参数扫描并注明。
   - B13：float32 对 float64（CPU float64 为参考）的残差差异与分支选择一致率。
3. 计时
   - 单次与批量（批大小扫描，例如 1、13、13×N…），CPU 单线程/多线程与 GPU 分开；GPU 计时用 CUDA event 或同步后计时；区分首次调用/预热；报告 p50/p95/p99 与吞吐，输入须包含失败与边界情况。
   - 路径依赖：同一路径内各检查点依次依赖上一解（B.4），按“路径内检查点顺序依赖、路径间批量”的形状测，不得把全部检查点独立求解后拼接。
   - B14：若预算允许，测按检查点循环＋掩码与其他批内推进方式的开销。B9（360°深度渲染时机）不在本次必做范围，只写依赖说明；若能在预算内用最小原型测，标明原型。
4. 成本估算与可行范围
   - 每次决策成本 ≈ K×N×检查点数×(IK＋每检查点其他开销)。K≤13；检查点间隔按 B8 的推导（相邻检查点位移≤0.05 m）与路径长度范围扫描；N 取一组范围扫描。训练总墙钟只代入 task7.4 §14 等文档已给的交互量；文档未给的写“待定”，只给参数化曲线，不自行设定训练预算。
   - 给出可行范围与瓶颈；B8、B13、B14 以及解析/DLS 的选择写成建议交用户决定，不自行冻结。

== 输出 ==
- 代码：forem/scripts/bench_task7_ik.py（必要时再加 forem/scripts/bench_task7_*.py）；一致性测试可放 forem/tests/task7/。
- 日志放 forem/logs/task7/t7.6-bench-20261020-r<k>/，产物放 forem/results/task7/t7.6-bench-20261020-r<k>/（json/csv，含代码哈希、git 状态、硬件、命令、样本数、分布）。后台 Python 用 python3 -u。
- 写 task7.6 RESULTS（run-id、命令、退出码、表格、结论与限制、“交用户决定”节）；同步 task7.6 TASK、PROCEDURE 顶部状态行；SOURCES 新增一条项目实测条目（run-id、产物路径与哈希、结论与限制）；更新 PROGRESS。完成后 task7.6 标 review（待 Claude/用户复核），不要标 done。
- 不改 task7.4/7.5/7.9 与父 TASK；对它们的影响写在 task7.6 RESULTS 里，由父任务回写。

== 验收 ==
- 一致性结论先于计时结论；每个数字可从产物复算。
- 墙钟/CPU/GPU 计时分开，包含失败与边界情况；记录版本、命令、退出码与产物路径。
- 未改变执行语义，未超出授权与预算；结束时没有你启动的残留进程（日志写明核查方法）。
- 最终回复用中文简要汇报：完成了什么、关键数字、未通过/无法核实的项、需要用户决定的事项。
```

## 启动记录

- 2026-10-20 14:05：正文已抽取到`forem/logs/task7/t7.6-codex-dispatch-20261020/prompt.txt`（43行，sha256 `38d8fbc96e98a4f2df51dbda758fdcc00fced5636963fd46ed2938439ad59f18`）。
- Claude两次尝试后台启动均被Claude Code自动权限拦截（理由“Create Unsafe Agents”），**Codex尚未启动**：①`-s danger-full-access -c approval_policy="never"`；②`--approve-for-me`（工作区写沙箱＋自动审核）。Claude未再尝试绕过，待用户自行启动或放行。
- 需要docker：提示要求Codex用`sg docker -c 'docker exec forem-dev …'`，工作区写沙箱可能无法访问docker套接字；用户启动时若用沙箱模式，Codex可能在第一步运行容器命令时失败。
- 建议启动命令（尚未执行），在仓库根目录运行：

```bash
D=forem/logs/task7/t7.6-codex-dispatch-20261020; setsid nohup codex exec -C /home/ybc/projects/CL-FoReM -m gpt-6.1-sol -c model_reasoning_effort='"medium"' -s danger-full-access -c approval_policy='"never"' --json -o $D/last_message.md - < $D/prompt.txt > $D/events.jsonl 2> $D/stderr.log &
```

- 监控：`pgrep -af 'codex exec'`；进展看`events.jsonl`、Codex日志`agent_logs/task7/task7.6/20261020-codex-ik-bench.md`；结束后最终回复在`last_message.md`。停止：对该`codex exec`进程发SIGINT/SIGTERM，并核查它在forem-dev内启动的进程。
- 也可在交互式Codex中直接粘贴上面的派发正文。
- 2026-10-20 14:08 用户在自己终端按上述命令启动（PID 1467278），约1分钟后失败退出：`turn.failed: workspace routing discovery failed`。原因经Claude核查：用户终端的HTTP(S)_PROXY为`127.0.0.1:17893`（mihomo监听，但TLS握手被断开，curl返回`unexpected eof`）；`127.0.0.1:7892`可正常访问chatgpt.com，现有Codex app-server亦使用7892。Codex未开始执行任何步骤。输出已移到`forem/logs/task7/t7.6-codex-dispatch-20261020/attempt1-proxy17893-failed/`。
- 重启建议：在命令前显式设代理为7892（尚未执行）：

```bash
D=forem/logs/task7/t7.6-codex-dispatch-20261020; HTTP_PROXY=http://127.0.0.1:7892 HTTPS_PROXY=http://127.0.0.1:7892 http_proxy=http://127.0.0.1:7892 https_proxy=http://127.0.0.1:7892 setsid nohup codex exec -C /home/ybc/projects/CL-FoReM -m gpt-6.1-sol -c model_reasoning_effort='"medium"' -s danger-full-access -c approval_policy='"never"' --json -o $D/last_message.md - < $D/prompt.txt > $D/events.jsonl 2> $D/stderr.log &
```
- 2026-10-20 14:1x 用户按上述带7892代理的命令重新启动（宿主PID 1480576）。Claude核查：`events.jsonl`无error事件，Codex已开始读文档（首条消息为“按task7.6授权边界执行，先核对文档、容器与现有进程……”）。后续执行情况以Codex日志为准。
