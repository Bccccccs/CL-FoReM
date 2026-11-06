# task10.16.3 结束检查与CPU报告修复

2026-11-03T22:26:14.121155+08:00 开始；Codex；实际模型/强度未知，推荐GPT6.1sol/medium、Sonnet5.5/medium，需核验报告接口与原件验收；执行者可自主选模和先建档委派，本次独立执行，父统一原件/预算。用户要求“检查”，沿既有完成交接授权，只检查已结束唯一run并修复必要CPU报告，不新增真实回合/更新/GPU，不重启。

run t10-kl-eval-20261103-s101，worker complete/error null，12完成/21决策/0更新/0缺失/0在途，launcher process_exited/rc0，driver finished，GPU无compute、无本run活进程。原报告failed，唯一issue是snapshot_checks(run, expected, rows, budget)误传4参给实际3参函数；原19专项report测试stub接受任意参数，漏掉该实际接口。保留原报告、冻结scripts/manifest/launch/weights；只新增独立CPU报告适配器与针对性测试，新报告另存v2，补原件核验后更新本节点/父RESULTS、PROGRESS、SOURCES和本日志。既有dirty改动保留，分支正确，HEAD91f538c。

## 2026-11-03T22:30:50.608942+08:00 · CPU报告修复后完整验收，交决策者审核

**当前状态review：工程执行与原件复算通过；最终审核归当前决策者。** 依据[SRC-T10-040](../../../../SOURCES.md#src-t10-040)，本节取代22:19时“完整验收未通过”的当前状态，原failed报告/交接和历史记录保留。实际执行者Codex，具体模型/强度未知；推荐GPT6.1sol/medium、Sonnet5.5/medium，涉及原始终态/报告接口核验。可自主选模与先建档委派，本次独立完成，父统一GPU/预算/原件验收。

原报告的snapshot_checks参数数量错误已通过独立CPU适配器修复，原冻结脚本不改；3项实际审计接口测试通过（3passed/1.36s/rc0）。修正版report-v2.json及父parent-check-v2.json均 **verified_complete、issues=[]、rc0**。完整12/12、缺失0、预留21=完成21、在途0、更新0；worker complete/error null，launcher正常退出rc0；12初态执行前匹配、独立原始快照/首次观测候选审计、冻结权重和eval/no_grad/记忆复位均通过。321冻结输入、254训练源文件、70检查前原件SHA均未变；训练源launch残留running及原外层退出码缺失仍原样保留。

|比较项|旧trained|新KL trained|旧uniform|
|---|---:|---:|---:|
|严格成功/12|0/12|10/12（83.33%）|10/12（83.33%）|
|sparse、standard|0/6、0/6|5/6、5/6|5/6、5/6|
|原地选择/本组决策|52/52|0/21|0/19|

**原地行为是否改变：改变。** 本轮所有21次真实决策均选移动候选；12个相同初态均从原地logit领先转为落后：旧范围+0.185466～+0.453505、均+0.297570；新范围−0.992232～−0.452743、均−0.715388。逐图精确值沿用上节及initial-logit-comparison.csv。原地比例是各自完整轨迹描述，logit比较仅用同12初态，不逐步比较分岔后的轨迹。

**任务成功率是否提高：相对旧trained提高，0/12→10/12（+83.33个百分点）；与旧uniform持平。** 配对新对旧trained为胜10/负0/平2/缺失0；对uniform为胜0/负0/平12/缺失0。自然结束原因：10严格成功、2失败上限、0停滞；失败图sparse00004为20次self_collision，standard00000为20次ik_rejected，其他碰撞归因0，按实际attempt及Core优先级核验。工程检查通过不代表普遍方法有效，单种子12validation场景限制保留。

实际唯一GPU执行22:06:51.829083–22:19:18.778081+08，launcher wall746.948999s（12m26.949s），预算90min未用尽；无本run活进程、GPU compute为空。没有重跑评估，没有新增真实交互/更新/GPU。两策略训练规模虽匹配，后续采样轨迹随策略变化，不能据此把改善归于唯一因果或保证泛化。

原件、精确命令及版本：run/report-v2.json、parent-check-v2.json、report-check-exits.json、handoff-v2.json为本次完整补证；run/report.json、handoff.json保留初次失败。适配器SHA `9353463e6480e6ada57ee94786815bfa6327e875acc52b0d8e9dd7c8a0a2d1f8`；report-v2 SHA `681b4725534ec574f9d1a8c0b516fbff6bb891cf4207909e70f70e2ca8bf35c8`；parent-check-v2 SHA `35fbe863860b1e17e4bb16f8a5d694f594d1e0132cf0fd7a2ffcc726ed3a56f5`；原manifest SHA仍为a1901e2f4efe714f0640003309eaa2faae018a82779e64f13a53614b05d76eff。下面三条实际CPU命令均0新增交互/0更新：

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -m pytest -q --basetemp=/tmp/t10-16-3-report-v2 /workspace/scripts/tests/test_task10_kl_validation_report_v2.py'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -u /workspace/scripts/task10_kl_validation_report_v2.py --run /workspace/results/task10/t10-kl-eval-20261103-s101 --output /workspace/results/task10/t10-kl-eval-20261103-s101/report-v2.json'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -u /workspace/results/task10/t10-kl-eval-20261103-s101/parent_check_v2.py'
```
均rc0；报告适配器拒覆盖已有输出。仅再次只读复算时使用新的--output路径，不重启worker。

交接：本轮已无运行任务；完整验收条件通过，交当前决策者复核report-v2、parent-check-v2与handoff-v2。没有擅自新增训练规模、场景、功能或下一实验。原外层训练退出码缺失属于保留限制，不伪造补写。
