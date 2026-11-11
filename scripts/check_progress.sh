#!/usr/bin/env bash
# Print a short progress summary for a training log, plus GPU status.
# Usage: ./check_progress.sh ~/runs/lift_physx_full.log
set -euo pipefail
LOG="${1:?usage: check_progress.sh <logfile>}"

grep -E "Learning iteration|Mean reward|success_rate|good_finger_contact|position_tracking|object_out_of_bound|ETA" "$LOG" | tail -8
echo "---"
nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total,power.draw --format=csv
