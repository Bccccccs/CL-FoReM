# task9.10.3 清单与预算账本核对 PROCEDURE

## 递归规则及边界

本层恰有 TASK/PROCEDURE/RESULTS 三份主要文档；本子任务不再派生子任务。只写本目录三文档及 `forem/doc/agent_logs/task9/task9.10/task9.10.3/` 独立记录。上游CSV、B3结果/manifest和父 execution-window JSON只读。不得运行模型/环境、改脚本或重扫大型checkpoint。

## 输入与步骤

1. 读取 task9.9 `blocked-cases-12.csv`、task9.8 canonical `frozen-cases-30.csv` 与B3封存A副本。核CSV行数、哈希和字节一致性。
2. 对每条blocked记录，以 `training_seed + map_id + episode_seed` 对应冻结CSV中的 `training_seed + map_id + seed`，要求恰好一条；保留冻结CSV全部身份/索引字段。读取对应原case JSONL并流式SHA256，不修改源文件。
3. 统计训练seed计数，合计应为12。逐例输出路径、冻结键及trace哈希到日志目录JSON；缺失/重复/哈希读取失败须单列，不删分母。
4. 首阶段读B3 `final-accounting.json` 与既有 `artifact-manifest.json`，不扫描大型checkpoint；之后父级追加授权并执行“追加依赖输入重新哈希步骤”，结论限于B3 input-verification与source-manifest登记项。
5. 复算 `5395.6091000027955 s × 6/5 = 6474.7309200033546 s ≈ 1.79853637 h`。这是用B3五个worker耗时和6批规划数量作线性推算，不是实测，也不证明各批成本相同。
6. 复算父级 `execution-window.json`：start/deadline相差14400s；检查其 max_episodes=1176、max_gpu_seconds=14400、max_output_bytes=2147483648。不得把已结束的旧B3预算结转到新窗口。
7. 汇报清单JSON路径、counts、差异/缺口和上述限制；父级负责独立复核与活动任务登记。

## 递归与模型推荐

递归规则同上：每层三份文档；若未来需要拆解，先由父级授权并建立下级三文档。Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，因任务为受限数据映射和算术复核，无特殊推理要求。实际运行模型/强度未知。

## 追加依赖输入重新哈希步骤

父级追加授权后，以task9.8 B3 `input-verification-after.json` 中25项和 `source-manifest.json` 中6项的路径并集作为核验集合；对checkpoint包含 `final.pt` 使用16MiB缓冲顺序读取，仅作SHA256，不反序列化。逐文件记录expected/actual SHA256、bytes与读前/读后stat（device/inode/size/mtime_ns/ctime_ns），要求散列读取期间身份和关键元数据不变。输出 `new-input-verification.json` 至本子任务agent_logs目录。不得运行B3/新环境。

## 追加A依赖小文件核验

按追加授权，复用A `frozen-inputs-parent-audit.json` 的historical 69项/current checkout分布与 `all-evaluation-maps-inventory.json` 的124 sidecar和3 index来源；以标准库只读流式SHA256逐项实核expected，不运行任何会写原证据的原核验脚本。补记 B3 `source-manifest.json` 的六份真实执行source snapshot，与当前checkout `forem/scripts/task9_8/*.py` 独立快照并列，不能把后者替代运行版。记录历史文件、现有checkout、sidecar、index和source snapshot各自expected_match分母；current checkout缺失单独列示。完整运行身份只从B3 run/container/loaded既有记录提取，不启动环境。
