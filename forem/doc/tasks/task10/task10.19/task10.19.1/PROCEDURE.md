# task10.19.1 流程

递归规则：若进一步拆分，先建继承编号子任务三文档并列依赖/独占范围；本次不拆。依赖父预登记口径，不依赖真实成绩；先实现再以CPU已知答案样例核查。

API `build_report(plan, rows)`；CLI `python3 forem/scripts/task10_expanded_report.py --run RUN`。读取run/plan.json::expected（episode_id,map_id,difficulty,j,strategy T/U1/U2），scenes每map id或map_id/difficulty/i；每map两初态各三臂必须齐全且计划身份唯一。读取run/shards/*/episodes/*.json；每行同五身份字段，完整episode仅complete is True、strict_success严格bool，未知不记失败，计划分母固定。

完整map两初态三臂整组、difficulty分层10000 bootstrap/seed191901，层等权1/2；缺失时只给计划最差/最好效应界和完整map补充区间，不作完整主结果。胜负平与U1/U2不一致、失败原因/时长/原地/停滞/成功及全体成本并列。退化/非零地图<=2（仅描述提醒）/任层完整map不足2图提示信息不足；跨0证据不足，不推等价/算法失败。

failure_kinds逐类求和，覆盖完整failure_kinds和failures行逐episode核和，输出不一致身份。shard budget、attempts原件完整保留；sessions/*.json的elapsed_seconds各session只计一次累计worker，不重复相加budget。launch finished-start给当前墙钟；首次launch开始至最终结束含恢复间隙给全局墙钟，未结束null。

CLI写report.json、REPORT.md，不写全局文档。CPU夹具验证聚类、两随机均值、不等层图数等权、缺失符号上下界、固定分母、退化、身份/标签、失败分类核和及session成本不重记。远端已执行证据见[RESULTS](RESULTS.md)。

依据链接见[TASK](TASK.md)及[父PROCEDURE](../PROCEDURE.md)。推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，因地图聚类、缺失及重复随机参照口径需核对。用户允许自主选模/强度及先建档委派；本子任务独立完成、禁止环境/GPU，父核原件统一交接。
