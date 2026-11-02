"""Task proposals, isolated RNG streams and explicit initialization validation.

This module is truth-authorized for reset/goal validation (SRC-0460).
The default sampler follows the user's E1–E3 decisions (SRC-0437); original
height/cost/joint provenance and implementation limits are in SRC-0465/0466.
"""
from dataclasses import dataclass
import math
import numpy as np
import torch
from .kinematics import LOW, HIGH
from .geometry import to_box


@dataclass
class EnvironmentStreams:
    maps: np.random.Generator
    initial: np.random.Generator
    other: np.random.Generator


class RandomStreams:
    """Stable per-environment, per-purpose streams; no torch/global RNG writes.
    Stream ids (map=0, initial=1, other=2) are bookkeeping, not task parameters.
    """
    def __init__(self, seed, batch):
        if not isinstance(seed, int) or seed < 0 or not isinstance(batch, int) or batch <= 0:
            raise ValueError('nonnegative integer seed and positive batch required')
        self._streams = [EnvironmentStreams(*[
            np.random.default_rng(np.random.SeedSequence(seed, spawn_key=(i, purpose)))
            for purpose in range(3)]) for i in range(batch)]

    def for_env(self, index):
        if not 0 <= index < len(self._streams): raise IndexError(index)
        return self._streams[index]


def sample_base(rng):
    """Uniform raw pose proposal across the complete 10x10m map.
    Collision rejection is separate; this function does not claim a free pose.
    """
    return np.array([rng.uniform(-5., 5.), rng.uniform(-5., 5.), rng.uniform(0., 2*math.pi)])


def sample_goal(base, rng):
    """Uniform radius [0.5,8]m, uniform azimuth and height [0.7,1.15]m.
    Same original half-circle+sign sampling, without the original clipping.
    Proposal may be outside the map and must then be rejected by the caller.
    Orientation belongs to the final planned segment, not this proposal.
    """
    distance = rng.uniform(.5, 8.); angle = rng.uniform(0., math.pi)
    return np.array([base[0]+distance*math.cos(angle),
                     base[1]+rng.choice([-1, 1])*distance*math.sin(angle),
                     rng.uniform(.7, 1.15)])


def validate_initial_state(base, q, kin, robot, collision):
    """Return actual FK, after joint limits and full collision validation.
    No IK result/target is ever substituted for the actual input joints.
    """
    if base.ndim != 2 or base.shape[1] != 3 or q.shape != (len(base), 6):
        raise ValueError('base/q shape')
    if not torch.isfinite(base).all() or not torch.isfinite(q).all(): raise ValueError('nonfinite initial state')
    low = torch.as_tensor(LOW, device=q.device, dtype=q.dtype)
    high = torch.as_tensor(HIGH, device=q.device, dtype=q.dtype)
    if (q < low).any() or (q > high).any(): raise ValueError('initial joint limits')
    if (base[:, :2].abs() >= 5).any(): raise ValueError('initial base outside map')
    if collision(base, robot(base, q)).any.any(): raise ValueError('initial collision')
    tcp = kin.world_tcp(base, q)
    # Confirm solvability using the common N1 solver, without replacing q.
    if not kin.solve_world(base, tcp, q).accepted.all(): raise ValueError('initial IK')
    return tcp


def sample_initial(rng, initial_joints, *, max_attempts, kin, robot, collision,
                   device, dtype):
    """Bounded rejection with an explicitly supplied joint-distribution policy.

    max_attempts is a caller-owned execution budget, never a feasibility
    threshold. Exhaustion raises rather than changing map, pose distribution,
    collision acceptance, or silently falling back to a nominal configuration.
    """
    if not isinstance(max_attempts, int) or max_attempts <= 0:
        raise ValueError('positive explicit proposal budget required')
    error = None
    for _ in range(max_attempts):
        base = torch.as_tensor(sample_base(rng), device=device, dtype=dtype)[None]
        q = torch.as_tensor(initial_joints(rng), device=device, dtype=dtype)[None].clone()
        try:
            tcp = validate_initial_state(base, q, kin, robot, collision)
        except ValueError as exc:
            error = exc
            continue
        return base, q, tcp
    raise RuntimeError(f'initial proposal budget exhausted ({max_attempts}); last rejection: {error}')


def validate_goal_position(goal, start_base, boxes, mask):
    """B12 position constraints only; does not certify an IK/collision witness."""
    if goal.shape != (len(start_base), 3) or not torch.isfinite(goal).all(): raise ValueError('goal shape/finite')
    radius = (goal[:, :2]-start_base[:, :2]).norm(dim=-1)
    valid = (goal[:, :2].abs() < 5).all(-1)&(radius >= .5)&(radius <= 8)&(goal[:, 2] >= .7)&(goal[:, 2] <= 1.15)
    local = to_box(goal[:, None], boxes)
    valid &= ~((local.abs() <= boxes[..., 3:6]).all(-1)&mask).any(-1)
    return valid


