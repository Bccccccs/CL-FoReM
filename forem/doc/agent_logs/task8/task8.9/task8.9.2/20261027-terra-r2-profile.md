# task8.9.2 B 24图 profile 固定执行

负责人 Terra，实际 gpt-6.1-terra / low。父授权仅执行 Sol 固定 profile 命令，不执行 build；推荐 Codex GPT6.1sol / low、Claude Sonnet5.5 / low，固定步骤无需特殊推理。

执行前账本 active=null、36.5121836476028/1800s；脚本 SHA256 a6055e44be7fd5ffb846596ef2971839c5849f8130960b37537f5dda582bebb7，与交接一致；配置 SHA256 501208cf26e3e4b3a851e42a94a9db39bb5467ede0932ff251e891c11b0d06a0。执行交接中固定 `sg docker ... --mode profile --config config/task8/pool_s3_v2.json --budget-limit 1800 --timeout 100`，退出码0，账本本次6.726704303175211s、累计43.23888795077801/1800s，active=null。

原件 `forem/results/task8/t8-pool-20261027/cube-pool-v2/profile-report.json`：count24，wall_s 6.722011715173721；6张先导缓存、18张新增，18/wall=2.6777698050374217图/秒，不能用报告的24/wall视为新增吞吐。generator SHA与脚本一致；source index SHA 95976a0767b5bcb89a550c9602d68b60cbcd5813cad582433859c31bf6330109 与实际一致。24个records均 production_target_equal=true、每盒target计数正；逐文件核PCD/侧车/源JSON SHA、PCD点数及实际坐标下界含上界不含均无错误。此检查未重算几何，须 Sol 对原件复核，不构成全池验收。

宿主首次只读检查因无 numpy 退出1，未执行数值核查；随后用Python标准库实际检查24图通过。未运行全量build/audit/finalize。
