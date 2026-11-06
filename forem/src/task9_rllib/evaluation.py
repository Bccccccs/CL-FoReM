"""The existing100 random+96 semantic development tasks, with read-only metrics."""
from pathlib import Path
import time
from task8_lower.evaluation import evaluate as original_evaluate
from task7_lower.training import atomic_json
from .observer import MetricsObserver

def evaluate(sac,config,output,**kwargs):
    started=time.monotonic();observer=MetricsObserver()
    result=original_evaluate(sac,config,output,observer=observer,**kwargs)
    result['observer']={'hook_wall_s':observer.observer_wall_s,'ik_timing':observer.ik_timing,
                        'scope':'original Core._finish success/d/r, first failed substep, per-action rejection counts, residuals; no new solves'}
    result['total_evaluator_wall_s']=time.monotonic()-started
    atomic_json(output,result)
    return result
