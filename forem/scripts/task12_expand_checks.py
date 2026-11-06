#!/usr/bin/env python3
"""Necessary new-entry smoke; no new teacher calls or sealed data."""
import argparse,json,tempfile,copy
from pathlib import Path
import torch
from torch.nn import functional as F
from task12_expand_stats import self_test,write
from task12_expand_train import assemble_training,selection_key,save,tload
import task12_expand_train as training
from task12_heatmap import Heatmap

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--run',type=Path,default=Path('/run'));a=ap.parse_args();checks=json.loads((a.run/'freeze-checks.json').read_text())['checks'];checks['stats_fixture']=self_test()['all_pass']
 # Reuse r6 only. A poison sealed directory proves assembly cannot open it.
 base=Path('/workspace/results/task12/t12-utility-20261105-r6');r3=Path('/workspace/results/task12/t12-cost32-20261104-r3');old=tload(base/'dataset-v1.pt');plan=json.loads((a.run/'plan.json').read_text());labels=json.loads((base/'labels-v1.json').read_text())['items'];geos=json.loads((base/'geometry-and-identities.json').read_text())
 with tempfile.TemporaryDirectory(prefix='t12-expand-smoke-') as tmp:
  out=Path(tmp);specs=[]
  for i in range(192):
   ref=geos[i%32];sid=f'fixture-{i:03d}';subset='train' if i<160 else 'development';spec=dict(state_id=sid,map_id=f'fixture-map-{i}',difficulty=ref['difficulty'],subset=subset);specs.append(spec);d=out/'states'/sid;d.mkdir(parents=True)
   source=r3/'states'/ref['state_id']
   for name in ('network.pt','source.pt','candidates.json','selection.json'):(d/name).symlink_to(source/name)
   write(d/'labels.json',dict(grid=[r for r in labels if r['state_id']==ref['state_id']]))
  specs.append(dict(state_id='sealed-poison-never-read',map_id='sealed-poison',difficulty='sparse',subset='sealed'))
  fake=copy.deepcopy(plan);fake['states']=specs;write(out/'plan.json',fake);data,frozen=assemble_training(out,base,fake);assert data['X'].shape[0]==216 and frozen['sealed_labels_read'] is False;checks['assembly184_train32dev_skips_poison_sealed']=True
  assert selection_key(dict(utility_hit_states=2,utility_positive_points=1,arrival_hit_states=0,development_loss=10,epoch=20))>selection_key(dict(utility_hit_states=1,utility_positive_points=99,arrival_hit_states=9,development_loss=0,epoch=10));checks['selection_state_priority']=True
  assert torch.cuda.device_count()==1;dev=torch.device('cuda:0');torch.set_num_threads(2);torch.manual_seed(1204);model=Heatmap(data['condition'].shape[1]).to(dev);optim=torch.optim.Adam(model.parameters(),lr=.001);X=data['X'][:8].to(dev);C=data['condition'][:8].to(dev);Y=data['target'][:8].to(dev);M=data['mask'][:8].to(dev)
  logits=model(X,C);logits.retain_grad();before=next(model.parameters()).detach().clone();loss=F.binary_cross_entropy_with_logits(logits[M],Y[M],pos_weight=torch.tensor(frozen['pos_weight'],device=dev));loss.backward();assert not torch.count_nonzero(logits.grad[~M]);optim.step();assert float((next(model.parameters())-before).norm())>0 and next(iter(optim.state.values()))['exp_avg'].device==dev
  save(out/'checkpoint.pt',dict(model=model.state_dict(),optimizer=optim.state_dict(),rng=torch.get_rng_state(),cuda_rng=torch.cuda.get_rng_state_all()));ck=tload(out/'checkpoint.pt',dev);restored=Heatmap(C.shape[1]).to(dev);restored.load_state_dict(ck['model']);op2=torch.optim.Adam(restored.parameters(),lr=.001);op2.load_state_dict(ck['optimizer']);model.eval();restored.eval()
  with torch.no_grad():assert torch.equal(model(X[:1],C[:1]),restored(X[:1],C[:1]))
  for a1,a2 in zip(optim.state.values(),op2.state.values()):
   for k in ('exp_avg','exp_avg_sq','step'):assert torch.equal(a1[k].cpu(),a2[k].cpu())
  checks['actual_cuda_masked_gradient_adam_restore']=True
  # Exercise the actual new trainer through a dev checkpoint, STOP and resume.
  original_stat=training.stat
  def until_ten(run,phase,**kw):
   original_stat(run,phase,**kw)
   if phase=='epoch_complete' and kw.get('epoch')==10:(run/'STOP').touch()
  training.stat=until_ten
  assert training.train(out,base)==130
  ck=tload(out/'training/latest.pt');assert ck['epoch']==10 and ck['updates']==230
  assert (out/'training/best.pt').exists() and not (out/'selected-model.json').exists()
  (out/'STOP').unlink()
  def until_eleven(run,phase,**kw):
   original_stat(run,phase,**kw)
   if phase=='epoch_complete' and kw.get('epoch')==11:(run/'STOP').touch()
  training.stat=until_eleven
  assert training.train(out,base)==130
  ck=tload(out/'training/latest.pt');assert ck['epoch']==11 and ck['updates']==253
  assert json.loads((out/'training/save-restore-evidence.json').read_text())['optimizer_all_state_tensors_equal']
  checks['actual_trainer_development_checkpoint_stop_resume']=True

  evidence=dict(device=str(dev),gpu_uuid=str(torch.cuda.get_device_properties(0).uuid),loss=float(loss),known=int(M.sum()),unlabelled_nonzero=int(torch.count_nonzero(logits.grad[~M])),optimizer_device=str(next(iter(optim.state.values()))['exp_avg'].device),teacher_calls=0,r8_training_updates=0,fixture_updates=254,production_training_updates=0)
 result=dict(all_pass=all(checks.values()),checks=checks,gpu_smoke=evidence,reused_evidence=['SRC-T12-007/009 teacher/recovery','SRC-T12-018/019 utility/FK/decoder','SRC-T12-023 old labels'],scope='freeze identities, assembly isolation, predeclared selection priority, actual CUDA gradient and complete optimizer save/restore');write(a.run/'targeted-tests.json',result);print(json.dumps(result))
if __name__=='__main__':main()
