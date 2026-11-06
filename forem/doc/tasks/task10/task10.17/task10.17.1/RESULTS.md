# task10.17.1 结果

2026-11-03T23:02:01.023793+08:00 · Codex · **review，CPU实现/夹具通过，待父A真实恢复核验**。实际模型与推理强度平台未提供可核实名称，记未知；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，涉及完整恢复、预算和跨进程身份。执行者可自主选模与先建档委派，本子独立完成，无下级派发。父统一GPU、阶段总预算、启动与最终原件验收。[来源](../../../../SOURCES.md#src-t10-043)

## 已实现

- 新`boundary_state.py`使用封闭类白名单，将Core动态字段、State/Candidate/PackedRoute/Grid、场景几何/传感累积/动作队列/时钟/缓存/历史trace、sampler planner/streams、观测与候选编码为纯CPU数据树；没有pickle活Core/环境或CUDA graph。fresh constructor提供kin/robot，显式重建SceneCollision/PcdPanorama引用；不调用reset/抽样/候选推演来恢复。PrimitiveScene的纯查询bank缓存重建，其科学输入张量按字节保存。
- `recovery.py`追加`save_decision_boundary` / `load_decision_boundary`；format=`task10-decision-boundary-v1`，保留原自然终局API与拒绝规则。保存必须正常prepare_next、自然ended行reset完成、core.done全真、无pending/inflight/terminal placeholder。已存路径拒覆盖。完整journal与replay身份数等于completed账本、逐字段相等，当前行episode/decision及history逐内容对应replay。
- learner/target/Adam/scheduler/temperature/replay与采样RNG、全局所有RNG、policy generator、model/target的VCM运行记忆与梯度、训练模式均保存。load必须新PID、旧PID退出、同boot/source/runtime/determinism/config，原ledger与journal哈希不变；独占锁后重核证据，恢复后立即落盘新PID ownership，沿原started/deadline，拒绝旧检查点回滚。

## CPU验证

初轮新专项18passed/18.67s；新+旧恢复与字节exact专项44passed/24.20s。最后补充不可变文件及history内容校验后，**45passed/25.38s/rc0**，原件`forem/logs/task10/task10.17.1/cpu-tests-v2.txt`；原`cpu-tests.txt`保留。`py_compile`与`git diff --check`均rc0。实际命令：

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime python3 -m pytest -q --basetemp=/tmp/t10-17-1-final-v2 /workspace/src/task10/tests/test_decision_recovery.py /workspace/src/task10/tests/test_recovery.py /workspace/src/task10/tests/test_collector_exact.py'
```

batch8结构夹具由手工合成状态组成：4新episode（决策0）、4存活episode（决策8），64条明确标注synthetic replay/journal，已更新Adam。验证原场景/obs/candidate/grid/queue/cache/history/VCM完整状态、下一采样身份、policy随机选点、streams下一抽样、下一更新所有learner叶及RNG精确一致。独立子进程保存并退出，再由不同PID加载，原deadline/started保持逐值相等。另拒绝未提交pending/inflight、ended/placeholder未reset、history长度/内容、缺journal/replay、源版本/runtime/config/schema/journal/ledger变化、同PID/第二owner与再次旧snapshot加载。

**限制**：这些是合成CPU结构夹具，不是128条真实核查的一部分，不是环境实测成功或GPU逐位恢复证据；本子没有真实交互/GPU训练、没有启动B/C。真实正常批混合行采集与恢复、下一批真实场景/观测/候选/选点、GPU更新和性能仍由父A统一验证。Core.reset源码中reset行done=True，存活行上一段自然done，因此正确正常边界允许done.all而不要求episode全结束。

## 交接

API参数与父约定相同；返回environment/policy_generator/budget/counters/histories。payload保留ledger_path/ledger/counters/started_monotonic/deadline_monotonic与learner/replay；导出`capture_environment(env)`用于父精确比较全部状态。该导出含测量墙钟字段；恢复起点应全精确，执行后端点需仅剔除测量字段。新checkpoint由父不可变文件+原子索引发布。无本子遗留进程；不提交、不推送。

源码SHA256（本子完成快照；父后续总冻结为实际GPU依据）：
- `forem/src/task10/boundary_state.py`：`6f3eb36911ca7ee048844fd19428beabc04d5696ff81cb091d926cf775ca6f33`
- `forem/src/task10/recovery.py`：`169ff4658518cd9f19719c8ab2f82eb0838d8f5d2e718ea21ece768e0224e770`
- `forem/src/task10/tests/test_decision_recovery.py`：`20daf953f618b6ac91a768a8ef96ca04bf42b6936a9969a758ab3d0c99a2d24b`

2026-11-03T23:30:28.721796+08:00 父真实A复核：正常混合6新/2存活64点、PID1678→1741，下一批/采样/梯度/更新/账本逐位一致，80共享真实/12诊断更新；本子恢复实现已核验。父A总体成本门NOT_READY，B未启动，不将本子恢复通过当48h通过。[SRC-T10-043](../../../../SOURCES.md#src-t10-043)。
