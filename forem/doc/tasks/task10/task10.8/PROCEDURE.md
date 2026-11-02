# task10.8 流程

递归规则：本节点恰有TASK/PROCEDURE/RESULTS三文档；继续拆分须先建子节点三文档，登记依赖、负责人和父验收。当前无子节点。

独占写入：forem/src/task10/gpu_diagnosis.py、forem/scripts/task10_gpu_diagnosis.py、forem/src/task10/tests/test_gpu_diagnosis.py，本节点三文档及对应独立日志；共享文档由父汇总。先读根AGENTS、ENV、task10三文档、SRC-T10-015及父日志。执行者可按难度选可用模型/强度并决定是否委派，先建档，子Agent共享父授权、总预算/截止，禁止自行GPU启动。父统一GPU1排期、验收原始证据。推荐GPT6.1sol/high、Sonnet5.5/high，跨模块状态核验需要；实际配置在RESULTS记录。

1. CPU测试先失败再最小实现，使用CUDA_VISIBLE_DEVICES空值、PYTHONPATH=/workspace/src、timeout120、pytest -p no:cacheprovider。测试合成小模型/回放，不采集、不算新真实数据。比较器使用稳定key排序和tensor字节比较（包含signed zero）。clone_memory深拷贝learner/replay对象图，不调用save/load或load_state_dict；检查optimizer参数指向克隆模型，原对象storage不共享。
2. 父加载旧recovery-fixture/derived-fixture.pt一次，验证其是已更新Adam的显式派生fixture；不制造1000预热计数。源非空真实回放保持只读；派生的32anchors并非32条独立真实数据。
3. 从同一内存前态，纯内存组创建两个deepcopy对象，各更新一次；存取组同样复制两个对象，仅右侧通过真实save_checkpoint/load_checkpoint。每组核对完整state、runtime、train模式、参数device/stride/梯度开关、全部replay、RNG及sample身份/原始prefix-burn-in-steps；恢复返回的RNG单独保留核验，禁止先重置掩盖缺陷。前置不等不执行该组更新，记录失败。
4. 每次更新前写attempts.json计数，包括抛错尝试；参数hook克隆保存每次backward得到的裁剪前梯度。保留loss、裁剪后梯度、更新后完整state、Adam参数名、global和sample RNG；GPU同步包围fixture_update计时。hooks克隆本身有开销，此处不是训练吞吐基准。
5. 每组两条更新结束保存原始.pt和progress.json；diagnosis.json列每叶逐位/最大绝对差、首差异、计时、SHA及实际设备。首差异为观察阶段顺序再按key稳定排序，不代表CUDA kernel实际执行顺序。默认一次4updates；必要deterministic再4updates、必要原设置重复再4updates，最多12。deterministic必须Python启动前设置CUBLAS_WORKSPACE_CONFIG=:4096:8，并设置torch.use_deterministic_algorithms(True)、cudnn.deterministic=True；TF32/benchmark仍false。
6. 父统一同一GPU相位绝对monotonic截止（首测+最多300s、且不晚于全局1800s截止），各进程用timeout包围，后续不得重置预算。入口参数：--checkpoint旧fixture --output新独立目录 --deadline-monotonic同一截止；deterministic追加--deterministic。每次4fixture更新、0真实，异常以attempts/progress及父总账保守收费，禁止自增预算或重启长训。

输入输出和原始命令见RESULTS及[独立日志](../../../agent_logs/task10/task10.8/20261102-codex-gpu-diagnosis.md)。父验收保持严格逐位口径；默认差异与确定性配置下结果分别报告，真实batch8边界交task10.9/父，不主动截短回合。
