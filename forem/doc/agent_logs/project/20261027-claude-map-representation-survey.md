# MAP-REPR-SURVEY-20261027 — 地图表示/PCD转实体地图调研

- 负责人：Claude（claude-opus-5-5，实际推理强度未知）。推荐：Codex GPT6.1sol / medium，Claude Sonnet5.5 / medium（需交叉核对项目几何链路与外部工具适用性，无需high）。
- 用户要求（2026-10-27）：PCD点云与现有地图不太兼容；调研适合的地图类型（便于引入自定义结构），或PCD如何转换为实体地图，是否有已有工作。
- 授权边界：**仅调研与建议**。不改代码/配置/task8合同，不派发、不训练；不干扰正在运行的TASK8.9-PHASE2-R2（Codex）。下列建议均待用户决定，不构成授权。外部来源登记见[SRC-1180](../../SOURCES.md#src-1180)。

## 项目现状核查（事实）

1. 两类地图的几何**源头都是带朝向的盒体**：立方体池由JSON盒体生成（task7.16 mapgen_a）；语义池`mapgen/outputs/all_maps/*.json`含`objects`（name/position/theta/category/size，如`Wall_South:segment_0`为5.0×0.12×1.6 m盒）与`scene`（rooms多边形、walls+openings）。PCD是从这些盒体**体内采样**得到的派生物（`config/task8/assets.json`：`point_representation=solid_volume_samples`）。
2. task8将PCD→0.05 m体素作为运行真值，反复出现采样/格点离散问题：8.7墙体空洞与射线穿墙（SRC-0999/1006）、8.8闭合面归属修复（v3）、8.9.2旋转盒局部格点混叠导致全内部缺格7303（SRC-1123/1125），现以cube-export-v2世界体素对齐采样绕过（SRC-1161）。
3. 已有解析能力：task7 `Panorama`对盒体直接求交；mapgen_a已有闭格子与OBB的SAT精确相交判定（2D）。

**推断**：问题不在“PCD格式本身”，而在“解析几何→采样点→再重建”这一有损往返。已有原始解析几何时，从点云重建只会引入误差。

## 外部调研要点（详见SRC-1180）

|类别|代表|适合做什么|对本项目的限制|
|---|---|---|---|
|原语场景（盒/柱/网格的场景图）|SAPIEN/ManiSkill `add_box_collision`、Gazebo SDF、URDF/MJCF|世界真值；自定义结构=新增原语或mesh|需维护导出器；体素/射线需从原语精确计算|
|网格场景+凸分解|OBJ/GLB；CoACD（SIGGRAPH 2022）；ManiSkill nonconvex/多凸碰撞|任意形状家具/结构|内外判定要求水密网格（Open3D RaycastingScene文档）|
|体素/八叉树/距离场|OctoMap（Hornung 2013）、Voxblox/nvblox TSDF/ESDF、OpenVDB|由传感器观测**建图**（机器人信念图）|OctoMap占据来自射线端点＝表面，非实体填充；不宜作世界真值|
|网格→实体体素|binvox（Nooruddin&Turk 2003 parity/ray stabbing）、Open3D occupancy|mesh到实心体素|薄壁/重叠对parity不稳；需水密|
|点云→网格|Poisson/GP3（PCL、Open3D）、gglaspell bag_to_gazebo_world / PC_to_OG|只有真实扫描、无解析源时|需可靠法向；Poisson会在无点区“幻想”表面；未找到成熟的PCD→Gazebo直接工具|

## 建议（待用户决定）

- **推荐方向A：以原语场景JSON为唯一世界真值，PCD降为派生/可视化产物。** 体素用盒-体素SAT精确判定（3D推广mapgen_a已有方法），射线沿用解析求交；同一JSON可直接导出ManiSkill（`add_box_collision`）及SDF/URDF，服务阶段二零样本验证。自定义结构：先加圆柱/斜置盒等原语，复杂物件用mesh+CoACD。
- 方向B：保留PCD为输入（如未来真实扫描），走PCD→Poisson网格→水密检查→parity/occupancy体素；误差与“幻想表面”需单独验收。
- 方向A会改变task8“PCD为实际几何来源”的用户决定（SRC-0984）及8.1–8.9合同，需用户明确批准后另建任务；本调研未实施任何内容。
