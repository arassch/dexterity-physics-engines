# Status
Updated: 2026-11-16 13:11 UTC by the server agent (wake-up: manual --once)

Instance hours since 15 Nov 16:00 UTC: **≈ 0.9 h ≈ $3.3** (estimate: ~0.3 h on 15 Nov, plus ~0.6 h today. Uptime
says it booted at 12:34 UTC.)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T22 A `noactpen` | PhysX (Lift) | 306 / 3,000 | 0.0 | 0.013 | 0.0 | ~3.0 h |
| T22 B `nograsp` | PhysX (Lift) | 322 / 3,000 | 0.0 | 0.012 | 0.0 | ~2.7 h |
| T23 eval ×4 | Reorient matched: physx→newton, newton→physx, physx→physx, newton→newton | building / starting | — | — | — | ~10–20 min |

GPU 21.9 GB / 46 GB. Training success rates include exploration noise.

## Since last update
- **T23 started** (eval only, alongside T22). Step 1: the T17 traces have no body names, so a new script,
  `scripts/dump_order.py`, wrote `results/joint_order.json` for both engines. Step 2: added
  `evaluate.py --match_order <engine>` (optional last argument of `eval.sh`). Step 3: the smoke test passed the name
  check (the action, joint_pos, joint_vel and hand-tip lists all equal PhysX's).
- The hand-tip bodies (`hand_tips_state_b`) resolve in the **same** order in both engines. In T6/T13 only the 16 hand
  joints were permuted (actions, joint_pos, joint_vel).
- Smoke result, PhysX → Newton matched (32 episodes only): **0/32 success, abnormal_robot 0.97**. That is too few
  episodes to conclude anything; the 1,024-episode cells will tell.
- Started the 4 Reorient matched cells (1,024 episodes each). The 4 Lift cells come after them (eval limit 4).

## Needs a human
- Sara: "What I learned" notes for T17 (`scripts/trace_episode.py`, `scripts/plot_traces.py`), and later for T23
  (`scripts/dump_order.py`, `evaluate.py --match_order`).
- Still open from before: watching the 10 Reorient clips.
