# Status
Updated: 2026-11-16 13:08 UTC by the server agent (wake-up: manual --once)

Instance hours since 15 Nov 16:00 UTC: **≈ 0.9 h ≈ $3.3** (estimate). On 15 Nov the last activity was ~15:50, so
`idle_stop.sh` would have stopped the instance by ~16:20 (~0.3 h). Today it has been up since ~12:34 UTC (~0.6 h).

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T22 A `noactpen` | PhysX (Lift) | 47 / 3,000 | 0.0 | — | — | ~2.5 h |
| T22 B `nograsp` | PhysX (Lift) | 19 / 3,000 | 0.0 | — | — | ~3.5 h |

GPU ~10.6 GB / 46 GB, 96% util. These are early readings; the ETAs will shift.

## Since last update
- T22 step 0: `train.sh` rejected `env.rewards.action_l2.weight=0` because its check didn't allow digits in term names.
  I widened the pattern to `[a-z0-9_]`; it still only accepts reward-weight overrides. The check run then showed
  `action_l2: weight: 0`. Started variants A and B.
- **T17 done.** `abnormal_robot` has one condition: |joint_vel| > 2× the velocity limit. PhysX → Newton: 14/16 envs
  end with it, median step 16 (10–35), always on hand joints, with the drives saturated at ~0.5 N·m. PhysX → PhysX:
  0/16. Written up in `results/abnormal_robot_diagnosis.md` with plots in `results/plots/trace_*.png`. New scripts:
  `trace_episode.py/.sh`, `plot_traces.py`, `joint_order.py`.
- **Surprise: the two engines order the 16 hand joints differently.** PhysX lists them by level (index_0, middle_0,
  ring_0, thumb_0, …), Newton by finger (index_0..3, middle_0..3, …). The arm joints match. Details in
  `notes/log.md`.
- T18 is now unblocked but not started (this wake-up ran out of time). It starts at the next wake-up unless the
  question below changes the plan.

## Needs a human
- **The joint-order mismatch may explain the 0% cross-engine success by itself.** The policy's actions
  (`RelativeJointPositionAction`, `joint_names=[".*"]`) and joint observations follow each engine's articulation
  order. So in T6/T13, a policy moved to the other engine probably read and drove permuted hand joints. Should
  `evaluate.py` remap the hand joints by name (or set `preserve_order=True` with an explicit joint list) and rerun the
  PhysX → Newton cells before T18–T20? That changes what it measures, so I left it alone. T18 will compare joints by
  name either way.
- Sara: "What I learned" notes for T17 (`scripts/trace_episode.py`, `scripts/plot_traces.py`).
- Still open from before: watching the 10 Reorient clips.
