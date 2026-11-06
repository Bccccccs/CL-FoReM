# task10.19.1 结果

状态review（统计代码及本地CPU构造核查已完成，父执行者核原件；真实评估尚未执行）。实际派发配置GPT6.1sol/medium；独立完成，未调用环境或GPU，未改合同/共享文档。

交付：`forem/scripts/task10_expanded_report.py`；API `build_report(plan, rows)`，CLI `python3 forem/scripts/task10_expanded_report.py --run RUN`生成`RUN/report.json`和`RUN/REPORT.md`。输入为父流程约定的plan及每身份唯一episode文件。身份重复/不在计划/字段不一致拒绝；有效终态仅complete为True且strict_success严格bool。成功固定计划分母，缺失上下界按带符号系数求；主效应按地图两初态平均，再难度层等权，T不复制。完整地图分层整簇10000bootstrap/191901；缺失主区间为null、完整地图补充区间单列。极稀少差异（非零地图<=2仅作描述提醒）、退化/层不足2图、跨0区间给信息/证据不足，不推出等价或算法失败。边界单训练seed/正式test未用均写明。

## 实际验证（CPU合成，非真实评估）

- `python3 -m py_compile work/task10_expanded_report.py` rc0。
- `python3 work/stats-fixture/check.py` rc0；覆盖聚类/两随机均值/难度等权/缺失符号和固定分母/无结果/严格bool/身份错误/退化/成本覆盖。
- 已知答案4图2/2、24回合：地图效应sparse[1,0]、standard[-.5,0]，主效应.125；bootstrap区间[-.25,.5]，非零地图2；去一个T成功，效应界[0,.125]；去一个U1失败，效应界[.0625,.125]；全缺失[-1,1]；全0及全1退化信息不足。夹具最初手写CI端点算错，纠正预期后通过，未为夹具修改统计实现。
- `python3 work/task10_expanded_report.py --run work/stats-fixture/run` rc0，输出JSON/Markdown，包含失败attempt账本与budget原件；各臂全体/成功条件成本并列，缺字段不补0。

累计成本：episode文件可被同身份重跑替换，单算最终episode不含早期失败成本，因此report::cost_evidence完整保留shard预算/attempts及根launch/state/budget原件，不把重叠账本相加。真实全局墙钟及累计worker字段由父执行器原件决定，不从文件时间推造。

证据与执行详情见[独立日志](../../../../agent_logs/task10/task10.19/task10.19.1/20261106-codex-stats.md)。本地证据为父工作区`work/stats-fixture/{check.py,run/report.json,run/REPORT.md}`。远端脚本已尝试上传；最终远端部署核验状态见日志追加，不将SSH中断误报通过。

推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，因地图聚类、缺失及重复随机参照口径需核对。用户允许自主选模/强度及先建档委派；本子任务禁止启动环境或GPU，父核原件统一交接。

## 远端最终核验追加

远端脚本SHA256 `0671b0a057fba7e8293f5a751064cbfce00f62418aee273c1ea5b907f0ab743c`。SSH恢复后已部署，并在`forem/results/task10/t10-expanded-stats-fixture-20261106/check.py`实际运行同一纯CPU夹具rc0，CLI对该目录run产物rc0（24合成回合complete）。补充failure_kinds分类汇总与native failures逐episode核和；预算副本不相加，累计worker由独立sessions elapsed_seconds之和给出。fixture两session100+29=129，global墙钟139、current29及失败attempt保留均核通过。原件见独立日志；真实评估尚未执行。

父核追加：已读脚本/原CPU夹具、独立重算地图均值与缺失符号、实际运行夹具rc0；统计子交付验收done。父后增prior失败成本字段并重跑同夹具rc0，版本以r2 plan::files为准；本子没有新环境或训练。父task10.19仍后台active待最终审核。
