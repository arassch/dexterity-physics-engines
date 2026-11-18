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
ALLOWED+=",Bash(scripts/eval.sh *),Bash(scripts/record_videos.sh *),Bash(column *),Bash(cut *)"
ALLOWED+=",Bash(scripts/run_isaac.sh *),Bash(scripts/pip_install.sh *),Bash(git rebase --continue)"

TS=$(date -u +%Y%m%dT%H%M%SZ)
OUT="$STATE/tick_$TS.log"
cd "$REPO" || exit 1

# Model: Sonnet for routine wake-ups (checking jobs, STATUS.md). Opus when an open task (todo/running) in PLAN.md has a
# "- model: opus" line (tasks that write or debug code). AGENT_MODEL overrides both.
MODEL="${AGENT_MODEL:-$(awk '
  /^### T/ { if (open && opus) found = 1; open = 0; opus = 0 }
  /^- status: (todo|running)/ { open = 1 }
  /^- model: opus/ { opus = 1 }
  END { if (open && opus) found = 1; print (found ? "opus" : "sonnet") }' PLAN.md)}"

PROMPT="$(cat scripts/agent_prompt.md)

Wake-up reason: $REASON
Current time (UTC): $(date -u +%FT%TZ)"

timeout 1800 claude -p "$PROMPT" --model "$MODEL" --output-format json \
  --add-dir /workspace/isaaclab --add-dir "$HOME/runs" \
  --add-dir "$(readlink -f /workspace/isaaclab/_isaac_sim)/kit/python" \
  --permission-mode dontAsk --permission-prompts none \
  --allowedTools "$ALLOWED" \
  > "$OUT.json" 2> "$OUT"
CODE=$?

# Turn the JSON result into the readable log, and record what the wake-up used.
USAGE=$(python3 - "$OUT.json" "$OUT" <<'PY' 2>/dev/null
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    print("usage: n/a"); sys.exit()
open(sys.argv[2], "a").write(str(d.get("result", "")) + "\n")
u = d.get("usage", {})
tok_in = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
print(f"turns={d.get('num_turns')} in={tok_in} (cached {u.get('cache_read_input_tokens', 0)}) "
      f"out={u.get('output_tokens', 0)} cost_usd={d.get('total_cost_usd', 0):.2f}")
PY
)
[[ -z "$USAGE" ]] && cat "$OUT.json" >> "$OUT" 2>/dev/null

echo "$(date -u +%FT%TZ) exit=$CODE model=$MODEL reason=[$REASON] output=$OUT ${USAGE:-usage: n/a}" >> "$STATE/ticks.log"
tail -6 "$OUT" | sed 's/^/    /' >> "$STATE/ticks.log"
exit $CODE
