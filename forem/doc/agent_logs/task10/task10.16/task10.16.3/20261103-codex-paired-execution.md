# task10.16.3 新KL配对评估执行

开始：2026-11-03T22:00:35.683862+08:00；负责人Codex；工作树`/home/ybc/projects/CL-FoReM-task10`，分支`codex/task10-upper-wm`，HEAD91f538cf2ee10bebffd6b643d5c908fa0d419ced，既有dirty改动保留。实际模型/推理档位未从平台核实，记未知；推荐GPT6.1sol/medium、Sonnet5.5/medium，因需核验冻结输入、预算与原件统计。执行者有自主选模和先建档委派权限，本次独立完成，父统一GPU1、预算及验收。

用户授权：新训练`t10-kl-online-20261103-s101`只读，核验relative_uniform固定alpha=.35、1200/200及CPU审计；复用旧`t10-eval-20261103-s101`的同12地图/seed101/B3seed4718，唯一新trained评估，12回合/1800真实/0更新/5400秒，先到即止、不重跑。训练launch残留running/外层退出码缺失保留；禁止调用task10_kl_pipeline.py。独立持久launcher启动核实后退出主动监督，可顺序CPU只读report。

准备修改：本日志、PROGRESS、SOURCES、本节点三文档及父RESULTS；必要修复仅评估scripts/专项tests；运行产物写入`/home/ybc/projects/CL-FoReM-task10/forem/results/task10/t10-kl-eval-20261103-s101`和logs/task10对应文件，训练/旧评估原件只读。未授权新增训练、场景、调参或自动重试。

已读根AGENTS、ENV、README、PROGRESS、16三文档、16.3三文档及19项CPU专项源码；现场GPU无compute进程，runtime只映射物理GPU1，参考挂载只读、/workspace为本工作树。CPU审计/冻结和评估尚未执行。

## 2026-11-03T22:06:30.692933+08:00 · CPU核验/冻结完成，准备独立持久启动

依据[SRC-T10-038](../../../../SOURCES.md#src-t10-038)，新run `t10-kl-eval-20261103-s101`，source-audit、preflight、freeze均rc0；新目标固定KL .35、1200/200、actor=final learner；旧reference-audit verified_complete，321冻结输入，manifest SHA `a1901e2f4efe714f0640003309eaa2faae018a82779e64f13a53614b05d76eff`。新旧初始权重相等，12地图/seed101/B3seed4718/环境配置同旧。已读19项CPU专项和实际执行路径，无必要执行修复，本轮没有改执行脚本或重跑专项；run内收尾脚本仅编译检查。

推荐GPT6.1sol/medium、Sonnet5.5/medium；实际模型/强度未知，本次独立执行；执行者可自主选模/建档委派，父统一GPU/预算。新评估尚未开始，原地行为/成功率均待真实评估。训练launch残留running及退出码缺失保留，不用pipeline。

实际CPU命令：
```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 /workspace/scripts/task10_online_audit.py --run /workspace/results/task10/t10-kl-online-20261103-s101 --output /workspace/results/task10/t10-kl-eval-20261103-s101/source-audit.json'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 forem-task10-runtime timeout 120s python3 -u /workspace/results/task10/t10-kl-eval-20261103-s101/preflight.py'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src -e OMP_NUM_THREADS=2 -e TASK10_CODE_COMMIT=91f538cf2ee10bebffd6b643d5c908fa0d419ced forem-task10-runtime timeout 120s python3 -u /workspace/scripts/task10_kl_validation.py freeze --run /workspace/results/task10/t10-kl-eval-20261103-s101 --source /workspace/results/task10/t10-kl-online-20261103-s101 --reference /workspace/results/task10/t10-eval-20261103-s101'
```
三者rc0。preflight/freeze stdout/stderr在新run下。脚本读取：19项专项覆盖清单/目标/严格预算/初态执行前拒绝/不完整分母/worker launcher异常不得通过；base worker eval/no_grad/每回合VCM reset/有效最大logit，未改src或执行脚本。只读训练目录，未写review覆盖源审计。

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

2026-11-03T22:30:50.608942+08:00 用户检查后CPU补证完成，原report参数错误保留，新增独立适配器及3专项，report-v2与父parent-check-v2均verified_complete/rc0。新handoff-v2完整验收true；最终10/12、原地0/21，配对同uniform持平。详见同目录20261103-codex-report-check.md与SRC-T10-040；没有重跑评估。
