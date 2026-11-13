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

## 2026-11-12 10:54 UTC: Finding 2 — neither Lift policy transfers to the other engine (T6, server agent)

The four cells ran together (rule change at 10:47), ~1,024 episodes each, 256 envs, deterministic, Play config,
seed 42. Full table: `results/cross_eval.md`.

| Trained → run in | Episodes | Success (95% CI) | abnormal_robot | object_out_of_bound | time_out |
|---|---|---|---|---|---|
| PhysX → PhysX | 1,025 | 95.9% (94.5–97.0) | 1.1% | 0.5% | 98.4% |
| PhysX → Newton | 1,025 | 0.0% (0.0–0.4) | 98.3% | 1.7% | 0.0% |
| Newton → Newton | 1,071 | 87.0% (84.9–88.9) | 13.6% | 0.3% | 86.1% |
| Newton → PhysX | 1,024 | 0.0% (0.0–0.4) | 22.9% | 12.0% | 65.5% |

- Newton → Newton at 87% rules out a broken Newton Play setup: the smoke test's 0% for PhysX → Newton is real.
- **Both directions drop to 0 successes in ~1,024 episodes** (from 95.9% and 87.0% in their own engine).
- The failures look different. PhysX → Newton: 98% `abnormal_robot` after ~23 control steps (1,025 episodes in 93
  steps with 256 envs), so the hand trips the abnormal-robot check almost immediately. Newton → PhysX: episodes
  mostly last to the time limit (65.5%); 12% drop the object out of bounds, 23% `abnormal_robot`.
- Same-engine numbers match training (PhysX ~93–98%, Newton ~86%, which include exploration noise).
- Next useful check (for a human to decide): the T7 videos, and whether `abnormal_robot` in PhysX → Newton is joint
  velocity/limit violation at the very first steps.

## 2026-11-12 11:13 UTC: T7 videos recorded (server agent)

11 Lift clips, each policy played in the engine it was trained in (4 envs, 360 steps, seed 42): PhysX at
250/1000/3000/8000/14999 and Newton at 250/1000/3000/8000/10000 (+14999 from the resume folder `2026-11-11_23-21-33`).
No Traceback or failed clip, ~50–70 s per clip; the only warnings were OmniHub reconnect noise. List with sizes in
`results/videos.md`; clips only on the server (`~/runs/videos/`). Newton clips from 3,000 on are ~40% smaller
(255–300 KB vs 410–490 KB for PhysX), which only means the frames compress differently. Nobody has watched them yet.
No cross-engine clip was recorded (not in PLAN.md).

## 2026-11-12 11:31 UTC: T8 Reorient PhysX timing at 4,096 envs (server agent)

300 iterations, alone on the GPU, finished normally (`Training time: 931.65 seconds`). Medians over iterations
100–299: iteration 3.19 s, collection 2.911 s, learning 0.274 s, 41,143 steps/s. GPU memory 9.3 GB at iteration 217
(60% util). At 299: success 0.000, ADR 0.000, abnormal_robot 0.0097, mean reward 3.63, episode length 315.
Estimate for 15,000 iterations: 47,850 s ≈ 13.3 h ≈ $48.5 at $3.65/hr.
Surprise worth noting: iteration time is **not flat**. It rose from ~2.65 s in the first iterations to 2.95 s at 100
and ~3.2 s by 250–299, all in collection time (learning flat at ~0.27 s), as episodes got longer (28.5 → ~315 steps).
If it keeps climbing, the full-run estimate is too low. Details in `results/reorient_4096_timing.md`.

## 2026-11-12 11:33 UTC: T12 Lift transfer clips (server agent)

Both final Lift policies recorded in the other engine (4 envs, 360 steps, seed 42), no Traceback:
PhysX → Newton `lift_physx_policy_in_newton/model_14999.mp4` (556,607 B), Newton → PhysX
`lift_newton_policy_in_physx/model_14999.mp4` (786,306 B). The play log doesn't print resets, so I can't count resets
per clip from the logs. Both clips are larger than the same policy's in-engine clip (PhysX policy 556,607 vs 486,627 B;
Newton policy 786,306 vs 254,974 B, ~3×), consistent with more motion or resets, but someone has to watch them.

