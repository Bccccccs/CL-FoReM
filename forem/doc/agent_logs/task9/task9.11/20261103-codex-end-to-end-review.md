# task9.11 端到端继续审核

开始：2026-11-03T22:08:30.654361+08:00；负责人Codex，实际模型/强度未知；推荐GPT6.1sol/high、Sonnet5.5/high（跨入口/进程/预算合同审查），本轮未委派。用户要求继续审核、集中解决返工原因。本轮只读源码/原证据、必要标准库静态分析与文档，不修改实现，不运行项目测试/模型/环境/Docker控制/训练。

沿用task9.11编号，最新子节点.7/.8；不建重复实施节点。已读最新PROGRESS、父RESULTS、.8三文档结果和关键实现；继续核实际worker G1、supervise/准入/prepare/评估/审计接口。保留现有dirty，写共享文件前重读增量追加。准备仅写本日志/审核JSON、父RESULTS、SOURCES、PROGRESS。

## 结论与返工原因

**NOT_READY；此次确认两个新的具体代码缺口，以及三个必须在同一交付中闭合的集成/合同缺口。** 旧资源检查期间watcher死亡反例已由launch_gate/request-ack修复，接受此前四反例和40项替身在其覆盖范围内的结果；不重复把已修问题当新问题。直接核.8裁决29项证据SHA全匹配，160项当前源码/配置保护清单无变化。本次只用AST/读取/hash，不执行测试或真实程序。[证据](end-to-end-review-evidence.json)

返工的主要工程原因：测试只覆盖局部函数/替身，真实worker入口未纳入同一验收；实现白名单禁止改worker，使新增测试与旧G1收集范围失配；另外“完整计费”尚无有限、可实现且获接受的结束边界，添加outer后仍要求再证明outer自身退出，正常成功路径一直不可达。独立审查正确写了NOT_READY，但“准备done”不等于整体修复完成。

### R1 · P1 · 实际G1收集路径必然撞上标准库测试的禁导入断言（新增）

`worker.py:60–64`执行pytest扫描整个`src/task9_lr/tests`；新`test_supervision_stdlib.py`符合收集规则，其`test_no_forbidden_runtime_imports`禁止sys.modules中出现pytest/torch。同目录conftest显式导入torch/pytest并activate。这意味着即使先修复续接门，按现有G1命令运行时该断言仍会失败，消耗G1资源后再STOP。直接python运行40项的PASS不能覆盖真实pytest入口。此为源码确定性矛盾，未实际执行G1。

一次性修正要求：冻结两个不同测试集合和入口——监督stdlib直跑；GPU科学合成G1只收集已审的明确白名单（例如既有test_contract.py）。不要删除禁导入断言或让stdlib测试在GPU入口“skip”冒充覆盖。核worker实际argv、conftest、依赖与每个收集项；启动真实GPU前先用标准库静态/替身证明两个集合不相互侵入。未来修复范围必须允许必要的worker G1收集行修改，训练逻辑仍不可改。

### R2 · P1 · 正常成功无法闭账或进入下一阶段（既有但需整体解决）

`supervise.py:405`无条件raise；`admission.py:120–122`无条件拒绝所有PASS；`prepare`也明确拒绝。失败时阻断是正确的临时措施，但目前没有任何合法完成状态/接收格式，正常路径也永远失败。单测证明“都拒绝”不是可运行性的证明。

修正前先冻结有限状态机：PREPARED/RESERVED/RUNNING/WORKER_EXITED/CLOSED或FAILED/UNKNOWN，规定每个状态的唯一写者、身份、时间字段、hash、允许后继与计费时刻。正常流程必须有实际可达的CLOSED路径；失败、缺证、旧PASS不能获得该路径。不得简单删除当前raise放行。

成本边界需先明确：被测完整作业进程从启动至实际wait返回的包围区间，包含其保存/退出；长寿命外部监督的控制/发布成本另列账本，并由有独立开始/结束边界的资源会话结算。不要无限加“外层的外层”证明所有审计者自己的退出。若此边界与已冻结“全wall”合同不同，必须写出差异并取得明确处置；本审核不擅自修改口径。完整训练成本与审查/等待仍都报告，不把未知填0。历史不可恢复的exit继续UNKNOWN，与未来计费方案分开；需要保守计费时只能用原证据能证明的包围区间/并行度推导并注明适用范围，不能凭空指定余量。

### R3 · P1 · 最外层wait超时绕过异常封口和停止（新增静态缺口）

`outer_wait:249`的`process.wait(timeout=cap+45)`位于后续异常收集/停止逻辑之外。TimeoutExpired直接抛出，既不执行该函数后面的backend.stop，也不写lifecycle错误记录；dispatch亦无对此路径的finally封口。若子监督卡住/故障，outer作为最后兜底恰好失效。现有SIGTERM/缺wait用例不等价于wait超时。此为静态异常路径结论，不声称实测有遗留worker。

