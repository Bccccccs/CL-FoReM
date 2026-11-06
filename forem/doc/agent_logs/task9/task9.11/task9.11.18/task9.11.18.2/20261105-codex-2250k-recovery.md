# 2250k原生完整状态恢复独审

2026-11-05T10:21:40.593614+08:00 · Codex · active（后台恢复，最终科学验收待完成）

目标/授权：用户要求修复退出并保持既有训练进度，沿当前AGENTS budget-review必要恢复；仅外部监控/恢复适配，native b8f3/protocol/checkpoint原字节保持。推荐GPT6.1sol medium、Sonnet5.5 medium（跨进程恢复/文件竞争），实际未知。父维护共享PROGRESS/SOURCES；此节点只写独立证据与结果。

已核：checkpoint-2250000.pt34320968995B，完整引用SHA03a0bf80082c88768838ef4f91f5dd41593ef4cc52a7bddf4d6391a9d1806c88；ZIP索引68537项正常。原safe_to_resume=True，journal最后8794action_calls/env2250192与meta对应，2250k consumed/pending192有完整覆盖。8个250k..2M周期各196完整，共own1568，2250k没有writeahead jobs且diagnostics仅0B events。恢复只补2250/2500/2750/3000四周期784，C完成own2352/global3724，既有数据不重跑。实际loader须原train内部一次成功验证2250000/up224975/env2250192/pending192/validation_pending2250k/config相同/真实CUDA再继续，未以actor代full。

旧native remaining原attempt FAIL/outerexit1保留，actualouter22789.560684s/owner22766.805205s/GPUallocation22843.423784s。新cap14400/save1800/active12600/control120，lease14640；5%等机械旧forecast不作为门，当前750k非周期3906.622953+4*评估1535.605937+4*save346.029552=11433.164910s，实际restore成本未知但active余1166.835s；全余3完整B1+final+2h控制恢复工程139386s=38.718h，对原deadline仍有约2h余量，不是硬保证。预算budget-review-v2、paid-storage-v1和旧failed/composite原件均在recovery-2250-v1。

仅三个原资源reader遇ENOENT重扫整轮最多3次，其他异常/40GiB等预算保持；sitecustomize失败exit78、三函数marker和每PID安装argv/env/SHA必要证明；复用实施三针对性rename/7B完整计费/权限异常/预算超额仍拒验证。外部恢复观察器只读原loader返回同对象不改学习/RNG。aggregate review-recovery单fixturePASS，明确attempts=[oldFAIL,newPASS]不重写oldFAIL，3M299975/12完整周期2352后才发原remaining聚合PASS；实际native m.prerequisites下一L前序验证通过。

签字竞态另留：v2签后recover7aac→f956日志写前收费修正，父已启动control旧字节，containerworker读取新字节failclosed，0transfer/0eval/无restore。actualGPU18.686824137s、工程outer24.618894577s嵌套不相加，CID已停，新增STOP已原样归档，空2250diagnostics亦归档attempt1。不覆写v1/v2或attempt1。最终resume-authorization-v3.json SHA4241c0fb41b6168608e33ae7f79238dd7647dcd270e4de9f7169a2a3837cb566使用attempt2，pin最终f956、bridge两源码、driver8288和reviewer5095；completion self路径v3及driver --resume/bridge已接。GPU微额计入预算与compositeallocation，无科学额度重置。

后续：父只确认原loader恢复/新2250评估开始与安装证据即可退LLM监督；恢复结束controller自动调用独审aggregate并后台恢复driver顺序继续L/C/L，final仍NEEDS_FINAL_SCIENTIFIC_ACCEPTANCE。正常不需再全量审/hash或G1/LON。停止/恢复：使用attempt2/STOP或父记录的controller SIGTERM；不可停不明GPU进程；查看attempt2/status.json、restore.json、worker.txt、io-bridge-v1每PID记录。


2026-11-05T10:23:06.439911+08:00 · 2250k恢复已真实启动，后台active（不代表3M/final完成）。父现场确认attempt2/restore.json PASS_NATIVE_FULL_RESTORE，原生一次load64.117379s：steps2250000/up224975/env2250192/pending192/validation_pending2250k/config原冻结；network/replay/optimizer moments CUDA0，原CPU optimizer step保持。待评2250k已实际开始，新writeahead16/own1584，events约1.4MB持续增长；旧8周期1568没有重跑、没有回退250k。后台hostworker1760315、control1760146、PPID1独立runner1760145，GPUe2eab186…d587。

最终授权recovery-2250-v1/resume-authorization-v3.json（4241c0fb…cb566），attempt2目录与restore/worker.txt/bridge每PID安装日志可核；14400含save1800/control120，lease14640。自动完成后仅外部review-recovery聚合oldFAIL22789.560684与newPASS实际，2352/3M299975/12周期符合才签原remaining综合PASS并driver --resume继续L；旧attempt/FAIL、pre-model0科学失败与18.686824sGPU费用保留。模型源b8f3/protocol/checkpoint原字节不改，作用仅已授权3reader bounded ENOENT重扫及readonly loader结果观测；最终B–E/final仍待独立科学验收。父按用户原意交接后退出主动监督，无新增人工轮询。

范围/负责人：本子继续保最终结论职责，日常由已签独立外部validator/issuer与driver执行；三文档递归规则不变，无新增下层任务。推荐GPT6.1sol medium、Sonnet5.5 medium（恢复因果核对），实际模型/强度未知。
