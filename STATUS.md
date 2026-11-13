# Status
Updated: 2026-11-13 08:33 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 5294/15000 | 0.108 | 0.014 | 0.0130 | ~18.5 h (6.5–6.7 s/it sharing GPU) |
| T11 Reorient, 4,096 envs | Newton | 9833/15000 | 0.469 | 0.242 | 0.3512 | ~5.2 h (3.7–3.9 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 97–100% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- First T10 early-stop check: mean training-time success (includes exploration noise) over 4,795–5,294 is 9.75%,
  vs 5.78% over 2,795–3,294 → +3.97 pp ≥ 2 pp, so **keep running** (but only ~2 pp above the threshold).
- Fifth T11 check: 44.43% (9,334–9,833) vs 30.08% (7,334–7,833) → +14.35 pp, **keep running**. The gain is slowing.
  ADR jumped 0.2156 → 0.3512, mean reward fell 11.27 → 8.94, abnormal_robot 500-it mean 0.254. Watching for NaN.
- Both checks are logged in `notes/log.md`.

## Needs a human
- FYI, cost (unchanged): sharing the GPU, T10 (PhysX) runs at ~6.5 s/it vs 3.19 s/it alone (T8). Running all 15,000
  iterations would take ~28 h total (~$100 at $3.65/hr). T10 could hit the early-stop rule soon (+4.0 pp at the first
  check). Nothing to do unless you want to change the plan.
