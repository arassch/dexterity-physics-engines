# Status
Updated: 2026-11-13 14:20 UTC by the server agent (wake-up: state changed, T11 process exited)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 8363/15000 | 0.275 | 0.010 | 0.0576 | ~6 h if it speeds up to ~3.2 s/it alone (T8) |

GPU: 9.3 GB / 46 GB in use. No Traceback / NaN / OOM in the T10 log.

## Since last update
- **T11 (Reorient Newton, 4,096 envs) finished normally** at 15,000 iterations (57,142 s, 0 resumes). Training-time
  success (includes exploration noise) last-500 mean 64.65%, abnormal_robot ~0.30, ADR 0.853, reward ~9.1. Backed up
  `model_14999.pt`, configs, final excerpt; RUNS.md, README, notes/log.md updated; T11 set `done`.
- T10 early-stop check #7: 25.05% (7,864–8,363) vs 14.23% (5,864–6,363) → +10.81 pp, **keep running**.
- T13 (Reorient cross-eval) waits for T10 `done`. Nothing else to start.

## Needs a human
- nothing
