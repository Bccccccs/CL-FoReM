# task10.19 固定模型扩大独立场景配对评估

状态active（2026-11-06用户已派发，r2独立持久评估已启动）。负责人Codex父执行者，当前审核聊天最终验收。

目标：在更多未参与task10诊断的validation地图和初态上，估计固定10k模型相对均匀合法选点的严格成功率差及不确定性，区分场景抽样与随机选点波动。当前只有一个训练seed，本轮不能估计跨训练seed方差或证明算法总体稳定性。[用户方向与限制](../../../SOURCES.md#src-t10-sample-uncertainty-20261106)

范围：80地图（sparse/standard各40）×每图2初态×3回合（固定10k、uniform U1、uniform U2），共160个场景、480回合、0训练更新。保持B3、候选/观测/奖励/失败/终止合同；正式test池保留。只评价预定10k终点，不回选2k/5k、不给task12热力网络或WM接入、不改变alpha或学习率。旧个案诊断结果不作为新抽样/参数依据。

主要交付：标签前冻结map/scene/策略随机种子清单；480回合与逐决策原件、配对初态证明、固定权重/设备、分层成功/失败/缺失；以地图为组的配对差与95%近似区间、随机参照重复差异、成本/恢复及解释限制。完整性与是否有收益分开验收，结果不明确亦须如实结束。[设计依据](../../../SOURCES.md#src-t10-expanded-eval-plan-20261106)

推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，理由为跨入口初态一致性、随机流隔离与地图分组统计；复杂恢复/统计疑点可high。执行者可自主选择平台可用模型和推理强度，可独立完成或派发子Agent，无需另请；Codex可按难度使用Terra/Luna。委派前按根AGENTS建子三文档，指定输入、独占范围、依赖、交付、验收和实际模型，父核原始证据统一交接；共享父预算与停止条件。


## 2026-11-06T11:23:22.448749+08:00 自动交接 · active

持久启动，host launcher PID2587567、client PID2587586，GPU3，计划480回合；首条产物和初态核查待运行。工程窗口16–24h，非硬截止；无按成绩提前停止。STOP=/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-expanded-20261106-r1/STOP；恢复先读结果保留partial，再显式launch --resume。

[实测来源](../../../SOURCES.md#src-t10-expanded-run-20261106)。原件：`forem/results/task10/t10-expanded-20261106-r1/`；日志：`forem/logs/task10/t10-expanded-20261106-r1/`。固定r2 10k、单训练seed101、validation地图、每图2初态、每初态2次随机参照，正式test未使用；0训练更新。推荐GPT6.1sol/medium、Sonnet5.5/medium，入口/随机流/地图组统计需跨模块核查；父实际模型/强度未知，统计子GPT6.1sol/medium。当前审核聊天保留最终验收。


## 2026-11-06T11:23:54.483008+08:00 自动交接 · blocked

worker rc=1，report rc=0，完整条件=False。保留全部partial/缺失与固定分母；未自动换图或重试。先定位日志，再按边界或同身份一次恢复，用户STOP未撤销不得恢复。

[实测来源](../../../SOURCES.md#src-t10-expanded-run-20261106)。原件：`forem/results/task10/t10-expanded-20261106-r1/`；日志：`forem/logs/task10/t10-expanded-20261106-r1/`。固定r2 10k、单训练seed101、validation地图、每图2初态、每初态2次随机参照，正式test未使用；0训练更新。推荐GPT6.1sol/medium、Sonnet5.5/medium，入口/随机流/地图组统计需跨模块核查；父实际模型/强度未知，统计子GPT6.1sol/medium。当前审核聊天保留最终验收。


## 2026-11-06T11:25:56.677912+08:00 自动交接 · active

持久启动，host launcher PID2589004、client PID2589025，GPU3，计划480回合；首条产物和初态核查待运行。工程窗口16–24h，非硬截止；无按成绩提前停止。STOP=/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-expanded-20261106-r2/STOP；恢复先读结果保留partial，再显式launch --resume。

[实测来源](../../../SOURCES.md#src-t10-expanded-run-20261106)。原件：`forem/results/task10/t10-expanded-20261106-r2/`；日志：`forem/logs/task10/t10-expanded-20261106-r2/`。固定r2 10k、单训练seed101、validation地图、每图2初态、每初态2次随机参照，正式test未使用；0训练更新。推荐GPT6.1sol/medium、Sonnet5.5/medium，入口/随机流/地图组统计需跨模块核查；父实际模型/强度未知，统计子GPT6.1sol/medium。当前审核聊天保留最终验收。

启动入口已核通过，首图6回合计正式；r2后台active，最终统计待完成，当前审核聊天最终验收。详细PIDs/STOP/恢复及CPU收尾见RESULTS最新交接，非仅方案就绪。
