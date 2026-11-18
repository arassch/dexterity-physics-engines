# Status
Updated: 2026-11-18 16:58 UTC by the server agent (wake-up: state changed, T21a ended)

Instance hours since 15 Nov 16:00 UTC: **≈ 14.0 h ≈ $51** (13.2 h at the 16:05 STATUS plus 0.85 h). T21b needs
about 3 h more (less now that it has the GPU alone), so ≈ $62 at the end before evals. About 27 h ≈ $99 left of the $150.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T21a Lift, corrected Newton | Newton (clamp + 8 substeps) | **done** 8,000 / 8,000 | 0.00 | 0.040 | 0.0002 | finished 16:51 UTC, 5.44 h |
| T21b Lift, corrected Newton + `--finger_dr` (restart) | Newton (clamp + 8 substeps + finger DR) | ~4,973 / 8,000 | 0.00 | – | – | ~3 h 04 min (≈ 20:00 UTC; log ETA, before the speed-up from running alone) |

GPU: 1.6 GB / 46 GB, 42 % utilisation, only T21b (pid 19261) running. No crash in either log. Training success rates
include exploration noise.

## Since last update
- T21a finished normally (`Training time: 19578.45 seconds`, no Traceback, 0 resumes). Backed up
  `checkpoints/lift_newton_corr/model_7999.pt`, `configs/lift_newton_corr/`, `results/log_excerpts/lift_newton_corr_final.txt`;
  RUNS.md #16, README training table, notes/log.md entry (success 0.00 at 2k/4k/6k/8k; mean reward 6.03 → 6.93;
  action std 0.78 → 0.96).
- No evals started: waiting for T21b, as said at 16:05.

## Needs a human
- T21a ended at 8,000 with success 0.00 at every checkpoint (the original Newton Lift run was at ~0.40 by 4,500). It
  touches the cube but never lifts it. T21b looks the same at ~4,970. Should step 3/4 (PhysX evals + clips) run as
  written on policies that never lifted, or do you want to change something first? Without an answer I'll wait for
  T21b to finish, back it up, and then run step 3 as written.
- T21b runs ~1.5× slower than T21a (3.7–3.9 vs 2.45 s/it while sharing the GPU). I haven't looked into why.
- Still open from before: T22 A/B surprise (Finding 6); the 4-vs-8 substep call is close. Sara: set T19 `done` when
  you're happy; "What I learned" notes for T17, T23, T18, T25, T25b, T22, T20, T26, T26b.
