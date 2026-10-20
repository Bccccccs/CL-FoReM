# task0.13 采集器P2与退出码独立代码复核

日期：2026-09-30；负责人：Codex 子Agent `/root/task0_remediation_review`；状态：done（只读代码复核及日志交付完成，不替代父Agent实际复测和task0验收决定）。

目标与授权：只判断task0.11发现的TERM/INT后采集器遗漏清理P2是否关闭，以及task0.12退出码是否被掩盖。不扩展无关问题，不改生产实现/共享文件、不启动Docker/ROS、不发真实信号、不提交；唯一写入文件为本日志。已读最新根AGENTS、task0.12及task0.13三文档，核查相关实现、进程退出码测试与采集器回归原始记录。父Agent负责活动进度、双环境45项测试、4项采集器/9项入口回归及新仿真。

HEAD：`438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804`；采集器修正仍在未提交工作区，既有其他文档整理及父Agent文件均保留。实际模型/档位未知，未切换。推荐Codex GPT6.1sol medium、Claude Sonnet5.5 medium：需要跨宿主中断、容器进程归属和退出码核对。

## 结论

**代码与现有同一回归的失败→通过证据支持关闭原采集器遗漏P2；未发现所限定采集器正常/失败/TERM/INT路径中的退出码被清理掩盖。** 父Agent仍须独立验证实际新回归结束后的完整容器进程清单，不能只依赖foreign=[]或本Agent审读结论。

上次发现的采集器问题确实不是已声明的“监督器SIGKILL前未记录极短命后代”限制：旧采集器由独立docker exec运行，本来就不属于launch/bag监督树。task0.12的修正直接改变了这条启动路径。

## 实现核验

- `forem/scripts/run_task0_smoke.sh:138–153`：check由 `task0_proc.py start --name check --allow-foreign` 启动，保存自身meta/tree；宿主轮询check的`status --tree`，然后读取独立root退出记录，而非长期阻塞在独立采集docker exec上。
- `run_task0_smoke.sh:52–72`：cleanup顺序check→bag→launch，每个实例按自身身份停止。采集器停止时仿真时钟尚未被先行撤掉，因此原先留下采集器等待停掉的clock的问题路径已消除。任一清理失败使cleanup_rc=15。
- `forem/scripts/task0_proc.py:140–173`：监督器收割managed root时，通过waitstatus_to_exitcode记录0、正常非零或负信号号至check.exit.json。记录root状态，而不是把监督器自身最终0当成采集成功。
- `task0_proc.py:215–221`：快速退出但已存在退出记录仍允许作为已启动实例，由上层读取其实际状态；避免把拒绝退出3混成启动失败或直接成功。
- `task0_proc.py:368–377`：exitcode读取已记录状态；未记录时输出exit_code=null且工具返回3，不产生成功采集码。
- `run_task0_smoke.sh:147–153,169–170`：正常路径保留记录的非零码，缺失/解析失败用97；check非零时最终失败1。没有因为stop返回0而覆盖check_exit。
- `run_task0_smoke.sh:61–70,107–108,74–104`：中断路径保留最终130/143；尚未获得check_rc时，在清理后读取退出记录，未知或0保守映射99，其他非零保留。真实原始root记录仍在check.exit.json，不将99误称为真实root退出状态。清理失败15具有优先级，仍为失败。
- `task0_proc.py:40–41,106–119`：foreign新增check_feedback，补充启动拒绝。真正验证本次中断残留仍应依赖完整命令行与身份记录。
- `forem/scripts/regress_task0_collector.py:37–40,57–91`：按docker top完整命令行中的本次`--run-id`检查，包括监督命令和采集命令；正常/拒绝/TERM/INT四种路径分别核对check_exit/final_exit和残留，覆盖上次名称名单漏项。

## 安全mock与语法验证（本Agent已执行）

使用PYTHONDONTWRITEBYTECODE=1导入真实task0_proc，并替换CDLL/prctl、signal.signal、Popen、identity、write_json_atomic、waitpid、descendants、sleep和open。无真实进程、信号或文件写入。真实cmd_supervise运行15次空扫描后退出：

|mock root wait status|监督器自身结果|写出的root exit_code|signal|
|---|---|---|---|
|0|0|0|null|
|3<<8|0|3|null|
|9（SIGKILL wait status）|0|−9|9|

按wrapper相同解析与决策表达式核对：原始0→正常check0/final0；原始3→check3/final1；原始−9→check−9/final1；未知→check97/final1。中断读取未知或0→check99；非零保留，TERM/INT最终仍143/130。`bash -n forem/scripts/run_task0_smoke.sh`退出0。该mock证明记录与值映射，真实中断生命周期仍由父Agent运行核验。

## 已有原始证据与源码身份（只读核对）

已读 `forem/results/task0/task0.12-before-report/report.json`：同一四项回归旧wrapper总体false，TERM/INT信号后仍有本次check_feedback命令行，check_exit=null；这准确重现上次失败路径。

已读 `forem/results/task0/task0.12-col1-report/report.json`：四项均true；TERM/INT信号前各有2条相关命令，信号后collector_after=[]。分别核读四个run的manifest、check.exit.json、check.cleanup.json：

|run-id|root原始退出码|manifest check_exit|final_exit|cleanup_exit|check residue|
|---|---|---|---|---|---|
|task0.12-col1-normal|0|0|0|0|[]|
|task0.12-col1-refused|3|3|1|0|[]|
|task0.12-col1-term|1|1|143|0|[]|
|task0.12-col1-int|1|1|130|0|[]|

四个run中的 `scripts/task0_proc.py`、`scripts/run_task0_smoke.sh`、`scripts/regress_task0_collector.py` 源码SHA256均与当前文件一致。退出失败来自采集器记录，中断失败来自wrapper记录，清理0没有覆盖它们。此处是对Claude既有数据的身份与内容核读，不把它写成父Agent本次新运行。

## 边界与交接

- 当前Linux subreaper/`/proc`与既有身份清理约定继续适用；wrapper SIGKILL不可捕获时不触发EXIT/INT/TERM清理，这一场景task0.12 RESULTS已明确声明，后续应按本次meta/tree人工停止；本审核没有将其描述为已通过的TERM/INT路径。
- 监督器被强杀之前未持久记录的极短命后代限制仍保留；它不能用来解释旧独立采集器漏清理。当前受监督check_feedback的已核验路径已关闭原问题。
- 没有重验ROS/物理配置或扩展task1；45项实际单元测试、4collector/9smoke回归和新的运动/HF/全容器清零证据由父Agent完成并汇总task0.13 RESULTS。

本Agent所有已执行命令为只读代码/数据核查、Python内存mock和bash语法验证，退出0；仅新增本日志，没有启动后台任务或需要停止的进程。建议父Agent在独立实际回归及全容器检查通过后关闭此P2，并按授权决定task0环境验收状态。
