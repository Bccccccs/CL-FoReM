# task10.9 结果

状态review；本节点CPU交付完成，父真实batch8采集及统一验收不在本节点结果中。[证据SRC-T10-018](../../../SOURCES.md#src-t10-018)。负责人Codex；实际派发GPT6.1sol/high（平台内部不可独立核验）。推荐GPT6.1sol/high、Sonnet5.5/high，因边界/RNG/账本跨模块因果核验需要。执行者可在父范围/总预算/截止内自主选模/强度、独立完成或先建档再委派；本节点未另派Agent。

## 修改与安全结论

初始HEAD ca57b4b，工作树codex/task10-upper-wm。独占改动recovery.py、test_recovery.py和新增test_runner_boundary.py；父修改runner/入口，未交叉写入。没有真实采集、GPU更新、启动训练、修改旧账本或提交。

原save只核对journal身份集合，可接受同ID但terminated/truncated/selected/reward/dt/bootstrap_mask不同，亦未拒绝replay终局类型与live core不同。先新增7个测试，实际7 failed/rc1，再最小实现：读取journal前显式fsync；拒重复身份；最后transition六字段与replay逐位一致，终局类型与live core一致。其余全batch自然终局/pending/inflight/计数/旧owner存活/同PID/锁后digest/host boot/原截止等限制保留。已有load未发现需修改的实证缺陷；其factory要求新环境未reset，恢复采样器后仅采样下一回合，不序列化物理Core。

## 实际CPU证据

2026-11-02，forem-task10-runtime，user1004:1004，PYTHONPATH=/workspace/src；宿主无torch，未在宿主安装。run-id归父t10-gpu-batch8-20261102。

- 安全RED：`forem/logs/task10/task10.9-safety-red.log`，7 failed/3.48s/rc1。首次写夹具曾括号语法错误，修正后才记录上述预期失败；未把收集错误当RED。
- 原runner RED：git show ca57b4b:forem/src/task10/runner.py写入logs下临时模块（未覆盖共享runner），仅将真实Budget容量限制24、更新0，沿旧train运行。旧入口正常budget_stop后缺collector-boundary.pt，1 failed/2.60s/rc1；`task10.9-old-runner-red.log`。早次未限容量触发synthetic字段缺失，随后修正夹具注入；本结论使用后一次明确缺文件的失败。
- 初组合GREEN：24 passed/12.19s/rc0，`task10.9-green.log`；连续参照新夹具单跑3 passed/9.74s/rc0，`task10.9-reference.log`。
- 最终组合：**25 passed/17.98s/rc0**，`forem/logs/task10/task10.9-final.log`、JUnit `task10.9-final.xml`。命令如下。

```bash
sg docker -c 'docker exec --user 1004:1004 -e PYTHONPATH=/workspace/src forem-task10-runtime python3 -m pytest -q -p no:cacheprovider --basetemp=/workspace/results/task10/t10-gpu-batch8-20261102/cpu-boundary-fixture --junitxml=/workspace/logs/task10/task10.9-final.xml /workspace/src/task10/tests/test_recovery.py /workspace/src/task10/tests/test_runner_boundary.py'
```

原件根：`forem/results/task10/t10-gpu-batch8-20261102/cpu-boundary-fixture/`。三个runner夹具：第1批4结束即reset4，第2批8行自然结束时保存，共16条；新PID恢复下一批后24条/24唯一(environment,episode,decision)身份，旧journal SHA不变；原started/deadline逐位相同。连续参照shadow8条与恢复8条在父runner自身比较器为verified，包含scene/观测/候选/选择、全局/策略/采样RNG、journal、回放和账本计数；旧/新PID不同。完整物理环境、GPU及B3推理均为显式synthetic CPU替身，因此这些是接线和恢复协议证据，不能代表真实batch8边界可达。

## 交接

父可从上述原件复核并复跑，再按统一GPU/1800s总截止与64真实选择/0更新上限开展真实阶段。本节点不自行启动；真实若无法到达全批自然终局，保持未验证。父需统一登记SRC-T10-018及最终源码hash/实际运行和全局账本；源代码已通知冻结。剩余风险是实际batch8终局同步可达性及真实恢复逐位性，不能由CPU夹具推断。未解决的GPU下一更新差异由task10.8/父处理。


## 父核验与最终交接

2026-11-02，Codex：父最终接线/安全修复afc56f6真实运行7批56/0，各批结束4/4/2/5/7/6/5，无全8安全边界，真实采集恢复未验。独立审核后ede1299改为字节判等、落盘恢复端完整树、GPU合同/截止验收补强；最终CPU163passed/3条件skipped，cpu-final双端原件字节复算exact，不能外推真实。 [父结果](../RESULTS.md) · [来源](../../../SOURCES.md#src-t10-018)。推荐GPT6.1sol/high、Sonnet5.5/high，因跨模块数值/状态边界核验；当前无本节点运行任务，状态review。
