# task10.2 独立日志

开始 2026-11-02T15:12:30.870185+08:00；授权及文件归属见本节点TASK；实际模型 gpt-6.1-sol/high（派发参数）。尚未执行。

## 2026-11-02 15:20 +08:00 · 实现与CPU确定性核验

已读根AGENTS、forem/AGENTS、README/PROGRESS、ENV、本节点三文档、父PROCEDURE B/C及原task7_upper model/VCM/replay/SAC/stages代码。父负责共享进度；本子任务独占文件范围未改变。使用test-driven-development和verification-before-completion技能约束先写测试、后实现、据命令报告；using-superpowers声明派发子Agent跳过其外层流程。实际派发gpt-6.1-sol/high；推荐GPT6.1sol/high、Sonnet5.5/high，因终局/回放/恢复边界核查复杂。

发现旧路径仅按terminated决定bootstrap，固定8步序列丢弃前4步，短回合没有采样起点。已实现独立learning.py包装，不改共享模块。API为attempt_reward、EpisodeReplay.append/sample、Stage1Learner、sequence_outputs/update_sequences；详细输入输出在本节点PROCEDURE。完整prefix无梯度重建、最多4步burn-in、最多8真实loss位置、每个真实决策起点都可采样，容量淘汰整回合保持初态历史。

测试先写初次运行退出码2：缺失task10.learning，pytest cache权限警告；未把此导入RED写成断言级失败。实现后本节点12passed/3.19s/rc0；补两个边界测试后，本节点14项＋旧task7_upper全部CPU回归83passed、2GPU条件skipped/13.22s/rc0。精确命令：

`sg docker -c 'docker exec -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=1 -e MKL_NUM_THREADS=1 forem-task10-exec python3 -m pytest -q -p no:cacheprovider /workspace/src/task10/tests/test_learning.py /workspace/src/task7_upper/tests'`

独立容器由父建立，worktreeforem挂/workspace可写，主仓results挂/reference/results只读；torch2.7.1+cu128，本次CPU张量/optimizer，无GPU核验。git diff --check rc0；起始HEAD7b705c1a802aee0e53fb0bb1025ed7232f2dc4a0，分支codex/task10-upper-wm。无训练/采集/配对/提交/推送，无运行中的本子任务长任务。

实际改动：forem/src/task10/learning.py、tests/test_learning.py，本节点TASK/PROCEDURE/RESULTS与此日志。其他task10文件父或其他子Agent维护，未触及。来源草稿交RESULTS，父登记SOURCES。状态review待父复跑；父接入真实env前重点查复位前next字段、非空下一mask、尝试计时和独立mask。尚无真实闭环/GPU梯度/下层hash/性能证据，不把CPU夹具作为任务收益结论。

## 2026-11-02 15:23 +08:00 · Core.begin零尝试纠正

父审计发现无进展inplace在Core.begin即可结束段，零尝试仍计真实决策/stall。已先加 `test_zero_attempt_stall_preserves_clock_and_terminal_does_not_bootstrap`，单测rc1/1failed/14deselected，失败在旧attempt_reward正数校验。随后允许非负attempted_steps/dt（负值仍拒绝），回放同步允许dt0，零尝试g1且终局不bootstrap。不虚造消耗时间。

同上完整回归命令最终84passed、2条件GPUskipped/13.08s/rc0，本节点15项。git diff --check、python3 -m py_compile各rc0。最新接口记录覆盖原“dt必须正数”的旧约束；父已通知该变化。update_sequences返回均有updated，结果与可选timing字段为JSON可序列化标量，不含tensor。仍review交父，无训练或新增运行任务。
