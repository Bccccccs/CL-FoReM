#!/bin/bash
set -euo pipefail
repo=/home/ybc/projects/CL-FoReM
sg docker -c "docker run --rm --name forem-task12-causes-r5 --user $(id -u):$(id -g) --cpuset-cpus 10-11 -e OMP_NUM_THREADS=2 -e OPENBLAS_NUM_THREADS=2 -e MPLCONFIGDIR=/tmp/matplotlib -e PYTHONDONTWRITEBYTECODE=1 -e PYTHONPATH=/original/frozen-source/src -v $repo/forem/results/task12/t12-abc-20261104-r1:/original:ro -v $repo/forem/results/task12/t12-cost32-20261104-r3:/baseline:ro -v $repo/forem/results/task12/t12-radius075-20261104-r4:/probe:ro -v $repo/forem/results/task12/t12-causes-20261105-r5:/output -v $repo/forem/scripts/task12_failure_analysis.py:/analysis.py:ro mm_husky:node01 /opt/python310/bin/python3 -u /analysis.py"
