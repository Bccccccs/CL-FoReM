# 正式与最终测试必要入口交付（待独审）

2026-11-04T15:04:10.739531+08:00 · Codex实施 · review。来源[SRC-1448](../../../../../../SOURCES.md#src-1448)，用户新授权[SRC-1446](../../../../../../SOURCES.md#src-1446)，原SRC1435消费及FAIL/UNKNOWN均保留。推荐GPT6.1sol/high、Sonnet5.5/high：源码合同、跨阶段设备/累计预算因果；实际后端型号和强度未知。

交付：184源SHA `5a1574769dcea9d697dadd0652de56af0c8884205225de5ad9c833fe515878f9`，freeze-program-v1.json和frozen-source-program-v1/保留完整原件。相对LON仅6必要入口改/2新增/176同，151科学文件字节全同。real-contract-program-v1.json SHA `e51cfa3c4b77fb803e6c37f159f5da137eb870e9b168da5dd4468c0943dee1ad`；run `t9.11-real-program-20261104-r1`只封协议，结果/日志空间尚未创建，不是正式启动。

真实验证：两轮real_* stdlib分别82/86项rc0，原wait及前后184源snapshots见commands/program-adapter-v1、v2（v1当时较早源）；rootwait累计34.12705397605896s，退出已poll。v2含15项新增program边界：固定12stage及算术、10GiB新授权及旧前门源兼容、source漂移拒绝、4719/final argv目录、past/new路径增长去重及诊断.pt、独审指针原件/目录逃逸、profile完整config/steps/unsafe/pending边界、两activity生产prepare的独立allocation/receipt及同stage拒重、实际worker惰性profile/final原生加载与manifest路由。mock不等真实GPU/环境/科学测试；本次无模型/GPU/Docker实际调用。最初未封收据的定点stdlib命令也已实际执行（工具原server终态保留），费用由父全会话包围继续扣，不能只把34s当本次全部成本。

必要语义：profile250k+remaining2750k各为原3M一部分；12周期每run2352、四run9408，final每run296、共1184；历史1176先扣，固定stage写前quota不随扫描数量滚动放宽。每stage独立allocation及有界lease，保存/恢复、控制费单独独审；原生loader合同完整保留，正式不走LON bridge。全部源码/配置/测试冻结后不能再增改；后续独裁、manifest、四model bundle只在doc或results写外部refs，不纳artifact_files。

预算：独立全案budget schema `task9-lr-real-program-budget-admission-v1`，PASS_PROGRAM只在全案可行时签。basis严格7项historical-worker/historical-gpu/C-policy/open-participants/background-inventory/full-program-future-reservation/storage，UNKNOWN保留；显式证据participant rates替代旧硬4slot长窗，future_reserved为纯未来新增五类worker/GPU/calendar/storage/diagnostic，不含额外40GiB fullsave/256MiB unmetered固定预留，后者校验另加一次。全案未来含当前stage，release取max(stage reservation,future_reserved)，不叠加同一阶段两次。历史snapshot逐canonical路径计bytes/diagnostic，covered_external_roots严格两旧证据root；全球past一次入账，现证据树全后缀仅正增长，shrink不退旧额。科学recorder局部view去除已计externalroots，返的仅newroot/log同past snapshot确有重叠项，避免scanner再扣一次。它不是全局余额替代。

独审文件约定：source `task9-lr-real-program-source-review-v1` PASS绑定全部源；release `task9-lr-real-program-release-v1` PASS绑定protocol/source、intended_activity、arm/seed、exactCID/UUID、max_worker/max_gpu/control/save/expiry、source_review/budget_review、完整allocation lease、固定expected_evaluation_before/evaluation_reservation。out/reviews/上一阶段.json仅写 `{"independent_verdict": <.18.2原件ref>}`，原件format `task9-lr-real-program-stage-verdict-v1`/PASS_COMPLETE/活动源身份/固定evaluation_episodes/consumed_transfers/exact_container_stopped True/worker_enclosing_upper_s/evidence；token predecessor_review绑定独审原件ref。remaining另外绑定7项own profile证据（含JSONL/完整checkpoint，文件SHA读，不误作JSON对象）。final须开发PASS_B_E、四run剩余完整独裁、四3M final checkpoint/actor/meta bundle、同一独立200+96 manifest；原test_jobs heldout/碰撞检查先于模型activate，所有完整文件SHA准入核一次，运行期资源轮询不重复读几十GB。

首次正式命令（尚未执行，缺独审资源令）：

```bash
python3 -B -u forem/scripts/task9_11/real_batch.py --prepare-program --contract forem/doc/agent_logs/task9/task9.11/task9.11.18/task9.11.18.1/resume-v1/real-contract-program-v1.json --phase profile --arm C --seed 4718 --infrastructure-release <独审原件绝对路径>
```

exactCID独审后将独审阶段令原字节放program out/releases/profile-C-4718.json，再执行同CLI `--execute-program --contract <同协议> --phase profile --arm C --seed 4718`。后续阶段不改protocol，按固定表推进；任何不足/FAIL保留写前消费，不重启同identity。当前资源独裁NOT_READY，因此以上均尚未执行，没有需清理的新增容器或训练进程。还需独审完整冻结源和全案资源门；本子不自签、不把测试通过当可开训。
