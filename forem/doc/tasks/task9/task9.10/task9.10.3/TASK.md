# task9.10.3 清单与预算账本核对 TASK

**状态：review（只读核对与清单交付完成，待父级独立复核）。** 负责人：Codex；实际模型/推理强度未知。该子任务只核验 task9.9 的12个受阻案例、task9.8冻结30例身份、源trace及现有B3运行成本/父级窗口账本；不加载模型、不启动环境、不改脚本、不作因果解释。

## 范围与交付

- 逐项将 `blocked-cases-12.csv` 按 `(training_seed,map_id,episode_seed)` 唯一映射到冻结30例的 `seed`，并保留对应完整冻结键、来源评测文件和源trace SHA256。
- 核对每seed数量、输入CSV哈希、B3既有A副本与canonical冻结CSV一致性；追加核验B3两个既有依赖台账登记的文件哈希。
- 复算 B3 `worker_wall_sum_s × 6/5` 规划量，并核 execution-window 的上海时间、epoch差、回合/GPU秒/墙钟/输出上限。
- 交付逐例机器可读清单与依赖文件哈希账本：[case inventory JSON](../../../agent_logs/task9/task9.10/task9.10.3/20261103-case-inventory.json)，账本与检查限制记于 [RESULTS](RESULTS.md)。没有新增独立来源主张；数字均由项目原始账本推算或复算。

## 验收

12行均唯一映射，源trace可读且有SHA256；每seed计数合计12；输入与B3既有manifest范围说明清楚；公式、单位和预算窗口复算无误。父级复核后方可将子任务标为done。

## 模型推荐

Codex GPT6.1sol/medium：键映射及账本算术需交叉核对，但不涉及复杂因果分析；Claude Sonnet5.5/medium：同样适用于独立重复核对。实际运行模型与强度未知。
