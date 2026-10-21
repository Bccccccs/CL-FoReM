# 2026-10-20 Claude：给Codex的两份派发提示（task7.13 CBL代码核查；两层SAC文档复核）

- 任务ID：TASK7.13-DISPATCH-20261020
- 作者：Claude（claude-opus-5-5，推理强度未知）
- 用户指示（本会话）：“你给我提示词就可以了，我去派发”。
- 2026-10-20稍后更新：用户按推荐确定一批项（SRC-0401），两份提示已同步改为3维动作并加读SRC-0401；以本文件当前版本为准。Claude只写提示，不启动Codex；由用户派发。
- 两份提示互相独立，可并行：A写task7.13 RESULTS、SOURCES和自己的日志；B只写自己的日志。二者共享写入只有PROGRESS（各写自己的一行，写前重读）。
- 推荐：Codex GPT6.1sol，medium（需核对多处代码与文档因果关系）。实际模型/强度由执行方在日志中记录，无法核实写“未知”。

---

## 提示A：task7.13第1步——CBL下层代码核查（只读）

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7.13-CBL-AUDIT-20261020。推荐模型GPT6.1sol、推理强度medium；在日志里写明你实际的模型与强度，无法核实写“未知”。

【先读】根 AGENTS.md（尤其“功能范围硬性约束”“论据与引用来源”“项目级任务组织规则”）；forem/doc/README.md；forem/doc/PROGRESS.md；forem/doc/tasks/task7/TASK.md 的“2026-10-20 两层SAC”节、§2.3、§2.7、§3中U31–U38；forem/doc/tasks/task7/task7.13/ 三文档；forem/doc/SOURCES.md 的 SRC-0400（含“2026-10-20补充”）、SRC-0401、SRC-0360、SRC-0388、SRC-0394。

【开工登记】在 forem/doc/PROGRESS.md“项目级记录”表加一行（写前重读，保留他人内容）：TASK7.13-CBL-AUDIT-20261020｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/task7.13/20261020-codex-cbl-audit.md，写用户要求、授权边界、要处理的文件。

【背景】task7改为两层SAC：下层SAC以候选点为子目标、10 Hz输出3维（末端速度vel_norm＋底盘ω＋v，与CBL一致；SRC-0401），机械臂由IK求解，单独训练后冻结；上层离散SAC选点。task7.13要写下层规格，需要先把CBL（Husky+UR5，task5.5所用链路）下层的实际口径核清楚。

【核查范围（只读静态阅读，代码以根仓库当前HEAD为准，记下commit）】
代码：forem/src/modulation_rl/（scripts/main.py、sac.py、model.py、modulation/envs/combined_env.py、robotenv.py、eeplanner.py、modulation/utils.py、src/robot_env.cpp、src/robot_husky.cpp、src/myutils.cpp）；forem/scripts/scwm_sac.py、task3_sac_entry.py；forem/config/task3/、config/task5/（task5.5实际使用的配置）。
逐项给出“代码位置（文件:行/符号）—实际取值—说明”：
1. 动作：Husky差速时的动作维数、各维名称与顺序（get_ranges标签顺序 vs _convert_policy_to_env_actions实际取用顺序，task_contract.yaml:83–89写法是否一致）、各维缩放范围（base_vel_rng、base_rot_rng、vel_norm的[0.01, 0.3]）、执行裁剪与加速度裁剪；task5.5实际运行时learn_vel_norm是否开启、取值多少（区分RLlib best_defaults与main.py/ScwmSAC路径）。
2. 时序与IK：解析环境步长（TIME_STEP_TRAIN）；末端计划如何按vel_norm推进；“先算下一底盘位姿、再对该位姿求IK”的调用顺序；IK失败的判定与处理（ik_fail_thresh、ikslack相关参数）；底盘积分方式（calcDesiredBaseTfDiffDrive）。
3. 观测：机器人状态向量的组成与维数；局部地图尺寸、分辨率、通道，末端计划叠加/拼接方式；是否拼接上一动作；有无循环/记忆结构。
4. 奖励与终止：calculate_reward全部项与权重（含vel_norm项、加速度惩罚、碰撞惩罚、IK失败惩罚）、回合终止条件；与SRC-0360已登记内容只补差异，不重复。
5. SAC实现：model.py网络结构（地图编码、MLP宽度、输出头）；task5.5实际超参（lr及衰减、gamma、tau、alpha/目标熵及其学习率、batch、buffer、每步更新次数、learning_starts）；GPU replay；哪些部分与modulation_rl环境耦合、复制到forem/src新模块复用时需要改哪些接口；代码里有无可复用于离散动作SAC的部分（如无，直接说明）。

