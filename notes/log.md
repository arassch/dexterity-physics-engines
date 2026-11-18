# Working notes

Older entries (11–16 Nov: Lift, Reorient, cross-evaluation, joint order, step response, velocity limits, the
reward experiment, the fit design) are in `notes/archive.md`. Append new entries at the end of this file.

## 2026-11-17 15:55 UTC · What I learned: T19, the system-ID fit (Sara)

From writing `scripts/sysid_fit.py` (make_grid, refine_grid, score_candidate, choose_best) and its first run:
default Newton 22 blow-ups → fitted 0 (armature 0.0131, damping ×1.149, effort ×1.591 on the 16 finger joints), with
lower tracking error on all three signals (a 0.091 → 0.019, b 0.074 → 0.049, c 0.335 → 0.324). 12 s per 16
candidates, about 6 minutes in total.

- We calibrate the simulator (Newton) against the "real robot" (PhysX), so the reference is what the real hand
  actually does, including its overshoot and lag, not the targets it was given. A simulator that tracks targets better
  than the real robot is a worse simulator.
- No policy runs during the fit: both hands get the same recorded target sequences (open loop). With a policy in the
  loop, differences in observations would change its commands, and we couldn't tell physics differences from policy
  reactions.
- The loss compares both position and velocity. Velocity is where the engines differ (Newton's fingers overshoot the
  speed limit and blow up); position catches offsets in where the finger ends up. Matching both over time constrains
  the dynamics (acceleration) indirectly.
- Each is divided by a natural scale (0.3 rad of motion, the 6.28 rad/s velocity limit) before combining, because they
  have different units and sizes; otherwise velocity would dominate.
- The blow-up penalty is graded by time (early blow-ups cost more, so the search can tell "nearly survived" from
  "failed at once"), and measured against one fixed yardstick taken from the default run. My first version took the
  yardstick from each candidate's own survivors, so the same blow-up cost more in a candidate whose survivors tracked
  badly; a fixed yardstick makes losses comparable between candidates.
- Surprise: the fit raised the effort limit (×1.59) instead of slowing the hand down. Likely reason (hypothesis, not
  yet tested): MuJoCo clips the *sum* of the PD drive's spring and damping forces at the effort limit, so when a fast
  finger saturates, its damping is clipped away exactly when it needs braking, and it runs away. More headroom keeps
  the damping working. The substep count (8) and velocity clamp were fixed before the fit, not part of it.
- With only three parameters, a log-spaced grid (6 × 6 × 6, then a finer grid around the best point) beat CMA-ES:
  it shows the whole landscape, and the coarse best landing on the effort bound (2.0) was a visible warning that the
  refinement then resolved (1.59, inside the range).
- Next time: fit on a smaller set of the recorded episodes and keep the rest for validation, so I know the fit isn't
  tuned to those particular motions.

## 2026-11-17 16:03 UTC: Finding 11, the fit doesn't survive its checks, and PhysX policies still fail in fitted Newton (T19 fit, T20, server agent)

**The fit (Sara, T19, `results/sysid_robot.json`):** 6³ coarse + 5³ fine grid. Best point: armature 0.0131, damping
×1.149, effort ×1.591. Over the 64 references: loss 0.208 vs 0.316 at defaults, blow-ups 0 vs 22, RMS a 0.019 vs
0.091, b 0.049 vs 0.074, c 0.324 vs 0.335. All with the fixed corrections (finger velocity clamp every physics
step, 8 substeps).

**Check 1, step response (signal a, `results/sysid_check.md`):** the fit leaves the step response almost unchanged.
Mean over 15 finger joints: rise time PhysX 0.086 s, default Newton 0.083 s, fitted 0.089 s. Overshoot PhysX 38.5%,
default 44.5%, fitted 44.4%. Steady-state error PhysX 0.002 rad, default and fitted 0.014 rad. The hand is not
sluggish: fitted Newton overshoots *more* than PhysX, not less. The thumb is the worst joint: thumb_joint_0
overshoots 41% in PhysX, 76% in default Newton and 65% fitted. thumb_joint_2 has a single reference env, which reset
at defaults. Plots: `results/plots/sysid_step_{ring_joint_0,thumb_joint_0,ring_joint_1}.png`.

**Check 2, held-out episodes:** the 64 references hold 15 trace episodes. I reran Sara's grid search (her functions
unchanged, `scripts/sysid_check.py`) on episodes 0–9 (44 reference envs), then tested on 10, 11, 12, 14, 15 (20 envs):

