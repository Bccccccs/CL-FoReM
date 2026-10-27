#!/usr/bin/env python3
"""Recompute task8.9.1 r2 report from preserved profile JSON; CPU standard library only."""
import csv
import hashlib
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'results/task8/t8-perf-20261027'
LEDGER=ROOT/'logs/task8/t8-perf-20261027/budget.json'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((DATA/name).read_text())
def quantile(values,q):
    v=sorted(values);a=(len(v)-1)*q;i=int(a);j=min(i+1,len(v)-1)
    return v[i]+(v[j]-v[i])*(a-i)
def stats(values):return dict(n=len(values),sum_s=sum(values),p50_s=quantile(values,.5),p95_s=quantile(values,.95),max_s=max(values))
def gpu_csv(path):
    rows=[]
    for row in csv.DictReader(path.open()):
        try:rows.append({k.strip():float(v) for k,v in row.items() if k.strip()!='timestamp'})
        except (ValueError,TypeError):continue
    return dict(n=len(rows),scope='1Hz whole-command samples, including startup/cold/warmup; not only measured steps',metrics={k:dict(p50=quantile([r[k] for r in rows],.5),p95=quantile([r[k] for r in rows],.95),max=max(r[k] for r in rows)) for k in rows[0]}) if rows else dict(n=0)
def group(names,*,raw):
    docs=[read(n) for n in names]
    for d in docs:
        assert d['completed_warmup']==2 and d['guard']==dict(optimizer_constructed=0,backward_calls=0)
        assert d['completed_steps']==len(d['steps'])
        assert sum(s['active'] for s in d['steps'])==d['transfers']
        assert abs(sum(s['wall_s'] for s in d['steps'])-d['measured_loop_s'])<1e-8
        if raw:
            assert d['measurement_protocol']=='r2-independent-windows-v1'
            for k in ['environment_step','panorama_including_raycast','raycast','replay_consume_loop','drain_history']:
                assert len(d['timing_samples'][k]['wall_s'])==d['completed_steps']
            for k,v in d['timings'].items():
                reconstructed=stats(d['timing_samples'][k]['wall_s'])
                assert all(math.isclose(reconstructed[key],v[key],rel_tol=1e-12,abs_tol=1e-12) for key in ['n','sum_s','p50_s','p95_s','max_s'])
    steps=[s for d in docs for s in d['steps']];total=sum(d['measured_loop_s'] for d in docs);transfers=sum(d['transfers'] for d in docs)
    components={}
    if raw:
        keys=set().union(*(d['timing_samples'] for d in docs))
        for key in sorted(keys):
            values=[x for d in docs for x in d['timing_samples'].get(key,{}).get('wall_s',[])]
            components[key]=dict(**stats(values),share_of_loop=sum(values)/total,note='Nested labels overlap; never sum all shares.')
    else:
        components=docs[0]['timings'].copy()
        for k,v in components.items():v['share_of_loop']=v['sum_s']/total
    clean=['candidates','observation','actor_preprocess','actor_inference','interaction_ledger','environment_step','replay_consume_loop','drain_history']
    result=dict(inputs=names,family=docs[0]['family'],batch=docs[0]['batch'],unique_scene_count=docs[0]['unique_scene_count'],warmup_per_window=2,windows=[dict(input=n,status=d['status'],completed_steps=d['completed_steps'],measured_loop_s=d['measured_loop_s'],transfers=d['transfers']) for n,d in zip(names,docs)],step_wall=stats([s['wall_s'] for s in steps]),transfers=transfers,measured_loop_s=total,transfers_per_s=transfers/total,seconds_per_transfer=total/transfers,window_seconds_per_transfer=[d['measured_loop_s']/d['transfers'] for d in docs],sim_committed_s=sum(d['sim_committed_s'] for d in docs),components=components,top_level_ranking=sorted([dict(label=k,sum_s=components[k]['sum_s'],share=components[k]['share_of_loop']) for k in clean if k in components],key=lambda x:-x['sum_s']),peak_gpu_allocated_bytes=max(d['runtime']['peak_gpu_allocated_bytes'] for d in docs),peak_gpu_reserved_bytes=max(d['runtime']['peak_gpu_reserved_bytes'] for d in docs),devices=[{k:d.get(k) for k in ['actor_device','actor_dtype','state_device','scene_device','scene_dtype','replay_device']} for d in docs],runtime=docs[0]['runtime'],gpu_monitors={n.replace('.json','-gpu.csv'):gpu_csv(DATA/n.replace('.json','-gpu.csv')) for n in names},cold_reset_samples_s=[d.get('cold_timings',d['timings']).get('reset_factory_cold',{}).get('sum_s') for d in docs],cold_nested_isolated=raw,nested_distribution_limitation=None if raw else 'Original IK/collision/raycast/Grid nested summaries include one cold-reset sample. Environment_step/panorama/actor/top-level per-step distributions are post-warmup20. Original per-call raw nested samples absent; cannot retrospectively remove cold p50/p95/max. Do not treat these nested distributions as clean P2 acceptance.')
    assert result['step_wall']['n']==20
    return result

