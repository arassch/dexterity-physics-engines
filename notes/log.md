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