| parameters | train blow-ups (a/b/c) | held-out blow-ups (a/b/c) |
|---|---|---|
| default | 16 (7/2/7) | 10 (2/3/5) |
| full fit (sysid_robot.json) | 18 (5/5/8) | 10 (2/4/4) |
| best on episodes 0–9 (0.0110, ×1.149, ×1.149) | 0 | 5 (0/0/5) |

- **Surprise: the full fit's "0 blow-ups" does not reproduce.** Here the same parameters on the same 64 references
  give 28 blow-ups (18 + 10), against 26 for the defaults. In the fit run they gave 0 and 22. Both runs scored the
  default and the fitted point in their first rollout call (envs 0–127). Many other grid points get 0 blow-ups in
  both runs (188 of 343 rows in the fit, 220 of 343 on the train envs here). So a blow-up count of 64 references
  seems to vary from run to run by more than the gap between candidates. Choosing the minimum over 343 candidates
  then favours a lucky draw. I haven't tested repeatability (same params, repeated calls, different env blocks).
- The point fitted on 10 episodes keeps all 5 blow-ups on held-out signal c (5 of 20 envs), the same as the defaults.

**Cross-evaluation (`results/cross_eval.md`, "Fitted robot"; 1,024+ episodes, `--match_order`):**
- PhysX → fitted Newton: Lift **1.0%** (0.5–1.8), Reorient **0.1%** (0.02–0.6), vs 0.2% / 0.0% in default Newton.
  `abnormal_robot` drops (Lift 98.5 → 88.7%, Reorient 95.1 → 70.9%) and episodes last longer (171 / 362 control steps
  for ~1,024 episodes, vs 92 / 118), but the policies still fail, now also with the cube out of bounds (11.3% / 25.2%).
- Newton → fitted Newton (control): Lift **94.8%** (93.2–96.0) vs 86.9% default (`abnormal_robot` 13.6 → 3.4%);
  Reorient 65.6% vs 63.9% (overlapping intervals). Fitting doesn't break Newton's own policies.
- Newton → PhysX, unchanged (T21 baseline): T23's matched rows, 0.0% in both tasks.

So the calibrated simulator fails the fidelity check. The fit removes part of the robot blow-ups in closed loop,
not the gap.

## 2026-11-17 16:48 UTC: Finding 12, blow-up counts depend on the rollout call number, not on luck (T26, server agent)

`scripts/sysid_repeat.py` → `results/sysid_repeat.md` / `.json`. Newton harness (clamp + 8 substeps, ADR max), 1,024
envs = 4 candidates × 4 blocks of 64 envs, the same params array rolled out in 5 calls; Sara's `score_candidate`
unchanged. Blow-ups per 64-env block (calls separated by "·", the 4 blocks inside each):

| candidate | call 1 | call 2 | calls 3–5 |
|---|---|---|---|
| default | 37/26/29/36 | 9/8/8/8 | 5 in all 12 blocks |
| full fit (T19 best: 0.0131, ×1.149, ×1.591) | 31/36/36/33 | 5/6/5/7 | 0 (one block: 1) |
| T20 train best (0.0110, ×1.149, ×1.149) | 28/33/31/23 | 6/6/6/6 | 4–6 |
| 0 in T19 and T20 (0.0158, ×1.149, ×1.516) | 34/31/29/38 | 3/2/1/2 | 0 (two blocks: 1) |

- The first rollout call after the env is built gives +25–30 blow-ups to **every** candidate. Counts settle by call 3.
  The smoke test (512 envs, 2 calls) showed the same pattern (call 1 ≈ 23–36, call 2 ≈ 1–7).
- Within one call, blocks differ by about 1 (mean std 0.7–1.1). Nothing is bit-identical: 0/60 block pairs and 0/64
  call pairs have identical `joint_pos`/`reset_step`.
- T19's fit scored the default alone in call 1 (22 blow-ups, and the penalty level 0.465 came from it). T20 scored
  [default, full fit] in call 1 (26 vs 28). Every grid point ran in call ≥ 2. So "22 → 0" and "28 vs 26" are both
  the call-1 effect, not the winner's curse. Settled, the full fit still does better than the defaults: 0 vs 5 per
  64 references, with the gap ≫ the block noise.
