# task10.10 独立审核交接

2026-11-02 17:28 +08，负责人Codex子Agent，实际派发 terra/high。授权只读审查 ca57b4b..afc56f647108c79456dc35d0da2ec8edf779614b；无GPU或采集权限，独占本节点三文档与日志，不修改共享文档和运行代码。读根AGENTS、ENV、README、PROGRESS、父三文档、SRC-T10-015/016、父日志，检查git状态、进程、代码及诊断原件；未停止运行。发现恢复比较器非逐位，已通知父。原件/结论和待验收限制见 [RESULTS](../../../tasks/task10/task10.10/RESULTS.md)。真实运行尚在进行，父负责最终结果、预算与验收核查；本节点未自行修改代码或运行测试。

CPU 反例命令（宿主 Python 缺 NumPy，首次命令退出1；改为容器 CPU，未使用 GPU）：

```bash
sg docker -c 'docker exec --user 1004:1004 -e PYTHONPATH=/workspace/src -e CUDA_VISIBLE_DEVICES= forem-task10-runtime python3 -c '\''import numpy as np, torch; from task10.recovery import tree_equal,mismatch_report; from task10.gpu_diagnosis import compare_tree; pairs=[("tensor",torch.tensor([0.]),torch.tensor([-0.])),("numpy",np.array([0.],dtype=np.float32),np.array([-0.],dtype=np.float32)),("scalar",0.,-0.)]; [print(n,tree_equal(a,b),mismatch_report(a,b),compare_tree(a,b)["exact"]) for n,a,b in pairs]'\'''
```

输出三行分别为 `tensor True [] False`、`numpy True [] False`、`scalar True [] False`，退出0。恢复合同选定字段遗漏硬件等及 deadline/start 布尔值非 status 门槛，也已告知父。真实运行代码冻结，不作修复。
