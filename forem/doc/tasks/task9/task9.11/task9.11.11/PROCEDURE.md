# task9.11.11 · 流程

负责人Codex，请求GPT6.1sol/high，实际后端/强度UNKNOWN；兼容推荐Sonnet5.5/high，因跨阶段时间/身份/账本一致性。范围：四必要core admission/continuation/supervise/prepare、必要stdlib新module与专用测试；旧科学/worker/audit只读；只写自身三文档/日志。授权/冻结合同见[父日志](../../../../agent_logs/task9/task9.11/20261103-codex-cross-stage-repair.md)、SRC-1412；禁止真实实验/旧run恢复/旧证据改写/科学或预算截止改变，不签真实许可。

递归规则：本层恰有TASK/PROCEDURE/RESULTS，不再委派；父.11联合实现稳定后.12独立审查，父核原始证据和SHA，不以自报代通过。先读AGENTS、PROGRESS、父/.9/.10三文档、integration-review/verification、SRC1408–1412及冻结合同，保存before，按用户完整矩阵实现/测试；同一最终artifact必要回归+独审，失败全部保留。

## 已实现接口与复核顺序

1. 首prepare前固定candidate科学/路径身份；需要动态追加成本时显式冻结`dynamic_cost_policy=costs.make_policy(p)`。synthetic时钟也必须在prepare前绑定`clock.initialize`返回anchor与root。legacy静态库存不自动迁移。
2. 生产prepare冻结精确原科学四配置与输入；独立预算角色`task9.11.12-cost-reviewer`读全roots/source/event/journal、原继承账和生产resource核算后发布version/previous-hash snapshot。角色不同于原静态release reviewer `.10`，真实candidate仍false-execution。
3. release绑定`budget_snapshot=costs.current_ref(p)`；dispatch原reservation临界区和guard最后真实worker.Popen临界区与cost writer/reviewer共用cost.lock。原worker.main再次load/release/prereq/resource/ledger。
4. outer actualwait记录completion_capture，CLOSED引用其SHA；历史读原reservation capture/原release和snapshot前序，不按当下expiry重签。显撤阻资格，原闭账费保留。
5. 新费用先`costs.measured_command`真实有界wait测wall，再`append_event`提交唯一event/source及journal，未审即stale；独立review发布新snapshot，下一新release绑定该snapshot。nested同run/stage且区间包含，最外层唯一计费。未知wall、未闭command、丢失/篡改/extra/并发不完整均拒绝。
6. 标准库专用入口`python3 -B forem/src/task9_lr/tests/test_cross_stage_stdlib.py`。父统一freeze后跑必要旧标准库回归并交.12独立自建反例；所有命令通过run_evidence.py保存raw/source-before-after/rc/wall。任一源码修改须重新统一freeze，不拼不同SHA的PASS。

三文档递归规则与模型推荐沿本流程开头；本轮不再委派、不运行科学/GPU测试。实际版本、原始失败与限制见RESULTS，方法均为授权工程候选，无真实执行release。

v2控制口径补充：source发布、event追加、snapshot审核/发布各独立预留并全额计既有候选控制包络，actualwait payload另列；immutable control reservation/journal→artifact SHA→completion receipt、pending/rejected与包络尾核查；当前snapshot计入自身reviewcontrol，不留下一版。所有控制费用工程候选applied:false；普通校验拒绝可封denial保费，写盘/commit后未知保持拒绝。新费用后guard最后actual worker launch锁区仍重验，成本锁等待按原deadline/save reserve轮询终止；不能等待他进程释放才发现到期。35项入口与不改的独审原反例同断言复跑、版本和原件以RESULTS末节为准，父统一freeze后独审。

## 父最终接收

.11实现→v2冻结→.12独立→父直接核验已完成，真实NOT_READY。最新稳定源码、精确五条回归命令、费用边界/角色/续行顺序与剩余决定见[RESULTS末节](RESULTS.md)、[父PROCEDURE N](../PROCEDURE.md#n-f1f2最终生产调用与续行边界)。此前v1流程及失败保留；修改实现将使相关旧PASS失效，须重新冻结同版本核验。
