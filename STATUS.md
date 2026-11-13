# Status
Updated: 2026-11-13 01:27 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 1588/15000 | 0.048 | 0.014 | 0.0045 | ~25.7 h (6.9 s/it sharing GPU; rsl_rl prints "01:57:20", which drops the day) |
| T11 Reorient, 4,096 envs | Newton | 2983/15000 | 0.059 | 0.071 | 0.0061 | ~12.1 h (3.6 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 96–98% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- Nothing changed except progress. Training-time success (includes exploration noise) keeps rising: PhysX 2.1% → 4.8%,
  Newton 2.4% → 5.9%. Mean reward PhysX 11.82, Newton 15.35. ADR still small (0.005–0.006).

## Needs a human
- FYI, cost: sharing the GPU, T10 (PhysX) runs at ~6.9 s/it vs 3.19 s/it alone (T8). Running all 15,000 iterations
  would take ~29 h total (~$105 at $3.65/hr), about twice the T8 estimate (13.3 h, $48.5). The early-stop rule
  starts at 5,000 iterations (PhysX reaches it in ~6.5 h, Newton in ~2 h). Nothing to do unless you want to change the plan.
