# task10.17.2 独立执行记录

## 2026-11-03T22:59:05.673100+08:00 · CPU交付待父验收

已实现，状态review。实际模型/推理强度平台未提供可核实身份，未知；推荐GPT6.1sol/high、Sonnet5.5/high，恢复/预算/跨run合同。未派下级，无GPU/真实交互/诊断更新/正式训练；父负责A与B启动。

独占代码：entry.py新增显式long-10k profile并路由long_training；新long_training.py（LongBudget/UTD/一致检查点与训练worker）；kl_10k.json；task10_long_run.sh；task10_long_launch.py；tests/test_long_training.py。旧smoke/trial limits、runner、learning不改。

CPU专项与旧entry回归：**37 passed / 6.20s / rc0**，原件forem/logs/task10/task10.17.2/cpu-tests.txt。命令：`sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -m pytest -q --basetemp=/tmp/t10-17-long-v2 /workspace/src/task10/tests/test_long_training.py /workspace/src/task10/tests/test_entry.py'`。py_compile、bash -n及git diff --check均rc0。夹具不生成真实消费，launcher测试替换Popen为CPU假进程。核实固定10000/9000/172800与旧profile边界、1000预热/9000欠账计算、9000指数LR端点1e-6、旧200 scheduler拒绝、256/2000/5000/10000保存点、不可变产物+上一index、partial拒绝、原epoch恢复和已有run拒新建。

实际容器只挂物理GPU1（docker inspect DeviceIDs=[1]），新launcher使用CUDA_VISIBLE_DEVICES=0指容器内唯一可见卡，TASK10_PHYSICAL_GPU=1作物理证据；此为只读环境核查，未加载GPU。

必要限制：完整端到端保存/恢复、正式初始化相同、实际GPU更新、保存规模成本与48h可行性仍由父A验收；CPU通过不等于放行。代码未提交，保留全部既有未提交修改。后续接口与产物见PROCEDURE；训练停止或任何中断不自动重跑，无法核清消费只保留partial。
