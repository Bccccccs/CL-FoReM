# P1 扩量训练的有界内存方案

2026-09-28，RESEARCH-028。用户要求：“关于上次内存爆炸的问题也要给出合理的解决方案，现在的内存就这么多”。**方案已由P1-FIX-028落实M0–M4并完成100/1000/9600三级有限验收（2026-09-28）；M5已完成1000回合单seed正式train/val诊断（D36），独立test/跨seed仍未验收。** 证据见[任务交接](agent_logs/20260928-p1-fix.md)与[实测摘要](agent_logs/20260928-p1-resource-summary.json)。下文容量推算与初始计划保留为历史设计，不替代实测。 沿用现有采集数据、固定encoder、MLP、loss、优化器和训练/评测入口，不要求增加物理内存。

## 1. 根因与容量证据

当前机器RAM约251GiB。D29历史实测训练RSS约236GB并大量使用swap；本轮不重现全量OOM。主包HEAD `2a1348a87b3b5c45f495fafacad526f7eaee7749`，只读证据见[容量计算](agent_logs/20260928-memory-sizing.json)及[环境快照](agent_logs/20260928-research-environment.json)。

训练manifest确认9600个完整episode、2,373,775个转移、2,383,375个观测帧；地图float32、120×120×1：

| 分配 | 计算规模 | 含义 |
|---|---|---|
| 原始地图一份 | 137,282,400,000 bytes ≈127.85GiB | 磁盘压缩大小约0.86GB不能代表解压内存 |
| episode列表 + concatenate地图 | 至少255.71GiB | 已超过物理内存，尚不含其他数组/运行时 |
| 固定encoder输出（1041维FP32）一份 | 9.24GiB | 适合落盘缓存，不应反复全部拷贝 |
| 全量一步窗口特征 | 18.41GiB | 当前还会标准化再分配一份 |
| 全量五步窗口特征上界 | 55.23GiB | 不含rollout预测与临时tensor |
| 当前最长episode原始地图 | 53.61MiB（975步+首帧） | 单回合解压可以有界完成 |
| 512个一步特征窗口 | 4.07MiB | 仅输入张量，不含网络/梯度 |
| 128帧编码地图输入 | 7.03MiB | CNN中间激活须另行实测 |

以上为shape×dtype推算，不是实测峰值；完整manifest、ZIP目录读取无需全量解压，计算命令见主任务日志。

本轮还在现有容器中调用了真实`window_tensors`做小型CPU复现，并用NumPy1.23.5临时小文件验证：压缩NPZ成员即使传`mmap_mode='r'`仍为ndarray，NPY为memmap。见[复现脚本与原始输出](agent_logs/20260928-window-index-probe.json)。该检查没有加载真实地图全集、启动训练或修复代码。

代码中至少五处分配要一起处理：

