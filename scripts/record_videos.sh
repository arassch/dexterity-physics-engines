#!/usr/bin/env bash
# Record a short clip of a policy at several checkpoints, for the "watch it learn" shot. Runs in the foreground,
# one checkpoint after another (each is a separate Isaac Lab play run with --video).
#
# Usage:
#   scripts/record_videos.sh <lift|reorient> <physx|newton> <run_folder> [checkpoint numbers...]
#   e.g. scripts/record_videos.sh lift physx 2026-11-11_11-08-26 250 1000 3000 8000 14999
#
# Clips are copied to ~/runs/videos/<task>_<engine>/model_<N>.mp4 (not committed to git: too big).
# Isaac Lab's play script writes every clip to <run_folder>/videos/play/ under the same name, so each one is moved
# out right after it is recorded.
set -uo pipefail

# Always run in the background (one call records all checkpoints; can take ~15 min). Progress goes to the log below.
if [[ -z "${RECORD_VIDEOS_CHILD:-}" ]]; then
  mkdir -p "$HOME/runs"
  RECORD_VIDEOS_CHILD=1 nohup "$0" "$@" > "$HOME/runs/videos_${1:-x}_${2:-x}_driver.log" 2>&1 &
  echo "Started recording in the background (pid $!). Progress: tail -f ~/runs/videos_${1:-x}_${2:-x}.log"
  exit 0
fi

TASK_SHORT="${1:?usage: record_videos.sh <lift|reorient> <physx|newton> <run_folder> [N ...]}"
ENGINE="${2:?engine}"; RUN="${3:?run folder}"; shift 3
CHECKPOINTS=("$@"); [[ ${#CHECKPOINTS[@]} -gt 0 ]] || CHECKPOINTS=(250 1000 3000 8000 14999)

case "$TASK_SHORT" in
  lift)     TASK=Isaac-Dexsuite-Kuka-Allegro-Lift-Play-v0 ;;
  reorient) TASK=Isaac-Dexsuite-Kuka-Allegro-Reorient-Play-v0 ;;
  *) echo "task must be lift or reorient" >&2; exit 1 ;;
esac
case "$ENGINE" in physx) PHYSICS=physx ;; newton) PHYSICS=newton_mjwarp ;; *) echo "engine must be physx or newton" >&2; exit 1 ;; esac

ISAACLAB_DIR="${ISAACLAB_DIR:-/workspace/isaaclab}"
RUN_PATH="$ISAACLAB_DIR/logs/rsl_rl/dexsuite_kuka_allegro/$RUN"
OUT="$HOME/runs/videos/${TASK_SHORT}_${ENGINE}"
LOG="$HOME/runs/videos_${TASK_SHORT}_${ENGINE}.log"
VIDEO_STEPS="${VIDEO_STEPS:-360}"     # 360 control steps at 60 Hz = one 6 s episode
mkdir -p "$OUT"
[[ -d "$RUN_PATH" ]] || { echo "no such run folder: $RUN_PATH" >&2; exit 1; }

cd "$ISAACLAB_DIR"
for N in "${CHECKPOINTS[@]}"; do
  CKPT="$RUN_PATH/model_${N}.pt"
  if [[ ! -f "$CKPT" ]]; then echo "skip: $CKPT not found" | tee -a "$LOG"; continue; fi
  echo "=== $(date -u +%FT%TZ) recording $TASK_SHORT/$ENGINE model_$N" | tee -a "$LOG"
  rm -f "$RUN_PATH"/videos/play/*.mp4 2>/dev/null
  PYTHONUNBUFFERED=1 ./isaaclab.sh play --rl_library rsl_rl --task "$TASK" \
    --num_envs 4 --checkpoint "$CKPT" --video --video_length "$VIDEO_STEPS" --seed 42 --headless \
    physics="$PHYSICS" presets=cube >> "$LOG" 2>&1
  CLIP=$(ls -t "$RUN_PATH"/videos/play/*.mp4 2>/dev/null | head -1)
  if [[ -n "$CLIP" ]]; then
    mv "$CLIP" "$OUT/model_${N}.mp4" && echo "saved $OUT/model_${N}.mp4 ($(du -h "$OUT/model_${N}.mp4" | cut -f1))" | tee -a "$LOG"
  else
    echo "FAILED: no video produced for model_$N (see $LOG)" | tee -a "$LOG"
  fi
done
ls -la "$OUT"
