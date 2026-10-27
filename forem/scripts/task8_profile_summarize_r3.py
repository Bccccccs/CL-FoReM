#!/usr/bin/env python3
"""Read preserved r3 profile originals; standard-library report, no simulation/tests."""
import csv
import hashlib
import json
import math
from pathlib import Path
from task8_profile_summarize import stats, gpu_csv

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'results/task8/t8-perf-opt-20261027'
OLD=ROOT/'results/task8/t8-perf-20261027'
LEDGER=ROOT/'logs/task8/t8-perf-opt-20261027/budget.json'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_text())
def close(a,b):return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-12)

def main():
    baseline=load(OLD/'summary-r2.json');plan=load(DATA/'r3-fixed-profile-jobs.json');ledger=load(LEDGER)
    # This is data aggregation only. Floating tolerances below reconstruct numpy
    # report percentiles with stdlib; the O1 tensor equivalence remains exact.
    if ledger['active'] is not None:assert ledger['active']['name'].startswith('r3-report-recompute')
    assert ledger['used_s']<=ledger['budget_s']==1500
    for p,expected in plan['hashes'].items():assert sha(ROOT.parent/p)==expected,p
    groups={};files=[]
    independent_path=ROOT/'results/task8/t8-phase2-20261027/r3-independent-opt-final.json'
    independent=load(independent_path) if independent_path.exists() else None
    for job in plan['jobs']:
        path=ROOT.parent/job['output'];d=load(path);files.append(path)
        assert d['status']=='pass' and d['completed_steps']==len(d['steps'])==20 and d['completed_warmup']==2
        assert d['guard']==dict(optimizer_constructed=0,backward_calls=0)
        assert sum(s['active'] for s in d['steps'])==d['transfers']
        assert sum(s['committed_substeps'] for s in d['steps'])>=d['transfers']
        assert close(sum(s['wall_s'] for s in d['steps']),d['measured_loop_s'])
        assert close(sum(s['sim_s'] for s in d['steps']),d['sim_committed_s'])
        assert close(d['transfers']/d['measured_loop_s'],d['transfers_per_s'])
        for label in ('environment_step','panorama_including_raycast','replay_consume_loop','drain_history','candidates','actor_inference'):
            assert d['timings'][label]['n']==20,label
        components={}
        for label,v in d['timings'].items():
            raw=d['timing_samples'][label];s=stats(raw['wall_s'])
            assert len(raw['wall_s'])==len(raw['cuda_event_s'])==v['n']
            assert all(close(s[k],v[k]) for k in s),(path,label)
            assert close(sum(raw['cuda_event_s']),v['cuda_event_sum_s'])
            components[label]=dict(**s,share_of_loop=s['sum_s']/d['measured_loop_s'],cuda_event_sum_s=v['cuda_event_sum_s'])
        resets=d['timings'].get('reset_factory_ended',{}).get('n',0)
        assert d['timings']['raycast']['n']==20+resets
        assert d['timings']['grid_update']['n']==20+resets
        row=next(c for c in ledger['commands'] if c['name']==job['name'])
        assert row['exit_code']==0 and row['command']==job['argv'][9:] and row['wall_s']<210
        monitor=path.with_name(path.stem+'-gpu.csv');files.append(monitor)
        key=f"{d['family']}_b{d['batch']}"
        g=dict(input=path.name,input_sha256=sha(path),family=d['family'],batch=d['batch'],unique_scene_count=d['unique_scene_count'],
            completed_warmup=2,completed_steps=20,guard=d['guard'],transfers=d['transfers'],measured_loop_s=d['measured_loop_s'],
            transfers_per_s=d['transfers_per_s'],seconds_per_transfer=d['measured_loop_s']/d['transfers'],
            sim_committed_s=d['sim_committed_s'],step_wall=stats([s['wall_s'] for s in d['steps']]),components=components,
            cold_timings=d['cold_timings'],cached_ended_reset_calls=resets,runtime=d['runtime'],
            devices={k:d[k] for k in ('actor_device','actor_dtype','state_device','scene_device','scene_dtype','replay_device')},
            actor_checkpoint=d['actor_checkpoint'],actor_sha256=d['actor_sha256'],versions=d['versions'],replay_capacity=d['replay_capacity'],
            capacity100k_replay_tensor_bytes=d['capacity100k_replay_tensor_bytes'],gpu_monitor=gpu_csv(monitor),
            script_wall_s=d['wall_s'],ledger_wall_s=row['wall_s'],source='SRC-1194')
        old=baseline['groups'].get(key)
        if old:
            olddocs=[load(OLD/f) for f in old['inputs']]
            overlaps=[];new_weighted_wall=0;old_wall=0;old_transfers=0
            for oldname,od in zip(old['inputs'],olddocs):
                n=od['completed_steps'];new_prefix=d['steps'][:n]
                keys=('iteration','active','committed_substeps','sim_s','failures','replay_size')
                match=all(all(a[k]==b[k] for k in keys) for a,b in zip(od['steps'],new_prefix))
                assert match,(key,oldname,'step metadata mismatch')
                new_weighted_wall+=sum(s['wall_s'] for s in new_prefix)
                old_wall+=od['measured_loop_s'];old_transfers+=od['transfers']
                overlaps.append(dict(old_input=oldname,n=n,metadata_fields=list(keys),metadata_exact=True))
                files.append(OLD/oldname)
            g['comparison_r2']=dict(r2_transfers=old['transfers'],r2_measured_loop_s=old['measured_loop_s'],r2_rate=old['transfers_per_s'],
                all20_window_throughput_ratio=g['transfers_per_s']/old['transfers_per_s'],
                r2_repeated_window_prefixes=overlaps,
                matched_prefix_weighted_new_seconds=new_weighted_wall,matched_prefix_weighted_old_seconds=old_wall,
                matched_prefix_weighted_transfers=old_transfers,matched_prefix_weighted_ratio=old_wall/new_weighted_wall,
                note='All20 ratio compares same transfers/wall metric, but r2 b256 windows restart repeated prefixes; r3 is one continuous20-step trajectory. Matched-prefix ratio reuses r3 prefix timing observations with r2 window weights; it is not additional independent measurements. Metadata equality does not by itself prove complete Transition equality; O1 supplies separate exact semantic checks.')
            if d['batch']==256:
                g['comparison_r2']['raycast_seconds_per_transfer_ratio']=(old['components']['raycast']['sum_s']/old['transfers'])/(components['raycast']['sum_s']/g['transfers'])
                g['comparison_r2']['raycast_scope']='All measured raycast calls, including cached reset rays when present; not a pure kernel matched-input benchmark.'
            else:g['comparison_r2']['raycast_scope']='Old b64 nested raycast distribution includes a cold reset, so no raycast speed ratio is claimed.'
        else:g['comparison_r2']=dict(available=False,note='No r2 semantic_b64 result; no speedup ratio can be computed.')
        groups[key]=g
    update_counts={str(k):{str(n):max(0,n//k-257//k) for n in (512,1000,1000000,3000000)} for k in (1,10)}
    framework=dict(status='STATIC_FRAMEWORK_PENDING_C_SMOKE_NOT_A_COST_ESTIMATE',units='seconds, transfers, updates',
        update_rule_source='task8_lower/sac.py::update_due and training.py::consume_transition; test old replay before insertion, batch_size256',
        updates_formula='U_k(N)=max(0,floor(N/k)-floor(257/k)); resumed interval (a,b]: U_k(b)-U_k(a)',
        update_counts=update_counts,smoke_density=dict(B0=743/1000,B3=75/1000),formal_3M_density=dict(B0=2999743/3000000,B3=299975/3000000),
        steady_loop_formula='c_steady_g = c_observed_loop_g + (rho_formal_g-rho_observed_g)*c_update_g + delta_replay_fill_g + delta_state_distribution_g',
        total_formula='T_g(N) = T_start_g + N*c_observed_loop_g + (U_k(N)-N*rho_observed_g)*c_update_g + Delta_replay_state_g(N) + R_g(N)*c_random_reset_g + 3000*c_diagnostic_g + 12*c_eval196_g + sum(j=1..12)c_full_checkpoint_g(250000*j,100000) + c_final_checkpoint_g(N,100000) + J_g*c_restore_full_g + T_uninstrumented_logging_g + T_contention_g',
        definitions=dict(c_observed_loop='Smoke top-level training loop cost per consumed transfer, after separately excluding cold startup/restore, random resets, diagnostics, checkpoint and validation. If no reliable subtraction is available, report raw CLI throughput as a scenario and leave this term unknown.',
            c_update='Measured incremental sample+SAC update cost for the same group/path. Current CLI consume_transition timer combines push/set_transfer/update/sample, so c_update is NOT separately identified by that timer alone; do not transplant old task7 timing as a new measurement.',
            c_eval196='One completed100 validation+96 transfer pass under the same policy/group, including scene construction/sampling. Existing evaluation JSON gives a bundled196 wall time, not separate100/96 timing.',
            Delta_replay_state='Unmeasured correction for replay occupancy/sample state distribution and scene/planner cache growth; retain explicit uncertainty, do not set to zero for readiness.',
            R='Actual policy-dependent number of ended-episode resets overN, not cached-factory resets measured here.',
            checkpoints='Formal loop saves12 periodic full checkpoints at250k..3M, plus one final full checkpoint. Actor/meta copies and CPU snapshot work are included. Recovery countJ is explicit scenario, zero only when expressly assuming uninterrupted execution.'),
        raw_cli_extraction='Use primary512 summary wall plus resumed diagnostic.elapsed_s through1000 for the existing reported pre-evaluation metric; this includes primary final checkpoint, cold reset, model creation and load/restore, so it cannot directly become steady long-run transfer cost. Use CLI outer wall for full worker/global accounting; reconcile starts and persisted previous_wall_s without double counting.',
        full_checkpoint_warning='Replay.state_dict serializes [:size] CPU clones. Smoke checkpoints at512/1000 contain only512/1000 valid rows despite100k GPU capacity; formal first250k checkpoint contains100k rows. Their save/load latency, payload, host-RAM and I/O cost remain unmeasured. Do not multiply or fill with0 as measured full-buffer cost.',
        replay_row_bytes=98925,replay_valid_payload_bytes=dict(smoke512=98925*512,smoke1000=98925*1000,formal100000=98925*100000),
        pending=['C real CLI B0/B3 actual updates/active counters/throughput/optimizer devices/peak GPU and complete196 evaluation/time',
            'full100k-valid-row checkpoint and restore cost; tiny smoke payload is insufficient',
            'steady incremental group-specific update/sample cost needed to correct smoke update density',
            'formal random reset frequency/cost, trained policy state distribution and scene/planner cache growth',
            'four-worker GPU/storage/CPU contention and periodic logging/checkpoint bounds'],
        source='SRC-1194; code-derived arithmetic, not experimental measurements or additional-run authorization')
    for p in (OLD/'summary-r2.json',DATA/'r3-fixed-profile-jobs.json',ROOT/'src/task8_sim/scene.py',ROOT/'scripts/task8_profile_lower.py',ROOT/'src/task8_lower/training.py',ROOT/'src/task8_lower/sac.py',ROOT/'src/task8_lower/replay.py',ROOT/'src/task7_lower/replay.py',Path(__file__)):files.append(p)
    result=dict(status='O1_O4_PASS_P5_PENDING' if independent and independent.get('O4')=='PASS' else 'O3_PROFILE_ORIGINALS_RECOMPUTED_P5_PENDING',source='SRC-1194',actual_roles=dict(analysis='gpt-6.1-sol/high, parent explicitly dispatched',fixed_execution='gpt-6.1-terra/low per fixed execution log',independent_review=dict(path=str(independent_path.relative_to(ROOT)),status=independent.get('status'),reviewer=independent.get('reviewer'),model=independent.get('model')) if independent else 'pending parent record'),groups=groups,cost_framework=framework,
        budget_snapshot_before_report=dict(budget_s=ledger['budget_s'],used_s=ledger['used_s'],remaining_s=ledger['budget_s']-ledger['used_s'],active_command=ledger['active']),
        artifact_sha256={str(p.relative_to(ROOT)):sha(p) for p in files},
        limits=['Finite64 cube/24 semantic cached accepted episodes, not formalcube-export-v2 random training distribution.',
            'Frozen actor, no optimizer/backward; replay1024 using task7 replay kernels, not actual B0/B3 losses/diagnostic metadata or100k-long-run state.',
            'Warmup2 and20 complete contiguous r3 steps; cold reset isolated. Semantic20 steps include cached ended resets, making raycast/grid call counts exceed20 legitimately.',
            'Loop wall includes sync/instrumentation, per-transfer replay/audit; excludes process startup, cold reset and per-step summary JSON flush. Nested labels overlap and cannot be summed.',
            'CUDA event intervals include CPU/Python stream idle and do not equal active GPU kernel time. CSV is1Hz whole-command monitoring, including cold/warmup.',
            'No independent r3 repetition; matched-prefix weights reuse measured samples, no confidence interval or worst-case latency bound.',
            'O3 throughput gains alone cannot settle real training48h or four-worker memory gates. P5 requires C smoke and unresolved full-replay costs.'])
    (DATA/'summary-r3.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# task8.9.1.1 r3 — 森林raycast固定负载性能','', '四组原件均20完整post-warmup步、warmup2、guard0；只读复核及推导依据[SRC-1194](../../../doc/SOURCES.md#src-1194)，固定Terra执行[SRC-1193](../../../doc/SOURCES.md#src-1193)。全部raw分项n/sum/p50/p95/max及CUDA events累计、逐步transfer/wall/sim和已复算，机读细节见[summary-r3.json](summary-r3.json)。本汇总没有新测试/profile/训练。','', '|负载|场景|转移/测量秒|转移/s|相对R2整体吞吐|step p50/p95/max(s)|allocated/reserved峰值GiB|','|---|---:|---|---:|---|---|---|']
    for key,g in groups.items():
        c=g['comparison_r2'];ratio=f"{c['all20_window_throughput_ratio']:.3f}×" if 'all20_window_throughput_ratio' in c else '无旧基准'
        s=g['step_wall'];r=g['runtime'];lines.append(f"|{key}|{g['unique_scene_count']}|{g['transfers']}/{g['measured_loop_s']:.6f}|{g['transfers_per_s']:.6f}|{ratio}|{s['p50_s']:.4f}/{s['p95_s']:.4f}/{s['max_s']:.4f}|{r['peak_gpu_allocated_bytes']/2**30:.3f}/{r['peak_gpu_reserved_bytes']/2**30:.3f}|")
    lines+=['', 'R2 cube64同为连续20步；R2 cube256是10+10重复前缀，semantic256是8+6+6重复前缀，R3各连续20步。以上256倍数是相同“有效转移/测量loop wall”口径的完整窗口比，不能称20步逐项配对因果估计。语义R3为5074转移，旧5119；R3发生4次缓存factory复位，旧重复窗口尚未进入同样后段。semantic64没有R2基准，不计算提速。','', '公共前缀元数据（iteration/active/committed/sim/failure/replay size）与R2每窗精确一致；按R2窗口长度给R3前缀重复加权，可比时长比为：']
    for key,g in groups.items():
        c=g['comparison_r2']
        if 'matched_prefix_weighted_ratio' in c:lines.append(f"- {key}: {c['matched_prefix_weighted_ratio']:.3f}×（旧{c['matched_prefix_weighted_old_seconds']:.6f}s / 新前缀加权{c['matched_prefix_weighted_new_seconds']:.6f}s）。")
    lines+=['', '加权只复用原有R3测量，无新增独立样本或置信区间；元数据相等不代替O1完整Transition等价。64→256吞吐cube与semantic分别为以下实测比：']
    for family in ('cube','semantic'):lines.append(f"- {family}: {groups[family+'_b256']['transfers_per_s']/groups[family+'_b64']['transfers_per_s']:.3f}×；环境数4×并不等于吞吐4×。")
    labels=['environment_step','raycast','panorama_including_raycast','collision','IK_solve_world','grid_update','candidates','observation_build','replay_consume_loop','actor_inference','interaction_ledger','reset_factory_ended']
    for key,g in groups.items():
        lines+=['',f"## {key} 分项",'', '|分项|n|总秒/loop占比|p50/p95/max秒|','|---|---:|---|---|']
        for label in labels:
            c=g['components'].get(label)
            if c:lines.append(f"|{label}|{c['n']}|{c['sum_s']:.6f}/{c['share_of_loop']:.2%}|{c['p50_s']:.6f}/{c['p95_s']:.6f}/{c['max_s']:.6f}|")
        lines.append(f"\n冷reset单列；测量期cached ended-reset调用{g['cached_ended_reset_calls']}次，raycast {g['components']['raycast']['n']}次，全部属于20完整loop。嵌套分项相互包含，不能相加。")
    lines+=['', '## 设备、内存与限制','', 'forem-dev、物理GPU0→cuda:0；torch2.7.1+cu128/CUDA12.8，冻结actor/Core state/scene/replay均CUDA float32，intra2/inter64，CPU affinity0–63；完整runtime与1Hz全命令CSV分布见JSON。GPU事件含Python控制/流空闲，不是内核active时间。CSV含冷启动与warmup，不能解释为测量20步的利用率。峰值只对应冻结actor+replay1024，不认证正式SAC/100k有效回放/完整地图缓存或四worker显存。','', '立方体256 raycast占比下降后的其他分项仍保留：本次不实施碰撞/replay/reset优化。固定64/24scene轮转，不代表正式10000图分布或训练收益；测量同步/审计写盘等口径与正式CLI不同。R2超时与冷样本污染原件保留，本次不重写旧验收。','', '## P5静态成本框架（待C smoke，不能据此判48h）','', '`U_k(N)=max(0,floor(N/k)-floor(257/k))`，因为old replay在插入前需size>256；B0 k1，B3 k10。1000转移实际更新数应为743/75（初512为255/26，恢复后488转移新增488/49），3M应为2,999,743/299,975；warmup1000只替换动作，不关闭这些更新。[SRC-1194](../../../doc/SOURCES.md#src-1194)','', '初1000的更新密度0.743/0.075低于正式3M约0.999914/0.099992。不能把smoke原始吞吐直接乘3M而忽略密度；也不能把profile每转移无条件sample加旧SAC成本当新B3成本。分组修正：','', '`c_steady_g = c_observed_loop_g + (rho_formal_g-rho_observed_g)*c_update_g + delta_replay_fill_g + delta_state_distribution_g`。`c_update_g`须为同组实际增量sample+SAC时间；现有consume_transition计时还含push/set_transfer，单凭该计时不能识别独立更新成本。未知时保留符号，不能代入旧task7均值冒充新测量。','', '`T_g(N) = T_start_g + N*c_observed_loop_g + (U_k(N)-N*rho_observed_g)*c_update_g + Delta_replay_state_g(N) + R_g(N)*c_random_reset_g + 3000*c_diagnostic_g + 12*c_eval196_g + Σ(j1..12)c_full_checkpoint_g(250000*j,100000) + c_final_checkpoint_g(N,100000) + J_g*c_restore_full_g + T_logging_g + T_contention_g`（N3M，单位秒）。观测loop成本必须先剥离cold/reset/diagnostic/save/eval，无法剥离时只报包含这些项的原始CLI情景，不当稳态值。','', 'C smoke的既定训练到1000口径是primary summary wall＋恢复CLI的1000 diagnostic.elapsed_s，含初始构建/reset、512保存、恢复/load、诊断；需要与外层CLI wall分别报告，不能当稳态loop。100验证＋96迁移评估仅JSON合并196的wall可识别，按12次完整周期计；没有独立100/96计时就不伪造拆分。正式每250k保存一次、共12次，结束另保存final一次，故13次完整保存；恢复J为明示情景。','', '关键缺项：Replay.state_dict只序列化[:size]，smoke512/1000只保存512/1000有效行，尽管GPU已分配100k容量。每行98,925B（含task8元数据），1000有效行98,925,000B，正式100k行9,892,500,000B，仅回放payload。512/1000保存/加载实测不能验收满回放CP/restore时延，也不能可靠线性放大为实际成本，更不能填0。正式随机reset频率、训练后状态分布、scene/planner缓存增长和四worker争用同样未知。','', '不同实施者Sol/high的r3-independent-opt-final.json已判O3固定负载PASS、O4 PASS（SRC1198由父续记）；本汇总与独立原件数字一致。优化验收仅涉及本节点，P5仍待smoke及未解成本项，不启动3M。来源草稿统一交父，推荐Sol/Sonnet5.5 high作成本归因与终审、固定步骤Terra low。']
    (DATA/'summary-r3.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(status=result['status'],groups={k:dict(rate=g['transfers_per_s'],ratio=g['comparison_r2'].get('all20_window_throughput_ratio'),prefix_ratio=g['comparison_r2'].get('matched_prefix_weighted_ratio')) for k,g in groups.items()})))

if __name__=='__main__':main()
