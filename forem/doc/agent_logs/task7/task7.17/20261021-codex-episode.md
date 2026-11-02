# TASK7.17-EPISODE-20261021

## 开工核查（2026-10-21T10:05+08:00）
- 负责人Codex；实际模型/强度：未知（平台无可核验标识）。推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium：跨原代码与本项目合同核对。
- 授权SRC-0431；只改本任务TASK归属代码、三个测试、RESULTS、本日志、PROGRESS自己行、SRC-0460–0469。不训练、不启停容器、不提交、不改参考库；用户指定原地并行，不另建worktree/委派/文档复核轮次。
- main；已有共享文档与task7_sim/config未提交改动，保留；三个待建模块不存在。forem-dev仅docker-init/sleep；GPU2 UUID GPU-656ca5c1-681f-48a2-7d1f-a00824723f68，四卡14MiB/0%。
- run-id=t7.17-r1-20261021；core_before.py保存于同名results目录。容器每命令timeout600，累计≤5400s，只用CUDA_VISIBLE_DEVICES=2；无后台Python。
- PROGRESS登记暂受阻：读取发现已有无效UTF8，byte2424附近task7.15行插入正文；本任务尚未写入，随后检查“项目级记录”标题已被并行写入删除。不修其他Agent内容，待安全定位自己行后定点登记。
- 基线：forem-dev GPU2环境运行原测试，日志logs/task7/t7.17-r1-20261021/baseline.log；命令退出0，结果待读取。
- 计划：原代码核对表/来源→失败测试/实现→独立reset/G1→全套/等价/CPU64/有界计时→review交接。

## 待决定
- task7.5 RESULTS:327（B12）写高度线性；task7.17授权要求照原代码，eeplanner.py:624–637根据障碍高度抬升。仅暂停高度策略选择，其他继续。

## 10:13阶段记录
- PROGRESS已在旧记录表前定点加入自己行；随后共享文档由并行方恢复为有效UTF8与正确标题（本任务未修其他内容）。
- 已写SRC-0460和RESULTS核对表后实现。迁入/上游eeplanner差异仅两处height_preference布尔：CBL均True，上游generate_base_feasible用eval、update_weights为False；对应原参数分歧也保留，不把两者说成完全相同。
- red.log：三个模块缺失导致3 collection errors（pytest退出2）；green1.log：10 passed, 1 failed in 5.24s，失败为随机平移初态的CPU64/GPU32栅格离散差异。
- 使用systematic-debugging流程定位：precision_probe输入/输出及results/precision_probe.json；未改Core快照与当前实现、原点/随机平移两组均有相同差异。传感器valid完全一致，落点误差约3.55e-6m，但障碍平面x=-1.8m正好在0.05m格边界，两精度floor落到相邻格；原点343格、平移344格observed不同，height最大差1.597m。问题位于只读perception.py的射线落点→Grid离散，不修改，不加容差吸附，不放宽对照。GPU随机回合验收暂停，保留失败测试。
- 当前实现是显式输入的A*、插值、候选采样/初态与终点校验、分环境分用途RNG；独立Core的batch facade完成reset/begin/step，不决定未定关节/高度/代价政策。默认完整地图到任务入口尚未实现，不报告可训练验收。
- Core只加G1三计数和record_render，不改reset/begin/step语义；reset通过重建单环境Core，其他环境对象/队列/栅格/流不动。初始扫描另计sensor_frames，原render_count仅动作末渲染，语义不变。
- additional_red退出2（sample_initial尚未实现）；随后实现显式joint policy的有界初态拒绝采样。正在验证非法动作批次不应部分提交的失败测试，再加batch入口预校验。

