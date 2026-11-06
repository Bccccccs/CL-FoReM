# task9.11.5 实施记录

2026-11-03，负责人Codex。请求GPT6.1sol/high；实际后端/强度未知（不把推荐当实配）。推荐GPT6.1sol/high、Claude Sonnet5.5/high，原因是跨进程退出与预算因果审查。

授权：只修supervise.py/admission.py并增加专用标准库替身验证；不运行模型/torch/numpy/环境/旧pytest/conftest/smoke/训练/独立任务测试，不修改原活动或STOP，不重启旧run，不重置窗口或预算。父维护共享PROGRESS/SOURCES，独立.6核验。

开工已读根/forem AGENTS、README/PROGRESS、父三文档H/I、.3/.4/.5三文档及父stop-review、STOP JSON。分支codex/task9-lower-improve；既有dirty保留；ps仅命中本次只读命令，无当前task9_11运行。源码版本前副本在before/，旧conftest明确activate并import torch，禁止收集。

方案：dispatch→脱离会话guard→独立watcher，继承同一flock；watcher持有截止/父与guard身份、核容器ID与mount、独立持久退出证据。exec客户端死不能代表worker已死；失败仅精确容器ID停机并核State，不能pkill。worker成功需精确容器内/proc中无worker证据。所有证据失败/未知维持拒绝；双guard同时SIGKILL/主机断电只能保留started拒绝恢复，不能保证全故障有终态。旧prepare路径拟显式拒绝，本轮不恢复。

测试尚未执行；先保存专用脚本AST收集项与全部直接/传递项目导入链，再直跑python3 -B专用unittest；所有运行只临时目录与stdlib替身子进程。失败输出逐次保留。

完成准备：源码与测试冻结SHA见final-implementation-handoff.json、collection-review-v7.json。最终attempt07 rc0、30项、wall5.271597858518362s。before副本与diff保留。01路径映射/fixture失败、02半JSON发布竞态、.6独立quiet→stop尾反例、06测试自清理误杀自身均实际保留；03/04/05旧PASS不冒充最终版本。07后只写本三文档/日志，无生产源码再变。

完整控制调用25s是各5s timeout固定链工程预留，不证明真实fsync/内核调度；owner/guard全退出wall和worker独立exit UNKNOWN。整体NOT_READY，旧STOP与原活动不改。本轮无真实Docker调用，无模型/torch/numpy或环境导入/构造，无smoke/训练/任务test，无后台运行。父归集准备成本，.6独立审查，禁止由本子自签许可。依据将由父登记SRC-1400/1401。
