#!/usr/bin/env python3
"""task6.6 section 1: extract `policy_state_dict` from the cbl-uploaded SAC checkpoints (pure copy, verified tensor by tensor).

Runs inside forem-dev (CPU only). Reads results/task6/t6.6-ckpt/raw/<dir>/<file> (copies of the read-only archive files, sha256 checked
against results/task6/t6.6-precheck/archive_sha256.txt), writes results/task6/t6.6-ckpt/<tag>.pt (a plain policy state_dict, the format
eval_task6_final.py --policy loads) and results/task6/t6.6-ckpt/manifest.json. The source files are cbl's own local uploads, so
torch.load(weights_only=False) is used if the safe loader refuses them (recorded per file in the manifest).
"""
import ray  # noqa: F401  (import before torch, see task3_env.py)
import hashlib
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
CK = ROOT / "results" / "task6" / "t6.6-ckpt"
REF_HASHES = ROOT / "results" / "task6" / "t6.6-precheck" / "archive_sha256.txt"
SRC_PREFIX = "archive/husky_ur5/mm_husky_ws/src/modulation_rl/scripts/"
TAGS = [("so%02d" % i, "checkpoints_simpleobstacle", "sac_checkpoint_husky_ur5_%d" % (i * 1000)) for i in range(1, 15)]
TAGS.append(("pp4000", "checkpoints_pnp_plus", "sac_checkpoint_husky_ur5_4000"))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def opt_step(sd):
    steps = [s.get("step") for s in sd["state"].values() if "step" in s]
    steps = [int(torch.as_tensor(x).item()) for x in steps]
    return dict(first=steps[0] if steps else None, n_params_with_step=len(steps), all_equal=len(set(steps)) <= 1)


def main():
    ref = {}
    for line in open(REF_HASHES):
        h, p = line.split()
        ref[p] = h
    manifest = dict(note="policy_state_dict extracted verbatim; torch.equal checked on every tensor", entries=[])
    for tag, d, fname in TAGS:
        src = CK / "raw" / d / fname
        src_sha = sha256(src)
        want = ref[SRC_PREFIX + d + "/" + fname]
        if src_sha != want:
            sys.exit("SHA MISMATCH %s: got %s want %s" % (src, src_sha, want))
        loader = "weights_only=True"
        try:
            ck = torch.load(src, map_location="cpu", weights_only=True)
        except Exception as exc:  # noqa: BLE001
            loader = "weights_only=False (safe loader failed: %r)" % (str(exc)[:120],)
            ck = torch.load(src, map_location="cpu", weights_only=False)
        pol = ck["policy_state_dict"]
        out = CK / (tag + ".pt")
        torch.save({k: v.detach().clone() for k, v in pol.items()}, out)
        back = torch.load(out, map_location="cpu", weights_only=True)
        if set(back) != set(pol):
            sys.exit("KEY MISMATCH " + tag)
        for k in pol:
            if not (back[k].dtype == pol[k].dtype and back[k].shape == pol[k].shape and torch.equal(back[k], pol[k])):
                sys.exit("TENSOR MISMATCH %s %s" % (tag, k))
        e = dict(tag=tag, source=SRC_PREFIX + d + "/" + fname, raw_copy=str(src.relative_to(ROOT)), source_sha256=src_sha, ref_sha256=want,
                 sha256_match=True, extracted=str(out.relative_to(ROOT)), extracted_sha256=sha256(out), loader=loader,
                 top_keys=sorted(ck), n_policy_keys=len(pol), policy_opt_step=opt_step(ck["policy_optimizer_state_dict"]),
                 critic_opt_step=opt_step(ck["critic_optimizer_state_dict"]), torch_equal_all_tensors=True)
        manifest["entries"].append(e)
        print(tag, "keys", len(pol), "policy_step", e["policy_opt_step"]["first"], "critic_step", e["critic_opt_step"]["first"], loader, flush=True)
    json.dump(manifest, open(CK / "manifest.json", "w"), indent=1)


if __name__ == "__main__":
    main()
