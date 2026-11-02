# task9.6 RESULTS

状态**done**（2026-11-02 14:14父核验；三模型/288回合复评完成，非独立Agent验收）。[SRC-1355](../../../SOURCES.md#src-1355)。下方启动记录保留为历史。

目标/授权、输入与验收见[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)及[SRC-1354](../../../SOURCES.md#src-1354)。负责人Codex。

## 模型推荐
Codex GPT6.1sol / medium；Claude Sonnet5.5 / medium。固定协议评估，需核对加载、种子和输出隔离；实际本Agent模型/强度未知。

## 启动记录 2026-11-02T11:35:49.192061+08:00

- 已启动：2026-11-02T11:35:19.529372+08:00；宿主supervisor PID 3548635，seed4718首worker宿主PID3548679；三seed串行GPU0，forem-dev。版本沿现工作区dirty，不commit/push。
- 脚本：`forem/scripts/task9_semantic_eval.py`、`forem/scripts/task9_semantic_queue.py`；来源与hash `forem/logs/task9/t9-semantic-20261102/provenance.json`。AST核原evaluate除函数名与transfer-only角色循环之外完全一致，原有helper直接import，路径/seed身份核验保留，`derivation-check.json`。CPU --help实际rc0、两脚本AST通过；这些不是GPU评估通过。
- 日志：`forem/logs/task9/t9-semantic-20261102/queue-state.json`、`queue.log`、`seed4718.log`等；输出：`forem/results/task9/t9-semantic-20261102/seed<seed>/`，最终`summary.json`和`report.md`自动生成。初次现场docker top已核真实worker，加载/实际CUDA尚待loaded.json，不提前声称完成。
- 监控：读取queue-state与seed日志；每seed完成写evaluation/status，全部结束后状态completed_pending_review。失败不自动重试，余下不启动。
- 停止：先核PID/cmdline，通过docker exec向当前worker发送TERM（非旧训练进程）；该worker退出非0，supervisor停止后继。无需重启容器，不删除模型/旧结果。评估不保存训练状态；未完成会保留状态/异常证据。
- 当前剩余：真实模型加载/CUDA核查、三96回合及分类汇总、逐case与旧结果比对；不把启动当完成。

## 最终结果与父核验（2026-11-02）

依据[SRC-1355](../../../SOURCES.md#src-1355)，[原始汇总](../../../../results/task9/t9-semantic-20261102/summary.json)、[类别报告](../../../../results/task9/t9-semantic-20261102/report.md)、[父审计](../../../../logs/task9/t9-semantic-20261102/completion-audit.json)。

|训练seed|成功/96|成功率|逐case成败匹配原结果|
|---|---:|---:|---:|
|4718|49|51.04%|96/96|
|4719|39|40.625%|96/96|
|4720|44|45.83%|96/96|

合计132/288=45.83%。11:35:19–12:06:31串行约31分12秒；三阶段rc0、无重试/超时，各模型loaded核CUDA及actor tensor一致，父逐case复核固定身份/24×4/分类/总数及脚本hash通过。14:13现场容器仅保活、GPU compute空。

类别见报告：本固定样本workshop24/36、library22/36较高，home8/36、restaurant10/36较低；不作类别普适难度结论。非成功156例中147终态failures=20，9终态failures=0，未据此断言唯一根因。

本次交付/必要核验完成，剩余无；未训练、不冻结下层、不推进task7。task9.4全批独立验收仍另待。复评原有固定96episode，不作为新独立测试。实际CPU mmap读取全检查点元数据/对象，只将policy/critic恢复到GPU，未将replay/optimizer恢复成训练状态；不声称CPU完全不反序列化回放。
