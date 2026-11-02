# T10-GPU-BATCH8-20261102

开始：2026-11-02T17:17:59.865682+08:00；负责人Codex，实际父模型/强度：平台未公开，未知。工作树 /home/ybc/projects/CL-FoReM-task10，分支codex/task10-upper-wm，初始HEAD ca57b4b，祖先检查rc0，工作区干净。已读根AGENTS、ENV、README、PROGRESS、task10三文档及SRC-T10-015。GPU1空闲；GPU2有其他任务，禁止干扰；现有task10容器未运行、GPU1映射已核对。

授权：只定位GPU下一更新差异、接入正常batch8入口的自然整批边界恢复。保持冻结B3 seed4718、上层seed101、batch8、1000预热/奖励/地图/终止原语义。不启动1000预热、1200/200试训、7h训练、配对或task11；旧账本只读。新namespace t10-gpu-batch8-20261102。

统一预算（尚未开始计时）：自首次新数值测量起绝对1800s，全局等待/失败/参照/恢复都计入，GPU1严格串行。GPU诊断最多300s、0真实决策、12次派生fixture更新；正常train真实验证最多1320s、总计64真实决策（参照与恢复均计入）、0更新；预留180s给复验/报告/失败清理，若前相位未用完不自行加大后相位。CPU确定性接线测试不采集、不做GPU更新，单次120s。正式新测量前在新总账写绝对开始/截止；每phase cap不得超过全局剩余。

分工/文件归属：task10.8 GPU诊断agent独占新gpu_diagnosis.py、task10_gpu_diagnosis.py、test_gpu_diagnosis.py及10.8三文档/日志；task10.9恢复agent独占recovery.py、test_recovery.py、新test_runner_boundary.py和10.9三文档/日志。父独占runner.py、正常入口包装、共享文档、预算/新运行。子Agent不自主启动GPU、不提交、不写共享文档；可自主选择模型/强度或进一步委派但须先建档、共享本预算/截止，不扩大授权。父核验原始证据统一签收。

实施计划（writing-plans；位置按AGENTS三文档约定）：
- [ ] 10.8从旧非空已更新fixture建立内存连续/连续及连续/实际存取两组；逐项核对更新前状态、样本/RNG，记录loss/梯度/权重/Adam首差异和耗时，必要时同输入确定性复测。
- [ ] 10.9审查边界API，提供正常入口确定性batch8接线夹具（混合结束不保存，整批自然结束保存；跨进程/截止/去重）；只修复实证缺陷。
- [ ] 父给train接入全批自然结束且journal/replay已提交、无pending/inflight的保存/退出/新PID恢复；不为等待边界保留已结束行。
- [ ] 父复跑夹具后启动有界真实验证；若未达全终局，保留逐批ended计数及未验证项，不扩时、不伪造边界。
- [ ] 更新RESULTS/PROGRESS/SOURCES、复算预算建议，交回决策者；本地提交不推送。

验收：严格逐位口径不变；任何未满足项明确未验证/原因未定位。建议Codex GPT6.1sol/high、Claude Sonnet5.5/high，因CUDA数值归因和跨进程采集状态/截止需跨模块核对。

正常入口初实现：显式--stop-at-boundary才保存collector-boundary.pt；默认训练条件不改。--resume只读原contract并校验源码/actor/配置，继承原ledger/deadline，不先reset。--boundary-reference仅允许0更新诊断，使用同循环自然继续一批但独立shadow账本/原run身份，随后恢复原learner/replay供退出artifact一致。参照额外8和恢复额外8均由父计费；真实primary max56（最晚boundary48后ref8+resume8，若boundary56则无ref预算、只报告部分），总保守不超过64。CPU RED/GREEN夹具由10.9构造中；未启动数值测量。

新测量启动 2026-11-02T17:22:53.495147+08:00；绝对epoch开始/截止 1793611373.4949822 / 1793613173.4949822；GPU相位monotonic截止 8820432.186586944，默认4更新+deterministic4+必要复现4，最多12；所有后续尝试共享原截止。总账见新namespace measurement-ledger.json。

GPU三测已结束，各4更新、0真实，default rc0但exact_mismatch、deterministic rc0 verified、default-repeat rc0但exact_mismatch；共12更新无追加。首观测差异在CNN backward梯度层；不是CUDA执行顺序定位，具体kernel未定位。CPU父首复跑因容器默认pytest临时目录owner不符25 setup errors（0真实/0更新），加独立--basetemp后复跑中；失败日志保留，时间计入总窗。

