#!/usr/bin/env bash
# Event-driven supervisor for the server agent. Cheap checks every INTERVAL seconds (no Claude usage);
# wakes Claude (agent_tick.sh) only when something changes, or every HEARTBEAT seconds regardless.
#
# Start:  nohup ~/dexterity-physics-engines/scripts/agent_watch.sh > ~/runs/agent/watch.log 2>&1 &
# Stop:   pkill -f agent_watch.sh
# Once:   ~/dexterity-physics-engines/scripts/agent_watch.sh --once     (one wake-up now, then exit)
# History of wake-ups: ~/runs/agent/ticks.log ; full output of each: ~/runs/agent/tick_*.log
set -uo pipefail

REPO="${REPO:-$HOME/dexterity-physics-engines}"
STATE="${STATE:-$HOME/runs/agent}"
INTERVAL="${INTERVAL:-300}"      # 5 minutes between cheap checks
HEARTBEAT="${HEARTBEAT:-3600}"   # wake Claude at least every hour
mkdir -p "$STATE"
cd "$REPO" || exit 1

snapshot() {
  # What counts as "something changed":
  #  - PLAN.md on GitHub changed (someone edited the plan)
  #  - the set of running Isaac Lab training/eval processes changed (a run started, finished or crashed)
  #  - a training log gained a crash signature
  git fetch -q origin main 2>/dev/null
  local plan runs errs
  plan=$(git rev-parse --verify -q origin/main:PLAN.md 2>/dev/null || echo none)
  runs=$(pgrep -f "reinforcement_learning/(train|play)\.py|scripts/evaluate\.py" 2>/dev/null | sort -n | tr '\n' ',')
  errs=$(grep -lE "Traceback|NaN values|CUDA out of memory" "$HOME"/runs/*.log 2>/dev/null | sort | tr '\n' ',')
  echo "plan=${plan:0:12} runs=[$runs] crashed_logs=[$errs]"
}

wake() {
  echo "$(date -u +%FT%TZ) waking agent: $1"
  "$REPO/scripts/agent_tick.sh" "$1"
  snapshot > "$STATE/last_snapshot"     # snapshot AFTER the agent acted, so its own changes don't re-trigger
  date +%s > "$STATE/last_tick"
}

if [[ "${1:-}" == "--once" ]]; then wake "manual --once"; exit 0; fi

echo "$(date -u +%FT%TZ) watcher started (check every ${INTERVAL}s, heartbeat every ${HEARTBEAT}s)"
while true; do
  last=$(cat "$STATE/last_snapshot" 2>/dev/null || echo "")
  last_tick=$(cat "$STATE/last_tick" 2>/dev/null || echo 0)
  cur=$(snapshot)
  now=$(date +%s)
  if [[ "$cur" != "$last" ]]; then
    wake "state changed. before: {$last} now: {$cur}"
  elif (( now - last_tick >= HEARTBEAT )); then
    wake "heartbeat"
  fi
  sleep "$INTERVAL"
done
