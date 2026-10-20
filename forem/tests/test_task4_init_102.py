"""Regression: real official KLT must supply both initializer half-windows on original raw inputs."""
import json
import subprocess
import unittest
from pathlib import Path
import yaml

class OriginalInitializationInputs(unittest.TestCase):
    def test_original_101_and_102_supply_official_disparity_windows(self):
        root = Path(__file__).resolve().parents[1]
        cfg = yaml.safe_load((root/'config/task4/estimator.yaml').read_text().replace('%YAML:1.0\n', '', 1))
        probe = root/'results/task4/t4.3.1-tracker-evidence/probe-histogram'
        for seed, run in [(101, 't4.3.1-init-r1'), (102, 't4.3.2-init-r1')]:
            with self.subTest(seed=seed):
                manifest = root/'results/task4'/run/'exact_manifest.txt'
                self.assertTrue(probe.is_file() and manifest.is_file(), 'original raw evidence required')
                result = subprocess.run([str(probe),str(cfg['init_max_features']),str(manifest),str(cfg['min_px_dist']),cfg['histogram_method']],text=True,capture_output=True,timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)
                rows = [line.split() for line in result.stdout.splitlines() if line.startswith('PROBE ')]
                self.assertEqual(len(rows), 80)
                last = rows[-1]
                self.assertEqual(float(last[5]), float(last[1]), 'no current feature database timestamp')
                self.assertGreaterEqual(int(last[6]), 15, 'official oldest-half feature requirement fails')
                self.assertGreaterEqual(int(last[7]), 15, 'official newest-half feature requirement fails')

if __name__ == '__main__':
    unittest.main()
