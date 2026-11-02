"""Rule candidates, task7.9 A / R1–R6 (SRC-0401), implementation SRC-0440.

Inputs are the decision-start local sensor crop, proprioception and task route.
No truth map, collision oracle, random sampling, history or network is accepted.
All lengths are metres; relative poses use B_t, counterclockwise yaw in radians.
The shared search uses the current N1 IK contract, including its DLS fallback.
"""
from dataclasses import dataclass
import math
import time
import torch
from .core import State
from .geometry import rectangle_hits
from .motion import wrap
from .search import inplace_progress


@dataclass
class CandidateBatch:
    """Fixed [E,13] slots. Only async has a progress tensor [E,13].

    pose: [E,13,3] relative (dx,dy,dyaw); discarded slots are zero padded.
    mask marks generation only, never downstream path feasibility.
    info holds diagnostics (including synchronous internal s_in), not features.
    """
    pose: torch.Tensor
    mask: torch.Tensor
    progress: torch.Tensor | None
    inplace: torch.Tensor
    info: dict

    def world_pose(self, base):
        """Anchor once using the decision-start world base pose, for Core/rollout."""
        c, s = base[:, 2, None].cos(), base[:, 2, None].sin()
        x, y = self.pose[..., 0], self.pose[..., 1]
        return torch.stack([base[:, 0, None] + c*x - s*y,
                            base[:, 1, None] + s*x + c*y,
                            wrap(base[:, 2, None] + self.pose[..., 2])], -1)


def _corridor_coverage(reference):
    """Reuse LocalCollision's exact closed-square SAT, without new tolerances.

    [0,.99] union [.61,1.6] longitudinally is exactly the 1.6 x .67 corridor.
    Two overlapping .99 x .67 footprints thus share rectangle_hits unchanged.
    Work is independent of E; return [12,128*128] covered-cell booleans.
    """
    device, dtype = reference.device, reference.dtype
    axis = (torch.arange(128, device=device, dtype=dtype) + .5 - 64)*.05
    yy, xx = torch.meshgrid(axis, axis, indexing='ij')
    xy = torch.stack([xx, yy], -1).reshape(-1, 2)
    boxes = torch.zeros(128*128, 8, device=device, dtype=dtype)
    boxes[:, :2] = xy
    boxes[:, 3:6] = .025
    boxes[:, 6] = 1
    angle = torch.arange(12, device=device, dtype=dtype)*(math.pi/6)
    centre = torch.tensor([.495, 1.105], device=device, dtype=dtype)
    base = torch.stack([angle[:, None].cos()*centre,
                        angle[:, None].sin()*centre,
                        angle[:, None].expand(-1, 2)], -1).reshape(24, 3)
    hits = rectangle_hits(base, boxes[None].expand(24, -1, -1))
    return hits.reshape(12, 2, -1).any(1)


def _synchronize(reference):
    if reference.is_cuda:
        torch.cuda.synchronize(reference.device)


@torch.no_grad()
def generate_candidates(local, state, route, kin, *, synchronous):
    """Generate rule candidates from G [E,128,128,2] and decision-start state.

    Calls shared search only for generated async slots or the sync in-place slot.
    Diagnostic search time is synchronized wall time, including E x valid K
    assembly and route selection. IK targets includes every sampled pose passed
    to the shared solver after R_pre, including retained later samples after
    the first prefix failure; sampled_targets counts before coarse filtering;
    it is not a count of analytic branches or of DLS iterations.
    """
    E = len(state.s)
    if local.shape != (E, 128, 128, 2) or state.base.shape != (E, 3) or state.q.shape != (E, 6):
        raise ValueError('candidate input shape')
    references = [local, state.base, state.q, route.xyz, route.quat]
    if state.s.dtype not in (torch.float32, torch.float64) or any(
            t.device != state.s.device or t.dtype != state.s.dtype for t in references):
        raise ValueError('candidate inputs require matching float32/float64 device and dtype')
    if E == 0 or route.length.shape != state.s.shape:
        raise ValueError('candidate batch/route shape')
    if any(not torch.isfinite(t).all() for t in [local, state.base, state.q, state.s]):
        raise ValueError('nonfinite candidate input')
    if (state.s < 0).any() or (state.s > route.length).any():
        raise ValueError('candidate progress outside route')

    covered = _corridor_coverage(local)
    occupied = ((local[..., 0] > 0) & (local[..., 1] > 0)).flatten(1)
    # Matrix reduction over shared coverage avoids an E x 12 x 16384 allocation.
    blocked = occupied.to(local.dtype) @ covered.T.to(local.dtype) > 0
    mask = torch.cat([~blocked, torch.ones(E, 1, device=local.device, dtype=torch.bool)], -1)
    angle = torch.arange(12, device=local.device, dtype=local.dtype)*(math.pi/6)
    sectors = torch.stack([angle.cos(), angle.sin(), angle], -1)
    pose = torch.cat([sectors, torch.zeros(1, 3, device=local.device, dtype=local.dtype)], 0)
    pose = pose[None].expand(E, -1, -1).clone().masked_fill(~mask[..., None], 0)
    inplace = torch.zeros_like(mask)
    inplace[:, 12] = True
    out = CandidateBatch(pose, mask, None, inplace, {})

    _synchronize(local)
    start = time.perf_counter()
    selected = inplace if synchronous else mask
    env, slot = torch.where(selected)
    world = out.world_pose(state.base)
    search_state = State(world[env, slot], state.q[env], state.s[env])
    found, search_info = inplace_progress(search_state, route.select(env), kin, return_info=True)
    # Padding is initialized to s_cur (zero delta), and always accompanied by mask=0.
    progress = state.s[:, None].expand(E, 13).clone()
    progress[env, slot] = found
    _synchronize(local)
    search_seconds = time.perf_counter() - start
    if not synchronous:
        out.progress = progress
    out.info = dict(n_gen=mask[:, :12].sum(-1), only_inplace=~mask[:, :12].any(-1),
                    discard_reason=blocked.long(), # 0 generated, 1 observed positive-height cell
                    inplace_progress=progress[:, 12].clone(),
                    inplace_delta_s=progress[:, 12]-state.s,
                    ik_targets=search_info['targets'], ik_batch_calls=search_info.get('ik_batch_calls',1),
                    sampled_targets=search_info.get('sampled_targets',search_info['targets']),
                    coarse_rejected=search_info.get('coarse_rejected',0),
                    ik_accepted=search_info['accepted'], dls_fallbacks=search_info['dls_fallbacks'],
                    search_wall_seconds=search_seconds)
    if not synchronous:
        out.info['delta_s'] = progress-state.s[:, None]
    return out
