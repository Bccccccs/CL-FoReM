# task10.8 结果

2026-11-02，状态review，三组GPU诊断及CPU原件复算完成，待父核验。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high；跨模块状态/数值因果核验需要。父派发sol/high，当前平台精确模型/强度不可自证。授权/决策依据[SRC-T10-015](../../../SOURCES.md#src-t10-015)，本轮结果待父统一登记SOURCES，不作为既有通过结论。

已新增gpu_diagnosis.py、task10_gpu_diagnosis.py、test_gpu_diagnosis.py；不改recovery.py、runner.py、共享文档。测试CPU使用容器forem-task10-runtime、CUDA_VISIBLE_DEVICES空、PYTHONPATH=/workspace/src、timeout120。

CPU证据：首次新增模块不存在时pytest收集rc2；5项夹具后运行rc0、5 passed/6.26s。测试覆盖严格signed zero比较、optimizer克隆别名与storage隔离、CPU双对照逐位、原对象和RNG不变、空Adam拒绝、存取返回RNG被篡改时更新前拒绝；其中RNG反例先失败（DID NOT RAISE），修正后通过。第6项非有限相等字节JSON安全测试先失败（NaN max_abs），按父要求GPU三组测量期间冻结代码；全部GPU结束后修复：字节相等max_abs=0，不相等且非有限的差值max_abs=null并保留finite=false。最终定向CPU测试rc0、6 passed/6.28s。GPU输入本轮全部有限不受该修复影响；测量版与最终版SHA分别记录。

完整task10 CPU回归曾在10.9并发red阶段运行：18 failed、67 passed、2 skipped/20.76s；11项test_lower（all_frozen_hashes_and_geometry、real_actor_matches_original_sac_and_freezes[cpu]、8项metadata_mismatch_rejected、invalid_inputs_rejected_and_no_stochastic_path）因未设TASK10_ARTIFACT_ROOT，容器硬编码宿主inventory路径不存在；另外7项是10.9当时的journal字段/terminal core反例，已向父报告。父指示用TASK10_ARTIFACT_ROOT=/reference、等10.9实现完成再由父全套验收；本节点不修他人文件。该失败运行没有GPU/真实采集。

GPU默认结果由父唯一启动，rc0，输入sha256 b9ddd64e125392602dc7ed1e734df2fc4b0939daad21a32b01be137a9274abcf；原件位于forem/results/task10/t10-gpu-batch8-20261102/gpu-default/{diagnosis.json,memory_vs_memory.pt,memory_vs_checkpoint.pt,actual-checkpoint.pt,attempts.json,progress.json}。共4fixture更新、0真实，进程9.9709280785s。两组更新前state4163个tensor叶、sample5472叶逐位相同；loss/global RNG/sample RNG相同。纯内存组裁剪前4梯度叶不同，稳定排序首为model.vcm.f_enc.cnn.0.bias[0]、max_abs5.4569682106e-12；更新后state10叶不同，首model.vcm.f_enc.cnn.2.weight、max_abs3.7252902985e-9。存取组裁剪前5梯度叶不同，首同bias梯度、max_abs2.9103830457e-11；post_state13叶不同。

目前证据只表明差异无需save/load即可发生，观察首阶段为卷积裁剪前梯度；不认定检查点恢复引入差异，不冒称具体CUDA kernel根因。deterministic和原设置复现见以下最终汇总。默认严格下一更新验收仍失败。

三组最终结果（GPU均父统一启动；每组4fixture更新、40个loss位置/更新、0真实；严格字节判等，不用容差）：

|运行|纯内存组/存取组|裁剪前不同梯度叶|不同post_state叶|进程墙钟s|新进程首更新s|后三次更新s|
|---|---|---|---|---|---|---|
|gpu-default|均exact_mismatch|4 / 5|10 / 13|9.970928|1.064186|0.092946 / 0.093046 / 0.090655|
|gpu-deterministic|均verified|0 / 0|0 / 0|10.734226|1.260951|0.136963 / 0.138486 / 0.136430|
|gpu-default-repeat|均exact_mismatch|5 / 4|11 / 11|9.943892|1.055803|0.095489 / 0.096687 / 0.092599|

六组更新前state、sample、loss及RNG均完全相等。默认和重复的稳定排序首差异均为root.model.vcm.f_enc.cnn.0.bias[0]裁剪前梯度；重复纯内存/存取首差max_abs分别1.8189894035e-12 / 1.4551915228e-11。默认纯内存/存取裁剪前最大差5.8207660913e-11 / 8.7311491370e-11，Adam最大差均7.2759576142e-12；重复两组梯度最大差均5.8207660913e-11、Adam最大差均7.2759576142e-12。各差异张量完整名称、逐位标志和最大差保留原JSON/原.pt，紧凑复算只保留首差/最大差与计数。

复算原件：forem/results/task10/t10-gpu-batch8-20261102/gpu-analysis.json（38,903字节），新增forem/scripts/task10_gpu_diagnosis_report.py从三份诊断和六份.pt重算所有比较树，完全等于原诊断，退出0，输出`controls 6 updates 12 raw_recomputed True`。命令：

```bash
sg docker -c 'docker exec -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime timeout 120 python3 /workspace/scripts/task10_gpu_diagnosis_report.py --root /workspace/results/task10/t10-gpu-batch8-20261102 --output /tmp/task10-gpu-analysis.json --verify-raw'
sg docker -c 'docker cp forem-task10-runtime:/tmp/task10-gpu-analysis.json /home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-gpu-batch8-20261102/gpu-analysis.json'
```

首轮复算检查均通过但写namespace失败rc1（容器uid与宿主目录权限不匹配），改写/tmp后成功；两次均CPU读取原件、0新增更新。未修改旧账本、旧数据、三份GPU诊断或六份原始.pt。

三次实测模块SHA均557d44a15e75d44dfcf19c0031685641520880b4a748c2f37d7c094d18aa2c7d；非有限JSON修复后模块SHA349e6d9c98d3aa769e3860e8cbfda6780d12b133388c306eacfcbe99c3494606；GPU入口SHAe0c2b528d8de165f9069e951e6905d7b66b5008636cf5b3c6f859d4066eaa2af不变。复算脚本SHAd4ee861f845e36f6d1e234b9b08bdff440a59e7d0ef24be3cb1a80c1cf93d17d，结果中也记录脚本/输入/原件SHA。最终py_compile和git diff --check均退出0。未自行启动GPU、未提交。

限定结论：纯memory重复本身也差；确定性组合设置在同一夹具消除了两组差异；定位观察层为CNN反向参数梯度，具体CUDA kernel原因未定位，不能从此区分deterministic algorithms、cuDNN flag、CUBLAS工作区三项各自贡献。只支持本旧夹具下一更新，不能外推真实batch8在线更新或正式训练全部通过。耗时包含hooks与夹具重建；保留每次新进程冷首和整个进程时间，不能仅用热更新估工期。12fixture更新已到上限，禁止再GPU。

交接：目标/授权见TASK，当前负责人Codex子Agent；实现、CPU定向6项和三组原件复算已完成。父统一更新SOURCES/PROGRESS并做最终核验；batch8真实边界与恢复属于10.9/父。没有本节点运行中进程；没有额外GPU请求或待执行训练。本节点review，默认逐位失败保留，后续是否采用确定性配置属于决策者判断，不在本次自行实施范围。


## 父核验与最终交接

2026-11-02，Codex：父已核验三组原件与GPU12更新总账；默认纯内存亦差、确定性组合两组逐位一致，具体kernel未定位。最终CPU组合163passed/3条件skipped；本节点原始测量hash保留，代码后续非有限JSON修复与GPU测量明确区分。 [父结果](../RESULTS.md) · [来源](../../../SOURCES.md#src-t10-018)。推荐GPT6.1sol/high、Sonnet5.5/high，因跨模块数值/状态边界核验；当前无本节点运行任务，状态review。