- Not known: why call 1 differs (state left by env construction or the first `u.reset()`, ADR or curriculum state,
  graph capture, warm-start?). It isn't explained yet. The penalty level, and so every loss in T19/T20, came from a
  call-1 rollout.

## 2026-11-18 10:58 UTC: Finding 13, the "call-1 effect" was ADR demotion (gravity drifting to 0); with ADR frozen the fit changes (T26b, server agent)

**Mechanism.** The Play configs start ADR at `max_difficulty` 10 without `promotion_only`, so `DifficultyScheduler`
lowers the difficulty by 1 on every reset of an env that didn't succeed. With the cube parked nothing succeeds.
Difficulty scales `variable_gravity` (0 → −9.81) and the observation noises.

**Evidence** (`results/sysid_repeat.md` "ADR drift", `results/sysid_repeat_drift.md`): unfrozen, ADR mean / gravity
at the start of each signal: call 1 a 8.00 / −7.85, b 6.84 / −6.71, c 5.71 / −5.60; call 2 a 4.49 / −4.41,
b 3.49 / −3.42, c 2.48 / −2.44. With `--freeze_adr` (`promotion_only=True`): 10.00 / −9.81 in every signal of all
5 calls (`results/sysid_repeat_adrmax.md`). The old PhysX reference `t19_ref_physx.npz` drifted the same way
(gravity −5.79 after signal c).

**Repeat test with ADR frozen** (1,024 envs, 4 candidates × 4 blocks of 64, 5 calls; blow-ups per block, mean ± std
over 20 blocks): default 62.6 ± 4.4, T19 fit 54.5 ± 5.2, T20 train best 54.0 ± 4.7, "0 in T19/T20" 52.3 ± 6.6.
There's no call effect any more: within-call std ≈ between-call std ≈ 4–5. Gravity adds a lot of blow-ups: with no
gravity (T26, calls ≥ 3) these were 5 / 0 / 5 / 0.

**Refit with ADR frozen** (`sysid_fit.py --repeats 4`, ref `t19_ref_physx_adrmax.npz`, `results/sysid_robot_adrmax.json`,
log `~/runs/sysid_fit_adrmax2.log`):

| | armature | damping_scale | effort_scale | blow-ups / 64 (mean ± std of 4) | loss |
|---|---|---|---|---|---|
| default | 0.0100 | 1.000 | 1.000 | 65.5 ± 5.9 | 0.649 |
| old fit (T19, drifted ADR) | 0.0131 | 1.149 | 1.591 | (repeat test: 54.5 ± 5.2) | (0.586) |
| ADR-max fit | 0.0923 | 0.545 | 1.206 | 34.5 ± 6.0 | 1.244 |
| lowest loss in the coarse grid | 0.0100 | 1.741 | 1.149 | 46.0 ± 5.2 | 0.522 |

- `choose_best` ranks by blow-ups first, so the new fit buys fewer blow-ups with a much worse tracking loss (1.24 vs
  0.65 for the default). Armature is near its upper bound (0.1), damping near its lower bound (0.5).
- The top candidates by blow-ups are within one std of each other (≈ 6), so the winner is partly chosen by noise even
  with 4 repeats.

**sysid_check with ADR frozen** (`results/sysid_check_adrmax.md`): step response (a), mean over 14 joints: rise time
PhysX 0.086 s, default 0.083 s, ADR-max fit 0.199 s; overshoot 38.6 % / 47.5 % / 89.6 %; steady-state error
0.002 / 0.018 / 0.090. So the fitted robot is much slower and overshoots more than PhysX: it tracks worse than the
default. Held-out episodes (20 ref envs, max 60): default loss 0.627, 18 blow-ups; fit 1.293, 16; train-best
(0.0398, ×2.64, ×0.871) 0.933, 15. The blow-up gain on held-out data (18 → 16) is within the noise, and the train-best
point is far from the full fit: the three parameters aren't identifiable from these signals.

**Evals** (`evaluate.py --freeze_adr`, Reorient PhysX policy, `results/cross_eval.csv`): PhysX → fitted Newton (old
fit) 0.29 % frozen vs 0.10 % drifting; PhysX → PhysX 51.0 % vs 51.5 %. The drift barely changes these cells.

