# Status
Updated: 2026-11-18 13:55 UTC by the server agent (wake-up: heartbeat)

Instance hours since 15 Nov 16:00 UTC: **≈ 11.1 h ≈ $41** (estimate: 10.1 h at the 12:52 STATUS plus 1 h). T21 still
needs about 2.8 h (T21a) to ~6 h (T21b), so ≈ $62 at the end. About 30 h ≈ $109 left of the $150.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T21a Lift, corrected Newton | Newton (clamp + 8 substeps) | 3,700 / 8,000 | 0.00 | 0.024 | 0.0002 | 2 h 46 min (≈ 16:40 UTC), 2.5 s/it |
| T21b Lift, corrected Newton + `--finger_dr` (restart) | Newton (clamp + 8 substeps + finger DR) | 2,043 / 8,000 | 0.00 | 0.030 | 0.0002 | 5 h 58 min (≈ 19:50 UTC; earlier once T21a ends), 3.9 s/it |

GPU: 3.2 GB / 46 GB, 99 % utilisation. No Traceback or NaN in either log. Training success rates include exploration
noise. Mean reward: T21a 6.69 (was 7.09 at 2,216), T21b 5.25.

## Since last update
- Nothing changed; both runs progressing (pids 14022 and 19261).
- T21a still at success 0.00 at iteration 3,700 (position_tracking 0.023, good_finger_contact 0.33,
  object_out_of_bound 0.11), so it still isn't lifting, and mean reward dipped slightly (7.09 → 6.69). I'll check
  the 4k number next wake-up as step "on done" asks.

## Needs a human
- Git permissions: in this wake-up, `git pull --rebase` refused to run because the working tree had uncommitted
  changes (the unpushed 12:52 STATUS.md), and `git stash` isn't in the allowed tools. I commit STATUS.md first and
  then pull. If this STATUS.md isn't on `main`, the commit or push was refused too.
- T21a has 0.00 success after 3,700 of 8,000 iterations. Should it run to 8k regardless? (Default: yes, no change.)
- T21b runs ~1.6× slower than T21a (3.9 vs 2.5 s/it). I haven't looked into why.
- Still open from before: T22 A/B surprise (Finding 6); the 4-vs-8 substep call is close. Sara: set T19 `done` when
  you're happy; "What I learned" notes for T17, T23, T18, T25, T25b, T22, T20, T26, T26b.
