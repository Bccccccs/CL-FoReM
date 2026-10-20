"""Real official-tracker regression for original seal101 raw pixels/timestamps."""
import unittest,subprocess
from pathlib import Path
import yaml

class Seal101InitializerInput(unittest.TestCase):
 def test_config_retains_features_in_both_original_initialization_windows(self):
  root=Path(__file__).resolve().parents[1]
  probe=root/'results/task4/t4.3.1-tracker-evidence/probe-histogram'
  manifest=root/'results/task4/t4.3.1-init-r1/exact_manifest.txt'
  if not probe.is_file() or not manifest.is_file():self.skipTest('original raw diagnostic/library-linked probe evidence unavailable')
  cfg=yaml.safe_load((root/'config/task4/estimator.yaml').read_text().replace('%YAML:1.0\n','',1))
  self.assertEqual((cfg['fast_threshold'],cfg['grid_x'],cfg['grid_y'],cfg['use_stereo']),(20,5,5,True))
  result=subprocess.run([str(probe),str(cfg['init_max_features']),str(manifest),str(cfg['min_px_dist']),cfg['histogram_method']],text=True,capture_output=True,timeout=30)
  self.assertEqual(result.returncode,0,result.stderr)
  rows=[line.split() for line in result.stdout.splitlines() if line.startswith('PROBE ')]
  self.assertEqual(len(rows),80)
  last=rows[-1]
  self.assertGreaterEqual(int(last[6]),15,'official oldest-half disparity window feature requirement fails')
  self.assertGreaterEqual(int(last[7]),15,'official newest-half disparity window feature requirement fails')
  self.assertEqual(float(last[5]),float(last[1]),'feature database has no genuine current camera timestamp')

if __name__=='__main__':unittest.main()
