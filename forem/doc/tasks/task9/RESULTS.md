# task9 RESULTS — 原语后端下层SAC长程对照

状态：**review（2026-11-02：全部训练已退出；9.5六run完成3M，三5M全部完成，最终验收按子任务分别记录）**。依据[TASK](TASK.md)、[PROCEDURE](PROCEDURE.md)、[SRC-1351](../../SOURCES.md#src-1351)。

|子任务|状态|结果|
|---|---|---|
|9.1|done with conditions：B0/B3 512→恢复→1000＋196评估全部完成，账本1409.94/4300s；B0-preserve因检查脚本缺陷重做一次（SRC-1314）；成本推导B0≈21.3h、B3≈7.9h/run（不含训练中重置等未知项）|[RESULTS](task9.1/RESULTS.md)|
|9.2|done with conditions：B3×2到3M不退化（3M验证0.63/0.64）；B0×2看门狗发散停止（1.645M/2.463M）；L5独立验收通过（SRC-1317）|[RESULTS](task9.2/RESULTS.md)|
|9.3|done with conditions：S1–S3＋V4（SRC-1320/1321）；阶段2已批准（SRC-1322/1323/1326）|[RESULTS](task9.3/RESULTS.md)|
|9.4|review：13run已退出（6正常完成、5保护停止、2用户停H）；三5M最终67/63/64%，本批全13run最终独立验收仍待|[RESULTS](task9.4/RESULTS.md)|
|9.5|done：六run均3M且未触退化，三新方向未观察改善；独立执行/协议验收PASS（SRC-1352）|[RESULTS](task9.5/RESULTS.md)|

以下为历史快照，不代表当前运行：

2026-10-31最新状态以[task9.4本次复核](task9.4/RESULTS.md)和[SRC-1329](../../SOURCES.md#src-1329)为准：2正常完成、4发散停止、4运行、3等待；首个5M已到3.5M，最终独立验收未完成。

2026-10-31 20:43最新状态：[task9.4 RESULTS](task9.4/RESULTS.md)、[SRC-1332](../../SOURCES.md#src-1332)。首个5M正常完成，另外两个5M及H两路运行，已无等待run。

2026-11-02：新优化三方向/原5M完整结果见9.5第11节及SRC-1351；本轮未新开训练、不自动替换基线。状态汇总推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium，跨协议独立验收high；实际父模型/强度未知。

2026-11-02：新增[task9.6语义复评](task9.6/RESULTS.md)，用户要求现在启动、下午看结果；仅既有B3三5M final与24×4固定语义回合，不训练。[SRC-1354](../../SOURCES.md#src-1354)。

2026-11-02 14:14：[task9.6](task9.6/RESULTS.md) done，12:06三B3-5M语义复评完成、父逐case核验PASS，132/288=45.83%，与原成败全部一致；[SRC-1355](../../SOURCES.md#src-1355)。不替代9.4全批独立验收。
