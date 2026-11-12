#!/usr/bin/env bash
# Evaluate one checkpoint in one engine (one cell of the cross-evaluation table), in the background.
#
# Usage:
#   scripts/eval.sh <lift|reorient> <train_engine:physx|newton> <eval_engine:physx|newton> <checkpoint.pt> [episodes]
#   scripts/eval.sh smoke <lift|reorient> <train_engine> <eval_engine> <checkpoint.pt>   # 16 envs, 32 episodes, test only
#
# Appends a row to results/cross_eval.csv (smoke runs go to results/cross_eval_smoke.csv).
# Log: ~/runs/eval_<task>_<train>_in_<eval>[_smoke].log
set -euo pipefail

SMOKE=0
if [[ "${1:-}" == "smoke" ]]; then SMOKE=1; shift; fi
TASK_SHORT="${1:?usage: eval.sh [smoke] <lift|reorient> <train_engine> <eval_engine> <checkpoint.pt> [episodes]}"
TRAIN="${2:?train engine}"; EVAL="${3:?eval engine}"; CKPT="${4:?checkpoint}"; EPISODES="${5:-1024}"

case "$TASK_SHORT" in
  lift)     TASK=Isaac-Dexsuite-Kuka-Allegro-Lift-Play-v0 ;;
  reorient) TASK=Isaac-Dexsuite-Kuka-Allegro-Reorient-Play-v0 ;;
  *) echo "task must be lift or reorient" >&2; exit 1 ;;
esac
physics_of() { case "$1" in physx) echo physx ;; newton) echo newton_mjwarp ;; *) echo "engine must be physx or newton" >&2; exit 1 ;; esac; }
PHYSICS=$(physics_of "$EVAL"); physics_of "$TRAIN" > /dev/null

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ISAACLAB_DIR="${ISAACLAB_DIR:-/workspace/isaaclab}"
RUN_DIR="${RUN_DIR:-$HOME/runs}"
CKPT="$(cd "$(dirname "$CKPT")" && pwd)/$(basename "$CKPT")"
[[ -f "$CKPT" ]] || { echo "no such checkpoint: $CKPT" >&2; exit 1; }

NUM_ENVS=256; CSV="$REPO/results/cross_eval.csv"; NAME="eval_${TASK_SHORT}_${TRAIN}_in_${EVAL}"
if (( SMOKE )); then NUM_ENVS=16; EPISODES=32; CSV="$REPO/results/cross_eval_smoke.csv"; NAME="${NAME}_smoke"; fi

mkdir -p "$RUN_DIR" "$REPO/results"
cd "$ISAACLAB_DIR"
PYTHONUNBUFFERED=1 nohup ./isaaclab.sh -p "$REPO/scripts/evaluate.py" \
  --task "$TASK" --checkpoint "$CKPT" --num_envs "$NUM_ENVS" --episodes "$EPISODES" --seed 42 --headless \
  --label "$TASK_SHORT" --train_engine "$TRAIN" --eval_engine "$EVAL" --csv "$CSV" \
  physics="$PHYSICS" presets=cube \
  > "$RUN_DIR/$NAME.log" 2>&1 &

echo "Started $NAME (pid $!). Follow with: tail -f $RUN_DIR/$NAME.log"
