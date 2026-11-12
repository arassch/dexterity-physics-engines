# Status
Updated: 2026-11-12 23:25 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 573/15000 | 0 | 0.009 | 0 | ~27–30 h (7.4 s/it sharing GPU; rsl_rl prints "03:09:27", which drops the day) |
| T11 Reorient, 4,096 envs | Newton | 1047/15000 | 0 | 0.050 | 0 | ~14.0 h (3.7–3.9 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 98–100% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- Nothing changed except progress. Success still 0 in both runs (training-time, includes exploration noise);
  mean reward PhysX 7.91, Newton 9.28.

## Needs a human
- FYI, cost: sharing the GPU, T10 (PhysX) runs at 7.4 s/it vs 3.19 s/it alone (T8). Running all 15,000 iterations
  would take ~27–30 h (~$100–110 at $3.65/hr), about twice the T8 estimate (13.3 h, $48.5). The early-stop rule
  starts at 5,000 iterations (PhysX reaches it in ~9 h). Nothing to do unless you want to change the plan.
