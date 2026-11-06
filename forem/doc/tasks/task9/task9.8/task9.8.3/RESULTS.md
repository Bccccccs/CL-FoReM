# task9.8.3 诊断字段与成本结果

2026-11-02，状态 **review**；负责人 Codex 子Agent task9.8.3。只读调查已执行，父仍须核原件；B未执行。本轮请求配置 gpt-6.1-sol/medium；平台实际模型及推理档位无法独立核实，记未知。推荐 Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，原因是跨字段与成本单位核查。授权 [SRC-1364](../../../../SOURCES.md#src-1364)，本节事实、推导、工程预留及限制统一对应 [SRC-1367](../../../../SOURCES.md#src-1367)，待父登记。

原件根 `/home/ybc/projects/CL-FoReM/forem`，文档工作树 `/home/ybc/projects/CL-FoReM-task9`，HEAD `d198e5ca48f86071c05274f9da753f393ce058b4`。执行标准库JSON/字节读取、代码静态核查、nvidia-smi、docker ps/inspect/top、容器标准库metadata命令；均rc0。没有模型导入、环境运行、训练、容器启停、生产代码写入。复算程序、完整输入SHA256/文件字节、现场命令和输出见[独立日志](../../../../agent_logs/task9/task9.8/task9.8.3/20261102-codex-audit.md)、[成本JSON](../../../../agent_logs/task9/task9.8/task9.8.3/cost-audit.json)、[资源快照](../../../../agent_logs/task9/task9.8/task9.8.3/resource-snapshot.json)。

## 1. 实际路径与哈希

9.6 `scripts/task9_semantic_queue.py:23` 明确 `PYTHONPATH=/root/mm_husky_ws/src`；旧 `loaded.json` 和 `logs/task9/t9-semantic-20261102/provenance.json` 指向基础 `src/task8_lower/evaluation.py`。初查先读了 `task9_opt/runtime/src/` 副本，随后经实际入口和父复核纠正为基础src；本结果所有下述行号均按基础src。core/primitive/training副本与基础字节相同，不因此把优化副本当实际运行入口。evaluation副本hash不同，不能替代生产文件。[SRC-1367](../../../../SOURCES.md#src-1367)

|基础生产文件（相对forem）|SHA256|
|---|---|
|src/task7_sim/core.py|e8b91d60b2d5e1639f4966521d64aa4005772c5555f7532e23bd370e1da6a67b|
|src/task7_lower/training.py|36c02dbcad56ed6df5651591ed0f9d399308d5b2ea30b0e1a4a56e32cae3a99c|
|src/task8_lower/evaluation.py|178e81125b082bcc2b8e260ebaacdbe6e68e64396287c52199ef015ddf148f48|
|src/task8_sim/primitive_scene.py|62fcce99f8bafcd4dc7d33fb7bbf0085dba29e08b6cef99fa3210448f8bde30b|
|scripts/task9_semantic_eval.py|69b17dc3a5fdf8460f5166c473f7d27ed41086aafa34545210f5adeb8d8887b9|

其他辅助文件及旧原件/当前工作树两侧hash在成本JSON的inputs。没有仅凭HEAD断言dirty源码一致。

## 2. 三类字段与未来钩子缺口

|问题|旧文件已有|重放中可采（当前内存，不代表已持久化）|当前缺失/必要钩子位置|
|---|---|---|---|
|case与首次拒绝action/substep|rows有map_id、seed、stream_index、role、source_split、proposal_seed、终态failures/transfers；全role仅有失败类型总计|Core.step:248–278可读active、两次循环顺序、IK status、commit、三碰撞布尔；status=0/1等价accepted，见kinematics:167–174|旧rows无顺序。外层加每case动作号/segment号；Core:255–278在归约前采子步号、failed/accepted/pending。`first_failure_time`在267每次失败覆盖、依赖已提交segment_substeps，且begin重置，不能当回合首次拒绝时间|
|候选base与关节、提交base/q|无逐步字段|Core:250 start是提交前理想状态；259有trialbase/trials；278有previous_q与返回的ik.q；279–280原子commit；285 trace只含成功提交状态|attempts没有trialbase/trials/显式accepted；需在259–280采样。kinematics.solve_tcp_in_arm:249–251用held替换拒绝解，故attempts.candidate_q是**返回/保持q**，并非拒绝前原始求解q；原始q/残差须在249前后额外只读采样才有。state.q是理想提交状态，不是编码器反馈|
|原始/执行动作与前后状态|actions仅聚合分位/均值，无逐case序列|Transition:25–38保存raw_action、observation/next_observation、attempted、committed、reason；Core:249计算u,w,v；250有queue和start；317计算rho|在evaluate原step处关联case键与tr；采249执行速度和前后base/q/s、queue。不能从动作指令回填实际物理反馈|
|原子目标进展、身份、切换原因|仅子段reached/timeout/failed总计和终态|choose_candidate:32–47有生成候选mask、选槽slots、pose/progress/inplace；Core.begin:127–164设置start/candidate/cap；Core:286–296 reached/route_end/timeout、reason|候选slot和稳定segment/event id当前不保存；下一choose_candidate前保存旧reason，不能让begin清空后补猜。记距离rho及朝向残差、s/cap、arrived、route_end、stalls与终止谓词，区分到达后切换和timeout/停滞。恢复判读只限同segment，不能把换目标后距离变小算原目标恢复|
|碰撞类型与优先级遮蔽|step_failure_counts仅优先类型1 IK→2 base→3 arm→4 self|Core:262先算完整coll；265优先归类；attempts:278保留三布尔。几何三布尔可同时采，暴露类型遮蔽|IK未接受时coll基于held q与trialbase，不能称原始拒绝IK解的碰撞，也不能把三布尔当独立可致因普查。未采的并发情况标unknown|
|碰撞对象与三维几何见证|sidecar可按box行关联object/part，但日志没有当时命中box|primitive_scene._chassis_block:201–217有逐box SAT overlap；_arm:230–238有env/cap/box索引和d2；primitive_boxes:383–385可读形状；GhostRobotGeometry.self_contacts:48–54可诊断配对|Collision仅base/arm/self三个布尔（geometry:101–106）；chassis在217 any归约、arm在238与239合并并丢配对，当前API无对象ID/三维接触点/法线。若未来获准需在原判定局部保留box/capsule索引、端点/半径、OBB位姿尺寸/d2及ground分支；self取原判定配对。base合同只做全高度XY投影，**没有3D交叠证据**，不能据base=True宣称撞了家具实体|

静态依据均为[SRC-1367](../../../../SOURCES.md#src-1367)。`evaluation.py:126`（基础文件）及semantic脚本:48每步调用 `drain_history`；training.py:73–77清空transitions/trace/attempts。`begin`亦清历史。因此这些内存字段不是旧日志可恢复数据。未来钩子涉及 evaluation.py / semantic runner、training.choose_candidate、Core.step/begin、kinematics.solve_tcp_in_arm（若需原始拒绝解）、primitive_scene碰撞判定与必要self-contact接口；这里只列缺口，**未实现、未获B授权**。不能靠外层包一层env.step就声称对象和子步候选信息齐全。

## 3. 旧实际成本输入

旧完整评估文件为 `results/task9/t9-stage2-20261029/B3_5M-seed<seed>/validation-5000000.json`（100random+96semantic）；9.6为 `results/task9/t9-semantic-20261102/seed<seed>/evaluation.json`。[SRC-1367](../../../../SOURCES.md#src-1367)

|seed|196回合实际wall s|196实际transfers|文件bytes|9.6 96回合wall s|9.6 transfers|9.6文件bytes|9.6 status−eval s|
|---|---:|---:|---:|---:|---:|---:|---:|
|4718|1107.264043|21173|134841|476.395101|10170|65862|104.397959|
|4719|1168.423173|20884|134888|510.083844|9396|65839|116.226998|
|4720|1190.881621|22278|134840|518.036887|10470|65825|137.336325|

196文件合404569bytes/64335transfers≈6.29bytes/transfer，但它们是**聚合摘要**，绝不是trace逐转移字节率。status−eval包含模型加载、构建/检查与外层JSON等成本，不是纯加载profile。未测逐批wall、记录器同步/拷贝/序列化/写盘开销、候选/IK诊断追加开销；旧训练期间评估与现在独立回放的资源条件也不相同。上述实际数据不构成新回放的工期保证。

## 4. 回合、转移、trace与预算分母

**父最终复核纠正：严格执行“两例on/off通过后再完成其余目标”的门顺序，主方案为980回合。** 先4718 off196、on196只采两控制例；门通过后4718再完整196只采剩8目标，随后4719/4720各196。`5×196=980`，目标详细trace仍30例、2695历史动作，每目标只详记一次。先前784把门前同批其余8目标附带详记直接算完成，漏了门依赖；本子Agent与父最初均未及时识别。用户新指令沿原入口未撤销门顺序，故不能自动采用784；784仅保留为监督者明确接受门前附带采集的待裁决优化。同理严格整批口径为208=144+32off+32on-repeat；176也是需接受门前附带采集的条件优化，不能叫严格最小。此纠正覆盖下文较早“主路径784”的措辞；未因此运行任何回放。

**原784条件优化的计数保留（不得自动采用）**：沿原evaluate入口，仅目标保存详细trace。若监督接受门前附带采集，合并不裁剪入口方案为每seed完整196各一次，再将4718完整196无记录执行一次；总784实际回合。前置开关阶段为4718完整196的on/off两次，共392实际回合，其中on196已计入588，故不是588+392=980。目标两例在同一4718 evaluate里同时出现，开关on详细trace只191动作；门后剩余目标2504动作，完整30目标trace2695动作。旧结果不同须保留新旧两次并按本次轨迹解释；本表transfers沿历史计数只用于估算，不要求旧逐步轨迹相等，也不是新实测。此更新优先于早期子集/拆批假设，最新授权沿 [SRC-1364](../../../../SOURCES.md#src-1364) 由父统一追加；A未获得784回合运行授权。

开关建议两例固定为4718 random成功row53 `standard_validation_00003`（107transfers）与semantic失败row8 `home_map_002`（84transfers）；同一case分别off/on，合4回合，2个on已计入30。其完整身份在成本JSON selected_cases。此选择是工程诊断选例，非新随机抽样，也不证明可拆批。[SRC-1367](../../../../SOURCES.md#src-1367)

|口径|实际执行回合|recorded-run回合（目标）|总transfers代理|有记录动作数（若全批也记录）|子步尝试记录上限|32KiB/action工程trace bytes|
|---|---:|---:|---:|---:|---:|---:|
|原evaluate严格门顺序（当前主方案）|980|784（30）|106681|2695|5390|88309760|
|原批严格门顺序（替代边界）|208|176（30）|24572|2695|5390|88309760|
|原evaluate入口开关（严格/优化共用前置）|392|196（2）|42346|191|382|6258688|
|原evaluate合并（784条件优化）|784|588（30）|85508|2695|5390|88309760|
|仅两例on/off，假设可独立等价回放|4|2（2）|382|191|382|6258688|
|理想30+2合并|32|30（30）|2886|2695|5390|88309760|
|只做开关但保持原16批形状|64|32（2）|7714|3857|7714|126386176|
|三目标批合并（176条件优化）|176|144（30）|20715|16858|33716|552402944|
|合并两role，完整196×三seed+off32|620|588（30）|68192|64335|128670|2108129280|
|保留两个入口各自完整role：196+96每seed+off32|908|876（30）|98228|94371|188742|3092348928|

整批目标涉及 random offset48（16行，含sparse同伴），semantic offset0与32（各16行）；3批×16×3seed=144，其中30目标+114同伴。开关阶段4批×16=64，32on已包含144，仅额外32off，故在接受门前附带采集的条件下合并176；严格门顺序需门后再跑4718控制涉及的两批32回合，合并208。同伴即使不写trace也算执行回合。620是合并两role且接受门前附带采集的范围计数，并非完全保留9.4与9.6两个独立入口；若连角色循环也不裁剪，908覆盖196+96各三次（同样未计严格门后重跑，仅条件备用）。若off也必须完整未裁剪入口，则还会高于908，**尚未预算，须另核授权**。[SRC-1367](../../../../SOURCES.md#src-1367)

980主方案动作数只为目标详细trace；下方其他方案全批记录字节只是可选容量对照，**实际仅目标详记，不记录同伴详细trace**。动作数来自旧目标逐行transfers求和；本次路径可有差异，故实际记录数/字节必须另核；单动作最多2个0.05s子步来自Core.step:255–259，所以记录上限=2×actions，不是实测尝试数。32KiB/action是假设每动作含两子步、状态/目标/少量见证的JSON预留，未写过真实trace，亦非对任意对象列表的硬上界；不包括全栅格/图像/逐候选全表/复制checkpoint。若仅30目标写trace，整批方案的目标trace仍用88309760bytes代理；开关2off需额外比较数据，若也保存同结构额外6258688bytes，所有方案同伴输出可更大。主路径建议新结果/日志 **1GiB** 工程磁盘窗口，依据目标trace88.31MB、两次on/off比较数据约12.52MB加摘要/版本/异常余量；该1GiB不是实测或已批准额度，实施后须测实际序列化字节。前期16GiB建议改为仅在决定全同伴详记等更大输出时另审的可选预留，**不列主预算、不增加当前字段/功能授权**。不复制大checkpoint。每次采样后必须计字节，达到核准上限即停，不能删样本维持预算。

## 5. 时间代理与工程窗口（不是授权或保证）

推导采用 `r=max(full_eval_wall_s/transfers)=0.05594824615 s/transition`；`L=max(status.wall_s−evaluation.wall_s)=137.336324923s`。代理 `T=N×r+k×L`，顺序单worker、单GPU时卡时≈worker h≈wall h=T/3600。k严格主方案980为5次；开关为2次；784条件优化为4次；其他假设方案完成30目标时on/off4718各一次及其余两seed、最后余项分段等共5次；908方案按6完整入口+2off共8次。k是工程假设，实际runner若另开进程必须追加，不能遗漏模型冷启动。没有GPU利用率计量，卡时为占用预留，不是kernel计时。[SRC-1367](../../../../SOURCES.md#src-1367)

|口径|T代理秒|顺序单GPU/worker/wall h代理|
|---|---:|---:|
|严格主方案980|6655.296|1.8487|
|严格原批替代208|2061.442|0.5726|
|原evaluate开关392|2643.857|0.7344|
|原evaluate合并784条件优化|5333.368|1.4815|
|两例独立开关4回合|296.045|0.0822|
|理想30+2|848.148|0.2356|
|原批开关64回合|706.257|0.1962|
|最小整批176|1845.650|0.5127|
|合并完整196口径620|4501.904|1.2505|
|双入口完整908|6594.375|1.8318|

980直接累计旧wall：`sum(3seed完整196wall)+2×4718完整196wall+5×L=6367.778547s=1.76883h`；最大转移率加5次外层代理为6655.296472s=1.84869h。5次全额计费代理仍为6641.089732s=1.84475h；三个数均未含真实记录器开销，不能作上界。主预留仍建议17:00–20:00、3 GPU h/3 worker h/3h墙钟、1GiB，须监督核准，不能据1.85h代理承诺3h内完成。

784条件优化另可直接累计旧wall：`1107.264043+1168.423173+1190.881621+1107.264043+4×137.336325=5123.178180s=1.42311h`；开关392为`2×(1107.264043+137.336325)=2489.200736s=0.69145h`。这些额外加入了独立启动代理；原评估部分本就在训练进程中，无法直接给出重放冷启动耗时。较宽的784工程计费代理为`4×(1190.881621+137.336325)=5312.871786s=1.47580h`，仍未测trace开销，且稍低于按最大单转移率推的1.4815h，均不能作为上界。

**线性比例不能当上界**：批内tail、冷缓存/候选重采、批大小与对象数量导致非线性。更宽的计费代理可把5次调用全按最慢完整196+L计：`5×(1190.881621+137.336325)=6641.089732s=1.84475h`；908按8次为10625.743571s=2.95160h。即便此代理仍没有实测trace开销，不能称“保证3小时完成”。建议若后续批准且部署已准备好：**2026-11-02 17:00–20:00 Asia/Shanghai**，物理GPU2一张，最多3 GPU h/3 worker h/3h墙钟；若改为908口径应另审17:00–21:00、4h预留。均是留审核/实现及未知开销余量的工程窗口，不是预约、用户授权或性能承诺。窗口届满若工作未完就安全退出，不能自动延期；不批准超回合预算则全部留在A。

## 6. 现场资源与依赖

2026-11-02约15:30 +08快照：4×RTX PRO6000，GPU0–3均14MiB/97887MiB、0% util、无compute进程；驱动590.48.01。`forem-dev`仅docker-init/sleep，image `sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430`，但其 `/root/mm_husky_ws` 是**旧历史根RW挂载**，不含本task9工作树，因此不满足隔离写入要求。不能直接复用旧命令写回原件。[资源快照](../../../../agent_logs/task9/task9.8/task9.8.3/resource-snapshot.json)

新出现的 `forem-task10-exec` 与 `forem-task10-runtime` 属其他任务，均DeviceIDs=[1]，挂task10工作树、历史参考只读，当时只sleep；不占用或停止它们。建议GPU2避免与其声明的卡1冲突，但快照不代表未来空闲或资源锁。当前未发现task9工作树隔离容器，B部署路径须父另核，A不创建容器。

容器只执行标准库 `sys`/`importlib.metadata`，没有import torch/numpy/scipy：Python3.10.18、torch distribution2.7.1+cu128、numpy1.23.5、scipy1.10.1，rc0；见[metadata](../../../../agent_logs/task9/task9.8/task9.8.3/dependency-metadata.json)。历史runtime.json记torch2.7.1+cu128、CUDA12.8、threads2、interop64、TF32=False；9.6 loaded.json确认当时policy/critic cuda:0、actor tensors equal，**不证明本轮已加载或新容器tensor设备**。/home空闲约10.138TB（原始df bytes在快照），没有磁盘可用性承诺。

## 7. 给父的裁决输入

字段与成本调查已交付；**B NOT_READY**：用户现优先原入口，仅目标详记，严格门顺序980实际回合主方案超过原30+2；严格整批208、784/176条件优化、合并620、双入口908只作替代边界对照，不在A自行选择实施。旧结果差异应保留两次，不以旧轨迹严格相同为前提；记录开关对同次输入的非干扰检查仍须父定。当前无完整记录器、原始拒绝IK解/对象三维见证无持久化接口；旧容器挂历史根RW，隔离工作树部署未核准。本调查不以“内存可读”当非干扰验收，不以预算代理当性能验收。下一步父核查清单、来源及等价性，决定是否向用户报具体超界；不在A自行改合同或进入B。没有本任务后台PID、模型、环境进程或待停止任务。
