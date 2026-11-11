#!/usr/bin/env bash
# Part 1: train DexSuite Lift on PhysX (baseline).
# Run from /workspace/isaaclab inside the Isaac Launchable.
#
# Usage:
#   ./train_lift_physx.sh            # full run (15,000 iterations, ~8.3 h on 1x L40S)
#   ./train_lift_physx.sh timing     # 300-iteration timing run (~10 min)
set -euo pipefail

ISAACLAB_DIR="${ISAACLAB_DIR:-/workspace/isaaclab}"
RUN_DIR="${RUN_DIR:-$HOME/runs}"
SEED="${SEED:-42}"
NUM_ENVS="${NUM_ENVS:-512}"   # same on both engines, to keep the comparison fair

if [[ "${1:-full}" == "timing" ]]; then
  ITERS=300;   NAME="lift_physx_timing"
else
  ITERS=15000; NAME="lift_physx_full"
fi

mkdir -p "$RUN_DIR"
cd "$ISAACLAB_DIR"

PYTHONUNBUFFERED=1 nohup ./isaaclab.sh train --rl_library rsl_rl \
  --task Isaac-Dexsuite-Kuka-Allegro-Lift-v0 --headless \
  --num_envs "$NUM_ENVS" physics=physx presets=cube \
  --seed "$SEED" agent.max_iterations="$ITERS" \
  > "$RUN_DIR/$NAME.log" 2>&1 &

echo "Started $NAME (pid $!). Follow with: tail -f $RUN_DIR/$NAME.log"
