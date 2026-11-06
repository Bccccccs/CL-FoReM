# task9.10.2 协议及独立验收 RESULTS

**当前状态done，独立验收完成；最终结论见文末。** 以下保留14:48开工阶段事实：2026-11-03 14:48 +08，Codex /root/reviewer，请求配置gpt-6.1-sol/high，实际后端模型/强度未知。当时启动前只读审查进行中，正式C/T尚未执行；本子始终未加载网络模型/创建仿真环境。[授权](../../../../SOURCES.md#src-1383) · [冻结设计](../../../../SOURCES.md#src-1382)。

已读父/.2三文档、execution-window、9.8现行协议/B3/C记录、9.9原件摘要与blocked-cases-12.csv、基础Core/Actor/evaluate/RNG/coverage源码。分支codex/task9-lower-improve，既有dirty文档和脚本保留。已向实施者传达action_start输入边界精确比较、mean_action对照、全批前向、RNG全流摘要与_finish零动作段编号风险。待实现稳定版逐项核查；此时不发READY。

详细命令、问题与交接随[独立日志](../../../../agent_logs/task9/task9.10/task9.10.2/20261103-codex-independent-review.md)追加。最终原件统计尚未执行；没有新恢复或成功率结论。

推荐GPT6.1sol/high、Sonnet5.5/high，因需核跨批RNG、动作边界与原成功语义。

## 2026-11-03 14:57 +08 首C准入

**READY_FOR_FIRST_C_ONLY**：独立核全部5项执行脚本与snapshot/inventory字节一致；正式容器9项合成门/26项原coverage回归通过，零导入未加载模型/运行环境。单次触发、动作边界、全流RNG、原_finish编号与success/stalls记录、完整196 C/B逐row比较均已审。详见[准入原件](../../../../agent_logs/task9/task9.10/task9.10.2/code-admission-1457.json)及独立日志；来源登记[SRC-1384](../../../../SOURCES.md#src-1384)。父仍负责输入身份/资源释放门；C/T正式结果尚未产生，不能当机制通过。

## 2026-11-03 15:18 +08 C4718独立验收

**PASS（仅首C）**。自写标准库检查从原evaluate/JSONL复核196历史row精确相等、5完整轨迹/原_finish逐段语义/终态及R1/N4；唯一R仍case2净rho减0.0003749274617164122m，5例原success与strict_success均false、20failures。未导入实施者score/coverage。证据[独立JSON](../../../../agent_logs/task9/task9.10/task9.10.2/independent-C-4718.json)，来源登记[SRC-1384](../../../../SOURCES.md#src-1384)。其余C/T待执行与独立核验，尚无干预改善结论；判据与原始事实依据[SRC-1382](../../../../SOURCES.md#src-1382)、[SRC-1379](../../../../SOURCES.md#src-1379)。

## 2026-11-03 15:36 +08 C4719独立验收

**PASS（第二C）**：196历史row及4完整trace精确相同，原_finish语义核对通过；N4、success/strict均false。累计9目标R1/N8，仍待C4720补齐12门。证据[独立JSON](../../../../agent_logs/task9/task9.10/task9.10.2/independent-C-4719.json)，[SRC-1384](../../../../SOURCES.md#src-1384)。

实际schema单位注记：`original_finish.r_rad`沿原`metrics`第二返回值，真实为无量纲CBL旋转残差`1-(qa·qb)^2`；angle才以弧度计。字段名误导，不把原success的`r<=0.05`解释成0.05rad。原计算/判定未变，不改活代码；源码位置`forem/src/task7_sim/kinematics.py:131`，[来源](../../../../SOURCES.md#src-1384)。

## 2026-11-03 15:54 +08 三C独立验收

**PASS_CONTROLS_GATE**：C4720的196历史row与3完整trace精确匹配、3N；三C共588完整/588历史row精确相同，固定12目标R1/N11/U0、原success0/strict0。逐动作/子步覆盖及原_finish段归属、success与stalls均独立核过，未导入实施score/coverage。证据[三C门](../../../../agent_logs/task9/task9.10/task9.10.2/independent-controls-gate.json)、[C4720](../../../../agent_logs/task9/task9.10/task9.10.2/independent-C-4720.json)，来源[SRC-1384](../../../../SOURCES.md#src-1384)。T结果仍待执行/复核。

## 2026-11-03 16:12 +08 T4718独立验收

**PASS（仅首T）**：196完整，5次单次raw/执行动作替换、精确前缀/输入边界/均值对照、采样JSON/SHA/seed身份与RNG摘要均独立通过。R2/N3：保留case2，新增case6；success/strict均false，20failures。case6全段最大rho减0.0012711500405742093m，但段末净减-0.0037452972849869592m，终态反而更远。非目标196row对账差异0，随机strict67/100、语义49/96与C相同。证据[首T独立JSON](../../../../agent_logs/task9/task9.10/task9.10.2/independent-T-4718.json)，[SRC-1384](../../../../SOURCES.md#src-1384)。其余T及最终12例CPU epsilon检查待完成；当前只支持该子集的临时局部恢复事实。

## 2026-11-03 16:30 +08 T4719独立验收

**PASS（第二T）**：196完整、4次真实raw/执行替换，精确边界/均值与前缀、SHA/seed/RNG检查通过；独立N4、success/strict均false。非目标row差异0；随机strict63/100、语义39/96与C相同。累计T9例R2/N7，末3例及CPU epsilon/最终账本待核。证据[第二T独立JSON](../../../../agent_logs/task9/task9.10/task9.10.2/independent-T-4719.json)，[SRC-1384](../../../../SOURCES.md#src-1384)。

## 2026-11-03 16:41 +08 CPU独立抽样重建

**PASS_EPSILON_IDENTITY_ONLY**：同镜像CPU独立重建12/12 epsilon逐值exact；0网络模型/仿真环境/环境回合、无GPU。CPU float32公式与GPU保存动作只有1/12逐位同，最大实际差5.960464477539063e-08，逐分量公开且不设容差、不放宽GPU精确前缀门。总launch墙钟2.014545s、stdout14050B/stderr0，仅写本目录，输入只读。证据[采样复核](../../../../agent_logs/task9/task9.10/task9.10.2/independent-cpu-sampling.stdout.json)、[命令](../../../../agent_logs/task9/task9.10/task9.10.2/independent-cpu-sampling-command.json)，[SRC-1384](../../../../SOURCES.md#src-1384)。末T尚待完整封口，随后把CPU读取的完整intervention对象SHA与最终trace重新对应。

## 最终独立交付 · 2026-11-03T16:49:47.830405+08:00

**PASS：协议/实现/完整性、随机流与1176回合预算均通过。** 采用自写标准库扫描24条原JSONL与6份原evaluate，不导入实施者score/coverage；另以同torch镜像CPU独立重建12个epsilon。原件未修改，无额外仿真回合/网络模型/训练。父仍负责项目层总裁决；本子独立工作已交付。[来源](../../../../SOURCES.md#src-1384)。

固定12模型-案例对：C为R1/N11/U0，T为R2/N10/U0；保留R1、获得R1、丢失R0、保持N10。12次均为首拒绝后的下一真实同段动作，raw与物理执行值均实际改变；全部前缀/替换边界输入及原均值精确相同，12个RNG前后摘要一致。原success均0/12，strict均0/12；全部目标仍20次失败终止。新增R仅4718/case06，全同段最大rho减少1.271150mm，但段末净减少为−3.745297mm，最后距离更远。只有局部暂时恢复证据，未改善完整路线到达或严格成功，不证明可部署能力或生产效率提高。

|训练seed|case|C→T|同段最大rho减 C/T（m）|同段末净rho减 C/T（m）|首拒绝后commit C/T|最终原success C/T|
|---|---|---|---|---|---|---|
|4718|02|R→R|0.000374927461716/0.000374927461716|0.000374927461716/0.000374927461716|1/1|0/0|
|4718|03|N→N|0/0|0/0|0/0|0/0|
|4718|04|N→N|0/0|0/0|0/0|0/0|
|4718|06|N→R|0/0.00127115004057|-0.00383839327323/-0.00374529728499|8/66|0/0|
|4718|09|N→N|0/0|0/0|0/0|0/0|
|4719|03|N→N|0/0|0/0|0/0|0/0|
|4719|04|N→N|0/0|0/0|0/0|0/0|
|4719|06|N→N|0/0|0/0|0/0|0/0|
|4719|09|N→N|0/0|0/0|0/0|0/0|
|4720|03|N→N|0/0|-0.00738368725761/-0.00977095822158|2/2|0/0|
|4720|04|N→N|0/0|0/0|0/0|0/0|
|4720|06|N→N|0/0|0/0|0/0|0/0|

每seed完整池的strict计数C/T完全相同：随机验证分别67/100、63/100、64/100；语义分别49/96、39/96、44/96。全部588个C row精确匹配B，C/T每seed196 row的非目标差异均0。1176是完整评估运行成本，非1176个独立新任务样本；固定12属于开发诊断，不作显著性或总体成功率推断。

CPU审查12/12 epsilon逐值exact、12个intervention对象canonical SHA与最终封口原件完全相同。CPU float32完整公式与GPU保存动作只有1/12逐位同，最大实差5.960464477539063e-08，逐分量公开；未设事后容差，未把CPU近似当GPU精确复现。GPU公式由冻结代码和原均值/执行前缀门核验；CPU仅验证预登记随机抽样身份。

原6份写前账本各196、去重job身份齐全，1176完整、6worker rc0；5项执行source/snapshot一致，18份实际instrumented函数文件与首次审查版本一致。容器原ID已停止、Pid0；保守GPU资源窗口6885.213066s，实际容器窗6885.037545s；全局至监督停机7154.890500s，至本次独立交付7296.608344s，均在原4h窗口内。6worker累计6355.128382s，分别有嵌套而不相加。核查时run+log为14,033,669B，外部指定范围实测2,675,212B小于16MiB预留，保守记30,810,885B（后续交接小文件仍在外部预留内），低于2GiB。

逐seed worker墙钟T/C为1.010065、0.998177、1.002381；监督进程段为1.010029、0.997067、0.999498。原actor批次同步延迟P50/P95/P99在完整性JSON中；该计时混合尾批形状。reset/core_step/emit有嵌套，sample未覆盖前RNG摘要，环境构造/候选/保存/退出未完整分项，因此不相加冒充完整成本、不宣称生产吞吐收益。CPU独立容器无GPU、2.014545s、stdout14050B，已计全局墙钟及外部范围。

证据：[24原轨迹独立配对](../../../../agent_logs/task9/task9.10/task9.10.2/independent-final-paired.json) · [CPU抽样](../../../../agent_logs/task9/task9.10/task9.10.2/independent-cpu-sampling.stdout.json) · [CPU与final记录对应](../../../../agent_logs/task9/task9.10/task9.10.2/cpu-final-record-match.json) · [预算/代码/设备/停机](../../../../agent_logs/task9/task9.10/task9.10.2/independent-final-integrity.json)。可复算命令（工作树根）：`python3 -B forem/doc/agent_logs/task9/task9.10/task9.10.2/independent_check.py --run /home/ybc/projects/CL-FoReM-task9/forem/results/task9/t9.10-paired-20261103T144811+0800`。CPU命令与镜像/flags/退出码在本目录独立命令JSON中。

风险/剩余：本次完整核验无未解决科学门，未启动后续训练/部署。单次预登记抽样和12个定向病例不能证明所有替代动作效力，新增局部R也未转化成功；阶段计时覆盖限制与r_rad字段无量纲误名已明示。移交父汇总与来源更新，下一步不由本子擅自启动。推荐GPT6.1sol/high、Sonnet5.5/high；本轮请求gpt-6.1-sol/high，实际底层模型/强度未知。
