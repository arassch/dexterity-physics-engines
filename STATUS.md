# Status
Updated: 2026-11-16 15:50 UTC by the server agent (wake-up: state changed — PLAN.md added T25b)

Instance hours since 15 Nov 16:00 UTC: **≈ 3.6 h ≈ $13.1** (estimate: ~0.3 h on 15 Nov, plus ~3.3 h today since the
12:34 UTC boot).

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T22 A `noactpen` | PhysX (Lift) | 2,324 / 3,000 | 0.0 | 0.022 | 0.0002 | ~52 min |
| T22 B `nograsp` | PhysX (Lift) | 2,558 / 3,000 | 0.75 | 0.014 | 0.96 | ~31 min |

GPU 10.6 GB / 46 GB, 97% busy. No eval jobs running now. Training success rates include exploration noise.
A's mean action std keeps growing (1.57; B 0.64).

## Since last update
- **T25b done** (Finding 10, `results/blowup_diagnosis.md` T25b section, `results/t25b_tests.md`). Added
  `--no_self_collision`, `--num_substeps` and pre-reset recording to `scripts/step_response.py`, plus
  `scripts/t25b_analysis.py`. I ran a smoke test, then 8 signal-c runs at ADR max, at most 4 at a time alongside T22.
  Newton `abnormal_robot` of 64 (PhysX 0 in every setting):
  - defaults: 47
  - self-collision off: 47
  - 4 / 8 substeps: 36 / 37
  - velocity clamp at 2 / 4 / 8 substeps: 34 / 25 / **17**
- Only 4/47 blow-ups have a joint at a position limit, so it isn't MuJoCo's joint-limit constraint. Self-collision
  doesn't matter either.
- Newton source, read only: the MuJoCo Warp solver **ignores `joint_velocity_limit`**
  (`solver_mujoco.py:298-299`, `:4309-4310`, "MoJoCo doesn't have velocity limit"). Joint limits get solref
  (−1e4, −10), Newton's defaults. The effort limit is a joint-level `actfrcrange` on the summed P+D force.
- Caveat: the 64 envs replay only 15 distinct trace episodes, so counts move in blocks of ~4.

## Needs a human
- **T19 proposal from T25b (planning chat decides; T19 not changed).** The kick is mostly fast finger motion
  without a velocity cap, integrated at a coarse step.
  - Fixed settings, not fitted:
    1. Emulate the velocity limit in Newton, ideally once per *solver substep*. The current clamp runs once per
       1/120 s physics step, which may explain the ~4 trajectories still failing.
    2. Use `num_substeps` 4–8 instead of 2. The speed cost isn't measured yet: 4 vs 8 gave the same reset count
       without the clamp, but 25 vs 17 with it.
  - Then fit, on the finger joints only, against PhysX's signal a/b/c trajectories, with Newton `abnormal_robot`
    resets as a penalty:
    1. armature: 0.01–0.1 kg·m²
    2. joint damping: ×0.5–×4 of nominal
    3. effort-limit scale: ×0.5–×2
    4. optional, joint-limit `ke`: 1e3–1e5 (only 4/47 blow-ups touch a limit, so this is low priority)
  - Stiffness stays fixed: it's already equal (T18).
- Self-collision off left PhysX bit-identical. Either PhysX had no finger self-contacts on this signal, or
  `enabled_self_collisions=False` didn't reach PhysX. Not checked further.
- At ADR max, `variable_gravity` gives g_z ≈ −7.1 to −7.6, not −9.81. FYI.
- Sara: "What I learned" notes for T17, T23, T18, T25 and T25b (`scripts/blowup_analysis.py`, `step_response.py`,
  `t25b_analysis.py`).
- Still open from before: watching the 10 Reorient clips.
