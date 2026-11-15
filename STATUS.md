# Status
Updated: 2026-11-15 15:45 UTC by the server agent (wake-up: manual --once)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T14 cmd 1 (Reorient PhysX progress clips, 1000/5000/10000/14999) | PhysX | video, loading | — | — | — | minutes |
| T14 cmd 2 (Reorient Newton progress clips, 1000/5000/10000/14999) | Newton | video, loading | — | — | — | minutes |
| T15 cmd 1 (Reorient PhysX policy in Newton, 14999) | Newton | video, loading | — | — | — | minutes |

No training runs. T15 command 2 (Newton policy in PhysX) starts once command 1 finishes.

## Since last update
- Restart after the Fri idle stop: all four T13 rows were already in `results/cross_eval.csv`, so no cell was rerun.
  Committed them (they had been left uncommitted on the server).
- T13 written up and set `done`: Reorient section in `results/cross_eval.md`, Finding 3 in `notes/log.md`, README table.
  PhysX→PhysX 51.5% (48.5–54.6), PhysX→Newton 0.0% (94% abnormal_robot), Newton→Newton 64.9% (62.0–67.8),
  Newton→PhysX 0.0% (64% time-out, 24% abnormal_robot). The failure modes are the same as for Lift.
- Started T14 commands 1 and 2, and T15 command 1.

## Needs a human
- nothing (Bash works again for the allow-listed commands. Last wake-up's problem is resolved)
