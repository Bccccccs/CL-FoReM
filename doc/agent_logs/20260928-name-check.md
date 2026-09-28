# NAME-CHECK-028 学术名称查重

- Agent：Codex /root
- 开始：2026-09-28T15:51:53.050443+08:00
- 状态：done（公开检索，非唯一性保证）
- 范围：FoReM、FoAM、CLAM简称与完整展开的公开论文/项目检索；不改正式名或代码。
- 已读：AGENTS、README、PROGRESS、DECISIONS、NAME-028；已注意DOCS-028正在调整文档，本任务仅维护独立记录与自身进度行。
- 进度：首轮发现FoAM机器人前瞻操纵论文、CLAM机器人学习论文；FoReM主要出现Forem社区软件，需要继续定向检索。
- 长任务：无。

## 检索范围与实际查询

2026-09-28，通过web搜索检索简称、全称及机器人/机器学习/world model组合；定向搜索arxiv.org、openreview.net、proceedings.mlr.press、roboticsproceedings.org、dblp.org、ieeexplore.ieee.org、dl.acm.org、proceedings.neurips.cc。这是搜索引擎站点限定检索，不是数据库全量查重；DBLP返回robots限制，不能称直接完成DBLP数据库检索。没有直接检索Google Scholar付费/登录接口。

查询包括：
- "FoReM" robotics machine learning paper
- "FoAM" "manipulation"
- "CLAM" "robot" learning manipulation
- "FoReM" machine learning / "FOREM" robot paper
- "Foresight-Refined Mobile Manipulation"
- "FoReM" site:arxiv.org / site:arxiv.org/abs/
- "forem" site:openreview.net / site:proceedings.mlr.press / site:roboticsproceedings.org
- "FoReM" "world model" / "manipulation"
- "FoReM" site:dblp.org
- "FoReM" (site:ieeexplore.ieee.org OR site:dl.acm.org OR site:proceedings.neurips.cc)
- "Foresight and Adaptation for Mobile Manipulation"
- "Closed-Loop Adaptive Manipulation"
- "FoReM" robotics，排除forem.com/dev.to/leforem域名复查

## 查重结果与原始来源

1. FoAM：同领域直接简称冲突，建议淘汰。
   论文FoAM: Foresight-Augmented Multi-Task Imitation Policy for Robotic Manipulation，Litao Liu等，首次提交2024-09-29，修订2025-03-26。摘要将FoAM展开为Foresight-Augmented Manipulation Policy，机器人多任务模仿学习及前瞻增强，与候选名称概念高度接近。
   原文：https://arxiv.org/abs/2409.19528 （已打开核验标题、日期、摘要）
2. CLAM：同领域直接简称冲突，建议淘汰。
   论文CLAM: Continuous Latent Action Models for Robot Learning from Unlabeled Demonstrations，Anthony Liang等，首次提交2025-05-08。机器人动作学习/动力学预测方法。
   原文：https://arxiv.org/abs/2505.04999 （已打开核验）
   作者项目：https://clamrobot.github.io/ （搜索结果正文支持）
3. FoReM：本轮未检出机器人/世界模型领域同名方法，也未检出拟定完整展开Foresight-Refined Mobile Manipulation的论文命中；仅代表本轮覆盖范围，不能证明不存在。
   确切跨领域软件重名：Forem是支撑dev.to的开源社区平台。
   官方仓库：https://github.com/forem/forem （搜索结果官方README明确说明）
   OpenReview命中BACKENDFORGE中Forem作为被测社区软件任务，并非同名机器人算法；其他命中多为博客平台/机构/普通词。

## 建议

撤回FoAM、CLAM作为优先候选；FoReM可继续作为有条件首选：同领域学术冲突暂未检出，但通用检索辨识度存在缺点。正式首次出现配完整标题与robotics/mobile manipulation关键词；仅大小写变化不算消除重名。若用户要求跨领域也尽量独特，应另拟新候选再查，而不是声称FoReM全网唯一。
原有展开保留：FoReM — Foresight-Refined Mobile Manipulation。用户尚未正式定名，不批量更改项目、包名或路径。

## 验证与交接

实际web检索完成、两篇arXiv原文页面核验成功；本记录保留来源与检索限制。Python写入记录及自身进度行，检查ID唯一和来源链接存在。未改算法、未操作其他Agent实验/文档重构。下一步由用户确定是否接受FoReM的跨领域重名，或重新起名。
