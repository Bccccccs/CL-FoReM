from pathlib import Path
from datetime import datetime
stamp=datetime.now().astimezone().isoformat(); report='agent_logs/20260928-p1-retrain-report.md'
p=Path('doc/DECISIONS.md'); s=p.read_text(); assert '## D36 ' not in s
s+='''
## D36 — 修复后1000回合正式train/val诊断（2026-09-28，P1-RETRAIN-028）

按用户明确授权执行D27/D34协议：train seeds0–999/val9600–9899、seed11、hidden64/lr3e-4/wd1e-3/batch512/max200epoch/patience20，无max-train-batches。没有修改训练算法或控制语义。无动作86epoch/best66/40678batch；动作107epoch/best87/50611batch，均完整epoch并正常早停。

300val逐回合等权标准化total：一步copy0.253411/no_action0.173332/action0.167075，五步copy0.492552/no_action0.405974/action0.389825。action相对copy改善34.07%/20.86%，相对no_action改善3.61%/3.98%；四组配对episode-bootstrap95%CI均负。全部回合纳入，包括高误差9881和五步唯一略差于no_action的9699。完整结果见[报告](agent_logs/20260928-p1-retrain-report.md)。训练+评测1031.71s；RSS3.029GiB/cgroup3.032GiB/GPU compute合计1482MiB/task swap0/宿主swap增量0，16GiB/no-swap硬隔离通过。65测试复跑通过；best-val重评与最佳曲线完全一致。

解释边界：这是单训练seed、用于早停的验证集上的P1a初步预测证据。没有独立最终test或跨seed稳定结论，不将CI视为包含选型与训练seed变化。原采集初始观测与floorplan图像精确hash跨split无交集，但近重复场景/场景族隔离未验证。本轮不使用旧test，不扩大9600，不进入P2，不声明闭环控制改善。建议先保持配置验证seed22/33并完善未曝光独立test协议（尚未执行）。P1研究出口review；P2–P5保持blocked。无精确resume CLI，latest包含完整epoch状态不等于支持精确续训。
'''; p.write_text(s)
p=Path('doc/PROGRESS.md'); s=p.read_text(); s=s.replace('初步预测证据（D35）','初步预测证据（D36）').replace('当前优先事项：D35初步证据','当前优先事项：D36初步证据').replace('正式重训完成（D35）','正式重训完成（D36）'); p.write_text(s)
p=Path('doc/P1_WORLD_MODEL.md'); s=p.read_text(); pos=s.index('> 执行 Agent'); s=s[:pos]+'> 2026-09-28正式诊断：P1-RETRAIN-028已完成1000train/300val、seed11完整重训；动作模型一步/五步均优于复制/无动作，配对CI均低于0。仅P1a初步预测证据，独立test与跨seed未验收，不放行P2。见[报告]('+report+')与D36。\n\n'+s[pos:]; p.write_text(s)
p=Path('doc/P1_MEMORY_PLAN.md'); s=p.read_text(); s=s.replace('M5正式研究重训未启动。','M5已完成1000回合单seed正式train/val诊断（D36），独立test/跨seed仍未验收。'); s+='\n## 2026-09-28 M5诊断实测增补\n\nP1-RETRAIN-028完整epoch：no_action86、action107，300val全部一步/五步；RSS3.029GiB、USS2.415GiB、cgroup3.032GiB、GPU compute合计1482MiB、task swap0、宿主swap增量0，cache1.252GiB。训练+预测1031.71s，预算通过；没有9600回合正式重训或精确resume。长期epoch验证及P1a初步预测结果见[报告]('+report+')，不等于独立test或闭环验收。\n'; p.write_text(s)
p=Path('doc/README.md'); s=p.read_text(); s=s.replace('M5研究重训未启动','M5单seed train/val诊断已完成，独立test待验收'); s=s.replace('旧P1结果仍需正确重训重验（D33）','旧P1结果降级（D33）；新1000回合正式重训已给出单seed train/val初步证据（D36）'); s+='\n最新P1a正式训练诊断：[P1-RETRAIN-028报告]('+report+')。一步/五步动作预测均优于两对照；独立test、跨seed与闭环收益仍待验证。\n'; p.write_text(s)
p=Path('doc/agent_logs/20260928-p1-retrain-diagnostic.md'); s=p.read_text(); s=s.replace('- 状态：active','- 状态：done（实训/val诊断；独立test与跨seed待验收）',1); s+=f'''
## 最终验收与交接（{stamp}）

状态：done（1000回合实训及完整val诊断，不代表P1完整研究出口）。

交付：[报告](20260928-p1-retrain-report.md)，含三组一步/五步total/robot/map/raw、逐回合分布/配对CI/分组、学习曲线、资源、异常与边界；产物根results/p1-retrain-20260928，大产物不入Git。实际修改仅根doc（日志/报告/PNG/任务脚本/PROGRESS/DECISIONS D36/README/P1_WORLD_MODEL/P1_MEMORY_PLAN）；主包冻结diff及已有改动完全一致。

实测：训练退出0，no_action86epoch/best66/40678batch、action107epoch/best87/50611batch；val300回合79593一步/78393五步，评测退出0。action相对copy改善34.07%/20.86%、no_action3.61%/3.98%；四组episode配对总误差CI为负。RSS3.029GiB/USS2.415GiB/cgroup3.032GiB，GPU单进程784MiB/compute合计1482MiB，task swap0/宿主swap增量0。训练+评测1031.71s，预算通过。65测试退出0；分析退出0，最佳权重一致、best-val重评差0。

最终证据：diagnostic-r1/final-verification.json确认1300源分片SHA与11缓存块SHA全部一致，源码/encoder/协议/主包diff未改、diff --check退出0、报告链接存在；all-containers-final.json确认训练/分析/测试三个容器退出0、未OOM、未运行。docker ps仅原mmhusky-node01/mmhusky-node01-gz，nvidia compute为空。旧ROS及用户进程未停止，任务无遗留长进程，退出容器和产物保留。

并发协调：共享DECISIONS重读后发现11:15由另一任务新建D35投稿目标记录，原拟占D35的断言拒绝（退出1，未覆盖该决策）。本轮改用空闲D36，并重读/保留VENUE-028及OUTLOOK-028-B等新增进度行；投稿任务内容不属本轮范围，未修改其决定。文档同步完成标准后更新任务done。

限制：单训练seed、val参与早停；精确layout/initial hashes互斥但未验证近重复/场景族隔离；没有独立test、反事实动作或控制收益。最高误差9881和五步略退化9699完整保留。无精确resume CLI，固定r1已存在，不能盲目重复命令；同配置新seed需新任务/容器/output。建议seed22/33及全新未曝光test协议完善，尚未启动。P1-A为review初步证据，P1-B/P2–P5不放行，用户本轮范围已完成。
'''; p.write_text(s)
print(stamp)
