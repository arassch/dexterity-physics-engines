# T19 · Fixed corrections for every Newton run

## 1. Velocity-limit emulation: per physics step

The 16 finger joints' velocities are clipped to ±`joint_vel_limits` (mean 6.283 rad/s) once per physics step
(1/120 s, decimation 2), inside the action term's `apply_actions`, using `write_joint_velocity_to_sim_index`.
The per-solver-substep hook (a wrapped `NewtonManager._step_solver` plus CUDA graph re-capture) crashed with
`CUDA error: an illegal memory access` twice, so this is PLAN.md's fallback, which the planning chat accepted on
16 Nov 16:35. Code: `scripts/sysid_harness.py` (`--clamp_mode physics_step`, the default) and
`scripts/train_clamped.py` (training).

## 2. `num_substeps`: **8**

Rule (PLAN.md T19): the smallest of 2/4/8 whose signal-c abnormal_robot count is within 2 of the 8-substep count.

| num_substeps | signal c abnormal_robot (64 envs) | c resets | c finger RMS to PhysX | a / b RMS (rad) | Lift 512 envs, s/iter (50 its) | total 50-it time |
|---|---|---|---|---|---|---|
| 2 | 26/64 | 26/64 | 0.127 rad | 0.0269 / 0.0220 | **0.98** | 52.3 s |
| 4 | 19/64 | 23/64 | 0.101 rad | 0.0269 / 0.0218 | **1.11** | 58.8 s |
| 8 | **16/64** | 18/64 | 0.0995 rad | 0.0270 / 0.0215 | **1.31** | 80.6 s* |

- Blow-ups: `scripts/sysid_harness.py --check --num_envs 64 --num_substeps N` (Reorient-Play env, ADR max, cube parked,
  default params, clamp on). PhysX reference: 0/64 resets on signal c. Logs `~/runs/t19_harness_check64{,_sub4,_sub2}.log`.
- Speed: `scripts/train_clamped.py --num_substeps N`, Lift, 512 envs, seed 42, `presets=cube`, 50 iterations, one run
  at a time. s/iter is the steady-state mean (iterations 20–50, GPU otherwise idle). *The 8-substep run's first
  ~15 iterations overlapped the end of a video recording (about 2.0 s/iter), which inflates its total time. Logs
  `~/runs/t19_speed_sub{2,4,8}.log`.
- 4 substeps is 3 over the 8-substep count, so the rule picks **8**. Speed cost: 8 substeps are ~18% slower per
  iteration than 4 and ~34% slower than 2.
- One seed and 64 envs per count. A difference of 3 (16 vs 19) is within what resampling could plausibly change.