## 10:21阶段记录
- 原73＋自有18项联合：90 passed、1 failed（完整观测CPU/GPU），38.06s；原73无回退。新增初态合法性、原后端路径对照后待最终全套。
- 发现初版自写A*与安装后端在30权重夹具的路径/成本不同；按原行为要求改为直接调用pyastar（原flags），不擅自“修正”为自写最优搜索。安装metadata指向dhonerkamp/pyastar commit4303b3d200f91016bbccbfdfc43cdc3b67fc6264；原Python wrapper已读取，远程该commit C++未取得，未把hjweide当前源码当安装版依据。routes_green：5 passed/0.82s，含30图逐元素对照。
- 非法第二行raw动作会导致第一环境先提交，action_red复现；已在整个active批次预校验动作范围/finite/device/dtype，避免输入错误造成部分提交。reset_validation_red证明非法q未被拒绝；已在reset调用完整碰撞/限位/FK/同合同IK校验，并按N1精确容差检查路线起点为实际FK。reset_validation_green：14 passed（单独留完整观测失败项未跑；不是全套通过）。
- E16/64夹具计时已执行：每回合路线0.03m、两次0.1s动作（各两子步）、真正terminated后全员reset；各两样本，无训练/阈值。该实现E1 Core串行封装，约16转移/s，不是E维GPU张量融合，性能限制明示；当前未称可供阶段L正式训练。E256计时运行中，工具session62991，命令有timeout600，日志profile_E256.log；只停本调用可用终端给该前台命令Ctrl-C/工具write_stdin，禁止停止其他进程。
- task7.16索引/地图产物已出现，尚未见最终RESULTS交付；准备对两档×三split各一张执行只读读入＋显式诊断q初态验证（不是替其验收、不决定默认q），不改地图产物。
- 实际资源快照2026-10-21T10:20:30+08:00：E256容器宿主PID2311730（python3），父timeout PID2311722；GPU compute UUID仅GPU2，1166MiB；其余卡无本任务compute。命令超600s会自行结束；必要时只对已核实本任务PID2311730发SIGTERM，不操作容器。前一阶段标题时间为近似记录时间。

## 收尾交接（2026-10-21T10:27+08:00）
- 部分交付，PROGRESS自己行→review，交Claude核验；未标done。未定高度/初始关节/障碍代价策略及完整默认任务组装仍停止，完整GPU观测验收受只读perception边界问题阻塞。
- 最终全套147项：146 passed、1 failed、1 warning/56.07s（命令58.168s，退出1）；原73全部通过、本任务20项19通过。唯一失败test_wrapper_cpu64_gpu32保留，无调宽/跳过。连续状态与奖励/mask对照单独通过；全套包含并行模块54项通过，不代其复核。
- Core仅12行G1相关新增；equivalence CPU64/GPU32各5场景（首步失败、半步失败、路线终点、零推进、120动作段超时），所有Transition/状态/计数/队列/attempts/trace/f_k逐元素相同。证据results/task7/t7.17-r1-20261021/equivalence.json、core.diff。
- E16/64/256有界计时与6张地图池读入/初态校验完成，来源SRC-0463；线程1未见收益，不改包级线程；E1 Core串行限制明确，不声称阶段L可用或性能已优化。
- 所有实际命令/退出码/日志/时长完整列入本节点RESULTS；runner累计286.865089s，早期手工调用与只读小命令保守加105s，总预算391.865089s（6.531分钟），最长84.751334s；没有90分钟预算耗尽。只GPU2，未训练/启停容器/Git提交/改参考库。
- 10:24:36收尾资源核查：forem-dev仅docker-init/sleep，无GPU compute；本任务PID/工具session均退出，无后台任务需恢复。自己的日志/产物UID/GID1004。
- 最终代码/测试7文件SHA见source_manifest.json；原pyastar后端版本/commit/二进制SHA/实际wrapper见backend-provenance.json。实际模型/强度未知；推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium。
- 接收方先读RESULTS最终节与本日志，复核XML/manifest/原始输入；解决已列待决定与对应只读模块归属后再继续完整组装，不从聊天推断未授权默认值。无新文档复核轮次，无委派。

## r2开工（2026-10-21T10:42+08:00）
- 已重读用户本轮授权、TASK E1–E5/SRC-0437、PROCEDURE、Claude复核、r1账本；r1保守391.865089s，剩余5008.134911s。推荐Codex GPT6.1sol/medium，Claude Sonnet5.5/medium；实际模型/强度未知。
- 仅归属四模块/对应测试、自己日志/RESULTS/PROGRESS行和SRC-0465–0469；不训练/启停容器/提交/改参考。main保留已有并行改动；forem-dev仅入口/sleep；GPU2 UUID656ca5c1-681f-48a2-7d1f-a00824723f68，四卡14MiB/0%。
- 保存core_r1.py/env_r1.py于results/task7/t7.17-r2-20261021。计划先失败测试：masked begin/reset、非重置行等价、E4格边界；随后原高度/代价核对与默认任务组装；最后全套/真实分布E扩展及r1/原Core对照。无委派/新复核轮次。
- 本轮Core采用E维执行，mask选中行才初始化/重新开段；保留未选中行start/timeout/queue/first/trace有效掩码。路线用终点等姿态重复padding，不改变弧长/原始节点，其他模块只读。

