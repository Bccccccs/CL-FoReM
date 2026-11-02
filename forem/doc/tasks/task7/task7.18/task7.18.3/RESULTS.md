# task7.18.3 — 结果

状态：**review（尝试与有界测量完成；严格连续等价失败，候选未采用；交Claude复核）**。

## run-id t7.18.3-r1-20261021

负责人Codex，实际gpt-6.1-sol/high（宿主exec PID2997303参数核实）。推荐Codex GPT6.1sol/high（CUDA、RNG、连续数值核查），Claude Sonnet5.5/medium（复核证据与口径）。授权沿[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)、[SRC-0908](../../../../SOURCES.md#src-0908)，原始派发`forem/logs/task7/codex-dispatch-20261021-2130/t7.18.3/prompt.txt`已读；独立[日志](../../../../agent_logs/task7/task7.18/task7.18.3/20261021-codex-sac-speedup.md)。宿主时钟与派发文件21:30标签不一致，精确执行时间以commands.jsonl为准。

### 交付结论与采用状态

GPU异步校验Normal参数/样本约束，加上原逐算子目标soft_update的CUDA graph，在单次更新测量中有收益；**未通过规定的1000步连续loss/权重门，不采用**。原eager与自身在同初始完整状态、同批次与全部RNG下也不能通过该门；不能把这一事实视作候选通过或自行放宽门槛。生产SAC、训练、经验池、网络与配置均恢复/保持开工原字节，默认原eager路径；没有新增未经验证的训练性能开关。诊断CLI的`--candidate`也默认eager，生产LowerSAC不暴露候选选择方法。[SRC-0550](../../../../SOURCES.md#src-0550)、[SRC-0552](../../../../SOURCES.md#src-0552)、[SRC-0554](../../../../SOURCES.md#src-0554)

仅新增`forem/src/task7_lower/profile_speedup.py`、`speedup_candidates.py`与`tests/test_speedup.py`，供诊断复核；不改task7_sim/task7_upper，不改超参/batch/更新数/采样口径/精度/网络，不启动正式训练、不提交Git、不停止其他进程。最终[源码清单](../../../../../results/task7/t7.18.3-r1-20261021/source_final.json)、[快照](../../../../../results/task7/t7.18.3-r1-20261021/source_final)、[原始文件逐一字节核查](../../../../../results/task7/t7.18.3-r1-20261021/final-audit.json)证明原有20个lower源码/测试文件及配置全部一致。

### 设备、版本与输入

已有forem-dev，镜像sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430；物理GPU3 UUID GPU-29fe1ea1-d4e9-c14b-64f2-cb875ae92a0a映射cuda:0。开工无compute；只用该卡，Xorg不参与占用判定。torch2.7.1+cu128/CUDA12.8，参数/动量/经验池CUDA float32，原Adam step CPU；线程2、interop64（端到端runtime.json）。TF32 matmul=False/cudnn=True，cudnn deterministic=False/benchmark=False、deterministic_algorithms=False，保持原状，没有AMP。设备与精度来源[SRC-0550](../../../../SOURCES.md#src-0550)。

原始版本在[source_before](../../../../../results/task7/t7.18.3-r1-20261021/source_before)、[清单](../../../../../results/task7/t7.18.3-r1-20261021/source_before.json)。为隔离7.18.2/7.22并发修改，端到端仿真源码/配置固定在[workspace](../../../../../results/task7/t7.18.3-r1-20261021/workspace)及[e2e清单](../../../../../results/task7/t7.18.3-r1-20261021/e2e-input-manifest.json)；该清单早期生成后补齐了harness，前版保留为`e2e-input-manifest-pre-harness-update.json`，不是最终E2E清单。两组E2E使用同一冻结输入；只代表该快照，不能作为最终几何修复版训练放行证据。[SRC-0553](../../../../SOURCES.md#src-0553)

### 连续等价：失败证据

初轮随机审计fixture的deepcopy对照已失败，保留报告与scheduler warning；随后独立构造两个实例，完整load同一真实E2E checkpoint的SAC/optimizer/scheduler和回放状态，断言初始full_state逐元素相同，才执行连续1000次更新。同步74维、不同步75维，batch256，每步从两份独立private random.Random流产生同一索引，gather七字段逐元素对照；恢复并比较Python、NumPy、torch CPU与所有可见CUDA RNG。四组的初始状态、全部1000批次/索引/采样RNG与全局RNG均相同，loss/参数仍分歧。最终命令带`--fail-gate`，四项均exit1，完整1000步已记录，不是运行提前崩溃。[SRC-0551](../../../../SOURCES.md#src-0551)、[SRC-0552](../../../../SOURCES.md#src-0552)

|对照（各1000步）|loss首次不等|权重首次>1e−6|全轨迹权重最大差|结论|
|---|---:|---:|---:|---|
|eager-sync|5|9|0.03314245865|失败|
|candidate-sync|4|10|0.02946130745|失败|
|eager-async|4|7|0.03309722617|失败|
|candidate-async|4|8|0.03907056898|失败|

“eager”行为比较原eager与自身；“candidate”为eager与候选。下表为每一步所有参数的最大绝对差，并非loss容差；所有1000点、逐步loss差/相等标志、RNG标志在各`real-*-fullrng.json`和[CSV](../../../../../results/task7/t7.18.3-r1-20261021/trajectories.csv)，[门汇总](../../../../../results/task7/t7.18.3-r1-20261021/strict-gate-summary.json)。

|更新步|eager-sync|candidate-sync|eager-async|candidate-async|
|---:|---:|---:|---:|---:|
|1|7.4505806e-09|7.4505806e-09|7.4505806e-09|7.4505806e-09|
|10|0.00010180846|4.15463e-06|0.00015830249|3.2184646e-05|
|100|0.013164623|0.014614396|0.0098384861|0.010215405|
|250|0.017845482|0.018085646|0.019908456|0.017786397|
|500|0.028351925|0.020878363|0.030730976|0.030431373|
|750|0.03025789|0.025992718|0.029982338|0.038496383|
|1000|0.033142459|0.029461307|0.032997675|0.038473189|

[轨迹图PNG](../../../../../results/task7/t7.18.3-r1-20261021/trajectories.png) · [SVG](../../../../../results/task7/t7.18.3-r1-20261021/trajectories.svg)。没有把单次恢复SRC-0474的≤1e−6外推为长期保证，也未定位具体非确定性算子。初轮真实回放仅CUDA RNG复查的`real-eager-self-1000.json`、`real-candidate-1000.json`仍保留；以四份fullrng报告为最终完整RNG证据。

端到端比较中，两变体各2047组采样索引序列完全相同；同步/异步loss首次分歧分别update2/5，Transition全部字段的规范序列化摘要均前3批相同、第4批起不同（同步调用数9/10，不同步10/10），最终最大权重差分别0.160425603/0.20740217。同步最终CUDA RNG摘要不同，不同步相同；学习/分段调用轨迹已不同，不能声称端到端RNG/Transition精确等价。摘要不同已足以否定相同，未用摘要替代逐元素验收宣称通过。[端到端对照](../../../../../results/task7/t7.18.3-r1-20261021/e2e-comparison.json)、[SRC-0553](../../../../SOURCES.md#src-0553)。

### 单次更新与E256端到端

独立微基准各20次预热后300样本（不含采样），eager p50/p95=13.447001/13.548499ms，候选11.934905/11.985254ms；耗时约降11.24%。CUDA event p50=13.395296/11.898464ms，同stream event包含host提交空隙，非内核累计。原始[基线](../../../../../results/task7/t7.18.3-r1-20261021/eager-timing.json)、[候选](../../../../../results/task7/t7.18.3-r1-20261021/candidate-timing.json)，[profiler trace](../../../../../results/task7/t7.18.3-r1-20261021/eager-profiler.trace.json)，依据[SRC-0551](../../../../SOURCES.md#src-0551)。

每个E2E run从头seed4718、E256，**2304条有效动作转移（不是2304次E256批调用）/2047次更新**，原规则#258首次更新、1000条随机预热、每条有效转移一次更新，原batch256/回放容量100000/两种74/75维网络不变。走原training.train（普通日志/账本fsync/真实池/复位/采样搬运/推理/更新/插入/最终完整检查点），诊断子类仅在候选run替代更新。额外保存每次Transition摘要及每步loss/索引，额外审计开销包含在wall中并单列；最终检查点/summary/runtime/config/learning/interactions齐全，目录`e2e-<path>-<variant>/`。E2E样本未触及250k周期验证，未新做正式验证。[SRC-0553](../../../../SOURCES.md#src-0553)

|路径/变体|update p50/p95 (ms)|端到端wall (s)|转移/wall秒|审计(s)|最大reset(s)|末保存(s)|
|---|---:|---:|---:|---:|---:|---:|
|eager-sync|13.5205/13.7371|104.112781|22.129848|1.8973|44.8581|10.1212|
|candidate-sync|11.8705/12.1938|103.455526|22.270439|2.3457|44.9259|9.6301|
|eager-async|13.4132/13.7408|98.650586|23.355158|2.0830|44.5533|9.1635|
|candidate-async|11.7419/12.1427|96.065885|23.983540|2.3335|44.5521|9.0459|

|分项累计wall秒|eager-sync|candidate-sync|eager-async|candidate-async|
|---|---:|---:|---:|---:|
|reset|47.1066|48.7686|44.7001|44.6985|
|candidates|6.5580|7.5407|4.2078|5.0472|
|observation|0.8408|0.9342|0.9163|0.9146|
|inference|0.1162|0.1180|0.1191|0.1177|
|environment_step|6.8825|7.5644|7.4708|7.4780|
|replay_sample|0.9789|0.9837|0.9673|0.9793|
|replay_insert|1.1519|1.1544|1.1289|1.1486|
|sac_update|27.9898|24.6720|27.7464|24.4743|
|interaction_ledger|0.1044|0.0820|0.1114|0.0868|
|logging|0.0004|0.0004|0.0004|0.0004|
|checkpoint|10.1212|9.6301|9.1635|9.0459|
|未分项主循环/诊断等余量|2.2622|2.0069|2.1187|2.0745|

各项n/p50/p95/p99/max、模拟秒/尝试/提交/DLS/拒绝与GPU峰值在各E2E JSON。端到端吞吐含冷启动/保存，不能直接和被停正式长训48.7转移/s比较；不同学习轨迹导致复位/地图拒绝/调用数不同，不能把两run wall差都归因优化。峰值约27.9GB，原设备与计数口径均在报告中。

### 全步CUDA graph、组件与回归

直接将整个原更新放入CUDA graph，eager捕获失败（退出上下文的二次错误遮蔽首错，未声称定位）；去掉Normal host校验同步后，明确失败于原Adam `capturable=False`。两个探针exit2，报告[capture-eager](../../../../../results/task7/t7.18.3-r1-20261021/capture-eager.json)、[capture-async-checks](../../../../../results/task7/t7.18.3-r1-20261021/capture-async-checks.json)；安装版`Optimizer._cuda_graph_capture_health_check`原文在日志。不能据此说CUDA graph原则上不可实现。未在严格门连参考自身都失败的情况下继续变换优化器/LR或大规模compile尝试；没有改foreach/fused/精度。[SRC-0554](../../../../SOURCES.md#src-0554)

原lower全套加3项新测试：**18 passed，3个原路径warning，exit0**，[JUnit](../../../../../results/task7/t7.18.3-r1-20261021/lower-tests.xml)、[日志](../../../../../logs/task7/t7.18.3-r1-20261021/lower-tests-final.log)。新增测试分别核对候选仅显式可用/生产不暴露、batch256的1000次采样输出及RNG精确一致、1000次目标soft_update逐元素精确且load状态后仍正确。组件通过不能代替连续更新通过。候选异步assert保留了Normal约束，但无效输入异常类型/交付时机改变，生产异常恢复未验收，亦不采用。[SRC-0554](../../../../SOURCES.md#src-0554)

### 5M单趟墙钟：条件推导，不是重训放行

[projection.json](../../../../../results/task7/t7.18.3-r1-20261021/projection.json)保留全部秒单位输入、公式与两个独立worker假设。令N=5,000,000、Nu=4,999,743，n=2304、U=2047，W=E2E总wall，Tu=其中更新累计wall，S_trial=此次末保存wall；R取本短窗最大一次reset，作为只摊销一次的工程选择，其余reset仍在非更新成本内。使用：

`T = R + Nu*(Tu/U) + (N/n)*(W-R-S_trial-Tu) + 21*S_full + 20*V`（秒）。

这样不重复线性放大冷reset/小容量末保存，也补偿短窗前257次没有更新。每项其余成本、审计与首次update/首次候选开销按本短窗分布外推，**不是真实工期上界**。S_full=124.966s是[SRC-0475](../../../../SOURCES.md#src-0475)按全池planner与IO大小线性增长的历史推导，非本轮实测；V同步116.178s/异步562.856s来自同条历史100图验证。21次保存/20次验证沿原5M预算；新几何下周期成本、最终回放/缓存/长期策略分布和资源争用尚未测。[SRC-0553](../../../../SOURCES.md#src-0553)

|路径/变体|仅更新p50×Nu (h)|含历史周期成本的条件单趟(h)|
|---|---:|---:|
|eager-sync|18.7775|33.1227|
|candidate-sync|16.4860|32.7307|
|eager-async|18.6285|33.0541|
|candidate-async|16.3074|31.3201|

仅在未来有两个独立同成本worker且额外资源争用为0的条件下，原路径全局max≈33.1227h、累计worker≈66.1769h；候选示例max≈32.7307h、累计≈64.0508h。候选未等价、轨迹不同，上述不是已证明提速或时限承诺；修复最终版完整成本仍待核查，不据此启动正式训练、不改5M/更新频率或增加预算。

### 全部有界运行命令、退出码与预算

宿主公共入口：`python3 -u forem/logs/task7/t7.18.3-r1-20261021/run.py NAME <下表命令>`。run.py实际`sg docker -c`进入已有forem-dev，设置CUDA_VISIBLE_DEVICES=3、PYTHONPATH=/root/mm_husky_ws/src、PYTHONDONTWRITEBYTECODE=1、OMP_NUM_THREADS=2、MKL_NUM_THREADS=2、工作目录/root/mm_husky_ws，`timeout --signal=TERM --kill-after=5 590`。实际展开argv与各命令ISO时间在[commands.jsonl](../../../../../logs/task7/t7.18.3-r1-20261021/commands.jsonl)，完整输出见下表链接；原始输入探针/汇总/复核脚本在同logs目录。

|NAME（完整输出为NAME.log）|退出码|调用wall(s)|实际容器命令（公共前缀见正文）|
|---|---:|---:|---|
|[eager-self-1000](../../../../../logs/task7/t7.18.3-r1-20261021/eager-self-1000.log)|0|36.064818|`python3 -B -u -m task7_lower.profile_speedup equivalence --steps 1000 --output results/task7/t7.18.3-r1-20261021/eager-self-1000.json`|
|[inspect-torch](../../../../../logs/task7/t7.18.3-r1-20261021/inspect-torch.log)|0|1.816585|`python3 -B -c 'import inspect,torch; from torch.distributions import Normal,Distribution,constraints; print(torch.__version__); print(inspect.getsource(Normal.__init__)); print(inspect.getsource(Distribution.__init__)); print(inspect.getsource(type(constraints.real))); print(inspect.getsource(torch.nn.utils.clip_grad_norm_))'`|
|[eager-timing](../../../../../logs/task7/t7.18.3-r1-20261021/eager-timing.log)|0|9.327444|`python3 -B -u -m task7_lower.profile_speedup timing --steps 300 --output results/task7/t7.18.3-r1-20261021/eager-timing.json`|
|[async-equivalence](../../../../../logs/task7/t7.18.3-r1-20261021/async-equivalence.log)|0|34.162630|`python3 -B -u -m task7_lower.profile_speedup equivalence --candidate async_checks_target_graph --steps 1000 --output results/task7/t7.18.3-r1-20261021/async-equivalence.json`|
|[candidate-timing](../../../../../logs/task7/t7.18.3-r1-20261021/candidate-timing.log)|0|8.876473|`python3 -B -u -m task7_lower.profile_speedup timing --candidate async_checks_target_graph --steps 300 --output results/task7/t7.18.3-r1-20261021/candidate-timing.json`|
|[eager-profiler](../../../../../logs/task7/t7.18.3-r1-20261021/eager-profiler.log)|0|8.776142|`python3 -B -u -m task7_lower.profile_speedup profile --output results/task7/t7.18.3-r1-20261021/eager-profiler.json`|
|[e2e-eager-sync](../../../../../logs/task7/t7.18.3-r1-20261021/e2e-eager-sync.log)|0|107.617941|`python3 -B -u -c 'import sys; sys.path.insert(0,"results/task7/t7.18.3-r1-20261021/workspace/src"); from task7_lower.profile_speedup import main; main()' endtoend --candidate eager --steps 2304 --dim 74 --config results/task7/t7.18.3-r1-20261021/workspace/config/task7/lower_train.json --output results/task7/t7.18.3-r1-20261021/e2e-eager-sync.json`|
|[e2e-candidate-sync](../../../../../logs/task7/t7.18.3-r1-20261021/e2e-candidate-sync.log)|0|107.065087|`python3 -B -u -c 'import sys; sys.path.insert(0,"results/task7/t7.18.3-r1-20261021/workspace/src"); from task7_lower.profile_speedup import main; main()' endtoend --candidate async_checks_target_graph --steps 2304 --dim 74 --config results/task7/t7.18.3-r1-20261021/workspace/config/task7/lower_train.json --output results/task7/t7.18.3-r1-20261021/e2e-candidate-sync.json`|
|[real-eager-self-1000](../../../../../logs/task7/t7.18.3-r1-20261021/real-eager-self-1000.log)|0|38.818851|`python3 -B -u -m task7_lower.profile_speedup equivalence --candidate eager --steps 1000 --checkpoint results/task7/t7.18.3-r1-20261021/e2e-eager-sync/final.pt --output results/task7/t7.18.3-r1-20261021/real-eager-self-1000.json`|
|[real-candidate-1000](../../../../../logs/task7/t7.18.3-r1-20261021/real-candidate-1000.log)|0|37.522786|`python3 -B -u -m task7_lower.profile_speedup equivalence --candidate async_checks_target_graph --steps 1000 --checkpoint results/task7/t7.18.3-r1-20261021/e2e-eager-sync/final.pt --output results/task7/t7.18.3-r1-20261021/real-candidate-1000.json`|
|[e2e-eager-async](../../../../../logs/task7/t7.18.3-r1-20261021/e2e-eager-async.log)|0|102.160316|`python3 -B -u -c 'import sys; sys.path.insert(0,"results/task7/t7.18.3-r1-20261021/workspace/src"); from task7_lower.profile_speedup import main; main()' endtoend --candidate eager --steps 2304 --dim 75 --config results/task7/t7.18.3-r1-20261021/workspace/config/task7/lower_train.json --output results/task7/t7.18.3-r1-20261021/e2e-eager-async.json`|
|[e2e-candidate-async](../../../../../logs/task7/t7.18.3-r1-20261021/e2e-candidate-async.log)|0|99.710569|`python3 -B -u -c 'import sys; sys.path.insert(0,"results/task7/t7.18.3-r1-20261021/workspace/src"); from task7_lower.profile_speedup import main; main()' endtoend --candidate async_checks_target_graph --steps 2304 --dim 75 --config results/task7/t7.18.3-r1-20261021/workspace/config/task7/lower_train.json --output results/task7/t7.18.3-r1-20261021/e2e-candidate-async.json`|
|[real-eager-sync-fullrng](../../../../../logs/task7/t7.18.3-r1-20261021/real-eager-sync-fullrng.log)|1|39.674466|`python3 -B -u -m task7_lower.profile_speedup equivalence --candidate eager --steps 1000 --fail-gate --checkpoint results/task7/t7.18.3-r1-20261021/e2e-eager-sync/final.pt --output results/task7/t7.18.3-r1-20261021/real-eager-sync-fullrng.json`|
|[real-candidate-sync-fullrng](../../../../../logs/task7/t7.18.3-r1-20261021/real-candidate-sync-fullrng.log)|1|39.775292|`python3 -B -u -m task7_lower.profile_speedup equivalence --candidate async_checks_target_graph --steps 1000 --fail-gate --checkpoint results/task7/t7.18.3-r1-20261021/e2e-eager-sync/final.pt --output results/task7/t7.18.3-r1-20261021/real-candidate-sync-fullrng.json`|
|[real-eager-async-fullrng](../../../../../logs/task7/t7.18.3-r1-20261021/real-eager-async-fullrng.log)|1|39.423966|`python3 -B -u -m task7_lower.profile_speedup equivalence --candidate eager --steps 1000 --dim 75 --fail-gate --checkpoint results/task7/t7.18.3-r1-20261021/e2e-eager-async/final.pt --output results/task7/t7.18.3-r1-20261021/real-eager-async-fullrng.json`|
|[real-candidate-async-fullrng](../../../../../logs/task7/t7.18.3-r1-20261021/real-candidate-async-fullrng.log)|1|38.021471|`python3 -B -u -m task7_lower.profile_speedup equivalence --candidate async_checks_target_graph --steps 1000 --dim 75 --fail-gate --checkpoint results/task7/t7.18.3-r1-20261021/e2e-eager-async/final.pt --output results/task7/t7.18.3-r1-20261021/real-candidate-async-fullrng.json`|
|[lower-tests-final](../../../../../logs/task7/t7.18.3-r1-20261021/lower-tests-final.log)|0|24.953974|`python3 -B -m pytest -q -p no:cacheprovider src/task7_lower/tests --junitxml=results/task7/t7.18.3-r1-20261021/lower-tests.xml`|
|[summarize-evidence](../../../../../logs/task7/t7.18.3-r1-20261021/summarize-evidence.log)|0|11.434996|`python3 -B -u logs/task7/t7.18.3-r1-20261021/summarize.py`|
|[capture-eager](../../../../../logs/task7/t7.18.3-r1-20261021/capture-eager.log)|2|5.225016|`python3 -B -u logs/task7/t7.18.3-r1-20261021/capture_probe.py --candidate eager --output results/task7/t7.18.3-r1-20261021/capture-eager.json`|
|[capture-async-checks](../../../../../logs/task7/t7.18.3-r1-20261021/capture-async-checks.log)|2|5.276338|`python3 -B -u logs/task7/t7.18.3-r1-20261021/capture_probe.py --candidate async_checks --output results/task7/t7.18.3-r1-20261021/capture-async-checks.json`|

命令求和**795.705163s（13.261753分钟）**，最长**107.617941s**，20条，均在单条10分钟/累计120分钟内；CPU汇总与测试少量重叠，求和保守。初轮测量生成命令exit0只代表报告生成，passed=False仍是失败；最终4个fullrng命令exit1明确严格门失败，capture两次exit2为捕获失败。没有把这些红结果转成通过。[SRC-0554](../../../../SOURCES.md#src-0554)

开工只读核查命令为git status/branch、nvidia-smi compute与GPU UUID查询、ps、docker inspect、规定文档与源码读取，整体返回0；输出摘录在独立日志。收尾宿主`python3 forem/logs/task7/t7.18.3-r1-20261021/final_audit.py` exit0，生成final-audit/final-compute.csv/final-git-status。首次宿主内联收尾脚本exit1（宿主无psutil，导入即失败、未执行核查），改用标准库/proc后通过；未安装依赖。文档与证据导出命令为本目录write_report.py及stdlib核查，不发生环境转移/GPU更新。

### 交接与待决定

- 当前负责人Codex；交Claude review。已完成尝试、两变体各1000步严格对照、每组2304转移E256测量、组件/回归、5M条件推导；证据与失败均保留。
- **待决定：连续1000步loss必须逐元素相同及权重≤1e−6的口径，在当前原GPU默认路径连自对照都不能满足；需复核验收口径或另行明确可改变的确定性条件。** 本任务没有放宽标准，没有擅自开deterministic/关TF32/改AMP；仅停止优化采用与更深的生产路径改造，其余交付已完成。
- 原默认训练路径仍可用，但本任务不恢复旧STOP run、不启动从头5M、不提供修复最终几何版放行。7.18.2最终代码/回归及正式重训决定由原负责人处理。
- 2026-10-21T21:44:36.694636+08:00收尾：GPU3无compute，本任务无训练/测量worker遗留；GPU1其他compute保留。后续先读本文、独立日志和final-audit，再复核严格门/快照适用性；如要验证新方案仍须同口径，不把局部组件精确当长轨迹通过。

## Claude复核与关闭（2026-10-21 22:00）

- 候选更新p50 13.447→11.935 ms（约11%）；Codex设定的“1000步连续等价”验收连原eager自比也失败，属Claude派发口径错误（GPU非确定性逐步累积），非优化缺陷。收益小，用户决定不采用（SRC-0909），生产代码未改。closed。
