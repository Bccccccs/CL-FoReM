# task8.9 r4 独立验收记录

- 开始：2026-10-27 13:13 +0800；负责人 Codex `/root/review_r4`，父显式派发 gpt-6.1-sol / high，与实施者 `/root/init_r4` 不同。平台内部模型标识未另行核验。推荐 Codex GPT6.1sol / high、Claude Sonnet5.5 / high，需核对预算、严格等价、初始化与长期成本边界。
- 授权：[SRC-1210](../../../SOURCES.md#src-1210)；本角色仅只读代码/配置/原件，在本日志和 `forem/results/task8/t8-phase2-20261027/r4-independent-*` 写独立证据。共享 PROGRESS/SOURCES/任务三文档由父维护。
- 禁止：启动测试/采样/训练/重跑、加载或 hash 大 checkpoint/全量资产；新实际核验命令先交父。不改 task7、mapgen、科学条件；不启动3M，不重复已通过优化/资产计费。
- 已读：AGENTS、README/PROGRESS、ENV、task8.9及8.9.1/8.9.2/8.9.3/8.9.1.1/8.9.1.2三文档，r3独立/协调日志与就绪报告，SRC1190–1210，旧 smoke plan/wrapper、原C账本；只读 `assets.py`、`episode.py`、`env.py`、`scene.py`。
- 工作区：main ahead1，大量既有修改保留；父/实施者并行工作，未写其文件。初始宿主进程只读核查见本角色工具记录；未停任何进程。

## 初审（静态，非I1–I6通过）

独立报告：[r4-independent-plan-review.md](../../../../results/task8/t8-phase2-20261027/r4-independent-plan-review.md)。已向父报告两项必须明确的问题：全10324图双路径等价验收的1200s可行性尚无实测依据；旧resume内部1130s，235→900应避免默默下调resume。建议保留原resume1130s，仅primary235→900；最终以父对SRC1210明确解释为准。

本角色未新增实验费用，未运行验证脚本；等交付后核原件。来源1211–1229由父维护，本报告新主张目前是审查建议/推导草稿，不冒充已登记的新实测。

父已明确primary900/外920/ledger940、resume原1130/1155/1175不变，8job共4300；C实际limit尚未扩写、smoke未释放。独立审查来源草稿归SRC1213。I1由实施者唯一写1200s账本，GPU0、正式pool/seed4718/256/float32/threads2/dls_cuda_graph=true，内部380/外390，逐env快照路径 `forem/results/task8/t8-init-20261027/i1.json`。本角色只读脚本，未运行或改动。

已告父及实施者：I1包装器无RNG改动，save有观测扰动；components微小边界残差须说明；asset_other含manifest全JSON/sidecar/验证，非直接磁盘时延。若未256完成则后置批量校验/扫描未发生，I1 partial。全量离线多图CPU并行与I4采样并行不同，串行估算不能直接判预算失败；小块全路径成本/真实CPU quota/worker内存及累计worker秒需由父有界执行计划说明，不用理论64核当工期承诺。

13:18纯静态核C准备，写 [r4-independent-smoke-plan-static.json](../../../../results/task8/t8-phase2-20261027/r4-independent-smoke-plan-static.json)：8job总4300、三级时限符合父解释、新root、64项r3预期值全保留；snapshot pending/cache null禁止执行，原C395.0120486840606/3600、active空；AST读wrapper及8段嵌入Python语法，无实际执行。交父三处freeze前修正：r3/r2陈旧revision/previous_plan，允许incomplete后另组的陈旧note，预检增加已批准manifest/seed小文件精确hash断言。wrapper实际首失败即停正确。当前只是条件准备审查，不是实施I门或smoke验收。

父已明确授权必要最小恢复合同增项：assets.py/scene_cache.py hash及缓存root/index/runtime选择，原12C中training.py用精确旧/新diff登记，不变训练数学/恢复语义。待交付核验；canonical CPU64全量与GPU32有限pilot分别报告，不称全图GPU验证。

13:21独立核pilot固定原件完成，`r4-independent-pilot-review.json`：96 ID/顺序/去重等于plan；progress逐行等report；72cube分六层各12及全部24semantic。32worker循环wall4.831423747353256s、累计worker130.35365117620677s、外账本7.475169397890568s，10838012点、guard0、rc0/无timeout。旧parser参考hash同r3原assets；5个实际小代码hash和report绑定一致；full10228与pilot96不交、并集精确等两manifest10324。仅阅读脚本实际assert/日志/rows，未重载tensor/重hash原PCD。

已交父预算条件推导：循环wall按数量比例约515s，不能当全量上界；全量写盘/worker尾差与启动另计。剩余800.855s，full有界550–570s后约230–250s给I5/独立必要核验，可继续尝试但不得承诺必成。全量/I5均未通过，pilot不是正式池。I1最终partial76/256，380.334736s，stats拒绝200+1在途；实际执行旧import对象，末件hashes仅末次读盘已修改版本，执行版本以父启动64baseline、首快照旧hash和原脚本捕获对象核定，不重跑。

13:26历史v5 reset/M纯读复算，`r4-independent-i1-history-review.json`：原learning2,612,487B/3159行，SHA等i1-summary；step1M/1999698/2999698的episodes4346/13243/37625，窗口差4346/8897/24382、分母1M/999698/1M，率4346/8899.687705687118/24382一致。代码在ended后按单环境实例累加，初次reset不加，因此初始256每fresh run另加一次；不是批量调用次数/提案数。transfers/reset窗口比不严称完整episode平均长度；task7盒体/self sensor及退化后策略条件限制明确。

授权源码delta独立原件：`r4-independent-authorized-deltas.json`和三个diff。training旧原件用当前文件仅反向_contract已知增项重建，SHA严格等r3 a52224...，AST仅_contract变化；episode旧执行源SHA严格等r3，只有cache可选载入分支/构造及os导入；assets只finite检查及math导入。scene.py未变。新scene_cache target tensor_bytes发现后由实施者修正，GPU32脚本将核所有非timing provenance，尚未实际验证。

13:30全量原件独立PASS，`r4-independent-full-cache-review.json`：全10324 ID精确等两manifest，pilot96与full新10228不交；full前96行精确复用原pilot，余行顺序等full plan，progress逐行等新rows，index.records精确等10324 rows。五个来源代码SHA/两manifest SHA同pilot且当前匹配；每record的PCD SHA/scene SHA/v3等权威manifest与冻结scene。原脚本逐图旧/新uint64bits、CPU64 from_asset/cache八tensorequal断言和rc0覆盖全量；本角色无新增解析/重建/张量加载或全PCDhash。

full新10228循环wall383.723501031287s、累计worker12247.146155308932s、外账本386.65839939843863s，guard0；points1075280712仅新图，含pilot全图1086118724。cache index SHA5e99918286ebbc97cbd9e3c366dadb2a16dc62cc9200e61957ca98e22bbac5f2。已交父可按余额释放I5，未自行执行。I2 CPU64全量与I3全PCD合法输入比特门通过；错误格式/回归、GPU32有限对照和完整256 cached reset仍待I5。

I5 plan纯静态无阻断：全GPU回归70/内65、32图GPU32对照45/内40、cached256 reset115/外110/内105，总230。训练guard、测试输出隔离和全部非timing provenance比较已审；153测试仅预计。已建议最终原件记录新增test_scene_cache及参考parser SHA，无新增运行。
