#!/usr/bin/env python3
"""Recompute task7.6 claims from raw artifacts and independent URDF FK."""
from pathlib import Path
import json,time,numpy as np,torch
from bench_task7_ik import Model,residual,stats,dump,sha
ROOT=Path('/root/mm_husky_ws');BASE=ROOT/'results/task7';OUT=BASE/'t7.6-bench-20261020-r9'
def main():
    start=time.perf_counter();torch.set_num_threads(2);OUT.mkdir(parents=True,exist_ok=True)
    folder=lambda k:BASE/('t7.6-bench-20261020-r'+str(k))
    m=Model(folder(1)/'model.urdf');inputs=np.load(folder(1)/'inputs.npz');summ=json.loads((folder(1)/'consistency.json').read_text());checkcount=0
    p,r=residual(torch.tensor(m.fk(inputs['random_q'])),__import__('bench_task7_ik').fk(torch.tensor(inputs['random_q'])))
    for key,data in [('fk_position_m',p.numpy()),('fk_rotation_rad',r.numpy())]:
        assert np.allclose(list(stats(data).values()),list(summ[key].values()),atol=1e-14,rtol=1e-6);checkcount+=1
    for row in summ['thresholds']:
        key=str(row['position_tol_m']);a=np.load(folder(1)/('consistency_'+row['method']+'_'+key+'.npz'))
        assert int(a['ok'].sum())==row['ok'];assert (a['position'][a['ok']]<=row['position_tol_m']).all();assert (a['rotation'][a['ok']]<=row['rotation_tol_rad']).all();checkcount+=1
    for k in [2,3,4,5]:
        rows=json.loads((folder(k)/'timing.json').read_text());meta=json.loads((folder(k)/'metadata.json').read_text())
        assert sha(ROOT/'scripts/bench_task7_ik.py')==meta['script_sha256']
        for row in rows:
            assert row['wall_stats_s']==stats(row['wall_s']);assert row['cpu_stats_s']==stats(row['process_cpu_s'])
            if row['cuda_event_s']:assert row['cuda_stats_s']==stats(row['cuda_event_s'])
            assert len(row['wall_s'])>0;checkcount+=1
        for p in folder(k).glob('path_*.npz'):
            a=np.load(p); assert np.allclose(a['q_mask'],a['q_compact'],atol=1e-10 if meta['argv'][meta['argv'].index('--dtype')+1]=='float64' else 1e-5);checkcount+=1
    bio=np.load(folder(8)/'bioik.npz');pe,re=residual(torch.tensor(m.fk(bio['q'])),torch.tensor(inputs['target'][bio['indices']]))
    assert np.array_equal(pe.numpy(),bio['position']);assert np.array_equal(re.numpy(),bio['rotation']);boolok=bio['raw_code']==1
    reasons={}
    for tol in [1e-7,1e-5,1e-3]:
        badpos=bio['position']>tol;badrot=bio['rotation']>tol;badlim=~bio['limits_ok'];ok=boolok&~badpos&~badrot&~badlim
        reasons[str(tol)]={'raw_success':int(boolok.sum()),'accepted':int(ok.sum()),'bad_position_among_raw_success':int((boolok&badpos).sum()),'bad_rotation_among_raw_success':int((boolok&badrot).sum()),'bad_limit_among_raw_success':int((boolok&badlim).sum()),'note':'reason counts overlap'};checkcount+=1
    for k in [6,8]:
        clean=json.loads((folder(k)/'cleanup.json').read_text());assert all(r['returncode'] is not None for r in clean);checkcount+=1
    dump(OUT/'verification.json',{'status':'pass','artifact_checks':checkcount,'bioik_rejections':reasons,'script_sha256':sha(__file__),'wall_s':time.perf_counter()-start});print('PASS artifact checks',checkcount,flush=True)
if __name__=='__main__':main()
