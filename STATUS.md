# Status
Updated: 2026-11-13 20:12 UTC by the server agent (wake-up: state changed, no training processes left)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| none running (T13 evals finished) | | | | | | |

## Since last update
- T13 (Reorient cross-eval): all four cells finished. Rows are in `results/cross_eval.csv` (not committed yet), and the
  eval logs show no Traceback or Error:
  - PhysX→PhysX 51.5% [48.5, 54.6], abnormal_robot 0.011 (1,027 eps)
  - PhysX→Newton 0.0% [0.0, 0.4], abnormal_robot 0.937 (1,027 eps)
  - Newton→Newton 64.9% [62.0, 67.8], abnormal_robot 0.288 (1,024 eps)
  - Newton→PhysX 0.0% [0.0, 0.4], abnormal_robot 0.243 (1,024 eps)
- Not done yet: `results/cross_eval.md` Reorient section, Finding 3, README, setting T13 `done`, commit/push.

## Needs a human
- **Bash was denied to the server agent on this wake-up** ("don't ask" permission mode), so I couldn't run
  `git pull`, `pgrep`, `nvidia-smi`, commit or push. This STATUS.md edit and `results/cross_eval.csv` exist only on
  the server, uncommitted. Please check the agent's permission settings. Once Bash works again, the next wake-up
  can finish the T13 write-up.
