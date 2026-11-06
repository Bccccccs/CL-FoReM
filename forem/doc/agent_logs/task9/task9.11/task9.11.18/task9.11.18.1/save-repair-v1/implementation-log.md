# 大检查点必要修复


2026-11-04T16:18:03.514767+08:00 · 必要大检查点短写修复active，父沿AGENTS明确授权排错/恢复。仅active BudgetFile.write写全与必要准入/失败预算承接，不改科学算法、奖励/观测/周期或丢失败消费。r2已250k/196后native restore损坏，原件全保；推荐GPT6.1sol/medium、Sonnet5.5/medium（大I/O序列化因果），实际未知。验证先短写假stream，再新CPU-only固定镜像真实>2GiB torch.save/load，证实才写通过。不重启旧CID或GPU，不跑全套前门；三文档递归/父共享、兄弟独审仍适用。

# r3必要大检查点写入修复交接

2026-11-04T16:30:38.227969+08:00 · Codex实施 · review，待父/独审delta接收和r3首次真实启动。推荐GPT6.1sol/medium、Sonnet5.5/medium（序列化、大写入边界与累计消费因果），实际后端型号/强度未知。父维护共享台账与总预算，兄弟独审负责有限IO替换及阶段放行，本子不自签科学PASS；递归三文档规则沿原节点。

事实与根因：r2已250000消费转移、24975update、196周期评估，physical env_actions250213，native profile restore失败。原profile与250k checkpoint各物理13.523GB，ZIP64声明central_offset21.608GB，独审确认至少缺8.08GB，不从actor伪恢复。实际training.py直接`from task9_lr.diagnostics import BudgetFile`，active类在src/task9_lr/diagnostics.py。旧write只调用一次unbuffered raw.write，未处理正短写。

实际CPU边界实证：[io-boundary-result](../../../../../../../results/task9/t9.11-CPU-large-write-20261104-v1/io-boundary-result.json)记torch2.7.1+cu128、device CPU、cudaFalse、/dev/nvidia空。真实storage2147549184B（2GiB+65536），旧raw.write请求2147549184却返回2147479552，旧torch.load同样notZIP；新active BudgetFile raw第一次仍同短count，但循环补齐，完整档2147550825B，torch.load全tensor每字节torch.equal通过。old/new物理差69632B恰等短写未完成部分。旧档Python zipfile.is_zipfile仍True不能替代torch native load完整性；本次未把其当成功。整个CPU实际tensor回环29.649s，rootwait31.508832s（嵌套不相加）。新CPU-only CID949bdba1d21fe5f5cade003dce901c2c18891c290440ce5307132471bb2339eb，固定image e674…，DeviceRequests空，准确停止后exited137/PID0、OOMKilledFalse，Started08:19:59.814Z→Finished08:21:36.589Z。原GPU容器未重启，未新增GPU/科学训练或评估。

最小实现：BudgetFile.write以memoryview.cast B取得字节数，reserve一次整个payload，再循环仅写剩余view；正短count继续，None/0/负/布尔/非整数/大于剩余count抛OSError，不能假成功；返回完整字节数。预算不因每次短写重复扣，失败保留完整预留。4项假stream边界rc0（含多次短写、一次预算、无进展、异常、空/多字节buffer）。实际CPU结果/原wait与前后source snapshots在本目录commands/cpu-real-large-write-v1，rc0原server终态已取得；源码改的active类由真实container__file__确认。

必要兼容/消费接线：独审IO-WRITE-REPAIR-PASS-v1仅批准diagnostics.py原SHA71197199…→55cdcc89…的write-only修复，原151列表其余150逐原manifest核同。m.validate_contract只对该path且exactold/new独审ref允许替换，不泛化跳scienceguard。resource-envelope-v2-r3绑定该IO原件和失败证据，历史eval1372、失败250k/physical250213/up24975/eval196全保留；有效未来仍9408周期+1184final=10592，不拿失败250k抵新3M，累计eval cap11964。b/m从该envelope精确读取历史base，新reader实际1372+196=1568，当前197回合拒绝。4项独立定向admission/配额测试rc0，含IO path/hash/150承诺反例和旧1176/11768回退拒绝。原150科学/算法/奖励/动作/观测/环境/种子/LR/各3M均不改；保存I/O变化明确说明，不再声称151全字节同。

当前一次冻结[freeze-program-r3-v1.json](freeze-program-r3-v1.json)，184源SHA `b8f3d63b4fb0846156fcfc72663008763a5346d85020daef9025d7f790154c05`，相对r2仅diagnostics.py/real_program.py/real_batch.py三必要文件改、181同，futurefinal/test_jobs/native full restore全部仍含于本冻结。协议[real-contract-program-r3-v1.json](real-contract-program-r3-v1.json)SHA `0bdcbda6c1b00e2b165653248925e1e2fc86d88938ee441045db2a7dceab3691`，run t9.11-real-program-20261104-r3，新namespace尚未由本子启动。未重跑G1/LON或全套前门。CPU2GiB回环不等21GB原生full checkpoint恢复证明；r3自身首250k会实际完整save/restore并更新成本。

外部driver不纳native artifact。旧r2driver原字节按既存SHA4df85fac…7e99a精确归档archived-r2-driver.py；当前driver从sealedprotocol固定native source并允许明确保failed r2消费的r3，actual配置preflight通过（external-driver-r3-preflight-v1.json），native源hash不漂移；旧4项控制面mock复用，不重复全套。r3首阶段仍由父先原native prepare→独审allocation→execute，再driver采用已在跑rootwait。**未测试/未宣称fresh driver自主初始化**，因为先创建out/program-driver会使native初始freeze初始化误认为out已存在；按父决定不为此改native额外逻辑。父首启动后以r3新protocol/state-root/automation-r3启动driver即可，STOP/--resume保原安全链语义。

尚待：独审delta接收/新初始budget/source refs、父首C4718启动与实际步数核；之后daemon继续八stage，科学开发验收未过不伪final PASS。所有原失败r1/r2、损坏文件、CPU测试旧/新文件及成本保留。
