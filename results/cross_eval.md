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

# Joints matched by name (T23)

PhysX and Newton list the 16 Allegro hand joints in different articulation orders: PhysX by level (`index_0,
middle_0, ring_0, thumb_0, index_1, …`), Newton by finger (`index_0..3, middle_0..3, …`). The arm matches. The action
term and the `joint_pos`/`joint_vel` observations follow the engine's own order, so in the tables above a policy moved
to the other engine read and drove permuted hand joints. Here, `evaluate.py --match_order <training engine>` pins the
action term, `joint_pos`, `joint_vel` and `hand_tips_state_b` to the training engine's names (`preserve_order=True`).
The run checks the resolved names at startup. The hand-tip bodies already resolved in the same order in both engines.
Order lists are in `results/joint_order.json`. Settings are as above (final checkpoints, 256 envs, seed 42, Play
config, deterministic policy). Labels in `cross_eval.csv`: `lift_matched`, `reorient_matched`.

**Lift**

| Trained in → run in | Episodes | Success (95% CI) | abnormal_robot | object_out_of_bound | time_out | Control steps | Original (T6) |
|---|---|---|---|---|---|---|---|
| PhysX → PhysX | 1,025 | **95.9%** (94.5–97.0) | 1.1% | 0.5% | 98.4% | 1,440 | 95.9% |
| PhysX → Newton | 1,027 | **0.2%** (0.05–0.7) | **98.5%** | 1.6% | 0.0% | 92 | 0.0% |
| Newton → Newton | 1,070 | **86.9%** (84.8–88.8) | 13.6% | 0.4% | 86.1% | 1,440 | 87.0% |
| Newton → PhysX | 1,024 | **0.0%** (0.0–0.4) | 20.4% | 12.5% | 67.1% | 1,332 | 0.0% |

**Reorient** (4,096-env runs)

| Trained in → run in | Episodes | Success (95% CI) | abnormal_robot | object_out_of_bound | time_out | Control steps | Original (T13) |
|---|---|---|---|---|---|---|---|
| PhysX → PhysX | 1,027 | **51.5%** (48.5–54.6) | 1.1% | 2.2% | 96.7% | 1,440 | 51.5% |
| PhysX → Newton | 1,032 | **0.0%** (0.0–0.4) | **95.1%** | 5.0% | 0.0% | 118 | 0.0% |
| Newton → Newton | 1,026 | **63.9%** (61.0–66.8) | 30.0% | 0.0% | 70.1% | 1,103 | 64.9% |
| Newton → PhysX | 1,026 | **0.0%** (0.0–0.4) | 26.8% | 9.9% | 63.3% | 1,238 | 0.0% |

- **Matching the joints by name does not change the result.** The cross-engine cells stay at ~0%: 2 successes in
  1,027 Lift PhysX → Newton episodes, and 0 in each of the other three. The failure modes are as before. PhysX →
  Newton still ends almost every episode with `abnormal_robot` within ~25–30 control steps. Newton → PhysX still
  mostly times out.
- The controls reproduce T6/T13. For PhysX → PhysX the numbers are identical. Newton → Newton is within the intervals
  (Lift 86.9 vs 87.0%, Reorient 63.9 vs 64.9%). In the same-engine cells the remap is the identity, so nothing else
  changed.
- So the original cross-engine cells were confounded by the joint order, but that confound is not what makes transfer
  fail. The gap is elsewhere, in the dynamics (robot drives and joints, or contact). That is what T18–T20 test.

# Fitted robot (T20)

"Fitted Newton" = T19's fixed corrections (finger velocity clamp at ±limit every physics step, `num_substeps` 8)
plus Sara's fit from `results/sysid_robot.json` on the 16 finger joints: armature 0.0131, damping ×1.149, effort
limit ×1.591. These values are written after every reset, so they override the task's startup gain randomisation on
the fingers. The run prints and checks the applied values (all 16 × 256: armature 0.01311, damping 0.1149, effort 0.7955).
All runs use `--match_order <training engine>`. Settings otherwise as above (final checkpoints, 256 envs, seed 42,
Play config, deterministic policy). Label `lift_fitted` / `reorient_fitted` in `cross_eval.csv` (`robot_params=` in
the presets column). The "matched" column is the T23 row with default Newton.

