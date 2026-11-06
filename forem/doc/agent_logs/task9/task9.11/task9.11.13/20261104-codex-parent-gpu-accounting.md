# SRC-1417 P1 父实施协调与核验

开始2026-11-04T09:23:00.481592+08:00；负责人Codex，父实际模型/强度未知。实施.13与独审.14工具请求均gpt-6.1-sol/high，实际后端不可另行核实；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high用于设备区间和两账准入因果审查。授权与复算来源SRC-1419。

范围：本轮只修P1计费必要实现、专用stdlib替身、独立审查和文档。旧STOP/FAIL/UNKNOWN只读，58h/2TiB、原T0和11-06 03:18:20+08截止不重置，不改变B1/B1-L科学，不签真实许可。未调用真实Docker/GPU或加载模型/科学环境。

开工已读根/forem AGENTS、README、PROGRESS、task9.11父§16、.11/.12三文档、cross-stage-review和verification、ENV。分支codex/task9-lower-improve，HEAD d198e5ca48f86071c05274f9da753f393ce058b4，大量既有dirty/untracked保留。168源before逐项与旧c8523c…11ef177冻结一致；旧878保护及101联合归档核SHA一致。进程只读检查未见task9 worker，不触碰其他进程。原始保护见parent-initial-protection.json。

先复算后委派：parent-old-counterexample-command.json记录精确argv/cwd/raw/rc0/wall；双快照133→254.044678213 worker、143→233.078001564 GPU，GPU差.078001564+3×30。完整源JSON/path/SHA见old-counterexample-recalculation.json，逐控制源路径/操作/charged_s见parent-old-counterexample.stdout.txt。全部为替身值，非真实卡时和生产参数。

2026-11-04T09:28:08.645134+08:00 进展：已建立.13/.14恰三文档及写入边界再派工；父共享文档和parent-*日志独占，.13仅生产必要变更/自文档，.14仅自己审查脚本/文档。父双向追踪见parent-path-trace.md。发现supervise把cap+CPUcontrol作GPU新申请，要求必要显式GPUcap区分；发现初版GPU证据强制整个worker范围持卡，要求支持完整声明的部分/离散分配区间，容器完整持卡仍全额保守计。当前新代码尚未冻结，未将开发通过当验收。

parent-budget-start-command.json rc0，只读继承原账并纳新实际命令，下界及UNKNOWN保持，准备/审核完整会话/发布尾未闭合，真实余额不能声称精确。新freeze后父跑同SHA116相关回归，.14独立自算联合与边界，父再核原件/哈希。后续命令全部parent_run_evidence.py收raw/rc/wall/source before-after，失败保留。

2026-11-04T09:36:19.982020+08:00 v1 db02314ef8bb6e92e31755db9ece7a7db1d0b328d56df60111ec2d9f91175b7a冻结，父128项rc0、全部before/after同SHA；独审新增container-tamper-v1反例rc1，已审container start改晚5s仍准入并降低GPU5s。原失败保留，同范围必要修复回派.13；v1所有通过仅历史，不作最终验收。新SHA稳定后重跑全部相关项及原反例。来源待SRC-1420/1421统一登记。

v2 c53aa986…/170源父131项rc0，独审对容器start/stop/delete/device历史篡改与旧F1/F2等同源通过；但独立first-identity-v2反例发现首次review record/current均A、sealed inspect为B仍接受，必须补三者身份一致，原FAIL保留。v2通过不能移作v3验收。staticlegacy无独立时序basis严格UNKNOWN，旧5s正例收紧为拒绝；已审动态5s正例保原保守曝光。

边界公式核查澄清：父初疑afterGPU+110误加，但该近截止fixture容器自原T0持卡，继承110完全被容器覆盖；修后union只计一次，旧式container_duration+inherited110+external_worker确实多收110。已由独立raw边界复算验证，不改通过公式、不把父误读写成实现失败。

授权、实现、独审及实际预算来源：[SRC-1419](../../../../SOURCES.md#src-1419) · [SRC-1420](../../../../SOURCES.md#src-1420) · [SRC-1421](../../../../SOURCES.md#src-1421) · [SRC-1422](../../../../SOURCES.md#src-1422)。

2026-11-04T09:51:50.948895+08:00 父最终接收：最终170源0bbda355…7476c1a9与冻结副本相同；父132/独立54同源rc0；5689引用、878旧保护/59父/158旧裁决/101归档/688输出stat核真。对账和真实预算见父RESULTS §17与parent-budget-handoff.stdout.txt；独审正式SHA0c59ce7b…4c1e4856。未执行真实任务，实际会话成本和退出尾UNKNOWN，不签真实许可。

最终末检2026-11-04T09:53:14.898777+08:00：parent-final-integrity-v2 rc0；原轮rc1为检查器切半链接输入问题，原件/成本保留，修checker后99完整本地链接全部通过。源码170/独审5689及全部原件保护再核真，fixture进程空。日历余41.418084h，known worker下界至少4892.218635438s，完整/尾UNKNOWN；真实NOT_READY，不签release。父RESULTS§17及SOURCE1422已补此交接时点。本轮无后续真实任务或等待中的worker。