## 2026-11-12 11:48 UTC: T9 Reorient Newton timing at 4,096 envs (server agent)

300 iterations, alone on the GPU, finished normally (`Training time: 520.61 seconds`). Medians over iterations
100–299: iteration 1.80 s, collection 1.527 s, learning 0.273 s, 72,802 steps/s, so **~1.8× faster than PhysX** (T8:
3.19 s), all of it in collection. GPU memory 7.7 GB at iteration 6 (only reading). At 299: success 0.000, ADR 0.000,
abnormal_robot 0.0787 (PhysX 0.0097), object_out_of_bound 0.152, mean reward 5.90, episode length 301.5.
Estimate for 15,000 iterations: 27,000 s ≈ 7.5 h ≈ $27.4 at $3.65/hr. Same upward drift as PhysX: 1.56 s at 19 →
1.59 s at 99 → 1.81 s at 199 → 1.96 s at 299 (episode length 28 → 245 → 301), still rising at the end, so the estimate
is probably low (at 1.96 s: 8.2 h ≈ $29.8). Details in `results/reorient_4096_timing.md`.

## 2026-11-12 14:39 UTC: what the T7 and T12 clips show (Sara watched them)

Sara's observations, as she described them (4 envs per clip, 360 steps, seed 42):

**Lift, PhysX policy in PhysX** (2 robots visible, each with a table in front):
- 250: fails.
- 1,000: tries to grab, but can't pick up. 3,000: same.
- 8,000: successful pickup. The target position changes twice during the clip (the table turns red when it happens).
- 14,999: same as 8,000.

**Lift, Newton policy in Newton** (2 robots visible, **no table visible**):
- 250: fails; each time it fails the cube reappears in a different place and it fails again. 1,000: same.
- 3,000: tries to grab, but can't pick up; sometimes the cube reappears somewhere else.
- 8,000: success; the target position changes during the clip. 10,000 and 14,999: same.

**T12 transfer clips:**
- PhysX policy in Newton: fails to pick up and restarts from a different place. No table visible.
- Newton policy in PhysX: the arms move wildly and don't even touch the cube. The table is visible.

How this lines up with the numbers (my reading, not Sara's):
- The progression matches the training curves: no grasp at 250, reaching without lifting at 1,000–3,000, reliable
  lifts by 8,000, little visible change after that.
- "The cube reappears somewhere else" in Newton is an episode reset. It matches the early terminations in the
  numbers: PhysX → Newton ended 98.3% of episodes on `abnormal_robot` after ~23 steps (T6), and Newton's own training
  had ~14% abnormal resets (Finding 1).
- "Arms going crazy" for Newton → PhysX matches T6: 0% success, 65.5% time-outs, 22.9% abnormal_robot. The policy
  keeps moving without reaching the cube, so most episodes run to the time limit.
- **Open question: the table isn't rendered in the Newton clips** (seen in both Newton clips, present in both PhysX
  clips). The policies behave as if there is something to push against, so it's probably a rendering difference with
  the Newton backend rather than a missing collider, but nobody has checked. Worth checking before the final video,
  since a floating cube with no table looks wrong on screen.
- The "table turns red" moment is the goal changing. Not checked against the config yet.

## 2026-11-12 22:25 UTC · T5 speed benchmark done (server agent)

Lift, 512 envs, 300 iterations, each engine alone on the L40S. Medians over iterations 100–299:

| | PhysX | Newton |
|---|---|---|
| Iteration time | 1.98 s | 1.09 s |
| Steps per second | 8,293 | 15,073 |
| Collection time | 1.865 s | 0.978 s |
| Learning time | 0.105 s | 0.109 s |

Newton is 1.82× faster in steps/s; the gap is all in collection, the PPO update costs the same. Same ratio as the
Reorient 4,096-env timing runs (3.19 vs 1.80 s/it). Newton's run ended at iteration 299 with abnormal_robot 0.91
(early training). Details: `results/speed_benchmark.md`.

Note: nothing ran between ~12:03 and 22:16 UTC (T5 command 2 finished at 12:03; the last idle_stop.log line is
12:18, "15/20 min"; no wake-up in between). T10 and T11 started at 22:18 and 22:19.

## 2026-11-13 04:28 UTC · T11 early-stop check #1 (server agent)

