#!/usr/bin/env bash
# Run one of this repo's Python scripts with Isaac Lab's Python, in the background, with a live log.
# For the eval-only tasks from T17 on (trace_episode.py, step_response.py, sysid_robot.py, plot_*.py, ...).
#
# Usage:
#   scripts/run_isaac.sh <name_for_log> <script.py> [args...]
#   e.g. scripts/run_isaac.sh trace_reorient_physx_in_newton trace_episode.py --task ... physics=newton_mjwarp presets=cube
# Log: ~/runs/<name_for_log>.log
#
# The process command line contains "dexterity-physics-engines/scripts/<script>.py", which idle_stop.sh and
# agent_watch.sh count as activity.
set -euo pipefail

NAME="${1:?usage: run_isaac.sh <name_for_log> <script.py> [args...]}"
SCRIPT="${2:?usage: run_isaac.sh <name_for_log> <script.py> [args...]}"
shift 2
[[ "$NAME" =~ ^[A-Za-z0-9_.-]+$ ]] || { echo "log name may only contain letters, digits, _ . -" >&2; exit 1; }
[[ "$SCRIPT" =~ ^[a-z0-9_]+\.py$ ]] || { echo "script must be a file name in scripts/, e.g. trace_episode.py" >&2; exit 1; }

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ISAACLAB_DIR="${ISAACLAB_DIR:-/workspace/isaaclab}"
RUN_DIR="${RUN_DIR:-$HOME/runs}"
[[ -f "$REPO/scripts/$SCRIPT" ]] || { echo "no such script: scripts/$SCRIPT" >&2; exit 1; }

mkdir -p "$RUN_DIR"
cd "$ISAACLAB_DIR"
PYTHONUNBUFFERED=1 nohup ./isaaclab.sh -p "$REPO/scripts/$SCRIPT" "$@" > "$RUN_DIR/$NAME.log" 2>&1 &
echo "Started $NAME (pid $!). Follow with: tail -f $RUN_DIR/$NAME.log"
