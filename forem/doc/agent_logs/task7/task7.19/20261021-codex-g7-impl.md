# TASK7.19-G7-IMPL-20261021

负责人：Codex；实际模型 gpt-6.1-sol / medium（本次 codex exec 进程参数已核查）。推荐：Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium，逐项核对路径与执行合同。

授权：用户派发及 SRC-0431/0434；只写 task7.19 TASK 文件归属、任务 RESULTS、本日志、PROGRESS 自己一行、SOURCES SRC-0480–0489。禁止训练、正式D10、容器生命周期操作、Git提交、停止其他进程。

## 开工核查

- task7.15 done（Claude r2）；task7.17 done（Claude r2，文档153 passed，尚未本次重跑）。
- GPU3 无计算进程，仅 Xorg 4MiB；forem-dev 已运行；未启停容器。
- 工作区已有大量并行改动，保留。task7.18、7.20、7.21 codex exec 并行；本任务 PID 2530515。
- 既有测试数：文档153，待 collect 与完整重跑核查。
- 准备处理：g7.py、d10_eval.py、tests/test_g7.py、tests/test_d10_eval.py；必要加法快照接口。
- 系统实际时间与派发标注时间存在差异，记录命令实际时间，不据此改变预算。

## 计划（尚未执行）

按已定 G7-1–G7-5 实现；纯评估只接收状态/路线/栅格/运动学，不接真值。快照保存完整回合及 RNG；配对完成恢复策略结束状态。容器每命令≤600秒、累计≤5400秒，仅GPU3。运行日志归 forem/logs/task7/task7.19/。

## 待决定

暂无；读规格后追加，遇不明确部分暂停对应部分。

## 进展（14:38，run-id t7.19-r1-20261021）

- 新增 g7.py/d10_eval.py 与两测试文件；未改 core.py/env.py。
- RED：red.log，模块未实现而收集失败（退出2）；green1：朝向相差2π，测试改为等价朝向比较；green2：不同批维IK q最大约1e-31差，q对照1e-12（base/s仍逐元素）；green3：10 passed（退出0，38.42s）。
- green4（退出1）：新增重规划精确s测试暴露逐次累加浮点使s未精确等于cap；改为B.9显式绝对s曲线与精确封顶端点。同步曲线锚定决策初始s与连续提交时间，重规划不重置。green5：15 passed（79.31s，退出0）；之后计时字段及同步绝对曲线表达小改仍待最终重跑。
- regression.log采集时纳入并行task7.20新增测试，当前出现2项失败，须等输出定位，不能声称原153回退。下一轮仅精确原17模块＋本任务两模块。
- 有界完整几何profile启动：forem-dev，GPU3；命令 `timeout 580 python3 -u logs/task7/task7.19/profile.input.py 1 0`；宿主工具会话见dispatch events，容器PID写profile日志首行。仅脚本策略，非正式D10。
- 监控 `tail forem/logs/task7/task7.19/profile_E1_sync0.log`；正常timeout580；如须中止只核对本日志PID后向该PID发TERM，不碰其他会话进程。

## 待决定（仅正式验收运行协议，未运行）

- G7-4要求正式前写定补充回合种子规则；本派发未给种子列表，run_episode_batch只消费外部已reset环境与显式候选RNG，不自行选正式运行种子。
- bootstrap重复数未定；summarize强制调用方显式传入次数与seed，无默认预算。当前测试100次仅测试夹具，不作为正式统计设定。

- regression最终：退出1，157 passed / 2 failed（393.85s）；两失败均为并行task7.20的test_decision_env.test_complete_decision_reward_final_before_autoreset_and_export，dt=.8与测试期待.05不符。本任务未改其文件；非原153项失败。后续固定原17模块确认。
- 完整几何profile v1 E1异步：退出0，评估11.903s，执行20.412s；配对只选原地，不能据此推算普通候选配对。原JSON/log/input已留v1副本；新profile改普通.19m候选配对。
- E4异步普通候选：退出0，评估12.522s，执行21.623s，完整配对36.550s，2次重规划；仅夹具/脚本策略，不是验证池分布或D10结果。E16异步继续，单命令timeout580。

### 待决定：G7-2全不可行中出现纯超时

- 位置：task7.19 RESULTS G7-2（全不可行按⑨）、G7-5②（计划时长超T_seg→超时），task7.5 B.9 / task7.4⑨只定义“首个失败检查点”排序。
- 冲突：纯超时没有IK/碰撞首失败点；若全部路径不可行而有纯超时路径，不能自行把超时当失败点或赋无穷优先级。
- 可选理解（未实施）：按已提交安全前段时间比较；纯超时优先于预测失败；或另定超时路径键。需用户决定，不能据本日志自动授权。
- 仅该分支停止：evaluate抛SpecificationPending，D10配对恢复开始快照后向调用者传播，不把它算物理失败/超时、不跳过样本或更换候选。其余正常路径、纯预测失败排序、配对与有界计时继续。
- 邻接并行task7.20的SRC-0491也记录G1同类缺口，本任务未修改该文件/合同。

