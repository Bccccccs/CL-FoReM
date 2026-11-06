"""Independent CPU-only epsilon reconstruction; no project imports or models."""
import argparse,csv,hashlib,json,os,time
from pathlib import Path
import torch

p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--frozen',type=Path,required=True);a=p.parse_args()
started=time.perf_counter()
assert torch.__version__=='2.7.1+cu128',torch.__version__
assert not torch.cuda.is_available(),'CPU audit must not have CUDA access'
torch.set_num_threads(1)
frozen=list(csv.DictReader(a.frozen.open()));reports=[]
for seed in (4718,4719,4720):
 for trace in sorted((a.run/f'T-{seed}').glob('case*.jsonl')):
  records=[json.loads(x) for x in trace.read_text().splitlines(keepends=True) if x.endswith('\n')]
  identity=records[0]['comparison']['case_key'];case=records[0]['comparison']['case_no']
  f=next(x for x in frozen if int(x['training_seed'])==seed and int(x['case_no'])==case)
  assert all(identity[k]==f[k] for k in identity)
  entries=[x['detail']['intervention'] for x in records if 'intervention' in x['detail']]
  assert len(entries)==1
  intervention=entries[0]
  serialized=json.dumps([91020261103,seed,f['map_id'],int(f['seed']),int(f['stream_index']),f['role'],f['source_split'],int(f['proposal_seed'])],ensure_ascii=False,separators=(',',':'))
  digest=hashlib.sha256(serialized.encode('utf-8')).hexdigest();sample_seed=int.from_bytes(bytes.fromhex(digest)[:8],'big')%2**63
  assert serialized==intervention['serialized'] and digest==intervention['sha256'] and sample_seed==intervention['generator_seed']
  global_before=torch.get_rng_state().clone();g=torch.Generator(device='cpu');g.manual_seed(sample_seed)
  epsilon=torch.randn(3,dtype=torch.float32,generator=g)
  assert torch.equal(global_before,torch.get_rng_state())
  assert epsilon.tolist()==intervention['epsilon'],('epsilon mismatch',seed,case)
  mean=torch.tensor(intervention['mean'],dtype=torch.float32);log_std=torch.tensor(intervention['log_std'],dtype=torch.float32)
  cpu_formula=torch.tanh(mean+torch.exp(log_std)*epsilon);gpu_saved=torch.tensor(intervention['replacement_action'],dtype=torch.float32)
  cpu_mean=torch.tanh(mean);gpu_mean=torch.tensor(intervention['mean_action'],dtype=torch.float32)
  reports.append(dict(seed=seed,case_no=case,serialized=serialized,generator_seed=sample_seed,epsilon=epsilon.tolist(),epsilon_exact=True,global_cpu_rng_unchanged=True,cpu_float32_action=cpu_formula.tolist(),gpu_saved_action=gpu_saved.tolist(),cpu_minus_gpu_action=(cpu_formula-gpu_saved).tolist(),max_abs_action_difference=float((cpu_formula-gpu_saved).abs().max()),cpu_minus_gpu_mean_action=(cpu_mean-gpu_mean).tolist(),cpu_gpu_action_exact=torch.equal(cpu_formula,gpu_saved),trace_path=str(trace),intervention_record_sha256=hashlib.sha256(json.dumps(intervention,sort_keys=True,separators=(',',':')).encode()).hexdigest()))
assert len(reports)==12
print(json.dumps(dict(status='PASS_EPSILON_IDENTITY_ONLY',torch=torch.__version__,cuda_available=False,network_models_loaded=False,simulation_environments_created=False,environment_episodes=0,reports=reports,wall_s=time.perf_counter()-started,input_scope='Complete intervention records from append-only live traces; final full-trace coverage and record hashes will be cross-checked after sealing',numerical_scope='CPU float32 formula versus saved GPU formula differences reported without tolerance or approximate-equality claim; no numerical difference relaxes exact C/T prefixes'),ensure_ascii=False,indent=2))
