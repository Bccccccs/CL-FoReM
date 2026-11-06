# 外部driver脱离工具会话修复交接

2026-11-04T22:31:03.685880+08:00 · Codex实施 · ready / 父恢复启动。只改外部forem/scripts/task9_11_program_drive.py，SHA b07e1d1c5db968c8eaf61e979755880010efab46b158c685b7de0461534a9423；原driver精确字节归档archived-driver-before-fix.py和archive-manifest.json。native b8f3、原protocol、full checkpoint均未改。推荐GPT6.1sol/medium、Sonnet5.5/medium（生命周期与证据因果），实际后端未知；父维护共享台账、兄弟独审恢复裁决，三文档递归责任不变。

故障因果：旧driver把app托管CLI writer1241186失联等同于原生训练失败，提前退出；原生inner/owner/guardian/watcher实际随后完成，250k/24975update/196周期评估、完整21.553GB保存和native restore27.581s有效，exactStopped。原始rootwait缺失保持UNKNOWN；不伪造旧wait-receipt.json、不重跑250k或196回合、不从actor假恢复。

修复：wait_existing在writer死亡后仍有限等待原cap内native lifecycle/worker/exactStopped，核原封活动/source/protocol/release/CID/reservation及成功实际终态；成功只返回NATIVE_CLOSURE_READY_FOR_INDEPENDENT_RECOVERY/MISSING_KEEP_UNKNOWN，由独立review-stage授权裁决。nativeFAIL、晚于原cap完成或cap后无终态仍拒绝。实际r3原件只读preflight通过见actual-native-closure-preflight-v1.json，旧rootwait依旧缺失且未覆盖旧driver状态。独审已恢复profile PASS_COMPLETE并写out/reviews/profile-C-4718.json，--resume会跳过该已审profile转remaining，从原full profile.pt继续。

未来native prepare/execute由外部PPID1 runner承载：短命launcher fork后退出，runner明确reparent1并用独立stdin/stdout/stderr和session Popen实际CLI，持久化detached.json/terminal.json（真实子进程退出码），不依赖app管理工具会话。原native owner/guardian/watcher依原代码守护有效训练；driver STOP/SIGTERM仍只退后续控制，不给有效native链发停止信号。

必要验证一次4项rc0：writer死亡但native后来成功→保持outerUNKNOWN交独审、nativeFAIL拒、晚完成/超cap无证据拒、真实CPU-only detached runner PPID1及CLI子真实exit0终态。实际脱离证据actual-detached-PID1-proof-v1.json与detached-probe-v1/持久原件，launcher退出而runner父为1、CLI父为该runner，stdin/out独立。无GPU/Docker/新科学回合。初次测试命令路径拼写错导致exit2，纠正命令后4项rc0，原工具终态保留，未将其伪称代码首轮全通过。旧4mock适用部分复用，没有全suite重跑。

恢复启动：父沿既有r3 daemon命令加--resume，protocol仍save-repair-v1/real-contract-program-r3-v1.json、review-root仍.18.2/resume-v1/automation-r3、state-root仍r3/program-driver；先等待外部reviewer最终SHA稳定后一次后台启动，确认remaining实际消费从250k向前。已审profile不重新启动，后续阶段顺序不变，final依原科学开发门。尚待父确认实际remaining前进后退出LLM监督，本子不再改源码或追加验证/监控。
