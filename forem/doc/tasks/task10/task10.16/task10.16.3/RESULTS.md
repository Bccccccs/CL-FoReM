# task10.16.3 结果

当前（2026-11-03 CPU补证后）：**review，完整工程验收通过，待当前决策者最终审核**。新trained严格成功10/12、原地0/21；原report失败记录保留，完整补证为report-v2与parent-check-v2。[来源](../../../../SOURCES.md#src-t10-040)。

2026-11-03 16:58 +08 · Codex · review：最小单策略评估wrapper、独立launcher与CPU专项已新增，待父审核。父转达用户最新要求“如果启动了就退出监督，等他一直跑吧”，本子已停止新增工作，未启动评估或自动串联。唯一新目标训练由父此前启动，本子未触碰其进程与冻结输入。

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，涉及目标版本、跨run初态和硬预算核对；实际模型/强度无法独立核实，记未知。已独立完成，无下级委派。授权与参数来源：[SRC-T10-036](../../../../SOURCES.md#src-t10-036)，本CPU实现不代表新目标评估已完成。

实际新增且仅新增：

- `forem/scripts/task10_kl_validation.py`：freeze/supervise/worker/report接口，复用base.freeze/worker；仅12trained、6+6、1800决策、0更新、5400秒；强验新actor与完整learner固定KL .35目标。执行前逐原始初态比较旧trained，并核旧initial/uniform初态可复用；差异保存后拒绝env.step。保存新旧初始权重hash比较。报告重算原件，含固定分母missing、原地选择/logit领先、三旧策略配对、初态匹配、冻结文件和无更新核查；worker/launcher异常不因已落12行而通过。
- `forem/scripts/task10_kl_validation_launch.py`：独立一次启动，独占launch.json、拒重启，沿原epoch 5400秒shell及Python监督。
- `forem/scripts/tests/test_task10_kl_validation.py`：19项CPU专项。

未修改src、既有训练脚本或config，未提交。未执行新freeze、真实report、launcher/supervise/worker、GPU评估或自动串联。新模型/旧reference的完整freeze实际接线、launcher实际进程监督、新评估GPU入口、完整端到端和性能均**尚未验证**，不把CPU单元通过当成放行评估。

实际命令：

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -m pytest -q --basetemp=/tmp/t10-16-3-wrapper /workspace/scripts/tests/test_task10_kl_validation.py'
git diff --check
```

结果 **19 passed / 1.61s / rc0**，diff检查rc0；原始log：[wrapper-tests.txt](../../../../../logs/task10/task10.16.3/wrapper-tests.txt)。CPU专项验证：12身份过滤及重复/缺少拒绝、objective/version/fixed alpha合同、严格1800reserve及12回合限制、零更新、typed初态一致与dtype变化拒绝/差异落盘、reference文件变更拒绝、worker在初态差异时不进入执行且恢复base符号、partial固定12分母与missing、完整12行但failed worker/launcher rc非0/在途/summary错状态仍failed、干净完整状态才verified_complete。report状态测试使用合成fixtures及审计函数stub，仅验证集成判定，不声称真实原件完整审计通过。

交接：无本子遗留进程，父负责全局来源台账和共享进度。三个脚本接口按[PROCEDURE](PROCEDURE.md)已约定保留；后续用户再次唤起时，先确认训练与原硬期限状态，核新source审计，再独立审核freeze/launcher/真实入口；本轮不自动继续。过程记录：[日志](../../../../agent_logs/task10/task10.16/task10.16.3/20261103-codex-single-validation.md)。

## 2026-11-03T22:06:30.692933+08:00 · CPU核验/冻结完成，准备独立持久启动

依据[SRC-T10-038](../../../../SOURCES.md#src-t10-038)，新run `t10-kl-eval-20261103-s101`，source-audit、preflight、freeze均rc0；新目标固定KL .35、1200/200、actor=final learner；旧reference-audit verified_complete，321冻结输入，manifest SHA `a1901e2f4efe714f0640003309eaa2faae018a82779e64f13a53614b05d76eff`。新旧初始权重相等，12地图/seed101/B3seed4718/环境配置同旧。已读19项CPU专项和实际执行路径，无必要执行修复，本轮没有改执行脚本或重跑专项；run内收尾脚本仅编译检查。

推荐GPT6.1sol/medium、Sonnet5.5/medium；实际模型/强度未知，本次独立执行；执行者可自主选模/建档委派，父统一GPU/预算。新评估尚未开始，原地行为/成功率均待真实评估。训练launch残留running及退出码缺失保留，不用pipeline。

## 2026-11-03T22:08:07.747066+08:00 · 唯一评估已独立启动

run `t10-kl-eval-20261103-s101`，开始2026-11-03T22:06:51.829083+08:00，原epoch硬截止2026-11-03T23:36:51.829083+08:00（5400秒）；12回合/1800真实/0更新，先到即止。host driver PID534271（PPID1、SID534271），launcher PID534276，docker client PID534277；容器forem-task10-runtime，GPU1。detached-start.json与detached-status.json记载完整命令、PID、session、stdout/stderr和后续退出状态。原launcher命令保存在launch.json；无pipeline/重启。

实际执行：host Python subprocess.Popen(['/usr/bin/python3','-u','.../run_once.py'],start_new_session=True,stdin=DEVNULL,stdout=driver.stdout,stderr=driver.stderr)。run_once顺序调用task10_kl_validation_launch.py --run 新run --commit 91f538cf2ee10bebffd6b643d5c908fa0d419ced；同run launch.json独占创建并状态running。report与finalize仅在launcher返回后由独立driver执行，不依赖本聊天继续。stdout/stderr在forem/logs/task10/t10-kl-eval-20261103-s101/，worker合并日志为forem/logs/task10/t10-kl-eval-20261103-s101-eval.log。

进度与退出只读：检查run/detached-status.json、launch.json、budget.json、summary.json、report.json、handoff.json；末两者结束后生成。需要停止时先核实该run命令行与PID，只向对应worker发TERM，保留原件及缺失，不重启；不停止容器或其他进程。用户要求启动核实后退出主动监督，未安排周期监控。原地行为是否改变、任务成功率是否提高目前均待真实结果，不能提前给结论。最终交接由顺序report/finalize写本节点及父RESULTS、PROGRESS、SOURCES与日志，状态review待当前决策者审核。[来源](../../../../SOURCES.md#src-t10-038)。

2026-11-03T22:08:49.785967+08:00 启动核实完成并退出主动监督：容器worker PID1300，entry-check verified，实际upper/B3参数cuda:0（物理GPU1）、torch2.7.1+cu128、threads2、确定性True、eval/no_grad/记忆复位均实证通过；入口0新真实/0更新。首回合sparse_validation_00004在任何真实env.step前，physical/route/grid/observation/candidates/mask/proposal_seed/map_geometry全部typed hash匹配旧原始初态，differing_keys=[]。启动快照为1回合已开始、0回合完成、首决策在途1，不能当完成或收益证据。startup-verified.json记录本次收尾；原地行为与成功率仍待结束报告。已核实detached driver PPID1/SID=PID，stdout/stderr独立，后续无需聊天存活。只读报告、12初态logit CSV和文档交接已顺序排定；最终验收保留report verified_complete等全谓词，不重跑。依据[SRC-T10-038](../../../../SOURCES.md#src-t10-038)。

## 2026-11-03T22:19:41.078682+08:00 · 新KL唯一评估结束，交决策者审核

run `t10-kl-eval-20261103-s101`，状态 **review_incomplete**，完整验收=False。依据[SRC-T10-039](../../../../SOURCES.md#src-t10-039)，实际Codex模型/档位未知，推荐GPT6.1sol/medium、Sonnet5.5/medium；独立执行，无子Agent。执行者有自主选模/建档委派权限，父统一GPU与预算。

严格成功 **10/12**，完成12/12、缺失0、在途0、更新0；worker `complete`、launcher `process_exited` rc0；report `failed` rc1；hard epoch与worker账本核对见handoff.json。不是仅凭rc0认定完整。

原地行为是否改变：**完整验收未通过，不能给出完整12场景结论；已落盘原地0/21，旧trained 52/52。** 12个相同初态的原地领先定义为有效原地最大logit减有效移动最大logit，逐图数值在run/initial-logit-comparison.csv，下表保留缺失。不同后续轨迹logits不作逐步比较，完整轨迹的原地比例只作行为描述。

任务成功率是否提高：**完整验收未通过；已完成12/12，已知严格成功10/12、缺失0，不按完整样本宣称提高。** 配对胜负平缺失：`{"new_trained_vs_old_trained": {"win": 10, "loss": 0, "tie": 2, "missing": 0}, "new_trained_vs_old_initial": {"win": 10, "loss": 0, "tie": 2, "missing": 0}, "new_trained_vs_old_uniform": {"win": 0, "loss": 0, "tie": 12, "missing": 0}}`。终止主因：`{"failure_limit": 2, "strict_success": 10}`；原始attempt失败归因（IK→base→arm→self优先级）：`{'self_collision': 20, 'ik_rejected': 20}`；零尝试停滞不作为IK失败。

|地图|初态一致|旧trained原地logit领先|新trained原地logit领先|新首选原地|
|---|---|---:|---:|---|
|sparse_validation_00004|True|0.3073614165186882|-0.7207183931022882|False|
|standard_validation_00000|True|0.18546629697084427|-0.8024830296635628|False|
|sparse_validation_00005|True|0.24984685331583023|-0.842853382229805|False|
|standard_validation_00001|True|0.30537763983011246|-0.7940088901668787|False|
|sparse_validation_00006|True|0.26889366656541824|-0.798556923866272|False|
|standard_validation_00002|True|0.2829212471842766|-0.6458591893315315|False|
|sparse_validation_00007|True|0.23355264216661453|-0.8694502413272858|False|
|standard_validation_00003|True|0.4535053074359894|-0.4527432322502136|False|
|sparse_validation_00008|True|0.31625470519065857|-0.5746154580265284|False|
|standard_validation_00004|True|0.45152101665735245|-0.5142754465341568|False|
|sparse_validation_00009|True|0.19260545819997787|-0.9922315180301666|False|
|standard_validation_00005|True|0.323529452085495|-0.5768617112189531|False|

原件在`forem/results/task10/t10-kl-eval-20261103-s101/`：manifest/freeze-lock/launch/budget/summary/entry-check/weights、initial/initial-comparisons、episodes、decisions、report.json、handoff.json；逐原始journal/episode复算，不使用worker aggregate评分。源码及模型哈希见manifest/frozen-code，manifest SHA256 `a1901e2f4efe714f0640003309eaa2faae018a82779e64f13a53614b05d76eff`。只读复算入口为task10_kl_validation.py report；run内finalize.py补齐原始12初态logit表、训练目录递归SHA及完整验收谓词。source-input-hashes.json复核变化=0；异常=[]，report issues=["snapshot_checks failed: TypeError('snapshot_checks() takes 3 positional arguments but 4 were given')"]。detached-status.json保存launcher/report退出码，日志独立保存stdout/stderr，不重启/不补场景。

源训练launch.json残留running、外层退出码缺失原样保留；进入评估的依据是已核验worker终态、最终checkpoint及CPU原件审计。所有结论仅限单训练种子、12个validation场景，未跑test、未追加更新或训练。下一步由当前决策者审核；失败/到限原件及缺失保留，禁止自动重跑。

## 2026-11-03T22:30:50.608942+08:00 · CPU报告修复后完整验收，交决策者审核

**当前状态review：工程执行与原件复算通过；最终审核归当前决策者。** 依据[SRC-T10-040](../../../../SOURCES.md#src-t10-040)，本节取代22:19时“完整验收未通过”的当前状态，原failed报告/交接和历史记录保留。实际执行者Codex，具体模型/强度未知；推荐GPT6.1sol/medium、Sonnet5.5/medium，涉及原始终态/报告接口核验。可自主选模与先建档委派，本次独立完成，父统一GPU/预算/原件验收。

原报告的snapshot_checks参数数量错误已通过独立CPU适配器修复，原冻结脚本不改；3项实际审计接口测试通过（3passed/1.36s/rc0）。修正版report-v2.json及父parent-check-v2.json均 **verified_complete、issues=[]、rc0**。完整12/12、缺失0、预留21=完成21、在途0、更新0；worker complete/error null，launcher正常退出rc0；12初态执行前匹配、独立原始快照/首次观测候选审计、冻结权重和eval/no_grad/记忆复位均通过。321冻结输入、254训练源文件、70检查前原件SHA均未变；训练源launch残留running及原外层退出码缺失仍原样保留。

|比较项|旧trained|新KL trained|旧uniform|
|---|---:|---:|---:|
|严格成功/12|0/12|10/12（83.33%）|10/12（83.33%）|
|sparse、standard|0/6、0/6|5/6、5/6|5/6、5/6|
|原地选择/本组决策|52/52|0/21|0/19|

**原地行为是否改变：改变。** 本轮所有21次真实决策均选移动候选；12个相同初态均从原地logit领先转为落后：旧范围+0.185466～+0.453505、均+0.297570；新范围−0.992232～−0.452743、均−0.715388。逐图精确值沿用上节及initial-logit-comparison.csv。原地比例是各自完整轨迹描述，logit比较仅用同12初态，不逐步比较分岔后的轨迹。

**任务成功率是否提高：相对旧trained提高，0/12→10/12（+83.33个百分点）；与旧uniform持平。** 配对新对旧trained为胜10/负0/平2/缺失0；对uniform为胜0/负0/平12/缺失0。自然结束原因：10严格成功、2失败上限、0停滞；失败图sparse00004为20次self_collision，standard00000为20次ik_rejected，其他碰撞归因0，按实际attempt及Core优先级核验。工程检查通过不代表普遍方法有效，单种子12validation场景限制保留。

实际唯一GPU执行22:06:51.829083–22:19:18.778081+08，launcher wall746.948999s（12m26.949s），预算90min未用尽；无本run活进程、GPU compute为空。没有重跑评估，没有新增真实交互/更新/GPU。两策略训练规模虽匹配，后续采样轨迹随策略变化，不能据此把改善归于唯一因果或保证泛化。

原件、精确命令及版本：run/report-v2.json、parent-check-v2.json、report-check-exits.json、handoff-v2.json为本次完整补证；run/report.json、handoff.json保留初次失败。适配器SHA `9353463e6480e6ada57ee94786815bfa6327e875acc52b0d8e9dd7c8a0a2d1f8`；report-v2 SHA `681b4725534ec574f9d1a8c0b516fbff6bb891cf4207909e70f70e2ca8bf35c8`；parent-check-v2 SHA `35fbe863860b1e17e4bb16f8a5d694f594d1e0132cf0fd7a2ffcc726ed3a56f5`；原manifest SHA仍为a1901e2f4efe714f0640003309eaa2faae018a82779e64f13a53614b05d76eff。下面三条实际CPU命令均0新增交互/0更新：

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -m pytest -q --basetemp=/tmp/t10-16-3-report-v2 /workspace/scripts/tests/test_task10_kl_validation_report_v2.py'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -u /workspace/scripts/task10_kl_validation_report_v2.py --run /workspace/results/task10/t10-kl-eval-20261103-s101 --output /workspace/results/task10/t10-kl-eval-20261103-s101/report-v2.json'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -u /workspace/results/task10/t10-kl-eval-20261103-s101/parent_check_v2.py'
```
均rc0；报告适配器拒覆盖已有输出。仅再次只读复算时使用新的--output路径，不重启worker。

交接：本轮已无运行任务；完整验收条件通过，交当前决策者复核report-v2、parent-check-v2与handoff-v2。没有擅自新增训练规模、场景、功能或下一实验。原外层训练退出码缺失属于保留限制，不伪造补写。

## 2026-11-03 · 决策者最终验收
**done，本轮工程与固定12场景改善均通过。** CPU独立复跑v2为verified_complete/issues=[]/rc0，另核12身份与终局/账本。接受原地52/52→0/21、成功0/12→10/12的该清单结论，与uniform持平。两失败及单种子局限保留。原报告接口错误已按保留原件方式修复，不能据早期failed否定现已补齐的原始快照验收。[来源](../../../../SOURCES.md#src-t10-041)
