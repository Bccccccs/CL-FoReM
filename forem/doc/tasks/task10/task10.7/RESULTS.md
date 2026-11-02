# task10.7 结果

尚未执行。

推荐GPT6.1sol/high、Sonnet5.5/high，因测量口径、恢复时钟与无重复计数跨模块；实际派发gpt-6.1-terra/high（独立复核，与上轮sol容量替代一致）。

## 2026-11-02 初审（review，尚未最终验收）

首性能测量失败，实际8次重放、probe 76.355598秒，账本worker 77.750550秒；`old.batch0.observation`键不一致，不能作为同输入通过或有效性能比较。证据 `forem/results/task10/t10-cost-recovery-20261102/{cost-probe,measurement-ledger}.json`；父正在同一900秒截止/32决策总额度内修正并继续，结果待核验。

`load_episode_boundary` 账本摘要校验在获取恢复锁之前，另一恢复进程可能先校验、后等待锁，原持锁者提交并释放后再用旧快照恢复；此外同PID被允许，不能证明原collector退出。已通知父和实现者，修复后须检查锁内重验、异常释放及跨进程证据。`cost_probe` 的 `_boundary` 记录包括最终reset，但逐项同输入比较只涵盖已执行step的输入和结果，最终reset结果未逐项对照；两遍采样路径不同，时间差不能直接当纯仪表开销。CUDA stream interval可能包括CPU提交间隔，嵌套项及wall不能相加。新证据和实际限制待复核；成本预算只作建议，下一试训需决策者核定。

复核修订：恢复代码现在获取锁后验证账本及日志摘要、原boot和截止，异常关闭锁，默认拒绝同PID；静态上解决上述问题。CPU组合日志 `forem/logs/task10/task10.6-cpu-recovery-crossprocess2.log` 显示34 passed/8.60s；真实在线证据仍待测。manager当前实现延续原started_epoch/cap和attempt历史，最终须以运行账本核验。

### 性能续测终止（16:35 +08）

原phase截止下续测监督器rc124；两attempt worker合计458.295136秒，phase从原epoch起898.314078秒。新文件最后持久快照仍active、reserved24/completed16：两批baseline已逐项对照旧journal，仪表批已预留8但未落盘完成，保守按首失败8加续测最多24共32记预算，不假定其未执行。无法验证完整instrumented对照、分项GPU或最终reset全计数；不能将两批baseline或未完整输出当性能验收通过。修订代码已增加对应边界快照对照，包括仪表批最终reset，未运行完成故尚无通过证据。原phase绝对截止已耗尽，不得续开窗口。证据同目录 `measurement-ledger.json`、`cost-probe-repaired.json`。

补充核验 `reset-profile.json`：verification ledger rc0、worker 50.110秒；仅初始8场景、零真实决策/更新，初始观测及候选与旧首journal canonical逐项相等（排除搜索墙钟），记录68有效槽、13251尝试/13031提交，reset服务墙钟46.268秒。其为单次有仪表初始边界，不能外推为全部后续边界或证明仪表开销；CUDA流区间非纯kernel时间。

GPU恢复fixture首次attempt rc1（worker 7.944秒）：`verify_learner_checkpoint` 抛 `AssertionError: restored next update differs`，无summary；详见 `forem/logs/task10/t10-cost-recovery-20261102-recovery-fixture.log`。不能宣称GPU更新后下一步一致，原因尚待定位；首真实回放抽样的返回证据未独立落盘，不能按调用顺序当最终验收结果。仍受原300秒截止与全部attempt合计最多8更新约束。

后续GPU诊断 `recovery-diagnosis/diagnosis.json` 在同一已更新fixture上两分支：初始状态、sample身份、RNG及loss逐位一致，state 11叶有逐位差异（例权重最大绝对差3.7253e-9）；未开启确定性算法。仅证实严格相等失败及差异大小，不能据此证明原因或默认容差通过。诊断2次更新，加首attempt三次共5，仍在8上限内。不同GPU条件下训练与恢复可复现性仍须核定。

## 在线恢复与真实回放复核（review）

`collector-boundary/online-summary.json`：save PID 223、resume PID 231，两个子进程rc0；保存自然终局后重建，与直续下一场景、观测、候选、RNG、policy generator与选中槽逐项相等；恢复后提交一次并拒绝旧快照。只读加载checkpoint确认原monotonic截止减起点360秒；最终账本reserved=completed=2、inflight=0，耗时142.115秒、0更新。只读加载两个journal，身份分别为 `(collector-boundary,0,1,0)` 与 `(collector-boundary,0,2,0)`，未重复。锁内摘要/截止检查和旧PID检查见当前recovery源码与CPU日志；本次为batch1自然终局，不能推及活动中途或batch8同时终局。

`collector-boundary/real-replay-evidence.json` 独立记录旧真实回放16个非空anchor及RNG/身份一致，0更新；optimizer/next-update明确not_verified。GPU fixture首次严格比较失败，后续诊断虽rc0但JSON状态exact_mismatch，manager done仅表示诊断过程完成，不是恢复验收通过。

## 结论与交接

本节点只读审查与计数复算完成；独立证据支持首reset性能细分、限定batch1自然边界恢复和16条非空样本身份，但完整profile/仪表对照与默认GPU严格下一更新一致仍未通过。性能两批baseline的5个边界合计196有效槽、1037批/40948行B3、41893尝试/41166提交；仪表批超时不能计入完整测量。正式预算与下一1000预热试训须决策者核定，本节点不建议将局部测量外推为可兑现工期。原始证据路径 `forem/results/task10/t10-cost-recovery-20261102/`，日志 `forem/logs/task10/`；未运行额外采集/更新。后续如有依据主张登记由父统一维护SOURCES。

父统一登记依据：[SRC-T10-014](../../../SOURCES.md#src-t10-014)。父核验/预算交接见[父RESULTS](../RESULTS.md)，未将本节点自报或诊断rc0当总验收通过。当前review，原始未通过/限制保留。
