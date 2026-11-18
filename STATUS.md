# Status
Updated: 2026-11-18 18:09 UTC by the server agent (wake-up: heartbeat)

Instance hours since 15 Nov 16:00 UTC: **≈ 15.2 h ≈ $55** (estimate: 14.2 h at 17:10 plus 1.0 h; instance up
continuously, `uptime` 7:40). T21c ends in ~45 min, T21d in ~1 h 45 min (less once T21c frees the GPU), so ≈ $61
before step 3 evals. About 26 h ≈ $95 left of the $150.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T21c Lift, corrected Newton, no grasp rewards | Newton (clamp + 8 substeps) | 1,744 / 3,000 | 0.00 now; nonzero (≤ 0.06) in 34 iterations, first at 158, latest 1,744 | 0.027 | 0.001 | ~45 min (log) |
| T21d Lift, corrected Newton + finger DR, no grasp rewards | Newton (clamp + 8 substeps + DR) | 1,095 / 3,000 | 0.00 now; nonzero in 7 iterations (first 387, latest 1,039) | 0.013 | 0.000 | ~1 h 46 min (log) |

GPU: 3.2 GB / 46 GB, 98 % utilisation. No crashes, no NaN. 0 resumes each. Training success rates include
exploration noise. Mean reward: T21c 1.10, T21d 0.34; `position_tracking` 0.027 vs 0.006.

## Since last update
- Nothing changed except progress. T21c already shows occasional nonzero training success (unlike T21a/T21b, which
  never did), but it is still sporadic.

## Needs a human
- Nothing new. Once T21c/T21d finish I'll back them up and run step 3 (skipping any run with 0.00 training success).
- Still open from before: T21b ran ~1.5× slower than T21a while they shared the GPU (not investigated); T22 A/B
  surprise (Finding 6); the 4-vs-8 substep call is close. Sara: set T19 `done` when you're happy; "What I learned"
  notes for T17, T23, T18, T25, T25b, T22, T20, T26, T26b.
