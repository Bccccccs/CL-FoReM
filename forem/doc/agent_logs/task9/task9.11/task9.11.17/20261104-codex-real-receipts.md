# task9.11.17 真实收据与入口适配

2026-11-04T10:43:46.328839+08:00开始，负责人Codex，实际模型/强度未知；推荐GPT6.1sol/high、Sonnet5.5/high（真实计费/旧账/入口因果）。用户采纳前轮具体推荐，授权原件见[user-approval.json](user-approval.json)。

边界：旧C组合及局部核销已批准；其余UNKNOWN不获笼统豁免。只做必要实现/专用标准库验证/真实CPU收据和协议草案/独审；无真实GPU/模型/环境/Docker控制/执行令，不延原截止。基线171源冻结3ae8183a…97d3ad2，分支codex/task9-lower-improve/HEAD d198e5c，现有dirty保留。task10 GPU1 PID970022正在训练，GPU0无compute；不触碰。

拟处理：forem/src/task9_lr必要收据与草案模块、admission/gpu_costs等必要读取适配、forem/scripts/task9_11纯准备CLI与专用stdlib测试；本节点/独审节点三文档、独立日志、父三文档、PROGRESS/DECISIONS/SOURCES。新实验results/logs namespace只在草案声明，不创建。

## 2026-11-04T10:56:58.248623+08:00 · 首轮实现/验证与冻结

新增real_receipts.py：真实root启动到actual wait、返回码/信号/超时、PID/start_ticks/boot、固定epoch↔monotonic锚、stdout/stderr与source前后不可变拷贝；失败也留实际费用。root wait不自证descendants、设备、发布者退出或完整会话，以上始终UNKNOWN。输出用regular files避免逃逸后代持pipe导致无限communicate；timeout仅杀自己fresh process group，root.wait最多额外1s不能返回则保未知。1s是本准备工具退出等待的工程选择（非科学参数/实测OS硬上界），不据此允许真实任务。

设备读入接到生产gpu_costs.evidence/command：真实source必须指向真实wait、成本与时钟字段精确一致、独立reviewer绑定前后read-only inspect收据，精确container ID/Docker exec/UUID/时序与配置一致；CPU空集需strict runc/非privileged/无host设备与控制挂载的分配原件，host CPU标签不接受。当前开发root waits没有这种完整设备依据，其GPU仍UNKNOWN。没有新增任何真实GPU/容器控制或设备工作；此处只是schema/reader原语，未来真实设备路径仍待实际验证。

execution_draft.py与prepare --execution-draft生成真实新格式草案：已批准C组合/1800政策、旧账消费/unknown、完整源/科学四配置/三个输入manifest、新results/logs身份只声明不创建、11节点顺序DAG（G1/LON/四profile+remaining/final）、数值control=None、stage_releases空。生产protocol_read识别校验，prepare/supervise/worker与public resource/release读取在执行前拒绝；不可执行不等于生产训练链适配已全通过。

首次20项专用测试rc0，第二次补生产入口与新源21项rc0；原SRC1423矩阵未复跑。精确argv/rc/wall/输出/source原件见commands/incremental-tests-v1和v2的wait-receipt.json，内嵌测试子wait不额外计费。早期无收据的build只读检查0.452262315s仅工具输出下界，无全会话封口，保UNKNOWN，不补0。

冻结175源SHA22064fd70b6ad7c8fab7676f623c32693484d622ab48b10ff3e79fbb7fa8754e，见freeze-v1.json/frozen-source-v1；相对171基线只改prepare.py/admission.py/gpu_costs.py，新增receipts CLI、两模块、专用test，共3改4增。科学/worker/训练/记录器/环境与四配置未改。该源交独审.17.1；父不自签独审。

真实草案execution-protocol-draft-v1.json已由准备CLI生成，实际command=commands/draft-v1/wait-receipt.json，exit0；这是review日志文件，未创建草案声明的results/logs namespace，也没有release/真实运行。草案account包含此前两次外包测试实际wait，生成自己及此后费用须在最终新快照再加，不隐去尾。

