# Status
Updated: 2026-11-18 15:05 UTC by the server agent (wake-up: heartbeat)

Instance hours since 15 Nov 16:00 UTC: **≈ 12.2 h ≈ $45** (estimate: 11.2 h at the 14:04 STATUS plus 1.0 h; uptime
4 h 37 min). T21 still needs about 1.7 h (T21a) to ~4.9 h (T21b), so ≈ $63 at the end. About 29 h ≈ $105 left of the $150.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T21a Lift, corrected Newton | Newton (clamp + 8 substeps) | 5,439 / 8,000 | 0.00 | 0.023 | 0.0001 | 1 h 40 min (≈ 16:45 UTC), 2.4–2.5 s/it |
| T21b Lift, corrected Newton + `--finger_dr` (restart) | Newton (clamp + 8 substeps + finger DR) | 3,181 / 8,000 | 0.00 | 0.019 | 0.0002 | 4 h 53 min (≈ 20:00 UTC; earlier once T21a ends), 3.5–4.0 s/it |

GPU: 3.2 GB / 46 GB, 99 % utilisation. No Traceback or NaN in either log (pids 14022, 19261). Training success rates
include exploration noise. Mean reward: T21a 6.34, T21b 6.33; position_tracking 0.026 / 0.027, object position error
0.67 / 0.70 m (no lifting yet).

## Since last update
- Nothing changed except progress; both runs continue to 8,000 per the 14:05 answer.

## Needs a human
- T21a is at 5,439 iterations with success still 0.00 and ADR ≈ 0; the original Newton Lift run (T2) was at 0.40 by
  4,500 (per the 14:05 answer). Continuing as instructed, but this is now later than T2's rise.
- T21b runs ~1.5× slower than T21a (3.5–4.0 vs 2.4 s/it). I haven't looked into why.
- Still open from before: T22 A/B surprise (Finding 6); the 4-vs-8 substep call is close. Sara: set T19 `done` when
  you're happy; "What I learned" notes for T17, T23, T18, T25, T25b, T22, T20, T26, T26b.
