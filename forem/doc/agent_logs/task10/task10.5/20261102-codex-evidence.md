# task10.5 日志

开始2026-11-02T16:11:50.649490+08:00，实际派发gpt-6.1-terra/high；范围/独占文件见TASK；尚未执行。

2026-11-02：读取任务和父结果，旧真实执行journal各8条；仅旧事件保留初次68个有效槽，末次reset无法从决策日志补全。新增探针读取原始两批journal，baseline从种子101真实sampler捕获PcdEpisode并保留，再以factory对instrumented重放；每批与旧journal对照observation/candidates/selected/selected_prediction/actual/r_t/attempt/commit/termination/triggers，任一不等立刻失败；记录初次、prepare及每批结束行reset边界（包括末次）。计时wrapper采用嵌套wall inclusive/exclusive、独立GPU event inclusive；禁止相加。输入、上限32新决策、900秒已声明；GPU和真实环境未启动。`PYTHONPATH=forem/src python3 -m unittest task10.tests.test_profiling` 两项通过；初次RED因目标模块缺失，后GREEN；py_compile通过。宿主无torch，完整环境探针需父在容器验收。

父预审核要求修正非确定性候选wall诊断并按阶段归属。RED两项缺失API，GREEN后宿主 `PYTHONPATH=forem/src python3 -m unittest task10.tests.test_profiling` 4 passed；`python3 -m py_compile forem/scripts/task10_cost_probe.py forem/src/task10/profiling.py` rc0。期间曾有一次py_compile括号语法错误，修正后通过。唯一比较排除项与GPU stream区间限制列于RESULTS。未运行GPU探针。

父首probe于8真实决策后报旧observation键不等；只读CPU加载journal确认grid_uint8有、grid无。依据原journal存储exact_cpu进行双侧归一，保留唯一wall排除；增加2/1/24预算参数和硬检查。新增两项CPU测试先因API缺失RED，随后`CUDA_VISIBLE_DEVICES= ... python3 -m unittest task10.tests.test_profiling` 容器6 passed；宿主py_compile通过。未运行GPU或新决策。首失败及总截止由父管理。

应父要求补每个共同边界的观测/候选精确比较与JSON摘要，不增加决策；预期2+1批覆盖5/3/3，实际待父运行。新增摘要夹具RED缺API后GREEN，容器CPU unittest 7 passed，py_compile rc0；未启动GPU。

父执行后只读核算：修订baseline五边界slot 68+32+33+30+33=196；预测batch/row 1037/40948、attempt/commit 41893/41166；actual两批attempt/commit 2359/2299。instrumented只保存首边界比较且外层rc124，reserved24/completed16是陈旧快照，保守总决策预算32；末次reset 33是新重建补计。额外单初始reset profile rc0且旧首journal严格同输入，prediction exclusive各项求和与inclusive 39.686144秒完全一致；B3为0.469515秒（不是3.469515）。详细事实、限制和SRC-T10-012草稿见RESULTS。未重新运行测试/GPU、未修改共享docs。
