"""Pure G1 selection: parent TASK §4 / SRC-0392(9), SRC-0491, SRC-0905.

Feasible means arrived AND no predicted IK/local-collision failure. Feasible
progress ties retain candidate order. All-infeasible ties use progress, gap,
then candidate order; candidates without failure precede predicted failures.
"""
import torch


def select_g1(mask,f_k):
    if mask.dtype!=torch.bool or f_k.shape!=(*mask.shape,19) or mask.ndim!=2:
        raise ValueError('candidate mask / f_k shape')
    if mask.device!=f_k.device or not mask.any(-1).all() or not torch.isfinite(f_k[mask]).all():
        raise ValueError('nonempty finite candidate sets on same device required')
    feasible=mask&(f_k[...,0]>0)&(f_k[...,3:5].sum(-1)==0)
    no_feasible=~feasible.any(-1)
    failed=f_k[...,3:5].sum(-1)>0
    eligible=torch.where(no_feasible[:,None],mask,feasible)
    # SRC-0905: no failure has position 1.0 and precedes actual failures,
    # even when a failure's attempted checkpoint exceeds its timeout.
    no_failure=mask&~failed
    prefer_no_failure=no_feasible&no_failure.any(-1)
    eligible &= ~prefer_no_failure[:,None] | no_failure
    # For actual failures preserve the existing integer 0.05s checkpoint
    # comparison, avoiding float32 reconstruction noise at equal times.
    prefix=torch.round(f_k[...,6]*f_k[...,8]/.05)
    best=prefix.masked_fill(~eligible,-torch.inf).amax(-1,keepdim=True)
    compare_failure=no_feasible&~prefer_no_failure
    eligible &= ~compare_failure[:,None] | (prefix==best)
    progress=f_k[...,12].masked_fill(~eligible,-torch.inf)
    best_progress=progress.amax(-1,keepdim=True)
    # Feasible rows too: task7.4 RESULTS §15 G1 "max delta_s, ties by larger gap" (Claude review, SRC-0905).
    eligible &= progress==best_progress
    gap=f_k[...,16].masked_fill(~eligible,-torch.inf)
    best_gap=gap.amax(-1,keepdim=True)
    eligible &= gap==best_gap
    progress=f_k[...,12].masked_fill(~eligible,-torch.inf)
    return progress.argmax(-1),dict(no_feasible=no_feasible,feasible_count=feasible.sum(-1))
