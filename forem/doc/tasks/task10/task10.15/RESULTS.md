# task10.15 原地偏好与学习信号诊断结果

2026-11-03 · **review，诊断交付完成，交当前决策者审核**。本轮证据支持**初始化已存在的候选内容偏好、每决策熵带来的零耗时软价值、负终局学习不足三者并存**；未发现已核查路径偏离现行实现合同。不能裁定唯一原因，也不能把现象简单归结为“只需多训”。原始收益仍为task10.14的0/12、0/12、10/12；本轮没有新增收益评估。依据：[输入/授权](../../../SOURCES.md#src-t10-031)、[排序/覆盖](../../../SOURCES.md#src-t10-032)、[目标/梯度](../../../SOURCES.md#src-t10-033)、[裁定/条件预算](../../../SOURCES.md#src-t10-034)。

## 1. 负责人、范围与冻结

父执行负责人Codex；task10.15.1子Agent独立核查首更及停滞链，父已读取源码、原件、10项冻结哈希，重新核对49条首更原始身份及Bellman/actor/critic算式后接受其工程交付。子结果见[RESULTS](task10.15.1/RESULTS.md)。父/子实际平台标识GPT-6，具体变体与推理档位无法核实，记未知；推荐GPT6.1sol/high、Sonnet5.5/high，涉及真实回放、变时长Bellman与梯度因果。用户允许自主选模与先建三文档后委派；本轮子不使用GPU或执行更新，共享父预算，无后续委派。

工作树`/home/ybc/projects/CL-FoReM-task10`，分支`codex/task10-upper-wm`，HEAD `91f538cf2ee10bebffd6b643d5c908fa0d419ced`，既有dirty修改保留。训练合同记录原执行commit `b5b60ee581767e36c0b17efe596fc7bad612218b`；当前所有训练code_sha256项一致，评估frozen-code相应文件也全部一致。HEAD不是唯一版本依据。[SRC-T10-031](../../../SOURCES.md#src-t10-031)

新独立run `forem/results/task10/t10-diag-20261103-s101/`；只读源`t10-online-20261102-s101`与`t10-eval-20261103-s101`。`input-freeze.json`逐项列475文件SHA256；分析后`input-integrity-after.json`、最终`parent-verification.json`均核475项未变。源模型文件SHA256：

|输入|SHA256|
|---|---|
|initial-learner.pt（完整learner.model）|`9bf4083734120165a7f7d535e0b97db43479974ff4062332b3119b793cf0d9cb`|
|final.actor.pt（完整上层200更新）|`0fcd4e68c3aaeb85247380ab9e1e7b5a15f605c89880dab42016874d56c84a71`|
|first-update-before.pt|`458212d54ac47ae6282cb1e7f8e9b2df32e16452a73a9ead63e565f2c1d8bf1d`|
|first-update-after.pt|`61c8010be812f829e7d20ce26a0c9eedc3711726c781a18b71c2bfb6fc03bcfe`|
|冻结B3-5M seed4718|`3db11d9f00317849e35a523d66d0935ebc2e3567d82c519ccc42f3d8de42f7ae`|

本run `online-audit.json`为verified：1200 journal/replay唯一身份一致、200更新连续、首更真实样本与GPU证据通过；`eval-audit.json`为verified_complete/issues=[]，重新核B3/模型/地图与既有执行文件，并复现36完整回合0/0/10成功。原件两模型各52次原地、35零尝试、全部有有效移动候选均复现。[SRC-T10-031](../../../SOURCES.md#src-t10-031)

## 2. 怎么选：概率、Q与槽位

按每回合decision0起逐个真实观测恢复VCM；只比较两模型共有的52状态，观测与所有模型候选字段逐Tensor相同。没有用重置记忆的单帧代替真实历史。逐有效/无效槽的logit、概率、Q1/Q2/minQ、mask、6维几何、19维推演特征和归一化值均在[原始表格目录](../../../../results/task10/t10-diag-20261103-s101/)。[SRC-T10-032](../../../SOURCES.md#src-t10-032)

|52共享状态|initial|trained|
|---|---:|---:|
|原地argmax|52/52|52/52|
|原地概率范围（原GPU logits直接softmax）|20.8715–61.4978%|15.0060–31.5233%|
|原地概率均值|26.1330%|19.3781%|
|原地减最佳移动logit差，均值|0.463066|0.240309|
|上述差范围|0.265983–1.350909|0.027068–0.453505|
|minQ把原地排首|51/52|52/52|
|原地减最佳移动minQ差，均值|0.030783|0.084808|
|策略熵均值（CPU）|1.981310|2.058225|

**argmax全原地不等于采样近100%**。训练后分布更平坦、原地概率与logit领先缩小，但仍未跨过最大值排序；本轮没有运行采样评估，不能预测其成功率。initial唯一actor/critic不一致是sparse_validation_00007首状态：actor原地、critic槽7，原地Q差−0.002365。trained actor/critic全52状态均一致。

CPU相对原GPU有效logits最大差initial `9.61423e-5`、trained `1.58511e-4`，不宣称跨设备逐位一致；上表概率/logit差取原GPU记录另算，CPU恢复所得argmax全部一致。Q和熵取CPU前向，具体差值逐行保留。

52状态共437有效候选（52原地、385移动）。原地相对位姿为0、唯一inplace=true，移动slot0–11为单位米半径、每30度顺序；selected_prediction与选中槽f_k严格相同。start_base→world_pose手算最大float32差`2.38419e-7`。有效T_seg均正，按现行3.2m/T_seg缩放独立算归一化最大差0；无效padding被屏蔽，不能拿其T_seg=0判有效候选错误。原地段arrived均0.8654、delta_s均0.1005m；移动对应0.06234、1.2878m，说明“段到点”并非“任务完成”。完整字段分布见supplement-summary，差异本身不是实现bug或单因证明。

逆序同步重排全部候选几何、特征与mask，再恢复索引，logit最大差`7.153e-7`、Q最大差`2.385e-7`。候选网络没有slot位置编码，评分随内容重排；VCM的历史时间编码另属历史表示。**反证固定slot12接线/索引或槽位位置嵌入导致偏好（本次检查范围）**。初始模型在0更新时已全选原地，证明本种子偏好早于在线学习；不能据单初始化推出所有初始化都会如此。

## 3. 真实回放覆盖与回报

统计入口从offline-learner完整replay及按序真实batch journal读取，未把summary当逐条事实。[SRC-T10-032](../../../SOURCES.md#src-t10-032)

|覆盖|前1000预热|后200策略采样|合计|
|---|---:|---:|---:|
|真实决策|1000|200|1200|
|原地/移动|120/880|35/165|155/1045|
|零尝试|14|6|20|
|严格成功终局|441|88|529|
|所有终局|631|131|762|
|含失败尝试的决策|191|42|233|

763个episode含762完整和1个采集截止未完整，后者保留bootstrap，未伪造任务结束；完整最大长度8。终局主原因529严格成功、221失败上限、7停滞失败、5带失败到路线末端。失败尝试共4448；全13槽均有真实选择记录，逐槽数量在coverage-summary。1个严格成功回合同时触发stall，单列并发事件，不把它计作停滞失败。

**20个零耗时样本全部原地、非终局、g=1、bootstrap=1。训练完整回合最多出现2个零尝试，没有“反复原地直到停滞终局”的训练链。** 7个停滞失败终局全选移动槽1/2/3、dt=.05、r=−1、mask=0；而validation的7个停滞回合各连续5个零尝试原地。这是具体的覆盖差异，不是“没有失败样本”。没有持久化200次各自的抽样身份，不能声称7个终局都被学过或从未抽过。

按原episodes的route_length和真实attempted_substeps逐条复算r、Phi、g、bootstrap，reward/discount最大误差`2.97557e-8`；以同一折扣累乘，完整回合塑形和满足`ΣG_t(g_t Phi_next−Phi_t)=−Phi_initial`，最大误差`3.74857e-8`。失败回合最终基础回报0，塑形未凭中间进展留下任务收益。未完整回合另保留末Phi边界项。见replay-transitions.csv、episode-returns.csv。

## 4. 首更目标与梯度：有反向作用的两条熵链

[子原件与完整复算](task10.15.1/RESULTS.md)、[SRC-T10-033](../../../SOURCES.md#src-t10-033)。恢复原首更前完整learner/optimizer/scheduler/replay/RNG，32 anchors身份精确相同，得到49 loss rows、19个首决策、0padding。CPU critic `0.3479388952`、actor `−0.6639289856`；相对原GPU差`8.94e-8`/`5.96e-8`，joint norm差`4.88e-7`。父以原件tensor独立重算target最大差`5.96e-8`、逐49行原始身份核对通过。

|真实首更行；env/episode/decision|r；g；bootstrap|next E[minQ]|next αH|target|
|---|---|---:|---:|---:|
|33；2/41/1|0；1；1|−0.026708|0.780598|0.753890|
|39；3/4/2|0；1；1|−0.031517|0.700563|0.669046|
|46；1/24/4|0；1；1|−0.014818|0.455358|0.440539|

三行均零尝试原地。行33的Phi保持0.230257861、所选Q1/Q2仅0.123672/0.036014，但soft target0.753890，critic导数−0.012862/−0.014651，会抬高两Q。扣熵项的代数target均为负；此分解没有用于更新。**支持零物理耗时决策获得额外软价值，是否应赋予这类价值需决策者裁定。** 有限停滞终止避免无限bootstrap，仍不会取消此前的熵贡献。

另一条链是当前actor的熵项抑制概率集中：首更49/49行`dL_actor/dlogit12>0`，Q项拉高原地，但熵项更强、净方向降低原地。解析梯度与autograd最大差`6.403e-10`。所以不能说“熵梯度直接把actor推向原地”。

|同49个train状态，用保存权重前向|原地概率均值|argmax原地|
|---|---:|---:|
|before（0更新）|0.283805|49/49|
|真实首更after（1更新）|0.268547|49/49|
|final（200更新）|0.205615|49/49|

首更概率49/49下降，final相对before 48降1升；真实更新已响应，却未越过排序。没有额外执行一次step来复刻已保存的事实。

梯度边界符合合同：actor-only只更新actor头6张量，不向VCM、candidate_encoder或Q反传；critic向VCM/候选编码器/双Q反传，不到actor头。stage1候选detach是既有设计，不能擅自删除。optimizer包含全部85个可训练张量各一次，首更参数改变组与预期一致、冻结模块不变；对原保存梯度绝对值>1e-7的1,481,415个元素，Adam首步delta全部反向，未发现符号错误。lr按原200总更新从1e-4衰减至1e-6；alpha最终0.349984，仍近0.35。tau=.001的target传播很慢：仅在online一步跳变后保持常量的条件下，200步吸收18.135%；不是实测target距final比例。

## 5. 停滞如何传回Q和actor

8个stall trigger回合（7失败、1并发成功）完整真实历史，before/after-first/final各前向，共159行。7失败终局均mask=0、y=−1，next Q/熵贡献为0；**终局合同正确，不是忘关bootstrap**。[SRC-T10-033](../../../SOURCES.md#src-t10-033)

final所选移动Q1/Q2为−0.099331至0.192093，距−1仍残差0.900669–1.192093，负终局未充分拟合。同状态原地minQ 0.424661–0.489590，actor全7行仍原地，6行当前actor局部梯度继续增原地。例env1/ep49/decision5：真实selected3、target−1，Q1/Q2=−0.080646/−0.045288；原地minQ0.439342、最佳移动0.183937，原地概率0.334805，逐行actor原地导数−0.012845。

critic只对实际所选槽拟合负标签；前序通过next policy与target双Q的逐步bootstrap传播，actor再按当前minQ改变排序。现有数据没有原地停滞终局，不能把对移动槽的终局训练当作已经直接压低原地。第一保存样本也无stall终局，无法恢复200次全部历史抽样频次。以上支持“当前负终局拟合与传播不足”，不证明增加多少更新就会解决。

记录路径上的额外next熵贡献折扣和在7失败链为0.294902–1.966557；原始奖励折扣和约0（float32误差）。这是**条件于已记录off-policy动作链的算术拆项**，不是当前策略的期望回报，不证明另一行动一定更好或soft目标的全局最优策略必停滞。

## 6. 假设裁定与最小建议

|假设|裁定|具体证据/边界|
|---|---|---|
|固定slot12映射、mask或候选归一化错误|**反证（已核查范围）**|全部有移动候选，437有效槽映射/单位复算及逆序随内容重排通过；不等于全系统无bug。|
|原地概率接近100%，或模型没有改变|**反证**|原GPU logits softmax15–62%；首更/200更概率下降、argmax尚未改变。|
|奖励/势函数/终局bootstrap偏离合同|**反证（已核查范围）**|全回放回报与望远镜复算、7停滞失败mask0/y−1。|
|detach、optimizer漏参、梯度符号错误|**反证（首更及实际参数范围）**|首更loss/梯度/Adam方向/参数组符合合同。|
|零耗时原地存在额外熵软价值|**支持**|3个精确样本熵贡献0.455–0.781，已超过它们的Q项绝对值；不等于已证明其单因导致argmax。|
|200更新已充分学会负终局并压低原地|**反证**|终局残差0.90–1.19、训练无原地停滞终局、LR已到1e-6。|
|当前仅仅训练不够；直接10k即可修复|**证据不足**|学习不足与目标风险共存；原地偏好早于训练，未经目标选择或新有界对照不能保证。|
|更换候选生成器/热力网络即可解决|**证据不足**|本轮没有该反事实，uniform读数不能证明task12网络有效。|

本轮没有确认需修复的实现偏离，因此**没有修改生产实现**。最小待审协议建议是：由决策者先明确“相同物理时间内增加决策不应产生额外熵收益”是否为研究目标；若是，审议按真实尝试时长计熵、dt=0贡献为0的方向，并一致定义Bellman、actor与temperature。不能只在target删熵，不改变实际dt/discount、基础奖励、mask或终止来制造结果。具体尺度/公式、零时长与正时长及终局反例验收、配对方法待新协议批准；本轮未实施、未宣称改善。[SRC-T10-034](../../../SOURCES.md#src-t10-034)

若决策者保留原objective，单种子10k可以作为**训练充分性待审对照**，不是本轮结论。必须重新固定总LR更新数/冷启动或恢复合同、checkpoint、种子、截止与评估预算，不能直接接在200步衰减完的scheduler后。原wall16951.958s中200次update累计72.580s，非update14.06615s/决策、update0.362901s/次；按10000决策/1000预热/约9000更新线性算约39.98h训练，加同36回合配对约0.92h，共约40.90h。它假设策略/候选/场景/周期性开销分布不变，未作新性能核查、不是时限承诺或授权；不满足既定时限时应交瓶颈，不自动加预算或缩规模。

## 7. 命令、原件、成本与交接

所有命令在指定工作树执行，产物落独立run。以下各自已执行rc0；审计源文件只读。可复算命令：

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 -u /workspace/scripts/task10_preference_diagnostic.py'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 -u /workspace/scripts/task10_signal_diagnostic.py --source /workspace/results/task10/t10-online-20261102-s101 --output /workspace/results/task10/t10-diag-20261103-s101'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 -u /workspace/scripts/task10_diagnostic_supplement.py'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 -u /workspace/scripts/task10_diagnostic_verify.py'
```

注意：复算脚本会覆盖**本诊断run的派生表格**，不覆盖源run；复算前保存当前evidence-hashes，或使用副本目录和冻结脚本。signal脚本支持独立`--output`。冻结代码副本在本run/frozen-analysis-code及signal-code.py，哈希见evidence-hashes.json；不会重新运行环境或optimizer。

还执行两只读审计（均rc0）：`task10_online_audit.py --run /workspace/results/task10/t10-online-20261102-s101 --output /workspace/results/task10/t10-diag-20261103-s101/online-audit.json`；`task10_validation_audit_v2.py --run /workspace/results/task10/t10-eval-20261103-s101 --reference /reference/source --output /workspace/results/task10/t10-diag-20261103-s101/eval-audit.json`，同上述CPU docker前缀。

本轮CPU程序准备时有两次父脚本rc1：先误把候选timing诊断元数据当模型字段比较，后直接把无效padding的T_seg=0送normalize。已分别按模型字段、有效mask修正；不是源模型/执行异常，源原件未变。更早宿主Python不支持hashlib.file_digest的准备命令错误，改流式sha。最终成功版本仅分析代码改动。子v2→v3只修正并发success+stall分类，保留三份子日志。未重复生产测试或仿真，验证针对真实输入、原始梯度/权重和数值等式。

**D GPU诊断跳过**：原CPU首更复算、保存的真实before/after响应已满足梯度因果核查；无需固定样本再更新。实际新增环境决策0、诊断更新0、GPU使用0秒、生成诊断权重0。16:16核查GPU2有task9.10 T/4719进程286131，GPU1空闲；task12主仓最新记录仍A待教师联合核验，原600s预算独立，本轮未动任何他人进程/容器。

成功父CPU主分析三次内部wall12.698869/12.687256/12.704060s；子三次15.915427/27.272728/27.519428s，合70.707582s；补充1.014589s；父原件验证两次6.191301/12.195785s。已计时计算合128.199s，允许并行的父/子不能相加当全局elapsed；不含解释器启动、末尾落盘、两次父失败准备及只读审计/人工阅读，这些未分别精确计时，不伪报全轮CPU精确累计。任务整体起止与结束检查见执行日志。全部使用CPU float32/torch2线程，未宣称GPU性能改善。

本轮改动仅新增诊断脚本/独立产物/本节点与子节点三文档和日志，维护SOURCES、PROGRESS、父索引/交接；保留既有修改，未提交/推送/合并。下一步是当前决策者核原件、裁定目标与单种子训练协议；无在途诊断、无模型须接回、无环境恢复事项。task12、task11和正式10k/20k×3均未启动。剩余不确定性：单种子、仅首更持久抽样、CPU/GPU数值差、无目标消融及更长训结果、验证状态上未直接训练或选择超参。

结束核验：最终回放表将终局Phi_after明确置0，另保留raw_route_fraction_after，以免把真实路线比例与塑形终局势函数混淆；父再次核7失败终局的原replay身份，rc0。任务/子任务/日志23处本地链接及来源锚点检查0错误，git diff --check通过。最终脚本/表格哈希及起止信息见diagnostic-manifest.json、evidence-hashes.json。

## 决策者复核 · 2026-11-03
CPU独立重跑signal脚本，32 anchors/49 loss rows的critic 0.347938895、actor −0.663928986与原件一致，保留跨设备浮点差限制。接受本轮诊断工程交付done。下一节点16采用固定温度均匀先验KL目标，数学推导及反例先独立复核；原地初始化和负终局覆盖不足仍是独立待验因素，修正目标不能提前宣称任务收益。[修正依据](../../../SOURCES.md#src-t10-035)
