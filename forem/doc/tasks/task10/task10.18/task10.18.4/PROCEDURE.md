# task10.18.4 流程

递归规则：实际子节点先建三文档，父登记输入/独占范围/依赖及验收。独占本子文档/日志、scripts/task10_first_action_probe.py、results/task10/t10-diagnosis-20261106/first-action及logs/task10/t10-first-action-20261106/；不改旧原件/生产入口。冻结plan后再启动。

1. 复用task10_long_validation的真实环境/下层/初态/hash/结果记录函数，加载小10k actor.pt（不需完整boundary）。GPU1空闲才用，不碰GPU0/3任务；核容器现有挂载。沿batch1、seed101、原primitive地图/确定B3/动作与失败时钟/候选预测配置，按旧manifest唯一map identity重建。新入口CPU检查限定强制仅首步、合法槽及后续argmax；已有环境执行验证直接引用。
2. A正常10k argmax；B第一步强制9，其余同模型argmax。各回合从新同初态重置记忆；保存每步观测、候选、logits、Q、选中项、实际执行结果、回报与时长。先验证initial_snapshot所有typed hash与旧10k评估相等，不匹配不执行；B与A初态再次比较。最终严格成功按native Core，不能以到达路线替代。
3. A核对旧10k episode记录的选点序列、终态成功/失败/路线、数值按已有容差说明；若路径偏离保存差异且停止B，不能作因果结论。若A复现，B完整结束后报告两臂真实结果、Q估计与实际回报；只解释该固定状态下第一步干预，不能据两轨迹调正式策略、证明泛化或把slot9硬编码入部署。
4. 工程预估参考旧10k评估1328.1s/12回合约110.7s/回合但加载/重建等非线性，初排20min工程余量可据实际调整，非训练硬截止。最多2回合/300真实决策/0更新；沿每回合150决策与200s尝试时长原生任务限制。失败不得盲重跑，保存错误。预算/状态/退出码实时落盘。
5. 持久launch/worker/run日志独立，python3 -u；STOP安全边界，任务中断保留partial，不伪称精确恢复。主任务不依赖聊天在线；先由父核启动与首条有效记录，然后退出主动监督，结束自动写RESULTS/来源/进度或明确failed/partial交接。实际结果尚待执行，禁止提前声称首步是根因。

负责人Codex子Agent，计划Terra/high；推荐GPT6.1sol/high、Sonnet5.5/high，因为初态/执行路径同条件及因果限制需核查。执行者可自主选模/建档委派，父统一资源与验收。
