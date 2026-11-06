# task7.21 — 上层网络模块：VCM、候选编码、头A/B、偏置层与f_p

状态：**done（2026-10-21 Claude复核r4通过，见[RESULTS](RESULTS.md)末节）。原：draft（2026-10-21建立；实施已授权，[SRC-0439](../../../SOURCES.md#src-0439)；可立即派发）**。父任务：[task7](../TASK.md)。用户要求起草见[SRC-0438](../../../SOURCES.md#src-0438)。

## 目标

按已定规格实现上层的全部网络模块与前向/梯度路由，并用单元测试证明关键结构性质（零初始化等价、各阶段可训练参数与梯度截断、掩码不变性）。不涉及环境、经验池与训练循环（task7.20、7.22）。

## 规格来源

- VCM：[task7.8 RESULTS](../task7.8/RESULTS.md) B.1–B.4（f_enc：128×128×3栅格＋向量输入；L＝4注意力记忆、时间偏置λ初值0.1、相对几何与步差嵌入零初始化、门控偏置初值2.0；GRUCell，递推用未修正状态）；V4/N11尺寸（CNN 3层步长2、通道16/32/32＋线性层，D_v＝D_s＝128）。
- 候选编码、头A/B、偏置层：[task7.10 RESULTS](../task7.10/RESULTS.md) U.1、U.2、U.4（各阶段参数与损失路由表）、U.5、U.7、T1–T9；候选几何输入与f_k v1字段见[task7.13 RESULTS](../task7.13/RESULTS.md) D20。
- f_p：[task7.11 RESULTS](../task7.11/RESULTS.md) W.1（核心MLP 384→256→128、预测头128→128→D_v）、W.2（目标为f_enc编码并detach、1−cos）、W.5（G3随机冻结f_p与逐维仿射对齐）、F7(b)（测试期适应时L_fp可经e_k、h_ctx回传候选编码器）。
- 偏置层：父[TASK](../TASK.md) §2.7第5步与U16（两个Linear零初始化，h_k先detach，不加显式差值）。

## 范围

- 包含：
  1. `VCM`：f_enc、记忆库（按环境维护、回合边界重置、可从序列前缀无梯度重建）、检索与门控、GRU递推。
  2. `CandidateEncoder`：几何嵌入＋f_k投影→u_k；状态令牌＋候选的2层Transformer（宽128、4头、前馈256、padding掩码）→h_ctx、e_k；不使用槽位编号嵌入（R5）；固定常数归一化（T7）。
  3. `Heads`：Actor_A/B（Linear(128)–ReLU–LayerNorm–Linear(1)）、Critic_A/B双Q（[s_t, e]→256→256→1）；头B由头A复制初始化的接口。
  4. `BiasLayer`ψ：`g=sigmoid(W_g'[e;h])`、`δ=W_d[h;e]`、`e'=e+g⊙δ`，两个Linear的权重与偏置零初始化。
  5. `WorldModel`f_p：输入[h_ctx, e_k, u_k]，输出h_k与V̂_k；G3用的随机冻结版本及逐维仿射对齐接口（系数由task7.22计算后写入并固定）。
  6. `UpperModel`组装：按阶段（1、2、3、G2、G3、适应）返回可训练参数集合，前向中按U.4路由截断梯度。
- 不包含：经验池、损失与优化器、训练循环、环境；测试期适应的触发逻辑（G6，C类项未定）。

## 文件归属（只改这些）

新包`forem/src/task7_upper/`：`__init__.py`、`vcm.py`、`candidate_encoder.py`、`heads.py`、`bias.py`、`world_model.py`、`model.py`，以及`forem/src/task7_upper/tests/`下对应测试；必要时`forem/config/task7/upper_model.json`。不改`task7_sim`。

## 交付与验收

- 单元测试：
  1. **零初始化等价**：头B由头A复制、ψ零初始化时，头B的logits与双Q对任意输入与头A逐元素相等（记录float32容差）；只W_g'为0而W_d非0时不等价（反例测试）。
  2. **梯度路由**：按U.4表逐阶段检查——阶段1 Actor损失对VCM与候选编码器梯度为0、Critic损失非0；阶段2只有f_p有梯度；阶段3只有ψ与头B有RL梯度，f_p只从L_fp得梯度，h_k进入ψ前detach；适应期L_fp可回传候选编码器，而头A/B、ψ、VCM无梯度。
  3. **掩码**：补齐槽位对有效候选的输出无影响；候选槽位重排后输出相应重排（无槽位编号嵌入）。
  4. **VCM**：记忆长度4先进先出；前缀无梯度重建与逐步前向结果一致；回合边界重置。
  5. **f_p**：输出维数D_v＝128；随机冻结版本参数不更新；仿射对齐按给定系数逐维变换。
  6. 参数量与各模块前向计时（批32×8、K＝13），只记录。
- 运行：forem-dev内，单条命令≤10分钟、累计容器计算≤60分钟；只做小批量测试，GPU在派发提示中指定，显存≤4 GB以免影响并行训练；不训练、不启停容器、不提交git。
- SOURCES预留编号：SRC-0500–0509。

## r2待决定的处理（2026-10-21，[SRC-0903](../../../SOURCES.md#src-0903)）

f_enc、记忆检索、几何/步差编码、门控、GRU额外输入、Transformer选项（GELU、后归一化、eps 1e−12、dropout 0）、Critic激活（ReLU）、Δs归一化（÷3.2 m）均已由用户确定，详见SRC-0903；下一轮据此补完整VCM与32×8递推计时及全模型梯度验收。

## 模型推荐

|Agent|模型|推理强度|理由|
|---|---|---|---|
|Codex|GPT6.1sol|medium|多模块结构与逐阶段梯度路由须逐条对照规格，零初始化等价易出细节错误|
|Claude|Sonnet5.5|medium|同上（复核）|

推荐不等于实际配置；执行方在日志中记录实际模型与强度，无法核实写“未知”。

文档作者：Claude（claude-opus-5-5，推理强度未知），2026-10-21。
