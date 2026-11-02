# task9.5 RESULTS — 下层SAC参数台账、论文呈现与优化执行

状态：**done：全部六run正常完成3M，最终独立执行/协议验收PASS；本轮未找到满足改善标准的新配置。** 最新2026-11-02 00:28核查，三新方向均未达到预注册“观察改善”标准；六run均未退化。下方10-31执行中记录为历史，最新见第11节。[SRC-1351](../../../SOURCES.md#src-1351)。用户明确要求先设计流程再派子Agent执行，[SRC-1336](../../../SOURCES.md#src-1336)。事实与工程建议分开，实际训练仍以各run原件为准。

## 1. 快照与版本

[参数事实SRC-1337](../../../SOURCES.md#src-1337)；[完整机器快照](../../../../logs/task9/t9-opt-design-20261031/parameter-inventory.json)、[只读收集脚本](../../../../logs/task9/t9-opt-design-20261031/collect_parameters.py)。快照2026-10-31 21:33+08：**19配置JSON（含2smoke模板）、17正式run（旧4＋本批13）、69源码/配置hash**，原69冻结文件无漂移；包含实际config/runtime/summary和完整评估逐回合重算。pool/semantic/evaluation-seeds均记录hash。没有加载大检查点，不将盘点当全部历史实验重新验收。

HEAD121cb36，现分支codex/task9-sac-opt-20261031，保留全部dirty改动，无commit/push。不是按HEAD重新构造参数；硬编码值以快照中的实际文件hash/符号为依据。新代码只能在独立task9_opt命名空间，不改旧运行源码。

## 2. 优化器与更新参数（当前实际）

本节全部值对应[SRC-1337](../../../SOURCES.md#src-1337)与机器constants.sac/replay/evaluation及各raw config，来自源码审阅，不是假装实时检查每个活动tensor。

|项目|实际值/行为|位置/口径|
|---|---|---|
|算法基础|CBL自写SAC数学移植，双Q/高斯tanh策略|task7_lower/sac.py，task8_lower/sac.py|
|γ|0.99|构造硬编码，原JSON无gamma可调字段|
|τ|0.001|构造硬编码，目标Q软更新|
|target更新间隔|每1次梯度update|按梯度更新钟，不是每环境动作|
|batch|256|每次从旧回放采样|
|默认回放容量|100000全局转移|current/next128²×3 uint8在GPU|
|采样|均匀无放回random.sample|GPU回放，CPU生成采样索引；不是PER|
|插入/更新顺序|先按旧回放update，再插入当前转移|consume_transition|
|学习起点|旧回放len>256且转移数整除间隔|k1首258；k10/k20首260|
|随机动作起步|前1000全局转移|不禁止梯度update，不是每env1000|
|B0更新比|1update/1transfer|近似UTD1；不把256样本抽样数混作UTD|
|B3更新比|1update/10transfer|近似UTD0.1|
|优化器|actor Adam；两critic联合一个Adam；α单独Adam|不是每Q独立optimizer|
|Adam默认|betas(0.9,0.999)、eps1e-8、weight_decay0、amsgradFalse|容器torch签名只读核查，未新建optimizer|
|梯度裁剪|norm10|actor/联合critic/α各自param组，非所有模型一个总norm|
|critic损失|B0/B1/B2/B3/T均MSE；H为Huberδ1|两个Q损失相加；Huber小误差0.5x²|
|actor目标|mean(α·logπ−min(Q1,Q2))|继承CBL表达，未额外拆critic或改detach规则|
|初始α/logα|1.0/0.0|原capped首次自动更新后才使用乘数0.35|
|原温度|0.35·exp(logα)，降至0.05后固定|0.35不是上限；α LR固定1e-6|
|B3温度|exp(logα)，不做0.05冻结|α LR按转移线性1e-4→1e-6|
|目标熵|−3|三维归一化动作；构造硬编码|
|B0 actor/critic LR|1e-4按update指数向1e-6衰减|分母4,999,743updates；3M末未必到1e-6|
|B3 actor/critic LR|1e-4→1e-6，按当前总转移预算线性|3M或5M日程分别归一化|
|total_updates字段|4,999,743|保留日程字段，不是各run真实update数|
|3M真实update|k1=2,999,743；k10=299,975；k20=149,988|floor(N/k)−floor(257/k)|
|5M真实update|k10=499,975|同上|
|target初始化|复制在线critic参数|无actor target网络|

## 3. 网络与输入（实际，不随组改变）

来源同[SRC-1337](../../../SOURCES.md#src-1337)，对应task7_lower/networks.py、observation.py与Core.observe。

|项目|实际值|
|---|---|
|输入栅格|128×128×3：observed、height、future_route_xy|
|栅格分辨率/范围|0.05m/格，局部6.4m×6.4m|
|回放高度编码|0.01m量化，uint8上限2.55m；不是二值高度|
|同步向量|74维：q、tcp、next_tcp、route_points、subgoal、synchronous、previous_action|
|q归一化|除以[2π,2π,π,2π,2π,2π]|
|时间/失败输入|scan_timestamp不进入FIELDS；无失败计数/拒绝标志，无RNN隐藏状态|
|CNN|3层，通道16/32/32，kernel3/stride2/pad1，ReLU，flatten8192|
|MLP|512/512/256，ReLU|
|编码器共享|actor/Q1/Q2各自独立；target Q复制相应结构|
|策略分布|对角Normal重参数化后tanh；训练随机，评估tanh(mean)|
|log_std|裁剪[−20,2]；不是RLlib的[−5,2]|
|log_prob校正|epsilon1e-6|
|初始化|Linear Xavier uniform/zero bias；Conv Kaiming normal/ReLU|

## 4. 环境、数据与评估合同（固定）

来源[SRC-1337](../../../SOURCES.md#src-1337)，配置原值全部可在机器快照读取；完整奖励式/IK/碰撞语义以原Core源码和原任务协议为准，不另维护第二套公式。

|项目|实际值/定义|
|---|---|
|几何/传感器/profile|primitive-obb-v1 / ghost-v1 / sync_v5|
|环境数/精度|256并行，float32|
|扫描|360×90、水平360°/垂直90°、最大6m；base_footprint上0.5m|
|本体遮挡|ghost忽略本体遮挡，场景遮挡/非传感器碰撞保留|
|raw动作|3维[u,ω,v]，每维[−1,1]|
|同步物理映射|u=0.01+0.145(a0+1)∈[0.01,0.3]m/s；ω=a1 rad/s；v=0.3a2 m/s|
|执行周期|每action最多2×0.05s子步；失败子步不commit，实际dt可少于0.1s|
|上一动作|仅has_commit时更新queue；不把指令回填实际q/base|
|子目标|候选生成mask内均匀随机，不是已训上层|
|失败/停滞|累计20失败终止；连续5段无足够进展亦终止|
|回合上限|150决策或200s尝试时间，按原逻辑截断|
|严格成功|终点位置≤0.025m、cbl≤0.05且failures==0|
|bootstrap|reason0/1 mask0，其他mask1，保留原episode_end_bootstrap|
|地图池|10000train、100validation、200test；sparse/standard各半|
|语义迁移|24地图（8类各3）×4个固定episode，共96|
|训练种子|4718/4719，既有B0/B3/5M另有4720|
|验证随机种子表|evaluation-seeds.json固定；validation_seed14718为env构造字段，逐case种子见表|
|评估|每250k完整100验证＋96迁移，batch16，确定性动作|
|诊断/保存|每1000诊断、每250k full checkpoint；actor单独保存|
|选择限制|迁移不选模，200test本轮未调用，验证池用于调参不能称最终独立测试|
|停止|非有限立即保存停；500k后Qmax>10×自身500k参考保存停|
|退化定义|3M末三均值≤该run峰值−0.15；发散停止计退化且P字面不可判|
|默认单run wall上限|旧协议172800s；新任务还受绝对周一截止约束|

## 5. 当前各组配置与结果索引

来源[参数SRC-1337](../../../SOURCES.md#src-1337)、[结果SRC-1332/1333](../../../SOURCES.md#src-1332)；H用户提前停止单独登记，不把它改写为watchdog发散。下表是21:33参数盘点及其后事件摘要，最新运行结果见9.4 RESULTS/原件。

|组|相对B0改变|种子与预算|已见结果|
|---|---|---|---|
|B0|原配方|3种子×3M|三种子均保护停止|
|B1|update间隔1→10|2×3M|62%/72%，均正常完成且不退化|
|B2|温度＋actor/critic线性LR|2×3M|均保护停止|
|B3|B2＋update间隔10|3×3M|63%/64%/64%，均正常完成且不退化|
|T|仅温度包＋独立α线性LR|2×3M|均保护停止|
|H|仅MSE→Huberδ1|2×3M|后段下降，用户已批准保存提前停止；不是原Q阈值触发|
|B3-5M|B3按5M日程从头|3×5M|4718已完成67%；另两路继续、不得停止|

B3不是完整RLlib；target时钟、optimizer/clip、回放采样、log_std、mask等差异见task9.3勘误。旧环境task5.5成功率不与当前地图/评估直接混合。

## 6. 论文呈现建议

[建议SRC-1341](../../../SOURCES.md#src-1341)；算法原文[SRC-1338](../../../SOURCES.md#src-1338)、评估依据[SRC-1340](../../../SOURCES.md#src-1340)。**有必要交代，但定位为下层基线的实现与配置选择证据。**

- 方法章节：SAC算法来源与实际实现、最终冻结参数、与CBL/RLlib关系；不要把B3写成RLlib原版或提出新SAC理论。
- 实验章节：简洁呈现更新比×温度/LR包2×2对照，解释为何选稳定强基线；若后续论文主贡献不是SAC机制，正文不需要铺开所有调参历史。
- 附录/补充：B0/B1/B2/B3/T/H及新方向的全种子曲线、负结果、硬编码参数、预算、停止规则、失败恢复局限。
- 最终比较：下层一旦冻结，后续世界模型/上层组统一使用同一基线，不能人为弱化对照。重复使用100验证调参的局限公开，最终独立测试留给冻结后正式实验。两种子探索不作显著性/普适提升断言。

实验主线见[experiment0](../../../experiments/experiment0/TASK.md)，论文主线见[paper2](../../../paper/paper2/TASK.md)，只引用本任务协议/结果，不重复维护参数。

## 7. 新三方向、门与状态

具体矩阵/假设/验收以[TASK](TASK.md)、[实施流程](PROCEDURE.md)为唯一协议，[SRC-1342](../../../SOURCES.md#src-1342)。以历史B3-3M同种子4718/4719作参考，组均最终63.5%、末三均值57.333%；额外4720不混入两配对种子均值。

|方向|唯一轴|实际执行状态|
|---|---|---|
|U20|间隔10→20|两seed正式3M完成，最终63/59%；第11节|
|E15|目标熵−3→−1.5|两seed正式3M完成，最终52/62%；第11节|
|R200|回放100k→200k|满200k/正式3M均完成，最终57/54%；第11节|

每组2种子×3M，共6新run目标、18M预算；12h/run只是基于旧完整9.49–9.55h的条件代理。首250k作为计入3M的有界profile，科学limit保持3M、pending批保留，不能用旧--transfers250000改变最后向量动作批。所有smoke/等价/恢复/全周期性能门未过前不放行新增长训。

预审9.5.1发现F1 profile边界、F2离散截止排程、F3分阶段release、F4冻结root/import合同，已纳入PROCEDURE与实施brief。子Agent9.5.2隔离实现/CPU候选和F1–F3修复已交付，9.5.4只读审计已核验；静态与实际G1分别独立PASS，22:42自主队列启动（[SRC-1348](../../../SOURCES.md#src-1348)、[SRC-1349](../../../SOURCES.md#src-1349)、[SRC-1350](../../../SOURCES.md#src-1350)）。CPU/static审查→G1专用令牌→G1实际证据审查→smoke/profile/逐run剩余预算策略令牌，不能用一个笼统令牌直接放行全部。

## 模型、风险与交接

父实际模型/强度未知；子Agent按显式派发gpt-6.1-sol/high（预审/实施/独立验收）、medium（性能）。Claude推荐Sonnet5.5相同档位；理由是恢复/科学合同需high，常规统计medium。没有自动改更大型号或提交推送。

当前本轮已完成全部smoke/profile/逐卡准入/3M及最终独立验收；下方执行中的交接文字为10-31历史，未重新加载最终大pt、真实截止保存未触发等限制见第12节。新任务07:00训练结束、08:00汇总为父保守解释，旧5M保留。H已保存退出并经核验，可在每次确认空闲后复用0/1；保存中的进程不强杀。

## 8. 用户停止H与性能审计更新

[SRC-1344](../../../SOURCES.md#src-1344)：H两路已保存并退出，0/1已空闲；两个5M不改、不停止。H为用户提前停止，不替换原发散规则结论；新矩阵仍仅改SAC参数。

[SRC-1343](../../../SOURCES.md#src-1343)：预审F1–F4已纳入合同；[原件](../../../../logs/task9/t9-opt-design-20261031/preflight-review.md)。[SRC-1345](../../../SOURCES.md#src-1345)：性能审计[报告](../../../../logs/task9/t9-opt-design-20261031/performance-review.md)与[JSON](../../../../logs/task9/t9-opt-design-20261031/performance-review.json)显示完整wall约40%评估、8%保存，GPU未满但不能仅从util推加速比；CUDA每转移计时同步收益尚未A/B，当前隔离实现优先保持字节一致以建立可靠基线。新profile将保留原完整周期成本，不删评估或关闭有限检查。

历史v1 CPU候选24passed仍被独立审查要求修复保存预留/退出分类/G1绝对截止；后续fix1和G1已分别独立验收并启动队列，见第9–10节。若后续评估纯计时优化，须同输入/RNG/更新/ledger等价，且在既有有界预算内实测；未验证不启用、不称已提速。

## 9. 静态审查修复与放行边界

[CPU候选SRC-1346](../../../SOURCES.md#src-1346)、[独立审查SRC-1347](../../../SOURCES.md#src-1347)：24passed的v1仍有三项调度问题，specFAIL/qualityCHANGES_REQUIRED；已交原实施者fix1/5：实测保存与取消/排空预留门、interrupted/diverged分别记录、G1绝对截止。新digest必须有针对性CPU证据并独立复审，未发任何GPUtoken。工程policy草案见[SRC-1342](../../../SOURCES.md#src-1342)及同目录JSON，草案不是放行，保存余量不作为硬上界证明；07:00未退出必须如实报unresolved。

22:29更新：[fix1 CPU证据SRC-1348](../../../SOURCES.md#src-1348)已核，16passed/rc0，新digest07e2b541a3230a4134ad527bf3423ad1073ac871e846c4d8c45f827f07bd033d，原69无漂移；同独立reviewer限定复审，GPU仍HOLD。

22:37更新：[实际G1与目录权限SRC-1349](../../../SOURCES.md#src-1349)已核原件：36passed/rc0、GPU0、policy/replay/optimizer CUDA，worker20.211s；独立实证验收前不发training-policy。原始host目录权限启动失败0GPU秒保留，原有5M不动。新增实际run目录继承ACL后仍要核宿主可写STOP。

## 10. 自主队列运行交接

[SRC-1350](../../../SOURCES.md#src-1350)：22:42实际队列启动，host1900665、独立截止monitor1900735；日志/账本`forem/logs/task9/t9-opt-20261031/{queue-state.json,deadline-monitor.json,training-queue.txt}`。首U20-4718 smoke512 GPU0，host1900841/container2677105，39imports隔离、正式配置预算3M/间隔20不变；真实smoke目录hostACL已核可写。当前只有smoke已开，不把它当正式3M进度；首250k/剩余2.75M自动准入仍须实际过门。

截止monitor06:30只对新增formal/smoke目录写STOP，07:00报告未退出者，旧5M全部保留。所有full196/成熟显存/保存恢复/最终3M结果及逐种子成功率仍待实测和最终独立验收；后台运行不依赖当前聊天持续打开。科学失败不自动重试，先前G1基础设施mkdir失败的0GPU记录保留。被release绑定的review/code/config不再改，后续结果另文件追加。

22:45父复核：`root-first-smoke-check.json`确认首U20-4718已保存512证据、恢复消费1000/38updates，科学limit仍3M，实际full196未complete；队列/截止monitor和两个旧5M PID全部存在，host写权限与STOP不存在均核。正式sixrun尚未启动，不能用smoke结果宣称成功率提升。[SRC-1350](../../../SOURCES.md#src-1350)。

## 11. 2026-11-02全量终态与训练效果

[原始核验SRC-1351](../../../SOURCES.md#src-1351)；[机器快照](../../../../logs/task9/t9-opt-20261031/status-20261102/results-snapshot.json)、[标准库重算脚本](../../../../logs/task9/t9-opt-20261031/status-20261102/collect_results.py)。234份JSON/192×196评估共37632回合重算错误0；全部新run完成3M且两阶段rc0，final/full/actor/meta存在，未加载最终大pt重演。新队列11-01 21:16:31+08结束，正式累计56.6976worker h，全局22.5693h；原三5M也都完成，现场无训练、四卡空闲，仅截止monitor等待既定时刻。

|组|4718最终/100|4719最终/100|最终组均|末三组均|相对B3最终/末三pp|退化/观察改善|
|---|---:|---:|---:|---:|---:|---|
|B3参考3M|63|64|63.5%|57.333%|0/0|均不退化，参考|
|U20|63|59|61%|54%|−2.5/−3.333|均不退化，未改善|
|E15|52|62|57%|55.833%|−6.5/−1.5|均不退化，未改善|
|R200|57|54|55.5%|57.833%|−8/+0.5|均不退化，未改善|

固定判定要求最终和末三组均均超过同两seed B3，故R200不能只拿末三+0.5pp称提升。所有组仅2训练种子，100评估回合不等于100训练种子，不作显著性断言。最终均值是描述性比较，不因此判定SAC其他优化方向无效或确认唯一失败原因。B1旧同两seed最终62/72%、均67%保留，不把B3称已证明最强基线。

|新run|2.5/2.75/3M成功数（/100）|末三均值|最终sparse/50、standard/50|最终transfer/96|完整两阶段worker h|
|---|---|---:|---|---:|---:|
|U20-4718|48/54/63|55%|37、26|41|8.814|
|U20-4719|44/56/59|53%|35、24|38|8.893|
|E15-4718|48/55/52|51.667%|31、21|40|10.038|
|E15-4719|54/64/62|60%|35、27|43|9.357|
|R200-4718|63/57/57|59%|35、22|38|9.741|
|R200-4719|59/57/54|56.667%|36、18|42|9.854|

三组smoke均在4300worker s/group内通过；所有profile科学limit3M、消费250k与额外pending动作收费一致并满容量回放，源码artifact07e2…033d及旧69hash无漂移。U20总149988updates，其余299975。R200实际满200k而非仅分配测试，最终CUDA分配峰43.67/43.80GiB、final.pt约41.65/41.66GiB；profile保存max207.83/198.81s，保存/取消余量门均ready。最终checkpoint metadata resume_safe为记录事实，未冒充已重新加载重放。

原B3-5M按4718/4719/4720：最终67/63/64%，平均64.667%；4.5/4.75/5M末三分别57/62/67、62/68/63、57/68/64%，各均62/64.333/63%，总均63.111%。迁移49/39/44（/96）。同三seed B3-3M最终63/64/64%、均63.667%，5M最终均值仅+1pp；预算与LR日程不同，5M末三是描述性补充，不能作原3M退化判据/统计显著结论。

目前结论：本轮三参数方向稳定完成但没有找到更高成功率的配置；不自动替换基线、不另开新实验。最终独立结果验收现已PASS，原件与适用限制见下节。父实际模型/强度未知；推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium整理，独立科学协议验收high。

## 12. 最终独立验收与交付

[独立验收SRC-1352](../../../SOURCES.md#src-1352)、[报告](../../../../logs/task9/t9-opt-20261031/review/final-results-review-20261102.md)、[JSON](../../../../logs/task9/t9-opt-20261031/review/final-results-review-20261102.json)。不同于实施者的reviewer从原始评估与18M动作/消费账本重算，执行/协议/记录PASS；科学结论为三组均未达到约定“观察改善”，不是优化成功。父重合指标交叉核对一致后接受。task9.5 done表示本轮设计/参数归档/三方向探索/记录及验收交付完成，不表示下层已冻结或问题根因解决。

所有训练已于截止前结束，四卡空闲；仅截止monitor仍待原时刻，无新任务。未停止它或新开实验。实际截止保存未被触发，最终大pt未重新加载，保留独立报告相应限制。task9.4全13run最终独立验收另待，不能由此扩大关闭。后续论文可引用本轮全部负结果与真实条件，不只挑R200末三/某seed或峰值。