## r2进展（2026-10-21T11:02+08:00附近）
- E1/E2/E3默认入口已实现：固定池split抽图、CBL固定q、.05m闭格相交、原代价(.98膨胀/10000/低障碍.25/＋1)、原障碍抬升、连续TCP线段与OBB顶高度检查、底盘格心连通域＋真实IK/完整碰撞见证。参数/实际位置SRC-0465/0466。每次失败换proposal seed与map draw，无上限，全部拒绝原因计数。
- E5替换原串行封装，只有一个Core；初始化/规划允许host逐环境，step为E维GPU张量。Core新增mask begin/reset，first每行记录，route endpoint padding保留已有s/quat，trace有效位按行更新；reset只允许terminated/truncated，初次全批创建例外。
- mask_red（缺reset）、planner_red（缺高度/规划函数）、sampler_red、batch_env_red均先观察失败再实现。batch_env_green 7通过；regression1全目录146 passed/59.09s，原73不回退。
- E4强化到实际局部观测：只排除valid深度落点距格线≤1e-5m实际可能更新的格，非整图屏蔽；带外observed与uint8高度精确相同，局部裁剪索引/路线通道精确相同、其他连续字段1e-4对照。e4_observation通过，夹具30882带内落点/792影响格/692 observed差异；perception.py未改。最终统计将另保存。
- 真实train池E16探测：52提案接受16（拒绝initial22/goal12/base_connected_region1/witness1），reset7.090s；路线长度0.658–6.234m、最大110节点。8动作步26.0转移/s；实际执行DLS16/256（6.25%），终点见证DLS221/1028。仅探测不是最终性能。与r1短段q不同比较必须配同输入原Core/r1，正在补。
- 已启动完整真实分布E16异步64动作预算/2次初始reset测量，日志profile_real_E16.log，工具session17094为旧probe（已退出）；本次新session见工具记录。所有循环只是有界测量窗口，不改变episode终止；policy为固定零raw＋规则候选均匀抽取（外部rng），无训练。

## r2真实分布计时阶段（2026-10-21T11:09+08:00附近）
- E16最终：2次初始reset、64次动作预算，route0.658–6.234m；step p50=609.897ms/26.194转移s，含两次初始化/候选=19.149转移s；执行DLS127/2047有效尝试（6.20%）；窗口实际episode reset=0，不伪造reset频率。E64最终step p50=682.670ms/93.251转移s，reset p50=27.431s，执行DLS641/8190有效尝试（7.83%），实际episode reset=0。
- 重采样率：E16拒绝36/52=69.23%、E64拒绝129/193=66.84%，主要起始碰撞/终点位置约束；已向用户报告，没有设拒绝率上限或改条件。完整原因/所有样本/路线分布/版本SHA见profile_real_E16/64_async_final.json。
- E256真实分布同方法（64调用窗口、2初始化）已启动；单调用timeout600，日志profile_real_E256.log。上一E64宿主Python PID2359444已退出。停止仅本任务核实PID，不操作容器/他人程序。
- 初始reset统计是完整默认入口；r1和task7.14无该入口，后续配同一批已采样Episode分别计Core/封装开销，不拿r1短段16节点的历史数字直接当真实路线收益。连续测量中的规则候选生成时间单列、pipeline分母包含它，无网络训练。

