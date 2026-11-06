# TASK7.18-STAGE-L-20261021

负责人：Codex。实际模型 GPT6.1sol，推理 high（宿主 PID2530514 的 codex exec argv 已核实）。推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high；SAC数值与跨模块性能需逐项核验。

## 授权与边界

用户授权见 task7.18 TASK 派发参数 / SRC-0901、SRC-0431；两变体各1种子×5M，正式训练前容器计算≤4小时。仅新 task7_lower 包及测试、专用脚本、lower_train.json、DLS性能修改；本任务三文档/日志，PROGRESS本行，SOURCES0470–0479。其他模拟模块只读，禁止修改 lower_policy.py；不启停容器、不提交Git、不停止他人进程、GPU0/1禁用；开发核查GPU2。

## 开工核查

- PROGRESS task7.15、7.16、7.17 均done；7.17 Claude r2 全目录153通过（历史RESULTS首行待决定已由末节复核替代）。
- 宿主时钟2026-10-21 14:22，派发文本14:45与宿主有差异，实际时间按命令记录，不改系统时钟。
- main分支；已有多份并行文档及task7_sim未提交改动，完整git status已读，保留。
- forem-dev Up 2 weeks；GPU2仅Xorg 4MiB，无compute；GPU0/1/3保留其他任务。/home 19TB空闲。
- 7.17真实池GPU2基线：E16/64/256纯step25.9/94.8/274.1转移/s，E256约911ms，约6%IK走DLS。仅历史基线，非本轮测量。来源 SRC-0468/0469、task7.17 RESULTS末节。
- CBL参考 forem/scripts/scwm_sac.py 最后来源commit2380ff51c31ac30fc8506ac2dbac5c6cad24d42a，SHA256 06e6335cee2ad1dbaa63928942c6eb6aecbf9cec0bc904fa4bc834e3870e08d1。

## 计划（尚未执行）

先写量化、SAC与回放/恢复测试；实现新地图编码器、观察向量、SAC；核查DLS语义等价优化。真实池E扩展分项核查与两变体试训，推算5M≤48h才启动正式训练。检查点/评估/恢复接口将落RESULTS。

## 待决定

当前无。规格缺失时只停相关部分，记录位置和选项，不自行补科学阈值。

## 14:30 实现与首轮核查

