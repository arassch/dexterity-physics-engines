#!/usr/bin/env bash
# Evaluate one checkpoint in one engine (one cell of the cross-evaluation table), in the background.
#
# Usage:
#   scripts/eval.sh <lift|reorient> <train_engine:physx|newton> <eval_engine:physx|newton> <checkpoint.pt> [episodes]
#   scripts/eval.sh smoke <lift|reorient> <train_engine> <eval_engine> <checkpoint.pt>   # 16 envs, 32 episodes, test only
# Optional last argument (T23): physx|newton = evaluate with that engine's joint/body order matched by name
# (evaluate.py --match_order; label <task>_matched, log name ..._matched). E.g.
#   scripts/eval.sh reorient physx newton <ckpt> 1024 physx
#
# Appends a row to results/cross_eval.csv (smoke runs go to results/cross_eval_smoke.csv).
# Log: ~/runs/eval_<task>_<train>_in_<eval>[_smoke].log
set -euo pipefail

# T21: optional leading `--label <csv label>` and/or `--tag <log suffix>` (before `smoke`/task) override the CSV label
# and add a suffix to the log name, so several checkpoints of one cell can run side by side. E.g.
#   scripts/eval.sh --label lift_sim2real --tag corr_nograsp lift newton physx <ckpt> 1024 newton frozen
LABEL_OVERRIDE=""; TAG=""
while [[ "${1:-}" == --label || "${1:-}" == --tag ]]; do
  case "$1" in --label) LABEL_OVERRIDE="${2:?--label needs a value}" ;; --tag) TAG="${2:?--tag needs a value}" ;; esac
  shift 2
done
SMOKE=0
if [[ "${1:-}" == "smoke" ]]; then SMOKE=1; shift; fi
TASK_SHORT="${1:?usage: eval.sh [smoke] <lift|reorient> <train_engine> <eval_engine> <checkpoint.pt> [episodes]}"
TRAIN="${2:?train engine}"; EVAL="${3:?eval engine}"; CKPT="${4:?checkpoint}"; EPISODES="${5:-1024}"
# T23: optional last argument physx|newton = --match_order <engine> (joints/bodies matched by name to that engine).
# T20: optional last argument `fitted` (after the match engine) = "fitted Newton" (evaluate.py --robot_params
# results/sysid_robot.json; label <task>_fitted, log name ..._fitted). E.g.
#   scripts/eval.sh reorient physx newton <ckpt> 1024 physx fitted
# T26b: optional very last argument `frozen` = evaluate.py --freeze_adr (ADR stays at the Play config's max; label and
# log name get a _frozen suffix). E.g.  scripts/eval.sh reorient physx newton <ckpt> 1024 physx fitted frozen
FROZEN=0
if [[ "${@: -1}" == "frozen" ]] && (( $# >= 5 )); then FROZEN=1; set -- "${@:1:$(($# - 1))}"; fi
FITTED=0
if [[ "${@: -1}" == "fitted" ]] && (( $# >= 6 )); then FITTED=1; set -- "${@:1:$(($# - 1))}"; fi
MATCH=""
if [[ "${@: -1}" =~ ^(physx|newton)$ ]] && (( $# >= 5 )); then
  MATCH="${@: -1}"
  [[ "$EPISODES" == "$MATCH" ]] && EPISODES=1024
fi
if (( FITTED )) && [[ -z "$MATCH" || "$EVAL" != "newton" ]]; then
  echo "fitted needs the match engine before it and eval engine newton" >&2; exit 1
fi

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
LABEL="$TASK_SHORT"; MATCH_ARGS=()
if [[ -n "$MATCH" ]]; then LABEL="${TASK_SHORT}_matched"; NAME="${NAME}_matched"; MATCH_ARGS=(--match_order "$MATCH"); fi
if (( FITTED )); then
  LABEL="${TASK_SHORT}_fitted"; NAME="eval_${TASK_SHORT}_${TRAIN}_in_${EVAL}_fitted"
  MATCH_ARGS+=(--robot_params "$REPO/results/sysid_robot.json")
fi
if (( FROZEN )); then LABEL="${LABEL}_frozen"; NAME="${NAME}_frozen"; MATCH_ARGS+=(--freeze_adr); fi
[[ -n "$LABEL_OVERRIDE" ]] && LABEL="$LABEL_OVERRIDE"
[[ -n "$TAG" ]] && NAME="${NAME}_${TAG}"
if (( SMOKE )); then NUM_ENVS=16; EPISODES=32; CSV="$REPO/results/cross_eval_smoke.csv"; NAME="${NAME}_smoke"; fi

mkdir -p "$RUN_DIR" "$REPO/results"
cd "$ISAACLAB_DIR"
PYTHONUNBUFFERED=1 nohup ./isaaclab.sh -p "$REPO/scripts/evaluate.py" \
  --task "$TASK" --checkpoint "$CKPT" --num_envs "$NUM_ENVS" --episodes "$EPISODES" --seed 42 --headless \
  --label "$LABEL" --train_engine "$TRAIN" --eval_engine "$EVAL" --csv "$CSV" "${MATCH_ARGS[@]}" \
  physics="$PHYSICS" presets=cube \
  > "$RUN_DIR/$NAME.log" 2>&1 &

echo "Started $NAME (pid $!). Follow with: tail -f $RUN_DIR/$NAME.log"
