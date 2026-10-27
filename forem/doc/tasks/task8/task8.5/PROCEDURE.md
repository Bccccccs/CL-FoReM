# task8.5 — 执行流程

状态：**done（2026-10-26本节点本次24图诊断由Sol及父核查通过；独立总验收待8.6）**。实际Sol gpt-6.1-sol/medium、Luna gpt-6-luna/low，推荐GPT6.1sol/Sonnet5.5 medium作合同/验收、Luna/Sonnet5.5 low固定执行；证据[SRC-0992](../../../SOURCES.md#src-0992)、[SRC-0996](../../../SOURCES.md#src-0996)。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；当前无再分子任务。若确需拆分，子目录继承task8.5.N，每节点同样三文档；先登记顺序、依赖、负责人、模型/强度、三文档链接和父验收关系再派发，编号稳定不复用。未建立子节点不代表可以绕过父文件归属或预算。

## 输入与顺序

依赖：导入依8.1；环境逐图验证依8.4；可先做独立离线部分。 必须先核输入hash/版本、父预算余额和文件写入所有权。独立Agent仅改本节点TASK列出的代码/配置/tests与自身RESULTS/日志，接口问题向父报告。

- [ ] 复查24对是否仍与SRC-0986 hash一致；不同则记录新版本，不覆盖旧审计。校验配对、PCD真实点数/边界/重复点、metadata。按map-id分类报告坏图，不跳过异常伪造全批成功。
- [ ] 保留PCD点及JSON原字节；manifest保存两者hash/scene类别/单位/坐标/采样语义，split=smoke。若sidecar缺失/字段未知，严格按8.1合同拒绝或显式声明，不能自动猜单位/中心角点约定。
- [ ] 做点云与sidecar几何差异诊断：点是否落入声明几何、空box/无对应点、补墙风险、旋转/裁剪边界；诊断用JSON只作参照，不能反过来修PCD真值。无法确立object对应则保留原语义树与差异清单，不伪造逐点类别。
- [ ] 同一PCD使用sidecar元数据不变/删语义标签的副本，运行几何和扫描应一致；同时改PCD而保持sidecar，更新对应manifest/hash后几何应变化。源文件及旧地图池hash不变。
- [ ] 先在随机立方体PCD通过完整链路，再对24图逐图有界初始化/扫描/动作诊断：记录map-id、seed、初态/FK、采样拒绝、有效深度/观察图、碰撞和step、域规则，至少一次非零动作尝试；每图30s，超时明确未验收。存在合法随机任务再做真实step；无合法任务只能报告初始化失败，不能仅摆好robot冒称默认采样成功。
- [ ] 全批表格区分load_failed/geometry_failed/reset_timeout/reset_rejected/step_checked；异常崩溃单列error，不能归为地图不可行。附至少一张语义图完整真实链路证据。若某类无法运行，父报告部分迁移及依赖，不能删图/换名宣布全量可用。交8.6复核。

## 验证命令与异常（尚未执行）

在已运行forem-dev内，`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests`，实际执行只选择本节点已交付的tests文件；父最终集成时再运行所需集合。通过标准不是只有exit0，还须满足[TASK](TASK.md)所列断言。宿主通过`sg docker -c`调用，日志保留实际argv/退出码；不在宿主装ROS。

全任务共享累计1800s验证预算，单smoke≤120s/64步、先batch1后2；语义图单图30s，均为SRC-0987工程上限。子任务不能重置预算；没有GPU份额时先完成不依赖GPU的部分。超时/依赖缺失写未验收，不删失败数据、不降条件、不静默CPU回退。失败定位后最小修复与必要复验，改变科学合同或扩大范围须先交父说明。

## 输出与交接

逐run写RESULTS：目标/授权、实际负责人/模型/强度、文件与源hash、命令/退出码、证据、通过/未通过门、资源账本、限制/风险、下一步；如有进程附PID/容器/日志/监控/停止方法。当前尚无运行任务。父复核后才标done；共享SOURCES条目由父落账，子Agent提交主张与精确证据位置。

正式逐图诊断入口为`forem/scripts/task8_map_diagnostics.py`，与本run已执行logs/run_maps.py原字节/hash相同，历史原件保留供证据复核；不增加功能，按AGENTS源码/入口归位。当前24图诊断不代表所有任务可达，完整限制见[SRC-0996](../../../SOURCES.md#src-0996)。
