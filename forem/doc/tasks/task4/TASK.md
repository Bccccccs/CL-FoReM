# Task4 — Husky普通SAC Gazebo基线与首次WM尝试（阶段一：CBL复现）

状态：**closed（2026-10-16按用户指令归入阶段一“CBL复现”，不再推进）**。世界模型闭环研究自[task7](../task7/TASK.md)起从头构建，本任务的WM部分不再继续。

## 目标（历史）

在Task3迁移的Husky+UR5链路上，用cbl自写SAC（`ScwmSAC`，逐行沿用`SAC.update_parameters`）在Gazebo中从头训练普通SAC基线，并首次尝试SC²-WM式执行前反馈（候选动作→冻结WM预测→修正表征→SAC最终动作）。

## 保留的子节点

|节点|内容|结果要点|
|---|---|---|
|[task4.7](task4.7/TASK.md)|状态/动作/奖励/终止合同核对|41维robot_state来源、规划与实测字段区分，见其RESULTS|
|[task4.8](task4.8/TASK.md)（含[4.8.1](task4.8/task4.8.1/TASK.md)）|Gazebo普通SAC三种子×100万步；多实例隔离|学不会：最终验证成功≈0，约91%回合因20次IK失败终止|
|[task4.9](task4.9/TASK.md)|动作条件WM（10万步分叉点）|预登记设计负结果：256维trunk表征上WM只比恒等好2.8–4.1%，几乎不用动作；改用41维robot_state后skill +15.4%|
|[task4.10](task4.10/TASK.md)|冻结WM的执行前反馈实现|`FeedbackGaussianPolicy`代码与8项单元测试；反馈臂t4s-fb-s0/1/2训练到约100万步，最后验证物理成功同为0/5|

## 已删除节点（2026-10-16，用户确认）

task4.1–4.6（视觉惯性定位路线，2026-10-09已弃用）与task4.11–4.13（未执行的比较/适配/复核计划）已删除；原文在`/home/ybc/projects/CL-FoReM-reset-backups/20261016-doc-cleanup/forem-doc-before-cleanup.tar.gz`。[SRC-0321](../../SOURCES.md#src-0321)

## 对阶段二的意义

- Gazebo直接训练失败的原因由[task6](../task6/TASK.md)诊断，不在本任务继续。
- 4.9/4.10的表征选择、观测一步滞后（`o_{t+1}`不含`a_t`对底盘/地图的物理影响）和反馈实现，是task7设计时的参考输入，不是task7的验收证据。

## 模型推荐

本任务已关闭，无后续执行。查阅/引用时推荐Codex GPT6.1sol、Claude Sonnet5.5，low/默认。
