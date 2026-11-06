# task10.17.3 · 三检查点评估适配

负责人Codex子Agent；记录 2026-11-03T23:05:35.910867+08:00。实际模型/强度平台未提供独立可核实名称，未知。推荐GPT6.1sol/high、Sonnet5.5/high：新旧模型计数、初态和跨进程预算合同。可自主选模与先建档委派，本子独立完成；父统一GPU、真实预算和原件验收。

授权边界：仅新增scripts/task10_long_validation.py、scripts/tests/test_task10_long_validation.py及本子三文档/日志；不得GPU/真实交互/更新/实际freeze启动。已读根AGENTS、ENV/README/PROGRESS、17父/子三文档、16.3最终验收和旧执行/审计源码；保留其他未提交修改。

实现：显式task10-decision-boundary-v1读取2000/1000、5000/4000、10000/9000，校真实replay/ledger计数、9000 scheduler与48h原预算、KL .35、stage1、新初始0/0/9000及不可变index内容hash。沿用base.worker科学执行路径，本进程临时适配payload_state、fixture_check、12/1800 budget及初态比较，finally恢复符号；不改src/旧脚本。参照使用旧legacy independent-audit-v2及旧KL report-v2；原始初态typed hash在任何env.step前核对。

CPU核验先发现旧legacy审计实际名independent-audit-v2.json，显式纠正；宿主无matplotlib、容器有，sequence结束CUDA隐藏调用container curves。支持stopped_boundary终态与原run resume-summary，保留原training-summary并核worker-exit状态。

实际命令与结果：
- python3 -m py_compile forem/scripts/task10_long_validation.py：rc0。
- sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -m pytest -q --basetemp=/tmp/t10-17-3-long-eval-v6 /workspace/scripts/tests/test_task10_long_validation.py'：26 passed/1.57s/rc0，log forem/logs/task10/task10.17.3/cpu-tests-v6.txt。前面v1–v5各CPU迭代日志保留，无失败。测试从未创建真实env/训练更新/调用实际GPU或评估子进程；launch与sequence进程为mock。
- 旧参照原件只读CPU命令在reference-input-check.txt：legacy200文件与KL52文件、同12初态/模型均verified_reference_inputs/rc0，8.30s。只读取既有原件，没有新freeze/真实决策/更新。
- python3 forem/scripts/task10_long_validation.py --help：宿主入口可加载，rc0；git diff --check指定新文件rc0。

源码SHA256：long_validation=f4e70971866dd7e774d28953fb3929e54f423a1918176a1da6c103f54f390c81；tests=59b21b4ab007f1fcf0b11962edfdcc1254a5af2c0a6381a8a0c0adebd22870a6。

交接：状态review，父待复核。实际C尚未执行，26项测试不等于GPU/端到端验收；0新增交互/0更新/0GPU。后续父在B最终退出后调用sequence并核原始报告；D可再CPU读原件复算、更新共享台账/进度。无本子遗留进程。当前协议来源SRC-T10-042，新增CPU事实已送父统一登记SOURCES；不得当作训练效果/恢复门通过依据。

## 2026-11-03T23:15:38.545669+08:00 · 父复审修正组内报告截止

父发现sequence报告仅夹紧global deadline，若worker耗满原90分钟仍可新增最多300秒CPU报告窗口。已仅修改本子script/test/log：报告可执行条件与timeout同取min(group_epoch+5400, global_epoch+16200)，预留2秒kill grace；组截止标missing_group_deadline，全局较早则missing_global_deadline，不启动报告并保留checkpoint/worker原件，D可另做CPU只读补证，不延GPU。

新增四个sequence集成夹具，模拟组截止前10秒/已过以及global较早的前10秒/已过；前者报告timeout恰为8秒，后者无报告子进程且保留对应missing，检查点原件不变。子进程/时钟为mock，无GPU/真实环境/更新。

实际命令：sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -m pytest -q --basetemp=/tmp/t10-17-3-long-eval-v7 /workspace/scripts/tests/test_task10_long_validation.py'。结果30passed/1.59s/rc0，日志forem/logs/task10/task10.17.3/cpu-tests-v7.txt；git diff --check指定script/tests rc0。

当前SHA256：long_validation=9aa0e18d0a1da58baa4e6aeff497f201672a9e93b7463582400e919d8a4993d0；tests=c101e7bc7559b227c4ab9812dbdfbb17eac5927819e3a70a220a153a7de931c9。早先SHA与26项为历史，不覆盖原件。没有改src、共享文档或运行GPU；父A冻源不受本子script修改影响。
