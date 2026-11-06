# task12.3 结果与交接

当前状态review（运行与执行负责人原件复核完成，待决策者最终签收）。以下为启动前记录：

状态active（准备），负责人Codex，2026-11-04T22:41:21.835642+08:00。run `t12-radius075-20261104-r4`，尚无新增标签或优劣结论。预登记[plan.json](../../../../results/task12/t12-radius075-20261104-r4/plan.json)。同32快照、旧24与新24严格配对、0更新、新点≤384。初始2h工程窗，来自task12.2的32批近环2084.133s/远环3881.980s和全流程写盘208.206s作参考加余量，非新探针工期实测或优势判断。

推荐GPT6.1sol/medium、Sonnet5.5/medium，实际模型/强度未知；独立执行，根选模/先建档委派权限保留。[SRC-T12-012](../../../SOURCES.md#src-t12-012)。持久完成后追加可复算结果。

## 2026-11-04T22:52:38.674893+08:00 · 持久启动核实

run `t12-radius075-20261104-r4` 于2026-11-04T22:50:31.285833+08:00启动。driver PID1451167（独立session），docker client1451175，容器forem-task12-radius075-r4、host worker PID1451226/容器PID1，物理GPU2 UUID GPU-656ca5c1-681f-48a2-7d1f-a00824723f68→cuda:0，CPU8–9。GPU1 task10 PID970022和GPU0 task9 PID1439435保持运行。

32份源/缓存绑定、实际新旧各24点选择和复用映射均已在新增标签前冻结，inputs-frozen.json记录new_moving_needed=384≤384、new_labels_computed_before_freeze=0。旧源SHA、旧24分数/选择一致，模型权重固定；新前向0、新状态取得0（只读载入成本另记），训练更新0。没有把准备完成当作新增标签或改善结论。CPU定向测试复现旧筛前19/后18、网络14/最近16，配对增损与严格复用键通过，真实教师测试调用0。

主命令`python3 -u forem/scripts/task12_radius075_launch.py launch --run /home/ybc/projects/CL-FoReM/forem/results/task12/t12-radius075-20261104-r4`；实际argv/版本见driver.json/code-version.json，旧r1/r2/r3以只读挂载。初始2h工程窗可依实测调整，预计约1–2h，非硬截止或收益承诺。进度current.json，日志forem/logs/task12/t12-radius075-20261104-r4/driver.log、worker-01.log，退出码与累计尝试成本自动入driver.json/attempts.jsonl。STOP仅本run文件，停止后明确移除再用同命令恢复，完成状态/批次跳过；native在途恢复直接复用task12.2已测试机制。

依用户偏好退出聊天主动监督，持久launcher继续到32固定配对后停止，自动写paired-states.csv/jsonl、gain-loss-cases.json、summary/handoff和分项成本，再追加父/子RESULTS、SOURCES、PROGRESS与日志。最终是否保留0.75及下个瓶颈交当前决策者；不试第二半径、不训练、不扩制数。

## 2026-11-04T23:35:01.350460+08:00 · t12-radius075-20261104-r4 等点数配对交接

状态review，负责人Codex；实际模型/强度未知，推荐GPT6.1sol/medium、Sonnet5.5/medium，理由是冻结合同的配对/成本核查。独立执行，保留根选模及先建档委派权限。当前决策者最终验收，本节为持久launcher按原始记录自动汇总。[SRC-T12-012](../../../SOURCES.md#src-t12-012)。

已处理32/32，完整配对32、缺失0；新旧各24点、0更新。**是否保留：保留旧0.5m＋1.5m方案；0.75m未提高筛选后净覆盖。下个更接近的瓶颈：候选覆盖。** 原因按新组各门漏失状态数{'candidate_coverage': 14, 'geometry': 1, 'network_ranking': 1}定位，不是方法收益/泛化的统计证明。

|组|完整/计划|筛前覆盖|筛后覆盖|网络条件命中|网络整体命中|最近条件命中|最近整体命中|
|---|---|---:|---:|---|---|---|---|
|旧0.5＋1.5|32/32|19|18|14/18|14/32|16/18|16/32|
|新0.5＋0.75|32/32|18|17|16/17|16/32|16/17|16/32|

严格配对分母32：筛前{'gain': 1, 'loss': 2, 'both': 17, 'neither': 12, 'net': -1}；筛后{'gain': 1, 'loss': 2, 'both': 16, 'neither': 13, 'net': -1}。原13无正状态中，已配对原无正分母13，找回1、其中筛后保留1。筛前新增状态['state-07']，损失['state-13', 'state-15']；筛后新增['state-07']，损失['state-13', 'state-15']。损失状态的old_far_positive_ids、三半径标签及原姿态在逐状态原件，不能以新三环并集抵消新24点丢失。

|难度|完整配对/计划|筛前旧→新|筛后旧→新|后配对|
|---|---|---|---|---|
|sparse|16/16|10→10|9→9|{'gain': 0, 'loss': 0, 'both': 9, 'neither': 7, 'net': 0}|
|standard|16/16|9→8|9→8|{'gain': 1, 'loss': 2, 'both': 7, 'neither': 6, 'net': -1}|

新组网络命中16，最近允许点命中16；两者几何集合相同、选择不读标签，条件分母17、整体分母32，旧组分母另列于表。若后覆盖净增加而网络低于最近点，采样收益可保留但排序问题独立；若相当/下降则保留旧方案。只筛前增加而后无净增加时，读各状态geometry-positive-exclusions.json中的可见正高度格及实际距离走廊SAT条件，并与后覆盖损失同时分析，不能仅归因于几何。36点并集仅诊断：{'complete_states': 32, 'pre_cover': 20, 'post_cover': 19, 'not_a_24_point_scheme': True}，不是新24点成绩。

新增推演/复用计数{'new_rollouts_submitted': 384, 'new_probe_labels_reused': 0, 'old_grid_labels_reused': 768, 'old_rule_labels_reused': 246, 'old_inplace_labels_reused': 32}；其中旧两环768标签、规则及原地只引用，不重跑；新增移动最大384硬限，只有同源SHA/实际世界姿态/inplace/教师配置合同一致才复用。冻结热力图来自同输入/同权重r3缓存，核旧分数和选择一致，新前向0（不是网络训练）；预测读取/解码/写盘分项实测如下。新状态取得0，快照读取单列。

|成本项|总秒|逐状态p50|p90|max|
|---|---:|---:|---:|---:|
|active_state_wall_s|2665.291|93.29851148370653|157.30803773757071|160.05104289017618|
|candidate_registration_s|0.003|7.891561836004257e-05|0.00010544229298830034|0.0001619253307580948|
|decode_s|0.912|0.02373182214796543|0.023951195739209653|0.17813951335847378|
|network_inference_s|0.000|0.0|0.0|0.0|
|probe075_s|2604.363|91.84333785995841|153.42420760579407|157.61459131538868|
|snapshot_prediction_read_s|2.699|0.07924014795571566|0.11589347794651986|0.17269196175038815|
|state_acquisition_s|0.000|0.0|0.0|0.0|
|write_s|50.895|1.650645918212831|2.4320536077022554|3.7603486105799675|

本次墙钟2670.032s，rc0；主进程起止与历次中断成本在driver.json/attempts.jsonl。B3计时扣定时快照写盘、write_s单列，active_state_wall_s不可与其子项重复相加。PyTorch峰值allocated=1315489280bytes/reserved=2669674496bytes；设备采样峰值3434MiB（含驱动）。GPU1长训不动、独立单GPU，退出后容器--rm。

原件`forem/results/task12/t12-radius075-20261104-r4/`：plan.json、inputs-frozen.json、code-version.json、paired-states.csv/jsonl、gain-loss-cases.json、summary.json/handoff.json；states/<id>包含候选/纯分数选择/复用依据/新增probe075原件及在途resume.pt/标签/几何排除条件/成本。来源快照和旧记录位于r3，只读挂载。主命令`python3 -u forem/scripts/task12_radius075_launch.py launch --run /home/ybc/projects/CL-FoReM/forem/results/task12/t12-radius075-20261104-r4`；具体argv/PID/设备/退出在driver.json/launch.json，日志forem/logs/task12/t12-radius075-20261104-r4/。STOP及恢复沿本run独立标记，已完成状态/批跳过，未进行教师A/旧重放/新网络训练。

剩余：已到本轮预登记单探针对照边界，交当前决策者；未继续试半径或实施后续建议。

<!-- task12-radius-final-t12-radius075-20261104-r4-1 -->

## 2026-11-05T09:58:49.189917+08:00 · 执行负责人复核与建议

**已完成本轮运行和定向原件核查，建议保留旧0.5m＋1.5m方案，不采纳0.75m替换。** 32/32配对、384新增标签（10正）、到达/失败增量/压紧ID/源SHA以及网络和最近选择器的独立复算均一致；新增教师调用0。原件[final-audit.json](../../../../results/task12/t12-radius075-20261104-r4/final-audit.json)、[native-record-audit.json](../../../../results/task12/t12-radius075-20261104-r4/native-record-audit.json)，依据[SRC-T12-013](../../../SOURCES.md#src-t12-013)。

筛后覆盖18/32→17/32，找回state-07，丢失state-13与state-15，净−1；三例均standard，地图分别standard_train_00003、00006、00007。原13无正仅找回1/13。虽网络命中14/32→16/32，但新组与最近点同为16/32，不表明学习或采样覆盖优势；按事先固定的后覆盖净增加条件，本轮替换不保留。更主要仍是候选覆盖，而非几何或排序：保留旧组13个无正、1个全几何排除、4个排序漏选，新组对应14/1/1。无采样正点不等于整张状态空间没有可执行点。

主运行昨晚23:35退出rc0，总2670.032秒（44分30秒），无缺失，0更新。GPU2已释放，本轮容器不存在；GPU1 task10仍在运行。本次CPU原生记录检查23.247秒单列，未重跑教师/训练。已到预登记单半径对照边界；最终交当前决策者签收，未实施其他半径或扩大制数。推荐GPT6.1sol/medium、Sonnet5.5/medium用于这类字段/配对核查，实际模型/强度未知，本轮未委派。

## 2026-11-05 · 决策者最终签收
本轮工程与等点数对照验收done。逐状态标签公式和allowed/selected集合复算一致，筛后新增1/丢失2，保留旧0.5+1.5方案。冻结网络命中增加但与最近点持平，未证明网络学习或采样覆盖优势。下一步优先读现有无正候选的结束原因及进展，定位采样/教师能力边界。[依据](../../../SOURCES.md#src-t12-014)
