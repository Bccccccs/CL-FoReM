# task9.11.11 · F1/F2 联合实现记录

负责人Codex；请求GPT6.1sol/high，实际模型/推理后端UNKNOWN。兼容推荐Claude Sonnet5.5/high，原因是跨时间证明、快照前序和真实进程启动的联合因果核验。本节点不再委派。开始沿父2026-11-03T23:11:10.673033+08:00登记；开工已读根/forem AGENTS、README/PROGRESS、父及.9/.10/.11三文档、integration-review及verification、SRC1408–1412、冻结合同。工作树codex/task9-lower-improve，HEAD d198e5ca48f86071c05274f9da753f393ce058b4，既有dirty保留。

授权仅四必要core与必要stdlib时钟/成本module、专用测试及本日志/三文档；父后续明确允许test_contract现有deadline测试几处clock接口兼容修改。不改worker/audit/runtime算法、科学配置、历史证据。未运行真实Docker/GPU/模型/环境/仿真/回放/smoke/训练/科学test。所有进程测试都是标准库临时目录与独立虚构旧账。真实CLI/后端仍硬拒candidate；没有实验许可、旧C/UNKNOWN核销或预算截止重置。[授权与冻结合同](../20261103-codex-cross-stage-repair.md)。

## 实际改动

[稳定manifest](implementation-ready.json)记录artifact `ae070d9978376fe6f9dd9213bc2b99a22dd7197e76b553b5f6f06f2ffd3e8068`、167文件SHA及8个逐文件diff。before原件沿父快照，未覆盖；所有新diff独立追加。本次停止源码后只写文档，最终同SHA回归与独立审核由父统一冻结后执行。

- admission：新启动可信当前时钟；dynamic模式不接受caller clock；历史CLOSED验证原release SHA、不可变reservation的admission_clock、outer实际wait completion_clock和同boot/epoch/单调映射、原cap/expiry/deadline及累计stage额度。原自然expiry不撤销历史。资格读取遇显撤拒绝，resource核费读取仍保留原CLOSED charge。
- clock.py：默认真实系统epoch与Linux boot单调域；synthetic服务仅允许temp、false-execution、protocol冻结anchor，append-only hash前序generation只允许前进。所有监督进程读同一服务；历史按被冻结generation证明原映射，不调用caller-selected clock。没有改宿主时间。
- costs.py：首prepare前可选冻结dynamic policy；不可变event有ID、stage、source path/SHA、实测wall和parent关系；source必须完整CLOSED、argv/实际exit、finite墙钟与起讫capture。真实measured_command有界wait结束后封source，未结束/超时留下pending UNKNOWN。事件追加journal防未审核event与source双删后伪恢复旧snapshot。nested仅同stage、同run且完整区间包含的父子，计最外层一次；未知父/循环/越界拒绝。
- 独立budget reviewer角色固定`task9.11.12-cost-reviewer`，不同event writer `task9.11.11-cost-owner`；旧release证据reviewer沿既有静态`.10`，不是把本轮预算review误当新真实执行release。snapshot immutable version/previous hash/commit、review起讫、expiry、完整根coverage/source/event/journal hash、生产全资源核算与剩余额，下一release绑最新snapshot；原protocol/release/closure不改。历史只验原snapshot及其前序，自然过期不追溯，较新损坏不重写原费用。
- 锁：cost.lock兼容线程ID重入与真实跨进程flock；append/review、dispatch原reservation提交共锁。guard在真实worker.Popen紧邻位置用同锁重新read_release、backend.resources、launch_gate，再创建worker与started证据；不跨wait，worker原main再次生产准入。新费用在最后原resources与launch ack间到来时，worker尚未创建即拒绝。运行期资源核查仍覆盖最新费用；未知/未审不转0。
- prepare继续静态科学/路径/输入身份冻结。legacy静态库存模式严格保持，新command仍拒绝；只有首prepare前声明dynamic policy的新候选使用追加事件/快照，不自动迁移旧静态protocol。
- test_contract只改原deadline测试的正常/身份调用使用默认可信当前clock、增加caller-clock拒绝并用原T0作为过期负例。科学GPU套件仍14项，未运行。

