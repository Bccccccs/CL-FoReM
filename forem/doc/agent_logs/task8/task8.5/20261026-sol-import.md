# task8.5 Sol 导入协议与验收 — t8-exec-20261026

负责人Codex，实际模型gpt-6.1-sol / medium（派发明确）。推荐Codex GPT6.1sol / medium、Claude Sonnet5.5 / medium：需要核对资产协议、语义与几何差异；固定导入交GPT6 Luna / low，Sol验收。授权与参数沿SRC-0984/0987/0989/0990，父统一SOURCES，本文新增事实待父登记。

范围：独占import_mapgen.py、task8_import_maps.py、test_mapgen_import.py、semantic_pool.json及本节点RESULTS/日志。只离线导入；逐图默认采样依8.4及父放行。源mapgen不写，source副本只读；JSON完整字节保留、PCD唯一真值、split smoke、difficulty原scene类别。不训练，不改变策略输入。已读dispatch-common、AGENTS、ENV、README、PROGRESS、父/本节点三文档、SRC-0984–0990、assets.py合同；main既有dirty内容保留，相关并行8.2/8.3文件不触碰。父已登记PROGRESS。

协议：输出index.json和diagnostics.json；每个源stem（包括孤立JSON/PCD）均生成诊断，错误不跳过且CLI退出1。成功条目通过8.1 load_asset逐点核数、有限性、半开边界、hash/sidecar object校验后进入manifest；源文件逐字节复制。objects仅对有明确position/size/theta且与boxes数值唯一匹配者记录box-index，否则unknown/ambiguous；不生成点级语义。boxes按map_builder._voxelize_box的角点坐标/绕z旋转解释，仅计算差异不回填。诊断同时记录严格闭OBB与1e-6m舍入容差OBB计数；1e-6为诊断工程容差，不改变点/边界/运行占据。报告空box、未被box包含点、重复点、旋转/跨域box；source代码并非旧资产生成版本证明，差异机制只作候选，不作已证根因。

TDD：先写失败测试，再最小实现。所有测试/导入统一父run_budget owner8.5，离线累计≤100s、CPU only、容器timeout。尚未执行测试或正式24图导入。

## 离线实现阶段

已新增4实现/测试/配置文件（源码和CLI/test/config各一），未触碰scene、task7或mapgen。测试导入API为import_pool(source_dir, output_dir)，只写全新输出目录。index消费8.1 load_asset完整合同，diagnostics各图均记录失败，不因一图错误丢弃整批记录；CLI有任意错误退出1。

真实命令共用：`python3 forem/logs/task8/t8-exec-20261026/run_budget.py --owner 8.5 --limit 20 -- sg docker -c 'docker exec -w /root/mm_husky_ws forem-dev timeout 18s env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B -m pytest -q -p no:cacheprovider src/task8_sim/tests/test_mapgen_import.py'`。

- RED：37d614326d，rc1，0.5148436557501554s，7 failed，均缺待实现import_mapgen模块；原始日志`forem/logs/task8/t8-exec-20261026/37d614326d.log`。
- GREEN：d650173dcd，rc0，0.414801430888474s，7 passed in 0.10s；原始日志`forem/logs/task8/t8-exec-20261026/d650173dcd.log`。
- owner8.5当前累计0.9296450866386294s，配额100s；CPU only、无torch或GPU运行，无后台进程。

已给父固定75s（容器73s）导入命令，源source/、新输出semantic-pool/。正式24图导入尚未执行，代码暂冻结等Luna执行后Sol验收。未做默认初始化、扫描/step、24图几何查询，仍依8.4。对象mapping只是JSON primitive到JSON box候选对应，不是点级标签。

## Sol离线原产物审查（2026-10-26）

父followup授权恢复验收。直接读取Luna原始日志27181bf341、index/diagnostics与四实现文件；四文件均本轮untracked，因此git diff输出空不代表无改动，审查以文件全文和SHA为准。

Luna实际gpt-6-luna low固定导入，账本owner8.5-luna，2026-10-26T10:58:03.050892+08:00至10:58:47.778013+08:00，rc0、44.725895307958126s，24 validated。执行argv在budget.json id27181bf341及原始日志完整保留；此为格式/点检查通过，不是几何query门或运行门通过。

Sol独立核验脚本`forem/logs/task8/t8-exec-20261026/review_import.py`，命令：`python3 forem/logs/task8/t8-exec-20261026/run_budget.py --owner 8.5 --limit 15 -- sg docker -c 'docker exec -w /root/mm_husky_ws forem-dev timeout 13s env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B logs/task8/t8-exec-20261026/review_import.py'`。账本ea1b1fa271、rc0、3.0183366080746055s；产物`forem/results/task8/t8-exec-20261026/import-sol-review.json`。

