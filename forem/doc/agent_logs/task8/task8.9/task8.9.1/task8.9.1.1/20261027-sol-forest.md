# task8.9.1.1 跨场景森林实施

负责人 Codex /root/opt_r3；父显式指定 gpt-6.1-sol / high。推荐 GPT6.1sol / high、Claude Sonnet5.5 / high，因需核查GPU批量遍历与比特等价。授权 [SRC-1190](../../../../../SOURCES.md#src-1190)，父登记PROGRESS及共享来源，本节点不并发写共享文档。

2026-10-27 开始：已读根AGENTS、README、PROGRESS、ENV、task8/8.9/8.9.1及本节点三文档、r2日志/summary/就绪报告、SRC1190。main既有大量修改保留；仅写scene.py、必要新增等价tests/验证入口、本节点三文档与本日志。初始scene.py SHA256=d9d98d98d0dd51094eecb999d24e0eaf44fb6bcd7611275bf818732fb7f6de55。GPU初检compute空，forem-dev已运行；不建停容器、不改task7、不训练。

计划（尚未执行）：先RED测试，后共享森林raycast；保持_slab算术与dtype，保留loop开关；replace失效缓存，select继承开关。碰撞占比2–3%，本次不动。O1固定24语义+32立方体、CPU64/GPU32、b1/16/64/256距离/命中/Depth、每设备50 Core Transition逐字段相等；O2全task8_sim回归；O3交Terra固定清单；O4由不同Sol终验。新账本1500s，运行前核GPU，所有测试/profile/独立验收/P5计入，预留充分余额。

## 编码与CPU证据

- RED `red-forest` rc1：3项因缺少raycast_backend参数失败（2.5987s）；GREEN `green-forest` rc0：3 passed（2.6142s）。实际命令完整保存在新budget.commands与同名stdout。
- scene.py仅SceneBatch：默认forest，显式loop参照；唯一scene BVH拼接、children偏移、行root映射、65536射线有界packet；_slab、单scene路径、体素几何及碰撞不改。65536是本次工程存储界限选择，不宣称外部标准或已最优。select继承开关；replace失效缓存；序列化剔除纯派生森林，恢复惰性重建，不改task8_lower checkpoint协议。[SRC-1191](../../../../../SOURCES.md#src-1191)由父登记。
- O1 CPU64 rc0（122.9077s外层）：32立方体+24语义原PCD重构+empty/边角fixture；b1/16/64/256距离/命中torch.equal；Depth7字段全等；50 Core.step/100 active转移/199 committed子步，Transition全部13字段全等。CPU执行版脚本保存在accept-cpu-executed.py；后续env.reset只调用SceneBatch.replace，保持loop。GPU执行版新增逐步forest/loop断言与reset计数。
- O2 CPU rc0（27.4043s外层）：131 passed/11 skipped，optimizer_constructed=backward_calls=0。CPU空CUDA可见，11 skip为CUDA专门项；完整task8_sim suite无训练操作。CPU回归未触发GPU专属旧产物写入。
- 为避免GPU全回归覆盖t8-voxv3旧cube-default JSON，仅test_pcd_env输出增加可选TASK8_TEST_ARTIFACT_ROOT（默认不变），父明确认可必要验证范围。原文件副本test-pcd-env-before.py，SHA256 3b5fc6ed116a5d435cab2220ae961324b98048efe0f3c40039aac7fd0c209f7e；GPU将指向本r3目录。生产环境未受影响。
- 新账本已用155.5249131666s，active为O1GPU；本次GPU启动前nvidia-smi compute为空。固定4job清单r3-fixed-profile-jobs.json（cube/semantic b64/256各warmup2+20测量步）已准备、尚未执行；复制prepare描述，引用原cache，不重复prepare或改R2原件。Terra固定执行、独立Sol审核尚待。

## 实施验证交付（等待独立验收/固定性能）

O1GPU rc0/113.8979995959s，四batch全部距离/命中/Depth7字段全等，Core50step/100active/179committed、13字段全等；每步forest/loop断言通过，resets0。O2GPU rc0/55.851224849s，142passed/0skip，guard0；GPU专门产物写本run regression-gpu，不触旧JSON。新账本325.2741376115/1500s、余1174.7258623885s、active=null，无本节点后台任务。scene最终交付hash d8a9dfdd261161b3e65aa38b6e19a5a61496a0781334213cb5ef8b3028507041，implementation-hashes.json及scene.diff已保存。共享SOURCES/PROGRESS/父文档未改，无提交/推送/合并。

已交父：本节点三文档、1191/1192草稿及1194待补位置、O1/O2原件/账本/明确diff、Terra四job固定清单。父安排不同Sol high独立核原件及Terra执行，本实施者按父要求先结束释放槽位，待followup汇总1194/RESULTS和A P5。不把本轮O1/O2当O3/O4通过，不跑训练或额外优化。风险/剩余/下一步见RESULTS交接节。

最终freeze-profile-inputs rc0，4个清单hash匹配，4jobs尚未执行；费用0.029857791s，同账本最终325.3039954025/1500s、余1174.6960045975s、active=null。

## 固定性能后父followup：只读汇总与P5静态框架

父明确追加范围：读取Terra四原JSON/CSV/固定日志，汇总summary-r3.json/md与1194完整草稿；允许更新task8.9.1本节点三文档，task8.9/共享来源进度仍归父。不得新增profile/测试/训练；C smoke未执行，P5只出静态设计与缺项。

已完成标准库原件复核：四组各20完整step、warmup2、guard0；逐步transfer/wall/sim和、所有raw分项n/sum/p50/p95/max/CUDA events、frozen hash、账本命令/退出码、GPU CSV均一致。新入口forem/scripts/task8_profile_summarize_r3.py仅报告读取，无模拟器/torch加载。首次汇总rc1为argv切片错误把`--`包含在命令中；修正切片后rc0，不是数据/语义不一致，原失败保留。第三次只读汇总纳入已到位独立O3/O4结果rc0。三条报告命令总0.2958099823445s，不新增任何GPU测试/profile。

cube64/256=109.542321/145.353020 transfer/s，semantic64/256=94.622670/116.288947；相对R2完整窗口cube64/2566.190314×/8.081314×、semantic25610.620398×。语义64无旧基准。R2重复256前缀、R3连续20步且semantic后段4次cached ended-reset，整体比不是20步配对因果量。公共前缀step非wall元数据精确相同，加权公共前缀比cube64/2566.190314×/7.517871×、semantic25611.867125×；复用计时不作独立样本/置信区间。新cube/semantic256 raycast占loop38.45%/34.36%，其他原分项/显存限制见summary。

不同实施者Sol/high的r3-independent-opt-final.json已判O3固定负载PASS/O4 PASS，已亲读并核其数字与本汇总一致；本优化子节点done，父A节点仍review/P5 pending。实际模型仍父明确gpt-6.1-sol/high，固定Terra gpt-6.1-terra/low；推荐Sol/Sonnet5.5 high作归因/验收。

P5只按代码推导：U_k(N)=max(0,floor(N/k)-floor(257/k))，B0/B3 1000实际743/75更新、3M为2999743/299975；smoke更新密度较低，不能直接按CLI吞吐乘3M。c_update须为同组增量sample+SAC，现consume_transition混push/set_transfer无法单独识别；100+96只合并196有wall；正式13次完整CP/12次196/3000诊断。state_dict保存[:size]，smokeCP非满100k，满回放仅payload推导9,892,500,000B，save/load时延/随机reset/缓存增长/争用保留未知、不填0、不移植旧task7均值冒充新测量。未新运行任何东西以补这些缺项，不增加功能/实验授权。

完整SRC1194草稿、summary-r3.json/md已交父；子节点与task8.9.1三文档同步结果并保留全部历史。共享SOURCES/PROGRESS/task8.9未改。最新opt账本473.033114723861/1500s，余1026.966885276139s，active=null；四profile147.433309338987s＋报告复算0.2958099823445s。无本节点后台，无提交/推送/合并；等待C smoke完成后父followup成本。

## C smoke释放后的P5 followup准备

父明确C固定8job已因优化/正式池独立PASS释放，GPU1原3600s账本，B0-primary进行中。本负责人仅读实际原件，允许写P5脚本/成本模板、8.9.1 RESULTS及SRC1201草稿，禁止生产/C实现、共享来源进度、额外GPU/加载/optimizer或自行重试；任何新实际验证先报父。模型仍父显式Sol/high，推荐GPT6.1sol/Sonnet5.5 high。

已新增纯标准库 `task8_cost_summarize_r3.py`，首次opt runner `p5-cost-snapshot-prepare` rc0/0.0387233244s；输出cost-r3.json/md为进行中模板（preflight rc0、B0-primary进行中/B3未跑、无完整summary，无P5或48h通过）。只读JSON/JSONL/CSV和checkpoint stat，无torch/checkpoint加载或任何实际验证。SRC1201完整进行中草稿sources-p5-r3-draft.md已给父；后续每primary/resume结束读取更新，发现C失败先报父，不修/重试。

## P5最终失败交接（不再运行）

父通报C首失败并要求最终只读收尾。原件确认preflightPASS，B0-primary ba918a165a rc1，CLI243.166660481s、原账本243.370039869s/timeout=false，初始reset逐环境采样在episode.py:100检出deadline SamplingIncomplete；metadata0steps/0actions，无有效训练吞吐，B0恢复/B3/196均未跑。原serial表子项status仍running但整体stopped/exit1/end/finished命令证明已停，保持原件不改。CSV243个1Hz样本峰值11306MiB，仅全命令设备采样，非PyTorch精确训练峰值。失败513566022B interrupted.pt与18576975B actor仅stat，未加载/单独测时，不当成功CP/恢复证据。

cost-r3.json/md和SRC1201草稿已最终同步失败事实/trace/费用/未知项，标题不再“待更新”，文字笔误修正。8.9.1三文档review/P5 blocked；优化子节点done仍成立。建议仅交Claude决定是否授权保持原256环境与采样/接受/几何规则的一次有界初始化分项诊断及预算，再据其结果决定执行时限分段；不自动延限/缩规模/优化/重试/3M。没有初始reset分项/采样接受计数，0转移不称0接受episode，不把trace检出位置独断为唯一根因。

A本轮三次标准库报告快照rc0共0.1196311293169856s计opt，无新实际验证/训练/采样/加载。最终opt473.1527458531782/1500s、余1026.8472541468218s、active=null；C395.0120486840606/3600s、active={}。源1201完整草稿已交父，未改共享SOURCES/PROGRESS/task8.9或C生产。无本节点后台/提交推送合并；父最终交接，按要求结束，不再复算或运行。