## r2近奇异精度问题与待决定（11:24+08:00附近）
- extra_validation：3 passed/1 failed。新增真实validation池seed4617 CPU64/GPU32对照，E4带外格一致，但归一化关节某项差0.0001118427，原始关节差0.0003513642rad，超过测试沿用1e-4。未放宽、未skip、未改只读kinematics。
- precision_real退出0：同两张实际Episode，分别与task7.14原Core逐元素比较，每精度内所有Transition与q完全一致；原Core重现跨精度差。两动作TCP差最大3.52418e-6m/3.50445e-6rad，分支/status/提交一致；数据precision_real.json。判定为原求解器近伸直关节数值差，不是本轮mask引入。保留失败项，并把完整E4比较放在连续字段汇总断言前，确保带内计数仍报告。
- 待决定：task7.14 RESULTS:297沿用连续字段1e-4，TASK:49同时要求按task7.6位置/姿态量级记录；近奇异的关节向量差是否属于已接受分支精度边界，或需要所属运动学任务处理。可选A：由用户明确接受该已复现近奇异关节差，B：交运动学归属任务解决并复测。此处只停该额外精度验收，保持失败，不发起文档复核轮次，其余继续。
- E256完整真实分布：2次reset各105.598/104.760s，64调用step p50=940.451ms、265.853转移/s；含两次reset与候选59.065转移/s。789提案接受256，拒绝533（67.55%），主要initial348/goal171；witness DLS4403/17458。0自然episode reset的有限窗口，不外推稳态频率。
- 同输入对照paired_E16/E64通过：新批量和原task7.14每字段torch.equal，r1奖励差0。E64缓存任务reset新87.683ms/r1 1760.673ms；步进两样本新182.419/131.856ms、原批量159.005/131.303ms、r1串行4222.008/3714.897ms。候选首个有效非原地（与完整分布均匀候选计时分开）；所有实际IK target/DLS计数单列含无效行计算，不能用有效attempt比率代替整体求解成本。
- E256同输入对照正在执行，session30255；PID/timeout容器原命令由runner记录，单条上限600s。无训练/后台Python。

## r2选中路线存储精度修复（2026-10-21T11:26+08:00）
- masked_profile_E16自然结束2行（112转移后），选中reset706.051ms，其他状态/grid/queue精确不变；E64首次在begin遇到progress beyond route，停止该测量并定位。
- 原motion.Route.select调用构造器重算norm/cumsum/quat，在打包前后float32舍入使子路线终点略大于父length。不能改只读motion/search/candidates，也不能夹候选或加容差。归属routes.py增加PackedRoute.select原字段索引，batch_routes/replace_routes返回该子类，保持原物理路线与存储量，不改插值规则。
- route_select_red原始日志退出1/s字段不相等；route_select_green退出0，18 passed/1 known-real-precision deselected，含新同步masked reset CPU64/GPU32测试。最终仍跑全部测试，不以排除集替代。
- 重试E64误复用runner名字覆盖首次.log，已将工具返回失败转录为masked_profile_E64_attempt1_failure.txt（明确不是原始字节副本）；commands.jsonl保留首次退出码/wall，独立route_select_red原始失败日志完整。今后用v2名字保留各版。不会把重试成功覆盖为首次成功。
- 先前profile_real_*_final.json对应选择器修复前SHA，保留；现执行final_v2完整分布测量。episode/routes顶部仅同步了已定E1–E3说明，initial_targets加注释，其他生产变更只有上述select存储保真。

- 当前masked_profile_E256长命令宿主Python PID2376363，父timeout2376355（资源核查运行80s）；仅GPU2 compute764MiB，其余卡无本任务compute。监控tail masked_profile_E256.log；如需停止仅对已核实PID2376363发SIGTERM或对应session51453 Ctrl-C，超600s自行结束，禁止操作容器/他人PID。

## r2最终版本计时（2026-10-21T11:34+08:00）
- PackedRoute.select修复后最终生产SHA已存source_manifest.json/source_snapshot，Core没有再改。E16 final_v2完整入口2次reset＋64调用：25.895转移/s、reset p50=6.8157s；E64 final_v2：94.827转移/s、reset p50=26.9550s。拒绝/有效DLS计数与前版相同；旧final数据明确标历史。
- masked E64重试成功：自然结束1行、384转移后reset520.306ms；E256：自然结束1行、1536转移后reset513.025ms，未选中状态/grid/queue精确不变。单事件频率为1/384、1/1536，仅特定原地候选诊断，不能外推常规策略。
- 当前E256 final_v2长命令session88990；宿主Python PID2381577/timeout2381570，11:34:25核查已运行72s，仅GPU2 compute764MiB。监控profile_real_E256_v2.log；停止仅该PID的SIGTERM/session Ctrl-C，600s自动结束。旧E256 masked PID2376363已退出。
- 仍待：原Core五场景×两精度完整等价、最终全套JUnit、当前版本配对与最终账本/来源/PROGRESS review。无未授权范围扩展，无后台Python/训练。