def main():
    groups={f'cube_b{b}':group([f'cube-run-b{b}.json'],raw=False) for b in [1,16,64]}
    groups['cube_b256']=group([f'cube-run-b256-r2-{w}.json' for w in ['w1','w2']],raw=True)
    groups['semantic_b256']=group([f'semantic-run-b256-r2-{w}.json' for w in ['w1','w3','w4']],raw=True)
    ledger=json.loads(LEDGER.read_text());assert ledger['active'] is None and ledger['used_s']<=1800 and all(r['wall_s']<=300 for r in ledger['commands'])
    old_update=27.9898/2047
    models={}
    for key in ['cube_b256','semantic_b256']:
        g=groups[key];c=g['seconds_per_transfer'];low=min(g['window_seconds_per_transfer']);high=max(g['window_seconds_per_transfer'])
        models[key]=dict(profile_seconds_per_transfer=c,profile_window_range_s=[low,high],old_sac_mean_seconds_per_update=old_update,conditional_base_hours={str(u):{str(n):dict(point=(n*c+u*max(0,n-257)*old_update)/3600,window_scenario_range=[(n*low+u*max(0,n-257)*old_update)/3600,(n*high+u*max(0,n-257)*old_update)/3600]) for n in [1000000,3000000]} for u in [1.,.1]},raycast_share=g['components']['raycast']['share_of_loop'],amdahl_scenario_speedups={str(s):1/(1-g['components']['raycast']['share_of_loop']+g['components']['raycast']['share_of_loop']/s) for s in [2,4]},scope='Conditional arithmetic only, repeated finite scenes, no measured SAC update. Window ranges are workload timing scenarios, not confidence intervals, upper bounds or full training estimates.')
    inputs=sorted(set(n for g in groups.values() for n in g['inputs'])|{'cube-run-b256.json','cube-prepare.json','semantic-prepare.json'})
    hashes={str((DATA/n).relative_to(ROOT)):sha(DATA/n) for n in inputs}
    for p in [LEDGER,ROOT/'scripts/task8_profile_lower.py',ROOT/'src/task8_sim/profile_lower.py',ROOT/'src/task8_sim/profile_budget.py',Path(__file__)]:hashes[str(p.relative_to(ROOT))]=sha(p)
    result=dict(status='review_NOT_READY',source='SRC-1163',actual_roles=dict(implementation='gpt-6.1-sol/high, parent dispatched; underlying service not independently verified',fixed_execution='gpt-6.1-terra/low per parent handoff, executor logs authoritative',independent_review='pending different Sol/high'),groups=groups,budget=dict(budget_s=ledger['budget_s'],used_s=ledger['used_s'],remaining_s=ledger['budget_s']-ledger['used_s'],active=ledger['active'],commands=ledger['commands']),preserved_failures=[dict(input=n,status=read(n)['status'],completed_steps=read(n)['completed_steps'],note=note) for n,note in [('cube-run-b256.json','Original17 is not merged: missing raw samples, cold/partial nested contamination; failure retained.'),('semantic-run-b256-r2-w1.json','Command timeout retained; its8 completed steps are eligible after exact count/total/raw rollback checks; merged with6+6.')]],cost_models=models,cost_formula='T(N,U)=T_cold + N*c_profile + U*max(0,N-257)*c_SAC_old + R(N)*c_random_reset + Kcp(N)*c_checkpoint + Kv(N)*c_validation100 + Kt(N)*c_transfer96 + T_logging + T_contention',cost_inputs=dict(old_sac='task7.18.3 eager-sync27.9898s/2047 updates; old geometry/path not task8 update benchmark',known_checkpoint_reference_s=10.1212,checkpoint_reference_scope='Historical task7 short-run checkpoint only, not formal100k task8 full state. Not inserted as new measured cost.',evaluation_protocol='N3M,250k interval =>12 scheduled100+96 eval cycles (not measured); number of extra/final/checkpoint copies depends on final entry implementation. Keep Kcp/Kv/Kt explicit.'),unmeasured=['Formal random episode reset frequency and cost under trained policies; no ended reset in chosen short windows.', 'Formal task8 full196 episode evaluation; first-step/partial tests cannot estimate complete episodes.', 'Formal100k full checkpoint/restore size, serialization latency and periodic logging.', 'SAC/optimizer/critic/target memory and new B0/B3 training E2E; GPU profile is frozen actor only.', 'New cube-export-v2 formal-map subset performance; optional supplement omitted per parent budget instruction.', 'Resource contention between four actual training workers.'],replay_capacity_projection=dict(profile_capacity=1024,formal_capacity=100000,formal_tensor_bytes=9891600000,formula='profile replay tensor bytes *100000/1024; same74dim float32 field layout; excludes optimizer/model/Grid/scenes/planners/allocator'),gates=dict(P1='Measured frozen actor/Core/scene/replay CUDA0 float32 and process monitor; no optimizer permitted. Formal-training memory not certified.',P2='All requested workloads aggregate20 complete post-warmup steps; STRICT PARTIAL for original b1/16/64 nested cold-contaminated distributions. Independent judgment pending.',P3='Measured cube1/16/64/256 and semantic256;256 windows repeat initial trajectories; no256 unique-scene claim.',P4='Profile-backed hotspot ranking and conditional optimization scenarios only; no optimization implemented or benefit proven.',P5='Conditional model and symbolic missing periodic terms delivered; full per-run timing/48h gate NOT_READY. B0 cube UTD1 conditional base57.725h>48h, not a new training measurement.',P6='All ledger commands<=300s,total<=1800,guards0; two rc124 preserved; independent review pending.'),limits=['Instrumented loop wall includes synchronize/events/audit/fsync and per-transfer replay; excludes cold startup and per-step summary flush.', 'CUDA event elapsed includes CPU launch/control idle; not sum of GPU kernel active time.', 'Independent windows restart same cached episodes and seed4718; repeated timing observations are not independent episode coverage or continuous training.', 'Capacity1024/reused episodes/no warmup random policy/no optimizer differ from formal training. UTD0.1 projection retains UTD1 no-op replay consumption and is conditional.', 'Do not claim formal B0 real runtime>48h from transplanted old update cost; current readiness projection fails, actual smoke must still be reported.'],artifact_sha256=hashes)
    (DATA/'summary-r2.json').write_text(json.dumps(result,indent=2)+'\n')
    lines=['# task8.9.1 r2 — profile与条件成本（review / NOT_READY）','', '所有数值依据[SRC-1163](../../../doc/SOURCES.md#src-1163)；原始计数、分布、命令、hash见[summary-r2.json](summary-r2.json)。独立Sol验收尚待进行。','', '|负载|完整post-warmup步数|场景去重数|转移/秒|step p50/p95/max(s)|allocated/reserved峰值GiB|','|---|---:|---:|---:|---|---|']
    for key,g in groups.items():
        s=g['step_wall'];lines.append(f"|{key}|{s['n']}|{g['unique_scene_count']}|{g['transfers_per_s']:.4f}|{s['p50_s']:.4f}/{s['p95_s']:.4f}/{s['max_s']:.4f}|{g['peak_gpu_allocated_bytes']/2**30:.3f}/{g['peak_gpu_reserved_bytes']/2**30:.3f}|")
    lines+=['','256 cube为两个10步窗口，semantic为超时原件内8完整步＋两个6步窗口；每窗独立预热2。各自重启同缓存与seed，轨迹重复，不冒称连续20步/独立episode。原cube256 rc124与semantic256 rc124均保留；只对完整step原始样本合并。','', '原batch1/16/64的environment_step/panorama/actor等20步分布干净；IK/collision/raycast/Grid部分嵌套统计混入一次cold reset，不能追溯删除其分位数，严格P2部分未满足。不重跑已过档。新256窗口已隔离cold且回滚不完整step。','', '|256热点|cube总秒/loop占比|semantic总秒/loop占比|','|---|---|---|']
    for key in ['environment_step','raycast','panorama_including_raycast','collision','IK_solve_world','grid_update','candidates','observation_build','replay_consume_loop','actor_inference','interaction_ledger']:
        cs=groups['cube_b256']['components'][key];ss=groups['semantic_b256']['components'][key];lines.append(f"|{key}|{cs['sum_s']:.4f}/{cs['share_of_loop']:.2%}|{ss['sum_s']:.4f}/{ss['share_of_loop']:.2%}|")
    lines+=['','上述嵌套项相互包含，不能求和；按顶层environment_step最重，内部raycast最重。CPU/GPU数据已在CUDA，GPU利用率不等于吞吐成因证据。','', '只出优化方案：','', '1. 首先评估SceneBatch.raycast逐环境循环与VoxelScene.raycast分块/while遍历的跨场景批量组织，位置scene.py:319/213；cube每环境扫描p50从batch16约0.05091s、64约0.05049s、256约0.05098s，近线性；能否减少launch/host等待需额外验证，当前不实施。固定输入下CPU64/GPU32分别比较距离（含inf、擦边、边界）、碰撞和完整Transition逐元素一致；禁改h、几何、量程、step、mask或RNG。','2. scene缓存只解决冷读取/构建，不假设加速已缓存step。prepare原64/24图asset+scene累计14.7662/23.3086s、几何常驻93,082,488/35,263,368B；scene变更/hash/device/dtype必须成为键，不能缓存过期几何。当前短窗已复用缓存，因此不能再次从step成本里扣缓存收益。','3. collision跨场景批处理与reset数据准备并行仅作次级候选，当前collision占比数个百分点；即使完全消除collision，cube/semantic整体理论上限仅约1.031/1.025倍，不是可实现承诺。随机reset频率未测，无法估计长期收益；当前已缓存窗口从scene缓存候选可额外扣减的稳态成本为0。先核形状/闭接触/自碰撞/partial reset与RNG及账本顺序；CPU线程当前intra2/inter64，不因nproc2就当两核硬限，不凭增加Python线程假定收益。','4. replay按转移的串行插入/采样约1–2%量级；即使完全消除当前消费loop，cube/semantic整体理论上限仅约1.017/1.010倍。批量化必须保留update-before-insert、逐转移RNG、索引、可恢复cursor与UTD顺序；收益上限小于射线项，不优先动科学合同。','', '理论Amdahl情景（只加速raycast，其余不变，不是收益承诺）：','']
    for key,m in models.items():lines.append(f"- {key}:raycast占{m['raycast_share']:.2%}，假设其2×/4×则总加速{m['amdahl_scenario_speedups']['2']:.3f}×/{m['amdahl_scenario_speedups']['4']:.3f}×。未实现/未验收。")
    lines+=['','条件成本公式（秒）：`'+result['cost_formula']+'`。N=转移数，U=1或0.1；c_profile按测量loop/有效转移，c_SAC_old=27.9898/2047秒/update，来自旧task7.18.3。R为随机episode复位次数，Kcp/Kv/Kt分别为完整保存、100图验证与96episode迁移评估次数。3M/250k有12次周期评估，但完整实际episode/保存成本尚未测，不填0。','', '|有限负载|每百万基础小时 UTD1 / UTD0.1|3M基础小时 UTD1 / UTD0.1|','|---|---|---|']
    for key,m in models.items():
        h=m['conditional_base_hours'];lines.append(f"|{key}|{h['1.0']['1000000']['point']:.3f}/{h['0.1']['1000000']['point']:.3f}|{h['1.0']['3000000']['point']:.3f}/{h['0.1']['3000000']['point']:.3f}|")
    lines+=['','这些是有限固定输入＋旧SAC代入的条件基础项，**不是实际B0/B3新长训实测，也不是工期上界**。原task7正式48.7 transfer/s（约5.704h/M）与本轮无更新、含仪器同步且不含随机reset/周期保存的口径不同；只作背景，不能计算严格性能回退倍数。cube B0基础57.725h已过48h投影门；B3基础47.471h也不能容纳未知周期成本保证。语义池是迁移评估，不拿semantic负载替立方体正式训练分布。','', f"账本{ledger['used_s']:.9f}/1800s，余{1800-ledger['used_s']:.9f}s，active=null。不再增加GPU profile，不补正式导出池子集；未实施任何性能优化。",'', '设备：forem-dev、物理GPU0→cuda:0，torch2.7.1+cu128/CUDA12.8；冻结actor、Core state、scene和replay实际CUDA float32。所有guard optimizer_constructed=backward_calls=0。完整GPU CSV与实际runtime/CPU affinity/线程在JSON；只监控1Hz全命令，含cold/warmup，不能当GPU内核利用率。正式100k replay张量推导9,891,600,000B，不含SAC/optimizer/target或正式scene池，不能据此认证四卡显存。','', '当前门：P1冻结路径设备已测；P2数量齐但部分旧嵌套分布受冷启动污染；P3有限负载扩展性已测；P4方案和条件收益情景已给但未实施；P5完整工期未成立；P6guard/预算通过，独立Sol验收待办。整体review，NOT_READY。']
    (DATA/'summary-r2.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(groups={k:dict(n=v['step_wall']['n'],transfers_per_s=v['transfers_per_s']) for k,v in groups.items()},budget=result['budget']['used_s'],cost=models)))

if __name__=='__main__':main()
