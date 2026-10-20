# TASK7.7-OBS-20261019：观测与底盘碰撞设计

- Agent：Claude（claude-opus-5-5，推理强度未知）；推荐Codex GPT6.1sol / Claude Sonnet5.5，medium。
- 状态：done（设计写入）；2026-10-19约20:55–21:10。
- 用户要求：讨论7.7扫描设计；用户问“为什么不是像SCWM里面的全景观测”、局部栅格怎么选、底盘间隙；随后确认“三项都按建议定：全景深度观测、128×128、0.05 m双通道局部栅格、所有障碍算挡底盘。写进task7.7并登记来源。”
- 只读核查：CBL `husky/src/husky_ur5/urdf/husky_ur5.xacro:18–24`（两台VLP-16，origin (±0.5,0,0.2)）；`forem/src/husky_description/urdf/husky.urdf.xacro:85–122`（车体碰撞底面在base_link原点，base_link离地≈0.132 m）；`scwm/run_r2r/r2r_vlnce.yaml:13–21`、`ss_trainer_ETP.py:1713、1930–1935`。
- Claude先推荐“按URDF模拟两台VLP-16”，用户指出应照SC²-WM全景观测，改为全景深度。
- 写入：SOURCES SRC-0372（代码事实）、SRC-0373（用户决定）——首次追加误用了已被Codex占用的0365/0366（Codex同时在登记task7.5(A)的SRC-0365–0371），已立即改号为0372/0373，未改动Codex条目；task7.7 RESULTS“观测与底盘碰撞设计”；父TASK §2.4、U9、U10、§5风险；task7.4 RESULTS §9、§10、§12、§13中观测表述；DECISIONS TASK7-OBS-20261019。
- 未定：S1–S5（安装高度、分辨率与量程、累积方式、自遮挡掩码、机械臂碰撞判定）；U8、U12。
