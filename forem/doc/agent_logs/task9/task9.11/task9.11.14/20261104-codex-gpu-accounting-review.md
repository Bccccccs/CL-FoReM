# GPU两账独立审核

开始2026-11-04T09:23:00.481592+08:00，授权边界与写入范围同本节点TASK。实际模型/强度未知，委派请求sol/high。当前尚未执行。

## 只读准备

已读根AGENTS、README、PROGRESS、9.11结果§16、.11/.12结果、旧跨阶段审核/核验JSON与生产调用链。独立保护脚本核旧联合101件及.12相关原件共195件SHA一致；清单`preparation-protection.json`。仅自身文件写入。请求GPT6.1sol/high；实际后端与强度无法独立核验，记UNKNOWN。推荐GPT6.1sol/high与Sonnet5.5/high，因同区间去重、worker与GPU分账及跨阶段准入因果审查。来源父维护SRC-1419。

待执行矩阵：同冻结SHA联合生产两stage；按原始时间/device独立计算费用；CPU证据GPU零增；container+event相同区间只计一次、新区间按秒计；重复读取/审核/幂等无GPU重复；原预算附近CPU后继可过、真实GPU新增超额拒；缺失/矛盾/越界/篡改证据UNKNOWN；继承/legacy及设备Count-all等保守。准备不构成验收，等待稳定SHA。

## 独立期望与范围核对（稳定SHA前）

`check_old_archive.py`只读复算旧GPU143→233.0780015643686，差90.0780015643686恰为CPU payload0.07800156436860561＋metadata控制90；保存`old-p1-reproduction.json`，不作修后通过。

自写`independent_gpu_checks.py`13项已准备但尚未执行。GPU oracle是原始device区间端点扫描，worker oracle从原始inherited100、未继承base命令wall、顶层event payload、每份实际control reservation.charged_s及lifecycle的owner_wait_returned_monotonic−job_started_monotonic＋原stage30推导，均不调用生产会计公式。running snapshot按其保存的可信resource_observed_epoch与原container.start推导，核累计GPU区间、余额与预留；实际运行active cap4与worker34分列。

已发现并反馈必要fixture缺口：lifecycle Backend原time.time观察与fixture clock域不一致，有container.json时会阻止实际worker二次准入；.13已改用生产clock.epoch，与真实DockerBackend一致。父另要求partial/disjoint device intervals、review(container_state)和原始资源观察；实现已相应保留。没有修改生产或旧原件。

## db023冻结独审与实质失败

稳定源`db02314ef8bb6e92e31755db9ece7a7db1d0b328d56df60111ec2d9f91175b7a`下，旧F1/F2独立8、审核费原断言1、控制故障5、生产GPU12均rc0；own13 v1/v2分别有2/1个自身fixture ERROR（硬编码已过期expiry、父active只读未带原nonce、near release声称预算超已审余额），全部保留命令/raw/脚本快照/原始临时树，不冒实现FAIL。修自身setup：expiry沿原deadline、active读携实际reservation nonce、release逐维不超过snapshot余额，未改验收断言。

但针对已审container基底的独立原断言发现实质P1：`container-tamper-v1`rc1，已审GPU119.9999997616s，原Id不变只把container.json.start后移5s，resourcecheck接受GPU114.9999997616s。`container-tamper-variants-v1`三项rc1：缩短已停FinishedAt、删container.json、sealed与current DeviceRequests一起改CPU[]都能减少GPU却未拒绝。原断言要求拒绝，未放宽。完整raw在各command记录及`raw-fixtures/<attempt>/`，每项含原snapshot和original_path→archive SHA清单。已通知父及.13集中修复；db023虽已有PASS不作为最终验收。

随后父要求的running→早停与staticlegacy无anchor检查，执行时.13已开始修复，记录中间`beb591233c72b116d36f1c20e7debf1bbc0c69db35efb6bcbd1c777f1c62812b`，**不是最终冻结验收**。dynamic早于已审观察的fake停止已拒，staticlegacy无immutable container interval仍接受、原预期UNKNOWN断言FAIL；已派回。最终19项待新稳定SHA统一执行。

近余额旧式疑问只读复算：父near-balance原archive container206800.001060009＋继承110＋payload1903＋控制150＝208963.001060009＞208800；新union206800.001060009。因为继承110包含在container全持有区间，旧标注+110恰是复算原式。证据`independent-boundary-recalculation.json`。此复算不调用生产会计公式，不是修后验收。独审证据来源由父登记[SRC-1421](../../../../SOURCES.md#src-1421)。

## 最终v3同SHA独立交付

170源`0bbda355c9eaf3018b7f73a27fc033e346dc06d7c0b2b940d1334fce7476c1a9`冻结后，own23 `gpu-independent-final-v5` rc0；旧独立F1/F2 8、审核费1、控制5与生产GPU16 `*-final-v3`均rc0，共53，所有sourcebefore/after一致。此前标签`gpu-independent-final-v3`实际为c53/20历史通过，**不作最终0bb证据**。

已保留并修复的追加实质失败：c53首review record/current alien Id但sealed原Id可被签，`first-identity-v2`原拒绝断言FAIL；v3增加sealed非空/三Id一致后本反例与missing sealed Id通过。近余额source1700s只为原预算内输入，真实CPU payload+三control后旧原式从208768.197382212到208858.441373557；新原GPUcap4仍实际后继通过。完整两stage后新发生GPU500s压力输入独立expected208958.788191080、worker875.096860116，审核精确`cumulative GPU cap`拒绝；已显式标注继承/新增区间前移原T0之前为虚构算术压力，不冒实际卡时或项目余额。源/预算/科学条件未改。

原own fixture问题全部保留并记录：第一次hardcoded expiry、父active nonce、release预算超过已审snapshot；第二次near successor expiry超过总deadline、ISO微秒舍入导致非完全相同区间；新增压力第一次10s release不容原1800s save。只改自身输入setup，最终同SHA整套23通过；发生GPU拒绝用明确cap错误，不用其他失败替代。

最终原件、双账/余额/预留表与限制见本节点RESULTS、`final-verification.json`和`FINAL-INDEPENDENT-VERDICT.json`。原件保护195旧文件及101旧联合件；最终所有raw复制保绝对原路径及SHA，不改旧证据。父将独立核全部引用及全局费用，不把synthetic worker/control/GPU输入叠加真实外包runner。真实NOT_READY，所有旧C/UNKNOWN/STOP和原限额截止保持。来源[SRC-1421](../../../../SOURCES.md#src-1421)。

## 拒绝control费用补核

父指出新发生GPU表行875.096860116为self.audit拒绝之前，未含拒绝自身30。保持final-v5及其raw不改，独立恢复该tmp原字节只读调用costs.inventory后清理；`denial-reconciliation-final-v3`1项rc0、0bb同SHA，完整worker905.096860116，差30一次，raw/生产external743.012717912吻合。GPU event500不变，持有窗口继续增长，原拒绝receipt起讫GPU范围208958.789285898–208958.927470207，拒绝前GPU不冒封口精确值。原denial理由明确cumulative GPU cap。正式裁决升级53主体＋1归档补核，共54同SHA；详见denial-reconciliation.json与RESULTS新增表/小节。真实NOT_READY不变。
