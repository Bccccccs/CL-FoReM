# task9.11.17.1 独立审核记录

开始：2026-11-04T10:44:53.204921+08:00；负责人Codex独审，实际模型/推理强度未知。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因为需审真实wait/设备区间/累计预算和不可执行草案。授权[SRC-1429](../../../../../SOURCES.md#src-1429)，前轮事实来源[SRC-1428](../../../../../SOURCES.md#src-1428)。

父任务已在PROGRESS登记本次实施与独审关系；本独审只写自身三文档和本目录，不更新共享文档、不改实现、不启动模型/环境/GPU/真实Docker控制/执行令。工作树分支codex/task9-lower-improve，HEAD沿父登记d198e5c；现有dirty保留。

## 先行历史检查（不是实现验收）

[原件检查](historical-precheck.json)：旧STOP七引用SHA全部匹配，旧科学记录仅这次C4718 smoke trajectory非干扰，host终态仍缺。局部政策核销1800−618.7961928844452=1181.2038071155548s；原prelaunch6.389356852s及其它外包审核费用保留，不能把inner614.966974538s重复相加。旧FAIL不改，其他会话/尾UNKNOWN不受该政策消除。

## 待冻结源码验收清单

1. 真实收据必须绑定唯一event/run/stage/source SHA、argv/cwd、实际launch/actual wait和返回码/信号、boot/单调时钟锚、owner/child身份和原始输出。未完成/篡改/重复/嵌套不当拒绝，失败费用保留。
2. 真实CPU空设备集不得仅凭gpu_devices=[]、环境变量、无nvidia-smi采样进程或代码说明成立；若没有完整隔离/分配证据，应明确UNKNOWN。GPU持卡区间需要原始inspect/Id/UUID/不变时序basis，已用与预留分列，重叠并集。
3. 原GPU scalar7252.530197859s与归档容器StartedAt→FinishedAt7252.448673015s相差约0.081525s，不默改旧账或假称精确同值。
4. 草案采用独立识别的non-executing格式，生产prepare/supervise/worker/直接准入均拒绝执行；不能只在命令行展示层拒绝。用户准备授权不是stage release。
5. 新身份与旧账继承、固定deadline/58h/2TiB/8GiB、4000smoke/980评估/formal0/test0、科学四配置不变，旧STOP原件保持；stage DAG/角色/模型输入清单完整。
6. 窗口/成熟性能/真实保存恢复与设备验证缺口必须显式保留。真实G1和L ON均未执行，不签任何阶段令，不把零模型验证结果当科学实验。

当前父尚未冻结源码，本独审未运行测试且不作PASS裁决；收到冻结后只针对新增适配设计必要反例，不复跑SRC-1423全套矩阵。

## v1冻结独审与5个拒绝缺陷

冻结175源22064fd70b6ad7c8fab7676f623c32693484d622ab48b10ff3e79fbb7fa8754e。新增独立脚本[independent_checks.py](independent_checks.py)22项：19过、3失败；[真实outer wait收据](commands/independent-v1/wait-receipt.json)及[原stderr](commands/independent-v1/stderr.bin)保留。测试包含实际小型CPU子进程wait/非零/timeout；设备正例与攻击反例全为惰性JSON schema输入，绝无执行其docker/shell/GPU argv，不是物理设备验证。

P1-A：真实CPU分配reader接收sg docker -c字符串时，仅shlex.split核前缀/独立分隔token，未按shell语义约束。`$(nvidia-smi)`替换、换行后宿主命令、附着分号`true;nvidia-smi`三种输入仍被g.command接受空设备集。此时真实shell若运行会在容器外执行内容，所以不能归为CPU隔离容器scope。已向父报告，建议canonical shlex.join roundtrip或禁shell形式；本独审不改生产。

补充[independent_extra_checks.py](independent_extra_checks.py)2项均失败，原[收据](commands/independent-v1-extra/wait-receipt.json)/[stderr](commands/independent-v1-extra/stderr.bin)保留。P1-B：CPU分支在StartedAt解析前return[]，同时缺StartedAt或同时未来2099仍接受。无合法连续allocation时间依据。已要求CPU/GPU共同先验StartedAt起点/时区及before观察包围。

v1独审结论暂为工程拒绝缺陷未关闭，真实NOT_READY。等待父修复/新冻结后，用相同逻辑输入重验，旧v1及失败费用永久保留，不将开发失败改成旧代码PASS。

## v2最终独立裁决（2026-11-04T11:03:19.178889+08:00）

审核交付done，**PASS_PREPARATION_ENGINEERING_ONLY；真实NOT_READY，不签执行令**。[SRC-1431](../../../../../SOURCES.md#src-1431)。源175文件`46218cc54e5f88ae0b38953ddcb5d6d80625161e13264b80b34c8dd0c423f587`，v2首项逐文件匹配，最终[source-after](final-source-after.json)再次逐项一致；父冻结源只读。

独立28项全部通过，脚本[independent_checks_v2.py](independent_checks_v2.py)，实际[stdout](commands/independent-v2/stdout.bin)/[stderr](commands/independent-v2/stderr.bin)/[outer真实wait](commands/independent-v2/wait-receipt.json)。其中原5个失败反例直接从v1原raw读取相同JSON及SHA重审，原件清单在[同输入manifest](raw-v2/test_26_original_v1_five_counterexample_inputs_now_reject/same-original-input-manifest.json)，全部由生产g.command拒绝。CPU严格隔离/GPU完整分配窗口/规范sg命令惰性正例保持通过；后者均不是实际物理设备验证。

实际CPU root成功/exit13/timeout、源删除导致未闭账、epoch/源快照篡改拒绝、无设备review拒绝、真实source成本/clock字段一致、错误容器/自审/privileged或设备挂载拒绝、全部草案直接准入/prepare/worker/supervise于模型激活或Docker控制前拒绝、旧FAIL/预算/科学分配/UNKNOWN不能修改、foreign和duplicate收据拒绝、嵌套wait仅union安全下界（并列wall sum、exact仍UNKNOWN）覆盖完成。本次无旧SRC-1423矩阵重跑，无模型/真实GPU/环境/Docker控制/科学测试。

[正式独裁](FINAL-INDEPENDENT-VERDICT.json)SHA `472909aa2a414b3cd1565b69f8814415d90822d56d563424318a0cd0b98234d4`，518稳定引用及3次top command完整argv/cwd/rc/wall/原stdout-stderr SHA，v1/v1-extra失败保留。3次已闭合outer root.wait合**7.353106319904s**，内嵌CPU wait/惰性GPU区间不重复相加。finalizer自身随后由另一个[outer wait收据](commands/independent-finalize/wait-receipt.json)rc0闭合**0.114786442369s**，在上述正式独裁生成后，需另计，4次合7.467892762274s；不据此闭合全部独审会话/文档/发布/退出尾。

限制与剩余依赖：真实CPU/GPU归属/旧不可变时序basis未物理验证，历史及当前完整控制/会话尾费用UNKNOWN；真实costs/inherited/动态控制准入仍被这些缺证阻断，新原语不能当完整可执行链；新G1/L ON196、成熟250k/profile/保存恢复/真实Docker尾及全案原截止可行性均未验，独立阶段令不存在。原58h/2TiB/8GiB/T0/deadline、4000smoke/980评估/formal0/test0不变。

交接父：直接核正式独裁518引用、175源、28项原输出、5旧输入manifest及4条真实wait收据，再收录SRC-1431/父RESULTS。目标是准备交付，不是放行；本独审无后台进程，不启动任何下一阶段。

### 父交付草案/余额补核

只读核[实际v2草案与预算](parent-handoff-independent-check.json)：生产load_protocol/validate接受不可执行草案，175源身份、8份top wait原件、C局部核销及账户一致，208800减法/原deadline日历/53h占额差算式成立；NOT_READY/无release/无namespace与真实设备未验证标记保持。

初次补核checker误把load_protocol新增的_sealed_sha256一侧删除后做全字典相等断言，导致rc1；改checker为同一已sealed值校验后rc0，没有改生产/预算/schema或放宽验证。两轮receipt均保留：

- `parent-handoff-check`：rc1，wall0.665037417784s，[原收据](commands/parent-handoff-check/wait-receipt.json)。
- `parent-handoff-check-v2`：rc0，wall0.665169365704s，[原收据](commands/parent-handoff-check-v2/wait-receipt.json)。

截至此补核6次独审top root.wait合8.798099545762s；正式独裁中的3次计数原样保留，之后finalizer/两次父交付补核另有上述完整收据供父预算追加，不重复叠内层。当前文档/会话/发布退出尾仍UNKNOWN。
