# Status
Updated: 2026-11-18 16:05 UTC by the server agent (wake-up: heartbeat)

Instance hours since 15 Nov 16:00 UTC: **≈ 13.2 h ≈ $48** (estimate: 12.2 h at the 15:05 STATUS plus 1.0 h; uptime
5 h 37 min). T21 still needs about 0.7 h (T21a) to ~4 h (T21b), so ≈ $63 at the end. About 28 h ≈ $102 left of the $150.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T21a Lift, corrected Newton | Newton (clamp + 8 substeps) | 6,896 / 8,000 | 0.00 | 0.041 | 0.0000 | 44 min (≈ 16:49 UTC), 2.45 s/it |
| T21b Lift, corrected Newton + `--finger_dr` (restart) | Newton (clamp + 8 substeps + finger DR) | 4,140 / 8,000 | 0.00 | 0.034 | 0.0000 | 3 h 56 min (≈ 20:00 UTC; earlier once T21a ends), 3.7–3.9 s/it |

GPU: 3.2 GB / 46 GB, 99 % utilisation. No crash in either log (pids 14022, 19261 alive). Training success rates
include exploration noise. Mean reward: T21a 7.54, T21b 6.67; position_tracking 0.023 / 0.025, object position error
0.61 / 0.67 m (no lifting yet). Mean action std 0.95 / 0.99.

## Since last update
- Nothing changed except progress; both runs continue to 8,000 per the 14:05 answer.

## Needs a human
- T21a is at 6,896 iterations with success still 0.00 and ADR 0; the original Newton Lift run (T2) was at 0.40 by
  4,500. It will most likely end at 8,000 without learning to lift; T21b (4,140) looks the same so far. The step 3
  evals will then measure policies that never lifted. Do you still want step 3/4 run as written when T21a finishes,
  or a change first? (Without an answer I'll back T21a up and wait for T21b before evaluating.)
- T21b runs ~1.5× slower than T21a (3.7–3.9 vs 2.45 s/it). I haven't looked into why.
- Still open from before: T22 A/B surprise (Finding 6); the 4-vs-8 substep call is close. Sara: set T19 `done` when
  you're happy; "What I learned" notes for T17, T23, T18, T25, T25b, T22, T20, T26, T26b.
