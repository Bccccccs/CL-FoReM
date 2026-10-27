# task8.6 — 执行流程

状态：**review（功能验证/性能/证据交付已完成；执行越界使严格合规失败，不能标无偏差done）**。实际独立Agent gpt-6.1-sol/high；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨模块证据核查需高强度；父已亲自复验。证据[SRC-0997](../../../SOURCES.md#src-0997)、[SRC-0998](../../../SOURCES.md#src-0998)。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；当前无再分子任务。若确需拆分，子目录继承task8.6.N，每节点同样三文档；先登记顺序、依赖、负责人、模型/强度、三文档链接和父验收关系再派发，编号稳定不复用。未建立子节点不代表可以绕过父文件归属或预算。

## 输入与顺序

依赖：8.1–8.5实现/结果交齐；不得仅采信子Agent自报。 必须先核输入hash/版本、父预算余额和文件写入所有权。独立Agent仅改本节点TASK列出的代码/配置/tests与自身RESULTS/日志，接口问题向父报告。

- [ ] 重新读源码/差异和失败测试，不把父计划或子RESULTS写成事实。核8.1点云改变干预、8.2解析参照、8.3collision/occlusion、8.4reset与truth隔离、8.5逐图状态；源task7代码和资产hash未改。
- [ ] 在budget余额内执行必要CPU单元/集成和一张已核空闲GPU上的float32链路；选旧回归中相关Core/kin/observation用例验证只读复用，无新改动或未解疑点不反复全量跑。run元数据必须带实际模型/设备/版本/variant。
- [ ] smoke：随机立方体PCD，batch1再batch2，既有同步下层profile和两种旧决策profile分别验证接口；用受控非零动作证明机器人位移或碰撞阻止，记录实际q/FK/base，至少一次状态提交和后续scan。固定脚本actor只用于结构检查；旧actor可另做冻结推理，无optimizer调用，不能以训练成功率作门。
- [ ] 验证每种链路完整性：scan depth→Grid→observation→candidate→local rollout→selected subgoal→action→IK→collision→commit/reject→scan。标清truth消费者，遮挡后障碍不可提前进入Grid，场景碰撞不绕过；更改PCD的反例可复现。
- [ ] semantic 24图采用8.5已有产物，复核证据和代表性失败，不重复花费全批运行预算。记录完整成功/失败/超时分母；全批不可运行则按本TASK强制门与pass_with_map_limitations区分；不作地图完全可行结论，不把程序异常归为采样失败。
- [ ] profile分开测加载/体素化及缓存、reset采样、路线/IK、collision、raycast/Grid、CPU→GPU搬运、候选/局部推演、冻结推理、日志/输出；warm与cold分开，wall/sim/GPU时间分开，p50/p95注明实际样本数，峰值内存/显存和实际tensor设备齐全。窗口少不作长训工期外推。
- [ ] 若有明显热点，只在当前实现范围做同输入分块/缓存/独立数据准备等优化；保持点云/采样/步长/数据顺序/碰撞语义不变。优化回所属子任务修改并重验，不扩大运行预算。没有收益照实保留证据。
- [ ] acceptance.json逐门给pass/fail/not_run及证据路径；父亲自复查命令、原产物和hash再更新状态。交下层SAC下一阶段：新环境版本/观测差异/初始化可行性/吞吐成本，旧v5退化和D10未闭合项另列；只建议下一调查输入，不直接设计新实验组/启动训练。

## 验证命令与异常（尚未执行）

在已运行forem-dev内，`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests`，实际执行只选择本节点已交付的tests文件；父最终集成时再运行所需集合。通过标准不是只有exit0，还须满足[TASK](TASK.md)所列断言。宿主通过`sg docker -c`调用，日志保留实际argv/退出码；不在宿主装ROS。

全任务共享累计1800s验证预算，单smoke≤120s/64步、先batch1后2；语义图单图30s，均为SRC-0987工程上限。子任务不能重置预算；没有GPU份额时先完成不依赖GPU的部分。超时/依赖缺失写未验收，不删失败数据、不降条件、不静默CPU回退。失败定位后最小修复与必要复验，改变科学合同或扩大范围须先交父说明。

## 输出与交接

逐run写RESULTS：目标/授权、实际负责人/模型/强度、文件与源hash、命令/退出码、证据、通过/未通过门、资源账本、限制/风险、下一步；如有进程附PID/容器/日志/监控/停止方法。当前尚无运行任务。父复核后才标done；共享SOURCES条目由父落账，子Agent提交主张与精确证据位置。


## P0 本轮规划独立审查（不运行实现验收）

本轮按brainstorming技能委派只读builder-check：输入父/子21份规划文档、根AGENTS及SRC-0984–0987；输出会阻止执行的歧义/范围问题，仅返回父，不改共享文件或代码、不运行仿真。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high（几何/接口合同复核）；实际子Agent模型/强度按可核信息记未知。父接收后亲自修订与验证；P0完成不等于8.6运行验收完成。独立日志在agent_logs/task8/task8.6/。其余运行阶段尚未执行。
