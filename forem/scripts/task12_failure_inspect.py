import torch,json
from pathlib import Path
from task10.boundary_state import decode
p=Path('/baseline/states/state-07')
def show(v,depth=0):
 if depth>2:return str(type(v))
 if isinstance(v,torch.Tensor):return {'shape':list(v.shape),'dtype':str(v.dtype),'sample':v.flatten()[:20].tolist()}
 if isinstance(v,dict):return {k:show(x,depth+1) for k,x in v.items()}
 if isinstance(v,(tuple,list)):return {'len':len(v),'first':show(v[0],depth+1) if v else None}
 if hasattr(v,'__dict__'):return {type(v).__name__:show(vars(v),depth)}
 return str(v)
for file in ['source.pt','grid-0/data.pt']:
 x=torch.load(p/file,map_location='cpu',weights_only=False);c=decode(x['core'],device='cpu');print(file,json.dumps(show(c),indent=2));
print('trace detailed',json.dumps(show(c.get('trace'),-1),indent=2))
print('attempts detailed',json.dumps(show(c.get('attempts'),-1),indent=2))
