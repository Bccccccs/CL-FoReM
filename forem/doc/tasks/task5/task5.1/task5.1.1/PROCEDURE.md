# task5.1.1 监督流程

递归规则：本节点/后代各恰有TASK/PROCEDURE/RESULTS，父task5.1列顺序、依赖、负责人/验收；目前无后代。
1. 读根AGENTS/父三文档/本三文档与监控脚本；核查现有主机监控PID、A容器train PID、后处理PID。不派发实施。
2. 读取5秒CPU与30分钟jsonl，确认持续落地。R7/D11生效后，主机CPU连续5分钟窗口时间加权均值>56核仅写alert并报告，任何情况下不得因CPU自动停止训练；旧连续两样本SIGINT规则撤销。子Agent只报告，不调整阈值/worker。
3. 每30分钟独立记录环境步数、episode、最近评估/CPU/PID；无需重复父全部原日志。期间等待用≤60秒工具，重要变化通知父Agent；不要每个不变快照都留言。
4. 若训练/监督程序失败或采样断档，立即通知父Agent，自己不修复/重启。CPU告警立即报告但继续监督，不能因此结束训练/后处理。训练exit0后等已部署父§4–6监督器；检查posttrain_status.json和最终评估九任务/每朝向50episode原始证据，自己的RESULTS置review（证据交付），交父最终核查。
5. 只更新自己节点三文档与doc/agent_logs/task5/task5.1/task5.1.1/独立日志，不写父RESULTS/PROGRESS/SOURCES，避免并发。父负责汇总/来源。
模型推荐Codex gpt-6.1-sol/low，Claude Sonnet5.5/low或默认，明确监督步骤无复杂实施；实际派发低强度记录。