## 进展（14:50）

- 两变体E=1/4/16完整几何夹具计时完成；所有输出见profile_E*_sync*.json/log；仅v1 E1异步配对为原地，不能混入普通候选配对推算。
- 真验证池有界计时探针运行中（real_profile.input.py，seed71901仅计时夹具，不作为正式种子列表；GPU3，timeout580，PID见real_sync0.log）。单样本不能估计G7可行比例或正式分布成本。
- 新增近退化弧测试先RED：max_substeps=2仍因完整计划步数超int64报溢出（arc_overflow_red.log，退出1）。修复仅为数值存储：完整duration用float64，超过int64的steps饱和存储，控制仅展开T_seg内；排序仍读完整duration，不新增几何阈值、不把近退化有效弧掩码。修复后需最终重跑。
- 统计与正式运行缺口、全不可行纯超时排序缺口仍保留待决定。

## 性能路径核查与必要优化（14:55）

- real_sync0：进程退出0但逻辑未完成配对，318.155s后捕获SpecificationPending；地图sparse_validation_00030、slot0；reset1.143s、生成.309s。这不是一次D10配对完成的成本。状态已由paired恢复初始快照。
- 审计发现：评估器仍为masked/done路径执行后续IK；它们的无效目标可能持续触发固定64次DLS，不能算有效路径必要成本。active_pruning_red先失败：所有调用都是14条，证明未跳过掩码/结束路径（退出1，2.37s）。
- 仅g7.py加活动行索引与冻结传感器/route子集缓存；同一活动路径的控制、s目标、上一q、N1、碰撞、评分与时间语义不变。完整trace仍按原索引scatter；未改kinematics或任何共享源码。
- 优化前g7快照：forem/logs/task7/task7.19/g7.before_active_pruning.py；必须做同输入前后语义核查、最终CPU/GPU与原153回归，之后重测计时。real_sync1当前仍是优化前已启动进程，不能把它当新版本结果。

## 固定范围回归与根因（15:03）

- final命令排除并行task7.20的两个新模块，原17模块＋本任务2模块：174 passed / 2 failed，退出1，174.59s；XML逐项核查原153全通过。
- 两个本任务失败：①零/终点测试字面量.0075略大于Route由实际坐标差得到的length，修正夹具使用route.length；不修改Core边界。②完整机器人异步CPU/GPU用时差.05s：Sa未封顶u时本应在T_base恰到s_k，却以ds>u*T_base判断补完，Python舍入导致多加1子步。按规格只在ds>.3*T_base（速率上限确实不足）时补完；这是曲线bug修复，不放宽任何测试或改变已定速度。
- 为单独验证活动行优化，保存原始before_active_pruning.py；另派生before_active_pruning_fixed_curve.py，仅应用同一Sa修复以固定动作合同。equivalence.input.py将对该控制基准与最终实现逐点比较，不能将原始旧曲线运行时间当严格同协议加速基准。
- RNG测试加强：三类numpy流、CPU torch RNG和本任务GPU RNG都主动消耗后恢复；不只比较未消耗的快照。
- owned_final重跑全部本任务测试，原153因生产改动不影响其依赖（本任务模块未被原测试导入）不重复无关测试。

## 验证通过及最终计时启动（15:07）

- owned_final：退出0，23 passed / 91.62s（g7 18、d10 5）；三类numpy＋CPU/CUDA RNG主动消耗后逐元素恢复通过。原final.xml内17原模块153/153通过；最终聚合见test_counts.json。
- Core/env哈希仍等于task7.17 source_manifest：core a05e52f21ce3e185d217c2e9d43fbe73c9c9e100f20ab73458db5ba1221c792a；env d4ace6a95be44ed0aca4e9ecb1f9b1c4fd10acf0eff59964a8ed24887930d5d9。
- active_equivalence：退出0，48.357s。控制基准已同样修Sa曲线，CPU64/GPU32×两变体，best/feasible/first_bad/failure_kind及trace活动掩码完全相同；f_k误差全0，base/s误差全0；CPU64 q误差0、GPU32异步q最大6.676e-6rad（低于既有E6 1e-3rad），同步0。此测试为有界夹具，不声称所有边界构型证明。
- 同输入计时 before→after（秒，单次）：CPU异步6.410→5.743，同步4.667→4.486；GPU异步5.057→4.975，同步6.868→6.580。实际收益小，不把历史318s与它直接比较为收益倍数。
- real_sync1旧版：退出0但逻辑未配对，238.044s捕获同一SpecificationPending；仍不是D10到达/失败/超时样本。
- 最终profile_batch_v2：单命令timeout580，forem-dev GPU3；6项E1/4/16×变体顺序，子命令/退出码/wall逐项写profile_v2_commands.json，PID见profile_batch_v2.log/各子日志。停止仅本任务timeout进程组；不触及其他会话。原始profile均保留，最终表只用v2。

## 最终掩码修复与验证（15:25）

