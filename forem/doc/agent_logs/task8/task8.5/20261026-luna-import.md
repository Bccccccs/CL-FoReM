# task8.5 固定离线导入执行记录 — t8-exec-20261026

负责人：GPT-6 Luna / low（派发指定）。

## 授权与边界

按父派发只执行一次固定命令：从已逐字节复制的 `forem/results/task8/t8-exec-20261026/source/` 导入24对源PCD/JSON到全新 `semantic-pool/`。不分析失败根因，不判task验收通过，不修改实现、配置、task RESULTS或共享文档，不改源/旧task7，不启动额外运行或派发子Agent。逐图统计仅依据导入输出的 `index.json`、`diagnostics.json`。

## 运行记录

- 开始前预算状态：共享上限1800s，已用19.9184612641111s，余额1780.081538735889s，active为空；读取时semantic-pool输出目录不存在。
- 固定命令（只运行一次）：

  ```bash
  python3 forem/logs/task8/t8-exec-20261026/run_budget.py --owner 8.5-luna --limit 75 -- sg docker -c 'docker exec -w /root/mm_husky_ws forem-dev timeout 73s env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B scripts/task8_import_maps.py --source results/task8/t8-exec-20261026/source --output results/task8/t8-exec-20261026/semantic-pool'
  ```

- 退出码：0；账本命令ID `27181bf341`；实际耗时44.725895307958126s；该命令结束时共享预算余额1735.3556434279308s，active为空。未重试。
- 容器：`forem-dev`；`CUDA_VISIBLE_DEVICES=`，CPU运行；未训练。
- 命令输出：`ok=true`、`map_count=24`、`validated_count=24`；预算日志 `forem/logs/task8/t8-exec-20261026/27181bf341.log`。
- 产物：`forem/results/task8/t8-exec-20261026/semantic-pool/index.json` 与 `diagnostics.json`。

## 输出逐图状态（仅抄录JSON状态，不作原因判断）

`diagnostics.json`共24项，24项均为 `status=validated`；未出现 `error`、`exceptions` 或 `failures` 字段/内容。对应 `index.json` 含24个地图条目。完整ID如下：

| map id | diagnostics状态 | error/exception/failure |
|---|---|---|
| home_map_000 | validated | 无 |
| home_map_001 | validated | 无 |
| home_map_002 | validated | 无 |
| hospital_map_000 | validated | 无 |
| hospital_map_001 | validated | 无 |
| hospital_map_002 | validated | 无 |
| laboratory_map_000 | validated | 无 |
| laboratory_map_001 | validated | 无 |
| laboratory_map_002 | validated | 无 |
| library_map_000 | validated | 无 |
| library_map_001 | validated | 无 |
| library_map_002 | validated | 无 |
| office_map_000 | validated | 无 |
| office_map_001 | validated | 无 |
| office_map_002 | validated | 无 |
| restaurant_map_000 | validated | 无 |
| restaurant_map_001 | validated | 无 |
| restaurant_map_002 | validated | 无 |
| warehouse_map_000 | validated | 无 |
| warehouse_map_001 | validated | 无 |
| warehouse_map_002 | validated | 无 |
| workshop_map_000 | validated | 无 |
| workshop_map_001 | validated | 无 |
| workshop_map_002 | validated | 无 |

## 限制与交接

这次只是离线导入命令及其输出状态记录。没有执行场景扫描、默认采样、step或环境链路；因此不说明地图可运行、不说明场景扫描已识别PCD，也不构成task8.5或task8验收结论。源副本的逐字节复制/hash记录位于 `forem/results/task8/t8-exec-20261026/source-copy.json`，本轮未改动。交由Sol按要求核查diff和原产物。

## 逐图 geometry 固定清单（第二阶段派发）

负责人：GPT-6 Luna / low。执行前按 `run_budget.py --status` 核实时共享预算：已用355.82924129161984s、余额1444.1707587083802s、active为空。固定清单为 `forem/logs/task8/t8-exec-20261026/map-geometry-commands.json`，24个jobs按原序逐项用 `subprocess.run(job["argv"])` 调用，argv未重写、未执行总清单runtime空项。每条仅运行一次；无GPU。全部24条返回码均为0，没有超时或非零项；不对诊断含义或验收状态作判断。

