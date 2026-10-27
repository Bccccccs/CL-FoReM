# task8.3 — 执行流程

状态：**done（2026-10-26本节点范围已由父及独立Sol high复核通过；task8整环境尚待后续）**。实际模型/强度：gpt-6.1-sol/medium实施、gpt-6.1-sol/high独立复核。证据[SRC-0993](../../../SOURCES.md#src-0993)、[最终依赖门SRC-0994](../../../SOURCES.md#src-0994)。推荐Codex GPT6.1sol / Claude Sonnet5.5，几何high/传感器medium（复杂排错high）；推荐不代替实际配置。历史规划/过程保留。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；当前无再分子任务。若确需拆分，子目录继承task8.3.N，每节点同样三文档；先登记顺序、依赖、负责人、模型/强度、三文档链接和父验收关系再派发，编号稳定不复用。未建立子节点不代表可以绕过父文件归属或预算。

## 输入与顺序

依赖：8.1共享合同；robot策略可独立做，PcdPanorama最终依8.2。 必须先核输入hash/版本、父预算余额和文件写入所有权。独立Agent仅改本节点TASK列出的代码/配置/tests与自身RESULTS/日志，接口问题向父报告。

- [ ] 读robot.py所有body碰撞/球-盒/索引/缓存路径与URDF实际link；按明确名单只禁传感器body碰撞，保持link/TF/外参和非sensor几何。schema4 self_body_allowed/zero_sphere_body_pairs若仍引用原索引，不得简单删列表导致错位；优先独立检测掩码。
- [ ] 构造只碰传感器的球/姿态和只碰top_plate/车体/其他arm的独立正负例；新策略前者忽略、后者保留。核关节FK、IK接受/避碰分支通过GhostRobotGeometry使用同一豁免；豁免不传播到环境障碍物或地面。
- [ ] 沿原像素中心方向、base相对(0,0,0.5)m、360×90/6m调用scene.raycast，加原解析地面。自身caps/body不参加射线遮挡；sensor原点落在机器人内部也不使扫描失效，落在场景实体内仍按scene语义处理并让初始化拒绝。
- [ ] 返回Depth尺寸/valid/points一致；ghost模式self_hit和origin_inside_self字段为false并附模式元数据，含义是未应用自身遮挡。不得把valid全设true或绕过场景最近命中。
- [ ] 用相同base、不同q/机器人包络确认扫描相同；改变base XY/yaw确认sensor随底盘；近障碍遮远障碍依然成立。reset scan与动作末scan调用同一配置，不只修初始帧。
- [ ] 与8.2联合跑真实PCD夹具；记录sensor/robot衍生hash、碰撞豁免名单和全部未豁免正例，交8.4。

## 验证命令与异常（尚未执行）

在已运行forem-dev内，`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests`，实际执行只选择本节点已交付的tests文件；父最终集成时再运行所需集合。通过标准不是只有exit0，还须满足[TASK](TASK.md)所列断言。宿主通过`sg docker -c`调用，日志保留实际argv/退出码；不在宿主装ROS。

全任务共享累计1800s验证预算，单smoke≤120s/64步、先batch1后2；语义图单图30s，均为SRC-0987工程上限。子任务不能重置预算；没有GPU份额时先完成不依赖GPU的部分。超时/依赖缺失写未验收，不删失败数据、不降条件、不静默CPU回退。失败定位后最小修复与必要复验，改变科学合同或扩大范围须先交父说明。

## 输出与交接

逐run写RESULTS：目标/授权、实际负责人/模型/强度、文件与源hash、命令/退出码、证据、通过/未通过门、资源账本、限制/风险、下一步；如有进程附PID/容器/日志/监控/停止方法。当前尚无运行任务。父复核后才标done；共享SOURCES条目由父落账，子Agent提交主张与精确证据位置。
