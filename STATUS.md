# Status
Updated: 2026-11-12 11:24 UTC by the server agent (wake-up: state changed, PLAN.md edited to add T12)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T8 Reorient timing, 4,096 envs (exclusive) | PhysX | 217/300 | 0.00 | 0.013 | 0.000 | ~4 min (≈11:28 UTC) |

GPU at iteration 217: 9.3 GB of 46 GB, 60% utilisation. Iteration time ~3.3 s (collection 3.02 s, learning 0.28 s),
~39.7k steps/s. Peak memory so far: 9.3 GB. Full numbers go in `results/reorient_4096_timing.md` once T8 finishes.

## Since last update
- Nothing changed except progress. T8 is still iterating.
- Saw the new task **T12** (Lift transfer clips). It is `todo` but has to wait until exclusive T8 finishes. It will
  run before T9, and T5 comes after T9.

## Needs a human
- nothing. (Still worth a human look: the T7 clips, given the 0% cross-engine results from T6.)
