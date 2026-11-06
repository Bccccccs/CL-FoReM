# task10.15.1 首更信号与梯度核查结果

2026-11-03 · **done，父原件复核已接受工程交付**。完成CPU只读复算，0新增环境决策、0诊断更新、0 GPU使用。全部数据依据[SRC-T10-033](../../../../SOURCES.md#src-t10-033)。负责人Codex子Agent；实际平台GPT-6，具体变体/推理档位未知，未伪称推荐配置。推荐GPT6.1sol/high、Sonnet5.5/high，理由为变时长目标与梯度因果复核。执行者可自主选模及先建档委派，本子未再派发。

工作树`/home/ybc/projects/CL-FoReM-task10`，分支`codex/task10-upper-wm`，HEAD`91f538cf2ee10bebffd6b643d5c908fa0d419ced`加工作树代码；未修改训练源码或源run。只读online原首更before/after/sample/evidence、offline完整learner/replay与episodes.jsonl。复算脚本为`forem/scripts/task10_signal_diagnostic.py`，冻结副本及全部原件在`forem/results/task10/t10-diag-20261103-s101/signal-*`，哈希见`signal-evidence-hashes.json`。共享SOURCES与总预算由父统一登记。

## 复算方法与实际执行

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 -u /workspace/scripts/task10_signal_diagnostic.py --source /workspace/results/task10/t10-online-20261102-s101 --output /workspace/results/task10/t10-diag-20261103-s101'
```

执行三次均rc0，日志`signal-command.log`（首更）、`signal-command-v2.log`（增加保存模型前后与stall链前向）、`signal-command-v3.log`（只修正分类：并发stall trigger与strict_success须分别列示）。不执行optimizer.step，保留三份日志，最终表格以v3为准。三次脚本内部计时分别15.915427、27.272728、27.519428秒，合计70.707582秒；包括读取/前向/梯度/统计至汇总，不含解释器启动与末尾落盘，不冒充完整outer墙钟。torch线程2、CPU float32；CUDA_VISIBLE_DEVICES为空。

从before checkpoint恢复learner、optimizer、scheduler、温度与完整replay，恢复CPU/Python/NumPy RNG，再从replay原RNG抽样。32个fragment身份与原`first-update-sample.json`完全一致，按原`sequence_outputs`重建前缀/记忆与next分支，得到49个真实loss transitions，无padding loss，在线/target行身份一致。以episodes.jsonl的真实route_length重算奖励；最大绝对差`1.4318316e-8`。表格保留每行环境/episode/decision/map/selected、实际phi/r/g/mask、next Q/熵、target、actor项及梯度，避免仅凭均值归因。first sample没有stall终局，不能推断200次更新分别抽中过哪些条目。

## 首更目标、梯度与保存模型响应

|量|CPU复算|原GPU执行|绝对差|
|---|---:|---:|---:|
|critic loss|0.3479388952|0.3479388058|8.94e-8|
|actor loss|−0.6639289856|−0.6639290452|5.96e-8|
|joint gradient norm|2.1153285618|2.1153280735|4.88e-7|

首更逐head原始gradient与CPU差最大`1.49e-7`，norm低于原clip10，没有剪裁影响。actor logit梯度与解析式`p_k[αlog p_k−Q_k−E_p(αlog p−Q)]/49`最大误差`6.40e-10`。原地logit在49/49行梯度均为正，局部梯度下降方向是降低原地logit；Q项拉高原地，熵项抑制其集中且占优。不能将此局部坐标结论等同神经参数步进结果，因此同时前向读取真实保存的after-first与final模型：

|在原首更49个train loss状态前向|原地概率均值|原地argmax|相对before概率下降|
|---|---:|---:|---:|
|before（0更新）|0.283804741|49/49|—|
|after-first（保存的真实1更新）|0.268547091|49/49|49/49|
|final（保存的真实200更新）|0.205615069|49/49|48/49|

实际一次更新令原地logit平均下降0.111270124，原地概率平均下降0.015257649，所选Q1/Q2平均上升0.049646472/0.055440230。它已产生符合局部actor方向的概率变化，但尚未改变argmax。final相对before原地概率平均下降0.078189671，1行增加；不能把argmax未变说成模型没有学习。

actor loss只给head_a.actor 6个参数张量梯度，不进入VCM、candidate_encoder或Q；critic只进入VCM35（34非零）、candidate_encoder32、Q1/Q2各6张量，不进入actor。这符合stage1候选embedding detach和actor-Q detach的现行设计。optimizer恰含全部85个trainable张量各一次；原首更实际改变VCM34、候选encoder32、head_a18张量，head_b/bias/两个WM均不变。对`|grad|>1e-7`的1,481,415个元素，原首更参数delta全与joint gradient反向，0反向错误、0未变；这只验证首步Adam方向，不代表200次历史梯度已逐次保存。

## 零耗时软价值与终局传播

首样本有3行零尝试原地，r=0、dt=0、g=1、bootstrap=1：

|loss行；环境/episode/decision|next E[minQ]|next αH|实际target|代数去熵target|
|---|---:|---:|---:|---:|
|33；2/41/1|−0.026708415|0.780598223|0.753889799|−0.026708424|
|39；3/4/2|−0.031516992|0.700562596|0.669045627|−0.031516969|
|46；1/24/4|−0.014818355|0.455357790|0.440539449|−0.014818341|

行33真实phi保持0.230257861；selected Q1/Q2=0.123671800/0.036014099，因soft target0.753889799，critic对两Q导数为−0.012861593/−0.014650525，梯度下降会抬高两者。该步没有物理耗时，却获得0.780598223的next熵贡献；去熵数值仅为同目标拆项，未用于更新。行39/46 phi均为1但尚未严格成功，r仍0，不能把route_s==length当成功。

全回放8个episode有stall trigger，其中**7个停滞失败，1个同时strict_success**（环境4/episode12，原件stalls5、strict_success真），二者不能混并。对8条完整真实链共53状态，用before/after-first/final三个保存模型各恢复真实VCM历史并只前向，产出159行`signal-stall-chain-rows.csv`。

7个失败终局实际所选均为移动槽1/2/3，r=−1、bootstrap=0，因此target恒为−1，next Q和熵贡献严格0。final所选Q1/Q2仍落在−0.099331111至0.192093313，残差0.900668859至1.192093372。**终局负标签存在且mask正确，但明显未拟合；它直接监督这些实际移动槽，不能当作原地终局被充分监督的证据。** 同状态原地minQ为0.424660712–0.489589840，actor argmax7/7仍原地；在最终模型按每行平均前的actor局部梯度，6/7行仍推动增大原地logit，1/7推动减小。例环境1/episode49/decision5：真实selected3、target−1，Q1/Q2=−0.080645874/−0.045287654；原地minQ0.439341784，最佳移动minQ0.183937222，原地概率0.334805071，`dL_actor/dlogit12=−0.012844759`（逐行未除batch），显示未拟合及候选价值差如何进入actor。

`signal-stall-chain-returns.csv`另列记录路径的折扣reward和逐步`bootstrap*g*αH(next)`贡献。7失败链原始折扣reward约−2.09e-7至−3.47e-7（float32望远镜残差），所观察next熵贡献总和0.294901860–1.966556982，故两项相加可为正。**这是沿记录的off-policy路径的代数诊断，不是该策略期望回报或反事实行动效果。** 最终stall确实停止bootstrap，不会形成无限环，但之前附加的软价值仍然存在。并发成功链单列，没有把其正reward错算为失败回报。

## 日程、假设裁定与交接

原optimizer lr从首步前`1e-4`，首更后`9.7723722e-5`，200步后`1e-6`。调度按`lr(u)=1e-4*0.01^(u/200)`实现，总200步lr之和0.0043492053，属于现有工程配置；不等于优化效果或科学标准。target τ=.001，若online在第一步一次跳变后固定，200步吸收比例`1−(1−.001)^200=0.181351171`；实际online在变动，是不同历史参数的EMA，不能把18.14%说成实测target距final程度。最终α=0.349984137，仍近初始0.35。

|假设|裁定|证据与限制|
|---|---|---|
|actor/critic符号、optimizer漏参或detach误实现造成原地|**反证（本轮检查范围）**|原样本loss/梯度复算、正确参数组与首步变化均一致；detach是合同要求。不能宣称所有实现问题已穷尽。|
|argmax一直原地意味着概率100%或模型未变|**反证**|49 train状态原地概率均值0.284→0.269→0.206，argmax仍49/49。|
|零耗时原地获得额外软价值|**支持**|3个确切r0/g1样本熵贡献0.455–0.781；有限链mask终止不消除先前软价值。|
|终局停滞惩罚已充分传回Q/actor|**反证**|7真实失败终局target−1而Q残差0.90–1.19；实际所选是移动，直接原地终局监督缺证。|
|当前最终argmax单由熵目标导致，或单纯学习不足|**证据不足**|初始化即偏原地；熵直接actor梯度抑制集中，间接target抬Q；不足拟合与目标激励风险共存，缺因果消融，不能单因裁定。|

CPU读取真实首更前后已验证梯度方向及响应，无必要重复GPU更新；是否跳过GPU由父统一裁定。本子建议先由决策者审议“按尝试时间累计熵、dt=0附加贡献为0”的最小目标修订方向，并同步定义Bellman/actor/temperature，尚未实施或证明有效。若维持当前目标直接单种子10k，必须先说明为何接受该风险，重新固定总LR预算和时限，不能复用200步已经衰减完的scheduler后盲目追加。

剩余：父对原件与上述推导统一复核；父全回放/validation排序结果合并后交当前决策者。不修改科学合同，不启动长训，不将诊断前向当收益验收。无本子运行进程、GPU任务或权重需接管。

父验收补记：`parent-verification.json`核10项子产物SHA、49行原首更replay身份、原始tensor重算target/loss及7失败终局隔离，rc0/verified；未把子自报当原件验收。子工程done，父节点仍review交决策者。
