# task9.11.13 · GPU两账计费修复

状态done（v3同源父回归、独审与原件接收完成；真实NOT_READY）；负责人Codex，开始2026-11-04T09:23:00.481592+08:00。[授权SRC-1419](../../../../SOURCES.md#src-1419)，实施/实测依据由父统一登记[SRC-1420](../../../../SOURCES.md#src-1420)。

目标：修复SRC-1417 P1；worker保留payload及有限candidate control合同，GPU仅按获准设备与有证据的完整占用区间并集计费。已用与后续申请预留分列；CPU未知不当GPU使用，缺失/矛盾/篡改保持UNKNOWN。保留F1/F2、R1/R3/R5及原STOP/FAIL/UNKNOWN、4000smoke/980评估/正式0/test0、58h/2TiB和原截止。

实施范围仅必要costs/admission/continuation/supervise及新增stdlib GPU证据模块、专用测试和必要fixture适配；worker/runtime/audit/科学配置不改。不加载模型、不控制真实Docker，不运行GPU验证/环境/仿真/回放/smoke/训练/最终测试，不新增监控或真实归属API。

交付为同SHA生产prepare→dispatch→实际worker.main二次准入→actualwait→CLOSED→新增审核费→独立snapshot→新release→后继、GPU持有空闲/重复/独立区间、余额边界、证据反例、源快照与最小diff。v1独审发现容器证据可改短，原FAIL与v1全部PASS只保历史；v2绑定已审容器身份/时序；v3补首basis中record/sealed/current三方Id必须一致且非空。v2身份矛盾FAIL及全部PASS保留为历史。静态旧容器没有独立时序basis则UNKNOWN，不自动迁移。详见[RESULTS](RESULTS.md)。

推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因设备区间、累计费用与跨阶段身份核验。本轮委派请求sol/high；实际后端/推理强度平台未提供可核实字段，记录未知。推荐不构成实际配置。
