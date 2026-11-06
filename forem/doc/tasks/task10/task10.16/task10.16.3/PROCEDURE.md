# 流程
递归规则按根约定，各层三文档，父审核。新脚本仅调用task10.validation，不能改src/当前训练代码。可先用base.freeze新run然后在launch前明确过滤trained期望12行、预算1800/12、记录新目标和旧评估reference及初态hash。wrapper worker覆盖本进程EvalBudget为更严格12/1800（5400秒不变），在initial_snapshot完成后与旧run对应trained原始snapshot比较typed hash；不同直接失败且保存差异。base worker多加载initial但只执行trained可接受，如实记权重冻结。supervise和outer epoch统一，独立launch拒重复。
旧freeze需要review-20261103.json，父训练结束后CPUaudit生成该审计文件。输入训练必须1200/200且objective relative_uniform+fixed.35。manifest先完成冷启动freeze，再记录wrapper脚本自身hash及旧reference初态/冻结模型hash。每个未开始/部分回合均保留并正确分母12。评估后支持CPU只读report，复算12回合、原地比例、与旧trained/initial/uniform配对，来源哈希核验，不改原run。
最少测试预算12/1800上限、过滤清单唯一12、同初态一致与变化拒绝、参考/模型objective版本拒绝。每条CPU命令≤120s，不GPU。

## 已实现接口（尚未启动评估）

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需核查跨运行初态、冻结输入、预算和失败分母。执行者可选模型/强度、先建档委派，范围/预算不扩；本次独立执行。

`task10_kl_validation.py freeze --run NEW_EVAL --source NEW_TRAIN --reference OLD_EVAL [--pool POOL]`：先强验新actor/offline/initial learner的固定KL .35版本、最终1200/200、actor与offline权重相等和训练config目标；复用base.freeze完成冷启动模型读取与来源冻结；确认旧36回合及全部三策略旧原始初态匹配，仅保留12个trained身份，6 sparse+6 standard，预算12/1800/0/5400。记录新旧初始模型hash差别而非隐去差别。父训练结束后须先生成review-20261103.json；本子未执行freeze。

`task10_kl_validation_launch.py --run NEW_EVAL --commit COMMIT`：独占创建launch.json避免并发双启动；外层shell先设置原epoch和5400秒守护，调用wrapper的supervise，后者使用同epoch监督worker。拒已有launch/budget，不重启。此入口尚未实际启动，单元测试未调用launcher或Docker评估。

`task10_kl_validation.py supervise --run NEW_EVAL` / `worker --run NEW_EVAL`：worker先核冻结文件、新目标和清单，再在本进程临时替换base EvalBudget及initial_snapshot，结束恢复；实际环境reset后的原始snapshot在任何env.step前同对应旧trained snapshot按typed hash比较，不同落initial-comparisons差异和新原始snapshot并失败。12行清单限制回合数，预算reserve另严格限制1800决策，原5400秒不变。复用worker仍冻结/加载initial并作旧真实fixture检查，但不执行initial/uniform新回合。

`task10_kl_validation.py report --run NEW_EVAL --output REPORT [--workspace ROOT --artifacts-root REFERENCE_FOREM]`：CPU读取episode原件与原始decision journals，复用独立v2的决策/初态/权重核查函数，不以worker汇总作为评分来源。固定分母12，未开始/部分回合保留missing；复算新trained对旧trained/initial/uniform胜负平缺失、原地选择及其logit领先、结束原因、逐初态匹配、0更新和冻结hash。只有完整12、budget/summary complete、launcher正常退出rc0、无在途/来源变更等才verified_complete；12行落盘后再失败不能冒充完成。尚未对真实新评估产物执行report。

2026-11-03 16:58 +08用户新指令由父转达：训练既已启动，退出监督让其自行运行。本轮不执行上述freeze/launch/supervise/worker/真实report或任何自动串联，后续等待用户再次唤起。

