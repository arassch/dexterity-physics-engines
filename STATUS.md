# Status
Updated: 2026-11-12 11:49 UTC by the server agent (wake-up: state changed, T9 training process exited)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T5 speed benchmark, command 1 (exclusive) | PhysX (Lift, 512 envs) | 2/300 | just started | — | — | a few minutes; then command 2 (Newton) |

## Since last update
- **T9 done** (finished normally, `Training time: 520.61 seconds`). Medians over iterations 100–299: iteration
  1.80 s, collection 1.527 s, learning 0.273 s, 72.8k steps/s (PhysX T8: 3.19 s, 41.1k steps/s, so Newton is ~1.8×
  faster). ~7.7 GB GPU (one early reading). At 299: success 0, ADR 0, abnormal_robot 0.079, mean reward 5.90.
  Newton column added to `results/reorient_4096_timing.md`; configs in `configs/reorient_newton_4096_timing/`,
  last 60 lines in `results/log_excerpts/`. No checkpoint copied (timing run, same as T8).
- Iteration time rose during T9 too (1.56 s at it. 19 → 1.96 s at 299, as episodes got longer), so its estimate is
  probably low.
- Started **T5** command 1 (`scripts/train.sh lift physx 300`, folder `2026-11-12_11-46-23`): its requirements are
  met (T4/T8/T9 done, GPU idle). It's iterating. Command 2 (Newton) comes next, alone on the GPU.

## Needs a human
- **T10/T11 budget decision (T9 asks for this).** Full-run estimates at 4,096 envs, 15,000 iterations, $3.65/hr:
  - Reorient PhysX (T10): 3.19 s/it → **≈ 13.3 h, ≈ $48.5**
  - Reorient Newton (T11): 1.80 s/it → **≈ 7.5 h, ≈ $27.4** (≈ 8.2 h / $29.8 at the final 1.96 s/it)
  - Both, one after the other: ≈ 20.8 h ≈ $76. Both estimates are probably low: iteration time was still rising at
    300 in both runs. Running them at the same time would slow each one down (not measured).
  T10/T11 stay on `hold` until you set iterations and budget in PLAN.md.
- If you want the T8/T9 `model_299.pt` files in the repo, say so (they're on the server).
- The T7 and T12 clips are ready to watch.
