# TASK7.9-RULE-SPEC-20261020：候选生成规则版规格、改造方案与子目标环暂缓条件

- Agent：Claude（claude-opus-5-5，推理强度未知）
- 状态：review（草案v1已交付，待用户确认R1–R8）；2026-10-20T12:15:17–12:20+08:00
- 用户要求（原话）：“接着起草task7.9候选生成规则规格，写进三文档并登记来源。”
- 授权边界：只读与文档（task7.9 TASK）。不写代码、不运行、不改mapgen与参考仓库；不新增实验组、观测通道、奖励项或候选机制；父TASK §2.8已定规则1–6只细化不改动，需改动处列为待定交用户。
- 已读：根AGENTS、doc/README、PROGRESS、父TASK §2.3/§2.7–§2.9/U17/U30、task7.9三文档、task7.4 §9–§12与合同缺口⑦⑨、task7.5(B) B.4–B.10、task7.7、task7.8；SRC-0330、0334、0335、0337、0358、0389、0390、0392。
- 准备处理：task7.9 RESULTS（主交付）、TASK/PROCEDURE状态行、父PROCEDURE/TASK中的子任务状态句（只改状态，不改设计）、PROGRESS、SOURCES新增条目、本日志。

## 执行记录与证据

- 只读核对（本次）：
  - SC²-WM `scwm/` commit `f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b`，`vlnce_baselines/ss_trainer_ETP.py:1944–2033`：热力图减最小值；12个扇区以`direction_idx*30°`为中心±15°取峰值；用预测占据图删去落在占据格的峰值；`merge_scale=8`即按16格（0.05 m/格时0.8 m）分箱、4种偏移合并近点、保留较大值；`topk(k=8)`；只保留0.1–5 m；角度按3°、距离按0.25 m离散。
  - N²M²/CBL `arm_range: 0.8`（`husky/src/modulation_rl/gazebo_world/husky_ur5/robot_config.yaml:25`）只在`eeplanner.py:539`（H与U `mobile-rl/` commit `6281205846b1bac4525d05ee230a47bddf42023d` 同行）作末端路线规划时底盘路径的膨胀半径，代码注释“EE离底盘的最大允许距离（约臂长）”；不是IK可达判据。

- 写入（只写文档，未运行项目程序、未提交）：
  - `tasks/task7/task7.9/RESULTS.md`：(A)规则版规格A.1–A.8、(B)改造方案B.1–B.4、(C)暂缓条件、(D)待定R1–R8、交接。
  - `tasks/task7/task7.9/{TASK,PROCEDURE}.md`：状态行。
  - `tasks/task7/{TASK,PROCEDURE,RESULTS}.md`：只改子任务状态句（“task7.9–7.11未开始”→task7.9草案v1已写、7.10–7.11未开始）；未改§2.8、U17、U30等设计内容，按task7.9 PROCEDURE由父任务在用户确认后回写。
  - `SOURCES.md`：新增SRC-0395（SC²-WM后处理代码）、SRC-0396（arm_range用途）、SRC-0397（本规格推导与工程选择）。
  - `PROGRESS.md`：本任务行与task7行。
- 规格要点：12扇区以正前方为0、逆时针；候选距离d建议1.0 m（d≤2.6 m）；直线走廊长d＋0.6 m、宽0.67 m，谓词同LocalCollision底盘判定，未知格不触发；s_k以IK判定、取从s_cur起第一段连续可达样本的末端，全不可达时Δs＝0仍生成；原地候选按SRC-0392⑦；固定槽位、被放弃扇区按空位掩码，路径不可行候选不掩码；诊断量只进日志。
- 范围控制：没有加入回退量、多距离、历史候选等新机制（只在限制/改造方案中列为以后可选，须用户确认）；没有新增实验组；(C)只记录重新考虑的触发情况，不自动启动。

## 交接

- 已完成：task7.9草案v1；状态review，待用户确认R1–R8。
- 未完成：R1–R8；确认后回写父TASK §2.8、U17、U30。
- 下一步：用户确认R1–R6后可起草task7.10（依赖K、掩码与槽位约定）。

## Agent模型与推理强度

- 推荐：Codex GPT6.1sol / medium；Claude Sonnet5.5 / medium（候选质量、信息边界与接口一致性）。
- 实际：Claude claude-opus-5-5，推理强度未知。
