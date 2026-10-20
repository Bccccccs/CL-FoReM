# Mapgen 项目说明与 Agent 入口

- 任务 ID：PROJECT-MAPGEN-AGENTS-20261016。
- 用户授权：阅读 mapgen 项目，补充 Agent 文档，详细说明其为上层 Husky 世界模型项目制作地图的用途。
- 负责人：Codex；实际模型与推理强度未知（未从运行环境核实）。
- 推荐：Codex GPT6.1sol、Claude Sonnet5.5，low 或平台默认；普通文档任务没有特殊推理要求。推荐不代表实际配置。
- 开始：2026-10-16 15:59 +08:00；状态 active。
- 范围：新增 mapgen/AGENTS.md；按上层共同约定追加本记录、PROGRESS 与 SOURCES。只读核对代码、提示词和历史输出，不改代码，不调用付费 API，不启动 ROS/Gazebo 或训练，不复制地图到参考仓库。
- 初始状态：mapgen 为独立 Git，main，HEAD 765e06448758dfbe34282edcac00f39ffad36aa5；无本地 AGENTS.md/agent.md。已有未跟踪 .DS_Store、.idea/misc.xml、docs/、outputs/；保留。父仓库 PROGRESS/SOURCES 已有改动，仅追加本任务内容。未见独立 mapgen/pytest 活动进程。
- 证据与结果：阅读 mapgen 核心模块、README、prompts/system.txt、outputs 的说明；具体核查与限制将在完成时追加。

## 交付与验证

- 已新增 `mapgen/AGENTS.md`（182行），说明 Husky 世界模型配套地图工具定位、上层职责、代码目录、角点坐标/旋转协议、PCD/JSON/索引、配置优先级、命令、历史资产和实现限制。未改源码与提示词。
- 证据登记为 [SRC-0333](../../SOURCES.md#src-0333)；最初候选0327在重读共享台账时发现已由其他工作占用，未覆盖，改用当时未占用的0333并修正文档链接。
- 验证：`git diff --check` 退出0；文档链接存在性、来源锚点及逐行尾部空白检查通过；all_maps按文件名统计8类各3张，共24份JSON均有配对PCD；抽查两份JSON扩展字段。
- 入口实测：`python3 -m mapgen --help` 和 `python3 -m mapgen -n 2 --prompt 'warehouse shelves, narrow aisles' --dry-run` 均退出1，原因宿主 `ModuleNotFoundError: No module named 'numpy'`。未安装依赖、未调用模型，文档已明确该环境限制。
- 未执行：测试套件（当前无测试源码）、真实地图生成、所有历史点云逐点验收、ROS/Gazebo接入、机器人通行性或模型训练。
- 风险与后续：文档任务完成；实现限制只记录未修复。后续若用户授权接入/修复，先准备相应运行环境，核对上层加载器及历史扩展协议再验收。
- 状态：done（文档与静态核对完成；入口运行验证未通过的环境限制已如实保留）。
