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

# Cross-evaluation · Reorient 2×2 (T13)

Measured Fri 13 Nov 2026, 20:06–20:09 UTC, 1× L40S, same script and settings as Lift (all four cells in parallel).
Policies: final 4,096-env checkpoints `checkpoints/reorient_physx_4096/model_14999.pt` and
`checkpoints/reorient_newton_4096/model_14999.pt`. Task `Isaac-Dexsuite-Kuka-Allegro-Reorient-Play-v0`,
`presets=cube`, 256 envs, seed 42, deterministic actions, stop after ≥1,024 completed episodes. Interval = 95% Wilson.
Raw rows: [`cross_eval.csv`](cross_eval.csv).

| Trained in → run in | Episodes | Success (95% CI) | abnormal_robot | object_out_of_bound | time_out | Control steps |
|---|---|---|---|---|---|---|
| PhysX → PhysX | 1,027 | **51.5%** (48.5–54.6) | 1.1% | 2.2% | 96.7% | 1,440 |
| PhysX → Newton | 1,027 | **0.0%** (0.0–0.4) | **93.7%** | 6.4% | 0.0% | 141 |
| Newton → Newton | 1,024 | **64.9%** (62.0–67.8) | 28.8% | 0.0% | 71.3% | 1,106 |
| Newton → PhysX | 1,024 | **0.0%** (0.0–0.4) | 24.3% | 11.4% | 64.3% | 1,250 |

Summary as a 2×2 (success rate):

| | Run in PhysX | Run in Newton |
|---|---|---|
| Trained in PhysX | 51.5% | 0.0% |
| Trained in Newton | 0.0% | 64.9% |

Notes:
- Same pattern as Lift: 0 successes in ~1,024 episodes in the other engine, in both directions.
- PhysX → Newton again ends almost every episode with `abnormal_robot`, fast: 1,027 episodes in 141 control steps
  with 256 envs, so ~35 steps (~0.6 s) per episode. Newton → PhysX mostly runs to the time limit (64.3%) without
  succeeding, with 24.3% `abnormal_robot` and 11.4% objects out of bounds, almost the same split as Lift Newton → PhysX
  (65.5 / 22.9 / 12.0%).
- The same-engine numbers agree with training (last-500 means PhysX 49.8%, Newton 64.7%; training numbers include
  exploration noise). Newton → Newton keeps 28.8% `abnormal_robot`, close to its training-time 0.30.
- The two policies reached different ADR levels in training (PhysX 0.50, Newton 0.85), so they were not trained at
  equal difficulty.
