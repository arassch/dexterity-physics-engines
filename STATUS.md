# Status
Updated: 2026-11-18 14:04 UTC by the server agent (wake-up: state changed, PLAN.md answer for T21a)

Instance hours since 15 Nov 16:00 UTC: **≈ 11.2 h ≈ $41** (estimate: 11.1 h at the 13:55 STATUS plus 0.1 h; uptime
3 h 36 min). T21 still needs about 2.6 h (T21a) to ~5.8 h (T21b), so ≈ $62 at the end. About 30 h ≈ $109 left of the $150.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T21a Lift, corrected Newton | Newton (clamp + 8 substeps) | 3,973 / 8,000 | 0.00 | 0.015 | 0.0000 | 2 h 36 min (≈ 16:40 UTC), 2.4–2.5 s/it |
| T21b Lift, corrected Newton + `--finger_dr` (restart) | Newton (clamp + 8 substeps + finger DR) | 2,223 / 8,000 | 0.00 | 0.028 | 0.0000 | 5 h 48 min (≈ 19:50 UTC; earlier once T21a ends), 3.7 s/it |

GPU: 3.2 GB / 46 GB, 98–99 % utilisation. No Traceback or NaN in either log. Training success rates include
exploration noise. Mean reward: T21a 6.44 (7.43 two iterations earlier; it swings), T21b 5.66.

## Since last update
- Read the 14:05 answer: both runs continue to 8,000 regardless; Finding 14 will note where each run's success first
  rises above 0. No action needed; both runs progressing (pids 14022 and 19261).

## Needs a human
- T21b runs ~1.5× slower than T21a (3.7 vs 2.4 s/it). I haven't looked into why.
- Still open from before: T22 A/B surprise (Finding 6); the 4-vs-8 substep call is close. Sara: set T19 `done` when
  you're happy; "What I learned" notes for T17, T23, T18, T25, T25b, T22, T20, T26, T26b.
