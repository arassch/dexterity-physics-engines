# Status
Updated: 2026-11-18 19:05 UTC by the server agent (wake-up: state changed, T21c finished)

Instance hours since 15 Nov 16:00 UTC: **≈ 16.1 h ≈ $59** (estimate: 15.2 h at 18:09 plus ~0.9 h; instance up
continuously). T21d ends in ~40–50 min, then step 3 evals. About 25 h ≈ $91 left of the $150.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T21c Lift, corrected Newton, no grasp rewards | Newton (clamp + 8 substeps) | **done** 3,000 / 3,000 | 0.90 final (0.00 at 1k, 0.31 at 2k) | 0.077 | 0.977 | – |
| T21d Lift, corrected Newton + finger DR, no grasp rewards | Newton (clamp + 8 substeps + DR) | 2,095 / 3,000 | 0.12 (0.05 a few its earlier) | 0.012 | 0.004 | ~50 min (log, should drop now it's alone) |

GPU: 1.6 GB / 46 GB. No crashes, no NaN. 0 resumes each. Training success rates include exploration noise.

## Since last update
- T21c finished normally (6,903 s). Corrected Newton reaches **0.90** training success at 3,000 once the grasp rewards
  are off (T21a, with them, stayed at 0.00 for 8,000). ADR jumped 0.02 → 0.98 between 2k and 3k; abnormal_robot rose
  0.03 → 0.08. Backed up `checkpoints/lift_newton_corr_nograsp/model_2999.pt`, configs, log excerpt; RUNS.md #19,
  README table, notes/log.md updated.
- Step 3 not started yet: I'll run all T21 evals together once T21d finishes.

## Needs a human
- Step 3 asks for label `lift_sim2real` and a "home" eval in corrected Newton (clamp + 8 substeps, `--finger_dr` for
  T21d). `eval.sh`/`evaluate.py` have neither: the clamp + substeps only come with `--robot_params` (fitted json). My
  plan unless told otherwise: add a small `--corrected` option (clamp + `num_substeps 8`, no fitted params) and a
  `--finger_dr` option to `evaluate.py`/`eval.sh` reusing `train_clamped.py`'s code, plus a label override, smoke-test
  it, then run the cells. Say so in PLAN.md if you'd rather do it differently.
- Still open from before: T21b ran ~1.5× slower than T21a while they shared the GPU (not investigated); T22 A/B
  surprise (Finding 6); the 4-vs-8 substep call is close. Sara: set T19 `done` when you're happy; "What I learned"
  notes for T17, T23, T18, T25, T25b, T22, T20, T26, T26b.
