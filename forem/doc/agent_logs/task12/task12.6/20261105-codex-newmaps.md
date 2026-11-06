# task12.6 新地图验证执行记录

2026-11-05T15:35:21.912008+08:00 · active · Codex父执行者。实际模型/强度：平台未提供可核实型号/强度，未知；推荐GPT6.1sol/medium、Sonnet5.5/medium，用于地图身份、同支持排序及统计；复杂教师语义核查可high。用户授权自主选模/先建档委派，父统一版本/资源与最终交接。

授权：固定r6/model-weights.pt、task12-utility-v1、旧0.5m+1.5m、既定几何，32新train图(sparse16/standard16)，seed1206/126000+i，最多768移动标签，0更新。正式test池保留；无原地/规则新增教师调用。保留全部既有修改。已读根/forem AGENTS、README、PROGRESS、ENV、12.6三文档、SRC-T12-019/020及既有worker/标签代码。

计划文件：新增scripts/task12_newmaps{,_stats,_launch,_tests}.py；本节点三文档、独立日志、PROGRESS、SOURCES追加。原教师r1 frozen-source、r3 worker恢复逻辑、r6模型/解码均复用只读证据。启动前冻结排除清单/manifest；持久launcher有限运行后自动汇总写文档，启动核实后退出主动监督。预计教师约2–3h，依据SRC-T12-010/020；实际合理调整、分项计时并保留失败原件。停止仅本run STOP，恢复跳过完成记录。

资源现场：2026-11-05约15:34+08，GPU0 PID1870826活动，GPU1 task10 PID970022活动约75GiB；GPU2/3无计算任务。根HEAD121cb36e64e53163be232dbafa8c32ff065a290b，分支codex/task9-sac-opt-20261031；大量已有未提交修改不覆盖。尚未启动制数。

2026-11-05T15:44:49.692831+08:00 完成清单冻结和新入口定向核查。新增freeze/worker/stats/launcher/tests五脚本（均仅task12.6范围）；地图排除最终33，首轮误扫描frozen-source中全池manifest导致选不到16、退出1，用时8.87s，未冻结plan/未制数；修正目录范围后1.44s成功，未按标签换图。原native boxes和排序几何hash同时保留，16+16身份与seed独立复算通过。

任务12.6.1 Codex子Agent独占统计模块与节点记录，父核代码/schema/构造用例后接受（子模块工程done，实验结果待运行）。统计0推演/0更新；参考子RESULTS。CPU实际新utility提取复用r3 state00/grid0 12终态，等于r6已验收标签。最终targeted-tests all_pass/rc0；源码freeze前后版本保留，第二轮改动只细分source_read/decode_h2d/reconstruction计时，已重新定向核查。

实际命令：`python3 forem/scripts/task12_newmaps_freeze.py --run forem/results/task12/t12-newmaps-20261105-r7`；`python3 forem/scripts/task12_newmaps_launch.py freeze-code --run forem/results/task12/t12-newmaps-20261105-r7`；CPU测试通过sg docker -c docker run（mm_husky:node01、user1004、CPU10-11、CUDA空、/workspace及/original只读、/run可写），执行`/opt/python310/bin/python3 -u /run/code/task12_newmaps_tests.py --run /run`，rc0。命令argv将存validation-command.json，stdout的所有断言结果已保存targeted-tests.json。初次准备与核验累计墙钟不计训练预算，最终运行工程成本另记driver/attempts。

2026-11-05T15:46:47.941414+08:00 持久启动验收通过并退出主动监督。driver1892068/PPID1/独立SID，hostworker1892130（容器PID1），GPU2实际UUID/device验证通过，GPU0/1原PID运行。32prepared均ready，inputs-frozen在教师前落盘；首grid-0 utility实际保存{'records': 12, 'known': 12, 'candidate_ids': ['candidate-00', 'candidate-03', 'candidate-06', 'candidate-09', 'candidate-12', 'candidate-15', 'candidate-18', 'candidate-21', 'candidate-24', 'candidate-27', 'candidate-30', 'candidate-33']}，当前state-01/grid-0，无worker-error。startup-verification.json保存证据。观察到current.map_id在教师阶段保留末张获取图：只展示字段残留，实际source.spec、state_id/plan映射和标签身份正确，文档明确以state_id关联，未编辑运行快照或打断有效任务。

后续由冻结code/task12_newmaps_launch.py持久等待worker，正常/异常均写attempts/driver退出状态并尝试finalize；标准库统计和自动追加共享文档使用task12 append锁。自动收尾失败时finalization-error.json保留，人工同run finalize可重入（标记防重复）。0新训练，不扩大任务。活动监督结束后只由有限launcher继续；最终结论交当前决策者。

2026-11-05T16:14:54.294261+08:00 持久进度：已写状态7/32，本次1804.3s；工程预计14400s，当前阶段current.json，更新0。

2026-11-05T16:44:58.744358+08:00 持久进度：已写状态15/32，本次3608.8s；工程预计14400s，当前阶段current.json，更新0。

2026-11-05T17:15:02.493622+08:00 持久进度：已写状态24/32，本次5412.5s；工程预计14400s，当前阶段current.json，更新0。

2026-11-05T17:43:29.955283+08:00 自动收尾：review，完整32/32，rc0，本次7119.833s。可正扇区中网络选正96/107、最近点74/107，网络相对最近净+22点。 整体命中网络17/32、最近点18/32，净-1状态；配对{'gain': 2, 'loss': 3, 'both': 15, 'neither': 12, 'net_hit_states': -1}。 存在11个有可选正点却选负的扇区；最大负−正分差0.0997697、logit差0.509672（state-03/扇区9）。分差为排序现象，未定义校准概率或显著性阈值。 优先处理泛化问题：点级/状态级未同时形成明确净收益；保留本轮固定合同结果，数据多样性、目标与局部几何特征的后续方案另行登记/审核。 原件handoff.json及RESULTS/SOURCES/PROGRESS已更新，0更新，未进入后续实验。

<!-- task12-newmaps-final-t12-newmaps-20261105-r7-1 -->
