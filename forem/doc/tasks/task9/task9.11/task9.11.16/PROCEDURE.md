# task9.11.16 · 独立审核流程

负责人：Codex独立审核；推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，理由为设备归属、首审与历史快照两路径及预算因果核验。请求sol/high；实际后端型号/推理强度未知。授权[SRC-1424](../../../../SOURCES.md#src-1424)，原问题[SRC-1423](../../../../SOURCES.md#src-1423)，实施[SRC-1425](../../../../SOURCES.md#src-1425)，本独审依据/实测[SRC-1426](../../../../SOURCES.md#src-1426)。

递归规则：每层恰TASK/PROCEDURE/RESULTS三份主要文档；本节点不再拆分。依赖task9.11.15修复冻结后执行；负责人Codex独审，父Agent核验原件后接收，不能把自报直接当父验收。

1. 读根约定、doc入口/进度、父RESULTS §17–18、SRC-1423日志/JSON及本节点三文档，核分支/dirty/进程；不覆盖共享文档。
2. 独立按实际文件内容枚举源码/配置，计算逐项SHA及canonical JSON汇总，核freeze-v2与171个冻结副本，读生产admission、gpu_costs、costs.review和supervise.create_container。
3. 只抑制fixture构造器的自动初审，保证首审前snapshot/commit均空；实际review、resource与公式不mock。直接重放before/result.json的三份原始输入，核before/raw字节与SHA相同。分别测同卡/无卡/缺字段默认/矛盾/异卡/inspect缺失与不一致，独立从原始区间端点积分GPU预期。
4. 首审拒绝检查无snapshot/commit/release、dispatch零启动、拒绝control30与既有未继承CPU3分别保留；不得把无snapshot导致的资源拒绝称为设备校验通过。
5. 另从合法snapshot建立8例设备/声明变化，先证snapshot仍有效，再调用check_resources（含显式current inspect）须由设备或历史不可改写校验拒绝；重审拒绝且保原快照与新失败control30。
6. 在同SHA运行移入自身目录的既有独立4例两账回归与8例F1/F2；所有临时raw、manifest、失败和stdout/stderr落本日志目录。outer_runner记录每次实际argv/cwd/rc/wall及source-before-after；失败也计入本地已知command wall，替身内逻辑账不当真实预算。
7. 冻结源若变化先停止并通知父Agent重新冻结；检查器自身错误保留原失败后只修检查器。发布裁决前逐项核raw manifests、原始证据hash及每次runner元数据。

实际命令、完整参数与结果见[command清单](../../../../agent_logs/task9/task9.11/task9.11.16/FINAL-INDEPENDENT-VERDICT.json)；不在本流程生成真实许可。剩余缺证见RESULTS。
