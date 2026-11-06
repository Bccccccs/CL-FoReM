# 后续真实入口具体适配草案（尚未实施）

授权仍[SRC-1435](../../../../../SOURCES.md#src-1435)。本文件是已授权剩余范围的工程实施草案，不授予独审令、不把尚未执行写成通过；因G1 180源冻结正独审，以下尚未改生产。当前G1入口来源[SRC-1437](../../../../../SOURCES.md#src-1437)。推荐GPT6.1sol/high、Sonnet5.5/high：完整CID/设备、跨阶段准入与费用因果；实际平台模型档位未核实。

## L ON196最小接通

1. 后续新协议保原T0/截止/58h/科学配置，单独绑定新冻结源及已完成G1的独立PASS原件；以新namespace接L ON+正式剩余链，保留G1 namespace和令，不重开G1、不改其冻结协议。当前builder只是不创建namespace，后续协议须使G1成为已验收依赖、不得进入新可执行阶段集。
2. 将real_g1的精确source/budget/infra/lease、owner/guardian/watcher wait抽成可传(stage,arm,seed)的真实阶段适配；生产admission按新协议明确支持gate-evaluate-L-4718、四profile/remaining与四个final-test，拒绝smoke512/1000及额外C ON/G1。阶段release仍由.18.2原件逐门同SHA发布；旧G1原件只作证据，不能当新source放行。
3. L ON全用新隔离容器及新写目录；旧run通过/workspace只读挂载可读，无需复制2.635GB checkpoint。L阶段令必须绑定旧L4718 final.pt、config/summary、OFF196与parity全部精确路径/SHA，父已有`parent-initial-reuse-check.json`，独审需限定接收；worker在load前再流式校验二进制SHA与配置，严格stored config的1000步/arm=L/seed4718，然后只调用原evaluate(recording=True,parity=True)。
4. worker目前gate-evaluate默认out/final.pt；必要补token.initial_checkpoint只读ref，改从该精确ref load，输出仅新out/recording-on-evaluation.json与新diagnostics/parity。旧checkpoint与OFF/parity不复制/不覆盖；不执行train。配置仅走原smoke1000校验（total_transfers=1000的原值），保持科学语义。
5. 新阶段账预留LON196，写前episodes-started各batch保留；stage cap<=1800，save尾仅该评估实际需要的已有保护。退出后独审精确196、OFF/ON parity与原自然计算链、终止/扫描完整性、实际wait/stop/device/费用，再发正式可行性门。旧C的FAIL永留，限定科学承接只能引用原审查，不能改旧记录为PASS。

## 一次接通正式四run与独立test

- 已有worker profile(train从头→250k暂停→full replay restore核250k/3M/设备)与remaining(own profile→原validate_profile/save_readiness→train resume)可复用。不可用短基准证明成熟吞吐。正式第一个profile前独审全案日历/worker/GPU/存储可行性；每个run自己的250k完成后再独审成熟窗口/保存恢复/剩余预算，原序C4718,L4718,C4719,L4719，own250k包含各自3M。
- 调度按固定DAG串行且一次性消费stage identity；可每阶段独立GPU租约/容器，目录formal-arm-seed保full profile供remaining读取。每run阶段累计cap不得越43200原限；cap+有限控制/保存/停止尾纳58h累计。精确stopped inspect缺失保整租约费用，不能退成0。
- 容器可按阶段新分配，需inspect identity(startedAt/restart/DeviceRequests/mount/user)各自封存；宿主/容器准入均读同独审stage/budget/source，watcher动态检查current resources；cleanup不因新启动令过期而丢失exact-ID停止能力。每个actual root wait绑定新全源前后快照，保持no-retry。
- 最终阶段需独审开发B–E通过、冻结4个3M checkpoint及独立manifest原件；每arm/seed仅296(200 test+96新semantic)，总1184。已有worker final-test/test_jobs可复用，但real-path evidence解析需按新namespace/HOST↔container实际路径适配，不沿旧run强映射。

## 资源/计数入口必须补齐

- 当前旧base evaluate计数只扫描新/output，历史980不在新账；不能直接依赖原max_evaluation_episodes11768。新资源适配须用历史980+新write-ahead账+当前阶段完整quota预留检查；固定DAG只发196、每run196+2156、每run final296，一次性消费身份，不另加评估。可在传给原evaluate的本地资源view把可用新数量限制为10788，仍保封存协议原11768及消费980，明确这是剩余账映射。
- 当前Observer/OutputBudget本地只数新目录；install_output_budget与guarded_size必须使用扣除独审历史storage/diag上界的资源view，并计所有.18控制/源快照/评估tensor。全局限额不变，40GiB临时full-save预留、256MiB现有日志保留不丢；参数/模型配置完全不改。
- 历史与新会话费依独审metadata持续滚动（4worker/4GPU上界），不把当前UNKNOWN直接当0；实际stage wait和父会话区间重叠须保持明确上界，不能伪装精确累计。成熟吞吐仅正式全案/remaining前门使用，不当G1/L ON阻断。

上述改动计划在G1真实证据与独审完成后实施；当前生产仍G1-only SHA4b69383c…，未改。
