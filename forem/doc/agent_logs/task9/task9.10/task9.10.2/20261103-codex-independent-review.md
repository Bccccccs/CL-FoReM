# task9.10.2 独立审查记录

2026-11-03 14:48 +08接手；负责人Codex /root/reviewer，请求gpt-6.1-sol/high，实际后端模型/强度未知。用户授权依父[SRC-1383](../../../../../SOURCES.md#src-1383)，预算起点14:48:11.222061/截止18:48:11.222061 +08，不另取资源。只写.2三文档及本日志；不运行环境/模型、不改实现、不另委派。推荐GPT6.1sol/high、Sonnet5.5/high。

## 14:48–14:50 只读准备

执行pwd/rg文件检索、cat父与本三文档/AGENTS/README、rg PROGRESS、git branch/status、读取execution-window与9.8/9.9文档、基础src/task8_lower/evaluation.py、task7_sim/core.py、task7_lower/networks.py/training.py、task7_sim/episode.py、scripts/task9_8/replay.py/analysis.py。命令退出0；最初合并输出被工具截断，随后针对关键文件重读。ps仅初查，没有停止进程。当前分支codex/task9-lower-improve，已有dirty全局文档和9.8/9.9脚本，保留。

事实：父协议固定6×196、目标12，9.9 CSV分seed为5/4/3，原分类R1/N11。设计/阈值沿SRC-1382，历史结果依据SRC-1377/1379。execution-window明确1176回合/14400s/2147483648bytes。

已向父与实施者同步的准入检查（工程审查要求，尚非运行结果）：
- 替换action_start.raw不应要求与C相等，但同条输入state/target及段动作号仍必须相等；另核原均值等于C raw。
- 从原批Actor.params取得mean/log_std，禁止通过不同单例前向改变数学路径；参数到替换的mean/epsilon/log_std/tanh可复算。
- 抽样前后摘要需涵盖同batch全部env streams的maps/initial/other及global Python/NumPy/torch CPU/CUDA，不能只证明目标other。
- 新_finish事件应放detail或兼容投影，不可让旧coverage把额外事件误判未知；Core.begin内部_finish早于原Observer段号递增，零动作段需正确编号。

实施者答复：在forem/scripts/task9_10/replay.py继承Observer，comparison保持旧schema，_finish locals放detail，采样在Core.step下一动作wrapper、全批params校验均值。待稳定代码后审查；当前尚未给准入。

剩余：审查实现/零回合证据与预算启动门；C完成后独立核B及R1/N11；最终从原JSONL复算，交父汇总。风险：批内数值污染、额外schema不兼容、干预时机错段、RNG快照范围不足。

## 14:50–14:54 滚动实现审查

已读scripts/task9_10/replay.py、supervisor.py、test_protocol.py首版。当前代码检查点见review-source-checkpoint-1454.json，只是滚动审查hash，不能当正式执行快照。实现隔离SHA256/整数JSON种子正确；Generator(cpu)一次randn(3,float32)；全批params均值与原raw逐位torch.equal；采样前后global与全batch三purpose摘要；首次拒绝记录后仅下一真实同段动作抽一次；前缀将替换action_start.raw替回mean比较，输入state/target仍覆盖。新增_finish局部success/stalls/d/r/term/trunc放detail，基础comparison不变，旧coverage仍独立对每侧原evaluate row验完整性。

发现并已向实施者/父报告：
1. begin内部_finish段号旧值，当前14:54版本已加begin_mask与仅选中行+1偏移；仍待合成fixture和稳定版本复审。
2. 首版仅12trace历史比较，当前已补196原evaluate row逐项compare与historical-evaluation-match.json。
3. prepare-only在try/finally外，零检失败可能留GPU容器，要求准备失败可靠清理/计费及零命令timeout；当前等待修复。
4. 现有采样3fixture未覆盖错段不可补抽、单次门、action_start与零动作_finish编号，要求纯mock补齐。

排除的疑点：evaluate.first_Q仅首个真实动作写一次，干预由首拒绝后的下一动作触发，最早动作2；本轮不会把first_Q误标为替换动作Q。此判断来自原evaluate顺序与当前step触发，非实测性能结论。

编写本目录independent_check.py（仅标准库，不导入实施者score/coverage/torch），从原JSONL独立核动作/子步/提交/终态、首拒绝后同段R、C/B精确匹配、C/T输入边界与单次替换、SHA256抽样身份、原success与stalls、最终配对计数；只做语法py_compile（rc0），未对尚不存在的正式C/T执行。生成的本地pycache已清除。epsilon数值本身需对照正式容器零fixture/原值，不以标准库math重现GPU浮点假装逐位相等。

未给READY；剩余：修复准备失败收尾、补核心mock、冻结代码/原件身份、正式容器零检查由实施者做，父最终准入。

## 14:57 首C代码准入

独立核source-inventory全部5项当前文件SHA、snapshot SHA与登记SHA相同：replay 0149fb9ad6e3aacbb82f617a43506bc82a73c324b2c52ef47758e2912d70308f；supervisor f3918c3ba8901b6b569e599a934b4c554d2213ee91f76f1e87fc79b4ed419de3；test_protocol bff18e0e2db2742fb5b85fa7fa40288407510c5d878dd07137d1039532ce0ce1；legacy两项见code-admission-1457.json。核原zero-fixtures-final.log确有Ran9/OK，覆盖一次门、错段/结束/非目标/控制不抽、动作边界精确输入、零动作_finish新段；legacy-coverage.log为26/OK，zero-import明确0回合/未加载模型/未reset，Queue为stdlib/正式UID0与TMPDIR合同。

审查裁决：READY_FOR_FIRST_C_ONLY。实现问题已修复，允许父在其原件身份/资源门通过后放行第一C；这不代表C/T运行或机制验收。准备异常verify不符时不自动停止未经确认容器，以父已核新建container ID证明归属后收尾；当前挂载核对无冲突。旧prepared9fixture尚未重核的担忧已由final日志消除；关于snapshot“可能晚于修改”的推断已被5项独立SHA一致核对消除，未把该推断保留为事实。

下一步：随C原件到达独立复核完整性/历史一致；全部C通过R1/N11后才T，运行者单独持有启动权。审查者不运行模型/环境。

14:58补充最终freeze：实施者在首次准入检查期间完善了startup异常清理，supervisor最终SHA变为9b54deade586ecee661c866bf495520d8055a0f86f1d75b09e5de15494d2b5a1；现按container-create返回64hex不可变ID清理，无二次verify阻断。已读修改并再次核5项source/snapshot/inventory全匹配，最终inventory SHA2ab19529f5fef2d3cf191840ab7ee6cf3c7c309343f5d0b2163720551e2a2216，final-zero-validation确认为9fixture/26coverage/0回合PASS。代码准入READY_FOR_FIRST_C_ONLY维持，此最终hash覆盖前个滚动hash，不把旧hash当运行版本。

15:00启动前最后修订：实施者自查C没有干预却在step末期/finish被误记unavailable，父尚未启动并撤销release。最小修复已同时在step跳过C干预资格判定、finish仅T补unavailable，C明确control_deterministic。审查者核两个分支代码，控制fixture改为拒绝后换段仍无applied/unavailable，正式容器9项重核OK；无动作/前缀/恢复定义改变。最终replay SHA724764c3c4273820806109d57650f2cb872aea250deef4186d008749c2271cd7，test SHA6021efbcff7722be972f814c289ed06db30fc76222cd9b1c7ad7b88766ffce5c，supervisor9b54de不变。5项source/snapshot/inventory再次匹配，inventory最终7cc78e6b68f7f19b20ed25384de16b569518dd94e5d069676fffdbb9a22a92b2；final-zero-validation明确0回合、9fixture及26既有coverage。READY_FOR_FIRST_C_ONLY/PASS，之前checkpoint均为历史，以本hash冻结执行。

## 15:17 持续执行交接/覆盖限制

父已放行，C4718单worker运行，审查者仍仅只读。读取loaded.json：policy/critic与optimizer参数均cuda:0，最终script SHA724764c3匹配；实际GPU NVIDIA RTX PRO 6000 Blackwell Server Edition、torch2.7.1+cu128、线程2、TF32 matmul=false/cudnn=true。将真实instrumented Core.step/_finish/choose_candidate用标准库AST与历史原src逐函数核对，仅去除3个观察回调后完全相同，证据runtime-instrumentation-audit.json，命令rc0。

15:16原progress为196已启动/186完成，5目标case已有动作终态但final事件及evaluate尚未封口；未把部分轨迹当独立验收通过，不补造final。等待原evaluate及final完整后独立复算。父确认先前准入范围和等待状态，未要求重复全量代码审查。

性能解释限定：reset_s含reset/采样及相应元数据；core_step_s含step及emit钩子，emit_s与其嵌套；sample_s不完整覆盖前RNG摘要成本；actor_s为同步测量。不得把这些分量相加当完整成本。环境对象构造、候选生成、保存/退出没有独立完整分项计时，记录覆盖限制；整体worker墙钟与GPU容器资源保留窗可分别报告。计时本身已加入同步，不能当生产吞吐收益证据。

下一步仍为首C完整原件独立核验；其余C/T唯一启动者.1，由父监控预算。脚本与模型不改，未启动任何审查侧GPU工作。

## 15:18 首C4718独立复算PASS

父通知首C封口后执行python3 -B标准库内联统计（rc0），runpy仅载入本目录independent_check.py定义，不导入实施者score/coverage/torch。读取5原JSONL、C原evaluation/status及B3对应原evaluation/trace。输出independent-C-4718.json，含SHA和逐case全量数字，源数据只读。

独立确认196/196完整，所有历史row字段精确相同；5case动作/子步/pending/attempted/committed/状态/目标/终态/完整键与final对账，comparison全事件与历史相同。恢复R1/N4；case2首拒绝segment2/action39/substep1，后一次commit的最大/净rho减0.0003749274617164122m；case6虽后8commit但净rho减为-0.0038383932732326542m，不误判R。5例原success/strict_success均false、failures20。原_finish逐段号与end动作号、success=route_complete且d<=.025且r<=.05、stalls逐段递推均通过。C控制未替换，未将其记不可干预。

原worker rc0、196 started/completed，wall1011.0073873996735s；监督者1023.941s与eval969.194s为不同覆盖区间，不相加。已向父与实施者报PASS，首C机制分类仅这5例；其余C/T未独立核，不能提前认完整12或新改善。继续只读等待C4719。

## 15:36 C4719独立复算PASS

父通知第二C封口后用同一标准库独立read_trace逐原件核对（rc0，未导入实施score/coverage/torch）：196历史row精确相同，4trace完整且comparison全事件相同；原_finish逐段/动作归属、success残差公式及stalls递推通过。4N、原success/strict均false、failures20。证据independent-C-4719.json含原件SHA；原worker1064.383472442627s、196开始/完成、rc0。累计9目标R1/N8、392完整evaluate。已报父PASS，仅第二C，不提前通过12例或干预机制。C4720按父预算门在运行，审查者继续只读。

父已授权最终在同镜像做CPU三维epsilon独立重建，0网络模型/仿真环境，不干扰GPUworker、不写run原件；允许临时CPU容器无GPU。已准备independent_sample_check.py与run_cpu_sample_audit.py，尚未执行：显式不传--gpus、CUDA_VISIBLE_DEVICES为空、NVIDIA_VISIBLE_DEVICES=void、全部绑定只读，stdout/命令/错误只写本目录并计外部预留。epsilon逐值exact门；CPU float32公式与GPU保存动作只报告实际分量差/最大差，不设事后容差、不把CPU近似称GPU精确。

## 15:47 原_finish旋转残差单位注记（无运行合同变更）

直接读forem/src/task7_sim/kinematics.py:131–137的metrics：返回(d,r,angle)，其中r=(3-trace(R))/4=1-(qa·qb)^2，源码明确dimensionless, not radians。实现记录original_finish.r_rad取loc[r]，字段名误导；真实值仍为原success所需的无量纲CBL旋转残差，0.05阈值不是0.05rad。原计算与布尔判定完全未变，独立检查也按相同原值核，不因此停运行或改冻结代码。已向父和实施者同步，最终报告必须澄清字段历史误名；来源登记沿SRC-1384并由父补metrics符号定位。后续如需改schema，另版本处理，本轮不动活代码。

## 15:54 三C独立门PASS_CONTROLS_GATE

C4720封口后用标准库独立read_trace读取3原trace/原evaluation/status与B3原件（rc0）：196历史row精确相同，3完整trace的comparison全事件相同；原_finish逐段/动作号、success原残差公式及stalls递推通过。3N。三C汇总588完整evaluate、12目标R1/N11/U0、原success0/strict0，逐seed为1R4N/4N/3N。证据independent-C-4720.json与independent-controls-gate.json，均含原件定位或引用。已即时报父/实施者独立PASS，科学门无差异。实施者按既定门已启动T4718且尚未目标干预，父知悉；审查侧未新增环境回合，未改原件/实现。

下一步等T各seed封口从原JSONL独立核单次动作边界、前缀、RNG摘要、R/N/净rho/原success与非目标row差异；最终另做CPU epsilon精确重建。采样数值未产生前不下机制结论。

## 16:12 T4718独立验收PASS（部分干预组）

标准库自写read_trace与原件逐项检查rc0：196完整/原worker1021.1829042434692s，5条原JSONL各恰一次替换，raw及执行(u,w,v)均实际改变；首次拒绝锚点至下一同段动作输入边界精确匹配C，边界mean_action与C raw相同；JSON/SHA256/seed独立重建一致，原全流RNG前后摘要相同。未调用实施score/coverage或模型/环境。证据independent-T-4718.json含hash、逐例原值/替换和RNG。

独立R2/N3：case2保留R，case6从N→R；原success/strict均false、failures20，未到达原同段目标。完整遍历同段（不在首次R提前返回）：case6最大rho减少0.0012711500405742093m，但段末净减少-0.0037452972849869592m，即终态距离更大；后续66commit，不能把临时改善解释为最终推进/任务成功。case2最大/净仍0.0003749274617164122m。实施者提醒旧score在首R即返回，其max字段只覆盖截至首次R；本独立全扫恰见case6全段max与首R相同，不因此假定所有case都相同。

另外独立核全部196 C/T row身份/字段，非目标差异0；5目标MC/Q_minus_MC均变化，case6还time_s/transfers变化。随机strict均67/100、语义49/96，C/T相同。只交首T，固定12完整机制判据尚待T4719/T4720与CPU epsilon复核；未提前声称严格成功率提高或可部署。已即报父/实施者关键局部/净值差别。

## 16:30 T4719独立验收PASS

读取第二T原evaluation/status/4JSONL与同期C原件，自写标准库检查rc0，未导入实施score/coverage/torch。196完整，4case各恰一次raw及物理执行动作改变；首拒绝至下一同段动作输入边界/均值精确前缀、JSON/SHA/seed与全流RNG前后摘要通过。独立4N、原success/strict均false。全部196row身份/字段对账，非目标差异0；随机strict63/100与语义39/96的C/T计数分别相同。原worker1062.4434924125671s、rc0。证据independent-T-4719.json含完整采样和SHA；已报父PASS。累计9条T为R2/N7，仅局部新增case6；末3条T/CPU epsilon及最终资源停机待完成，不提前下全12结论。

## 16:41 CPU独立epsilon重建PASS_EPSILON_IDENTITY_ONLY

父确认12个干预事件已落盘而末T尚未196封口，要求先做CPU核。为避免将append中的整trace哈希误称final，CPU脚本只读取已换行完整JSON事件，并对完整intervention对象做canonical JSON SHA；封口后另与最终原trace逐例对应。不把当前输入当完整episode。先读forem/ENV.md（版本说明旧，实际以本run image/loaded为准），随后执行python3 -B本目录run_cpu_sample_audit.py，rc0。helper在同冻结image中docker run --rm、--read-only、--network none、user1004:1004、无--gpus、CUDA_VISIBLE_DEVICES为空/NVIDIA_VISIBLE_DEVICES=void、OMP/OPENBLAS线程1，所有绑定只读，无网络/仿真环境/模型创建，仅3维CPU张量；命令和SHA在independent-cpu-sampling-command.json。CPU容器已正常--rm，不触及主GPU容器。

12/12独立JSON/SHA/seed与cpu Generator randn(3,float32)的epsilon逐值exact，global CPU RNG未消耗；torch2.7.1+cu128、cuda_available=false。完整CPU float32 exp/tanh公式与GPU保存action仅1/12逐位同，其余逐分量差已全公开，最大绝对差5.960464477539063e-08。没有设事后容差或把CPU近似称GPU逐位证明；原GPU参数/动作公式由代码审查与原mean/C raw精确门支持，CPU差异不放宽任何前缀门。输出independent-cpu-sampling.stdout.json 14050bytes、stderr0、总launch墙钟2.014544725418091s（非GPU占用），计本轮全局墙钟与外部预留；内部采样计时不等于完整launch。

已即报父。仍待T4720完整封口、CPU记录SHA与final干预对象对应、原始账本/停机核验，故此时未给最终全实验PASS。

## 最终交付 · 2026-11-03T16:49:47.830405+08:00

T4720封口后运行标准库independent_check.py（rc0）从24原trace/6evaluate独立完整复算，最终R1/N11→R2/N10，配对RR1/NR1/NN10/RN0，12raw及执行动作真变，原success均0/12，全部同池strict计数相同、非目标row差异0。CPU已读12干预对象canonical SHA与final对象12/12匹配，cpu-final-record-match.json。最后T3为3N；无新增失去R。

运行independent_integrity_check.py初次rc1：宿主Python的datetime.fromisoformat不接受Docker9位纳秒时间戳；仅审查脚本解析错误，未触及运行或数据。修为整秒UTC加原小数秒解析后rc0，无容差放宽。核原6写前账本各196/去重job完整、状态全rc0、5source/snapshot一致、18生成函数文件一致、loaded网络/优化器参数cuda、原容器ID stopped/Pid0。预算/计时/bytes及局部R实际米数详见RESULTS和independent-final-integrity.json。

已完成0额外环境回合的独立验收，.2状态done；父总裁决仍由父从原件复核。最终采样CPU只重建3维张量，无模型/仿真环境；全局至独立交付7296.608344s小于原14400s截止。剩余无本子科学/完整性核验项；不启动后续实验/训练。风险为单次样本/开发定向案例外推有限、R短暂且没有完整路线收益、阶段计时嵌套覆盖不全、r_rad真实无量纲。独立工具和派生JSON均仅写.2目录，旧输入/原run只读，主执行/共享文档由父维护。
