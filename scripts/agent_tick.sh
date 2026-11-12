#!/usr/bin/env bash
# One wake-up of the server agent: run Claude Code non-interactively with a fixed allow-list of commands.
# Called by agent_watch.sh; you can also run it by hand: scripts/agent_tick.sh "manual check"
set -uo pipefail

REPO="${REPO:-$HOME/dexterity-physics-engines}"
STATE="${STATE:-$HOME/runs/agent}"
REASON="${1:-manual}"
mkdir -p "$STATE"

# Only one wake-up at a time.
exec 9>"$STATE/tick.lock"
if ! flock -n 9; then echo "$(date -u +%FT%TZ) skipped: a wake-up is already running" >> "$STATE/ticks.log"; exit 0; fi

# Everything the agent may do without asking. Anything else is denied (not waited on).
ALLOWED="Read,Edit,Write,Glob,Grep"
ALLOWED+=",Bash(git status),Bash(git status *),Bash(git diff *),Bash(git log *),Bash(git add *),Bash(git commit *)"
ALLOWED+=",Bash(git pull --rebase),Bash(git pull --rebase *),Bash(git push),Bash(git push origin main),Bash(git fetch *)"
ALLOWED+=",Bash(git rev-parse *),Bash(git ls-files *),Bash(git show *)"
ALLOWED+=",Bash(nvidia-smi),Bash(nvidia-smi *),Bash(ps *),Bash(pgrep *),Bash(grep *),Bash(tail *),Bash(head *)"
ALLOWED+=",Bash(cat *),Bash(ls),Bash(ls *),Bash(du *),Bash(wc *),Bash(date),Bash(date *),Bash(sort *),Bash(awk *)"
ALLOWED+=",Bash(cp *),Bash(mkdir *),Bash(cd *),Bash(sleep *),Bash(find *),Bash(dirname *),Bash(basename *)"
ALLOWED+=",Bash(scripts/train.sh *),Bash(scripts/check_progress.sh *),Bash(scripts/stop_run.sh *)"

TS=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$STATE/tick_$TS.log"
cd "$REPO" || exit 1

PROMPT="$(cat scripts/agent_prompt.md)

Wake-up reason: $REASON
Current time (UTC): $(date -u +%FT%TZ)"

timeout 1800 claude -p "$PROMPT" \
  --add-dir /workspace/isaaclab --add-dir "$HOME/runs" \
  --permission-mode dontAsk --permission-prompts none \
  --allowedTools "$ALLOWED" \
  > "$OUT" 2>&1
CODE=$?

echo "$(date -u +%FT%TZ) exit=$CODE reason=[$REASON] output=$OUT" >> "$STATE/ticks.log"
tail -6 "$OUT" | sed 's/^/    /' >> "$STATE/ticks.log"
exit $CODE
