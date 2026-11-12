# Status
Updated: 2026-11-12 12:00 UTC by the server agent (wake-up: state changed, T5 command 1 exited; PLAN.md updated)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T5 speed benchmark, command 2 (exclusive) | Newton (Lift, 512 envs) | 82/300 | early | — | — | ~4 min (1.04 s/it) |

## Since last update
- **T5 command 1 done** (Lift PhysX 300, finished normally, `Training time: 594.88 seconds`, last iteration time
  2.02 s). Started **T5 command 2** (`scripts/train.sh lift newton 300`, folder `2026-11-12_11-57-32`), alone on the
  GPU; it's iterating. `results/speed_benchmark.md` gets written when it finishes.
- Saw the new plan (11:54): T10 and T11 start together as soon as T5 is done (next wake-up after command 2 ends).

## Needs a human
- If you want the T8/T9 `model_299.pt` files in the repo, say so (they're on the server).
- The T7 and T12 clips are ready to watch.