| 顺序 | map id | owner | rc | elapsed_s | 账本id | 输出 |
|---:|---|---|---:|---:|---|---|
| 1 | home_map_000 | 8.5-geometry-home_map_000 | 0 | 2.818150 | 55a0eeb84c | `map-diagnostics/home_map_000-geometry.json` |
| 2 | home_map_001 | 8.5-geometry-home_map_001 | 0 | 2.818095 | 6716fea1ad | `map-diagnostics/home_map_001-geometry.json` |
| 3 | home_map_002 | 8.5-geometry-home_map_002 | 0 | 2.817978 | 9eedc10c91 | `map-diagnostics/home_map_002-geometry.json` |
| 4 | hospital_map_000 | 8.5-geometry-hospital_map_000 | 0 | 2.968248 | 48fc0a132f | `map-diagnostics/hospital_map_000-geometry.json` |
| 5 | hospital_map_001 | 8.5-geometry-hospital_map_001 | 0 | 2.818080 | 1f7d7df95c | `map-diagnostics/hospital_map_001-geometry.json` |
| 6 | hospital_map_002 | 8.5-geometry-hospital_map_002 | 0 | 2.617706 | da39b273b5 | `map-diagnostics/hospital_map_002-geometry.json` |
| 7 | laboratory_map_000 | 8.5-geometry-laboratory_map_000 | 0 | 2.817990 | 85a13ff3b0 | `map-diagnostics/laboratory_map_000-geometry.json` |
| 8 | laboratory_map_001 | 8.5-geometry-laboratory_map_001 | 0 | 2.717961 | 125f2f47a7 | `map-diagnostics/laboratory_map_001-geometry.json` |
| 9 | laboratory_map_002 | 8.5-geometry-laboratory_map_002 | 0 | 2.617744 | c0604830e9 | `map-diagnostics/laboratory_map_002-geometry.json` |
| 10 | library_map_000 | 8.5-geometry-library_map_000 | 0 | 2.918191 | dd21c066eb | `map-diagnostics/library_map_000-geometry.json` |
| 11 | library_map_001 | 8.5-geometry-library_map_001 | 0 | 2.868578 | 3bc75df753 | `map-diagnostics/library_map_001-geometry.json` |
| 12 | library_map_002 | 8.5-geometry-library_map_002 | 0 | 2.968308 | 5d5b4746aa | `map-diagnostics/library_map_002-geometry.json` |
| 13 | office_map_000 | 8.5-geometry-office_map_000 | 0 | 2.817860 | a8582f9108 | `map-diagnostics/office_map_000-geometry.json` |
| 14 | office_map_001 | 8.5-geometry-office_map_001 | 0 | 2.767977 | ff423a4574 | `map-diagnostics/office_map_001-geometry.json` |
| 15 | office_map_002 | 8.5-geometry-office_map_002 | 0 | 2.668114 | 4820f132b5 | `map-diagnostics/office_map_002-geometry.json` |
| 16 | restaurant_map_000 | 8.5-geometry-restaurant_map_000 | 0 | 2.918136 | 5db143acd9 | `map-diagnostics/restaurant_map_000-geometry.json` |
| 17 | restaurant_map_001 | 8.5-geometry-restaurant_map_001 | 0 | 2.868245 | 14f9ca51f1 | `map-diagnostics/restaurant_map_001-geometry.json` |
| 18 | restaurant_map_002 | 8.5-geometry-restaurant_map_002 | 0 | 2.918097 | 723280cd2e | `map-diagnostics/restaurant_map_002-geometry.json` |
| 19 | warehouse_map_000 | 8.5-geometry-warehouse_map_000 | 0 | 2.717955 | 502ee02f04 | `map-diagnostics/warehouse_map_000-geometry.json` |
| 20 | warehouse_map_001 | 8.5-geometry-warehouse_map_001 | 0 | 2.768015 | 80ecaa0417 | `map-diagnostics/warehouse_map_001-geometry.json` |
| 21 | warehouse_map_002 | 8.5-geometry-warehouse_map_002 | 0 | 2.818232 | 414e9ca30f | `map-diagnostics/warehouse_map_002-geometry.json` |
| 22 | workshop_map_000 | 8.5-geometry-workshop_map_000 | 0 | 2.818068 | d7479c6396 | `map-diagnostics/workshop_map_000-geometry.json` |
| 23 | workshop_map_001 | 8.5-geometry-workshop_map_001 | 0 | 2.868027 | 66a1c67480 | `map-diagnostics/workshop_map_001-geometry.json` |
| 24 | workshop_map_002 | 8.5-geometry-workshop_map_002 | 0 | 2.767921 | 71c42aa149 | `map-diagnostics/workshop_map_002-geometry.json` |

