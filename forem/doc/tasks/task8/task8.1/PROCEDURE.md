# task8.1 — 执行流程

状态：**done（2026-10-26第一阶段8.1范围父及独立Sol复核通过；27 tests，非整环境验收）**。实际实现gpt-6.1-sol/medium，固定导出gpt-6-luna/low，独立审查gpt-6.1-sol/medium；[证据SRC-0991](../../../SOURCES.md#src-0991)。推荐仍按下文GPT6.1sol/Claude Sonnet5.5对应强度；历史规划与过程保留。

范围依据[用户SRC-0984](../../../SOURCES.md#src-0984)、[代码SRC-0985](../../../SOURCES.md#src-0985)、[资产SRC-0986](../../../SOURCES.md#src-0986)、[工程规划SRC-0987](../../../SOURCES.md#src-0987)。本子任务全部参数与方法选择属父TASK继承或SRC-0987工程选择，未实测；新主张须父同步登记。父合同见[task8 TASK](../TASK.md)、[共享接口](../PROCEDURE.md#interfaces)。

## 递归规则

本层恰有TASK/PROCEDURE/RESULTS三文档；当前无再分子任务。若确需拆分，子目录继承task8.1.N，每节点同样三文档；先登记顺序、依赖、负责人、模型/强度、三文档链接和父验收关系再派发，编号稳定不复用。未建立子节点不代表可以绕过父文件归属或预算。

## 输入与顺序

依赖：无；先读父共享接口。 必须先核输入hash/版本、父预算余额和文件写入所有权。独立Agent仅改本节点TASK列出的代码/配置/tests与自身RESULTS/日志，接口问题向父报告。

- [ ] 列出当前PCD头字段/JSON schema实际组合，解析FIELDS/SIZE/TYPE/COUNT/WIDTH/HEIGHT/POINTS/DATA，声明只支持本批ASCII xyz；不把注释/额外字段顺序当xyz列位置。检测行数、有限值、尺寸、边界、单位、hash；空图仅允许明确fixture标志，普通空输入拒绝。
- [ ] 写负例测试后实现严格读取；输入不合法要带map-id/行号/原因，不能静默删除NaN/越界点、回退到JSON boxes。保留不认识的JSON语义字段，不伪造点级语义。
- [ ] 用固定局部RNG生成最小立方体夹具：轴对齐、绕z旋转、两障碍前后遮挡、边界贴近、离地薄板；随机场景固定seed=20261026，4个cube、尺寸0.5–1.0m、保留原点测试净空。尺寸/数量/seed均是测试工程选择（SRC-0987），不称训练分布。固定夹具不依随机成功，保存预期占据/解析参照。
- [ ] PCD先写临时文件再原子完成manifest；只从落盘PCD重新load获得运行几何。重复生成同配置hash相同，乱序/重复点不改变后续occupancy；侧车删除仍能通过manifest元数据加载。
- [ ] 运行本节点测试，记录源/夹具hash、实际命令/退出码；父核manifest及PCD-only反例后交8.2/8.3/8.5。

## 验证命令与异常（尚未执行）

在已运行forem-dev内，`PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests`，实际执行只选择本节点已交付的tests文件；父最终集成时再运行所需集合。通过标准不是只有exit0，还须满足[TASK](TASK.md)所列断言。宿主通过`sg docker -c`调用，日志保留实际argv/退出码；不在宿主装ROS。

全任务共享累计1800s验证预算，单smoke≤120s/64步、先batch1后2；语义图单图30s，均为SRC-0987工程上限。子任务不能重置预算；没有GPU份额时先完成不依赖GPU的部分。超时/依赖缺失写未验收，不删失败数据、不降条件、不静默CPU回退。失败定位后最小修复与必要复验，改变科学合同或扩大范围须先交父说明。

## 输出与交接

逐run写RESULTS：目标/授权、实际负责人/模型/强度、文件与源hash、命令/退出码、证据、通过/未通过门、资源账本、限制/风险、下一步；如有进程附PID/容器/日志/监控/停止方法。当前尚无运行任务。父复核后才标done；共享SOURCES条目由父落账，子Agent提交主张与精确证据位置。
