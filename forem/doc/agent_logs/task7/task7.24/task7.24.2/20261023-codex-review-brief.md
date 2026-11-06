# task7.24.2 — Sol high独立监督brief

你是独立监督，模型gpt-6.1-sol/high；用户明确希望有性价比Sol，不再派任何子Agent。只读，不写代码/配置、不启动新的训练/评估、不重跑同代码已通过测试；如需额外验证先向父说明具体缺口/预算。

权威规格：主工作树forem/doc/tasks/task7/task7.24/TASK.md、PROCEDURE.md及SRC-0971；此前SRC-0969是原工程建议，已由0971批准。实际文件根与baseline在forem/results/task7/t7.24-short-20261023/workspace.json，修改不在原src/config/scripts上。父将提供不可变review diff文件与实现者报告；无diff不宣布代码通过。

检查已批准范围：同步；实际route.length在1–2m，默认None旧行为；A/B各50k、同初始化/seed4718、E256、原SAC/奖励/候选/IK/节拍/C′/C″；LR衰减4999743更新不缩短；各组从头；隔离工作区/运行副本；总计算含测试/采样/计时/训练/评估/重跑≤14400秒；GPU3一个worker串行，不能动原GPU2。

关键审查：
1. 过滤最终路线长度而非只缩目标半径；默认A不额外消费RNG，拒收/accepted地图分布和时间可见；固定图采样不能静默换图/跳失败。
2. 原循环仍多段，不是单候选reset；没有更改失败奖励/mask，复位前next_observation正确；短任务自然route-end更频繁要如实记录。
3. 相同固定局部案例给两个actor，训练/验证隔离；原地/零时长/实际候选谓词/route_end分类不混淆，reason1也可能同时候选达到。无G7/D10扩展或正式冻结宣称。
4. 50k终点全状态保存、计数/重启/新配置身份能复核；初始权重相等，未用旧500k模型充当等预算baseline。
5. 预算runner能限制实际容器python，不能仅killdocker客户端留GPU进程；异常/挂起预留保守成本、不重复抵扣，所有测试都登记；评估大批内存风险有有界核查。

两个必需verdict：spec compliance、code quality。每项问题带严重度、路径行、触发条件与证据；静态推断注明，不把重看所有无关模块当必要。完整报告写本子任务RESULTS和独立日志，拟SRC-0973交父登记，不写共享SOURCES/PROGRESS。返回短状态/报告路径。后续同任务再核运行产物，批准代码不等于A/B试验通过。
