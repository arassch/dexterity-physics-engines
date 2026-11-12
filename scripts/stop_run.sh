#!/usr/bin/env bash
# Stop one Isaac Lab training/eval process by PID, refusing anything else.
# Usage: scripts/stop_run.sh <pid>
set -euo pipefail
PID="${1:?usage: stop_run.sh <pid>}"
[[ "$PID" =~ ^[0-9]+$ ]] || { echo "not a pid: $PID" >&2; exit 1; }
CMD=$(ps -o args= -p "$PID" 2>/dev/null || true)
if [[ "$CMD" != *"reinforcement_learning/train.py"* && "$CMD" != *"reinforcement_learning/play.py"* && "$CMD" != *"scripts/evaluate.py"* ]]; then
  echo "refusing: pid $PID is not an Isaac Lab training/eval process: ${CMD:-<no such process>}" >&2
  exit 1
fi
kill -INT "$PID"
sleep 20
if kill -0 "$PID" 2>/dev/null; then kill "$PID"; fi
echo "stopped $PID"
