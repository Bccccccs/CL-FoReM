# task9.10.3 清单与账本核对日志

- 用户授权边界：只读核对task9.9 blocked-cases-12.csv与task9.8 frozen-cases-30.csv完整键；产出12行清单、每seed count、源trace/hash；复核B3 runtime成本6/5推导及父execution-window起止预算。只写.3三文档与本目录；不加载模型/运行环境/改脚本、不重扫104GB checkpoint、不作因果判断、不派Agent。
- 负责人：Codex。实际模型/推理强度未知。推荐GPT6.1sol/medium、Sonnet5.5/medium。
- 工作区起始检查：cwd `/home/ybc/projects/CL-FoReM-task9`。发现父级task9.10、task9.8、task9.9及全局文档已有改动/未跟踪文件；未覆盖。此次只改 task9.10.3 三文档和本日志目录。
- 输入核对：blocked CSV 12行，SHA256 `b22d099863d728b33bb3d861d741bd71f7cf1bfff1d7babe275602fe6a23b559`；canonical frozen CSV 30行，SHA256 `e36d1888b3bb5621f4a8c70d2eb2cea5316ae5883361017dead80de4169a57b8`；B3 A封存副本30行，SHA同canonical且字节一致。
- 键映射：blocked `(training_seed,map_id,episode_seed)` 与 frozen `(training_seed,map_id,seed)` 唯一对应；延展保留完整frozen key。成功12/12，无缺失/重复。counts：4718=5、4719=4、4720=3。逐例 trace 和源evaluation JSON路径/SHA位于 `20261103-case-inventory.json`。
- 账本：B3 worker wall sum 5395.6091000027955s；乘6/5得6474.7309200033546s=1.79853637h。该值是预算线性推算，不是测量。父window起止相差14400s，max episodes=1176、GPU=14400s、output=2147483648 bytes。父execution-window SHA256 `34c6f18639243dfdc7e6511c5234702c4585d18c75553f0f78891db3966a9a0a`。
- 命令：标准库Python只读解析CSV/JSON、对12条源trace与输入CSV流式计算SHA；`sha256sum`核对账本文件。未加载checkpoint或运行项目程序。
- 证据/风险：清单JSON已完成。只核已有B3 final-accounting/artifact-manifest，不做大型文件重扫；B3 manifest外资产未核。6/5假定每worker相同，实际批次成本存在未知差异。未核运行时卡空闲或预算消耗。
- 交接：请父级独立复核JSON键/哈希与公式，完成其范围内的PROGRESS登记；当前子任务标review，待复核后更新。

## 追加：B3输入依赖重哈希

- 父级追加授权：从task9.8 B3 input-verification/source-manifest找实际checkpoint/config/actor/source/index，将所有登记依赖重新hash（含三个final.pt流式读取），记录expected/actual/match及stat前后；输出本子任务日志目录 `new-input-verification.json`；不启动环境。
- 合并B3 `input-verification-after.json` 25项与 `source-manifest.json` 6项，31个唯一文件；逐序SHA256，16MiB读缓冲，无模型加载/反序列化。完成31/31，104,635,709,969字节，约95.10秒；所有expected/actual SHA和大小一致，fd和路径读前/读后device/inode/size/mtime_ns/ctime_ns一致。
- 三个final.pt分别34,861,361,635、34,861,549,731、34,861,336,931 bytes，全流通过；其expected与actual hashes列在JSON。完整31项也包括configs、validation json、loaded/evaluation、semantic pool index/manifest/evaluation seeds、provenance、源码及6项source snapshot。
- 输出路径 `/home/ybc/projects/CL-FoReM-task9/forem/doc/agent_logs/task9/task9.10/task9.10.3/new-input-verification.json`；文件SHA256 `2aca4141da61640505c5b5fe1f88cc4cd67ba38c7e09e3ca84783124d7250202`。说明只覆盖两个B3台账登记范围，不证明其外行为，也不扫描登记外项目文件。
- 可供task9.10.1实施方引用的checkpoint/config/source/index具体路径和核验结果在JSON `files` 数组；摘要路径同上。父级抽查小文件。

## 追加：A全依赖小文件核验

- 父级追加要求：核A原69项与124 sidecars实际依赖，复用A小文件清单，不跑写原证据脚本；补充 historical src/current checkout 关系及legacy `task9_8`当前源码snapshot；输出 `full-dependency-small-check.json`。不重扫大文件，不增加实验协议。
- 输入清单：`a-audit-WeDbvWnl/copy/frozen-inputs-parent-audit.json`（69 historical期望项及current checkout对应项）、`task9.8.1/all-evaluation-maps-inventory.json`（124 sidecar+3 index）、B3 `source-manifest.json`（6实际执行snapshot源码）。使用标准库只读流式SHA256并记录读前/后stat；未调用task9.8核验脚本。
- 结果：`full-dependency-small-check.json` status PASS，all_expected_match_pass=true；262/262 expected match：historical 69/69，current checkout现存60/60，sidecar 124/124，index/manifest/seeds 3/3，B3 actual source snapshot 6/6。另9项current checkout路径缺失，historical副本各自匹配expected，缺失未当作哈希错。
- legacy current checkout源快照 `forem/scripts/task9_8/*.py` 七项已独立登记：6个同名可比B3 snapshot中5相同、`supervisor.py`不同（current checkout后续版）；`test_supervisor.py`仅当前checkout有。实际B3执行源码仍按source-manifest的六个只读source-snapshot文件声明。没有把当前版混作运行版。
- 完整运行身份在JSON `full_run_identity`：镜像sha、容器/只读历史源码挂载、只读current checkout挂载、GPU UUID、5个worker的loaded checkpoint/config/actor/evaluation/core/script hash、实际CUDA设备/torch、地图索引文件与sidecars。此前task9.10.3新输入核验负责三个大checkpoint本体hash；本次不重读。
- 父交接：已向父级报小文件核验完成，可供首C放行审核；请以JSON内expected_match明细和版本分层为准。
