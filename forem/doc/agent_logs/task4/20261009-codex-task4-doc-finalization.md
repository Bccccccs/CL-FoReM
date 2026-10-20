# Task4新版文档核对与完善

- 开始：2026-10-09T09:53:13.751068+08:00；负责人Codex /root；状态done（文档交付，未实施）。
- 用户本轮仅授权文档：不改源码/运行配置、不装依赖、不构建、不启动仿真、不采集新实验数据、不训练、不派发Agent。只读源码/已有证据可用于方案。
- 研究范围：同任务/观测权限/训练预算下移植SCWM内部反馈思想到Husky普通SAC；惯性估计已弃用；不以证明同种潜态累积漂移为前置。
- 已读：根AGENTS、README、PROGRESS、SOURCES、Task4父三文档/旧节点及本会话重写日志。
- 所有权：Task4重写为本会话TASK4-SCWM-REPLAN（中断未完）；另一Codex的PROJECT-SCWM-*核查已done且日志明确不改本路线。保留其SRC0168/0169/0175–0177和独立记录；本轮新增来源先检查编号。
- Git：main，大量历史未提交/未跟踪内容；不还原/提交/推送。根命令进程过滤未发现gzserver/rosmaster/roslaunch；这不是新实验验证。
- 初步问题：新4.7–4.13只在父文档被引用，子三文档缺失；父RESULTS仍旧VIO；前稿自定共同前缀/预算分配/额外测试模式及噪声/固定周期更改被写成执行合同，需按本轮范围区分草案和有效授权。
- 拟修改：Task4父三文档、新4.7–4.13三文档、旧节点历史标注、必要AGENTS/README/PLAN/PROGRESS/DECISIONS/SOURCES及本日志。不会修改ENV运行事实或forem/config等运行文件。
- 推荐：Codex GPT6.1sol、Claude Sonnet5.5；普通文档low/默认，跨模块机制核对medium。实际模型/强度未知；没有启动Claude/子Agent。
- 只读保护快照：同目录20261009-task4-doc-scope-before.json，记录源码/配置/脚本/docker/tests文件size/mtime，结束核对；它是文档审计证据，不是实验采集。

## 完成交付与验证

- 完成：父三文档更新、新4.7–4.13共21份三文档；54份旧递归文档加历史退出标记，原文保留。父RESULTS集中交接，不增加同职责第四文档。
- 同步：根AGENTS（用户追加的性能优化职责）、forem/AGENTS、README/PLAN/PROGRESS/DECISIONS、SOURCES0178–0181及旧草案效力说明。保留另一Agent的来源0182和PROJECT-PPT记录，没有接管其文件。
- 文档方案：普通SAC有限先导→动作条件WM→冻结WM执行前反馈→公平任务比较→后续独立TTA。补齐实际末端/时间口径、数据切分/身份/动作信息检查、连续SAC分布和梯度一致性。未恢复VIO或制造误差。
- 范围修正：先前草案自定预算切片、共享前缀、实验组/测试编号/固定数值不作为授权；用户规模与时限保留，覆盖在4.7按有效协议核对。未修改live配置。
- 命令/结果：只读git status/文档与源码核查；stdlib文档检查退出0；git diff --check（共同约定/全局文档）退出0。有效父/子24文档链接、来源锚点、三文档、递归声明/模型和未实施状态无错误。人工复核依赖顺序及4.12非首轮前置。
- 保护核对：[检查JSON](20261009-task4-doc-verification.json)；875份src/config/scripts/docker/tests文件与开工size/mtime一致，0变化。没有安装、构建、启动、采集、训练、停止进程或委派。
- 交接：[父RESULTS](../../tasks/task4/RESULTS.md)，后续Claude收到实施授权后从4.7核对合同/预算开始登记接手；本轮到文档交付止。
- 限制：没有新实测，不能宣称GPU/多线程已提速或72小时已可达，不能将旧结果计为新验收。Task4研究仍review/尚未实施；普通文档推荐low/默认、跨模块medium，GPT6.1sol/Sonnet5.5，实际未知。
