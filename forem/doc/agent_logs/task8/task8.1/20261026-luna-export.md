# task8.1 固定导出与 source 复制执行记录

- run-id：`t8-exec-20261026`
- 负责人：Codex，实际模型/强度：gpt-6-luna / low（按派发记录）
- 授权范围：仅执行固定夹具导出、复制既有 mapgen 资产及只读核对；不训练、不修改代码/配置/任务结果/共享文档，不做根因判断或验收判定。
- 输入依据：SRC-0984–0990；父基线核查 `forem/results/task8/t8-exec-20261026/baseline-check.json` 显示 checked=157、drift=[]。

## 执行

1. 夹具导出命令：`python3 forem/logs/task8/t8-exec-20261026/run_budget.py --owner 8.1-luna --limit 60 -- sg docker -c 'docker exec -w /root/mm_husky_ws forem-dev timeout 55s env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m task8_sim.fixtures --output /root/mm_husky_ws/results/task8/t8-exec-20261026/cube-pool --seed 20261026'`。退出码 0；预算记录 id `6222ad7b17`，elapsed 0.5149s，日志 `forem/logs/task8/t8-exec-20261026/6222ad7b17.log`。
2. 源复制命令：`python3 forem/logs/task8/t8-exec-20261026/run_budget.py --owner source-copy-luna --limit 30 -- python3 forem/logs/task8/t8-exec-20261026/copy_sources.py`。退出码 0；预算记录 id `51c289f84a`，elapsed 0.3147s，日志 `forem/logs/task8/t8-exec-20261026/51c289f84a.log`。输出报告复制并逐文件哈希核对 48 个源文件，目标为 `forem/results/task8/t8-exec-20261026/source/`。

## 输出只读核对

- 导出目录实际产生 `manifest.json`，未发现指派文字提到的 `index.json`。manifest 列出 7 个 ID：`empty`、`axis_aligned`、`rotated`、`occlusion`、`boundary`、`floating_slab`、`random_cubes`；七项 `geometry_backend` 均为 `pcd-voxel-v1`，`sidecar_path` 和 `sha256.sidecar` 均为 null。随机项 seed 为 20261026。manifest 路径：`forem/results/task8/t8-exec-20261026/cube-pool/manifest.json`。
- 源复制报告 `forem/results/task8/t8-exec-20261026/source-copy.json` 的 count=48；脚本 stdout 为 `Copied and hash checked 48 files`。父基线 JSON checked=157、drift=[]。
- 未更改或修正任何异常；`index.json` 与执行器预期的文件名差异交父 Agent 复核。

## 预算与交接

- 父账本状态在两条命令后 `used_s=4.37715625949204`、`remaining_s=1795.622843740508`，active 为空；本代理两次实际 elapsed 合计约 0.8296s。每次均在分配上限内。
- 产物和原始日志路径如上；无后台进程。
- 后续：交由 Sol 按任务协议复核文件名差异、manifest 与 hash 结果；本执行记录不代表 task8.1 验收通过。
