# T10-ONLINE-TRIAL-20261102

开始 2026-11-02T19:02:12.223057+08:00；负责人Codex，实际父模型/强度平台未公开，未知；工作树 /home/ybc/projects/CL-FoReM-task10，分支codex/task10-upper-wm，HEAD c8edc2a，祖先检查rc0、初始干净。已读根AGENTS、ENV、README、PROGRESS、task10三文档及第三次复核/SRC-T10-020。当前四卡无compute、无task10进程；forem-task10-runtime停止中。

授权：本次一次连续、允许中断后不完整结项的在线试训；新run-id t10-online-20261102-s101；真实1200/在线更新200/训练wall25200s先到即停，不重跑不恢复不追加。固定B3-5M seed4718、上层101、batch8、train、1000真实均匀预热及既定候选/观测/奖励/折扣/strict success；不配对、不正式长训/task11。真实batch8恢复保持独立未通过。

入口准备/验证是必要工作：先CPU确定性及截止夹具，单命令最大120s/0真实/0GPU；旧fixture经正常runner入口GPU核验设置/同输入与timeout，统一预检最大600s、0真实、最多8派生fixture更新，所有失败共用此预检绝对截止；旧数据不进入新试训。训练25200s从唯一外层启动前epoch开始，含import/加载/采集/更新/journal/checkpoint/清理，所有Agent共享；只有父能启动GPU1和唯一在线run。原冒烟默认1800s保留。

分工：10.11入口合同agent独占runtime.py、scripts/task10_run_bounded.sh、新entry.py、config/task10/online_trial.json及tests/test_entry.py（可更新test_runtime.py），其三文档/日志；10.12首更证据agent独占新training_evidence.py、tests/test_training_evidence.py及其三文档/日志。父独占runner.py、正常入口验证/训练集成、报告脚本、共享文档、启动与计账。每次派发可自主选平台模型/强度或先建档再委派；所有子Agent共享父授权、总预算及截止，禁止私自GPU或真实采集，不提交；父核验原件。两子选GPT6.1sol/high（跨模块时钟/梯度因果）；推荐Claude Sonnet5.5/high。

计划：先RED→GREEN实现显式smoke1800/trial25200 profile、实际确定性设置合同、Python/ledger/timeout同一原epoch硬截止；初更新前后保存actor/q1/q2梯度/参数/Adam设备和B3哈希/无grad，warmup1000和首次update事件、回放原件、分阶段计时。父复跑入口检查，独立审查后提交代码；唯一在线运行新建空回放，持续监控至结束/故障/截止，失败不重启。结束只读核对journal/ledger/replay/更新checkpoint，写结果与限制。

验收：三个问题均需本次真实证据，不把fixture或旧16/56行当预热；没有有效更新如实not_verified。成功率是否提升不在范围。

入口集成进展：10.11最终独占23passed（默认30min/显式7h、旧epoch超时、TERM忽略KILL、pre-Python CUBLAS）；10.12独占15passed（独立三头、Adam合法lazy未用参数与B3原件检查）。父旧入口RED3failed后接initialize/配置/持久learner、在线禁止resume，GREEN8passed（含既有边界夹具）。父初全组合201passed/3条件skipped/44.46s。独立10.13指出Python解析前无hard保护和对照失败仍额外fixture，新增反例2failed/6.56s，已补shell前置timeout与sameepoch/对照失败立即退出（最终组合进行中）。父只启动GPU；真实尚未开始。新增取证：warmup1000完整learner/replay/RNG，firstbefore真实1008及下一样本身份、0→1原件/后checkpoint、每次update权重写前计数及分头gradient报告、每8更新完整replaycheckpoint；没有环境恢复声明。

独立审核两问题已最小修复：shell用同原epoch的前置TERM hard-2/KILL hard覆盖Python启动/解析，内部supervisor仍核定相同硬截止；entry-check若严格双对照不verified即停止、不进入第五fixture。RED2failed已观察；首次全套仅测试将GNU timeout组KILL返回-9误限定为124/137（实际按硬截止KILL正确），将信号返回-9纳入后完整复验中。真实科学条件未改。正常入口GPU预检将做4对照fixture+1真实CUDA取证路径fixture（总5，≤8），全部旧derived replay且0真实；若失败先修不采集，不重置预检截止。父唯一运行脚本task10_online_launch.py新建独占run目录和launch.json，原epoch传入容器，不重试；此时在线尚未启动。

正常入口预检完成：代码b5b60ee，原derived-fixture SHA b9ddd64e...，run-id t10-online-entry-20261102，预检600s/0真实/8fixture cap下实际14.641088s、rc0、5fixture更新，两组严格verified，取证verified_cuda；flags实际全符合要求，GPU1无fallback。预检原件entry-contract/entry-summary/entry-update-evidence和controls，命令/epoch在preflight-ledger。CPU最终203passed/3条件skipped/47.09s/rc0。入口门通过，所有src和shell/config冻结，后续只写独立报告脚本/文档，不改训练代码。下一命令唯一启动在线25200s/1200真实/200在线更新，空回放seed101、B3seed4718、batch8、1000真实预热。预检5更新明确不计入在线200。

唯一试训已启动：开始 2026-11-02T19:29:28.225644+08:00，硬截止 2026-11-03T02:29:28.225644+08:00，原epoch=1793618968.2256439。父PID3815493、docker client 3815501、容器worker PID554；exec会话39972。actual contract profileonline-trial/1200/200/25200，Python与两层timeout硬截止epoch逐值相同；CUDA/driver/CPU亲和和flags在contract.actual_runtime。监控：task10_online_report.py --run ... --compact，tail *-train.log及budget/events/updates/batch-boundaries；停止仅在确认run身份后给worker PID554发送TERM，保留原deadline且不得重启。当前未启动恢复/配对/task11。
