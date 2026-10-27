# task8.9 r2 独立 Sol 验收

- 负责人 `/root/independent_r2`，实际按父显式派发为 `gpt-6.1-sol / high`；底层运行标识不可独立核实。推荐 Codex GPT6.1sol / high、Claude Sonnet5.5 / high，原因是闭合 OBB、离散化、生产加载、性能归因与精确恢复需交叉核验。
- 目标与授权：SRC-1081/1160/1161/1162，仅独立验收 B 六图先导与后续全量/200原件，再接续 A/C 已完成交付；不生产修改、不训练、不 mapgen、不使用 GPU、不重跑有效大批量。共享 SOURCES/PROGRESS/父文档由父维护，来源草稿预留 SRC-1138/1139。
- 已读：AGENTS（根与forem）、ENV、README/PROGRESS、task8.9父三文档、三个子RESULTS、r2协调/实施日志、指定来源；核查main工作区大量既有改动保留；现场A/C使用GPU0/1，不干扰。
- 准备写入范围：本日志、results/task8/t8-phase2-20261027/r2-independent-*；必要数值复算须由父协调B账本锁并记同账本，不与Terra写冲突。
- 已纯读：cube-pool-v2/pilot-report.json、pilot-audit-report.json、导出器、配置、生产scene.py、strict PCD解析、task8_voxel_diagnostics.py、合同回归。六图报告①–⑤PASS，600683点/11442562B、33432深墙射线漏0；当前仅实施原件，不作为独立复算结论。
- 方法审查：A闭合盒中心、B原fixture局部中心样本的闭格；B采用16ε×max坐标（约1.78e-14m）浮点边界表示容差，SAT沿用1e-10m。二者与生产τ=5e-5m分开；数学恰面与近面数值不可无限精度区分，需独立核本次输入是否出现实质分歧。每盒own_target单独核supercover，避免被其他盒掩盖；exact内部=8角投影包含。SRC1081使用360×90像素中心、base(0,0,0)、扫描原点z=.5、不限量程与.05m inset。验证不泛化到任意基座姿态或全部连续射线。
- 下一步：等待父确认B账本锁，最多一次60s CPU独立六图目标重建/严格PCD与生产scene核对（尚未执行），再给全量是否可继续意见。预算成本仍需24图profile，几何先导PASS不等于1800s全量可行。

## B先导独立结论

父明确B账本锁后仅一次CPU独立六图复算，rc0，7.3540240582078695s；内数值5.694256838411093s。未调用target_cells的longdouble重建88盒目标，与逐盒counts和target_sha256/真实CPU64生产占据完全一致，逐盒supercover0/非空；hash、点数、边界、中心全部通过，最大持久化中心误差1.7763568394002505e-15m。六图600683点/11442562B。exact洞0/33432深墙漏0核原audit及源码，未重复大批射线。账本累计36.5121836476028/1800s、余1763.4878163523972s、active=null，已告父释放供Terra24图profile。

交付：results/task8/t8-phase2-20261027/r2-independent-review.md与r2-independent-pilot.json/py、budget.py、sources-draft.md（SRC1138草稿）；几何先导PASS允许全量，但总预算门由profile另定，不许直接smoke/长训。剩余全池10300/200与A/C交付后继续独立审；无本Agent运行任务或GPU使用。共享文档/生产/实施/任务文档未写。

## C第一次阶段0独立审查

父续派审C，先纯读避免Terra固定验证账本冲突。已完整读C training/sac/replay/diagnostics/evaluation/CLI、13测试、原task7对应继承实现、B0/v5配置与snapshot、固定原日志。Terra13pass与CLIhelp rc0成立，恢复单测局部证据有效；父取消第三广泛task8_sim回归，未运行。

阶段0门FAIL：C1正式语义种子split semantic_transfer与实际资产split smoke的校验冲突，真实196计划会启动前报错；C2job seed仅控制sampler，候选选择仍依env validation_seed+batch row，与每job独立流声明不符。已即时反馈父交C修，我未改实现。reset疑点由继承_ids(None)排除，也已通知父，不修改。

交付r2-independent-c-stage0.md/json，报告明确实现局部门与未运行真实smoke门。读时snapshot11项无漂移；C原账本126.06330782920122/3600s active空，本独立纯读不运行新预算命令。下一步C修接口/流后父续派复核，A/B全量仍待交付；不GPU测试/优化/smoke/长训。

## C1/C2修复后复核

父续派后只读修复源码/新增合同测试/6544bdfdf6原日志与账本，22pass、rc0/无timeout。C1严格role/source及真实manifest相对forem根path/hash/content绑定；C2同一per-job流给reset factory sampler与candidate，跨batch位置轻量流合同成立。12项snapshot独立SHA核全无漂移，B冻结导出器未变。无新runtime/GPU测试或预算费用，C149.02423150185496/3600s active空。

结论C阶段0实现门PASS，第一次FAIL报告和快照保留；实际完整196/主循环checkpoint-resume/吞吐/显存smoke仍NOT_RUN，正式seed发布后实际对接待核。交付r2-independent-c-fix-review.md/json，SRC1139追加草稿已给父。未修改共享文档/实现，未smoke/长训。下一步等A/B原件交付，父可续派。

## A严格验收与smoke计划纯读审查

父续派纯读smoke清单，随后交A最终summary原件并要求判断全门前置。已读A任务三文档、实施/固定日志、原run/prepare JSON、summary/final-sol-check、账本和计时/guard/汇总源码；独立标准库复算原件有效转移/loop/p50/p95、256raw计数/热点/成本、全部listed hash，确认数字成立，无新profile/测试/GPU/账本写入。A1597.584848462604/1800s、余202.415151537396s、active空；本次原件复算不产生新benchmark费用。

独立A门：P1冻结设备PASS、P2严格partial未通过（低batch嵌套cold/raw缺，b1无sample，随机reset未知）、P3有限64cube/24semantic轮转PASS、P4方案PASS、P5完整周期成本未通过、P6guard/预算/独立原件核验PASS。3M条件基础cube57.725/47.471h正确但非完整成本实测/上界。明确用户“A/B/C全部过才smoke”前置不成立，已即时反馈父，不可自把partial改pass；父指令B当前块收尾后停止新块/不finalize、不smoke/长训。

smoke计划条件技术PASS：8job AST/hash/预算静态核对，2970reservation后C余480.9758s；512正常full checkpoint按原bytes/meta保存，同config恢复1000触完整196路径成立，update255/26→743/75正确。只smoke checkpoint_interval变1000；256env/100k/warmup/日程保持。monitor自清/物理GPU1空检/innerdeadline/timeout/外runner、不重试/完整与incomplete规则均明确；非运行完成/成本保证或当前授权释放。

交付r2-independent-a-review.md、r2-independent-smoke-plan-review.md、r2-independent-a-and-smoke-plan.json；SRC1139追加草稿。总门NOT_READY：B六图PASS，全量待停止原件；C实现修复后PASS、真实smoke未执行；A硬门未全过。下一步Claude/用户决定证据/预算或前置排序，父不能自行变更。本独立审查结束，无后台任务、无GPU/额外测试费用；历史FAIL/修复与限制全部保留。
