# task8.9.1 r2 性能核查续接

- 负责人 Codex `/root/perf_r2`；父指定实际模型/强度 gpt-6.1-sol / high，平台底层标识未独立核验。推荐 Codex GPT6.1sol / high、Claude Sonnet5.5 / high，因为跨 CPU/GPU 计时与成本归因需要推理；固定步骤按 SRC-1162 交 Terra low，独立验收由不同 Sol high。
- 授权 SRC-1160/1161/1162：沿用 t8-perf-20261027，累计≤1800s/单命令≤300s；GPU0；只冻结推理及 profile。不构造 optimizer、不 backward、不 SAC 更新，不改生产几何/语义/task7，不重复 prepare、不实施优化。共享 SOURCES/PROGRESS/父文档由父维护。r2来源使用新增 SRC-1163，草稿交父。
- 已读 AGENTS、ENV、README、PROGRESS、task8/task8.9 父三文档、本节点三文档与全部现有日志、SRC-1160/1161/1162/1103–1119。main 既有大量改动保留，文件归属仅 scripts/task8_profile_lower.py、src/task8_sim/profile_*.py、本节点三文档/本日志、自己的日志与结果。
- 开工只读核查：原账本81.76879678107798/1800s，active=null；GPU compute空，forem-dev仅保活。已准备 cube64/semantic24 cache 继续使用，不重复 prepare。
- 计划固定执行：cube batch1/16/64/256、semantic batch256；各 warmup2 + measured20，内层288s、容器292s、外层295s。每条前检查GPU0与剩余额度；首非零或样本不足停止交回Sol，不把部分结果当通过。尚未执行。

## Terra首轮后Sol复核与有界窗口修复

- 原件确认cube b1/16/64均20步，吞吐5.161773/14.553979/17.695761 transfer/s；cube b256 rc124，warmup2+17完整步、4352转移/239.725406测量秒=18.154104 transfer/s，原外层289.619989s；账本505.1480193603784/1800s，active=null。semantic256尚未执行。
- 256 step约14s，cold reset13.378243s，加warmup2与20步超过300s。不是GPU容量失败。父确认P2允许多个有界窗口累计≥20，因此采用两个各10步窗口、每窗warmup2；同seed4718/缓存episode产生重复轨迹，计时样本重复测同输入，不冒称连续20步或20独立episode。原超时保留。
- 仅profile测量修复：--window-steps/--window-id独立命名，窗口状态window_complete不能独窗通过；cold_timings隔离、测量前clear；保存原始wall/event样本；信号异常回滚未完成step分项。生产代码/算法/环境条件未改。原b1/16/64嵌套collision/raycast/IK包含cold reset样本，environment_step/panorama/actor等20测量样本未混冷；不重跑，严格P2留独立验收。
- 四条新固定清单r2-window-jobs.json（cube w1/w2再semantic w1/w2），尚未执行，首失败即停。两修改文件AST parse通过，纯静态验证；运行由Terra执行，归因交Sol。

## 最后两个语义窗口计划与成本框架

- Sol核semantic r2-w1：completed_steps=steps长度=environment_step/raycast/panorama/replay_consume/drain计数=8；转移数逐步和2047、wall逐步和194.010178308934s均相符；未完成step已rollback，因此8个完整样本可保留累计（整个命令仍rc124/incomplete）。
- cube r2-w1/w2各warmup2+10，5120转移/284.660929161124s，约17.9863 transfer/s；新窗口只统计warmup后完整分项，冷启动独立。
- 新清单r2-final-window-jobs.json只semantic w3/w4，各warmup2+6，计划合并8+6+6=20；未执行，不重跑20。原账本1176.3628219533712/1800s、余623.637178s。
- 条件成本框架r2-cost-framework.json：task8 profile无更新c + U*(旧eager-sync27.9898/2047 s/update)，另列未知随机复位、正式checkpoint、100/96评估、logging/争用项，不把未知项取0作验收。cube UTD1的3M条件基础项已>48h；UTD.1基础项接近48h但不能证明就绪。SAC旧测量仅条件迁移，非task8实测。

## r2最终交付

- semantic w3/w4各warmup2+6，原件与Terra报告核对，8+6+6共20完整步、5119转移/467.506323815323s=10.9495845066304 transfer/s；cube两个10步共17.986310994938034 transfer/s。所有窗口raw分项重算/步数/transfer与wall和一致。原两个124保留，cube旧17不加入汇总，semantic8经rollback核验计入。
- 输出summary-r2.json/md、sources-r2-draft.md、summary-recompute-r2.log、final-sol-check-r2.json；新增标准库只读汇总入口scripts/task8_profile_summarize.py。SOURCES/PROGRESS/父文档仍由父维护。本节点三文档更新当前review/NOT_READY，并完整保留r1历史、cold污染/重复轨迹/正式池未补测限制。
- 计时归因：256cube/semantic raycast91.69%/94.67%最重，给代码位置、CPU64/GPU32逐元素距离/碰撞/Transition等价门、只出方案与Amdahl敏感性，不实施。成本旧SAC条件基础cube3M UTD1/.1=57.725/47.471h，正式reset/196评估/100k保存/真实SAC与争用未测，不用0填满，不作新B0真实运行>48h实测断言。
- 汇总CPU命令首次rc1：numpy与stdlib分位数末位精确比较不等；仅对报告复算一致性改为rel/abs1e-12后rc0，不是实验逐元素等价门放宽。四个工具AST可解析；final check全部输入hash一致/五负载各20。无额外GPUprofile、无SAC操作。
- 最终账本1597.584848462604/1800s，active=null、余202.415151537396s；最大命令289.722394312732s。后续留父独立必要审查，禁止再额外GPUprofile或补正式子集。本实施者不标done，不自行派Agent；父登记SRC-1163后安排不同Sol/high独立验收，仍需C真实smoke和完整周期成本才判断长训就绪。
