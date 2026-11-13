# Status
Updated: 2026-11-13 04:29 UTC by the server agent (wake-up: heartbeat)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T10 Reorient, 4,096 envs | PhysX | 3147/15000 | 0.073 | 0.012 | 0.0066 | ~22.7 h (6.9–7.0 s/it sharing GPU) |
| T11 Reorient, 4,096 envs | Newton | 5964/15000 | 0.121 | 0.091 | 0.0175 | ~9.1 h (3.5–3.7 s/it sharing GPU) |

GPU: 17.1 GB / 46 GB in use, 97–100% utilisation. No Traceback / NaN / OOM in either log.

## Since last update
- First T11 early-stop check: mean training-time success (includes exploration noise) over 5,465–5,964 is 11.13%,
  vs 5.34% over 3,465–3,964 → +5.78 pp ≥ 2 pp, so **keep running**. Logged in `notes/log.md`.
- T10 progress only: success 7.3% (single iteration), reward 12.8, ADR 0.0066. Its early-stop checks start at 5,000
  (~3.6 h from now).
- Newton ADR has started to rise (0.0090 → 0.0175); abnormal_robot 0.083 → 0.091.

## Needs a human
- FYI, cost (unchanged): sharing the GPU, T10 (PhysX) runs at ~6.9 s/it vs 3.19 s/it alone (T8). Running all 15,000
  iterations would take ~29 h total (~$105 at $3.65/hr). The early-stop rule may cut it short. Nothing to do unless
  you want to change the plan.
