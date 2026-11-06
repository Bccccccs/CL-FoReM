"""Rejecting final arc length or consuming default RNG would break these checks."""
import importlib.util
from pathlib import Path
import sys
import numpy as np
import pytest
import torch
from task7_sim.episode import EpisodeSampler, RandomStreams
from task7_sim.motion import Route

POOL='/root/mm_husky_ws/results/task7/maps/a/20261021T021400Z'


def test_default_none_matches_frozen_baseline_episode_and_rng():
    path=Path('/root/mm_husky_ws/results/task7/t7.24-short-20261023/source-baseline/src/task7_sim/episode.py')
    spec=importlib.util.spec_from_file_location('task7_sim._short_task_baseline_episode',path)
    old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
    a=old.EpisodeSampler(POOL,split='validation',device='cuda')
    b=EpisodeSampler(POOL,split='validation',device='cuda',route_length_bounds=None,sampling_deadline=90)
    ar=old.RandomStreams(4605,1);br=RandomStreams(4605,1)
    x=a.sample(ar.for_env(0));y=b.sample(br.for_env(0))
    assert (x.map_id,x.seed)==(y.map_id,y.seed)
    for name in ('base','q','boxes','witness_base','witness_q'):assert torch.equal(getattr(x,name),getattr(y,name))
    for name in ('xyz','quat','length'):assert torch.equal(getattr(x.route,name),getattr(y.route,name))
    for name in ('maps','initial','other'):assert repr(getattr(ar.for_env(0),name).bit_generator.state)==repr(getattr(br.for_env(0),name).bit_generator.state)
    for name,value in a.stats.items():assert value==b.stats[name]


def test_filter_uses_final_arc_length_instead_of_end_distance():
    sampler=EpisodeSampler(POOL,device='cpu',route_length_bounds=[1,2])
    route=Route(torch.tensor([[[0.,0,0],[0.,1,0],[1.,1,0],[1.,0,0]]]),torch.tensor([[[0.,0,0,1.]]*4]))
    assert not sampler.route_length_allowed(route)  # endpoints 1m apart, arc 3m
    for length in (1.,2.):
        route=Route(torch.tensor([[[0.,0,0],[length,0,0]]]),torch.tensor([[[0.,0,0,1.]]*2]))
        assert sampler.route_length_allowed(route)


def test_short_route_keeps_actual_witness_and_distribution_accounting():
    from task7_sim.episode import validate_goal_witness
    from task7_sim.geometry import TruthCollision
    sampler=EpisodeSampler(POOL,split='validation',device='cuda',route_length_bounds=[1,2],sampling_deadline=90)
    episode=sampler.sample(RandomStreams(4718,1).for_env(0))
    assert 1 <= float(episode.route.length.item()) <= 2
    boxes=episode.boxes[None];mask=torch.ones(boxes.shape[:2],device='cuda',dtype=torch.bool)
    _,valid=validate_goal_witness(episode.witness_base,episode.witness_q,episode.route.at(episode.route.length),sampler.kin,sampler.robot,TruthCollision(boxes,mask,robot=sampler.robot))
    assert valid.item()
    assert sum(g['proposals'] for g in sampler.stats['by_map'].values())==sampler.stats['proposals']
    assert sum(g['accepted'] for g in sampler.stats['by_difficulty'].values())==1
    assert sampler.stats['accepted_lengths']==[float(episode.route.length.item())]


def test_pinned_map_deadline_aborts_without_map_substitution():
    sampler=EpisodeSampler(POOL,split='validation',device='cuda',route_length_bounds=[1,2],sampling_deadline=1e-12)
    sampler.entries=sampler.entries[:1];before=sampler.entries.copy()
    with pytest.raises(TimeoutError,match=before[0]['id']):sampler.sample(RandomStreams(4718,1).for_env(0))
    assert sampler.entries==before and sampler.stats['accepted']==0


@pytest.mark.parametrize('bounds',[[2,1],[0,1],[1,float('inf')],[1],[-1,2]])
def test_invalid_bounds_fail_before_sampling(bounds):
    with pytest.raises(ValueError):EpisodeSampler(POOL,route_length_bounds=bounds)