def validate_goal_witness(base, previous_q, target, kin, robot, collision):
    """Return the common solver result and its full collision-free acceptance.
    A rejected finite witness is not proof that no feasible base exists.
    Witness search/distribution is deliberately supplied by the caller.
    """
    result = kin.solve_world(base, target, previous_q)
    valid = result.accepted&~collision(base, robot(base, result.q)).any
    valid &= (base[:, :2].abs() < 5).all(-1)&torch.isfinite(base).all(-1)
    return result, valid


# Literal vector passed to CBL's manipulator joint group, SRC-0437/E2.
CBL_Q=(-0.0007863513851198434,-1.5705042627235626,-0.01111974792726489,
       -1.5713908974689739,-0.0005968816301642477,-0.006540936480208259)


@dataclass
class Episode:
    base: torch.Tensor
    q: torch.Tensor
    route: object
    boxes: torch.Tensor
    map_id: str = '<fixture>'
    witness_base: torch.Tensor | None = None
    witness_q: torch.Tensor | None = None
    seed: int | None = None


class EpisodeSampler:
    """E1–E3 complete default sampler on the fixed task7.16 pool.

    Rejected proposals consume a new independent proposal seed and map draw;
    there is no retry cap, fallback task or relaxed acceptance condition.
    Geometry is available only here, rendering and execution collision checks.
    The witness is a free-grid connected base with accepted IK and full robot
    collision checks; it is not a guarantee of learned-policy success.
    """
    def __init__(self,pool=None,*,split='train',difficulty=None,device='cuda',dtype=torch.float32,kin=None,robot=None):
        import json
        from pathlib import Path
        from .robot import RobotGeometry, ROOT
        from .kinematics import Kinematics
        self.pool=Path(pool) if pool is not None else ROOT/'results/task7/maps/a/20261021T021400Z'
        self.entries=[x for x in json.loads((self.pool/'index.json').read_text())['maps'] if x['split']==split and (difficulty is None or x['difficulty']==difficulty)]
        if not self.entries:raise ValueError('map pool split/difficulty has no maps')
        self.device=torch.device(device);self.dtype=dtype
        self.kin=Kinematics() if kin is None else kin;self.robot=RobotGeometry() if robot is None else robot
        self.planners={};self.stats=dict(proposals=0,accepted=0,rejections={},witness_targets=0,witness_dls=0,initial_targets=0)

    def sample(self,streams):
        import json
        from .routes import TruthPlanner
        from .geometry import TruthCollision
        while True:
            self.stats['proposals']+=1
            entry=self.entries[int(streams.maps.integers(len(self.entries)))];key=entry['id']
            seed=int(streams.initial.integers(0,np.iinfo(np.int64).max));rng=np.random.default_rng(seed)
            if key not in self.planners:self.planners[key]=TruthPlanner(json.loads((self.pool/entry['path']).read_text()))
            planner=self.planners[key]
            boxes=torch.as_tensor(planner.boxes,device=self.device,dtype=self.dtype)
            mask=torch.ones(1,len(boxes),device=self.device,dtype=torch.bool)
            collision=TruthCollision(boxes[None],mask,robot=self.robot)
            base=torch.as_tensor(sample_base(rng),device=self.device,dtype=self.dtype)[None]
            q=torch.tensor(CBL_Q,device=self.device,dtype=self.dtype)[None]
            try:
                # Historical stats key counts validation proposals, including
                # early collision rejection; it is not an actual IK-call count.
                self.stats['initial_targets']+=1
                start=validate_initial_state(base,q,self.kin,self.robot,collision)[0]
            except ValueError:
                self._reject('initial');continue
            goal=torch.as_tensor(sample_goal(base[0].cpu().double().numpy(),rng),device=self.device,dtype=self.dtype)
            if not validate_goal_position(goal[None],base,boxes[None],mask).item():
                self._reject('goal');continue
            try:route=planner.plan(start,goal)
            except ValueError:
                self._reject('route');continue
            target=route.at(route.length)
            xy=planner.witness_cells(base[0].cpu().double().numpy(),goal.cpu().double().numpy())
            if not len(xy):self._reject('base_connected_region');continue
            order=rng.permutation(len(xy));xy=xy[order];yaw=rng.uniform(0,2*math.pi,len(xy))
            witness=None
            # Execution chunking only, never an acceptance/retry limit; visit
            # the entire finite candidate set until a valid witness is found.
            for offset in range(0,len(xy),64):
                end=min(offset+64,len(xy));n=end-offset
                poses=torch.as_tensor(np.c_[xy[offset:end],yaw[offset:end]],device=self.device,dtype=self.dtype)
                result,valid=validate_goal_witness(poses,q.expand(n,-1),target.expand(n,-1,-1),self.kin,self.robot,collision)
                self.stats['witness_targets']+=n
                self.stats['witness_dls']+=int((result.branch<0).sum())
                ids=torch.where(valid)[0]
                if len(ids):
                    j=int(ids[0]);witness=(poses[j:j+1].clone(),result.q[j:j+1].clone());break
            if witness is None:self._reject('goal_IK_collision_witness');continue
            self.stats['accepted']+=1
            return Episode(base,q,route,boxes,key,*witness,seed)

    def _reject(self,reason):
        rejected=self.stats['rejections'];rejected[reason]=rejected.get(reason,0)+1
