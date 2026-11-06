"""Compare completed development rows against historical B3-5M originals; no model/environment."""
import json,argparse,time
from pathlib import Path
O=Path('/output');H=Path('/history/results/task9/t9-stage2-20261029')
fields=('strict_success','failures','transfers','terminated','truncated')
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--partial',action='store_true');args=parser.parse_args();sources={};checks=[];differences=[]
 for seed in (4718,4719,4720):
  p=H/f'B3_5M-seed{seed}'/'validation-5000000.json';doc=json.loads(p.read_text());sources[seed]=str(p)
  old={(domain,r['map_id'],r['seed']):r for domain,key in [('random','validation'),('semantic','transfer')] for r in doc[key]['rows']}
  for batch in sorted(O.glob(f'formal-current-{seed}-*')):
   if not batch.is_dir() or not (batch/'result.json').exists():continue
   data=json.loads((batch/'result.json').read_text())
   for row in data['rows']:
    key=(row['domain'],row['map_id'],row['seed']);ref=old[key]
    delta={k:dict(current=row[k],historical=ref[k]) for k in fields if row[k]!=ref[k]}
    checks.append(dict(seed=seed,key=key,batch=batch.name,exact=not delta))
    if delta:differences.append(dict(seed=seed,key=key,differences=delta))
 if not args.partial:assert len(checks)==588,('incomplete baseline',len(checks))
 result=dict(status='PASS' if not differences else 'FAIL',complete=len(checks)==588,rows=len(checks),fields=fields,sources=sources,checks=checks,differences=differences,epoch=time.time(),scope='original same episode keys and five historical outcome fields only; no claim byte-identical all tensors, no environment rerun')
 p=O/('historical-current-audit-partial.json' if args.partial else 'historical-current-audit.json');p.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('checks','differences')}))
 if differences:raise SystemExit(1)
if __name__=='__main__':main()
