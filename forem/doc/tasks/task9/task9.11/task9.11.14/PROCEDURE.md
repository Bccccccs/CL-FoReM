# task9.11.14 · 流程

负责人Codex独审；开始2026-11-04T09:23:00.481592+08:00。推荐Codex GPT6.1sol/high、Claude Sonnet5.5/high，因设备区间、跨阶段费用与准入因果核验；本次委派请求GPT6.1sol/high，实际后端/强度无法独立核验，记UNKNOWN。授权来源[SRC-1419](../../../../SOURCES.md#src-1419)。

范围：仅自身三文档、日志、独立stdlib检查；生产代码与其他节点只读。仅CPU/替身时钟/占位进程，不加载模型、不控制真实Docker、不运行GPU/仿真/回放/smoke/训练/最终测试。旧STOP、C FAIL、UNKNOWN、58h/2TiB及原截止不变。

递归规则：每层恰有TASK/PROCEDURE/RESULTS，本节点不再委派。顺序：父复算旧归档→.13实现/专用测试→冻结→父相关回归与.14独立原事件复算→父核验汇总。依赖和验收以三文档及原件为准，不以自报代通过。

验收：F1/F2联合全生产事件/快照/资源/release路径；CPU只加worker；重复GPU区间一次、独立区间增计；旧公式误拒边界修后通过而真实超额拒；证据缺失/矛盾/篡改阻断；旧件hash不变。

最终执行顺序：旧原件保护195项及101联合原件→db023实际篡改FAIL→.13集中修复→c53首次identity矛盾FAIL→.13最小核验修复→0bbda355最终同SHA五组53项＋1项拒绝费补核→独立核raw文件hash/正向closure绑定/worker与GPU区间余额→父复核后交付。每轮失败和自身fixture ERROR独立保存，未覆盖原输出；不将未宣布冻结的中间源作最终证据。

`run_independent_evidence.py`保存exact argv/cwd、sourcebefore/after、实际脚本副本、stdout/stderr/rc/wall；自写GPU每项在cleanup前复制整个原始临时树并保original_path→archive SHA。原始区间由独立端点扫描计算并与snapshot/admission used、reserved、remaining逐维比对；worker从原始单调端点与逐件候选control reservation计费，不调用生产公式作oracle。已审记录/时间/设备/identity坏件既阻准入也阻新审核；合法running→stopped仍通过。

近余额正向保持原58h/单卡/T0/保存1800/总deadline：已有1700s CPU输入使旧式在新CPU之前仍208768.197382＜208800，真实CPU子进程＋三独立元数据control之后208858.441374＞208800；新GPU按持有窗口、只预留cap4，真实生产worker后继通过。另单列已发生GPU超额：显式虚构继承区间前移到原T0之前作算术压力输入，保持全部原上限，联合闭账后新增不重叠500s GPU event，使实用208958.788191＞208800而拒绝前worker875.096860仍低于原上限（拒绝自身30封口后905.096860，另以原receipt与生产inventory核准），审核精确以`cumulative GPU cap`拒绝；不是用deadline/worker/stale代替拒绝。此输入不是实际卡时历史，不为真实余额补证。[SRC-1421](../../../../SOURCES.md#src-1421)。
