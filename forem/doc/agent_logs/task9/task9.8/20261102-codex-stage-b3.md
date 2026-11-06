# task9.8 B3 TMPDIR修复后继续

负责人Codex；实际底层模型/强度未知。推荐GPT6.1sol/high、Sonnet5.5/high，因需核验回放非干扰和独立覆盖判分。

用户已在异步问答明确允许TMPDIR修复、验证后继续OFF；不是自动重试。run-id `t9.8-B3-20261102T163355+0800`，当前2026-11-02T16:33:55.522994+08:00，原19:02+08硬截止不变。累计既往实际回合0、GPU157.427090秒、新输出5837311bytes。登记剩余墙钟8884.477秒、GPU10642.572910秒、输出1067904513bytes；新目录原子创建，旧两run不写。

修复TMPDIR=/output/tmp（新run内计费），零回合验证补临时文件写读删、torch._dynamo和distributed.nn.jit.instantiator实际动态导入；保留前次代码/日志/账本。后续仍按五次完整evaluate、先两例覆盖与精确门。C独立。

2026-11-02T16:35:20.342081+08:00：A独立副本重核PASS/30/124，原parent-verification前后hash一致；新正式镜像TMPDIR写读删和Adam动态模块import均PASS/rc0、26合成回归rc0，首OFF已启动，模型加载合同待本轮loaded证据。队列host PID3699512；监控B3日志gpu-monitor.jsonl与queue-state，手停写本run STOP（仅本容器，保留排空），禁止自行追加/重试。

16:36 +08：首OFF loaded.json确认5M、actor_tensors_equal、policy/critic cuda:0、torch2.7.1+cu128、threads2等实际设备/flags；GPU UUID由隔离inspect及compute PID3699828对应GPU2确认。首16个启动、15个结束，尚无目标trace（目标在validation offset48及transfer offset0）。只读/root产生可选torch kernel cache无法创建警告，运行继续、实际输出正常；本轮保留原计算/flags且不在OFF/ON之间改变cache路径，将警告列为性能条件限制。

2026-11-02T16:52:04.997614+08:00：OFF原196已产完整evaluation及两目标coverage，row53动作107/子步213/commit213/拒绝0、row8动作84/子步148/commit128/拒绝20；两例begin各1，事件430/319，独立coverage PASS。原始终态/历史差异待独立汇总，不以OFF单侧判非干扰；ON仍须完整覆盖后精确比较，③不得先启动。

2026-11-02T17:10:11.176249+08:00：ON完整196/rc0，两侧独立coverage及749事件精确比较PASS，gate.json已通过，父再从原evaluate row53/row8重算coverage+逐项compare且核trace SHA，写parent-gate-verification.json；非C。实际前两次392完成，第三次4718剩8已按顺序放行。两次wall分别[1033.8905699923635, 1055.092065487057]秒。

2026-11-02T17:27:54.480049+08:00：第三次完整196/rc0、八目标coverage均PASS；累计588完整，4718十份正式轨迹齐。父标准库report再次逐份从本轮原row核coverage+score，落diagnosis-after-4718，计数{'no_rejection': 5, 'R': 1, 'N': 4, 'U': 0, 'not_executed': 20}；保持诊断选样限制，不外推。第四次4719已按余额检查后启动，原19:02截止未变。三次wall [1033.8905699923635, 1055.092065487057, 1060.9159328863025]秒。

2026-11-02T17:46:48.394055+08:00：第四次4719完整196/rc0，十目标coverage均PASS；累计784完整、20份正式详细trace完整。父标准库report从原row独立重算写diagnosis-after-4719，计数{'no_rejection': 11, 'R': 1, 'N': 8, 'U': 0, 'not_executed': 10}；第五次4720已在剩余196回合/原19:02与GPU/磁盘余额核查后启动。未提前结束、未缩预算或重试。

## B最终交付 · t9.8-B3-20261102T163355+0800（2026-11-02T18:11:15.773420+08:00，待独立C）