## 原始执行与失败保留

所有命令写本目录stdout/stderr/command JSON，不覆盖任何label；源码摘要随command记录。父的`run_evidence.py`从cross-dev03起同时保存before/after完整源SHA、实际argv/cwd/rc/wall。

- lifecycle-dev01：旧14项生产生命周期开发回归PASS/38.211486s。最初自写runner的workspace parent索引错误导致source map为空；已修runner但原件不改，该PASS仅开发信息，**不作最终同SHA回归证据**。
- cross-dev01/dev02：各13项，3 ERROR；release 30s/1800s容不下原协议1800s保存预留，保留原失败。改fixture release为2400s，时钟推进3600s跨release与snapshot；没有改原协议预留。
- cross-dev03：13 PASS/4.971054s，早期联合合同版本；不拼为最终证据。
- cross-dev04：12 PASS/1 FAIL，真实审核子进程未继承模块sys.path，exit1；补明确src导入路径，保留原失败。
- cross-dev05/dev06：各21 PASS；dev07 22 PASS；dev08 23 PASS，均为开发源，仅说明演进，不拼不同版本PASS。
- [cross-dev09-command](cross-dev09-command.json)：25 PASS、wall9.1771049686s；源before=after且对应implementation-ready。联合新增实际审核子进程wall0.0735155977s、exit0，增费恰一次。原[stdout](cross-dev09.stdout.txt)、[stderr](cross-dev09.stderr.txt)；所有临时产物由测试自动清理，stdout保留原SHA和计费摘要，不把已清理temp路径充永久证据。

## 交接

源码稳定，父接手统一freeze和同SHA必要旧回归、.12另一个sol独立自写反例。精确入口`python3 -B forem/src/task9_lr/tests/test_cross_stage_stdlib.py`（25项，零heavy imports）；旧supervision/lifecycle/continuation/entry-audit按父既有标准库入口。新helper `fixture(base)`走生产prepare，`release(p)`绑costs.current_ref，`clock.advance(p,3600)`跨旧expiry；实际Docker/科学执行复用life.Adapter/WorkerExecutionAdapter，未mock生产prepare/admission/resources/worker.main/clock判定。

剩余限制：真实candidate execution_allowed:false，历史真实UNKNOWN未核销，旧C FAIL原件不改，控制包络仍未获用户批准，最外层真实命令/发布退出成本仍不冒精确余额。预算与可行性由父cross_stage_budget_audit原始快照核，不从虚构fixture推导真实可行性。若独审发现同范围缺口，本节点继续修并重新统一freeze；不将当前自报PASS当最终验收。

## 2026-11-03 v2 · 独审F2漏费派回与集中修复

独审原`.12/independent-review-cost-v1-command.json` rc1，原脚本不改：无stage时snapshot review正墙钟但cumulative103→103。父明确同范围补source/event/review发布控制session，不新增无限监督层；新增必要stdlib cost_control.py。每个独立operation full30既有候选包络，artifact/receipt/journal与pending/rejected保护，payload实际wait另列。snapshot当版包括自身reviewcontrol；缺失/失败不充0，旧前序保费。canonical/symlink写前/读核与cost.lock原deadline轮询补齐，仍applied:false/真实硬拒。详.11 RESULTS最新v2节。

稳定v2 source `c8523c9aecc314ce7ae0e71fd16e41ad9531aaf4e3e1315576ecd4d7411ef177`，168文件，implementation-ready-v2.json/9个v2-diff。停止源码后父统一freeze。cross-dev16 35 PASS rc0/11.430235s，同before/after；原反例同断言复跑v2b rc0/.264629s，review累计133→163，新增30。联合新增payload .075548s＋source/event/review metadata90s，旧件SHA不变。开发dev10失败2项原件保留，后续旧开发版本PASS不充新SHA证据。
