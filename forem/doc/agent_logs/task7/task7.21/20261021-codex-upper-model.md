# TASK7.21-UPPER-MODEL-20261021 开工核查与阻塞交接

- 负责人：Codex；实际模型/推理强度：未知（会话未提供可核实的具体标识）。推荐：GPT6.1sol / medium；复核推荐Claude Sonnet5.5 / medium，原因是跨模块梯度路由核查。
- 开始：2026-10-21T14:22:48+08:00；记录：2026-10-21T14:23:02+08:00。派发文本称14:45，与宿主当前时间不一致，保留实测时间，不推断原因。
- 授权：[SRC-0439](../../../SOURCES.md#src-0439)，以[task7.21 TASK](../../../tasks/task7/task7.21/TASK.md)为边界。仅实现指定task7_upper文件和验证，不训练、不改task7_sim、不启停容器、不提交git、不停止其他进程。
- Git分支main；已有大量其他任务改动，未覆盖。forem-dev已运行；未进入容器执行计算。新包task7_upper不存在。
- 已读取根/forem AGENTS、doc README、PROGRESS、ENV、本任务三文档；规格文档批量读取的工具输出发生截断，**不宣称已完整核查规格**。恢复后必须重新精确读取所列章节，再确认实现清单。

## 计划结构清单（仅TASK摘录，尚未实现/尚未完成原规格核查）

1. VCM：128×128×3，D_v=D_s=128；CNN三层stride2、16/32/32；记忆L=4、时间偏置初值0.1、几何/步差零初始化、门控偏置2.0、GRUCell且递推未修正状态。出处：TASK规格来源task7.8 B.1–B.4、V4/N11。
2. CandidateEncoder：几何与f_k投影，2层Transformer、宽128、4头、FF256，padding mask，无槽位编号嵌入，固定归一化。出处：TASK规格来源task7.10 U.1/U.2/U.5/U.7、T1–T9、task7.13 D20。
3. Heads：Actor Linear128–ReLU–LayerNorm–Linear1；双Q [s,e]→256→256→1；B复制A。出处：TASK范围第3项及task7.10。
4. BiasLayer：g=sigmoid(Wg[e;h])，delta=Wd[h;e]，e'=e+g*delta；两个Linear权重与偏置零初始化，h先detach。出处：TASK范围第4项、父TASK §2.7步骤5/U16。
5. WorldModel：拼接[h_ctx,e,u]，核心384→256→128，预测头128→128→128；G3随机冻结与外部给定逐维仿射系数。出处：TASK范围第5项、task7.11 W.1/W.2/W.5。
6. UpperModel：阶段1/2/3/G2/G3/适应参数集合和梯度路由；适应L_fp可回传候选编码器。出处：TASK范围第6项、task7.10 U.4、task7.11 F7(b)。

以上为获授权任务的索引，不是新增结构选择；恢复实施前须登记已核查原规格的来源条目。

## 阻塞证据与待决定

GPU0存在/usr/lib/xorg/Xorg，PID2212，类型G，4MiB；GPU总占用14MiB，利用率0%。两次nvidia-smi均显示该进程。宿主ps显示该进程自2026-07-23运行。证据与限制见[SRC-0500](../../../SOURCES.md#src-0500)。没有CUDA计算进程并不等于没有其他GPU进程。

本次用户硬约束原文：“开工与每次运行前用nvidia-smi核实GPU0无其他进程，被占用则停下报告。”因此在开工检查处停止；未自行豁免Xorg，也未结束该进程。此停止由用户派发要求引起，非技能或自动审批拒绝。

待决定：是否明确允许GPU0常驻Xorg显示进程作为例外。若仍要求无任何其他进程，则依赖GPU0实际满足该条件后重派；本Agent无权停止Xorg。

## 交接

- 状态blocked；实现/六组单测/参数量/前向计时/CPU64-GPU32容差均尚未执行，不标review或done。
- 改动仅本日志、本任务RESULTS、PROGRESS本任务行、SOURCES预留SRC-0500，以及本任务preflight日志；未改源码、配置、TASK、PROCEDURE或其他任务文件。
- 没有本任务运行进程；容器计算0秒、GPU测试0次。
- 下一步：Claude接收上述GPU阻塞事实，取得明确例外或核实GPU0已无其他进程后恢复；恢复时重读共享文档与完整规格、再次核实GPU，再实施/测试并交review。


## 恢复 t7.21-r2-20261021

- 用户明确更正GPU门禁：Xorg为图形服务不算占用，只检查compute进程。GPU0 `nvidia-smi -i 0 --query-compute-apps=pid,process_name,used_memory --format=csv`退出0、仅表头，恢复active。历史blocked保持为当时记录，不继续沿用。
- 实际模型/强度：进程2535684命令为`-m gpt-6.1-sol -c model_reasoning_effort="medium"`；与本次派发相符。推荐仍为Codex GPT6.1sol/medium、Claude Sonnet5.5/medium（跨模块梯度核查）。
- main分支；task7.18/19/20并发进程存在，遵守文件隔离；forem-dev已运行、挂载forem到/root/mm_husky_ws，镜像sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430。无启停容器或其他进程。
- 已重新完整读取task7.8/10/11 RESULTS、task7.13 D20、父TASK §2.7与U16。上方六项规格清单原文核对完成：VCM CNN三层16/32/32 stride2、128维、L4/λ0.1/门偏置2；候选几何6维、f_k19维；Transformer2层宽128/4头/FF256；Actor128→128→1、双Q256→256→256→1；ψ两个Linear256→128全零；f_p384→256→128与128→128→128(GELU)。出处统一登记[SRC-0501](../../../SOURCES.md#src-0501)。
- 使用test-driven-development技能进行合同测试；作为明确派发的实施任务，不再发起设计/文档复核轮次。

### 待决定（只停对应部分）

1. task7.8 B.1/V4给出CNN通道和stride，但未给kernel/padding/激活、图像向量融合结构、向量MLP层宽与输入最终维数。不能自行选kernel3/flatten/fusion等。f_enc具体结构停止，接口接受显式外部模块。
2. task7.8 B.2没有检索注意力头数/QKV投影结构、几何嵌入最终输入定义（2D/3D）、步差嵌入大小/超范围策略、gate输入结构，B.3没有动作特征和结果r编码维数。检索/门具体网络停止；只做可注入模块的FIFO/GRU编排，GRU额外输入维数须调用方显式给出，测试夹具不作为项目选择。
3. task7.10 U.1/U.7明确Transformer层数/头数/FF宽，但未明确dropout/激活/norm顺序；这些将作为必填构造参数，不提供隐含默认值，测试夹具取值不成为项目网络配置。
4. U.5/D20指定Δs除以候选可达半径，但本任务未给半径输入；归一化接口要求调用方提供正半径，不自行取值。时间t_c/T_seg；T_seg字段自身归一化为1；角度/比例保留原字段值，距离除3.2。固定常数不产生运行统计。

授权剩余：实现明确模块与组装接口，六类合同测试能执行部分；实际f_enc/检索网络及完整VCM参数量、完整端到端前向计时不能作为已通过，交review时明确这些依赖。


### 中间验证与接口收敛

首轮CPU 12 passed，扩展GPU 20 passed（4.09s）；GPU allocator峰值28,071,936 B、reserved33,554,432 B。首轮计时/CPU64对照亦退出0，但后续接口明确化后会重跑，最终报告以最终run为准。

额外待决定：U.7 Critic只给MLP宽度，未明确激活；`Heads`和`UpperModel`要求调用方显式提供`critic_activation`，测试ReLU只是夹具值。VCM门接口改为gate(v,context)，其拼接策略完全由注入模块定义，不在生产编排里补结构。CandidateEncoder的LN epsilon同样显式给出。没有新项目配置文件。`UpperModel`需调用者在阶段1权重载入后显式`copy_head_b_from_a()`；set_stage不覆盖已训练B。log_alpha、目标副本、loss/optimizer和触发逻辑属task7.22，本包不实现。


## 最终验证与交接（2026-10-21T14:40:44+08:00）

依据[SRC-0502](../../../SOURCES.md#src-0502)，CPU/GPU最终各24 passed，三条最终命令退出0；数值对照最大绝对差1.58166632369e-06，atol1e-5/rtol1e-4，零初始化另严格0。明确模块总参数1,241,094；GPU快照738MiB、allocator峰值53869056B。具体命令/日志/计时表/每组限制写入[RESULTS本run](../../../tasks/task7/task7.21/RESULTS.md)。

真实离散Actor公式补测发现需要显式区分Actor专用截断Q值和Critic输出；先写4项失败测试（actor-red.log，退出1），再加入actor_q1/2接口，最终全部通过。无loss/训练循环。一次合成SGD只验证随机f_p不更新。

### 待决定的可选理解（仅列解释，不作项目选择）

- task7.8 B.1/V4：kernel/padding可能采用保持尺寸的卷积或valid卷积，输出线性输入维数随之变化；图像与向量可能concat后线性或分支MLP后融合；未给精确结构/向量字段最终维数，本轮未实施具体f_enc。
- task7.8 B.2：检索可为单头或多头、带/不带QKV投影；相对几何位移可能取平面2维或空间3维；步差可为有限查表或其他显式编码，需给范围/超界处理。gate可拼接当前v与检索c，也可用其他原实现输入结构；本轮不选择，注入接口仅收v、c。
- task7.8 B.3：上一动作特征可能是所选候选几何或其编码，r可能是标量或结果one-hot；GRU input_size依赖其决定，接口只要求显式action_result_dim。
- task7.10 U.1/U.7：Transformer dropout0或非零、激活ReLU或GELU、pre/post norm等需定；Critic MLP激活未定。构造参数全部显式必填，不提供项目默认，夹具ReLU/零dropout不能默认为授权配置。
- U.5：可达半径需要由候选生成合同给入，接口不推断；T_seg来自D20字段8。归一化具体字段变换已在[SRC-0501](../../../SOURCES.md#src-0501)列出供复核。

### 文件、资源与下一步

实际仅修改task7_upper新包、本日志、本任务RESULTS、PROGRESS自己行、SOURCES0501/0502与run日志/结果。source_manifest.json存日志目录（容器创建的results子目录root属主导致宿主写manifest被拒，未改权限；改存授权日志目录后成功），没有源码运行失败或权限升级。

状态review（部分交付）；并非done，不满足7.22的done依赖。请Claude核查明确模块与上述待决定项；完整VCM及真实递推32×8计时未实施。没有本任务后台计算，无需停止/恢复。最终两个验证组三命令精确总wall保留JSON；全部11次计算各限120s，保守上界1320s＜60分钟。无训练、无容器启停、无git提交、无参考仓库修改。复核推荐Claude Sonnet5.5/medium、后续执行推荐Codex GPT6.1sol/medium（跨模块梯度因果核查）；与实际运行配置区分。


## r3恢复 t7.21-r3-20261021

- 开始核查2026-10-21T16:54+08:00；实际进程2695455：gpt-6.1-sol / medium。Codex推荐GPT6.1sol / medium、Claude复核Sonnet5.5 / medium；理由为跨模块梯度核查。
- 已重读共同入口、环境、本任务三文档、task7.8 B/4、7.10 U/T、7.11 W/F、7.13 D20与父TASK §2.7/U16；main存在其他会话改动，task7.18与7.20并行，本包无其他修改进程。forem-dev运行中，镜像与r2相同。GPU compute查询仅表头，Xorg不计。
- 授权与本轮确定项：[SRC-0903](../../../SOURCES.md#src-0903)，不训练、不启停容器、不改其他包、不提交git。原待决定项均按本轮决定实现；旧r2停止状态仅为历史。
- 结构逐项：f_enc Conv3×3 valid stride2 3→16→32→32/ReLU，128→63→31→15，展平7200与显式向量输入拼接→Linear128；检索单头QKV128、scale=exp(logit_scale)，初log10，−|λ|δ初0.1，后LN及4×GELU FFN；几何(Δx,Δy,sinΔθ,cosΔθ,距离) Linear5→128+LN（Linear全零，沿原码LN标准初始化），步Embedding5全零并clamp0..4；gate Linear256→128权重std1e−4/偏置2；GRU额外输入4维上一目标当前坐标表示、不同步加Δs，及19维f_k；候选Transformer GELU/postnorm/eps1e−12/dropout0、Critic ReLU、Δs÷3.2。出处SRC-0903、task7.8 B、task7.10 U、task7.13 D20。
- 参数量按显式vector_dim和同步/不同步分别记录，不擅定末端路线点数或姿态表示；本包接收已拼接向量与已转换到当前B_t的上一候选几何，环境适配归task7.22。测试固定向量维数会明确为合成输入夹具。
- 下一步（尚未执行）：补默认模块与完整递推验收，32×8真正按时间推进而非展平状态；预算延续r2，仅有界计算。

### r3实现与中间核查（2026-10-21T17:02+08:00）

- 真实VCM、默认配置与UpperModel.forward_step已实现；[SRC-0503](../../../SOURCES.md#src-0503)记录规格/原码映射。CPU首轮34 passed；增加不同步全阶段梯度覆盖后GPU首轮39 passed/1 failed，失败为全模型重算严格torch.equal（零ψ与同特征头A/B严格相等测试仍通过）。
- `diagnose.log`表明阶段切换重算candidate e差约8.34e−7、logits约4.77e−7，重复同阶段为0、给同e两头为严格相同；不把其断言失败伪装成结构通过。整网切换按逐元素atol=rtol=1e−6记录；ψ本身与同e两头继续0容差。
- 数值初轮失败：默认Transformer native fastpath下CPU64/GPU32最大e差2.906719968494e−4；关TF32无改善。`numeric-diagnose.log`显示关闭mha fastpath后最大context差1.835819146034e−6、hidden1.085964682346e−7、f_enc9.214128671164e−8。局部实测只定位到native fastpath相关，不声称已审计其底层数值近似原因。
- 基准将同时记录unfused对照（atol1e−5/rtol1e−4）与默认native路径（工程记录容差atol5e−4/rtol1e−4，来自上述差异，不是任务成功率验收阈值）。产品不关闭fastpath，计时为native默认路径；TF32在此基准显式关闭，未改任何训练代码/配置。
- 有界基准运行中：容器forem-dev，宿主docker exec PID2710830、容器timeout PID2710865/python PID2710871，timeout120s；输出benchmark-final.log（命令结束后写出）及results/task7/t7.21-r3-20261021/benchmark.json。仅本任务进程，自动timeout退出，不停止别的任务。尚未取得最终结果，不标review。

### r3最终交接（2026-10-21T17:06:39+08:00）

- **review，交Claude复核，不标done。** 用户SRC-0903确定的全部网络已作为默认实现，无剩余结构待决定；实际文件为task7_upper的vcm/candidate_encoder/heads/model/__init__、tests/test_contracts/test_full_vcm/benchmark；bias/world_model沿用r2。其余仅本RESULTS/日志/PROGRESS自己行/SOURCES0503–0504与本run日志产物。未改其他任务、未训练、未启停容器、未停止其他进程、未提交git。
- 最终CPU32/GPU32各40 passed；六类验收含真实同步/不同步六阶段梯度、前4步预热/后4步递推、真实CNN/检索/门/GRU、FIFO/reset/前缀逐元素一致、掩码、随机f_p/仿射/目标detach。命令退出0，证据与每类具体结论见[RESULTS r3](../../../tasks/task7/task7.21/RESULTS.md)。
- 真实32×8 K13同步GPU32完整前向中位56.02484ms（CUDA55.99333）；不同步56.16952ms（CUDA56.13400）；参数总量同步D80=2,511,624，异步D81=2,512,136，D80/81为合成输入并非新增项目规格。f_enc每加一向量维加128参数；同D异步GRU多384。数据路径参数/输入均cuda:0。
- 数值限制明确：默认native快速路径CPU64/GPU32最大2.90672e−4（工程记录atol5e−4/rtol1e−4）；非融合参考最大1.83582e−6（atol1e−5/rtol1e−4）。完整阶段切换GPU32 logits最大4.17233e−7、双Q≤7.45058e−8（逐元素atol=rtol1e−6）；ψ恒等与同e头A/B仍严格0。生产不全局改fastpath/TF32；基准TF32关闭，不把数值容差写为任务性能通过阈值。
- 本轮10条容器计算命令wall合计109.994s，最长65.401s、每条timeout120s；继承r2保守上界1320s仍<60min。精确argv/退出码/时间见commands.json。原失败日志全部保留，不只报告最终通过。
- GPU0基准快照1012MiB，allocator峰值280,296,960B/reserved350,224,384B；最终门禁仅compute表头，无本任务运行进程，无停止/恢复操作。
- 原始证据：`forem/logs/task7/t7.21-r3-20261021/`（含source_manifest、commands、final-gate），`forem/results/task7/t7.21-r3-20261021/benchmark.json`；SOURCE0503为映射、0504为实测。benchmark源码哈希已与当前包逐项核对相同。
- 下一步Claude Sonnet5.5/medium复核默认参数、完整梯度/递推与数值边界，必要时复跑最终两条测试；通过后再由其标done。task7.22据实际环境字段对接vector_dim/r_t→f_k v1/grid量化解码、加载阶段1后复制B、loss/optimizer/target副本，不把本轮合成计时外推端到端训练。后续Codex仍推荐GPT6.1sol/medium，原因同跨模块合同核查。


## r4恢复 t7.21-r4-20261021

- 2026-10-21T20:16+08:00开工；实际派发PID2912552参数为 `gpt-6.1-sol / medium`，推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium（变体输入与梯度合同核查）。
- 授权只修Claude r3复核第1项：候选几何同步6维/不同步7维，末维目标Δs_k÷3.2 m（SRC-0903第8项、task7.10 U.1）；T_seg自除与native路径明确容差保持。
- 已读共同入口、三文档、复核、ENV、代码；main有其他任务未提交改动，保留。task7.18.1诊断/task7.20并行，仅改task7_upper/{candidate_encoder.py,model.py,tests/}及本任务日志/RESULTS/PROGRESS自己行/SOURCES预留0505起。没有训练授权，不启动训练。
- forem-dev运行且挂载forem；compute初查为空，Xorg不计。测试每次timeout120s，CPU先RED后全目录，GPU运行前重查0，有compute则用2；不占1/3。预算继承r2保守1320s+r3实际109.994s，不重跑基准。
- 测试拟捕获：固定6维漏目标进度、错用候选半径缩放、7维padding污染/槽位依赖、阶段切换零初始化失效；异步全六阶段梯度既有测试改用真实7维。以上测试尚未执行。

### r4完成交接（2026-10-21T20:18+08:00，review）

- RED已复现缺7维（1 failed/1 passed，退出1），随后最小修复：CandidateEncoder按6/7维构造、异步末维目标Δs_k÷3.2m，UpperModel传变体宽度，forward拒绝不匹配宽度；只修改已登记包文件和测试。全CPU/GPU0各44 passed，退出0；异步全六阶段梯度改用7维，掩码/零初始化两变体覆盖。T_seg与既有数值容差未改。
- 异步阶段切换logits差4.76837e−7，双Q≤7.45058e−8，atol=rtol=1e−6通过；同e两头与ψ恒等严格相等。GPU allocated/reserved峰值51,413,504/65,011,712B，运行前后compute为空，未占GPU1/2/3，无本任务计算进程。
- 证据`forem/logs/task7/t7.21-r4-20261021/`：commands.jsonl/red.log/cpu-final.log/gpu-final.log/gpu-preflight.txt/gpu-final-gate.txt/source_manifest.json/summary.json；[SRC-0505](../../../SOURCES.md#src-0505)登记，RESULTS新run已追加。三条计算wall13.177s，继承预算累计上界1443.171s<60min；不重跑基准。benchmark仅修异步夹具与输出目录，AST检查通过、尚未执行。参数量加128为推导，不冒充实测。
- 全局git diff --check发现PROGRESS其他任务行62旧尾空格，保留不改。共享PROGRESS只用UTF-8 bytes按本行替换，未覆盖其他行；SOURCES仅新增0505。未训练、未启停容器或停止其他任务、未提交git、未修改其他包。
- 下一步Claude Sonnet5.5/medium核查r4和源哈希后决定done。task7.22必须给异步7维目标进度，不用实际推进量替代；旧异步6维投影检查点形状不兼容。整网切换容差1e−6，其他限制沿r3。负责人Codex，授权边界与目标见本节恢复记录；没有恢复/停止操作。状态review。
