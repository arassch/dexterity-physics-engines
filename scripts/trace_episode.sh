#!/usr/bin/env bash
# Trace the first control steps of one checkpoint in one engine (T17), in the background, via run_isaac.sh.
#
# Usage:
#   scripts/trace_episode.sh <lift|reorient> <train_engine:physx|newton> <eval_engine:physx|newton> <checkpoint.pt> [num_envs] [steps]
#
# Output: ~/runs/traces/<task>_<train>_in_<eval>.npz   Log: ~/runs/trace_<task>_<train>_in_<eval>.log
set -euo pipefail

TASK_SHORT="${1:?usage: trace_episode.sh <lift|reorient> <train_engine> <eval_engine> <checkpoint.pt> [num_envs] [steps]}"
TRAIN="${2:?train engine}"; EVAL="${3:?eval engine}"; CKPT="${4:?checkpoint}"; NUM_ENVS="${5:-16}"; STEPS="${6:-120}"

case "$TASK_SHORT" in
  lift)     TASK=Isaac-Dexsuite-Kuka-Allegro-Lift-Play-v0 ;;
  reorient) TASK=Isaac-Dexsuite-Kuka-Allegro-Reorient-Play-v0 ;;
  *) echo "task must be lift or reorient" >&2; exit 1 ;;
esac
physics_of() { case "$1" in physx) echo physx ;; newton) echo newton_mjwarp ;; *) echo "engine must be physx or newton" >&2; exit 1 ;; esac; }
PHYSICS=$(physics_of "$EVAL"); physics_of "$TRAIN" > /dev/null

REPO="$(cd "$(dirname "$0")/.." && pwd)"
RUN_DIR="${RUN_DIR:-$HOME/runs}"
CKPT="$(cd "$(dirname "$CKPT")" && pwd)/$(basename "$CKPT")"
[[ -f "$CKPT" ]] || { echo "no such checkpoint: $CKPT" >&2; exit 1; }
CELL="${TASK_SHORT}_${TRAIN}_in_${EVAL}"

exec "$REPO/scripts/run_isaac.sh" "trace_${CELL}" trace_episode.py \
  --task "$TASK" --checkpoint "$CKPT" --num_envs "$NUM_ENVS" --steps "$STEPS" --seed 42 --headless \
  --out "$RUN_DIR/traces/${CELL}.npz" physics="$PHYSICS" presets=cube
