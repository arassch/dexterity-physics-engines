# Status
Updated: 2026-11-16 15:40 UTC by the server agent (wake-up: state changed — PLAN.md T16 note by Sara)

Instance hours since 15 Nov 16:00 UTC: **≈ 3.4 h ≈ $12.4** (estimate: ~0.3 h on 15 Nov, plus ~3.1 h today since the
12:34 UTC boot).

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T22 A `noactpen` | PhysX (Lift) | 2,189 / 3,000 | 0.0 | 0.020 | 0.0000 | ~1.0 h |
| T22 B `nograsp` | PhysX (Lift) | 2,414 / 3,000 | 0.80 | 0.009 | 0.94 | ~0.7 h |

GPU 10.6 GB / 46 GB, 95% busy. No eval jobs running. Training success rates include exploration noise.
- B is learning fast: success went from 0.30 (iteration 1,674) to 0.80, ADR from 0.065 to 0.94,
  object_out_of_bound down to 0.03. Its good_finger_contact reward is 0 as designed, yet it still lifts.
- A is still at 0 success at iteration 2,189. Its mean action std keeps growing: 1.42 → **1.55** (B: 0.61).

## Since last update
- Nothing changed except progress. The PLAN.md change was Sara's T16 note (Unreal renders done for the Reorient
  home cells); no agent action needed. T20 stays `todo` waiting on T19 (`hold`).

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
- Sara: "What I learned" notes for T17, T23, T18 and T25 (`scripts/blowup_analysis.py`, `step_response.py` changes).
- Still open from before: watching the 10 Reorient clips.
