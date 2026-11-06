# task10.19 结果

当前状态active：r2 `t10-expanded-20261106-r2` 在GPU3独立运行，固定80地图/480回合/0更新；r1零决策入口失败已保留并修复，r2首态typed hash与r1完全相同，尚无总体收益结论。最终验收由当前审核聊天负责。

2026-11-06：尚未执行。已完成流程设计和派发提示词；未创建实际评估清单、未启动新回合、未计算新成功率或区间。

规划时已读原池manifest：validation为sparse50/standard50；task10现已完成episode记录使用各6图，既定额外排除sparse00000–00003，按身份剩40/44图。拟80图各40、每图2初态、T/U1/U2共480回合；执行前再核新增使用/几何排除。128张新图方案因实际容量不足未采用。[来源](../../../SOURCES.md#src-t10-expanded-eval-plan-20261106)

交接模板：run-id/实际负责人和模型；地图与随机种子清单；三臂初态一致性；完整回合/缺失/重试消耗；T/U1/U2成功与主要配对差、地图组区间/限制；失败原因/时长/原地；设备、持久进程、退出/停止恢复及成本；是否支持下一阶段研究。无结果时保持尚未执行，不以本计划代替验证。

推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，理由为跨入口初态一致性、随机流隔离与地图分组统计；复杂恢复/统计疑点可high。执行者可自主选择平台可用模型和推理强度，可独立完成或派发子Agent，无需另请；Codex可按难度使用Terra/Luna。委派前按根AGENTS建子三文档，指定输入、独占范围、依赖、交付、验收和实际模型，父核原始证据统一交接；共享父预算与停止条件。

## 2026-11-06T11:14:18.748514+08:00 执行接手

active，已授权按A→B→C→D连续推进，当前尚无新结果。父实际模型/强度未知；19.1计划GPT6.1sol/medium，统计实现与CPU样例独立。GPU1占用需核查。详情见独立日志。

## 2026-11-06 11:23 +08 执行前冻结与定向核查

已核18份真实episodes.jsonl＋手工18.4清单，仅旧12图；额外排除4图，共16身份。validation100图canonical OBB去重与现有source/target哈希索引交叉，候选sparse40/standard44，按预定Random1919选40/40，无缩量、无test。80图/160场景/480回合及320独立策略seed、轮换顺序已冻结，父独立公式复算通过。plan SHA 8d6a3c7aa7052a3fdec5b743aa8e14d9b7724c99533324a92009d10e2a561e89；actor文件SHA 64a2faf77a105991dd7ea055534c23859ed6a79c2c7f8716b5203841564c77e3；model typed state e90ec29a0c3a9de20ee892650536719fb31f5828fe9d1bc004fc6b42d48cbf62。固定alpha=.35、relative_uniform，无优化器/更新。

GPU1被task9.12 bioik PID2564991使用，不停止或共用；GPU0/2其他任务使用，选择空闲GPU3单worker。独立容器forem-task10-19-gpu3，设备仅3→cuda:0，network none，workspace本树、主树只读/reference；独立shards/worker0锁/账本/日志/随机流，不启ROS/TF服务。旧task10容器不动，task12不触碰。

复用17最终训练/恢复/教师审计，未加载23GiB boundary。新CPU选点/RNG专项rc0，统计19.1原件CPU已知答案及远端夹具rc0，父复核公式和原件；统计script SHA0671b0a057fba7e8293f5a751064cbfce00f62418aee273c1ea5b907f0ab743c。新入口本体py_compile通过。首正式图6回合继续核真实初态/合法性/设备，正确即计正式；首2图12回合正常吞吐自动修正16–24h排期，旧外推14.76h仅参考，不设以工程窗口为硬停。SSH间歇reset用ControlMaster恢复，准备约10分钟、0环境/0GPU评估成本；不将连接失败记科学失败。

自动launcher每30min只写完整性心跳，不按中途成功率决策；终局CPU原件审计→统计→handoff→三文档/SOURCES/PROGRESS/独立日志。单训练seed/地图簇近似区间限制保留。[执行实测来源](../../../SOURCES.md#src-t10-expanded-run-20261106)。


## 2026-11-06T11:23:22.448749+08:00 自动交接 · active

持久启动，host launcher PID2587567、client PID2587586，GPU3，计划480回合；首条产物和初态核查待运行。工程窗口16–24h，非硬截止；无按成绩提前停止。STOP=/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-expanded-20261106-r1/STOP；恢复先读结果保留partial，再显式launch --resume。

[实测来源](../../../SOURCES.md#src-t10-expanded-run-20261106)。原件：`forem/results/task10/t10-expanded-20261106-r1/`；日志：`forem/logs/task10/t10-expanded-20261106-r1/`。固定r2 10k、单训练seed101、validation地图、每图2初态、每初态2次随机参照，正式test未使用；0训练更新。推荐GPT6.1sol/medium、Sonnet5.5/medium，入口/随机流/地图组统计需跨模块核查；父实际模型/强度未知，统计子GPT6.1sol/medium。当前审核聊天保留最终验收。


## 2026-11-06T11:23:54.483008+08:00 自动交接 · blocked

worker rc=1，report rc=0，完整条件=False。保留全部partial/缺失与固定分母；未自动换图或重试。先定位日志，再按边界或同身份一次恢复，用户STOP未撤销不得恢复。

[实测来源](../../../SOURCES.md#src-t10-expanded-run-20261106)。原件：`forem/results/task10/t10-expanded-20261106-r1/`；日志：`forem/logs/task10/t10-expanded-20261106-r1/`。固定r2 10k、单训练seed101、validation地图、每图2初态、每初态2次随机参照，正式test未使用；0训练更新。推荐GPT6.1sol/medium、Sonnet5.5/medium，入口/随机流/地图组统计需跨模块核查；父实际模型/强度未知，统计子GPT6.1sol/medium。当前审核聊天保留最终验收。

## 2026-11-06 r1入口失败修复→r2

r1 worker24.276733s，0实际决策/0完成回合/0更新，在reset后的capture_environment拒绝map_ids创建的采样lambda。没有产生成功/失败标签，未改样本。根因是Task10Env.reset(map_ids)为固定地图设置factory，而现有边界编码显式拒绝custom mutable factory；新入口先将原sampler.entries限定为同一单图，再调用原reset()，与旧lambda所调用的同类型sampler.sample相同。只改本次scripts入口，不改生产环境或采样器。r1原脚本已归档freeze，账本/partial/初态/报告/rc全部保留。r2逐身份、种子、次序、全部预算与r1完全相同（父独立assert），首态typed hash还须对齐r1，正确才执行第一步。

r2 plan SHA 247227870b2e6e279e73d8fb88300099b16d3627d0fdd17222b1a7c52250e412；所有文件哈希重新冻结，0结果筛图/0科学条件调整。r1失败累计成本已在r2 prior-cost.json登记，并在最终统计累计worker总计中单列加回；r1 wall 30.109813s（含入口）、worker 24.276733s。修复及重验证工程耗时单列，不因旧预计窗口阻塞。报告补充prior成本读取后同CPU夹具rc0。统计子原始交付SHA已记录，父新增成本字段后版本以r2 plan为准。

后台恢复命令（尚未执行/供后续）：确认worker/launcher均退出、用户STOP已撤销（没有撤销不得恢复）后，`nohup python3 -u forem/scripts/task10_expanded_eval.py launch --resume > forem/logs/task10/t10-expanded-20261106-r2/resume-时间.log 2>&1 < /dev/null &`。已完成身份复用；优先boundary.pt+meta SHA同版本恢复env/VCM/global RNG/独立策略generator，已提交原件有尾部但无有效最新边界时保留partial并仅同初态重跑一次；反复错误不循环。每个身份最多2 attempt，所有额外成本保留。


## 2026-11-06T11:25:56.677912+08:00 自动交接 · active

持久启动，host launcher PID2589004、client PID2589025，GPU3，计划480回合；首条产物和初态核查待运行。工程窗口16–24h，非硬截止；无按成绩提前停止。STOP=/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-expanded-20261106-r2/STOP；恢复先读结果保留partial，再显式launch --resume。

[实测来源](../../../SOURCES.md#src-t10-expanded-run-20261106)。原件：`forem/results/task10/t10-expanded-20261106-r2/`；日志：`forem/logs/task10/t10-expanded-20261106-r2/`。固定r2 10k、单训练seed101、validation地图、每图2初态、每初态2次随机参照，正式test未使用；0训练更新。推荐GPT6.1sol/medium、Sonnet5.5/medium，入口/随机流/地图组统计需跨模块核查；父实际模型/强度未知，统计子GPT6.1sol/medium。当前审核聊天保留最终验收。

## 2026-11-06 自动后处理格式适配

父CPU读取首批原件确认exact_cpu将map_ids保存为tuple；原审计写list相等导致AssertionError，属于审计格式错误，worker科学状态无异常。冻结entry/plan与运行中代码不编辑、不重启有效评估；补充独立scripts/task10_expanded_finalize.py，唯一内存代码归一化tuple比较，所有科学身份值/顺序和其余原审计保持，CPU原件专项通过（4完整回合、5步、2配对初态，0新交互/更新，frozen_files_unchanged=true）。不是把480缺失计失败，报告verified_partial。完整原始报错保留工具日志；终局原handoff若因同一断言标incomplete会归档handoff-initial-audit-format.json，随后CPU v2审计/统计统一再发布handoff.json与三文档，绝不为后处理错误重跑环境。

CPU补充收尾PID2592521，脚本SHA53d5649f5c787d0edfcea37dd11ba9b593dd381dd0455ceb752644c0310913dc，配置results/task10/t10-expanded-20261106-r2/finalization-config.json；等待worker与原launcher正常退出，自动统计/文档，日志logs/task10/t10-expanded-20261106-r2/finalizer.log、audit-v2.log、report-final.log。原launcher2589004、GPU worker host2589052/container90继续，唯一worker。

STOP：`touch /home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-expanded-20261106-r2/STOP`，安全边界保存后退出；不依赖聊天。恢复前确认用户撤销暂停并移除STOP、无本任务worker/launcher，再后台`python3 -u /home/ybc/projects/CL-FoReM-task10/forem/scripts/task10_expanded_eval.py launch --resume`，独立日志重定向；确认新launch running后也后台`python3 -u /home/ybc/projects/CL-FoReM-task10/forem/scripts/task10_expanded_finalize.py watch`，若watcher锁仍持有则复用原watcher不重复。已完成身份不重跑；同身份最多一次重试，快照/随机流/extra成本见前述。

## 2026-11-06 启动核查完成，退出主动监督

状态active（后台评估），非最终收益验收。首张正式图sparse_validation_00042的6回合、8真实决策已计入480计划；父CPU逐一读取6个initial.pt独立复算八项typed hash，每j三臂一致，逐步raw mask/身份/原地/合法动作核查通过；初态入口修复对旧r1初态typed hash完全相同。固定r2模型/B3 actual CUDA设备证据与前后权重一致，0更新。startup-check.json、shards/worker0/first-map-check.json及startup-raw-audit.json为原件；本轮没有额外smoke或profile。交接时实际完整回合10、已完成真实决策12；不读取中途成功率作停止/换图决策。

持久身份：host launcher2589004（PPID1、SID自身）；host GPU worker2589052（容器PID90、独立SID）；CPU收尾2592521（PPID1、SID自身），容器forem-task10-19-gpu3仅GPU3。三进程现场存活。主运行日志：forem/logs/task10/t10-expanded-20261106-r2/worker-1793935556.log，launcher.log；收尾finalizer.log、audit-v2.log、report-final.log。结果目录forem/results/task10/t10-expanded-20261106-r2。完整性查看budget.json、progress.jsonl、finalizer.json、launch.json，完成看handoff.json（需complete=true）、audit.json和report.json/REPORT.md；当前未生成最终收益结论。首2正式地图后自动写throughput-first-two-maps.json修正排期，未为测吞吐额外交互。启动核查已完成，父退出主动监督，后台不依赖聊天在线。

STOP及恢复按本任务PROCEDURE最新追加：STOP安全边界保存；恢复须先确认暂停已由用户撤销/无活动worker，再launch --resume及对应CPU watch，不能自动无授权撤销暂停。全部partial/重试与r1失败成本保留，不按成绩重启。前述CPU tuple格式兼容收尾已持久配置，保持原冻结入口和旧错误记录。最终三文档/SOURCES/PROGRESS/独立日志由收尾更新到review，审核聊天最终验收；固定单训练seed限制始终保留。
