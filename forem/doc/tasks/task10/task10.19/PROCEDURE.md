# task10.19 执行流程

递归规则：实际拆分子任务须继承编号，各有TASK/PROCEDURE/RESULTS；父流程登记编号、顺序、依赖、负责人/模型、输入/独占写入与验收链接。顺序A冻结→B新入口定向检查→C持久评估→D一次统计/交接；独立脚本准备可并行，运行按依赖推进。参数依据统一见[SRC-T10-EXPANDED-EVAL-PLAN-20261106](../../../SOURCES.md#src-t10-expanded-eval-plan-20261106)，统计方法边界见[SRC-T10-CLUSTER-BOOTSTRAP-20261106](../../../SOURCES.md#src-t10-cluster-bootstrap-20261106)。

推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，理由为跨入口初态一致性、随机流隔离与地图分组统计；复杂恢复/统计疑点可high。执行者可自主选择平台可用模型和推理强度，可独立完成或派发子Agent，无需另请；Codex可按难度使用Terra/Luna。委派前按根AGENTS建子三文档，指定输入、独占范围、依赖、交付、验收和实际模型，父核原始证据统一交接；共享父预算与停止条件。

## A 样本与比较对象冻结

先读主工作区最新根AGENTS（优先于task10树旧版）、README/PROGRESS、ENV及10.17最终/10.18结论，核Git改动、正在运行进程和GPU；登记run-id/负责人/日志。主工作在CL-FoReM-task10/forem，原件只读。不得将历史“partial/300s报告超时”误认最终训练未完成。

地图取主树cube-pool-v2 manifest的validation池，各难度50图。核全部真实task10 episodes/手工诊断使用清单和既定EXCLUDED；当前已知旧12图及sparse_validation_00000–00003共16个身份，剩sparse40/standard44。不要把manifest/contract引用的全池清单当全部已使用。检查是否有新增已用身份；排除旧诊断图及相同source/geometry，沿用已核train/validation互斥证据，新增身份/source hash做定向检查，不重复全库hash。几何去重可复用已有索引，无索引仅核受影响候选地图。

各难度候选map_id排序后，使用一个Python Random(1919)，依次shuffle sparse、standard，各取40，合计80；组合先sparse后standard形成i=0..79。原池容量不足128新图，不能从test补齐，也不生成新地图。若新增排除/几何重复导致某层不足40，先记录真实可用量；在看任何新结果前可将两层一致缩到较小可用数，改plan及全部分母/资源推导并说明，不按成绩改规模或换图。

每图j=0,1两个独立初态，scene_seed=190000+2*i+j，使用原sync_v5采样器接受的初始决策边界；不人为改路线分布、过滤困难状态。对每个(map_id,j)执行T/U1/U2三个回合：T加载r2 decision-010000.actor.pt，eval/no_grad，合法logit argmax且平局最小槽；U1/U2每次决策均在当时有效槽均匀采样，保留原地，使用独立torch.Generator，policy_seed=191000+4*i+2*j+r（r=0,1）。随机流不得消费环境或另一个策略的RNG。先冻结身份/种子/顺序，再看结果；三个策略按(i*2+j)%3循环轮换执行次序。

冻结plan/manifest/exclusions/权重SHA、目标版本和设备/入口版本。只加载已验收的小actor及必要元数据，复用SRC-T10-FINAL-20261106完整训练/恢复审计，不重新加载23GiB boundary做重复报告。模型实际参数、alpha及B3前后不变；本轮不实例化优化器、不进行更新。80图是对task10的新诊断留出，不声称整个项目从未见过；参与本轮后不再称未观察集。

## B 新入口的必要核查

复用Task10Env、原候选推演/下层执行/量化观测及严格成功定义，沿用已验收batch1/primitive/sync_v5/cbl_continue配置与性能选项。为本任务提供显式新profile/manifest，不伪装成旧12图合同或修改旧冻结run。

定向检查：清单/策略与随机种子唯一；U1/U2生成器隔离并可恢复；合法uniform与T argmax；同(map,j)三臂physical/route/grid/observation/candidates/mask/proposal/geometry typed hash全部一致（排除仅运行身份/日志时间的非科学字段需沿既有函数）；跨map不要求初态相同。全部严格回合终态来自native Core，累计尝试/提交失败分开。任一真实输入/模型或标签语义不一致先定位修复受影响入口，不带错跑完整批。

统计CPU构造样例核地图成组、两次随机均值、缺失固定分母及区间；不同任务规模允许新CPU夹具，已有教师/模型/物理/精确恢复证据直接引用。首个正式map的6回合兼作真实入口检查，正确即计正式480回合，不为验收再重复同一场景。

## C 持久执行与资源

总80map、160场景、480回合、最多72000实际决策（480×原每回合150上限）、0更新；原每回合200s尝试时长与失败/停滞规则不变。数量是有限协议上界，不能通过提前结束失败回合换吞吐。获取失败保留原身份，不换地图/初态；未知/中断不记失败标签。

默认用空闲GPU1单worker。最多两张空闲GPU，若采用第二卡须先核容器GPU映射、输出目录/锁/日志/账本/随机流与进程身份隔离；按地图i奇偶分为两组、每图全部6回合在同worker完成，避免一对策略跨硬件。共享冻结plan但独占shard输出，父只在汇总时写共享文档。总计仍480回合，不是每worker480；不同分片不共享ROS/TF等状态。优先复用已有隔离能力，若新并行入口未核实，单worker正常推进，无需为两卡另建复杂框架或阻塞。

成本参考旧10k固定12图launch1328.066s：480/12×1328.066≈53122.6s≈14.76h单worker（含该run启动/执行，旧模型加载/场景分布不同）。先排16–24h串行工程窗口，非用户硬截止；两卡墙钟不直接承诺减半。先用前2个正式map的正常吞吐更新估价，不额外profile/弃掉已完成样本。代码准备/失败排错/评估实际/写盘/报告/排队分列，报告累计worker和全局墙钟。

持久launcher脱离聊天，python3 -u；预算/身份/每回合/每步原件/退出码落盘。完成后自动统计并同步三文档、SOURCES、PROGRESS、独立日志。既有已完成回合复用，不重跑已知结果；中断先按有效快照恢复同回合原RNG/状态，无法精确恢复则保留partial/失败尝试、明确从原初态重跑同身份一次所增加成本，不伪造续跑、不择优选尝试。反复同因失败先定位，不盲重试。STOP在安全边界保存，用户暂停未撤销不得恢复。必要恢复/工程耗时按最新根预算原则自主登记处理。

启动核实实际GPU、冻结模型/首条合法产物、独立持久进程及后续收尾配置后退出主动监督；程序每30min记录进度。无需等待整轮完成才回复用户，不依赖聊天在线。运行期间只跟踪完整性/错误/资源，不根据暂时成绩提前停止或追加地图。

## D 固定统计口径与判读

每状态记二元严格成功T_ij、U_ij1、U_ij2；主要效应为Δ=mean_i d_i，其中d_i=mean_j[T_ij−(U_ij1+U_ij2)/2]。80张地图等权，sparse/standard各半。T成功数分母160；U1、U2分别160，合并随机参照分母320且不得把T复制两遍虚增样本量。另给T-U1、T-U2逐状态胜/负/平、U1-U2不一致数和分难度结果，均为描述统计；主检验/区间仍只针对T-平均U的一个预登记比较，不在多个对比中挑最好者。

近似95%区间：按difficulty分层，在各层40张map中有放回抽40张，整张map的2初态及所有策略一起抽；10000次、统计RNG seed191901，取Δ*的2.5/97.5百分位。报告地图样本量、非零d_i地图数、区间宽度、各层效应及随机重复差异。依据聚类bootstrap的组内依赖思路，本项目选择与有限样本覆盖性质不可混为论文保证；这里的区间条件于固定训练seed/策略，只近似反映本地图/初态抽样及这两次随机抽样，不覆盖训练seed不确定性。若差异极稀少或bootstrap退化（如全部d_i相同），标注区间信息不足，不能将零宽区间当作证明等效。

缺失：保留80/160/480计划分母及各策略已知成功/缺失上下界；每个缺失二元结果取0/1可直接求整体Δ最差/最好界（正系数T缺失用0/1，负系数U缺失反向）。只对完整map簇可补充描述性区间且明示缺失map数；有缺失不得冒充完整主结果或将其全部记失败。优先恢复完整合同后再交付。

报告严格成功之外的失败原因、尝试时长、真实决策数、原地次数/比例、停滞终止、成功路线耗时及全体回合耗时分别统计，避免只挑成功样本掩盖成本。推演误差、原地个案只作诊断，不据此硬筛或改训练目标。

完成且区间整体高于0：当前固定seed有正向配对证据，再规划独立训练seed复核；整体低于0：当前固定seed有负向证据，再做跨场景共性诊断/受控优化。跨0、退化区间或宽区间：证据不足，不说策略等价/算法失败，不自动加20k×3。任何结果都不自动扩样直到显著、不启动WM/热力接入，不挑2k代替10k终点。训练seed变化须下一阶段独立预登记。

交付父执行者核原件和统计一致性后标review，当前聊天最终验收。后续结论必须同时说明当前模型单训练seed、80地图、每图2初态、每初态2次随机参照及正式test未用。

## 本轮子任务

[19.1 TASK](task10.19.1/TASK.md) · [PROCEDURE](task10.19.1/PROCEDURE.md) · [RESULTS](task10.19.1/RESULTS.md)：统计脚本/CPU样例，GPT6.1sol/medium，独占脚本及自身记录；与父清单/入口准备独立并行，父核后自动汇总复用。


## 2026-11-06T11:23:22.448749+08:00 自动交接 · active

持久启动，host launcher PID2587567、client PID2587586，GPU3，计划480回合；首条产物和初态核查待运行。工程窗口16–24h，非硬截止；无按成绩提前停止。STOP=/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-expanded-20261106-r1/STOP；恢复先读结果保留partial，再显式launch --resume。

[实测来源](../../../SOURCES.md#src-t10-expanded-run-20261106)。原件：`forem/results/task10/t10-expanded-20261106-r1/`；日志：`forem/logs/task10/t10-expanded-20261106-r1/`。固定r2 10k、单训练seed101、validation地图、每图2初态、每初态2次随机参照，正式test未使用；0训练更新。推荐GPT6.1sol/medium、Sonnet5.5/medium，入口/随机流/地图组统计需跨模块核查；父实际模型/强度未知，统计子GPT6.1sol/medium。当前审核聊天保留最终验收。


## 2026-11-06T11:23:54.483008+08:00 自动交接 · blocked

worker rc=1，report rc=0，完整条件=False。保留全部partial/缺失与固定分母；未自动换图或重试。先定位日志，再按边界或同身份一次恢复，用户STOP未撤销不得恢复。

[实测来源](../../../SOURCES.md#src-t10-expanded-run-20261106)。原件：`forem/results/task10/t10-expanded-20261106-r1/`；日志：`forem/logs/task10/t10-expanded-20261106-r1/`。固定r2 10k、单训练seed101、validation地图、每图2初态、每初态2次随机参照，正式test未使用；0训练更新。推荐GPT6.1sol/medium、Sonnet5.5/medium，入口/随机流/地图组统计需跨模块核查；父实际模型/强度未知，统计子GPT6.1sol/medium。当前审核聊天保留最终验收。


## 2026-11-06T11:25:56.677912+08:00 自动交接 · active

持久启动，host launcher PID2589004、client PID2589025，GPU3，计划480回合；首条产物和初态核查待运行。工程窗口16–24h，非硬截止；无按成绩提前停止。STOP=/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-expanded-20261106-r2/STOP；恢复先读结果保留partial，再显式launch --resume。

[实测来源](../../../SOURCES.md#src-t10-expanded-run-20261106)。原件：`forem/results/task10/t10-expanded-20261106-r2/`；日志：`forem/logs/task10/t10-expanded-20261106-r2/`。固定r2 10k、单训练seed101、validation地图、每图2初态、每初态2次随机参照，正式test未使用；0训练更新。推荐GPT6.1sol/medium、Sonnet5.5/medium，入口/随机流/地图组统计需跨模块核查；父实际模型/强度未知，统计子GPT6.1sol/medium。当前审核聊天保留最终验收。

## 2026-11-06 自动后处理格式适配

父CPU读取首批原件确认exact_cpu将map_ids保存为tuple；原审计写list相等导致AssertionError，属于审计格式错误，worker科学状态无异常。冻结entry/plan与运行中代码不编辑、不重启有效评估；补充独立scripts/task10_expanded_finalize.py，唯一内存代码归一化tuple比较，所有科学身份值/顺序和其余原审计保持，CPU原件专项通过（4完整回合、5步、2配对初态，0新交互/更新，frozen_files_unchanged=true）。不是把480缺失计失败，报告verified_partial。完整原始报错保留工具日志；终局原handoff若因同一断言标incomplete会归档handoff-initial-audit-format.json，随后CPU v2审计/统计统一再发布handoff.json与三文档，绝不为后处理错误重跑环境。

CPU补充收尾PID2592521，脚本SHA53d5649f5c787d0edfcea37dd11ba9b593dd381dd0455ceb752644c0310913dc，配置results/task10/t10-expanded-20261106-r2/finalization-config.json；等待worker与原launcher正常退出，自动统计/文档，日志logs/task10/t10-expanded-20261106-r2/finalizer.log、audit-v2.log、report-final.log。原launcher2589004、GPU worker host2589052/container90继续，唯一worker。

STOP：`touch /home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-expanded-20261106-r2/STOP`，安全边界保存后退出；不依赖聊天。恢复前确认用户撤销暂停并移除STOP、无本任务worker/launcher，再后台`python3 -u /home/ybc/projects/CL-FoReM-task10/forem/scripts/task10_expanded_eval.py launch --resume`，独立日志重定向；确认新launch running后也后台`python3 -u /home/ybc/projects/CL-FoReM-task10/forem/scripts/task10_expanded_finalize.py watch`，若watcher锁仍持有则复用原watcher不重复。已完成身份不重跑；同身份最多一次重试，快照/随机流/extra成本见前述。
