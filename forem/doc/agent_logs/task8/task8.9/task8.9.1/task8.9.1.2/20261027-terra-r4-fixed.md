# task8.9 r4固定执行记录

2026-10-27T13:17+08:00 接手；父派实际配置 gpt-6.1-terra / low（平台内部标识未独立核验）；推荐 Codex GPT6.1sol / low、Claude Sonnet5.5 / low 用于固定步骤，无特殊推理要求。父维护共享PROGRESS与SOURCES。

范围：仅执行父明确释放的固定离线缓存pilot、10324图PCD比特及scene tensor equal、I5测试与重测、C smoke；所有原件交Sol独立复核。当前未释放任何运行；不改生产代码及共享文档，不启动实验。禁止mapgen、task7写入、3M、提交/推送/合并。失败、超时、预算不足或容量错误即停止报告。

只读核查：根AGENTS、README、PROGRESS、ENV、task8.9.1.2三文档、SRC-1210、父协调与I1日志；main ahead 1，已有大量改动保留。forem-dev运行；GPU0 compute PID 1547663，GPU1 compute查询为空。init账本上限1200s，used 4.484440801665187s，I1 active reservation 390s，账本有并发写入，禁止自行并发记账。C账本上限仍3600s，used 395.0120486840606s，active空；扩至7200尚未实际执行。以上为13:17时瞬时快照，启动前须复核。

等待父或init_r4提供精确固定plan、argv、hash、单job reservation及明确启动门；smoke还需I2–I6独立PASS。未运行任何job，尚无原产物。下一步仅在明确释放且资源和预算门满足后执行。

## pilot一次执行

父明确释放且init确认代码冻结后执行，计划SHA256 `84cec58841f65944de9e2cd1f45f36f4f89f1690dbc91ff10ccd6f10059e26c6`；脚本 `45119c37890322529abe0c0190b3b6621d924e82c187a416e902ae7a19841893`，scene_cache `b4e058d2928514ee9c772f4502d94d42eb73a7f97caea6a569c5421874e446bb`，assets `73c9e766f8713a1cf35709180a0f11ebcecc5a6defe06591c44fbdccb219e838`。精确argv及日志由账本记录 `1fd4074520`，reservation 65s，CPU 32 workers、内部timeout 58s。exit 0，runner 7.475169397890568s；pilot自报 wall 4.831423747353256s，worker累计 130.35365117620677s，96新图、10838012点，optimizer/backward均0。原件 `forem/results/task8/t8-init-20261027/pilot.json`、`pilot.json.progress.jsonl`、scene-cache，日志 `forem/logs/task8/t8-init-20261027/1fd4074520.log`。原件等待Sol独立复核，不将自报pass当验收。未释放全量及smoke。

## 全量一次执行

父释放后核full-plan SHA256 `84748d929392adac50258a6db1b905506d66ec84a7f2a1164da8261a24803f14`，源码/manifest hash同pilot；计划10228新图、reuse_reports指已通过pilot 96行，共10324。job `965d4db8df` 退出0，账本wall 386.65839939843863s，余414.0824358575046s；报告自报wall 383.723501031287s、worker累计12247.146155308932s、optimizer/backward均0。原件 `forem/results/task8/t8-init-20261027/full.json`、`full.json.progress.jsonl`、scene-cache/index.json；日志 `forem/logs/task8/t8-init-20261027/965d4db8df.log`。已通知父和Sol复核，不据自报认定验收；I5及smoke未运行。
