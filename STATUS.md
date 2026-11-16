# Status
Updated: 2026-11-16 16:20 UTC by the server agent (wake-up: state changed — PLAN.md rewrote T19)

Instance hours since 15 Nov 16:00 UTC: **≈ 3.9 h ≈ $14.2** (estimate: ~0.3 h on 15 Nov, plus ~3.6 h since the
12:34 UTC boot, uptime 3:22 at 15:57).

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T22 A `noactpen` | PhysX (Lift) | 2,427 / 3,000 | 0.0 | 0.028 | 0.0 | ~44 min |
| T22 B `nograsp` | PhysX (Lift) | 2,668 / 3,000 | 0.83 | 0.015 | 0.98 | ~23 min |
| T19 harness smoke (eval) | Newton | – | – | – | max | minutes |

GPU 10.6 GB / 46 GB at 15:57. Training success rates include exploration noise. Iteration time A 4.55 s, B 4.15 s.

## Since last update
- **T19 started (agent part).**
  - Recorded the PhysX reference at ADR max, signals a+b+c, 64 envs: `~/runs/step_response/t19_ref_physx.npz`
    (log `~/runs/t19_ref_physx.log`, finished without errors). The stored T18 a/b were at ADR 0, so T19 needed this.
  - Wrote `scripts/sysid_harness.py` (module + `--check` CLI, API as in PLAN.md). The velocity clamp runs **once per
    solver substep**: it wraps `NewtonManager._step_solver` with a Warp kernel on the finger dofs of `state_0.joint_qd`
    and re-captures the CUDA graph. MuJoCo Warp copies `state.joint_qd` into its data at every substep
    (`update_data_interval=1`, `solver_mujoco.py:3278`), so the clamp takes effect each substep.
  - 8-env smoke test of `--check` running (`~/runs/t19_harness_smoke.log`). Not verified yet.
- Still to do for T19: verify the smoke test; full `--check` at 64 envs; signal-c counts at 2/4/8 substeps with the
  per-substep clamp; the training-speed test (Lift 512 envs, 50 iterations, 2/4/8 substeps with the clamp). The speed
  test waits for the two T22 training slots to free up (~44 min). It also needs the clamp inside training, i.e. a small
  wrapper around train.py. I'll check that this counts as allowed before I write it.

## Needs a human
- T19 speed test: training with the per-substep clamp needs `train.py` launched through a wrapper that installs the
  clamp. `scripts/train.sh` can't do that. Unless told otherwise, I'll write `scripts/train_clamped.py` (it only
  installs the clamp, then runs Isaac Lab's train.py unchanged) and launch it with `scripts/run_isaac.sh`, 50
  iterations, one at a time, in a free training slot.
- At ADR max, `variable_gravity` gives g_z ≈ −7.1 to −7.6, not −9.81. FYI.
- Sara: "What I learned" notes for T17, T23, T18, T25 and T25b.
- Still open from before: watching the 10 Reorient clips.
