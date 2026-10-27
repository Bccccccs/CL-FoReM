# task8.4 — 执行流程

状态：**done（2026-10-26本节点父及独立Sol high验收通过；语义图与总验收待后续）**。实际实施/独立复核均gpt-6.1-sol/high；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，跨模块状态合同需推理。证据[SRC-0995](../../../SOURCES.md#src-0995)，历史过程保留。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；当前无再分子任务。若确需拆分，子目录继承task8.4.N，每节点同样三文档；先登记顺序、依赖、负责人、模型/强度、三文档链接和父验收关系再派发，编号稳定不复用。未建立子节点不代表可以绕过父文件归属或预算。

## 输入与顺序

依赖：8.2、8.3完整验收；不能只靠mock开始最终集成验收。 必须先核输入hash/版本、父预算余额和文件写入所有权。独立Agent仅改本节点TASK列出的代码/配置/tests与自身RESULTS/日志，接口问题向父报告。

- [ ] 列出旧EpisodeEnv.reset全部box/renderer构造、EpisodeSampler.sample/validate_goal_position、TruthPlanner各处真值入口、DecisionEnv内部构造与versions；逐项改由scene对象供给，不保留隐式旧pool默认路径。
- [ ] PcdTruthPlanner保持原A*代价/障碍抬升/连通与见证语义，height由scene同一占据投影；路线clear沿原“低于障碍顶”保守判定，只替换几何查询。不得用场景JSON boxes来规划或自动补标准围墙；地面和域规则显式记录。
- [ ] 保持地图/初始化RNG流、CBL固定关节、目标分布/IK见证与拒绝语义，新增输入只为选择scene。sampler可接受取消/外部deadline，以便运行预算结束返回incomplete而不伪造失败episode；拒绝不自动换成易图/放宽姿态/降低障碍。固定测试factory/回放state允许验证step但与随机采样能力分别报告。
- [ ] 实现单批Core及mask reset：只替换选中scene/route/初态/Grid/timestamp/counters/map_id/seed；重新扫描只更新选中行；不访问旧c.renderer.boxes、c.collision.boxes。上下文相同的未选行逐字段保持。
- [ ] sync_v5和decision_*_legacy显式传Core参数；对照原同几何/相同ghost策略的受控输入确认动作映射、dt、IK/奖励/终止输出一致。地图离散/ghost导致差异单列，不强求与旧传感器观测逐元素相同。
- [ ] 接入候选生成及原局部rollout：只传Grid快照和GhostRobotGeometry，未知仍未知。更改场景隐藏障碍而保持观测快照，候选/局部rollout不应变化；真实执行可以在看不到处因碰撞失败。这是信息边界检查，不修改科学定义。
- [ ] PcdDecisionEnv注入新episode入口而非继承旧构造默认；map-id强制选择/自动结束行reset等原能力走新后端。versions含scene/ghost/原观察动作版本及profile；新环境入口拒绝旧env/replay恢复。若提供actor，沿FrozenLowerPolicy.load的actor-only校验并记录权重hash。
- [ ] 两图batch部分reset、随机初始化和固定factory各跑必要测试；确认step提交的真实q/FK来自实际状态，不能以目标值代填。交8.5/8.6。

## 验证命令与异常（尚未执行）

在已运行forem-dev内，`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests`，实际执行只选择本节点已交付的tests文件；父最终集成时再运行所需集合。通过标准不是只有exit0，还须满足[TASK](TASK.md)所列断言。宿主通过`sg docker -c`调用，日志保留实际argv/退出码；不在宿主装ROS。

全任务共享累计1800s验证预算，单smoke≤120s/64步、先batch1后2；语义图单图30s，均为SRC-0987工程上限。子任务不能重置预算；没有GPU份额时先完成不依赖GPU的部分。超时/依赖缺失写未验收，不删失败数据、不降条件、不静默CPU回退。失败定位后最小修复与必要复验，改变科学合同或扩大范围须先交父说明。

## 输出与交接

逐run写RESULTS：目标/授权、实际负责人/模型/强度、文件与源hash、命令/退出码、证据、通过/未通过门、资源账本、限制/风险、下一步；如有进程附PID/容器/日志/监控/停止方法。当前尚无运行任务。父复核后才标done；共享SOURCES条目由父落账，子Agent提交主张与精确证据位置。
