# task10 结果与交接

2026-11-02，Codex 已登记[目标](TASK.md)与[流程](PROCEDURE.md)。本次交付仅为计划，接口适配、实现、训练与评估尚未执行。

接手时在 /home/ybc/projects/CL-FoReM 读取 codex/task10-upper-wm 分支，仅细化上层 SAC 协议。原始产物在同一仓库的 forem/results、forem/logs。

[用户决定及接口依据](../../SOURCES.md#src-1360)。推荐 GPT6.1sol / medium、Sonnet5.5 / medium，用于跨模块接口核对。

## 2026-11-02 · 设计 v1 交接

Codex 已根据用户委托选定单个冻结 B3、普通上层 stage 1、按尝试时钟折扣的严格成功奖励及进度塑形，并写出 A–D 接口、训练、试训和评估合同。[协议](PROCEDURE.md) · [源码与工程选择](../../SOURCES.md#src-t10-001)。设计交付完成。实现、B3 动作一致性、场景配对、吞吐、学习曲线和成功率均尚未执行。既有下层成功率不能作为本任务结果。

执行入口为本地 codex/task10-upper-wm 分支，工作树 /home/ybc/projects/CL-FoReM-task10，原始 B3 文件在 /home/ybc/projects/CL-FoReM/forem/results。先读根 AGENTS.md 及本层三文档，按 A→B→C 交付有界证据。风险是旧环境沿用 legacy、短回合被序列采样漏掉，以及推演不慎读取执行真值。逐项核验后将 run-id、源码版本、输入哈希、命令、退出码、实际决策/更新数、最慢阶段、缺失及成本估算追加到这里。D 依赖单独预算授权。推荐 GPT6.1sol/high、Sonnet5.5/high，理由为跨层执行与回放一致性核查。

派发更新：执行负责人可自行选模型与推理强度并派发子 Agent，具体分工由接手者登记。见[父流程](PROCEDURE.md)及[授权](../../SOURCES.md#src-t10-002)。


## 2026-11-02 · A→B→C 执行（active）

负责人 Codex；工作树 `/home/ybc/projects/CL-FoReM-task10`，分支 `codex/task10-upper-wm`，起始HEAD为7b705c1且祖先检查rc0；父实际模型/强度未知。推荐GPT6.1sol/high、Sonnet5.5/high，原因是跨层时钟、终局折扣与回放边界集成。当前用户授权单次1200真实决策/200更新/1800s及4场景配对另1800s，全部Agent共用；正式长训/task11未授权。[SRC-T10-006](../../SOURCES.md#src-t10-006)。

三子模块通过父复跑：冻结B3 69源码/9推理依赖hash及同设备CPU/CUDA原版对照误差0（14测试）；学习器支持零dt、终局独立mask及短回合首步；环境局部预测与真实执行分离、attempt clock/首次失败、只selected真实标签。父组合117passed/2既有条件skipped（21.02s/rc0），最后增加pending候选禁止入回放及atomic_json目录fsync后，定向35passed/7.57s/rc0；py_compile及git diff --check rc0。证据和限制分别见[SRC-T10-003](../../SOURCES.md#src-t10-003)、[004](../../SOURCES.md#src-t10-004)、[005](../../SOURCES.md#src-t10-005)、[007](../../SOURCES.md#src-t10-007)。

独立task10.4发现并已修复两P1：真实执行完整原子journal先于账本complete；容器内timeout1798s TERM/1800s KILL，短有界监督夹具实际-9/0.203s。磁盘写失败保留in_flight、不重试；混合批reset保留survivor状态/观测/候选逐位一致。环境不支持中途恢复；offline-learner仅验证学习器RNG/下一回放/更新计数，不能作为在线collector恢复。[独立审查](task10.4/RESULTS.md)。

运行版本将在启动前本地提交；run-id `t10-smoke-20261102-s101`；新产物位于本工作树`forem/results/task10/t10-smoke-20261102-s101`与`forem/logs/task10/`。独立容器`forem-task10-runtime`，GPU1，主仓forem及results只读，工作树forem挂/workspace；2 CPU线程，8真实env，局部推演仅有效槽；配置`forem/config/task10/smoke.json`。先检查GPU空闲后启动；目前试训/配对尚未执行，所有真实计数为0。
