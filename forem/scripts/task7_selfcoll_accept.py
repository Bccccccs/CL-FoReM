"""Literal acceptance gate; a failed candidate must remain visibly failed."""
import json,sys
from pathlib import Path
P=Path('results/task7/t7.18.2-r1-20261021');s=json.loads((P/'summary.json').read_text());c=s['chain'];upper=c['pairs']['2,13']
checks=dict(all_stored_poses_referenced=all(s[k]['complete'] for k in ['chain','sync','async']),chain_true_13_detected=c['TP']==13 and c['FN']==0,upper_topplate_true_6_detected=upper[0]==6 and upper[3]==0,FPR_no_worse_than_diagnostic_B=c['FP']<=26)
r=dict(passed=all(checks.values()),checks=checks,chain={k:c[k] for k in ['N','TP','FP','TN','FN','FPR']},expected_FP_max=26,expected_negative_poses=375,upper_topplate_TP_FP_TN_FN=upper,production_activated=False)
(P/'acceptance.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2));sys.exit(0 if r['passed'] else 1)