独立重读每份PCD数据行并numpy float64解析，不调用import_pool/asset解析器复算点数：24图合计3,193,408点，逐图实际行数=POINTS=diagnostics点数；全部有限、三轴半开域内。48份导入PCD/JSON与source逐字节相同，SHA逐一等于旧t8-plan map-assets-audit、manifest及diagnostics；完整JSON解码相同，未知字段/objects/scene/category/name随原字节保留；24个ID与旧审计集合相同。manifest smoke/原文件类别difficulty/semantic_policy_input=false逐一核对。四实现文件SHA保存在核验产物code_sha256。

几何差异：严格闭OBB不包含388,268点，1e-6m容差诊断不包含0点；所有box均可解释，无诊断box错误。**1e-6m是工程诊断选择**，只用来揭示严格判定对序列化/边界误差的敏感性，不能据此断言原始生成根因、几何等价、重建精度或“差异已修复”。PCD与box可能不同的候选机制包括历史生成过滤/旋转/裁剪/舍入；本次未复原历史生成过程，不证明某机制已造成差异。PCD仍唯一运行真值，不补墙/改点。

离线账本总计48.67387700267136s（Sol3.947981694713235s + Luna44.725895307958126s），仍在父给予离线100s累计上限内；CPU only，无GPU，无后台进程。本次脚本结束余额1715.4209928466007s为共享瞬时快照，可能随并发下降。

离线原证据核验通过（仅离线gate）。24图geometry query gate、默认初始化、扫描与非零step gate均not_run，依8.4及父放行；run_maps.py等待8.4接口确定后准备，绝不先启动采样。新增实测主张已交父统一登记SOURCES，未自行维护共享文档。

## 逐图诊断准备（尚未执行）

父明确8.2/8.3已独立验收，8.4尚未通过；本轮只准备`forem/logs/task8/t8-exec-20261026/run_maps.py`和固定`map-diagnostic-commands.json`，不做semantic几何或采样/扫描。与8.4责任人只读确认构造/reset、deadline、SamplingIncomplete、FK/Grid/provenance及step接口；未改8.4文件。

脚本每进程一图、分geometry/runtime两阶段；原子JSON在每阶段更新，外部kill保留最后stage与running（必须视incomplete，不能作passed）。geometry独立原点/0.05m floor重建全部原PCD体素参照，与scene occupancy相等之外，还用该参照的指定行列求从x=-6进入地图的正距离x轴命中、occupied centre contains、域外nohit及占据XY底盘碰撞。每图记录查询样本/期待/实际、版本/hash、设备/dtype/耗时；此为少量query回归，不宣称全射线全碰撞证明。

runtime保留默认采样分布及witness规则，只将manifest限定当前map（无factory）；记录完整sampling拒绝/timing、初态实际FK、scene provenance、depth/Grid；候选由原generate_candidates(Grid crop/state/route/kin)生成，取首个可用移动候选，非零raw=[0,0,0.5]仅作固定动作诊断，沿sync_v5原Core执行。记录attempted/committed/IK/碰撞原记录、实际提交后FK、自动渲染计数与诊断nextscan；初/末depth/Grid写NPZ。固定动作不是训练策略、不代表成功率。默认候选无可用移动项记error/incomplete，不换factory或改地图条件绕过。

超时按stage区分：只有reset且sampler accepted=0才reset_timeout；sample已接受后的reset验证/scan、query/candidate/step/nextscan超时记stage_timeout（不当可行性限制）。异常保留traceback记error，typed SamplingIncomplete取消记reset_cancelled，非自然truncated。初始deadline覆盖加载/构造及采样，运行每图内部29s、容器29.5s、账本30s；24runtime最高720s。先全部geometry（内部9s/容器9.5s/账本10s，每图）再由Sol核结果、父放行runtime/GPU0；单GPU串行。geometry额外开销须仍计父共享预算，不偷偷增加预算。

准备语法检查账本167279012f，rc0/0.164420708s：容器内ast.parse，没有import task8、GPU、semantic读取/query或采样。原命令见budget.json对应id/日志。最后编辑仅增加运行代码/config SHA记录，未运行脚本。下一步父cube完整链路+8.4放行后才交Luna执行固定清单；本轮状态prepared/unverified。

最终文件语法复验465c847cd3，rc0/0.164383386s，仍仅ast.parse、无import/query/采样；本轮准备总验证0.328804094s（≤10s）。当前共享瞬时余额1600.582417s。运行清单待父许可，原日志完整保留。

## 执行前每图预算合同修订（父指令；无运行）

