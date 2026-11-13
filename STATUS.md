# Status
Updated: 2026-11-13 10:35 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 6391/15000 | 0.132 | 0.010 | 0.0205 | ~15.8 h (6.6 s/it sharing GPU) |
| T11 Reorient, 4,096 envs | Newton | 11698/15000 | 0.577 | 0.285 | 0.6533 | ~3.5 h (3.9 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 97% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- T10 early-stop check #3: mean training-time success (includes exploration noise) 14.31% (5,892–6,391) vs 7.10%
  (3,892–4,391) → +7.21 pp, **keep running**.
- T11 check #7: 54.60% (11,199–11,698) vs 43.36% (9,199–9,698) → +11.24 pp, **keep running**. ADR 0.5172 → 0.6533;
  abnormal_robot 500-it mean levelled off at 0.284 (0.289 before). Mean reward down 9.26 → 7.77 as ADR rises.
- Both checks are logged in `notes/log.md`.

## Needs a human
- FYI, cost (unchanged): sharing the GPU, T10 (PhysX) runs at ~6.6 s/it vs 3.19 s/it alone (T8). If neither run
  stops early, T10 needs ~16 more hours (~$58 at $3.65/hr). Once T11 finishes (~3.5 h) T10 should speed up.
  Nothing to do unless you want to change the plan.
