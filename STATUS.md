# Status
Updated: 2026-11-13 02:27 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 2107/15000 | 0.047 | 0.013 | 0.0063 | ~24.4 h (6.7–7.0 s/it sharing GPU; rsl_rl prints "00:53:52", which drops the day) |
| T11 Reorient, 4,096 envs | Newton | 3975/15000 | 0.074 | 0.070 | 0.0061 | ~11.0 h (3.5–3.7 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 97% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- Nothing changed except progress. Training-time success (includes exploration noise; single-iteration values are
  noisy): PhysX ~4.7% (flat vs 4.8% an hour ago), Newton 5.5–7.4% (up from 5.9%). Mean reward PhysX 13.19,
  Newton 14.87. ADR still small (~0.006). Newton reaches the 5,000-iteration early-stop check in ~1 h.

## Needs a human
- FYI, cost: sharing the GPU, T10 (PhysX) runs at ~6.8 s/it vs 3.19 s/it alone (T8). Running all 15,000 iterations
  would take ~29 h total (~$105 at $3.65/hr), about twice the T8 estimate (13.3 h, $48.5). The early-stop rule
  starts at 5,000 iterations (PhysX reaches it in ~5.5 h, Newton in ~1 h). Nothing to do unless you want to change the plan.
