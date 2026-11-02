# TASK7.18.3-SAC-SPEEDUP-20261021

- 开始：2026-10-21约21:15 +08:00（派发文本21:30与主机时钟不一致，以commands.jsonl实际时间为准）；负责人Codex，实际gpt-6.1-sol / high（派发进程2997303参数核实）。推荐Codex GPT6.1sol/high（连续数值等价与CUDA捕获）；Claude Sonnet5.5/medium（复核）。
- 授权：[TASK](../../../../tasks/task7/task7.18/task7.18.3/TASK.md)、[PROCEDURE](../../../../tasks/task7/task7.18/task7.18.3/PROCEDURE.md)、[SRC-0908](../../../../SOURCES.md#src-0908)。只优化lower SAC/训练/经验池与相关tests；config仅新增性能开关。禁止改超参/精度/网络/采样更新顺序，不启动正式训练、不提交Git、不停止他人进程。
- 已读根/forem AGENTS、README、PROGRESS、ENV、7.18性能/正式训练节及SRC-0470–0475、7.18.3三文档。main分支，已有大量其他Agent改动，保留。GPU3 UUID GPU-29fe1ea1-d4e9-c14b-64f2-cb875ae92a0a无compute；GPU2 PID2996181为7.18.2，未干预。7.22独立运行。
- 准备处理：sac.py、training.py、replay.py及性能诊断/测试（实际按需要）；不改task7_sim/task7_upper。先保存源码快照、建立逐命令预算账本，检查基线≥1000连续更新可复现性与单次耗时，再试CUDA graph/host overhead候选；任何失败记录并不采用。
- run-id：t7.18.3-r1-20261021；日志logs/task7/t7.18.3-r1-20261021，产物results/task7/t7.18.3-r1-20261021。单命令timeout 590秒，累计容器预算7200秒。停止只针对本次timeout/会话，不影响其它任务。
- 尚未执行：基线/候选更新核查、E256≥2000转移端到端、5M推算；无通过结论。

## 21:25进度（以宿主时钟为准）

- 初始日志/PROGRESS 21:33是沿派发文本时间的记录错误；主机实测21:19完成首个36s命令，以commands.jsonl的ISO时间为准。PROGRESS下一次更新时一并纠正，不改其它Agent行。
- eager自身1000步首loss分歧step3，首步权重最大2.3245811e-6（已超过1e-6）；1000步最大0.02022636。两套采样索引/RNG及gather batch均相同。未证明具体底层kernel；先不以此单独归因cuDNN。
- async Normal约束GPU检查+原目标soft_update CUDA graph候选，1000步同样不满足严格loss/权重门，未采用。初步300样本更新p50 13.447→11.935ms。全部TF32/deterministic flags沿原值；Adam默认foreach路径，不改优化器/学习率。
- 已把候选移到speedup_candidates.py诊断子类，生产sac.py恢复至source_before字节一致；默认路径保持原eager。后续用独立实例load完整初始状态复查，避免deepcopy scheduler warning干扰解释。
- 为避开7.18.2/7.22共享仿真文件并发变化，拷贝只读输入到results/.../workspace（源码/配置快照）。端到端仅在该快照上运行，不修改原task7_sim，也不代表修复最终版训练性能。E2562304转移包含原warmup/采样/逐转移更新/日志/最终检查点，额外记录Transition摘要、全部loss/索引及审计成本；非正式训练。

## 21:31进度

- 实例独立构造、完整load同一真实回放与初始SAC状态（包含优化器/调度器）后，初始full_state逐元素相同已断言。real-eager-self-1000仍passed=False，最大权重差0.028852962；real-candidate-1000 passed=False，最大0.027155071。索引/回放采样RNG/CUDA RNG/全部gather字段相同。不能把基线不可复现说成候选等价通过。源码/运行证据见[SRC-0551](../../../../SOURCES.md#src-0551)，最终真实回放与端到端将补SRC-0552/0553。
- E256 sync各2304转移/2047更新已完成：wall104.1128/103.4555s（eager/candidate），含初始reset与最终checkpoint；额外Transition/loss审计1.8973/2.3457s。更新p50=13.5205/11.8705ms，但后续轨迹不同，不能将端到端0.6%差异归因加速。两者采样索引序列相同，loss从update2不同，Transition前3批hash相同、第4批起不同，完整json保留。
- e2e-eager-async正在同一只读快照运行，容器/主机进程由run.py与exec会话74742管理（timeout590s，train内部max_wall510s）；不触动其他进程。监控logs/.../e2e-eager-async.log；只终止本次run的timeout进程可停止，本次没有手动停止。累计已完成容器调用390.05s，最长107.62s。

## 收尾交接（2026-10-21，review）

- 推荐/实际模型与授权沿开头；未委派其他Agent。全部20条容器命令、退出码、完整argv/ISO时间/日志在logs/task7/t7.18.3-r1-20261021/commands.jsonl与NAME.log；汇总表在[RESULTS](../../../../tasks/task7/task7.18/task7.18.3/RESULTS.md)。累计795.705163s、最长107.617941s，预算内；最终四组fullrng与E2E对照依次完成；CPU导出与测试短暂重叠且均计账。
- 最终四组fullrng连续1000步：完整初始SAC状态、全部批次/索引、private采样流与Python/NumPy/CPU/all visible CUDA RNG均相同；全部loss/权重严格门失败，命令exit1。最大差见SRC-0552与CSV/PNG/SVG，不擅自归因kernel，不以原eager自比失败推翻门。只停止优化采用与更深生产改造，其他交付完成。[SRC-0552](../../../../SOURCES.md#src-0552)
- 两变体E256各2304转移/2047更新，before/candidate对照完成；包含真实池、复位、采样、GPU路径、推理、更新、账本/logging/末完整保存与审计。轨迹不同，不宣称端到端可靠提速；固定workspace快照不是7.18.2最终修复版放行。5M单趟条件推算、公式/输入/历史周期成本适用性见SRC-0553/RESULTS。[SRC-0553](../../../../SOURCES.md#src-0553)
- 18 passed/3原warning；1000次Normal采样/RNG与1000次target graph逐参数组件测试通过，不代替连续门。整步捕获两个探针exit2（eager退栈遮蔽首错、async_checks明确Adam capturable=False），未改优化器或精度。候选异常交付语义尚未生产验收，未采用。[SRC-0554](../../../../SOURCES.md#src-0554)
- 最终新增文件仅profile_speedup.py、speedup_candidates.py、tests/test_speedup.py；sac.py曾临时修改后恢复，原20文件与配置逐字节相同。候选仅诊断，不进入生产；原eager默认保持。不改sim/upper、不提交Git、不启动正式训练、不动STOP/他人进程。source_before/source_final/workspace与manifest全部保留。
- 宿主首个内联最终资源脚本exit1（psutil不存在，导入即失败、未执行），改标准库/proc的final_audit.py exit0；没有装依赖。final-audit.json与final-compute.csv证实21:44:36 GPU3无compute、无本任务测量worker残留，GPU1其他compute保留。
- 剩余/风险/下一步：**待决定**连续门与原GPU默认路径自比不一致的处理；Claude先读RESULTS/SRC-0550–0554/真实fullrng JSON与manifest，再复核。未经明确口径调整不采用候选；不视作正式重训授权或最终几何的48小时放行证据。无后台训练监控/停止事项。

- 2026-10-21 21:51：write_report.py exit0；stdlib逐链接/SRC-0550–0554唯一anchor/原lower SHA核查exit0；轨迹图已目视核查。PROGRESS写前重读，只改本任务UTF-8行并断言其余字节相同，改review。无剩余本任务执行进程；交接正文以RESULTS为准。
