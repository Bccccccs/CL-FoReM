# 2026-10-20 Claude：task7下层改为SAC（两层SAC）的文档更新

- 任务ID：TASK7-LOWER-SAC-20261020
- 负责人：Claude（claude-opus-5-5，推理强度未知）
- 开始：2026-10-20T16:08+08:00
- 状态：done（只写文档）

## 用户要求与授权边界

本会话用户指出“CBL的SAC输出底盘动作，我们的SAC输出点的选择”出现偏差，提出两层都用SAC、世界模型先只反馈到选点，经讨论确认（原话见[SRC-0400](../../SOURCES.md#src-0400)）：

1. 单独训练一个下层SAC，训练后冻结作为固定网络；
2. 候选特征改为冻结下层SAC对每个候选的确定性推演（Claude方案(a)），每个候选一条，不做多次随机采样；推演时下层观测用当前累积地图按推演位姿裁剪、未知区保持未知；
3. 下层动作为10 Hz连续(v, ω)，机械臂由IK求解（与CBL一致）；
4. 保留“上层SAC＋规则执行器（10-19原设计）”作对照组；
5. 确认TD-MPC2式序列规划不采用（10-19已不采用，此次连同路径族与固定评分一并去掉）；
6. “更新文档吧”。

授权：只更新设计文档。不写代码、不安装、不训练、不评估。用RLlib还是CBL自写SAC：Claude推荐CBL自写SAC，用户未单独表态，按“Claude推荐、待确认”记录。

## 准备处理的文件

SOURCES（新增SRC-0400）、DECISIONS（新增TASK7-LOWER-SAC-20261020）、task7 TASK/PROCEDURE/RESULTS、新建task7.13三文档、task7.4/7.5/7.6/7.10/7.11 TASK状态行加影响说明、PROGRESS、PLAN。

## 已核查的事实（只读）

- CBL/N²M²差速底盘动作：`forem/src/modulation_rl/scripts/modulation/envs/robotenv.py:49–71` `get_ranges`，`drive=='diff'`时动作为`tiago_base_vel`、`tiago_base_angle`（可选再加`vel_norm`），均在[-1,1]；`combined_env.py:435–448`按`base_vel_rng`换算`vel_norm`；`robotenv.py:249`按`_velocity_ranges`缩放底盘动作；`src/myutils.cpp:405–422` `calcDesiredBaseTfDiffDrive`先转`dt·angle`再沿新朝向前进`dt·v`；`eeplanner.py:22` `TIME_STEP_TRAIN = 0.1`。代码版本：根仓库commit 2380ff5。
- CBL自写SAC：`forem/src/modulation_rl/scripts/sac.py:11` `class SAC`、`:71` `update_parameters`；task3派生`forem/scripts/scwm_sac.py`（ScwmSAC），task5.5用其在GPU上训练5M（[SRC-0394](../../SOURCES.md#src-0394)）。
- RLlib路线：task5.4实测模型与optimizer都在CPU（[SRC-0312](../../SOURCES.md#src-0312)）；task6.2实测RLlib SAC执行计划`bulk_sync`使worker相互等待（[SRC-0245](../../SOURCES.md#src-0245)）。

## 实际改动

见本日志末尾“完成”节。

## 完成

- 新增[SRC-0400](../../SOURCES.md#src-0400)；[DECISIONS](../../DECISIONS.md) TASK7-LOWER-SAC-20261020（并在TASK7-FRAMEWORK-20261019下追加“部分被取代”注）。
- [task7 TASK](../../tasks/task7/TASK.md)：新增“2026-10-20 两层SAC”入口节、更新框图、§2.3、§2.7第3/7步与说明、§2.9、U5、U18、U20、U23、U25、新增U31–U38、§4（G1措辞、新增G7）、§5、§6、§7。
- [task7 PROCEDURE](../../tasks/task7/PROCEDURE.md)：实施阶段草案加入下层SAC，准备子任务表新增task7.13，受影响子任务注明。
- 新建[task7.13](../../tasks/task7/task7.13/TASK.md)三文档（draft，未执行）。
- task7.4、7.5、7.6、7.10、7.11 TASK状态行下加一行影响说明（未改其正文）。
- [task7 RESULTS](../../tasks/task7/RESULTS.md)、[PROGRESS](../../PROGRESS.md)、[PLAN](../../PLAN.md)同步。
- 没有代码、安装、训练或评估。

## 未解决与下一步

- U31–U38（下层观测/奖励/子目标采样/不同步变体的末端推进方式/执行时是否确定性/到达与超时重定义/推演成本/SAC实现选择）待task7.13与用户确定。
- task7.4合同⑦（到达、决策超时以“路径计划”定义）、⑨（全部路径不可行时的分层排序）、B6/SRC-0393风险特征（“最优路径扫过区域”）、task7.5 B7（不同步路径族s分配）与task7.6成本公式须按新下层重写；当前只在各TASK标注受影响，正文未改。

## 2026-10-20稍后：用户按推荐确定的一批项

- 用户原话：“都按你的推荐来，写进文档吧”。内容见[SRC-0401](../../SOURCES.md#src-0401)、[DECISIONS](../../DECISIONS.md) TASK7-DEFAULTS-20261020。
- 前置核查（只读）：CBL Husky动作3维，`forem/config/task3/task_contract.yaml:83–89、118`，`modulation/utils.py:112`，`configs/best_defaults_ray.yaml:10`（更正：该行属pr2块，Husky为`:68–77`，且实际生效值见`task_contract.yaml:21`，据Codex复核#8与SRC-0402）；已补入SRC-0400“2026-10-20补充”。
- 改动：task7 TASK入口节、§2.3、§2.7第7步、§2.8、§2.9、术语补充、U17、U30、U31、U33–U35、U38；PROCEDURE中4L行与task7.13行；task7.9 TASK状态行、RESULTS (B) L1/B.1/B.4、(D)；task7.13 TASK；task7.4 RESULTS §1加注；task7 RESULTS、PROGRESS、PLAN；Codex派发提示同步为3维并加读SRC-0401。
- 剩余待定：U32（下层奖励数值）、U36（到达/超时）、U37（推演成本）、E1–E9、S1–S5、V4/V5、B10；末端速度范围与放慢惩罚权重以提示A核查结果冻结。没有代码、训练或评估。
