# SAC 分线交接

2026-11-02 14:24 +08 开始，Codex，实际模型/强度未知。授权仅限现有版本快照、本地分支、计划和派发文本。原始产物根为 /home/ybc/projects/CL-FoReM/forem。

按 parameter-inventory.json 的 source_sha256 逐文件核对 69 项。各工作树从同一 Git 标签 lower-sac-baseline-v1 起步。下列 SHA-256 绑定推理 actor 及运行配置；完整恢复文件 final.pt 留在各 run 原位置，未重新计算其哈希。

- forem/results/task9/t9-stage2-20261029/B3_5M-seed4718，final.actor.pt SHA-256 `3db11d9f00317849e35a523d66d0935ebc2e3567d82c519ccc42f3d8de42f7ae`，config.json SHA-256 `52d0d7a33019b73601c0e4997d999d9ca366d5da01750a66a4a35b7a469f7086`。

- forem/results/task9/t9-stage2-20261029/B3_5M-seed4719，final.actor.pt SHA-256 `fb9b0054168091e5b4b1953416d8d6e47d03a1834e5a9b0dc4148c85e4574688`，config.json SHA-256 `a7c5db8a4369de00d13a8217cbc9ac5a51d583c5b045d9bdb8b526de276287de`。

- forem/results/task9/t9-stage2-20261029/B3_5M-seed4720，final.actor.pt SHA-256 `c1d7300e6567af18cbd9dde7205e5365f1b681349f4f9de82535955ff0bb330b`，config.json SHA-256 `10f9c7ee281305e0e77f2318172c0705d977a5e72b8e0746b34e0cfeb50d1669`。

- pool · forem/results/task8/t8-pool-20261027/cube-pool-v2/manifest.json · `a501c76edb29939782a7d7c7ac0e6d34fccc4756ed1fb4c510a2ef41769a0fc4`

- transfer_pool · forem/results/task8/t8-exec-20261026/semantic-pool/index.json · `a2071c66df7039f64e76ad729f2c0e398f918b9674c220153c0137247055a343`

- evaluation_seeds · forem/results/task8/t8-pool-20261027/cube-pool-v2/evaluation-seeds.json · `8c7720078023734550c6a15c7f23b74f652adf14fb9120f3bc9639d2fcf4ad76`

采用 B3-5M 全三种子作为 task10 的下层版本。正式比较前固定运行所用种子及其理由。task9.4 整批独立验收另列待办。[分线依据](../../SOURCES.md#src-1356) · [验证结果](../../SOURCES.md#src-1353) · [语义复评](../../SOURCES.md#src-1355)。

2026-11-02 · SAC-SPLIT · Codex · done。共同标签 lower-sac-baseline-v1（1e03d61）；本地 codex/task9-lower-improve（d198e5c）及 codex/task10-upper-wm（ed4fe40）分别位于 /home/ybc/projects/CL-FoReM-task9、/home/ybc/projects/CL-FoReM-task10。已核两分支祖先、计划链接、工作区干净及相对标签仅文档差异。流程待用户派发，未运行实验。

2026-11-02 · 分线布局更正：经核查两个附加 worktree 均干净，已收回目录。两个本地分支、计划提交与基线标签保留；此前派发提示的附加目录已失效，统一从 /home/ybc/projects/CL-FoReM 读取相应分支。
