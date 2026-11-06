# GPU两账计费修复实施记录

开始2026-11-04T09:23:00.481592+08:00；负责人Codex，状态review。委派请求GPT6.1sol/high，实际后端/强度未获可核实字段，记未知。兼容推荐Claude Sonnet5.5/high，因设备区间/累计费用/跨阶段身份核验。授权[SRC-1419](../../../../SOURCES.md#src-1419)；实施/实测[SRC-1420](../../../../SOURCES.md#src-1420)。

授权边界：只必要GPU/worker会计修复与stdlib占位进程/fixture时钟；不改worker/runtime/audit/科学参数，不加载模型、不控制真实Docker，不运行GPU/环境/仿真/回放/smoke/训练/最终测试，不新增监控/legacy认证schema。不写共享PROGRESS/SOURCES/父文档，父负责登记；本节点无子委派。

开工已读根AGENTS、README/PROGRESS、父RESULTS §16、.11/.12任务/流程、20261104 cross-stage-review。Git分支codex/task9-lower-improve，既有dirty保留；父已检查并发范围与保护168源，原旧式反例143→233.078001564由父重算，非本轮真实GPU。before-source/manifest由父保存且实施未改。

## 设计与trace

GPU不能继承worker总wall。新增gpu_costs仅按明确授权UUID及有完整归属证据的区间union；CPU显式空设备/空区间为0。真实external API无device attribution receipt，缺证与真实自报均UNKNOWN，只支持本次已说明inert synthetic输入。scope可包含离散/partial/重复GPU区间，不要求占满payload；已包含command GPU必须被历史并集覆盖，aggregate与并集一致。

完整读取链：continuation.inherited_accounting→static.validate_external_costs或dynamic costs.inventory→costs.review/_check_resources→snapshot→release.remaining→supervise cap/worker二次resources。container已有record/精确inspect/start/stop证明完整持有含idle，与历史/命令取union；新GPU cap不含CPUcontrol。worker保持最外层payload＋原有限candidatecontrol。snapshot保留精确资源时点、全局GPU并集和原容器basis，用已有container_state入参复用生产资源接口，不新增monitor。

原reserved_worker_seconds只代表active预约，为兼容保持；proposed_worker_seconds另列，resource_reservations为二者合计。reserved_gpu_seconds为active及拟申请GPUcap总计，proposed_gpu_seconds另列。snapshot limit-used与扣预约后的余额分别保留；新release/最后启动前仍实时重核。

## v1及失败

v1冻结db02314ef8bb6e92e31755db9ece7a7db1d0b328d56df60111ec2d9f91175b7a /170，原source-freeze-final/minimal-final/final-source与final-gpu原输出仍在，12项rc0、四组352文件原件归档joint-final。该PASS已不足以交付：.14原expected-reject反例证明同Id改晚start、缩短stop、删record、sealed/current共同改CPU可减少既审GPU。父确认必要修复后重新冻结，未覆盖原FAIL/旧PASS。

开发失败原件全部dev-*/dev-v2-*保存。测试输入问题包括：fixture时钟隔离、整resource字典含随时变化wall、legacy false-execution早拒、ISO微秒舍入、near-balance新令预算未收紧至snapshot/expiry不容原save1800；v2新增反例初稿在同namespace复用review denial费用导致stale遮蔽，改成各独立fixture。均未放宽生产准入或独立expected-reject。

## v2必要补丁

最近已审snapshot容器basis约束当前record/sealed inspect全等；已停窗口不能改end或重启，运行→停止必须覆盖原resource_observed_epoch。丢record同样拒。正常resource与review override同一核验，不允许改短再重新签新snapshot。无独立时序basis的staticlegacy容器明确UNKNOWN；旧未审5s正例由当前用户缺证规则收紧，保留原before-source历史，新增等价dynamic已审5s idle正例。

最终v2 c53aa98688aa69b058b36bdae3113b5ca500213b91f83ba0abc614945798aff7 /170，source-freeze-v2、final-source-v2、minimal-v2.patch（2b6007218c7b6584081156c6a68b92552e7f32073554d85c6348946d8ca14527）。相对168源仅8改2新增，160不改、无删除：admission/continuation/costs/supervise＋4stdlibfixture，新增gpu_costs与专用test。模型/worker/runtime/audit/科学配置字节不改。

final-v2-gpu-command.json保存exact argv/cwd/env/exit/wall/source前后、stdout/stderr；执行入口python3 -B forem/src/task9_lr/tests/test_gpu_accounting_stdlib.py，TASK9_GPU_JOINT_ARCHIVE指向joint-v2。15项rc0、wall9.227331739s，同170源前后与冻结一致。joint-v2四组351份文件逐SHA核真，汇总implementation-evidence-summary-v2.json。父116相关回归、.14独立同SHA原反例/原件核验另由父汇总，当前不自报独审通过。

CPUactual独立审核joint：worker增payload0.078493727＋三control90，GPU110不变；旧令与旧snapshot自然到期后历史CLOSED保留，新snapshot/令后继actualworker成功，旧protocol/release/closure不改，幂等不新开worker。GPUheld joint按raw current观察端点计完整持有；union130→重复130→独立3后133。near-balance原T0至当前持有与历史110重叠，新union约206800；旧原式为container_duration+inherited_scalar110+external.worker+proposed34，错误多计重叠/CPU会误拒，修后GPU申请4可完成actualworker，超余额GPU申请拒。

所有归档command人工wall1900/20/3及历史110均由actualrunner内生成的synthetic输入，只用于会计反例，不是实际消耗；真实预算只取外层command实际wall，后续会话/发布尾仍UNKNOWN。未在此核销历史未知成本。

## 交接

目标/授权如上；当前实现负责人Codex，源码冻结，等待父回归/.14裁决/父直接核验。无本节点后台长期作业。证据为本目录source-freeze-v2/final-v2-gpu/implementation-evidence-summary-v2/joint-v2及三文档。旧v1和所有失败保留；本轮源码如果再改必须重新freeze与必要同源验证。

真实执行NOT_READY：旧C完整门FAIL、完整历史UNKNOWN、有限candidate控制政策applied:false、真实设备归属/G1/profile/Docker尾与真实执行许可/截止可行性均未解决。本轮不做研究合同决定，不改STOP/4000smoke/980评估/正式0/test0、58h/2TiB和原截止。

## v3最终交付追加（09:44后）

独审在v2确认首次record/current共同改alien而sealed.Id保留原值可被首review接受；原first-identity-v2 expected-reject FAIL保留。.13按父授权仅补必要三方Id非空一致断言，及1method含4个首basis身份缺失/矛盾case，不开展额外范围。最终v3 **0bbda355c9eaf3018b7f73a27fc033e346dc06d7c0b2b940d1334fce7476c1a9 /170**；source-freeze-v3/final-source-v3/minimal-v3.patch（SHA da936d088c92913e383339546d1be02c806cb7894ff0141674356b64e993f104）。v2所有PASS为历史，不能迁移。

final-v3-gpu实际16项rc0，wall9.728704695s；exact argv/cwd/env/raw/source before-after均在command及stdout/stderr。implementation-evidence-summary-v3核170源冻结/前/后/当前一致、joint-v3四组351原件SHA一致。两组actualworker联合、union、near-balance均在同SHA完成；父116相关回归与.14原反例/22独立项另核，不代签。当前状态review、源停止改动。后续只做本节点文档核验/交接；无后台长期作业，所有实际外层runner成本归父预算统计，synthetic内嵌账源不重算实际费用。
