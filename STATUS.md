# Status
Updated: 2026-11-18 11:31 UTC by the server agent (wake-up: manual --once)

Instance hours since 15 Nov 16:00 UTC: **≈ 8.75 h ≈ $32** (estimate: 8.2 h at the last STATUS at 10:58, plus the
33 min since; `uptime` 55 min at 11:22). T21's two runs add about 5–7.5 h (≈ $18–27), so ≈ $50–60 at the end.
About 32 h ≈ $118 left of the $150.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T21a Lift, corrected Newton | Newton (clamp + 8 substeps) | 52 / 8,000 | 0.00 | 0.017 | 0.00 | 4 h 42 min (≈ 16:10 UTC), 2.1 s/it |
| T21b Lift, corrected Newton + `--finger_dr` | Newton (clamp + 8 substeps + finger DR) | 33 / 8,000 | 0.00 | 0.006 | 0.00 | 7 h 16 min (≈ 18:45 UTC, earlier once T21a ends), 3.0–3.5 s/it |

GPU: 3.2 GB / 46 GB, 99 % utilisation.

## Since last update
- T21 step 1: added `--finger_dr` to `scripts/train_clamped.py`. Smoke run (64 envs, 5 iterations,
  `~/runs/t21_smoke_dr.log`) passed: the values read back vary across envs and all stay inside the ranges (armature
  0.0106–0.0498, damping ×0.753–1.948, effort ×1.012–1.987; resampled on the next reset).
- T21 step 2: started T21a and T21b at 11:24 (`~/runs/lift_newton_corr_8000.log`, `~/runs/lift_newton_corr_dr_8000.log`).
  Both show `Learning iteration` lines. T21 is `running`.

## Needs a human
- **T21a and T21b share one run folder, `2026-11-18_11-24-37`.** They started in the same second, and rsl_rl names
  the folder by the second. Each `model_N.pt` gets overwritten by whichever run reaches N later, which is T21b, the
  slower one. I tried to stop T21b and restart it with `--run_name`, but `scripts/stop_run.sh` refuses
  `train_clamped.py` (it only accepts `train.py` / `evaluate.py`), and I didn't change that guard. Options:
  1. (what happens if nobody acts) Leave both running. The next wake-up after T21a finishes (~16:10) copies
     `model_7999.pt` right away. It then belongs to T21a, because T21b is ~1,400+ iterations behind. Risks: a NaN
     resume of either run would pick up mixed checkpoints, and the milestone checkpoints are T21b's.
  2. Stop T21b (python pid **14025**) by hand, and restart it with `--run_name corr_dr` added to the same command
     (in RUNS.md #17). About 5 min lost.
  Also, should `stop_run.sh` accept `scripts/train_clamped.py`? The agent can't stop T21 runs without it.
- T21b runs ~1.6× slower than T21a (3.0–3.5 vs 2.1 s/it). I haven't looked into why.
- Still open from before: T22 A/B surprise (Finding 6); the 4-vs-8 substep call is close. Sara: set T19 `done` when
  you're happy; "What I learned" notes for T17, T23, T18, T25, T25b, T22, T20, T26, T26b.
