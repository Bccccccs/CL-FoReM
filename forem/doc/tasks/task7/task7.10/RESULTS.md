# task7.10 — 结果

状态：**进行中（2026-10-20 Claude写上层离散SAC与偏置层规格v1，T1–T9已由用户确定，[SRC-0413](../../../SOURCES.md#src-0413)；只写文档，未实现）**。

## 运行记录

### 2026-10-20 上层离散SAC与偏置层规格草案v1（Claude）

- 作者：Claude（claude-opus-5-5，推理强度未知）；只写文档。记录见[日志](../../../agent_logs/task7/task7.10/20261020-claude-upper-spec.md)。
- 依据：框架与已定事项见[父TASK](../TASK.md)（§2.7、§4、U16、U27、U28）；离散SAC公式[SRC-0382](../../../SOURCES.md#src-0382)；SC²-WM打分结构[SRC-0412](../../../SOURCES.md#src-0412)、反馈层[SRC-0358](../../../SOURCES.md#src-0358)；CBL SAC配方[SRC-0406](../../../SOURCES.md#src-0406)；VCM [task7.8 RESULTS](../task7.8/RESULTS.md)；候选与槽位[task7.9 RESULTS](../task7.9/RESULTS.md)（R5：固定槽位、不用槽位编号嵌入）；推演原始量f_k字段[task7.13 RESULTS](../task7.13/RESULTS.md) D20；“忠于三个原项目”[SRC-0409](../../../SOURCES.md#src-0409)。
- 标记：**已定**＝用户已决定；**T#**＝原Claude建议，2026-10-20已由用户全部确定（[SRC-0413](../../../SOURCES.md#src-0413)）；数值均为工程选择。

#### U.1 一次决策的前向（对应父TASK §2.7第2–6步）

1. VCM给出状态s_t（task7.8，维数D_s，V4待定）。
2. 候选输入：K_max＝13个固定槽位（12扇区＋原地，R5），每槽有效掩码m_k（只标补齐空位，不标推演不可行，U24）。每个候选的原始输入x_k＝[几何c_k；推演原始量f_k]：几何为(Δx, Δy, sinΔθ, cosΔθ)、距离、原地标志，不同步另加Δs_k；f_k为D20字段表。
3. **候选编码（T1）**：x_k经固定常数归一化（T7）后，`u_k = LN(W_g·几何) + W_f·f_k`（对应SC²-WM的位置嵌入加候选特征，[SRC-0412](../../../SOURCES.md#src-0412)①）；把`[状态令牌W_s·s_t；u_1…u_K]`送入2层Transformer编码器（自注意力，padding掩码），输出状态令牌h_ctx与候选上下文特征e_k（对应SC²-WM的CrossmodalEncoder与NAV令牌；本项目没有指令，用状态令牌代替）。候选原始投影u_k保留，作为f_p的“原始特征”输入（对应V_raw）。
4. **第一评分（头A）**：Actor_A给logit_A(k)＝MLP_A(e_k.detach())；Critic_A给Q_A,i(k)＝MLP_Qi([s_t, e_k])，i＝1, 2。
5. **世界模型与偏置层（阶段3起）**：f_p输入[h_ctx, e_k, u_k]，输出h_k（task7.11）；阶段2/3中VCM与候选编码器参数冻结，三项输入不需要梯度；测试期适应时L_fp经这三项回传到候选编码器（F7(b)），故不对输入做永久detach（2026-10-20按[Codex冻结前复核](../../../agent_logs/task7/20261020-codex-spec-freeze-review.md)#7更正原“h_ctx.detach()”）；h_k先detach；`g_k=sigmoid(W_g'[e_k; h_k])`、`δ_k=W_d[h_k; e_k]`、`e_k'=e_k+g_k⊙δ_k`，W_g'、W_d零初始化（已定，U16，[SRC-0358](../../../SOURCES.md#src-0358)）。
6. **增强评分（头B，T2）**：Actor_B给logit_B(k)＝MLP_B(e_k')；Critic_B给Q_B,i(k)＝MLP_QBi([s_t, e_k'])。
7. 选点：π(k|x)＝softmax(logit)，只在m_k＝1的槽位上归一化；训练时采样，评估时取最大（父TASK §2.7）。阶段1用头A，阶段3及之后用头B。

#### U.2 两套头（T2，忠于SC²-WM两头结构）

- SC²-WM有独立的第一评分头与增强评分头，最终动作取增强评分（[SRC-0412](../../../SOURCES.md#src-0412)②）。本项目对应：阶段1训练头A（Actor_A与Critic_A）；阶段3新建头B，**用头A的权重复制初始化**，接入时e_k'＝e_k（零初始化），因此头B输出与头A完全相同，满足“接入时输出与阶段1一致”（父TASK §2.7第5步）。
- 阶段3训练的参数＝ψ（W_g'、W_d）＋头B（Actor_B、Critic_B）；VCM、候选编码器、头A冻结。这与用户已同意的“冻结基线、只训练偏置层与输出头”（建议c）一致：头B就是这里的“输出头”。
- 好处：头A在同一网络里保留阶段1的选择，可直接统计“偏置层改变选择的决策比例”（task7.4世界模型指标），不必另开一个G2网络取同一状态。
- G2（基线续训）：同一两头结构，头B也从头A复制，但输入e_k（不接ψ与f_p），以同预算训练头B。G3（容量对照）：同G4，但h_k来自随机初始化后冻结的f_p（已定，[SRC-0392](../../../SOURCES.md#src-0392)）。

#### U.3 损失（离散SAC，[SRC-0382](../../../SOURCES.md#src-0382)；掩码与折扣为本项目合同）

对当前训练的那套头（阶段1为A，阶段3为B），记有效候选集合𝒦(x)：
- Critic：`L_Q = E[ ½ Σ_i (Q_i(x, k*) − y)² ]`，`y = R + (1 − terminated)·γ^(Δt/τ)·V̄(x')`，`V̄(x') = Σ_{k∈𝒦(x')} π(k|x')·[min_i Q̄_i(x', k) − α·log π(k|x')]`；Q̄为软更新的目标网络；截断不切断自举（task7.4）；y不回传梯度。下一状态的候选集与f_k'从经验池取（I4，task7.4修订节第2条）。
- Actor：`L_π = E_x Σ_{k∈𝒦(x)} π(k|x)·[α·log π(k|x) − min_i Q_i(x, k)]`。
- 温度（T5、T6，2026-10-20按[Codex冻结前复核](../../../agent_logs/task7/20261020-codex-spec-freeze-review.md)#9改为CBL代码的形式）：优化变量为log_alpha，`L_α = −log_alpha · E_x[ Σ_{k∈𝒦(x)} π(k|x)·(log π(k|x) + H̄(x)) ].detach()`（对应`forem/scripts/scwm_sac.py:232`的`-(log_alpha*(log_pi+target_entropy).detach()).mean()`，连续动作的log_pi换成离散分布上的期望）；alpha＝0.35·exp(log_alpha)，≤0.05后固定为0.05并停止调温；alpha优化器Adam、lr 1e−6；H̄(x)＝0.98·log K(x)，K(x)为有效候选数。
- R、Δt、terminated按task7.4与父TASK §2.7；γ＝0.99、τ＝0.1 s（N3，[SRC-0417](../../../SOURCES.md#src-0417)）。

#### U.4 梯度路由（T3）

- VCM与候选编码器（含候选间Transformer）只由Critic损失训练，Actor梯度在s_t与e_k处截断（沿已定的V2“VCM只由Critic训练”，依据DrQ/SAC-AE，[SRC-0383](../../../SOURCES.md#src-0383)；SC²-WM第一评分也作用于detach后的特征，[SRC-0412](../../../SOURCES.md#src-0412)②）。
- f_p只由自身预测损失训练，输出detach（已定，U4）；ψ与头B由RL损失训练。

**各阶段参数与损失路由（2026-10-20按[Codex冻结前复核](../../../agent_logs/task7/20261020-codex-spec-freeze-review.md)#7、#9写明；只整合已定内容）**

|阶段|训练的参数|损失|冻结|
|---|---|---|---|
|L|下层SAC（task7.13）|下层SAC损失|上层全部|
|1|VCM、候选编码器、头A的Actor_A与Critic_A（Q1、Q2）、log_alpha|Critic损失→VCM、候选编码器、Critic_A；Actor损失→Actor_A（在s_t、e_k处截断）；温度损失→log_alpha|下层|
|2|f_p|L_fp|下层、VCM、候选编码器、头A|
|3|ψ（W_g'、W_d及其偏置）、头B的Actor_B与Critic_B（整个MLP，各层都训练）、log_alpha；f_p继续|RL损失→ψ、头B；L_fp→f_p|下层、VCM、候选编码器、头A|
|G2（续训）|头B（输入e_k，无ψ）、log_alpha|RL损失|同阶段3，另无ψ与f_p|
|测试期适应（G6）|f_p、候选编码器|L_fp|下层、VCM、头A、头B、ψ|

- “输出头”＝头B的整个Actor_B与Critic_B MLP（由头A复制初始化），不是只训最后一层；G2与G4解冻范围相同（G4另有ψ）。
- 目标网络（沿CBL：目标网络是整个Critic的软更新副本，[SRC-0406](../../../SOURCES.md#src-0406)）：Q̄包括Critic路径上所有当前可训练的模块的软更新副本（阶段1：VCM、候选编码器、Critic_A；阶段3：ψ、Critic_B；冻结模块直接共用），τ_soft＝0.001，每次更新后软更新；进入某阶段时目标副本由当时的在线参数复制初始化。
- 偏置层的两个Linear权重与偏置都零初始化（W_d与其偏置为0才使δ＝0；W_g'为0只使门值为0.5），接入时检查头B输出与头A一致。
- 跨阶段：阶段3的log_alpha由阶段1末值继续，优化器重新建立；阶段3使用新经验池D3。
- 开始更新的条件（对应CBL“经验池长度>batch”）：经验池中可取出的完整长度8片段数≥32，且随机预热的1000次决策已完成。

#### U.5 归一化（T7）

候选输入用**固定常数**归一化（距离除以3.2 m、Δs除以候选可达半径、时间除以T_seg、比例原样），不用运行统计。理由：冻结后若归一化统计还在变，头A/头B的输入会漂移，破坏“接入时输出一致”。

#### U.6 训练超参（T6，沿CBL task5.5配方，[SRC-0406](../../../SOURCES.md#src-0406)，单位改为“决策”）

Adam，lr 1e−4按更新次数指数衰减到1e−6（衰减长度＝该阶段总更新数）；目标网络软更新τ_soft＝0.001；每次决策更新1次；随机预热：前1000次决策在有效候选上均匀随机选；经验池容量10万次决策；温度沿CBL capped规则（alpha＝0.35·exp(log_alpha)，≤0.05后固定，[SRC-0406](../../../SOURCES.md#src-0406)）；梯度范数裁剪10。批采样按回合序列（I3）：每批32条长度8的决策片段，前4步只用于恢复VCM记忆与GRU状态（预热段不回传梯度，[SRC-0384](../../../SOURCES.md#src-0384)），后4步算损失（片段与预热长度已定，T9、N11）。

#### U.7 网络宽度（T4）

候选编码与Transformer宽度128、4头、前馈256；头A/头B各为Linear(128)–ReLU–LayerNorm–Linear(1)（与SC²-WM `NextActionPrediction`同形，去掉Dropout以免SAC目标带噪，[SRC-0412](../../../SOURCES.md#src-0412)②）；Critic的MLP为[s_t, e_k]→[256, 256]→1。SC²-WM隐藏维768面向预训练视觉特征，本项目输入维数小得多，故取128（工程选择）。

#### U.8 评估与诊断

- 评估：确定性取最大logit（阶段1用头A，阶段3用头B）。
- 诊断（已在task7.4指标中，不新增）：**最终头B相对冻结头A的选择变化比例**＝头B与头A的argmax不同的决策占比；它同时包含ψ与头B续训两部分影响，不能单独归因于偏置层（2026-10-20按[Codex冻结前复核](../../../agent_logs/task7/20261020-codex-spec-freeze-review.md)#15改名；ψ的作用仍由G4对G2比较）；各组无可行候选比例。

#### T1–T9（2026-10-20用户按建议确定，[SRC-0413](../../../SOURCES.md#src-0413)）

|编号|内容|Claude建议|忠于原项目的说明|
|---|---|---|---|
|T1|候选编码|几何嵌入（Linear＋LN）＋f_k投影，再经2层Transformer（状态令牌＋候选，padding掩码）|对应SC²-WM位置嵌入＋CrossmodalEncoder；无指令，用状态令牌代替NAV|
|T2|两套头|头A（阶段1）与头B（阶段3，由头A复制初始化），最终选点用头B|对应SC²-WM第一评分头/增强评分头|
|T3|梯度路由|VCM与候选编码器只由Critic训练|沿已定V2；SC²-WM第一评分作用于detach特征|
|T4|宽度|128维、2层、4头|SC²-WM为768维（预训练视觉特征），工程缩小|
|T5|目标熵|H̄(x)＝0.98·log K(x)，K(x)为该状态的有效候选数|0.98为离散SAC原文的系数（[SRC-0382](../../../SOURCES.md#src-0382)），按每个状态的有效候选数计|
|T6|训练超参|沿CBL task5.5（lr衰减、τ_soft、温度capped规则、预热1000、每决策1次更新、经验池10万）|沿CBL|
|T7|归一化|固定常数，不用运行统计|保证冻结等价|
|T8|f_p输入|[h_ctx, e_k, u_k]，交task7.11|对应SC²-WM [NAV, V_mixed, V_raw]|
|T9|序列批|32条×8步，前4步预热|V4的建议值|

γ、τ与各阶段预算已由N3、N12确定（[SRC-0417](../../../SOURCES.md#src-0417)）。

## 交接

- 当前负责人：Claude（规格v1）；T1–T9已定（[SRC-0413](../../../SOURCES.md#src-0413)）。
- 下一步：已回写父TASK（U2、U27、U28）与task7.4修订节第11条；f_p输入（T8）交task7.11起草。未实现、未训练。