T11 (Reorient Newton, 4,096 envs) at iteration 5,964. Mean training-time `Metrics/success_rate` (includes
exploration noise), 500 iterations each:

| Window | Iterations | Mean success |
|---|---|---|
| Recent | 5,465–5,964 | 11.13% |
| 2,000 earlier | 3,465–3,964 | 5.34% |

Improvement +5.78 pp ≥ 2 pp, so **keep running**. Current: abnormal_robot 0.091, ADR 0.0175, 3.5–3.7 s/it sharing
the GPU. T10 (PhysX) is at 3,147, so no check for it yet.

## 2026-11-13 05:29 UTC · T11 early-stop check #2 (server agent)

T11 (Reorient Newton, 4,096 envs) at iteration 6,966. Mean training-time `Metrics/success_rate` (includes
exploration noise), 500 iterations each:

| Window | Iterations | Mean success |
|---|---|---|
| Recent | 6,465–6,964 | 19.13% |
| 2,000 earlier | 4,465–4,964 | 7.00% |

Improvement +12.13 pp ≥ 2 pp, so **keep running**. Current: abnormal_robot 0.090, ADR 0.0402, 3.6 s/it sharing
the GPU. T10 (PhysX) is at 3,671 (single-iteration success 4.9%, ADR 0.0068), still before its first check at 5,000.

## 2026-11-13 06:30 UTC · T11 early-stop check #3 (server agent)

T11 (Reorient Newton, 4,096 envs) at iteration 7,968. Mean training-time `Metrics/success_rate` (includes
exploration noise), 500 iterations each:

| Window | Iterations | Mean success |
|---|---|---|
| Recent | 7,470–7,969 | 31.35% |
| 2,000 earlier | 5,470–5,969 | 11.17% |

Improvement +20.19 pp ≥ 2 pp, so **keep running**. Current (single iteration): success 37.1%, ADR 0.0995 (from
0.0402 at 6,966), 3.5–3.7 s/it sharing the GPU.

Something to watch: `Episode_Termination/abnormal_robot` is rising alongside ADR. Means per 500 iterations:
5,000–5,499 0.080 · 5,500–5,999 0.085 · 6,000–6,499 0.090 · 6,500–6,999 0.092 · 7,000–7,499 0.109 ·
7,500–7,968 0.133 (last iteration 0.160). No NaN or Traceback so far. T10 (PhysX) is at 4,196 (success 7.9%,
abnormal_robot 0.013, ADR 0.0087), still before its first check at 5,000.

## 2026-11-13 07:31 UTC · T11 early-stop check #4 (server agent)

T11 (Reorient Newton, 4,096 envs) at iteration 8,903. Mean training-time `Metrics/success_rate` (includes
exploration noise), 500 iterations each:

| Window | Iterations | Mean success |
|---|---|---|
| Recent | 8,401–8,900 | 38.91% |
| 2,000 earlier | 6,401–6,900 | 18.42% |

Improvement +20.49 pp ≥ 2 pp, so **keep running**. Current (single iteration 8,900): success 40.4%, ADR 0.2156
(from 0.0995 at 7,968), reward 11.27, 3.9 s/it sharing the GPU.

abnormal_robot keeps rising with ADR: 500-it mean 0.172 at 7,901–8,400 → 0.205 at 8,401–8,900 (iteration 8,900:
0.234). No NaN or Traceback so far. T10 (PhysX) is at 4,744 (success 9.4%, abnormal_robot 0.009, ADR 0.0103),
first check at 5,000.

## 2026-11-13 08:33 UTC · T10 early-stop check #1, T11 check #5 (server agent)

Mean training-time `Metrics/success_rate` (includes exploration noise), 500 iterations each:

| Run | Recent window | Mean | 2,000 earlier | Mean | Change | Decision |
|---|---|---|---|---|---|---|
| T10 PhysX | 4,795–5,294 | 9.75% | 2,795–3,294 | 5.78% | +3.97 pp | keep running |
| T11 Newton | 9,334–9,833 | 44.43% | 7,334–7,833 | 30.08% | +14.35 pp | keep running |

T10 passes its first check, but only just (about 2 pp above the threshold). Iteration 5,294: success 10.8%,
abnormal_robot 0.014, ADR 0.0130, reward 13.25, 6.5–6.7 s/it sharing the GPU.