**What it affects.** Every open-loop run through `sysid_harness.py` / `step_response.py` / `sysid_repeat.py` with the
Play config before `--freeze_adr` (T19, T20 step 1, T26, and the `t19_ref_physx.npz` reference) ran with a drifting
gravity: −7.9 at the first signal, falling towards 0 over later calls. Earlier step-response tasks (T18, T25, T25b)
probably drifted the same way if they reset several times, but I haven't checked them one by one. Finding 12's "call-1 effect" is this drift and not a simulator artifact. T19's
fit was scored mostly at near-zero gravity. The closed-loop cross-eval numbers (T6, T13, T20, T23) hardly change
(the two cells above).

## 2026-11-18 11:30 UTC: T21 started; finger DR smoke check; both runs share one run folder (server agent)

`train_clamped.py --finger_dr` samples log-uniform values per env on every reset: armature 0.01–0.05, damping
×0.75–2.0 and effort ×1.0–2.0 of the per-env nominal values left by the startup events. Smoke run: 64 envs,
5 iterations (`~/runs/t21_smoke_dr.log`). Values read back from `robot.data` at reset call 1: armature 0.0106–0.0498
(std across envs 0.0118), damping scale 0.753–1.948, effort scale 1.012–1.987, all `inside=True`. Call 2 resampled
them (armature 0.0115–0.0493, ...). Nominal finger values: damping mean 0.125, effort 0.5, armature 0.01.

Speed with both runs on the GPU, iterations ~20–50: T21a 2.1 s/it (ETA 4 h 42 min), T21b 3.0–3.5 s/it (ETA 7 h 16 min).
So the DR run is ~1.6× slower. I haven't checked why (higher armature/damping, or the writes at each reset).

**Both runs write to `2026-11-18_11-24-37`.** They started in the same second, and rsl_rl names the folder by the
second. Each `model_N.pt` gets overwritten by whichever run reaches N later, which is T21b, the slower one. So
T21a's final checkpoint has to be copied as soon as T21a finishes, before T21b reaches iteration 7,999.

## 2026-11-18 16:58 UTC: T21a finished at 8,000 iterations without ever lifting (server agent)

T21a (Lift, corrected Newton: clamp + 8 substeps, no finger DR) ended normally (`Training time: 19578.45 seconds`,
no Traceback, 0 resumes). Training-time numbers (with exploration noise), log `~/runs/lift_newton_corr_8000.log`:

| iteration | success | abnormal_robot | ADR | mean reward | position_tracking | object position error | action std |
|---|---|---|---|---|---|---|---|
| 2,000 | 0.00 | 0.028 | 0.0000 | 6.03 | 0.020 | 0.70 m | 0.78 |
| 4,000 | 0.00 | 0.030 | 0.0000 | 6.58 | 0.032 | 0.68 m | 0.94 |
| 6,000 | 0.00 | 0.043 | 0.0000 | 7.13 | 0.022 | 0.62 m | 0.96 |
| 7,999 | 0.00 | 0.040 | 0.0002 | 6.93 | 0.019 | 0.72 m | 0.96 |

The policy reaches and touches the cube (fingers_to_object 0.52–0.66, good_finger_contact 0.31–0.41) but never lifts
it, and the action std grew from 0.78 to 0.96 instead of shrinking. For comparison, the original Newton Lift run (T2,
4 substeps, no clamp) was at ~0.40 success by iteration 4,500. Backed up `checkpoints/lift_newton_corr/model_7999.pt`
and `configs/lift_newton_corr/`. (The 11-24-37 folder's `model_7999.pt` is T21a's: T21b moved to its own folder at
iteration 368.) T21b (finger DR) is at ~4,970 / 8,000, also 0.00. Step 3 evals wait for T21b (see STATUS.md).

## 2026-11-18 17:10 UTC: T21b stopped (never lifted); T21c/T21d started without grasp rewards (server agent)

Per Sara's 17:05 decision, T21b (corrected Newton + finger DR) was stopped at iteration 5,134 of 8,000. Training-time
numbers (with exploration noise), log `~/runs/lift_newton_corr_dr_8000_r2.log`:

| iteration | success | abnormal_robot | ADR | mean reward | iteration time |
|---|---|---|---|---|---|
| 2,000 | 0.00 | 0.029 | 0.0002 | 5.75 | 3.65 s (shared GPU) |
| 4,000 | 0.00 | 0.021 | 0.0000 | 6.31 | 3.93 s (shared GPU) |
| 5,000 | 0.00 | 0.016 | 0.0002 | 6.71 | 2.57 s (alone) |
| 5,134 (last) | 0.00 | 0.020 | 0.0002 | 6.70 | 2.56 s (alone) |

