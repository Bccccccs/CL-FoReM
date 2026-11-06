# task9.11 · 冻结协议与分阶段派工

> 最新用户采纳与准备交付见[RESULTS §21](RESULTS.md#21-用户采纳后task91117准备适配与独审交付2026-11-04)：.17收据原语/非执行草案限定通过，真实完整链仍NOT_READY；原窗/预算和旧FAIL不变。

> **最新交付（2026-11-04）：SRC-1417 P1 GPU两账修复与独立审核done；真实NOT_READY。** 冻结170源 `0bbda355…7476c1a9`，父132项、独立54项同SHA通过；CPU仅加原worker账，GPU按设备/区间去重并与预留分列；篡改反例已修，旧FAIL/STOP/UNKNOWN保留。详[父RESULTS §17](RESULTS.md#17-src-1417-p1-gpu两账修复最终交付2026-11-04)、[.13实施](task9.11.13/RESULTS.md)、[.14独审](task9.11.14/RESULTS.md)及[SRC-1420](../../../SOURCES.md#src-1420)/[1421](../../../SOURCES.md#src-1421)/[1422](../../../SOURCES.md#src-1422)。

> **此前F1/F2交付：跨时间与新增审核成本联合修复、独立审核done；当时真实NOT_READY。** 统一168源码artifact `c8523c9a…11ef177`，父116项、独立130项及另一次原件归档联合执行通过；旧件不变，旧C/会计/历史UNKNOWN/真实执行合同仍待决。详[.11完整矩阵](task9.11.11/RESULTS.md)、[.12独审](task9.11.12/RESULTS.md)、本文末节及[SRC-1413–1415](../../../SOURCES.md#src-1413)。

> **此前交付：R1–R5工程集成与独立替身验收完成，真实NOT_READY。** 同v3 artifact `1ba4e989…9105b1`，父81/独立86项PASS；旧C/历史UNKNOWN与会计/执行合同待决定，无真实许可。详[完整矩阵/预算/准确CLI](task9.11.9/RESULTS.md)、[独立裁决](task9.11.10/RESULTS.md)、[SRC-1408–1410](../../../SOURCES.md#src-1408)。


> **上一轮历史交付（2026-11-03）：review，修复与独立审核完成；结论不能放行（NOT_READY）。** 启动反例/实际退出见证链与计费封口合成PASS；最外层发布/退出尾及旧完整成本UNKNOWN，旧C完整性FAIL保持。候选合同已封存但不可执行，未签训练许可。[SRC-1403](../../../SOURCES.md#src-1403) · [SRC-1404](../../../SOURCES.md#src-1404) · [SRC-1405](../../../SOURCES.md#src-1405)。

> **上一轮历史交付（2026-11-03）：review，准备与独立审查完成，等待正式执行派发；真实执行 NOT_READY。** .5最小阶段持久化/预算补丁、.6独立37项合成PASS；完整host退出与真实Docker尾时UNKNOWN，旧STOP未解除。4000 smoke消费/980评估、正式0/test0保留；不重启旧run，不重置预算/截止。[SRC-1399](../../../SOURCES.md#src-1399) · [SRC-1400](../../../SOURCES.md#src-1400) · [SRC-1401](../../../SOURCES.md#src-1401)。

> **上一轮历史交付（2026-11-03）：review，仅规划复核，等待正式执行派发。** 已有task9.11曾实施到smoke并因监督终态记录缺失而STOP，正式3M训练与独立test未开始；下文早期“全部尚未执行/文件不存在”及后来“active”均为历史时点，不是当前状态。本轮未改实现或运行实验，不恢复旧run、不新增重复预算。科学方案沿B1-L唯一变量；未来执行须先处理既有STOP并重核窗口/余额。[SRC-1398](../../../SOURCES.md#src-1398) · [本轮交接](../../../agent_logs/task9/task9.11/20261103-codex-plan-rehandoff.md)。


**review；仅规划交付，以下新实施/实验/测试命令均尚未执行。** 数值类别：沿旧协议与实测分别引用SRC-1359/1360/1361，新增记录/预算/验收均为[SRC-1387](../../../SOURCES.md#src-1387)、[SRC-1388](../../../SOURCES.md#src-1388)、[SRC-1389](../../../SOURCES.md#src-1389)、[SRC-1390](../../../SOURCES.md#src-1390)登记的工程选择，不是文献最优或已测上界。

## 0. 递归规则、负责人及执行边界

每层恰有TASK/PROCEDURE/RESULTS；子编号继承父编号。委派前建立子三文档、范围/模型强度/输入/日志和验收关系；父读原件独立汇总，不把子自报当通过。以下A–E是后续**顺序阶段**，不是已启动的新子任务；若未来再委派，先建相应稳定编号及三文档。

|本轮子任务|负责人/模型请求|依赖与边界|父验收|
|---|---|---|---|
|[9.11.1 TASK](task9.11.1/TASK.md) / [流程](task9.11.1/PROCEDURE.md) / [结果](task9.11.1/RESULTS.md)|Codex证据审计，sol/high|与父成本整理独立；只读源码/原trace，只写自己文档/日志|复查原字段、源码、未知和最小补证|
|[9.11.2 TASK](task9.11.2/TASK.md) / [流程](task9.11.2/PROCEDURE.md) / [结果](task9.11.2/RESULTS.md)|另一Codex独立方案审查，sol/high|父初稿完成后；仅自身三文档/日志|父逐项裁决并修订；实现/实验仍未执行|

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需独立核科学合同、因果与资源。未来常规执行可GPT6.1sol/medium或Sonnet5.5/medium；本轮委派模型只限sol/terra/luna，Claude不派。请求与实际后端分开，不自动切当前模型。[SRC-1385](../../../SOURCES.md#src-1385)

## A. 冻结前准备与无干扰记录（获正式派发后）

先读根AGENTS、ENV、PROGRESS、本三文档及9.10.2独立终验；重核Git/dirty、其他任务、容器/GPU UUID/磁盘/依赖。当前观察到task10 online训练进程，不得按旧ENV或旧“空闲”记录分配它的资源。只读挂载历史root`/home/ybc/projects/CL-FoReM/forem`，隔离新实现/输出。旧69项与运行实际导入路径/设备、地图/seed/配置均重核；大模型不需要为从头训练加载。新代码/四配置/评估清单/阈值/成本口径/种子配对在**任何结果产生前**封存SHA与审查签字。

最小补证只记录自然发生的计算，不作为网络输入、不改RNG/候选/动作/IK分支/判定/提交，训练梯度保持。两臂同一记录实现。详细字段及其解释来自[SRC-1386](../../../SOURCES.md#src-1386)、[SRC-1387](../../../SOURCES.md#src-1387)：

|触发时刻|必须保存字段|能区分什么；仍不能证明什么|
|---|---|---|
|每个真实动作开始；首拒绝时封存当前及前一个动作输入（t−1不存在则NA）|六字段case键＋训练seed/arm/checkpoint/科学版本，segment/action/substep，提交base/q/s、candidate/route identity；原74向量与网络实际preprocess后的128×128×3完整字节/shape/dtype/hash，raw grid与扫描timestamp；previous_action及queue/visible_previous；raw action、实际u/ω/v；均值动作（原评估已有）、不额外采样|确认首失败前策略实际可见什么、是否同输入重复；仅保存当前状态不能重建被丢弃高度结构/可行替代动作|
|首pending&failed子步，判定后、回滚前|试探base/s/目标TCP，IK accepted/status/branch/exact、位置残差m/无量纲CBL旋转残差/角度rad、返回q与held标志；已有原始求解q须在hold之前捕获并明确身份（不能拿返回held q替代）；coll.base/arm/self全部布尔、优先kind；提交/attempted/committed、完整前后状态|区分最早IK拒绝与各碰撞类别、并发遮蔽；IK未接受时的held-q碰撞不能用来判原始求解候选安全|
|上述首拒绝的原几何判定内部|使用的map/robot几何hash、碰撞原语/球对或胶囊/地面见证、对象id及候选姿态、实际参与判定的几何；对应扫描可见性、global observed/height与crop索引/边界/quantization参数|对象在原始扫描/全局格/局部格何处消失，或判定是否符合当前合同；当前布尔API不返回见证时要在**同一原计算**旁路记录，未实现/拿不到就明确unknown，不另调用IK/搜索来假造见证|
|首拒绝后的下一真实动作及该段结束|同一输入/输出字段、commit、距离ρ、yaw、s、原arrived/route_end/reason、failures/stalls、原_finish的success与strict_success|区别重复输入、动作变化和实际恢复；不把拒绝后恢复归入严格成功改善|
|每次候选生成前/抽签后/Core.begin前后（含零动作段）|generated全13槽pose/mask/inplace/info.only_inplace及原地search输出、选择槽/抽签RNG前后摘要；传入progress与Core重算progress/cap、begin前后s/base/q、零段/stall计数；搜索内部样点s/accept/reject状态若本来计算则记录|区分只生成原地/有平移却抽原地、两次搜索差异和零进展形成处；mask有效不证明未选槽能前进|
|每段结束及每回合结束（所有评估case，不限12例）|精确原success布尔、strict、s/length、终点TCP残差m/无量纲CBL旋转残差、failures、stalls、decisions/time/attempt_time、terminated/truncated和触发掩码（允许多原因并存）、动作数/子步数|分开最终到达但有拒绝、零拒绝停滞、带拒绝停滞、失败上限、时间/决策截断及未知，避免从failures=0反推超时|

最小存储策略：动作输入在设备内保留当前/前一窗口，只在首拒绝及下一动作落完整快照；每次begin/finish和所有回合的首拒绝摘要完整保存。原始求解支路/几何见证暂不可得则保留unknown，不能妨碍主指标统计，也不能宣布根因闭合。诊断新增API必须经无干扰门，不可改变原IK分支选择；若无法旁路读取，删去该因果结论并记录缺失，不以扩大实验补齐。

**可区分的假设及后续触发**：

1. 信息不足H_obs：首次拒绝相关对象在truth中存在、扫描/全局/局部/编码某层确实缺失或混叠，是候选证据；强证据还需同一编码输入对应不同可执行风险/动作的对照见证。单次缺对象不能证明该动作不可避免或新观测一定改善。
2. 有信息但学习不足H_learn：需在相同已提交状态/同目标找到可执行且推进的替代动作，并证明区分风险的信息已在实际输入中；它只排除该时刻“没有任何局部推进动作”，不证明所有网络都可学、完整目标可行或LR是原因。
3. 子目标难执行H_goal：单个原动作拒绝不支持不可行；一小组替代动作都失败也不能证明不可行。候选/轨迹可行性证书或有界尝试只支持对应覆盖范围。

主实验**不运行额外反事实IK/动作/候选试探**。若自然记录仍不能区分，上述字段封存后另提交有界影子反事实协议（固定状态、预算、动作集合、无污染RNG、不提交、不包装策略），再获派发；其IK/环境调用须另计。旧日志无完整输入、原始拒绝IK解、对象见证和未选候选，不能靠离线补算把新计算伪装成旧实测。

## B. 唯一主实验合同

沿9.7单变量构想，但增加本轮冻结诊断/成本/独立任务测试；本节是未来执行唯一入口，旧9.7不另跑。[SRC-1361](../../../SOURCES.md#src-1361) · [SRC-1388](../../../SOURCES.md#src-1388)

|字段|同期C：B1|处理L：B1-L|
|---|---|---|
|起点/训练seed|从头4718、4719|相同；不从B3-5M或历史B1续训|
|科学预算|每run3,000,000消费转移|相同|
|唯一自变量：actor和critic共同LR日程|exp_updates：1e−4×(1e−6/1e−4)^(u/4,999,743)|linear_transfers：1e−4+(1e−6−1e−4)×clip(t/3M,0,1)|
|α|capped，α LR两端1e−6，显式alpha_lr_schedule=exp_updates|完全相同规则；α数值随学习变化不要求相同|
|更新|每10消费转移；首update在t=260，3M时299,975updates（warmup1000只控制随机动作，不禁止此前update）|相同|
|其它|B1配置逐字段继承；256环境、batch256、replay100k、warmup1000、checkpoint250k、log1000；primitive-obb-v1、ghost-v1、sync_v5、cbl_continue及原bootstrap|全部相同|

u为已经完成update数，t为全局已消费转移数；保存/恢复保存u/t、优化器、日程器、RNG、完整环境与pending。profile在250k暂停，scientific_limit仍3M，不能把日程临时归一化到250k。组名/路径/seed仅身份；配置diff白名单除身份外只有lr_schedule，alpha_lr_schedule两组都显式相同。α LR不是第二自变量。C末端LR约7.586e−5仅说明待检日程特征，不推“越小越好”。

固定原100随机validation（50 sparse＋50 standard）与96语义（24图×4既有episode）每250k评估一次，全部评估同一确定性tanh(mean)策略；不选峰值。主开发比较固定3M最终与2.5/2.75/3M末三。随机/语义、每seed、每case配对单列；现24语义图也已用于设计，因此都标为**开发证据**，语义分数不作中途选模/停止。历史B3-5M194/300、132/288只列参照，绝不作为3M实验的因果对照。

## C. 能力、机制与效率判据

所有严格成功沿Core._finish：route s到终点，TCP位置残差≤0.025m、CBL旋转残差≤0.05（无量纲），且failures=0。不要沿用旧记录器r_rad误名。既有定义来源[SRC-1384](../../../SOURCES.md#src-1384)，新验收逻辑为[SRC-1388](../../../SOURCES.md#src-1388)。

- **执行合格**：四run正常完成3M及对应updates、全部评估完整、case身份与合同一致、成本/恢复/pending账本齐全。非有限或保护发散不能从组均剔除。沿旧稳定性要求，仅对每run**随机validation**的末三均值要求>自身随机validation全曲线峰值−15pp；不把该门套到语义或独立test曲线；未完成或不满足者分别报告，不称改善。
- **开发严格成功改善**：L随机最终组均与末三组均均严格高于同期C；同时两训练seed的最终配对差均≥0，至少一个>0。语义最终与末三组均均≥同期C；开发阶段允许语义某个seed为负，必须完整展示，不能把语义任一seed负差偷加成中途停止条件。没有统计显著性或两seed普适提升宣称。上述非负/严格正值是工程决策门，不是显著性阈值；达不到即停止本LR配置，不追加seed/改选峰值。
- **机制辅助**：episode首次拒绝率=存在任一pending&failed的完整回合/完整回合；首次类别IK/base/arm/self互斥按原优先级，另列全部碰撞标志。记录首拒绝动作序号与前缀长度，首动作即拒绝另报；不能把“首次拒绝率”误解为仅动作1失败率。失败动作次数与回合数另表。所有回合原路线success、无拒绝stall、带拒绝stall、失败上限、截断、其它unknown分别报告。首拒绝减少却stall增加需公开，不能当严格成功改善。若两域L首次拒绝率均降低且stall失败率均不增加，才称“拒绝机制方向得到支持”；若还两域stall均严格减少，才称完整减少两类失败目标获支持。仅严格成功提高则只称该能力指标获支持，不能宣称停滞已修复。
- **恢复**：只对有首次拒绝的case按旧同段R/N/U判据复算，>1e−6m门沿9.8；commit、yaw或route_end不替代原目标arrived。恢复统计不进入主验收。
- **学习曲线/配对**：所有250k点的strict、首次拒绝、终点到达、stall分域画表；逐seedΔL−C和每case双方成功/仅L/仅C/双方失败四格。case键保map_id、seed、stream_index、role、source_split、proposal_seed；训练seed是两次重复，地图内episode/多checkpoint不当作独立训练seed。不同策略候选轨迹自然分叉，不要求动作后缀一致。固定250k等间隔严格成功率算开发AUC=12个点的算术均值（只在0.25M–3M网格，非从0推积分），高于C才称曲线样本效率改善；AUC未提高只能说末端同交互预算能力改善。
- **效率**：分别报告env_actions、consumed、pending、子步attempted/committed、reset/初始化、采样/搬运、推理、update、日志/评估/保存/恢复/排空和等待；计训练进程从首次启动到最终退出的全时段，恢复前后与暂停等待不漏记。同时给累计执行worker wall（包括初始化/采样/训练/评估/日志/保存/恢复/退出）与首启到末退日历wall，暂停审查/队列等待单列，绝不删掉后者只报纯训练；组间等待差异不能归因LR。给累计worker时、单卡GPU保守占用与全局墙钟，阶段嵌套不相加；CPU/仿真时间与CUDA kernel时间分开。学习曲线按累计完整训练wall再画一次。周期评估次数/每次wall、每次checkpoint字节/fsync/保存wall及恢复wall单列，不把去掉评估后的纯训练速度叫完整效率。
- **推理延迟**：只用实际评估的相同批形状/活跃数/设备，记录预处理＋actor端到端P50/P95/P99与CUDA事件时间、batch总耗时/有效动作数；混合尾批单列。预冻结的10%主门只取**3M final开发评估、input batch=16且active_count=16**，随机与语义各自、每arm/seed至少100次自然推理调用；不够判UNKNOWN，不新增forward凑样。100是P99至少覆盖百次自然调用的工程最低记录量，不是精度/显著性保证。每seed/域/arm的P95/P99用线性插值经验分位数；域内两seed等权算分位数的组均（不混合原样本），ratio=组均L/组均C，C为0/缺失则UNKNOWN。随机与语义的P95/P99共四个ratio都≤1.10才过该匹配批次推理门；任一>1.10即成本门未过。所有其它(batch,active_count)分层的计数、分位数/比值分别列出，无共同支持的层UNKNOWN；不得把主门结论扩展到这些层或混合尾批。同步计时开销双方相同并计入评估cost；未测batch1则不声称部署单任务实时性。无额外微基准、模型forward或环境回合。
- **同成本裁决**：先比较相同3M交互量，绝不用L多训来补成绩。以累计完整执行worker wall为成本比（含全部训练阶段及周期评估/保存/恢复，排除另列的非运行审查等待；首启到末退wall仍完整报告）。L最终能力过门但该完整执行wall组均比C增加>10%或推理P95/P99任一增加>10%，标“能力/成本权衡，效率未通过”，不自动采用。≤10%仅是工程容忍，不等于提速；只有同交互量能力过门且累计完整执行wall组均≤C，才称本实验执行墙钟效率不差；只有首启到末退wall也不更差且无不平衡外部等待，才可作端到端日历wall结论；严格更低且各seed时间差公开才称观测到墙钟降低。正式声称本实验匹配批次下的总体效率改善还须AUC高于C且上述推理门通过，未覆盖batch/active层明确不在此结论内。若仅成本门未过，停止自动晋级，交回权衡，不改科学合同换吞吐。10%沿9.10容忍思想、本次对完整wall/推理预登记工程选择，非噪声显著性界。

## D. 有界资源、停止与完整账本

[SRC-1389](../../../SOURCES.md#src-1389)登记以下工程预算，实际执行前须正式派发并写上海时区绝对起点T0/截止T0＋58h。一张现场核实空闲GPU串行，不能据四卡理论缩工期，也不停止task10。无卡则NOT_READY，不启动计费检查/训练；T0定义为获派后首项资源准备开始，等待一并计入。

|阶段|依赖/上限|环境与评估计数|
|---|---|---|
|A冻结/CPU与G1 GPU合成/保存恢复合同检查|≤1,800worker s；独立实现审查后才B|0真实环境转移/0评估回合；G1只合成输入，不跑原旧测试集内可能包含的环境测试|
|B smoke|C4718→L4718→C4719→L4719；每组≤4,300worker s|每run512保存→恢复到1000，四run≤4,000消费转移；每run一次完整196，共784|
|B记录非干扰门|在上述C4718/L4718的同一1000 checkpoint各附加一次ON评估，≤3,600worker s|smoke原196用OFF，新增ON各196，共392；逐动作/子步/状态/RNG/原终态精确比；原始判定支路/zero段合成覆盖另审；没有比较到的真实分支明确记录|
|C正式|四run各≤12h；顺序C4718→L4718→C4719→L4719；各250k暂停profile审后续跑|各3M，首250k在内；4×12×196=9,408评估回合|
|D一次独立测试|开发门通过且全部合同/模型身份封存后，≤4worker/GPU h|四final actor×(200随机test＋96新语义任务)=1,184，见E；不得调用旧完整196入口冒充新test|
|总上限|≤58worker h、≤58单卡GPU h（保守暴露）及≤58h全局wall；准备、审查等待、保存/退出/最终独立验收均计入|正式12M＋smoke≤4,000=12.004M消费转移；开发10,584＋独立1,184=11,768评估回合上限|

“环境交互预算”另列实际env_actions/attempted子步，向量pending超前不能隐去。smoke每run到1000最多保留255条pending，四runenv_actions合计上限5,020（256环境一批的推导）；若实现不能保证此上限则开跑前NOT_READY。正式最终每runenv_actions=consumed=3M，不能越界或丢弃pending；250k等中途多生成部分保存在原3M账本中。正式采样/初始化失败尝试单列，所有评估启动含未完成/同伴回合计入上限，不自动重试。

48h正式＋1800/3600＋8600/3600＋1h记录门＋4h独立测试=55.889h，预留到58h（工程取整）；剩余2.111h为准备/队列/审查/退出余量，非新实验预算。旧B1实测10.161/10.265h含周期评估保存，12h代理沿9.7；新增392和1184回合按9.10每196约1,059.188worker s估算分别约0.588h、1.777h，分别预留1h/4h，不是保证。正式250k成熟窗口要实测全周期，模型/优化器/replay CUDA实际设备、资源与profile覆盖全部通过；预计装不入剩余预算就NOT_READY，不能缩步数/跳评估/延时。C、L首250k都审，L不能仅借C profile放行。

每run及全局保存退出预留起草1,800s（沿9.7工程代理，已含上限）；512/1000恢复＋满replay250k profile实测排空/写盘/恢复后重新核定，不足则NOT_READY。临近deadline按本run STOP安全退出，PID/容器/STOP路径与监控记日志；外部硬截止只限制本任务命名空间，不误杀他人。

存储：历史B1-seed4718全部pt仅stat计414,474,404,996B，四run保留同样12周期＋final约1.508TiB；成熟profile/恢复/临时副本还会增加，拟≤2TiB新输出总额，含logs/tmp/审查副本；诊断/日志≤8GiB，单次新满checkpoint临时空间先预留40GiB。此是历史代理，不是新运行精确尺寸；新250k确认剩余可行性。保留旧/新科学证据，不删旧checkpoint来过预算。未获额外同意不执行压缩/异步/并行改造，不能为成本改变科学条件。[仅stat证据](../../../agent_logs/task9/task9.11/checkpoint-storage-stat.json)

非有限、文件/身份/哈希/隔离/非干扰失败立即落盘停；500k以后Q_abs_max>自身500k参考10倍按旧保护停，参考取值/检查频率沿旧冻结实现，无样本剔除。用户停止、资源截止和保护发散分开。完整性失败不重跑；预算未完成不判科学阴性，方向没有通过证据，交回问题。开发能力门阴性不运行独立test，保留封存集合给未来独立协议；禁止围绕本结果继续扫LR终值、追加seed或续5M。

## E. 冻结后一次独立任务测试

独立测试的**选集规则现在冻结，实际manifest与模型清单在方案冻结后、测试首次运行前由独立人封存**；全套结果一次性揭盲，不能看完一个seed再决定是否继续或改方案。[SRC-1390](../../../SOURCES.md#src-1390)

1. 随机：旧cube-pool-v2的200个test地图及evaluation-seeds.json的test行，先核此前未进入训练/验证/调参。沿已有同分布与环境合同；完整200固定任务，不按模型成败选case。若发现test泄漏则不称独立、不自换池，停止测试阶段并交回新拆分需求。
2. 语义：现有24图，每图4个**新任务seed**，地图不换、场景分布不偷偷简化。新seed取SHA256(`task9.11-final-v1|semantic|map_id|episode_index|nonce`)前8hex转uint32，nonce从0起取最小不与旧episode/proposal种子或已选seed冲突者；固定episode_index=0..3。保留collision检查清单及manifest SHA。它是已知24图上的独立episode测试，**不是未见语义地图测试**，不能用于地图级泛化宣称；若研究要未见整图，另立生成/划分协议，本轮不借名称替代。
3. 四final actor只在开发门通过后统一冻结、只选3M final，不挑最佳checkpoint或seed。测试环境构造/候选/初始化规则沿原实现，改evaluation_plan只增加显式test role/输入manifest，不能绕过原身份校验或把test当validation。每case同初始随机流与候选流规则，允许策略后续分叉；测试结果不影响训练/选模。
4. 输出独立随机/语义的全部逐seed strict、Δ、配对四格与相同辅助指标/成本。最终支持要求两域L组均strict都>C，且每域每seedΔ≥0；仅开发改善或单域改善就只报告相应范围，**不宣布最终两域能力改善**，不追加测试/调参补过。首次拒绝/stall及效率结论仍按C单独门，不用strict通过覆盖其它失败。此为两seed探索复核，无泛化/显著性承诺。

## F. 后续允许的实现文件与命令合同（全部尚未创建/运行）

新实现统一在`forem/`内隔离，不改旧task9_opt准入矩阵/已过期STOP_AT，不使旧U20/E15/R200发布令牌接受新组。原`task7_*`/`task8_*`/`task9_opt/frozen`、task9.8–9.10脚本与所有历史产物只读。获派后可写白名单：[SRC-1391](../../../SOURCES.md#src-1391)

|拟议新文件|范围|
|---|---|
|`forem/config/task9/task9_11/{protocol.json,C_seed4718.json,C_seed4719.json,L_seed4718.json,L_seed4719.json}`|单变量配置、阶段预算/绝对时刻、路径和role清单；不改旧配置|
|`forem/src/task9_lr/{runtime.py,admission.py,diagnostics.py,evaluation.py,origin-manifest.json,tests/…,runtime/src/…,runtime/config/…,frozen/src/…,frozen/config/…}`|隔离激活/显式B1与L矩阵/版本锁，旁路记录A字段，固定开发和一次test入口；新runtime冻结副本引用清单记录来源d198e5c和实际dirty字节；复制必要task9_opt runtime训练/恢复代码，不静默改算法|
|`forem/scripts/task9_11/{prepare.py,worker.py,supervise.py,audit.py}`|只在新namespace准备、单卡阶段调度/截止/锁/账本、独立标准库审计；test manifest封存；无动作过滤/选择包装|
|`forem/results/task9/<新run-id>/`、`forem/logs/task9/<同run-id>/`|原件隔离只读，新账本/模型/trace/汇总；新目录原子创建，重名拒绝|

已有`task9_opt/runtime.py:GROUP_AXES/validate_formal_config`只允许旧三方向，`admission.py:STOP_AT`是过期旧日期，因此不能直接套旧worker命令。下面是**未来入口必须实现并经独立审查的CLI合同**，目前文件不存在，不能当成可立即执行的现成命令；代码准备是正式派发A的交付。

```bash
# 宿主只读预检；本轮仅列示，不执行下面整个块
cd /home/ybc/projects/CL-FoReM-task9
git status --short
sg docker -c 'docker ps --format "{{.Names}} {{.Status}}"'
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_gpu_memory --format=csv
# 以下在未来获派的隔离容器内，/workspace仅挂本树forem，新out单独可写
python3 -B -u /workspace/scripts/task9_11/prepare.py --protocol /workspace/config/task9/task9_11/protocol.json --output /output/freeze
python3 -B -m pytest -q -p no:cacheprovider /workspace/src/task9_lr/tests --ignore-glob '*environment*'
python3 -B -u /workspace/scripts/task9_11/supervise.py --protocol /output/freeze/protocol.json --phase smoke-and-gates
python3 -B -u /workspace/scripts/task9_11/supervise.py --protocol /output/freeze/protocol.json --phase train
python3 -B -u /workspace/scripts/task9_11/audit.py --run /output --phase development --output /review/development
python3 -B -u /workspace/scripts/task9_11/supervise.py --protocol /output/freeze/protocol.json --phase final-test --release /review/development/release.json
python3 -B -u /workspace/scripts/task9_11/audit.py --run /output --phase final --output /review/final
```

单worker CLI须支持`--arm C|L --seed 4718|4719 --phase smoke512|smoke1000|profile|remaining|gate-evaluate|final-test --protocol PATH --output PATH`，无有效阶段签字/剩余预算则拒绝；smoke使用独立配置total_transfers=1000（L的线性日程也仅按此smoke预算归一化；不作科学效果结论），512只是暂停点，科学limit不从512变更；正式始终3M。CLI测试只验证配置差分、u/t/α日程、pending恢复/零段计数、原success/单位/首次类别、无干扰/RNG、累计deadline和拒绝旧token；GPU G1仅合成输入/回放，不额外启动环境。启动前要核测试收集清单，不能沿旧全套pytest意外带起环境。独立audit不导入实施score作为唯一判分，原JSONL自行复算。

## G. 可直接交给执行者的分阶段提示词

**A · 正式执行获派后先做准备；不自动越门**
> 你是task9.11实现准备者（优先GPT6.1sol/high；常规编码可sol/medium或获派terra）。到/home/ybc/projects/CL-FoReM-task9读根AGENTS、PROGRESS、task9.11三文档及9.10.2独立核验。当前只执行PROCEDURE A/F的隔离代码与配置准备、零真实环境测试；按照B1-L唯一变量及新旁路字段建立源码/配置/评估manifest，核只读输入和活动task10资源，不改旧实现或原件。交回diff、精确命令、合成测试、源版本、阶段账本与NOT_READY/READY_FOR_G1。若委派先建子三文档和写边界。不得仅凭本提示词启动smoke/训练/独立test；等待独立实现审查和本次正式资源释放令。请求/实际模型强度分别记录，更新独立日志。

**B · 资源释放与实现审查通过后做smoke/门**
> 按task9.11 PROCEDURE D获批绝对窗口和预算运行G1→四个512/恢复1000 smoke→C/L4718 OFF/ON门，单卡串行。新真实训练转移总≤4000、smoke与门合计1176评估回合；G1零真实环境。先核采集分支、原成功语义、LR/α与pending恢复、CUDA路径、记录非干扰和成本；任何门失败保留证据停，不重试或调整科学合同。交回完整原件、账本、预计四3M可行性，独立审核后才允许正式首250k。无有效释放令不自行运行。

**C · 正式训练释放后**
> 按task9.11 B/D执行C4718→L4718→C4719→L4719，各科学limit3M、每250k完整196；首250k暂停测成熟全周期、保存/恢复和剩余工期，每run对应profile经独立签字后继续原3M。env_actions/consumed/pending完整记账，不跨预算、不缩步/跳评估/改语义，不触碰其他任务。每run12h、全局58h/新输出2TiB等以正式发布令更早截止为准。完成只交四final与完整曲线/原字段/成本，独立开发验收前不运行test、不自动替换B3或task10下层。

**D · 开发门通过后的独立任务测试执行者**
> 你独立于训练/选模，读task9.11 E，核四3M final及方案/代码/阈值已封存，检查200随机test未泄漏，再封存随机test和24已知语义图新任务seed manifest。一次运行四模型共1184回合，上限4h且计入原全局58h。不得逐seed揭盲调参、重跑/换case或把已知语义图说成未见图。任一缺项安全停并交未知；所有结果完整回传，不将test用于方案选择。

**E · 独立验收提示词（必须另一人，优先sol/high）**
> 你是task9.11独立验收人，遵循根AGENTS、该任务三文档及阶段已授权范围。只读原件，从配置逐键差分、实际导入路径/源码SHA与四run输入身份核唯一变量；从原JSONL自行复算每域/seed strict、首次拒绝类别/分母、原success、无拒绝及带拒绝stall、多原因终止与unknown、配对和全部曲线，严格区分动作与回合。独立核smoke OFF/ON逐步/RNG、u/t/α日程、恢复pending、完整3M/299975updates、保护停止、全部评估/成本/存储/绝对截止；训练全wall不能用恢复后summary替代。开发先按C出结论并签/拒final-test release；最终独立test仅一次且manifest预封存，不替实施者补跑或修数据。分开判执行合规、开发能力、拒绝/停滞、样本/墙钟/推理效率、最终两域复核。逐项PASS/FAIL/UNKNOWN和证据路径写独立日志，交父核验；不以loss下降或恢复2/12替代strict。不可把两个训练seed扩大成普适/显著结论，不自动部署。


## 2026-11-03 正式派发与当前执行覆盖说明

用户“派发吧”已授权按本已审方案执行，状态active；上文review/未来/待批准文字保留为设计阶段历史，不要求用户再次逐门批准。科学合同B–E不变，门须实际独立通过；代码/实测失败不重试，超预算不扩。T0=2026-11-03T17:18:20+08:00，截止2026-11-06T03:18:20+08:00，run `t9.11-lr-20261103T171820+0800`；详[窗口](../../../agent_logs/task9/task9.11/execution-window.json)及[SRC-1395](../../../SOURCES.md#src-1395)。

|子任务|负责人/请求模型|依赖与验收|三文档|
|---|---|---|---|
|9.11.3 隔离实施与分阶段执行|Codex sol/high|先A/F零环境→.4代码审查→G1→smoke门→父/.4审核→每run250k profile/remaining→开发通过后一次test；独立门真实通过才续进|[TASK](task9.11.3/TASK.md) / [PROCEDURE](task9.11.3/PROCEDURE.md) / [RESULTS](task9.11.3/RESULTS.md)|
|9.11.4 独立实现/性能/结果验收|另一Codex sol/high|实施稳定版后审代码；独立核G1/smoke/成熟profile/开发与finaltest原件，父汇总；不写实现/共享文件|[TASK](task9.11.4/TASK.md) / [PROCEDURE](task9.11.4/PROCEDURE.md) / [RESULTS](task9.11.4/RESULTS.md)|

模型推荐仍GPT6.1sol/high、Sonnet5.5/high，理由为跨模块科学合同/恢复/研究设计；本次仅派sol。父负责只读现场资源与统一账本/来源协调。GPU0为当前空闲优先选，GPU1有task10不触碰；正式启动前再次核UUID/进程与锁，当前快照不作长期空闲保证。

父派发执行细化（SRC-1396）：完整首拒绝/候选/finish诊断范围为全部评估case；训练只沿原训练统计/交互与pending/profile，不把12M训练回合全部写三窗口。实际独立门签字由.4代理执行，.3必须核签字绑定的源码/配置SHA、阶段、原证据SHA、剩余资源及绝对截止；真实门PASS后在原授权内自主续进，无需用户或父在每一门重复点头。空白预签、只凭自报/文件名/旧PASS均禁止。父保留最终原件核验与共享汇总职责。执行政策见[execution-policy](../../../agent_logs/task9/task9.11/execution-policy.json)。最终test由未参与训练的.4独立执行冻结入口，仅当开发门、泄漏核查及四final/manifest封存完成且剩余总预算可行时，写本run/final-test与所属审查日志；.3不执行或逐seed利用test结果。此安排不新增回合/训练、改变科学合同或取消独立验收。


## H. 本轮重交接的执行前置说明（2026-11-03，仅规划）

本节修正F/G的时点，不改B–E科学合同；模型推荐仍GPT6.1sol/high、Sonnet5.5/high，独立审查应另一人；本轮没有新增委派。既有.1/.2证据审计和规划审查已完成，.3/.4执行链在smoke监督完整性门停止。编号和三文档递归关系保留，不新建同职责节点。[SRC-1398](../../../SOURCES.md#src-1398)

**派工入口顺序**：先正式派发下述准备交接 → 独立审查修复方案/代码与账本 → 明确被停止阶段如何处置及有效窗口/剩余额度 → 原B–E逐门执行。当前仅交规划，下面提示词与命令均未执行。

> 准备执行者：先读本三文档顶部当前状态与SRC-1397/1398、.4原STOP签字。沿F白名单，优先提交监督中断后独立持久化退出证据与预算守卫的修复方案；模拟父监督中断、子进程先/后完成的竞争，覆盖不能依靠finally处理的SIGKILL情形，均使用零环境替身。不要把缺失历史host exit/wall补成成功。逐项对照F设计CLI与现有prepare/worker/supervise/audit实际参数，交精确命令、版本差异、依赖与待放行阶段；不得照抄旧protocol/旧release启动。科学C/L配置、记录器及严格成功语义不改。将已有4000/980消费及未知成本保留入账，明确新准备成本计入何处；无法证明剩余资源可行则报告NOT_READY，不自动重置窗口或申请后即执行。当前提示词供未来派发，本次不实施修复。

> 独立验收者：先核原STOP及7个引用SHA，再核准备者提交的中断/退出持久化设计、实际CLI和只写本namespace边界。旧C4718原件非干扰只支持该次smoke，不代替L门或成熟profile；未测字段保留UNKNOWN。修复不能把主自变量从LR日程变成环境、候选或动作包装。明确恢复方案是否需要重测及其预算，不自行补跑。后续沿G的独立验收提示词从原件复算科学指标，区分执行完整性失败、科学阴性与效率未过；不得用历史PASS给改版预签。

可列入准备验收的**只读命令**（本轮不运行项目脚本）：

```bash
cd /home/ybc/projects/CL-FoReM-task9
git diff --check
rg -n 'add_argument|def dispatch|start_new_session|finally' forem/scripts/task9_11
```

未来合成检查与运行命令沿F模板，但必须由准备者按实际CLI重新列出并由独立审查确认；不得将`--ignore-glob`本身当作测试无环境证明，要先审所有收集项。当前不提供一条绕过STOP的可运行恢复命令。旧完整实验上限不是剩余额度，当前没有授权的新起点/延长时限。此为已有失败后的必要执行依赖，不改变唯一主实验。[SRC-1398](../../../SOURCES.md#src-1398)


## I. 2026-11-03 监督修复准备派发（不派真实执行）

最新用户授权仅准备：新增顺序子任务[.5 TASK](task9.11.5/TASK.md) / [流程](task9.11.5/PROCEDURE.md) / [结果](task9.11.5/RESULTS.md)，负责人sol/high最小监督修复；稳定后[.6 TASK](task9.11.6/TASK.md) / [流程](task9.11.6/PROCEDURE.md) / [结果](task9.11.6/RESULTS.md)，另一sol/high独立审查，禁止写实现/共享文档。父逐项核原件汇总，沿本文件递归规则；旧.3/.4不恢复，原STOP不变。范围/日志见[准备记录](../../../agent_logs/task9/task9.11/20261103-codex-supervision-preparation.md)。推荐GPT6.1sol/high、Sonnet5.5/high（进程竞争与预算恢复审查），实际配置另记。

## J. 准备验收后的续跑合同与精确CLI（仅计划，全部真实命令未执行）

本轮准备/独立审查已完成，真实执行NOT_READY；结论及边界见[.6正式裁决](../../../agent_logs/task9/task9.11/task9.11.6/FINAL-INDEPENDENT-VERDICT.json)。独立人未修改实现/共享文档；父复核原stdout/rc/SHA。推荐GPT6.1sol/high、Sonnet5.5/high（完整监督与成本合同审查），实际型号/档位未知。[SRC-1399](../../../SOURCES.md#src-1399) · [SRC-1400](../../../SOURCES.md#src-1400)

**先恢复准备合同，不直接恢复旧run**：未来正式派发须明确原FAIL阶段处置、C科学原件复用裁决、新续接namespace/账本继承与新release身份，T0仍2026-11-03T17:18:20+08、截止仍2026-11-06T03:18:20+08；不得重置总额。当前protocol_read仍锁旧run，旧out/freeze存在、未闭活动与新源码SHA均阻断运行。新namespace准入适配尚未实现；要另行正式派发必要适配/独立审查，不把下述现入口命令称可直接续跑。[SRC-1401](../../../SOURCES.md#src-1401)

1. 明确完整host退出/发布尾的独立见证与成本合同，并修复/验证prepare生命周期；当前仅阶段持久完成与client rc，不冒称完整owner/worker wait status。真实Docker控制、fsync/OS上界和成熟性能未证，继续NOT_READY。新协议必须继承旧4000/980和UNKNOWN，并纳入本轮.5/.6/父准备成本；现external roots仅旧.3/.4，不能漏计新增路径。
2. 原四smoke/检查点和C4718该次OFF/ON科学原件可只读引用；新源码的独立代码/冻结审查与G1必须重测。smoke剩余0，不能重跑四组；新正式从头3M，不从1000 smoke续训。旧源码release不迁移到新SHA。C原host FAIL保留，科学非干扰只支持该次轨迹；证据复用须独立裁决，不能当整门PASS。
3. 若独立裁决要求C ON重测，则现剩10788已全部分配（L ON196+正式9408+test1184），无额外196；继续NOT_READY交用户明确范围/预算处置，不挪评估、不放宽门。本轮不批准重测或增加额度。
4. 完成前述合同并正式获派后，才按新代码G1→未执行L ON196独立门→C4718/L4718/C4719/L4719各自从头250k profile及审核→同run remaining至3M推进。每个profile成熟回放/CUDA/完整周期/保存恢复尾均须实测，L不借C。无法装入原剩余窗口/字节/预算则停，不缩步/跳评估/延时。
5. 开发strict、首次拒绝、停滞、最终到达、曲线与全成本按B–D分别裁决；恢复仅诊断。开发门通过且四final/test manifest/泄漏核查/余额独立封存后，最终一次1184回合测试保持E，不用于选方案，不自动晋级task10。

本轮已执行且可复核的**零环境精确命令**（不是授权真实运行）：

```bash
cd /home/ybc/projects/CL-FoReM-task9
python3 -B /home/ybc/projects/CL-FoReM-task9/forem/src/task9_lr/tests/test_supervision_stdlib.py
python3 -B /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/task9.11.6/independent_stdlib_checks.py
python3 -B /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/preparation_readonly_audit.py
```

每次测试前先核专用收集/SHA，不用旧pytest/conftest；最终原件分别在.5 attempt07、.6 final-suite-independent与independent-attempt02，不把计划当新执行结果。

|实际入口|准确参数合同/未来绑定|当前拒绝/限制|
|---|---|---|
|prepare.py|`--protocol PATH --output DIR`|旧freeze已存在；它只封存源码，不创建/审查新容器生命周期。|
|supervise.py|`--protocol PATH --phase prepare`|本版明确NOT_READY；--release不恢复该路径。|
|supervise.py|`--protocol PATH --phase smoke-and-gates`|组内串行G1/smoke/ON；无单stage host参数，旧started/FAIL阻断。旧四smoke不准重跑。|
|supervise.py|`--protocol PATH --phase train`|依序profile/remaining；仍要求各阶段独立releases和前置门，不等于单个profile令。|
|worker.py|`--arm L --seed 4718 --phase gate-evaluate --protocol /output/freeze/protocol.json --output /output/smoke-L-seed4718`|仅未来经审host守卫与新续接身份下调用，须`/output/releases/gate-evaluate-L-4718.json`，禁止直接绕守卫。|
|audit.py|`--run ROOT --phase development --output NEW_DIR`，或`--phase final`|output是新目录；描述性复算，不签独立放行令。|
|supervise.py|`--protocol PATH --phase final-test`|实际逐arm/seed读取`releases/final-test-ARM-SEED.json`；F中通用`--release /review/development/release.json`不被此phase使用，不能作放行。|

精确旧路径阻断对照命令及各自拒绝原因在[续跑交接](../../../agent_logs/task9/task9.11/20261103-codex-supervision-preparation.md)。当前无合法的新namespace/protocol/release/output绑定，故**不存在可以诚实交付的当前可执行正式续跑命令**；不编造新参数、不套旧run。下一阶段所需派发是先补上述监督/prepare/续接及预算合同和独立审查，再明确授权新G1/L ON/正式各阶段；本轮停在准备完成，不执行这些步骤。[SRC-1401](../../../SOURCES.md#src-1401)

## K. 本轮启动/完整生命周期/续接修复（2026-11-03）

最新授权仅修复与零模型零环境合成，不运行真实Docker控制或实验。新增稳定子编号.7实施（sol/high）：[TASK](task9.11.7/TASK.md)/[PROCEDURE](task9.11.7/PROCEDURE.md)/[RESULTS](task9.11.7/RESULTS.md)；稳定后.8另一sol/high独立验收：[TASK](task9.11.8/TASK.md)/[PROCEDURE](task9.11.8/PROCEDURE.md)/[RESULTS](task9.11.8/RESULTS.md)。沿递归规则，父汇总并核原件；独立人只写自身记录，不能改实现/共享文档。推荐GPT6.1sol/high、Sonnet5.5/high（并发启动、完整成本与续接合同审查），实际后端未知另记。旧STOP/历史评估/预算/截止不变，等待本轮独立是否可放行结论，不签训练许可。

## L. 本轮最终续接合同与准确命令（2026-11-03；不授权真实执行）

递归关系沿K：.7实施→.8独立审核→父核原件汇总；两子仅准备结束，主任务review。推荐GPT6.1sol/high、Sonnet5.5/high因启动竞态与完整计费，实际后端未知。最终[独立逐项裁决](../../../agent_logs/task9/task9.11/task9.11.8/FINAL-INDEPENDENT-VERDICT.json)：启动/退出见证与成本封口合成PASS，原完整成本UNKNOWN，旧C完整门FAIL，真实NOT_READY。[SRC-1404](../../../SOURCES.md#src-1404)

### L1. 生命周期与计费边界

新实现为outer→专用owner→guard→watcher；guard实际wait watcher写watcher-wait，owner实际wait guard写guardian-wait，outer实际wait owner后核全部身份/nonce/rc/发布SHA与已退出状态，持久化lifecycle。stage终态仍只是watcher发布前；容器worker状态/quiet见证与docker-exec客户端rc分开。上层只记录下层实际wait，不让进程自证已退出。

单阶段已见证区间`T_chain − T_reserved`含owner/guard/watcher各自发布与退出，不与嵌套stage/worker时间相加；**完整CLI成本**还应含预约前准备＋outer自身发布/退出＋必要外部观察者成本。后者尚无独立闭账，closed_wall保持UNKNOWN。所有仅PASS+wall_s、无format/旧v1/阶段v2均不得准入为closed成本；旧started/FAIL仍全局阻断，不能通过改格式避开。原统计仅保存已知下界，外层launcher差额按原独立非重叠记录算，不重复加inner。

未来如保持原完整成本要求，需要独立job/命令包围证据实际覆盖outer退出与全部写盘，并将观察者成本另列一次。若想改为保守占额替代缺失actual cost，须另提有依据的上界与明确会计合同变更；当前未给固定数值、未放宽验收。[SRC-1404](../../../SOURCES.md#src-1404) · [SRC-1405](../../../SOURCES.md#src-1405)

### L2. 已封存的合法准备输入/输出

[continuation-proposal-20261103T213737+0800.json](../../../agent_logs/task9/task9.11/continuation-proposal-20261103T213737+0800.json)是**非执行候选**：新identity=`t9.11-continuation-20261103T213737+0800`；提议输出/日志分别`forem/results/task9/<该identity>`、`forem/logs/task9/<该identity>`，当前均未创建。原协议/STOP/7引用与累计快照均绑定SHA，四个C/L科学配置逐字段冻结；原账4000 smoke/980评估、正式0/test0、10788固定分配及UNKNOWN继承。执行标志必须false、stage_releases=[]，旧PASS不迁移为新活动。

父review包[candidate-freeze-20261103T213737+0800/source-inventory.json](../../../agent_logs/task9/task9.11/candidate-freeze-20261103T213737+0800/source-inventory.json)封存160文件artifact `84c986cdb8e7afdc0939b9c686c3f5e7fac48409a9446cb060063cfd13e3912c`、候选/账本SHA及四配置；独立人用真实原件在自身目录另生成review包。只复制源码/JSON，不加载模型，不创建容器或真实run。该schema被execution protocol parser拒绝；不把“结构合法候选”说成“可执行训练协议”。

本轮实际已执行的精确纯准备CLI如下，父原输出/rc见[lifecycle-candidate-freeze-command.json](../../../agent_logs/task9/task9.11/lifecycle-candidate-freeze-command.json)。目录已存在，原命令再执行应拒绝，不要覆盖；下一次如需新快照须使用新的未占用review输出路径并保留旧包。

```bash
python3 -B /home/ybc/projects/CL-FoReM-task9/forem/scripts/task9_11/prepare.py \
  --continuation-contract /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/continuation-proposal-20261103T213737+0800.json \
  --output /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/candidate-freeze-20261103T213737+0800
```

下一步允许核查的现成命令（不运行模型/环境/Docker）：

```bash
python3 -B /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/lifecycle_budget_audit.py
python3 -B /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/test_continuation_proposal.py
```

当前没有已授权的执行adapter、新namespace execution protocol或阶段release。实际supervise仍为`--protocol PATH --phase prepare|smoke-and-gates|train|final-test`，prepare显式拒绝；worker的g1/gate-evaluate/profile等单stage参数不能套给host。未来目标绑定是`<新namespace>/freeze/protocol.json`和`releases/STAGE-ARM-SEED.json`，必须等下面决定与适配/独立审核完成才可生成。本轮不伪造这两个文件，也不提交一条使用旧protocol/旧release的假续跑命令。[SRC-1405](../../../SOURCES.md#src-1405)

### L3. 可复用、须重测与待用户决定的具体差异

- 可复用：旧四smoke的消费/配置/检查点/工程原件与C4718该次科学非干扰记录，只读引用并绑定旧SHA；不能当新源码代码/G1通过，不把smoke1000接成正式3M，不能搬旧PASS/release到新账。
- 必须重测（需后续真实阶段派发，本轮未执行）：新源码/冻结独立代码门、新G1、尚未做的L ON196、四run各自从头250k成熟profile/保存恢复/全周期成本门及remaining至各3M；开发通过且四final/manifest/泄漏/余额冻结后，最终一次1184测试。
- **原C门差异待决定**：原合同要求C ON科学一致与完整host终态均PASS；拟议复用只满足科学部分，完整性FAIL永久保留。若另用新执行完整性门承接，是验收组合变化，必须由用户明确接受且独立协议审核后再实施；当前未应用。若坚持原完整门必须重测C，则现10788已全部分给L196+正式9408+test1184，没有额外196，继续NOT_READY，不挪评估。
- **完整计费待闭合**：outer自发布/退出尾、预约前流程及旧UNKNOWN尚无完整外层包围证据，不填0；要求保持原验收则继续停。任何“用预留替实测”的会计政策须有独立上界和明确批准，当前没有。
- **续接准入待派发**：仅在前两项有合法处置、实时剩余资源可行后，另行授权执行adapter/prepare真实生命周期与阶段签字；原T0/deadline/预算原封继承。不能借候选自动解除STOP、签训练令或升级task10。

这些差异已经写入候选`pending_user_decisions`，均`applied:false`，不是本轮已授权放宽。当前不能放行，也不启动部分正式实验。

## R1–R5集中集成修复（2026-11-03T22:19:23.656939+08:00）

本轮active，只修入口/监督/计费/续接身份/审计，冻结合同见[日志](../../../agent_logs/task9/task9.11/20261103-codex-integration-repair.md)。新增.9集成，子.9.1生命周期/.9.2续接并行，之后.10独立审核；递归保持各层三文档，父核子结果后验收。推荐GPT6.1sol/high、Sonnet5.5/high，因跨模块生命周期/预算合同审查；实际未知。旧C门、历史UNKNOWN和真实执行许可本轮不决定。

- [task9.11.9 TASK](task9.11.9/TASK.md)
- [task9.11.9 PROCEDURE](task9.11.9/PROCEDURE.md)
- [task9.11.9 RESULTS](task9.11.9/RESULTS.md)
- [task9.11.10 TASK](task9.11.10/TASK.md)
- [task9.11.10 PROCEDURE](task9.11.10/PROCEDURE.md)
- [task9.11.10 RESULTS](task9.11.10/RESULTS.md)

## 最新准确入口与剩余合同

本层递归保持三文档，.9（含.9.1生命周期/.9.2续接）整体集成后由.10独立审核，父已核原件；两分支写范围/负责人/依赖与三文档链接见.9 PROCEDURE。准确纯准备CLI、实际生产替身命令、状态/写者/读者和完整R矩阵见[.9 RESULTS](task9.11.9/RESULTS.md)。候选CLI不能真实执行；旧C门承接、有限会计边界、历史UNKNOWN处置和获批execution协议/release仍待决定，不把不可执行候选改true。每run250k成熟profile/G1/真实Docker尾和全方案预算可行性留后续获派；不重置T0/截止，不重跑smoke/多C ON。模型推荐GPT6.1sol/high、Sonnet5.5/high，实际UNKNOWN。[SRC-1409](../../../SOURCES.md#src-1409)。

## F1/F2跨阶段集中修复（2026-11-03T23:11:10.673033+08:00）

本轮active，新增.11单一联合实施→稳定源码→.12独立审查→父核原件；递归每层恰三文档。授权与冻结矩阵见[父日志](../../../agent_logs/task9/task9.11/20261103-codex-cross-stage-repair.md)/[SRC-1412](../../../SOURCES.md#src-1412)。推荐GPT6.1sol/high、Sonnet5.5/high，实际UNKNOWN，因跨时间/新成本前序合同审查；不重做R1/R3/R5、不签真实执行。

[task9.11.11 TASK](task9.11.11/TASK.md) · [task9.11.11 PROCEDURE](task9.11.11/PROCEDURE.md) · [task9.11.11 RESULTS](task9.11.11/RESULTS.md)

[task9.11.12 TASK](task9.11.12/TASK.md) · [task9.11.12 PROCEDURE](task9.11.12/PROCEDURE.md) · [task9.11.12 RESULTS](task9.11.12/RESULTS.md)


## N. F1/F2最终生产调用与续行边界

递归沿本层三文档：.11联合实施→冻结168文件→.12独立验收→父直接核原件，均done。Codex推荐GPT6.1sol/high、Claude Sonnet5.5/high，因可信时间/账本/竞争因果核验；请求sol/high、实际后端/强度UNKNOWN。新结果见[.11](task9.11.11/RESULTS.md)、[.12](task9.11.12/RESULTS.md)和父RESULTS §15，不拼旧版本PASS。

新候选须在首次prepare之前冻结dynamic_cost_policy与fixture clock anchor。旧legacy静态库存仍严格集合校验，不将旧真实protocol迁移成dynamic。prepare冻结科学/代码/namespace/路径/旧账引用→预算独立人核完整费用并发布不可变snapshot→release绑定最新snapshot与静态协议→dispatch锁内校验当前时间/余额与reservation→guard最后真实Popen前再锁内核费→worker.main二次真实准入→actualwait→CLOSED。历史读取核原reservation启动捕获、actualwait完成捕获及原令SHA/cap/deadline；自然到期保资格，显式撤销否决资格但保费用。新费/source/event/control journal与独审新snapshot追加，不改旧件；current新启动必须最新且未过期、无缺费/未审费/UNKNOWN。[SRC-1413](../../../SOURCES.md#src-1413)。

本轮已执行精确命令（cwd `/home/ybc/projects/CL-FoReM-task9`；全为stdlib替身，原argv/输出/rc在.11/final-v2-*-command.json）：

```bash
python3 -B forem/src/task9_lr/tests/test_cross_stage_stdlib.py
python3 -B forem/src/task9_lr/tests/test_supervision_stdlib.py
python3 -B forem/src/task9_lr/tests/test_lifecycle_candidate_stdlib.py
python3 -B forem/src/task9_lr/tests/test_continuation_stdlib.py
python3 -B forem/src/task9_lr/tests/test_entrypoints_audit_stdlib.py
```

下一次可直接从[最终冻结源](../../../agent_logs/task9/task9.11/task9.11.11/source-freeze-v2.json)、[独审裁决](../../../agent_logs/task9/task9.11/task9.11.12/FINAL-INDEPENDENT-VERDICT.json)、[最新真实预算读取脚本](../../../agent_logs/task9/task9.11/task9.11.11/cross_stage_budget_audit.py)接手；读取命令为 `python3 -B /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/task9.11.11/cross_stage_budget_audit.py`，只读JSON/hash/stat，不加载模型或控制Docker。输出仍是已知下界/余额上界，不能作许可。

**没有当前可运行的真实续训命令。** 真实CLI/adapter/worker仍拒非执行候选；不得将execution_allowed改true绕过。须一次集中决定旧C组合验收、有限job/control会计及取值、历史UNKNOWN处置、真实execution协议/release；随后重核不可重置的当前窗口与全方案成熟成本。不能承诺只派执行即可：若这些决定改变schema/边界，仍需定点接口及独审；原R1/R3/R5设计与本轮同源证据无需无因重做，新的真实G1/四run成熟profile/实际Docker尾是后续获批阶段必要门，替身不能代替。[SRC-1415](../../../SOURCES.md#src-1415)。

## O. SRC-1417 P1 GPU两账修复

依赖顺序：父复算旧原件→[.13 TASK](task9.11.13/TASK.md) / [PROCEDURE](task9.11.13/PROCEDURE.md) / [RESULTS](task9.11.13/RESULTS.md)实施→冻结→[.14 TASK](task9.11.14/TASK.md) / [PROCEDURE](task9.11.14/PROCEDURE.md) / [RESULTS](task9.11.14/RESULTS.md)独审→父核验。模型推荐GPT6.1sol/high、Sonnet5.5/high（设备区间及两账准入核查），本轮模型限制沿SRC-1419；实际配置另记。恰三文档递归约定不变，无真实许可。

### O.1 最终生产路径与复验入口

父复算旧101归档→.13实施/冻结v3→父132相关标准库检查与.14独立原事件审核→父逐SHA/原输出接收已完成。节点仍各恰三份主要文档，未再拆子任务；.13负责人Codex实施、.14负责人Codex独审，父负责共享文档及接收。推荐GPT6.1sol/high、Sonnet5.5/high用于两账/区间/身份因果审查，实际模型/强度未知。

GPU来源为static/dynamic命令及继承账的明确synthetic设备区间、容器完整持卡窗口；同UUID并集只计一次。metadata控制和真实CPU payload保原worker规则。`check_resources(new_worker_seconds=cap+control,new_gpu_seconds=cap)`分别预留；worker内二次准入不重复计自身cap。快照保存`cumulative`、`reserved_resource_budget`、`remaining_resource_budget`、`remaining_after_reservations`、精确resource观察时点及容器basis；运行中容器review显传已有inspect数据输入，缺当前证据仍UNKNOWN。

`measured_command(...,gpu_devices=[])`仅是显式false-execution fixture输入，不提供真实CPU核销；真实external归属API不足、static旧容器没有immutable时间basis均UNKNOWN。新snapshot继承已审record/sealed分配，三方Id一致，窗口不可缩短/移写/重启；原release/closure不重签，Running→Stopped保已审区间合法。旧F1/F2/R1/R3/R5设计保持；首basis身份及历史窗口反例原FAIL保留。

精确命令以[.13 parent-final-v3-*-command.json](../../../agent_logs/task9/task9.11/task9.11.13)与[.14正式裁决](../../../agent_logs/task9/task9.11/task9.11.14/FINAL-INDEPENDENT-VERDICT.json)为准；统一SHA变化须重新冻结/复验，旧通过不移作新验收。所有命令只跑stdlib替身，禁止真实Docker/GPU/科学实验。实际预算继续累加，交接余额与缺口见RESULTS §17。[SRC-1420](../../../SOURCES.md#src-1420) · [SRC-1421](../../../SOURCES.md#src-1421) · [SRC-1422](../../../SOURCES.md#src-1422)。

## P. SRC-1423首次设备归属修复

递归沿三文档：.15实施→冻结→.16独立审核→父核原件。Codex GPT6.1sol/high、Claude Sonnet5.5/high，因三方设备证据/预算核验；实际未知。

- [. 15 TASK](task9.11.15/TASK.md)
- [. 15 PROCEDURE](task9.11.15/PROCEDURE.md)
- [. 15 RESULTS](task9.11.15/RESULTS.md)
- [. 16 TASK](task9.11.16/TASK.md)
- [. 16 PROCEDURE](task9.11.16/PROCEDURE.md)
- [. 16 RESULTS](task9.11.16/RESULTS.md)
仅授权标准库替身，无真实执行许可。[SRC-1423](../../../SOURCES.md#src-1423)。

### P.1 最终接收

.15实施/143项→同171源3ae8183a…97d3ad2→.16独立32项→父658矩阵原件/2313新引用/5689旧引用/8实际独审命令核验done。各节点恰三文档，独审不改生产；准确argv/rc认.15/.16根command JSON。见[父§19](RESULTS.md#19-src-1423首次gpu设备归属最小修复2026-11-04)/[SRC-1426](../../../SOURCES.md#src-1426)。真实仍NOT_READY。

## 2026-11-04 用户采纳放行评审推荐：task9.11.17真实准备

用户已采纳SRC-1428具体推荐，授权[SRC-1429](../../../SOURCES.md#src-1429)。旧C科学原件＋新版本完整性门限定承接、旧FAIL保留；旧C host以1800s作政策核销（非实测）替换618.796192884s下界，prelaunch与其它UNKNOWN保留。会计原则分job actual wait/CPU control/GPU allocation union/预留；真实控制数额未冻结，不沿用fixture30s。原T0/截止/58h/2TiB/8GiB、科学四run和全部消费不变，无真实G1/模型/环境/正式训练/最终test/签令授权，原窗不自动延长。

本层递归每节点恰三文档；顺序：父[task9.11.17 TASK](task9.11.17/TASK.md) / [PROCEDURE](task9.11.17/PROCEDURE.md) / [RESULTS](task9.11.17/RESULTS.md)实施真实收据/生产只读入口与协议草案→冻结→另派独审[task9.11.17.1 TASK](task9.11.17/task9.11.17.1/TASK.md) / [PROCEDURE](task9.11.17/task9.11.17.1/PROCEDURE.md) / [RESULTS](task9.11.17/task9.11.17.1/RESULTS.md)→父直接核原件与实时可行性。父负责共享文档，子只改独审文档/日志，不并发覆盖实现。

推荐GPT6.1sol/high、Sonnet5.5/high，因跨进程实际wait、设备归属与旧账准入因果；实际型号/强度未知。新草案可由生产protocol_read校验但所有真实执行/资源准入/阶段令入口继续拒绝；完整真实cost/inherited/event/control/Docker链仍受历史UNKNOWN与设备/控制/工期门阻断，不以新原语通过声称已真实READY。源码/必要测试与缺口以.17结果为准，不重复SRC-1423已过矩阵。

task9.11.18：[TASK](task9.11.18/TASK.md) / [PROCEDURE](task9.11.18/PROCEDURE.md) / [RESULTS](task9.11.18/RESULTS.md)。依赖及负责人见该节点。


新直接派发SRC-1435由[task9.11.18 TASK](task9.11.18/TASK.md) / [PROCEDURE](task9.11.18/PROCEDURE.md) / [RESULTS](task9.11.18/RESULTS.md)递归承载；父核子原件，依赖与逐门自动续行/停止条件见父RESULTS §22。负责人父Codex；子.18.1实施、.18.2独审/阶段令、.18.3历史工具/异步证据，仅各自边界写入。先前已过门不重复验证。推荐GPT6.1sol/high、Sonnet5.5/high（真实生命周期和会计），实际后端/强度未知。
