# Status
Updated: 2026-11-13 07:31 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 4744/15000 | 0.094 | 0.009 | 0.0103 | ~19.6 h (6.5–6.6 s/it sharing GPU) |
| T11 Reorient, 4,096 envs | Newton | 8900/15000 | 0.404 | 0.234 | 0.2156 | ~6.2 h (3.9 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 96–100% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- Fourth T11 early-stop check: mean training-time success (includes exploration noise) over 8,401–8,900 is 38.91%,
  vs 18.42% over 6,401–6,900 → +20.49 pp ≥ 2 pp, so **keep running**. Logged in `notes/log.md`.
- T11: ADR 0.0995 → 0.2156 in ~930 iterations; abnormal_robot still climbing with it (500-it mean 0.172 at
  7,901–8,400 → 0.205 at 8,401–8,900; last iteration 0.234). Iteration time up from ~3.6 to 3.9 s. Watching for NaN.
- T10 progress only: success 9.4%, reward 13.8, ADR 0.0103. First early-stop check at 5,000 (next wake-up or so).

## Needs a human
- FYI, cost (unchanged): sharing the GPU, T10 (PhysX) runs at ~6.5 s/it vs 3.19 s/it alone (T8). Running all 15,000
  iterations would take ~28 h total (~$100 at $3.65/hr). The early-stop rule may cut it short. Nothing to do unless
  you want to change the plan.
