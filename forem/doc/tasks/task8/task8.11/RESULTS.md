# task8.11 RESULTS — 原语后端训练前置核查

状态：**done（2026-10-27）**：W/I/C硬门通过（X2独立验收），R/T为报告门，限制见文末。依据[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)、[SRC-1312](../../../SOURCES.md#src-1312)。

|门|状态（X1，父已核对标*项）|证据|
|---|---|---|
|W 接线|pass*（equiv CPU/CUDA status pass、守卫0；父读wiring.diff 93行，仅解析/传递/记录map_backend）|`W/equiv_{cpu,cuda}.json`、`W/wiring.diff`、`W/pytest.txt`|
|I 初始化|pass*（P 53.43s 256/256，deadline 235s）|`I/summary.json`|
|R reset分布|report|`R/summary.json`|
|T 吞吐|report*|`T/summary.json`|
|C 合规|pass（X2：19个产物守卫0，账本无训练命令）|账本、`x2/acceptance.json`|

产物根`forem/results/task8/t8-precheck-20261027/`，账本`forem/logs/task8/t8-precheck-20261027/`（X1 21条830.9s/2400s）。

## r1 X1执行（2026-10-27）

执行者Claude子Agent claude-sonnet-5-5 / high，[X1日志](../../../agent_logs/task8/task8.11/20261027-x1-run.md)。

- **W**：`evaluation.py`新增`resolve_map_backend(config)`（缺省`pcd-voxel-v3`，与`environment_geometry_version`矛盾即ValueError），评估sampler/env传入；`training.py` env_factory传入后端，checkpoint写入并校验`map_backend`（旧ckpt缺键按V3），`runtime.json`记录。新增`config/task8/lower_train_B{0,3}_prim.json`（只改`environment_geometry_version`=`primitive-obb-v1`并增`map_backend`），原B0/B3未改。V3缺省改前/改后同种子训练与评估reset的map_ids/proposal_seeds/versions/state/route/grid/observation全部torch.equal（CPU、CUDA，4环境；旧训练路径按原调用形式复现，未执行原`train`以免构造LowerSAC）。测试31 passed、2 skipped（无optimizer用例，未跑task7_lower）。
- **I**（cube-pool-v2 train、种子4718、256环境）：P 53.43s，256/256，提案931，拒绝initial 409/goal 254/route 5/base_connected_region 6/witness 1；分项asset_scene 12.83（其中`load_backend_scene` 8.47、planner 4.35）、initial 14.48、planning 5.15、witness 19.42s。V3对照**用8.9.1.2场景缓存**：50.10s，256/256，提案897；V3无缓存冷启动未重测（8.9.1 P5已知超deadline）。P无缓存。
- **R**（种子4718–4721，每臂1024 episode）：接受率P 0.2714、V3 0.2796（z=−0.79，抽样误差内）；超抽样误差的拒绝原因：route P 22/V3 0（z 4.63）、base_connected_region 25/8（z 2.88）、witness 13/27（z −2.31）；接受episode的起点/目标/朝向/route_length/图分布KS D≤0.0098。逐env配对991/1024接受同一提案，route_length差均值+0.0137m、最大2.53m。X1初判（推断，未隔离）：route/连通域拒绝来自P派生占据（闭合接触计入）与V3体素化差异。
- **T**（无optimizer，warmup2+20步，GPU0，`--family cubepool`=cube-pool-v2 train按stride取64图，每图采一次后factory复用）：转移/s b64 P 200.2 / V3 100.1（2.00×），b256 P 345.6 / V3 139.3（2.48×）；b256分项environment_step P 7.22/V3 27.51s、raycast 1.35/13.28、collision 0.24/8.62；显存峰值allocated b256 P 3997/V3 4438MiB。P首跑缺PrimitiveSceneBatch分项，补wrap重跑，旧文件保留在`T/P/superseded-r0-no-primitive-batch-labels/`。不代表完整随机训练状态分布，不含SAC更新成本。

## r1 X2独立验收（2026-10-27，父核查要点）

执行者Claude子Agent claude-sonnet-5-5 / high（≠X1），报告`forem/results/task8/t8-precheck-20261027/x2/acceptance.md`/`.json`（recommendation“done with stated conditions”），[X2日志](../../../agent_logs/task8/task8.11/20261027-x2-acceptance.md)。账本X1 830.9s＋X2 68.1s＝**899.1s/2400s**。

- W：PASS（带限制）。W/orig与`git show HEAD:`同sha；`src/task8_sim`、`src/task7_*`无改动；`_prim.json`逐键仅后端字段差。X2用新种子31337与不同训练/验证图独立复跑CPU等价（训练与评估各52叶子torch.equal，B0/B3）；P配置下两路径`map_backend`均为primitive-obb-v1。
- 测试：PASS，所跑用例无LowerSAC/optim/backward。I：PASS，提案=接受＋拒绝自洽。R、T：从原件复算一致。C：PASS。
- **限制（判done时写明）**：①V3臂I/R用8.9.1.2场景缓存，V3冷启动未测；②T为cube-pool-v2训练图64图有界轮换（每图采一次、factory复用），replay容量1024非100k，不含SAC更新，2.48×只适用于该负载；③P下`train()`/`evaluate()`全流程未运行（X2补查24张语义迁移图P下可加载，`x2/x2_semantic_p_load.json`），留待smoke；④T中P b256 raycast p50约67ms而8.10 G门P b256为463ms，未解释（父推测：P暴力ray×box成本随盒数增长，立方体图盒数远少于G门所用图，**待核**）；⑤R中route/连通域/witness拒绝差的归因只是X1推断，未隔离验证。
- **流程偏差（父的责任）**：PROCEDURE §2.2要求测试清单经父核准后运行；父派发prompt写为“写入日志后再运行”，与PROCEDURE不一致，X1按prompt执行，未有核准记录。X2事后核查所跑用例均不含optimizer。
- 其他低项：账本rc为`| tail`管道退出码（X1全部rc0且产物status pass）；SHA256SUMS未覆盖interactions/gpu.csv/episodes.pt。
- **转入task8.12待决（M1）**：`training._contract()`哈希清单不含`src/task8_sim/primitive_scene.py`、`primitive_assets.py`（父读`training.py` L30–37核实），用P训练时P几何代码变更不会被检查点合同检出。

