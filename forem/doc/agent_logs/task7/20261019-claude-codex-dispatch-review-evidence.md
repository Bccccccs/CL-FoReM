# 给Codex的派发提示（A 复核今天的设计文档＋B 补齐8项待补证据）

- 编写：2026-10-19 约23:20，Claude（claude-opus-5-5，推理强度未知），应用户要求“把A（复核今天的设计文档）和B（8项待补证据）合写成一份可以直接粘贴给Codex的派发提示”。
- 状态：已写好，由用户转交；Claude未派发。下面代码块为可直接粘贴的正文。

```text
你在 /home/ybc/projects/CL-FoReM 工作。本次两项任务都是只读核查与写文档：不写代码、不安装、不训练、不评估，不修改任何参考仓库（husky/、mobile-rl/、nmoma/、scwm/、archive/、mapgen/）和 forem/src、forem/config。推荐模型 GPT6.1sol，推理强度 medium（跨文档一致性审查与原文核查）；在日志里写明你实际使用的模型和强度，无法核实写“未知”。

注意并发：task5.5最终sim评估正在后台运行（见 forem/doc/agent_logs/task5/task5.5/20261019-codex-final-sim-eval.md），不要在运行它的容器里执行任何命令，不要占用GPU。另有Claude会话可能在写 forem/doc 下的共享文件：每次写共享文件前重读；向SOURCES.md追加条目前先看文件末尾当前最大编号（今晚已到SRC-0381），从下一个编号开始，写入时确认文件在你读取后没有被别人改过。不要 git add -A、不要提交。

开工前必读：根 AGENTS.md（来源登记规则、不擅自扩展功能）、forem/AGENTS.md、forem/doc/README.md、forem/doc/PROGRESS.md。在 PROGRESS.md 登记本次两项任务（负责人Codex、状态active、开始时间、记录路径），完成后改状态。独立日志：forem/doc/agent_logs/task7/YYYYMMDD-codex-review-evidence.md。

== 任务A：复核今天（2026-10-19）定下的task7设计 ==
范围：
- forem/doc/tasks/task7/TASK.md：开头“2026-10-19框架确定”、术语、§2.3–§2.9、§3（U1–U30）、§4–§7。
- forem/doc/tasks/task7/task7.4/RESULTS.md 全文（任务定义、接口表、经验池字段、训练阶段、对照与评估协议，以及按你上次7条意见修订的部分）。
- forem/doc/tasks/task7/task7.5/RESULTS.md：(B) B.0–B.17，含今晚用户已定的B1–B14。
- forem/doc/tasks/task7/task7.7/RESULTS.md、task7.8/RESULTS.md。
- forem/doc/DECISIONS.md 末尾 2026-10-19 的十条 task7 决定；SOURCES 中 SRC-0358–SRC-0381（其中0379、0380属task5.5，可跳过）。
检查内容：
1. 文档之间是否互相矛盾（同一事项在TASK、task7.4、task7.5、DECISIONS里说法不一致；已定事项还被写成待定，或待定事项被写成已定）。
2. 与代码或配置事实是否冲突（你在task7.5(A)审计时核过的H/U/F/M代码）。
3. 有没有需要来源却没有链接SOURCES条目的主张；SOURCES条目是否如实记录了用户原话与核查程度。
4. 对照组是否公平（各组共用同一环境、候选生成器、执行器、精确信息与奖励；没有人为削弱基线）；有没有在没有说明的情况下改变奖励、终止、动作或观测语义。
5. 接口能否闭合：从环境→观测→VCM→候选→路径评估→f_p→偏置层→SAC→执行器→结果与奖励→经验池，每个接口的输入输出、单位、坐标系是否对得上。
输出：在 forem/doc/agent_logs/task7/20261019-claude-codex-sync.md 末尾新增一节“Codex第二轮复核（2026-10-19）”，逐条列出问题：所在文件:行、问题、严重程度（会导致实现错误/表述不一致/措辞）、建议改法。只提建议，不提新功能、不加实验组。**不要直接修改task7的TASK/PROCEDURE/RESULTS和DECISIONS**，由Claude按你的意见修改。

== 任务B：补齐8项“待补证据/待核” ==
每项都要找到原始来源（论文原文、官方文档或官方/本地代码）并核查，按根AGENTS来源规则在SOURCES.md登记（支撑的主张、来源类型、作者/版本、URL或本地路径、精确位置、核查日期与核查人、原始结论、本项目采用方式及限制）；未能读到原文的如实标注，不得写成已核验。下面括号里的文献名只是查找线索，未经核实，请以你读到的原文为准。
1. 离散动作SAC的损失公式（线索：Christodoulou 2019，“Soft Actor-Critic for Discrete Action Settings”）。用于task7.10、父TASK §2.7与U28。
2. 从图像学习SAC时，编码器只由Critic损失训练、Actor梯度在编码器处截断的做法及理由（线索：SAC-AE、DrQ）。用于task7.8 RESULTS B第4条。
3. 循环网络从经验池按序列采样并先“预热”隐状态的做法（线索：R2D2）。用于task7.8 RESULTS B第5条。
4. UR5的关节位置限位，以及CBL/FoReM实际使用的UR5运动学参数。forem/src/husky_ur5/urdf/husky_ur5.xacro 引用的 ur_description 不在forem/src；可以在已运行的 forem-dev 容器里只读查看（例如用 sg docker -c 'docker exec forem-dev ...' 执行 ls、cat 或已source环境后的 rospack find），不得启动、停止、重建容器，不得安装。结果用于task7.5 B4，也是UR5解析IK（B3）的前提：请写清参数来源、版本，以及与标准UR5 DH参数是否一致。
5. Robotiq 85的TCP（夹爪尖端）相对 gripper_base_link 的距离，核对CBL配置 tip_to_gripper_offset=0.15 m（forem/src/modulation_rl/gazebo_world/husky_ur5/robot_config.yaml:6–9）。本地有 forem/src/robotiq_85_description；可参考官方规格。用于task7.5 B2。
6. N²M²任务中 use_fwd_orientation 的含义与终点姿态的采样方式（forem/src/modulation_rl/scripts/modulation/envs/tasks.py 及其调用的采样函数；必要时对照上游 mobile-rl）。用于task7.5 B12的终点姿态。
7. N²M²末端规划器速度常量 MIN_PLANNER_VELOCITY=0.001、MAX_PLANNER_VELOCITY=0.1（eeplanner.py:17–18）的单位与在C++/Python中的实际用法。用于task7.4 E8。
8. VLN-3DFF与CWP原文中候选航路点的标签生成与训练细节（SRC-0335目前只有网页摘要抽取）。用于task7.9改造方案。
输出：SOURCES新条目；在交流文档同一节末尾列出“建议替换”表：每项对应的文档文件:行、现在的“待补证据/待核”原文、建议改成的文字与来源链接。**不要自己修改task7各文档中的这些标记**，由Claude统一替换。

两项任务互相独立，可先后做。不要委派子Agent，除非先建立对应子任务三文档并在日志里写明。完成后在独立日志“交接”节写明：已完成、证据路径、未解决问题、下一步；更新PROGRESS状态。
```
