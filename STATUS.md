# Status
Updated: 2026-11-13 05:29 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 3671/15000 | 0.049 | 0.010 | 0.0068 | ~21.8 h (6.8–7.0 s/it sharing GPU) |
| T11 Reorient, 4,096 envs | Newton | 6966/15000 | 0.196 | 0.090 | 0.0402 | ~8.1 h (3.6 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 97% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- Second T11 early-stop check: mean training-time success (includes exploration noise) over 6,465–6,964 is 19.13%,
  vs 7.00% over 4,465–4,964 → +12.13 pp ≥ 2 pp, so **keep running**. Logged in `notes/log.md`.
- T11 is improving fast: ADR 0.0175 → 0.0402 in ~1,000 iterations; abnormal_robot steady at ~0.09.
- T10 progress only: success 4.9% (single iteration; ~7–8% recently), reward 12.9, ADR 0.0068. Its early-stop checks
  start at 5,000 (~2.5 h from now).

## Needs a human
- FYI, cost (unchanged): sharing the GPU, T10 (PhysX) runs at ~6.9 s/it vs 3.19 s/it alone (T8). Running all 15,000
  iterations would take ~29 h total (~$105 at $3.65/hr). The early-stop rule may cut it short. Nothing to do unless
  you want to change the plan.
