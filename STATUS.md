# Status
Updated: 2026-11-13 09:34 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 5843/15000 | 0.103 | 0.010 | 0.0169 | ~17.4 h (6.7 s/it sharing GPU) |
| T11 Reorient, 4,096 envs | Newton | 10764/15000 | 0.553 | 0.287 | 0.5172 | ~4.3 h (3.8–3.9 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 97–98% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- T10 early-stop check #2: mean training-time success (includes exploration noise) 11.60% (5,342–5,841) vs 5.97%
  (3,342–3,841) → +5.63 pp, **keep running**.
- T11 check #6: 49.79% (10,262–10,761) vs 37.66% (8,262–8,761) → +12.13 pp, **keep running**. ADR 0.3512 → 0.5172;
  abnormal_robot 500-it mean rose to 0.289 (from 0.254). Watching for NaN.
- Both checks are logged in `notes/log.md`.

## Needs a human
- FYI, cost (unchanged): sharing the GPU, T10 (PhysX) runs at ~6.7 s/it vs 3.19 s/it alone (T8). If neither run
  stops early, T10 needs ~17 more hours (~$63 at $3.65/hr). Nothing to do unless you want to change the plan.
