# task10.19.1 统计实现记录

2026-11-06，负责人stats子Agent；实际GPT6.1sol/medium（父派发标记），独立完成，不另派发。已读最新AGENTS、父PROCEDURE和SOURCES两条预登记统计依据、自己的三文档。独占scripts/task10_expanded_report.py、自身三文档和本日志，不改共享文档，不运行环境/GPU。

## 接口与当前进展

本地实现work/task10_expanded_report.py已完成；纯stdlib、无torch。API `build_report(plan, rows)`；CLI `python3 forem/scripts/task10_expanded_report.py --run RUN`。输入RUN/plan.json，expected每行episode_id/map_id/difficulty/j/strategy（T/U1/U2），scenes每图id或map_id/difficulty/i；每图必须恰有j=0/1、各三臂。读取shards/*/episodes/*.json；实际行必须保留同样五个身份字段。重复、不在计划、身份字段不一致抛ValueError。只有complete is True且strict_success严格bool计有效。其他记录保留已观测诊断及计划缺失。

可选episode标量字段decisions/inplace_count/stalls/failures/attempted_seconds/committed_seconds/wall_seconds/route_seconds；reason及triggers.stall_limit用于终止原因统计。所有缺失指标报告n=0，不补0。成功路线成本同时列attempted/committed/wall/route_seconds；与全部有效、全部已观测成本并列。原地比率只在同时具备decisions与inplace_count行计算并报告覆盖。

累计成本原样保留shards/*/*budget*.json、shards/*/attempts.jsonl以及根*budget*.json、launch*.json、state.json到report::cost_evidence，不将互相重叠预算/episode累计求和。episode_cost仅是当前唯一身份文件，不能替代替换前失败尝试账本。父可按持久执行器实际预算字段进一步指定累计worker/global墙钟展示；原件不丢弃。

主效应按每地图两初态T−均值U，再难度层等权；固定计划分母成功率/缺失结果带符号效应上下界；完整地图才重抽，10000次seed191901，层内整图bootstrap。缺失时primary.effect/interval为null，补充单独primary.complete_map_supplement。非零地图<=2标“极稀少差异”仅描述提醒，不作为显著性或功效门；退化/任层不足2图也提醒信息不足。跨0证据不足，不声称等价/算法失败。

## 已执行与证据

- `python3 -m py_compile work/task10_expanded_report.py`：rc0。
- `python3 work/stats-fixture/check.py`：rc0。覆盖地图聚类/两随机均值、不等地图数难度等权、10000重抽已知端点、缺失正负号/固定分母、无结果上下界[-1,1]、严格bool完整标签、身份重复/不匹配、退化全0/全1区间提醒、诊断覆盖。
- 构造4地图2/2×2初态×3臂24回合；sparse地图效应[1,0]，standard[-.5,0]；主效应.125，区间[-.25,.5]，非零2图，信息不足；去一个T成功结果上下界[0,.125]；去一个U1失败结果[.0625,.125]。
- 初版夹具CI手写预期误为[-.5,.75]导致断言失败；复算整层权重后纠正预期[-.25,.5]，统计实现未改。该失败及后续通过均保留本地工具执行记录。
- `python3 work/task10_expanded_report.py --run work/stats-fixture/run`：rc0，生成report.json、REPORT.md。纯CPU合成数据，未当真实评估。

状态active；待远端部署、远端同一CPU夹具验证后更新RESULTS为review交父核原件。

## 完成追加

父通过文档约定episode failure_kinds及session成本字段后，已追加failure_kinds各类别汇总、与native failures按episode核和及不一致身份清单。成本读取shards/*/sessions/*.json，每session elapsed_seconds只计一次累计worker；预算副本不再相加。launch.json finished_epoch−started_epoch给当前launch墙钟；所有launch-prior及当前launch最早开始至最晚结束给全局墙钟（含恢复间隙，当前launch未结束时为null）。attempts原件保留。

追加CPU已知答案：两session100+29=129，预算129不重复加入；prior launch10→110、current120→149，全局139、当前29；failure_kinds ik_rejected=2与failures=2一致；失败attempt保留。`python3 work/stats-fixture/check.py`和CLI均rc0。

SSH曾连续reset，后恢复。已部署远端脚本，并实际执行：

- `python3 /home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-expanded-stats-fixture-20261106/check.py` rc0，两行PASS（与本地同夹具，唯一改动导入远端脚本绝对路径）。
- `python3 /home/ybc/projects/CL-FoReM-task10/forem/scripts/task10_expanded_report.py --run /home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-expanded-stats-fixture-20261106/run` rc0，status=complete、24合成有效回合；远端生成report.json和REPORT.md。
- `sha256sum /home/ybc/projects/CL-FoReM-task10/forem/scripts/task10_expanded_report.py`：0671b0a057fba7e8293f5a751064cbfce00f62418aee273c1ea5b907f0ab743c。

状态review，交父核原件。未运行环境/GPU或真实评估；不承诺真实策略效果；没有git提交/推送。剩余事项：父审阅统计口径与真实入口字段，真实结果完成后自动CLI输出并按父流程统一交接。无运行任务需监控。
