# task9.8.2 回放等价性审查结果

2026-11-02，状态 **review**（A静态调查完成，待父核验；B回放尚未执行）。负责人 Codex 子Agent task9.8.2；请求 gpt-6.1-sol/high，实际模型/强度无法独立核实，记未知。推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为批次、随机流与数值执行路径需跨模块审查。授权 [SRC-1364](../../../../SOURCES.md#src-1364)，全部本节主张及推导交父统一登记 [SRC-1366](../../../../SOURCES.md#src-1366)。

**当前建议：严格保留“两例on/off先通过，再采其余目标”的顺序，完整原evaluate需980实际回合，仅保存30目标详细trace；超原32回合上限，先交监督者调预算，B尚未执行。第8节是当前裁决；784仅在监督者另行接受门前附带采集时成立。** 以下初版严格复现审查保留为历史，旧轨迹一致性不再是门。 局部RNG可按案例重建，但没有运行证据证明宽16改成宽1仍逐步精确等价。保留选定案例的最小原批需144个实际回合（30目标＋114同伴）；两次原批无记录对照另需32，共176，超过父流程30+2上限。这里不是断言单例必然产生差异，而是不能把尚未验证的数值等价当成已满足条件；不得在A补跑或自动扩预算。

证据与可复算入口：[独立日志](../../../../agent_logs/task9/task9.8/task9.8.2/20261102-codex-audit.md)、[标准库脚本](../../../../agent_logs/task9/task9.8/task9.8.2/recompute.py)、[完整哈希/原批同伴清单](../../../../agent_logs/task9/task9.8/task9.8.2/audit.json)。脚本rc0，30目标、9个原批、144回合、22对基础源码两树字节一致。未import环境/模型、未加载pt、未运行torch/仿真/训练。

## 1. 实际入口与版本绑定

工作树 `/home/ybc/projects/CL-FoReM-task9`，HEAD `d198e5ca48f86071c05274f9da753f393ce058b4`；历史只读根 `/home/ybc/projects/CL-FoReM/forem`，核查时HEAD `121cb36e64e53163be232dbafa8c32ff065a290b`。HEAD只标记核查版本，不将dirty源码误称为该commit原样；逐文件SHA是字节身份依据。

原B3_5M的实际命令见历史 `logs/task9/t9-stage2-20261029/queue-state.json:471,516`（4718/4719）与 `extra/waiter-state.json:64`（4720）：`PYTHONPATH=/root/mm_husky_ws/src`，调用 `scripts/task8_lower_train.py`。该脚本 `/home/ybc/projects/CL-FoReM-task9/forem/scripts/task8_lower_train.py:8–10,21` 又将基础 `src` 放到sys.path首位，导入task8_lower.training并设配置线程数。不是task9_opt/runtime副本。9.6的入口为基础 `scripts/task9_semantic_eval.py`。以上路径的历史日志位于只读根下。

基础源码 `/home/ybc/projects/CL-FoReM-task9/forem/src/task8_lower/evaluation.py` SHA256 `178e81125b082bcc2b8e260ebaacdbe6e68e64396287c52199ef015ddf148f48`；`/home/ybc/projects/CL-FoReM-task9/forem/scripts/task9_semantic_eval.py` SHA256 `69b17dc3a5fdf8460f5166c473f7d27ed41086aafa34545210f5adeb8d8887b9`，均匹配三seed `loaded.json`与历史provenance。本次22对基础源码逐字节匹配两树，完整绝对路径与SHA见audit.json.hashes；没有读取opt副本作为B3证据。

读取三seed `results/task9/t9-stage2-20261029/B3_5M-seed<seed>/{config.json,runtime.json,validation-5000000.json}` 与 `results/task9/t9-semantic-20261102/seed<seed>/{loaded.json,evaluation.json}`。实际eval宽由 **validation_environments=16** 控制；config的batch_size=256是训练replay批，environments=256是训练环境数，均不是eval宽。`validation_seed=14718/14719/14720`传给临时env后，被独立EvaluationStreams替换，不能把它误作案例proposal seed。

三seed原runtime共同记录torch `2.7.1+cu128`、CUDA `12.8`、RTX PRO 6000 Blackwell、threads=2、interop_threads=64、affinity=0–63、TF32 matmul=false/cudnn=true；原训练GPU分别3/3/2。9.6 loaded只证明当时记录policy/critic在cuda:0、actor_tensors_equal=true、CUDA_VISIBLE_DEVICES=0及所列hash，不记录numpy/scipy/pyastar/cuDNN精确版本、线程/TF32/确定性算法开关；不能用原训练runtime替代9.6缺失runtime，也不能用当前容器版本倒填历史。本轮未加载模型独立复核张量等同，沿用loaded的历史记录并明确此限制。

## 2. RNG、初始化和目标顺序

下表源码均为绝对前缀 `/home/ybc/projects/CL-FoReM-task9/forem/`，历史对应 `src/...`原件与本树字节相同，SHA在audit.json。

|源码/符号/精确行|静态事实与条件|
|---|---|
|`src/task8_lower/evaluation.py:evaluation_plan:24–60`|jobs保留evaluation_seeds记录次序，不按本次选样排序重新排批；强制stream_index=0、role/source_split/manifest路径和hash身份。案例排序只用于选择，不能改原执行位置。|
|`src/task8_lower/evaluation.py:EvaluationStreams.__init__:63–68`；`src/task7_sim/episode.py:RandomStreams:22–35`|每job创建RandomStreams(job.seed,1).for_env(0)，purpose=maps/initial/other分别为0/1/2，SeedSequence spawn_key=(0,purpose)。eval batch位置不进入seed，不使用训练256环境的stream_index。|
|`src/task8_lower/evaluation.py:evaluation_environment:71–86`|每job独立sampler，entries强制单一原地图；factory把同一job对象流传给sample。临时env原validation_seed流在reset前被替换。|
|`src/task8_sim/episode.py:PcdEpisodeSampler.sample:90–148`|maps流选entries；initial流逐proposal取int64 seed，再创建局部np.default_rng(seed)。同一个局部rng依次生成base、goal、witness permutation与yaw；拒绝后回到下一proposal。goal/route/IK任一接受结果变化均可能改变最终proposal_seed、任务身份。proposal_seed是最终接受proposal的seed，不能代替job seed后跳过原拒绝过程。|
|`src/task8_sim/env.py:PcdEpisodeEnv.reset:55–95`|初次必须整个当前batch reset；按升序id依次sample，再拼接state/route/scene并作批量初态复核、render、grid。单例能构造自己的初态，但批量复核/初始观测数值仍需确认。|
|`src/task7_lower/training.py:choose_candidate:31–48`|对done未终止行按升序id生成候选，各row从自己的.other流在升序有效slot列表随机取一项；没有共享候选RNG。保持同一候选mask、边界次数和other流状态才可保持抽样；只重设相同全局seed不能替代此条件。|
|`src/task7_lower/training.py:rng_state/restore_rng:87–92`；`src/task8_lower/evaluation.py:evaluate:97,136`；`scripts/task9_semantic_eval.py:evaluate_transfer:19,58`|保存/恢复Python random、numpy旧全局RNG、torch CPU与全部CUDA RNG；此机制保护调用者全局状态，不是重设独立Generator，也没有证明底层GPU运算确定。|
|`src/task8_lower/training.py:train:176–181`；`scripts/task9_semantic_eval.py:73–85`|训练fresh入口显式seed Python/numpy/torch/CUDA，9.6入口只设threads=2，没有这些重seed。模型构造会消费torch初始化RNG，但随后载入参数；确定性actor与本次追到的采样/候选路径不依赖其残余全局随机状态。不能把9.6未seed写成“整个任务未固定seed”。|

**局部随机流推导**：在相同库语义、相同job seed/stream、相同地图、相同采样接受分支下，单case无需消耗更早batch或同伴的RNG，即可重建maps/initial/other序列。原episode_index用于绑定种子记录，不另参加RandomStreams计算。本推导只涉及源代码随机依赖，未执行numpy取样或环境重建验证，不是数值轨迹复现。

## 3. 确定性actor与原批形状边界

actor的确定性只选择均值路径：`/home/ybc/projects/CL-FoReM-task9/forem/src/task7_lower/sac.py:28–32`→`networks.py:36–37`，返回params均值的tanh，不调用Normal.rsample。网络无Dropout/BatchNorm；`networks.py:14–31`仍含channels_last Conv2d、Linear、ReLU，输入为整个env.batch。`task8_lower/evaluation.py:110–121`与`task9_semantic_eval.py:32–43`即使部分行结束，也对全batch推理，再以active屏蔽转移。只保留目标行、提前删掉结束同伴，或拿dummy行凑16，都未证明保留实际执行形状/顺序。

下列是**源码显示的形状依赖和待验证风险**，不声称本次已经测出数值差异：

- `src/task7_lower/training.py:33–37`按当前边界行动态压缩候选batch；`src/task7_sim/search.py:39–58`以当前batch剩余路线最大值确定sample count，拼B×N目标后按keep压缩。同行终止时刻或路线长度不同会改变压缩形状与重复端点个数。
- `src/task7_sim/kinematics.py:235–251`按fallback掩码压缩DLS输入；`175–199`按fallback数量上取2幂capacity建CUDA graph，含warmup/capture/缓存；`200–221`含矩阵乘与线性求解。保留同一case但换同伴，会改变fallback数、图bucket和计算调用形状。branch argmin及accepted阈值也受数值结果约束。
- `src/task7_sim/routes.py:89–123`原本保存各row既有长度/弧长，避免重算；共同padding宽由最长route确定。`src/task8_sim/primitive_scene.py:_Bank:110–125,_context:486–496`按共同最大box数padding并建rowmap；raycast/collision采用这些形状。它们在数学语义上按row隔离，但尚无本目标集的单例/原批逐步对照。
- `src/task7_sim/core.py:255–311`对子步进行整batch IK/碰撞再以pending/commit屏蔽；失败子步不提交，先前已提交子步不回滚，CBL失败后本action后续子步停止。分类优先IK→base→arm→self；`329`仅有commit才更新queue。首个阈值/分类差异可进一步改变状态、候选边界与other流消耗。

原runtime没有记录torch deterministic_algorithms、cudnn.deterministic、cudnn.benchmark或CUBLAS_WORKSPACE_CONFIG；生产路径也没有强制这些设置。**A不能保证**跨batch形状、GPU、线程数、库/驱动版本的逐位相等；也不能为追求可复现擅自改变旧TF32或确定性开关。相同checkpoint+确定性选动作是必要身份条件，不能单独证明这些数值条件。需要B获授权后保存真实版本/设备/线程/flags，并区分精确相等与事前批准的浮点容差。

## 4. 选定案例的原批位置与预算推导

按父规则从4718 standard旧rows排序选首成功 `standard_validation_00003`、首failures=20非成功 `standard_validation_00000`；三seed同完整key均存在，原seed文件与输出row次序逐行匹配。全部索引下表为0-based，三seed位置相同，完整目标键/原批同伴键在audit.json。

|来源role|目标|原row|batch_index|batch内位置|原批宽|
|---|---|---|---|---|---:|
|旧validation|standard_validation_00000|50|3|2|16|
|旧validation|standard_validation_00003|53|3|5|16|
|9.6 transfer|home_map_002，原4例|8–11|0|8–11|16|
|9.6 transfer|library_map_002，原4例|44–47|2|12–15|16|

计数按实际执行episode，不能把未记录同伴从预算中删掉：

|保留方式（未执行，均须另审）|每seed|三seed|与32上限|
|---|---:|---:|---|
|仅10目标，单例或重组批|10|30；再2个无记录=32|计数合限，但原批→子集等价未证，不能据此READY|
|最少三个原批，保留原位置/同伴/结束时序|16+16+16=48|144；再两个16宽无记录对照=176|超界；30记录目标之外还有114次同伴执行|
|分别保留旧validation与9.6 transfer各自role前缀直到目标批末|64+48=112|336，未含额外对照|超界；这是调用前缀方案，不是RNG强制需求|
|完整两个来源role（validation100与9.6 transfer96）|196|588，未含额外对照|超界；需能够只执行原validation role|
|两个生产入口均完整不裁剪：原evaluate的196＋9.6 evaluate_transfer的96|292|876，未含额外对照|超界；原evaluate也会执行旧transfer96，不能漏算|

**何时应保留整批/前缀**：在没有额外运行等价证据而要求尽量保持原数值调用上下文时，至少保留目标所属16行原批，并从原初态让全体同伴运行到生产循环自然结束；禁止dummy、重排、提前删除或冻结同伴。若还要求保留首次CUDA graph/kernel warmup、allocator/backend缓存及前批调用次序，应重放相应role/入口前缀或完整入口；局部RNG无此依赖，但A未证明跳过前批对这些执行状态无影响。完整重放也不自动消除GPU数值重复性的证据缺口。旧validation发生在训练后，原训练的全部底层隐式状态未在runtime存档，不能承诺用新进程逐位还原。

这里的整批方案是保守工程边界，不是已证“任何子集都不可能等价”。在不改变预算/协议前提下，父A应停在具体缺口，交监督者决定，不自行把114个同伴当免费执行。

## 5. 必须分开的两个运行验收门（均尚未执行）

1. **记录器非干扰**：相同调度/批形状下，无记录与带记录比较每步raw action、候选/接受/commit、状态、终态。该门验证钩子不改执行。
2. **原批→子集等价**：保留原16行参考与候选子集运行逐步比较，且保留初始化proposal/goal/route、候选序列与子步结果；同库/设备/线程/flags，首次差异即停。此门需要额外原批参考和同伴，现预算没有覆盖，不能在A或B默认增加。

现旧JSON只存逐回合终态、transfers、Q/return和全组actions聚合，没有逐步动作/状态。两次**单例**记录开关对照只通过第一门，不能通过第二门；同旧strict_success/failures/transfers匹配也不能证明旧轨迹逐步一致。9.6每case成败匹配旧结果是已有终态层级证据，不是本30项的单例等价测试。无需把所有库环境状态能否逐位复原这一缺口写成“必定不等价”。

## 6. 交接与来源登记字段

目标/授权：仅A只读审查；当前负责人Codex子Agent。已完成：实际基础src路径、22对源码/hash/git绑定、三seedconfig/runtime/loaded、随机流/初始化/候选/回滚追踪、30目标原批位置及144/176预算推导、两类等价门区分。剩余：父从原件核验并登记来源；监督者决定如何处理单例数值等价缺口及超回合预算。无本轮后台进程、无停止/恢复操作。风险：历史无逐步基准、语义runtime字段不全，A静态证据不足以证明单例或跨设备精确重放。下一步停在A，不进入B。

提交父登记 **SRC-1366** 的完整字段：

- 主张：独立job/purpose RNG与原批数值形状是不同条件；目标在9个16行原批，最少144实际回合、加两批对照176，超过30+2；单例重放尚未运行证实，记录器非干扰不能替代原批→子集等价。
- 类型：项目原始源码/运行JSON静态核查＋标准库计数推导＋保守工程判定；不是新仿真实测、不是外部文献结论。
- 作者/机构与标题：FoReM项目 / Codex task9.8.2，《A阶段回放等价性审查》；年份/版本：2026-11-02，工作树与历史HEAD见第1节，逐文件SHA见audit.json。
- URL/本地证据：本RESULTS、独立日志、recompute.py、audit.json（本节链接）；历史JSON绝对根 `/home/ybc/projects/CL-FoReM/forem`，run-id `t9-stage2-20261029`、`t9-semantic-20261102`；task9.8 A run-id `t9.8-A-20261102`。
- 精确位置：第1–3节逐符号/行号表；audit.json.selected含30目标，original_batches含9个原批全部144行，metadata含三seed原config/runtime/loaded，hashes含来源绝对路径与SHA。
- 核查日期与人：2026-11-02，Codex子Agent task9.8.2；父须独立核验，不把本自报当父PASS。实际模型/强度未知，请求gpt-6.1-sol/high。
- 原始结论：代码可重建每job局部流；没有本目标集单例/原批逐步对照；原批width/IK fallback/route及scene padding形状可由同伴改变；上述预算是根据原row位置和width=16计算。
- 采用方式/限制：仅用于A的NOT_READY与预算/验收缺口，不作为单例必不等价或机制失败原因的结论；未加载模型、未验证真实浮点差异，未批准新增回放、记录器实现、训练或改评估入口；来源条目不能授权扩范围。

## 7. 用户后续补充：改以本次轨迹分析，优先原入口（上一版；顺序计数由第8节修正）

本节按父转交的最新用户指令更新，**覆盖上文把历史精确轨迹视为准入条件的结论**；上文保留为本次调查前半段事实及推导记录。用户允许：优先原评估入口采轨迹；单case容易则单跑，若拆批改变RNG或需要额外开发则按原批重评，仅保存目标详细trace；冻结模型/地图/seed/成功判据；新旧结果不同均保留，按本次轨迹分析。整批超原回合上限先报监督者调整。授权依据由父同步维护 [SRC-1364](../../../../SOURCES.md#src-1364)，审查仍为 [SRC-1366](../../../../SOURCES.md#src-1366)。

**上一版建议为784回合；父最终核验发现它隐含门前采其余目标trace，当前按第8节严格顺序980修正。** 不以历史逐步/终态一致作为门。 记录器on/off非干扰仍须通过。本子任务没有执行B，也没有批准784回合预算；具体时间由成本子任务/父核算，不能从回合数保证耗时。

### 7.1 原入口没有case/batch筛选或现成trace hook

生产 `/home/ybc/projects/CL-FoReM-task9/forem/src/task8_lower/evaluation.py:evaluate:96` 仅接受sac/config/output/deadline/cancel，`101`固定validation与transfer两role，`103–107`依据validation_environments切原连续批，`127–130`只输出终态/聚合结果。没有case集合、batch offset、role filter、callback或trace参数。`evaluation_plan:25–60`要求完整100validation与24×4transfer身份，因此改pool/seed文件为目标子集会被合同拒绝，不能用配置静默筛选。

`evaluation_environment:71`虽可接受任意非空jobs并依次构造环境，但只是构造helper，不执行完整评估循环。通过它只跑9个目标原批，仍需新调度包装（或增加evaluate筛选参数/复制循环/受控动态包装range等）；当前没有无需额外开发的单例入口，也没有现成任意原批选择API。A不实现这些途径。`deadline/cancel`用于SamplingIncomplete异常，不能用来正常跳过前批或当成选择API。

任何方案都需经B批准后加入诊断采样钩子。生产当前可在外部包装evaluation模块的evaluation_environment返回env，再对其step/begin作只读采样，或包装相应core调用；这是待设计的诊断集成，不是现成接口，更不能在A宣称已具备采集功能。完整入口方案只需诊断集成，176方案除此之外增加调度/结果包装维护。不得将“无现成hook”解释为用户未授权B必要诊断钩子，B仍须由监督者明确派发。

### 7.2 176与784的比较（均未执行）

|方案|实际回合计数|必要实施变化|当前取舍|
|---|---:|---|---|
|选定原批，保留16行与原同伴顺序|3seed×3batch×16=144；4718两个role各一批off重复=32；总176|诊断钩子＋原批筛选/派发包装；可重用evaluation_environment，但生产evaluate本身无此入口|工作量更大、回合更少；若监督者优先减少运行成本可另审，不由A自动选择或实施|
|完整原evaluate，原配置宽16|3seed×196=588；4718完整196重复一次作off/on=196；总784|诊断钩子；直接调用原evaluate，无case/role/batch调度变化|按用户“优先原入口、避免为拆分额外开发”推荐；超32，须监督者调整预算|

784安排：4718完整一次无详细trace、一次开启目标trace，以其中随机和语义各一个预定目标case做on/off逐步非干扰比较；另外两seed各完整一次并仅保留目标trace。开启记录一侧30目标模型-case不变，两个对照case已包含在30之内。实际回合计数为784，不能因只保存30份详细trace写成30+2回合。对照基准逐步比较如何保存/流式核验属于B诊断集成，需在执行前写清，不把本段当成已经采集结果。

新协议不要求额外调用9.6 transfer-only入口：完整evaluate已含相同原transfer jobs及helper/循环语义，9.6原件保留为旧比较表。即使新旧终态/transfer数或动作轨迹不同，都保留双方并标注本次来源/版本，按本次轨迹分析；**不因与旧结果不同自动失败**。首次on/off不一致、身份漂移等依旧按父门停报。前文876是同时强制两个旧入口完整复刻的计数，在新规则下没有必要采用。

### 7.3 更新后的条件分类

- **静态已确认可保持**：原evaluation_plan完整案例身份、顺序与16宽原批；独立job/purpose RNG构造；确定性均值actor路径；原成功判据、冻结地图/模型/seed合同。保持这些条件不等于已证明运行结果。
- **B运行待确认**：真实加载设备/版本/flags及身份；采样proposal身份；记录器on/off非干扰；本次实际轨迹、终态及与旧结果的差异。历史逐步精确/终态匹配已撤为验收门。
- **本轮不能声称**：单case精确保持旧轨迹、跨形状/设备/线程/库的逐位不变、784回合已经获预算或已运行、诊断hook已实现。无需为这些旧轨迹保证另做原批→子集证明，新规则仅在选择单例实现时如实说明范围。

当前交接：A静态调查已完成，提交父核验；实施方案可准备，但回合预算及B派发仍需监督决定。不存在以历史精确复现缺口强制新增实验的理由。

SRC-1366最终登记结论须同时采用第7节：历史精确轨迹/终态匹配已撤为验收门；原evaluate无选择/trace API，784完整入口为最少调度改动建议，176是新增原批包装的备选；均是未执行预算推导，须监督调整。记录器on/off仍必要。不得仅摘录第6节早期NOT_READY理由而遗漏最新用户授权。


## 8. 父最终核验纠正：严格先过两例门，再采其余（当前裁决）

父核验指出：第7节784与176的计算把4718首次on对照运行同时当成其余目标的正式trace采集。原B仍要求“两例记录开关先通过，再完成其余组合”，最新用户只取消历史轨迹/终态一致要求，**没有明确取消该先后门**。因此784/176不是严格保持现流程时的预算，不能自动采用门前附带详细采集。本人接受此纠正；原计算及其成立条件保留在第7节，本节覆盖其推荐结论。授权仍为 [SRC-1364](../../../../SOURCES.md#src-1364)，推导证据为 [SRC-1366](../../../../SOURCES.md#src-1366)。

### 8.1 严格守门：完整原evaluate为980回合

|顺序|调用与采集|实际回合|新增目标详细trace|
|---|---|---:|---:|
|1|4718原evaluate完整off；仅为两例对照准备必要逐步基准，不采其余目标正式详细trace|196|0|
|2|4718原evaluate完整on；仅两个预定对照case开详细trace，核验on/off|196|2|
|门|两例非干扰核验全部通过才可继续；失败即停，以下预算不意味着失败后仍执行|0|0|
|3|4718原evaluate再次完整on，只采剩余8目标详细trace，两已通过控制目标不重复采正式trace|196|8|
|4|4719原evaluate完整on，只采10目标详细trace|196|10|
|5|4720原evaluate完整on，只采10目标详细trace|196|10|
|合计|5×196|**980**|**30=2+8+10+10**|

off对照的必要逐步基准/流式核验仍须由B实施方案定义；“无详细trace”不能被误写为没有任何比对证据。原批所有同伴必须执行，详细trace筛选只决定存哪些目标的诊断，不减少回合数。980是拟议全门通过路径预算，不是已运行耗时，也不是已批准预算；仍需监督者核时间/磁盘/截止与B派发。

### 8.2 严格守门：新增原批调度包装为208回合

控制目标固定4718随机组一例、语义组一例，各属于不同的16宽原批。严格顺序为：off两批32回合，on两批32回合只采2个控制目标；全部过门后，4718剩余8目标仍分布在原validation batch3、transfer batch0、transfer batch2，须再跑3批48回合；4719与4720各3批48回合。总计 **32+32+48+48+48=208**，详细目标trace仍为2+8+10+10=30。

也可从144个原批正式采集回合推导：首次门off32＋on32，共额外64；过门后正式采集144但跳过两个已采控制目标的详细记录，总208。与旧176的差32，来自旧方案把on两批同时用于采同批其余目标，严格门要求其余目标过门后重新运行；整批同伴执行无法代替事后不存在的早期详细trace。208方案仍需原批选择/派发包装，不能通过原evaluate参数直接实现，故不因回合较少自动优先。

### 8.3 784与176成立的条件及当前推荐

- **784=4×196**：监督者明确接受4718 on对照调用在两例通过前，附带保存其余8目标详细trace，并在门通过后才将其纳入正式分析。即便先标“待验证”再使用，采集的先后顺序已改变，仍需监督者裁决，不能从“以本次轨迹分析”推定获授权。
- **176=144+32**：同理需允许on两批门前附带采同批其余目标详细trace；还需新增原批调度包装。门后只补尚未采的批，不重复两控制所在批。
- **当前推荐为980**：保留原生产evaluate与先后门，实施调度变化最少；**208**为需要新调度包装的较少回合备选；784/176仅列为待监督者裁决的合并采集优化。四种方案均超原30+2回合上限，先报监督调整，A不执行、不改生产入口、不视为授权。

计数可复核见 [budget-order.json](../../../../agent_logs/task9/task9.8/task9.8.2/budget-order.json)。本次只修正文档计算/条件，未重新生成输入audit.json，原22对源码/30目标/原批证据及SHA不变。父登记SRC-1366时须采用本节最终口径，同时保留先前784/176及父发现的纠正记录；实际模型/强度仍未知，Codex GPT6.1sol/high与Claude Sonnet5.5/high推荐不变。
