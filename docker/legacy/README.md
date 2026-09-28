# 来源机器遗留构建与验证产物（仅溯源）

2026-09-28 DOCREV-028 移入。来源机器（RTX 2080 Ti / Python 3.8 / Torch 1.8.1）基于本地 `mm_husky:deps`
增量构建 `mm_husky:p0-ready` 的 Dockerfile、依赖覆盖与审计快照，以及当时的验证输出。本机 node01
不存在 `mm_husky:deps`，无法直接构建；现行环境见仓库根 `ENV.md` 与 `docker/Dockerfile.node01`。
`validation/p0-ready/manifest.json` 中的哈希对应这些文件移动前的 `docker/` 路径。
