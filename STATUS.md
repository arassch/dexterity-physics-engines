# Status
Updated: 2026-11-13 06:30 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 4196/15000 | 0.079 | 0.013 | 0.0087 | ~20.8 h (6.9–7.0 s/it sharing GPU) |
| T11 Reorient, 4,096 envs | Newton | 7968/15000 | 0.371 | 0.160 | 0.0995 | ~7.1 h (3.5–3.7 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 96% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- Third T11 early-stop check: mean training-time success (includes exploration noise) over 7,470–7,969 is 31.35%,
  vs 11.17% over 5,470–5,969 → +20.19 pp ≥ 2 pp, so **keep running**. Logged in `notes/log.md`.
- T11: ADR 0.0402 → 0.0995 in ~1,000 iterations. abnormal_robot is climbing with it (500-it mean 0.092 at
  6,500–6,999 → 0.133 at 7,500–7,968; last iteration 0.160). Watching for a NaN crash; numbers in `notes/log.md`.
- T10 progress only: success 7.9%, reward 13.3, ADR 0.0087. Its early-stop checks start at 5,000 (~1.5 h from now).

## Needs a human
- FYI, cost (unchanged): sharing the GPU, T10 (PhysX) runs at ~6.9 s/it vs 3.19 s/it alone (T8). Running all 15,000
  iterations would take ~29 h total (~$105 at $3.65/hr). The early-stop rule may cut it short. Nothing to do unless
  you want to change the plan.
