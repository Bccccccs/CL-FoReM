# task8.9.1.2 — 结果与交接

**2026-10-27 已作废（closed）**：用户指令“现在的8.9作废吧，要优化好了整体的地图再开始训练”（[SRC-1220](../../../../../SOURCES.md#src-1220)）。本节点不再执行；以下为作废前的历史状态与记录，原样保留。

状态：**active（I1部分诊断与96图pilot已取证；全量/I5执行中，尚未验收完成）**。2026-10-27 Claude（claude-opus-5-5）建档，授权[SRC-1210](../../../../../SOURCES.md#src-1210)。

## 运行记录

（尚无。）

## r4 I1与初步实现（2026-10-27）

实际实施Codex，父显式gpt-6.1-sol / high；固定Terra gpt-6.1-terra / low；推荐Codex GPT6.1sol与Claude Sonnet5.5同角色强度，跨层等价/恢复合同high，判据固定执行low。[授权SRC1210](../../../../../SOURCES.md#src-1210)。

I1 runner3db950f4c4，内部380s，部分76/256、277提案、273新场景；初态拒110、goal87、witness2、connected_region1，另1未完成提案。380.334736s中asset_scene361.841027s（95.1375%）；PCD读0.245911（0.0647%）、解析171.727805（45.1518%）、asset其他143.537164（37.7397%）、体素/height9.375016（2.4649%）、pack34.007063（8.9414%）、BVH1.108359（0.2914%）、上传0.374096（0.0984%）、planner建立1.358327、初态4.829062、planning1.447970、witness10.460557（2.7504%）。asset其他含manifest读/JSON解析/查找、sidecar/hash/metadata/bounds等，未进一步实测拆分，不当作PCD I/O。分项近似互斥，细小双计时读开销残差保留。[SRC1212](../../../../../SOURCES.md#src-1212)。

I1保留`forem/results/task8/t8-init-20261027/i1.json`与`i1-summary.json`。未进入后置256批量初态核查/首扫描；逐env JSON/hash/runtime快照扰动计入deadline。运行期间磁盘源码开始实施改动，但执行的是此前import对象；末件hash是disk-at-save，不是执行版本。`i1-execution-source/{assets,episode,scene}.py`严格SHA等父r4-preservation-start，summary已assert。

v5旧实测推导：首1M4346次reset/M（230.10转移/reset窗口比），中段8899.6877/M（112.36窗口比），后1M24382/M（41.01窗口比）。输入是旧task7正式v5 learning.jsonl逐step累计episodes，公式`Δepisodes/Δtransfers*1e6`，不含初始256。此为旧策略阶段条件估计，不是task8实测、保证或上界；新PCD/ghost/策略变化可改变episode长度，不能将1000转移smoke偶见0reset外推为百万0。[SRC1212](../../../../../SOURCES.md#src-1212)。

缓存TDD先2个预期缺模块FAIL、8解析对比PASS；实现后10PASS。恢复合同先1预期FAIL，再1PASS。正式I5全回归尚未执行，不能以小测试代替。唯一解析行为改动是逐点有限性检查；新增scene_cache与必要sampler接入，scene.py未改。

96图pilot（立方体train/validation/test各24，语义24）实际全局4.831405s、累计worker130.353651s、10838012点，新旧bits/CPU64八张量均PASS，父派Terra执行成本7.475170s；容器cpu.max=max/cpuset0-63/memory.max=max，32workers各线程1。全量10228新图+复用96正按固定full-plan运行；仍待全量结果、GPU32有限覆盖、I5/独立终审。[SRC1214](../../../../../SOURCES.md#src-1214)。

## r4全量校验原件（已执行，独立审核中）

full job965d4db8df，rc0，runner386.658399s；全局循环383.723501s，新增10228图累计worker 12247.146155s；复用pilot96后10324图累计worker 12377.499806s、1086118724点，全部旧/新parser uint64位一致、CPU64八张量逐图torch.equal。`full.json.worker_wall_s`及`points`只计本job新增10228，`rows`含全部10324；不混算。使用32workers，各torch/OMP/MKL/OpenBLAS1线程；guard optimizer/backward均0。无重验pilot、无GPU/采样/训练，逐row progress与完整manifest/source hash均保留。

证据：`forem/results/task8/t8-init-20261027/full.json`、`full.json.progress.jsonl`、`scene-cache/index.json`。账本此时785.9175641424954/1200s，余414.0824358575046s，active空。全量原件已经取证，尚待不同Sol终核和I5，不将生成者自报当独立通过。

## Claude现场记录（2026-10-27 13:34，claude-opus-5-5）

- Codex r4于13:33因平台额度用尽（“You’ve hit your usage limit … try again at Nov 2nd, 2026 3:08 PM”）turn.failed退出，未写last message。
- 退出时容器内仍有I5缓存reset诊断（账本job `c8cdced0b0`，owner i5-cached-reset，13:32:58启动，内层timeout110s）；Claude未干预，等其自行结束：`forem/results/task8/t8-init-20261027/i5-reset.json` status=pass、51.50s、256/256接受（提案897，拒绝initial396/goal237/witness6/connected2），asset_scene10.35s、initial13.37s、planning4.58s、witness18.42s，峰值GPU allocated1.82GB，optimizer/backward guard均0。
- 账本`forem/logs/task8/t8-init-20261027/budget.json`中该job的active条目因runner随Codex退出而未结账（used显示861.3s）；按原件实际约51.5s＋开销，需后续执行者核对后结账，不由Claude改账本。
- 尚未完成：全量缓存的不同Sol终核、I5全回归、独立验收；C smoke（8 jobs）、就绪报告r4、3M长训。