修正要求：把outer等待超时、读取损坏、进程身份读取失败和发布失败纳入同一有界异常封口；只停止精确绑定任务，实际wait或明确UNKNOWN；不能将cap+45继续叠加未计的停止/退出时长。明确最外层进程退出时后台链应停止还是由持久监督承接，并据此测试，不只杀新命名的owner子进程。杀死所有监督/主机故障不得承诺自动写出终态，重启时须由外部恢复检查隔离未知。

### R4 · P1 · 续接只是候选，入口、依赖和累计账本必须一起适配（既有集成缺口）

prepare候选明确非执行，没有execution adapter。`protocol_read/evidence`仍硬编码旧run/path，`prerequisites`仍要求旧四smoke和C/L整门PASS，源已变而旧证据不能搬成新PASS；host jobs仍从G1和四smoke重列。若只把protocol或prepare放开会继续在后续门失败，甚至拟重跑已满smoke。

执行前必须给可测试的阶段DAG和新旧证据引用类型：新代码门/G1→有明确处置的C证据组合→L ON→四个从头profile/remaining→开发→一次final。历史原件只读引用，不复制为新执行PASS；新账初始化携带旧4000/980及累计worker/GPU/存储。核host与container路径映射、reviewer身份、release/run/hash、外部输出根（旧protocol只有.3/.4，之后.5–.8与父成本不能漏）、实际worker/test manifest与audit入口。旧C整门如何处置是科学证据/执行完整性组合的明确合同决定，不能由代码默认解决；保持原门不变则没有额外196预算，不启动。

### R5 · P2 · 最终描述性审计的配对器遗漏右侧重复检查（新增小缺口）

`audit.py:paired`只核len(a)==len(left)及左右键集合相等，未核len(b)==len(right)。开发阶段audit又未逐域强制100/96，因此右侧追加重复row仍可标complete并通过配对，rates的分母却已改变。final入口的固定长度限制缩小该风险，但通用paired与development仍有缺口。此工具注明不是独立release，降低即时影响；仍需在同批修复中检查双侧唯一性、各checkpoint域分母/expected身份，不让描述性报告误导审核。以纯JSON构造重复/缺失case反例，不运行环境。

## 一次交付的验收矩阵（后续实施要求，本轮未执行）

|层|至少证明的成功路径|至少证明的失败路径|
|---|---|---|
|实际CLI/测试收集|prepare候选与未来execution清楚分离；G1实际argv仅科学合成白名单；stdlib单独直跑|目录新增测试不会混入G1；错误role/phase/path/code/release拒绝且零启动|
|启动|实际host dispatch→owner→guard→watcher→替身worker，生产调用链不绕过；request/ack身份一致|resources内watcher死/terminal/deadline/owner死，启动标记永不创建|
|退出与计费|正常client完成→全部约定wait/包围区间→CLOSED→独立准入下一合法阶段|outer wait超时、外层被杀、守卫死、读取/发布盘错、缺receipt、未知成本均不放行；停止/残留如实记录|
|幂等与版本|同一已闭合任务重复请求不启动、不重复扣费|旧FAIL/旧PASS/新SHA不能伪装成新CLOSED；并发请求只有一个启动者|
|续接|只读历史引用和累计余额下，新namespace的合法后继阶段可达|重跑smoke、额外C ON、预算超限、过期令、旧目录可写、漏计外部成本均拒绝|
|科学与最终审计|四配置只有LR轴差异，正常C/L合成统计与固定成功门一致|双侧重复/缺case、分母错、旧验证充test、包装归因混淆拒绝|

要减少返工，最终独立验收必须沿真实入口跑一个**零模型、零环境、零真实Docker的端到端替身闭环**，包含正常完成进入下一阶段；不能通过mock掉admission/closure来假造闭环。底层Docker/worker可替换，协议校验、状态机、计费、签字校验必须使用生产函数。真实GPU/容器/成熟profile另有已批准门；替身闭环不替代它们。修复者交一张需求→实现→测试→证据表，独立验收后冻结同一SHA，不再把多个互不相容版本的PASS拼一起。

## 执行顺序与边界

先形成完整边界/旧C/历史成本的具体合同处置，再在同一批必要范围内修R1/R3/R5及R2/R4接口；最后进行上述真实调用链替身验证与独立审查。纯代码缺陷可以准备修复，但在合同仍PENDING时不得声称整体已修好。此前对子任务禁止改worker等范围，需要后续派工明确扩大到必要入口行和审计校验，不能靠实现者越界“顺手修”。

本轮未实现上述修正或改变合同；没有额外训练额度/窗口，没有新回合。下一阶段预算必须用当时实数核算，22:04旧快照不是新的可用额度。继续保留旧STOP，所有科学效能仍未检验。没有本次后台任务；git diff/保护核验仅限审核文档和既有源码不变。

## 最终校验 2026-11-03T22:12:50.117521+08:00

R5另作标准库AST隔离提取纯paired函数的合成字典核验（没有导入项目模块或运行测试套件）：左1行、右同key2行被接受，返回both=1，原件存end-to-end-review-evidence.json。其余源码缺口仅静态核查。29项独立原证据hash一致；160源码/配置保护清单无变化，git diff --check通过。仅本日志/审核JSON与保护清单、父RESULTS、SOURCES、PROGRESS更新。
