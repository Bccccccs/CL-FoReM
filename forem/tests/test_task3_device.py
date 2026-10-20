"""Catch CPU defaults and integration stages silently overriding the selected SAC device."""
import csv,json,os,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
try:
 import task3_sac_entry as E
except ImportError as e:
 E=None
import validate_task3_core as V

@unittest.skipIf(E is None,'container torch stack required')
class DeviceSelection(unittest.TestCase):
 def test_auto_uses_available_cuda(self):
  with patch.object(E.torch.cuda,'is_available',return_value=True):
   self.assertEqual(E.resolve_device('auto'),'cuda')
 def test_auto_uses_cpu_only_when_cuda_is_unavailable(self):
  with patch.object(E.torch.cuda,'is_available',return_value=False):
   self.assertEqual(E.resolve_device('auto'),'cpu')
 def test_explicit_cpu_is_respected_on_gpu_host(self):
  with patch.object(E.torch.cuda,'is_available',return_value=True):
   self.assertEqual(E.resolve_device('cpu'),'cpu')
 def test_explicit_cuda_index_is_preserved(self):
  self.assertEqual(E.resolve_device('cuda:1'),'cuda:1')

class IntegrationDevice(unittest.TestCase):
 def test_default_does_not_force_cpu_and_explicit_device_reaches_both_stages(self):
  # Replace only expensive process launches. Run the real main/argument parsing and check its emitted stage commands.
  for extra,want in [([], 'auto'),(['--device','cuda:1'],'cuda:1'),(['--device','cpu'],'cpu')]:
   with self.subTest(extra=extra),tempfile.TemporaryDirectory() as td:
    ph=Path(td)/'physics';ph.mkdir()
    with (ph/'timeseries.csv').open('w',newline='') as f:
     w=csv.DictWriter(f,fieldnames=['phase','t_sim','truth_x','truth_y','truth_yaw']);w.writeheader()
     for name,v,omega in [('hold',0,0),('straight',0.2,0),('turn',0,0.5),('coord',0.15,0.2)]:
      for t in [0,0.02]:w.writerow(dict(phase=name,t_sim=t,truth_x=v*t,truth_y=0,truth_yaw=omega*t))
    (ph/'physics_summary.json').write_text(json.dumps({'phases':{'straight':{'path_speed':0.2},'turn':{'mean_rate':0.5},'coord':{'path_speed':0.15,'mean_rate':0.2}}}))
    def record(name,cmd,res,run,timeout):
     return dict(stage=name,cmd=' '.join(cmd),returncode=0,wall_s=0,dir=str(Path(res)/name))
    with patch.object(V,'stage',side_effect=record),patch.dict(os.environ,{'FOREM_RES_DIR':td}),patch.object(sys,'argv',['validate','--run-id','fixture']+extra):
     self.assertEqual(V.main(),0)
    stages=json.loads((Path(td)/'integration_summary.json').read_text())['stages']
    for st in stages:
     if st['stage'] in ('sac_smoke','sac_eval'):
      argv=st['cmd'].split();self.assertEqual(argv[argv.index('--device')+1],want)

if __name__=='__main__':unittest.main()
