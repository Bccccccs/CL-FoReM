import os,sys,json,torch,numpy as np
import os
os.environ['CUBLAS_WORKSPACE_CONFIG']=':4096:8'
sys.path.insert(0,'/workspace/src')
from task9_lr.runtime import activate
activate()
torch.set_num_threads(2)
torch.backends.cudnn.deterministic=True
torch.backends.cudnn.benchmark=False
from task9_rllib.native import NativeSAC
from ray.rllib.policy.sample_batch import SampleBatch
from ray.rllib.algorithms.dqn.dqn import calculate_rr_weights
cfg=json.load(open('/workspace/config/task9/task9_11/C_seed4718.json'))
sac=NativeSAC(74,'cuda',cfg)
print('DEVICE',sac.device, 'MODEL',type(sac.native_policy.model),'OPTIMIZERS',len(sac.native_policy._optimizers),'RR',calculate_rr_weights(sac.algorithm.config),flush=True)
for i in range(26):
    obs={'map':np.zeros((10,128,128,3),np.uint8),'vector':np.zeros((10,74),np.float32)}
    batch=SampleBatch(obs=obs,new_obs=obs,actions=np.zeros((10,3),np.float32),rewards=np.zeros(10,np.float32),terminateds=np.zeros(10,np.bool_),truncateds=np.zeros(10,np.bool_))
    sac.set_transfer((i+1)*10); losses=sac.train_native_batch(batch)
    print('STEP',sac.env_steps,'UPDATES',sac.update_count,'LOSS',[float(x) for x in losses],flush=True)
print('DONE',dict(sac.algorithm._counters),flush=True)
sac.close()
