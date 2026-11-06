"""Explicitly scoped smoke-only bridge for evaluation metrics-only source additions."""
import types
from pathlib import Path
import torch

def load_smoke(path):
    from task9_rllib import training
    stored=torch.load(path,map_location='cpu',weights_only=False)
    actual=training._contract();old=stored['contract']
    if old==actual:return training.load_checkpoint(path,'cuda')
    if Path(path).parent.name not in {'task9.13-smoke-C','task9.13-smoke-R','task9.13-smoke-C-r2','task9.13-smoke-R-r2'} or old['environment']!=actual['environment']:
        raise ValueError('engineering bridge only accepts original C smoke and unchanged environment source')
    a,b=old['adapter'],actual['adapter']
    changes={k for k in set(a)|set(b) if a.get(k)!=b.get(k)}
    if not changes<={'evaluation.py','observer.py'}:raise ValueError('smoke scientific adapter changed:'+str(changes))
    globals_copy={**training.load_checkpoint.__globals__,'_contract':lambda:old}
    loader=types.FunctionType(training.load_checkpoint.__code__,globals_copy,training.load_checkpoint.__name__,training.load_checkpoint.__defaults__,training.load_checkpoint.__closure__)
    return loader(path,'cuda')
