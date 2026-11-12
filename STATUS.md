# Status
Updated: 2026-11-12 10:21 UTC by the server agent (wake-up: state changed — PLAN.md updated)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T4 Reorient | Newton | 1,735 / 15,000 | 0.00 | 0.86 | 0.00 | stop at 3,000 by plan: ~10:45 UTC (1.15 s/it) |

GPU: 1.6 GB used, 24% utilisation.

## Since last update
- Read the new PLAN.md: T4 is to be stopped at the first wake-up at or after iteration 3,000, then T8 → T9 (4,096-env
  timing runs), then T5. No action yet; T4 is at 1,735.
- T4 abnormal_robot is coming down (0.99 at 1,140 → 0.85–0.86 now); mean episode length ~50–63 steps (was ~25–30).

## Needs a human
- nothing (both earlier questions are answered by the new PLAN.md: T4 stop condition, and 4,096 envs for Reorient).
