# task7.18 — 结果

**2026-10-26执行冻结：paused。** 用户已冻结task7全部后续执行，见[父冻结入口](../TASK.md#2026-10-26-当前冻结入口)。已完成成果与下文历史状态保留；不得依旧授权自动续训、恢复或派发。当前转入task8地图迁移规划。

状态：**active（新几何正式重训中）**。当前事实见文末run-id `t7.18-v3-20261021`；两变体各从头5M，未完成/冻结。旧formal仅保留历史。

## 运行记录

（尚无。每次执行按run-id追加：执行Agent与实际模型/强度、改动文件、命令、版本、退出码、证据路径、结论与限制。）

## 交接

- 当前负责人：Codex（GPT6.1sol/high，exec参数核实）。当前交接见文末正式训练记录；前述进行中快照是历史状态。


## run-id t7.18-20261021 — 实现与有界核查（进行中）

负责人Codex；实际模型GPT6.1sol / high（宿主codex exec PID2530514 argv核实）。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high：核查SAC数值、GPU路径与跨模块语义。授权与边界按[TASK派发参数](TASK.md#派发参数2026-10-21claude工程选择src-0901)、[SRC-0901](../../../SOURCES.md#src-0901)、[SRC-0431](../../../SOURCES.md#src-0431)。完整过程[独立日志](../../../agent_logs/task7/task7.18/20261021-codex-stage-l.md)。

### 实现与来源

- 新包`forem/src/task7_lower/`：observation、networks、replay、sac、training、inference、profile与tests；入口`forem/scripts/task7_lower_train.py`，supervise/monitor脚本，`forem/config/task7/lower_train.json`。`task7_sim/kinematics.py`仅DLS启动优化，其余模拟模块/阶段一/参考仓库只读，未创建或修改lower_policy.py。
- CBL来源commit/hash、超参对应、新编码器工程选择、74/75维向量顺序及uint8量化协议见[SRC-0470](../../../SOURCES.md#src-0470)。SAC四方法直接复制`forem/scripts/scwm_sac.py`，更新前旧replay>256、#258首次更新，单条有效转移1更新；5M总更新4,999,743，指数衰减长度按此数。随机预热1000有效动作，独立于开始更新。
- 观察使用Core L.2字段，不使用真值/全局底盘/扫描时间戳；图在线和经验池共同调用encode_grid/decode_grid。同步74维，异步75维；量化`round(h/.01).clamp(0,255)`解码米，二值通道0/1。
- DLS默认保留eager，本任务显式启用CUDA Graph，向上二次幂补独立行、64迭代及接受阈值均保留。机制、失败记录与已做等价测试见[SRC-0471](../../../SOURCES.md#src-0471)。只消费完毕的诊断历史释放，不改状态、奖励、终止或mask。

### 已执行测试与限制

原始证据和适用性：[SRC-0472](../../../SOURCES.md#src-0472)。

命令公共前缀：宿主`python3 -u forem/logs/task7/t7.18-20261021/run.py NAME ...`→已有forem-dev，CUDA_VISIBLE_DEVICES=2、PYTHONPATH=/root/mm_husky_ws/src、OMP/MKL线程2、单次timeout≤590s。精确argv/退出码/保守容器调用墙钟在[commands.jsonl](../../../../logs/task7/t7.18-20261021/commands.jsonl)。

- 基础RED缺模块退出2，GREEN 6 passed；新增完整checkpoint/RNG/replay/队列恢复、历史消费等价后8 passed。更新测试从原SAC AST提取方法，在同模型/输入/RNG上核对所有损失与参数逐元素相同，包括温度触底与恢复后的下一次更新。
- 原DLS图捕获失败两次，保留原日志；修复后n=1/3/16/65各两组所有IKResult字段torch.equal、接受集合不变，1 passed。
- 全目录误收集7.19/7.20并行active测试，2项decision_env失败（当时实际dt=.8而active测试期望.05）；只SIGINT核实的本任务pytest，92项已通过，非本任务最终验收。重跑限定task7.17最终JUnit列出的17个稳定模块，153项全通过；新增唯一失败为导入旧SB3路径失败。AST直接加载vendor原分布类后本包12项通过，包含原SB3 action/log_prob精确一致、精确预算挂起行不尝试/不改状态。后来新增Actor导出测试尚待执行，不将12项扩大为当前全套通过。
- 当前结论仅为有界单测/配对覆盖，非阶段L训练完成、非冻结验收；已知URDF保守胶囊遮挡与“上臂–顶板整对放行”等限制沿task7.14，未移动传感器/改碰撞。

### 性能（中间记录，不是正式启动依据）

实测来源：[SRC-0472](../../../SOURCES.md#src-0472)。

GPU2实际参数与Adam动量cuda:0，Adam step计数器CPU为torch默认；batch256更新预热后约13.7ms。DLS n=1/16/64/256 eager约270ms，graph预热后约28–32ms，首次捕获约1s；单独微基准不代替端到端。

真实训练池seed4718，raw=0，E16/64 eager与graph分别独立完整reset/8调用；地图/提案种子/全部Transition字段逐元素相同，实际DLS回退计数相同。E64纯环境吞吐约95→321–327转移/s，reset约26→16s。原始分布、计数/精度/冷启动成本见`results/task7/t7.18-20261021/profile-E*-*.json`。E256/分项/线程/试训/评估/检查点/墙钟推算仍在执行，不以中间值启动5M。

### 交接接口（供task7.20）

- 小文件`checkpoint-NNNNNNN.actor.pt`/`final.actor.pt`：torch.save字典，format=`task7-lower-actor-v1`，含policy state_dict、synchronous、vector_dim、steps及同值step、action_version=`lower-action-l1-d8-v1`、versions(checkpoint/observation/action/synchronous)、observation_version=`lower-observation-d20-v1`。此时只是格式，尚无正式训练完成Actor。
- `from task7_lower.inference import DeterministicActor`；`policy = DeterministicActor(path, device='cuda')`；`raw = policy(observation)`。输入为Core批量观测dict[str,torch.Tensor]（所有字段float32且与Actor同设备），输出Tensor[E,3]的归一化原始动作[u,ω,v]，确定性tanh(mean)；内部执行统一量化→解码。每变体加载各自权重/74或75维，不互换。
- 完整文件format=`task7-lower-full-v1`，显式action_version=`lower-action-l1-d8-v1`：sac含网络/targets/三个Adam/两个scheduler/log_alpha/alpha与开关/update_count；replay含uint8当前/下一地图、向量/action/reward/mask、环位置/size/采样RNG；env含Core、地图、路线、初态与分流RNG、队列/扫描/计数；state含已消费数、子步/仿真秒和待消费批转移cursor；rng含Python/NumPy/torch/CUDA。DLS图缓存不持久化，恢复重建。
- 每250k精确消费数存完整状态再验证；若验证中断，validation_pending使恢复补齐该次验证。最终预算不足E批时只挂起超出预算的行，避免多尝试后丢样本。保存临时文件fsync后原子替换。
- 后台试训driver尚在执行/等待（宿主PID2560522），当前并行E扩展driver PID2553175，日志`forem/logs/task7/t7.18-20261021/{profile-sweep-v2.host,pilot-driver}.log`。不得把这两个PID用于停止其他任务。正式supervisor尚未启动；正式PID/停止/恢复将在启动后追加。


### 同步试训完成（不同步仍在运行）

依据[SRC-0473](../../../SOURCES.md#src-0473)补记：sync 50000转移/49743更新，退出0，wall1124.756s，其中完整保存58.245s；到达270/6901段，失败6631（IK1817/底盘216/臂环境0/自碰撞4598），超时0。完成1281回合、严格成功6，不能视作效果通过；所有曲线点loss/Q/alpha有限，末alpha=.33305、固定前256条replay诊断Q_abs_max20.3365。尝试/提交96036/89405子步，4470.25模拟秒，G1整帧3208/47613。

同步历史final.pt和final.actor.pt创建于metadata补齐之前，保留原件；**不能直接交task7.20严格loader**。后续finish将另导出compatible.actor.pt、逐Tensor核对，再使用新格式作正式保存。最终loader集成测试/完整GPU恢复/100图验证尚待执行，不先写通过。


## run-id t7.18-20261021-formal — 续接核验与正式训练（2026-10-21 16:59启动）

负责人Codex，实际GPT6.1sol/high（当前exec宿主PID2695454的argv核实）。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high：需核对数值恢复、训练预算与跨模块接口。沿用[SRC-0901](../../../SOURCES.md#src-0901)、[SRC-0431](../../../SOURCES.md#src-0431)授权；本节替代前述“试训仍在运行/正式未启动”的当前状态，不撤销历史失败。

### 续接与恢复验收

- 前置task7.15/16/17均done；旧driver/worker已退出，无残留本任务compute；启动前GPU2/3均无compute，task7.19已退出。Xorg不算compute。保留main全部已有改动，不提交Git、不启停容器、不干预其他会话/进程。
- 已读取两试训final/summary、两finish报告、100图验证、IO与ledger-probe；不重做已经验证的环境扩展/稳定153项回归。最终本包全15项（含新增mask、metadata、恢复预算守卫）通过：`python3 -u forem/logs/task7/t7.18-20261021/run.py resumed-final-tests python3 -B -m pytest -q -p no:cacheprovider src/task7_lower/tests --junitxml=results/task7/t7.18-20261021/lower-tests-resumed.xml`，退出0；[JUnit](../../../../results/task7/t7.18-20261021/lower-tests-resumed.xml)、[log](../../../../logs/task7/t7.18-20261021/resumed-final-tests.log)。原CBL方法保留的3个PyTorch warning未转成错误或重写训练公式。[SRC-0475](../../../SOURCES.md#src-0475)
- 按用户最新批准的工程口径（[SRC-0474补记](../../../SOURCES.md#src-0474)），两变体完整恢复后初始SAC完整状态hash、action、loss、replay采样RNG与环境Transition全部字段精确相同；单次GPU更新最大权重差同步1.4901161193847656e−8、异步7.450580596923828e−9，均≤1e−6，**按批准口径通过**。严格post-update hash仍False，历史红日志保留，不声称逐位恢复。cuDNN deterministic/benchmark与deterministic_algorithms均False，不改正常吞吐路径。精确产物[同步](../../../../results/task7/t7.18-20261021/resume-accepted-sync.json)、[异步](../../../../results/task7/t7.18-20261021/resume-accepted-async.json)，两命令退出0；只新增诊断CPU权重快照，不改训练更新。
- task7.20 metadata集成测试已通过；历史full缺action_version不回写，仅[同步compatible.actor.pt](../../../../results/task7/t7.18-20261021/pilot-sync/compatible.actor.pt)、[异步compatible.actor.pt](../../../../results/task7/t7.18-20261021/pilot-async/compatible.actor.pt)供接口冒烟，policy逐Tensor与历史导出相同。它们是50k试训模型，**不是已冻结下层**；正式各250k后的actor具完整metadata。未编辑lower_policy.py。

### 试训曲线与分项

来源[SRC-0472](../../../SOURCES.md#src-0472)、[SRC-0473](../../../SOURCES.md#src-0473)、[SRC-0475](../../../SOURCES.md#src-0475)。两变体各50000转移/49743更新、退出0；图[曲线](../../../../results/task7/t7.18-20261021/pilot-curves.png)，CSV：[sync](../../../../results/task7/t7.18-20261021/pilot-sync-curve.csv) / [async](../../../../results/task7/t7.18-20261021/pilot-async-curve.csv)。导出退出0，无新增环境试验。所有50个曲线点loss/Q/alpha有限，不将数值有限当作效果通过。

|指标|同步|不同步|
|---|---:|---:|
|完整wall秒（含final保存）|1124.756|950.161|
|SAC update累计秒 / p50毫秒|654.554 / 13.134|662.272 / 13.352|
|reset累计秒 / p50秒|223.638 / .8522|67.681 / .1804|
|候选 / 观测累计秒|24.956 / 17.998|16.929 / 17.843|
|推理 / 环境step累计秒|.3774 / 87.105|.3833 / 88.171|
|replay sample / insert累计秒|22.632 / 25.357|22.735 / 26.373|
|日志 / final保存秒|.0103 / 58.245|.0112 / 37.730|
|末alpha / 末次固定replay诊断Q绝对峰值|.333053 / 20.3365|.333035 / 15.8322|
|训练段到达 / 总段|270 / 6901|42 / 1145|
|失败IK/底盘/臂环境/自碰撞|1817/216/0/4598|73/59/0/895|
|段超时 / 已完成回合 / 严格成功|0 / 1281 / 6|76 / 138 / 2|
|尝试 / 提交子步|96036 / 89405|99413 / 98386|
|提交仿真秒|4470.250|4919.300|
|尝试IK中DLS回退数|68207 / 96036|96572 / 99413|
|G1整帧 / 传感器帧|3208 / 47613|357 / 49853|

训练后的真实动作分布DLS回退远高于旧零动作基线，仍包含在实际update/环境/重置wall中；不得套用旧“6%”作本轮训练率。网络、replay、optimizer动量在GPU，Adam step标量CPU；试训峰值allocated约27.97GB/worker。线程1/2/4同输入精确等价但无稳定收益，保留2；未增加异步进程/后台预采样。同步/不同步真实E256纯环境 eager→graph吞吐274.3→440.7、277.1→580.2转移/s（含首次捕获），完整reset100.4→43.5、101.0→43.9s；DLS n=1/3/16/65所有输出字段与接受集合精确相同。CPU→GPU显式构造87064 bytes/1792次及其限制、线程分布见parts.json，不将已拦截路径称全部runtime memcpy。详源条目与原JSON。

### 独立100图验证（50k模型）

[同步报告](../../../../results/task7/t7.18-20261021/pilot-validation-sync.json)、[不同步报告](../../../../results/task7/t7.18-20261021/pilot-validation-async.json)。两档各50张×1完整回合，确定性动作、规则候选均匀抽、地图拒绝不换图，独立环境/RNG，评估后恢复训练全局RNG。[SRC-0475](../../../SOURCES.md#src-0475)

|指标|同步|不同步|
|---|---:|---:|
|段数|497|799|
|到达 / 失败 / 超时率|.038229 / .959759 / .002012|.033792 / .237797 / .728411|
|IK / 底盘 / 臂环境 / 自碰撞失败率|.181087 / .064386 / 0 / .714286|.031289 / .005006 / 0 / .201502|
|平均段 / 回合仿真秒|.993662 / 4.938501|12.089174 / 96.594307|
|严格成功率|.04|0|
|G1整帧 / 总帧 / 比例|765 / 5093 / .150206|87 / 96843 / .000898|
|实际wall秒|116.178|562.856|

这些是短训模型指标，失败/超时明显，**不构成阶段L效果验收、G7/D10冻结或进入上层训练的许可**。已知保守碰撞/遮挡限制沿task7.14，未改动作、奖励、阈值或观测。

### IO、预算与5M推算

[SRC-0475](../../../SOURCES.md#src-0475)登记全部输入/公式/单位/条件；[formal-gate.json](../../../../results/task7/t7.18-20261021/formal-gate.json)保存可机器读取结果。

- 合成重复填10万条仅用于IO：完整文件13274022619 bytes、save94.099s/load15.020s，uint8 replay完整恢复；不进入训练样本。全10000图planner cache按已测4139图pickle线性增长，估最终checkpoint约17.628GB、save124.966s，非实测上界。
- `T_v=100*(50k_wall_v-50k_final_save_v)+21*124.966+20*validation_wall_v+ceil(5M/256)*.00408059`，单位秒。含20次250k完整检查点＋最终重复full、20次100图验证及两fsync交互账本；初次冷启动留在base×100里。同步**31.0218h**、不同步**29.2234h**；各独占GPU时全局预计max＝31.0218h、累计worker＝60.2452h。满足单次≤48h启动门；不承诺实际工期，后续policy改变reset/超时/DLS分布及CPU/IO争用均会影响耗时。
- 正式前命令ledger累计＋早期60s保守预留 **4224.835s（70.414分钟）<4h**，含恢复失败诊断、两50k、100图验证、IO与最终测试；命令原始退出码全保留。正式训练另按授权5M预算，不计入前置4h，也不把试训/ledger-probe追加为正式转移。
- 配置默认E64→已测选定E256；其余训练超参与科学条件不改。全量cache与timing列表/IO临时内存有增加，磁盘约740.4GB的两run检查点估算低于现有19TB空闲；非完整RAM上界。正式版本[manifest](../../../../results/task7/t7.18-20261021/source-manifest-formal.json)、[源码快照](../../../../logs/task7/t7.18-20261021/source_snapshot_formal/)，保留旧试训源码快照，不覆盖。

### 正式启动、监控与停止/恢复

2026-10-21 **16:59:17+08:00**，forem-dev现有容器内启动。各从头seed4718、E256、目标5000000动作转移/4999743次更新。启动命令（已执行，各退出0，分配GPU空闲检查内置，仅看compute）：

```bash
python3 forem/scripts/task7_lower_launch.py --variant sync --gate forem/results/task7/t7.18-20261021/formal-gate.json --output forem/results/task7/t7.18-20261021/formal-sync
python3 forem/scripts/task7_lower_launch.py --variant async --gate forem/results/task7/t7.18-20261021/formal-gate.json --output forem/results/task7/t7.18-20261021/formal-async
```

|变体|物理GPU|宿主sg启动PID|宿主supervisor / worker PID|容器supervisor / worker PID|run目录|
|---|---:|---:|---|---|---|
|sync|2|2704891|2704925 / 2704934|2546630 / 2546636|`forem/results/task7/t7.18-20261021/formal-sync/`|
|async|3|2704936|2704971 / 2704977|2546637 / 2546643|`forem/results/task7/t7.18-20261021/formal-async/`|

精确argv/启动前compute和GPU UUID见各run `launch.json`；`host.log`、`supervisor.log`、`worker.log`、`heartbeat.json`（每30s）、`learning.jsonl`（每1000转移）、`interactions.jsonl`（每环境批intent/complete并fsync）。GPU0/1如出现compute属于其他会话，本任务未使用。[SRC-0476](../../../SOURCES.md#src-0476)

宿主只读监控（已执行）：

```bash
python3 forem/scripts/task7_lower_monitor.py forem/results/task7/t7.18-20261021/formal-sync
python3 forem/scripts/task7_lower_monitor.py forem/results/task7/t7.18-20261021/formal-async
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory --format=csv
```

需要有意停止本run时，在对应run目录创建`STOP`（尚未执行）；supervisor/worker在转移边界保存`interrupted.pt`后退出。不要停止容器或其他PID。恢复（尚未执行）：核查本run所有旧supervisor/worker已退出、对应GPU无compute，确认`interrupted.pt.meta.json`与interactions账本由safe_to_resume判定覆盖全部动作，移除**该run** STOP后，在同容器/同GPU/同版本/config下重启 `python3 -u scripts/task7_lower_supervise.py --config config/task7/lower_train.json --variant VARIANT --environments 256 --output /root/mm_husky_ws/results/task7/t7.18-20261021/formal-VARIANT --gate /root/mm_husky_ws/results/task7/t7.18-20261021/formal-gate.json`，带与launch.json相同CUDA_VISIBLE_DEVICES/PYTHONPATH/线程环境。supervisor自动选择最新完整checkpoint；有checkpoint未覆盖的动作或未闭合intent则**阻止回退重复预算并报告**，不擅自从旧checkpoint重跑。相同checkpoint重复失败也停止报告。

### 剩余事项与交接

- 当前负责人Codex；PROGRESS保持active/训练中，不标review/done。训练尚在运行，后续每250k检查 `checkpoint-*.pt/.actor.pt/.meta.json` 与 `validation-*.json` 入账，关注数值、各失败/超时与G1。
- 两run最终须达到5M且updates4999743、完整状态/actor/最后验证与summary齐全，再汇总最终曲线和指标、核对预算/实际wall并将PROGRESS本行改review交Claude；尚未执行这些结束验收。
- D10由task7.19处理，本任务不冻结、不判断可行分母、不启动上层。无额外实验/功能授权，也未修改阶段一/参考仓库/其他会话文件。

### 启动后固定核查快照

[核查产物](../../../../results/task7/t7.18-20261021/startup-verification.json)（2026-10-21T17:04:32.708447+08:00）：sync 12000 / async 15000，各updates＝step−257、loss/Q/alpha有限，无worker退出/Traceback，心跳更新；GPU2/3 compute分别为上表worker。实际intra-op2/interop64（没有擅自改线程），torch2.7.1+cu128/CUDA12.8，TF32沿原默认。共享G1/G7/D10及其测试由并行任务变更，未被本下层训练导入；其余源码与formal manifest逐字节相同。[SRC-0476](../../../SOURCES.md#src-0476)


## run-id t7.18-v3-20261021 — schema4新几何从头重训（执行中）

负责人Codex；实际GPT6.1sol/high（宿主exec PID3182687 argv核实）。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由：并行源码执行路径等价、新几何SAC数值与长训成本核查。授权为本次派发原文`forem/logs/task7/codex-dispatch-stageL-retrain/prompt.txt`，沿原派发协议[SRC-0901](../../../SOURCES.md#src-0901)，版本/授权/路径证据[SRC-0477](../../../SOURCES.md#src-0477)。旧formal及checkpoint/interrupted保留历史，均不用于初始化/续训。

### 开工与源码路径核查

- PROGRESS task7.18.2为done，Claude r3复核通过；生产schema4 `selfcoll-multisphere-v4-spherepairs-20261021`，`robot_geometry.json` SHA256 `6c41120ad85bdea61a24b1089e825febf4f6b62eb93da0474e51f386167b084a`；环境几何`v1-unchanged`。已知几何限制仍见[子任务RESULTS](task7.18.2/RESULTS.md)。
- GPU2/3开工均无compute，Xorg不计；其他GPU任务不干预，既有forem-dev不启停。实际宿主开工23:27，派发与Claude记录使用23:30，保留原记录、不调整时钟。main既有未提交改动保留，本轮不提交Git。
- 全部sim/lower源码与tests、task7配置及lower脚本SHA256见[preflight manifest](../../../../results/task7/t7.18-v3-20261021/source-manifest-preflight.json)，字节快照`forem/logs/task7/t7.18-v3-20261021/source_snapshot/`。
- [静态导入/配置审计](../../../../results/task7/t7.18-v3-20261021/stage-l-import-and-config-audit.json)：全部下层生产源码与旧formal字节相同（SAC提速候选未采用）；原科学配置相同，仅新增4项几何元数据。task7.22的DecisionEnv不在阶段L递归导入链。Core新增选项在阶段L为retain_transitions=True、observation_chunk_size=32、reuse_route_raster=False，保留原行为。
- [同输入对照](../../../../results/task7/t7.18-v3-20261021/core-equivalence.json)：旧formal Core仅回填新几何q传递作为参考，与当前Core比较；E256每变体12步，sync3055/async3071条转移，构造器Tensor、候选信息（排除明确wall诊断计时）、全部观测、确定性Actor动作、Transition与Core Tensor逐元素相同。动态DecisionEnv未导入。r2退出0/145.620s；此前诊断脚本的计数生命周期/墙钟字段比较失败保留原脚本与日志并计预算。有限采样加默认分支源码核查支持本轮阶段L使用，不称任意选项全域等价。

### 有界阶段中间快照（历史；现已完成）

以下保留试训启动时的记录；当前状态以随后正式启动与交接小节为准，pilot-driver现已退出。

每变体选25000转移（用户≤50000上限内的有界停止点，不改总更新调度/预热/更新频率）；与旧试训25000快照比较，另保留旧50000终点作为历史。当前pilot-driver宿主PID3191241（首次PID3190436在计算前因并行上层配置变化被保护拒绝；原日志保留），仅顺序GPU2运行新pilot25k-sync/async、各100图确定性验证与新几何满经验池IO；其argv/返回码/墙钟记`forem/logs/task7/t7.18-v3-20261021/commands.jsonl`。旧预正式累计4224.835326s继续计入4h限额。

新结果目录`forem/results/task7/t7.18-v3-20261021/`；独立过程日志见[stage-l日志](../../../agent_logs/task7/task7.18/20261021-codex-stage-l.md)。本轮没有修改生产源码/配置、奖励/终止/动作/观测/频率或task7_sim几何。数值健康、分类对照、墙钟推算与新正式启动此刻**尚未完成**，待本轮实测追加。监控有界试训：`python3 forem/scripts/task7_lower_monitor.py forem/results/task7/t7.18-v3-20261021/pilot25k-sync`（后续async同理）；停止仅对该run创建STOP，worker保存interrupted后退出，driver收到失败不继续后续步骤；不得将该pilot恢复成正式run。


### 本轮有界结果与正式启动（2026-10-22T00:10:02.336643+08:00）

两变体各25000转移/24743更新全部退出0，各25次学习日志loss/Q/alpha均有限；下层更新代码与原版一致。新满池IO与各100图验证均退出0。原始分项、学习范围、旧25k/50k与新25k对照见[pilot-comparison](../../../../results/task7/t7.18-v3-20261021/pilot-comparison.json)，依据[SRC-0478](../../../SOURCES.md#src-0478)。

|变体/预算|结束段|到达|IK失败|底盘碰撞|机械臂环境碰撞|自碰撞|超时|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|sync 旧几何25k快照|3814|150 (3.93%)|1016|123|0|2525 (66.20%)|0|
|sync 新几何25k终点|1333|149 (11.18%)|700|108|0|375 (28.13%)|1|
|async 旧几何25k快照|759|29 (3.82%)|50|53|0|627 (82.61%)|0|
|async 新几何25k终点|195|42 (21.54%)|50|69|0|33 (16.92%)|1|

百分比均以已结束段为分母；自碰撞占失败的比例另记JSON。旧25k是消费步快照，可能包含已执行pending批；可用env_actions：sync None、async None（None为原试训未留账本，不能补造）。新终点均恰25000实际动作。新旧候选/reset/策略分布也不同，表只作描述对照，不宣称最终策略提升或全域无误报。新sync/async超时率分别0.08%/0.51%。

- 新100图验证sync：到达率16.09%，严格整回合成功率21.00%，wall 170.332s；async：到达率12.53%，严格成功率6.00%，wall 601.935s。其他失败分类、平均时间、G1整帧遮挡原值均在新validation JSON及comparison中，不作D10冻结。
- 不同步早期验证段超时率 **71.58%**，失败类型率（IK/底盘/机械臂环境/自碰撞）分别为 7.36%/2.58%/0.00%/5.94%；不是最终策略结果，保持原协议继续正式训练，不改超参/奖励/终止。
- 新IO满100k合成池仅测保存/加载：75.987/9.538s，测得11345292003 bytes。完整设备与缓存/分项在[io-new-geometry](../../../../results/task7/t7.18-v3-20261021/io-new-geometry.json)及试训summary；Actor/Critic/target/alpha/replay均cuda:0，Adam step CPU为原布局。合成IO文件禁止用于训练。
- [正式启动门](../../../../results/task7/t7.18-v3-20261021/formal-gate.json)：(新25k wall−最终保存)×200＋21次新满池/全cache估计保存＋20次新100图验证；sync **30.11h**、async **29.95h**，均≤48h。并行条件全局约30.11h、累计worker约60.06h；不是工期保证，后续策略分布与共享CPU/IO竞争会改变成本，无故障余量承诺。预正式累计6378.217s（含旧4224.835s和全部失败核查）＜14400s。

**已启动全新正式run，均无--resume、initialized_from=null；seed4718、E256、各5M/4999743更新，每250k完整检查点＋100图验证。** 新run版本v3与几何schema4/v4是不同命名；未改任何生产科学条件。依据[SRC-0479](../../../SOURCES.md#src-0479)。

|变体|新目录（forem/results/task7/t7.18-v3-20261021/下）|物理GPU|宿主supervisor / worker|容器supervisor / worker|启动核查消费步|
|---|---|---:|---|---|---:|
|sync|formal-v3-sync|2|3223574 / 3223585|2549329 / 2549335|2000|
|async|formal-v3-async|3|3223620 / 3223627|2549336 / 2549342|2000|

各run `launch.json`留精确命令/时刻/宿主launcher PID，`training-metadata.json`与`source-manifest.json`写明几何版本及源码/配置哈希；完整[source manifest](../../../../results/task7/t7.18-v3-20261021/source-manifest-formal-v3.json)、[启动核查](../../../../results/task7/t7.18-v3-20261021/startup-verification.json)与原始源码快照可复核。核查时两worker在各自GPU compute表，无Traceback/worker_exit，全部已记录数值有限；不等待5M完成，不作冻结。

### 新正式run监控、停止与恢复

在仓库根目录执行（以下sync，async将路径末尾改formal-v3-async）：

```bash
python3 forem/scripts/task7_lower_monitor.py forem/results/task7/t7.18-v3-20261021/formal-v3-sync
tail -n 5 forem/results/task7/t7.18-v3-20261021/formal-v3-sync/supervisor.log
```

停止仅创建对应新run的STOP；训练按转移边界保存`interrupted.pt`（含pending/replay/optimizer/RNG/env/geometry配置），监督器停止重启；检查worker_exit和PID退出后才视为停止完成：

```bash
touch forem/results/task7/t7.18-v3-20261021/formal-v3-sync/STOP
```

恢复前核查目标GPU无compute、该run旧supervisor/worker已退出、配置/几何与training-metadata中的全部阶段L依赖哈希相同、同run完整检查点存在且账本覆盖已执行动作；仅移除该run STOP。若supervisor报告budget_safe_resume_blocked，必须停报，不回退已执行交互或改账本。仅恢复**本轮新正式run自己的检查点**，禁止用旧formal或任何pilot/IO文件。确认后在既有容器按同配置后台重启supervisor：

```bash
rm forem/results/task7/t7.18-v3-20261021/formal-v3-sync/STOP
sg docker -c 'docker exec -d -e CUDA_VISIBLE_DEVICES=2 -e PYTHONPATH=/root/mm_husky_ws/src -e OMP_NUM_THREADS=2 -e MKL_NUM_THREADS=2 -e PYTHONDONTWRITEBYTECODE=1 -w /root/mm_husky_ws forem-dev python3 -u scripts/task7_lower_supervise.py --config config/task7/lower_train.json --variant sync --environments 256 --output results/task7/t7.18-v3-20261021/formal-v3-sync --gate results/task7/t7.18-v3-20261021/formal-gate.json'
```

async恢复同时替换GPU为3、variant为async及目录为formal-v3-async。上述停止/恢复命令是交接方法，**本轮正式运行未实际执行停止或恢复**；原正式历史STOP及产物保留。

交接：当前负责人Codex，后续按每250k full/actor/meta与100图验证监控数值、分类及实际成本；待5M/4999743且final/summary/末次验证齐全，再汇总并交Claude复核。风险：schema4已知有限几何误报、早期25k外推与共享资源竞争、崩溃后未覆盖交互导致安全恢复被阻断；未完成训练/冻结。未提交Git、未修改生产源码/配置/几何、未停止非本任务进程。
