# task9.11.7 · 流程

递归规则：本层恰有TASK/PROCEDURE/RESULTS；不再委派。父核原件汇总；.7稳定实现后.8独立复审，不把自报当PASS。

1. 先读输入、核活动编号/写边界/原SHA，登记实际模型未知。
2. 实施/审核watcher ready后resources期间死亡、失败terminal/耗时、owner退出；断言worker启动标记从未创建。先审纯stdlib收集与导入，不跑旧pytest/conftest。
3. 外层独立wait各生命周期成员并封完整证据/成本；阶段wall不能充closed成本。失败/缺失/盘错保留UNKNOWN且阻断，不填0；不得自证自身已退出。普通launch前二次检查不宣称覆盖任意竞争。
4. 保留历史30+7及全部失败原件，按变更选必要回归；独立读稳定代码/原输出和成本公式，另写反例复验，禁止改实现。
5. 准备新身份/原账继承/发布令/CLI，旧STOP不解除，不假迁移旧PASS；原58h/2TiB和deadline继承。交是否可放行结论，不签训练许可。

写边界：只写forem/scripts/task9_11/supervise.py、forem/src/task9_lr/admission.py、forem/src/task9_lr/tests/test_supervision_stdlib.py（必要时新增同目录专用stdlib测试），及自身三文档/日志；不改prepare.py（父负责）、worker/训练/环境/记录器/配置/旧证据/共享文档。

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需并发握手、外层wait证据与累计预算审查；本轮仅请求sol/high，实际后端/档位无法核实则记未知，不将推荐当实配。

## 实际实施与证据门

本轮实际直跑命令（cwd `/home/ybc/projects/CL-FoReM-task9`）：

```sh
python3 -B forem/doc/agent_logs/task9/task9.11/task9.11.7/run_stdlib_evidence.py attempt04
```

runner先保存39项AST收集及直接/传递源码SHA、导入清单，再以`python3 -B forem/src/task9_lr/tests/test_supervision_stdlib.py`启动unittest。不经pytest/conftest；模型/数组/环境库未导入。前三次attempt均保留，不将旧SHA的PASS挪给最终源码。[SRC-1404](../../../../SOURCES.md#src-1404)

启动顺序为watcher-ready identity/nonce核验→resources→身份/alive/owner/terminal/time重核→launch-request→watcher绑定request SHA与双方身份确认→紧邻Popen重核。此握手仅说明未在已观察无效时启动，不承诺OS在最后核验与exec之间不存在任意故障竞争。

实际独立wait顺序：guard `wait(watcher)`后持久化watcher-wait；owner `wait(guard)`后持久化guardian-wait；outer `wait(owner)`后核nonce、PID/startticks、waiter、rc、各ready/terminal/record关联及SHA。链区间从spec.started_monotonic到outer核验完成，阶段wall不得与它相加。outer最终发布/退出尾、预约前CLI预处理仍UNKNOWN；中间被杀缺wait证据也UNKNOWN，绝不由ready/进程已不存在反推退出码。v2 PASS阶段receipt不构成closed成本，admission明确拒绝后续；不暗改原验收合同。[SRC-1404](../../../../SOURCES.md#src-1404)

对旧协议的精确CLI未增加公开执行阶段。只增加内部`--_owner SPEC`，guard/watch仍内部入口；prepare保持NOT_READY。父提供的纯准备候选CLI由父文档定义，不是本节点发放执行许可。完整成本未闭合前不真实调用这些执行入口。

## 同轮续修（历史PASS通用封口）

父与.8独立旧格式反例FAIL后，保留.8原FAIL，在本.7追加attempt05。实际同一runner用参数`attempt05`先保存40项收集/SHA再直跑。admission公共PASS分支拒绝所有尚缺完整closure的记录（含缺format、v1、v2和未知格式），不定义新的获批CLOSED格式。外部命令去重与worker预算算术测试改用无activity fixture，不再靠无closure旧阶段wall充正测。旧attempt04源码快照及输出不改。[SRC-1404](../../../../SOURCES.md#src-1404)
