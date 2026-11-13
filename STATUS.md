# Status
Updated: 2026-11-13 12:37 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 7484/15000 | 0.237 | 0.012 | 0.0374 | ~14.2 h (6.6–6.7 s/it sharing GPU) |
| T11 Reorient, 4,096 envs | Newton | 13558/15000 | 0.637 | 0.272 | 0.8195 | ~1.5 h (3.8–3.9 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 96% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- T10 early-stop check #5: mean training-time success (includes exploration noise) 19.81% (6,985–7,484) vs 10.32%
  (4,985–5,484) → +9.49 pp, **keep running**.
- T11 check #9: 63.44% (13,059–13,558) vs 54.42% (11,059–11,558) → +9.02 pp, **keep running**. ADR 0.7447 → 0.8195;
  abnormal_robot 500-it mean 0.286 → 0.268.
- Both checks are logged in `notes/log.md`.

## Needs a human
- FYI, cost (unchanged): sharing the GPU, T10 (PhysX) runs at ~6.6 s/it vs 3.19 s/it alone (T8). Its ETA of ~14 h
  assumes sharing; once T11 finishes (~1.5 h) T10 should speed up to roughly 3.2 s/it (~6 h left at that point, so ~7.5 h total).
  Nothing to do unless you want to change the plan.
