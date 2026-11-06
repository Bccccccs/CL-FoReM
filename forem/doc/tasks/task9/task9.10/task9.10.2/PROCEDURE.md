# task9.10.2 协议及独立验收 PROCEDURE

递归规则：本层恰有TASK/PROCEDURE/RESULTS；本轮不再委派。如需再拆分，先建立下级三文档并由父核准。审查只写本任务与独立日志，全局由父维护。协议及阈值全部沿[父流程](../PROCEDURE.md)、[SRC-1382](../../../../SOURCES.md#src-1382)，执行授权沿[SRC-1383](../../../../SOURCES.md#src-1383)。

1. 开工读取AGENTS、README、PROGRESS、父与本子三文档、execution-window、9.8/9.9证据；核Git分支/dirty范围与相关进程，不覆盖他人。
2. 启动前逐项检查：完整case六字段、冻结模型/代码/批次；首pending&failed同段锁定，仅下一真实动作一次替换；不得跨段补抽；独立CPU Generator的JSON/SHA256/种子/epsilon；原批前向动作与采样参数一致；所有环境/候选及全局RNG未被新抽样消费。
3. 前缀比较包含首次拒绝、到下一动作输入边界；替换action_start仅排除raw_action，其segment/action/state/target仍须精确相同，另核mean_action等于C原raw。批内其它干预造成的目标前缀变化亦不得忽略。新增success/stalls钩子保留Core._finish原局部布尔与计数，基础comparison投影须兼容原coverage。
4. 每侧独立coverage核reset、完整case键、begin、动作连续号、真实pending子步、attempted/committed、终态及evaluate原row，不能靠两侧相等放过共同缺失。C/B基础共同字段精确比较；新增detail不要求旧数据有。全部C复算R1/N11才准T。
5. 执行后只读原JSONL自行遍历，以首pending&failed提交状态锁段；平移rho为XY欧氏距离，原地为max(cap-s,0)，float64、米，严格减少>1e-6或同段arrived为R。保留N/U/不可干预/动作未变，固定12分母，列获得/丢失R，不以commit或s进度代替rho恢复。单列原success、strict_success、拒绝/commit与最终进度。
6. 读取原episodes-started、status、容器inspect、计时/设备/文件清单核1176/4h/2GiB及停机，最终统计与实施者派生表交叉核对。原件哈希/代码快照及独立统计随记录给父，异常立刻发父与实施者，不自行修数据或重跑。

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为因果边界与跨文件完整性审查；本轮请求gpt-6.1-sol/high，实际后端模型/强度未知。
