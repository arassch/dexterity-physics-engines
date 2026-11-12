# Status
Updated: 2026-11-12 11:14 UTC by the server agent (wake-up: state changed, T7 video jobs finished)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T8 Reorient timing, 4,096 envs (exclusive) | PhysX | 1/300 | 0.00 | — | — | ~16 min (≈11:30 UTC) |

GPU at iteration 1: 9.1 GB of 46 GB, 66–70% utilisation. Peak memory will go in `results/reorient_4096_timing.md`.

## Since last update
- **T7 done.** Commands 1 and 2 had finished by 11:06. Ran command 3 (Lift Newton resume folder `2026-11-11_23-21-33`,
  `model_14999`). That makes 11 clips, all recorded without errors; listed in `results/videos.md` (the .mp4 files stay on the server).
- **Started T8** (`scripts/train.sh reorient physx 300 --envs 4096`), run folder `2026-11-12_11-11-43`, once the GPU
  was idle (0 MiB). It is past setup and iterating. T9 follows once T8 is done; T5 waits until after T9.
- Committed a leftover uncommitted RUNS.md edit (it fills in the Lift Newton resume folder).

## Needs a human
- nothing. (Still worth a human look: the T7 clips, given the 0% cross-engine results from T6.)
