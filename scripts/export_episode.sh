#!/usr/bin/env bash
# Record a policy's motion (joints, links, cube, target) to JSON for replay outside Isaac Lab, e.g. in Unreal.
# Runs in the background; ~1-2 minutes.
#
# Usage:
#   scripts/export_episode.sh <lift|reorient> <train_engine:physx|newton> <play_engine:physx|newton> <checkpoint.pt> [steps]
#   e.g. scripts/export_episode.sh reorient physx physx checkpoints/reorient_physx_4096/model_14999.pt
#
# Output: ~/runs/exports/<task>_<train>_in_<play>.json, and for PhysX playback also <same>.usd (flattened scene).
# Log:    ~/runs/export_<task>_<train>_in_<play>.log
set -euo pipefail

TASK_SHORT="${1:?usage: export_episode.sh <lift|reorient> <train_engine> <play_engine> <checkpoint.pt> [steps]}"
TRAIN="${2:?train engine}"; PLAY="${3:?play engine}"; CKPT="${4:?checkpoint}"; STEPS="${5:-720}"
case "$TASK_SHORT" in
  lift)     TASK=Isaac-Dexsuite-Kuka-Allegro-Lift-Play-v0 ;;
  reorient) TASK=Isaac-Dexsuite-Kuka-Allegro-Reorient-Play-v0 ;;
  *) echo "task must be lift or reorient" >&2; exit 1 ;;
esac
case "$PLAY" in physx) PHYSICS=physx ;; newton) PHYSICS=newton_mjwarp ;; *) echo "engine must be physx or newton" >&2; exit 1 ;; esac
case "$TRAIN" in physx|newton) ;; *) echo "engine must be physx or newton" >&2; exit 1 ;; esac

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ISAACLAB_DIR="${ISAACLAB_DIR:-/workspace/isaaclab}"
CKPT="$(cd "$(dirname "$CKPT")" && pwd)/$(basename "$CKPT")"
[[ -f "$CKPT" ]] || { echo "no such checkpoint: $CKPT" >&2; exit 1; }
NAME="${TASK_SHORT}_${TRAIN}_in_${PLAY}"
OUT_DIR="$HOME/runs/exports"; mkdir -p "$OUT_DIR"
STAGE_ARGS=()
[[ "$PLAY" == physx ]] && STAGE_ARGS=(--stage_out "$OUT_DIR/$NAME.usd")

cd "$ISAACLAB_DIR"
PYTHONUNBUFFERED=1 nohup ./isaaclab.sh -p "$REPO/scripts/export_episode.py" \
  --task "$TASK" --checkpoint "$CKPT" --num_envs 4 --steps "$STEPS" --seed 42 --headless \
  --label "$NAME" --out "$OUT_DIR/$NAME.json" "${STAGE_ARGS[@]}" \
  physics="$PHYSICS" presets=cube \
  > "$HOME/runs/export_$NAME.log" 2>&1 &
echo "Started export $NAME (pid $!). Follow with: tail -f ~/runs/export_$NAME.log"
