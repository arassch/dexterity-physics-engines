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
