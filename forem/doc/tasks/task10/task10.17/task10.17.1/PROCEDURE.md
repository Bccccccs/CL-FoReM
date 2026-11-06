# task10.17.1 流程

递归规则：每层恰有TASK/PROCEDURE/RESULTS三文档；再委派须先建档、指定输入/依赖/独占写入/交付/验收。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，涉及恢复或跨run训练/评估合同；实际配置由执行者如实记录。可自主选模与先建档委派；所有子Agent共享父授权与预算，父统一GPU、启动和原件验收。

输入与依赖：父17合同与16代码；17.2依赖17.1 API，17.3执行依赖B实际检查点。只实现CPU阶段，未获父统一启动不得GPU。

独占写入：forem/src/task10/recovery.py；新增forem/src/task10/boundary_state.py；forem/src/task10/tests/test_decision_recovery.py；本子三文档与对应日志。共享PROGRESS/SOURCES、其他子代码父处理，禁止覆盖现有未提交修改。

执行：阅读→实现最小必要修改→有意义CPU合同测试→记录命令/退出码/证据→交父审查。交付：代码、测试、说明API与限制。验收：父读原件并复测；子自报不等于通过。

接口：save_decision_boundary(path, learner, replay, *, environment, policy_generator, budget, config, counters, journal_paths, histories)；load_decision_boundary(path, learner, replay, *, environment_factory, config, test_only_allow_same_pid=False)。仅CPU夹具可显式同PID；正式恢复必须新PID。使用capture_environment返回纯状态树核对场景/传感/队列/候选；A端点仅忽略实测墙钟字段，科学字段逐位核验。CPU通过不放行B，父须在A共享128真实/64诊断更新/1h内核验。