Like T21a, it touches the cube (good_finger_contact ~0.35, contact_count ~0.62) but never lifts it; action std 1.00.
Backed up `checkpoints/lift_newton_corr_dr/model_5000.pt` (last milestone), configs, and the last 60 log lines. Neither
T21a nor T21b gets evaluated.

Step 2b: 64-env, 5-iteration smoke run with `env.rewards.good_finger_contact.weight=0
env.rewards.contact_count.weight=0` (`~/runs/t21c_smoke.log`). Both terms show weight 0 in the reward table and 0.0000
in every iteration, and it ended normally (7.6 s). Started T21c at 17:04 (`2026-11-18_17-04-21_corr_nograsp`) and T21d
(`--finger_dr`) at 17:05 (`2026-11-18_17-05-09_corr_dr_nograsp`). Both logs show the two weights at 0.

## 2026-11-18 19:05 UTC: T21c finished; corrected Newton learns Lift once the grasp rewards are off (server agent)

T21c (corrected Newton, clamp + 8 substeps, no grasp rewards, 3,000 iterations) ended normally after 6,903 s, no
crash, 0 resumes. Training-time numbers (with exploration noise), log `~/runs/lift_newton_corr_nograsp_3000.log`:

| iteration | success | abnormal_robot | ADR |
|---|---|---|---|
| 1,000 | 0.00 | 0.023 | 0.000 |
| 2,000 | 0.31 | 0.030 | 0.021 |
| 3,000 (2999) | 0.90 | 0.077 | 0.977 |

Final mean reward 21.84, `position_tracking` 0.897, `success` term 2.88, action std 0.79, 2.51 s/iter (shared GPU).
So the same corrected physics where T21a stayed at 0.00 for 8,000 iterations reaches 0.90 in 3,000 once
`good_finger_contact` and `contact_count` are zeroed, the same pattern as T22 B in PhysX (0.93 at 3,000). ADR went from
0.02 to 0.98 between 2k and 3k, and abnormal_robot rose with it (0.03 → 0.08). Backed up
`checkpoints/lift_newton_corr_nograsp/model_2999.pt`, configs, last 60 log lines. T21d (finger DR) is at ~2,095 / 3,000,
success 0.05–0.12, ADR 0.004.

## 2026-11-18 19:47 UTC: T21d finished; finger DR learns Lift too, later but to the same level (server agent)

T21d (corrected Newton + `--finger_dr`, no grasp rewards, 3,000 iterations) ended normally after 9,349 s, no crash,
0 resumes. Training-time numbers (with exploration noise), log `~/runs/lift_newton_corr_dr_nograsp_3000.log`:

| iteration | success | abnormal_robot | ADR |
|---|---|---|---|
| 1,000 | 0.00 | 0.013 | 0.000 |
| 2,000 | 0.00 | 0.019 | 0.000 |
| 3,000 (2999) | 0.92 | 0.023 | 0.977 |

Final mean reward 18.85, `position_tracking` 0.837, `success` term 2.43, action std 0.73, 2.52 s/iter. Compared with
T21c, success starts later (0.00 at 2k vs 0.31; first nonzero around 2.1k) but ends at the same level (0.92 vs 0.90),
and abnormal_robot ends about 3× lower (0.023 vs 0.077) at the same ADR (0.98). Backed up
`checkpoints/lift_newton_corr_dr_nograsp/model_2999.pt`, configs, last 60 log lines.

**Surprise: T21 step 3, both policies are 0.0% in PhysX.** 1,024+ episodes each, `--match_order newton`,
`--freeze_adr` (ADR 10, g −9.81), `results/cross_eval.md` "Sim-to-real (Lift)": T21c 0.0% (0/1,050, CI 0–0.4%,
abnormal_robot 8.5%, time_out 87.7%), T21d 0.0% (0/1,045, abnormal 7.2%, time_out 90.1%), original Newton Lift 0.0%
(abnormal 23.5%, time_out 66.3%). Corrections and finger DR cut blow-ups in PhysX by ~3× but no episode succeeds.
Added `--label`/`--tag` leading options to `scripts/eval.sh` (smoke 32 episodes passed) to label and separate these
logs. Home rows and the clips (step 4) not done yet.
