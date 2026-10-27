# task8.9.1.2 — 执行流程

状态：**active（I1完成有界部分诊断，a/b固定全量执行中）**。目标/验收见[TASK](TASK.md)。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；不再拆分。若需拆分，继承`task8.9.1.2.N`并先建三文档、登记顺序/依赖/负责人/模型强度/验收；编号稳定不复用。

## 步骤

1. 读父三文档、r3就绪报告、SRC-1210；建账本`forem/logs/task8/t8-init-20261027/budget.json`（≤1200s）。
2. I1诊断（有界、可中断，超时保留分项部分结果）。
3. 依诊断占比实施(a)/(b)，必要时(c)；先写等价测试再实现；派生缓存放`forem/results/task8/<run-id>/scene-cache/`，不入Git。
4. I2–I5；独立Sol验收；结果写RESULTS，父汇总。

## 异常

做不到逐元素等价则停止报告；若根因是采样规则本身（如拒绝率极高）而非实现开销，停止报告，不改规则。

## r4实际流程与固定清单

1. I1正式256、seed4718、train、float32、2线程、DLS CUDA graph，内部380s/runner390s。逐环境快照，不改RNG或采样分支。I1部分诊断不冒称256reset完成。
2. CPU64 canonical八张量写缓存；缓存键=原PCD sha256+未改scene.py sha256+pcd-voxel-v3。运行时`TASK8_SCENE_CACHE`显式目录；源PCD/sidecar实际hash、index key、payload hash与metadata必须匹配，否则拒绝，无重建fallback。无缓存时仍原路径。
3. `_read_pcd`只将逐行有限性检查由numpy调用改为Python math.isfinite；float()、行号、字段/格式/边界/哈希验证保留。旧完整assets原件在tests/assets_reference_r3.py，供逐值uint64位比较。
4. 离线validator仅把原load_asset中的manifest JSON读取替换为预读doc，其余原验证源码与旧解析器不变；新旧PCD全值bits一致，再from_asset CPU64→落盘→真实cache.load CPU64八张量equal。进程32、每worker库线程1；记录全局wall与worker累计wall。96图pilot与10228新图复用合并10324；source/manifest hash一致才准复用pilot，不重验96图。超时保留progress.jsonl，不发布新正式index。
5. 固定计划：`forem/results/task8/t8-init-20261027/{pilot-plan,full-plan,i5-jobs}.json`。I5依序GPU完整task8_sim回归（新artifact根）、32图GPU32八张量+全部非timing provenance、缓存正式256reset；同脚本cache未插桩细项不能用0当实际成本0。I1/I5前76行map_id/seed与累计stats纯读对比；独立Sol核原件。
6. 必要`task8_lower/training.py::_contract`新增assets.py、scene_cache.py源码hash和runtime cache resolved root/index sha256（未启用为None）。缓存改变拒绝恢复；不改环境恢复、RNG、主循环/SAC或预算语义。

实际/推荐模型同TASK；固定工作Terra low只执行父明确释放清单，I5不足则停止，不擅扩1200s。
