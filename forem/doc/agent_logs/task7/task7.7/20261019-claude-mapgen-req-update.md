# TASK7.7-MAPGEN-REQ-20261019：更新mapgen需求文档

- Agent：Claude（claude-opus-5-5，推理强度未知）；推荐Codex GPT6.1sol / Claude Sonnet5.5，low到medium。
- 状态：done（需求文档更新）；2026-10-19约20:30。
- 用户要求：“更新mapgen需求文档：加入椭圆柱体。先跟我确认地图是用于训练还是测试、各要多少张，再动文件。”
- 授权边界：只改`mapgen/docs/husky_ur5_map_requirements.md`与上层文档；不改mapgen代码、不生成地图、不调用LLM。mapgen为独立仓库，docs/当前未被其Git跟踪。
- 核查：读需求文档与mapgen AGENTS；N²M²迁移代码`forem/src/modulation_rl/scripts/modulation/envs/map.py:871–877`（障碍0.5概率取矩形或圆柱，Gazebo只用矩形）。
- 用户确认结果：A类“这里就先生成一些立方体吧，兼容Gazebo”；数量“验证50＋测试100”；形状“不要圆柱体先”；B类“不做这个”。与最初“加入椭圆柱体”的要求相反，按最新回答执行，不加椭圆柱体。
- 改动：需求文档开头更新说明、第1节（A类用途、B类不做、训练用法待定）、第4节（只用长方体及理由）、第6节（B类本轮不做）、第8节（数量表）；SOURCES新增SRC-0364并在SRC-0363注明被取代；task7.4 RESULTS §15、§16、§18与交接；父TASK §2.5；task7.7 TASK、RESULTS；DECISIONS TASK7-MAPS-20261019；PROGRESS。
- 待定：训练用法（在线或文件池）；B类不做后的未见场景与G6场景。
