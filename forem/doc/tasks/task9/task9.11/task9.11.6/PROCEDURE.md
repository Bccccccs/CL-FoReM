# task9.11.6 · 流程

当前状态done（独立准备审查完成）；37项最终替身/标准库PASS，完整host退出UNKNOWN，真实执行NOT_READY。

递归规则：本层恰有TASK/PROCEDURE/RESULTS；不再委派，父汇总且核原件。依赖：.5先实施并审收集清单、验证；.6在稳定SHA与原始输出后独立审查，不以自报为通过。

1. 读输入，核活动编号/原件与写边界；独立日志记录开始/实际模型。
2. 只用替身子进程，先静态审全部收集项及导入路径，覆盖父先退出(SIGTERM/SIGKILL)、子先退出、竞争、写盘失败、deadline、遗留活动、重复启动/计费与跨阶段拒绝。
3. 保存精确命令、rc、stdout/stderr、SHA及限制。失败修复后新证据复审，原失败不覆盖。
4. 不启动模型/环境/回放/smoke/训练/test；交回父并停在准备完成。

写边界：仅自身三文档与独立日志；实现、共享文档与旧证据只读。可用标准库替身复核，不导入torch/numpy/模型或环境。

推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需核跨进程竞争、SIGKILL、退出证据与原预算；本轮仅委派 sol/high，实际后端按工具返回记录，不把推荐当实配。

最终执行记录：独立先审收集/导入，稳定SHA下30项与额外7项直跑标准库通过；原slowquiet失败和修复后证据均保留。审查在准备交付结束，不继续测试或执行；父核原件/共享台账。完整host/真实Docker尾UNKNOWN、恢复NOT_READY详[RESULTS](RESULTS.md)及[SRC-1400](../../../../SOURCES.md#src-1400)，不由合成PASS替代。
