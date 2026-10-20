#!/usr/bin/env python3
"""task4.7 read-only counterexample: does GaussianPolicy.predict() squash the action twice?

Compares, for the SAME network parameters and observations,
  (a) predict(eval=True)          -- what Task3/Task4 SAC.select_action() executes in eval,
  (b) the mode of the distribution used by sample()/update_parameters (single tanh, SB3 SquashedDiagGaussianDistribution),
  (c) predict(eval=False) vs sample()  with identical torch RNG state.
Writes JSON. No ROS / Gazebo needed; imports only the policy.  Run inside forem-dev:
  python3 scripts/audit_scwm_policy_tanh.py --out results/task4/<run>/policy_tanh_audit.json
"""
import ray  # noqa: F401  (import order contract, see task3_env.py)
import argparse, json, sys
from pathlib import Path

import numpy as np
import torch
import gym

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src" / "modulation_rl" / "scripts"))
from model import GaussianPolicy  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    torch.manual_seed(a.seed)
    rs = gym.spaces.Box(-100, 100, (41,), dtype=np.float32)
    ms = gym.spaces.Box(-1.1, 10.1, (120, 120, 1), dtype=np.float32)
    asp = gym.spaces.Box(-1.0, 1.0, (3,), dtype=np.float32)
    pol = GaussianPolicy(ms, rs, 3, [512, 512, 256], asp, use_sde=False)
    pol.eval()
    B = 64
    rob = torch.randn(B, 41)
    mp = (torch.rand(B, 120, 120, 1) > 0.9).float()
    with torch.no_grad():
        mean, log_std, kw = pol.forward(mp, rob)
        a_pred_eval = pol.predict(mp, rob, eval=True)
        single = torch.tanh(mean)                      # mode of SquashedDiagGaussianDistribution (what sample() optimises)
        torch.manual_seed(123)
        a_sample, lp = pol.sample(mp, rob)
        torch.manual_seed(123)
        a_pred_stoch = pol.predict(mp, rob, eval=False)
        # gaussian pre-squash action for the same RNG
        torch.manual_seed(123)
        g = mean + log_std.exp() * torch.randn_like(mean)
        single_stoch = torch.tanh(g)
    # scale the mean so that |mean| spans the saturating range, to show the compression
    m2 = torch.linspace(-3, 3, 13)
    out = dict(
        eval_predict_equals_single_tanh_mode=bool(torch.allclose(a_pred_eval, single, atol=1e-6)),
        eval_predict_equals_double_tanh_mode=bool(torch.allclose(a_pred_eval, torch.tanh(single), atol=1e-6)),
        eval_max_abs_diff_vs_single=float((a_pred_eval - single).abs().max()),
        stoch_predict_equals_sample_action=bool(torch.allclose(a_pred_stoch, a_sample, atol=1e-6)),
        stoch_predict_equals_double_tanh_of_sample=bool(torch.allclose(a_pred_stoch, torch.tanh(a_sample), atol=1e-6)),
        stoch_max_abs_diff_vs_sample=float((a_pred_stoch - a_sample).abs().max()),
        sample_equals_single_tanh_of_gaussian=bool(torch.allclose(a_sample, single_stoch, atol=1e-6)),
        executed_action_abs_max_over_batch=float(a_pred_stoch.abs().max()),
        sampled_action_abs_max_over_batch=float(a_sample.abs().max()),
        range_demo=dict(gaussian_mean=m2.tolist(), single_tanh=torch.tanh(m2).tolist(), double_tanh=torch.tanh(torch.tanh(m2)).tolist()),
        note="double tanh bounds the executed action to +-tanh(1)=0.7616 while sample()/update_parameters optimise a single-tanh policy over (-1,1)",
        torch=str(torch.__version__), seed=a.seed)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "range_demo"}, indent=1))


if __name__ == "__main__":
    main()
