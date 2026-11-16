# Status
Updated: 2026-11-16 16:37 UTC by the server agent (wake-up: state changed, T22 B finished)

Instance hours since 15 Nov 16:00 UTC: **≈ 4.2 h ≈ $15.3** (estimate, as before plus ~0.3 h).

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T22 A `noactpen` | PhysX (Lift) | 2,800 / 3,000 | 0.0 | 0.011 | 0.0 | ~16 min |
| T22 eval: B in PhysX | PhysX | eval, 1,024 eps | – | – | – | minutes |

GPU 10.3 GB / 46 GB. Training success rates include exploration noise. A: 4.79 s/iteration, action std 1.65 (B: 0.73).

## Since last update
- **T22 B (`nograsp`) finished normally** (`2026-11-16_12-46-44`, 12,814 s, 0 resumes). Final: success 0.93
  (training), abnormal_robot 0.017, ADR 0.986, mean reward 19.05, 4.25 s/iter. Backed up `model_2999.pt`, configs,
  final excerpt; RUNS.md, README, notes/log.md updated.
- T22 evals: **T1 baseline `model_3000.pt` in Newton: 0.0%** (1,026 eps, abnormal_robot 97.1%). B in PhysX is running.
  Baseline in PhysX waits for B's eval to finish (`eval.sh` gives both the same log name).
  A in PhysX and Newton come after A finishes.
- **T19:** per-substep clamp smoke test failed again (attempt 2 of 2). The fix kept the first CUDA graph alive and
  synchronised around the re-capture; same `illegal memory access` on the first `env.step()`. The `--no_clamp` smoke
  test **passes**: signal-c finger RMS to PhysX 0.099 rad, 3/8 abnormal_robot (PhysX 0/8); a 0.027 rad, b 0.022 rad.
  So the harness works and the bug is in the substep patch. Next wake-up: switch to PLAN.md's fallback, a clamp once
  per physics step (like T25's `--clamp_vel`), unless told otherwise.

## Needs a human
- T19: the per-solver-substep clamp (wrapping `NewtonManager._step_solver` + graph re-capture) crashes CUDA twice. I'll
  use the plan's per-physics-step fallback. T25b's 17/64 was measured with a per-physics-step clamp, so the fallback
  should reproduce it. If you'd rather I debug the substep hook (for example, install it before the first graph
  capture), say so in PLAN.md.
- T19 speed test: it still needs a `scripts/train_clamped.py` wrapper (installs the clamp, then runs train.py
  unchanged). I'll write it unless told otherwise.
- At ADR max, `variable_gravity` gives g_z ≈ −7.1 to −7.6, not −9.81. FYI.
- Sara: "What I learned" notes for T17, T23, T18, T25 and T25b.
- Still open from before: watching the 10 Reorient clips.
