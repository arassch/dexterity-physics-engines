# Status
Updated: 2026-11-16 13:22 UTC by the server agent (wake-up: manual --once)

Instance hours since 15 Nov 16:00 UTC: **≈ 1.1 h ≈ $4** (estimate: ~0.3 h on 15 Nov, plus ~0.8 h today. Uptime
says it booted at 12:34 UTC.)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T22 A `noactpen` | PhysX (Lift) | 443 / 3,000 | 0.0 | ~0.013 | 0.0 | ~3.4 h |
| T22 B `nograsp` | PhysX (Lift) | 482 / 3,000 | 0.0 | ~0.012 | 0.0 | ~2.9 h |

GPU 10.6 GB / 46 GB. No eval jobs are running. Training success rates include exploration noise. Both variants are
still at 0 success this early (T1's normal run also needed several hundred iterations).

## Since last update
- **T23 done.** I wrote `scripts/dump_order.py`, which produced `results/joint_order.json`, and added
  `evaluate.py --match_order` (also the optional last argument of `eval.sh`). The smoke test passed the name check.
  I then ran the 8 cells with about 1,024 episodes each.
- **Result: matching the hand joints by name does not rescue transfer.** The cross-engine cells are:
  - Lift: PhysX → Newton **0.2%** (2/1,027, abnormal_robot 98.5%), Newton → PhysX **0%**.
  - Reorient: PhysX → Newton **0%** (abnormal_robot 95.1%), Newton → PhysX **0%**.

  The controls reproduce T6/T13. PhysX → PhysX is identical. Newton → Newton is within the intervals (86.9 vs 87.0%,
  63.9 vs 64.9%).
- The hand-tip bodies resolve in the same order in both engines, so only the 16 hand joints had been permuted.
- Wrote it up: "Joints matched by name" tables in `results/cross_eval.md`, Finding 7 in `notes/log.md`, and a line in
  the README.
- The away cells are still ~0%, so T18–T20 need no revision. T18 is next: it needs a new script, and there was no time
  left in this wake-up.

## Needs a human
- Sara: "What I learned" notes for T17 (`scripts/trace_episode.py`, `scripts/plot_traces.py`) and for T23
  (`scripts/dump_order.py`, `evaluate.py --match_order`).
- Still open from before: watching the 10 Reorient clips.
