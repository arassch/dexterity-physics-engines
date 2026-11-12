#!/usr/bin/env bash
# Train a DexSuite task on a chosen physics engine, in the background, with a live log.
# Run inside the Isaac Launchable (Isaac Lab at /workspace/isaaclab).
#
# Usage:
#   scripts/train.sh <lift|reorient> <physx|newton> [iterations]
#
# Examples:
#   scripts/train.sh lift physx                 # full run, 15,000 iterations
#   scripts/train.sh lift newton 300            # 300-iteration timing run
#   scripts/train.sh lift newton 5000 --resume 2026-11-11_13-06-41 model_10000.pt
#                                               # resume: iterations are *additional*
#   (the older form RESUME_RUN=... CHECKPOINT=... scripts/train.sh ... still works)
#
# Environment overrides: SEED (42), NUM_ENVS (512), ISAACLAB_DIR, RUN_DIR (~/runs)
set -euo pipefail

TASK_SHORT="${1:?usage: train.sh <lift|reorient> <physx|newton> [iterations]}"
ENGINE="${2:?usage: train.sh <lift|reorient> <physx|newton> [iterations]}"
ITERS="${3:-15000}"
if [[ "${4:-}" == "--resume" ]]; then
  RESUME_RUN="${5:?--resume needs <run_folder> <model_N.pt>}"
  CHECKPOINT="${6:?--resume needs <run_folder> <model_N.pt>}"
fi
[[ "$ITERS" =~ ^[0-9]+$ ]] || { echo "iterations must be a number" >&2; exit 1; }

case "$TASK_SHORT" in
  lift)     TASK=Isaac-Dexsuite-Kuka-Allegro-Lift-v0 ;;
  reorient) TASK=Isaac-Dexsuite-Kuka-Allegro-Reorient-v0 ;;
  *) echo "task must be lift or reorient" >&2; exit 1 ;;
esac
case "$ENGINE" in
  physx)  PHYSICS=physx ;;
  newton) PHYSICS=newton_mjwarp ;;
  *) echo "engine must be physx or newton" >&2; exit 1 ;;
esac

ISAACLAB_DIR="${ISAACLAB_DIR:-/workspace/isaaclab}"
RUN_DIR="${RUN_DIR:-$HOME/runs}"
SEED="${SEED:-42}"
NUM_ENVS="${NUM_ENVS:-512}"   # same on both engines, to keep the comparison fair

RESUME_ARGS=()
NAME="${TASK_SHORT}_${ENGINE}_${ITERS}"
if [[ -n "${RESUME_RUN:-}" ]]; then
  RESUME_ARGS=(--resume --load_run "$RESUME_RUN" --checkpoint "${CHECKPOINT:?set CHECKPOINT when resuming}")
  NAME="${NAME}_resume_$(date +%m%d-%H%M)"   # unique, so a second resume never overwrites the first log
fi

mkdir -p "$RUN_DIR"
cd "$ISAACLAB_DIR"

PYTHONUNBUFFERED=1 nohup ./isaaclab.sh train --rl_library rsl_rl \
  --task "$TASK" --headless \
  --num_envs "$NUM_ENVS" physics="$PHYSICS" presets=cube \
  --seed "$SEED" agent.max_iterations="$ITERS" \
  "${RESUME_ARGS[@]}" \
  > "$RUN_DIR/$NAME.log" 2>&1 &

echo "Started $NAME (pid $!)"
echo "Follow with: tail -f $RUN_DIR/$NAME.log"
