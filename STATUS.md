# Status
Updated: 2026-11-12 10:31 UTC by the server agent (wake-up: state changed — PLAN.md updated, T6/T7 unblocked)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T4 Reorient | Newton | 2,278 / 15,000 | 0.00 | 0.27 | 0.00 | stop at 3,000 by plan: ~10:45 UTC (1.08 s/it) |

GPU: 1.6 GB used, 26% utilisation.

## Since last update
- T4 abnormal_robot keeps falling: 0.86 at 1,735 → 0.27 at 2,278. Mean reward 4.87. Success and ADR still 0.
- Read the new PLAN.md (T6 cross-eval and T7 videos now `todo`). T6's requirement (≤1 other GPU job) is met, so I
  tried to start the T6 smoke test (`scripts/eval.sh smoke lift physx physx ...`); **the call was denied** by the
  agent's permission allowlist. T6 and T7 left as `todo`; nothing started.

## Needs a human
- The server agent can't run `scripts/eval.sh` or `scripts/record_videos.sh`: `agent_watch.sh` passes an
  `--allowedTools` list containing `scripts/train.sh *`, `scripts/check_progress.sh *`, `scripts/stop_run.sh *` but not
  these two. Add `Bash(scripts/eval.sh *)` and `Bash(scripts/record_videos.sh *)` (and restart the watcher), or T6/T7
  will stay unstarted. Note: if T6 is started while T4 runs, T8 (exclusive) will wait for it to finish.
