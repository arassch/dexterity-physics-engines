# Status
Updated: 2026-11-18 17:10 UTC by the server agent (wake-up: manual --once)

Instance hours since 15 Nov 16:00 UTC: **≈ 14.2 h ≈ $52** (estimate: 14.0 h at 16:58 plus 0.2 h). T21c/T21d need
~1.5–3 h side by side, so about ≈ $63 before step 3 evals. About 27 h ≈ $98 left of the $150.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T21b Lift, corrected Newton + finger DR | Newton (clamp + 8 substeps + DR) | **stopped** at 5,134 / 8,000 | 0.00 | 0.020 | 0.0002 | stopped 17:05 UTC (Sara's decision) |
| T21c Lift, corrected Newton, no grasp rewards | Newton (clamp + 8 substeps) | ~41 / 3,000 | 0.00 | – | – | ~1 h 09 min (log ETA; will grow now that T21d shares the GPU) |
| T21d Lift, corrected Newton + finger DR, no grasp rewards | Newton (clamp + 8 substeps + DR) | ~2 / 3,000 | 0.00 | – | – | ~2 h 52 min (log ETA at iteration 2, rough) |

GPU: 3.2 GB / 46 GB, 98–99 % utilisation. No crashes. Training success rates include exploration noise.

## Since last update
- Read the 17:05 answer. Stopped T21b (pid 19261 confirmed by `ps`, at iteration 5,134, success 0.00 at 2k/4k/5k).
  Backed up `checkpoints/lift_newton_corr_dr/model_5000.pt`, `configs/lift_newton_corr_dr/`,
  `results/log_excerpts/lift_newton_corr_dr_final.txt`. T21a/T21b are not evaluated.
- Step 2b smoke (64 envs, 5 its): `good_finger_contact` and `contact_count` at weight 0 in the reward table, terms 0.0000.
- Started T21c (17:04, `2026-11-18_17-04-21_corr_nograsp`) and T21d (17:05, `2026-11-18_17-05-09_corr_dr_nograsp`).
  Both logs show the two weights at 0 and learning iterations. 0 resumes each.

## Needs a human
- Nothing new. Once T21c/T21d finish I'll back them up and run step 3 (skipping any run with 0.00 training success).
- Still open from before: T21b ran ~1.5× slower than T21a while they shared the GPU (not investigated); T22 A/B
  surprise (Finding 6); the 4-vs-8 substep call is close. Sara: set T19 `done` when you're happy; "What I learned"
  notes for T17, T23, T18, T25, T25b, T22, T20, T26, T26b.
