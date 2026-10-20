# task5.2.1 监督流程

递归声明：本节点/后代恰有TASK/PROCEDURE/RESULTS，父列顺序/依赖/负责人/验收；目前无后代。
1. 读根AGENTS、父task5.2三文档、本三文档和R7/SRC0221；核查容器forem-t5-husky的train.pid、主机monitor.pid/posttrain.pid（results/task5/t5.2-train-s40）。
2. 至少每30分钟核查/记录环境步、episode、最近evaluation及CPU记录新鲜度。已有主机脚本每5秒采CPU/每30分钟落盘；你的独立日志在doc/agent_logs/task5/task5.2/task5.2.1/。重要变化通知父，等待每次≤60秒，不叙述不变快照。
3. D11连续5分钟主机CPU时间加权均值>56仅告警/报告，**绝不停止训练或监控，不发信号**。D6 CLUB不生效，若新异常只报告，不改代码/配置。
4. 训练exit0/≥1M后父监督器按§4–6导出/九任务最终评估/冻结；B bookstore原版完整入口一次默认50ep/seed999、含原版10reset重试但外部墙钟1800秒，失败允许N/A/不可运行，不入成功率。核查八可运行标准分支均值与九任务表N/A/8/9覆盖；不可运行不得记0。pnp额外朝向单列50ep。bookstore若不同原因失败仍需父/Claude决策。
5. 父后处理review后检查原始输出计数/指标与manifest，自己的RESULTS置review并通知父；父最终核验/来源汇总，Claude5.3独立复核。其他失败、采样断档立刻通知父，自己不重启/续训/新运行。只写自身节点/日志，避开父共享文件。
推荐Codex gpt-6.1-sol/low，Claude Sonnet5.5/low或默认，明确监控路径无需提高强度；实际派发另记。
