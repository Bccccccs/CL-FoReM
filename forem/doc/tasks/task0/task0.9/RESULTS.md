# task0.9 task0.7独立复核 — 结果

> **当前状态（2026-10-19核对）：done（复核交付）。** 本文件下方的状态行和“尚未执行/进行中”等表述是当时的记录，以本行为准。

状态：done（独立复核交付完成；task0.7与父task0仍review，存在待修正项）。负责人Codex /root；实际模型/推理档位未知。用户要求复核task0.7，本轮只审核/复测，不修改生产实现、不进入task1、不提交/push。

## 已核验的修正

- 接手源码HEAD `438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804`（此前已由他人提交；本轮没有提交）。静态审核日志：[独立代码审核](../../../agent_logs/task0/task0.9/20260930-codex-task0-remediation-code-review.md)。父Agent独立复现、核验其发现。
- `python3 -m unittest discover -s forem/tests -v`：20项全部通过，退出0。`catkin build forem_sim -j2 -p1`：1包成功，无警告，退出0（本轮增量构建）。日志 `forem/logs/task0/task0.9-checks/{unittest,build}.log`。
- `python3 forem/scripts/regress_task0_smoke.py --tag task0.9-reg`：现有8项入口异常回归全部PASS、退出0；结果 `forem/results/task0/task0.9-reg-report/report.json`，日志 `forem/logs/task0/task0.9-checks/entry-regression.log`。这些测试不覆盖下面新发现的失败路径。
- 两次新fresh launch，run-id `task0.9-r1`、`task0.9-r2`，参数 `--duration 8 --move 0.3 0.2 -0.3 0.2 0.3 0.4 --move-time 3`：均退出0，24项检查全部通过、125Hz、最大位置跟踪误差7.6441e-4rad，底座最大漂移5.35e-15；实际反馈/参考独立，无回填。终值actual−target从原始CSV重算与新报告一致；`results/task0/task0.9-checks/move-audit.json`。
- 新高频保持 `task0.9-hf-hold`（12s，settle2）及运动 `task0.9-hf-move`（8s/3s轨迹），使用 `--bag --hf-mode hold|move --launch-arg controller_config:=/root/mm_husky_ws/config/diagnostics/task0.7/ur5_controllers_hf2000.yaml`，均退出0。默认控制器增益不变，物理world直接求解；实际joint约1.81kHz。
- 历史quick→world→quick原始CSV独立复算，window t≥6s：速度高频残差最大2.8132e-2→1.5727e-10→2.8132e-2rad/s，支持当前场景下求解器修正的效果。最终旧/新高频数据另按summary的实际请求窗口裁切复算，六关节完整、所有值有限、连续三元组充分，world配置依旧满足既定1e-4rad/s、1e-7rad判据；证据 `results/task0/task0.9-checks/independent-data-audit.json`（复算脚本在logs同run目录）。没有因为下面脚本问题否定已经复核的真实修正收益。
- 最终5个旧run的manifest列出的44个文件中，仅scripts/README.md当前hash不同（文档后续更新）；执行代码与正式配置均匹配。探索期间的旧诊断manifest出现更多差异，系源码/正式世界后续更新；不能声称探索run全部hash匹配。见 `results/task0/task0.9-checks/source-audit.json`。

## 仍需修正的问题

### P1：root身份失效后仍按裸PID收养外来子树

`forem/scripts/task0_proc.py:164–171`：alive(root)为False时仍调用descendants(root.pid)，将当前复用该PID的外来父进程的子进程取得新身份加入known。之后SIGTERM/SIGKILL核验的是刚取得的child身份，不能证明它属于本次任务。

父Agent独立安全mock复现：root100旧身份无效，descendants100=[外来child200]，cmd_stop对200产生SIGTERM请求并返回0；没有向任何真实进程发信号。证据 `results/task0/task0.9-checks/pid-reuse-reproduction.json`，可执行复现脚本 `logs/task0/task0.9-checks/reproduce_pid_reuse.py`。

