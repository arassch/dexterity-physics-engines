# Working notes

## 2026-11-11: Setup and first PhysX runs

**Cloud setup**
- Brev Isaac Launchable (Isaac Sim 6.0.1, Isaac Lab 3.0.0-beta2-post1) on AWS `g6e.4xlarge` (1× L40S).
- Provisioning failed with "internal server error" in Stockholm and Frankfurt; succeeded in us-east-1.
- The VS Code terminal is a non-root container: no `sudo` or `tmux`. Using `nohup` + `PYTHONUNBUFFERED=1`.
  Without unbuffered output, the redirected log updates in bursts and stdout/stderr lines appear out of order.

**Task discovery**
- `list_envs.py --keyword Dexsuite --show_presets`: Lift and Reorient both support
  `physics: newton_mjwarp, physx`, plus domain presets `cube`, `shapes`, `state` and a range of camera modes.
- Using `presets=cube` on both engines (Newton can't do multi-shape spawning).

**Timing run: Lift, PhysX, 512 envs, 300 iterations**
- ~2.0 s per iteration, ~8,000 steps/s, 16,384 steps per iteration (512 × 32).
- Collection 1.9 s vs learning 0.1 s: the simulation is the bottleneck, not PPO.
- At 300 iterations: mean reward ≈ −0.4 (action penalties dominate), `fingers_to_object` ≈ +0.03 (reaching),
  success ≈ 0–2%, ~36% of episodes end with the cube knocked out of bounds.
- Full run of 15,000 iterations ≈ 8.3 h ≈ $30 at $3.65/hr.

**To investigate (Part 3/4)**
- PhysX start-up warning: *"TGS solver with enable_external_forces_every_iteration=False may cause noisy velocities."*
  Check whether the trained policy depends on this, e.g. by evaluating with the flag flipped.

**Full runs started**
- Lift · PhysX, 15,000 iterations, seed 42: run `2026-11-11_11-08-26`.
- Lift · Newton, same settings with `physics=newton_mjwarp`: run `2026-11-11_13-06-41`, sharing the GPU with the PhysX run.
- Repo cloned on the Brev box; pushes work through VS Code's built-in GitHub sign-in (device code), no token stored.

**Lift · PhysX: finished (late evening)**
- Final training metrics (last iterations, exploration noise on): success rate **~93–98%**, mean reward ~30,
  ADR level **0.99**, `abnormal_robot` terminations **~2%**.
- Progression: reaching by ~300 iterations; `good_finger_contact` 0.001 → 0.14 between iterations 300 and ~1,000
  (grasping starts, reward turns positive); lifting to target comes later.
- Speed: ~2.15 s/iteration on its own on the L40S (GPU ~64% busy, 5.3 of 46 GB used).

**Lift · Newton: NaN crash at iteration 10,234**
- RSL-RL stopped with: `ValueError: The observation group 'proprio' ... contains NaN values`.
  The simulation diverged in at least one environment.
- Last iterations before the crash: success 73–89%, `abnormal_robot` **~19%**, ADR **0.97**, action std **1.96**,
  action penalties ≈ −1.0. Large actions under near-maximum randomisation, with MuJoCo Warp going unstable.
- The crash happened around 19:00 and was only noticed at 23:13, so that GPU slot sat idle ~4 h.
  (Motivation for `scripts/idle_stop.sh` and for checking runs more often.)
- Resumed from `model_10000.pt` with `--resume --load_run 2026-11-11_13-06-41 --checkpoint model_10000.pt`.
  On resume, `agent.max_iterations` means *additional* iterations, so it was set to 5,000.

## 2026-11-12: Lift done on both engines

**Lift · Newton: finished after resume**
- Final training metrics: success rate **~86%**, mean reward ~38, ADR **0.98**, `abnormal_robot` **~14%**.
- No further NaN after resuming, even with ADR back near maximum. So high ADR alone doesn't trigger the divergence.

**Finding 1: Newton has ~7× more abnormal-robot terminations than PhysX, at the same ADR level**

| | PhysX | Newton |
|---|---|---|
| Training success (final) | ~93–98% | ~86% |
| `abnormal_robot` terminations | ~2% | ~14% |
| ADR level (final) | 0.99 | 0.98 |
| NaN divergences | 0 | 1 (iteration 10,234) |

Both trained under equally hard randomisation, so the difference comes from the engine, not the curriculum.
Training-time numbers include exploration noise; the deterministic cross-evaluation (Part 3) is the fair measurement.
Open question for Part 4: *what* goes abnormal (joint limits? penetration recovery? contact jitter?).
Plan: record abnormal episodes in slow motion and log contact forces and joint velocities.

**Fairness check: the PhysX and Newton configs differ only in the solver**
- Diffed `configs/lift_physx/env.yaml` against `configs/lift_newton/env.yaml`, and `agent.yaml` likewise.
- Identical on both: physics `dt = 1/120 s` (**120 Hz**), `decimation = 2` (policy at **60 Hz**), **6 s** episodes,
  512 envs, rewards, observations, actions, randomisation and ADR settings, and all PPO settings.
- Differences (solver only):
  - PhysX: TGS (`solver_type: 1`), up to 255 position / 255 velocity iterations,
    `enable_external_forces_every_iteration: false` (the "noisy velocities" warning), CCD off.
  - Newton: MuJoCo Warp, `implicitfast` integrator, elliptic friction cone, `impratio: 10`, 100 solver iterations,
    15 line-search iterations, **`num_substeps: 2`** (so effectively 240 Hz physics inside each 120 Hz step).
- So "higher reward but lower success on Newton" is *not* from longer episodes. Still to explain.

**Operational notes**
- Two training runs share one L40S fine. Speed per run drops, total throughput goes up, and the machine cost is shared.
  Speed comparisons between engines therefore need separate, isolated benchmark runs.
- Checkpoints are saved every 250 iterations, ~25 MB each (they include optimiser state).
  The repo keeps only the video milestones (250, 1000, 3000, 8000) and the final checkpoint per run.
- Mistake to avoid: picking a run folder by grepping configs for "physx" matched the 300-iteration *timing* run first.
  Identify runs by start time / log_dir, or by the folder that contains the final `model_14999.pt`.
- In the VS Code container `$HOME` is `/root`, so `~/runs` is `/root/runs`.

**Reorient · PhysX** started 23:21 (Wed), at 14,225 / 15,000 by 09:22. Faster than expected.

## 2026-11-12: Reorient PhysX finished (server agent)

**Reorient · PhysX (T3) finished normally, but it barely learned the task.** Run folder `2026-11-11_23-23-11`,
`Training time: 38364.77 seconds` (10 h 40 min), no Traceback. Final checkpoint `model_14999.pt` backed up.
Training-time numbers (include exploration noise):

| Iteration | success_rate | Curriculum/adr | abnormal_robot | Mean reward |
|---|---|---|---|---|
| 1,000 | 0.000 | 0.0000 | 0.008 | 2.73 |
| 3,000 | 0.042 | 0.0007 | 0.018 | 8.85 |
| 5,000 | 0.031 | 0.0059 | 0.010 | 11.35 |
| 10,000 | 0.018 | 0.0049 | 0.012 | 10.98 |
| 14,000 | 0.038 | 0.0079 | 0.022 | 10.96 |
| 15,000 (final) | 0.047 | 0.0042 | 0.014 | 11.41 |
| mean of last 500 | **0.042** | **0.0047** | **0.012** | |

- Success plateaued at ~3–5% from iteration ~3,000 on; reward plateaued at ~11 from ~4,000. ADR never left ~0.005
  (Lift reached 0.99), so the curriculum never got harder.
- Final: `Metrics/object_pose/orientation_error: 2.3451` (rad), `position_error: 0.1558`,
  `Mean action std: 1.58` (Lift is not comparable yet; noting for later), `time_out: 0.871`, `object_out_of_bound: 0.115`.
- Iteration time ~2.0–2.1 s mid-run (shared GPU), 3.5–3.8 s at the end (shared with Newton Reorient).
- The policy lifts and holds the cube (position reward ~1.1) but does not rotate it to the target.

**Reorient · Newton (T4) is in an early phase where most episodes end through `abnormal_robot`.** Run folder
`2026-11-12_09-31-46`. Training-time numbers:

| Iteration | abnormal_robot | Mean episode length | Mean reward |
|---|---|---|---|
| 100 | 0.213 | 300.4 | -1.32 |
| 200 | 0.623 | 105.4 | -0.44 |
| 300 | 0.902 | 51.4 | -0.24 |
| 500 | 0.989 | 25.2 | -0.14 |
| 1,100 | 0.991 | 33.7 | -0.12 |

Success 0, ADR 0, position_tracking 0. Mean reward is negative and goes up as episodes get shorter, so the policy may
have learned that triggering an `abnormal_robot` termination early is the best option (`early_termination` penalty
only -0.003). **Lift Newton went through the same phase and recovered** (from `lift_newton_full.log`):
abnormal_robot 0.986 / 0.988 / 0.984 / 0.826 / 0.224 / 0.093 at iterations 500 / 1,000 / 1,500 / 2,000 / 2,500 / 3,000,
episode length 25 → 275 by 2,500, success 0.40 by 4,500. So this is not yet a problem. Recheck T4 at ~3,000.
It is still running (ETA ~7 h at ~1.13 s/iteration, now alone on the GPU).

**Correction (planning chat, Thu 12 Nov):** the ADR curriculum (`dexsuite/mdp/curriculums.py`, `DifficultyScheduler`)
raises an environment's difficulty by one level after **any successful episode** (the sticky `succeeded` flag of the
`success` reward term) and lowers it otherwise. Earlier notes and slides said it needed orientations within
`rot_std/2`; that was wrong. The conclusion for T3 stands: Reorient rarely succeeded, so ADR stayed near 0.
Success itself (`dexsuite/mdp/rewards.py`, `success_reward`): thumb + at least one finger in contact with the object
and position error < `pos_std` (and orientation error < `rot_std` for Reorient), at any step of the episode.

