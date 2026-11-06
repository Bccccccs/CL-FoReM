"""Deterministic, one-episode-per-map evaluation; U.8/P3, SRC-0510."""
import math
import torch
from .sac_discrete import distribution
from task7_sim.g1 import select_g1


class ValidationSelector:
    """Require an explicit predeclared interval and tie rule; no invented default."""
    def __init__(self, interval, tie_rule):
        if not isinstance(interval, int) or interval <= 0 or tie_rule not in ('earliest', 'latest', 'arrival_then_earliest'):
            raise ValueError('validation interval and tie rule must be decided before training')
        self.interval, self.tie_rule = interval, tie_rule
        self.best = -math.inf; self.best_step = None; self.best_arrival = -math.inf

    def consider(self, step, strict_success_rate, arrival_rate=None):
        if not math.isfinite(strict_success_rate) or not 0 <= strict_success_rate <= 1:
            raise ValueError('invalid strict success rate')
        if step % self.interval:
            raise ValueError('validation outside the predeclared schedule')
        if self.tie_rule == 'arrival_then_earliest' and (arrival_rate is None or not math.isfinite(arrival_rate) or not 0 <= arrival_rate <= 1):
            raise ValueError('finite arrival rate required')
        take = strict_success_rate > self.best or (strict_success_rate == self.best and self.tie_rule == 'latest')
        if strict_success_rate == self.best and self.tie_rule == 'arrival_then_earliest':
            take = arrival_rate > self.best_arrival or (arrival_rate == self.best_arrival and step < self.best_step)
        if take:
            self.best_arrival = arrival_rate if arrival_rate is not None else -math.inf
            self.best, self.best_step = strict_success_rate, step
        return take

    def state_dict(self):
        return dict(interval=self.interval, tie_rule=self.tie_rule, best=self.best, best_step=self.best_step, best_arrival=self.best_arrival)

    def load_state_dict(self, state):
        if (state['interval'], state['tie_rule']) != (self.interval, self.tie_rule):
            raise ValueError('validation protocol mismatch')
        self.best, self.best_step = state['best'], state['best_step']
        self.best_arrival = state.get('best_arrival', -math.inf)


@torch.no_grad()
def evaluate_maps(make_environment, map_ids, *, group, model=None, adapter=None):
    """Fresh batch-one environment per map, exactly one episode, no test updates.

    Learned groups require the decided observation/result adapter. G7 supplies
    its own environment factory (read-only task7.19 module).
    """
    if group not in ('G1','G2','G3','G4','G7','stage1'):
        raise ValueError('unsupported evaluation group')
    if group != 'G1' and (model is None or adapter is None):
        raise ValueError('learned policy requires model and explicit environment adapter')
    if len(set(map_ids)) != len(map_ids):
        raise ValueError('each map may appear only once')
    results = []
    if model is not None:
        model.eval()
    for map_id in map_ids:
        env = make_environment(map_id)
        obs, candidates = env.reset(map_ids=[map_id])
        if model is not None:
            model.vcm.reset()
        decisions = no_feasible = changed = arrivals = 0
        sim_seconds = 0.; lower_steps = 0
        while True:
            feasible = candidates['mask'] & (candidates['f_k'][...,0]>0) & (candidates['f_k'][...,3:5].sum(-1)==0)
            no_feasible += int((~feasible.any(-1)).sum())
            if group == 'G1':
                selected, _ = select_g1(candidates['mask'], candidates['f_k'])
            else:
                item = adapter(env, obs, candidates)
                out = model.forward_step(**item)
                selected = out['logits'].argmax(-1)
                if model.stage != '1':
                    a = model.head_a.actor(out['e']).squeeze(-1).masked_fill(~candidates['mask'], -torch.inf)
                    changed += int((a.argmax(-1) != selected).sum())
            step = env.step(selected); decisions += 1
            arrivals += int(step.info['r_t'].get('arrived',torch.zeros(1)).sum())
            sim_seconds += float(step.dt.sum()); lower_steps += int(step.info['r_t']['lower_steps'].sum())
            if bool((step.terminated | step.truncated).all()):
                strict = bool(step.info['strict_success'][0])
                results.append(dict(map_id=map_id, strict_success=strict, decisions=decisions,
                                    sim_seconds=sim_seconds, lower_steps=lower_steps,
                                    no_feasible=no_feasible, head_b_vs_a_changes=changed, arrivals=arrivals))
                break
            obs, candidates = step.observation, step.candidates
    return dict(group=group, episodes=results,
                arrival_rate=sum(r['arrivals'] for r in results)/sum(r['decisions'] for r in results) if results else None,
                strict_success_rate=sum(r['strict_success'] for r in results)/len(results) if results else None)


def scheduled_validation(selector, previous_decisions, decisions, evaluate, save_best):
    """Exact declared decision boundary; never silently round an eval schedule.

    The bounded CLI cannot reach 10000. This hook and selector still make the
    declared future schedule reviewable without running unauthorized training.
    """
    if previous_decisions//selector.interval==decisions//selector.interval:
        return None
    if decisions%selector.interval:
        raise ValueError('batch crossed exact validation boundary; choose an aligned batch, do not round')
    result=evaluate()
    take=selector.consider(decisions,result['strict_success_rate'],result['arrival_rate'])
    if take:save_best()
    return dict(**result,selected_best=take,checkpoint_decisions=decisions)