真实测量即将执行（尚未执行）：正常task10_run_bounded.sh train，max56主账本、0更新、seconds1320；--stop-at-boundary --boundary-reference，自然整批结束后同循环参照再8，原进程退出后同绝对epoch新PID--resume。总收费主账本reserved+参照增量≤64；不丢survivors、不改自然终止/地图/RNG。GPU1；容器forem-task10-runtime，UID1004:1004，torch2线程，batch8。可监控新namespace batch8/{events,batch-boundaries}.jsonl和training-budget.json、宿主orchestrator PID；仅外层父脚本串行启动，timeout TERM/KILL及全局原绝对截止双重限制。不重置旧ledger。新脚本task10_batch8_probe.py负责记录命令/rc/原deadline与全局收费。

父复跑31passed/18.48s/rc0（独立basetemp）；本地实现提交afc56f6，当前真实运行该版本，所有src冻结。派发task10.10独立terra/high只读审查runner/recovery/预算/数值证据，独占三文档和日志，无采集或GPU；父仍负责验证签收。

独立审核10.10发现采集tree_equal数值相等未区分signed zero（原纯CPU反例已保存）；GPU诊断使用严格字节compare_tree不受影响。为不改变真实运行合同，src冻结至本次进程结束，再以RED/GREEN修复比较器并对能取得的原件做严格复算；不能把旧collector verified直接称逐位。当前训练初批8真实选择4行自然结束、无整批边界；不主动结束其他4行。

真实阶段完成：afc56f6正常入口，宿主父PID3743784/训练PID3743824（容器PID322），7批56真实、0更新，rc0；各批自然结束行数4/4/2/5/7/6/5，无整批安全边界。主ledger reserved=completed56、inflight0、replay56；未启动参照或恢复，64总上限中8未消费但不改变已登记主56cap追加采集。Python总wall614.676s、外层616.170s、相位616.173s，1320s阶段内按决策上限退出；不是达到整批自然结束。未发生硬kill，没有抛弃未终局行去凑边界；最后活动回合保留为未完成，offline learner不能恢复环境。

独立审核修复开始（真实进程已退出后）：signed zero比较3failed/1passed RED；完整恢复端start/end缺产物及deadline接受反例2failed/3passed RED；GPU合同用旧PID存活会掩盖反例，改为子进程保存后再次RED 1failed，确认原入口可接受GPU字段改变。现最小修复tree_equal采用tensor/array/float字节；resume全start/end原件落盘；deadline/start计入status判定并失败；补GPU/physical_gpu/code_commit/random_seed当前合同核对。修复不回写真实版本afc56f6的contract，不冒称真实运行验证后续补丁。完整CPU及原始账本/回放审计进行中，0新增真实/0GPU更新。

最终验证：完整task10+task7_upper CPU组合163passed/3条件skipped/40.09s/rc0；源补丁提交ede1299，跳过CUDA下层1项与显式GPU训练2项。真实7份journal/回放56身份与560字段逐位、选点掩码、连续decision IDs审计rc0，无漏重，B3 unchanged。最终合成CPU两端完整start/end已落cpu-final并独立字节重算exact；不冒称真实恢复。总账闭账后只读摘要复算两次cmp rc0；父另读取GPU六原件重算（日志t10-parent-gpu-raw-recompute），不追加GPU/真实。

三个问题交接：1. 差异不能归因checkpoint，memory重复本身也差，确定性组合两组exact，具体kernel原因未定位；2. 只支持同主机同boot的全批自然终局、journal/replay已提交无pending/inflight且下批未采样，CPU已验，真实7批未达边界故真实新PID/原deadline等未验；3. 新采集均价11.003s/dec不作为优化收益，保守旧15.709和4s/update等工程假设得6.844h→7h排期，不建议当前放行1200/200，交回决策者。未启动预热/长训/四配对/task11。

实际新文件/修改范围：task10 runner/recovery、GPU双对照/复算、正常入口有界包装/父调度/账本审计、必要测试；task10.8/10.9/10.10三文档与独立日志，父TASK/PROCEDURE/RESULTS、PROGRESS、SOURCES。所有实现只在forem；旧账本/参考目录只读。最后原件目录forem/results/task10/t10-gpu-batch8-20261102，所有运行结束后恢复自建runtime原停止状态，其他GPU2任务不动。下一步由决策者核定配置和真实边界验收预算；本执行者不擅自追加。

最终只读GPU原件复算6controls/12updates、cmp相同、rc0；摘要复算cmp rc0。独立runtime已确认无工作进程并停止，GPU1无compute；GPU2原用户任务保留。最终闭账global 1318.725992s/1800s，受监督GPU及真实采集worker655.057321s；所有最后CPU原件复算与清理计入，新增真实56、GPU fixture12、在线update0。
