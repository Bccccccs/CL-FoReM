# task9.11.5 · 流程

递归规则：本层恰有TASK/PROCEDURE/RESULTS；不再委派，父汇总且核原件。依赖：.5先实施并审收集清单、验证；.6在稳定SHA与原始输出后独立审查，不以自报为通过。

1. 读输入，核活动编号/原件与写边界；独立日志记录开始/实际模型。
2. 只用替身子进程，先静态审全部收集项及导入路径，覆盖父先退出(SIGTERM/SIGKILL)、子先退出、竞争、写盘失败、deadline、遗留活动、重复启动/计费与跨阶段拒绝。
3. 保存精确命令、rc、stdout/stderr、SHA及限制。失败修复后新证据复审，原失败不覆盖。
4. 不启动模型/环境/回放/smoke/训练/test；交回父并停在准备完成。

写边界：仅 forem/scripts/task9_11/supervise.py、forem/src/task9_lr/admission.py、forem/src/task9_lr/tests/test_supervision_stdlib.py 与自身三文档/日志；如确需其他白名单文件先通知父。不得改worker/训练/环境/记录器/配置/原件/共享文档。

推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需核跨进程竞争、SIGKILL、退出证据与原预算；本轮仅委派 sol/high，实际后端按工具返回记录，不把推荐当实配。


实际采用的阶段合同（工程选择，非真实实验放行）：

- dispatch持flock，在启动前独占发布reservation和活动；完整文件先同目录临时写、flush/fsync，再os.link排他发布并fsync目录，禁止半JSON可见。guard与watcher继承同一锁、脱离会话；started/FAIL/不明身份跨全部阶段拒绝。
- guard在watcher armed后才启动客户端；watcher先检查owner/guard生存身份（PID+Linux start ticks），再检查单调cap/绝对deadline；父/guard死亡或客户端失败均由独立watcher停止精确sealed容器ID。客户端退出0还须独立容器/proc无worker证据。禁止pkill/同名替代容器；本轮没有真实Docker调用。
- 原cap内部预留完整固定控制调用链25s：quiet的inspect+probe各5s，失败后stop的inspect/kill/inspect各5s。取backend既定尾与spec声明的较大者，spec不能降低生产backend的25s。该值仅是子进程调用timeout算术，不证明fsync/内核调度/主机故障的wall上界；超过或证据缺失仍UNKNOWN/拒绝。慢quiet失败→慢stop替身也须原cap内检查，不放宽失败断言。
- 全目录资源扫描保持原poll_s；watcher不等待该扫描来检查deadline。宿主映射/workspace、/output、/runlogs，容器映射宿主output/log根；外部命令缺wall不按0计，重复路径只计一次。活动reservation与marker/ready身份绑定，已终结的PASS须独立receipt、reservation、当前code/protocol/release SHA才可跳过；跳过不启动、不再计费。
- 失败或未测完整host退出仍UNKNOWN；owner/guard均被杀时只保留reserved并拒绝复用。阶段PASS仅表示独立阶段见证，并不证明owner全wall、worker独立wait状态或真实Docker控制可靠。旧prepare入口明确NOT_READY，原窗口/预算与STOP不变。

专用执行命令为 `python3 -B forem/src/task9_lr/tests/test_supervision_stdlib.py`，只允许这份标准库脚本直跑；父/独立审查复核其AST收集与惰性项目导入链后执行，不经pytest/conftest。所有替身在TemporaryDirectory内，实际sleep子孙用精确PID/start身份终止；原stdout/stderr/rc/wall、各版本清单与失败均保留。推荐和实际配置区分见TASK。[SRC-1400](../../../../SOURCES.md#src-1400)
