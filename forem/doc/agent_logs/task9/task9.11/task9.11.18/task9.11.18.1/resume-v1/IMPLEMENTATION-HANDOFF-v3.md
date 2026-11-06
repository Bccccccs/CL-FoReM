# 当前必要r2修复交接


## r1真实入口失败后的必要HOST引用修复（v3 / r2）

2026-11-04T15:19:47.785828+08:00 · Codex实施 · review。真实r1 worker在admission.read_release→real_program.release的租约ref比较失败，尚未activate/模型/训练；原日志与r1失败/实际allocation留存，费用由父与独审入账，不抹除身份。根因：inside root(p)=/output，因此原b.bound(allocation_root(...))发布/output ref，与独审HOST ref不相同。

最小修复新增allocation_reference(p,mode)，仅从Path(p.new_output_root)/allocations/activity/allocation-lease.json构造HOST ref；inside b.bound通过/workspace镜像读取同挂载但返回HOST身份。只改real_program.py和专用stdlib测试2文件，其余182同，151科学同、完整final仍同一次冻结。其他program refs核查：prerequisites只读独审HOST原件ref指针，不从out发布ref；final bundle/checkpoint refs强制HOST p.new_output_root且file_ref通过b.local_path读取；prepare及lifecycle收据只由HOST执行端发布，无同类运行时/output ref发布。

[freeze-program-v3.json](freeze-program-v3.json)封184源SHA `93349324b595a2a8de9c9d8575f4ecf05f32d1d2c73376d2ae82b9f2f6bc9d3b`，协议[real-contract-program-v3-r2.json](real-contract-program-v3-r2.json)SHA `038814a13238f5185d7eb7c3031c2a37b570021dc5e12e33629a81d916ee389c`，新run t9.11-real-program-20261104-r2。r1原协议/源/失败和消费保留，不修改既有full checkpoint（当前尚无正式checkpoint）。

定向4项rc0见commands/program-host-container-reference-v2：实际admission.read_release在HOST与ASSET_ROOT=/workspace且root=/output两域读同HOST租约返回完整相同token，/output伪ref拒；另复核active resources中途/到cap/nonce/CID、实际worker惰性profile/final原生路由。未重跑全部套件。首定向命令因cwd切至tests但继承relative PYTHONPATH导入失败，v1真实失败保留；v2仅把命令PYTHONPATH改绝对，源码未因该fixture改变。两次actualwait共0.8303429987281561s，4项测试实际终态已取得。另20项program定点直接rc0，工具原server终态保留；全会话费用仍另计，不能只扣receipt时长。

已交独审只核delta，资源全案此前PASS不重复返工；仍需新source/infra/profile独审令才真实启动r2。本子无新增真实模型/GPU/Docker/转移/评估调用，源保持冻结。推荐GPT6.1sol/high、Sonnet5.5/high（跨域原件身份必要修复），实际未知。
