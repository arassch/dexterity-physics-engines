# Status
Updated: 2026-11-13 00:26 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 1069/15000 | 0.021 | 0.011 | 0.0027 | ~27.5 h (7.1 s/it sharing GPU; rsl_rl prints "03:03:34", which drops the day) |
| T11 Reorient, 4,096 envs | Newton | 1992/15000 | 0.024 | 0.063 | 0.0033 | ~13.3 h (3.6–3.9 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 97–99% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- Nothing changed except progress. Success has started to move off 0 in both runs (PhysX 2.1%, Newton 2.4–3.0%;
  training-time, includes exploration noise), and ADR has started (0.003). Mean reward PhysX 10.67, Newton 12.08–13.40.

## Needs a human
- FYI, cost: sharing the GPU, T10 (PhysX) runs at ~7.1 s/it vs 3.19 s/it alone (T8). Running all 15,000 iterations
  would take ~29 h total (~$105 at $3.65/hr), about twice the T8 estimate (13.3 h, $48.5). The early-stop rule
  starts at 5,000 iterations (PhysX reaches it in ~7.8 h from now). Nothing to do unless you want to change the plan.
