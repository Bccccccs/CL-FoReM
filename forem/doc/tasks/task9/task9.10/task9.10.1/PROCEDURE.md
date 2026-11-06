# task9.10.1 实现与执行 PROCEDURE

递归规则：本层恰有三文档，再委派须先建下级三文档。先读根AGENTS与父协议，检查身份和独立输出，按职责处理，交父核验。子Agent只写本任务/独立日志与指定代码，不修改全局来源与进度。

推荐Codex GPT6.1sol/high用于关键工作、luna/medium用于重复统计；Claude Sonnet5.5同难度强度仅为平台备选，本轮实际子Agent仅sol/terra/luna。实际运行配置待记录。

## 已冻结执行与收尾入口（2026-11-03）

原协议与授权沿[SRC-1382](../../../../SOURCES.md#src-1382)、[SRC-1383](../../../../SOURCES.md#src-1383)。以父窗口14:48:11.222061—18:48:11.222061 +08和run `t9.10-paired-20261103T144811+0800`累计记账。执行源为`forem/scripts/task9_10/replay.py`和`supervisor.py`，只读复用9.8 Recorder/coverage。先prepare-only零回合，父输入/审核准入后正式一次启动C4718→C4719→C4720→T4718→T4719→T4720；失败不重试。每run196回合，不缩池。实例化/模型/环境运行都只在隔离容器，原件只读。

正式已执行命令：

```bash
python3 -B /home/ybc/projects/CL-FoReM-task9/forem/scripts/task9_10/supervisor.py --run-config /home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.10-paired-20261103T144811+0800/run.json
```

六run封口、监督器finally停止本次容器并确认无GPU compute进程后，纯CPU原件汇总入口：`forem/doc/agent_logs/task9/task9.10/task9.10.1/make-report.py`，输出同run下独立`report/`，不得覆盖历史报告。该脚本不加载模型/不实例化环境，只归并原JSONL/原evaluate，最终独立核验仍由.2负责。运行源freeze不因报告生成改动。输入最终小文件哈希/大模型stat及总字节由.3另核。

性能报告区分worker内部、监督完整进程段、原evaluate和整个GPU资源窗口；actor host计时每次同步CUDA。core_step含emit、reset含写前记录，不可把嵌套分项相加；没有单独save计时、没有采GPU利用率百分比，未知部分明示。`original_finish.r_rad`保留原证据key但其值为无量纲CBL旋转残差，按[SRC-1384](../../../../SOURCES.md#src-1384)勘误解释。报告脚本完整扫描同段计算峰值/净减少，不能把旧score首次R处的早返回值当整段峰值。
