# Status
Updated: 2026-11-16 13:56 UTC by the server agent (wake-up: state changed, PLAN.md updated)

Instance hours since 15 Nov 16:00 UTC: **≈ 1.7 h ≈ $6** (estimate: ~0.3 h on 15 Nov, plus ~1.4 h today. Uptime says it
booted at 12:34 UTC.)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T22 A `noactpen` | PhysX (Lift) | 781 / 3,000 | 0.0 | (not in summary) | 0.0 | ~2.9 h |
| T22 B `nograsp` | PhysX (Lift) | 870 / 3,000 | 0.0 | (not in summary) | 0.0 | ~2.5 h |

GPU 10.6 GB / 46 GB. No eval jobs are running now. Training success rates include exploration noise. Both variants are
still at 0 success. object_out_of_bound is ~0.25 for both. B's `good_finger_contact` is 0 as intended (weight 0).

## Since last update
- **T18 done.** I wrote `scripts/step_response.py` and `scripts/analyze_step_response.py`. The analysis needed 1 fix:
  signal (a) maps envs to joints in each engine's own order, so it is compared per named joint. Smoke tests passed on
  both engines. I then ran 64 envs × 120 steps on PhysX and Newton.
- **Result (Finding 8):**
  - The nominal robot parameters read identical in both engines.
  - Small commands track almost the same: mean RMS 0.0045 rad for the 0.3 rad steps and 0.0030 rad for the finger
    sine.
  - Replaying the PhysX policy's targets open-loop, **with no cube**, reset **28/64 Newton envs at steps 15–44**,
    almost certainly `abnormal_robot`. PhysX reset 0/64.
- Outputs: `results/step_response.md`, 6 plots in `results/plots/step_*.png`, and Finding 8 in `notes/log.md`.

## Needs a human
- **T19 premise (planning chat): please confirm before the next wake-up.** T19 fits scales on stiffness and damping,
  plus armature and friction. All four are already equal at their nominal values, and small signals match within
  ~0.005 rad. The gap only appears under the policy's large, fast commands (signal c). A fit can still compensate,
  but the cause may lie elsewhere: the solver/integrator, effort or velocity limits, or finger self-collision. If
  PLAN.md is unchanged, I start the T19 harness as written at the next wake-up.
- Also: at ADR 0 gravity is 0, so T18 ran the arm without gravity load. Say if T18/T19 should use ADR max gravity
  instead.
- Sara: "What I learned" notes for T17, T23 and now T18 (`scripts/step_response.py`, `scripts/analyze_step_response.py`).
- Still open from before: watching the 10 Reorient clips.
