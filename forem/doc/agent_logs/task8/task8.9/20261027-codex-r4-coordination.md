# task8.9 r4协调记录

- 开始：2026-10-27T13:12:01.101336+08:00；负责人Codex，按派发gpt-6.1-sol/medium（平台内部标识未独立核验）。
- 授权SRC-1210及本轮prompt：I1有界初始化诊断、新1200s账本；按诊断实施逐元素等价缓存/解析，必要才并行；独立Sol high验收后C原账本扩至7200s、固定smoke单job内部900s，最终r4报告停止交Claude。禁止3M、task7写入、mapgen、额外优化、提交/推送/合并。
- 已核：无r4任务产物/账本；r3优化与正式10300池保留不重跑，C395.0120486840606s历史费用保留。main既有大量改动不覆盖。Claude仍在规划/监督，父仅追加PROGRESS不改其行。
- 分工：实施Sol high仅task8_sim授权范围、新诊断/测试脚本、task8.9.1.2三文档与独立日志；独立Sol high另人审核；固定全量/ smoke用Terra low，原产物须Sol复核。共享文档及来源1211–1229由父维护。推荐Claude Sonnet5.5同角色强度；跨模块等价与归因high、固定执行low。
- 待执行：实施诊断、证据驱动修复、全量等价验收、smoke、成本模型及r4报告。

## 2026-10-27T13:15:30.454008+08:00 I1开测与smoke静态边界

- 64项原r3冻结hash当前全等，保存r4-preservation-start.json（仅源码/配置，不重hash大型产物）。GPU0唯一I1内380/外390s，正式B0 seed4718/256环境；逐env快照i1.json，不构造optimizer。
- 初步资产/场景主导，asset_other包含整manifest反复解析，不能冒称全部磁盘/PCD读取；最终以I1原件与独立核查为准。串行成本外推不足以认定预算不可行，已要求评估独立离线全量缓存/校验受控CPU并行；这不属于改变env采样顺序的(c)。先保留预算，不擅扩1200s。
- SRC1210的“235→900”按旧primary内部235放宽到900处理；原resume1130保留，避免擅缩196评估窗口。新8job静态reservation4300s、closeout≥140；7200扩限尚未写账，smoke未释放，旧失败目录不覆盖。此解释已由独立Sol建议、父明确通知prep，不能写成所有job均≤900。

## 运行时缓存与恢复的必要接入范围

(a)缓存需显式TASK8_SCENE_CACHE、源PCD/sidecar hash/metadata/key/payload核查与无fallback拒绝。父明确授权实施者在task8_lower/training._contract作此优化必需的最小增项：assets.py、scene_cache.py实现hash，cache root/index/hash及runtime启用方式；以准确旧新diff记录，不改变SAC/训练循环数学/恢复顺序，不静默豁免原C hash。此为已授权(a)必要恢复正确性，不新增独立manifest索引优化。全部10324 canonical CPU64逐张量equal，另GPU32有限pilot必须报告覆盖限制，bool/int不转float。

Terra fixed_r4已显式gpt-6.1-terra/low派发，仅读准备等待固定清单，尚无批量/新smoke执行。后续离线pilot应先实测并行收益与内存，不能拿理论64核直接除串行耗时作为预算可行证据。

## 2026-10-27T13:23:47.295440+08:00 I1 partial、pilot独立通过与full释放

I1内380.334736065s deadline/rc2，外382.900948012s，76/256 accepted、277提案，分项原件已登记SRC1212；不是完整reset。实现RED/GREEN账本费用保留，新init累计391.669575868s。Terra pilot96图（72cube分6层＋24semantic）一次rc0，7.475169398s；循环4.831423747s、worker130.353651176s、10838012点、guard0，旧新bits/CPU64八tensor equal原assert及源码已由不同Sol核验，SRC1213/1214。全量10228新图与先导96不交，reuse sourcehash/manifesthash严格一致，最终10324，不重复先导。

父明确释放一次full runner570/内560/32CPUworker，前余额800.855254734秒，留230.855给后续I5/审核；数量比例估514.75秒仅工程参考，非上界。I5拟完整GPU task8_sim回归65秒（包含CPU parser/fixture且预计0skip，不重复旧CPU全套）、GPU32有限严格等价20、缓存正式seed4718/256reset115、收尾约30；每项仍按full实际余额与父释放，不预写通过。全量首失败停，partial原件保留，不擅加预算或缩图。

## 2026-10-27T13:32:39.660113+08:00 全量独立PASS与I5释放

full job965d4db8df一次rc0，10228新+96复用=10324，loop383.723501031s、外386.658399398s；累计worker12377.499806485s（新12247.146155309+先导130.353651176），总点1086118724。full.points/worker字段只新图，已明确避免误报总量。不同Solr4-independent-full-cache-review.json通过ID/order/progress/源hash/index/key全覆盖与已审assert原执行，SRC1215。缓存indexSHA5e99918286ebbc97cbd9e3c366dadb2a16dc62cc9200e61957ca98e22bbac5f2。

init实际used785.917564142s、余414.082435858、active空后，父释放I5固定3job230秒：70 GPU完整回归、45 GPU32有限32图、115正式seed4718/256缓存reset。新artifact根与独立静态通过、每项前核GPU0空和精确hash；首失败停，不重试或缩图。完整GPU回归含CPU资产/fixture/格式等全部本目录测试，避免重复旧CPU全套。