## 2026-11-04T11:01:00.317827+08:00 · 独审v1失败保留与v2修复

独审v1共22项19过3FAIL，CPU[]错误接受宿主shell替换/换行/附着分号；另2项缺/未来StartedAt也误接受。全部只惰性JSON，未执行字符串里的Docker/GPU命令，原raw/stderr/两外包失败wait收据保留。父只修必要共同路径：sg shell严格要求shlex.join(shlex.split(raw))==raw；CPU/GPU共同先校验带时区非空StartedAt≤before observation，再分支。不是加标签把设备缺证改PASS。

为预算下界不因并发/嵌套不明误加，草案列全部root wait实测sum，但只按其时间区间并集计新增安全下界；并发worker/parent关系与完整会话仍UNKNOWN，不当精确累计账。新receipt仅限本PREP_RUN和本日志root，任何别任务费用不得借run_id/时间迁入。

父当前22项rc0；新冻结175源SHA46218cc54e5f88ae0b38953ddcb5d6d80625161e13264b80b34c8dd0c423f587（freeze-v2.json/frozen-source-v2）。v1源/草案与所有失败保留，v1不作为当前验收。v2交独审复核五个原反例及新增边界。

## 2026-11-04T11:09:10.558989+08:00 · 父接收与停点

独审最终175源46218cc5…f587、28项通过、518引用；父parent_acceptance.py只读原输出/元数据/原件并全部核真，未重跑检查。正式独裁SHA472909aa2a414b3cd1565b69f8814415d90822d56d563424318a0cd0b98234d4。独审6次top wait8.798099545762s含两个独审失败、finalizer与一次补核checker误断言失败/修后成功；全部通过真实source快照记录，内嵌/惰性不双加。

11:07:27.765359+08最终报告readiness-and-budget-v3.json：政策已计下界6204.463643357s，余额仅上界202595.536356643s；其中原实测下界＋新rootwait union=5023.259836242s，C政策另1181.203807116s。新rootwait union30.267223835s，10份已返回外包引用含所有失败，不把sum当精确累计账。快照后的外包handoff-v3又返回1.417020384222s，政策下界至少6205.880663741643s；此后文档/完整会话/发布退出尾仍UNKNOWN。

原截止余144652.234641s=40.181176289h；53h占额差−46147.765359s；历史主体参照差−2.535092386到−2.949751667h，再有Q未知。不能证全案可容纳，也无不可突破的新版本耗时下界。GPU0无compute；task10仍GPU1/PID970022，未触碰。逻辑/诊断34057978835/924662935B，原限余2164965276717/7665271657B，快照后新增文档/原件另扣，不删证据。

当前草案v3只更新已返回费用/现场，仍非执行；v2模板独审、v3生产validator生成，不冒充新的独立阶段签字。已落实C组合、局部核销与分账原则；真实完整costs/inherited/动态控制/实际dispatcher仍待合同/证据/必要适配与实际验证；原语工程通过不能称整条真实链完成。task9.11.17状态review（本轮限定准备交付），父review/NOT_READY。无本节点后台任务/模型/环境/GPU/真实Docker控制/阶段令，正式0/test0；不自动开始下一真实门。

下一步只能针对上述具体剩余合同与证据派发；无原窗可行证明，不派训练/正式前缀；延时与其它UNKNOWN核销未批准，不能由“全部推荐”推导成任意新deadline/预算。没有新增建议科学功能。全局来源登记SRC-1430/1431，PROGRESS/DECISIONS/父三文档同步，最后链接/源码/dirty检查另补原件。

最终只读检查2026-11-04T11:09:39.789510+08:00：175源SHA仍46218cc5…c423f587，74个本次新增文档本地链接有效，git diff --check rc0、HEAD不变、新namespace不存在。原件[final-integrity-v2](final-integrity-v2.json)及[实际wait](commands/final-integrity-v2/wait-receipt.json)，rc0、wall0.464768260717s；该返回费用再使政策下界至少6206.345432002360s。当前完整会话/后续文档/发布退出尾仍UNKNOWN，不称精确余额。本轮到此，状态review/真实NOT_READY，无后台真实任务。
