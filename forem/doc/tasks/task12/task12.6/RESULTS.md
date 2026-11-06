# task12.6 结果

2026-11-05T15:44:49.692831+08:00 · active（冻结与新入口核查完成，持久运行待启动核实）。执行负责人Codex，实际平台模型/强度未知；推荐GPT6.1sol/medium、Sonnet5.5/medium，地图身份/标签/配对口径需核查；拥有自主选模、强度及先建档委派权限。子任务12.6.1由Codex实现离线统计，父已读代码核schema及fixture。[SRC-T12-021](../../../SOURCES.md#src-t12-021)

run `t12-newmaps-20261105-r7`：manifest/排除清单在新标签前写入；排除旧33图及相同geometry/source hash，sparse/standard各16，按seed1206及既定排序，scene_seed126000+i。固定r6 SHA `32ebfd305dd297eca4b0831b0b960ba8a051868020897bba3c0a8e4e06914ce5`、效用v1/原两环及几何，0更新、最多768移动推演。正式test保留，获取失败不换图；规则/原地槽保留，不新制对应教师标签。

针对性新入口核查全通过，含真实旧终态12记录与r6标签一致；统计fixture14项通过，0新增教师/更新。不是新地图收益结论。冻结源码及实际命令/CPU验证日志见Agent记录及run/code-version.json、targeted-tests.json。[manifest](../../../../results/task12/t12-newmaps-20261105-r7/manifest.json) · [排除清单](../../../../results/task12/t12-newmaps-20261105-r7/exclusions.json)。

启动后按用户偏好退出主动监督。持久driver每30分钟写日志，逐状态/批保存、完成跳过、在途PredictionCore恢复；有限32状态结束后自动追加逐状态/候选指标、案例、实际成本与三问回答到本文件，并同步PROGRESS/SOURCES/独立日志。结果就绪前不宣称优于最近点或判断过置信是否改善。主排期沿用约2–3h实测依据，非硬超时；无新训练。

## 2026-11-05T15:46:47.941414+08:00 持久启动已核实（结果待运行）

run `t12-newmaps-20261105-r7`于2026-11-05T15:44:49.959565+08:00启动；父driver PID1892068/独立SID1892068、host worker PID1892130/容器PID1，容器forem-task12-newmaps-r7，物理GPU2 UUID GPU-656ca5c1-681f-48a2-7d1f-a00824723f68 → cuda:0，CPU10–11/2线程。runtime与driver实际设备核查通过；GPU0 PID1870826与GPU1 task10 PID970022保持。

32输入已全部冻结，状态{'ready': 32}，所有选择均在新教师标签前完成；首批新入口已完成12条候选记录，当前阶段state-01/grid-0，尚无完整32图收益结论。启动原件startup-verification.json、runtime.json、driver.json、launch.json。current.json的map_id仅在acquisition更新，教师阶段state_id才是进度关联键；地图身份请与plan/spec关联，不能把current中最后一次获取的map_id误当当前教师用图。该展示字段残留不影响保存的source/spec/候选身份或统计，未中断有效运行。

持久命令：`python3 -u forem/scripts/task12_newmaps_launch.py launch --run /home/ybc/projects/CL-FoReM/forem/results/task12/t12-newmaps-20261105-r7`。监控读取本run/current.json、states/*/row.json或日志`forem/logs/task12/t12-newmaps-20261105-r7/{driver,worker-01}.log`；停止创建本run/STOP，安全边界保存。不主动再监督；driver每30分钟追加日志，结束自动统计、记录退出码及交接，容器退出释放GPU2。失败保持原身份与原件，恢复跳过完成记录，不盲目重跑。本节状态active，自动终态追加后以最新终态为准。[来源](../../../SOURCES.md#src-t12-021)。

### 2026-11-05 16:00 · 决策者阶段核查
当前运行仍active，已完成4/32状态、96候选标签，正在state-04；0更新。32唯一新图分层/旧map排除/先冻结后制数与已完成行计数核对通过。最终排序及泛化验收待32图完整结果，当前不调整方案。[来源](../../../SOURCES.md#src-t12-022)

## 2026-11-05T17:43:29.832423+08:00 · t12-newmaps-20261105-r7 逐状态离线复算

状态review，0训练更新。主指标只合并完整24标签状态，缺失仍占计划分母32；部分原件的已知覆盖/命中下界另列summary.json，不将unknown记负。依据[SRC-T12-021](../../../SOURCES.md#src-t12-021)。

|集合/标签|完整/计划|筛前/筛后覆盖|可正扇区|网络选正/漏选|最近选正/漏选|网络条件/整体命中|最近条件/整体命中|缺失|
|---|---:|---|---:|---|---|---|---|---:|
|全部/utility|32/32|21/21（分母32）|107|96/11|74/33|17/21；17/32|18/21；18/32|0|
|全部/arrival|32/32|13/13（分母32）|13|6/7|12/1|6/13；6/32|12/13；12/32|0|
|sparse/utility|16/16|11/11（分母16）|56|51/5|34/22|10/11；10/16|9/11；9/16|0|
|sparse/arrival|16/16|7/7（分母16）|7|5/2|7/0|5/7；5/16|7/7；7/16|0|
|standard/utility|16/16|10/10（分母16）|51|45/6|40/11|7/10；7/16|9/10；9/16|0|
|standard/arrival|16/16|6/6（分母16）|6|1/5|5/1|1/6；1/16|5/6；5/16|0|

效用逐状态点数配对：{'gain_states': 8, 'loss_states': 3, 'same_states': 21, 'net_positive_points': 22}；状态配对：{'gain': 2, 'loss': 3, 'both': 15, 'neither': 12, 'net_hit_states': -1}。结构性未选正点48，几何排除正点83。
network选负192：该扇区无允许正点181、有正却误选11、未知未能分类0；漏正点合计59。
nearest选负214：该扇区无允许正点181、有正却误选33、未知未能分类0；漏正点合计81。

|难度/效用|点级增/损/同状态|点净增|状态增/损/同命中/同未命中|网络负点：无允许正/误选/未知|最近负点：无允许正/误选/未知|
|---|---|---:|---|---|---|
|sparse|5/1/10|+17|2/1/8/5|89/5/0|89/22/0|
|standard|3/2/11|+5|0/2/7/7|92/6/0|92/11/0|

可正扇区中网络选正96/107、最近点74/107，网络相对最近净+22点。
整体命中网络17/32、最近点18/32，净-1状态；配对{'gain': 2, 'loss': 3, 'both': 15, 'neither': 12, 'net_hit_states': -1}。
存在11个有可选正点却选负的扇区；最大负−正分差0.0997697、logit差0.509672（state-03/扇区9）。分差为排序现象，未定义校准概率或显著性阈值。
优先处理泛化问题：点级/状态级未同时形成明确净收益；保留本轮固定合同结果，数据多样性、目标与局部几何特征的后续方案另行登记/审核。

预登记大分差前三案例（不存在则absent）：
- state-03/扇区9：负candidate-27分数0.320720196/logit-0.750464022，正candidate-28分数0.220950529/logit-1.26013565，负−正差0.0997696668/logit差0.509671628。
- state-29/扇区6：负candidate-18分数0.119568415/logit-1.9965235，正candidate-19分数0.0364452191/logit-3.27481914，负−正差0.0831231959/logit差1.27829564。
- state-10/扇区10：负candidate-30分数0.955892622/logit3.0760181，正candidate-31分数0.900964558/logit2.20798802，负−正差0.0549280643/logit差0.868030071。

各难度首个点级/状态级改进退化：`{"sparse": {"point_improvement": {"state_id": "state-03", "map_id": "sparse_train_04405", "point_delta": 2, "state_pair": "gain"}, "point_degradation": {"state_id": "state-11", "map_id": "sparse_train_02441", "point_delta": -1, "state_pair": "loss"}, "state_improvement": {"state_id": "state-03", "map_id": "sparse_train_04405", "point_delta": 2, "state_pair": "gain"}, "state_degradation": {"state_id": "state-11", "map_id": "sparse_train_02441", "point_delta": -1, "state_pair": "loss"}}, "standard": {"point_improvement": {"state_id": "state-17", "map_id": "standard_train_00854", "point_delta": 1, "state_pair": "both"}, "point_degradation": {"state_id": "state-23", "map_id": "standard_train_03081", "point_delta": -1, "state_pair": "loss"}, "state_improvement": "absent", "state_degradation": {"state_id": "state-23", "map_id": "standard_train_03081", "point_delta": -1, "state_pair": "loss"}}}`。全部可避免误选保存rank-misses.json，所有候选及分数/logit见candidate-scores.csv；按分差降序、state-ID/sector破平局，未按结果更换地图或阈值。

|成本项|合计秒|逐计划状态p50秒|p90秒|最大秒|
|---|---:|---:|---:|---:|
|acquisition_s|36.732460|1.1155715640634298|1.2338388454169036|2.355413617566228|
|active_state_wall_s|7108.779929|273.79802313260734|338.88416836299007|353.20895694568753|
|candidate_generation_s|11.505366|0.3823405960574746|0.38449978101998566|0.38736216351389885|
|decode_s|0.031212|0.0009839655831456184|0.0009950755164027214|0.0010139402002096176|
|entry_decoder_verification_s|0.400971|0.012511355802416801|0.012724888883531094|0.01450733095407486|
|geometry_s|0.348977|0.010819396935403347|0.010935277864336969|0.012175537645816803|
|grid-0_s|2536.033964|92.42829671688378|133.64086853247136|135.29713333398104|
|grid-1_s|4323.792166|179.8504204582423|210.85064137559385|222.16361370123923|
|network_d2h_s|0.008452|0.00024160277098417282|0.0002833526581525803|0.0004932433366775513|
|network_inference_s|0.149116|0.0010396912693977356|0.001163399964570999|0.11433579958975315|
|network_input_construction_s|0.333080|0.009465953335165977|0.010494940914213657|0.03200742043554783|
|source_decode_h2d_s|0.029929|0.0009078141301870346|0.0009641721844673157|0.0014738589525222778|
|source_read_s|0.080622|0.002330145798623562|0.0031356655061244975|0.004164377227425575|
|source_reconstruction_s|0.358439|0.008825382217764854|0.009339142590761185|0.08008606359362602|
|terminal_fk_label_s|1.494371|0.030601929873228073|0.03256621640175581|0.39366733469069004|
|terminal_read_decode_s|21.623075|0.7939214278012514|0.89499302059412|0.94639478251338|
|write_s|154.559931|4.832953955046833|7.137046918459237|18.00858082436025|

成本分项以cost.json实际记录为准；累计/墙钟项不能和子项重复相加。无执行阶段为0，缺失见状态表；分数只解释为排序分数。单图初始状态和局部教师效用不等于整条任务成功。当前决策者负责最终验收。


负责人Codex父执行者，实际平台模型/推理强度未知；推荐GPT6.1sol/medium、Sonnet5.5/medium，地图身份/指标因果核查；执行者可自主选模强度及先建档委派，统计由task12.6.1子Agent提供并由父针对性核查。当前状态review，交当前决策者审核，未自动扩大制数或训练。

权重固定r6/model-weights.pt SHA256 32ebfd305dd297eca4b0831b0b960ba8a051868020897bba3c0a8e4e06914ce5，epoch200/训练历史600更新，本轮更新0。效用版本task12-utility-v1；32地图manifest/排除清单在任何新标签之前保存；正式test池保留，不按正点数换图。source.pt初始s=0、原sync_v5采样接受；每候选独立clone行、原B3教师，只运行grid-0/1两批。strict_success与实际提交终态FK共同核验；旧arrive标签并列。rule候选mask/姿态与inplace槽12有效/零姿态合同保留，无新规则/原地教师标签。两选择器只读24支持点/可见几何/固定分数，按candidate-ID关联唯一推演。

本次driver主墙钟7119.833秒，returncode=0，设备采样峰值3392MiB。多次尝试总消耗见attempts.jsonl；初始化/准备、状态获取、源快照恢复读取解码与H2D、网络输入构造、一次前向、几何、解码、教师、终态读取/FK、写盘分列。源状态构造内资产/采样细项见source.pt/sampler_timing，不能把同步墙钟当纯GPU时间。grid计时复用r3并扣快照写盘；active_state_wall与driver墙钟及子项不可相加。最初2–3h只是沿用SRC-T12-010/020排期，实际估计变更记driver.json，不改768/32/0更新。

原件 `forem/results/task12/t12-newmaps-20261105-r7/`：exclusions.json、manifest.json、plan.json、inputs-frozen.json；states/<id>/source.pt/candidates.json/selection.json/network.pt、grid-0/1/{data.pt,result.json,resume.pt,utility.json}、labels.json/row.json/cost.json；per-state.csv/json、candidate-scores.csv、rank-misses.json、case-selection.json、summary.json、handoff.json。冻结代码在code/及code-version.json（根HEAD不代表未提交源码）；targeted-tests.json包含新入口核查，原A/标签/坐标/恢复证据引用SRC-T12-007/009/018/019，未全量重复审核。资源/PID/启动argv/退出状态见gpu-before.json、launch.json、driver.json、runtime.json、attempts.jsonl、resource-samples.jsonl，日志forem/logs/task12/t12-newmaps-20261105-r7/。

只读原件复算（输出副本避免覆盖终态）：复制plan.json和states到独立输出目录，再执行 `python3 -u forem/results/task12/t12-newmaps-20261105-r7/code/task12_newmaps_stats.py --run <副本绝对目录>`；仅标准库，不需要GPU/教师，不再推演。原始终态FK对应提取函数code/task12_newmaps.py::Worker.utility_records，按已存data.pt可另目录重提取；部署分数及原logit在network.pt和逐候选CSV。

持久恢复命令：`python3 -u forem/scripts/task12_newmaps_launch.py launch --run /home/ybc/projects/CL-FoReM/forem/results/task12/t12-newmaps-20261105-r7`，先确认本run driver已退出，无STOP；若用户要求停止则创建本run/STOP，worker在安全边界保存；仅在用户撤销暂停后移除STOP。完成批/result及utility/row跳过，timeout恢复保存PredictionCore，不重推已完成candidate；旧失败文件保留。自动收尾不依赖聊天，写盘失败见finalization-error.json后可用同run恢复仅收尾。

未解决/下一步：本轮已达到固定32图边界，收益及反例见上表，当前决策者最终验收。

<!-- task12-newmaps-final-t12-newmaps-20261105-r7-1 -->

## 2026-11-05 · 决策者最终验收

状态 **done（本阶段评估及审核完成）**。独立读取32状态/768候选 labels、selection、row 原件复算标签公式、允许集合内选择及点/状态计数，与执行报告一致；在已检查范围内未发现阻断问题。driver正常退出，0训练更新，无缺失；复用有效隔图/设备/FK入口证据，未重跑教师。[审核依据](../../../SOURCES.md#src-t12-023)

网络可正扇区命中96/107，对最近74/107，说明点级排序收益在本批新图保留；状态命中17/32对18/32（增2、损3），尚未形成状态覆盖提升。原安全到点指标6/32对12/32。三次状态退化state-11/23/24均只有一个允许正点，且均为安全到点正样本，被网络错排；该现象应比“最大绝对分差”更优先处理，不能把加权BCE输出当校准概率。

结论：task12.6阶段签收，task12整体仍未完成泛化与系统收益验收。下一优先项是复用上述反例/标签分布指导更具多样性的训练数据及独立留出方案，先保留轻量结构、两环和效用合同；数据不足等解释仍待验证。暂不据本轮宣称可替代最近点或接入正式上层训练。没有启动新制数/训练，32张已分析地图不再算未来未观察集。

审核负责人Codex，实际模型/强度无法独立核实；推荐GPT6.1sol/medium、Sonnet5.5/medium，跨标签/选择/统计口径需要中等推理。执行者可按根约定自主选模/强度及先建档委派，本轮独立完成。