## 2026-11-03 训练完成后的派发
用户要求继续流程并提供派发词。新训练 t10-kl-online-20261103-s101 的1200/200及CPU原件审计已通过，review-20261103.json已存在，依据SRC-T10-037。训练launch.json仍running且launcher已退出，该原件保持原状并披露退出码缺失；以已核验worker终态/checkpoint和CPU审计进入本次评估，不使用等待旧launcher状态的task10_kl_pipeline.py。
执行者从CPU核验objective/最终权重、已有19项专项以及freeze开始，使用task10_kl_validation.py独立入口。新评估run必须独占、12trained回合/1800决策/0更新/5400秒。启动采用脱离聊天会话的持久launcher（明确标准输出/错误文件、PID），保留内部硬截止，避免外层父进程随会话退出丢失收尾；启动后按用户偏好退出主动监督。可把完成后的只读report顺序排在该launcher之后，失败同样保留状态及缺失，不重复启动。结束以实际worker/launcher/报告一致为准，部分报告rc0不等于完整。
必答：新策略原地比例与初始12状态原地logit领先是否改变，严格成功是否超过旧0/12，与旧uniform10/12的差异，剩余停滞/碰撞/IK失败。旧两模型和随机基线通过原件hash/初态核验后复用；不同后续轨迹不直接逐步比较logits。单种子和12验证场景限制继续保留。更新本节点/父RESULTS、PROGRESS与SOURCES，交当前决策者验收。执行者拥有根约定的自主选模/建档委派权限，父统一预算。推荐GPT6.1sol/medium或Sonnet5.5/medium，涉及冻结/初态/统计一致性。

## 2026-11-03T22:06:30.692933+08:00 · 本次持久启动与顺序复算

递归规则继续适用，本次不另建子任务、不委派；推荐GPT6.1sol/medium或Sonnet5.5/medium，实际未知。执行者有自主选模/先建档委派权限，父统一预算。run `t10-kl-eval-20261103-s101` 的run_once.py由host subprocess.Popen(start_new_session=True, stdin=DEVNULL)脱离会话启动；独占detached-claim拒重复，顺序调用既有task10_kl_validation_launch.py、CUDA隐藏的task10_kl_validation.py report、CPU finalize.py。不调用旧pipeline，失败/到限同样只生成报告并保留缺失，不重跑。driver/launcher/report/finalize的stdout/stderr各独立保存在logs/task10同run目录，worker输出沿既有*-eval.log。PID与退出码分别由detached-status.json及launch.json保存。report/finalize仅只读实验原件并写新报告/追加交接文档。

完整验收还核逐回合initial-comparisons、launcher/worker同epoch、12完成/0缺失/0在途/0更新、权重和冻结文件未变、worker/launcher正常及report verified_complete。初始原地logit差=max有效原地−max有效移动，输出12行CSV；后续不同轨迹不直接逐步比较logits。启动核实后退出主动监督。[授权与CPU证据](../../../../SOURCES.md#src-t10-038)。

## 2026-11-03T22:30:50.608942+08:00 · 只读报告v2补证入口

递归三文档规则及自主选模/先建档委派权限不变，本次独立执行；推荐GPT6.1sol/medium、Sonnet5.5/medium，实际未知。原冻结report函数给3参snapshot_checks误传第4个budget；原报告和执行脚本保留。新增task10_kl_validation_report_v2.py仅在报告调用期间适配参数、finally恢复原审计函数，保留全部评分与审计，输出新report-v2，不覆盖旧文件；真实checker专项3passed。另用run/parent_check_v2.py直接从原始终局PT字段、attempts、mask、初态及输入SHA核验完整谓词。此为CPU报告修复，不获得新回合/训练权限。[来源](../../../../SOURCES.md#src-t10-040)。

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -m pytest -q --basetemp=/tmp/t10-16-3-report-v2 /workspace/scripts/tests/test_task10_kl_validation_report_v2.py'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -u /workspace/scripts/task10_kl_validation_report_v2.py --run /workspace/results/task10/t10-kl-eval-20261103-s101 --output /workspace/results/task10/t10-kl-eval-20261103-s101/report-v2.json'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -u /workspace/results/task10/t10-kl-eval-20261103-s101/parent_check_v2.py'
```
均rc0；报告适配器拒覆盖已有输出。仅再次只读复算时使用新的--output路径，不重启worker。