1. [data.py](../src/modulation_rl/scripts/wm/data.py#L88) 逐回合加载全部成员并保存在列表；[第77行](../src/modulation_rl/scripts/wm/data.py#L77)再次concatenate，原列表仍被引用。
2. [encoder.py](../src/modulation_rl/scripts/wm/encoder.py#L40) 虽按batch编码，仍保留所有CPU输出，再`torch.cat`复制。
3. [train_offline.py](../src/modulation_rl/scripts/wm/train_offline.py#L29) 物化全部窗口并整体送device；[第41行](../src/modulation_rl/scripts/wm/train_offline.py#L41)又对整集标准化。
4. [训练第55–56行](../src/modulation_rl/scripts/wm/train_offline.py#L55) 每个epoch对整份train/val一次前向；训练batch变小也不改变这部分峰值。
5. [evaluate_prediction.py](../src/modulation_rl/scripts/wm/evaluate_prediction.py#L74) 全量构造1/5步窗口和rollout；[val_probe.py](../src/modulation_rl/scripts/wm/val_probe.py#L30)还会重新加载全部train拟合统计并整集推理，必须一起迁移。

另有独立正确性问题：`window_tensors`取出了`t`却未加到观测/动作偏移中，需要先完成时序索引复核/修复（D33）。节省内存不能保留这个错误来追求旧曲线一致。

## 2. 推荐方案：逐回合编码，缓存特征，按batch训练

固定encoder是P1a既定研究条件，直接利用这一点：原始地图只在特征缓存构建时读取一次，训练epoch只读取紧凑特征。数据、模型目标和float32精度保留。

```text
原有压缩episode文件（保留）
  → 校验manifest/分片SHA与episode完整性
  → 一次读取一个episode，按128帧编码
  → 分块写入FP32特征.npy + 小型episode/动作/dt索引
  → 释放当前episode及编码输出

每个epoch按既定RNG产生转移索引
  → 仅取本batch的 t..t+k 特征和 t..t+k-1 动作/dt
  → 本batch标准化、送GPU、训练或评测
  → 释放batch，累计标量/逐episode统计
```

**缓存身份**：至少绑定数据manifest及分片SHA、encoder checkpoint SHA、编码代码版本、特征顺序/dtype/shape、split、观测/动作/IK语义。使用临时文件、完成标记和原子rename；中断时只复用已校验的完整块，坏块重建，原始NPZ不覆盖。

**读取格式**：使用可映射的未压缩`.npy`特征分块，单块建议≤128MiB，打开映射/缓存总量≤512MiB；按batch涉及的分块分组读取，再还原抽样顺序。仅写`np.load(compressed.npz, mmap_mode='r')`并不能把ZIP成员变成按帧可映射数据。NumPy区分NPZ归档与NPY映射，`open_memmap`创建/读取NPY文件，参见[load文档](https://numpy.org/doc/stable/reference/generated/numpy.load.html)、[open_memmap文档](https://numpy.org/doc/stable/reference/generated/numpy.lib.format.open_memmap.html)。容器安装版本的行为仍由实现时小测确认。

**大episode保护**：缓存构建先读shape/dtype/压缩目录元数据。当前最大约54MiB可整episode读取；未来单个解压episode超过256MiB时，不扩大LRU，改为有界块解压到临时NPY或拒绝并报告超限。校验有限值也按块执行，避免大布尔临时数组。

**统计量**：仅对train观测用分块两遍统计或稳定的在线均值/方差，保持原来每个观测（含末帧）一次、`ddof=0`及Normalizer小方差规则；计算累积用float64，落盘float32，记录数值归约差异。不能用val/test计算统计量，也不能因窗口重复改变观测权重。

**训练语义**：保存完整episode边界、有效长度、subgoal、terminated/truncated与不完整轨迹标志。窗口必须用`obs_offset[e]+t+j`和`act_offset[e]+t+j`，j范围分别是0..k和0..k−1。首版沿用每epoch全局均匀转移打乱及seed；两列int64窗口约36MiB、一个permutation约18MiB，可暂保留，无须为了小索引先开发复杂采样器。不要用“每episode平均抽一样多”无意重权短轨迹。现有`torch.manual_seed`在创建model之后才进入train_model调用；新旧正确参考对比必须在创建模型之前设seed或加载相同初始state，并记录这项复现修正，不能仅因参数名seed相同就声称初始化相同。

**验证/评测**：全train/val forward改为分批累加误差和样本数，最后做加权平均，不能对不等长batch的均值再等权平均。研究报告仍按episode聚合后做配对bootstrap；五步预测批内递归，禁止使用真实中间特征作预测输入。只保存逐episode必要统计和诊断，bootstrap也分块抽样，不能新建随重复次数×episode数增长的巨型矩阵。

`val_probe.py`应复用共享流式读取/评测与checkpoint加载，使用checkpoint内hidden和normalizer；当前默认hidden构造无法加载v2的(64,)网络，重新用整train算normalizer也无必要。迁移前不要用其现有路径诊断9600回合；不能只修正式train/evaluate后遗漏这个诊断入口。

每batch从mapping复制到独立拥有的缓冲后才关闭/淘汰映射，不能让GPU搬运或后续计算引用已关闭底层内存。回归须覆盖k=5跨特征分块但不跨episode、LRU淘汰后batch仍有效、按块分组后还原样本顺序、最后不满batch。

## 3. 初始资源预算与监控

以下是**待验收预算**，不是已达到的吞吐或峰值承诺：

| 项目 | 首版设定 | 调整规则 |
|---|---|---|
| 单离线任务主存 | 正常目标≤12GiB；硬上限16GiB（含进程树/文件缓存时按隔离任务计量） | 超限停止该任务并保留产物，不扩大上限掩盖全量分配 |
| 单GPU | 首轮峰值预算8GiB，记录allocated/reserved与进程显存 | 编码batch独立128起步；依据实測下降或上调，先保持训练batch512 |
| 原始episode缓存 | 一次1个，解压预算≤256MiB | 超限走有界转换；不收集列表 |
| 特征映射/cache | 单块≤128MiB、总打开块≤512MiB | 关闭不用的mapping，不能永久保持全文件所有页驻留 |
| DataLoader | 先`num_workers=0`、无预取大队列、pin_memory关闭 | 仅在有吞吐证据后加1–2worker，并将worker/cache/prefetch全部计入预算 |
| 磁盘 | train特征约9.24GiB；含val/元数据/临时块先预留25GiB | 仅估算，开始前实测空间；缓存不是RAM |

避免给共享ROS容器整体设置16GiB限制，否则会影响已有进程。离线作业可复用同一镜像和挂载，在只包含该作业的容器/cgroup内设置16GiB内存且不增加swap额度；若隔离不可用，只做有限预检并使用进程树内存监控，不能把应用监控称为硬限制。实施时选用已有可用的资源隔离入口，不改宿主服务或杀其他任务。

记录峰值RSS/USS、任务cgroup memory.current/peak（若可用）、MemAvailable、swap增长、GPU峰值、缓存大小、每批时间。memmap是文件映射，仍占用页缓存；只有分块关闭、有限预取与实測才能证明资源有界。启动前保留至少32GiB宿主余量，若其他工作使余量不足则等待，不能依据本轮238GiB可用快照承诺以后可用。

## 4. 为什么不选其他方案

- **只减batch/加swap**：故障在训练循环开始前的全量解压和复制；没有消除根因。
- **只做NPZ懒加载并每epoch重编码**：可作为小样本正确性参考，但压缩随机读和重复CNN编码浪费时间，固定encoder已有更直接的缓存方案。
- **把全部原始地图转成memmap**：可行，但仍需约128GiB磁盘且反复做CNN；当前P1a优先缓存9.24GiB特征。若未来联合训练encoder，再单独研究原始分块读取，不误复用过期特征。
- **FP16/缩图/换模型/减少数据**：改变数值或研究设置，不是首轮内存修复需要的动作；以后作为独立性能实验。

## 5. 增量改动与验收顺序（均尚未执行）

| 顺序 | 文件/职责 | 必须通过的检查 |
|---|---|---|
| M0 | `train_offline.window_tensors`及测试 | 非恒定动作/状态、t>0、多个episode、k=1/5、末端/子目标边界；修复历史索引错位 |
| M1 | `wm/data.py`索引与逐episode读取；`wm/encoder.py`有界写缓存 | 校验和、缺失/损坏/超限文件；中断恢复；不同encoder/split不误复用 |
| M2 | `wm/train_offline.py`分batch取样/标准化/forward | 小样本对独立正确索引参考的特征、统计量、loss、更新一致；保持打乱与权重语义 |
| M3 | `wm/evaluate_prediction.py`与`wm/val_probe.py`共享流式rollout/episode聚合和checkpoint加载 | 分块误差、最后不满batch、paired CI与参考一致；正确读取v2 hidden/normalizer且不重载整train |
| M4 | 100→1000→9600回合规模预检 | 同资源预算、固定batch，缓存/短训练/完整验证的峰值不随全部地图线性增长；没有swap增长或ROS受扰 |
| M5 | 恢复P1实验 | 先登记新的train/val/test曝光协议，所有受索引缺陷影响的模型重新训练/评测；旧结果不覆盖 |

先实现并验证M0–M3，再做有限规模M4；全量缓存完成只代表工程里程碑，不能标训练完成。M4通过后才考虑完整200epoch预算；研究上先在原1000回合量级的正确train/val验证假设，再判断扩量是否有必要，不能把旧索引错误造成的现象归因数据不足。训练应有周期checkpoint与安全中止标记；没有实现恢复能力前不得声称可精确断点续训。

相关记录：[D29及后续决定](DECISIONS.md)、[实验审计](RESEARCH_EXPERIMENTS.md)、[主任务日志](agent_logs/20260928-research-foundation.md)。

## 2026-09-28 M5诊断实测增补

P1-RETRAIN-028完整epoch：no_action86、action107，300val全部一步/五步；RSS3.029GiB、USS2.415GiB、cgroup3.032GiB、GPU compute合计1482MiB、task swap0、宿主swap增量0，cache1.252GiB。训练+预测1031.71s，预算通过；没有9600回合正式重训或精确resume。长期epoch验证及P1a初步预测结果见[报告](agent_logs/20260928-p1-retrain-report.md)，不等于独立test或闭环验收。