完整逐命令argv、预算start/end、日志路径和账本数据均记录于父预算账本 `forem/logs/task8/t8-exec-20261026/budget.json`；每条原始命令日志位于同目录，以账本id命名。geometry产物均落在 `forem/results/task8/t8-exec-20261026/map-diagnostics/`。清单阶段完成后预算status显示used=355.82924129161984s、remaining=1444.1707587083802s、active为空。未读取/分类geometry JSON结果；runtime仍未获派发且未执行。交Sol核对原始产物。

## 逐图 runtime 固定清单执行（第三阶段派发）

负责人：GPT-6 Luna / low。父授权文件 `forem/results/task8/t8-exec-20261026/runtime-authorization.json` 指定清单SHA256 `c8a20eb8d56c05f0ea05305a659f2f65c86e0935f9aaf1d9db8070cd04064989`，开跑前对 `forem/logs/task8/t8-exec-20261026/map-runtime-commands.json` 实算SHA完全一致。清单metadata的pending字样按父指示保留，未修改。开跑前共享预算余额1442.5041764136404s、active为空；nvidia-smi记录GPU0–3无计算进程。按原序对24条 `jobs[].argv` 使用 `subprocess.run(argv)`，每条仅执行一次，保持清单参数不变；GPU0串行、未训练。全部24条rc=0，无预算拒绝、异常返回或timeout。未读/分类运行JSON内容，不作通过/地图可行性判断。

