# task9.11.13 · 流程

状态review；负责人Codex。推荐GPT6.1sol/high、Sonnet5.5/high，因跨阶段费用、区间和证据因果核验；实际模型/强度未知，委派请求sol/high。范围与授权见[TASK](TASK.md)、[SRC-1419](../../../../SOURCES.md#src-1419)。

递归规则：每层恰有TASK/PROCEDURE/RESULTS；本节点不再委派。顺序为父复算旧归档→.13必要实现与专用stdlib测试→冻结→父必要回归与.14独立原件复算→父核验。每次必要源码修改重新冻结，同SHA重新验证；旧PASS不迁移。所有原失败保存，不改旧保护/closure/release/evaluation。

1. 读取AGENTS、README/PROGRESS、父RESULTS §16、.11/.12三文档与20261104 cross-stage-review；父已保存168源before与旧GPU误计反例，实施只写本节点范围。
2. `gpu_costs`接受显式inert synthetic证据：`gpu_evidence.format=task9-lr-gpu-attribution-v1`，complete=true、synthetic_fixture=true、execution_allowed=false、scope start/end、devices与intervals。CPU设备和区间均为空；GPU仅preferred_gpu_uuid，区间在scope内且完整声明，不用payload wall填GPU。可含部分、离散、重复区间，按设备归并。真实external API未提供可核实设备归属，不支持以自报CPU替代，始终UNKNOWN。
3. inherited aggregate必须与有证据的并集相等，已包含的command GPU区间必须被该并集覆盖。static外费严格库存、dynamic source/event/journal/独立snapshot均核原件；GPU区间不随worker最外层payload去重而丢失。CPUcontrol候选包络只进入worker。
4. 已有inspect只认可明确授权设备；container从start到可信当前观察或已验证stop的完整持有窗口收费，含idle。与历史/外费区间取并集。新申请worker cap与GPU cap分别传入，supervise将GPU cap设为作业cap，不含CPUcontrol；active余GPU cap也不含control。
5. `costs.review(...,container_state=inspect)`只转交已有resource API，不创建监控或真实Docker操作；省略运行容器state时UNKNOWN。snapshot保留精确resource_observed_epoch、完整cumulative_gpu_intervals、原record/sealed/current inspect及独立已用/预留/剩余字段。remaining_resource_budget沿原接口为limit-used，remaining_after_reservations扣预留；准入再次实时核验。
6. v2以最近独立snapshot中的GPU container basis约束当前record与sealed inspect，禁止删除或改身份/设备/start。已Stopped的end不得更改/重启；Running→Stopped必须覆盖既有精确观察时点。snapshot review override也走同一核验；首basis亦须record/fallback、sealed inspect、current inspect三方Id非空一致，v3补此必要核验。静态旧容器无独立固定时序basis直接UNKNOWN；不新增legacy认证schema。
7. 标准库唯一专用入口`python3 -B forem/src/task9_lr/tests/test_gpu_accounting_stdlib.py`，覆盖实际worker链、CPU费用/控制、held GPU、旧令过期、新snapshot/后继、区间去重、边界、缺证/篡改与时序前进。`run_evidence.py`保留exact argv/cwd/env/stdout/stderr/exit/wall/source before-after；通过TASK9_GPU_JOINT_ARCHIVE归档临时原件并存映射/SHA。
8. v3固定源后父跑相关116项，.14复跑独立原反例及新GPU核验；任何失败先登记、修必要因果问题再重新冻结。只在父读原件核验后交付；真实执行始终NOT_READY。

当前170源冻结/最小diff、原件与剩余限制见[RESULTS](RESULTS.md)，方法与实测统一关联[SRC-1420](../../../../SOURCES.md#src-1420)。
