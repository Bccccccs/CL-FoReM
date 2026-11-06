# task10.17.3 流程

递归规则：每层恰有TASK/PROCEDURE/RESULTS三文档；再委派须先建档、指定输入/依赖/独占写入/交付/验收。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，涉及恢复或跨run训练/评估合同；实际配置由执行者如实记录。可自主选模与先建档委派；所有子Agent共享父授权与预算，父统一GPU、启动和原件验收。

输入与依赖：父17合同与16代码；17.2依赖17.1 API，17.3执行依赖B实际检查点。只实现CPU阶段，未获父统一启动不得GPU。

独占写入：新增forem/scripts/task10_long_validation.py；新增forem/scripts/tests/test_task10_long_validation.py；本子三文档与对应日志。共享PROGRESS/SOURCES、其他子代码父处理，禁止覆盖现有未提交修改。

执行：阅读→实现最小必要修改→有意义CPU合同测试→记录命令/退出码/证据→交父审查。交付：代码、测试、说明API与限制。验收：父读原件并复测；子自报不等于通过。

## 新入口与原件合同

`python3 -u forem/scripts/task10_long_validation.py sequence --source HOST_TRAIN_RUN --run HOST_EVAL_ROOT --commit COMMIT` 由父持久driver在B退出后调用；本子未执行。宿主可无torch/matplotlib，freeze/report/curves通过现有容器CUDA隐藏执行；GPU worker沿既有容器和物理GPU1隔离路径。

读取TRAIN/checkpoints/decision-002000.boundary.pt、005000、010000，配套decision-N.json不可变hash索引、initial-learner.pt、contract与终态summary。检查点直接声明task10-decision-boundary-v1，真实2000/1000、5000/4000、10000/9000，不伪装旧1200/200。完整learner total_updates9000、原ledger10000/9000/172800、replay真实数量、stage1、固定KL .35、新初始0/0/9000均强验。B先完整退出，接受complete/partial/failed/stopped_boundary；若发生显式恢复，优先resume-summary并核worker-exit，原summary保留。

各组freeze后唯一launch，外层shell、Python supervisor和worker共用组原epoch90min；sequence总原epoch16200s，组outer另取global deadline较早者。每组trained12/1800/0，总至多36/5400/0；缺失checkpoint/组/回合保留missing，无重启。freeze读取旧legacy independent-audit-v2与旧KL report-v2及模型/原始PT/快照，模型/地图/B3/初态均冻结hash。每回合原始snapshot按typed hash在任何env.step前比旧12初态，不一致落差异并拒绝执行。

输出ROOT/sequence.json（complete/partial/failed、阶段退出码、累计决策/回合/更新、worker与global成本），每组checkpoint-N/{manifest,launch,budget,entry-check,summary,weights,report}.json及initial/episodes/decisions原件。report schema task10-long-validation-v1-report，状态verified_complete/verified_partial/failed；独立v2读取raw journals重算严格成功、终态/缺失、初态与冻结权重，另核新计数合同。输出新策略对old_KL200/old_legacy/uniform配对、原地比例、12初态原地logit领先、实际attempt的IK→base→arm→self归因。训练预算终点固定为最终模型，验证不选模，test池不使用。

结束由CUDA隐藏container curves生成learning-curve.csv/png、initial-logit-comparison.csv、curve-summary.json。缺失点为缺口，不填0；baseline从已核参考原件读数，不重跑。若C硬窗已尽，保留CSV/missing并由D CPU只读curves补图，禁止新交互。独立复算：`... task10_long_validation.py report --run CONTAINER_EVAL --output NEW_REPORT`（新输出，保留旧原件）。

GLOBAL成本含整个sequence，cumulative_worker_seconds按freeze/launch/report/curves实际子进程墙钟累加；budget_charged_seconds单列组原epoch（含freeze的已消费时限），不将两者混加。所有执行仍由父统一GPU和资源，不能因CPU实现完成提前启动C。
