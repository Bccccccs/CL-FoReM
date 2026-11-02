# task9.5.4 PROCEDURE

递归规则：每层恰有TASK/PROCEDURE/RESULTS，进一步拆分先建task9.5.4.1三文档并经父明确依赖/验收；本次不再委派。

1. 读根AGENTS与自己/父TASK；查进程、原GPU CSV，保留H停止前/后窗口区分。
2. 已完成B3三个3M/首个5M summary：拆reset/candidates/observation/inference/environment_step/consume_transition/diagnostics/checkpoint/validation；注明计时是否可相加/CPU-GPU同步限制；不要把sum超wall当并行收益。
3. 对运行5M读取相邻非保存/评估learning间隔，采样CPU/IO/资源压力；GPU已有CSV统计均值/分位/空闲比例，停H后的空卡与慢不能混为一谈。
4. 写自己的RESULTS和日志、性能原件JSON/MD；所有“可加速”仅建议，未验证不叫已提速。不得改共享文档或任何训练代码/参数/进程。

模型推荐Codex GPT6.1sol/medium、Claude Sonnet5.5/medium；实际尚未执行。
