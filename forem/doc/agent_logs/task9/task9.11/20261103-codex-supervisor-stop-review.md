# task9.11 监督审核
2026-11-03 20:13 +08开始，Codex，实际模型/强度未知。用户要求审核，本轮仅只读代码/JSON/进程与文档。已读当前规划、.3执行与.4独立STOP，未运行模型或环境。推荐GPT6.1sol/high、Sonnet5.5/high，因需跨层监督与实验合同审查。

裁决保持FAIL_INCOMPLETE_SUPERVISION / STOP。四smoke完成4000消费、300updates和784 OFF，另C4718 ON196；主3M训练与独立test均未开始。父直接比较OFF/ON parity全部相同，196回合原有字段及分域聚合完全相同，STOP签字引用7个证据文件hash均匹配；当前docker inspect为exited/Pid0，GPU计算仅task10。未重复解码522快照，以已签独立审查及hash为证据，披露范围。

初次父比较整个row对象失败，因为ON新增诊断字段；随后核原有字段全集及聚合通过，不是运行差异。保留本核查过程。

P1 supervise.dispatch第95–109行：host监督终端记录仅在正常走完wait后写，dispatch无finally或SIGTERM处理；子进程使用start_new_session。host中断会留下started，而子进程可能继续落inner结果。本次host记录确实缺exit/wall。代码支持该中断窗口，未知外部为何退出，不能宣称已定位为工具超时。正式长训前需持久监督与独立退出落盘/预算守卫，模拟监督中断和子进程完成先后竞争做零环境验证。SIGKILL无法靠finally保证，应让退出证据由仍存活的外部监督独立持久化；不伪造历史exit0。

当前停止正确。科学原件支持C4718 smoke记录器非干扰，不能据此判B1-L收益或放行正式训练。规划仍可作为学习率假设试验，尚无已证训练根因。修复、重新冻结及续跑合同应另派，当前不更改源码/运行预算/签字或重启旧run。
