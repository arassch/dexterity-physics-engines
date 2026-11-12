# Status
Updated: 2026-11-12 10:52 UTC by the server agent (wake-up: state changed — PLAN.md updated, T6 note)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T6 cell 1 eval (Lift PhysX policy in PhysX, 1,024 episodes) | PhysX | n/a | running | | | minutes |

No training running. T4 stopped.

## Since last update
- **T4 stopped at iteration 3,315 by plan** (success 0, abnormal_robot 0.10, ADR 0, reward 8.1, 1.09 s/it).
  It recovered from the ~0.99 abnormal_robot phase like Lift Newton did, ~250 iterations sooner (table in
  `notes/log.md`). Backed up `model_3250.pt`, configs, final excerpt. Set `done`.
- **T6 smoke test done.** Fixed one mechanical bug in `scripts/evaluate.py`: termination fractions were read from
  `extras["log"]["Episode_Termination/*"]`, which in Isaac Lab 3.0.0 is a mean over all envs, not a per-step count;
  now counted from `termination_manager.get_term(name)[dones]`. Success counting unchanged. Re-ran both smoke tests.
- Smoke: Lift PhysX policy in PhysX 32/32 success; **in Newton 0/33, every episode ends `abnormal_robot` after
  ~20–25 steps.** Big gap; the Newton→Newton cell will show whether it's transfer or the Newton Play setup.
- Started T6 step 2 cell 1 (physx→physx). Cells 2–4 follow one at a time; then T7.

## Needs a human
- nothing (FYI: T8 is exclusive, so it waits until the T6 evals and T7 video jobs are finished.)
