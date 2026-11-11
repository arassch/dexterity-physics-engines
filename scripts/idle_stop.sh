#!/usr/bin/env bash
# Stop this Brev instance once no Isaac Lab training or playback has run for IDLE_MINUTES.
# Meant for unattended stretches (overnight). It does NOT count interactive work in
# VS Code as activity, so don't leave it running while you're working without a run going.
#
# Needs the Brev CLI, logged in (see setup/ENVIRONMENT.md).
# Usage (from anywhere):
#   nohup ~/dexterity-physics-engines/scripts/idle_stop.sh > ~/runs/idle_stop.log 2>&1 &
# Stop the watcher:
#   pkill -f idle_stop.sh
set -uo pipefail

INSTANCE="${INSTANCE:-isaac-launchable-0d404b}"
IDLE_MINUTES="${IDLE_MINUTES:-20}"
BREV="${BREV:-$HOME/bin/brev}"
PATTERN="isaaclab.sh (train|play)|train_rsl_rl.py|play_rsl_rl.py|reinforcement_learning/(train|play).py"

idle=0
echo "$(date -u +%FT%TZ) watching; will stop $INSTANCE after $IDLE_MINUTES idle minutes"
while true; do
  if pgrep -f -- "$PATTERN" > /dev/null; then
    idle=0
  else
    idle=$((idle + 1))
    echo "$(date -u +%FT%TZ) no training running ($idle/$IDLE_MINUTES min)"
  fi
  if (( idle >= IDLE_MINUTES )); then
    echo "$(date -u +%FT%TZ) idle for $IDLE_MINUTES min: stopping $INSTANCE"
    "$BREV" stop "$INSTANCE"
    exit 0
  fi
  sleep 60
done
