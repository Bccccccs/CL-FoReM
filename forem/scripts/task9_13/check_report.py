"""Inert report fixture; validates aggregation without any robot transitions."""
import json,sys,os
from pathlib import Path
from report import main
root=Path('/workspace/results/task9/task9.13-report-fixture');root.mkdir(exist_ok=True)
(root/'SYNTHETIC_INERT_FIXTURE_NOT_REAL_TRAINING.txt').write_text('Inert synthetic report test. No training or robot episodes occurred. Never include this directory in scientific results.\n')
for seed in (4718,4719):
 for arm in ('C','R'):
  job=root/f'{arm}-seed{seed}';job.mkdir(exist_ok=True)
  summary={'state':{'steps':3000000,'env_actions':3000000},'updates':299975,'timings':{}}
  (job/'summary.json').write_text(json.dumps(summary))
  (job/'profile-terminal.json').write_text(json.dumps({'wall_s':1000 if arm=='C' else 1500}))
  (job/'remaining-terminal.json').write_text(json.dumps({'wall_s':12000 if arm=='C' else 14000}))
  learning=[];costs=[];events=[]
  for step in range(250000,3000001,250000):
   ev={'complete':True,'step':step,'wall_s':10}
   for domain,count in [('validation',100),('transfer',96)]:
    rows=[]
    for i in range(count):
     success=i%(3 if arm=='C' else 2)==0
     rows.append({'map_id':f'm{i if domain=="validation" else i//4}','seed':i,'stream_index':0,'strict_success':success,'original_success':success,'first_rejection_present':False,'first_rejection':None,'no_rejection_stall':not success,'rejection_action_counts':{str(k):0 for k in range(5)}})
    ev[domain]={'episodes':count,'strict_success_rate':sum(x['strict_success'] for x in rows)/count,'rows':rows}
   (job/f'validation-{step:07d}.json').write_text(json.dumps(ev));events.append({'count':196})
   learning.append({'step':step,'elapsed_s':step/250000*900,'previous_wall_s':0 if step==250000 else 1000})
   costs.append({'path':f'checkpoint-{step:07d}.pt','total_wall_s':1})
  for name,rows in [('learning.jsonl',learning),('checkpoint-costs.jsonl',costs),('episodes-started.jsonl',events)]:
   (job/name).write_text(''.join(json.dumps(x)+'\n' for x in rows))
main(root)
report=json.loads((root/'comparison.json').read_text())
report.update(evidence_kind='synthetic_inert_fixture_not_real_training',actual=False)
(root/'comparison.json').write_text(json.dumps(report,indent=2))
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
image=mpimg.imread(root/'learning-curves.png');fig,ax=plt.subplots(figsize=(11,4));ax.imshow(image);ax.axis('off');ax.set_title('SYNTHETIC INERT FIXTURE — NOT REAL TRAINING',color='red');fig.savefig(root/'learning-curves.png',dpi=160);plt.close(fig)
assert report['actual_formal_transfers']==12000000 and report['actual_evaluation_episode_requests_including_failed_retries']==9408
assert abs(report['comparisons'][0]['endpoint_paired_strict']['delta_R_minus_C']-.16)<1e-9
assert len((root/'learning-curves.csv').read_text().splitlines())==97
print('INERT_REPORT_FIXTURE_PASS')
