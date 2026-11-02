"""Render already-recorded trial diagnostics; no run, selection or new gate."""
import argparse,csv,json
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);a=p.parse_args();root=Path(a.root)
 import matplotlib
 matplotlib.use('Agg')
 import matplotlib.pyplot as plt
 fig,axs=plt.subplots(2,3,figsize=(13,7))
 for variant in ('sync','async'):
  rows=[json.loads(x) for x in (root/f'pilot-{variant}/learning.jsonl').read_text().splitlines()]
  with (root/f'pilot-{variant}-curve.csv').open('w',newline='') as f:
   keys=['step','elapsed_s','q1_loss','q2_loss','policy_loss','alpha_loss','alpha','Q_abs_max','arrivals','segments','timeouts','episodes','G1_ratio'];w=csv.DictWriter(f,keys);w.writeheader()
   for r in rows:w.writerow(dict(step=r['step'],elapsed_s=r['elapsed_s'],q1_loss=r['losses'][0],q2_loss=r['losses'][1],policy_loss=r['losses'][2],alpha_loss=r['losses'][3],alpha=r['alpha'],Q_abs_max=r['Q_abs_max'],arrivals=r['arrivals'],segments=r['segments'],timeouts=r['timeouts'],episodes=r['episodes'],G1_ratio=r['G1_fully_occluded_frames']/r['sensor_frames'] if r['sensor_frames'] else 0))
  x=[r['step'] for r in rows]
  series=[([r['losses'][0]+r['losses'][1] for r in rows],'Twin Q loss'),([r['losses'][2] for r in rows],'Policy loss'),([r['alpha'] for r in rows],'Temperature alpha'),([r['Q_abs_max'] for r in rows],'Max abs Q (fixed first 256 replay rows)'),([r['arrivals']/r['segments'] if r['segments'] else 0 for r in rows],'Cumulative segment arrival rate'),([r['G1_fully_occluded_frames']/r['sensor_frames'] if r['sensor_frames'] else 0 for r in rows],'G1 fully occluded frame ratio')]
  for ax,(y,title) in zip(axs.flat,series):ax.plot(x,y,label=variant);ax.set_title(title,fontsize=10);ax.set_xlabel('Action transitions');ax.grid(alpha=.2);ax.legend()
 fig.tight_layout();fig.savefig(root/'pilot-curves.png',dpi=160);fig.savefig(root/'pilot-curves.svg');plt.close(fig)
if __name__=='__main__':main()
