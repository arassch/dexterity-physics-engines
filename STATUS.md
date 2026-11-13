# Status
Updated: 2026-11-13 13:38 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 8028/15000 | 0.246 | 0.012 | 0.0514 | ~13 h at 6.6 s/it sharing; ~6.5 h once T11 ends |
| T11 Reorient, 4,096 envs | Newton | 14483/15000 | 0.605 | 0.297 | 0.8439 | ~35 min (3.8 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 97% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- T10 early-stop check #6: mean training-time success (includes exploration noise) 23.83% (7,529–8,028) vs 12.50%
  (5,529–6,028) → +11.32 pp, **keep running**.
- T11 check #10: 64.88% (13,984–14,483) vs 58.53% (11,984–12,483) → +6.35 pp, **keep running**. ADR 0.8195 → 0.8439;
  abnormal_robot 500-it mean 0.268 → 0.281. Should finish normally in ~35 min; backup at the next wake-up.
- Both checks are logged in `notes/log.md`.

## Needs a human
- FYI, cost (unchanged): sharing the GPU, T10 (PhysX) runs at ~6.6 s/it vs 3.19 s/it alone (T8). Once T11 finishes
  (~35 min) T10 should speed up to roughly 3.2 s/it, leaving ~6 h. Nothing to do unless you want to change the plan.
