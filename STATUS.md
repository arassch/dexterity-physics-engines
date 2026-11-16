# Status
Updated: 2026-11-16 14:52 UTC by the server agent (wake-up: manual --once)

Instance hours since 15 Nov 16:00 UTC: **≈ 2.6 h ≈ $9.5** (estimate: ~0.3 h on 15 Nov, plus 2.3 h today; uptime says
it booted at 12:34 UTC).

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T22 A `noactpen` | PhysX (Lift) | 1,496 / 3,000 | 0.0 | 0.017 | 0.0002 | ~2.0 h |
| T22 B `nograsp` | PhysX (Lift) | 1,674 / 3,000 | 0.30 | 0.008 | 0.065 | ~1.5 h |

GPU 10.6 GB / 46 GB, 95% busy. No eval jobs running. Training success rates include exploration noise.
- B has started to learn: success rose from 0 at iteration 870 to 0.26–0.32 now; object_out_of_bound is 0.29.
- A is still at 0 success. Its mean action std has grown to **1.42** (B: 0.47), and its entropy loss is 40.5 (B: 15.3).
  With the action penalties off, the exploration noise grows instead of shrinking.

## Since last update
- **T25 done (Finding 9, `results/blowup_diagnosis.md`).**
  - Step 1, left uncommitted by an earlier wake-up, is now committed. PhysX caps finger joint velocity at exactly
    the limit (max 1.01×). Newton goes past the same limit (max 2.0× with no cube, 22.6× in the policy trace).
  - Step 3 (ADR max, gravity on, g_z ≈ −7.3): Newton 47/64 `abnormal_robot` at steps 13–40. PhysX had 0 (its only
    resets were 3 `object_out_of_bound`, from the parked cube falling).
  - Step 4: clipping Newton's joint velocities to ±limit before every physics substep cut the resets to only
    **34/64**. The 34 left reset at the same steps (13–21) as without the clamp: the velocity jumps past 2× the
    limit within one 1/120 s substep.
- `scripts/step_response.py` has new options: `--adr max`, `--signals`, `--clamp_vel`, and it records per-env
  termination terms. T18's defaults are unchanged.

## Needs a human
- **T25 → T19 proposal (planning chat).**
  - An emulated velocity limit is worth including: it removes 13 of 47 resets, and PhysX clearly enforces the limit.
  - It is not enough on its own. Most resets come from a large impulse within one Newton substep. Candidates,
    cheapest first:
    1. Rerun signal (c) with finger self-collision off in both engines.
    2. Log which joints are at their position limits at the reset step (MuJoCo's soft joint-limit constraint).
    3. Rerun Newton with more substeps (smaller physics dt) to test integrator stiffness.
  - A short "T25b" with 1–3 would tell T19 what to fit (e.g. joint-limit solref/solimp, or contact params) instead
    of stiffness/damping, which are already equal.
- T25 step 2 is half done. I couldn't check whether MuJoCo Warp reads `joint_velocity_limit`: the `newton` package
  is under `/workspace/isaaclab/_isaac_sim/kit/python/.../site-packages`, which this agent's permissions can't read.
  Sara could check by hand, or the allow-list could add read access.
- At ADR max, `variable_gravity` gives g_z ≈ −7.2 to −7.4, not −9.81, so even "max" gravity is reduced. FYI.
- Sara: "What I learned" notes for T17, T23, T18 and now T25 (`scripts/blowup_analysis.py`, `step_response.py` changes).
- Still open from before: watching the 10 Reorient clips.
