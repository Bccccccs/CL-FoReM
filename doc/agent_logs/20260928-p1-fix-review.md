# P1-FIX-028 independent review

- Agent: Codex /root/p1_review
- Start: 2026-09-28T09:52:53+08:00
- Status: active
- Scope: read-only working-tree review against authoritative package HEAD 2a1348a; no code/shared-document edits. Coordinator maintains PROGRESS row.
- Read: AGENTS.md, README, PROGRESS, DECISIONS D29–D33, P1_MEMORY_PLAN, primary P1-FIX log.
- Planned verification: CPU pytest streaming/data suite and focused adversarial probes. Real GPU/cgroup/RSS validation declined pending available container access.

## Verification at 2026-09-28 09:53–09:55 +08

Authoritative package HEAD: `2a1348a`; CPU environment observed `torch 2.7.1+cpu`, `numpy 1.26.4`, Python3.10 temporary dependencies. Actual command:

```bash
PYTHONPATH=/tmp/p1-fix-deps:src/modulation_rl/scripts python3 -m pytest src/modulation_rl/scripts/tests/test_wm_streaming.py src/modulation_rl/scripts/tests/test_wm_data.py -q
```

Exit 0: **22 passed in 2.45s**. This confirms covered CPU synthetic examples, not real-data/resource acceptance.

Focused probes ran with `PYTHONPATH=/tmp/p1-fix-deps:src/modulation_rl/scripts:src/modulation_rl/scripts/tests python3 -` (exit0 each), using temporary directories and `test_wm_streaming.cache_dataset`:

1. Construct two independent caches; set each `max_open=4`; read `cache[np.arange(len(cache))]` on both. Actual `len(first._maps)+len(second._maps)` = **8**. Both caches closed afterward. Tiny chunks reproduce mapping-count failure without stressing resources.
2. Print `sorted(wm.cache.code_identity())`: `__init__.py, cache.py, data.py, dynamics.py, encoder.py, evaluate_prediction.py, losses.py, train_offline.py, val_probe.py`. Actual defining CNN files are absent.
3. Create toy dataset, close cache, mutate only `manifest['episodes'][0]['seed']=987654`, write manifest, rebuild `EpisodeDataset.from_manifest` and `build_cache`. Actual `manifest_seed 987654 episode_seed 0 cache accepted 21`. Temporary data removed by context manager; no repository code/data altered.

## Findings (snapshot before coordinator fixes)

### R1 [P1] Include actual encoder implementation in feature identity

`src/modulation_rl/scripts/wm/cache.py:19–21,103–106` hashes only `wm/*.py`. `FixedEncoder` actually constructs policy/CNN from `scripts/model.py` and `scripts/modulation/models/mapencoder.py` (and dependent encoder implementation). A checkpoint SHA and unchanged wm wrapper do not identify feature computation: changing forward computation in mapencoder while preserving dimensions/weights reuses the existing cache. This can silently mix stale features and changed encoder behavior. Include the actual feature-defining dependency hashes (and relevant numerical/runtime identity), with cache invalidation regression.

Related checkpoint enforcement: `evaluate_prediction.py:92–99` and `val_probe.py:35–39` only enforce checkpoint SHA plus window string. Saved `feature_cache_identity` is not checked against runtime feature semantics/code. After a feature implementation change that rebuilds caches correctly, an old trained model can still be evaluated on incompatible new features. Check the relevant feature computation identity, allowing split/data identity to differ for held-out evaluation. Do not use the entire training/evaluation-script hash as immutable feature semantics if those scripts can change without changing features.

### R2 [P2] Enforce the mapping budget across simultaneous caches

`cache.py:25–29,55–63` bounds each object independently. `train_offline.py:146–150` keeps train and val caches alive; `train_model` alternates train/val accesses without closing inactive cache mappings. Up to eight 128MiB blocks can remain mapped (~1GiB), contrary to the documented total <=4/512MiB budget. Probe reproduced eight mappings. Close inactive phase cache(s), or use one shared total LRU. Cache construction/verification also needs to count transient mappings alongside already-populated caches. Test simultaneous train/val instances, not just one max_open=1 cache.

### R3 [P2] Restore manifest seed identity check

`data.py:110–137,143–147` changed validated `load_episode(path, rec['seed'])` to metadata indexing; `ds.seeds` now comes from the NPZ itself, and subsequent `read_episode` compares NPZ against its own seed. An incorrect manifest seed is accepted despite the old loader rejecting it. This permits contradictory data identity and outcome/report lookup. Probe above confirms complete cache build with manifest seed987654 and NPZ seed0. Explicitly compare NPZ seed to rec seed during indexing, and test from_manifest/build_cache mismatch. Existing standalone validate_episode seed test does not catch this regression.

All findings were sent to coordinator with file locations. Coordinator acknowledged R1/R2 and is implementing fixes; reviewer made no implementation changes.

## Test gaps / remaining acceptance work

- Current suite does not exercise NPZ decompression cap rejection before array loading, oversized/bad-shape/dtype feature blocks, cache manifest identity tampering, interrupted construction/retry, alternate encoder SHA or split invalidation, small standard deviations straddling Normalizer floor, or actual val_probe CLI with saved hidden/normalizer and verified no train reread.
- Near-floor Normalizer implementation is unchanged and visible in dynamics.py; statistics use stable FP64 observation weighting. These observations are not an executed near-floor boundary regression.
- Interrupted builds remain `.partial-*` directories and are not reused; atomic final publication is sensible, but resumability/recovery and disk cleanup are not demonstrated. Do not claim exact training restart or reusable incomplete blocks.
- No periodic training checkpoints/safe-stop mechanism is present in the reviewed train_model snapshot. This is a limitation for long 200-epoch research jobs, not evidence that the finite engineering path fails.

## Declined to judge

- Actual fixed-encoder GPU numerical identity/throughput, CUDA peak allocated/reserved, real-data cache correctness, 100/1000/9600 scaling, RSS/USS/cgroup/page-cache peaks, swap growth, physical task success, ROS non-interference.
- D32 train/test exposure isolation and layout dedup protocol; no new research training/evaluation evidence reviewed.
- P1 predictive benefit or P2 entry gate; passing synthetic CPU tests does not establish either.

ENV.md read during review contains authorized `sg docker -c '<command>'` group entry. Reviewer alerted coordinator, who reports it succeeds and is preparing real isolated resource checks. Those checks were not executed by this review agent.

Status: **review / changes requested**, 2026-09-28T09:55:15+08:00. Deliverable is this log plus findings to coordinator. No code or shared docs edited. Coordinator must record finding dispositions and fresh validation after fixes before claiming M0–M3/M4 acceptance.
2026-09-28T09:55:15+08:00
