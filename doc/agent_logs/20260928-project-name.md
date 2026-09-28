# NAME-028 项目命名建议

- 执行 Agent：Codex /root
- 开始时间：2026-09-28T15:31:49.243904+08:00
- 状态：done（候选建议交付，未定名）
- 用户要求：给新研究项目起类似TopAY的简短名字，mmhusky是旧项目名。
- 范围：命名建议及本记录，不更改代码、目录、包名或实验配置。
- 已读：AGENTS.md、doc/README.md、PROGRESS.md、DECISIONS.md、RESEARCH_GOAL.md、任务模板；最新机制参考D38/D39。
- 版本/环境：根仓库存在既有修改和未跟踪doc/docker；不涉及容器或算法执行。

## 进度

- 2026-09-28T15:31:49.243904+08:00：登记；研究方向为世界模型前瞻、执行前特征修正与真实执行反馈适应，SAC输出最终动作。命名不表示机制已验收。

## 长任务

无。

## 候选与建议

首选 FoReM：Foresight-Refined Mobile Manipulation，前瞻修正的移动操作；Fo=Foresight、Re=Refined、M=Mobile Manipulation。方法副标题可用 World-Model Foresight and Feedback Adaptation for Mobile Manipulation，覆盖D38计划中的反馈适应。
备选 FoAM：Foresight and Adaptation for Mobile Manipulation；CLAM：Closed-Loop Adaptive Manipulation。
建议根据机制与可读性选FoReM；没有进行名称查重，不宣称名称唯一。用户尚未选定，不记作正式重命名决策。

## 改动与验证

仅新增本日志和PROGRESS的NAME-028行。实际执行Python文档写入，退出码0；随后检查任务行、日志候选和文件存在性。不涉及算法测试、训练或实验验收。

## 交接

候选交付完成。后续按用户选择确定正式名，再做学术名称查重及有范围的文档命名统一；本轮不改旧工程路径。

## 2026-09-28 查重后续

NAME-CHECK-028已发现FoAM与CLAM同领域直接简称冲突，撤回二者推荐；FoReM暂未发现同领域方法重名，但与Forem社区软件重名。详见[查重记录](20260928-name-check.md)。原候选排序是查重前建议，不代表名称可用性结论。
