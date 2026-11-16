# Status
Updated: 2026-11-16 16:31 UTC by the server agent (wake-up: state changed, T22 B-in-PhysX eval finished)

Instance hours since 15 Nov 16:00 UTC: **≈ 4.2 h ≈ $15.3** (estimate; the previous STATUS stamp of 16:37 was a
mistake, since it was earlier than now).

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T22 A `noactpen` | PhysX (Lift) | 2,966 / 3,000 | 0.0 | 0.012 | 0.0 | ~3 min |
| T22 eval: baseline `model_3000.pt` in PhysX | PhysX | eval, 1,024 eps | – | – | – | minutes |
| T19 harness `--check`, 64 envs | Newton | rollout a/b/c | – | – | – | minutes |

GPU ~5–10 GB / 46 GB. Training success rates include exploration noise. A's success has been 0.0 throughout.

## Since last update
- T22 B (`nograsp`) in PhysX: **90.2%** (1,025 eps, CI 88.3–91.9%), abnormal_robot 0.8%. Row committed to
  `results/cross_eval.csv`. Its log is kept as `~/runs/eval_lift_nograsp_in_physx.log`.
- Started the T1 baseline `model_3000.pt` in PhysX eval (`~/runs/eval_lift_physx_in_physx.log`).
- **T19:** switched `scripts/sysid_harness.py` to PLAN.md's fallback: finger velocities are clamped once per physics
  step (`--clamp_mode physics_step`, the new default). The 8-env smoke test **passes**: signal c gives 1/8
  abnormal_robot (3/8 without the clamp); RMS a 0.027, b 0.022, c 0.100 rad. The 64-env `--check` is running
  (`~/runs/t19_harness_check64.log`).
- Next wake-up: back up A when it finishes, then run A's evals (PhysX and Newton) and the clips. Read the 64-env check.
  Then T19's speed test (2/4/8 substeps), which needs the `scripts/train_clamped.py` wrapper.

## Needs a human
- T19: the per-solver-substep clamp crashed CUDA twice, so the harness uses the per-physics-step fallback (smoke test
  OK). If you want the substep hook debugged instead, say so in PLAN.md.
- T19 speed test: I'll write `scripts/train_clamped.py` (installs the same per-physics-step clamp, then runs train.py
  unchanged) unless told otherwise.
- At ADR max, `variable_gravity` gives g_z ≈ −7.1 to −7.6, not −9.81. FYI.
- Sara: "What I learned" notes for T17, T23, T18, T25 and T25b.
- Still open from before: watching the 10 Reorient clips.
