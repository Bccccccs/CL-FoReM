# task8.2 — 执行流程

状态：**done（2026-10-26本节点范围已由父及独立Sol high复核通过；task8整环境尚待后续）**。实际模型/强度：gpt-6.1-sol/high实施及独立复核；闭接触fix1通过。证据[SRC-0993](../../../SOURCES.md#src-0993)、[最终依赖门SRC-0994](../../../SOURCES.md#src-0994)。推荐Codex GPT6.1sol / Claude Sonnet5.5，几何high/传感器medium（复杂排错high）；推荐不代替实际配置。历史规划/过程保留。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；当前无再分子任务。若确需拆分，子目录继承task8.2.N，每节点同样三文档；先登记顺序、依赖、负责人、模型/强度、三文档链接和父验收关系再派发，编号稳定不复用。未建立子节点不代表可以绕过父文件归属或预算。

## 输入与顺序

依赖：8.1的MapAsset与夹具验收后；与8.3独立文件可并行。 必须先核输入hash/版本、父预算余额和文件写入所有权。独立Agent仅改本节点TASK列出的代码/配置/tests与自身RESULTS/日志，接口问题向父报告。

- [ ] 写轴对齐体素union独立暴力参照和解析box射线/距离测试；区分参照实现与被测实现，不用同一DDA互证。CPU float64参照；GPU float32误差上限从输入尺度/算术及测试观测登记，不直接沿原box精度当PCD精度。
- [ ] 按父TASK的floor索引构建占据；重复点合并、无补洞无滤点。PCD数据域外输入拒绝；查询射线和已执行base不因此自动报碰撞或终止。射线支持域外入域、出域无命中；场景有限域外为空，地面独立。边界格/负坐标/旋转点/离地结构均可追溯。缓存键包含源hash、resolution、origin、backend版本、device/dtype。
- [ ] 实现空间遍历最近命中，保留场景遮挡；不得构造全量ray×point或ray×voxel巨大张量。允许DDA或等价空间索引；若合并邻体素为box，须严格保持union，禁止用整物体AABB填空腔。
- [ ] collide沿原base全高度XY投影与arm 3D胶囊/地面、自碰撞接口，接触算碰撞；使用空间候选缩小检查而不是改变接触容差。只有场景后端改变，robot.self_collision使用8.3提供的对象。scene.contains用于初态/目标校验；planning_height是truth-only且与占据同源。
- [ ] 验证PCD-only；保持sidecar不变、生成新manifest/hash后增/删一个可见立方体的点云，深度和碰撞结果必须对应变化；遮挡后点云变化不能泄漏进前景扫描。报告体素对解析原物体的几何差异/薄结构失效，不能把差异全称浮点误差。
- [ ] 记录单图预处理/查询内存、CPU/GPU设备与最小性能；父复核解析反例后交8.3/8.4。

## 验证命令与异常（尚未执行）

在已运行forem-dev内，`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests`，实际执行只选择本节点已交付的tests文件；父最终集成时再运行所需集合。通过标准不是只有exit0，还须满足[TASK](TASK.md)所列断言。宿主通过`sg docker -c`调用，日志保留实际argv/退出码；不在宿主装ROS。

全任务共享累计1800s验证预算，单smoke≤120s/64步、先batch1后2；语义图单图30s，均为SRC-0987工程上限。子任务不能重置预算；没有GPU份额时先完成不依赖GPU的部分。超时/依赖缺失写未验收，不删失败数据、不降条件、不静默CPU回退。失败定位后最小修复与必要复验，改变科学合同或扩大范围须先交父说明。

## 输出与交接

逐run写RESULTS：目标/授权、实际负责人/模型/强度、文件与源hash、命令/退出码、证据、通过/未通过门、资源账本、限制/风险、下一步；如有进程附PID/容器/日志/监控/停止方法。当前尚无运行任务。父复核后才标done；共享SOURCES条目由父落账，子Agent提交主张与精确证据位置。
