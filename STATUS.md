# Status
Updated: 2026-11-18 11:50 UTC by the server agent (wake-up: manual --once)

Instance hours since 15 Nov 16:00 UTC: **≈ 9.1 h ≈ $33** (estimate: 8.75 h at the 11:31 STATUS plus 19 min; `uptime`
1 h 19 min at 11:47). T21 still needs about 4.3 h (T21a) to ~7 h (T21b, restarted), so ≈ $58–60 at the end.
About 32 h ≈ $117 left of the $150.

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T21a Lift, corrected Newton | Newton (clamp + 8 substeps) | 605 / 8,000 | 0.00 | 0.036 | 0.00 | 4 h 20 min (≈ 16:10 UTC), 2.2 s/it |
| T21b Lift, corrected Newton + `--finger_dr` (restart) | Newton (clamp + 8 substeps + finger DR) | 3 / 8,000 | 0.00 | – (too early) | 0.00 | ~7 h 27 min at the current rate (≈ 19:15 UTC; earlier once T21a ends) |

GPU: 3.2 GB / 46 GB before the restart, 99 % utilisation. Training success rates include exploration noise.

## Since last update
- Per the 11:45 planning-chat answer: stopped T21b (pid 14025, confirmed with `ps`) at iteration 368 and restarted it
  with the same command plus `--run_name corr_dr` (log `~/runs/lift_newton_corr_dr_8000_r2.log`, pid 19247, folder
  `2026-11-18_11-46-21_corr_dr`). It shows `Learning iteration` lines, no Traceback. T21a untouched.
- In T21a's folder `2026-11-18_11-24-37`, `model_250.pt` was written by the old T21b; `model_0.pt`, `model_500.pt` and
  everything later are T21a's (RUNS.md #16–18).

## Needs a human
- T21b ran ~1.6× slower than T21a (3.0–3.5 vs 2.1 s/it) before the restart. I haven't looked into why.
- Still open from before: T22 A/B surprise (Finding 6); the 4-vs-8 substep call is close. Sara: set T19 `done` when
  you're happy; "What I learned" notes for T17, T23, T18, T25, T25b, T22, T20, T26, T26b.
