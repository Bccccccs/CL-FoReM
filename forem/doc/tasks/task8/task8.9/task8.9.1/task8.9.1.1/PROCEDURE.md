# task8.9.1.1 — 执行流程

状态：**done（O1–O4独立PASS，仅优化交付）**。目标/验收见[TASK](TASK.md)。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；不再拆分。若需拆分，继承`task8.9.1.1.N`并先建三文档、登记顺序/依赖/负责人/模型强度/验收；编号稳定不复用。

## 步骤

1. 读父三文档、r2 profile与就绪报告、SRC-1190；记录scene.py当前hash；建账本`forem/logs/task8/t8-perf-opt-20261027/budget.json`（≤1500s）。
2. 先写等价测试（新实现缺失时RED），再实现批量森林遍历，保留旧路径作参照开关。
3. 跑O1/O2；独立Sol审查diff与原输出。
4. terra/Luna按固定清单重测batch 64/256吞吐（O3）；Sol复核。
5. 结果写RESULTS；父汇总到task8.9.1与task8.9。

## 异常

无法做到逐元素相等时停止并报告差异与原因，不以容差替代；不改语义。

## 本轮具体执行与保留证据

实施 Codex /root/opt_r3，父显式gpt-6.1-sol/high；推荐GPT6.1sol与Claude Sonnet5.5均high，因为GPU批量遍历与严格状态等价需跨层核查。固定O3由父安排Terra low，不同Sol high独立验收；本实施者不再派Agent。

- 原始scene.py/hash保存在 `forem/results/task8/t8-perf-opt-20261027/scene-before.py`；最终diff为同目录scene.diff。
- 所有测试用原 `profile_budget.py` 串行写新1500s账本；完整命令、外层wall、退出码与stdout在 `forem/logs/task8/t8-perf-opt-20261027/`。不重置旧账本，不重复prepare。
- O1入口 `forem/scripts/task8_forest_accept.py --device <cpu|cuda:0> --output <new-json>`，CPU64/GPU32各自对旧loop；地图读取原32立方体+24语义，附empty/边角fixture，b1/16/64/256逐元素相等；四批Depth完整32400像素全字段；每设备50 Core.step、每step全部Transition字段相等。任一不等即退出，不使用容差。
- O2完整 `forem/src/task8_sim/tests`；CPU显式空CUDA可见，GPU设置TASK84_DEVICE=cuda:0与TASK8_TEST_CUDA=1；两者都用prohibit_training运行时guard。GPU的TASK8_TEST_ARTIFACT_ROOT设为本r3新目录，避免覆盖历史测试JSON。
- 森林缓存仅为派生数据，序列化时剔除并在恢复后惰性重建；select继承loop/forest开关，replace失效缓存。碰撞未优化。
- 固定profile清单：`forem/results/task8/t8-perf-opt-20261027/r3-fixed-profile-jobs.json`，四组cube/semantic b64/256，各warmup2+20完整测量step；GPU0逐命令初检空闲，保留账本>=150s独立复核/P5储备。尚未执行，禁止自行重复旧R2命令。

来源由父登记 [SRC-1191](../../../../../SOURCES.md#src-1191)、[SRC-1192](../../../../../SOURCES.md#src-1192)；O3执行SRC1193、汇总SRC1194待补。

## 固定执行与原件汇总完成

Terra已按四job清单各执行warmup2+20完整测量step，全部rc0/guard0，未重复prepare。Sol汇总入口 `task8_profile_summarize_r3.py`只用标准库读原件，逐分项raw统计、transfer/wall/sim、CSV、frozen hash与R2公共前缀元数据核验，输出summary-r3.json/md。首次argv分隔符索引错误的汇总rc1保留，修正报告脚本后rc0；无物理/等价失败，无新测试/profile/训练。[SRC-1194](../../../../../SOURCES.md#src-1194)

不同Sol high已在r3-independent-opt-final.json判O3固定负载PASS/O4 PASS；本节点结束，剩余P5属父8.9.1，在C smoke后followup。不新增训练或其他优化；后续全部额外成本继续原1500s账本。
