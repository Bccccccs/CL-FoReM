# task10.17.2 流程

递归规则：每层恰有TASK/PROCEDURE/RESULTS三文档；再委派须先建档、指定输入/依赖/独占写入/交付/验收。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，涉及恢复或跨run训练/评估合同；实际配置由执行者如实记录。可自主选模与先建档委派；所有子Agent共享父授权与预算，父统一GPU、启动和原件验收。

输入与依赖：父17合同与16代码；17.2依赖17.1 API，17.3执行依赖B实际检查点。只实现CPU阶段，未获父统一启动不得GPU。

独占写入：forem/src/task10/entry.py；新增forem/src/task10/long_training.py；新增forem/scripts/task10_long_launch.py；forem/config/task10/kl_10k.json；新增专项测试；本子三文档与对应日志。共享PROGRESS/SOURCES、其他子代码父处理，禁止覆盖现有未提交修改。

执行：阅读→实现最小必要修改→有意义CPU合同测试→记录命令/退出码/证据→交父审查。交付：代码、测试、说明API与限制。验收：父读原件并复测；子自报不等于通过。

新增必要独占入口：forem/scripts/task10_long_run.sh（旧shell仅允许smoke/trial，新shell只允许172800秒long-10k，沿原epoch外层timeout）。父已授权此scope。训练初始化必须传--initial-reference=/workspace/results/task10/t10-kl-online-20261103-s101/initial-learner.pt，核完整model state逐tensor相等，scheduler新9000总更新单列。

产物约定：checkpoints/decision-002000.boundary.pt、.learner.pt、.actor.pt、.json（另005000/010000及每256）；latest-checkpoint.json不可变文件hash与上一index。initial-learner.pt、real-executions/batch-XXXXXX.pt、updates.jsonl、decisions.jsonl、training-summary.json、worker-exit.json。launcher --run HOST --commit COMMIT --initial-reference HOST；父独立driver以start_new_session及独立stdout/stderr脱离聊天，结束后串联17.3 sequence再D。
