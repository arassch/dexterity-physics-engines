# Status
Updated: 2026-11-18 19:58 UTC by the server agent (wake-up: state changed, T21d finished)

Instance hours since 15 Nov 16:00 UTC: **≈ 16.9 h ≈ $62** (estimate: 16.1 h at 19:05 plus ~0.8 h; instance up
continuously, `uptime` 9 h 19 min at 19:47). About 24 h ≈ $88 left of the $150.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T21c Lift, corrected Newton, no grasp rewards | Newton | done 3,000 | 0.90 train / **0.0% in PhysX** | 0.077 / 8.5% | 0.977 | – |
| T21d Lift, corrected Newton + finger DR, no grasp rewards | Newton | **done** 3,000 / 3,000 | 0.92 train / **0.0% in PhysX** | 0.023 / 7.2% | 0.977 | – |
| T21 step 4 clips (T21c, T21d in PhysX) | PhysX | recording | – | – | – | ~15 min |

No training running. Training success rates include exploration noise.

## Since last update
- T21d finished normally (9,349 s, 0 resumes): training success 0.00 at 1k and 2k, **0.92** at 3,000;
  abnormal_robot 0.023 (T21c 0.077), ADR 0.977, mean reward 18.85. Backed up
  `checkpoints/lift_newton_corr_dr_nograsp/model_2999.pt`, configs, log excerpt; RUNS.md #20, README, notes/log.md.
- T21 step 3, PhysX cells (1,024+ episodes, `--match_order newton`, `--freeze_adr`, label `lift_sim2real`):
  **all three 0.0%** (CI 0–0.4%): T21c abnormal 8.5% / time_out 87.7%; T21d 7.2% / 90.1%; original Newton Lift
  23.5% / 66.3%. Table in `results/cross_eval.md` "Sim-to-real (Lift)". To do this I added leading `--label`/`--tag`
  options to `scripts/eval.sh` (smoke-tested).
- Step 4: recording PhysX clips of T21c and T21d (`~/runs/videos/lift_newton_corr[_dr]_nograsp_policy_in_physx/`).

## Needs a human
- **T21's sim-to-real result is 0.0% for every Newton-trained Lift policy in PhysX**, corrected and randomised
  included; the corrections only cut blow-ups (23.5% → 7–9%), and most episodes now just time out. Finding 14 and
  the README results wait until the home rows exist. T21 stays `running`.
- Home rows still missing: `evaluate.py` can't run corrected Newton (clamp + 8 substeps) without fitted params, nor
  `--finger_dr`. Unless PLAN.md says otherwise, next wake-up I'll add `--corrected` and `--finger_dr` to
  `evaluate.py`/`eval.sh` (reusing `train_clamped.py`'s code), smoke-test, and run the two home cells.
- Still open from before: T21b ran ~1.5× slower than T21a while sharing the GPU; T22 A/B surprise (Finding 6); the
  4-vs-8 substep call. Sara: set T19 `done` when ready; "What I learned" notes for T17, T23, T18, T25, T25b, T22,
  T20, T26, T26b.