| 顺序 | map id | owner | rc | elapsed_s | 账本id | 原始命令日志 |
|---:|---|---|---:|---:|---|---|
| 1 | home_map_000 | 8.5-runtime-home_map_000 | 0 | 6.973875 | a26374a7f6 | `logs/task8/t8-exec-20261026/a26374a7f6.log` |
| 2 | home_map_001 | 8.5-runtime-home_map_001 | 0 | 7.274157 | 129d8ea018 | `logs/task8/t8-exec-20261026/129d8ea018.log` |
| 3 | home_map_002 | 8.5-runtime-home_map_002 | 0 | 6.874068 | 7ad8dc4e80 | `logs/task8/t8-exec-20261026/7ad8dc4e80.log` |
| 4 | hospital_map_000 | 8.5-runtime-hospital_map_000 | 0 | 7.074208 | 9cdb66b9a5 | `logs/task8/t8-exec-20261026/9cdb66b9a5.log` |
| 5 | hospital_map_001 | 8.5-runtime-hospital_map_001 | 0 | 6.973801 | 416c3b2f93 | `logs/task8/t8-exec-20261026/416c3b2f93.log` |
| 6 | hospital_map_002 | 8.5-runtime-hospital_map_002 | 0 | 6.723282 | 30f2db9391 | `logs/task8/t8-exec-20261026/30f2db9391.log` |
| 7 | laboratory_map_000 | 8.5-runtime-laboratory_map_000 | 0 | 7.023713 | 06428eb9a0 | `logs/task8/t8-exec-20261026/06428eb9a0.log` |
| 8 | laboratory_map_001 | 8.5-runtime-laboratory_map_001 | 0 | 6.773470 | dc6d8d86e8 | `logs/task8/t8-exec-20261026/dc6d8d86e8.log` |
| 9 | laboratory_map_002 | 8.5-runtime-laboratory_map_002 | 0 | 6.573347 | 4aba9ca535 | `logs/task8/t8-exec-20261026/4aba9ca535.log` |
| 10 | library_map_000 | 8.5-runtime-library_map_000 | 0 | 7.124245 | cdc21a93ca | `logs/task8/t8-exec-20261026/cdc21a93ca.log` |
| 11 | library_map_001 | 8.5-runtime-library_map_001 | 0 | 7.023783 | 126fcd0b62 | `logs/task8/t8-exec-20261026/126fcd0b62.log` |
| 12 | library_map_002 | 8.5-runtime-library_map_002 | 0 | 7.123878 | b9a7cee0a4 | `logs/task8/t8-exec-20261026/b9a7cee0a4.log` |
| 13 | office_map_000 | 8.5-runtime-office_map_000 | 0 | 6.974064 | b89e240c69 | `logs/task8/t8-exec-20261026/b89e240c69.log` |
| 14 | office_map_001 | 8.5-runtime-office_map_001 | 0 | 6.723392 | 9f1a9a82e3 | `logs/task8/t8-exec-20261026/9f1a9a82e3.log` |
| 15 | office_map_002 | 8.5-runtime-office_map_002 | 0 | 6.523361 | ca6d47b58d | `logs/task8/t8-exec-20261026/ca6d47b58d.log` |
| 16 | restaurant_map_000 | 8.5-runtime-restaurant_map_000 | 0 | 7.124233 | 56b044c92b | `logs/task8/t8-exec-20261026/56b044c92b.log` |
| 17 | restaurant_map_001 | 8.5-runtime-restaurant_map_001 | 0 | 6.973680 | e11795b554 | `logs/task8/t8-exec-20261026/e11795b554.log` |
| 18 | restaurant_map_002 | 8.5-runtime-restaurant_map_002 | 0 | 7.073922 | 025200131f | `logs/task8/t8-exec-20261026/025200131f.log` |
| 19 | warehouse_map_000 | 8.5-runtime-warehouse_map_000 | 0 | 6.473111 | 285c327d99 | `logs/task8/t8-exec-20261026/285c327d99.log` |
| 20 | warehouse_map_001 | 8.5-runtime-warehouse_map_001 | 0 | 6.773427 | c5edda8432 | `logs/task8/t8-exec-20261026/c5edda8432.log` |
| 21 | warehouse_map_002 | 8.5-runtime-warehouse_map_002 | 0 | 6.723441 | 97a87481af | `logs/task8/t8-exec-20261026/97a87481af.log` |
| 22 | workshop_map_000 | 8.5-runtime-workshop_map_000 | 0 | 6.823534 | 2522828c0e | `logs/task8/t8-exec-20261026/2522828c0e.log` |
| 23 | workshop_map_001 | 8.5-runtime-workshop_map_001 | 0 | 7.124124 | 44032a285c | `logs/task8/t8-exec-20261026/44032a285c.log` |
| 24 | workshop_map_002 | 8.5-runtime-workshop_map_002 | 0 | 6.773635 | e8b290ec32 | `logs/task8/t8-exec-20261026/e8b290ec32.log` |

所有真实argv、start/end/rc/elapsed和stdout日志路径均见 `forem/logs/task8/t8-exec-20261026/budget.json`。结果目录出现24份 `<map-id>-runtime.json` 与48份 `*-initial-scan.npz` / `*-next-scan.npz`。全部命令完成后共享预算status：used=523.1155741801485s、remaining=1276.8844258198515s、active为空。nvidia-smi复核无compute进程，GPU0已释放。Luna未读取或判断runtime JSON/NPZ；下一步由Sol核原产物与状态，Luna不据rc=0判地图可行或task8.5通过。

## task8.5 固定入口原字节包装

按父派发将已执行脚本原字节复制到项目正式入口；未改写源文件或历史日志。执行前目标 `forem/scripts/task8_map_diagnostics.py` 不存在，共享预算余额1274.717371918261s、active为空。经预算运行标准库脚本（owner `8.5-package`、limit 5s）完成复制与双文件SHA256比较，命令rc=0，账本id `9f502d1af8`，elapsed 0.03218807466328144s，日志 `forem/logs/task8/t8-exec-20261026/9f502d1af8.log`。

- 源：`forem/logs/task8/t8-exec-20261026/run_maps.py`
- 正式入口：`forem/scripts/task8_map_diagnostics.py`
- 两者SHA256：`ea1a7a6e21c4116d2438b6af42a6c236dd0a8f451e4acc074458c2cff5bd16e5`（完全相同）
- 未运行场景测试或重复地图运行；未改CLI、参数、配置、结果或任务文档。该入口仅为相同字节的正式目录副本。
