# task0.11 四项修正的独立代码复核

2026-09-30；负责人：Codex 子Agent `/root/task0_remediation_review`；状态：done（本审核交付完成，不替代父Agent的真实复测与最终task0状态决定）。

目标与授权：只复核task0.10对上次四项问题的闭环；生产实现/数据只读，只写本日志。不运行Docker/ROS或真实仿真，不发真实进程信号、不改共享文件、不提交。已读根AGENTS、forem/AGENTS、doc/README、PROGRESS、ENV、task0.10与task0.11三文档，结合上次独立审核记录核对。共享进度由父Agent登记和维护。

接手HEAD仍为 `438c5f9fc9975e4a32a4ca4942dd3cfc2cc93804`，本轮实现未提交；既有未提交源码/文档与父Agent日志全部保留。实际模型/档位无法从平台核实，未知，未切换。推荐Codex GPT6.1sol medium、Claude Sonnet5.5 medium：核对进程所有权、持久身份和时间窗口的跨模块因果关系。

## 结论

**上次四项具体问题在当前Linux/ROS使用范围内均有针对性修正，代码与安全复现支持关闭；本次未发现这四项范围内需要阻断交付的新问题。** 父Agent仍须独立完成其39项测试、入口回归及新运行核验，不能仅凭本结论把task0置done。本结论不承诺任意外部强杀下所有瞬态后代都可追回，也不外推其他场景控制性能。

|上次问题|修正与准确位置|本Agent核验|结论|
|---|---|---|---|
|P1 失效root裸PID收养外来子树|`scripts/task0_proc.py:232–249` owned_alive只将alive(identity)成功的种子作为扩树起点；`261–284`停止时使用记录的root/supervisor/members；`286–294`发信号前再核验身份。|重放 `tests/test_task0_proc.py:194–216` 的原审核mock，1项OK：失效root100/外来child200场景信号列表为空，rc0。没有调用真实os.kill。|关闭上次确定的stale-root路径。|
|P2 root先退/孤儿遗漏及已有cleanup跳过残留|`task0_proc.py:137–184` Linux child-subreaper监督进程0.1s保存身份，空树连续15次才退出；`269–284`用持久members恢复归属；`307–315`仅重算后确实无成员才幂等返回；`350–355`非空路径记录残留并保留追加cleanup。|内存mock中root已退出，持久child200仍alive：stop向child200发mock SIGINT后rc0、child不存在、residue=[]；有旧cleanup文件时结果相同；无有效supervisor种子、但持久child有效时也可清理。已读真实root先退/supervisor先死/重复stop的9项测试源码，实际执行交父Agent。|在监督器正常运行或成员已经持久化的范围内关闭。|
|P2 高频空/2行/NaN/缺列/不足100triples假通过|`analyze_task0_feedback.py:140–167`完整六关节schema、非空、数值有限、时间递增检查；`99–107`每关节triples>=100及覆盖门槛；`113–137`缺证据与NaN/None不能通过；`186–214`CLI以非零退出报告错误/证据不足。|直接只读加载原task0.9输入：empty→InvalidInput/no data；two→INSUFFICIENT_EVIDENCE/pass=false；nan→InvalidInput/non-finite；few_triples→pairs120/triples60/INSUFFICIENT_EVIDENCE/pass=false。已读10项高频测试源码。|关闭原四种坏输入及缺列路径。|
|P2 整bag稀释运动异常|`evaluate_hf_windows.py:31–44`取summary的requested/motion/settle；`59–67`每段独立analyze+evaluate，任一失败整体失败；`run_task0_smoke.sh:135–142`正式调用该入口并传递失败。|原短时交替场景用真实windows()分段：requested[4.7685,12.7685] RMS7.741e-5/PASS；motion[4.7685,7.7685] RMS1.264e-4/FAIL；settle[8.7685,12.7685] RMS0/PASS。运动异常不再被请求窗口/其他安静样本稀释成整体通过。|关闭；现有真实运行亦确实使用分段输出。|

## 现有运行证据与源码身份核对（只读）

已读以下manifest、launch.json及hf_analysis_windows.json；其中四个关键脚本 `task0_proc.py`、`analyze_task0_feedback.py`、`evaluate_hf_windows.py`、`run_task0_smoke.sh` 的当前SHA256均与每次运行manifest一致，launch元数据subreaper均true：

- `results/task0/task0.10-final-hf-hold/`：manifest final/hf exit=0；requested[5.853,17.853] PASS；最少triples17366；连续步覆盖0.81575。
- `results/task0/task0.10-final-hf-move/`：manifest final/hf exit=0；requested[4.8335,12.8335]、motion[4.8335,7.8335]、settle[8.8335,12.8335]均PASS；对应最少triples11304/4130/5762，覆盖0.804375/0.792333/0.8135。
- `results/task0/task0.10-negctl-quick-hf-move/`：manifest final/hf exit=1；requested/motion/settle全部FAIL，最少triples11493/4462/5590，覆盖0.81225/0.829167/0.79925，失败不是缺证据造成。

这支持代码修正与Claude现有证据身份一致。此处只核读既有事实，不把Claude自测当成父Agent本次独立运行；完整真实复测证据由父Agent维护到task0.11 RESULTS。

## 适用边界与保留限制

1. 进程监督依赖Linux `/proc` 和child-subreaper；当前正式运行meta.subreaper=true，真实回归应继续验证。没有把本实现描述为跨平台进程管理器。
2. task0.10 RESULTS已明确声明：监督进程SIGKILL后，只能追回已持久记录或仍能从有效成员发现的后代；在0.1s记录之前通过极短命父链脱离且监督器又被强杀的后代不在保证范围内。同一PID在同一内核节拍复用也没有形式保证。这些不等于上次“正常root先退出必然丢孤儿”的路径仍未修复；不据此新增本轮阻断项。
3. 停稳段用既有hf残差+交替比例；没有声称它通过保持段的速度RMS/位置峰峰门槛。段划分按发令结束后额外1s开始，边界是代码与文档公开声明的选择。
4. 高频新增50%连续步覆盖门槛已在task0.10 RESULTS声明；原速度/位置高频门槛与100triples门槛没有放宽。HF不承诺完整2000Hz记录。
5. 原quick→world结果仅支持同固定底座UR5场景交替消除，不证明ODE内部迭代故障机理或其他姿态/负载/场景的精度与计算性能。task1未实施。

## 实际执行与交接

本Agent实际执行只读cat/nl/rg/git、Python内存数据调用与1项mock测试，命令退出码均0。Python设置PYTHONDONTWRITEBYTECODE=1；无新缓存、CSV、测试脚本、进程或Docker调用。mock替换load_json/alive/descendants/os.kill/write_json_atomic/next_cleanup_path/os.path.exists，信号与文件写入只落在内存列表；不存在真实进程信号。生产实现未改，唯一新增文件为本日志。

下一步由父Agent汇总独立真实测试/新run-id验收，核对无本轮残留，再决定task0/task0.10状态。模型与强度推荐及实际未知已在上文区分。无需本Agent进一步扩展任务或启动后续研究。