## 2026-11-12 10:49 UTC: Reorient Newton (T4) stopped at iteration 3,315 by plan (server agent)

Stopped with `scripts/stop_run.sh` (plan: stop at the first wake-up at or after 3,000). Run folder
`2026-11-12_09-31-46`; backed up `model_3250.pt` (latest saved; the run reached 3,315), configs, last 60 log lines.
Training-time numbers (with exploration noise) every 250 iterations, T4 next to T2 (Lift Newton) at the same iterations:

| Iteration | T4 abnormal_robot | T4 ep. length | T4 mean reward | T4 success | T2 abnormal_robot | T2 ep. length | T2 mean reward | T2 success |
|---|---|---|---|---|---|---|---|---|
| 250 | 0.831 | 64.6 | -0.30 | 0 | 0.823 | 54.0 | -0.27 | 0 |
| 500 | 0.986 | 25.1 | -0.13 | 0 | 0.981 | 29.9 | -0.16 | 0 |
| 750 | 0.998 | 28.8 | -0.13 | 0 | 0.997 | 20.5 | -0.10 | 0 |
| 1,000 | 0.996 | 27.4 | -0.11 | 0 | 0.989 | 29.6 | -0.12 | 0 |
| 1,250 | 0.985 | 29.4 | -0.10 | 0 | 0.988 | 26.8 | -0.09 | 0 |
| 1,500 | 0.972 | 33.4 | -0.09 | 0 | 0.979 | 28.6 | -0.09 | 0 |
| 1,750 | 0.819 | 68.4 | 0.08 | 0 | 0.951 | 41.4 | -0.10 | 0 |
| 2,000 | 0.615 | 141.6 | 1.20 | 0 | 0.829 | 70.0 | -0.03 | 0 |
| 2,250 | 0.283 | 248.7 | 4.32 | 0 | 0.507 | 174.9 | 1.15 | 0 |
| 2,500 | 0.081 | 304.9 | 6.15 | 0 | 0.216 | 275.6 | 3.35 | 0 |
| 2,750 | 0.075 | 291.8 | 6.94 | 0 | 0.134 | 288.6 | 4.73 | 0 |
| 3,000 | 0.059 | 317.8 | 8.14 | 0 | 0.094 | 304.1 | 6.14 | 0 |
| 3,250 | 0.098 | 309.5 | 8.23 | 0 | 0.079 | 313.0 | 6.55 | 0 |

