# task8.3 ghost sensor implementation

- run-id: t8-exec-20261026; owner Codex t83_sensor; actual model gpt-6.1-sol / medium (parent dispatch).
- Authorization: task8.1–8.6 implementation SRC-0990; own robot.py, perception.py, test_ghost_sensor.py, sensor.json, this log and own RESULTS only. No task7 edits/training/GPU/subagents.
- Recommendations: GPT6.1sol / medium and Sonnet5.5 / medium for sensor/index protocol; high for complex geometry ambiguity, per TASK. Actual and recommendation separate.
- Read AGENTS, forem/AGENTS, ENV, doc README/PROGRESS, parent and own three docs, SRC-0984–0990; parent owns shared progress/source updates. Existing main dirty preserved. Existing robot schema4 indexes and allowed/zero exemptions remain intact; explicit detection mask for two velodyne bodies only.
- Tests first: sensor-only body fixture with real transforms/config/body, non-sensor top_plate/arm-arm positive. Then real PCD SceneBatch scan/ground/origin/occlusion/Grid tests. CPU only; own cumulative allocation <=120s, commands <=60s via run_budget owner8.3, container timeout.

## CPU test-first and implementation record

- `0e0712faf8`: expected red, 2 failed (task8_sim.robot absent), rc1, elapsed 1.966861736s. Full argv/output in shared ledger/log.
- Added subclass with schema4 guard, source config deep copy, sensor-body check mask; retained original body list/allowed/zero tables. Raw contact APIs apply sensor detection policy; body boxes keep original indices for provenance.
- `1425518155`: 2 passed, rc0, elapsed 2.066977139s. Both explicit sensors ignored; real fixed top_plate and arm-arm checks preserved in independent relocated-sphere fixtures using real FK/config/body engine. These fixtures do not establish physical mesh accuracy.
- `d83078a73d`: expected red, 3 failed (task8_sim.perception absent), rc1, elapsed 2.017007009s.
- Added ghost-v1 config and panorama: same base z=.5m/pixel-centre rays/6m/slant/ground/Depth shapes; actual SceneBatch runtime query; caps/body ignored by design, self flags false denote disabled self occlusion.
- `368a942019`: 3 passed, 5 deselected, rc0, elapsed 2.267318589s. Real Kinematics.solve_world receives the same GhostRobotGeometry, accepted FK-generated target and returned collision/ground-clear pose.
- All commands use forem-dev CPU torch.float64, CUDA_VISIBLE_DEVICES empty, OMP/OPENBLAS=1; actual argv/container timeout in budget.json. Own spent 8.318164473s of 120s allocation so far. No GPU, no training. Geometry source remains pending; no scan acceptance claimed.

## Real SceneBatch integration, GPU authorization and review handoff

- 8.2 delivered real scene.py; `6ea597a13a` ran all own 8 CPU tests, rc0, 8 passed, pytest2.89s / ledger3.418797879s. Actual cube-pool manifest, no scene mock. Verified near x=1.25m occluder, scene-inside zero return, fixed base-relative sensor/ground/range, Grid landing-only, original inside-self all-invalid counterexample and real robot q-independence, environment/ground positive collision.
- Parent explicitly approved GPU0 cumulative<=30s within original 120s quota; queried nvidia-smi compute apps empty before run. `f69aae3409`: GPU parity1 passed/8 deselected, rc0, ledger3.569126088s; actual cuda:0/float32; valid masks identical, depth max abs5.881453315e-7m vs CPU64; synchronized combined query0.610648517s, peak allocated20,502,016bytes. Explicit2e-5m tolerance engineering gate (same max6m, no voxel tolerance/scan parameter change), measured error also below old task7 test2e-6m. Base/arm/self collision flags match. GPU lock released immediately to parent; no remaining GPU jobs.
- `f00db1cc7c`: all current task8 tests53 passed/2 skipped, rc0, ledger8.826349398s; GPU authorization flags unset/CPU only. Started before parent steering to avoid broad run; completed naturally before steering processed. Snapshot only, not final acceptance of concurrently edited8.2. No more broad tests run. Parent owns independent final review.
- Total own measured worker elapsed24.132437838s/120s. No timeout; two expected initial red runs recorded. No training/oldsource writes.
- Final own hashes and inherited inputs recorded in task8.3 RESULTS. Remaining: parent independent code/evidence audit and global source registration;8.4 reset/step same-config wiring and full task acceptance. Own status review, not done. No running sessions.
