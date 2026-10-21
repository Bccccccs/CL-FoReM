# 2026-10-20 Claude：task7.10上层离散SAC与偏置层规格草案v1

- 任务ID：TASK7.10-SPEC-20261020；负责人：Claude（claude-opus-5-5，推理强度未知）
- 开始：2026-10-20T20:06+08:00；状态：review（T1–T9待用户确认）
- 用户要求：上一步确认后“好的，暂缓”（验证平台），并按此前计划继续写task7.10；要求“忠于三个原项目”（SRC-0409）。
- 授权边界：只读参考代码、只写文档；不实现、不训练。

## 核查

只读`scwm/` commit f2f2f5f `vlnce_baselines/models/etp/vilmodel_cmt.py:566–621、880–1000`：候选位置/步嵌入＋CrossmodalEncoder；第一评分头作用于detach特征、独立增强评分头；世界模型输入[NAV, V_mixed, V_raw]；门控以V_mixed计算。登记SRC-0412。

## 改动

- SOURCES：SRC-0411（验证平台暂缓）、SRC-0412。
- 父TASK：U40（验证平台，暂缓）。
- task7.10 RESULTS：规格草案v1（U.1–U.8与T1–T9），覆盖原“尚未执行”模板并补交接节；TASK状态行。
- PROGRESS本行。

## 下一步

用户确认T1–T9后回写父TASK与task7.4接口表；起草task7.11。
