# 实际地图参考与汇报提示词修订

- ID：PROJECT-MAP-PROMPT-20261105；负责人Codex；状态active；开始2026-11-05T15:14:23.113961+08:00。
- 用户要求：参考实际训练地图，重写附图的生图提示词，展示当前工作。
- 授权：只读地图及代码，必要生成真实JSON几何参考图，聊天交付提示词；不运行训练/修改实验。
- 实际模型/强度未知；推荐Codex GPT6.1sol / low、Claude Sonnet5.5 / low，固定素材整理；执行者可自主选模/推理强度、先建档委派，本次独立完成。
- 读取：config/task8/lower_train_B3_prim.json、cube-pool-v2 manifest及sparse_train_00000/standard_train_00000 sidecar、semantic-pool index及office_map_000/library_map_000 JSON，旧sample_10_montage.png。
- 观察：随机图有四周围墙、任意朝向和尺寸/高度不一的长方体；语义图是parts组合成的原语几何，不是装修效果图。参考绘图将直接读取boxes，墙体透明仅为看清内部、非科学条件变更。

## 交付
- 状态done，2026-11-05T15:15:42.301732+08:00。读取真实JSON并绘制2x2参考，普通sparse/standard和office/library；实际几何保持，墙体半透明、颜色为展示选择。
- 初次宿主python缺numpy失败，使用已有ccm环境成功，未安装依赖。首版已目视确认形状，后缩小绘图区避免面板标题相互遮挡。
- 依据：SOURCES [SRC-MAP-REPORT-20261105](../../SOURCES.md#src-map-report-20261105)。聊天交付提示词及真实地图参考图；不生成AI新图，不改PPT/代码/实验。
