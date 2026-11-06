# task9.11.9.2 · 续接接口结果

状态review：实现及自身有界stdlib验证完成，等父统一源码冻结与.10独立审核；真实执行NOT_READY。负责人Codex，请求GPT6.1sol/high，实际平台型号/推理强度未知。兼容推荐Claude Sonnet5.5/high，因协议、身份、路径和累计会计需要跨入口核验；推荐不冒称实际配置。授权与原预算见[SRC-1407](../../../../../SOURCES.md#src-1407)、[SRC-1405](../../../../../SOURCES.md#src-1405)。无模型/环境/真实Docker/回放/smoke/训练/test；无科学参数、旧STOP、原件或共享文档修改。

实现文件仅`forem/scripts/task9_11/prepare.py`、新`forem/src/task9_lr/continuation.py`和新`forem/src/task9_lr/tests/test_continuation_stdlib.py`。原proposal CLI保留；新增`--continuation-candidate`把原proposal变为生产reader可读、不可执行的候选protocol。新包包含原协议/旧STOP/旧账SHA、明确mount映射、四科学配置、原配置输入路径→SHA和`input_aliases`→实际宿主输入路径、源码inventory及候选协议SHA。所有新增成本和review代际统一纳入task9.11递归command inventory；新增/遗漏/改写/缺wall成本均拒绝。CPU外部wall作为GPU费用的相同保守上界是候选工程计费，非GPU实测。旧账已含command按原快照SHA去重。

候选format=`task9-lr-continuation-candidate-v1`，`execution_allowed:false`始终拒真实CLI/Docker/worker；真实旧UNKNOWN/pending决定从未消除。只在独立临时目录显式`synthetic_fixture:true`、独立synthetic账本和synthetic review时，替身可以调用生产准入验证正常链；真实旧账schema不能伪装为synthetic ledger。旧C原完整门仍FAIL，旧科学证据只可REFERENCE_ONLY，不能迁移活动PASS。新review既核SHA又核内容的run/stage/arm/seed/protocol/code/reviewer/PASS。继承4000 smoke/980评估/formal0/test0，剩余10788=196+9408+1184、smoke余0和额外C ON0；T0、deadline、58h/2TiB不变。

|需求/边界|本子裁决|原证据|
|---|---|---|
|生产load_protocol/read_release/evidence/check_resources|PASS（纯临时JSON）；累计旧worker100+新增external3=103、旧评估980；路径/reviewer/code/protocol SHA精确绑定|[14项原命令](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.2/adapter-tests-command.json)，rc0，wall0.6718616132s|
|完整新DAG/非法旧PASS/额外C/smoke/漏依赖|PASS于专用JSON断言；jobs只有G1、L ON，再四profile→remaining和final；final缺development review拒绝|同14项stderr，未代替真实dispatch lifecycle验收|
|预算重置、缺/新增/改写/UNKNOWN外部成本、旧UNKNOWN伪fixture、贴kind冒新PASS、过期/旧reviewer/release|PASS于拒绝反例|同14项原stderr|
|原proposal兼容|PASS，11项rc0，wall0.1370949280s|[原命令](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.2/proposal-compat-tests-command.json)|
|新增纯review候选CLI|首跑FAIL rc1，/history配置路径被当宿主路径；原失败保留。显式mount修复后同argv PASS rc0，wall0.3460133877s|[原FAIL](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.2/candidate-prepare-command.json)、[attempt02](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.2/candidate-prepare-attempt02-command.json)，仅review包，未创建新run results/logs|
|最终inputs键兼容调整|待父统一复验：inputs保留原cfg路径键，另给显式host alias；此小改在上项CLI成功之后，不能把此前PASS冒称此版本CLI已执行|最终源码manifest与prepare-minimal.diff；原v1冻结包不覆写|
|真实历史完整成本/旧C替代/执行release|UNKNOWN/待决定；真实NOT_READY|真实原账保留UNKNOWN，候选pending且执行门拒绝|

稳定源码及最小diff：[manifest](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.2/stable-source-manifest.json)。prepare SHA `1bf8b05abc0d8569fdadd1163293601f535deacd52634dcc283eafd68dcffbd6`；continuation SHA `f0d20809bd219af2ca61fb3a020a42cf6d052477a651d836cd29102f7f1ffe5a`；test SHA `e51315b897b9b8aca7e96f866fc9abd602e2777686c9ea1275a40dad516a98c9`。before、stable快照和最小diff均在自身日志。whole artifact仅[交接时点快照](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.2/artifact-at-child-handoff.json)，兄弟/父仍修改其授权文件，不能称最终集成artifact。

接口交接：`is_continuation/validate_protocol/resolve_path/evidence/assert_execution_allowed/inherited_accounting/validate_external_costs/jobs/prerequisites/validate_release`；.9.1负责admission/supervise接入，父负责worker。fixture helper在上述专用测试`make_fixture(base)`和`fixture_release(p,stage,arm,seed)`，没有mock生产准入/成本/DAG。生产dispatch/收割/closure后继的正式验收由.9.1/.10完成，本子不代签。

下一步仅父统一冻结后重跑14+11、真实纯准备CLI和全链替身并独立审核。可运行的纯准备命令（**该新输出路径尚未执行**）：

```bash
python3 -B /home/ybc/projects/CL-FoReM-task9/forem/scripts/task9_11/prepare.py \
  --continuation-candidate /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/continuation-proposal-20261103T213737+0800.json \
  --output /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.11/task9.11.9/task9.11.9.2/candidate-review-final \
  --proposed-control-envelope-s 30
```

30s只是显式传入的未批准工程包络示例，不是实测或真实会计许可；所有真实入口继续拒绝。每次新准备/审核command会令旧external inventory过期，不能拿过期包释放余额；最终命令记录须纳入父累计成本审计。原失败、已生成review-v1和新旧记录保留。

## 最终接口v2补齐生产准备入口（2026-11-03，替代上方旧稳定SHA）

父发现生产prepare与dispatch仅分项通过、fixture手写freeze不能证明同条链，因此明确追加必要集成工作；本子在原写边界补`freeze_candidate_protocol(protocol_path, output)`及`--candidate-protocol`。函数先调用production `protocol_read`，仅接受execution=false candidate；real仅本项目review日志，synthetic仅已验证canonical临时工作区且output精确等于new_output_root/freeze，拒绝通过symlink把fixture临时mount指向真实目录。四真实配置经validate_matrix后原字节复制，inputs以原配置路径为键、aliases指向明确映射的host输入，协议和artifact SHA一并封存；不Docker、不worker、不release。

`make_fixture`现在在同一临时根的history中建立三个纯metadata JSON替身，再调用此生产freeze函数，返回协议不变。它不再手写freeze/protocol，.9.1/.10可以沿production prepare→dispatch→closure→后继使用同一fixture，不能将本子分项PASS代替全链独立验收。

- [15项v2原命令](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.2/adapter-tests-v2-command.json)，rc0，wall1.0598380007s；新增准备路径校验、四配置原字节和全部inputs/aliases SHA断言，原14项不删。
- [实际纯review新CLI](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.2/candidate-protocol-prepare-v2-command.json)，rc0，wall0.1399778761s；用v1候选JSON生成独立`candidate-protocol-review-v2`，其inventory已用最终inputs原path键＋host aliases。上文“此小改尚未验证”成为历史时点，现已由此v2实际准备验证。
- [v2稳定源码manifest](../../../../../agent_logs/task9/task9.11/task9.11.9/task9.11.9.2/stable-source-manifest-v2.json)：prepare `0e6cd5a6a7fc9099ee544022069a91f399857f5553713281e10d4f96fd87bb44`；continuation `8e2b308bbc292f5b9a2bf7d09c9aca7d09e559804b6b0a4c1bda876af9619bac`；test `a1db86166728d1c6b88a66525879a6d7cbdd1dd80fddfc7f9b79de149e28d25e`。v1源码/失败/产物均保留，新增stable-v2副本和v1→v2差分。

本子实现已再次停止，接口和稳定SHA发父/.9.1；状态仍review，等待父统一最终artifact与完整链复跑、.10只读独立验收。推荐/实际模型和授权限制不变，真实旧账UNKNOWN/旧C FAIL/候选执行false/pending决定不变。

父接受补注 2026-11-03T22:48:48.791274+08:00：本轮工程集成与独立验收done，真实NOT_READY。最终统一v3 artifact `1ba4e9891aa0aa53814fec9eee9064300da6f23a6240a56938d75e230c9105b1`；父81项及独立86项、54引用SHA均从原件核验，早期版本PASS不迁移。task9.11.9 RESULTS为本次事实汇总，旧C/历史UNKNOWN/预算/截止不变。来源SRC-1408–1410，父负责共享来源登记。