**B回放与主执行者必要核验完成，task9.8 保持 review 交监督者派C。** 实际 **980/980完整回合**、**30/30目标详细trace**；两例开关门先独立coverage后有限数值精确比较PASS。无额外smoke/训练/超额回合。五个worker全部rc0；调度器收尾rc1已人工修复且完整保留，不能写成“所有进程rc0”。结果仅是选定诊断病例，不能外推总体发生率或声称找到了物理碰撞机制。[SRC-1376](../../../SOURCES.md#src-1376)

### 交付索引与版本

- 当前负责人Codex；实际底层型号/推理强度未知。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，需核验跨批次、精确非干扰与子步恢复定义。子Agent仅实施[9.8.4覆盖/判分](task9.8.4/RESULTS.md)，父核验，均不担任C。
- 工作树HEAD `d198e5ca48f86071c05274f9da753f393ce058b4`，历史输入根HEAD `121cb36e64e53163be232dbafa8c32ff065a290b`，源码/配置继续原基础路径；**未改生产src/config**。修复文件为 `forem/scripts/task9_8/supervisor.py`（原queue.py改名、配置身份/预算/隔离、TMPDIR）、`replay.py`（零检查与覆盖门）、`analysis.py`、`test_analysis.py`，新增 `report.py`；实际执行代码在B3 source-snapshot/source-manifest，结束后UID修复另封存post-run-cleanup-fix，不能混称已用该修复重跑。
- 新run结果根 `/home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.8-B3-20261102T163355+0800`；日志根 `/home/ybc/projects/CL-FoReM-task9/forem/logs/task9/t9.8-B3-20261102T163355+0800`。 [逐例30行CSV](../../../../results/task9/t9.8-B3-20261102T163355+0800/diagnosis-final/case-results-30.csv) · [完整JSON](../../../../results/task9/t9.8-B3-20261102T163355+0800/diagnosis-final/summary.json) · [含首拒绝与yaw表的报告](../../../../results/task9/t9.8-B3-20261102T163355+0800/diagnosis-final/report.md) · [主执行者独立公式核验](../../../../results/task9/t9.8-B3-20261102T163355+0800/parent-independent-formula-audit.json)。各trace绝对路径/SHA逐行登记，完整文件hash见 `artifact-manifest.json`，A原件和旧两run不写。
- 全30冻结CSV SHA256为 `e36d1888b3bb5621f4a8c70d2eb2cea5316ae5883361017dead80de4169a57b8`。A按文首独立副本命令重算PASS/30/124，原parent-verification前后hash保持；25项原件含三final.pt在结束后再全文件流式hash匹配（input-verification-after.json）。代码、actor/config/地图/种子身份依据A副本与loaded逐项关联，不把字节hash当设备证据。
- GPU2 UUID `GPU-656ca5c1-681f-48a2-7d1f-a00824723f68`，隔离容器 `forem-t9-8-b3-20261102`，镜像 `sha256:e674db49b8156fded725ba4de8c2faf81aa491a367a1e151eddae169a1dfc430`；历史/root/mm_husky_ws和checkout/workspace RO，仅新/output、/runlogs RW，rootfs RO。五次loaded均核actor tensor相等、5M、policy/critic `cuda:0`，实际GPU进程落该UUID；threads2及TF32/interop/affinity实际值见各loaded，不倒填旧记录。

### 零回合与两例非干扰

正式镜像同工作目录、PYTHONPATH、脚本路径运行以下命令（容器/新目录身份由run.json与inspect另核）：

```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --import-check'
sg docker -c 'docker exec forem-t9-8-b3-20261102 python3 -B -m unittest discover -s /workspace/scripts/task9_8 -p test_analysis.py'
```

两命令均rc0；`queue.__file__=/opt/python310/lib/python3.10/queue.py`，PyTorch2.7.1+cu128、项目所需模块、torch._dynamo和distributed.nn.jit.instantiator动态导入成功，`TMPDIR=/output/tmp`临时写读删通过。检查无模型加载/reset/evaluate。26合成回归覆盖双方同漏、reset/final假完整、重复/乱序/缺字段、原始transfers/attempted/终态、合法无拒绝、平移/原地恢复、换段不算、零长度begin终态等；完成后额外2项UID纯mock回归，共28通过，不运行环境。B2较早两次零检查失败与首OFF初始化失败全部保留，不伪装首次即通过。

|两例|OFF/ON各动作数|各pending子步|各commit|各拒绝|各事件数|完整性与精确比较|
|---|---:|---:|---:|---:|---:|---|
|4718 validation row53 / case1|107|213|213|0|430|均PASS|
|4718 transfer row8 / case3|84|148|128|20|319|均PASS|

各侧动作数对各自原evaluation row.transfers、逐动作pending子步数对原Transition.attempted、commit计数对原Transition.committed；校验案例/段/动作/子步身份、顺序、重复缺失与终态后，才比较749事件的原始/执行动作、pending/IK接受/failed/commit、提交base/q/s和终态，finite数值完全相等、无容差。父从原JSON/trace重算通过，见parent-gate-verification；OFF/ON各196实际回合，门后ON两例计入30，未在门前采其余目标详细轨迹。

### 首次拒绝与恢复（完整30例）

|训练seed|无拒绝|R|N|U|全部受阻|R/(R+N)|严格成功|
|---|---:|---:|---:|---:|---:|---:|---:|
|4718|5|1|4|0|5|1/5|4/10|
|4719|6|0|4|0|4|0/4|5/10|
|4720|7|0|3|0|3|0/3|6/10|
|合计|18|1|11|0|12|1/12=8.3333%|15/30|

首次拒绝率12/30=40%；无缺失未判回放、未执行0。严格成功15/30；无拒绝18不等于成功，home case5三模型均无实际子步拒绝但严格失败，未混入受阻分母。U0只指恢复可判，碰撞对象/三维机制仍未知。

|训练seed|case|地图|动作数|严格成败|首次拒绝 段/动作/子步|原环境分类|拒绝后剩余量m|恢复分类|恢复动作/子步及净减少|
|---|---:|---|---:|---|---|---|---:|---|---|
|4718|1|standard_validation_00003|107|S|—|—|—|no_rejection|—|
|4719|1|standard_validation_00003|113|S|—|—|—|no_rejection|—|
|4720|1|standard_validation_00003|110|S|—|—|—|no_rejection|—|
|4718|2|standard_validation_00000|58|F|2/39/1|self_collision|1.035394085|R|40/0；Δ=0.000374927461716m|
|4719|2|standard_validation_00000|62|S|—|—|—|no_rejection|—|
|4720|2|standard_validation_00000|34|S|—|—|—|no_rejection|—|
|4718|3|home_map_002|84|F|1/65/0|IK|1.870658035|N|—|
|4719|3|home_map_002|61|F|1/42/0|IK|1.661961373|N|—|
|4720|3|home_map_002|91|F|1/71/1|IK|1.698732643|N|—|
|4718|4|home_map_002|50|F|1/31/1|IK|0.995289544|N|—|
|4719|4|home_map_002|24|F|1/5/0|base_projection_collision|0.984032982|N|—|
|4720|4|home_map_002|94|F|1/75/0|IK|1.005443310|N|—|
|4718|5|home_map_002|24|F|—|—|—|no_rejection|—|
|4719|5|home_map_002|75|F|—|—|—|no_rejection|—|
|4720|5|home_map_002|181|F|—|—|—|no_rejection|—|
|4718|6|home_map_002|121|F|1/98/1|IK|1.219070075|N|—|
|4719|6|home_map_002|80|F|1/61/0|IK|1.190861178|N|—|
|4720|6|home_map_002|67|F|1/48/0|base_projection_collision|1.657435475|N|—|
|4718|7|library_map_002|44|S|—|—|—|no_rejection|—|
|4719|7|library_map_002|40|S|—|—|—|no_rejection|—|
|4720|7|library_map_002|43|S|—|—|—|no_rejection|—|
|4718|8|library_map_002|49|S|—|—|—|no_rejection|—|
|4719|8|library_map_002|76|S|—|—|—|no_rejection|—|
|4720|8|library_map_002|58|S|—|—|—|no_rejection|—|
|4718|9|library_map_002|202|F|2/183/0|self_collision|1.513538063|N|—|
|4719|9|library_map_002|173|F|2/154/0|self_collision|1.171928878|N|—|
|4720|9|library_map_002|328|S|—|—|—|no_rejection|—|
|4718|10|library_map_002|159|S|—|—|—|no_rejection|—|
|4719|10|library_map_002|38|S|—|—|—|no_rejection|—|
|4720|10|library_map_002|49|S|—|—|—|no_rejection|—|

段/动作从1开始，子步0/1。所有12首次受阻目标均inplace=false；原地剩余量规则本轮没有真实受阻案例，只有合成回归覆盖。恢复严格按SRC-1370：first pending&failed后已提交状态为基准、同段、float64剩余量、严格减少>1e-6m或明确arrived；换目标/route_end不代替arrived。

唯一R为4718/case2，首次段2/动作39/子步1为原环境自碰撞分类；后续动作40/子步0只有一次commit，剩余量从1.035394084694m减少0.000374927461716m；未同段arrived，最终仍累计failures20、严格失败。11个N均无超过阈值的同段净进展/arrived后回合终止；其中4720/case3仍有2个、4718/case6有8个后续commit，s/yaw变化或动作被接受并不自动算平移目标恢复。拒绝后commit数、完整同段yaw最大变化、s和剩余量终差见post-rejection-event-counts.json及报告附表。

首次环境分类IK7、底盘投影碰撞2、自碰撞3。对象ID/三维几何见证与拒绝前原始IK解未采到，空字段明确保留；held q不当原始解或编码器反馈，不把投影碰撞称3D家具接触，不把IK/控制/感知误差混称已定位原因。

### 实际顺序、历史差异和启动命令

|顺序|完整原evaluate|实际完整回合|目标详细份数|worker rc|host worker wall s|
|---|---|---:|---:|---:|---:|
|1|01-4718-off|196|0|0|1033.890570|
|2|02-4718-on-gate|196|2|0|1055.092065|
|3|03-4718-remaining|196|8|0|1060.915933|
|4|04-4719-all|196|10|0|1105.014785|
|5|05-4720-all|196|10|0|1140.695746|

五次全部196的strict_success/failures/terminated/truncated/transfers对历史差异回合数均0，保留各新evaluation和原JSON；目标30也无这五字段差异。未声称与历史逐步轨迹复现，历史没有这份trace；开关精确对照才比较本轮两侧。各seed重复/地图相关且按结果挑样，不把980当独立研究样本。

实际host启动：`python3 -B -u forem/scripts/task9_8/supervisor.py --run-config /home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.8-B3-20261102T163355+0800/run.json`。五条实际worker argv来自原queue-state（未把argv[2]误当完整命令）：

```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 timeout --signal=TERM --kill-after=30s 8668.132s python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --seed 4718 --phase off --name 01-4718-off'
```
```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 timeout --signal=TERM --kill-after=30s 7634.048s python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --seed 4718 --phase gate --name 02-4718-on-gate'
```
```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 timeout --signal=TERM --kill-after=30s 6578.875s python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --seed 4718 --phase remaining --name 03-4718-remaining'
```
```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 timeout --signal=TERM --kill-after=30s 5517.905s python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --seed 4719 --phase all --name 04-4719-all'
```
```bash
sg docker -c 'docker exec forem-t9-8-b3-20261102 timeout --signal=TERM --kill-after=30s 4412.835s python3 -B -u /workspace/scripts/task9_8/replay.py --run-config /output/run.json --seed 4720 --phase all --name 05-4720-all'
```

### 资源、退出码、异常与交接

- 从最初起点 **2026-11-02 16:02:00+08**累计，绝对截止 **19:02:00+08**不变。B3新起点16:33:55.522994+08只用于新身份，不重置预算。最终墙钟（含修复、复核、保存）与新输出总bytes见final-accounting。全部尝试0+0+980=**980实际回合**；无额外smoke/训练。
- 第一次GPU88.847121s，B2（含两次零检查）68.579969s，B3容器GPU暴露5438.627223s，合计 **5596.054313s = 1.554459531 GPU h**≤3；按整个暴露窗保守计，不是kernel计时。五worker累计5395.609100s，不与墙钟/卡时混同。原输出2,822,519+B2 3,014,792=5,837,311bytes全部扣除，新输出含日志/tmp/A副本/阶段报告/代码版本与验证，见累计账本及manifest。
- 所有五worker rc0；旧两次worker/调度rc1保持；B3调度在所有worker完成后执行chown硬编码1000，而host实际uid/gid1004，导致自身写收尾标记PermissionError、**调度rc1**，并未因此重跑或改变轨迹。原queue-state的active状态是失败前历史快照，不能当现仍运行；manual-cleanup-recovery.json记录仅本run chown1004:1004 rc0、手工stop rc0，容器清理exit137，结束18:05:06.928440+08。未触碰其他容器/进程。
- UID错误已在当前supervisor修为读实际host uid/gid，2项mock回归先红后绿；post-run-cleanup-fix封存，**该修复没有用于重跑**。实际运行版仍是source-snapshot中旧版。只读/root可选torch kernel cache不可创建警告被如实保留；输入/输出正常，不在OFF/ON间改cache/flags。
- 目前本轮所有容器均已停、GPU compute无本轮进程、无后台任务。主体交付与必要核验完成但不冒充C；下一步监督者派另一位独立核验人从冻结清单、原evaluation、32份比较/详细trace和30逐例表复算，原件RO、独立新输出。剩余事项仅C独立判决；不得补跑、替执行者修结果、训练或扩大研究结论。

交接证据：B3 run.json、source-manifest、zero-import-check、parent-gate-verification、各evaluation/coverage/trace、diagnosis-final、parent-independent-formula-audit、input-verification-after、manual-cleanup-recovery、final-accounting、artifact-manifest；旧run/B2清单与异常保留。主执行者实际完成时间以final-accounting为准，C尚未执行。

2026-11-02T18:14:03.549694+08:00：最终B自检PASS（非C）：30完整/980完整、2695目标动作/106681总动作、全部finite与覆盖/开关门，原25文件结束后hash一致；旧首run59文件/B2 manifest104文件原hash均保持。五worker0；调度收尾错误1原栈保留；已人工归属1004与停机，所有本轮容器stopped、GPU2 compute空、无原PID。当前supervisor UID修复2项mock先红后绿，28回归通过，无重跑。最后生成final-accounting/manifest后交监督者派C。
