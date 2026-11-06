# 对照仓库远端同步

- ID：PROJECT-REFERENCE-SYNC-20261106；负责人 Codex；开始 2026-11-06T12:27:49+08:00；实际模型和推理强度未知；状态 active。
- 用户要求：将其他对照仓库推送项目远端。保留上游仓库历史与来源，不修改其工作区；大型数据、训练和构建产物不入 Git。
- 范围：nmoma、topay、scwm、mobile-rl；检查 Husky 和 archive 中的参考源码与嵌套仓库。
- 用户更正：不要独立分支，源码放在 main。四个上游 HEAD 导出至 `forem/references/`，保留许可证、上游地址和提交号；仓库导出不包含 Git 历史。清单列明排除的大型模型检查点及地图数据。
- 初步独立分支推送曾创建 nmoma、scwm、mobile-rl 分支；待 main 推送验证后删除。TopAY 推送已中断，未创建分支。
- 原版 husky 与 archive 包含非独立仓库的源码、构建与大量结果，不在此次四个独立对照仓库快照中；原有目录未改动。
- 状态 review：准备 main 提交及验证。
