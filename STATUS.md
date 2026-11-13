# Status
Updated: 2026-11-13 11:36 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 6938/15000 | 0.189 | 0.012 | 0.0275 | ~15.2 h (6.5–6.8 s/it sharing GPU) |
| T11 Reorient, 4,096 envs | Newton | 12628/15000 | 0.580 | 0.276 | 0.7447 | ~2.4 h (3.8–3.9 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 97% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- T10 early-stop check #4: mean training-time success (includes exploration noise) 16.70% (6,440–6,939) vs 8.71%
  (4,440–4,939) → +7.99 pp, **keep running**.
- T11 check #8: 58.46% (12,131–12,630) vs 49.07% (10,131–10,630) → +9.39 pp, **keep running**. ADR 0.6533 → 0.7447;
  abnormal_robot 500-it mean flat at 0.286. The margin is shrinking (+11.2 → +9.4 pp) but far above 2 pp.
- Both checks are logged in `notes/log.md`.

## Needs a human
- FYI, cost (unchanged): sharing the GPU, T10 (PhysX) runs at ~6.6 s/it vs 3.19 s/it alone (T8). Its ETA of ~15 h
  assumes sharing; once T11 finishes (~2.4 h) T10 should speed up to roughly 3.2 s/it (~7–8 h left at that point).
  Nothing to do unless you want to change the plan.
