# task10.11 流程

递归规则：本节点恰有TASK/PROCEDURE/RESULTS三文档，无子节点；若拆分，先建子三文档并登记编号/顺序/依赖/负责人/父验收关系及链接。执行者可自主选平台模型/强度及独立完成或建档委派，全部共享父授权/预算/截止。本节点由Codex独立完成，父负责runner.py接线、统一复核及唯一GPU/真实运行。[授权SRC-T10-021](../../../SOURCES.md#src-t10-021)。

推荐GPT6.1sol/high、Sonnet5.5/high，理由为跨模块时钟与确定性合同；派发配置GPT6.1sol/high，当前平台实际配置不可核实，记未知。

1. 读取根AGENTS、ENV、README、PROGRESS、task10三文档、SRC-T10-020、本节点三文档及父日志。核对分支/HEAD/工作区/容器，不停止已有进程。独占范围见TASK，不覆盖父/其他子Agent。
2. 先RED建立CPU反例，再实现entry无torch顶层导入、显式profile/config/limits、实际确定性设置与版本报告、Budget硬截止字段；shell在首个Python前设置CUBLAS并进入entry监督。
3. `resolve_profile(*, run_profile='smoke', config=None, seconds=None, max_decisions=None, max_updates=None, phase='train')`返回`run_profile/config_path/config/config_sha256/seconds/limits`；limits含decisions/updates/training_seconds/paired_seconds。smoke允许短诊断，支持entry-check；online-trial只支持train，必须25200/1200/200。config与批准的对应profile内容不符即拒绝。环境物理profile仍为sync_v5，不混用run_profile。
4. shell保留或创建原`TASK10_STARTED_EPOCH`，先`export CUBLAS_WORKSPACE_CONFIG=:4096:8`，再启动entry。entry.supervise用原epoch计算TERM=hard−2、KILL=hard，并向runner传原`TASK10_STARTED_MONOTONIC`及hard epoch/monotonic。旧epoch过期或已无TERM窗口时返回124，不启动runner。runner.main应调用`launched_from_environment()`，不能再减一次elapsed或创建新起点。
5. 父runner用`getattr(args,'run_profile','smoke')`等兼容旧CPU SimpleNamespace；Budget传resolved profile，Budget.deadline不减20。父另定义work_deadline=hard−20用于环境与工作循环，合同分别列hard/work/cleanup。在线禁止resume/stop_at_boundary/boundary_reference由父验证。entry的unknown参数（例如fixture-source）透传runner。
6. `initialize_determinism(seed, require_cuda=True)`验证CUBLAS环境，再设置deterministic algorithms、cudnn deterministic、TF32=False、benchmark=False、torch threads2及Python/numpy/torch种子。默认要求CUDA，禁止回退；CPU测试显式require_cuda=False。返回runtime_report，含实际Python/torch/numpy/CUDA/cuDNN、CPU线程/亲和、设备、确定性flags；CUDA路径另记录nvidia-smi返回码/driver/GPU信息。此处设置依据[SRC-T10-020](../../../SOURCES.md#src-t10-020)，GPU行为仍由父核查。
7. CPU单命令cap120秒、CUDA隐藏、独立basetemp；原件落logs。最终独占范围实际命令如下（已执行，见RESULTS）：

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e TASK10_ARTIFACT_ROOT=/reference -e PYTHONPATH=/workspace/src forem-task10-runtime timeout 120s python3 -m pytest -q /workspace/src/task10/tests/test_entry.py /workspace/src/task10/tests/test_runtime.py --basetemp=/tmp/task10-11-final'
```

错误/超时不改总预算或重启。先前宽测试遇到其他Agent并行RED及环境路径失败，完整保留，不能删失败后声称全套通过。父通知后不再启动额外套件；全部源码冻结后由父统一全套与预检。[证据SRC-T10-022](../../../SOURCES.md#src-t10-022)。
