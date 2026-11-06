# task9.8.2 A阶段回放等价性审查

开始：2026-11-02；负责人 Codex 子Agent task9.8.2。用户授权由父转交：仅 A 只读调查与本人文档；授权 SRC-1364，来源待父登记 SRC-1366。仅写本人三文档与本日志目录，不写共享文档、不派下级、不导入项目代码、不加载模型、不启动仿真/训练、不改生产代码。

请求配置 gpt-6.1-sol/high；实际模型/强度无法独立核实，记未知。推荐 Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为跨模块数值路径和随机流审查。

已读根/forem AGENTS、doc README/PROGRESS、父与本人三文档、9.6/9.7 RESULTS、ENV；工作分支 codex/task9-lower-improve，HEAD d198e5ca48f86071c05274f9da753f393ce058b4。git status显示共享文档与父/其他子任务有既有改动，不覆盖。ps过滤task9/semantic_eval/train_lower未见实际运行任务（只见查询本身）；未停止任何进程。父负责共享PROGRESS登记。

初步发现：EvaluationStreams逐job独立目的流，不依赖原batch位置seed；但actor和动态压缩IK的形状等价未运行证实。此为静态审查，不能声称单例精确回放通过。

## 核查完成与命令

使用cat/nl/sed/rg只读追踪基础src，读取三seedconfig/runtime/loaded/旧评估与seed索引，所有命令rc0；曾用head控制大量日志检索输出，不以截断文本作唯一证据。recompute.py为标准库脚本，唯一写入本人日志audit.json，rc0，assert确认30目标、9原批/144回合、22对基础源码两树字节相同；没有import项目或第三方包。初次audit.json SHA为f2d58a1bf3fd452eaa0d415bd4429819134ed94a7e1b08aeb78c8b3fd14c868b；时间字段导致重跑hash自然变化，后续以最终清单为准。

逐文件hash及Git绑定见audit.json.hashes/workspace_head/historical_head；实际命令复算：`python3 /home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.8/task9.8.2/recompute.py`。会重写本人audit.json，属于准备文档证据而非环境/模型执行。源码重点：evaluation.py/evaluate、EvaluationStreams、evaluation_environment；training.py/choose_candidate/rng_state；task8_sim episode/env；task7_sim candidates/search/kinematics/core；networks Actor；route/scene padding。详情/完整SRC-1366字段在本人RESULTS。

原B3实际基础src命令确认：历史queue-state.json:471,516及extra/waiter-state.json:64，PYTHONPATH=/root/mm_husky_ws/src；task8_lower_train.py:8–10将src插首。没有采用task9_opt/runtime副本。读取的runtime不含完整库/确定性flags，不能补造。

## 最新用户补充后的裁决

父转交用户取消历史逐步/终态一致门，保留on/off非干扰，优先原入口；本人RESULTS第7节覆盖旧严格等价准入结论。原evaluate无case/role/batch选择API或trace hook；单例/176原批需要额外调度包装，784=三seed各196＋4718额外196，无需为9.6另重复96。建议监督者优先784完整原入口方案并先审超32预算/时限；仅30目标详细trace，新旧不同保留，以本次轨迹分析。没有运行或实施，B仍未派发。

交付文件仅本人TASK/PROCEDURE/RESULTS和本日志目录；不动共享/他人文件。实际模型/强度未知，推荐GPT6.1sol/high与Sonnet5.5/high。剩余父原件核验、来源登记和监督预算决定，无后台进程或停止/恢复需求。

最终静态验证：补充入口脚本/原调度日志SHA到audit.json后重新运行recompute.py，rc0；audit.json SHA256 `2cc436683496ca5e3046ac408321130bb558bf57bb155c364711ae0c752e1487`。首次文档自查命令rc1，原因是文档模型名称有gpt-6.1-sol/GPT6.1sol两种写法且PROCEDURE未直接链接SRC-1364；已补直接授权链接并让自查接受用户名/平台名对应写法。第二次AST/JSON/30目标/9批/22源码对/三文档来源模型自查rc0。此为文档证据静态通过，不是环境/轨迹运行通过。


## 父最终门顺序核验纠正

父发现原784/176预算隐含控制on调用中同时采其余目标trace，原B先两例通过再采其余的顺序未被用户取消。已核并接受：严格完整evaluate需5×196=980（off196，on仅2目标196；过门后4718剩8目标196；另两seed各196），严格原批包装32off+32on+48+48+48=208。目标详细trace仍2+8+10+10=30。原784/176仅在监督者另行接受门前附带采集时成立；标待验证也不能自动绕先后门。RESULTS第8节为当前裁决，首段/TASK/PROCEDURE同步修正，保留第7节原建议及其纠正过程。父在SRC-1366采用新口径，授权仍SRC-1364。预算为静态推导且均超32，不实施、不运行。标准库生成budget-order.json，assert980/208/30通过；原audit.json及SHA不变。
