# task10.16.3 · 新目标单策略配对入口
用户批准新训练后同12场景最终策略评估≤90min。父训练已运行，严禁修改src目录及当前训练依赖。只新增scripts/task10_kl_validation.py、scripts/task10_kl_validation_launch.py及scripts/tests下CPU专项，子三文档/日志。复用现validation的freeze/worker以最小适配单trained12回合、1800决策、0更新、5400秒；保持旧3组入口不变。旧task10.14同初态及源输入hash对照，初态不一致在该回合执行前拒绝。负责人sol/high。推荐GPT6.1sol/high、Sonnet5.5/high；可自主选模/建档委派，同父预算。仅CPU验证，不启动任何GPU/评估，父统一启动。

2026-11-03 16:58 +08：实现与CPU专项完成，状态review；父转达用户要求已启动训练后退出监督，等其自行运行。本子立即收尾，不启动freeze、launcher、GPU评估或自动串联。脚本保留待后续唤起审核。实际模型/推理强度无法独立核验，记未知；本次独立完成，未派发子Agent。

交付三个新增文件：scripts/task10_kl_validation.py、scripts/task10_kl_validation_launch.py、scripts/tests/test_task10_kl_validation.py；原src、既有训练脚本、config均未修改。目标/预算来源为[SRC-T10-036](../../../../SOURCES.md#src-t10-036)，实际CPU证据见[RESULTS](RESULTS.md)。

2026-11-03T22:06:30.692933+08:00 本次用户明确授权CPU冻结、唯一真实新trained12回合及持久启动后退出主动监督/顺序只读复算，取代上文旧的“仅CPU/不启动”执行限制；预算与初态合同不变。推荐GPT6.1sol/medium、Sonnet5.5/medium，自主选模与先建档委派权限同根约定。[授权](../../../../SOURCES.md#src-t10-038)。

2026-11-03T22:30:50.608942+08:00 唯一评估及CPU报告补证完成，状态review交当前决策者。严格成功10/12、原地0/21，report-v2与父原件复算verified_complete；完整验收通过，单种子12validation限制保留。推荐GPT6.1sol/medium、Sonnet5.5/medium；不启动新实验。[结果依据](../../../../SOURCES.md#src-t10-040)。
