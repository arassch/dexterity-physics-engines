# Status
Updated: 2026-11-12 11:37 UTC by the server agent (wake-up: state changed, T8 training process exited)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|
| T9 Reorient timing, 4,096 envs (exclusive) | Newton | 6/300 | 0.00 | 0.029 | 0.000 | ~8 min (≈11:45 UTC) |

T9 so far: ~1.5 s/iteration (PhysX T8 was 2.6–3.2 s), 7.7 GB GPU memory, 44% utilisation. That's an early reading;
the T8 iteration time rose as episodes got longer.

## Since last update
- **T8 done** (finished normally, `Training time: 931.65 seconds`). Medians over iterations 100–299: iteration
  3.19 s, collection 2.91 s, learning 0.27 s, 41.1k steps/s; ~9.3 GB GPU. At 299: success 0, ADR 0,
  abnormal_robot 0.010. **15,000 iterations ≈ 13.3 h ≈ $48.5.** Written to `results/reorient_4096_timing.md`.
  Iteration time rose during the run (~2.65 s → ~3.2 s, all in collection), so that estimate may be low.
- Backed up the T8 configs to `configs/reorient_physx_4096_timing/` and saved the last 60 log lines. I did **not**
  copy `model_299.pt` into the repo, because it's a 300-iteration timing run (T5 says "no checkpoints" for its
  timing runs). It's still on the server.
- **T12 done:** both transfer clips recorded with no errors: PhysX → Newton (556,607 B) and Newton → PhysX
  (786,306 B), in `~/runs/videos/`. Listed in `results/videos.md`. The play log doesn't print resets, so the clips
  need to be watched.
- Started **T9** (`scripts/train.sh reorient newton 300 --envs 4096`), run folder `2026-11-12_11-32-53`, iterating.

## Needs a human
- Nothing blocking. The T12 transfer clips (and the T7 clips) are ready to watch.
- If you want the T8 `model_299.pt` in the repo, say so (it's on the server in `logs/.../2026-11-12_11-11-43/`).
- The T9 full-run estimate will go here when T9 finishes. T10/T11 stay on hold.