## r2回归与最后配对（2026-10-21T11:42+08:00）
- 最终全目录退出1：152 passed/1 failed/3 warnings（pytest70.98s，wall73.063377s），唯一test_real_pool_boundary_observations_cpu64_gpu32连续q失败，保留无skip。原11模块73全过；E4夹具/真实池带外observed与厘米高度差均0。带内observed692/497，高度字节709/572；计数在JUnit属性与stdout。其他连续字段≤沿用1e-4。
- equivalence退出0/wall23.226625s：两精度各五场景包括120动作段超时，所有Transition/State/计数/queue/attempts/trace/f_k逐元素相同。最终生产SHA稳定；新同步mask＋两精度全栅格/时间戳/计数和三个RNG流测试全过。
- 注意原73中的test_robot::test_mesh_capsules_enclose_vertices_and_fixed_gripper会调用原build_robot_config写回配置，故robot_geometry.json mtime变为11:38:47。内容SHA=d65450a719857c8e5c383ccfb5d00ca6ea9d19e82ee70afc4c1ddfbc913d2d47，与task7.14 r2 verification.json完全相同，是原测试的幂等产物；未编辑其配置或只读robot.py，不为恢复mtime再写文件。
- 当前paired_E256_v2 session92464为最后大批配对；上轮profile E256-v2完成274.148转移/s、完整reset p50=101.055s；完整预算稍后按runner账本汇总。其他已结束PID均不保留后台任务。

- 11:43:43核查paired_E256_v2长命令：宿主Python PID2390498/父timeout2390491，已运行119s；采样101.937s已完成，正在串行r1对照。监控paired_E256_v2.log；停止仅已核实PID2390498 SIGTERM或session92464 Ctrl-C，600s自动结束。不操作容器/其他进程。

## r2收尾交接（2026-10-21T11:48:01+08:00）
- 最终RESULTS已按run-id追加全命令/退出/wall/input/日志、当前与历史计时分开、原代码最终映射、E4计数、待决定、限制和接手方式。来源0465–0469均已登记；实际模型/强度未知，推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium。
- 最终全套152 passed/1 failed/0 skipped（3个JUnit属性格式warnings）；原73全部过。新增真实池近奇异q对照保留失败，无放宽/改kinematics；E4两样本带外差0。五场景×两精度equivalence全部逐元素相同；三批规模最终paired所有Transition与原Core逐元素相同，r1奖励差0。
- 当前性能E16/64/256：25.895/94.827/274.148转移s，完整reset p50=6.816/26.955/101.055s；拒绝约69.23/66.84/67.55%。连续窗口0自然reset；另原地候选诊断自然partial reset两行/一行/一行，693.437/520.306/513.025ms，未选中状态/grid/queue精确不变；限制不外推训练/稳态分布。
- r2 runner1756.556429s＋r1保守391.865089s＋收尾只读30s预留＝2178.421518s（36.307分钟），最长280.095456s，未超单条600/总5400预算。预算口径沿r1命令wall账本；不是把读文档/编辑/等待也声称为容器计算时间。源SHA与归属外依赖核对无漂移；provenance记录GPU2 RTX PRO 6000/torch2.7.1+cu128等实际版本。
- 11:46收尾资源核查forem-dev仅docker-init/sleep、GPU无compute；本任务所有PID/session已退出，无后台Python需恢复。uid/gid归还1004；未训练/启停容器/提交/改参考与阶段一。
- PROGRESS写前重读有效UTF8，仅本行同字节长度pwrite→review，其他字节不变；progress_edit.json保存offset/前后行和证明。未标done。下一步Claude先读r2最终节、XML/manifest/precision_real/逐元素证据，复核E1–E5与待决定精度；不需要恢复完整聊天，也不发起新文档复核轮次。
