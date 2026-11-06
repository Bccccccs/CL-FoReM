# task9.5.2 RESULTS

状态：**done（2026-11-02父接受独立最终验收；六正式3M均完成，未观察改善，历史阶段记录保留）**。负责人Codex，派发GPT6.1sol/high；内部模型核验未知。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由是隔离导入、完整随机恢复和截止排程需要跨模块核对。推荐不冒充平台实配。依据[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)、[SRC-1346](../../../../SOURCES.md#src-1346)，参数工程选择沿用[SRC-1342](../../../../SOURCES.md#src-1342)。共享文档由父Agent维护。

交付报告：`forem/logs/task9/t9-opt-design-20261031/implementation-report.md`；完整清单`implementation-manifest.json`、可审查差异`implementation-diff.patch`、六配置差异`config-matrix-manifest.json`。实现artifact SHA256：`b6efeeac1180d69b3ced8759df663fa953a9e1e2072d4d3e510871d5dd939b2c`，267文件。125个当前dirty依赖/配置原件冻结，独立runtime仅SAC/training/evaluation三文件相对原件变化。原69冻结文件复查drift0，见`implementation-original69-check.json`。

实际CPU验证：`forem/logs/task9/t9-opt-20261031/cpu/final/execution.json`，容器`forem-dev`、CUDA_VISIBLE_DEVICES空、退出码0、24.304096s容器调用墙钟（pytest内部21.98s）；`pytest.txt`为**24 passed**。覆盖B0/B3实际更新/动作/全优化器与恢复等价、E15实际α梯度差1.5及非法值、严格科学配置恢复拒绝、U20实消费/更新次数、R200真实capacity/shape/抽样/存储、六配置与100＋96评估计划、导入根、离散截止排程及放行阶段隔离。真实Core/IK三环境非对齐暂停：科学limit13，消费7时9动作已收费，cursor1保留2条，续至13共5次真实SAC更新，网络/target/优化器/LR/回放/全RNG/环境候选及交互账本与连续运行精确相等；测试批量2是明确测试fixture，正式六配置batch256/env256/3M不变。CPU评估使用有界fixture，不冒充196科学评估。fail-first原件保留，详见报告。

新queue/worker/monitor已经准备：G1与训练policy分离、哈希绑定与独立review证据、每卡锁/新输出根、两种子512→恢复1000→196 smoke/group4300s、正式250k不缩3M科学预算、成熟回放末50k分解、真实逐卡排程/二次准入、07:00前预留保存并仅对新输出写STOP、无实验重试。所有入口**尚未执行**。未修改原timing同步/统计/有限值检查；未声称加速。

未决与限制：GPU确定性/设备等价、R200成熟显存、真实196评估、实测保存恢复与端到端成本、多卡同时资源、实际截止保存均须后续G1/policy执行及独立验收。六run不是工期保证。最终/末三/分难度/全部种子结果尚无，不能据此声称改进。无子Agent遗留长进程。下一步由父组织task9.5.3静态审查，合格后仅发G1 release，再独立审查真实G1后发训练policy；当前不得训练。


## 2026-10-31 fix1 / v2

状态：**HOLD，待task9.5.3限定复审F1–F3；GPU/实验仍尚未执行**。依据父接受的独立审查及[本次修复SRC-1348](../../../../SOURCES.md#src-1348)。新artifact **07e2b541a3230a4134ad527bf3423ad1073ac871e846c4d8c45f827f07bd033d**，268文件；v1完整清单/差异/源字节保留，增量`forem/logs/task9/t9-opt-design-20261031/fix1/v1-to-v2.patch`、逐文件新旧hash `fix1/change-manifest.json`。完整实施报告同路径`implementation-report.md`追加fix1节；原69再次drift0。

F1：实际profile退出和remaining worker均检查成熟save_max＋明确工程cancellation_drain_bound＋独立正emergency_margin是否在原policy保存预留内；cancel值另须覆盖checkpoint/candidate/observation/inference/envstep/consume/diagnostics各max之和，包含在途周期保存，再单独留退出保存。whole196/reset有内部检查，不把其总耗时当取消gap。链路floor不是全部无检查路径或未来硬上界，采样IK/planner、评估critic/统计、reset收尾、fsync、恢复/启动/排空残差仍由经独立审阅的工程cancel/margin覆盖；无假实测上界、无自动加预留。不足明确NOT_READY，不改3M/4300/07:00。父需核预留扣减后smoke可执行窗口。

F2：真实checkpoint元数据记录stop_reason，worker日志保留异常类型/原因，queue保留interrupted/diverged及证据、隔离组且不重试；未知worker/launch/结果异常分别登记。F3：G1子进程timeout受cap、绝对STOP_AT和token期限共同钳制并留既有10s清理/写证据工程预留；过晚明确NOT_READY且不创建测试子进程。

针对CPU验证只运行`test_review_fixes.py`与既有`test_admission.py`：**16 passed，rc0，pytest4.06s，容器调用墙钟6.276164669543505s**；实际命令和输出`fix1/03-targeted-execution.json`、`03-targeted-final.txt`。覆盖真实profile准入分支、保存/链路算术、真实STOP保存原因、终态区别、新入口导入优先级及mockclock/subprocess晚G1。保留fail-first和一次13pass/1fail的测试修正原件；后者定位新入口作为测试module时插入原src覆盖隔离路径，现只在路径不存在时插入并断言真实training.__file__。未重跑全套CPU/GPU，无实验重试。

更正v1时钟口径：原24passed的21.98s是pytest时间，容器调用墙钟24.3040963280946s。模型推荐仍GPT6.1sol/high、Sonnet5.5/high，跨模块控制修复；派发前者，内部实配核验未知。下一步同独立reviewer核新digest/增量/证据，父再决定G1-only release。

## 2026-10-31 actual G1 / g1-v2

父已接受静态fix1独立审查并发G1-only token，artifact仍`07e2b541a3230a4134ad527bf3423ad1073ac871e846c4d8c45f827f07bd033d`，代码/config/tests均未修改。[GPU证据SRC-1349](../../../../SOURCES.md#src-1349)。状态：**G1执行PASS，待独立实证复审；smoke/profile/训练继续HOLD，尚未执行**。

先核GPU0/1空闲、旧queue无待派、保护5M PID1517927/1744078仍在原GPU3/2。初次queuePID1894521因新结果根父目录root权限失败，未建worker或输出/GPU测试，原件`g1-v2-launch-failure.json`及`g1-v2-queue.txt`保留。父仅修此前不存在的新根所有权，明确允许同token/run-id继续，未重置实验预算。随后父加新根默认ACL，containerroot新建子目录fixture经host1004成功touch STOP，原件`output-root-acl-verification.json`；未来首个实际smoke需核os.access继承，不能向实际run写测试STOP。

实际命令与时间：`forem/logs/task9/t9-opt-20261031/g1-v2-after-output-fix-launch.json`。2026-10-31 22:35:23.219335→22:35:44.025529+08，hostqueue1895653、Dockerexec1895726、worker容器PID2677049，实际CUDA pytest宿主PID1895770，GPU0。queue/worker rc0；pytest **36passed17.97s**，worker **20.211039135232568s**，hostqueue wall **20.806916940957308s**，低于原1800s总G1上限。初次失败无GPU/test耗时，未自行重试/修测试。

原件：`forem/results/task9/t9-opt-20261031/g1-v2/{g1-result.json,device-path.json,pytest.txt}`。实际policy/replay/actor/critic/alpha optimizer均cuda:0，torch2.7.1+cu128/CUDA12.8。原pytest临时输出的真实导入与非对齐暂停/连续/恢复summary已逐字节留存同G1目录`nonaligned-*.json`及`retained-test-evidence.json`，所有相关import.__file__为隔离runtime；全证据hash、PID/时钟/rc与GPU退出后现场见`forem/logs/task9/t9-opt-20261031/g1-v2-evidence-manifest.json`。真实CUDA测试包含13步/pause7已收费9/pending2/共5SAC更新的等价检查；不冒充3M、成熟R200或196科学评估。确定性flag与CUDA默认device仅测试子进程使用，生产未改。GPU0测试结束释放，旧两5M未动，无遗留G1进程。

后续仍需独立G1原件复审→父单独training-policy release→获准smoke/profile及准入；不得以本G1 token启动smoke。模型/强度沿已派发GPT6.1sol/high，内部核验未知。

## 2026-10-31 22:46+08 受控队列 active 交接

**当前active，运行中，未完成。** 父在独立G1实证PASS后发真正training-policy，SHA`865367cfd8bbe86f342abd9ef8955fc45c2b0013c6fe16a2c0ba2a54746e1c03`，原artifact07e2…033d未变。[SRC-1350](../../../../SOURCES.md#src-1350)。22:42:21.977995持久后台启动，hostqueue**1900665**，唯一独立monitor**1900735**；exactargv/cwd/log见`forem/logs/task9/t9-opt-20261031/training-queue-launch.json`。监控`queue-state.json`、`deadline-monitor.json`、`training-queue.txt`及active per-worker stdout。STOP请求2026-11-02 **06:30+08**，cutoff07:00，仅新12个formal/smoke outputs。旧5M PID1517927/1744078仍原卡，不动。实际首run的host1004 os.access(W|X)及getfacl继承均通过，未写真实STOP。

U20-seed4718：GPU0 smoke512 worker宿主1900841/容器2677105，512已消费/512已收费/2calls/13updates保存并rc0退出，checkpoint2,688,184,056 bytes；worker87.851620s，外层phase89.282908s。随后同output从smoke512.pt恢复，smoke1000容器PID**2677129**、Dockerexec**1901908**；已到1000/38updates诊断，1024动作收费/pending24，科学limit仍3M；CUDA policy/replay/moments、CPU非capturable Adam counters均核。获准196评估正在进行，尚未通过；正式六个3M仍全部queued、未启动。真实证据`training-first-smoke-verification.json`、`training-first-worker-verification.json`、`training-first-512-resume-verification.json`、`training-first-1000-diagnostic.json`，父另独立核`root-first-smoke-check.json`。

待门：其余既定smoke及三group判定→完整run离散准入→250k成熟profile/保存与成本门→余2.75M→最终独立验收。不得把smoke启动、1000诊断或G1当3M完成。背景queue/monitor交父继续观察；不重开monitor、不自主实验重试/预算重置。仅两条既定自动恢复边512→1000和已过门profile→remaining；其余恢复必须父核账本/配置/源码/预算。若需人为停止（尚未执行），先核并停止本新queue派发，再仅给其active新output写STOP，保留独立deadline monitor，不碰旧任务。完整方法追加实施报告。模型派发GPT6.1sol/high、内部核验未知；无需等待本轮196/长训结束才交接。

父2026-11-02接手终态：依据[SRC-1351](../../../../SOURCES.md#src-1351)、[独立验收SRC-1352](../../../../SOURCES.md#src-1352)，全部六3M/18M账本及保存/阶段rc核过，实施执行交付done；后续科学建议不自动授权新训练。当前正式artifact07e2…033d（v1 b6ef…为历史），运行全部结束，无需恢复，旧5M均保存完成。
