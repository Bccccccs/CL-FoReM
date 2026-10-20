#!/usr/bin/env bash
# Installed-only host entry: read-only host freeze gate, supervised Gazebo/CUDA
# campaign, fixed persistent campaign ledger. Parent receipt is mandatory.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
run=${1:-}; acceptance=${2:-}
[[ $# == 2 && $run =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]] || { echo 'usage: run_task4_formal.sh RUN_ID PARENT_ACCEPTANCE_PATH' >&2; exit 12; }
[[ -f $root/scripts/task4_formal_entry.py ]] || { echo 'refused: preparation draft is not installed' >&2; exit 12; }
# Never launch ROS for a disabled/missing/failed/stale freeze or acceptance.
PYTHONPATH="$root/scripts" python3 "$root/scripts/task4_formal_entry.py" --mode check --host --acceptance "$acceptance"
relative=$(python3 - "$root" "$acceptance" <<'PY'
import sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();path=Path(sys.argv[2]).resolve()
if root not in path.parents:raise SystemExit('parent acceptance must be under FoReM')
print(path.relative_to(root))
PY
)
# Outer process supervision only; independent actor watchdog retains the actual
# frozen 90000s campaign cap and does not inherit this cleanup allowance.
cap=$(python3 - "$root/config/task4/sac_baseline.json" <<'PY'
import json,sys
print(int(json.load(open(sys.argv[1]))['all_wall_total_cap_s'])+10)
PY
)
export FOREM_CHECK_TIMEOUT="$cap"
exec bash "$root/scripts/run_task4_localization.sh" "$run" -- python3 -u scripts/task4_formal_entry.py --mode campaign --acceptance "$relative"
