# 当前进度

2026-11-02T11:33:50.944467+08:00 TASK9.6-SEMANTIC-EVAL-20261102 **done**（14:14父核验）：12:06三B3-5M语义复评结束，49/39/44（各/96），合计132/288=45.83%；288逐case成败均与旧结果一致，三rc0，无遗留评估进程。[SRC-1355](SOURCES.md#src-1355)。[task9.6](tasks/task9/task9.6/TASK.md) · [日志](agent_logs/task9/task9.6/20261102-codex-semantic-eval.md)。

2026-11-02T11:29:43.424971+08:00 TASK9-LOWER-READINESS-20261102 **done**：Codex复核14最终评估/1400回合一致；现场无训练，已有稳定候选；9.4整批独立验收/下层冻结仍待，未启动下一阶段。[SRC-1353](SOURCES.md#src-1353)。记录：[日志](agent_logs/task9/20261102-codex-lower-readiness.md)。

2026-11-02 09:05 +08 PROJECT-GITHUB-20261102 **review**：Codex 排查 GitHub 连接；本机 HTTPS 与仓库 SSH 读取成功，Codex GitHub 连接器仓库列表为空且读取该仓库返回 404，具体界面错误和原因待确认。[记录](agent_logs/project/20261102-codex-github-connectivity.md)。

唯一活动进度表。状态：`active`执行中、`review`待核验、`blocked`明确依赖、`paused`用户要求暂停、`done`交付并验证完成、`closed`按用户指令结束、`draft`方向草案。

2026-10-16整理：旧进度表（925行，含task1/2、视觉惯性、旧Task4路线的全部历史）已替换为本精简版，原文见备份（[SRC-0321](SOURCES.md#src-0321)）；各任务的完整历史仍在其三文档与agent_logs中。

## 当前调度（2026-10-26）

**task7全部后续执行paused；task8第一阶段整体review（后端与本次24图链路功能通过，8.6误选SAC单测违反无训练边界，严格合规失败；SRC-0997）**。[用户决定SRC-0984](SOURCES.md#src-0984)。task7已完成成果保留，下方旧active/派发记录是历史；不自动恢复v5、D10、7.24、旧诊断或上层训练。task8先用立方体PCD跑通整环境，再接现有语义mapgen；ghost传感器固定随底盘、无实体碰撞且忽略本体遮挡，场景遮挡/非传感器碰撞保留。[task8三文档入口](tasks/task8/TASK.md)。

## 运行中

2026-11-02 00:33 +0800 **无训练运行：task9.5 done（独立执行/协议验收PASS，三新方向均未观察改善）**；全部六3M于11-01 21:16结束，原三5M均完成67/63/64%，四卡空闲。仅截止守护待时；task9.4全13run最终验收另待，不自动扩大关闭。[SRC-1352](SOURCES.md#src-1352)；[最新结果](tasks/task9/task9.5/RESULTS.md)。

2026-11-02 00:28 +08 **训练已全部结束，GPU四卡空闲**：task9.5六run均3M/两阶段rc0、11-01 21:16结束，最终独立结果验收中；新U20/E15/R200两seed最终分别63/59、52/62、57/54%，均未达到预注册改善标准且均未退化。原三B3-5M完成67/63/64%。截止monitor仅等待既定时刻，无训练进程。[SRC-1351](SOURCES.md#src-1351)；[最新结果](tasks/task9/task9.5/RESULTS.md)。下方执行中快照均历史。

2026-11-02T00:23:44.176892+08:00 TASK9.5-STATUS-20261102 done（父核原件并接受独立结果验收），Codex已核新六run与原三5M实际终态/评估，并接受独立结果验收、GPU空闲；[核查日志](agent_logs/task9/task9.5/20261102-codex-progress-results-check.md)。

2026-10-31 22:44 +0800 **task9.5自主队列已启动，首U20-4718已保存512→恢复1000/38updates，196 smoke评估中**；CPU/static/G1独立验收已过，GPU G1共36passed。hostqueue1900665、截止monitor1900735存活，实际smoke目录host可写STOP；三方向×两种子正式3M尚待smoke/profile逐门，未声称训练完成。保留旧5M两个原PID。[SRC-1350](SOURCES.md#src-1350)；[协议/参数结果](tasks/task9/task9.5/RESULTS.md)。

2026-10-31 22:37 +08:00 task9.5修复静态复审PASS后，实际GPU0 G1 **36passed/rc0**，worker20.211s，policy/replay/optimizer CUDA证据齐；新输出根/STOP权限已仅在新namespace修复核验。独立G1实证验收中，training-policy尚未发；旧5M两个原PID继续。[SRC-1348](SOURCES.md#src-1348)、[SRC-1349](SOURCES.md#src-1349)。

2026-10-31 22:16 +08:00 task9.5隔离候选CPU **24 passed/rc0**（[SRC-1346](SOURCES.md#src-1346)），独立代码审查进行中，GPU尚未放行；原5M两PID保持，0/1空闲。审查重点为真实保存预留与中断/发散终态，完成修复复审后才G1。

2026-10-31 21:58 +08:00 **最新：原task9.4仅两个5M运行；H×2已按用户授权保存提前停止**（1,990,833/2,000,000消费步，合法interrupted，非原Q规则触发），GPU0/1已释放。新task9.5参数台账/三方向流程已写、预审F1–F4采纳，子Agent实施CPU阶段及性能审计已派发，新增GPU/长训尚未放行。原五条保护停止与四条正常完成保留；[SRC-1343](SOURCES.md#src-1343)、[SRC-1344](SOURCES.md#src-1344)、[性能SRC-1345](SOURCES.md#src-1345)。下方为历史。

2026-10-31 21:10 +08:00 **最新task9.4 active**：仍4正常完成/5保护停止/4运行，无等待。H约1.89M/1.93M、最新1.75M验证22%/15%；剩余5M两路约2.29M/750k、最新完整2.25M 58%/500k 49%。B1两种子/B3三种子3M均不退化，首个5M已完成67%，最终独立验收/冻结未执行；队列/训练/守护存活。[SRC-1334](SOURCES.md#src-1334)。下方历史快照保留。

2026-10-31 20:43 +08:00 **最新task9.4 active**：本批13 run为**4正常完成/5发散停止/4运行/0等待**。新增首个B3-5M完成，最终验证67%、末三均值62%（5M非预注册描述）；B3第三种子3M完成64%，B0第三种子1.389M保护停止。H两路约1.82/1.86M、1.75M验证22%/15%；另两个5M已运行约2.24M/500k，追加4720于19:05自动启动。队列/守护存活，冻结一致；最终独立验收未执行。[SRC-1332](SOURCES.md#src-1332)。下方为历史。

2026-10-31 09:17 +08:00 **最新task9.4 active**：状态仍2正常完成/4发散停止/4运行/3等待；H约365k/403k，B0第三种子约1.359M，首个B3-5M约3.709M/5M、最新3.5M验证**57/100**。队列/训练/守护/等待存活，69冻结文件一致，未改训练。[SRC-1331](SOURCES.md#src-1331)。下方为历史快照。

2026-10-31 08:40 +08:00 **最新：task9.4 active**。13 run中**2正常完成（B1×2）、4发散停止（B2/T各2）、4运行、3等待**。B2准确停止1.932M/1.796M，T 1.615M/1.542M，均触发“Q最大值超过500k参考10倍”，按既定规则计退化，不能作已完成3M。现场H约264k/302k（250k验证49%/45%）、B0-4720约1.257M（1.25M验证33%）、**B3-5M-4718已自动启动并到3.5M/5M**（3.25M验证51%）。主队列另2 queued＋追加5M-4720 waiting。队列/守护/等待均存活，冻结一致，本轮只读核查和记录；[SRC-1329](SOURCES.md#src-1329)、[记录](agent_logs/task9/task9.4/20261031-codex-training-status.md)。下方为历史快照。

2026-10-30 21:29 +08:00 **最新：task9.4 active，Codex按用户指令接手Claude全部现有工作（保留原有状态/限制）**。共13 run：**B1×2已完成3M；B2×2、T×2运行中；主队列6待跑＋追加B3-5M-4720等待**。B1最终验证62/100、72/100，末三次均值63.67%/69%，按既定判据均不退化，最终独立验收待完成。B2两路1.75M（最新完整1.5M验证48/100、41/100）；T 431k/412k（250k验证42/100、43/100）。队列/GPU监控/250k守护/追加等待均存活，69冻结文件及13配置hash一致；未启停进程/改训练。下方旧“无运行进程”仅指9.2/9.3，不代表当前现场。[SRC-1328](SOURCES.md#src-1328) · [接手记录](agent_logs/task9/task9.4/20261030-codex-takeover-status.md)。

2026-10-29 **TASK9.2-PRIM-LONG已全部结束（done with conditions，无运行进程）**；TASK9.3 S1–S3与V4已结束（无运行进程）。原启动记录：forem-dev内4个`task8_lower_train.py`（B0-4718 GPU0、B0-4719 GPU1、B3-4718 GPU2、B3-4719 GPU3），`--max-wall-s 172800`；`logs/task9/t9-long-20261028/launch.json`记PID，监控`scripts/task9_long_monitor.py`，停止某run用其输出目录`STOP`文件。[task9.2](tasks/task9/task9.2/PROCEDURE.md)

2026-10-27T13:12:01.101336+08:00 **TASK8.9-PHASE2-R4 active**：Codex接续SRC-1210，先诊断初始化、新1200s账本，严格等价优化与独立验收后固定smoke（C总7200s、单job内部900s），最终r4就绪报告停交Claude，不3M。[日志](agent_logs/task8/task8.9/20261027-codex-r4-coordination.md)。

2026-10-27T13:04:58.502798+08:00 **TASK8.9-PHASE2-R3 blocked / NOT_READY**：优化O1–O4及B10300/200发布独立PASS；C首个B0训练job初次reset sampling deadline失败，0动作/转移，保存后停，后六job未跑。无真实训练/196/恢复成本，3M墙钟/48h无法判定，未长训。交Claude决定有界初始化诊断/预算，不自动重试。C395.012049/3600，B3132.918238/5400，active空。[报告](../results/task8/t8-phase2-20261027/long-training-readiness-r3.md)、[SRC-1202](SOURCES.md#src-1202)。

2026-10-27T12:55:34.163512+08:00 **TASK8.9-PHASE2-R3 active**：优化O1–O4独立PASS；B全10300/200发布独立PASS（原wrapper报告文件名失败保留，生产finalize rc0，未重跑）；C原3600s账本固定8job smoke已释放GPU1，仍禁止3M。B3132.918238/5400s，C释放前149.024232/3600s。[日志](agent_logs/task8/task8.9/20261027-codex-r3-coordination.md)。

2026-10-27 r3优化子任务 **task8.9.1.1 done**：不同Sol独立O1–O4 PASS，scene冻结；cube/semantic256固定负载145.3530/116.2889转移/s，整体窗口比8.081/10.620×（重复窗口/匹配前缀限制见原件），opt473.033114724/1500s active空。B全量仍执行，C smoke未运行，父active且3M禁止。[SRC-1194](SOURCES.md#src-1194)、[SRC-1198](SOURCES.md#src-1198)。

2026-10-27T12:19:07.500967+08:00 **TASK8.9-PHASE2-R3 active**：Codex接续SRC-1190；优化新1500s账本、B从job40/offset4000续原5400s、验收后C原3600s内固定smoke，最终r3报告停交Claude，不启动3M。独立Sol验收，来源1191–1209。 [日志](agent_logs/task8/task8.9/20261027-codex-r3-coordination.md)。

2026-10-27T12:14:33.298996+08:00 **TASK8.9-PHASE2-R2 blocked**：独立A P2/P5未过，按用户全部通过后smoke/遇需决定即停；B安全停在4013图7.430GB，未200审查/发布，从offset4000续接；C22测试+实现独立PASS但未smoke/完整196/正式显存。A1597.584848/1800、B1128.277368/5400、C149.024232/3600秒，active空。报告NOT_READY，待Claude决定补A证据/预算与P5-smoke顺序，不自动续导出/长训。[报告](../results/task8/t8-phase2-20261027/long-training-readiness-r2.md)、[SRC-1164](SOURCES.md#src-1164)。

2026-10-27T11:57:16.143498+08:00 **TASK8.9-PHASE2-R2 active**：B六图独立PASS、24图测速Sol复核PASS，5400s同账本分块全量已启动；C初验发现两评估接口缺陷，修复22测试后独立实现门PASS，尚未正式196/smoke。A立方体256有效20计时样本约17.99转移/s，语义尚补测；条件B0基础3M≈57.7h>48h（旧SAC成本迁移推导，未含reset/eval/checkpoint），不能长训放行。[r2日志](agent_logs/task8/task8.9/20261027-codex-r2-coordination.md)。

2026-10-27T11:35:08.011144+08:00 **TASK8.9-R2-INDEPENDENT active**：不同实施者Sol/high（/root/independent_r2）验收B六图先导，纯读审计开始，后续A/B全量/C验收仍待交付。[日志](agent_logs/task8/task8.9/20261027-sol-r2-independent.md)。

2026-10-27T11:26:39.860824+08:00 **TASK8.9-PHASE2-R2-20261027 active**：Codex接续SRC-1161/1162，保留r1账本/失败；A GPU0 profile、B CPU cube-export-v2、C GPU1阶段0并行，独立Sol验收与有界smoke后止于就绪报告。负责人Codex，实际父模型按派发gpt-6.1-sol/medium（内部标识未独立核验）。[r2日志](agent_logs/task8/task8.9/20261027-codex-r2-coordination.md)。

2026-10-27T11:21:32.863133+08:00 **TASK8.9-PHASE2-20261027 blocked**：B按task8.1局部中心采样导出24诊断图66.71MB，6分层先导全内部孔7337(sampled)/7303(exact)，墙孔0、33432深墙射线漏0；不同Sol已独立复算严格内部体素孔（最小角解析/采样公式无误），需用户决定采样规则，未启动10300全量/200抽样。A仅64+24图预采样，81.7688/1800s，无256吞吐/热点；C局部测试4pass1fail、7.78894/3600s，无训练入口/完整恢复；B复核后18.96860/1800s、active空。后续性能/测试/smoke已停止，未3M长训。52冻结文件无漂移。长训报告**NOT_READY**：[父RESULTS](tasks/task8/task8.9/RESULTS.md)、[报告](../results/task8/t8-phase2-20261027/long-training-readiness.md)、[SRC-1125](SOURCES.md#src-1125)、[SRC-1144](SOURCES.md#src-1144)。此前active为历史开工快照。

2026-10-27T11:08:51.814055+08:00 **TASK8.9-PHASE2-20261027 active**：Codex父协调，SRC-1160；并行A性能/GPU0、B全量PCD/CPU、C阶段0/GPU1；各独立验收后有界smoke停在长训就绪报告，不启动3M。初检无旧账本、GPU compute空，forem-dev nproc=2。共享文档父维护。[日志](agent_logs/task8/task8.9/20261027-codex-phase2-coordination.md)。

2026-10-26 task8.8 r4最终末检通过：522链接/锚点/状态与13生产hash通过；**8.8 done、8.7 closed被v3取代**，原账本573.518864573911/900s、余326.481135426089s、active空，最大单图29.400735581905/30s。父8保持review/8.6历史违规保留，不自动开始下一阶段。[SRC-1090](SOURCES.md#src-1090)、[终账](../results/task8/t8-voxv3-20261026/r4-parent-accounting.json)。

2026-10-26T23:15:22.664652+08:00 task8.8 r4 **done**：独立S4 A–F全部PASS，C/D各24通过0失败，297981深墙射线漏0；外壳32021、非墙9exact/572部分与8058接触外残差保留。task8.7 **closed（被v3取代）**，历史FAIL保留，父task8继续review/8.6历史违规不抹除，不训练或自动推进后续。S4后573.404702134430/900s、首图29.286573142425s，父末检另计。[SRC-1087](SOURCES.md#src-1087)、[SRC-1089](SOURCES.md#src-1089)、[RESULTS](tasks/task8/task8.8/RESULTS.md)。下方旧active/review/blocked均为历史时点。

2026-10-26T23:09:16.745939+08:00 task8.8 r4 active：S3原件后审完成，24图C/D PASS、297981深墙射线漏0，非墙581=572部分边界+9exact与8058严格接触外已分类；独立S4（Sol high，≠S1）正在A–F总验收，尚未标done/关闭8.7。原账本568.540669176/900s（S3交接时），home000累计28.994034378s。负责人父Codex/S4；[SRC-1085](SOURCES.md#src-1085)、[父日志](agent_logs/task8/task8.8/20261026-codex-r4-coordination.md)。

2026-10-26T23:04:43.682456+08:00 task8.8 r4续接 active：Codex接手原账本561.948020482/900s，从S3后审继续到独立S4与父收尾；不重复生成/D，不重置费用。负责人父Codex；记录[父r4日志](agent_logs/task8/task8.8/20261026-codex-r4-coordination.md)。

2026-10-26T23:02:59.147556+08:00 task8.8 r4 **review，平台容量中断（非任务失败）**：固定15job全rc0、24图C/D原报告均passed；S3后审turn再次遇Selected model is at capacity，按用户要求记录并结束，不重派/换模型。S3脚本仅准备、独立S4未执行，8.8不标done、8.7不关闭；原账本561.948020482/900s、余338.051979518s、active空。外壳报告32021，非墙残差新增14图待分类；下次从S3后审起，勿重生成/重复D。[SRC-1088](SOURCES.md#src-1088)、[父日志](agent_logs/task8/task8.8/20261026-codex-r4-coordination.md)。下方r4 active/r3 blocked是历史快照。

2026-10-26T22:55+08:00 task8.8 r4固定执行 active：保存10图按深度门C全部PASS，旧9图D引用；Luna low已派补library000 D并续14图，原账本余466.508s。生产13交付和保真全零漂移。独立S4尚未执行。[SRC-1083](SOURCES.md#src-1083)。

2026-10-26T22:50:33.672488+08:00 task8.8 r4 active：Codex接手，核无既有r4产物；同一账本402.465809844/900s、余497.534190156s、active空。按[SRC-1081](SOURCES.md#src-1081)复判保存10图、补library000 D并续14图、独立验收，不改生产、不训练。记录[父r4日志](agent_logs/task8/task8.8/20261026-codex-r4-coordination.md)。

2026-10-26 task8.8 r3 **blocked，独立总验收FAIL**：A/B/E PASS、C/F FAIL、D INCOMPLETE；C9通过1失败14未跑，D9通过15未跑。home002 D已补；library000合格长弦15条inf（6下出域/9上出域）两套独立复算一致，需用户明确长弦无命中与量程边界免责口径，或决定资产处理；未生成地图、未续后14图、未训练。擦边3065、量程边界4有限+350inf、非墙内部洞0；E全零漂移。独立S4超时命令保留不算通过，原账本继续沿用，最终快照见[RESULTS](tasks/task8/task8.8/RESULTS.md)、[SRC-1067](SOURCES.md#src-1067)。8.7历史blocked、父8 review保留，不自动启动SAC。

2026-10-26T22:33:29.728223+08:00 task8.8 r3停止续图、独立验收中：C9通过/1失败/14未跑，D9通过/15未跑；library000长弦15条无限量程未命中已S3独立核实，需用户决定边界覆盖/是否重新生成。home002 D已补，E保真全零漂移，原账本余503.344s；不改门、不续图、不训练。[SRC-1064](SOURCES.md#src-1064)、[SRC-1065](SOURCES.md#src-1065)、[SRC-1066](SOURCES.md#src-1066)。

2026-10-26T22:23:23.475921+08:00 task8.8 r3第二次续接 active：Codex接手同一账本（303.466526602/900s，active空），前三图保存C复判与22job清单已有，不重复计费；S3核交接后派Luna补home002 D并续21图，独立Sol high终审。记录[父日志](agent_logs/task8/task8.8/20261026-codex-r3-coordination.md)。

2026-10-26T22:07:56.466156+08:00 task8.8 r3首次续派 active：Codex核已完成三图复判，不重跑；原账本余596.848s，接续S3清单→Luna执行→独立Sol验收。[日志](agent_logs/task8/task8.8/20261026-codex-r3-coordination.md)。

2026-10-26T21:29:11.355119+08:00 task8.8 r3 active：Codex父协调 gpt-6.1-sol/medium，按SRC-1061复判前三图并续21图C/D、补home002 D与独立终审；沿用原900s账本，不训练、不改生产量程。记录[父r3日志](agent_logs/task8/task8.8/20261026-codex-r3-coordination.md)。

2026-10-26 task8.8 r2 **blocked，当前门整体FAIL**：A/B/E PASS、C/F FAIL、D未完成。C2通过/1失败/21未跑，D2通过/22未跑；home_map_002两条长弦解析entry<6m但首体素命中6.005069/6.002626m，量程截断inf触发门，S3和独立S4一致。需用户决定量程边界诊断口径；不支持必须重新生成地图，不自行改门或续图。GPU139passed无skip；新保真基线全零漂移，原r1失败与archive漂移保留。已停止且无训练/地图生成；原900s账本继续沿用。[RESULTS](tasks/task8/task8.8/RESULTS.md)、[SRC-1046](SOURCES.md#src-1046)、[SRC-1048](SOURCES.md#src-1048)、[父r2日志](agent_logs/task8/task8.8/20261026-codex-r2-coordination.md)。 最终账本300.710209670/900s、余599.289790330s、active空；无遗留验证进程。[SRC-1049](SOURCES.md#src-1049)。

r1历史记录（已由SRC-1041授权r2续跑）：2026-10-26 task8.8：地图执行已停止，首图v3内部洞0但16/12890合格墙射线漏墙；独立复算确认原PCD部分边界层无候选，**需要用户重新生成**。余23图与v3链路NOT_RUN；CPU128passed11skipped，GPU四卡他人compute未测；157冻结/48源/519旧产物保真，archive两条checkpoint在既有rsync同步期间漂移，严格E失败。独立总验收FAIL并交接完成，无训练/地图生成/后台任务。[RESULTS](tasks/task8/task8.8/RESULTS.md)、[SRC-1025](SOURCES.md#src-1025)、[SRC-1026](SOURCES.md#src-1026)。

2026-10-26 task8.7最终交接：无遗留验证/训练进程，GPU compute为空、容器仅保活。A/B/E通过、C/F失败、D未执行；首图墙类32格欠覆盖，余23图按异常停止。节点blocked待用户决定新重建协议，父task8继续review；累计223.416167/900s。[结果](tasks/task8/task8.7/RESULTS.md)、[SRC-1004](SOURCES.md#src-1004)、[SRC-1006](SOURCES.md#src-1006)。

2026-10-26本次task8交付收尾：无遗留验证/训练进程，GPU已释放、容器仅保活sleep；功能链路与24图本次诊断通过，因8.6误选单测发生8次CPU SAC更新，严格合规fail、整体review。[结果](tasks/task8/RESULTS.md)、[SRC-0997](SOURCES.md#src-0997)、[SRC-0998](SOURCES.md#src-0998)。下面task7时点记录为历史，不构成恢复许可。

2026-10-26T09:21+08:00，Codex只读复查（[SRC-0983](SOURCES.md#src-0983)，[记录](agent_logs/task7/task7.23/20261026-codex-training-status.md)）：**当前本机无训练进程，四GPU空闲**。v5已于10-23 17:06触发看门狗规则b，worker最终SIGTERM/rc1，保存3,160,018步中断状态，未完成5M；最新3M验证5/100，2.75M3/100，最佳仍500k54/100。STOP仍在，本轮未恢复。task7.24已有原分布预检退出0（累计454.604s，账本无active job），未见A/B训练结果；不能把旧“派发P2”写成已训练完成。D10/退化诊断归档/上层放行仍待原任务处理。以下10-23快照为历史，不再代表当前运行状态。

2026-10-23T14:23:34+08:00，Codex只读复查（[SRC-0965](SOURCES.md#src-0965)，[日志](agent_logs/task7/task7.23/20261023-codex-status1423.md)）：

- **v5同步下层续训 active**：GPU2，supervisor/worker 1010022/1010035、看门狗1010178仍活跃，已2,702,698步。新增100图验证：2M严格成功12/100、2.25M 7/100、2.5M 2/100；当前已观察最优仍500k54/100。退化加重、原因未确认，未修改/停止训练；规则a仍按SRC-0916停用、b保留，14:16检查尚未触发b。
- **同步500k正式D10已因CUDA OOM中断，待处理**：八worker日志均报显存不足且现场无原进程，GPU0/1空闲。八轮各只写首决策100条，共800条部分记录/112 eligible、0完整轮，不能正式汇总或宣布冻结。原claim/半轮数据保留，不自动清理/重启；恢复与汇总风险见[task7.23](tasks/task7/task7.23/RESULTS.md)。
- **task7.18.8退化诊断待收尾**：原h1进程已不在现场，已有中间产物但报告/归因仍未归档验收，未确认根因。**task7.18.7不同步候选调查review**：修正规则未决定，未重训不同步。
- **task7.22仍部分交付，上层正式训练未放行**：下层未冻结、同步流水线缺项与正式成本问题仍在。现阶段不能据此判断世界模型提升或失效。
- 本轮仅状态查询与记录，没有自动持续监控或新实验；既有续训独立运行。下次接手先查2.75M以后新验证、D10显存故障/安全恢复与退化诊断归档。

10:08“D10 active”已被此最新OOM现场取代；历史快照与原文件保留。原始证据及适用限制见SRC-0965；本轮未启停任何运行。

## 阶段一：CBL复现

|任务|状态|待办|
|---|---|---|
|[task0](tasks/task0/RESULTS.md) 环境|done|—|
|[task3](tasks/task3/RESULTS.md) 核心迁移|done|—|
|[task4](tasks/task4/RESULTS.md) Gazebo普通SAC与首次WM|closed|—|
|[task5](tasks/task5/RESULTS.md) sim对照训练|5.0–5.3 done；[5.4](tasks/task5/task5.4/RESULTS.md) paused；[5.5](tasks/task5/task5.5/RESULTS.md) done|5.5最终sim评估内部成功32/33/30（各50，均值0.63；同批场景F0 1M为0.43），10-20 Claude复核通过（[SRC-0394](SOURCES.md#src-0394)）；Gazebo零样本评估需另行授权|
|[task6](tasks/task6/RESULTS.md) Gazebo失败诊断|6.1、6.3 done；[6.2](tasks/task6/task6.2/RESULTS.md) paused；[6.4](tasks/task6/task6.4/RESULTS.md)阶段一done、阶段二暂缓；[6.5](tasks/task6/task6.5/RESULTS.md) closed（10-20用户：不再继续，[SRC-0422](SOURCES.md#src-0422)）|6.4阶段二待定；[6.6](tasks/task6/task6.6/RESULTS.md) done（2026-10-27）：CBL自己的检查点sim 0.480、Z-B 0.223、Z-A 0.236|

## 阶段二：世界模型闭环

|任务|状态|待办|
|---|---|---|
|[task7](tasks/task7/TASK.md)|paused（2026-10-26用户冻结；既有成果保留）|v5已停/下层未验收、D10 OOM、7.18.7/7.18.8/7.24未闭合项全部留档，不继续执行；上层正式/ManiSkill不放行。SRC-0983/0984。|
|[task8](tasks/task8/TASK.md)|review（8.8 r4独立A–F通过、C/D各24/24；8.7 closed被v3取代；8.6历史合规失败保留）|无训练/下一阶段自动授权；详见SRC-1087/1089及8.8 RESULTS。|

## 实验主线

尚未开始（2026-10-21建立入口，[experiments/](experiments/README.md)，[SRC-0430](SOURCES.md#src-0430)）。

## 论文主线

已开展[paper0](paper/paper0/RESULTS.md)投稿venue与需加强实验项调研，r2为review（[SRC-0631](SOURCES.md#src-0631)）；尚未选定venue或授权新增实验/写作范围。本轮只核文档，不重新核验CFP/CCF时效。

2026-10-27新增[paper1](paper/paper1/TASK.md)（draft）：记录两层SAC与生物运动系统分工的类比，作为论文叙事框架候选（[SRC-1300](SOURCES.md#src-1300)）；文献待核验，扁平SAC对照是否增加待用户决定，不构成实验或写作授权。

## 项目级记录（近期）

|任务ID|负责人|状态|记录|
|---|---|---|---|
|TASK9.5-SAC-OPTIMIZATION-20261031|Codex（实际模型/强度未知）|done（2026-11-02最终独立验收；6run/18M完成，三方向均未观察改善，未自动冻结/追加实验）|[task9.5](tasks/task9/task9.5/TASK.md) · [日志](agent_logs/task9/task9.5/20261031-codex-sac-optimization.md)|
|TASK9.5.1-PREFLIGHT-20261031|Codex子Agent GPT6.1sol/high|done（21:42–21:47，父已采纳F1–F4；不代表新训练通过）|[结果](tasks/task9/task9.5/task9.5.1/RESULTS.md)|
|TASK9.5.2-IMPLEMENT-20261031|Codex子Agent GPT6.1sol/high|done（六正式3M与全门已完成，最终独立执行验收PASS）|[结果](tasks/task9/task9.5/task9.5.2/RESULTS.md)|
|TASK9.5.3-REVIEW-20261031|独立Codex子Agent GPT6.1sol/high|done（静态/G1/最终运行与数据分别PASS；科学结论无改善组）|[结果](tasks/task9/task9.5/task9.5.3/RESULTS.md)|
|TASK9.5.4-PERFORMANCE-20261031|Codex子Agent GPT6.1sol/medium|done（只读审计已核原件；未声称性能优化已实现）|[结果](tasks/task9/task9.5/task9.5.4/RESULTS.md)|
|TASK9.4-SUCCESS-BOTTLENECK-20261031|Codex（实际模型/强度未知）|done（已有评估/源码分析：首个5M的33个验证失败均累计20失败；无commit固定点与随机子目标贡献尚待trace验证；未改训练）|[日志](agent_logs/task9/task9.4/20261031-codex-success-bottleneck.md) · [SRC-1335](SOURCES.md#src-1335)|
|TASK9.4-CBL-SAC-STATUS-20261031|Codex（实际模型/强度未知）|done（21:10已有CBL改版线状态/边界汇总；长训active，无训练改动）|[日志](agent_logs/task9/task9.4/20261031-codex-training-status.md) · [SRC-1334](SOURCES.md#src-1334)|
|TASK9.4-3M5M-COMPARE-20261031|Codex（实际模型/强度未知）|done（同种子已有结果比较；5M最终验证较3M +4个百分点，仅一个完成种子，不判稳定提升）|[日志](agent_logs/task9/task9.4/20261031-codex-causal-assessment.md) · [SRC-1333](SOURCES.md#src-1333)|
|TASK9.4-STATUS-20261031-2043|Codex（实际模型/强度未知）|done（20:43状态复核与记录完成，训练仍active；无手工启停）|[日志](agent_logs/task9/task9.4/20261031-codex-training-status.md) · [SRC-1332](SOURCES.md#src-1332)|
|TASK9.4-STATUS-20261031-0917|Codex（实际模型/强度未知）|done（09:17状态复核完成，训练仍active，无启停/配置修改）|[日志](agent_logs/task9/task9.4/20261031-codex-training-status.md) · [SRC-1331](SOURCES.md#src-1331)|
|TASK9.4-CAUSAL-ASSESS-20261031|Codex（实际模型/强度未知）|done（仅已有对照归因与逐组配置解释；低更新比在两套包内均稳定，内部唯一机制未定；未改训练）|[记录](agent_logs/task9/task9.4/20261031-codex-causal-assessment.md) · [SRC-1330](SOURCES.md#src-1330)|
|TASK9.4-STATUS-20261031|Codex（实际模型/强度未知）|done（2026-10-31 08:39–08:40状态复核与记录；长训仍active；未启停进程）|[记录](agent_logs/task9/task9.4/20261031-codex-training-status.md) · [SRC-1329](SOURCES.md#src-1329)|
|TASK9.4-TAKEOVER-STATUS-20261030|Codex（实际模型/强度未知）|done（2026-10-30 21:28开始，21:31完成接手核查/记录；训练仍active，未启停进程或修改代码/配置）|[记录](agent_logs/task9/task9.4/20261030-codex-takeover-status.md) · [SRC-1328](SOURCES.md#src-1328)|
|TASK6.6-CBL-CKPT-EVAL-EXEC-20261027|Claude子Agent（sonnet/Sonnet5.5，强度默认）执行；Claude（claude-opus-5-5）派发与复核|done（2026-10-27 16:06派发，18:38评估结束，18:55 Claude复核通过；45/45条，errored 0；15个检查点合计S 0.480、Z-B 0.223、Z-A 0.236；§2回归steps判据由复核裁定为流程错误，SRC-1244/1245）|[RESULTS](tasks/task6/task6.6/RESULTS.md) · [日志目录](agent_logs/task6/task6.6/)|
|TASK6.6-CBL-CKPT-EVAL-SETUP-20261027|Claude（claude-opus-5-5）|done（仅建档：task6.6三文档；登记no_grad发现SRC-1240并更正SRC-0200/0058、task3.4；预检检查点兼容SRC-1242；评估尚未执行，待派发）|[task6.6](tasks/task6/task6.6/TASK.md) · [记录](agent_logs/task6/task6.6/20261027-claude-setup.md)|
|TASK8.10-PRIM-PLAN-20261027|Claude（claude-opus-5-5）|done（仅建档：task8.10三文档与A–H对照验收方案；新增可选后端primitive-obb-v1，默认仍v3；未派发/未实施，不影响8.9 r2；SRC-1181）|[task8.10](tasks/task8/task8.10/TASK.md) · [记录](agent_logs/task8/task8.10/20261027-claude-primitive-plan.md)|
|MAP-REPR-SURVEY-20261027|Claude（claude-opus-5-5）|done（仅调研：两类地图PCD均为盒体采样派生，建议以原语场景JSON为世界真值、PCD降为派生物；待用户决定，未改代码/合同，SRC-1180）|[记录](agent_logs/project/20261027-claude-map-representation-survey.md)|
|TASK8.9-SAC-PHASE2-PLAN-20261027|Claude（claude-opus-5-5）规划、派发与监督；执行Codex父协调（gpt-6.1-sol/medium，子Agent Sol/terra）|closed（2026-10-27用户作废，SRC-1220；未smoke/未长训；历史结果、账本保留；v3森林raycast与scene缓存代码保留；训练待地图整体优化后另行规划）|[task8.9](tasks/task8/task8.9/TASK.md) · [记录](agent_logs/task8/task8.9/20261027-claude-phase2-plan.md)|
|TASK8.10-PRIM-IMPL-20261027|Claude（claude-opus-5-5）规划与派发；执行Claude子Agent S1–S4（sonnet-5-5）|done（2026-10-27：primitive-obb-v1可选后端验收通过，默认仍v3；A/C/E/F/H pass、B pass_approved（SRC-1310）、D/G报告；S4独立验收含B全量括号重放带外0；账本7484.8s/8400s；默认后端切换与训练规划待用户定）|[task8.10](tasks/task8/task8.10/TASK.md) · [记录](agent_logs/task8/task8.10/20261027-claude-impl-authorization.md)|
|TASK8.11-PRIM-PRECHECK-20261027|Claude（claude-opus-5-5）规划与派发；X1/X2 Claude子Agent（sonnet-5-5 / high）|done（2026-10-27：W/I/C pass经X2独立验收，R/T报告；P 256环境初始化53.4s、干跑b256 P 345.6 vs V3 139.3转移/s（有界轮换负载）；账本899.1s/2400s；限制见RESULTS；SRC-1312）|[task8.11](tasks/task8/task8.11/TASK.md) · [记录](agent_logs/task8/task8.11/20261027-claude-plan-dispatch.md)|
|TASK8.12-PRIM-SAC-PLAN-20261027|Claude（claude-opus-5-5）|superseded（2026-10-28：协议移至task9，SRC-1313）|[task8.12](tasks/task8/task8.12/TASK.md) · [记录](agent_logs/task8/task8.11/20261027-claude-plan-dispatch.md)|
|TASK8.13-M1-CLOSE-20261028|Claude（claude-opus-5-5）|done（2026-10-28：`_contract()`加入primitive_scene/primitive_assets，哈希核对一致；task8地图迁移收尾，SRC-1313）|[task8.13](tasks/task8/task8.13/RESULTS.md) · [记录](agent_logs/task9/task9.1/20261028-claude-smoke-dispatch.md)|
|TASK9.1-PRIM-SMOKE-20261028|Claude（claude-opus-5-5）规划与派发；执行/验收Claude子Agent（sonnet-5-5）|done with conditions（2026-10-28：smoke全部完成，账本1409.94/4300s；B0-preserve检查脚本缺陷重做一次SRC-1314；P2独立验收；长训未授权，SRC-1313/1315）|[task9.1](tasks/task9/task9.1/TASK.md) · [记录](agent_logs/task9/task9.1/20261028-claude-smoke-dispatch.md)|
|TASK9.2-PRIM-LONG-20261028|Claude（claude-opus-5-5）父启动与监控；独立验收Claude子Agent（sonnet-5-5 / high）|done with conditions（2026-10-29：B3×2到3M不退化；B0×2看门狗发散停止于1.645M/2.463M；L5独立验收通过；“发散停止是否等同退化”待用户确认，SRC-1317）|[task9.2](tasks/task9/task9.2/RESULTS.md) · [记录](agent_logs/task9/task9.2/20261028-claude-long-launch.md)|
|TASK9.3-B0-DIAG-20261029|Claude（claude-opus-5-5）规划/复核；执行Codex（gpt-6.1-sol / high，workspace-write）；V4另一Codex Sol / high|done with conditions（2026-10-29：S1–S3交付，V4 pass with condition，SRC-1320/1321；阶段2核心6 run与可选T/H待用户决定；无运行进程）|[task9.3](tasks/task9/task9.3/RESULTS.md) · [记录](agent_logs/task9/task9.3/20261029-claude-plan-dispatch.md)|
|TASK9.4-STAGE2-20261029|Claude（claude-opus-5-5）规划/审核；执行Codex（gpt-6.1-sol / high，用户终端启动，已交接）|active（G1重跑与G2四组通过，G4于2026-10-30 08:21启动12 run，队列PID 253817，预计11-02 00:08结束（条件估计）；Codex已交接，父监控＋250k守护PID 262591（SRC-1327）；追加B3-5M-4720由等待脚本PID 219930在有空卡后自动启动（SRC-1326）；长训结束后独立验收）|[task9.4](tasks/task9/task9.4/RESULTS.md) · [记录](agent_logs/task9/task9.4/20261029-claude-dispatch.md)|
|TASK8.8-VOXV3-EXEC-20261026|Codex父协调（gpt-6.1-sol/medium）|done（r4独立A–F PASS、C/D24通过0失败，历史失败/容量中断与残差保留；无训练）|[日志](agent_logs/task8/task8.8/20261026-codex-r4-coordination.md) · [结果](tasks/task8/task8.8/RESULTS.md)|
|TASK8.8-VOXV3-DISPATCH-20261026|Claude（claude-opus-5-5）建档派发与复核；执行Codex父协调（gpt-6.1-sol/medium，子Agent Sol/Luna）|done（2026-10-26 23:2x；pcd-voxel-v3 A–F全PASS，24/24图C/D通过、墙缺格0、深墙射线漏检0，Claude独立复核一致SRC-1100；task8.7 closed；未训练）|[task8.8](tasks/task8/task8.8/RESULTS.md) · [记录](agent_logs/task8/20261026-claude-review-pcd-sac-ghost.md)|
|TASK8.7-VOXFIX-EXEC-20261026|Codex父协调（gpt-6.1-sol/medium）|closed（被task8.8 v3取代；历史v2失败保留，SRC-1089）|[日志](agent_logs/task8/task8.7/20261026-codex-coordination.md) · [结果](tasks/task8/task8.7/RESULTS.md)|
|TASK8.7-VOXFIX-DISPATCH-20261026|Claude（claude-opus-5-5）建档派发；执行Codex父协调（推荐gpt-6.1-sol/medium，子Agent Sol/Luna）|done（派发与授权实施/失败交接已返回；task8.7 blocked待新协议决定，SRC-1006；父task8仍review；Claude复核同意S4 FAIL，并复算闭合面归属规则24/24墙无缺格、代价≤1体素外扩，SRC-1020；v3方案待用户决定）|[task8.7](tasks/task8/task8.7/TASK.md) · [记录](agent_logs/task8/20261026-claude-review-pcd-sac-ghost.md) · [SRC-1001](SOURCES.md#src-1001)|
|TASK8-REVIEW-CLAUDE-20261026|Claude（claude-opus-5-5）|done（2026-10-26审查完成并派发修复，v3通过见TASK8.8行；原：2026-10-26；审查PCD实现、archive中CBL原始训练代码与ghost传感器：发现PCD格点边界舍入致墙体空洞/4.6–8.0%射线穿墙，SRC-0999；CBL RLlib长程不退化对照，SRC-1000；未改代码/未训练，下一步待用户决定）|[记录](agent_logs/task8/20261026-claude-review-pcd-sac-ghost.md) · [证据](../results/task8/t8-review-claude-20261026/)|
|TASK8-PCD-EXEC-20261026|Codex父协调（父实际模型/强度未知；子Agent显式Sol/Luna）|review（8.1–8.5功能及24图通过；8.6误选SAC两单测/8次CPU更新，严格合规fail；授权功能/性能/交接已归档，父复验rc1功能pass，累计约727.57s/1800s）|[记录](agent_logs/task8/20261026-codex-pcd-exec.md) · [结果](tasks/task8/RESULTS.md) · [越界SRC-0997](SOURCES.md#src-0997)|
|TASK8-MODEL-DISPATCH-20261026|Codex（实际模型/强度未知）|done（2026-10-26T10:02:54+08:00；21份文档与执行prompt同步Luna low简单执行/Sol medium或high推理验收；仅文档核验）|[记录](agent_logs/task8/20261026-codex-model-dispatch.md) · [SRC-0989](SOURCES.md#src-0989)|
|TASK8-PCD-PLAN-20261026|Codex（实际模型/强度未知）|done（2026-10-26T09:55:21+08:00；task7冻结、task8父＋6子任务21份文档、执行prompt、独立初审修订与静态核验；未实施/运行）|[记录](agent_logs/task8/20261026-codex-pcd-plan.md) · [结果](tasks/task8/RESULTS.md) · [SRC-0988](SOURCES.md#src-0988)|
|TASK7.23-STATUS-20261026|Codex（实际模型/强度未知）|done（只读现场与末次训练产物核查；未启停训练）|[记录](agent_logs/task7/task7.23/20261026-codex-training-status.md) · [SRC-0983](SOURCES.md#src-0983)|
|TASK7.25-MAPS-WAYPOINT-RESEARCH-20261024|Codex（实际模型/强度未知）|done（2026-10-24T22:27:34+08:00；三问题调研/流程、24图静态核查、原论文与代码来源、文档链接/哈希核查完成；未实施/实验，不接管7.24）|[结果](tasks/task7/task7.25/RESULTS.md) · [流程](tasks/task7/task7.25/PROCEDURE.md) · [记录](agent_logs/task7/task7.25/20261024-codex-research.md)|
|TASK7.24-LOCAL-EPISODE-PLAN-20261023|实施/运行GPT6.1sol medium、监督GPT6.1sol high；Codex父协调|paused（2026-10-26用户冻结；以下为历史：2026-10-23T15:52:24.303095+08:00；实现经r4独立审查PASS，已派运行子Agent开始P2；起始累计373.537s/4h，A/B尚未放行）|[实现](tasks/task7/task7.24/task7.24.1/RESULTS.md) · [监督](tasks/task7/task7.24/task7.24.2/RESULTS.md) · [运行](tasks/task7/task7.24/task7.24.3/RESULTS.md)|
|TASK7.23-LOWER-EXPLAIN-20261023|Codex|done（2026-10-23T14:29:40.880978+08:00；核现有源码/run配置并解释下层同步v5训练循环，不改代码/配置或运行）|[核查](agent_logs/task7/task7.23/20261023-codex-lower-training-explanation.md) · [来源](SOURCES.md#src-0967)|
|TASK7.23-STATUS-1423-20261023|Codex|done（2026-10-23T14:26:47.653357+08:00；只读复查：训练270万步、2.5M验证2/100；D10八worker OOM退出、0完整轮，未启停或修复）|[日志](agent_logs/task7/task7.23/20261023-codex-status1423.md) · [来源](SOURCES.md#src-0965)|
|TASK7.23-TAKEOVER-AUDIT-20261023|Codex父Agent；3子Agent gpt-6.1-sol / medium|done（2026-10-23T10:13:59.129821+08:00；当前进度审核完成并父复核；确认v5续训、同步500k D10未完成、不同步候选失配/上层缺项/D10恢复与汇总风险；仅改文档，未启停运行）|[结果](tasks/task7/task7.23/RESULTS.md) · [日志](agent_logs/task7/task7.23/20261023-codex-takeover.md)|
|PROJECT-PPT-REVIEW-20261023|Codex|done（2026-10-23T09:12:14+08:00；已检查7页XML与渲染，核对task7.8/7.10/7.11合同，交付逐页组会汇报与视觉建议；不改原PPT、不改代码或实验；保留Claude制作任务）|[日志](agent_logs/project/20261023-codex-ppt-review.md)|
|PROJECT-DESIGN-REPORT-DECK-20261022|Claude（claude-opus-5-5）|active（2026-10-22 18:4x；按用户要求制作阶段二整体设计汇报幻灯片（claude.ai私有Slides artifact）；只读文档与训练产物、不改代码/实验；内容取自task7三文档、PLAN、PROGRESS、DECISIONS与v4训练中间验证）|[日志](agent_logs/project/20261022-claude-design-report-deck.md)|
|TASK7.22-UPPER-TRAIN-20261021|Codex（gpt-6.1-sol/high，exec PID2984488核实）|review（r2部分交付，2026-10-22；异步阶段1=1152决策/153 SAC，阶段2=31独特样本/1125epoch早停，阶段3=1024决策/25 SAC/25 FP；入口atol1e−6及两阶段独立恢复通过，schema4三目录332 passed、现有产物完整性通过；同步1152/0更新，阶段2/3未执行：数据不足且余量不足续采；累计21380.063s/21600s，仅GPU1/旧pilot50k，上层正式未启动）|[日志](agent_logs/task7/task7.22/20261021-codex-upper-train.md) · [结果](tasks/task7/task7.22/RESULTS.md)|
|TASK7.18.3-SAC-SPEEDUP-20261021|Codex（GPT6.1sol / high，exec参数核实）|closed（22:00用户决定不采用，提速约11%；SRC-0909；原：review（2026-10-21 21:51；有界尝试/对照完成；严格1000步连续门失败，原eager自比也失败，候选未采用；原SAC/训练/配置字节保留；GPU3已无compute；连续验收口径待决定，交Claude复核））|[日志](agent_logs/task7/task7.18/task7.18.3/20261021-codex-sac-speedup.md) · [结果](tasks/task7/task7.18/task7.18.3/RESULTS.md) · [等价](SOURCES.md#src-0552) · [核查](SOURCES.md#src-0554)|
|TASK7.18.2-SELFCOLL-FIX-20261021|Codex（GPT6.1sol / high，exec参数核实）|done（23:30 Claude复核r3：schema4，链式FPR4.53%、13真＋顶板6全检出、回放0误报、base–upper 412接触恢复检出；35 passed复验）；原：review（r3 2026-10-21T23:22:50.785346+08:00；schema4球对级零位许可已交，base–upper 10k TP412/FP1850/FN0；chain13/17/358/0，顶板6/6，回放0误报；331 GPU passed，容器8.116min；SRC-0560–0564；core.py本轮未改，不训练/不提交，交Claude复核）|[日志](agent_logs/task7/task7.18/task7.18.2/20261021-codex-selfcoll-fix.md) · [结果](tasks/task7/task7.18/task7.18.2/RESULTS.md) · [r3来源](SOURCES.md#src-0560)|
|TASK7.18.1-DIAG-20261021|Codex（GPT6.1sol / medium，exec参数核实）|done（20:55 Claude复核采纳：网格参照229报警216纯误报、上臂–顶板漏检6、DLS非bug、不同步超时待修几何后再看；用户定修复方案B＋网格证实允许表SRC-0906→task7.18.2；原：review（2026-10-21 20:26；六项只读诊断已交：链式229报警中216纯误报、上臂–顶板整对漏检6次；同姿态修复估算与限制已写；容器约16.03min，训练保持STOP、不恢复；SRC-0530–0535；待Claude复核））|[日志](agent_logs/task7/task7.18/task7.18.1/20261021-codex-diag.md) · [结果](tasks/task7/task7.18/task7.18.1/RESULTS.md)|
|PAPER0-VENUE-EXP-RESEARCH-20261021|Codex（实际模型/强度未知）|review（r2 2026-10-21T20:22–20:29+08:00；paper0-r2-20261021：按第七版重评11个A类候选，建议AAAI首选/ICLR会议备选/AIJ期刊备选；加强项优先级、成本依赖、r1更正及缺口已交；SRC-0632–0643；仅文档，交Claude复核）|[日志](agent_logs/paper/paper0/20261021-codex-venue-exp-research.md) · [结果](paper/paper0/RESULTS.md)|
|PAPER0-DISPATCH-20261021|Claude（claude-opus-5-5）|done（2026-10-21；按用户要求建paper0三文档（投稿venue与实验设计调研，只调研与写文档，SRC-0600），以codex exec派发Codex gpt-6-astra / medium）；20:2x用户上传CCF第七版目录：IJCAI为B、ICLR为A，r1首选IJCAI不成立，已记SRC-0630并在paper0 RESULTS补充；20:3x按用户要求派Codex r2（CCF-A重选venue＋需加强项，SRC-0631，PID 2924459）|[paper0](paper/paper0/TASK.md) · [派发记录](agent_logs/paper/20261021-claude-paper0-dispatch.md)|
|PAPER1-BIO-ANALOGY-20261027|Claude（claude-opus-5-5，强度未知）|draft（2026-10-27；按用户要求在论文主线记录两层SAC与神经系统分工的类比：修正对应表、设计历史与叙事分开、三个设计选择与对照组、扁平SAC缺口；SRC-1300–1308，文献待核验；仅文档）|[paper1](paper/paper1/RESULTS.md) · [记录](agent_logs/paper/paper1/20261027-claude-bio-analogy-record.md)|
|TASK7.18.1-SETUP-REVIEW7.21-20261021|Claude（claude-opus-5-5）|done（2026-10-21T19:50–20:10；task7.18.1三文档与派发提示已写（SRC-0521，现在可派，GPU0）；复核task7.21 r3：测试重跑通过，退回r4补不同步Δs_k；只读与写文档）|[task7.18.1](tasks/task7/task7.18/task7.18.1/TASK.md) · [7.21复核](tasks/task7/task7.21/RESULTS.md) · [7.21 r4提示](agent_logs/task7/task7.21/20261021-claude-review-r3.md)|
|TASK7.19-G7-IMPL-20261021|Codex|review（实现复核通过，20:25 Claude重跑39 passed；正式D10待7.18修复后重训检查点；原：r2 2026-10-21；SRC-0904纯超时排序与D10固定配置已落实；CPU34 passed/5 GPU用例延期Claude复核，GPU3已有compute；正式D10/训练未执行；SRC-0484–0485）|[日志](agent_logs/task7/task7.19/20261021-codex-g7-impl.md) · [结果](tasks/task7/task7.19/RESULTS.md)|
|TASK7.21-UPPER-MODEL-20261021|Codex|done（20:30 Claude复核r4：CPU/GPU各44 passed，不同步Δs_k已补；task7.22派发时断言须用明确容差）|[日志](agent_logs/task7/task7.21/20261021-codex-upper-model.md) · [结果](tasks/task7/task7.21/RESULTS.md)|
|TASK7.22-DISPATCH-20261021|Claude（claude-opus-5-5）|done（20:45以codex exec派task7.22上层训练流水线（PID 2931701，GPU1）；下层用7.18 pilot 50k检查点仅作流水线验证；正式训练未授权）|[派发记录](agent_logs/task7/20261021-claude-codex-exec-dispatch.md)|
|TASK7.20-DECISION-ENV-20261021|Codex|done（20:40 Claude复核r5：G1排序符合SRC-0905；Claude修正可行分支并列取间隙（g1.py两行＋1测试），27 passed；原：review（r5，2026-10-21；SRC-0905的G1两分支已补齐；定向14 passed，全目录218 passed/退出0；仅g1.py与其测试，GPU1已退出；不训练；SRC-0493，待Claude复核））|[日志](agent_logs/task7/task7.20/20261021-codex-decision-env.md) · [结果](tasks/task7/task7.20/RESULTS.md)|
|PROJECT-CBL-N2M2-LEARNING-20261022|Claude子Agent（Sonnet5.5）|done（2026-10-22；只读调查完成：CBL/N²M²训练曲线、失败构成、任务与评估差异、可借鉴技巧；登记SRC-0935–0939；结论为推断，待task7.18.5验证）|[报告](agent_logs/project/20261022-claude-sonnet-cbl-n2m2-learning.md)|
|TASK7.18.5-INTERIM-D10-20261022|Claude子Agent（Sonnet5.5）|review（2026-10-22 19:10；v4 1M检查点中期D10式诊断已完成，非正式D10；sync可行比例20.9%、可行候选到达69.2%；async可行比例6.4%、n=8；无遗留进程）|[RESULTS](tasks/task7/task7.18/task7.18.5/RESULTS.md)|
|TASK7.19-D10-V5-20261023|Claude子Agent（Sonnet5.5）|active（08:40；v5同步500k正式D10，GPU0/1）|[task7.19](tasks/task7/task7.19/TASK.md)|
|TASK7.18.8-DEGRADATION-20261023|Claude子Agent（Sonnet5.5）|active（08:40；只读诊断约1.2M后退化）|[TASK](tasks/task7/task7.18/task7.18.8/TASK.md)|
|TASK7.18.6-V5-20261022|Claude子Agent（Sonnet5.5）|续训中（2026-10-23 09:06；1.75M被规则a停止后按SRC-0916从interrupted续训，同run目录/配置/GPU2；supervisor 1010022、worker 1010035、看门狗1010178，规则a停用、规则b保留）；原：训练中（看门狗）|[TASK](tasks/task7/task7.18/task7.18.6/TASK.md)|
|TASK7.18.7-ASYNC-TIMEOUT-20261022|Claude子Agent（Sonnet5.5）|review（2026-10-23；原因：不同步非原地候选s_k恒＝s0而底盘目标距1 m，机械臂保持TCP的底盘位移仅0.15–0.4 m，136/136候选G7不可行；选项O1–O4待用户决定；只读，无遗留进程）|[RESULTS](tasks/task7/task7.18/task7.18.7/RESULTS.md)|
|TASK7.18.4-REWARD-FIX-20261022|Claude子Agent（Sonnet5.5）|v4两变体于约1.5–1.7M被看门狗停止（漏洞经回合终止复现，SRC-0915）；后续转task7.18.6/7.18.7；原：训练中（看门狗早停）：2026-10-22 12:34从头启动v4 sync(GPU2,worker 3949069)/async(GPU3,worker 3949120)各5M，C′＋async_time_penalty=0（SRC-0912/0913/0920/0921）；看门狗PID 3949173，规则与监控/停止/恢复见task7.18.4 RESULTS第六节|[TASK](tasks/task7/task7.18/task7.18.4/TASK.md)|
|TASK7.18-STAGE-L-20261021|Codex（GPT6.1sol / high，exec参数核实）|paused（2026-10-22 08:43放STOP：v3训练约1.58M步出现“主动失败”奖励漏洞，SRC-0911；修复与重训转task7.18.4）；原：active 训练中（2026-10-22T00:10:02.336643+08:00；schema4从头正式两变体各5M，sync GPU2 worker3223585、async GPU3 worker3223627；新25k/100图/IO及逐元素路径核查通过，估计30.11/29.95h；监控：python3 forem/scripts/task7_lower_monitor.py forem/results/task7/t7.18-v3-20261021/formal-v3-sync（async同理）；SRC-0477–0479；未完成/冻结；旧formal仅历史）|[日志](agent_logs/task7/task7.18/20261021-codex-stage-l.md) · [结果](tasks/task7/task7.18/RESULTS.md)|
|TASK7.18-SELFCOLL-STOP-20261021|Claude（claude-opus-5-5）|done（2026-10-21T19:20–20:05；CPU诊断：训练池40回合固定底盘沿路线链式IK，388个接受解中229个（59%）被判自碰撞，主要wrist_1–夹爪、前臂–wrist_3、前臂–夹爪，推测为胶囊包络重叠误报（脚本forem/logs/task7/claude-selfcoll-diag/）；用户“立即停训练并修复”，19:52放STOP；以codex exec派发另一Claude会话已写的task7.18.1只读诊断并附上述证据与网格复判要求（PID 2879737，GPU0）；修复另派）|[诊断脚本](../logs/task7/claude-selfcoll-diag/diag.py) · [task7.18.1](tasks/task7/task7.18/task7.18.1/TASK.md)|
|TASK7.11-G6-ISOLATION-20261021|Claude（claude-opus-5-5）|done（2026-10-21T11:00起；G6-1独立评估流、G6-2用测试池、推演/执行不一致诊断进task7.20 info（只诊断），用户按推荐确定（SRC-0520）；回写task7.11 W.7、task7.20 TASK与派发提示、父TASK U8/§4/§5；C类设计项至此全部定完；只写文档）|[日志](agent_logs/task7/task7.11/20261021-claude-g6-isolation.md)|
|TASK7-UPPER-DISPATCH-20261021|Claude（claude-opus-5-5）|done（2026-10-21；用户授权task7.20–7.22实施、正式训练另行授权（SRC-0439）；三任务状态改为已授权；派发提示已写：7.21现在可派（GPU0），7.20待7.17 done（GPU1），7.22待7.20、7.21 done（GPU1）；另：上层起草来源条目因与并发改号撞号由0436改为SRC-0438；只写文档，Claude未派发）|[派发提示](agent_logs/task7/20261021-claude-codex-dispatch-7.20-7.22.md)|
|TASK7-UPPER-IMPL-DRAFT-20261021|Claude（claude-opus-5-5）|done（2026-10-21；按用户要求起草上层实施任务三文档：task7.20决策级环境与G1、7.21网络模块、7.22训练流水线（有界核查与试训，正式训练另行授权）；**均未授权**，等用户授权；SRC-0438；只写文档）|[日志](agent_logs/task7/20261021-claude-upper-impl-draft.md)|
|TASK7.19-G7-GROUP-20261021|Claude（claude-opus-5-5）|done（2026-10-21T10:25起；G7-5 f_k映射到f_k v1同一布局、G7-6只训阶段1并对阶段1基线比较，用户按推荐确定（SRC-0435）；回写task7.19、父TASK §4、task7.4修订第6条、DECISIONS；只写文档；未做task7.15–7.17复核以免与另一Claude会话重复）|[日志](agent_logs/task7/task7.19/20261021-claude-g7-design.md)|
|TASK7.15-CANDIDATES-20261021|Codex|done（11:00 Claude复核r2通过；原：review r2：137 passed，原73/73无回退；仅排除并行test_env；R_pre/10000FK/近似接受/两变体等价/边界带/计时均已验证，累计268.0s；待Claude复核）|[日志](agent_logs/task7/task7.15/20261021-codex-candidates.md) · [结果](tasks/task7/task7.15/RESULTS.md) · [SRC-0443](SOURCES.md#src-0443)|
|TASK7.15-REVIEW-R1-20261021|Claude（claude-opus-5-5）|done（2026-10-21T10:14–10:30；重跑与读码，语义与task7.9一致；判定边界差异属已接受合同、R_pre须实施、旧A.4公式已作废；r2派发提示已写）|[复核](tasks/task7/task7.15/RESULTS.md)|
|TASK7.16-MAPGEN-20261021|Codex|done（10:55 Claude复核通过；原：review 2026-10-21；10300张正式地图；76 passed/20 CUDA延期；全量读取/PNG/种子审计通过，待Claude人工抽图与完整GPU复核；SRC-0451）|[日志](agent_logs/task7/task7.16/20261021-codex-mapgen.md) · [结果](tasks/task7/task7.16/RESULTS.md)|
|TASK7.16-REVIEW-20261021|Claude（claude-opus-5-5）|done（2026-10-21T10:35–10:55；10300张独立几何检查违规0、种子不重叠、高度层25/40/35；人工核对PNG与JSON；完整GPU回归146通过（唯一失败属进行中的task7.17）；task7.16标done）|[复核](tasks/task7/task7.16/RESULTS.md)|
|TASK7.19-G7-DESIGN-20261021|Claude（claude-opus-5-5）|done（2026-10-21；G7-1–G7-4起草并经用户按推荐确定（SRC-0436、SRC-0434；推导条目原误编号0433，已改号），回写task7.19三文档、父TASK U23/U25、task7.4 I5、task7.5 B10、父PROCEDURE；task7.19实现派发提示已写，待7.15、7.17 done后由用户派发；只写文档）|[日志](agent_logs/task7/task7.19/20261021-claude-g7-design.md)|
|TASK7-TRUTH-LINE-20261021|Claude（claude-opus-5-5）|done（2026-10-21T09:00–09:50；讲解感知栅格与SC²-WM/CBL差别；用户考虑真值地图线后决定不加、忠于SC²-WM（SRC-0432）；只读与写文档）|[日志](agent_logs/task7/20261021-claude-truth-map-line.md) · [SRC-0432](SOURCES.md#src-0432)|
|PROJECT-DOC-MAINLINES-20261021|Claude（claude-opus-5-5）|done（2026-10-21；按用户指令把文档分为项目/实验/论文三条主线：新建experiments/与paper/入口README，更新doc README、PROGRESS、AGENTS、DECISIONS、SRC-0430；只写文档，未设计具体实验或论文内容）|[日志](agent_logs/project/20261021-claude-doc-mainlines.md)|
|TASK7-IMPL-SETUP-20261021|Claude（claude-opus-5-5）|done（2026-10-21T09:30–09:50；用户授权后续实施（SRC-0431）：建task7.15–7.19三文档、父PROCEDURE表、7.15–7.17派发提示（可并行）；7.18待前三者done、7.19待G7设计；只写文档）|[日志](agent_logs/task7/20261021-claude-impl-setup.md) · [派发提示](agent_logs/task7/20261021-claude-codex-dispatch-7.15-7.17.md)|
|TASK7.17-EPISODE-20261021|Codex|done（14:40 Claude复核r2通过，E6口径SRC-0902，153 passed；原：review r2；单Core/完整入口/E4已交付，原73通过；近奇异关节精度待决定）|[日志](agent_logs/task7/task7.17/20261021-codex-episode.md) · [结果](tasks/task7/task7.17/RESULTS.md)|         
|TASK7.17-REVIEW-R2-20261021|Claude（claude-opus-5-5）|done（2026-10-21T14:17–14:40；批量Core恢复、E1–E5落实；近奇异关节按E6改测试容差，全目录153 passed；task7.17标done；随后经用户授权用codex exec派发7.18–7.21）|[复核](tasks/task7/task7.17/RESULTS.md) · [SRC-0902](SOURCES.md#src-0902)|
|TASK7-CODEX-EXEC-DISPATCH-20261021|Claude（claude-opus-5-5）|done（2026-10-21T14:46；经用户授权以codex exec后台派发task7.18（PID 2530514，high）、7.19（2530515）、7.20（2530516→Xorg误停后重启2535683）、7.21（2530517→重启2535684），GPU2/3/1/0；14:49–15:4x Codex容量/额度中断，16:53额度恢复后重启7.18（2695454）、7.20（2695455）、7.21第三轮（2695456）；17:15派7.19第二轮（2705435）；7.22待7.20、7.21 done）|[记录](agent_logs/task7/20261021-claude-codex-exec-dispatch.md)|
|TASK7.15-7.17-REVIEW-20261021|Claude（claude-opus-5-5）|done（2026-10-21T10:40–11:15；7.15 r2复核通过标done（DLS固定成本转7.18）；7.17 r1返工：逐环境串行吞吐16转移/s须改批量；用户定E1–E3；修复SRC-0433重号（G7推导改SRC-0436）；r2派发提示已写）|[7.15复核](tasks/task7/task7.15/RESULTS.md) · [7.17复核](tasks/task7/task7.17/RESULTS.md) · [SRC-0437](SOURCES.md#src-0437)|
|TASK7.14-ENVCORE-20261020|Codex|done（2026-10-21 Claude复核r2通过；原：review 2026-10-21T00:51:39+08:00；r2 P1–P7补完，73项通过；完整几何/CPU64对照/有界E扩展完成；累计1007.432s；SRC-0428）|[日志](agent_logs/task7/task7.14/20261020-codex-envcore.md) · [结果](tasks/task7/task7.14/RESULTS.md)|
|TASK7.14-REVIEW-R2-20261021|Claude（claude-opus-5-5）|done（2026-10-21T09:00–09:20；重跑73 passed；P5/P6/P3代码对照SRC-0425一致、信息隔离核对；记录“上臂–顶板”整对放行的漏检限制、G1遮挡报告与推演性能瓶颈；task7.14标done）|[复核](tasks/task7/task7.14/RESULTS.md) · [日志](agent_logs/task7/task7.14/20261021-claude-review-r2.md)|
|TASK7.14-REVIEW-R1-20261020|Claude（claude-opus-5-5）|done（2026-10-20T22:30–22:50；重跑46 passed；core.py对照L.0/L.3/D13–D20/N2/N4–N6无语义偏差；用户按推荐确定P1–P7（SRC-0425）；指出推演重复观测等性能风险；第二轮派发提示已写，由用户派发）|[日志](agent_logs/task7/task7.14/20261020-claude-review-r1.md) · [复核](tasks/task7/task7.14/RESULTS.md) · [派发提示](agent_logs/task7/task7.14/20261020-claude-codex-dispatch.md) · [SRC-0425](SOURCES.md#src-0425)|
|PROJECT-PROGRESS-AUDIT-20261020|Claude（claude-opus-5-5）|done（2026-10-20T21:25–21:40；进度审核；用户确认G1–G3（SRC-0421）、关闭task6.5（SRC-0422）；task7.6复核done；更正PROGRESS/PLAN/task7 TASK与PROCEDURE过时状态；只读核查与写文档）|[日志](agent_logs/project/20261020-claude-progress-audit.md)|
|TASK7-SPEC-FREEZE-REVIEW-20261020|Codex|done（交付复核意见；2026-10-20T20:33:37+08:00开始，20:44:08交付；18项：13必须改、5建议改；含上轮14项、一致性表26行与实现前接口缺口；仅本行和日志，未运行程序）|[日志](agent_logs/task7/20261020-codex-spec-freeze-review.md)|
|TASK7-SPEC-REVIEW3-20261020|Codex|done（2026-10-20T20:24:39+08:00开始，20:34:45交付；第三轮规格复核14项：8必须改、6建议改，含第二轮逐项核对；只写本行与日志，未运行程序）|[日志](agent_logs/task7/20261020-codex-spec-review3.md)|
|TASK7-BUDGET-ESTIMATE-20261020|Codex|done（交付推算；2026-10-20T20:24:37+08:00开始，20:34:35交付；输入/假设、L与冻结验收、G1–G7、两变体全局/worker参数表及有界核查清单；纳入收尾N1的DLS回退补算；未选预算、未运行实验，仅本行/日志/新增来源）|[日志](agent_logs/task7/20261020-codex-budget-estimate.md) · [SRC-0418](SOURCES.md#src-0418)|
|TASK7-REVIEW3-BUDGET-DISPATCH-20261020|Claude（claude-opus-5-5）|done（2026-10-20约20:20；写好两份Codex派发提示：A第三轮复核（D13–D20、忠于原项目、task7.10草案v1）、B阶段L与各组成本静态推算（供U15）；由用户派发，Claude未启动）|[派发提示](agent_logs/task7/20261020-claude-codex-dispatch-review3-budget.md)|
|TASK7-LOWER-SPEC-REVIEW-20261020|Codex|done（2026-10-20T17:06:01+08:00开始，17:13:19交付；D1–D12及上轮处理复核，14项意见：11必须改、3建议改；仅独立日志与本行，未运行程序）|[日志](agent_logs/task7/task7.13/20261020-codex-lower-spec-review.md)|
|TASK7.13-CBL-AUDIT-20261020|Codex|done（2026-10-20 Claude抽查复核采用，见task7.13 RESULTS；原记录：review（2026-10-20T16:26:04+08:00开始，16:37:42交付；CBL动作/时序IK/观测/奖励/实际SAC链路五项静态核查，含SRC-0401补充，待Claude复核；仅文档）|[日志](agent_logs/task7/task7.13/20261020-codex-cbl-audit.md) · [结果](tasks/task7/task7.13/RESULTS.md) · [SRC-0402–0406](SOURCES.md#src-0402)|
|TASK7-LOWER-SAC-REVIEW-20261020|Codex|done（2026-10-20T16:25:56+08:00开始，16:32:38交付；按SRC-0401及用户补充复核三维下层SAC，14项意见：9必须改、5建议改；仅独立日志与本行）|[日志](agent_logs/task7/20261020-codex-lower-sac-review.md)|
|TASK7.14-SETUP-20261020|Claude（claude-opus-5-5）|done（2026-10-20T21:03起；task7.14三文档、实现合同与Codex实施提示已写；G1–G3于21:35确认（SRC-0421）；只写文档）|[日志](agent_logs/task7/task7.14/20261020-claude-envcore-setup.md) · [派发提示](agent_logs/task7/task7.14/20261020-claude-codex-dispatch.md)|
|TASK7-SPEC-FREEZE-FIXES-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:49–20:55；B类5项登记SRC-0418；A类纠错与整合写入task7.13（L.0统一流程、f_k v1）、7.10（路由表、温度loss）、7.11（数据合同、触发谓词）、7.5（IK合同）、7.4、父TASK一致性表（#27、#28新增）与SOURCES更正；C类延后；只写文档）|[日志](agent_logs/task7/20261020-claude-spec-freeze-review-assessment.md#处理)|
|TASK7-SPEC-FREEZE-REVIEW-ASSESS-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:44；审核Codex第三轮18项：抽查6项源码均属实；分A类Claude直接修正、B类5项需用户决定、C类延后；只读与记录）|[日志](agent_logs/task7/20261020-claude-spec-freeze-review-assessment.md)|
|TASK7-SPEC-FREEZE-REVIEW-DISPATCH-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:32；写好Codex第三轮整体复核提示，由用户派发，Claude未启动）|[派发提示](agent_logs/task7/20261020-claude-codex-dispatch-review3.md)|
|TASK7-NUMBERS-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:25–20:32；N1–N12推荐写入task7.4 RESULTS（SRC-0416），用户“按照你的推荐”确定（SRC-0417），回写父TASK U15/§2.2/一致性表#8、task7.5 B.R、7.7 S1–S5、7.8 V4/V5、7.13 L.3；只写文档）|[task7.4 RESULTS](tasks/task7/task7.4/RESULTS.md)|
|TASK7.11-SPEC-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:11–20:18；核对SC²-WM预测损失与适应代码（SRC-0414），f_p训练方案v1；用户“忠于原项目”：F1–F9按忠于原项目选项确定、F7(b)、ψ保持代码形式（SRC-0415），回写父TASK与task7.4；只写文档）|[日志](agent_logs/task7/task7.11/20261020-claude-fp-spec.md)|
|TASK7.10-SPEC-20261020|Claude（claude-opus-5-5）|done（2026-10-20T20:06起；T1–T9已由用户确定（SRC-0413）并回写；核对SC²-WM打分结构（SRC-0412），task7.10上层离散SAC与偏置层规格草案v1写入RESULTS，T1–T9待用户确认；只写文档）|[日志](agent_logs/task7/task7.10/20261020-claude-upper-spec.md)|
|TASK7-FAITHFUL-20261020|Claude（claude-opus-5-5）|done（2026-10-20T19:53–20:03；D13–D20确定（D17/D18/D19按原则改取CBL做法）；三个原项目＝CBL、N²M²、SC²-WM（用户确认）；一致性表#5改回CBL、#6–#11保留（SRC-0410）；只写文档）|[日志](agent_logs/task7/task7.13/20261020-claude-lower-spec-review-fixes.md#d13d20确定与忠于原项目)|
|TASK7-LOWER-SPEC-REVIEW-FIXES-20261020|Claude（claude-opus-5-5）|done（2026-10-20T19:36–19:39；D13–D20已于19:53由用户确定；处理Codex第二轮14项：文字与公式更正已改入task7.13/7.4/7.6/7.10、父TASK、SOURCES、DECISIONS；接口补充D13–D20写入task7.13 RESULTS待用户确认；只写文档）|[日志](agent_logs/task7/task7.13/20261020-claude-lower-spec-review-fixes.md)|
|TASK7-LOWER-SPEC-REVIEW-DISPATCH-20261020|Claude（claude-opus-5-5）|done（2026-10-20T17:05；写好Codex第二轮复核提示，由用户派发，Claude未启动）|[派发提示](agent_logs/task7/task7.13/20261020-claude-codex-dispatch-review2.md)|
|TASK7-LOWER-SPEC-WRITEBACK-20261020|Claude（claude-opus-5-5）|done（2026-10-20T17:01–17:04；D1–D12登记SRC-0408与DECISIONS，回写父TASK、task7.4/7.5/7.6/7.10/7.13；只写文档）|[日志](agent_logs/task7/task7.13/20261020-claude-lower-spec.md#d1d12确定后的回写)|
|TASK7.13-SPEC-20261020|Claude（claude-opus-5-5）|done（2026-10-20T16:52起；D1–D12已由用户确定（SRC-0408）；复核Codex CBL核查并采用；task7.13下层规格草案v1写入RESULTS，SRC-0407登记；D1–D12待用户确认；只写文档）|[日志](agent_logs/task7/task7.13/20261020-claude-lower-spec.md)|
|TASK7-LOWER-SAC-REVIEW-FIXES-20261020|Claude（claude-opus-5-5）|done（2026-10-20T16:45–16:51；Codex两层SAC复核14项全部处理：父task7三文档、task7.4 TASK/RESULTS（文首修订节）、7.5/7.6/7.7/7.8/7.10/7.11/7.13 TASK、PLAN、DECISIONS、SRC-0400/0401更正与导航；新增待定U39与“同步上层奖励是否加时间项”；只改文档）|[日志](agent_logs/task7/20261020-claude-lower-sac-review-fixes.md)|
|TASK7-DEFAULTS-20261020|Claude（claude-opus-5-5）|done（2026-10-20；用户“都按你的推荐来”：下层3维动作、确定性执行、CBL自写SAC、下层无记忆与子目标均匀抽、task7.9 R1–R8、热力图处理写入task7文档，SRC-0401与DECISIONS登记；只写文档）|[日志](agent_logs/task7/20261020-claude-lower-sac.md#2026-10-20稍后用户按推荐确定的一批项)|
|TASK7.13-DISPATCH-20261020|Claude（claude-opus-5-5）|done（2026-10-20；写好两份Codex派发提示：A task7.13 CBL下层代码核查、B两层SAC文档复核；由用户派发，Claude未启动）|[派发提示](agent_logs/task7/task7.13/20261020-claude-codex-dispatch.md)|
|TASK7-LOWER-SAC-20261020|Claude（claude-opus-5-5）|done（2026-10-20T16:08起；用户决定两层SAC写入task7文档、新建task7.13、SRC-0400与DECISIONS登记；只写文档）|[日志](agent_logs/task7/20261020-claude-lower-sac.md)|
|PROJECT-GIT-PUSH-20261020|Codex|done（2026-10-20T15:12:00+08:00；当前文件提交2380ff5及此前42提交已推送origin/main，远程哈希一致；本条及日志作为收尾记录提交）|[记录](agent_logs/project/20261020-codex-git-push.md)|
|TASK7.6-BENCH-20261020|Codex|done（21:35 Claude复核通过；原：2026-10-20T14:46:35.571249+08:00交付；r1–r9有界基准、原件125项重算、清理/预算核查；非环境实施，待Claude/用户复核）|[日志](agent_logs/task7/task7.6/20261020-codex-ik-bench.md) · [结果](tasks/task7/task7.6/RESULTS.md) · [SRC-0399](SOURCES.md#src-0399)|
|TASK7-SECOND-REVIEW-A-20261019|Codex|done（2026-10-19T23:40:47+08:00开始；2026-10-19T23:54:56+08:00交付17项第二轮建议；仅只读核查与文档）|[记录](agent_logs/task7/20261019-codex-review-evidence.md)|
|TASK7-EVIDENCE-B-20261019|Codex|done（2026-10-20 Claude已采纳并写入task7文档，见[日志](agent_logs/task7/20261020-claude-second-review-fixes.md)；原记录：2026-10-19T23:40:47+08:00开始；2026-10-19T23:54:56+08:00八项核查/替换建议与SRC-0382–0390已交付；物理TCP等价未证实、R2D2原文未取得，官方代码已核）|[记录](agent_logs/task7/20261019-codex-review-evidence.md)|
|TASK7.6-DISPATCH-20261020|Claude（claude-opus-5-5）|done（Codex已交付，task7.6 done；原：2026-10-20 14:00起；task7.6派发提示已写、SRC-0398已登记；codex exec由用户启动（PID 1480576），Codex执行中；Claude不执行基准）|[派发日志](agent_logs/task7/task7.6/20261020-claude-codex-dispatch.md)|
|TASK7.9-RULE-SPEC-20261020|Claude（claude-opus-5-5）|done（R1–R8已由用户确定，SRC-0401；原：2026-10-20T12:15–12:20+08:00；task7.9规则版规格(A)、改造方案(B)、子目标环暂缓条件(C)草案v1已写入三文档，来源SRC-0395–0397；R1–R8待用户确认；只写文档）|[日志](agent_logs/task7/task7.9/20261020-claude-rule-spec.md)|
|TASK5.5-FINAL-SIM-REVIEW-20261020|Claude（claude-opus-5-5）|done（2026-10-20T12:02–12:06+08:00；原件哈希、逐回合重算与F0同口径对照全部通过，task5.5标done，PLAN过时行已更正；只读结果、只写文档）|[日志](agent_logs/task5/task5.5/20261020-claude-final-sim-review.md)|
|TASK5.5-FINAL-SIM-RESULTS-20261020|Codex|done（2026-10-20T11:48:37+08:00开始；2026-10-20T11:55:08+08:00核对入账完成；task5.5为review待Claude/用户复核；仅文档，[SRC-0394](SOURCES.md#src-0394)）|[记录](agent_logs/task5/task5.5/20261020-codex-final-sim-results.md)|
|TASK5.5-FINAL-SIM-EVAL-20261019|Codex|done（10-19 22:52评估及实例清理结束；10-20本次结果入账，task5.5为review；[SRC-0394](SOURCES.md#src-0394)）|[记录](agent_logs/task5/task5.5/20261019-codex-final-sim-eval.md)|
|TASK5-CBL-STATUS-20261019|Codex|done（2026-10-19 22:40 +0800开始；已核对：5.2原版RLlib已评估，5.5自写SAC最终sim评估未执行；未启动实验）|[记录](agent_logs/task5/20261019-codex-cbl-status.md)|
|TASK7-STATUS-CHECK-20261019|Codex|done（2026-10-19 22:40–22:41 +0800；现状核查与汇总；未实施，未运行实验）|[记录](agent_logs/task7/20261019-codex-status-check.md)|
|TASK6.2-SAMPLER-STOP-20261020|Claude（claude-opus-5-5）|done（2026-10-20 13:19–13:22；按用户指示核实t6.2-stress-r2遗留CPU采样器无人使用后只停该进程（宿主PID 2994901），输出文件保留，容器未动）|[日志](agent_logs/task6/task6.2/20261020-claude-stop-stress-r2-sampler.md)|
|TASK5.5-DISPATCH-PROMPT-20261020|Claude（claude-opus-5-5）|done（2026-10-20；写好给Codex的派发提示：task5.5最终sim评估结果入账、PROGRESS更新、与F0同口径对照；Claude未派发，待用户转交）|[派发提示](agent_logs/task5/task5.5/20261020-claude-codex-dispatch-prompt.md)|
|TASK7-SECOND-REVIEW-FIXES-20261020|Claude（claude-opus-5-5）|done（2026-10-20 11:17–11:21改文档，11:32写入用户对距离锚点、终点姿态、风险特征定义的决定SRC-0393；只写文档）|[日志](agent_logs/task7/20261020-claude-second-review-fixes.md)|
|TASK7.4-CONTRACT-GAPS-20261020|Claude（claude-opus-5-5）|done（2026-10-20 11:10–11:12；用户决定合同缺口7–11按Claude推荐，写入task7.4/7.5/7.8/父TASK/DECISIONS并登记来源；只写文档）|[日志](agent_logs/task7/task7.4/20261020-claude-contract-gaps.md)|
|TASK7-CODEX-REPLY-ENVSPEC-20261019|Claude（claude-opus-5-5）|done（B1–B14已由用户确定，SRC-0377/0378/0381；原：2026-10-19 21:40–21:51；Codex 7条意见的措辞修订完成；task7.5(B)规格草案v1已写，B1–B14待用户确认；只写文档）|[日志](agent_logs/task7/20261019-claude-codex-reply-and-env-spec.md)|
|TASK7-CODEX-SUPERVISION-20261019|Claude（claude-opus-5-5）|done（2026-10-19 21:21–21:30只读核查task7.5(A)与7.1–7.3收尾；2026-10-20复查：task5.5最终sim评估10-19 22:52已结束rc=0、内部成功32/33/30（/50），但结果未入账、PROGRESS未更新；Codex第二轮17项待Claude处理；10-20 13:20复查：Codex task5.5入账11:55完成、数字与哈希经抽查一致，已由Claude复核标done）|[记录](agent_logs/task7/20261019-claude-codex-supervision.md)|
|TASK7.5-A-REUSE-AUDIT-20261019|Codex|done（2026-10-19 20:55–21:15 +0800；a–g静态复用审计、SRC-0365–0371、文档核对完成；(B)未写，未运行程序）|[记录](agent_logs/task7/task7.5/20261019-codex-reuse-audit.md)|
|TASK7.1-7.3-CLOSEOUT-20261019|Codex|done（2026-10-19 20:55–21:15 +0800；SRC-0341–0355补登、父抽查、日志与新框架适用性收尾；仅文档验收）|[记录](agent_logs/task7/20261019-codex-research-closeout.md)|
|PROJECT-MAPGEN-AGENTS-20261016|Codex|done（新增mapgen/AGENTS.md；静态文档检查通过，入口因宿主缺numpy未运行成功）|[记录](agent_logs/project/20261016-codex-mapgen-agents.md)|
|PROJECT-WM-RL-LITERATURE-20261014|Codex|review|[文献笔记](agent_logs/project/20261014-codex-wm-rl-literature.md)|
|PROJECT-SC2WM-SENSORS-20261016|Codex|done（2026-10-16 15:15 +08:00开始；平台与传感器只读核查）|[记录](agent_logs/project/20261016-codex-scwm-sensors.md)|
|PROJECT-SC2WM-READING-20261016|Codex|done|[阅读笔记](agent_logs/project/20261016-codex-sc2wm-reading.md)|
|CBL-ARCHIVE-AUDIT-20261016|Claude|done（只读核查与复核）|[核查](agent_logs/project/20261016-claude-cbl-archive-audit.md) · [复核](agent_logs/project/20261016-claude-cbl-archive-recheck.md)|
|DOC-CLEANUP-20261016|Claude（claude-opus-5-5）|done|[日志](agent_logs/project/20261016-claude-doc-cleanup.md)|
|MAPGEN-REQ-20261016|Claude（claude-opus-5-5）|done（需求文档交付；地图未生成）|[需求文档](../../mapgen/docs/husky_ur5_map_requirements.md) · [task7 RESULTS](tasks/task7/RESULTS.md)|
|DOC-FIX-20261019|Claude（claude-opus-5-5）|done|[日志](agent_logs/project/20261019-claude-doc-fix.md)|
|TASK7-CLAUDE-CODEX-SYNC-20261019|Claude（claude-opus-5-5）|done（Codex已于21:15回复7条意见与Q4；另一Claude会话21:40–21:51已按意见修订措辞）|[记录](agent_logs/task7/20261019-claude-codex-sync.md)|
|TASK7-FRAMEWORK-DOCS-20261019|Claude（claude-opus-5-5）|done（2026-10-19 19:03–19:35；框架写入与task7.4–7.12三文档，未派发未运行）|[日志](agent_logs/task7/20261019-claude-framework-docs.md)|
|TASK7.4-TASKDEF-20261019|Claude（claude-opus-5-5）|done（草案已交付，后续数值由N1–N12定，SRC-0417；原：2026-10-19 19:45开始；任务定义、接口表与经验池字段草案v1已写；数值E1–E9与接口问题I1–I5待定）|[日志](agent_logs/task7/task7.4/20261019-claude-task-definition.md) · [task7.4](tasks/task7/task7.4/TASK.md)|
|TASK7.7-MAPGEN-REQ-20261019|Claude（claude-opus-5-5）|done（2026-10-19；mapgen需求改为只生成长方体、每档验证50/测试100、B类不做；未生成地图）|[日志](agent_logs/task7/task7.7/20261019-claude-mapgen-req-update.md) · [需求文档](../../mapgen/docs/husky_ur5_map_requirements.md)|
|TASK7.7-OBS-20261019|Claude（claude-opus-5-5）|done（2026-10-19；全景深度、128×128×2局部栅格、所有障碍挡底盘已定；S1–S5待定）|[日志](agent_logs/task7/task7.7/20261019-claude-scan-design.md) · [task7.7 RESULTS](tasks/task7/task7.7/RESULTS.md)|
|TASK7.8-VCM-20261019|Claude（claude-opus-5-5）|done（2026-10-19；VCM方案V1–V3已定，V4网络尺寸、V5是否单独检验待定）|[日志](agent_logs/task7/task7.8/20261019-claude-vcm-design.md) · [task7.8 RESULTS](tasks/task7/task7.8/RESULTS.md)|
|TASK7.5-B-ITEMS-20261019|Claude（claude-opus-5-5）|done（2026-10-19 22:35起；B2、B3（SRC-0377）、B11（SRC-0378）、B1/B4–B10/B12–B14与地图大小（SRC-0381）已定；B8/B9/B13/B14与各数值交task7.6）|[日志](agent_logs/task7/task7.5/20261019-claude-b-items.md)|

|TASK7-DESIGN-REVIEW-20261019|Codex|done（2026-10-19 09:54 +0800开始；整体实验设计文档审查完成，未实施）|[记录](agent_logs/task7/20261019-codex-design-review.md)|

|TASK7-SEQUENCE-RESEARCH-20261019|Codex（父；上午3个调研子Agent，本次未再委派）|done（2026-10-19 10:04开始，21:15收尾；task7.1–7.3来源登记/父抽查/新框架适用性完成；仅调研文档）|[记录](agent_logs/task7/20261019-codex-sequence-design.md)；本次[收尾](agent_logs/task7/20261019-codex-research-closeout.md)|
|TASK7-CLAUDE-DISCUSSION-20261019|Claude（claude-opus-5-5）|done（仅讨论与只读核查；未重复派子Agent）|[记录](agent_logs/task7/20261019-claude-design-discussion.md)|

|PROJECT-N2M-READING-20261019|Codex|done（2026-10-19 16:47 +0800开始；原文核查与来源登记完成，未实施）|[记录](agent_logs/project/20261019-codex-n2m-pose-preference.md)|

## 容器

`forem-dev`（task5.5训练已结束，10-19无训练进程）；task5/6另有上游与Husky原版容器，使用前先核实状态，不停止未经核实的进程。

|PROJECT-REPORT-ROBOT-20261022|Codex（实际模型/强度未知）|done（2026-10-22T18:47:58+08:00；只读核对机器人选型与控制接口，为整体汇报整理；无实现/实验改动）|[记录](agent_logs/project/20261022-codex-report-robot.md)|

|PROJECT-REPORT-FRAMEWORK-20261022|Codex（实际模型/强度未知）|done（2026-10-22T19:01:34+08:00；参照SC²-WM Fig.2重绘整体框架，PNG目视核对，交付PNG/SVG/PDF；未改变设计或实验）|[记录](agent_logs/project/20261022-codex-report-robot.md)|

|PROJECT-REPORT-FRAMEWORK-V2-20261022|Codex（实际模型/强度未知）|done（用户确认现行机制；突出下层推演、上层选点与下层执行，交付宋体风格PNG/SVG/PDF，已目视检查）|[记录](agent_logs/project/20261022-codex-report-robot.md)|

2026-10-26 task8.8 r3最终收尾：独立总验收FAIL/blocked；原账本402.465809844434/900s、余497.534190155566s、active空，403链接/hash/来源/现场末检通过。无遗留验证、容器仅保活、GPU compute空。用户明确无命中长弦与量程边界豁免关系或资产处理前，不续图、不生成地图、不训练；8.7不关闭。[SRC-1068](SOURCES.md#src-1068)。

2026-11-02 14:24 +08 · SAC-SPLIT · Codex · active · 固定现有下层推理基线，建立两个本地分支和文档计划。[交接](agent_logs/project/20261102-codex-sac-split.md)

2026-11-02 · SAC-SPLIT · Codex · done（本地分线和首版计划）；task10 review 待派发。[TASK](tasks/task10/TASK.md) · [PROCEDURE](tasks/task10/PROCEDURE.md) · [RESULTS](tasks/task10/RESULTS.md) · [日志](agent_logs/task10/20261102-codex-plan.md)。

2026-11-02：先 [task10 上层 SAC](tasks/task10/TASK.md)，再 [task11 世界模型](tasks/task11/TASK.md)。以[最新分期](SOURCES.md#src-1360)取代旧合并草案。 Codex · 分期文档 done，task10 待细化评审，task11 待基线。[记录](agent_logs/project/20261102-codex-task10-task11-scope.md)。

2026-11-02 15:01 +08 · T10-SAC-DESIGN · Codex · active · 上层协议与派发交接。[记录](agent_logs/task10/20261102-codex-sac-design.md)

2026-11-02 · T10-SAC-DESIGN · Codex · done（设计交付）；task10 实施待派发，正式运行待预算。[交接](tasks/task10/RESULTS.md)
