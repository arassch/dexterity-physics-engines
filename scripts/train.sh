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
#   scripts/train.sh reorient physx 300 --envs 4096   # other number of environments
#   scripts/train.sh lift newton 5000 --resume 2026-11-11_13-06-41 model_10000.pt
#                                               # resume: iterations are *additional*
#   (the older form RESUME_RUN=... CHECKPOINT=... scripts/train.sh ... still works)
#
# Environment overrides: SEED (42), NUM_ENVS (512), ISAACLAB_DIR, RUN_DIR (~/runs)
set -euo pipefail

TASK_SHORT="${1:?usage: train.sh <lift|reorient> <physx|newton> [iterations] [--envs N] [--resume <run_folder> <model_N.pt>]}"
ENGINE="${2:?usage: train.sh <lift|reorient> <physx|newton> [iterations] [--envs N] [--resume <run_folder> <model_N.pt>]}"
ITERS=15000
if [[ -n "${3:-}" && "${3}" != --* ]]; then ITERS="$3"; shift 3; else shift 2; fi
while [[ $# -gt 0 ]]; do
  case "$1" in
    --envs)   NUM_ENVS="${2:?--envs needs a number}"; shift 2 ;;
    --resume) RESUME_RUN="${2:?--resume needs <run_folder> <model_N.pt>}"; CHECKPOINT="${3:?--resume needs <run_folder> <model_N.pt>}"; shift 3 ;;
    *) echo "unknown option: $1" >&2; exit 1 ;;
  esac
done
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
NUM_ENVS="${NUM_ENVS:-512}"   # default; PLAN.md says when a task uses another value

RESUME_ARGS=()
[[ "$NUM_ENVS" =~ ^[0-9]+$ ]] || { echo "--envs must be a number" >&2; exit 1; }
NAME="${TASK_SHORT}_${ENGINE}_${ITERS}"
[[ "$NUM_ENVS" != 512 ]] && NAME="${NAME}_${NUM_ENVS}envs"
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