T11's gain is slowing (+20.5 pp at check #4 → +14.4 pp now). ADR jumped 0.2156 → 0.3512 in ~930 iterations. Mean
reward fell 11.27 → 8.94 and mean episode length is 262.7. abnormal_robot 500-it mean 0.254 (iteration 9,833:
0.242). Iteration time 3.7–3.9 s. No NaN or Traceback in either log.

## 2026-11-13 09:34 UTC · T10 early-stop check #2, T11 check #6 (server agent)

Mean training-time `Metrics/success_rate` (includes exploration noise), 500 iterations each:

| Run | Recent window | Mean | 2,000 earlier | Mean | Change | Decision |
|---|---|---|---|---|---|---|
| T10 PhysX | 5,342–5,841 | 11.60% | 3,342–3,841 | 5.97% | +5.63 pp | keep running |
| T11 Newton | 10,262–10,761 | 49.79% | 8,262–8,761 | 37.66% | +12.13 pp | keep running |

T10 at 5,843: success 10.3%, abnormal_robot 0.010 (500-it mean 0.012), ADR 0.0169, reward 12.57, 6.7 s/it sharing
the GPU.

T11 at 10,764: success 55.3%, ADR 0.5172 (from 0.3512 at 9,833), reward 9.26, episode length 290, 3.8–3.9 s/it.
abnormal_robot keeps rising with ADR: 500-it mean 0.289 (was 0.254 at check #5). No NaN or Traceback in either log.

## 2026-11-13 10:35 UTC · T10 early-stop check #3, T11 check #7 (server agent)

Mean training-time `Metrics/success_rate` (includes exploration noise), 500 iterations each:

| Run | Recent window | Mean | 2,000 earlier | Mean | Change | Decision |
|---|---|---|---|---|---|---|
| T10 PhysX | 5,892–6,391 | 14.31% | 3,892–4,391 | 7.10% | +7.21 pp | keep running |
| T11 Newton | 11,199–11,698 | 54.60% | 9,199–9,698 | 43.36% | +11.24 pp | keep running |

T10 at 6,391: success 13.2%, abnormal_robot 0.010 (500-it mean 0.013), ADR 0.0205, reward 12.78, 6.6 s/it sharing
the GPU.

T11 at 11,698: success 57.7%, ADR 0.6533 (from 0.5172 at 10,764), reward 7.77, episode length 264, 3.9 s/it.
abnormal_robot 500-it mean 0.284 (0.289 at check #6), so it has levelled off while ADR keeps climbing. Mean reward is
falling (9.26 → 7.77) as ADR makes the task harder. No NaN or Traceback in either log.

## 2026-11-13 11:36 UTC · T10 early-stop check #4, T11 check #8 (server agent)

Mean training-time `Metrics/success_rate` (includes exploration noise), 500 iterations each:

| Run | Recent window | Mean | 2,000 earlier | Mean | Change | Decision |
|---|---|---|---|---|---|---|
| T10 PhysX | 6,440–6,939 | 16.70% | 4,440–4,939 | 8.71% | +7.99 pp | keep running |
| T11 Newton | 12,131–12,630 | 58.46% | 10,131–10,630 | 49.07% | +9.39 pp | keep running |

T10 at 6,938: success 18.9%, abnormal_robot 0.012 (500-it mean 0.012), ADR 0.0275, reward 11.99, 6.5–6.8 s/it
sharing the GPU.

T11 at 12,628: success 58.0%, ADR 0.7447 (from 0.6533 at 11,698), reward 9.16, episode length 258, 3.8–3.9 s/it.
abnormal_robot 500-it mean 0.286 (0.284 at check #7), still flat. The margin keeps shrinking
(+14.4 → +12.1 → +11.2 → +9.4 pp) but stays well above the 2 pp threshold. No NaN or Traceback in either log.

## 2026-11-13 12:37 UTC · T10 early-stop check #5, T11 check #9 (server agent)

Mean training-time `Metrics/success_rate` (includes exploration noise), 500 iterations each:

| Run | Recent window | Mean | 2,000 earlier | Mean | Change | Decision |
|---|---|---|---|---|---|---|
| T10 PhysX | 6,985–7,484 | 19.81% | 4,985–5,484 | 10.32% | +9.49 pp | keep running |
| T11 Newton | 13,059–13,558 | 63.44% | 11,059–11,558 | 54.42% | +9.02 pp | keep running |

T10 at 7,484: success 23.7%, abnormal_robot 0.012 (500-it mean 0.012), ADR 0.0374, reward 12.21, 6.6–6.7 s/it
sharing the GPU.

T11 at 13,558: success 63.7%, ADR 0.8195 (from 0.7447 at 12,628), reward 8.13, episode length 262, 3.8–3.9 s/it.
abnormal_robot 500-it mean 0.268 (0.286 at check #8), slightly down. Margin +9.4 → +9.0 pp, still well above
2 pp. No NaN or Traceback in either log.

## 2026-11-13 13:38 UTC · T10 early-stop check #6, T11 check #10 (server agent)

Mean training-time `Metrics/success_rate` (includes exploration noise), 500 iterations each:

| Run | Recent window | Mean | 2,000 earlier | Mean | Change | Decision |
|---|---|---|---|---|---|---|
| T10 PhysX | 7,529–8,028 | 23.83% | 5,529–6,028 | 12.50% | +11.32 pp | keep running |
| T11 Newton | 13,984–14,483 | 64.88% | 11,984–12,483 | 58.53% | +6.35 pp | keep running |

T10 at 8,028: success 24.6%, abnormal_robot 0.012 (500-it mean 0.012), ADR 0.0514 (from 0.0374), reward 12.45,
episode length 339, 6.6 s/it sharing the GPU.

T11 at 14,483: success 60.5%, ADR 0.8439 (from 0.8195), reward 8.83, episode length 266, 3.8 s/it.
abnormal_robot 500-it mean 0.281 (0.268 at check #9). Margin +9.0 → +6.4 pp, still above 2 pp; ~520 iterations
left, so it should finish normally in ~35 min. No NaN or Traceback in either log.

## 2026-11-13 14:14 UTC · T11 finished; T10 early-stop check #7 (server agent)

**T11 (Reorient, Newton, 4,096 envs) finished normally** at iteration 14,999 (`Training time: 57142.06 seconds`,
15.9 h, no NaN, no Traceback, 0 resumes). Backed up `checkpoints/reorient_newton_4096/model_14999.pt`, configs and
`results/log_excerpts/reorient_newton_4096_final.txt`.

| Metric (training-time, includes exploration noise) | Last-500 mean (14,500–14,999) | Iteration 14,999 |
|---|---|---|
| `Metrics/success_rate` | 64.65% | 66.01% |
| `Episode_Termination/abnormal_robot` | 0.300 | 0.296 |
| `Curriculum/adr` | — | 0.8525 |
| Mean reward | 9.07 | 9.47 |
| Iteration time (sharing GPU with T10) | 3.92 s | 4.03 s |

Last window vs 12,500–12,999 (62.00%): +2.65 pp, so the gain was flattening near the end. Compared with the 512-env
T4 run (0% success at 3,315), 4,096 envs made Reorient learnable on Newton. abnormal_robot stays high (~30%, vs ~1%
for T10 PhysX), like Lift Newton (~14%).

**T10 check #7** (training-time success, 500-it means): 25.05% (7,864–8,363) vs 14.23% (5,864–6,363) → **+10.81 pp,
keep running**. At 8,363: success 27.5%, abnormal_robot 0.010, ADR 0.0576, reward 11.20. Now alone on the GPU.

**T10 check #8** (2026-11-13 15:16 UTC, training-time success, 500-it means): 31.72% (9,050–9,549) vs 20.29%
(7,050–7,549) → **+11.43 pp, keep running**. At 9,551: success ~33%, abnormal_robot 0.014, ADR 0.098, reward ~11,
~3.1 s/it alone on the GPU.

**T10 check #9** (2026-11-13 16:17 UTC, training-time success, 500-it means): 34.28% (10,214–10,713) vs 26.92%
(8,214–8,713) → **+7.36 pp, keep running**. Margin is shrinking (+11.43 → +7.36 pp). At 10,711: success 33.7%,
abnormal_robot 0.012, ADR 0.130, reward 9.24 (down from ~11 at check #8 while ADR rose 0.098 → 0.130), ~3.2 s/it.
