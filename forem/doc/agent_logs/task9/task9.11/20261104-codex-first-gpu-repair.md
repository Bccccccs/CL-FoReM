# SRC-1423 首次GPU设备归属修复

开始2026-11-04T10:01:46.171023+08:00，负责人Codex；实际模型/强度未知。推荐GPT6.1sol/high及Sonnet5.5/high，因三方归属与首次/历史预算因果审查。授权：必要实现、标准库替身、独审、文档；禁止真实Docker/GPU/模型/环境/科学运行，不调整预算截止。已读AGENTS/README/PROGRESS/父§17–18/原审核与JSON/ENV；分支codex/task9-lower-improve、既有dirty保留。.14为已有最大子编号，新建.15实施和.16独审。进程中有task10及其他工程任务，未触碰；未见本修复同文件活动任务。

拟改admission/gpu_costs与必要测试；父共享文档仅父写。.15复现原反例→修复→冻结→.16从原件独立核验→父核验。缺失gpu_uuid沿原preferred_gpu_uuid默认；明确null表示空声明须两份inspect同时确认（仅既有synthetic无卡协议可通过）。计划尚未执行。

已复现：.15/before source0bbda355/170，两路径接受GPU110，expected-reject rc1；原raw保留。最小生产修复仅admission/gpu_costs。container_allocation复用allocation，比较包含空集合；gpu_uuid缺失保原protocol默认、null显式空声明，真实CPU仍UNKNOWN。当前稳定freeze-v2 SHA3ae8183a…97d3ad2/171，.16请求sol/high独审已启动，只写自身记录。

开发验证失败保留：matrix-v1对无snapshot读取误期望可核GPU、负例错误匹配UNKNOWN；matrix-v2误期望dispatch缺令抛异常（实际hold）；matrix-final误以为已有外部CPU基线为0（实际3）。只纠正fixture断言，不改生产语义。上述实际命令成本缺完整outer闭账，UNKNOWN并保留原输出，不计0；虚构control30不得加到真实CPU或GPU。matrix-v4 11项rc0；最终同SHA外包runner另录准确wall/rc/source-before-after。

完成2026-11-04T10:14:04.273849+08:00：父143项+同输入反例、.16独立32项同171源3ae818…3ad2通过；父直接核658矩阵/2313新引用/5689旧引用及8独审命令，rc0，独裁SHAa710ce64…07b43d。父接收v1漏读references只作局部检查，v2/最终强制2313后通过，原输出保留。SRC-1423冻结工程关闭、两账保留。实际预算/缺证/风险及下一步见父§19/SRC-1425，精确真实余额UNKNOWN；无真实GPU/容器/科学执行或许可，旧STOP不变，负责人Codex交接。
