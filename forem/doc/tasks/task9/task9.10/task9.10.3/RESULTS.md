# task9.10.3 清单与预算账本核对 RESULTS

**状态：review，交父级复核。** 本轮只读计算完成；未运行模型、环境、训练或脚本；未判断任何因果机制。实际模型/强度未知。

## 12例身份核对

源CSV：`forem/results/task9/t9.9-offline-20261102/blocked-cases-12.csv`（12行，SHA256 `b22d099863d728b33bb3d861d741bd71f7cf1bfff1d7babe275602fe6a23b559`）。Canonical冻结CSV：`forem/doc/agent_logs/task9/task9.8/task9.8.1/frozen-cases-30.csv`（30行，SHA256 `e36d1888b3bb5621f4a8c70d2eb2cea5316ae5883361017dead80de4169a57b8`）。B3已封存A副本同为30行、同SHA，且与canonical文件逐字节相等。

匹配以blocked的 `(training_seed,map_id,episode_seed)` 对应冻结表 `(training_seed,map_id,seed)`，得到唯一冻结行；每例完整冻结键（含proposal seed、角色、来源split、源评测JSON和row索引）及blocked原trace路径/SHA均在[逐例JSON清单](../../../agent_logs/task9/task9.10/task9.10.3/20261103-case-inventory.json)。匹配12/12，无缺失或重复；每seed数量 **4718:5、4719:4、4720:3**，总数12。每个对应源case JSONL均已读并计算SHA256。B3冻结副本的A审核manifest原已登记；首阶段未扫描大型训练checkpoint；追加核查已对台账登记的三个checkpoint做流式哈希，仍未验证manifest之外文件。

## B3成本与父级execution window

B3既有 `final-accounting.json` 中 `worker_wall_sum_s=5395.6091000027955`。按父协议的6/5规划换算：`5395.6091000027955 × 6/5 = 6474.7309200033546 s = 1.79853637 h`（约1.799h）。这是从五个worker总墙钟成本线性推算六批的预算规划值，不是本轮新实测；批间成本未必相同。B3 GPU暴露窗、episode和历史输出累计数仍以原final-accounting为准，没有移植到task9.10新窗口。

父级 `forem/doc/agent_logs/task9/task9.10/execution-window.json` 哈希为 `34c6f18639243dfdc7e6511c5234702c4585d18c75553f0f78891db3966a9a0a`。start=`2026-11-03T14:48:11.222061+08:00`，deadline=`2026-11-03T18:48:11.222061+08:00`；epoch相减恰为14400秒（4小时）。窗口预算为1176回合、14400 GPU秒、2147483648字节（2GiB）。本核查只确认窗口字段内部算术一致，不代表已消费量、开工资源状态或未来实际运行成本。

## 证据与交接

逐例JSON：[20261103-case-inventory.json](../../../agent_logs/task9/task9.10/task9.10.3/20261103-case-inventory.json)。核心账本来源：task9.8 B3 `final-accounting.json`（SHA256 `43fafe390a156d72037edf5438db7d1e732ee7aa5240c84be3c4f081902995cc`）及 `artifact-manifest.json`（SHA256 `46c4656b45c805d9d6e5430bddf30d551459e68d94ef157023e5f87da1303c95`）；随后经父级追加授权，对B3两份输入台账登记的文件完成全量重哈希，详见下节。

遗留：父级需独立抽查键匹配、哈希和预算复算，并在其允许的全局进度位置登记负责人/状态；本子任务未改 `PROGRESS.md`，遵守限定写入范围。父级复核前保持review。

推荐 Codex GPT6.1sol/medium、Claude Sonnet5.5/medium；为常规清单和算术复核。实际运行配置未知。

## 追加：B3输入依赖全量SHA256复核

按父级追加任务，将B3 `input-verification-after.json` 的25项与 `source-manifest.json` 的6项按路径去重，得到31个文件。结果写入 [new-input-verification.json](../../../agent_logs/task9/task9.10/task9.10.3/new-input-verification.json)，文件自身SHA256为 `2aca4141da61640505c5b5fe1f88cc4cd67ba38c7e09e3ca84783124d7250202`。共顺序读取104,635,709,969字节，耗时约95.10秒；31/31 expected bytes与SHA256均匹配，读前/读后文件及打开fd的device、inode、size、mtime_ns、ctime_ns保持一致。三个final.pt分别为34,861,361,635、34,861,549,731、34,861,336,931字节，均以16MiB缓冲逐字节流式SHA256，没有反序列化。

复核覆盖B3登记的checkpoint（包含实际actor权重的final.pt）、三seed训练config、validation评测JSON、semantic loaded/evaluation快照、semantic-pool索引与manifest、evaluation seeds、provenance、训练评测源码、B3执行配置以及六份B3 source snapshot。逐文件expected/actual/hash match/stat前后、来源账本和路径均在JSON中。该核验只证明当前路径内容与B3两个既有台账登记哈希一致；不证明原训练时实际加载行为超出B3原loaded记录所述，也不核对manifest外文件。未运行环境、程序或模型。

## 追加：task9.8 A 69项与124个sidecar依赖小文件核验

按父级追加要求，以A封存的 `frozen-inputs-parent-audit.json`、`all-evaluation-maps-inventory.json` 作为expected清单，对小文件作只读SHA256复核；未运行会写原证据的verify脚本，也未重扫三个大型checkpoint。完整机器可读报告为 [full-dependency-small-check.json](../../../agent_logs/task9/task9.10/task9.10.3/full-dependency-small-check.json)，明确 `status=PASS`、`all_expected_match_pass=true`：262/262 expected match（历史A 69/69、当前checkout现存项60/60、124 sidecar/124、场景索引/manifest/seed index 3/3、B3 source-manifest runtime snapshot 6/6）。9项历史A工件在当前checkout缺失，但其historical原件均实测匹配expected；缺失不记成哈希不匹配，也不据此声称这些文件存在于当前checkout。

完整运行身份摘要在JSON中：B3 image digest、container/user/GPU与只读挂载；五个worker的loaded记录含checkpoint路径、5M步、policy/critic CUDA设备、actor hash、三seed config hash、evaluation/core/script hash及torch/GPU身份；场景侧含semantic index、random manifest、evaluation-seeds及124个逐sidecar hash。历史执行根 `/home/ybc/projects/CL-FoReM/forem` 只读挂到 `/root/mm_husky_ws`，因此实际运行基础源码/模型/配置/场景文件来自该历史根；本checkout `/workspace` 只读挂载，B3诊断runner实际版本以 `source-manifest.json` 封存的 `source-snapshot/` 为准。

另明确登记当前checkout的legacy `forem/scripts/task9_8/` 七文件快照：与B3同名六文件中五个内容哈希相同、当前 `supervisor.py` 与B3运行snapshot不同；`test_supervisor.py` 是当前独有。当前checkout代码快照单独列出，不能替代B3实际运行snapshot。这是版本身份区分，不改变262项expected-match计数。没有作科学或因果判断。
