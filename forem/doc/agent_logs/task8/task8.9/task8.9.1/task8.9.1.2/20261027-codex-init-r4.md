# task8.9.1.2 r4诊断/实现日志

负责人Codex，父显式派发gpt-6.1-sol / high；推荐Codex GPT6.1sol / high、Claude Sonnet5.5 / high，因逐元素等价及跨层归因；实际底层标识未独立核验。授权[SRC-1210](../../../../../SOURCES.md#src-1210)，父维护共享PROGRESS/SOURCES。

## 范围与开始

2026-10-27核根AGENTS、README、PROGRESS、ENV、task8.9/task8.9.1/task8.9.1.2三文档与r3报告/失败trace。main分支大量既有未提交内容，保留；仅本子任务必要task8_sim源码/新脚本/测试、三文档与此日志可写。不得训练、调用mapgen、改task7或规则。系统化排错先取证再决定实现。GPU compute列表空；forem-dev已运行，不启动/停止容器。

## 预算计划（尚未执行）

新账本forem/logs/task8/t8-init-20261027/budget.json，上限1200s；runner来自已存在r4 v3父账本runner，只换账本目录，按实际wall累加含失败。I1一次256正式seed4718，内部380s/外部390s；其余810s留实现/等价/重测/回归/独立验收。固定10300+24全量生成/校验交父派Terra，先估计成本，若超预算即报告。

## I1结果与方案（已执行）

I1到内部380s，76/256，273新场景，asset_scene95.14%，PCD parse45.15%/asset其他37.74%/pack8.94%；非采样规则CPU主导，保留原规则。GPU0旧已import代码运行不受磁盘实施改动影响；summary按父start保全hash重建三旧原件并严格校验，动态disk-at-save hash限制明确。summary运行3028a12df3 rc0/0.114419s。

父要求考虑离线独立CPU并行；96图32worker pilot已PASS，源码/manifest hash冻结。full预算570/内部560，由父派Terra执行，不自行执行10324全量。I5已准备三job总reservation200s：GPU完整回归65、GPU32等价20、缓存256reset115；不重复CPU全套。等待父据余额释放。

新增/修改：src/task8_sim/scene_cache.py、assets.py、episode.py；tests/assets_reference_r3.py、test_scene_cache.py；scripts/task8_init_diagnose.py、task8_scene_cache_build.py、task8_scene_cache_gpu_check.py、task8_sim_regression_r4.py、task8_init_summarize.py。父明确追加允许唯一C文件training.py::_contract，绑定cache实现/资产实现与runtime root/index hash，其他数学/恢复状态不动。无(c)采样并行、无optimizer/训练/mapgen，scene.py未变。

## r4全量校验原件（已执行，独立审核中）

full job965d4db8df，rc0，runner386.658399s；全局循环383.723501s，新增10228图累计worker 12247.146155s；复用pilot96后10324图累计worker 12377.499806s、1086118724点，全部旧/新parser uint64位一致、CPU64八张量逐图torch.equal。`full.json.worker_wall_s`及`points`只计本job新增10228，`rows`含全部10324；不混算。使用32workers，各torch/OMP/MKL/OpenBLAS1线程；guard optimizer/backward均0。无重验pilot、无GPU/采样/训练，逐row progress与完整manifest/source hash均保留。

证据：`forem/results/task8/t8-init-20261027/full.json`、`full.json.progress.jsonl`、`scene-cache/index.json`。账本此时785.9175641424954/1200s，余414.0824358575046s，active空。全量原件已经取证，尚待不同Sol终核和I5，不将生成者自报当独立通过。