**It recovered.** The two Newton runs follow almost the same early-termination curve (~0.99 abnormal_robot for
iterations 500–1,500, then a fast drop); Reorient got out ~250 iterations sooner than Lift. At the stop: success 0,
ADR 0, abnormal_robot 0.10, time_out 0.81, object_out_of_bound 0.09, orientation error 2.36 rad, 1.09 s/iteration
alone on the GPU. Lift Newton was also at 0 success at 3,250 (0.40 by 4,500), so 3,315 iterations say nothing about
whether Reorient Newton would learn to succeed.

## 2026-11-12: T6 smoke test, and a fix to `scripts/evaluate.py` (server agent)

**Fix (mechanical, termination counting only):** `evaluate.py` summed `extras["log"]["Episode_Termination/<name>"]`
on every step with done envs, treating it as a count. In Isaac Lab 3.0.0 that value is
`self._last_episode_dones.float().mean(dim=0)` (`managers/termination_manager.py:144`), the fraction of **all**
envs whose last episode ended that way, so the `term_*` columns were wrong (first PhysX smoke row: time_out 0.0625
for 32 time-out episodes). Now it counts `termination_manager.get_term(name)[dones]` per step. Success counting
(`Metrics/success_rate` is the mean over the envs reset that step, times `n_done`) was already right and is unchanged.
The first two rows in `results/cross_eval_smoke.csv` (10:35:59, 10:36:41) have the wrong `term_*` values; the
rows from 10:43:32 and 10:48:04 are after the fix.

Smoke results (16 envs, deterministic policy, Play config):

| Policy | Run in | Episodes | Success | abnormal_robot | time_out | Steps |
|---|---|---|---|---|---|---|
| Lift PhysX `model_14999.pt` | PhysX | 32 | 1.00 (95% CI 0.89–1.00) | 0.00 | 1.00 | 720 |
| Lift PhysX `model_14999.pt` | Newton | 33 | 0.00 (95% CI 0.00–0.10) | 1.00 | 0.00 | 46 |

**Surprise:** in Newton the PhysX policy ends **every** episode through `abnormal_robot`: 33 episodes from 16 envs
in 46 control steps, so episodes last ~20–25 steps (~0.4 s). That is either the real transfer gap or something about Newton in the Play config; the Newton→Newton cell
of step 2 will tell which.
