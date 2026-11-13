# Status
Updated: 2026-11-13 03:28 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 2627/15000 | 0.065 | 0.011 | 0.0064 | ~23.4 h (6.7–6.9 s/it sharing GPU; rsl_rl prints "23:51:36", which drops the day) |
| T11 Reorient, 4,096 envs | Newton | 4968/15000 | 0.073 | 0.083 | 0.0090 | ~10.3 h (3.7 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 97% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- Nothing changed except progress. Training-time success (includes exploration noise; single-iteration values are
  noisy): PhysX 4.8–6.5% (vs ~4.7% an hour ago), Newton 7.3–8.3% (vs 5.5–7.4%). Mean reward PhysX 13.0–13.7,
  Newton 14.4–15.4. ADR still small (PhysX 0.0064, Newton 0.0090). Newton abnormal_robot up slightly (0.070 → 0.083).
- T11 is 32 iterations short of 5,000; the first early-stop check happens at the next wake-up.

## Needs a human
- FYI, cost: sharing the GPU, T10 (PhysX) runs at ~6.8 s/it vs 3.19 s/it alone (T8). Running all 15,000 iterations
  would take ~29 h total (~$105 at $3.65/hr), about twice the T8 estimate (13.3 h, $48.5). The early-stop rule
  starts at 5,000 iterations (PhysX reaches it in ~4.5 h, Newton at the next wake-up). Nothing to do unless you want
  to change the plan.
