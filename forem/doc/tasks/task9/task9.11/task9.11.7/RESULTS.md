# task9.11.7 · 结果

状态done（本轮修复与独立准备审核完成；真实执行NOT_READY）。负责人Codex，请求GPT6.1sol/high，实际模型/强度未知。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，原因是启动竞争、wait链及不重不漏成本映射。用户授权与约束见[SRC-1403](../../../../SOURCES.md#src-1403)；本节点实现与合成依据见[SRC-1404](../../../../SOURCES.md#src-1404)。不将推荐当实配。

## 改动与实际验证

只改生产supervise.py、admission.py与专用stdlib测试；不改prepare/worker/训练/环境/记录器/科学配置/旧STOP及原件。watcher资源检查后退出时，guard通过ready身份、双向request/ack及实际launch前核验拒绝启动；四个资源回调分别注入watcher SIGKILL、已发布FAIL terminal、耗尽时间、owner SIGKILL，全部同时断言回调已触发、worker-started与worker自身worker-launched标记从未创建。保留正常子先、父SIGTERM/SIGKILL、guard SIGKILL、双guard死亡、残留子进程、串行锁、写盘失败、资源/预算等回归。握手不声称消除最后核验后的任意OS竞争。

|尝试|结果与wall|说明|
|---|---|---|
|[attempt01](../../../../agent_logs/task9/task9.11/task9.11.7/attempt01-command.json)|36项PASS，rc0，11.4996738806s|首次新增四个启动反例与正常/父死wait链|
|[attempt02](../../../../agent_logs/task9/task9.11/task9.11.7/attempt02-command.json)|38项，rc1，12.4241726082s|测试先wait回收owner后再让outer读身份，tamper测试FileNotFound；原失败保留。publication当时过宽OSError断言也同步收紧|
|[attempt03](../../../../agent_logs/task9/task9.11/task9.11.7/attempt03-command.json)|38项PASS，rc0，12.3545549866s|不预先reap owner；publication要求精确注入原因及mock实际调用|
|[attempt04](../../../../agent_logs/task9/task9.11/task9.11.7/attempt04-command.json)|39项PASS，rc0，12.9307403676s|按独立审查静态反馈进一步绑定terminal activity/publisher与record身份，并新增publisher篡改反例|

每次cwd `/home/ybc/projects/CL-FoReM-task9`；直跑`python3 -B forem/src/task9_lr/tests/test_supervision_stdlib.py`。原stdout/stderr、精确命令/rc/wall/SHA及先保存的AST收集均在[自身证据目录](../../../../agent_logs/task9/task9.11/task9.11.7/)；最终[collection](../../../../agent_logs/task9/task9.11/task9.11.7/attempt04-collection.json)、[原stderr](../../../../agent_logs/task9/task9.11/task9.11.7/attempt04.stderr.txt)。只用stdlib和临时替身进程，DockerBackend方法只有mock；真实Docker控制、模型/环境/回放/smoke/训练/最终test均未执行。旧.5/.6原件未覆盖。

上一版attempt04源码SHA（历史，仅对应39项）：

- supervise.py `40df05d8e5ed0236460d45d0bd5db3a1bb1314ef7c749c75ab8409e12c9812c2`
- admission.py `f8a81dd74ad0b4aa9a167dcb90b0b402d85253ff93ad5047a3665210c1ea1101`
- test_supervision_stdlib.py `83bad64d7c224a7b8c36a5fdb3d0598c0b3153b0783f5e484e6d94ed1da86b42`

上一版三源码snapshot为`attempt04-*.py`；[supervise最小diff](../../../../agent_logs/task9/task9.11/task9.11.7/supervise.py.diff)、[admission最小diff](../../../../agent_logs/task9/task9.11/task9.11.7/admission.py.diff)。为精确比对，由.5不可变before＋最终diff在本节点重建baseline，SHA核得原71a2/0507，旧原件未改。whole artifact待父prepare收尾统一封存，不把局部SHA当全artifact签字。

## 生命周期与成本映射

|证据/变量|实际含义|能否closed计费|
|---|---|---|
|worker-result / exit_code|docker-exec客户端actual wait结果；容器worker由quiet/stop单独见证|不能代替owner/完整链|
|watcher-wait|guard实际wait watcher后发布，绑定nonce/identity/waiter/rc|只是其中一跳|
|guardian-wait|owner实际wait guard后发布，同样绑定|只是其中一跳|
|lifecycle.owner|outer实际wait专用owner的独立rc/identity|有真实外层wait，非进程自证自身退出|
|lifecycle.chain_status|核全部wait链、ready绑定、terminal activity/publisher、record身份与各SHA；成员不得仍alive|正常合成PASS；缺证/篡改/owner死为UNKNOWN|
|stage_terminal_wall_s|预约启动至watcher发布前的阶段下界|不能充closed|
|observed_chain_wall_s|spec.started_monotonic至outer完成wait链核验的单个包围区间，单位秒；不与嵌套stagewall相加|下界，仍非完整CLI成本|
|closed_wall_s / outer_exit_code / outer_publication_exit_tail_s|outer无法独立见证自身最终发布/退出，预约前CLI预处理亦未闭合|UNKNOWN；不造0，不放行|

outer在owner退出后才持久化独立lifecycle.json；这是真实额外wait与证据链实现，不是把原stage字段换名。中间SIGKILL丢失receipt时，即使观察对应identity不再alive，也不编造wait rc；盘错不能产生完整收据。outer自身尾及预约前预处理仍无独立闭账证明，因此admission对v2阶段PASS明确拒绝closed计费/跳过/跨阶段进入。原“同版本阶段PASS可跳过”的测试已改成必须拒绝，不维持已知错误的合同断言。当前不授予新的closed格式，不把UNKNOWN改成保守0，不改变原预算/截止或验收。[SRC-1404](../../../../SOURCES.md#src-1404)

## 交接

已向.8提交上述稳定SHA和原输出；其独立审核未由本节点代签。父负责共享PROGRESS/SOURCES/预算/续接候选，候选仍非执行许可。旧STOP、4000 smoke/980评估、正式0/test0及历史未知费用均保持；全闭账成本、真实Docker尾与续接科学证据接受仍未解决，[SRC-1405](../../../../SOURCES.md#src-1405)。本节点无继续运行的替身任务；下一步只接独立审查与父汇总，不启动真实执行。

## 同轮续修：全部缺closure的PASS统一拒绝

父与.8随后独立发现上一版f8a8只封v2，缺format与legacy v1 PASS/exit0/wall3仍被当closed消费。独立原[FAIL命令](../../../../agent_logs/task9/task9.11/task9.11.8/independent-legacy-cost-attempt01-command.json)及[原stderr](../../../../agent_logs/task9/task9.11/task9.11.8/independent-legacy-cost-attempt01.stderr.txt)保留：1测试、2subFAIL。该发现推翻上一版“通用封口已完成”的理解，不影响旧启动反例或实际wait链结果。[SRC-1404](../../../../SOURCES.md#src-1404)

本次只把admission的完整成本UNKNOWN拒绝从v2局部分支移到所有PASS公共分支；未增加任何合格CLOSED验收格式。所有缺完整closure的PASS均拒绝activity_rows/check_resources/dispatch，不launch。新增1测试覆盖缺format/v1/未获批format三种身份；其余资源算术测试用空activity集合，external实际命令去重单列7s，新worker cap用101>原测试上限100，不再让旧stagewall为资源算术提供完整成本正测。历史lower统计helper不受影响。

先保存[attempt05 collection](../../../../agent_logs/task9/task9.11/task9.11.7/attempt05-collection.json)，再直跑同一unittest脚本；[精确命令](../../../../agent_logs/task9/task9.11/task9.11.7/attempt05-command.json)，40项PASS/rc0/wall12.9649648461s，[原stderr](../../../../agent_logs/task9/task9.11/task9.11.7/attempt05.stderr.txt)。cwd仍为`/home/ybc/projects/CL-FoReM-task9`；未导入模型/环境，无真实Docker控制。旧attempt01–04及所有失败完全保留。

最终稳定SHA（替代上方attempt04作为当前交付）：

- supervise.py `40df05d8e5ed0236460d45d0bd5db3a1bb1314ef7c749c75ab8409e12c9812c2`（未改）
- admission.py `84594d21d63412567b45df51ce6362a606b433a2e86fe5e3dd7f00e1bb4e792e`
- test_supervision_stdlib.py `59d9fd322802f98eaa4830e5bd0da6c3876076f42c2f2b4a6c246756161f9f54`

对应完整源码快照`attempt05-*.py`已保存，最小diff同步；.8已接收此稳定SHA独立复验。当前outer自身尾、预约前处理/历史未知成本继续UNKNOWN；旧STOP/科学/预算/截止均未改，真实执行NOT_READY。whole artifact由父在prepare与本修复均稳定后封存，不用局部SHA代签。

续修独立结果：已只读核.8[最终40项命令/SHA](../../../../agent_logs/task9/task9.11/task9.11.8/final-cost-suite-independent-command.json)及原stderr，rc0/wall13.0745058041s；其同一旧格式反例[attempt02](../../../../agent_logs/task9/task9.11/task9.11.8/independent-legacy-cost-attempt02-command.json)为1test/2sub PASS、rc0/wall0.0543614272s，旧attempt01 FAIL保留。独立正式裁决仍由.8与父汇总，不由本节点代签；这些结果支持通用封口修复，不改变完整成本UNKNOWN/真实NOT_READY。

父接受补注 2026-11-03T22:05:09.937568+08:00：已从.8正式裁决及原输出/rc/SHA核本轮修复与独立复验，接受准备交付，子状态done仅指本轮授权范围完成；原完整合同/成本UNKNOWN与真实NOT_READY、旧STOP不变。最终[父完整性原件](../../../../agent_logs/task9/task9.11/lifecycle-final-verification-v2.stdout.json)支持740保护与源/证据一致，不是训练许可。[SRC-1404](../../../../SOURCES.md#src-1404)。
