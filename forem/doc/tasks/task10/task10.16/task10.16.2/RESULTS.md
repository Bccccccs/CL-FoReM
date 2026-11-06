# task10.16.2 结果

2026-11-03 · Codex · review：固定.35均匀先验KL目标实现和CPU合同核查完成，待父独立验收。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因需核查数学目标、入口接线和checkpoint兼容；实际模型/强度无法独立核实，记未知。本次独立执行。目标/参数选择为 [SRC-T10-035](../../../../SOURCES.md#src-t10-035) 的工程决定，数学依据 [16.1](../task10.16.1/RESULTS.md)；以下为本项目CPU测试证据，父负责同步全局来源台账。

实际改动：

- `forem/src/task10/learning.py`：relative_uniform与legacy独立版本；固定温度无optimizer/可训练参数。next target双Q同减alpha logN，复用原DiscreteSAC全部loss、梯度与优化器；actor结果加当前alpha logN均值常数。当前常数不改变actor梯度，next平移改变critic目标。保存learning_objective和alpha；历史无合同状态仅可入legacy，跨目标/版本/固定alpha/温度合同不匹配先失败。
- `forem/src/task10/entry.py`：只在登记relative_uniform_trial.json精确路径接受新配置；旧smoke/online严格条件未放宽。
- `forem/src/task10/runner.py`：新建/恢复使用解析config工厂；final.actor.pt保存目标合同与alpha；entry-check读取checkpoint目标。
- `forem/src/task10/recovery.py`：父补授权的最小目标透传，默认复验工厂不会把新目标重建成legacy。
- 新`forem/config/task10/relative_uniform_trial.json`：相对旧online_trial仅增加objective、objective_version、alpha，保持formal_training_authorized=false；新`tests/test_relative_uniform.py`。

实际命令（工作树`/home/ybc/projects/CL-FoReM-task10`，容器`forem-task10-runtime`的`/workspace`映射forem，用户1004:1004）：

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -m pytest -q --basetemp=/tmp/t10-16-2-special-final /workspace/src/task10/tests/test_relative_uniform.py'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -m pytest -q --basetemp=/tmp/t10-16-2-regression /workspace/src/task10/tests/test_learning.py /workspace/src/task10/tests/test_entry.py /workspace/src/task10/tests/test_recovery.py /workspace/src/task10/tests/test_online_runner.py'
git diff --check
```

专项最终 **11 passed / 3.23s / rc0**，旧路径回归 **62 passed / 12.78s / rc0**，diff检查rc0。原始log：[专项](../../../../../logs/task10/task10.16.2/special-tests.txt)、[回归](../../../../../logs/task10/task10.16.2/regression-tests.txt)。首次未指定basetemp的专项为8passed/2setup errors/rc1（3.26s），原因是既存`/tmp/pytest-of-unknown`所有权不符；改用独占basetemp后10passed/3.13s，再补实际runner.train接线检查后11passed。未修改共享临时目录权限。

专项验证了多N均匀正则0、非均匀期望非正、无效槽NaN忽略、单有效、dt0/正值/终局、直接公式和Q平移的实际critic loss一致、actor解析与autograd/legacy梯度一致、固定温度不更新、legacy更新逐位一致、历史状态恢复与跨目标/版本/alpha拒绝、正常config工厂及非法复制路径拒绝、默认recovery工厂保留新目标。normal runner.train的CPU stub集成实际执行setup，把新config传入工厂建立新learner，随后在采集循环前sentinel退出，日志确认0决策/0更新；没有真实环境reset或GPU调用。

限制与交接：本轮0GPU、0新增真实交互、0实际试训；单元测试有合成张量上的optimizer调用。新目标GPU入口、正式性能、收集与有效在线更新、新训练结果均**尚未执行**。现有online-trial仍禁止entry-check阶段；旧fixture只验证其原目标，不能把旧GPU验收当成新目标已通过。旧独立诊断脚本若默认legacy读取新目标状态会明确失败，未扩展其协议。该实现不证明原地排序改善，不证明成功率提高。父继续原始证据核验并单独决定是否放行新试训；无本子任务遗留进程。来源登记应链接本结果、上述log和代码符号，不把实现测试当效果实测。

过程记录：[独立日志](../../../../agent_logs/task10/task10.16/task10.16.2/20261103-codex-kl-implementation.md)。未提交、未修改父共享文档或原实验产物。
