# Cross-evaluation · Lift 2×2 (T6)

Measured Thu 12 Nov 2026, 10:52–10:54 UTC, 1× L40S, with `scripts/eval.sh` / `scripts/evaluate.py`.
Policies: final checkpoints `checkpoints/lift_physx/model_14999.pt` and `checkpoints/lift_newton/model_14999.pt`.
Task `Isaac-Dexsuite-Kuka-Allegro-Lift-Play-v0` (ADR at maximum difficulty), `presets=cube`, 256 envs, seed 42,
deterministic actions (policy mean), stop after ≥1,024 completed episodes. Success = the task's own `success_reward`
test at any step of the episode. Interval = 95% Wilson. Raw rows: [`cross_eval.csv`](cross_eval.csv).

| Trained in → run in | Episodes | Success (95% CI) | abnormal_robot | object_out_of_bound | time_out | Control steps |
|---|---|---|---|---|---|---|
| PhysX → PhysX | 1,025 | **95.9%** (94.5–97.0) | 1.1% | 0.5% | 98.4% | 1,440 |
| PhysX → Newton | 1,025 | **0.0%** (0.0–0.4) | **98.3%** | 1.7% | 0.0% | 93 |
| Newton → Newton | 1,071 | **87.0%** (84.9–88.9) | 13.6% | 0.3% | 86.1% | 1,440 |
| Newton → PhysX | 1,024 | **0.0%** (0.0–0.4) | 22.9% | 12.0% | 65.5% | 1,258 |

Summary as a 2×2 (success rate):

| | Run in PhysX | Run in Newton |
|---|---|---|
| Trained in PhysX | 95.9% | 0.0% |
| Trained in Newton | 0.0% | 87.0% |

Notes:
- Neither policy transfers: both drop to 0 successes out of ~1,024 episodes in the other engine.
- They fail in different ways. The PhysX policy in Newton ends almost every episode through `abnormal_robot`, fast:
  1,025 episodes in 93 control steps with 256 envs, so ~23 steps (~0.4 s) per episode. The Newton policy in PhysX
  mostly runs to the time limit (65.5%) without succeeding, with 22.9% `abnormal_robot` and 12.0% of objects
  out of bounds.
- The same-engine numbers agree with training (PhysX ~93–98%, Newton ~86%; training numbers include exploration noise).
- Termination fractions are from the termination manager's flags of the envs that ended each step (see the
  `evaluate.py` fix in `notes/log.md`). A small overlap is possible (time_out + abnormal_robot on the same step), so
  the columns may sum to slightly more than 100% (three rows sum to 100.0%, Newton → PhysX to 100.4%).
