# Status
Updated: 2026-11-16 17:00 UTC by the server agent (wake-up: manual --once)

Instance hours since 15 Nov 16:00 UTC: **≈ 4.7 h ≈ $17** (estimate: the previous 4.2 h at 16:31 plus 0.5 h).

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| none | – | – | – | – | – | – |

The GPU is idle and no `todo` task can start: T20 needs T19 `done` (Sara's fit), T21 is blocked, and T16 is run by
hand. `idle_stop.sh` will stop the instance after 20 idle minutes.

## Since last update
- **T22 done.** A (`noactpen`) finished normally at iteration 2999 (13,652 s, 0 resumes): training success 0.00
  throughout, ADR 0.0002, abnormal_robot 0.017. Its action std grew from 1.00 to 1.69. The previous wake-up backed
  it up and ran its evals but left them uncommitted; they are committed now. Evals: A in PhysX 0.0%, A in Newton
  0.0% (98.5% abnormal_robot). Baseline `model_3000`: PhysX 7.9%, Newton 0.0%. B: PhysX 90.2%. Recorded the 3 clips
  (`~/runs/videos/lift_physx_{noactpen,nograsp,baseline3000}/`). I used `--out` names so A and B don't overwrite
  each other. Wrote `results/reward_experiment.md` and Finding 6.
- **T19 harness ready.** 64-env `--check`, signal-c abnormal_robot: 16/64 at 8 substeps, 19/64 at 4, 26/64 at 2.
  Wrote `scripts/train_clamped.py` (smoke test OK). Speed, Lift 512 envs, steady state: 0.98 / 1.11 / 1.31 s/iter
  at 2 / 4 / 8 substeps. The rule picks **8** (`results/sysid_settings.md`). T19 set `blocked` for Sara's fit.

## Needs a human
- **T19 harness ready for Sara.** `scripts/sysid_harness.py` (`run_with_harness`, `rollout`, `default_params`,
  `param_bounds`, `--check`). Fixed corrections: per-physics-step clamp and 8 substeps. Next is your
  `scripts/sysid_fit.py`.
- Surprising: T22 A (no smoothness penalties) never succeeded once in 3,000 iterations, while B (no grasp rewards,
  90.2%) beat the full-reward baseline at the same iteration (7.9%). Details in Finding 6.
- The 4-vs-8 substep call is close: 19 vs 16 blow-ups, one seed, 64 envs, and 4 substeps is ~18% faster. Change it
  in PLAN.md if you prefer 4.
- Sara: watch the 3 T22 clips and add your description to `results/reward_experiment.md` / Finding 6.
- At ADR max, `variable_gravity` gives g_z ≈ −7.1 to −7.6, not −9.81. FYI.
- Sara: "What I learned" notes for T17, T23, T18, T25, T25b (and now T19, T22).
- Still open from before: watching the 10 Reorient clips.
