# 2026-10-21 Claude：地图设计讲解与“真值地图线”决定

- Agent：Claude（claude-opus-5-5），推理强度未知。任务ID：TASK7-TRUTH-LINE-20261021。
- 用户要求：讲解task7进度与设计，重点是感知栅格；讨论是否像CBL/N²M²那样训练用真值地图。
- 授权边界：只读核查与写文档；不改代码、不运行程序。

## 过程

1. 只读核对：task7 TASK/PROCEDURE/RESULTS、task7.7 RESULTS、task7.14 RESULTS；SC²-WM `waypoint_networks/utils.py:377–419`（`est_occ_from_depth`三类占据计数）、`semantic_grid.py:115–127`（逐格贝叶斯乘积归一化）、`ss_trainer_ETP.py:1880–1940`（栅格只进占据/语义补全与航路点U-Net）；CBL `forem/src/modulation_rl/scripts/modulation/envs/map.py:132–180、221–311`（sim真值平面图旋转裁剪后`>0.1`二值化，Gazebo用costmap≥20）。
2. 向用户说明：两通道“看到过＋最高高度”与SC²-WM概率融合、CBL真值二值图的差别；静态场景中真值地图≈已知到达后观测，f_p在真值线中基本无可预测信息；SC²-WM训练与部署均只用自身传感器。
3. 用户先提出“保留两条线”，Claude以选择题询问细节，用户未答而追问；说明后用户回复“ok忠于SCWM旧可以”。

## 改动文件

- `forem/doc/SOURCES.md`：新增SRC-0432。
- `forem/doc/DECISIONS.md`：新增TASK7-NO-TRUTH-LINE-20261021。
- `forem/doc/tasks/task7/TASK.md`：一致性表#12补注。
- `forem/doc/PROGRESS.md`：项目级记录新增本行。

## 结果与下一步

- 设计不变：不加真值线，task7.14实现与task7.15–7.19范围不受影响。
- 未解决：讲解中提到的“最高高度取max不能纠错，ManiSkill深度噪声下可能累积幽灵障碍”只作风险说明，用户未要求改动。
