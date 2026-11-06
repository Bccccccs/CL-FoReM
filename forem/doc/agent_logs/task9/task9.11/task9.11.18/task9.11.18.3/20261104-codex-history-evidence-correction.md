# 历史证据归档与CommandExecution遗漏纠正

2026-11-04T11:58:43.799477+08:00。按父新增授权，只修冻结原件归档与3旧root定点metadata核验，无全图扩扫描，无科学运行。

我在第一次宣告v1冻结后为补跨thread caveat覆写了同名FINAL/manifest/generator，这是我的错误，导致期间引用path+SHA失配。现从精确文本反补丁和预存独审SHA恢复旧FINALce14、manifestf687（16项逐hash通过）；原manifest创建时间候选只有完全命中旧f687才接受。最新覆写状态按原字节移存v2，FINAL7ddb、manifestec96（17项按别名物理路径逐hash通过）。恢复不等于覆盖未发生，受影响父/独审引用须追加更正，旧证据不删除。恢复方法、精确路径/全SHA及v2别名见EVIDENCE-CORRECTION-v1.json和v1-recovery-status-v1.json。

原工具响应扫描只看response_item，遗漏event_msg.item_completed.CommandExecution内部终态。按父限定仅原3根定点检查：原rollout572/574/587分别90732/83240/16223，均原completed/exit0；终点1793716725.355/1793716734.163/1793716761.807。原事件与SHA已保存three-root-command-event-recovery-v1.json及三行工具事件raw，无聊天导出。开始继续用早于spawn的outercall1793716724.05，避免metadata start晚于child.started_epoch产生少算。

先前缺终态/全至现场预留是扫描缺陷下的历史候选，不等于根进程真正存活或GPU占用；131响应API终态加3内部metadata恢复，当前22434由父/.18.1另有原内部终态证据。完整detached后代/GPU全局上界仍不由本子自证。新增证据交父/.18.2独裁，不改旧FAIL/UNKNOWN的原记录，不签阶段令；此后所有新证据新文件版本，不再修改冻结v1/v2。
