# Status
Updated: 2026-11-12 10:57 UTC by the server agent (wake-up: state changed — PLAN.md updated, T6 note)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T7 videos, command 1/3 (Lift PhysX, 5 checkpoints) | PhysX | n/a | | | | started 10:55; unknown, rendering has begun |

No training running.

## Since last update
- **T4 stopped at iteration 3,315 by plan** (success 0, abnormal_robot 0.10, ADR 0, reward 8.1, 1.09 s/it). It
  recovered from the ~0.99 abnormal_robot phase like Lift Newton did, ~250 iterations sooner (table in
  `notes/log.md`). Backed up `model_3250.pt`, configs, final excerpt. `done`.
- **Fixed a mechanical bug in `scripts/evaluate.py`**: termination fractions were read from
  `extras["log"]["Episode_Termination/*"]` (a mean over all envs in Isaac Lab 3.0.0, not a per-step count); now
  counted from `termination_manager.get_term(name)[dones]`. Success counting unchanged. Smoke tests re-run after it.
- **T6 done (Finding 2): neither Lift policy transfers.** Success (95% CI), ~1,024 episodes each:
  PhysX→PhysX 95.9% (94.5–97.0) · PhysX→Newton **0.0%** (0.0–0.4), 98% abnormal_robot after ~23 steps ·
  Newton→Newton 87.0% (84.9–88.9) · Newton→PhysX **0.0%** (0.0–0.4), 66% time-out, 23% abnormal_robot, 12% out of bounds.
  Written to `results/cross_eval.md`, README, `notes/log.md`.
- Started T7 command 1. Commands 2 and 3 follow one at a time. T8 (exclusive) starts once T7 is finished.

## Needs a human
- nothing. (The 0% in both directions is a big result; worth a look at the T7 clips and maybe a PhysX→Newton clip
  before building on it. Not in PLAN.md, so I haven't recorded one.)
