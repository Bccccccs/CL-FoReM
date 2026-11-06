# task9.13 冻结训练实现栈差异（执行版r2）

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high：框架更新/恢复因果核查。实际执行gpt-6.1-sol/high。来源：[SRC-T9-RLLIB-EXEC-20261106](../../../SOURCES.md#src-t9-rllib-exec-20261106)、[用户范围](../../../SOURCES.md#src-t9-explore-20261106)。本表是实现栈比较，不能称单一SAC参数因果或算法优劣。

|项|C/B1同期控制|完整RLlib SAC R|处理/限制|
|---|---|---|---|
|框架|现役冻结task8_lower.sac.LowerSAC只读导入|Ray2.40.0原生SAC Algorithm，旧API栈SACTorchPolicy/ModelV2|Python3.10.18、Torch2.7.1+cu128、Gymnasium1.0.0、pyarrow17；新隔离容器，不升级现役|
|环境/IK|GPU256 PcdEpisodeEnv，primitive OBB/ghost，sync_v5，原解析IK→DLS|同一只读类与源码，不包装逐环境CPU step|显式动作恢复核查；不含BioIK|
|观测|map128×128×3，字节高度0.01m，向量74原单位|相同encode/decode、向量排列与独立CNN/MLP容量|无额外归一化/观测滤波|
|网络|三stride2卷积16/32/32；MLP512/512/256；三维均值/logstd；两个独立Q|仅原生SACTorchModel的policy/Q自定义网络，复用相同网络定义|无共享编码器；初始随机数消费/建网顺序不同，非逐位匹配初始化|
|动作/概率|Normal.rsample→tanh；logstd[-20,2]；Jacobian epsilon1e-6|原生TorchSquashedGaussian；同范围与logstd截断，logp执行atanh/安全clamp并将Gaussian logp clamp[-100,100]|小batch非饱和输入logprob核查，饱和边界计算差异保留；不替换原生分布|
|训练初态/种子|共同trainer实际seed4718/4719，从头|同身份seed，由共同trainer播种，RLlib config.seed=None|Ray2.40 seed函数会硬写错误CUBLAS字符串，避免内部重播种；实际种子写config/identity/runtime，None不表示无种子|
|共同数值条件|CUBLAS_WORKSPACE_CONFIG=:4096:8，cudnn.deterministic=True，benchmark=False|同左|必要工程修复；不称与旧9.11数值逐位相同。旧smoke原件保留；最终版另做1000|
|奖励/失败/终止|原cbl_continue、零失败strict_success；episode_end_bootstrap=True|同原transition reward/mask|原动作失败并非episode终止；不暗改奖励/终止|
|bootstrap/auto reset|保存tr.next_observation后入回放；mask沿原语义|terminateds=(mask==0)，n_step=1；tr.next_observation直接入原生replay|没有Gym autoreset丢失final observation；实际episode标志在环境/指标保存，terminateds列用于原bootstrap mask|
|warmup|前1000消费对应active rows均匀[-1,1]动作；更新独立于warmup|同一GPU动作覆盖路径；native learning_starts=250|首更新260，而非等1000。原生10转移采样→每次1更新，RR实证[1,1]|
|replay|100000，GPUuint8 ring，random.sample无放回|100000，原生MultiAgentReplayBuffer/ReplayBuffer，CPU保存np字节图，有放回均匀采样|非PER；不压缩/量化额外维度；采样batch转GPU成本计入native训练栈|
|插入/更新时序|消费260前用旧259条；之后push当前条|原生先插入251–260，再采样/更新一次|必要原生时序差异保留，未重写训练step|
|真实UTD|每10消费1update；1000=75、3M预期299975|原生training_intensity=25.6样本/新转移，fragment10、batch256、RR[1,1]|25.6不是25.6次update/转移。生成/待消费/实际消费/回放抽样总数分开；3M计数待实际完整训练|
|actor/critic/alpha更新|先critic更新，再用更新后Q算actor，再alpha|原生一次loss构图、原生四优化器梯度/step流程|每次各更新一次，actor目标所用Q时刻不同|
|critic loss|两Q MSE之和，单critic Adam|原生两独立Huber(delta1)均值，分Q Adam|保持原生loss，不能称loss对齐；固定batch验证各自公式/梯度|
|Adam/clip|默认eps1e-8；合并双Q grad norm10|原生Adam eps1e-7，独立双Q优化器/各参数组clip10|独立critic clipping与合并C不等价；明确保留|
|alpha|初始1；第一更新后exp(logα)×0.35；<=0.05固定并停调参|初始1，原生exp(logα)，不断调参/无0.35缩放与0.05停调参|R真实alpha_rule=rllib，不能因继承C旧元数据误写capped|
|target entropy/γ/τ|−3/.99/.001|同左，target每update原生同步|构建后用原生update_target(tau=1)对齐C初始hardcopy；实际学习target在target_models[model]，不是CPU target_model模板|
|LR|1e-4→1e-6按exp_updates；跨度4999743历史updates；alpha1e-6恒定|每原生update后按相同4999743更新跨度设置现有Adam LR；alpha1e-6恒定|3M horizon一直固定，不将profile250k当衰减终点；总updates配置不是实际更新预算|
|调度/资源|同GPU型号、单卡、cpuset24–31最多8CPU，Torch/库线程2|同左；本地RLlib sampler桥，非分布式Ray EnvRunner|完整SAC.training_step及native replay/learner/target实际执行；不声称Ray远端调度收益|
|停止/异常|本任务共同只停nonfinite与真实错误/用户STOP|同左|不继承旧9.11“Q>500k参考10倍”停止门；该共用工程差异已登记，不能据Q门挑seed|
|checkpoint|完整模型/optimizer/scheduler/replay/environment/RNG/pending/cursor/计数|原生policy.get_state含optimizers、实际GPU target、native replay.get_state、原生counters＋共同完整环境/RNG/pending与10批未插入队列|非空pending与下一update恢复核查；不把单actor文件称可精确恢复|
|评估|每250k到3M同冻结100随机+96语义|同左；两seed各自报告|四run共9408开发回合，开发集反复使用；不读9.11保留test；终点比较不选峰值|
|指标|原strict_success、Core._finish success/d/r、首拒绝与原因、拒绝动作数/回合、无拒绝停滞|相同轻量只读Observer|原最终成功=(s==length)&d<=.025&r<=.05。route_complete/terminated不能替代；IK APIwall/CUDAevents、observer开销单列|

本表对实际源代码/对应tag做定向核查，当前不包含训练胜负结论。实际配置在`config/task9/task9_13/*_seed*.json`和每run runtime.actual_native_config；源码/版本/容器与运行证据见独立执行日志及RESULTS。
