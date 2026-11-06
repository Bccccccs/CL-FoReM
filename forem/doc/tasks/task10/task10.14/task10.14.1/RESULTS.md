# task10.14.1 独立复算结果与交接

状态 done，2026-11-03独立交付完成，父已直接核对全部原件并接受本子任务；总体task10.14保持review交决策者最终审核。负责人 Codex 子Agent，未启动任何GPU/真实环境；全部审计命令显式 `CUDA_VISIBLE_DEVICES=''`，仅CPU读取父唯一run `t10-eval-20261103-s101`。实际Agent具体模型/推理强度未知；推荐GPT6.1sol/medium、Sonnet5.5/medium，原因是加载、配对和统计需跨模块核对。父执行者唯一启动评估并负责共享PROGRESS/SOURCES；本子任务无运行进程。[实际原件与复算来源](../../../../SOURCES.md#src-t10-028)。

## 工程核查

最终 `independent-audit-v2.json` 为 **verified_complete，issues=[]，rc0**。独立读取manifest、36份episode、123份raw决策及对应JSON、36份raw初态、entry-check、weights、budget；不读取aggregate summary作为统计输入。36个唯一预期身份全完成，12组物理/路线/栅格时间/观测/候选/mask/几何/seed完全配对；初态还与首决策raw输入独立对应。119冻结文件哈希一致、完整127张量initial/final源模型哈希与B3原policy一致，eval/no_grad和VCM/RNG门证据齐。123写前预留/123完成/0在途/0更新，36完成/0缺失，全部触发标志与复位前终态、失败尝试计数可复算。[实际原件与复算来源](../../../../SOURCES.md#src-t10-028)。

父唯一运行outer wall3311.918092s、worker账本3310.928055s，均在原5400s窗内；旧输入GPU入口10.668243s包含在其中。子终态CPU审计v2 11.146881s、诊断6.250057s，不增加GPU工作。实际原workertorch2.7.1+cu128、CUDA12.8、numpy1.23.5、逻辑CUDA0/物理GPU1；父真实退出rc0。[实际原件与复算来源](../../../../SOURCES.md#src-t10-028)。

预审发现父DecisionStep字段和根grid快照两处必发异常，父已在GPU前修复并补CPU夹具；全程没有真实评估重跑。独立v1审计首次rc1仅因审计脚本误把raw `map_ids` tuple与list直接比较，误报123条内容相同的身份；该初次结果/日志保留。父批准另建v2，仅一行改为 `list(fields.get('map_ids', ()))` 后精确核内容，3个新增CPU夹具覆盖正确tuple/list及错误地图。v1原脚本和冻结清单均未修改，实际评估结果未变。[实际原件与复算来源](../../../../SOURCES.md#src-t10-028)。

## 三策略结果

|策略|完整/预期|严格成功|缺失|sparse|standard|真实决策|尝试时长s|回合wall合计s|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|trained|12/12|0/12|0|0/6|0/6|52|52.749995|1264.789200|
|initial|12/12|0/12|0|0/6|0/6|52|52.749995|1261.995311|
|uniform|12/12|10/12|0|5/6|5/6|19|208.250335|772.057052|

trained对initial胜/负/平/缺失为0/0/12/0，对uniform为0/10/2/0。每个分母保持预登记固定口径；本次无缺失。回合wall含复位/推演/执行等，三组之和之外还存在GPU入口与最终汇总开销；失败早停的尝试时长不能当性能收益。[实际原件与复算来源](../../../../SOURCES.md#src-t10-028)。

|场景|trained与initial（完全相同）|决策|最终路线比例|uniform|决策|
|---|---|---:|---:|---|---:|
|sparse_validation_00004|failure_limit / self_collision20|2|0.073839|failure_limit / base_collision20|2|
|standard_validation_00000|stall_limit / 零尝试停滞|6|0.043704|failure_limit / ik_rejected20|2|
|sparse_validation_00005|failure_limit / self_collision20|1|0.072553|strict_success|2|
|standard_validation_00001|failure_limit / self_collision20|2|0.072468|strict_success|2|
|sparse_validation_00006|failure_limit / self_collision20|1|0.070667|strict_success|2|
|standard_validation_00002|stall_limit / 零尝试停滞|7|0.269317|strict_success|1|
|sparse_validation_00007|failure_limit / self_collision20|1|0.072060|strict_success|2|
|standard_validation_00003|stall_limit / 零尝试停滞|6|0.220607|strict_success|1|
|sparse_validation_00008|stall_limit / 零尝试停滞|6|0.261008|strict_success|1|
|standard_validation_00004|stall_limit / 零尝试停滞|6|0.190085|strict_success|1|
|sparse_validation_00009|stall_limit / 零尝试停滞|8|0.115803|strict_success|2|
|standard_validation_00005|stall_limit / 零尝试停滞|6|0.261008|strict_success|1|

逐场景的失败类型、累计失败、决策、尝试时长、wall、选择序列与路线原值完整保存在 `independent-diagnostics.json.scenes` 与 `independent-audit-v2.json.episode_details`。上表引用同一原件，未混旧4图或训练成功率。[实际原件与复算来源](../../../../SOURCES.md#src-t10-028)。

## 选点与失败解释

trained与initial **各52/52次选择slot12原地候选，所有52个边界均有其他有效候选**（平均8.403846个），12/12场景完整选择序列相同；同状态前缀52次logits全部变化，最大绝对变化1.235067，但最大值排序未改变选择。共享raw模型输入无错配，未在分岔后的不同状态直接比较logits。两组各5回合触发failure_limit、原attempts中100次失败全部self_collision；各7回合触发stall_limit。另直接从JSON按 `r_t.attempted_substeps==[0]` 计得两组各35/52次决策没有实际下层尝试，对应7×5次原地停滞；不能将停滞称为IK失败。uniform0/19零尝试、从未选slot12，两失败分别为20次base_collision和20次ik_rejected，其余10回合严格成功。[实际原件与复算来源](../../../../SOURCES.md#src-t10-028)。

平均最终路线比例trained/initial同为0.14359315，uniform0.92640833。既有训练曲线每50更新critic loss均值0.2034121→0.1593865→0.1564493→0.1473248，actor loss均值-1.0459400→-1.1139889→-1.1289483→-1.1365148；update1在真实1008决策、update200在1200决策。loss和权重变化只证明学习数值改变，本轮没有观察到实际选点或严格成功改善。[实际原件与复算来源](../../../../SOURCES.md#src-t10-028)。

**独立判断：**工程原件/配对/统计审计通过；这12个场景不支持200更新改善选点，trained在本清单与initial行为完全相同、低于uniform。优先基于现有raw回放排查原地候选持续占最大值及其反馈/有效梯度/排序变化，再由决策者评估新增训练预算；本轮未定位唯一根因，也不能证明更多训练无效或跨种子结论。没有修改策略、参数或奖励，没有追加训练、test池或task11。[实际原件与复算来源](../../../../SOURCES.md#src-t10-028)。

## 复算与原件

工作区HEAD `91f538cf2ee10bebffd6b643d5c908fa0d419ced` 加未提交独立评估实现；manifest逐文件hash为真实代码版本。脚本hash：v1审计 `d20989ff7e7d22e5ee8fbfd22efdec6120e26dcf98825e2bf33c73cfbbf0edce`（保持冻结）；v2 `25099fb719e2a156ecc661417c863886def7a1362a46349ebbcb5e89d115eaf3`；诊断 `6d6d498ab33d5bbab2f186c7689de568d86151da53cda910e1a15a46587c4a63`。CPU必要夹具：v1统计/raw13 passed、诊断4 passed、tuple修正3 passed，均rc0；失败历史完整保留。[实际原件与复算来源](../../../../SOURCES.md#src-t10-028)。

```bash
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 /workspace/scripts/task10_validation_audit_v2.py --run /workspace/results/task10/t10-eval-20261103-s101 --reference /reference/source --output /workspace/results/task10/t10-eval-20261103-s101/independent-audit-v2.json'
sg docker -c 'docker exec --user 1004:1004 -e CUDA_VISIBLE_DEVICES= -e PYTHONPATH=/workspace/src forem-task10-runtime python3 /workspace/scripts/task10_validation_diagnostics.py --run /workspace/results/task10/t10-eval-20261103-s101 --output /workspace/results/task10/t10-eval-20261103-s101/independent-diagnostics.json'
```

以上命令已执行，首行rc0/11.146881s，第二行rc0/6.250057s；完整命令、原始rc、成本与日志路径在[独立日志目录](../../../../agent_logs/task10/task10.14/task10.14.1/) 的audit-command.json、audit-v2-command.json、diagnostics-command.json；日志为 `forem/logs/task10/t10-eval-20261103-s101-independent-{audit,audit-v2,diagnostics}.log`。复算如需保留现有报告应改用另一个输出文件名，不覆盖已交付原件。

产物SHA：初次v1误报 `f7e22356fca837a0dd173dab35ca7388ae792482cd1d35c3614c87551cdbc3ab`；最终v2 `9c202b4edc7446db99931b4d3fa7e720617bfaf171bf5fddd895fe6dfe0857cd`；诊断 `0024604ffbf7f3e08e7f89d14244970230894b9d90010b1e5b2d6594aeea488d`。父独立复核后统一交决策者；余项仅最终审核与后续排错/预算决定，无运行中任务。[实际原件与复算来源](../../../../SOURCES.md#src-t10-028)。
