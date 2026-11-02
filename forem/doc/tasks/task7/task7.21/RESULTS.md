# task7.21 — 结果

状态：**尚未执行**（2026-10-21建立；实施已授权，[SRC-0439](../../../SOURCES.md#src-0439)，尚未派发）。

## 运行记录

（尚无。每次执行按run-id追加：执行Agent与实际模型/强度、改动文件、命令、代码/配置版本、退出码、证据路径、结论与限制。）

## 交接

- 当前负责人：未登记（授权后拟由Codex执行、Claude复核）。

## run-id：t7.21-preflight-20261021

2026-10-21T14:22:48+08:00开工，14:23:02复核；负责人Codex，实际模型/强度未知。推荐GPT6.1sol / medium；复核Sonnet5.5 / medium，理由为多模块梯度路由核查。状态：**blocked，尚未实施**，保留上方初始模板历史。

GPU0已存在Xorg PID2212（G，4MiB；整卡14MiB）。按本次用户派发“GPU0无其他进程，被占用则停下报告”停止，无权自行豁免显示进程。证据见[SRC-0500](../../../SOURCES.md#src-0500)及[独立日志](../../../agent_logs/task7/task7.21/20261021-codex-upper-model.md)。

|检查|命令|退出码|结果/日志|
|---|---|---|---|
|GPU0占用|`nvidia-smi -i 0`|0|[gpu0.txt](../../../../logs/task7/t7.21-preflight-20261021/gpu0.txt)，存在Xorg|
|进程身份|`ps -p 2212 -o pid,lstart,comm`|0|[process.txt](../../../../logs/task7/t7.21-preflight-20261021/process.txt)，长期运行Xorg|
|六组单测、参数量与前向计时|尚未执行|不适用|未实现网络；CPU64/GPU32对照容差亦未测|

改动：本RESULTS、本任务独立日志、PROGRESS本任务行、SOURCES SRC-0500及preflight原始日志；未创建task7_upper、未改配置/其他源码。容器计算累计0秒，无训练或后台测试。初次规格读取有输出截断，恢复前须重新按章节完整核查，不将TASK摘录当完成原规格核查。

交接Claude：当前GPU条件阻塞，须明确是否允许常驻Xorg例外，或待GPU0满足无其他进程条件后恢复。没有本任务运行进程。恢复后重新核查GPU与规格，再执行六组验收；交付通过必要验证后方可改review，本次不标完成。


## run-id：t7.21-r2-20261021（2026-10-21T14:40:44+08:00交接）

**当前状态：review（部分交付，非任务完成）。** 负责人Codex；已恢复compute门禁并完成无歧义部分及有界验证，交Claude核查。完整VCM网络规格仍有未定项，**不满足task7.22的task7.21 done依赖**。历史preflight blocked仅保留当时事实；本轮用户明确Xorg为图形服务不计占用。依据[SRC-0501](../../../SOURCES.md#src-0501)，实测依据[SRC-0502](../../../SOURCES.md#src-0502)。

实际模型/强度：派发进程2535684参数`gpt-6.1-sol / medium`。推荐Codex **GPT6.1sol / medium**、Claude **Sonnet5.5 / medium**，理由为多模块梯度与零初始化等价核查；推荐不是复核已执行的配置。

### 实际改动与接口

新包`forem/src/task7_upper/`下7个生产文件：

|文件|实际内容与边界|
|---|---|
|`__init__.py`|导出六类模块|
|`bias.py`|两个Linear256→128全零，h先detach，e＋sigmoid(Wg[e,h])⊙Wd[h,e]|
|`heads.py`|Actor128→128(ReLU/LN)→1，双Q256→256→256→1；B复制A接口；Critic激活必填，未代替用户选定|
|`world_model.py`|384→256→128核心、128→128(GELU)→128预测、随机冻结版本、外部固定仿射系数；目标编码no_grad/detach|
|`candidate_encoder.py`|几何6＋f_k19投影、状态令牌、2层128/4头/FF256 Transformer；无槽位编号；固定归一化；Transformer未定选项必填；屏蔽值先清零避免补齐NaN污染有效槽位|
|`vcm.py`|仅FIFO4/按env重置/无梯度前缀恢复/未修正GRU状态编排。f_enc、retrieval、gate必须注入，动作/结果合并维数必须给定；**未实现具体CNN/几何与步差注意力/门网络**|
|`model.py`|从外部VCM状态组装候选/头/ψ/f_p，按1/2/3/G2/G3/adapt冻结及返回可训练参数组；可注册VCM以统一冻结。Actor使用`actor_q1/2`截断值，Critic使用`q1/q2`，防止真实离散Actor loss沿Q分支泄漏；无loss/optimizer/训练循环|

测试文件：`tests/test_contracts.py`与`tests/benchmark.py`；没有新增项目配置。另改本RESULTS、独立日志、PROGRESS本行、SOURCES0501–0502，以及本run日志/JSON产物。没有修改task7_sim、阶段一或参考仓库，没有git提交，没有启停/重建容器或停止非本任务进程。

组装时task7.22须在阶段1检查点载入后显式调用`copy_head_b_from_a()`再进入3/G2/G3；`set_stage()`只切路由，不覆盖已有B权重。`trainable_parameters()`只枚举本包注册参数，不含下层、log_alpha与目标副本；它们属task7.22。VCM runtime memory/hidden按env保存在对象内、不在state_dict内；换环境/恢复序列须reset或rebuild_prefix。

### 命令、退出码与证据

共同前缀：`sg docker -c 'docker exec -e CUDA_VISIBLE_DEVICES=0 -e PYTHONPATH=/root/mm_husky_ws/src -e OMP_NUM_THREADS=1 … forem-dev timeout 120 python3 …'`。精确argv、开始unix时间、wall和退出码见[commands-v2.json](../../../../logs/task7/t7.21-r2-20261021/commands-v2.json)。每条前先核查GPU0 compute；最终各gate文件均仅表头。

|运行|命令差异|退出码|结果与日志|
|---|---|---|---|
|初始RED|`-m pytest -q …/task7_upper/tests`（包尚不存在）|外层未保存pytest码；日志为collection error|[red.log](../../../../logs/task7/t7.21-r2-20261021/red.log)，明确失败，不当通过|
|初轮GREEN|同上|0|[green1.log](../../../../logs/task7/t7.21-r2-20261021/green1.log)，12 passed|
|Actor真实公式RED|`-m pytest -q …/task7_upper/tests -k discrete_sac_actor`|1|[actor-red.log](../../../../logs/task7/t7.21-r2-20261021/actor-red.log)，4 failed（缺Actor截断Q接口），随后实现并复测|
|最终CPU|`-e TASK721_DEVICE=cpu … -m pytest -q -s /root/mm_husky_ws/src/task7_upper/tests`|0|[cpu-final-v2.log](../../../../logs/task7/t7.21-r2-20261021/cpu-final-v2.log)，24 passed/3.08s；容器命令wall 3.836s|
|最终GPU|`-e TASK721_DEVICE=cuda … -m pytest -q -s /root/mm_husky_ws/src/task7_upper/tests`|0|[gpu-final-v2.log](../../../../logs/task7/t7.21-r2-20261021/gpu-final-v2.log)，24 passed/4.18s；容器命令wall 5.075s|
|最终数值/计时|`-u /root/mm_husky_ws/src/task7_upper/tests/benchmark.py`|0|[benchmark-final-v2.log](../../../../logs/task7/t7.21-r2-20261021/benchmark-final-v2.log)，[benchmark.json](../../../../results/task7/t7.21-r2-20261021/benchmark.json)；wall 11.200s|

首轮20项GPU与旧接口计时以及final-v1日志保留为历史。最终以v2为准。共11次容器计算命令，每次timeout120s，保守预算上界1320s＜60分钟，未计时的早期命令不虚构精确累计；有精确记录的两个最终组三命令累计40.214s。无长训或后台计算；单测一次合成SGD用于检查随机f_p参数不更新，非训练任务。

代码版本：主仓库HEAD `cac6c15599efcbe47a1a7ed30f59a475e4997fd4`；未提交包与测试逐文件SHA256见[source_manifest.json](../../../../logs/task7/t7.21-r2-20261021/source_manifest.json)。容器/torch/GPU见[SRC-0502](../../../SOURCES.md#src-0502)。

### 六组验收逐项结论

|验收组|实际验证|结论与限制|
|---|---|---|
|1 零初始化|CPU/GPU32逐元素比较ψ(e,h)与e、A/B的logits与双Q；Wg零且Wd非零反例|通过所测输入，float32 atol=rtol=0；数学依据Wd权重/偏置全零使δ逐元素0（有限输入）|
|2 梯度路由|`test_trainable_sets_and_routes`六阶段；`test_discrete_sac_actor_objective`真实离散Actor公式；`test_vcm_freeze_by_phase`与VCM Actor/Critic路由；h进入ψ前detach|明确模块/注入夹具通过。阶段1 Actor对VCM/候选0而Critic非0；2只有f_p；3 RL只ψ/B，预测只f_p；G2只B；G3随机f_p冻结；adapt预测回候选/f_p，其他0。完整VCM结构尚未验收|
|3 掩码|padding改变含NaN不影响有效输出；移除补齐槽位；全槽重排对应重排；固定归一化检查|通过夹具Transformer配置；无槽位嵌入/BatchNorm。非法全空mask/T_seg/可达半径拒绝|
|4 VCM|FIFO只留最近4步、前缀no_grad重建逐元素一致、只重置指定env、GRU保留未修正状态|**部分通过**：仅编排与注入夹具，真实f_enc/检索注意力/门未实现，不能宣称完整VCM通过|
|5 f_p|128输出维、随机版本冻结且一次其他参数更新后不变、状态序列化、逐维给定仿射、目标detach|通过；系数由外部给定，没有拟合留出统计，尚无训练后f_p|
|6 参数/计时|32×8展平为256个状态、K13，各明确模块20次测量|**部分交付**：不含真实VCM，也不是32条8步的递推全路径；完整VCM与完整上层计时尚未执行|

### 参数量与数值、计时

固定测试夹具（**非项目已定配置**）：Transformer dropout0、ReLU、norm_first=False、LN epsilon1e-5、bias=True，Critic激活ReLU；VCM夹具为Linear3→128＋均值检索＋拼接门，仅供编排测试，不用于上述计时。默认项目网络配置仍待定。

GPU32与CPU64逐阶段输出对照，最大绝对差 **1.58166632369e-06**；本次工程检查容差atol1e-5、rtol1e-4。零初始化等价另用严格0容差。CPU64/GPU32不是相同数值精度的速度对比，不能据此宣称端到端GPU收益。

以下都是**每256状态前向**毫秒中位数；torch单线程、eval/no_grad、预热3次、样本20次、GPU逐次同步；原始min/max与全部数值在JSON。

|模块|参数量|CPU64 wall ms|GPU32 wall ms|CUDA事件 ms|
|---|---:|---:|---:|---:|
|candidate_encoder|285,184|61.2650|1.6421|1.6146|
|head_a|280,579|30.4536|0.3622|0.3474|
|head_b|280,579|30.4229|0.3543|0.3392|
|bias|65,792|8.7722|0.1323|0.1188|
|world_model|164,480|19.2604|0.2092|0.1959|
|random_world_model|164,480|19.2902|0.2075|0.1934|
|upper_from_state（含上述部分路径，非VCM）|注册总量1,241,094|139.1303|2.3788|2.3516|

参数总量包括A/B和随机f_p，不等于每阶段可训练参数量。GPU参数/输入设备均cuda:0；测试allocator峰值28,071,936 B、reserved33,554,432 B；计时allocator峰值53,869,056 B、reserved71,303,168 B；nvidia-smi该测试进程快照738MiB，低于4GB。不是长期峰值实测；另用3.5GiB allocator限制留出上下文空间，未发生OOM或CPU回退。

### 待决定、未通过与交接

无当前测试失败；**任务整体未验收**。停止部分的精确位置/缺口/可选理解详见[独立日志](../../../agent_logs/task7/task7.21/20261021-codex-upper-model.md)“待决定”。本次不发起文档复核轮次，不自行确定缺失结构或默认参数。

交Claude：先复核明确模块与证据、保留其他会话改动；需确定VCM具体f_enc/检索/gate/GRU输入编码、Transformer选项和Critic激活后，才可补完整VCM与真实32×8序列参数/计时及全模型梯度验收。task7.22不能把本轮review当done依赖。下一执行仍限定本任务包与原预算；没有剩余运行进程，无需停止或恢复容器。本轮没有性能优化方案/训练效果结论。


## run-id：t7.21-r3-20261021（2026-10-21T17:03:44+08:00验收，review）

负责人Codex，实际模型`gpt-6.1-sol / medium`（宿主派发PID2695455参数核实）。推荐执行Codex **GPT6.1sol / medium**、复核Claude **Sonnet5.5 / medium**，理由为跨模块梯度与递推合同核查。按用户本轮决定[SRC-0903](../../../SOURCES.md#src-0903)补全r2停止部分，结构映射见[SRC-0503](../../../SOURCES.md#src-0503)，全部实测及限制见[SRC-0504](../../../SOURCES.md#src-0504)。上方初始“尚未执行”、preflight blocked及r2部分review均为历史，本轮为**完整网络实现与必要合成验证已交付，待Claude复核**，不自行标done。

### 实际改动与调用接口

- `forem/src/task7_upper/vcm.py`：新增真实ObservationEncoder（三层3×3 valid/stride2/ReLU，3→16→32→32，7200维展平拼向量→128）、单头MemoryRetrieval（QKV/exp(logit_scale)/时间偏置/postnorm/4×GELU）、零初始化几何Linear和Embedding5、std1e−4/bias2门、GRU输入同步151/不同步152；保留按env FIFO4/reset/rebuild_prefix。真实检索在一个batch内计算，不逐环境调用网络；无额外损失/机制。
- `candidate_encoder.py`：默认GELU/postnorm/eps1e−12/dropout0/bias=True；Δs固定÷3.2；其余沿用r2。旧`reachable_radius`可继续传正值但不再决定Δs缩放（只兼容校验）；新调用可省略。`heads.py`：Critic默认ReLU。
- `model.py`：`UpperModel(vector_dim=D, asynchronous=False/True)`直接组装默认完整网络；`forward_step(vcm_inputs, geometry6, features19, mask)`真实递推VCM后走候选/两头/ψ/f_p路由；`forward(state,...)`仍可用于已有状态。原训练参数组与Actor专用截断Q保持不变。
- `__init__.py`导出ObservationEncoder/MemoryRetrieval；`tests/test_contracts.py`改用新默认候选配置与固定Δs断言；新增`tests/test_full_vcm.py`；`tests/benchmark.py`替换为真实递推与各模块分项计时。`bias.py/world_model.py`沿用r2未改。没有新增配置文件。
- 其他写入：本RESULTS、原独立日志、PROGRESS仅本任务行、SOURCES0503/0504、本run日志/JSON。没有修改task7_sim、下层、参考仓库、其他任务源码；没有训练、启停容器、停止非本任务进程或git提交。

**调用者输入边界**：f_enc接收`(grid[N,3,128,128], vector[N,D])`；grid为已解码的3通道观测，vector按task7.8 B.1包含关节/TCP/路线/上一执行结果/上一候选/变体/失败计数/卡住计数，由task7.22对接，D必须显式给定以适配既有路线布局，不新增默认路线点数。VCM的`action_result[N,23/24]`顺序为上一候选当前B_t的4维相对位姿、不同步另1维Δs、19维f_k v1上一执行结果。`VCM.previous_features(previous_world_pose,current_world_pose,result_v1,delta_s=None)`可完成位姿换系与拼接；不自行从环境r_t缺省猜出19维。网络包不渲染/不量化/不构造经验池。

`pose[N,3]`、整数`step[N]`、Python `env_ids`只用于记忆几何/时间/归属；episode reset或重建前缀由调用者显式给定。runtime memory/hidden不在state_dict中。阶段1末载入权重后仍须显式`copy_head_b_from_a()`，set_stage不覆盖已训练B；log_alpha、优化器、loss、目标副本归task7.22。

### 命令、退出码与失败保留

共同命令前缀：`sg docker -c 'docker exec -e CUDA_VISIBLE_DEVICES=0 -e PYTHONPATH=/root/mm_husky_ws/src -e OMP_NUM_THREADS=1 -e MKL_NUM_THREADS=1 … forem-dev timeout 120 python3 …'`。每次运行前GPU0 compute门禁仅表头；精确argv/start/wall/退出码见[commands.json](../../../../logs/task7/t7.21-r3-20261021/commands.json)。

|运行|命令/输入差异|退出码|实际结果与日志|
|---|---|---|---|
|首轮CPU|`-e TASK721_DEVICE=cpu … -m pytest -q -s /root/mm_husky_ws/src/task7_upper/tests`|0|[cpu-first.log](../../../../logs/task7/t7.21-r3-20261021/cpu-first.log)，34 passed；随后加不同步六阶段测试|
|首轮GPU|`-e TASK721_DEVICE=cuda … -m pytest …`|1|[gpu-first.log](../../../../logs/task7/t7.21-r3-20261021/gpu-first.log)，39 passed/1 failed；完整网络重算严格torch.equal失败|
|首轮数值|`-u …/tests/benchmark.py`|1|[benchmark.log](../../../../logs/task7/t7.21-r3-20261021/benchmark.log)，native Transformer CPU64/GPU32超旧1e−5容差|
|定位1/2|`docker exec -i … python3 -`，输入脚本分别保存|各0|[diagnose.log](../../../../logs/task7/t7.21-r3-20261021/diagnose.log)、[attention.log](../../../../logs/task7/t7.21-r3-20261021/attention.log)：同特征头A/B精确相等；改fastpath与TF32未消除阶段重算末位差异|
|TF32关闭再测|`-u …/tests/benchmark.py`|1|[benchmark-fp32.log](../../../../logs/task7/t7.21-r3-20261021/benchmark-fp32.log)，跨精度差异不变|
|数值定位|`docker exec -i … python3 -`，输入见numeric-diagnose.py.txt|0|[numeric-diagnose.log](../../../../logs/task7/t7.21-r3-20261021/numeric-diagnose.log)，误差定位至native快速路径相关，未声称底层原因|
|最终数值/递推计时|`-u …/tests/benchmark.py`|0|[benchmark-final.log](../../../../logs/task7/t7.21-r3-20261021/benchmark-final.log)，wall65.401s；[benchmark.json](../../../../results/task7/t7.21-r3-20261021/benchmark.json)|
|最终CPU|`-e TASK721_DEVICE=cpu … -m pytest …`|0|[cpu-final.log](../../../../logs/task7/t7.21-r3-20261021/cpu-final.log)，40 passed/4.14s，命令wall4.928s|
|最终GPU|`-e TASK721_DEVICE=cuda … -m pytest …`|0|[cuda-final.log](../../../../logs/task7/t7.21-r3-20261021/cuda-final.log)，40 passed/5.13s，命令wall6.042s|

本轮10条容器计算命令wall累计109.994s，最长65.401s；每条timeout120s。继承r2保守累计上界1320s，再加本轮109.994s仍<60min。单测沿用的一次合成SGD仅检查随机f_p不变，不是训练任务。无后台长计算。HEAD仍`cac6c15599efcbe47a1a7ed30f59a475e4997fd4`，未提交包逐文件哈希见[source_manifest.json](../../../../logs/task7/t7.21-r3-20261021/source_manifest.json)，与benchmark记录逐项核对相同。

### 六组验收

|验收组|本轮完整验证与结论|
|---|---|
|1 零初始化|CPU/GPU32逐元素0容差验证ψ(e,h)=e、同e下A/B logits与双Q完全相等；Wg零/Wd非零反例。完整网络同状态跨阶段重算按逐元素atol=rtol=1e−6通过：CPU差0，GPU logits最大4.172325e−7、Q1≤7.450581e−8/Q2≤6.332994e−8。**整网重算不宣称逐位相同**；严格恒等层和复制头的性质仍为0容差|
|2 全模型梯度|同步/不同步两变体六阶段均验收；4步真实VCM no_grad预热＋4步递推图。阶段1真实离散Actor公式只给Actor_A梯度；双Q loss给CNN/融合/检索QKV/FFN/几何/Embedding/λ/logit_scale/gate/GRU及候选编码/双Q梯度。阶段2仅f_p；3仅ψ/B有RL梯度，f_p只受1−cos预测损失；G2仅B；G3随机f_p完全冻结；adapt预测回候选/f_p而VCM/A/B/ψ无梯度。h进入ψ前detach测试保留|
|3 掩码与固定归一化|新默认GELU/eps1e−12下有效槽不受补齐值（含NaN）或移除补齐槽影响，重排对应重排，无槽位嵌入；距离/Δs固定÷3.2，时间/T_seg；不使用BatchNorm/运行统计|
|4 真实VCM|CNN、真实单头检索、初始几何/步差编码及非零编码反例、手算注意力公式、SE(2)换系、clamp、门初始化；同步/不同步FIFO4、no_grad前缀重建逐元素一致、指定env重置/整批重置、空记忆直接用v、未修正GRU逐步等式均通过|
|5 f_p|128维输出、随机冻结参数不更新/序列化、逐维给定仿射作用于h而非预测头、真实f_enc目标no_grad/detach均通过；无留出集仿射系数拟合或训练后f_p|
|6 参数/计时|真实32流各按时间递推8步（K13，其中11个有效+2补齐），完整VCM与UpperModel同步/不同步计时；单模块另用256状态批测，不混称递推。全部原始20次样本、min/max、中位数与CUDA事件在JSON|

### 参数量与前向计时

下表同步**合成向量D=80**，含A/B与随机f_p的总参数为**2,511,624**；VCM为**1,270,530**（f_enc946,304、检索183,426、门32,896、GRU107,904）。不同步例D=81总2,512,136，VCM1,271,042。向量每增一维f_enc增加128参数；相同D时不同步GRU比同步多384参数，故该异步示例比同步多512。实际环境向量D由task7.22按其字段布局给入，**80/81不是新增项目观测规格**。

各阶段可训练参数组：1＝VCM1,270,530＋候选285,184＋A280,579；2＝f_p164,480；3＝B280,579＋ψ65,792＋f_p164,480；G2＝B280,579；G3＝B280,579＋ψ65,792；adapt＝候选285,184＋f_p164,480。均不含log_alpha、下层或目标副本。

计时为CPU64/GPU32的eval/no_grad；torch单线程，预热3次/采样20次，逐次GPU同步；TF32关闭、Transformer native fastpath开启。单位ms，数值为中位数，不是训练/环境端到端成本；不以两种精度的比值宣称GPU优化收益。

|模块/输入规模|参数量|CPU64 wall|GPU32 wall|CUDA事件|
|---|---:|---:|---:|---:|
|f_enc，256观测|946,304|624.2451|0.4829|0.4741|
|记忆检索，256×4|183,426|4.0793|0.7990|0.7782|
|门，256|32,896|0.2585|0.0644|0.0513|
|GRU，256|107,904|1.1922|0.0980|0.0851|
|候选编码，256×13|285,184|48.4363|1.6492|1.6232|
|头A，256×13|280,579|30.2774|0.3554|0.3408|
|头B，256×13|280,579|30.2639|0.3523|0.3376|
|ψ，256×13|65,792|8.9792|0.1321|0.1186|
|f_p，256×13|164,480|18.9879|0.2071|0.1931|
|随机f_p，256×13|164,480|18.9359|0.2062|0.1925|
|VCM，真实32×8|1,270,530|333.5855|36.9936|36.9644|
|完整上层同步，真实32×8×13|2,511,624注册总量|472.6465|56.0248|55.9933|
|完整上层不同步，真实32×8×13|2,512,136注册总量|466.4668|56.1695|56.1340|

完整前向计时为阶段3实际路径（用B/f_p/ψ，不重复运行未用的A/随机f_p）；总参数列包含注册但当次未执行的分支。CPU64整批CNN与按步32批的耗时不能相加替代真实递推耗时。

### 数值、GPU与已知限制

- CPU64/GPU32完整8步六阶段的**非融合参考路径**最大差1.835819146034e−6，逐元素atol1e−5/rtol1e−4通过。**native快速路径**最大2.906719968494e−4，工程记录容差atol5e−4/rtol1e−4；不同步阶段3 logits差1.674441e−4，其他关键输出亦通过该容差。默认路径不满足旧1e−5容差，初次失败日志保留；诊断只定位到native路径相关，未核查其底层近似，不改生产fastpath开关。该容差是合成数值对照口径，不能变成训练成功率/研究效果验收。
- 基准所有网络参数与输入在cuda:0，GPU0进程快照1012MiB，allocator峰值280,296,960 B/reserved350,224,384 B，低于4GB。最终GPU单测allocator峰值51,412,480 B/reserved65,011,712 B。未发生OOM或CPU回退；快照/allocator不是长训显存承诺。
- [final-gate.txt](../../../../logs/task7/t7.21-r3-20261021/final-gate.txt)仅compute表头；没有本任务运行进程。不占GPU1/2/3、不停止其他任务。
- 没有剩余网络规格待决定或最终失败测试；环境r_t→f_k v1映射、vector字段拼接/维数、量化解码与检查点加载由task7.22在其授权内对接，未改其文件。没有训练、环境/经验池端到端计时、G3统计拟合、任务成功率或预测质量结论。

### 交接

当前状态**review，交Claude复核**。目标/授权仅task7.21完整网络与合成验收，负责人Codex；代码/参数/计时/失败原因/容差已落上述证据路径。r2待决定已按用户SRC-0903实施；本轮不再存在被停止的具体网络结构。Claude下一步读本run和原独立日志，核查默认参数、零初始化、全模型梯度与数值边界，再决定是否标done；task7.22的done依赖应以Claude实际复核为准。无运行任务需停止或恢复。

## Claude复核 t7.21-r3（2026-10-21T19:55–20:10，claude-opus-5-5，推理强度未知；只读核查＋重跑测试）

- 授权：用户“顺便你复核7.21”（[SRC-0521](../../../SOURCES.md#src-0521)）。未改task7_upper代码。
- 重跑：`docker exec … TASK721_DEVICE=cpu|cuda, CUDA_VISIBLE_DEVICES=0 … pytest -q -p no:cacheprovider …/task7_upper/tests` → CPU 40 passed（4.19 s）、GPU0 40 passed（5.26 s），与r3一致。
- 读码核对（bias.py、heads.py、world_model.py、candidate_encoder.py、model.py；vcm.py抽查接口）：
  - 偏置层两Linear权重与偏置零初始化、h进入前detach，形式同U16 ✓。
  - 阶段路由与U.4表一致：阶段1只训VCM/候选编码/头A，Actor输入e detach、Actor用detach后的Q；阶段2只f_p；阶段3为ψ/头B/f_p且state detach；G2只头B且不接ψ；G3用随机冻结f_p＋仿射缓冲；适应期只候选编码与f_p、策略输出detach ✓。
  - 头A/B结构、Critic ReLU、Transformer（GELU、后归一化、eps 1e−12、dropout 0、无槽位嵌入）、f_p 384→256→128＋预测头与SRC-0903、W.1一致 ✓。
- 独立小验证（scratchpad脚本，CPU）：阶段1 Actor损失对状态与候选编码器梯度为0、Critic损失对状态梯度非0；阶段1末复制头B后进入阶段3，同一输入logits最大差5.4e−7、Q1差8.9e−8（来自Transformer在训练/评估模式下的native快速路径，与r3“整网重算不宣称逐位相同”一致）。
- **须返工（r4）**：
  1. **不同步变体缺候选目标进度Δs_k**。task7.10 U.1写明候选几何为(Δx, Δy, sinΔθ, cosΔθ)、距离、原地标志，**不同步另加Δs_k**；实现固定为6维（`candidate_encoder.py`的`nn.Linear(6, 128)`与`normalize`的形状检查），两变体相同。f_k ⑦的Δs是推演实际推进量，推演提前失败时不等于目标Δs_k，因此不能替代。须按变体取6/7维（Δs_k按SRC-0903第8项除以3.2 m），并补测试；`UpperModel(asynchronous=True)`应把该维数传给候选编码器。
- 记录、不要求改：
  2. f_k ⑤T_seg被归一化为常数1（自除），丢失T_seg本身；D20原意为“供固定常数归一化”。补上Δs_k后，T_seg由几何（初始距离、朝向差）与Δs_k决定（D7），信息冗余，暂按现实现接受；若要改为固定常数需另定常数，由用户决定。
  3. 阶段3接入一致性在native快速路径下为~1e−7量级而非逐位相等；task7.22的硬性断言须使用明确容差（如atol 1e−6）或在断言时用非融合参考路径，不能用严格相等。
- 结论：**未标done，退回Codex做r4**（只修第1项及其测试，预算沿原任务剩余额度）；第3项写入task7.22派发前提示。


## run-id：t7.21-r4-20261021（2026-10-21T20:18+08:00，review）

负责人Codex；实际`gpt-6.1-sol / medium`（派发PID2912552参数核实）。推荐Codex **GPT6.1sol / medium**、Claude **Sonnet5.5 / medium**，理由为变体输入及跨模块梯度合同核查。本轮只处理Claude r3复核第1项，规格与证据统一见[SRC-0505](../../../SOURCES.md#src-0505)，目标进度缩放沿[SRC-0903第8项](../../../SOURCES.md#src-0903)。

### 实际改动与接口

- `candidate_encoder.py`：显式`geometry_dim=6|7`，同步默认6维，不同步7维；输入顺序`[Δx, Δy, sinΔθ, cosΔθ, 距离, 原地标志, (异步Δs_k)]`。`normalize`接受6/7维，末维目标Δs_k独立除以3.2 m，和f_k第12索引的实际推进量分别保留；forward拒绝与实例变体不符的宽度。其他归一化不变。
- `model.py`：`UpperModel(asynchronous=True)`向默认候选编码器传`geometry_dim=7`，同步传6；显式注入的编码器仍由调用者负责构造。
- 测试：输入夹具支持6/7维；两变体的掩码/NaN padding/移除补齐/重排/归一化、目标进度独立性及错误维数拒绝；异步六阶段完整递推梯度测试使用真实7维；整网阶段1→3零初始化测试覆盖两变体，保留atol=rtol=1e−6。同e两头及ψ恒等仍严格相等。
- `tests/benchmark.py`异步输入补目标Δs_k，输出目录改为r4，避免覆盖r3证据；本轮**没有执行基准**，仅AST语法核查。其他代码未修改；f_k⑤T_seg自除保留，未改fastpath或既有容差。

### 命令、结果与预算

运行于已有`forem-dev`；精确命令/退出码/wall见[commands.jsonl](../../../../logs/task7/t7.21-r4-20261021/commands.jsonl)。共同前缀`sg docker -c 'docker exec -e CUDA_VISIBLE_DEVICES=0 -e TASK721_DEVICE=cpu|cuda -e PYTHONPATH=/root/mm_husky_ws/src -e OMP_NUM_THREADS=1 -e MKL_NUM_THREADS=1 forem-dev timeout 120 python3 -m pytest …'`；全目录命令为`-q -s -p no:cacheprovider /root/mm_husky_ws/src/task7_upper/tests`。

|运行|退出码|实际结果|
|---|---|---|
|RED：test_contracts.py -k variant_geometry|1|[red.log](../../../../logs/task7/t7.21-r4-20261021/red.log)：1 failed/1 passed；异步应7维实际6维，先复现再修复|
|CPU全目录|0|[cpu-final.log](../../../../logs/task7/t7.21-r4-20261021/cpu-final.log)：44 passed，4.14s|
|GPU0全目录|0|[gpu-final.log](../../../../logs/task7/t7.21-r4-20261021/gpu-final.log)：44 passed，5.23s|

GPU0在运行前无其他compute进程，故未使用GPU2；未占GPU1/3。allocator峰值allocated 51,413,504 B、reserved 65,011,712 B。同步/不同步阶段切换logits最大差分别4.17233e−7/4.76837e−7，双Q最大7.45058e−8，在既有容差内。最终[compute门禁](../../../../logs/task7/t7.21-r4-20261021/gpu-final-gate.txt)仅表头，没有本任务运行进程。

三次计算wall合计13.177s、单条最长6.293s；继承r2保守1320s＋r3实际109.994s，本轮累计上界约1443.171s（24.053min），仍低于原60min预算。汇总与代码哈希见[summary.json](../../../../logs/task7/t7.21-r4-20261021/summary.json)、[source_manifest.json](../../../../logs/task7/t7.21-r4-20261021/source_manifest.json)。全包Python AST解析通过。全工作区`git diff --check`仍报告其他任务PROGRESS行62旧行尾空格，本轮未修改该行。

### 限制与交接

r4异步候选编码器参数量由r3加128权重，推导为285,312；D81异步完整注册参数量推导2,512,264，同步不变（推导输入/公式见SRC-0505）。r3异步计时属于旧6维实现，不作为r4实测；本轮没有新增性能或跨精度结论。

状态**review，待Claude复核，不标done**。task7.22接入时同步候选6维、不同步7维，末维给目标Δs_k，勿用f_k实际推进量替代；旧异步6维投影权重形状不兼容。阶段切换断言继续明确atol=rtol=1e−6，不能改为严格整网相等。无剩余本轮修改项，无本任务后台进程；未启动/恢复训练、未启停容器、未停止非本任务进程、未提交git，未修改task7_sim等其他任务包。下一步Claude按上述证据复核本项后决定是否标done，task7.22依赖仍以实际复核为准。

## Claude复核 t7.21-r4（2026-10-21T20:20–20:30，claude-opus-5-5，推理强度未知）

- 重跑（GPU3空闲）：`TASK721_DEVICE=cpu`与`cuda`下`src/task7_upper/tests`各**44 passed**。
- 读码：`CandidateEncoder(geometry_dim=6|7)`，不同步第7维Δs_k÷3.2 m（SRC-0903第8项），形状不符即报错；`UpperModel(asynchronous=True)`传7维；f_k距离类字段÷3.2 m。r3复核第1项已解决；第2、3项按记录接受（task7.22断言须用明确容差）。
- 结论：**task7.21 done**。
