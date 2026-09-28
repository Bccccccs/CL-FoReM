"""Independent bounded CPU audit. Synthetic data only; originals untouched."""
import json
import tempfile
from pathlib import Path
import numpy as np
from wm.data import EpisodeDataset, DataError, file_sha256
from wm.cache import build_cache, FeatureCache
from wm.train_offline import WindowSource

class Encoder:
    dim=42
    checkpoint_sha256='audit-synthetic'
    numerical_identity={'device_type':'cpu','implementation':'audit'}
    def iter_numpy(self, robot, maps, batch):
        for i in range(0,len(robot),batch):
            yield np.concatenate([robot[i:i+batch],maps[i:i+batch,0,0,:]],axis=1)

with tempfile.TemporaryDirectory(prefix='p1-acceptance-cache-') as d:
    root=Path(d)
    eps=[]; recs=[]
    for i,(T,complete) in enumerate([(7,True),(7,False),(1,True),(0,True)]):
        n=T+int(complete)
        robot=np.broadcast_to((100*i+np.arange(n,dtype=np.float32))[:,None],(n,41)).copy()
        maps=np.broadcast_to((np.arange(n,dtype=np.float32)/10)[:,None,None,None],(n,120,120,1)).copy()
        ep=dict(robot_state=robot,local_map=maps,action=np.broadcast_to((np.arange(T,dtype=np.float32)/10)[:,None],(T,3)).copy(),dt=.1+np.arange(T,dtype=np.float32)/100,reward=np.zeros(T,np.float32),done=np.zeros(T,bool),complete=complete,seed=i,subgoal_index=np.arange(n)//3)
        path=root/f'ep{i}.npz'; np.savez_compressed(path,**ep)
        recs.append(dict(split='train',seed=i,path=path.name,sha256=file_sha256(path)))
        eps.append(ep)
    manifest=root/'dataset.json'; manifest.write_text(json.dumps({'episodes':recs}))
    ds=EpisodeDataset.from_manifest(manifest,'train')
    cache=build_cache(ds,Encoder(),root/'cache',batch=2,chunk_bytes=42*4*2,max_open=2)
    dense=np.concatenate([np.concatenate([e['robot_state'],e['local_map'][:,0,0,:]],axis=1) for e in eps])
    np.testing.assert_array_equal(cache[np.arange(len(dense))],dense)
    for k in [1,5]:
        for exclude in [False,True]:
            src=WindowSource(ds,cache,k,exclude)
            expected=[(i,t) for i,e in enumerate(eps) for t in range(max(0,len(e['robot_state'])-k)) if not exclude or np.all(e['subgoal_index'][t:t+k+1]==e['subgoal_index'][t])]
            assert src.windows.tolist()==[list(x) for x in expected]
            seen=0
            for batch in src.batches(3,'cpu'):
                for row,(i,t) in enumerate(zip(batch['episode'],batch['t'])):
                    np.testing.assert_array_equal(batch['h'][row,:,:41].numpy(),eps[i]['robot_state'][t:t+k+1])
                    np.testing.assert_array_equal(batch['action'][row].numpy(),eps[i]['action'][t:t+k])
                    np.testing.assert_array_equal(batch['dt'][row].numpy(),eps[i]['dt'][t:t+k])
                seen+=len(batch['h'])
            assert seen==len(expected)
    mean,std=cache.statistics()
    np.testing.assert_allclose(mean,dense.astype(np.float64).mean(0),rtol=1e-6)
    np.testing.assert_allclose(std,dense.astype(np.float64).std(0),rtol=1e-6)
    peers=[FeatureCache(cache.root,max_open=4) for _ in range(3)]
    owned=cache[np.array([0,4,9])]
    for peer in peers:
        peer[np.arange(len(dense))]
        assert len(FeatureCache._pool)<=4
    for peer in peers: peer.close()
    np.testing.assert_array_equal(owned,dense[[0,4,9]])
    location=cache.root
    cache.close()
    block=location/'features-000000.npy'
    contents=bytearray(block.read_bytes()); contents[-1]^=1; block.write_bytes(contents)
    try: FeatureCache(location)
    except DataError: pass
    else: raise AssertionError('corrupt block accepted')
    assert len(FeatureCache._pool)==0
    print(json.dumps(dict(result='PASS',episodes=4,observations=len(dense),horizons=[1,5],goal_switch_modes=2,tail_batch=3,cache_block_rows=2,global_lru_limit=4,zero_transition_episode=True,corrupt_block_rejected=True)))
