# Why does `abnormal_robot` fire? (T17)

**What it checks** (`dexsuite/mdp/terminations.py`, `abnormal_robot_state`): `(|joint_vel| > 2 × joint_vel_limits).any()`
over all 23 robot joints. That is the only condition: no position-limit or torque check. All hand joints have a
velocity limit of 6.28 rad/s, so a joint ends the episode above **12.57 rad/s**.

**Traces:** `scripts/trace_episode.py`, Reorient, final 4,096-env checkpoints, Play config, deterministic policy,
seed 42, 16 envs, first 120 control steps (dt 1/60 s). The state is recorded inside the termination check, before the
reset. Files: `~/runs/traces/reorient_<train>_in_<eval>.npz` (not in git). Summary: `scripts/plot_traces.py`.

| Cell | First episode ends with abnormal_robot | Step of first abnormal_robot: median (min–max) | Joints most often over 2× limit at that step (envs) |
|---|---|---|---|
| PhysX → PhysX | 0/16 (15 still running at step 120, 1 out of bounds) | — | — |
| PhysX → Newton | 14/16 | 16 (10–35) | index_joint_3 (6), middle_joint_1 (4), index_joint_0 / ring_joint_1 / index_joint_2 (4 each) |
| Newton → Newton | 2/16 | 10 (6–15) | index_joint_3, middle_joint_1, ring_joint_1, ring_joint_2 (1 each) |
| Newton → PhysX | 3/16 | 58 (41–84) | ring_joint_1 (2), thumb_joint_0 (1), thumb_joint_2 (1) |

Medians at the breaking step, taken over the envs where that joint is above 2× its limit:

| Cell | Joint | abs(vel) [rad/s] | abs(vel) / limit | abs(target − pos) [rad] | abs(applied torque) [N·m] |
|---|---|---|---|---|---|
| PhysX → Newton | index_joint_3 | 16.5 | 2.62 | 0.21 | 0.50 |
| PhysX → Newton | middle_joint_1 | 27.6 | 4.39 | 0.15 | 0.50 |
| PhysX → Newton | index_joint_0 | 34.2 | 5.45 | 0.09 | 0.50 |
| Newton → PhysX | ring_joint_1 | 25.7 | 4.10 | 2.77 | 0.50 |
| Newton → Newton | ring_joint_1 | 28.7 | 4.57 | 0.39 | 0.49 |

- All of these are **hand** joints. No arm joint went over the limit in any cell.
- At the breaking step the applied torque is about 0.50 N·m in every case, which looks like the finger effort
  limit. The drives are saturated.
- In PhysX → Newton, abs(target − pos) is small (0.1–0.2 rad) while the speed is 2.6–5.5× the limit. The finger is
  moving fast near its target, not chasing a far-away one.

## Caveat: the two engines order the joints differently

The `joint_names` in the traces differ between engines (`scripts/joint_order.py`). The arm joints 0–6 match, but the
16 hand joints are permuted:

- PhysX: `index_0, middle_0, ring_0, thumb_0, index_1, middle_1, …, thumb_3` (by level)
- Newton: `index_0, index_1, index_2, index_3, middle_0, …, thumb_3` (by finger)
- PhysX index → Newton index: `[0..6, 7, 11, 15, 19, 8, 12, 16, 20, 9, 13, 17, 21, 10, 14, 18, 22]`

The policy's action term (`RelativeJointPositionAction`, `joint_names=[".*"]`) and the joint observations follow the
articulation order. If they do, a policy moved to the other engine **reads and drives the wrong hand joints**, and
that alone could explain the 0% cross-engine success in T6/T13 and these early velocity blow-ups. This is not yet
verified by a run with the order remapped (see STATUS.md).

## Plots

`results/plots/trace_reorient_physx_in_newton.png` and `trace_reorient_newton_in_physx.png`: for the cell's 3 joints,
target (dashed) vs actual (solid) position, the same policy in both engines, env 0. Joints are matched by name.
Env 0 does not start from the same pose in both engines: the reset randomisation draws differ.