修正要求：只有身份仍匹配的已确认root/已确认后代才能扩展所有权；不得从失效root的裸PID重新收养子树。补PID复用阴性测试，验证外来进程不被signal。

### P2：原root先退出时遗留孤儿子进程，却返回清理成功

`task0_proc.py:163–178`：后代仅在stop开始时建立known；父进程已退出、子进程已reparent后树不可达，known为空且residue=[]，返回0。`160–162`的已有清理记录分支也只检查root消失，不重新核验之前残留。

父Agent用自己创建的短命Python父进程+sleep30子进程真实复现：父退出0，子仍活；cmd_stop退出0且residue=[]。随后已核实身份并停止该自建子进程。证据 `results/task0/task0.9-checks/orphan-reproduction.json` 与 `logs/task0/task0.9-checks/reproduce_orphan.py`，不涉及用户进程。

修正要求：运行期间建立/保存可靠的本次后代所有权（监督进程/适当隔离机制或身份跟踪），父异常退出后仍能清理已确认后代；幂等stop须核验已有残留，不以root退出等同全树清零。补父先退出及重复stop回归。

### P2：高频坏数据及证据不足仍可PASS

`analyze_task0_feedback.py:123–135`：空数据或仅2行产生空verdict，all([])=True；NaN残差与阈值比较为False也可通过；缺六关节schema未拒绝。`86–87`只要求100连续pairs，未执行task0.7预声明的100连续triples门槛。

父Agent实际CLI复现四例：empty、two、110行全NaN、120pairs但只有60triples，全部exit0且pass=true。证据 `results/task0/task0.9-checks/hf-negative-reproductions.json`，坏输入CSV及JSON同目录，复现脚本 `logs/task0/task0.9-checks/reproduce_hf.py`。坏输入仅合成数据，未当真实运行。

修正要求：完整六关节列、有限且递增的时间及数值、非空有效数据；顶层insufficient_evidence一律非零；每关节triples≥100；任何判据结果非有限均失败。添加对应失败输入回归。

### P2：高频判定窗口使用整bag，额外静止段会稀释异常

`run_task0_smoke.sh:140`没有传t-min/t-max，实际评估包括记录前settle及记录后时间的整bag。旧最终保持请求12s而bag18.78s，运动请求8s而bag13.1545s。已独立用真实数据裁窗复算，当前修正依旧通过；但自动门槛存在被安静段稀释的失败路径。

父Agent纯数据复现：只在短时段交替±2e-4rad/s，整13s残差6.0778e-5（过）、3s运动段1.2653e-4（失败），同阈值1e-4。证据 `results/task0/task0.9-checks/window-dilution-reproduction.json`。至少应从summary取实际recording_window并显式传入分析、核验覆盖及充分样本；运动与保持的关键区间应明确单独报告，避免将“运动模式”整bagRMS当运动段结论。

## 判定与交接

最终结论：求解器修正、常规反馈判定、报告误差符号和健康路径启动均有独立证据；新增四项问题尚未修正，task0.7及父task0保持review，不能标done。优先处理P1所有权边界，再处理孤儿清理、高频坏输入与时间窗口，追加失败→修正→通过回归后复核。具体ODE内部机理及其他场景性能仍未验证，不扩大因果结论。

本轮未修改生产源码/配置，不开启人为延迟或task1。60s保持task0.9-hold退出0，125Hz、24项检查通过，最大跟踪误差3.4569e-8rad、底座漂移4.92e-15。全部本轮仿真已停止，容器foreign输出[]；forem-dev仍Up。所有自建复现进程已清理。日志logs/task0/task0.9-checks/hold-run.log，原始数据results/task0/task0.9-hold。恢复使用ENV入口，新run-id不可复用；不要通过宽泛pkill清理。

## 模型与推理强度

推荐Codex GPT6.1sol、Claude Sonnet5.5，medium：跨模块审核进程所有权、判据与数据窗口。实际Codex/root和代码审核子Agent的模型/档位未知，未主动切换模型。