| Task | Trained in → run in | Episodes | Success (95% CI) | abnormal_robot | object_out_of_bound | time_out | Control steps | Matched, default Newton (T23) |
|---|---|---|---|---|---|---|---|---|
| Lift | PhysX → fitted Newton | 1,027 | **1.0%** (0.5–1.8) | **88.7%** | 11.3% | 0.0% | 171 | 0.2%, abnormal 98.5%, 92 steps |
| Lift | Newton → fitted Newton | 1,029 | **94.8%** (93.2–96.0) | 3.4% | 0.5% | 96.1% | 1,440 | 86.9% (84.8–88.8), abnormal 13.6% |
| Lift | Newton → PhysX (unchanged) | 1,024 | 0.0% (0.0–0.4) | 20.4% | 12.5% | 67.1% | 1,332 | same row (reused) |
| Reorient | PhysX → fitted Newton | 1,026 | **0.1%** (0.02–0.6) | **70.9%** | 25.2% | 4.0% | 362 | 0.0%, abnormal 95.1%, 118 steps |
| Reorient | Newton → fitted Newton | 1,024 | **65.6%** (62.7–68.5) | 25.9% | 0.0% | 74.1% | 1,327 | 63.9% (61.0–66.8), abnormal 30.0% |
| Reorient | Newton → PhysX (unchanged) | 1,026 | 0.0% (0.0–0.4) | 26.8% | 9.9% | 63.3% | 1,238 | same row (reused) |

- **The fidelity check fails: PhysX policies still don't work in fitted Newton** (Lift 1.0%, Reorient 0.1%). Fewer
  episodes end in `abnormal_robot` (Lift 98.5 → 88.7%, Reorient 95.1 → 70.9%) and episodes last longer (1,024
  episodes take 171 / 362 control steps instead of 92 / 118). More of them now end with the cube out of bounds
  (Lift 1.6 → 11.3%, Reorient 5.0 → 25.2%).
- **Fitting doesn't break Newton's own policies; for Lift it helps.** Lift Newton → fitted Newton 94.8% vs 86.9% with
  default Newton (the intervals don't overlap), with `abnormal_robot` 13.6 → 3.4%. Reorient 65.6% vs 63.9% (the intervals overlap).
- Newton → PhysX with nothing changed is identical to T23's matched rows (same checkpoints, flags and engine), so
  those rows are reused as T21's uncalibrated baseline: 0.0% in both tasks.

## Sim-to-real (Lift)

T21 step 3, Wed 18 Nov 19:52 UTC. Policies trained in Newton, evaluated **in PhysX** (the "real robot"), 256 envs, seed 42,
`--match_order newton`, `--freeze_adr` (ADR 10, gravity −9.81 throughout). Label `lift_sim2real` in `cross_eval.csv`.

| Policy | Trained in | Episodes | PhysX success (95% CI) | abnormal_robot | out of bound | time_out | steps |
|---|---|---|---|---|---|---|---|
| T21c `lift_newton_corr_nograsp/model_2999.pt` | corrected Newton, no grasp rewards | 1,050 | **0.0%** (0.0–0.4) | 8.5% | 3.8% | 87.7% | 1,440 |
| T21d `lift_newton_corr_dr_nograsp/model_2999.pt` | corrected Newton + finger DR, no grasp rewards | 1,045 | **0.0%** (0.0–0.4) | 7.2% | 2.8% | 90.1% | 1,440 |
| original `lift_newton/model_14999.pt` | default Newton | 1,024 | **0.0%** (0.0–0.4) | 23.5% | 10.3% | 66.3% | 1,305 |

- **No policy trained in Newton lifts the cube in PhysX**, with or without the corrections and finger randomisation
  (training-time success in Newton: 0.90 / 0.92). The corrected runs end far fewer episodes in `abnormal_robot`
  (8.5% / 7.2% vs 23.5%), and most episodes time out, so they fail without blowing up.
- The "home" rows (each policy in its own corrected Newton setup) are not measured yet: `evaluate.py` has no option for
  clamp + 8 substeps without fitted parameters, or for `--finger_dr`.
