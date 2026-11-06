# task9.11.6 独立监督修复审查

开始：2026-11-03T20:35:40.582705+08:00；负责人Codex，父请求GPT6.1sol/high，本会话工具未暴露可核实实际后端/强度，实际记未知。推荐GPT6.1sol/high、Sonnet5.5/high：跨进程SIGKILL、docker客户端/容器worker分离、退出竞争与预算恢复需高强度；本轮只sol，不另委派。

授权：只读核验并在本子三文档/本日志目录写证据；标准库替身，不导入torch/numpy/模型/环境，不运行真实回合、不重启旧run。父负责共享PROGRESS与SOURCES登记。新修复结论的来源台账登记由父完成，当前尚无修复结论；既有STOP/历史依据见[SRC-1397](../../../../SOURCES.md#src-1397)、[SRC-1398](../../../../SOURCES.md#src-1398)。

已读根/forem AGENTS、README、PROGRESS、父三文档与H/I、.3/.4/.6三文档、原STOP签字、监督审核及重交接。分支codex/task9-lower-improve，HEAD d198e5ca48f86071c05274f9da753f393ce058b4；既有dirty不改。进程快照存在task10 PID325288；未操作它或任何既有进程。

独立标准库核STOP与7引用SHA全部一致，详见initial-stop-and-baseline.json。STOP仍FAIL_INCOMPLETE_SUPERVISION；原host缺exit/wall不得补成功；已知4000消费/980评估/300updates、formal0/test0保留。旧容器收尾exit137与ON退出码不可混淆，原143仅实施者报告，原因UNKNOWN。

审查重点（计划，尚未执行新实现验证）：稳定源码SHA与最小差分；测试收集和所有导入必须纯标准库；SIGKILL后独立守卫持续落终态与失败证据；Docker exec客户端死亡不代表容器worker退出；父先/子先/竞争均单写终态；写盘故障不放行；started残留、重复启动和重复计费、跨阶段token、deadline/保存预留/总额边界；实际CLI逐入口核对；新freeze不能接受旧PASS或改旧证据。等待.5交付稳定SHA及原stdout/stderr/rc后独立复核。

当前写入仅本日志及initial-stop-and-baseline.json。没有真实运行，没有代码导入或后台任务。

独立CLI/预算静态核验：首报表仅因ast.literal_eval遇到type=int的ast.Name失败（rc1，ValueError malformed node；未导入项目/未写报表），保留此失败记录；改为对非字面量标注expression后同原件读取通过。closed host=2738.7610445022583s，评估启动=980；详细参数与恢复前置见independent-cli-budget-preconditions.json。恢复判NOT_READY：硬编码旧run/deadline、原输出与freeze已存在、旧PASS不绑定新artifact、原STOP待处理；不能给一条新namespace恢复命令冒称现入口可用。未知完整host wall不能变为精确剩余额度。

父v3只读脚本经逐行静态审查后独立执行：仅ast/datetime/hashlib/json/pathlib/time与原JSON读取/文件stat，不读模型内容、不导入项目。精确命令与source SHA、wall/rc见budget-independent-command.json，stdout/stderr均保留。rc0，时点known worker lower bound3508.2106014120222s/remaining upper bound205291.78939858798s；980评估/余10788、4000smoke/0formal/0test。路径定义diagnostic848256323B含diagnostics/*.pt和全部外部审计，逻辑33981572223B、唯一inode22905126135B。快照随后日志写入会增长；本命令自身与后续审查还未在该时点入账，unknown不消除。父旧v1/v2 suffix口径不采用，不把下界改名完整耗时。

## 独立替身第一轮（原件保留）

静态审全部7项与导入链（independent-collection-v2.json），直跑independent_stdlib_checks.py，不经pytest/conftest、不导入heavy模块，精确命令/rc/SHA与stdout/stderr见independent-attempt01-*。6项PASS；slow quiet失败→stop链FAIL：cap0.6s、原起点已过0.2s、停止尾0.2s，quiet0.3s失败再stop0.25s使stage_terminal_wall0.7514183577150106s越cap。该结果是合成逻辑反例，非真实Docker性能实测。已通知父/.5，等待修复复审，不能以首29项快替身PASS替代此链验收。

其他独立通过：跨stage/arm release拒绝、reservation嵌套cap不重复计、40GiB全checkpoint预留精确边界、别臂legacy started阻断全stage、不含heavy导入、PASS record写出后terminal receipt写盘失败仍不可admit。

独立全套复验预检因.5交付后测试SHA改变而断言拒绝（rc1，尚未启动任何测试）；.5说明v6新直接watch单测tearDown把当前unittest PID当替身杀死，原attempt06 rc-9保留，正在仅修测试清理跳自身，生产SHA不变。等待v7。自身7项独立复验先单独运行，原cap0.6与断言保持，仅依新backend接口声明合成quiet+stop总链0.55s；首版反例不删。见independent-attempt02-*原件。

## 最终独立交付（2026-11-03）

**阶段持久性/准入替身PASS；完整host退出与真实尾时UNKNOWN；真实执行NOT_READY。** 审查已完成，原FAIL_INCOMPLETE_SUPERVISION/STOP不变，不是实验放行。本轮来源见[SRC-1399](../../../../SOURCES.md#src-1399)、[SRC-1400](../../../../SOURCES.md#src-1400)、[SRC-1401](../../../../SOURCES.md#src-1401)。

最终生产supervise SHA `71a2f9130f2bc722e233cdd8c5aac12cf35a6e4783191e2a6a8e30fd5754ec49`；admission `0507c9a53a49b88cfc25506a839f770b6a3dfa519877b06b850c4378271afa90`；标准库专用测试 `c9ee81bd5eab388c70d084ac9419322f37fa8026caca344dfb086b13207d733d`。独立先审30项收集与直接/传递导入，再直跑，全部PASS/rc0/5.2235643435s：[收集/SHA](final-suite-independent-collection.json) · [命令](final-suite-independent-command.json) · [原stderr](final-suite-independent.stderr.txt)。另7项自身独立边界全部PASS/rc0/0.263s，原慢quiet→stop反例保留；新实现预留完整25s固定Docker调用链，原cap/断言不增。新backend接口仅声明替身自身0.55s调用链上界，不把真实fsync/OS调度包装为有界实测。

已覆盖父先SIGTERM/SIGKILL、guard SIGKILL、子先、采样竞争、独立残留sleep子进程、双guard死亡无receipt、写盘前/后失败、串行锁、有效PASS同版本跳过无重跑/重计、身份变更拒绝、残留started跨门拒绝、release跨phase/arm拒绝、reservation不双计、全checkpoint40GiB和诊断/episode/worker等边界。真实Docker方法仅mock，从未执行Docker控制；真实worker/模型/环境/回放/训练/test均0。

语义限制必须保留：`exit_code/client_exit_code`是docker-exec客户端结果，不是owner或容器worker独立wait状态；`stage_terminal_wall_s`截止到发布前，不包括完整owner/guard/watcher最终退出和全部持久化尾。owner_alive只是采样。已明确owner/full-wall/container-worker-exit UNKNOWN；收到阶段持久终态后owner随后退出不能当成已取证host exit。双守卫同时死亡/断电可残留reserved并阻断，不能承诺所有故障均写终态。原问题的完整host退出保证尚未通过。

精确CLI差异：host只有prepare/smoke-and-gates/train/final-test，prepare本版显式NOT_READY拒绝；单stage参数属于worker。host `--release`虽解析，对final-test并不充当统一最终令；实际worker逐arm/seed读取`/output/releases/final-test-ARM-SEED.json`。audit `--output`为新建目录，产物audit.json且只是描述性、不签独立PASS。新namespace/冻结/累计旧账适配不在现实现中，不能给一条现成恢复命令；禁止重启旧run。

旧四smoke/原checkpoint与C ON仅可作只读历史证据，不能把旧PASS迁到新SHA或把C原整门FAIL补PASS。新G1须在合法新冻结/身份下另审，当前不得执行。smoke4000已满，正式四run各3M从头；余10788评估=未执行L ON196＋正式9408＋一次独立test1184，未授权再C ON196。若恢复协议要求C重测，须先明确预算/门处置，不挪正式/L/test、不缩步、不延截止。成熟profile/精确剩余额度/退出尾尚无实测，继续NOT_READY。

最终原STOP及7引用SHA再次独立一致；4000/980/300updates、formal0/test0保留。无本审查后台任务，仅写本子三文档与自身日志。精确PASS/FAIL/UNKNOWN、源码与原证据SHA、恢复限制和交接见[最终独立裁决](FINAL-INDEPENDENT-VERDICT.json)。父负责共享来源/预算与交接汇总，下一步停在准备完成，未经新合同不得真实执行。推荐GPT6.1sol/high、Sonnet5.5/high；请求sol/high，实际后端与强度未知。