父发现原固定清单geometry10s+runtime30s会重复给同一图完整上限。本轮尚无语义运行，因此在派发前修正，先前“runtime每图30s另加geometry”的文字及命令不再是有效执行合同。

有效合同：**每图geometry+runtime累计实际账本elapsed_s≤30s**，包含wrapper/container/startup、失败、超时和所有重验；不会重领30s。离线导入/点box诊断已计共享1800s，和此次逐图几何+运行门分开，不再次扣入该30s（父允许可保守扣，并未要求必扣）。共享全局预算仍另受实际余额约束。

已更新`map-diagnostic-commands.json`：runtime全部argv=null、not_executable_recompute_after_geometry，删除旧无条件30s argv，不能派Luna执行runtime。新增`map-geometry-commands.json`只含24条可提交父批准的geometry固定命令，单条账本≤10s/容器9.5s/脚本9s；owner明确`8.5-geometry-<map_id>`，目前全部pending_parent_geometry_release。每个运行账本id由run_budget生成后，以唯一owner和map_id加入逐图预算映射；重验相同owner继续累计。

24geometry完成后由Sol逐map汇总budget.json所有`8.5-geometry-<map_id>`和`8.5-runtime-<map_id>`记录（含所有重验）的id/rc/elapsed/timeout，remaining=max(0,30-sum elapsed)。先检查全部24 geometry gate与原始query记录；几何异常/超时/缺记录不能当采样限制。Sol基于实际remaining生成新runtime固定清单后交父批准，不让Luna自行推理额度/分类。

新runtime账本limit=remaining-0.25s保守guard，容器timeout=limit-0.5s，脚本内部max-wall=limit-1s；limit≤1s则不再运行，记budget_exhausted/incomplete，保留精确stage，不伪造reset_timeout/passed。总实际目标仍是每图≤30s，额外guard用于账本launcher终止开销，不给科学合同增加参数。runtime owner固定`8.5-runtime-<map_id>`。默认采样/候选/动作/终止与脚本保持；只有执行时限缩到真实剩余额度，科学分布不变。

此轮仅清单/日志编辑，没有semantic查询、GPU或采样，没有新增验证计算。下一步父8.4/cube放行后Luna只执行geometry清单，再由Sol核24原始几何与预算；不得提前执行runtime。

## 24geometry Sol原证据复核与runtime剩余额度（READY，未运行runtime）

父已确认8.4独立high通过并派Luna固定执行24geometry。本Sol收到后直接读取原JSON，不采信自报完成。新增不同目的审查脚本`review_geometry.py`：重读source原PCD与sidecar核hash；独立numpy floor构建期望占据、期待正距离ray，逐图对比几何JSON的点数/占据数/首占据中心/ray origin/方向/期望与实际hit、contains及base collision记录；逐map精确owner定位账本id，检查真实argv与固定清单一致、rc0、无timeout、版本与PCD provenance hashes相等。没有重复调用scene query，没有启动采样/scan或GPU。

审查命令：`python3 forem/logs/task8/t8-exec-20261026/run_budget.py --owner 8.5-geometry-review --limit 15 -- sg docker -c 'docker exec -w /root/mm_husky_ws forem-dev timeout 13s env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python3 -B logs/task8/t8-exec-20261026/review_geometry.py'`。e905636917 rc0/1.6665822947397828s，24 maps/3,193,408 points；`results/task8/t8-exec-20261026/geometry-sol-review.json`为逐图证据/精确geometry账本id/期待与实际ray/范围限制。每图仅一条非平凡正distance入域ray、occupied/outside contains、一项occupied XY base碰撞，独立核完整occupancy参照；不是穷尽几何证明。

全部24geometry_gate=reviewed_pass；24geometry真实父账本累计67.4836772121489s。账本逐图id/owner/elapsed/rc及后续runtime owner/id槽写入`results/task8/t8-exec-20261026/map-budget.json`。父已复核8.4/cube不替本24图runtime验收。

为保守执行每图30s累计合同，runtime前额外扣离线导入每图diagnostics.elapsed + 导入命令27181bf341实际44.725895s减各图处理和后的非负wrapper余量等额摊分；再将离线独立review ea1b1fa271(3.018337s)与本几何review e905636917(1.666582s)完整实际命令耗时各等额摊分至24图。此为局部预算保守计费，不将全局账本重复加耗。再扣全部精确`8.5-geometry-<mapid>`/`8.5-runtime-<mapid>`命令实际耗时（包括未来重验）。

