# task7.25 调研记录

- 开始：2026-10-24T22:14:09+08:00；负责人Codex；实际模型/推理强度未知。
- 用户要求：搜索信息，制定三项流程文档：旧mapgen有场景意义地图能否测试现有高度地图；能否借鉴SC²-WM U-Net生成更好的前瞻点；明确当前项目问题空间。
- 授权：网络检索、只读源码/既有资产/记录检查与流程文档；无新功能、训练、地图生成、仿真、进程启停、Git提交/推送授权。
- 计划文件：task7.25三文档，本日志；父task7三文档增量索引；PROGRESS、SOURCES；必要入口链接。保留全部既有改动，mapgen/scwm只读。
- 初查：根分支main，HEAD cac6c15，已有大量修改/未跟踪文件；scwm HEAD f2f2f5ff2e1f21a08f7d7c51fbbd5c17b0d6778b；mapgen HEAD 765e06448758dfbe34282edcac00f39ffad36aa5，outputs未跟踪。最新任务记录至7.24，不以根早期草案代替当前合同。进程列表可见其他Agent，未发现本任务同名记录；共享文件每次改前重读，只追加本轮内容。
- 技能：using-superpowers、brainstorming用于先查现状/比较路线；写作风格技能无可用检索工具，沿用户明确格式，不声称匹配历史写作。此次交付是调研文档，非获准实施设计。
- 推荐：Codex GPT6.1sol / Claude Sonnet5.5，medium；需核对跨地图格式、候选与控制接口的因果关系。

## 执行记录

- 已读根用户约定、forem/AGENTS、mapgen/AGENTS、doc README、PROGRESS与父流程；用rg定位实际文件。初次猜测observation.py/maps.py不存在（命令rc2），之后按真实perception.py/mapgen_a.py核查。
- 网络检索已开始：SC²-WM、N²M²，后续仅将读过的原论文/官方代码登记为已核验。

## 交接（进行中）

当前交付尚未完成；待源码/资产审计、论文定位、三文档与来源台账及链接验证。未运行任何新实验。

## 调研交付与核查记录

- 新建task7.25三文档；增量追加父task7三文档入口；SOURCES追加SRC-0974–0982。只更新PROGRESS本任务行，未重写他人运行状态、README、DECISIONS或原7.9方案。没有形成新的已采纳研究决策，故不将建议写入DECISIONS。
- 本地源码：perception.py的落点amax/observed与LocalCollision，geometry.py的角点加载/补墙/底盘XY投影，candidates.py的12+1槽，episode.py地图池索引/采样，core.py三通道观测/rollout及上层链；读task7.9 B/D确认R7已定，不重复选型。
- 资产：标准库读取24 JSON/PCD头并哈希48文件；按float64 eps×32、旋转误差1e-6和现load_map中心/包围边界公式静态复算（均沿既有代码）。退出0，得到8类各3图、65–167盒/图、24图均离地、1328离地盒、所核拒绝项0、标准墙匹配0；不是load_map执行成功/PCD逐点一致性/机器人可行性。保存forem/results/task7/t7.25-research-20261024/map-assets-audit.json和source-manifest.json。
- 网络检索：以SC2WM self correcting world model waypoint UNet、N2M2 mobile manipulation、VLN-3DFF、Spatial Action Maps、U-Net为检索主题；只采用SC²-WM和VLN-3DFF原文相关章节、N²M²作者页、SAM/U-Net原始摘要。两篇PDF/一作者页读取失败的具体限制见RESULTS/SOURCES；不假称全文已核。
- 未执行：任何GPU/容器计算、加载/扫描/仿真、候选标签采样、训练/评估、地图生成、进程启停、git提交/推送。静态证据保存不属于实现接入。
- 推荐顺序是A地图表示诊断→B0候选覆盖→有授权时L1生成器→固定条件WM对照，均是建议。训练不稳定、D10 OOM等只引用10-23已有记录，不冒称10-24实时状态。
- 原命令读取不存在observation.py/maps.py及all_maps/README.md出现rc2/rc1；之后按rg真实路径核查。最终验证结果见后续追加。

## 最终交接（2026-10-24T22:27:34+08:00）

- 状态done仅指本轮调研与流程文档。目标、授权和负责人见文首；没有启动任何后续任务或后台监控。
- 交付：[TASK](../../../tasks/task7/task7.25/TASK.md)、[PROCEDURE](../../../tasks/task7/task7.25/PROCEDURE.md)、[RESULTS](../../../tasks/task7/task7.25/RESULTS.md)；SOURCES 0974–0982及父三文档增量索引。
- 验证命令`python3 forem/logs/task7/task7.25/verify_documents.py`退出0；14源码/48地图资产哈希未变，新增来源锚点唯一，本轮本地链接有效。机读证据为forem/results/task7/t7.25-research-20261024/document-verification.json；验证脚本只导入Python标准库，不运行项目模型。收尾修改状态后再次执行同命令核验。
- 剩余：后续A/B/C计算步骤均未执行；网络收益、mapgen整机可行性、WM贡献仍待证据。建议先讨论旧布局补墙处理及表示诊断协议，再授权有界实验。原7.24已有授权由其负责人继续，不重复请求。
- 风险：离地空腔被单值height压缩、底盘真值投影语义、L1教师/输入别名与新候选分布、当前下层未冻结。不得由文档done推断这些问题已解决。
- 无运行任务由本轮交接，无停止/恢复命令；Git未提交/推送，参考仓库/生产源码/配置未改。
