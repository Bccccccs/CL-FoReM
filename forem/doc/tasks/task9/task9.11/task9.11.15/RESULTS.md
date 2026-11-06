# task9.11.15 · SRC-1423首次设备归属修复结果

实施与父同SHA回归完成，独立审核.16与父接收完成；真实NOT_READY。推荐GPT6.1sol/high、Sonnet5.5/high（设备三方归属与首次/历史预算因果核验）；主会话实际模型/强度未知，独审请求sol/high。授权[SRC-1424](../../../../SOURCES.md#src-1424)，实施实测[SRC-1425](../../../../SOURCES.md#src-1425)。

## 版本与最小改动

HEAD仍d198e5ca48f86071c05274f9da753f393ce058b4、分支codex/task9-lower-improve，既有dirty/untracked保留，未提交/推送。修前170源逐项等于旧0bbda355c9eaf3018b7f73a27fc033e346dc06d7c0b2b940d1334fce7476c1a9；修后171源 **3ae8183a93e2acf80f3aec23c79357cb96df91faecf2f3b355261d28197d3ad2**，见[freeze-v2](../../../../agent_logs/task9/task9.11/task9.11.15/freeze-v2.json)与[frozen-v2](../../../../agent_logs/task9/task9.11/task9.11.15/frozen-v2)。

只改admission.py、gpu_costs.py，新增test_first_gpu_stdlib.py；旧其余168文件逐字节不变。[最小patch](../../../../agent_logs/task9/task9.11/task9.11.15/minimal-v2.patch) SHA `012f691d49829cb69c81a58e146e7e84d74686d272540b612b5555b697146f5b`。admission统一调用gpu_costs.container_allocation，复用allocation核sealed/current且无条件比较record声明。supervise.create_container原本写gpu_uuid，未修改启动器或schema；缺失gpu_uuid仍沿protocol preferred，显式null表达空声明且须两inspect显式空/原synthetic限制。缺失inspect字段UNKNOWN，不能跳过current检查。首次review、后续check_resources、重新review同一规则；历史不可改写限制继续生效。

## 修复前后相同反例

[复现脚本](../../../../agent_logs/task9/task9.11/task9.11.15/reproduce.py)，准确修后argv/rc/wall见[same-counterexample-final-command](../../../../agent_logs/task9/task9.11/task9.11.15/same-counterexample-final-command.json)。修前[原输入/输出](../../../../agent_logs/task9/task9.11/task9.11.15/before/result.json)、修后[原输入/输出](../../../../agent_logs/task9/task9.11/task9.11.15/after-v2/result.json)及各raw完整临时目录均封存。两轮均从没有历史快照的新目录开始；仅省略fixture自动首审，真实首次costs.review与admission.check_resources没有替换。三份设备JSON逐字节相同，见[same-input-check](../../../../agent_logs/task9/task9.11/task9.11.15/same-input-check.json)；整个fixture新路径/clock anchor及源码绑定的协议引用自然不同，不称整个目录同字节。

同Id，record.gpu_uuid明确为preferred UUID，sealed/current DeviceRequests=[]，started=1793721594、FinishedAt=1793721599（5s替身）。修前两个调用接受，GPU110；同一expected-reject断言失败rc1。修后首次review抛GPU record/allocation contradiction UNKNOWN，无snapshot；check_resources因缺有效snapshot拒绝，断言rc0。没有选择哪份记录正确、没有补造5s、未改继承110账。资源读取在已有合法snapshot后的设备校验由.16独立另核，不能把本例snapshot missing当设备公式已单独覆盖。

## 同SHA验收矩阵

以下窗口增量相对继承110，全部为显式synthetic、execution_allowed:false，非真实GPU实测/生产参数。[11份原始目录与结果](../../../../agent_logs/task9/task9.11/task9.11.15/matrix-stable)。

|输入声明 / sealed / current|首次审核|资源读取|GPU增量(s)|后继能否准入|
|---|---|---|---|---|
|GPU / 同GPU / 同GPU，Id/时间一致|PASS|PASS|5|synthetic release读验PASS|
|null / [] / []|PASS|PASS|0|synthetic release读验PASS|
|GPU / [] / []（原反例）|拒绝UNKNOWN|拒绝，无snapshot|UNKNOWN|否，dispatch hold、adapter零调用|
|null / GPU / GPU|拒绝UNKNOWN|拒绝，无snapshot|UNKNOWN|否|
|其他卡声明 / GPU / GPU|拒绝UNKNOWN|拒绝，无snapshot|UNKNOWN|否|
|GPU / 其他卡 / 其他卡|拒绝UNKNOWN|拒绝，无snapshot|UNKNOWN|否|
|GPU / GPU / [] 或 null / [] / GPU|拒绝UNKNOWN|拒绝，无snapshot|UNKNOWN|否|
|gpu_uuid缺失 / GPU / GPU|PASS，沿preferred|PASS|5|synthetic release读验PASS|
|gpu_uuid缺失 / [] / []|拒绝UNKNOWN|拒绝，无snapshot|UNKNOWN|否|
|GPU / GPU / current缺HostConfig|拒绝UNKNOWN|拒绝，无snapshot|UNKNOWN|否|

每个负例无有效snapshot/commit/release；生产dispatch缺release返回hold，adapter.calls=0。拒绝review的control reservation/completed/denial receipt保留且无pending；cost_control.inventory=30，costs.inventory worker=33（已有外部CPU3+本次审核30），不是GPU补费。正例复审保持同区间，不重复计GPU，独立review仍按原合同计worker30。

## 必要回归与失败保留

[validation-summary](../../../../agent_logs/task9/task9.11/task9.11.15/validation-summary.json)：同最终SHA，11首次+35cross+40supervision+14lifecycle+15continuation+12entry/audit+16GPU=143项，另同输入反例一次，全部rc0；每条`*-command.json`记录实际argv/cwd/outer wall/source-before-after。精确入口`python3 -B forem/src/task9_lr/tests/test_{first_gpu,cross_stage,supervision,lifecycle_candidate,continuation,entrypoints_audit,gpu_accounting}_stdlib.py`，这是七条命令的缩写，真实argv以JSON为准。

GPU专用回归仍证CPU仅增worker、GPU110不动，同GPU重叠区间115不增、独立新增2秒117；已用与预留分列，F1自然expiry历史有效、F2动态成本新增须新审合同保留。原始联合归档见[gpu-joint-stable](../../../../agent_logs/task9/task9.11/task9.11.15/gpu-joint-stable)。R1–R5未重设计。

matrix-v1/v2/matrix-final断言失败输出保留：初版误在无snapshot时要求读GPU、误期望dispatch缺令抛异常、误把既有CPU3当0，修正测试后matrix-v4及最终143项通过。中间freeze/source-final和after记录仅开发历史，不作为最终SHA验收。失败及未封口会话成本继续UNKNOWN，不记0；真实预算后续父交接只累加有outer runner证据的有限wall，虚构30/110等逻辑账不叠加真实CPU/GPU。

## 交接

目标/授权不变，负责人Codex；.16须自冻结源码和原raw独立核验后由父核原件裁决SRC-1423。历史真实设备证据缺失仍UNKNOWN；旧STOP/C完整门FAIL、科学规模、预算截止、4000smoke/980评估/正式0/test0保持，无真实Docker/GPU调用。不得签真实release。实际预算与最终独裁见父RESULTS后续§19。

最终独立32项及父658矩阵原件/2313引用核验通过，SRC-1423冻结工程反例关闭；真实NOT_READY。[父§19](../RESULTS.md#19-src-1423首次gpu设备归属最小修复2026-11-04)/[SRC-1426](../../../../SOURCES.md#src-1426)。推荐GPT6.1sol/high、Sonnet5.5/high因设备证据/两账核验，实际未知。