每图remaining范围24.352274398–25.677165026s。runtime账本limit=remaining−0.25s，容器timeout=limit−0.5s，脚本max-wall=limit−1s；24runtime账本上限合计597.105508577s。新固定`logs/task8/t8-exec-20261026/map-runtime-commands.json`含24条完整argv，状态READY_pending_parent_runtime_approval；owner=`8.5-runtime-<mapid>`，GPU0串行，**未运行**。总清单原runtime argv仍null，避免误执行旧无条件30s。未来错误/超时/重验均追加精确id并重新算remaining，不可照旧命令重领额度。

已立即交父路径和READY信息；下一步父审预算清单后才派Luna固定runtime，Sol再读原记录分类。geometry异常未出现不代表runtime可行，不把几何通过当默认采样/scan/step通过。新增实测主张与证据已交父维护SOURCES。

## 24runtime最终Sol原产物验收（READY，父阶段不自判done）

Luna按父授权SHA固定清单单次24runtime，Sol恢复后亲读冻结run_maps.py、PcdEpisodeEnv/reset/Core.step/record_render与默认sampler实现；默认无factory分支，原sample_base/sample_goal、CBL_Q及witness64沿8.4验收版，脚本只限定当前图manifest。运行记录implementation_sha256与当前源码/配置逐项相符；几何与运行可处于8.4最终审核前后不同SHA，分别保留，未拿旧SHA冒充当前。未改生产实现/已冻结脚本、未重跑runtime。

新增原证据审查脚本`logs/task8/t8-exec-20261026/review_runtime.py`；完整命令：`python3 forem/logs/task8/t8-exec-20261026/run_budget.py --owner 8.5-sol-final --limit 25 -- sg docker -c 'docker exec -w /root/mm_husky_ws forem-dev timeout 23s env CUDA_VISIBLE_DEVICES= OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/root/mm_husky_ws/src python3 -B logs/task8/t8-exec-20261026/review_runtime.py'`。afa3d68003 rc0/2.167053901590407s，CPU only；共享结束瞬时余额1274.717371918261s、无本轮后台进程，未使用GPU或仿真。

审查全部24runtime JSON、48scan/Grid NPZ、24geometry JSON、manifest/source语义字节及精确逐图父账本argv/id/rc/elapsed/timeout；额外CPU Kinematics由实际保存的base/q重算初末FK，检查独立常速直线位移v=.15m/s、每个提交子步.05s、q从最后committed候选进入真实状态的关系。不是仅自报passed。

结果：24/24 status step_checked，geometry gate与runtime gate均reviewed_pass；每图默认accepted=1，proposal内部initial/goal等拒绝完整保留，无reset_rejected/reset_timeout/error。每图attempted=2/committed=2，固定raw=[0,0,.5]、base/q均改变，actual FK跨设备最大矩阵分量差1.1920928955078125e-7。复核工程容差3e-6为float32 CPU/GPU算术比较（平移m、旋转无量纲），不是控制执行精度指标。actual q/FK指自写理想执行环境中已提交状态，不是物理驱动反馈，也不是把未提交IK候选回填为已执行状态。

自动sensor_frames各1→2，Core action自动render_count=1，Grid时间0→0.1s、observed掩码保留；初/末valid depth均非零且范围0–6m、depth有变化。NPZ next depth来自额外诊断renderer，Grid来自Core自动扫描更新；额外诊断render不会增加Core自动帧数，已明确区分。传感器self_occlusion=ignored，不解读为实测机器人无几何相交。全部实际cuda:0/float32、scene hashes/versions匹配；source与pool的48文件字节和hash再次核同，完整sidecar保真。

24runtime父账本实际累计165.61975059378892s。保存`map-summary.json`与`map-budget.json.actuals`，保留原planned maps，不覆盖执行前预算；每图精确geometry/runtime id/owner/rc/实际elapsed均可追溯。本阶段final review实际2.1670539s全部均分摊入各图，连同之前离线导入/审查保守费用，最终每图保守累计10.936490018–12.812227325s，全部≤30s。实际全局账本不因局部摊分重复计数。生成summary最终化第一次直接写root-owned产物遇宿主PermissionError（只有文档/汇总写入，未运行复验，未改数据）；随后用同目录临时文件原子replace完成，原始运行产物无覆盖。

交付：`results/task8/t8-exec-20261026/map-summary.json`状态READY_for_independent_8.6_review，all_maps_runnable_this_diagnostic=true、all_maps_within_30s=true；RESULTS已24图逐行表，完整CPU核验脚本/日志/输入产物可复核。此结论只涵盖seed20261026每图一次默认采样与一次固定非零动作，不证明完整任务可达性、跨种子成功率、SAC表现或WM效果；少量geometry queries不构成穷尽几何证明。新事实、原产物、3e-6工程对照容差与限制已交父登记SOURCES。下步独立Sol high进行8.6，父亲自复查后决定父状态；本节点不自判第一阶段done。