【输出】
- 写入 forem/doc/tasks/task7/task7.13/RESULTS.md“运行记录”下新增“2026-10-20 CBL下层代码核查（Codex）”节：上述1–5的表格；区分“代码事实/配置事实/推断”；最后一小节列出对U31–U36的影响（只写影响与可选项，不替用户做决定，不写成已定设计）。
- 在 forem/doc/SOURCES.md 末尾追加新条目（写前重读文件，取当时最大编号+1，不改已有条目），按根AGENTS要求记录主张、精确位置与commit、核查日期/人、适用限制；RESULTS中链接这些条目。
- 完成后：日志写改动文件、核查范围、未解决问题；PROGRESS本行改为review（待Claude复核）。

【禁止】不运行任何程序、容器、训练或评估；不修改代码与参考仓库（husky/、nmoma/、scwm/、mobile-rl/、archive/）；不修改父task7 TASK/PROCEDURE/RESULTS和其他子任务文档；不新增功能、实验或设计决定；发现其他Agent正在改同一文件先停下说明。
```

---

## 提示B：两层SAC文档改动复核（只读，只写自己的日志）

```text
你是Codex，在 /home/ybc/projects/CL-FoReM 工作。任务ID：TASK7-LOWER-SAC-REVIEW-20261020。推荐模型GPT6.1sol、推理强度medium；在日志里写明你实际的模型与强度，无法核实写“未知”。

【先读】根 AGENTS.md；forem/doc/README.md；forem/doc/PROGRESS.md；Claude的改动日志 forem/doc/agent_logs/task7/20261020-claude-lower-sac.md；forem/doc/SOURCES.md 的 SRC-0400、SRC-0401；forem/doc/DECISIONS.md 的 TASK7-LOWER-SAC-20261020、TASK7-DEFAULTS-20261020 与 TASK7-FRAMEWORK-20261019。

【开工登记】在 forem/doc/PROGRESS.md“项目级记录”表加一行（写前重读，保留他人内容）：TASK7-LOWER-SAC-REVIEW-20261020｜Codex｜active｜日志路径。建独立日志 forem/doc/agent_logs/task7/20261020-codex-lower-sac-review.md。

【背景】2026-10-20用户决定task7改为两层SAC：下层SAC 10 Hz输出3维（末端速度vel_norm＋ω＋v，同日稍后由两维修订，SRC-0401）、机械臂由IK求解，单独训练后冻结；候选特征改为冻结下层对每个候选的一次确定性推演（观测用当前累积地图按推演位姿裁剪、未知区保持未知）；世界模型先只反馈到上层选点；原“每点N条路径＋固定评分”的规则执行器保留为对照组G7；不采用TD-MPC2式序列规划。Claude据此改了文档（只改设计，未实施）。

【复核范围】forem/doc/tasks/task7/TASK.md、PROCEDURE.md、RESULTS.md；task7.4–task7.13各TASK.md（含新建task7.13三文档）；forem/doc/PLAN.md、PROGRESS.md、DECISIONS.md、SOURCES.md的SRC-0400、SRC-0401；task7.9 RESULTS (B)(D)。检查：
1. 残留冲突：仍把“路径评估/非学习执行器/每点N条路径/走一段重规划”写成主方案、而未标为G7或历史的地方；task7.4–7.11正文中依赖旧执行器、但状态行影响说明里漏列的内容。
2. 主张—来源—适用性：SRC-0400列出的代码行号与描述是否属实（直接打开代码核对）；文档中新写的“Claude建议/用户决定/待定”是否区分清楚，有无把建议写成已定。
3. 设计逻辑：推演与真实执行的一致性说明是否准确；G1–G7的可比性（同一冻结下层、预算、G7的定位）；训练阶段L→1→2→3与冻结范围；f_p输入改为推演特征后与task7.4接口表、经验池字段（只存精确量I4）是否矛盾；半马尔可夫折扣与下层10 Hz步长的关系是否需要补说明。
4. 是否有未经用户决定的语义改动（奖励、终止、动作、观测）。

【输出】只写自己的日志：按编号列出发现，每条含“位置（文件:行）—问题—建议改法—依据”，并标严重程度（必须改/建议改/可选）。不直接修改任何task或共享文档（由Claude统一处理）；完成后PROGRESS本行改为done（交付复核意见）。

【禁止】不运行程序、容器、训练或评估；不修改代码、参考仓库和除PROGRESS本行及自己日志外的任何文件；不新增功能、实验或设计决定。
```