- masked_replan_red：退出1，5.86s；已结束row1残留目标/过期T_seg参与评估，抛SpecificationPending，阻塞活动row0，证明真实缺陷。
- g7重规划与d10初始资格评估都仅取活动行；replans.indices保留回原E行的映射。执行队列时序仅更新实际尝试动作的行，未参与行的visible_previous不被其他行推进。未修改Core/env语义；原始源码在g7.before_masked_replan.py / d10.before_masked_pair.py。
- owned_masked_final：退出0，25 passed（g7 19/d10 6），110.77s，包含加强后的前10子步/真实隐藏几何改变/主动RNG消耗恢复及新增终止行不阻塞测试。无生产改动后的未核验分支（规格待决定分支除外）。
- 前一source_manifest/source_snapshot保留为*_pre_mask；最终v3计时正在用当前生产版本重跑六项，外层timeout580，仅GPU3。当前未运行正式D10或训练；此后只做文档/证据收尾，不扩大范围。

## 最终交接（15:34）

- 状态review（部分停止），交Claude复核；不是done。负责人本次Codex，实际exec配置gpt-6.1-sol/medium；推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（跨模块合同核验）。
- 交付：g7.py、d10_eval.py、两测试；无core/env修改；25自有通过、原153无回退（分次证据）。最终v3六计时均退出0，源码/依赖哈希匹配manifest。GPU3 compute查询只剩表头，无本任务计算进程留存。
- 证据：forem/results/task7/t7.19-r1-20261021/{source_manifest.json,source_snapshot,owned_masked_final.xml,profile_v3_commands.json,profile_E*_v3.json,conditional_projection_v3.json,commands.json}；过程命令/原始日志位于forem/logs/task7/task7.19；SOURCES只用0480–0483。
- 保守账本3327.7s=55.46min，含未测外层调用的60s/项余量；单条实际≤10min。E16两变体各1000可行对的夹具条件配对成本3768.811s=1.047h，p=1/满批/短候选/脚本策略，未含正式生成/复位/统计/推理，不承诺正式预算。
- 未通过/未做：全不可行含纯超时路径的排序分支SpecificationPending；真实地图旧探针因该缺口未完成配对；正式D10、最终5M检查点验证、正式地图/种子/补回合/bootstrap配置尚未执行。所有失败/RED和旧版数据保留。
- 下一步Claude先核对RESULTS/manifest/四文件及已停止分支，再请用户决定具体排序键与正式协议；正式D10另派发并核准预算，不自动开始训练或验收。
- 无Git提交、无容器启停、无参考或阶段一代码改动；无需要停止或恢复的本任务长进程。

## r2 开始 2026-10-21T17:00:37.356617+08:00

实际模型 GPT6.1sol（exec命令 gpt-6.1-sol），推理强度 medium（派发进程参数已核对）。授权：SRC-0904两项实现与CPU/GPU有条件测试；文件限g7.py、d10_eval.py、两份对应测试、新d10_protocol.json、本日志/RESULTS、PROGRESS自己行及SRC-0484–0489。不改core/env及其他任务，不训练、不正式D10、不提交、不停止他人进程。GPU3 compute PID2704977，GPU回归延期Claude复核。已读入口、进度、三文档、父TASK、ENV及r1复核；其他会话在7.18/7.20/7.21，各自文件不触碰。

### r2 中间核查

- 已移除SpecificationPending类/分支，排序category显式可行2/纯超时1/失败0；失败位置归一化，未失败1.0，U25/固定序号与mask仍保留。
- 新d10_protocol.json与读取/调度/汇总接口完成，来源SRC-0484。seed审计宿主首次因旧ROS日志latest权限失败（退出1），随后容器内只读脚本退出0、22215文本/0冲突，未提权改文件权限。
- 首轮owned_cpu：退出1，33 passed/1 failed/5 deselected，66.83s；失败为新增断言把失败位置索引误写3，应6，已改，保留原log/XML。清理已不用的旧首失败整数计数；summarize最小配对数现为必填参数，正式入口从配置读取。最终CPU重跑中：forem-dev、CUDA_VISIBLE_DEVICES空、timeout580，宿主工具会话40052，日志logs/task7/task7.19/r2/owned_cpu_final.log；不启动GPU进程。

### r2 交付 2026-10-21T17:07:32.846684+08:00

- 最终CPU退出0，34 passed/5 deselected，66.33s；5个GPU用例延期由Claude复核执行（GPU3 compute门禁），无本任务遗留计算。完整命令、日志、XML、种子审计及源码快照见RESULTS r2链接；正式D10/训练均未执行。
- 协议来源SRC-0484，原始CPU实测SRC-0485；只用了本任务预留编号。core/env SHA与r1一致。未改其他任务或提交git。
- 待办：Claude复核+GPU回归；正式D10等待task7.18最终5M检查点和独立运行预算核验；G7训练前性能优化仍未实施。本轮实现范围完成，状态review而非冻结done。推荐复核Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（跨排序/协议核查），实际本轮GPT6.1sol/medium；Claude实际待记录。