- RED缺模块退出2；基础GREEN6 passed（5.37s）；加入完整环境/回放恢复与诊断消费等价后8 passed（8.55s）。原SAC更新方法AST提取独立对照，普通/alpha触底与下一次恢复更新所有参数逐元素相同。[SRC-0470](../../../SOURCES.md#src-0470)
- GPU update微基准15次，初次0.748s、预热后约13.7ms；参数和optimizer动量cuda:0（物理GPU2），Adam step计数CPU是torch默认，不是网络回落CPU。尚不是端到端成本。
- DLS直接CUDA Graph失败；原失败记录保留。solve_ex免主机检查＋常量缓存后n=1/3/16/65各两组所有结果字段精确相同，1 passed/8.63s，详SRC-0471。仅本任务显式启用，其他会话默认eager行为保持。
- 新包拥有网络、量化、经验池、训练/评估、完整checkpoint、测试；入口和lower_train.json。尚未正式训练；下一步真实池E扩展分项与等价、两变体各50k试训。

## 14:32 运行接口与正确性

- 完整checkpoint格式task7-lower-full-v1：policy/critic/targets、3个Adam、2个调度器、alpha开关与数值、uint8 replay与索引RNG、EpisodeEnv及分流RNG、torch/NumPy/Python/CUDA RNG、计数、待消费批转移及cursor。每250k精确消费数保存，pending保证不重复环境交互或丢转移。
- 训练consumer读取Core后消费diagnostic histories（trace/attempts/transitions）以避免地图转移永久驻留；配对测试证明后续Transition逐元素相同。科学状态与mask不修改。
- 验证独立100图（两档各50），每图固定后拒绝重抽同图，均匀规则候选、确定性tanh(mean)，恢复训练全局RNG；未作D10冻结决定。
- 训练E批开始取策略动作、有效行env id升序消费；每条在旧replay>256时先更再插，保持首更新#258及5M−257总更新。随机预热按active序号精确1000个有效动作，不按无效行计数。

14:35：全目录回归收集了并行7.19/7.20 active测试，出现两失败；限定回归至7.17 final-suite.xml列出的17个稳定模块＋本包。宿主直接SIGINT自有pytest PID2543375权限不足；核实NSpid与本run XML后经现有容器仅SIGINT自有PID2545525，保留输出，不停止其他进程。

## 精确预算边界

训练pending用于250k检查点；最终5M不足完整E批时不能额外尝试后丢样本。task7_lower.training.limited_step仅临时挂起超出预算的行，保存/恢复其所有Core/State/Grid逐行tensor（含finished/queue/visible_previous），selected行仍调用原Core；悬挂行attempted=0。新增配对测试核验selected转移精确相同、未选中完整状态与下次观测不变。其他task7_sim文件不改。

## 14:39 稳定回归与交接接口

稳定17模块回归153项通过，新测试10项通过；唯一新增失败为standalone PYTHONPATH缺旧vendored SB3路径，并非公式差异。改为AST加载原分布类（不启动ROS/Ray/gym），新增包12项全部通过，含原SB3单tanh action/log_prob逐元素一致。完整旧回归不因导入修复重跑；新增预算边界测试也通过。

检查点同时导出小文件 `*.actor.pt`（task7-lower-actor-v1）：仅Actor权重/变体/74或75维/观察版本/消费步数。`task7_lower.inference.DeterministicActor(path, device)(observation)`给task7.20直接调用，输入Core批量字典float32，输出同device `[E,3]` raw tanh(mean)，内部统一量化→解码。未创建或修改lower_policy.py。完整文件和Actor文件均临时写＋fsync＋原子替换。

## 14:54 E扩展/分项完成，试训运行中

- 六份真实池profile（E16/64/256×sync/async）全部Transition逐元素相同；E256 async吞吐277.1→580.2、sync274.3→440.7转移/s，包含首次捕获，reset101.0→43.9s /100.4→43.5s。各计数与输入列表在profile-E*-*.json（SRC-0472）。选择E256，selection.json保留选择过程；不是用微基准替代端到端。
- parts：真实E16 reset记录1792次显式host→device构造，共87064 bytes、同步wall累计.065717s；仅所拦截torch.tensor/as_tensor主机路径，不冒充全部runtime memcpy（采样index也会从主机建GPU索引）。在线图、向量、网络与经验池均GPUtensor，未新增逐步CPU地图搬运。IK/collision/render/grid/update/observation分项与1/2/4线程同输入等价见parts.json。step p50 .07128/.07374/.07137s、总3.094/2.934/3.058s，增加线程无稳定收益，保留2。
- 本包最终13项通过，lower-tests.xml；稳定原153项通过记录保留。compile直接内存编译13源通过；宿主py_compile写入root已有pycache权限失败，不是源码语法失败。
- 正式前账本已记946.87s；同步50k试训于14:48:16开始（pid文件mtime核查），之后同GPU2顺序async50k。driver宿主PID2560522，docker worker宿主PID2564347（容器PID可由docker top/proc NSpid核实），supervisor为pilot_driver.py；日志pilot-sync.log/learning.jsonl，状态、完整argv/最终退出码由commands.jsonl入账。
- 首3000转移：2743更新，loss/Q/alpha有限，alpha=.34906、Q_abs_max≈11.03。失败主要self_collision，8/575段到达；属于早期实测，不判断训练成功。G1整帧遮挡46/3004帧。不能由此断言数值健康达成/48h可行，待50k完整成本。
- 监控：`python3 forem/scripts/task7_lower_monitor.py forem/results/task7/t7.18-20261021/pilot-sync`。如需停本试训，创建该run的STOP文件，worker逐转移边界保存interrupted.pt退出；driver收到非零则不启动后续async。只限本run目录，不停止他人进程/容器。恢复用同config/variant/E256及--resume本run interrupted.pt；勿将pilot追加计入5M正式预算。

14:56代码检查：验证factory内部EpisodeSampler有独立kin，已显式启用同一已验证DLS graph，避免验证reset沿默认eager付固定成本；只改evaluate未执行路径，不改变正在运行试训的train实现/超参。验证分项将使用最终版本实测。

## 恢复布局与停止边界核查

代码检查发现torch.load(map_location=cuda)也会搬动非capturable Adam的CPU step计数，已在load_checkpoint后按原Adam布局移回CPU，动量留GPU；SAC复制更新方法不改。另在外层环境步前检查STOP，避免验证结束后才在下一批消费中发现停止。两处仅恢复/停止路径，不改变正在运行试训的正常训练计算；实际GPU续算与最终新代码测试在finish核查执行。精确试训开始时间为14:48:16（此前“约14:52”已纠正），原始时间一律以commands/pid文件为准。

试训曲线与健康口径登记[SRC-0473](../../../SOURCES.md#src-0473)，中间47000步快照仍不是训练效果验收。此前3000步等中间数字保留原日志；精确命令时间以PID/commands为准。

## 15:12 交接metadata相容性核查

只读task7.20 lower_policy.py发现其正式loader要求action_version且小文件loader要求versions/step；已在本任务保存格式补`lower-action-l1-d8-v1`及显式versions与step alias（steps同值）。动作、权重、预处理均不改；未编辑task7.20文件。历史pilot final文件不回写，finish核查另导出compatible.actor.pt并逐Tensor核对权重相同。新增只读调用task7.20两种loader的测试，待GPU2当前试训结束后执行；正式保存格式包含全部metadata。

2026-10-21T15:14:57.015279+08:00：同步50000/49743完成退出0，最终full保存58.245s，实际源码/数据结果见SRC-0473补记。async已接续，仍GPU2，初期21000步loss/Q/alpha有限。finish-driver PID2571063等待async summary；正式尚未启动。

## 15:29 GPU恢复严格测试失败与定位

finish-sync / resume_diagnose严格比较post-update所有权重hash失败；action/loss/replay RNG/环境转移全部字段精确相同。独立AST调用原CBL更新重复重现卷积权重差，最大7.45e−9，71个元素；没有新增epsilon或打开deterministic。详SRC-0474，保留红日志与resume-comparison-sync-r2-failed.json。严格GPU后续轨迹逐位恢复**未通过**，不能写成通过；完整初始SAC状态hash与动作/采样/物理精确恢复继续检查（不同于不必要的GPU浮点轨迹保证）。不改正常训练科学条件；finish-driver-v2宿主PID2607095接续独立IO与验证，仍GPU2、4h账本内。原CPU更新/恢复与DLS精确对照通过结论不变。

2026-10-21T15:40:42.381214+08:00：完整恢复初始SAC状态hash/action/loss/sample RNG/环境转移精确相同；严格post-GPU权重仍False并保留限制。sync验证100图116.18s、497段、到达率.038229。10万完整池13.274GB full save94.099s/load15.020s。async验证仍在运行（GPU2 PID2611825），没有挂起或停掉；task7.19已review收尾、codex PID退出、GPU3无compute，满足之后async用GPU3的执行结束条件（非代其复核/冻结）。

## 续接 2026-10-21T16:54:54.210062+08:00

负责人Codex，实际GPT6.1sol/high（当前codex exec PID2695454 argv核实）。前置7.15/16/17均done；main和已有他人改动保留。forem-dev运行中不启停；GPU2/3无compute，其他会话PID2695455/6仍在工作不干预；宿主19TB空闲。两50k summary/final/compatible actor、finish-sync/async、100图验证和IO产物均在磁盘，原driver已结束。PROGRESS仅本行由paused恢复active。按最新派发，GPU恢复允许权重最大差≤1e−6，其余完整状态/RNG、转移/loss逐元素相同；保留严格hash失败历史，不打开deterministic。下一步补容差实测、最终所有新增测试、账本与墙钟推算；≤48h后同步GPU2/异步GPU3正式启动。此前已验证部分不重跑。

## 2026-10-21T16:57:35.776643+08:00 恢复与最终启动核查

两变体按新批准恢复口径均通过，sync最大权重差1.4901161193847656e−8、async7.450580596923828e−9，初始SAC状态hash/action/loss/replay RNG/环境转移精确相同；strict hash均False保留。新产物resume-accepted-{sync,async}.json，两个命令退出0；未打开deterministic。最终新增测试/曲线导出执行中，旧153稳定回归沿用。配置默认E从64写为已测选择256（两试训原本均E256，不变科学条件）。历史finish两份报告、满池IO、ledger-probe均已读，计入旧账本4077.632s＋初始保守60s，余量足够。按两试训实际wall扣单次final保存后×100，加21次满池/全地图cache保存估算、20次100图验证、持久账本成本，sync31.02h/async29.22h。该推算不是工期保证，后续策略改变失败/超时/reset分布会改变成本。准备生成可审阅gate/版本快照并在GPU2/3各启动正式5M（从头，不将pilot计入正式预算）。

## 正式启动与交接 2026-10-21T17:04:32.708447+08:00

新launcher scripts/task7_lower_launch.py只操作既有forem-dev，强制sync GPU2/async GPU3、目标run不存在及目标GPU无compute；正式两命令退出0，启动时刻16:59:17+08。sync宿主supervisor2704925/worker2704934（容器2546630/2546636），async2704971/2704977（容器2546637/2546643）；sg宿主2704891/2704936。两者各从头5M seed4718/E256，初始核查sync 12000、async 15000转移，无Traceback/退出，loss/Q/alpha有限。启动快照startup-verification.json；formal-gate/source-manifest-formal与完整源码快照已保存。完整results/启动argv/PID/停止恢复说明写RESULTS文末；PROGRESS本行active训练中。

最终本包15项通过，旧稳定153通过不重做。预正式总账本＋初始60s预留4224.835s<4h。SOURCES仅本任务0474补记与0475/0476，保留旧严格hash失败；恢复单次差sync1.49e−8/async7.45e−9均≤1e−6，训练开关不改。曲线PNG/SVG/CSV生成退出0，formal门估31.02/29.22h，不保证实际工期。其他会话改G1/G7/D10及测试，不在本任务导入链，不干预；实际训练依赖文件与快照相同。收尾生成证据曾因共享只读d10_eval也变更触发“未知源码变更”保护assert而退出1，未改训练/文档；只读核实属非训练导入链后归入并行文件，重做证据采集成功。

当前负责人Codex；交接范围是已启动训练的持续监控，未完成训练/冻结。下一步按每250k full+100图验证查数值/资源/实际成本；到5M/4999743并final/summary/末验证齐全后汇总、PROGRESS改review交Claude。监控：python3 forem/scripts/task7_lower_monitor.py forem/results/task7/t7.18-20261021/formal-{sync,async}（分别查看）。STOP仅本run，graceful保存interrupted再退出；恢复先查无旧进程/GPU空闲/账本覆盖、同GPU/config/版本重启原supervisor，见RESULTS。若崩溃状态不覆盖账本，不允许重复交互回退，停报人工处置。未提交Git、未启停容器、未停止其他进程、未用GPU0/1、未作D10。

## 重训续接 2026-10-21T23:27:08.912101+08:00 — run-id t7.18-v3-20261021

实际GPT6.1sol/high，宿主codex exec PID3182687 argv核实。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high：需核对并行Core路径逐元素等价及新几何数值/成本。用户授权原文logs/task7/codex-dispatch-stageL-retrain/prompt.txt；依据SRC-0477（本轮待补实测）。仅本任务日志/RESULTS/PROGRESS本行/SOURCES0476–0479及必要运行产物；不改任何生产源码或科学条件、task7_sim几何，不提交、不停止他人进程。

开工：task7.18.2 PROGRESS done，Claude 23:30复验35通过；生产schema4，geometry_version=selfcoll-multisphere-v4-spherepairs-20261021，SHA256 6c41120ad85bdea61a24b1089e825febf4f6b62eb93da0474e51f386167b084a。GPU2/3无compute，GPU1他人Python保留；forem-dev运行两周不启停，/home余19TB，main既有改动保留。全部sim/lower源码、task7配置及lower脚本哈希/快照见results/task7/t7.18-v3-20261021/source-manifest-preflight.json与logs/task7/t7.18-v3-20261021/source_snapshot。

计划尚未执行：同输入比较原Core＋已授权新几何q传递与当前Core默认阶段L路径（E256两变体），DecisionEnv静态导入链核查；两变体各≤50k全新试训，数值/分类/新100图验证成本，再推算≤48h才启动新formal-v3目录。旧formal/checkpoint/interrupted均不用于初始化或续训。沿原4h预正式预算，历史4224.835326s计入，新命令累计登记commands.jsonl；两GPU并行容器wall按累计worker核算。

新核查core-equivalence首轮退出1：诊断脚本把刚构造Core的零sensor_frames与已reset渲染过的Core比较，时点不同；不是生产语义不等价证据。按systematic-debugging定位具体字段，改为两端都重新构造再比较；原脚本/失败日志保留。未改生产源码，r1正在GPU2执行。宿主实际开工23:27，派发/Claude文档23:30为其记录时间；不改时钟。

本轮有界检查选择每变体25000转移（用户上限50000内，停止点为执行预算，不改变5M调度/1000预热/每转移1更新等配置）；与旧50k试训learning.jsonl的25000同预算快照比较，同时列旧50k终点作历史。理由：既有SAC实现/恢复已核验，本轮针对几何替换与路径核查；25000含24743实际更新，并完整覆盖reset/candidate/环境/采样/update/log/最终IO。数值诊断每1000沿原协议，不把两几何策略分布的差异称因果隔离效果。准备的pilot_driver严格只做两新试训＋两次100图验证，尚未启动，顺序GPU2遵守原开发资源约定；正式时才分别GPU2/3。

r1退出1定位candidate.search_wall_seconds：实际性能计时不可能相同，不是候选数值字段；精确比较仅排除此明确wall诊断键，其余候选字段、全部观测/转移与Core tensor仍要求torch.equal，不设容差。原脚本/日志保留，r2运行中。两次失败均计预算，无生产修改。

2026-10-21T23:34:17.162342+08:00：r2退出0/145.620s；两变体E256各12步，共sync3055/async3071转移，全部观测、确定性Actor输出、Transition各字段、Core tensor逐元素相同。构造器同输入比较也通过；仅排除性能计时键。DecisionEnv动态未导入，静态递归导入链也不涉及。下层全部生产源码与旧formal字节相同；原配置仅几何元数据4键新增。证据core-equivalence.json、stage-l-import-and-config-audit.json，SRC-0477追加。现在启动有界driver宿主PID3190436，顺序GPU2各25k＋100图验证＋新几何满池IO测量；日志logs/task7/t7.18-v3-20261021/pilot-driver.host.log、commands.jsonl；正式尚未启动。

pilot-driver首次启动在任何容器计算前被哈希保护拒绝：并行task7.22改upper_train.json（不在阶段L加载路径）。核查实际依赖集合完全未变，改保护为全部下层递归依赖＋lower入口/配置/model/几何；全目录变化仍记录而非忽略。原driver/失败日志保留；新driver宿主PID3191241，pilot尚无任何重复或续训。RESULTS先前PID3190436是失败历史，以新PID为当前。

2026-10-21T23:49:47.409026+08:00 中间交接：同步有界试训、满池IO与100图验证已完成（全部退出0，精确数值和命令在本轮summary/learning/io-new-geometry/pilot-validation-sync.json及commands.jsonl；最终由SRC-0478统一登记）。不同步新pilot25k-async已在同一driver内顺序接续，真实argv/PID在pilot25k-async.pid.json，未加载历史检查点；正式训练仍尚未启动。当前源依赖无变化，只有并行非阶段L upper_train.json变化已单列。尚待不同步有界试训/100图验证及总成本门；不改科学条件。

2026-10-22T00:08:28.681164+08:00：两变体新25k/24743更新及各100图验证完成退出0，SRC-0478已登记。gate推算sync30.105014h/async29.953297h，累计预正式6378.217235s＜4h。不同步验证超时率71.5762%原样记录，数值有限；不改奖励/终止/超参，不预设最终有效。现在按已授权门在新目录分别从头启动GPU2/3各5M。

## 正式新几何重训启动与交接 2026-10-22T00:10:02.336643+08:00

两变体25k/24743更新，全部25次日志loss/Q/alpha有限；新100图验证/满池IO退出0，全部命令见commands.jsonl。精确分类/验证/分项/新旧对照在pilot-comparison.json与RESULTS文末，来源SRC-0478。墙钟门sync30.1050h/async29.9533h，公式(新25k wall−final保存)×200＋21次新IO满cache估计＋20次新100图验证。累计预正式6378.217235s＜4h，含历史与失败诊断。条件外推非工期承诺/最终效果。

已用既有launcher/supervisor在新formal-v3-sync/async从头各5M；宿主supervisor/worker同步3223574/3223585、异步3223620/3223627；容器映射/完整argv/时刻/版本在startup-verification、launches、各run launch/metadata。initialized_from=null、无resume；旧formal/pilot/IO均未初始化。几何schema4/v4，环境v1；source-manifest-formal-v3及字节快照记录全部源码/配置与实际依赖哈希。启动核查sync2000、async2000步，loss/Q/alpha有限，updates=step−257，GPU2/3各自compute PID一致、无退出/Traceback，依赖未变；SRC-0479。

当前负责人Codex，交接为持续监控，非训练完成/冻结。监控python3 forem/scripts/task7_lower_monitor.py forem/results/task7/t7.18-v3-20261021/formal-v3-sync（async同理）；STOP仅对应新run、等待完整interrupted及PID退出；恢复先核对GPU空闲/旧进程退出/版本哈希/同run完整状态与动作账本，仅移除本run STOP，复用RESULTS命令。预算安全恢复被拒绝则停报，不回退交互。正式恢复尚未实际执行。剩余5M完整训练与末次验证，之后交Claude复核。风险为已知几何局限、分布/共享资源改变成本和未覆盖交互阻断自动恢复。未改生产源码/配置/几何、未提交Git、未启停容器、未停止其他进程、未占GPU0/1。按用户指令启动后结束会话，不等待长训完成。

最终核查2026-10-22T00:10:44.556628+08:00：handoff-verification.json确认全部阶段L依赖哈希不变、SRC0477/0478/0479各一条、PROGRESS训练中、两worker与supervisor存活、无STOP/退出/Traceback；当前步sync4000/async4000。不同步早期100图验证超时71.5762%及分类已显式补入RESULTS/SRC0478，不以数值有限作任务效果验收。此时按用户要求结束会话，后台正式训练继续。
