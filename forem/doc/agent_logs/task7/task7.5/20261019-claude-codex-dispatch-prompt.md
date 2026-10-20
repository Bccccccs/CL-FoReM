# 给Codex的派发提示（task7.5(A)审计＋task7.1–7.3收尾）

- 编写：2026-10-19 20:50，Claude（claude-opus-5-5，推理强度未知），应用户要求“写一段可以直接粘贴给Codex的派发提示”。
- 状态：已写好，由用户转交；Claude未派发。下面代码块为可直接粘贴的正文。

```text
你在 /home/ybc/projects/CL-FoReM 工作。本次有两项任务，都只读和写文档：不运行程序、不安装、不训练、不修改任何参考仓库（husky/、mobile-rl/、nmoma/、scwm/、archive/、mapgen/）和 forem/src、forem/config。推荐模型 GPT6.1sol，推理强度 medium（跨仓库核对实现语义、核查论文与代码出处）；在日志里写明你实际使用的模型和强度，无法核实写“未知”。

开工前必读：
1. 根 AGENTS.md（任务组织、来源登记、不准擅自扩展功能）、forem/AGENTS.md、forem/doc/README.md、forem/doc/PROGRESS.md。
2. task7 当前框架：forem/doc/tasks/task7/TASK.md 开头“2026-10-19框架确定”、§2.3、§2.7–§2.9、§3；forem/doc/DECISIONS.md 末尾 TASK7-FRAMEWORK / TASK7-TASKDEF / TASK7-INTERFACE / TASK7-PROTOCOL / TASK7-MAPS 五条；SOURCES 中 SRC-0358–SRC-0364。
3. Claude 写给你的交流文档：forem/doc/agent_logs/task7/20261019-claude-codex-sync.md（先读第0节）。
4. task7.4 已起草的任务定义与接口：forem/doc/tasks/task7/task7.4/RESULTS.md（§1–§13）。
在 PROGRESS.md 登记两条任务（负责人Codex、状态active、开始时间、记录路径），完成后改状态。修改共享文件前重读，保留他人内容；当前工作区有大量他人未提交改动，不要 git add -A、不要提交。

== 任务一：task7.5(A) 只读代码复用审计 ==
三文档：forem/doc/tasks/task7/task7.5/{TASK,PROCEDURE,RESULTS}.md。独立日志：forem/doc/agent_logs/task7/task7.5/YYYYMMDD-codex-reuse-audit.md。
目标：查清 husky/src/modulation_rl/（CBL快照）、mobile-rl/（上游N²M²，记录commit）、forem/src/（FoReM迁移版）中，哪些实现能用于 task7 的自写理想执行 sim。逐模块审计：
  a. 底盘运动学积分（含差速底盘的处理方式；已知 myutils.cpp:405–421 为先转后走）
  b. UR5 正运动学与IK（求解器种类、是否依赖MoveIt/BioIK/ROS、多解与连续性、失败返回语义）；引用并对照 task7.3 RESULTS 的已有IK审计，不重复劳动
  c. 碰撞检查：底盘与障碍、机械臂自碰撞、**机械臂与环境障碍**（task7新增要求；N²M²据SRC-0360可能不检查，请核实）
  d. 末端路线/运动生成（eeplanner等），以及“同步（末端按时间前进）”与“不同步（底盘与机械臂可互相等）”两种推进方式各需要改什么
  e. 局部占据地图与扫描/射线求交（task7要求路径评估只用扫描累积的局部地图，不用真值地图，SRC-0362）
  f. 地图读取：mapgen长方体JSON（position为底面角点、绕角点旋转，SRC-0333）与N²M²程序生成地图
  g. 任务、奖励与终止的实现位置（只作参考，task7定义见task7.4 RESULTS §1–§6）
每个模块给出：文件:行号与commit、语言与依赖、可复用判断（直接复用 / 改写后复用 / 只作参考 / 不可用）及理由、需要改动的点、是否适合GPU批量（N个环境并行，父TASK §2.1）、以后实现时应写的单元测试。
交付：写入 task7.5 RESULTS 新增“(A) 代码复用审计”一节（汇总表＋逐模块说明＋给(B)环境规格的建议）；不写(B)规格（由Claude起草）。新的代码事实登记到 SOURCES.md：写入前先看文件末尾当前最大编号，从下一个编号开始（今天已用到SRC-0364；SRC-0341–0355预留给任务二，不要占用）。
验收：每个判断都有文件:行与commit；只读，未运行任何程序；结论与task7已定框架不冲突，若发现冲突写进交流文档的“Codex回复”节，不直接改task7父文档。

== 任务二：收尾 task7.1–7.3 并补登 SRC-0341–SRC-0355 ==
背景（见交流文档第1节）：task7.1–7.3 的RESULTS和SOURCES引用了SRC-0341–0355，但SOURCES中这15条不存在；三份子日志写着“登记文本见本日志/已交父Agent”，正文却仍是“调研中/尚未执行”，登记文本没有落盘。父日志 forem/doc/agent_logs/task7/20261019-codex-sequence-design.md 仍为active。
要求：
  1. 补写SRC-0341–0355到SOURCES.md（编号对应：0341–0345 task7.1 TD-MPC2/POPLIN/LOOP，0346–0350 task7.2 SC²-WM/MBPO/DreamerV3等，0351–0355 task7.3 IK相关），格式按根AGENTS来源规则。若原登记文本已无从恢复，按各RESULTS所列原文与commit重新核查后登记，并如实写明核查程度（全文/部分章节/仅摘要/未核查），不得标为已核验而实际未读。插入位置：放在SRC-0340与SRC-0356之间，保持编号顺序。
  2. 补全三份子日志与父日志的执行记录，完成父Agent抽查并更新task7.1–7.3 RESULTS的状态（review→done或写明未通过的原因）。
  3. 对照2026-10-19晚确定的新框架（离散SAC在候选前瞻点间选点、每点多路径精确评估、f_p经零初始化门控偏置层接入、全部候选同时预测与修正、不设初选），在每个子RESULTS末尾追加“新框架下的适用性”一节：哪些结论仍适用、哪些因框架改变而不再需要（例如task7.2关于两阶段策略log概率的推导）。
  4. 把你对新框架的复核意见（与task7.1–7.3结论或代码事实冲突之处）写进交流文档的“Codex回复”节。
  5. 不修改task7父TASK/PROCEDURE/RESULTS；它们现由Claude按用户指示维护。

两项任务互相独立，可以先后做也可以分开做；不要委派子Agent，除非先建立对应子任务三文档并在日志里写明。完成后在两份独立日志的“交接”节写明：已完成、证据路径、未解决问题、下一步。
```
