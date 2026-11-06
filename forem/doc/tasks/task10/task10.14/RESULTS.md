# task10.14 结果与交接

2026-11-03 · **review，交决策者审核**。执行与必要复核已完成；本清单未观察到200次在线更新改善选点。三策略36/36回合、0缺失，trained0/12、initial0/12、uniform10/12，真实123决策/0更新，outer55分11.918秒。依据均为[SRC-T10-028](../../../SOURCES.md#src-t10-028)，入口/夹具为[SRC-T10-027](../../../SOURCES.md#src-t10-027)，授权为[SRC-T10-026](../../../SOURCES.md#src-t10-026)。

## 1. 实际执行与冻结

执行负责人Codex；独立CPU审计task10.14.1由Codex子Agent完成，父核验原件后统一交接。两者实际平台标识GPT-6，具体变体/推理档位无法核实，记未知；推荐GPT6.1sol/medium、Sonnet5.5/medium，因需核对完整模型加载、隐藏记忆、配对与统计。推荐不当作实际配置。执行者有自主选模与先建档委派权限，本轮不再派发后续研究。

工作树`/home/ybc/projects/CL-FoReM-task10`，分支`codex/task10-upper-wm`，HEAD `91f538cf2ee10bebffd6b643d5c908fa0d419ced`，加本次未提交入口/审计代码。既有未提交修改保留。精确执行代码见[manifest](../../../../results/task10/t10-eval-20261103-s101/manifest.json)的files和frozen-code副本；post-run audit_v2与diagnostics另记哈希。未提交、未推送、未合并。

run-id `t10-eval-20261103-s101`；容器`forem-task10-runtime`，镜像`sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430`；GPU物理1/容器CUDA0，workerPID820、宿主launcher223745。实际torch/CUDA/cuDNN/driver/线程/确定性配置及tensor设备见[entry-check](../../../../results/task10/t10-eval-20261103-s101/entry-check.json)。源训练目录只读打开，结束时全部源文件hash不变。GPU2他人任务未动，本轮结束后GPU1无compute、本轮worker已退出；容器保活。

共用冻结B3-5M seed4718、sync_v5/cbl_continue、primitive-obb-v1、float32、单环境、场景seed101。性能配置沿用risk_chunk256/observation_chunk128/route-raster复用/DLS CUDA graph；无奖励、观测、动作、终止或求解器变更。uniform每场景独立CUDA generator102；模型策略eval/no_grad，按有效最大logit、平局最小索引，每回合清空VCM记忆/历史。

|输入|文件SHA256|完整tensor state SHA256|
|---|---|---|
|trained（final.actor.pt，200更新）|`0fcd4e68c3aaeb85247380ab9e1e7b5a15f605c89880dab42016874d56c84a71`|`d8012d9a14aa6720f3de5c237668c8a6c1f1bd4a89771bdfa271363a46d712c8`|
|initial（initial-learner.pt → learner.model，0更新）|`9bf4083734120165a7f7d535e0b97db43479974ff4062332b3119b793cf0d9cb`|`f84740d7dd1827c2c84e20dbbb576afe3b98e50a7ce4d0bcaf2e26080d363f15`|
|B3 final.actor.pt（5M seed4718）|`3db11d9f00317849e35a523d66d0935ebc2e3567d82c519ccc42f3d8de42f7ae`|`993825e4e24872971e208ecf77159d63d7951721af1d04a91314658409b8c776`|

manifest SHA256 `672d11e93ad1c9dfcdee684d837190c7449942d5c3d8351c84a7a3e04a94dbee`；配置online_trial.json SHA `d123ced1866fe40a675f02b672b3aad49a4566b5cab2cb4055670edebd2fbfb7`。地图来自冻结主仓cube-pool-v2，只取validation，sparse00004–00009与standard00000–00005各6张，ID排序并交替，场景内策略顺序循环轮换，旧4张稀疏图排除；与train的ID及几何hash互斥。地图完整entry/sidecar hash、执行次序和36预期身份均在启动前manifest落盘。

## 2. 验证与成本

CPU全回归最终155passed/2条件skipped/44.37s；最终专项22passed/3.95s；后加诊断4专项、审计v2 tuple原件3专项均通过。未执行额外GPU夹具或新采集，GPU入口用旧batch-000008真实观测前向，0真实/0更新；完整127张量strict加载、raw learner与评估模型输出、记忆复位输出严格一致，独立CUDA RNG核验通过。

早期失败保留：pytest临时目录已有其他UID所有权，改专属basetemp；旧lower测试默认宿主路径造成11失败，加TASK10_ARTIFACT_ROOT=/reference重验通过；fake夹具漏timing字段已补。独立静态审查发现replay_fields接口/原始grid存储两错，GPU前修复并加实际schema夹具。真实评估没有工程异常。

唯一启动15:01:22.668413+08，绝对截止16:31:22.668413+08，实际15:56:34.586509+08退出，rc0，不重跑/不补场景。预算36回合/5400真实决策/0更新/5400s，全部遵守。GPU入口10.668243s计同窗，outer3311.918092s，worker退出记录3310.930164s（最后budget flush3310.928055s）；回合累计3298.841563s。单worker顺序运行，所以无并行累计成本放大。其余worker开销约1.42s，outer与worker约0.99s为监督/进程退出差。

|策略|决策数|失败尝试|尝试仿真秒|提交仿真秒|回合墙钟秒|
|---|---:|---:|---:|---:|---:|
|trained|52|100|52.749995|47.750019|1264.789200|
|initial|52|100|52.749995|47.750019|1261.995311|
|uniform|19|40|208.250335|206.249499|772.057052|

尝试/提交时间来自Core原始float32累积，不能当wall。父由整数substeps×0.05s另复算，最大尝试累积差0.000071335s、提交差0.000144196s，保留原记录，不修改终止与结果。

|策略|复位含首次推演wall秒|后续候选推演wall秒|真实执行wall秒|推理wall秒|落盘wall秒|
|---|---:|---:|---:|---:|---:|
|trained|377.545|791.584|80.674|0.409|2.567|
|initial|373.736|791.568|80.952|0.401|2.549|
|uniform|374.108|112.380|269.110|0.008|4.127|

复位包含场景采样/路线/初始观测及首次候选推演；raw initial_reset_timing另分candidate_seconds与rollout_seconds。上表不是嵌套GPU-only微基准，采用同步墙钟，不把失败早停当性能优势。

## 3. 三策略与配对结果

|策略|完整/预期|严格成功/分母|缺失|sparse|standard|
|---|---:|---:|---:|---:|---:|
|trained|12/12|0/12（0%）|0|0/6|0/6|
|initial|12/12|0/12（0%）|0|0/6|0/6|
|uniform|12/12|10/12（83.33%）|0|5/6|5/6|

严格成功配对trained对initial：**胜0/负0/平12/缺失0**；对uniform：**胜0/负10/平2/缺失0**。没有不完整配对；分母不混入预热/旧4图/训练成功率。

终止主原因：trained及initial各failure_limit5、stall_limit7；uniform strict_success10、failure_limit2。三组均0决策上限、0时间上限、0完成但带失败、0其他工程原因。全部并发trigger保存在回合JSON和raw replay，不用单一reason抹掉多触发。

以下每行一个预登记回合。失败列为raw attempts按Core优先级归因；“无尝试停滞”不是IK失败。所有complete=true、missing=0。地图简写sparse/standard后的数字与manifest完整ID后缀一致。

|地图|策略|严格成功|终止/失败类型|失败尝试|决策|尝试秒|墙钟秒|
|---|---|---|---|---:|---:|---:|---:|
|sparse 00004|trained|否|failure_limit；self_collision:20|20|2|7.100000|72.100|
|sparse 00004|initial|否|failure_limit；self_collision:20|20|2|7.100000|70.381|
|sparse 00004|uniform|否|failure_limit；base_collision:20|20|2|17.700012|62.978|
|standard 00000|initial|否|stall_limit；无尝试停滞|0|6|1.350000|197.278|
|standard 00000|uniform|否|failure_limit；ik_rejected:20|20|2|29.050055|100.413|
|standard 00000|trained|否|stall_limit；无尝试停滞|0|6|1.350000|197.011|
|sparse 00005|uniform|是|strict_success；无失败|0|2|24.050055|82.730|
|sparse 00005|trained|否|failure_limit；self_collision:20|20|1|5.250002|46.988|
|sparse 00005|initial|否|failure_limit；self_collision:20|20|1|5.250002|46.560|
|standard 00001|trained|否|failure_limit；self_collision:20|20|2|5.500001|54.443|
|standard 00001|initial|否|failure_limit；self_collision:20|20|2|5.500001|54.025|
|standard 00001|uniform|是|strict_success；无失败|0|2|22.700050|78.920|
|sparse 00006|initial|否|failure_limit；self_collision:20|20|1|3.949998|50.660|
|sparse 00006|uniform|是|strict_success；无失败|0|2|24.350056|90.939|
|sparse 00006|trained|否|failure_limit；self_collision:20|20|1|3.949998|50.977|
|standard 00002|uniform|是|strict_success；无失败|0|1|7.349996|30.588|
|standard 00002|trained|否|stall_limit；无尝试停滞|0|7|2.650000|134.332|
|standard 00002|initial|否|stall_limit；无尝试停滞|0|7|2.650000|133.702|
|sparse 00007|trained|否|failure_limit；self_collision:20|20|1|3.749999|42.868|
|sparse 00007|initial|否|failure_limit；self_collision:20|20|1|3.749999|42.821|
|sparse 00007|uniform|是|strict_success；无失败|0|2|28.200071|103.990|
|standard 00003|initial|否|stall_limit；无尝试停滞|0|6|2.899999|100.604|
|standard 00003|uniform|是|strict_success；无失败|0|1|8.099995|30.615|
|standard 00003|trained|否|stall_limit；无尝试停滞|0|6|2.899999|100.814|
|sparse 00008|uniform|是|strict_success；无失败|0|1|6.899996|27.545|
|sparse 00008|trained|否|stall_limit；无尝试停滞|0|6|1.950000|99.304|
|sparse 00008|initial|否|stall_limit；无尝试停滞|0|6|1.950000|98.993|
|standard 00004|trained|否|stall_limit；无尝试停滞|0|6|6.699996|141.379|
|standard 00004|initial|否|stall_limit；无尝试停滞|0|6|6.699996|141.188|
|standard 00004|uniform|是|strict_success；无失败|0|1|9.450000|46.461|
|sparse 00009|initial|否|stall_limit；无尝试停滞|0|8|9.349999|207.690|
|sparse 00009|uniform|是|strict_success；无失败|0|2|23.700054|88.654|
|sparse 00009|trained|否|stall_limit；无尝试停滞|0|8|9.349999|207.438|
|standard 00005|uniform|是|strict_success；无失败|0|1|6.699996|28.226|
|standard 00005|trained|否|stall_limit；无尝试停滞|0|6|2.300000|117.136|
|standard 00005|initial|否|stall_limit；无尝试停滞|0|6|2.300000|118.093|

## 4. 行为与失败诊断

trained和initial各52/52次选择slot12（固定inplace），52次均有其他有效候选，平均有效候选8.403846，不是mask只留原地。12/12场景完整选点序列和全部共享raw输入/物理执行结果一致；52个共享状态logits全部变化，最大绝对差1.235067，但argmax未变。uniform19次决策没有选12；其分布只是固定seed102的这次观测，不能据此声称uniform一般不会选原地。

两模型各5个回合触发失败上限，每回合20次self_collision，共100次；另7个回合无失败但反复原地，合计35/52决策为0尝试（7×5），触发stall_limit。两者平均路线完成比例均14.3593%。uniform平均92.6408%，sparse00004为20次base_collision，standard00000为20次ik_rejected（该图路线约96.83%但不满足严格成功）。失败按IK拒绝→底盘→机械臂环境碰撞→自碰撞优先级复算，未把IK目标当实际状态。

既有训练updates.jsonl按连续50更新复算critic均值0.203412→0.159386→0.156449→0.147325；actor loss、梯度范数及alpha曲线在independent-diagnostics.json。该数值变化与本轮logits变化均不代表策略行为改善。

## 5. 原件、复算与验收

[原件目录](../../../../results/task10/t10-eval-20261103-s101/)；[独立审计v2](../../../../results/task10/t10-eval-20261103-s101/independent-audit-v2.json)为verified_complete、issues=[]；[独立诊断](../../../../results/task10/t10-eval-20261103-s101/independent-diagnostics.json)；[父JSON复算](../../../../results/task10/t10-eval-20261103-s101/parent-recompute.json)；[父逐原件复算](../../../../results/task10/t10-eval-20261103-s101/parent-raw-recompute.json)。训练目录、模型、地图和执行文件119项hash一致，36初态原件、123 raw/JSON决策与1..123写前预留连续无漏重，全部权重冻结，0更新。

首份独立audit v1误将tuple map_ids与list直接比较，产生123同类schema误报；冻结v1脚本、independent-audit.json及日志保留。修正版audit_v2只增加list归一化，未改执行代码或原件，3专项通过，rc0。父直接读取全部123原件逐Tensor校验，独立复现12完整同初态和trained/initial完整轨迹一致。

已执行的唯一真实命令（禁止重复启动）：

```bash
python3 -u forem/scripts/task10_validation_launch.py --run forem/results/task10/t10-eval-20261103-s101 --commit 91f538cf2ee10bebffd6b643d5c908fa0d419ced
```

可只读重算（均已执行rc0，不产生GPU/新回合）：

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 /workspace/scripts/task10_validation_audit_v2.py --run /workspace/results/task10/t10-eval-20261103-s101 --reference /reference/source --output /workspace/results/task10/t10-eval-20261103-s101/independent-audit-v2.json'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 /workspace/scripts/task10_validation_diagnostics.py --run /workspace/results/task10/t10-eval-20261103-s101 --output /workspace/results/task10/t10-eval-20261103-s101/independent-diagnostics.json'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 /workspace/results/task10/t10-eval-20261103-s101/parent_raw_recompute.py'
```

审计/诊断不读取aggregate summary作为统计输入。v2脚本SHA `25099fb719e2a156ecc661417c863886def7a1362a46349ebbcb5e89d115eaf3`，诊断脚本SHA `6d6d498ab33d5bbab2f186c7689de568d86151da53cda910e1a15a46587c4a63`；输出SHA见run/evidence-hashes.json。命令/退出码及CPU日志详见[独立子结果](task10.14.1/RESULTS.md)和[父日志](../../../agent_logs/task10/task10.14/20261103-codex-execution.md)。

工程验收：本轮授权范围内的入口、唯一有界执行、原件与复算完成；**收益验收：未观察到改善**。任务保持review供决策者最终审核，不以工程通过替代收益判断。

## 6. 交给决策者

这12个验证场景不支持200次在线更新改善选点：trained与initial全部选点/真实轨迹相同，且严格成功均低于本次uniform读数。这里的“低于”是固定清单观察差异，没有跨种子统计显著性或泛化保证。

建议**优先做上层评分与学习信号的有界排查，再决定增加训练预算**：核对为何inplace在所有可选其他候选的状态中始终排首，已有self_collision和零尝试停滞样本怎样影响回报、Q和actor排序。当前加载/模式/记忆/mask/RNG/配对均已通过，不应把初始策略重新初始化或重跑来改善读数。尚未定位到具体实现bug，也不能断言多训练无效；200更新少的事实不能替代本轮行为证据。上述是工程建议，未实施新诊断/调参/训练，后续需要决策者另行派发。

单训练种子/12个validation场景；未跑test池/未启动task11/未调整参数或预算。训练完成和数值loss变化不作为任务改善结论。无本轮运行任务需接管；下一步仅审核本交付和决定后续排查/训练范围。

历史：2026-11-03首版为设计未执行，协议见SRC-T10-025；本次执行取代该状态描述，历史设计事实保留。

## 决策者验收 · 2026-11-03
独立CPU复跑审计v2为verified_complete、issues=[]。工程交付验收done；本清单收益未改善，0/12对0/12与10/12。下一步task10.15先诊断原地排序与学习目标，再决定扩大训练。task10整体继续review。[审核依据](../../../SOURCES.md#src-t10-030)。
